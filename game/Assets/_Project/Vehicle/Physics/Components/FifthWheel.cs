using System;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// Fifth wheel / kingpin coupling as a custom velocity-level constraint between two rigid bodies.
    ///
    /// The solver predicts both bodies' velocities at the end of the step from the forces the models produced
    /// (plus gravity, with the same semi-implicit Euler a rigid-body host uses), then solves with sequential
    /// impulses:
    /// <list type="bullet">
    /// <item>kingpin point: rigid 3-DOF ball joint (3x3 block solve, Baumgarte feedback with a speed cap);</item>
    /// <item>roll: stiff torsional spring-damper as an implicit soft constraint (unconditionally stable) plus a hard roll stop;</item>
    /// <item>pitch: free plate oscillation inside +/- pitch limit (one-sided stops);</item>
    /// <item>yaw (articulation): free inside +/- yaw limit, so jackknife is possible, with greased plate Coulomb friction.</item>
    /// </list>
    /// The result is returned as an equivalent force at the kingpin plus a pure torque per body for this step,
    /// so any host that integrates F/m and I^-1 tau (PhysX, the .NET runner) applies it with ordinary force calls.
    /// No allocations.
    /// </summary>
    public sealed class FifthWheel
    {
        public readonly FifthWheelDefinition Def;
        public bool Coupled;

        /// <summary>Constraint force on the trailer at the kingpin [N, world] (the tractor gets the opposite).</summary>
        public Vec3 ForceOnTrailer;
        /// <summary>Pure constraint torque on the trailer [N m, world] (the tractor gets the opposite).</summary>
        public Vec3 TorqueOnTrailer;
        public Vec3 KingpinWorld;
        /// <summary>Force the trailer puts on the tractor, in the tractor frame: x lateral, y = vertical load (positive = pressing down), z longitudinal (positive = pushing forward).</summary>
        public Vec3 KingpinLoadLocal;
        /// <summary>Articulation angle (tractor heading relative to trailer, + = tractor turned right) [rad], plate pitch and relative roll [rad].</summary>
        public double Articulation, PitchAngle, RollAngle;
        public double PositionError;
        public int CouplingEvents, UncouplingEvents;
        /// <summary>Time since the jaw locked [s]; during the engagement phase the kingpin point is compliant.</summary>
        public double SinceCoupled = 100;

        public FifthWheel(FifthWheelDefinition def) { Def = def; }

        struct Body
        {
            public double InvMass;
            public Mat3 InvI;
            public Vec3 V, W, R; // predicted velocities, anchor offset from CoM
        }

        /// <summary>Returns true and couples when the kingpin is inside the capture window of the open jaw.</summary>
        public bool TryCapture(in ChassisState a, Vec3 anchorA, in ChassisState b, Vec3 anchorB)
        {
            if (Coupled) return true;
            Vec3 pA = a.LocalToWorld(anchorA), pB = b.LocalToWorld(anchorB);
            Vec3 d = a.Rotation.InverseRotate(pB - pA);
            double horiz = Math.Sqrt(d.x * d.x + d.z * d.z);
            Vec3 rel = b.PointVelocity(pB) - a.PointVelocity(pA);
            Vec3 fa = a.Rotation * Vec3.Forward, fb = b.Rotation * Vec3.Forward;
            if (horiz < Def.captureDistance && Math.Abs(d.y) < Def.captureHeight && rel.Magnitude < Def.captureMaxSpeed && Vec3.Dot(fa, fb) > 0.9)
            {
                Coupled = true;
                CouplingEvents++;
                SinceCoupled = 0;
                return true;
            }
            return false;
        }

        /// <summary>Magnitude of the throat ramp force of the last <see cref="ComputeThroatGuide"/> call [N] (0 = not touching).</summary>
        public double GuideForce;
        /// <summary>Kingpin offset from the jaw centre in the tractor frame (x right, y up, z forward) while not coupled, for HUD / telemetry.</summary>
        public Vec3 OpenJawOffset;

        /// <summary>
        /// R5: coupling throat. While the jaw is open, a kingpin inside the funnel but outside its local half-width is pushed
        /// towards the centre line by the ramp. Returns true with the force on the trailer at the kingpin (the tractor gets the
        /// opposite force at the same point). Zero outside the funnel (miss), too high or too low, or when coupled.
        /// </summary>
        public bool ComputeThroatGuide(in ChassisState a, Vec3 anchorA, in ChassisState b, Vec3 anchorB, out Vec3 forceOnTrailer)
        {
            forceOnTrailer = Vec3.Zero;
            GuideForce = 0;
            if (Coupled) return false;
            Vec3 pA = a.LocalToWorld(anchorA), pB = b.LocalToWorld(anchorB);
            Vec3 d = a.Rotation.InverseRotate(pB - pA);
            OpenJawOffset = d;
            double len = Def.captureThroatLength;
            if (len <= 1e-6 || Math.Abs(d.y) >= Def.captureHeight || d.z > Def.captureDistance || d.z < -len) return false;
            double ax = Math.Abs(d.x);
            if (ax > Def.captureThroatHalfWidth) return false;
            // The ramps end in the jaw cup, half the capture radius wide, so the guided kingpin is inside the capture radius.
            double jaw = 0.5 * Def.captureDistance;
            double m = Math.Max(0, (Def.captureThroatHalfWidth - jaw) / len);
            double zr = Math.Min(0, d.z);
            double pen = ax - (jaw + m * (-zr));
            if (d.z > 0) m = 0;
            if (pen <= 0) return false;
            double sgn = d.x >= 0 ? 1 : -1;
            Vec3 vrel = a.Rotation.InverseRotate(b.PointVelocity(pB) - a.PointVelocity(pA));
            double n = Def.captureGuideStiffness * pen + Def.captureGuideDamping * (sgn * vrel.x + m * vrel.z);
            n = MathUtil.Clamp(n, 0, Def.captureGuideMaxForce);
            if (n <= 0) return false;
            Vec3 dir = new Vec3(-sgn, 0, -m) * (1.0 / Math.Sqrt(1 + m * m));
            forceOnTrailer = a.Rotation * (dir * n);
            GuideForce = n;
            return true;
        }

        /// <summary>Back to an open, empty jaw without counting an uncoupling event (trailer swapped out, see <see cref="CombinationModel.SetTrailer"/>).</summary>
        public void ResetState()
        {
            Coupled = false;
            ForceOnTrailer = Vec3.Zero; TorqueOnTrailer = Vec3.Zero; KingpinLoadLocal = Vec3.Zero; KingpinWorld = Vec3.Zero;
            Articulation = 0; PitchAngle = 0; RollAngle = 0; PositionError = 0;
            GuideForce = 0; OpenJawOffset = Vec3.Zero;
            SinceCoupled = 100;
        }

        public void Release()
        {
            if (Coupled) UncouplingEvents++;
            Coupled = false;
            ForceOnTrailer = Vec3.Zero; TorqueOnTrailer = Vec3.Zero; KingpinLoadLocal = Vec3.Zero;
        }

        /// <summary>
        /// Solves the coupling for one step. fA/tA and fB/tB: total model forces and torques (about each CoM) for this
        /// step, excluding gravity and the coupling itself. gravity: the host's gravity vector.
        /// </summary>
        public void Solve(double dt, in ChassisState a, in MassProperties ma, Vec3 anchorA, Vec3 fA, Vec3 tA,
            in ChassisState b, in MassProperties mb, Vec3 anchorB, Vec3 fB, Vec3 tB, Vec3 gravity)
        {
            Vec3 pA = a.LocalToWorld(anchorA), pB = b.LocalToWorld(anchorB);
            KingpinWorld = pB;
            Vec3 upA = a.Rotation * Vec3.Up, rightA = a.Rotation * Vec3.Right, fwdA = a.Rotation * Vec3.Forward;
            Vec3 upB = b.Rotation * Vec3.Up, rightB = b.Rotation * Vec3.Right, fwdB = b.Rotation * Vec3.Forward;
            Articulation = Math.Atan2(Vec3.Dot(fwdA, rightB), Vec3.Dot(fwdA, fwdB));
            PitchAngle = Math.Asin(MathUtil.Clamp(Vec3.Dot(upB, fwdA), -1, 1));
            RollAngle = Math.Asin(MathUtil.Clamp(Vec3.Dot(upB, rightA), -1, 1));
            Vec3 cErr = pB - pA;
            PositionError = cErr.Magnitude;
            if (!Coupled)
            {
                ForceOnTrailer = Vec3.Zero; TorqueOnTrailer = Vec3.Zero; KingpinLoadLocal = Vec3.Zero;
                return;
            }

            SinceCoupled += dt;
            Body A = Predict(a, ma, fA, tA, gravity, dt, pA);
            Body B = Predict(b, mb, fB, tB, gravity, dt, pB);

            // Point constraint effective mass K = (1/mA + 1/mB) I - [rA] IA^-1 [rA] - [rB] IB^-1 [rB].
            Mat3 K = Mat3.Diagonal(A.InvMass + B.InvMass, A.InvMass + B.InvMass, A.InvMass + B.InvMass);
            K = Sub(K, SkewISkew(A.R, A.InvI));
            K = Sub(K, SkewISkew(B.R, B.InvI));
            // Engagement phase after the jaw locks: the kingpin point acts as a stiff spring-damper (jaw / kingpin
            // play and buffers) instead of a rigid joint, so a coupling impact is spread over ~0.1-0.2 s.
            double gammaP = 0, betaP = Def.positionCorrection;
            if (SinceCoupled < Def.engageTime)
            {
                double mEff = 3.0 / (K.m00 + K.m11 + K.m22);
                double w = 2 * Math.PI * Def.engageFrequencyHz;
                double k = mEff * w * w, c = 2 * mEff * w;
                gammaP = 1.0 / (dt * (c + dt * k));
                betaP = dt * k / (c + dt * k);
                K.m00 += gammaP; K.m11 += gammaP; K.m22 += gammaP;
            }
            Mat3 Kinv = K.Inverse();
            Vec3 bias = cErr * (betaP / dt);
            double bm = bias.Magnitude;
            if (gammaP == 0 && bm > Def.maxCorrectionSpeed) bias = bias * (Def.maxCorrectionSpeed / bm);

            // Angular rows: constraint value C and Jacobian axis n with dC/dt = n . (wB - wA).
            Vec3 nRoll = Vec3.Cross(upB, rightA);
            double cRoll = Vec3.Dot(upB, rightA);
            Vec3 nPitch = Vec3.Cross(upB, fwdA);
            double cPitch = Vec3.Dot(upB, fwdA);
            Vec3 nYaw = -upB; // d(articulation)/dt = (wA - wB) . upB
            double mRoll = 1.0 / Math.Max(1e-12, Quad(nRoll, A.InvI) + Quad(nRoll, B.InvI));
            double mPitch = 1.0 / Math.Max(1e-12, Quad(nPitch, A.InvI) + Quad(nPitch, B.InvI));
            double mYaw = 1.0 / Math.Max(1e-12, Quad(nYaw, A.InvI) + Quad(nYaw, B.InvI));

            // Soft roll spring (Catto's soft constraint): gamma, beta from stiffness and damping.
            double kR = Def.rollStiffness, cR = Def.rollDamping;
            double gammaR = 1.0 / (dt * (cR + dt * kR));
            double betaR = dt * kR / (cR + dt * kR);
            double mRollSoft = 1.0 / (1.0 / mRoll + gammaR);

            double sinRollLim = Math.Sin(Def.rollLimitDeg * MathUtil.Deg2Rad);
            double sinPitchLim = Math.Sin(Def.pitchLimitDeg * MathUtil.Deg2Rad);
            double yawLim = Def.yawLimitDeg * MathUtil.Deg2Rad;
            double prevVertical = Math.Max(0, KingpinLoadLocal.y);
            double frictionCap = Def.plateFrictionCoeff * prevVertical * Def.plateFrictionRadius * dt;
            // Creep: damper c = break-away torque / creep rate, as a soft constraint (gamma = 1 / (dt c), no spring).
            double creep = Def.plateFrictionCreepRateDegS * MathUtil.Deg2Rad;
            double gammaF = 0, mFricSoft = 0;
            if (creep > 0 && frictionCap > 0)
            {
                double cF = (frictionCap / dt) / creep;
                gammaF = 1.0 / (dt * cF);
                mFricSoft = 1.0 / (1.0 / mYaw + gammaF);
            }

            Vec3 P = Vec3.Zero;
            double accRoll = 0, accRollLim = 0, accPitch = 0, accYaw = 0, accFric = 0;
            Vec3 angImpulse = Vec3.Zero;
            for (int it = 0; it < Math.Max(1, Def.iterations); it++)
            {
                // Kingpin point.
                Vec3 cdot = (B.V + Vec3.Cross(B.W, B.R)) - (A.V + Vec3.Cross(A.W, A.R));
                Vec3 lam = Kinv * (-(cdot + bias + P * gammaP));
                ApplyLinear(ref A, ref B, lam);
                P += lam;

                // Roll spring.
                double rdot = Vec3.Dot(nRoll, B.W - A.W);
                double lr = -mRollSoft * (rdot + betaR * cRoll / dt + gammaR * accRoll);
                accRoll += lr;
                ApplyAngular(ref A, ref B, nRoll, lr); angImpulse += nRoll * lr;

                // Hard limits.
                Limit(ref A, ref B, nRoll, cRoll, sinRollLim, mRoll, Def.stopFrequencyHz, 0.7, dt, ref accRollLim, ref angImpulse);
                Limit(ref A, ref B, nPitch, cPitch, sinPitchLim, mPitch, Def.stopFrequencyHz, 0.7, dt, ref accPitch, ref angImpulse);
                Limit(ref A, ref B, nYaw, Articulation, yawLim, mYaw, Def.yawStopFrequencyHz, 1.0, dt, ref accYaw, ref angImpulse);

                // Plate friction about the kingpin axis.
                if (frictionCap > 0)
                {
                    double ydot = Vec3.Dot(nYaw, B.W - A.W);
                    // ADR 0151: below the break-away torque the plate creeps (viscous, slip rate proportional to torque, the
                    // full cap at plateFrictionCreepRateDegS) instead of sticking: an ideal stick held a released
                    // combination at a fixed articulation and a steady yaw rate with straight wheels. 0 = ideal Coulomb.
                    double lf = gammaF > 0 ? -mFricSoft * (ydot + gammaF * accFric) : -mYaw * ydot;
                    double nacc = MathUtil.Clamp(accFric + lf, -frictionCap, frictionCap);
                    lf = nacc - accFric; accFric = nacc;
                    ApplyAngular(ref A, ref B, nYaw, lf); angImpulse += nYaw * lf;
                }
            }

            ForceOnTrailer = P / dt;
            TorqueOnTrailer = angImpulse / dt;
            Vec3 onTractor = -ForceOnTrailer;
            KingpinLoadLocal = new Vec3(Vec3.Dot(onTractor, rightA), -Vec3.Dot(onTractor, upA), Vec3.Dot(onTractor, fwdA));
        }

        static Body Predict(in ChassisState s, in MassProperties m, Vec3 f, Vec3 t, Vec3 g, double dt, Vec3 anchorWorld)
        {
            Mat3 iw = Mat3.Rotate(m.Inertia, s.Rotation);
            Mat3 iwInv = iw.Inverse();
            Vec3 w = s.AngularVelocity;
            var b = new Body
            {
                InvMass = 1.0 / m.Mass,
                InvI = iwInv,
                V = s.LinearVelocity + (f / m.Mass + g) * dt,
                W = w + iwInv * (t - Vec3.Cross(w, iw * w)) * dt,
                R = anchorWorld - s.CenterOfMassWorld,
            };
            return b;
        }

        static void ApplyLinear(ref Body A, ref Body B, Vec3 lam)
        {
            B.V += lam * B.InvMass;
            B.W += B.InvI * Vec3.Cross(B.R, lam);
            A.V -= lam * A.InvMass;
            A.W -= A.InvI * Vec3.Cross(A.R, lam);
        }

        static void ApplyAngular(ref Body A, ref Body B, Vec3 n, double lam)
        {
            B.W += B.InvI * (n * lam);
            A.W -= A.InvI * (n * lam);
        }

        /// <summary>
        /// One-sided soft stop keeping C inside [-limit, limit]: an implicit spring-damper (frequency f, damping
        /// ratio zeta relative to the row's effective mass) that only pushes, so contact with the stop is spread
        /// over a few steps instead of a single-step impulse (deformable cab / plate contact).
        /// </summary>
        static void Limit(ref Body A, ref Body B, Vec3 n, double c, double limit, double m, double f, double zeta, double dt, ref double acc, ref Vec3 angImpulse)
        {
            double err;
            if (c > limit) err = c - limit;
            else if (c < -limit) err = c + limit;
            else return;
            double w = 2 * Math.PI * f;
            double k = m * w * w, cd = 2 * m * zeta * w;
            double gamma = 1.0 / (dt * (cd + dt * k));
            double beta = dt * k / (cd + dt * k);
            double ms = 1.0 / (1.0 / m + gamma);
            double cdot = Vec3.Dot(n, B.W - A.W);
            double l = -ms * (cdot + beta * err / dt + gamma * acc);
            double nacc = err > 0 ? Math.Min(acc + l, 0) : Math.Max(acc + l, 0);
            double d = nacc - acc;
            acc = nacc;
            ApplyAngular(ref A, ref B, n, d);
            angImpulse += n * d;
        }

        static double Quad(Vec3 n, Mat3 m) => Vec3.Dot(n, m * n);

        static Mat3 Sub(Mat3 a, Mat3 b)
        {
            Mat3 r;
            r.m00 = a.m00 - b.m00; r.m01 = a.m01 - b.m01; r.m02 = a.m02 - b.m02;
            r.m10 = a.m10 - b.m10; r.m11 = a.m11 - b.m11; r.m12 = a.m12 - b.m12;
            r.m20 = a.m20 - b.m20; r.m21 = a.m21 - b.m21; r.m22 = a.m22 - b.m22;
            return r;
        }

        /// <summary>[r] M [r] for the skew-symmetric cross-product matrix [r].</summary>
        static Mat3 SkewISkew(Vec3 r, Mat3 m)
        {
            Mat3 s;
            s.m00 = 0; s.m01 = -r.z; s.m02 = r.y;
            s.m10 = r.z; s.m11 = 0; s.m12 = -r.x;
            s.m20 = -r.y; s.m21 = r.x; s.m22 = 0;
            return Mat3.Mul(Mat3.Mul(s, m), s);
        }
    }
}
