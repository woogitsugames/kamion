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
    /// <item>yaw (articulation): free, so jackknife is possible, with greased plate Coulomb friction. The articulation is
    /// limited by the physical contact of the trailer body with the cab / mudguards / frame (<see cref="CouplingContact"/>,
    /// ADR 0228: soft, no-rebound contact rows solved together with the joint rows); the angular yaw stop is only the
    /// fallback for definitions without body boxes.</item>
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
        /// <summary>Elastic energy stored in the coupling at the start of the last solve [J]: roll spring 0.5 kR roll^2 and the compliant stops 0.5 k err^2 (diagnostics / energy balance).</summary>
        public double RollSpringEnergy, StopSpringEnergy;
        /// <summary>Last solve, diagnostics: accumulated angular impulses per row [N m s] and the row axes (dC/dt = n . (wTrailer - wTractor)); KingpinImpulse = ForceOnTrailer dt.</summary>
        public double ImpRoll, ImpRollStop, ImpPitchStop, ImpYawStop, ImpFriction;
        public Vec3 AxisRoll, AxisPitch, AxisYaw;
        public int CouplingEvents, UncouplingEvents;
        /// <summary>Time since the jaw locked [s]; during the engagement phase the kingpin point is compliant.</summary>
        public double SinceCoupled = 100;

        /// <summary>Tractor-trailer body contact (ADR 0228): geometry from the definitions' body boxes, set by <see cref="CombinationModel"/>.</summary>
        public readonly CouplingContact Contact = new CouplingContact();
        /// <summary>Body contact of the last solve: force on the trailer [N, world] (the tractor gets the opposite) and the torque it makes about each CoM [N m, world].</summary>
        public Vec3 ContactForceOnTrailer, ContactTorqueOnTrailer, ContactTorqueOnTractor;
        /// <summary>Contact points with a non-zero normal impulse in the last solve, their deepest penetration [m] and total normal impulse [N s].</summary>
        public int ContactPoints;
        public double ContactPenetration, ContactNormalImpulse;
        /// <summary>Elastic energy in the contact springs at the start of the last solve, sum 0.5 k pen^2 [J] (energy balance).</summary>
        public double ContactSpringEnergy;

        // Contact rows (fixed buffers, no allocation per step).
        readonly Vec3[] _cRA = new Vec3[CouplingContact.MaxPoints], _cRB = new Vec3[CouplingContact.MaxPoints], _cN = new Vec3[CouplingContact.MaxPoints],
            _cT1 = new Vec3[CouplingContact.MaxPoints], _cT2 = new Vec3[CouplingContact.MaxPoints];
        readonly double[] _cMN = new double[CouplingContact.MaxPoints], _cMT1 = new double[CouplingContact.MaxPoints], _cMT2 = new double[CouplingContact.MaxPoints],
            _cSoft = new double[CouplingContact.MaxPoints], _cSc = new double[CouplingContact.MaxPoints], _cRhs = new double[CouplingContact.MaxPoints],
            _cJN = new double[CouplingContact.MaxPoints], _cJT1 = new double[CouplingContact.MaxPoints], _cJT2 = new double[CouplingContact.MaxPoints];

        public FifthWheel(FifthWheelDefinition def) { Def = def; Contact.Margin = def.contactMargin; }

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
            ClearContact();
        }

        void ClearContact()
        {
            ContactForceOnTrailer = Vec3.Zero; ContactTorqueOnTrailer = Vec3.Zero; ContactTorqueOnTractor = Vec3.Zero;
            ContactPoints = 0; ContactPenetration = 0; ContactNormalImpulse = 0; ContactSpringEnergy = 0;
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
            ClearContact();
            bool geometry = Contact.HasGeometry;
            int nc = 0;
            if (geometry)
            {
                Contact.Detect(a, b);
                nc = Contact.Count;
            }
            if (!Coupled)
            {
                ForceOnTrailer = Vec3.Zero; TorqueOnTrailer = Vec3.Zero; KingpinLoadLocal = Vec3.Zero;
                if (nc == 0) return;
                // Uncoupled trailer (on its legs) touched by the tractor: contact rows only.
                Body Au = Predict(a, ma, fA, tA, gravity, dt, pA);
                Body Bu = Predict(b, mb, fB, tB, gravity, dt, pB);
                PrepareContacts(ref Au, ref Bu, a.CenterOfMassWorld, b.CenterOfMassWorld, upA, nc, dt, pB, Vec3.Zero, 0);
                for (int it = 0; it < Math.Max(1, Def.iterations); it++) SolveContacts(ref Au, ref Bu, nc);
                FinishContacts(nc, dt);
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
            if (nc > 0) PrepareContacts(ref A, ref B, a.CenterOfMassWorld, b.CenterOfMassWorld, upA, nc, dt, pB, nYaw, mYaw);

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

            RollSpringEnergy = 0.5 * kR * cRoll * cRoll;
            StopSpringEnergy = StopEnergy(cRoll, sinRollLim, mRoll, Def.stopFrequencyHz) + StopEnergy(cPitch, sinPitchLim, mPitch, Def.stopFrequencyHz)
                + (geometry ? ContactSpringEnergy : StopEnergy(Articulation, yawLim, mYaw, Def.yawStopFrequencyHz));

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
                Limit(ref A, ref B, nRoll, cRoll, sinRollLim, mRoll, Def.stopFrequencyHz, Def.stopDampingRatio, Def.stopRecoveryRateDegS * MathUtil.Deg2Rad, dt, ref accRollLim, ref angImpulse);
                Limit(ref A, ref B, nPitch, cPitch, sinPitchLim, mPitch, Def.stopFrequencyHz, Def.stopDampingRatio, Def.stopRecoveryRateDegS * MathUtil.Deg2Rad, dt, ref accPitch, ref angImpulse);
                // ADR 0228: with body geometry the articulation is limited by the cab / trailer contact rows, not by an angle.
                if (!geometry) Limit(ref A, ref B, nYaw, Articulation, yawLim, mYaw, Def.yawStopFrequencyHz, 1.0, Def.stopRecoveryRateDegS * MathUtil.Deg2Rad, dt, ref accYaw, ref angImpulse);
                if (nc > 0) SolveContacts(ref A, ref B, nc);

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

            if (nc > 0) FinishContacts(nc, dt);
            ImpRoll = accRoll; ImpRollStop = accRollLim; ImpPitchStop = accPitch; ImpYawStop = accYaw; ImpFriction = accFric;
            AxisRoll = nRoll; AxisPitch = nPitch; AxisYaw = nYaw;
            ForceOnTrailer = P / dt;
            TorqueOnTrailer = angImpulse / dt;
            Vec3 onTractor = -ForceOnTrailer;
            KingpinLoadLocal = new Vec3(Vec3.Dot(onTractor, rightA), -Vec3.Dot(onTractor, upA), Vec3.Dot(onTractor, fwdA));
        }

        /// <summary>
        /// Contact rows (ADR 0228): per point a unilateral implicit spring-damper along the normal (soft constraint, Catto GDC 2011,
        /// same form as the chassis-ground contact of ADR 0165) on the two-body effective mass, k = m (2 pi f)^2,
        /// c = 2 zeta m (2 pi f); a point still in the speculative gap may only close it this step. No rebound: the push may never
        /// separate the bodies faster than contactRecoverySpeed (crushing panels, restitution ~0). Coulomb friction (circular cone).
        /// While coupled, the mass that sets the spring is the larger of the free two-body point mass and the articulation inertia
        /// seen at the point (mYaw / arm^2, arm = lever of the normal about the kingpin axis): the kingpin joint makes the
        /// jackknife mode far heavier than the free point mass, and a spring tuned on the free mass alone would be several
        /// times softer than its nominal frequency in that mode.
        /// </summary>
        void PrepareContacts(ref Body A, ref Body B, Vec3 comA, Vec3 comB, Vec3 upA, int nc, double dt, Vec3 kingpin, Vec3 nYaw, double mYaw)
        {
            double omega = 2 * Math.PI * Def.contactFrequencyHz;
            for (int c = 0; c < nc; c++)
            {
                Vec3 p = Contact.Point[c], n = Contact.Normal[c];
                Vec3 rA = p - comA, rB = p - comB;
                Vec3 t1 = Vec3.Cross(upA, n);
                double tl = t1.Magnitude;
                t1 = tl > 1e-9 ? t1 / tl : Vec3.Cross(n, Vec3.Right).Normalized;
                Vec3 t2 = Vec3.Cross(n, t1);
                _cRA[c] = rA; _cRB[c] = rB; _cN[c] = n; _cT1[c] = t1; _cT2[c] = t2;
                double mN = PointMass(A, B, rA, rB, n);
                _cMN[c] = mN; _cMT1[c] = PointMass(A, B, rA, rB, t1); _cMT2[c] = PointMass(A, B, rA, rB, t2);
                double mS = mN;
                if (mYaw > 0)
                {
                    double arm = Math.Abs(Vec3.Dot(Vec3.Cross(p - kingpin, n), nYaw));
                    if (arm > 0.05) mS = Math.Max(mS, mYaw / (arm * arm));
                }
                double k = mS * omega * omega, kc = k * dt + 2 * Def.contactDampingRatio * mS * omega;
                double pen = -Contact.Separation[c];
                _cRhs[c] = pen >= 0 ? pen * k / kc : pen / dt;
                _cSc[c] = 1.0 / (dt * kc);
                _cSoft[c] = 1.0 / (1.0 / mN + _cSc[c]);
                _cJN[c] = 0; _cJT1[c] = 0; _cJT2[c] = 0;
                if (pen > 0) ContactSpringEnergy += 0.5 * k * pen * pen;
                if (pen > ContactPenetration) ContactPenetration = pen;
            }
        }

        void SolveContacts(ref Body A, ref Body B, int nc)
        {
            double recovery = Def.contactRecoverySpeed, mu = Def.contactFriction;
            for (int c = 0; c < nc; c++)
            {
                Vec3 rA = _cRA[c], rB = _cRB[c], n = _cN[c];
                Vec3 vrel = (B.V + Vec3.Cross(B.W, rB)) - (A.V + Vec3.Cross(A.W, rA));
                double vn = Vec3.Dot(vrel, n);
                double dj = _cSoft[c] * (_cRhs[c] - vn - _cSc[c] * _cJN[c]);
                // No rebound: the push may not drive the bodies apart faster than the recovery speed.
                dj = Math.Min(dj, _cMN[c] * (recovery - vn));
                double jn = Math.Max(0, _cJN[c] + dj);
                dj = jn - _cJN[c];
                _cJN[c] = jn;
                if (dj != 0) ApplyPoint(ref A, ref B, rA, rB, n * dj);
                if (mu <= 0) continue;
                vrel = (B.V + Vec3.Cross(B.W, rB)) - (A.V + Vec3.Cross(A.W, rA));
                double a1 = _cJT1[c] - _cMT1[c] * Vec3.Dot(vrel, _cT1[c]);
                double a2 = _cJT2[c] - _cMT2[c] * Vec3.Dot(vrel, _cT2[c]);
                double lim = mu * jn, mag = Math.Sqrt(a1 * a1 + a2 * a2);
                if (mag > lim) { double sc = mag > 1e-12 ? lim / mag : 0; a1 *= sc; a2 *= sc; }
                double d1 = a1 - _cJT1[c], d2 = a2 - _cJT2[c];
                _cJT1[c] = a1; _cJT2[c] = a2;
                if (d1 != 0 || d2 != 0) ApplyPoint(ref A, ref B, rA, rB, _cT1[c] * d1 + _cT2[c] * d2);
            }
        }

        void FinishContacts(int nc, double dt)
        {
            Vec3 f = Vec3.Zero, tB = Vec3.Zero, tA = Vec3.Zero;
            int active = 0; double jSum = 0;
            for (int c = 0; c < nc; c++)
            {
                if (_cJN[c] <= 0) continue;
                active++; jSum += _cJN[c];
                Vec3 j = _cN[c] * _cJN[c] + _cT1[c] * _cJT1[c] + _cT2[c] * _cJT2[c];
                f += j; tB += Vec3.Cross(_cRB[c], j); tA -= Vec3.Cross(_cRA[c], j);
            }
            ContactPoints = active; ContactNormalImpulse = jSum;
            ContactForceOnTrailer = f / dt; ContactTorqueOnTrailer = tB / dt; ContactTorqueOnTractor = tA / dt;
        }

        static double PointMass(in Body A, in Body B, Vec3 rA, Vec3 rB, Vec3 d)
        {
            double k = A.InvMass + B.InvMass + Quad(Vec3.Cross(rA, d), A.InvI) + Quad(Vec3.Cross(rB, d), B.InvI);
            return 1.0 / Math.Max(1e-12, k);
        }

        static void ApplyPoint(ref Body A, ref Body B, Vec3 rA, Vec3 rB, Vec3 j)
        {
            B.V += j * B.InvMass;
            B.W += B.InvI * Vec3.Cross(rB, j);
            A.V -= j * A.InvMass;
            A.W -= A.InvI * Vec3.Cross(rA, j);
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
        /// ADR 0201b (F2): the stop does not rebound. While the row approaches or rests on the stop the impulse is the soft
        /// spring-damper one; it may never drive the rows apart faster than <paramref name="recoveryRate"/> [rad/s]. A Kelvin-Voigt
        /// stop gives part of its stored spring energy back as relative velocity (ζ 0.7: 4.5 kJ of a 58 kJ plate-pitch
        /// impact in the tumbling free fall of F2, energy that KE + PE does not contain); now the stored energy is released
        /// only as a slow recovery of the penetration (stop crush / hysteresis), at most 0.5 m recoveryRate^2 of kinetic energy.
        /// </summary>
        static void Limit(ref Body A, ref Body B, Vec3 n, double c, double limit, double m, double f, double zeta, double recoveryRate, double dt, ref double acc, ref Vec3 angImpulse)
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
            // Rebound cap in "push" coordinates (s = +1 when c > limit): outward rate u = -s cdot, push p = -s acc >= 0.
            double sgn = err > 0 ? 1.0 : -1.0;
            double u = -sgn * cdot;
            double dp = Math.Min(-sgn * l, m * (recoveryRate - u));
            double nacc = err > 0 ? Math.Min(acc - dp, 0) : Math.Max(acc + dp, 0);
            double d = nacc - acc;
            acc = nacc;
            ApplyAngular(ref A, ref B, n, d);
            angImpulse += n * d;
        }

        static double StopEnergy(double c, double limit, double m, double f)
        {
            double err = c > limit ? c - limit : c < -limit ? c + limit : 0;
            double w = 2 * Math.PI * f;
            return 0.5 * m * w * w * err * err;
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

    /// <summary>
    /// Tractor-trailer body contact detection (ADR 0228, B-077): the coupling-flagged body boxes of the tractor (cab, frame,
    /// mudguards; tractor frame) against those of the trailer (body, beams, underrun; trailer frame), from the definitions'
    /// <see cref="BodyBoxDefinition"/> arrays, the same boxes the runner uses for the chassis-ground contact.
    ///
    /// Model: in the tractor frame each pair is a 2D box-box test in the ground plane (separating axes of both footprints,
    /// reference face + clipped incident edge, Box2D b2CollidePolygons style), run at two height slices (bottom and top of the
    /// boxes' common height range, so a trailer leaning on the plate pitch / roll is seen where it actually is), at most
    /// 2 points per slice, plus the vertical overlap of the two boxes at each point measured in the trailer frame. Only side
    /// contacts (horizontal normal: trailer side wall or front corner against the cab) are kept; a point whose vertical
    /// overlap is smaller than its horizontal penetration (boxes meeting top-to-bottom) is dropped. Points closer than
    /// <see cref="Margin"/> are speculative. The fifth wheel solves the points as soft contact rows together with the joint.
    /// No allocations in <see cref="Detect"/> (arrays are sized in <see cref="SetGeometry"/>).
    /// </summary>
    public sealed class CouplingContact
    {
        /// <summary>Points per box pair: 2 height slices x 2 points.</summary>
        public const int PointsPerPair = 4;
        /// <summary>Capacity: 4 tractor x 4 trailer coupling boxes x <see cref="PointsPerPair"/>. <see cref="SetGeometry"/> rejects
        /// geometry that could need more (a DLC trailer with more coupling boxes must raise this, not lose points silently).</summary>
        public const int MaxPoints = 64;
        Vec3[] _aC = new Vec3[0], _aH = new Vec3[0], _bC = new Vec3[0], _bH = new Vec3[0];
        int _na, _nb;

        /// <summary>Contacts of the last <see cref="Detect"/>: world point, unit world normal (direction the trailer is pushed), separation [m] (&lt; 0 = penetration).</summary>
        public readonly Vec3[] Point = new Vec3[MaxPoints];
        public readonly Vec3[] Normal = new Vec3[MaxPoints];
        public readonly double[] Separation = new double[MaxPoints];
        /// <summary>Indices of the touching boxes (into the coupling-flagged boxes, in definition order) — diagnostics.</summary>
        public readonly int[] TractorBox = new int[MaxPoints], TrailerBox = new int[MaxPoints];
        public int Count;
        /// <summary>Speculative margin [m] (FifthWheelDefinition.contactMargin).</summary>
        public double Margin = 0.05;

        public bool HasGeometry => _na > 0 && _nb > 0;
        public int TractorBoxCount => _na;
        public int TrailerBoxCount => _nb;

        /// <summary>Copies the coupling-flagged boxes (null / empty trailer = no contact). Allocates: call on setup / trailer swap only.</summary>
        public void SetGeometry(BodyBoxDefinition[] tractor, BodyBoxDefinition[] trailer)
        {
            int na = CountCoupling(tractor), nb = CountCoupling(trailer);
            if (na * nb * PointsPerPair > MaxPoints)
                throw new FormatException($"CouplingContact: {na} tractor x {nb} trailer coupling boxes need up to {na * nb * PointsPerPair} contact points, capacity {MaxPoints} (ADR 0228): raise CouplingContact.MaxPoints");
            _na = Fill(tractor, ref _aC, ref _aH);
            _nb = Fill(trailer, ref _bC, ref _bH);
            Count = 0;
        }

        /// <summary>Number of coupling-flagged boxes (null = 0).</summary>
        public static int CountCoupling(BodyBoxDefinition[] src)
        {
            int n = 0;
            if (src != null) foreach (var b in src) if (b != null && b.coupling) n++;
            return n;
        }

        static int Fill(BodyBoxDefinition[] src, ref Vec3[] c, ref Vec3[] h)
        {
            int n = CountCoupling(src);
            c = new Vec3[n]; h = new Vec3[n];
            int k = 0;
            if (src != null)
                foreach (var b in src)
                    if (b != null && b.coupling) { c[k] = b.center; h[k] = b.size * 0.5; k++; }
            return n;
        }

        struct Rect { public double cx, cz, e0x, e0z, e1x, e1z, h0, h1; }

        /// <summary>Finds the contact points between tractor <paramref name="a"/> and trailer <paramref name="b"/>.</summary>
        public void Detect(in ChassisState a, in ChassisState b)
        {
            Count = 0;
            if (!HasGeometry) return;
            Quat qa = a.Rotation, qaInv = qa.Conjugate;
            Quat rel = qaInv * b.Rotation, relInv = rel.Conjugate;
            Vec3 t = qaInv * (b.Position - a.Position);
            Vec3 u = rel * Vec3.Right, upR = rel * Vec3.Up;
            double ul = Math.Sqrt(u.x * u.x + u.z * u.z);
            if (ul < 0.5 || upR.y < 0.5) return; // trailer rolled / pitched > 60 deg against the tractor: left to the chassis-ground contact
            double ux = u.x / ul, uz = u.z / ul;
            for (int j = 0; j < _nb; j++)
            {
                Vec3 cB = rel * _bC[j] + t, hB = _bH[j];
                double radB = Math.Sqrt(hB.x * hB.x + hB.z * hB.z);
                for (int i = 0; i < _na; i++)
                {
                    Vec3 cA = _aC[i], hA = _aH[i];
                    var ra = new Rect { cx = cA.x, cz = cA.z, e0x = 1, e0z = 0, e1x = 0, e1z = 1, h0 = hA.x, h1 = hA.z };
                    double dx = cB.x - ra.cx, dz = cB.z - ra.cz, rr = Math.Sqrt(ra.h0 * ra.h0 + ra.h1 * ra.h1) + radB + Margin;
                    if (dx * dx + dz * dz > rr * rr) continue;
                    // Height slices: the common height range of both boxes at the column of the tractor box centre. A pitched /
                    // rolled trailer leans, so its footprint changes with height: the 2D test runs at the bottom and at the top
                    // of the common range (one slice when the range is thin).
                    Vec3 qc = relInv * (cA - t);
                    double yb0 = (rel * new Vec3(qc.x, _bC[j].y - hB.y, qc.z) + t).y, yb1 = (rel * new Vec3(qc.x, _bC[j].y + hB.y, qc.z) + t).y;
                    if (yb0 > yb1) { double tmp = yb0; yb0 = yb1; yb1 = tmp; }
                    double lo = Math.Max(cA.y - hA.y, yb0), hi = Math.Min(cA.y + hA.y, yb1);
                    const double inset = 0.02;
                    int slices = hi - lo > 4 * inset ? 2 : 1;
                    for (int k = 0; k < slices; k++)
                    {
                        double ys = slices == 1 ? 0.5 * (lo + hi) : (k == 0 ? lo + inset : hi - inset);
                        double lam = (ys - cB.y) / upR.y;
                        var rb = new Rect { cx = cB.x + upR.x * lam, cz = cB.z + upR.z * lam, e0x = ux, e0z = uz, e1x = -uz, e1z = ux, h0 = hB.x, h1 = hB.z };
                        Collide(a, qa, rel, relInv, t, i, j, ra, rb, ys);
                        if (Count >= MaxPoints - 1) return;
                    }
                }
            }
        }

        void Collide(in ChassisState a, Quat qa, Quat rel, Quat relInv, Vec3 t, int i, int j, in Rect ra, in Rect rb, double ys)
        {
            double sA = MaxSeparation(ra, rb, out double nAx, out double nAz, out double hNA, out double tAx, out double tAz, out double hTA);
            if (sA > Margin) return;
            double sB = MaxSeparation(rb, ra, out double nBx, out double nBz, out double hNB, out double tBx, out double tBz, out double hTB);
            if (sB > Margin) return;
            bool refB = sB > sA + 1e-3; // prefer the tractor's faces (stable choice when both are equal)
            Rect rf = refB ? rb : ra, inc = refB ? ra : rb;
            double nx = refB ? nBx : nAx, nz = refB ? nBz : nAz, hN = refB ? hNB : hNA;
            double tx = refB ? tBx : tAx, tz = refB ? tBz : tAz, hT = refB ? hTB : hTA;
            IncidentEdge(inc, nx, nz, out double p1x, out double p1z, out double p2x, out double p2z);
            double s1 = tx * (p1x - rf.cx) + tz * (p1z - rf.cz), s2 = tx * (p2x - rf.cx) + tz * (p2z - rf.cz);
            if (!Clip(ref p1x, ref p1z, ref s1, ref p2x, ref p2z, ref s2, -hT, hT)) return;
            AddPoint(a, qa, rel, relInv, t, i, j, rf, refB, nx, nz, hN, p1x, p1z, ys);
            if (Count >= MaxPoints) return;
            AddPoint(a, qa, rel, relInv, t, i, j, rf, refB, nx, nz, hN, p2x, p2z, ys);
        }

        void AddPoint(in ChassisState a, Quat qa, Quat rel, Quat relInv, Vec3 t, int i, int j, in Rect rf, bool refB,
            double nx, double nz, double hN, double px, double pz, double ys)
        {
            double sep = nx * (px - rf.cx) + nz * (pz - rf.cz) - hN;
            if (sep > Margin) return;
            // Vertical overlap of the two boxes at this column, the trailer box measured in its own frame (plate pitch / roll).
            Vec3 cA = _aC[i], hA = _aH[i];
            double ya0 = cA.y - hA.y, ya1 = cA.y + hA.y;
            Vec3 q = relInv * (new Vec3(px, ys, pz) - t);
            double yb0 = (rel * new Vec3(q.x, _bC[j].y - _bH[j].y, q.z) + t).y;
            double yb1 = (rel * new Vec3(q.x, _bC[j].y + _bH[j].y, q.z) + t).y;
            if (yb0 > yb1) { double tmp = yb0; yb0 = yb1; yb1 = tmp; }
            double lo = Math.Max(ya0, yb0), hi = Math.Min(ya1, yb1);
            double vOverlap = hi - lo, hPen = -sep;
            if (sep > 0 && vOverlap < 0) return; // apart both horizontally and vertically
            // Only side contacts (horizontal normal). Where the vertical overlap is smaller than the horizontal penetration the
            // boxes meet top-to-bottom (a rolled / pitched trailer body over a mudguard or the frame end): not modelled
            // (ADR 0228): the graybox body box is full width down to 1.22 m where the real trailer has a narrow gooseneck,
            // and plastic mudguards on brackets do not carry the trailer.
            if (vOverlap <= 0 || vOverlap < hPen) return;
            // The slice must lie in the common height range at this column (a leaning trailer may not reach it here).
            if (ys < lo - 0.05 || ys > hi + 0.05) return;
            int c = Count;
            // Normal pushing the trailer: out of the tractor face (reference A), or into the trailer face (reference B).
            double mx = refB ? -nx : nx, mz = refB ? -nz : nz;
            Point[c] = a.LocalToWorld(new Vec3(px, MathUtil.Clamp(ys, lo, hi), pz));
            Normal[c] = qa * new Vec3(mx, 0, mz);
            Separation[c] = sep;
            TractorBox[c] = i; TrailerBox[c] = j;
            Count = c + 1;
        }

        /// <summary>Largest signed separation of <paramref name="r2"/> from the faces of <paramref name="r1"/> (SAT), with that face's normal, half-depth and tangent.</summary>
        static double MaxSeparation(in Rect r1, in Rect r2, out double nx, out double nz, out double hN, out double tx, out double tz, out double hT)
        {
            nx = 0; nz = 0; hN = 0; tx = 0; tz = 0; hT = 0;
            double best = double.NegativeInfinity;
            for (int k = 0; k < 4; k++)
            {
                double sg = (k & 1) == 0 ? 1 : -1;
                bool ax0 = k < 2;
                double ex = sg * (ax0 ? r1.e0x : r1.e1x), ez = sg * (ax0 ? r1.e0z : r1.e1z);
                double h = ax0 ? r1.h0 : r1.h1;
                double proj = Math.Abs(ex * r2.e0x + ez * r2.e0z) * r2.h0 + Math.Abs(ex * r2.e1x + ez * r2.e1z) * r2.h1;
                double s = ex * (r2.cx - r1.cx) + ez * (r2.cz - r1.cz) - h - proj;
                if (s > best)
                {
                    best = s; nx = ex; nz = ez; hN = h;
                    tx = ax0 ? r1.e1x : r1.e0x; tz = ax0 ? r1.e1z : r1.e0z; hT = ax0 ? r1.h1 : r1.h0;
                }
            }
            return best;
        }

        /// <summary>The face of <paramref name="r"/> most anti-parallel to the reference normal: its two end points.</summary>
        static void IncidentEdge(in Rect r, double nx, double nz, out double p1x, out double p1z, out double p2x, out double p2z)
        {
            double bestDot = double.PositiveInfinity, mx = 0, mz = 0, hm = 0, tmx = 0, tmz = 0, ht = 0;
            for (int k = 0; k < 4; k++)
            {
                double sg = (k & 1) == 0 ? 1 : -1;
                bool ax0 = k < 2;
                double ex = sg * (ax0 ? r.e0x : r.e1x), ez = sg * (ax0 ? r.e0z : r.e1z);
                double d = ex * nx + ez * nz;
                if (d < bestDot)
                {
                    bestDot = d; mx = ex; mz = ez; hm = ax0 ? r.h0 : r.h1;
                    tmx = ax0 ? r.e1x : r.e0x; tmz = ax0 ? r.e1z : r.e0z; ht = ax0 ? r.h1 : r.h0;
                }
            }
            double fx = r.cx + mx * hm, fz = r.cz + mz * hm;
            p1x = fx + tmx * ht; p1z = fz + tmz * ht;
            p2x = fx - tmx * ht; p2z = fz - tmz * ht;
        }

        /// <summary>Clips the segment p1-p2 (tangent coordinates s1, s2) to [lo, hi]; false when it lies outside.</summary>
        static bool Clip(ref double p1x, ref double p1z, ref double s1, ref double p2x, ref double p2z, ref double s2, double lo, double hi)
        {
            if ((s1 < lo && s2 < lo) || (s1 > hi && s2 > hi)) return false;
            if (s1 < lo) { double f = (lo - s1) / (s2 - s1); p1x += (p2x - p1x) * f; p1z += (p2z - p1z) * f; s1 = lo; }
            else if (s2 < lo) { double f = (lo - s2) / (s1 - s2); p2x += (p1x - p2x) * f; p2z += (p1z - p2z) * f; s2 = lo; }
            if (s1 > hi) { double f = (s1 - hi) / (s1 - s2); p1x += (p2x - p1x) * f; p1z += (p2z - p1z) * f; s1 = hi; }
            else if (s2 > hi) { double f = (s2 - hi) / (s2 - s1); p2x += (p1x - p2x) * f; p2z += (p1z - p2z) * f; s2 = hi; }
            return true;
        }

        /// <summary>
        /// Smallest articulation [deg] at which the coupled, level combination (kingpin in the jaw) first touches, sweeping the
        /// trailer yaw both ways (bisection to 0.01 deg). NaN when there is no geometry or no contact up to <paramref name="maxDeg"/>.
        /// Allocates (setup / tests / metrics only).
        /// </summary>
        public static double FirstContactArticulationDeg(VehicleDefinition tractor, TrailerDefinition trailer, double maxDeg = 179)
        {
            var c = new CouplingContact { Margin = 0 };
            c.SetGeometry(tractor.bodyBoxes, trailer.bodyBoxes);
            if (!c.HasGeometry) return double.NaN;
            double best = double.NaN;
            for (int sg = -1; sg <= 1; sg += 2)
            {
                double prev = 0, hit = double.NaN;
                for (double phi = 0.5; phi <= maxDeg; phi += 0.5)
                {
                    if (Touches(c, tractor, trailer, sg * phi)) { hit = phi; break; }
                    prev = phi;
                }
                if (double.IsNaN(hit)) continue;
                double lo = prev, hi = hit;
                for (int it = 0; it < 30; it++)
                {
                    double mid = 0.5 * (lo + hi);
                    if (Touches(c, tractor, trailer, sg * mid)) hi = mid; else lo = mid;
                }
                double art = Math.Abs(ArticulationAt(tractor, trailer, sg * hi));
                if (double.IsNaN(best) || art < best) best = art;
            }
            return best;
        }

        static void Pose(VehicleDefinition tractor, TrailerDefinition trailer, double yawDeg, out ChassisState a, out ChassisState b)
        {
            a = new ChassisState { Rotation = Quat.Identity };
            Quat qb = Quat.AngleAxis(yawDeg * MathUtil.Deg2Rad, Vec3.Up);
            b = new ChassisState { Rotation = qb, Position = tractor.fifthWheel.position - qb * new Vec3(0, trailer.kingpinHeight, 0) };
        }

        static bool Touches(CouplingContact c, VehicleDefinition tractor, TrailerDefinition trailer, double yawDeg)
        {
            Pose(tractor, trailer, yawDeg, out ChassisState a, out ChassisState b);
            c.Detect(a, b);
            for (int k = 0; k < c.Count; k++) if (c.Separation[k] < 0) return true;
            return false;
        }

        static double ArticulationAt(VehicleDefinition tractor, TrailerDefinition trailer, double yawDeg)
        {
            Pose(tractor, trailer, yawDeg, out ChassisState a, out ChassisState b);
            Vec3 fwdA = a.Rotation * Vec3.Forward, fwdB = b.Rotation * Vec3.Forward, rightB = b.Rotation * Vec3.Right;
            return Math.Atan2(Vec3.Dot(fwdA, rightB), Vec3.Dot(fwdA, fwdB)) * MathUtil.Rad2Deg;
        }
    }
}
