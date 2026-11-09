using System;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// Combined-slip tire model with relaxation (contact-patch deflection states).
    ///
    /// Transient slip: d(u)/dt = -Vs - (Vref/sigma) u with Vref = max(|Vx|, |omega R|).
    /// Transient slip quantities kappa' = ux/sigma_x, tan(alpha') = uy/sigma_y converge to the classic
    /// steady-state slips when rolling, and become a pure spring (u integrates sliding displacement) at
    /// standstill. With the wheel locked by a brake (omega == 0 exactly) and Vx -> 0 there is no decay,
    /// so the vehicle is held by a spring + low-speed damper without creep.
    ///
    /// Steady-state forces: Magic Formula per direction, combined via normalized slip vector
    /// (pure-slip curves reproduced exactly, friction-ellipse-like saturation under combined slip).
    /// One instance per TireDefinition; stateless (wheel state lives in WheelState).
    /// </summary>
    public sealed class TireModel
    {
        public readonly TireDefinition Def;
        // Normalized peak positions x_pk where C*atan(x - E(x - atan x)) = pi/2.
        readonly double _xPeakX, _xPeakY;

        public TireModel(TireDefinition def)
        {
            def.Validate();
            Def = def;
            _xPeakX = SolvePeak(def.shapeCx, def.curvatureEx);
            _xPeakY = SolvePeak(def.shapeCy, def.curvatureEy);
        }

        static double SolvePeak(double c, double e)
        {
            double target = Math.Tan(Math.PI / (2.0 * c));
            // phi(x) = x - E(x - atan x) is monotonic for E < 1; bisection.
            double lo = 0, hi = 100;
            for (int i = 0; i < 100; i++)
            {
                double mid = 0.5 * (lo + hi);
                double phi = mid - e * (mid - Math.Atan(mid));
                if (phi < target) lo = mid; else hi = mid;
            }
            return 0.5 * (lo + hi);
        }

        static double Mf(double b, double c, double d, double e, double slip)
        {
            double bx = b * slip;
            return d * Math.Sin(c * Math.Atan(bx - e * (bx - Math.Atan(bx))));
        }

        /// <summary>Peak friction coefficient for a single tire load on a surface.</summary>
        public double PeakMu(double fzPerTire, double frictionScale)
        {
            double dfz = fzPerTire / Def.nominalLoadN - 1.0;
            double mu = Def.peakMu * (1.0 + Def.muLoadSensitivity * dfz);
            if (mu < 0.1 * Def.peakMu) mu = 0.1 * Def.peakMu;
            return mu * frictionScale;
        }

        /// <summary>
        /// Slip stiffness per unit load at a single-tire load fzt: degressive, K = k0 * Fz0 * (Fz/Fz0)^p,
        /// so K/Fz = k0 * (Fz/Fz0)^(p-1). p &lt; 1 gives the real-tire "stiffness grows slower than load"
        /// behaviour, which is what makes a vehicle understeer (heavily loaded steer axle, dual rear tires).
        /// </summary>
        public double KxPerLoad(double fzt) => Def.longitudinalStiffnessPerLoad * Math.Pow(Math.Max(fzt, 100.0) / Def.nominalLoadN, Def.longitudinalLoadExponent - 1.0);
        public double KyPerLoad(double fzt) => Def.corneringStiffnessPerLoad * Math.Pow(Math.Max(fzt, 100.0) / Def.nominalLoadN, Def.corneringLoadExponent - 1.0);

        /// <summary>Peak longitudinal slip ratio for the given mu and single-tire load.</summary>
        public double PeakKappa(double mu, double fzt) => _xPeakX * Def.shapeCx * mu / KxPerLoad(fzt);
        /// <summary>Peak lateral slip (tan alpha) for the given mu and single-tire load.</summary>
        public double PeakTanAlpha(double mu, double fzt) => _xPeakY * Def.shapeCy * mu / KyPerLoad(fzt);

        /// <summary>
        /// Steady-state combined forces for a wheel end carrying fz (all tires of the wheel end).
        /// kappa: slip ratio, tanAlpha: tangent of slip angle (positive -> positive Fy along the wheel's right axis).
        /// </summary>
        public void CombinedForces(double fz, int tireCount, double frictionScale, double kappa, double tanAlpha,
            out double fx, out double fy, out double mu)
        {
            fx = 0; fy = 0;
            double fzt = fz / tireCount;
            mu = PeakMu(fzt, frictionScale);
            if (fz <= 0) return;
            double kxl = KxPerLoad(fzt), kyl = KyPerLoad(fzt);
            double kpk = _xPeakX * Def.shapeCx * mu / kxl;
            double apk = _xPeakY * Def.shapeCy * mu / kyl;
            double sx = kappa / kpk;
            double sy = tanAlpha / apk;
            double s = Math.Sqrt(sx * sx + sy * sy);
            double d = mu * fz;
            double bx = kxl / (Def.shapeCx * mu);
            double by = kyl / (Def.shapeCy * mu);
            if (s < 1e-9)
            {
                fx = kxl * fz * kappa;
                fy = kyl * fz * tanAlpha;
                return;
            }
            double fx0 = Mf(bx, Def.shapeCx, d, Def.curvatureEx, s * kpk);
            double fy0 = Mf(by, Def.shapeCy, d, Def.curvatureEy, s * apk);
            fx = fx0 * sx / s;
            fy = fy0 * sy / s;
        }

        /// <summary>Longitudinal deflection stiffness of a wheel end carrying fz on tireCount tires [N/m].</summary>
        public double LongitudinalDeflectionStiffness(double fz, int tireCount) => KxPerLoad(fz / tireCount) * fz / Def.relaxationLengthX;
        public double LateralDeflectionStiffness(double fz, int tireCount) => KyPerLoad(fz / tireCount) * fz / Def.relaxationLengthY;
    }
}
