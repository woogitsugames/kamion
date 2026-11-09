using System;
using System.Collections.Generic;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// The wheel ends of one rigid body (tractor or trailer): multi-ray contact, suspension (steel or levelled
    /// air springs, anti-roll), tire relaxation + combined slip, wheel spin and the brake Coulomb constraints.
    /// Shared by <see cref="VehicleModel"/> and <see cref="TrailerModel"/>. No allocations after construction.
    /// </summary>
    public sealed class WheelGroup
    {
        public readonly WheelState[] Wheels;
        public readonly AxleDefinition[] Axles;
        readonly int[] _left, _right;
        readonly double[] _rayCos, _raySin;
        readonly int _constraintIterations;

        /// <param name="referenceAxleLoads">Per-axle static load [N] of the vehicle's own definition (solo / empty); defines the design ride height.</param>
        public WheelGroup(AxleDefinition[] axles, IDictionary<string, TireDefinition> tires, SolverSettings settings,
            double[] referenceAxleLoads, double comX, double steerRefZ, string namePrefix)
        {
            Axles = axles;
            _constraintIterations = settings.constraintIterations;
            var wheels = new List<WheelState>();
            var tireModels = new Dictionary<string, TireModel>();
            _left = new int[axles.Length];
            _right = new int[axles.Length];
            for (int ai = 0; ai < axles.Length; ai++)
            {
                var a = axles[ai];
                if (!tires.TryGetValue(a.tireId, out var tdef)) throw new FormatException($"Tire '{a.tireId}' not found");
                if (!tireModels.TryGetValue(a.tireId, out var tm)) { tm = new TireModel(tdef); tireModels[a.tireId] = tm; }
                for (int side = -1; side <= 1; side += 2)
                {
                    double x = side * a.trackWidth * 0.5;
                    double frac = 0.5 + side * comX / a.trackWidth;
                    var su = a.suspension;
                    double refLoad = su.referenceLoadN > 0 ? su.referenceLoadN : referenceAxleLoads[ai] * frac;
                    var ws = new WheelState
                    {
                        Name = namePrefix + a.name + (side < 0 ? "_L" : "_R"),
                        AxleIndex = ai,
                        Side = side,
                        Axle = a,
                        Tire = tm,
                        TireCount = a.tiresPerSide,
                        Steered = a.steered,
                        Driven = a.driven,
                        Radius = tdef.radius,
                        Inertia = tdef.wheelInertia * a.tiresPerSide,
                        StaticLoad = referenceAxleLoads[ai] * frac,
                        ReferenceLoad = refLoad,
                        Preload = refLoad,
                        WheelbaseFromRef = a.positionZ - steerRefZ,
                    };
                    ws.SStatic = su.staticPositionFraction * su.travel;
                    // Hardpoint: with the reference load the wheel sits at the static position and the
                    // vehicle origin is on the ground (design ride height).
                    double tireDefl = refLoad / (tdef.radialStiffness * a.tiresPerSide);
                    ws.HardpointLocal = new Vec3(x, tdef.radius + ws.SStatic - tireDefl, a.positionZ);
                    ws.S = ws.SStatic;
                    if (side < 0) _left[ai] = wheels.Count; else _right[ai] = wheels.Count;
                    wheels.Add(ws);
                }
            }
            Wheels = wheels.ToArray();
            SetStaticLoads(referenceAxleLoads, comX, true);

            int n = Math.Max(1, settings.contactRays);
            _rayCos = new double[n];
            _raySin = new double[n];
            double arc = settings.contactArcDeg * MathUtil.Deg2Rad;
            for (int i = 0; i < n; i++)
            {
                double th = n == 1 ? 0 : -arc + 2 * arc * i / (n - 1);
                _rayCos[i] = Math.Cos(th);
                _raySin[i] = Math.Sin(th);
            }
        }

        public int LeftOf(int axle) => _left[axle];
        public int RightOf(int axle) => _right[axle];

        /// <summary>Sets the static load of the current configuration; air springs are pre-levelled to it.</summary>
        public void SetStaticLoads(double[] axleLoads, double comX, bool levelAirSprings)
        {
            foreach (var w in Wheels)
            {
                double frac = 0.5 + w.Side * comX / w.Axle.trackWidth;
                w.StaticLoad = axleLoads[w.AxleIndex] * frac;
                if (w.Axle.suspension.airLevelling && levelAirSprings) w.Preload = w.StaticLoad;
            }
        }

        public double TotalStaticLoad
        {
            get { double s = 0; foreach (var w in Wheels) s += w.StaticLoad; return s; }
        }

        /// <summary>Axle load signal used by load-sensing (EBS ALB): bellows force for air springs, static load for steel springs.</summary>
        public double AxleLoadSignal(int axle)
        {
            var l = Wheels[_left[axle]]; var r = Wheels[_right[axle]];
            return l.Axle.suspension.airLevelling ? l.Preload + r.Preload : l.StaticLoad + r.StaticLoad;
        }

        // ------------------------------------------------------------------ contact & suspension

        public void UpdateContacts(double dt, in ChassisState c, Vec3 up, IGroundQuery ground, Steering steering)
        {
            for (int i = 0; i < Wheels.Length; i++)
            {
                var w = Wheels[i];
                w.SteerAngle = w.Steered && steering != null ? steering.WheelAngle(w.HardpointLocal.x, w.WheelbaseFromRef) : 0;
                UpdateContact(w, dt, c, up, ground);
            }
            ApplyAntiRoll();
            for (int i = 0; i < Wheels.Length; i++) FinalizeContact(Wheels[i], c, up);
        }

        void UpdateContact(WheelState w, double dt, in ChassisState c, Vec3 up, IGroundQuery ground)
        {
            var su = w.Axle.suspension;
            Vec3 hp = c.LocalToWorld(w.HardpointLocal);
            Vec3 wheelFwd = c.Rotation * new Vec3(Math.Sin(w.SteerAngle), 0, Math.Cos(w.SteerAngle));
            Vec3 down = -up;
            double r = w.Radius;
            double maxDist = su.travel + r + 0.05;

            double bestS = double.MaxValue;
            Vec3 bestPoint = Vec3.Zero, bestNormal = up;
            int bestIdx = -1;
            double friction = 1, rrScale = 1; int surface = 0;
            int n = _rayCos.Length;
            int mid = n / 2;
            for (int i = 0; i < n; i++)
            {
                Vec3 origin = hp + wheelFwd * (r * _raySin[i]);
                if (!ground.Raycast(origin, down, maxDist, out GroundHit hit)) continue;
                double s = hit.Distance - r * _rayCos[i];
                if (s < bestS)
                {
                    bestS = s; bestPoint = hit.Point; bestIdx = i;
                    bestNormal = hit.Normal;
                    friction = hit.FrictionScale; rrScale = hit.RollingResistanceScale; surface = hit.SurfaceId;
                }
            }

            if (bestIdx < 0 || bestS > su.travel)
            {
                w.Contact = false;
                w.S = su.travel;
                w.Fz = 0;
                w.SuspensionForce = 0;
                w.CompressionRate = 0;
                w.HasPrev = false;
                w.Ux *= 0.5; w.Uy *= 0.5;
                w.Compression = w.SStatic - w.S;
                return;
            }

            w.Contact = true;
            w.S = bestS;
            Vec3 center = hp + down * bestS;
            Vec3 normal = bestNormal;
            if (n > 1 && bestIdx != mid) normal = (center - bestPoint).Normalized; // edge contact acts through the wheel centre
            w.ContactPoint = bestPoint;
            w.Normal = normal;
            w.FrictionScale = friction; w.RollingResistanceScale = rrScale; w.SurfaceId = surface;

            // Tire radial compliance in series with the suspension: solve F = f_susp(s_geo + F/k_tire) (Newton).
            double kt = w.Tire.Def.radialStiffness * w.TireCount;
            double fs = SpringForce(su, w, w.S);
            for (int it = 0; it < 6; it++)
            {
                double se = Math.Min(w.S + Math.Max(fs, 0) / kt, su.travel);
                double g = fs - SpringForce(su, w, se);
                double kloc = SpringStiffness(su, w, se);
                double dfs = -g / (1 + kloc / kt);
                fs += dfs;
                if (Math.Abs(dfs) < 1e-3) break;
            }
            double sEff = Math.Min(w.S + Math.Max(fs, 0) / kt, su.travel);
            w.TireDeflection = Math.Max(fs, 0) / kt;

            double rate = w.HasPrev ? (w.SPrev - sEff) / dt : 0;
            rate = MathUtil.Clamp(rate, -2.0, 2.0);
            w.CompressionRate = rate;
            w.SPrev = sEff;
            w.HasPrev = true;
            w.Compression = w.SStatic - sEff;
            w.SuspensionForce = SpringForce(su, w, sEff) + DamperForce(su, rate);
        }

        static double RateScale(SuspensionDefinition su, WheelState w) =>
            su.airLevelling && w.ReferenceLoad > 0 ? w.Preload / w.ReferenceLoad : 1.0;

        /// <summary>Spring (preload + linear + cubic progression) + bump stop force at centre drop s.</summary>
        public static double SpringForce(SuspensionDefinition su, WheelState w, double s)
        {
            double x = w.SStatic - s;
            double f = w.Preload + su.springRate * RateScale(su, w) * x + su.progressiveRate * x * x * x;
            if (s < su.bumpStopClearance)
            {
                double b = su.bumpStopClearance - s;
                f += su.bumpStopRate * b * b;
            }
            return f;
        }

        /// <summary>-dF/ds (positive stiffness) of SpringForce.</summary>
        public static double SpringStiffness(SuspensionDefinition su, WheelState w, double s)
        {
            double x = w.SStatic - s;
            double k = su.springRate * RateScale(su, w) + 3 * su.progressiveRate * x * x;
            if (s < su.bumpStopClearance) k += 2 * su.bumpStopRate * (su.bumpStopClearance - s);
            return k;
        }

        static double DamperForce(SuspensionDefinition su, double v)
        {
            double c = v >= 0 ? su.damperBump : su.damperRebound;
            double av = Math.Abs(v);
            double mag = av <= su.damperKneeVelocity
                ? c * av
                : c * su.damperKneeVelocity + c * su.damperHighSpeedFactor * (av - su.damperKneeVelocity);
            return Math.Sign(v) * mag;
        }

        void ApplyAntiRoll()
        {
            for (int ai = 0; ai < Axles.Length; ai++)
            {
                var a = Axles[ai];
                if (a.suspension.antiRollStiffness <= 0) continue;
                var l = Wheels[_left[ai]]; var r = Wheels[_right[ai]];
                if (!l.Contact || !r.Contact) continue;
                double kLin = a.suspension.antiRollStiffness / (a.trackWidth * a.trackWidth);
                double df = kLin * (l.Compression - r.Compression);
                l.SuspensionForce += df;
                r.SuspensionForce -= df;
            }
        }

        void FinalizeContact(WheelState w, in ChassisState c, Vec3 up)
        {
            if (!w.Contact) { w.Vx = 0; w.Vy = 0; return; }
            double cosN = Vec3.Dot(w.Normal, up);
            if (cosN < 0.3) cosN = 0.3;
            w.Fz = Math.Max(0, w.SuspensionForce) / cosN;
            Vec3 wheelFwd = c.Rotation * new Vec3(Math.Sin(w.SteerAngle), 0, Math.Cos(w.SteerAngle));
            Vec3 fwd = Vec3.ProjectOnPlane(wheelFwd, w.Normal).Normalized;
            w.Forward = fwd;
            w.Lateral = Vec3.Cross(w.Normal, fwd);
            Vec3 vp = c.PointVelocity(w.ContactPoint);
            w.Vx = Vec3.Dot(vp, fwd);
            w.Vy = Vec3.Dot(vp, w.Lateral);
        }

        /// <summary>
        /// Air-spring height levelling (one levelling valve per axle, symmetric): the bellows force moves so
        /// that the mean compression of the axle returns to zero. Interconnected axles share the pressure.
        /// </summary>
        public void UpdateLevelling(double dt)
        {
            for (int ai = 0; ai < Axles.Length; ai++)
            {
                var su = Axles[ai].suspension;
                if (!su.airLevelling) continue;
                var l = Wheels[_left[ai]]; var r = Wheels[_right[ai]];
                if (!l.Contact && !r.Contact) continue;
                double mean = 0.5 * (l.Compression + r.Compression);
                double err = mean > su.levellingDeadband ? mean - su.levellingDeadband : (mean < -su.levellingDeadband ? mean + su.levellingDeadband : 0);
                if (err == 0) continue;
                double tau = Math.Max(su.levellingTimeConstant, dt);
                l.Preload += dt / tau * su.springRate * RateScale(su, l) * err;
                r.Preload += dt / tau * su.springRate * RateScale(su, r) * err;
                double floor = 0.1 * l.ReferenceLoad;
                if (l.Preload < floor) l.Preload = floor;
                if (r.Preload < 0.1 * r.ReferenceLoad) r.Preload = 0.1 * r.ReferenceLoad;
            }
            // Interconnected bellows: equalise per side within a group.
            for (int ai = 0; ai < Axles.Length; ai++)
            {
                int g = Axles[ai].suspension.levellingGroup;
                if (g == 0 || !Axles[ai].suspension.airLevelling) continue;
                bool first = true;
                for (int k = 0; k < ai; k++) if (Axles[k].suspension.levellingGroup == g) { first = false; break; }
                if (!first) continue;
                double sl = 0, sr = 0; int cnt = 0;
                for (int k = ai; k < Axles.Length; k++)
                    if (Axles[k].suspension.levellingGroup == g) { sl += Wheels[_left[k]].Preload; sr += Wheels[_right[k]].Preload; cnt++; }
                sl /= cnt; sr /= cnt;
                for (int k = ai; k < Axles.Length; k++)
                    if (Axles[k].suspension.levellingGroup == g) { Wheels[_left[k]].Preload = sl; Wheels[_right[k]].Preload = sr; }
            }
        }

        /// <summary>
        /// Static ground-contact height of an axle in the vehicle frame [m] (mean of both sides) for the current
        /// static loads: 0 when the axle carries its reference load, negative when it is more loaded (sags).
        /// Used to place a vehicle at equilibrium before the first step.
        /// </summary>
        public double StaticGroundOffset(int axle)
        {
            double sum = 0;
            for (int k = 0; k < 2; k++)
            {
                var w = Wheels[k == 0 ? _left[axle] : _right[axle]];
                var su = w.Axle.suspension;
                double s = w.SStatic;
                for (int it = 0; it < 30; it++)
                {
                    double g = SpringForce(su, w, s) - w.StaticLoad;
                    double kk = SpringStiffness(su, w, s);
                    double ds = g / kk; // F decreases with s
                    s += ds;
                    if (Math.Abs(ds) < 1e-9) break;
                }
                double kt = w.Tire.Def.radialStiffness * w.TireCount;
                double defl = w.StaticLoad / kt, deflRef = w.ReferenceLoad / kt;
                // ground y = hp.y - s - r + defl = SStatic - s + defl - deflRef
                sum += w.SStatic - s + defl - deflRef;
            }
            return 0.5 * sum;
        }

        // ------------------------------------------------------------------ tires & wheel spin

        public void ClearAccumulators()
        {
            for (int i = 0; i < Wheels.Length; i++) { var w = Wheels[i]; w.Fx = 0; w.Fy = 0; w.DriveTorque = 0; }
        }

        /// <summary>One substep of tire forces and free wheel spin (before the constraint solve).</summary>
        public void TireAndSpinSubstep(double h)
        {
            for (int i = 0; i < Wheels.Length; i++)
            {
                var w = Wheels[i];
                TireSubstep(w, h, out double fx, out double fy);
                w.Fx += fx; w.Fy += fy;
                double torque = -fx * w.Radius;
                double dOmega = h * torque / w.Inertia;
                if (w.RetarderTorque > 0)
                {
                    double dr = h * w.RetarderTorque / w.Inertia;
                    // Explicit retarder torque opposes rotation and never reverses it.
                    double o = w.Omega + dOmega;
                    if (o > 0) o = Math.Max(0, o - dr); else if (o < 0) o = Math.Min(0, o + dr);
                    w.Omega = o;
                }
                else w.Omega += dOmega;
            }
        }

        static void TireSubstep(WheelState w, double h, out double fx, out double fy)
        {
            fx = 0; fy = 0;
            var td = w.Tire.Def;
            if (!w.Contact || w.Fz <= 0)
            {
                w.SlipRatio = 0; w.SlipAngle = 0; w.Mu = 0;
                return;
            }
            double wr = w.Omega * w.Radius;
            double vsx = w.Vx - wr;
            double vref = Math.Max(Math.Abs(w.Vx), Math.Abs(wr));
            double sx = td.relaxationLengthX, sy = td.relaxationLengthY;
            double mu = w.Tire.PeakMu(w.Fz / w.TireCount, w.FrictionScale);
            double fzt = w.Fz / w.TireCount;
            double uxMax = sx * 1.0;
            double uyMax = sy * Math.Max(1.0, 4 * w.Tire.PeakTanAlpha(mu, fzt));
            // At low speed the deflection state is a real contact-patch spring: it cannot hold more than the
            // deflection at peak force (sliding beyond it is dissipated). Without this, a wheel that slid locked
            // keeps ~sigma of "deflection" when the vehicle stops and springs the truck back (rebound artefact).
            double moving = MathUtil.Clamp01(vref / td.lowSpeedFadeMs);
            if (moving < 1)
            {
                double uxStick = 1.2 * sx * w.Tire.PeakKappa(mu, fzt);
                double uyStick = 1.2 * sy * w.Tire.PeakTanAlpha(mu, fzt);
                uxMax = MathUtil.Lerp(Math.Min(uxStick, uxMax), uxMax, moving);
                uyMax = MathUtil.Lerp(Math.Min(uyStick, uyMax), uyMax, moving);
            }
            // Dissipate the excess before integrating, so the low-speed damper does not see the clamp as a rate.
            double uxOld = MathUtil.Clamp(w.Ux, -uxMax, uxMax), uyOld = MathUtil.Clamp(w.Uy, -uyMax, uyMax);
            double ux = (uxOld - h * vsx) / (1 + h * vref / sx);
            double uy = (uyOld - h * w.Vy) / (1 + h * vref / sy);

            ux = MathUtil.Clamp(ux, -uxMax, uxMax);
            uy = MathUtil.Clamp(uy, -uyMax, uyMax);
            w.Ux = ux; w.Uy = uy;

            double kappa = ux / sx;
            double tanA = uy / sy;
            w.Tire.CombinedForces(w.Fz, w.TireCount, w.FrictionScale, kappa, tanA, out fx, out fy, out mu);
            w.Mu = mu;
            w.SlipRatio = kappa;
            w.SlipAngle = Math.Atan(tanA);
            w.KinematicSlip = (wr - w.Vx) / Math.Max(Math.Abs(w.Vx), 0.5);

            // Low-speed contact damping on deflection rate (fades out with speed).
            double fade = MathUtil.Clamp01(1 - vref / td.lowSpeedFadeMs);
            if (fade > 0)
            {
                double kx = w.Tire.LongitudinalDeflectionStiffness(w.Fz, w.TireCount);
                double ky = w.Tire.LateralDeflectionStiffness(w.Fz, w.TireCount);
                fx += kx * td.lowSpeedDampingTau * (ux - uxOld) / h * fade;
                fy += ky * td.lowSpeedDampingTau * (uy - uyOld) / h * fade;
            }
            double lim = mu * w.Fz;
            double mag = Math.Sqrt(fx * fx + fy * fy);
            if (mag > lim && mag > 0) { double s = lim / mag; fx *= s; fy *= s; }
        }

        public void BeginConstraintSubstep()
        {
            for (int i = 0; i < Wheels.Length; i++) Wheels[i].BrakeImpulseAcc = 0;
        }

        /// <summary>One projected Gauss-Seidel pass over the brake (+ rolling resistance) Coulomb constraints.</summary>
        public void BrakeIteration(double h)
        {
            for (int i = 0; i < Wheels.Length; i++)
            {
                var w = Wheels[i];
                double rr = w.Contact ? w.Tire.Def.rollingResistanceCoeff * w.RollingResistanceScale * w.Fz * w.Radius : 0;
                double capB = (w.BrakeTorque + rr) * h;
                if (capB <= 0) continue;
                double dl = w.Omega * w.Inertia;
                double newLam = MathUtil.Clamp(w.BrakeImpulseAcc + dl, -capB, capB);
                dl = newLam - w.BrakeImpulseAcc;
                w.BrakeImpulseAcc = newLam;
                w.Omega -= dl / w.Inertia;
            }
        }

        /// <summary>Brake constraint solve of a wheel-only substep (trailer), after TireAndSpinSubstep and the chamber update.</summary>
        public void SolveBrakes(double h)
        {
            BeginConstraintSubstep();
            for (int it = 0; it < _constraintIterations; it++) BrakeIteration(h);
        }

        /// <summary>
        /// Wheel deceleration signal for ABS, updated every substep: tread acceleration over the substep, lightly
        /// filtered (5 ms, like a wheel-speed sensor signal chain) so it does not depend on the substep length.
        /// </summary>
        public void UpdateTreadAccel(double h)
        {
            double a = Math.Min(1.0, h / 0.005);
            for (int i = 0; i < Wheels.Length; i++)
            {
                var w = Wheels[i];
                double raw = (w.Omega - w.OmegaPrevStep) * w.Radius / h;
                w.TreadAccel += (raw - w.TreadAccel) * a;
                w.OmegaPrevStep = w.Omega;
            }
        }

        /// <summary>Averages the substep forces and adds the contact forces to the output list and resultants.</summary>
        public void AssembleForces(int substeps, in ChassisState chassis, AppliedForce[] forces, ref int count, ref Vec3 totalF, ref Vec3 totalT)
        {
            for (int i = 0; i < Wheels.Length; i++)
            {
                var w = Wheels[i];
                w.Fx /= substeps; w.Fy /= substeps; w.DriveTorque /= substeps;
                if (!w.Contact) continue;
                Vec3 f = w.Normal * w.Fz + w.Forward * w.Fx + w.Lateral * w.Fy;
                forces[count].Force = f;
                forces[count].Point = w.ContactPoint;
                count++;
                totalF += f;
                totalT += Vec3.Cross(w.ContactPoint - chassis.CenterOfMassWorld, f);
                double apk = w.Tire.PeakTanAlpha(Math.Max(w.Mu, 0.05), Math.Max(w.Fz, 1) / w.TireCount);
                double trail = w.Tire.Def.pneumaticTrail0 * MathUtil.Clamp01(1 - Math.Abs(Math.Tan(w.SlipAngle)) / apk);
                w.AligningTorque = -trail * w.Fy;
            }
        }
    }
}
