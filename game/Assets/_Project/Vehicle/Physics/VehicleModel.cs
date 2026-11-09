using System;
using System.Collections.Generic;

namespace Game.Vehicle.Physics
{
    /// <summary>Solver settings (not vehicle data).</summary>
    [Serializable]
    public class SolverSettings
    {
        /// <summary>Wheel / driveline substeps per fixed step.</summary>
        public int substeps = 4;
        /// <summary>Contact rays per wheel, spread over +/- contactArcDeg in the wheel plane.</summary>
        public int contactRays = 15;
        public double contactArcDeg = 63;
        /// <summary>Projected Gauss-Seidel iterations for clutch + brake constraints.</summary>
        public int constraintIterations = 4;
    }

    /// <summary>
    /// Stage 1 vehicle solver for a rigid tractor (no trailer). Pure C#, no UnityEngine.
    ///
    /// Per fixed step: reads a <see cref="ChassisState"/>, queries the ground through <see cref="IGroundQuery"/>,
    /// and produces forces at world points (<see cref="Forces"/>) plus their resultant about the CoM.
    /// It does NOT integrate the chassis and does NOT add gravity: that is the job of the rigid-body host
    /// (PhysX Rigidbody in Unity, RigidBody6Dof in the .NET runner).
    /// Zero allocations after construction.
    /// </summary>
    public sealed class VehicleModel
    {
        public readonly VehicleDefinition Def;
        public readonly SolverSettings Settings;
        public readonly MassProperties MassProps;
        public readonly WheelState[] Wheels;
        public readonly Engine Engine;
        public readonly AmtController Amt;
        public readonly Steering Steering;
        public readonly CabSuspension Cab;

        public readonly AppliedForce[] Forces;
        public int ForceCount { get; private set; }
        public Vec3 TotalForce { get; private set; }
        public Vec3 TotalTorque { get; private set; }

        // Telemetry-friendly state
        public double Time { get; private set; }
        public double SpeedForward { get; private set; }   // m/s along chassis forward
        public Vec3 LocalAcceleration { get; private set; } // m/s^2, vehicle frame (kinematic)
        public double YawRate { get; private set; }        // rad/s about chassis up
        public double GradeSin { get; private set; }
        public double ThrottleDemand { get; private set; } // after limiter / AMT scaling
        public double EngineTorque { get; private set; }    // N m net (averaged)
        public double ClutchTorque { get; private set; }    // N m transmitted (averaged)
        public double BrakeDemand { get; private set; }
        public double ParkingBrakeState { get; private set; }
        public bool HillHoldActive { get; private set; }
        public double AligningTorqueTotal { get; private set; }

        readonly int[] _driven;
        readonly double[] _rayCos, _raySin;
        readonly double _wheelRadiusRef;
        double _invDrivenInertiaSum;
        Vec3 _prevVelocityLocal;
        bool _hasPrevVelocity;
        bool _hsaArmed;
        double _hsaTimer;
        double _parking;

        public VehicleModel(VehicleDefinition def, EngineDefinition engine, GearboxDefinition gearbox,
            IDictionary<string, TireDefinition> tires, SolverSettings settings = null)
        {
            def.Validate();
            Def = def;
            Settings = settings ?? new SolverSettings();
            if (Settings.substeps < 1) Settings.substeps = 1;
            if (Settings.contactRays < 1) Settings.contactRays = 1;
            MassProps = MassProperties.Compute(def.massElements);
            Engine = new Engine(engine);
            Amt = new AmtController(gearbox, def.driveline.finalDriveRatio);
            Steering = new Steering(def.steering);
            Cab = new CabSuspension(def.cab);

            // Reference (non-steered) axle line for Ackermann: mean of non-steered axles.
            double refZ = 0; int nRef = 0;
            foreach (var a in def.axles) if (!a.steered) { refZ += a.positionZ; nRef++; }
            refZ = nRef > 0 ? refZ / nRef : def.axles[def.axles.Length - 1].positionZ;

            // Static axle loads (2-axle statically determinate split; Stage 1 is a 2-axle tractor).
            if (def.axles.Length != 2) throw new NotSupportedException("Stage 1 solver supports exactly 2 axles");
            double z0 = def.axles[0].positionZ, z1 = def.axles[1].positionZ;
            double w = MassProps.Mass * 9.81;
            double load0 = w * (MassProps.CenterOfMass.z - z1) / (z0 - z1);
            double[] axleLoad = { load0, w - load0 };

            var wheels = new List<WheelState>();
            var driven = new List<int>();
            var tireModels = new Dictionary<string, TireModel>();
            for (int ai = 0; ai < def.axles.Length; ai++)
            {
                var a = def.axles[ai];
                if (!tires.TryGetValue(a.tireId, out var tdef)) throw new FormatException($"Tire '{a.tireId}' not found");
                if (!tireModels.TryGetValue(a.tireId, out var tm)) { tm = new TireModel(tdef); tireModels[a.tireId] = tm; }
                for (int side = -1; side <= 1; side += 2)
                {
                    double x = side * a.trackWidth * 0.5;
                    // Lateral split of axle load by CoM x offset.
                    double frac = 0.5 + side * MassProps.CenterOfMass.x / a.trackWidth;
                    var ws = new WheelState
                    {
                        Name = a.name + (side < 0 ? "_L" : "_R"),
                        AxleIndex = ai,
                        Side = side,
                        Axle = a,
                        Tire = tm,
                        TireCount = a.tiresPerSide,
                        Steered = a.steered,
                        Driven = a.driven,
                        Radius = tdef.radius,
                        Inertia = tdef.wheelInertia * a.tiresPerSide,
                        StaticLoad = axleLoad[ai] * frac,
                        WheelbaseFromRef = a.positionZ - refZ,
                    };
                    var su = a.suspension;
                    ws.SStatic = su.staticPositionFraction * su.travel;
                    ws.SpringFree = ws.SStatic + ws.StaticLoad / su.springRate;
                    // Hardpoint placed so that, with the static tire deflection, the wheel sits at
                    // mid design travel and the vehicle origin is on the ground (design ride height).
                    double tireDeflStatic = ws.StaticLoad / (tdef.radialStiffness * a.tiresPerSide);
                    ws.HardpointLocal = new Vec3(x, tdef.radius + ws.SStatic - tireDeflStatic, a.positionZ);
                    ws.S = ws.SStatic;
                    if (a.driven) driven.Add(wheels.Count);
                    wheels.Add(ws);
                }
            }
            Wheels = wheels.ToArray();
            _driven = driven.ToArray();
            _invDrivenInertiaSum = 0;
            foreach (int i in _driven) _invDrivenInertiaSum += 1.0 / Wheels[i].Inertia;
            _wheelRadiusRef = Wheels[_driven[0]].Radius;

            int n = Settings.contactRays;
            _rayCos = new double[n];
            _raySin = new double[n];
            double arc = Settings.contactArcDeg * MathUtil.Deg2Rad;
            for (int i = 0; i < n; i++)
            {
                double th = n == 1 ? 0 : -arc + 2 * arc * i / (n - 1);
                _rayCos[i] = Math.Cos(th);
                _raySin[i] = Math.Sin(th);
            }
            Forces = new AppliedForce[Wheels.Length + 1];
        }

        /// <summary>Static wheel load sum check / helper.</summary>
        public double TotalStaticLoad
        {
            get { double s = 0; foreach (var w in Wheels) s += w.StaticLoad; return s; }
        }

        /// <summary>Initialise wheel speeds and drivetrain for a vehicle already moving at `speed` m/s.</summary>
        public void InitializeMoving(double speed, int gear)
        {
            foreach (var w in Wheels) { w.Omega = speed / w.Radius; w.Ux = 0; w.Uy = 0; }
            if (gear == 0 && speed > 0.5)
            {
                // Auto: pick the gear an AMT would hold at this speed (lowest engine speed above ~1000 rpm).
                gear = Amt.BestGearForSpeed(speed / _wheelRadiusRef, Amt.Def.downshiftRpmLight + 150);
                if (gear == 0) gear = 1;
            }
            Amt.ForceState(gear, gear != 0);
            if (gear != 0)
            {
                double eo = Math.Abs(Amt.TotalRatio * speed / _wheelRadiusRef);
                Engine.Omega = Math.Max(Engine.IdleOmega, eo);
            }
        }

        /// <summary>Advance the vehicle model by one fixed step.</summary>
        public void Step(double dt, in ChassisState chassis, in DriverInput input, IGroundQuery ground)
        {
            Time += dt;
            Vec3 up = chassis.Rotation * Vec3.Up;
            Vec3 fwdChassis = chassis.Rotation * Vec3.Forward;
            Vec3 vLocal = chassis.Rotation.InverseRotate(chassis.LinearVelocity);
            SpeedForward = vLocal.z;
            YawRate = Vec3.Dot(chassis.AngularVelocity, up);
            GradeSin = fwdChassis.y;
            if (_hasPrevVelocity) LocalAcceleration = (vLocal - _prevVelocityLocal) / dt;
            _prevVelocityLocal = vLocal;
            _hasPrevVelocity = true;

            Steering.Update(input.Steer, dt);

            // ---------------- contacts & suspension ----------------
            for (int i = 0; i < Wheels.Length; i++) UpdateContact(Wheels[i], dt, chassis, up, ground);
            ApplyAntiRoll();
            for (int i = 0; i < Wheels.Length; i++) FinalizeContact(Wheels[i], chassis, up);

            // ---------------- brakes (pressure dynamics, ABS, hill hold, spring brake) ----------------
            UpdateBrakes(dt, input);

            // ---------------- AMT ----------------
            double drivelineOmega = 0;
            foreach (int i in _driven) drivelineOmega += Wheels[i].Omega;
            drivelineOmega /= _driven.Length;

            // Speed limiter (acts on fuelling only, cannot brake).
            double vKmh = SpeedForward * 3.6;
            double limiter = MathUtil.Clamp01((Def.driveline.speedLimiterKmh - Math.Abs(vKmh)) / Def.driveline.speedLimiterBand);
            // Traction control (ASR, engine intervention only): cut fuelling while a driven wheel spins.
            UpdateAsr(dt);
            double pedal = Math.Min(MathUtil.Clamp01(input.Throttle), limiter) * AsrFactor;
            DriverInput amtInput = input;
            amtInput.Throttle = pedal;
            bool abs = false;
            for (int i = 0; i < Wheels.Length; i++) if (Wheels[i].AbsFactor < 0.999) abs = true;
            Amt.AbsActive = abs;
            Amt.Update(dt, amtInput, SpeedForward, drivelineOmega, Engine, MassProps.Mass, GradeSin, _wheelRadiusRef);
            if (Engine.Stalled && Amt.ClutchCommand <= 0.01) Engine.Restart();
            double demand = pedal * Amt.TorqueScale;
            ThrottleDemand = demand;

            // ---------------- substeps: tires, wheels, engine, clutch ----------------
            int ns = Settings.substeps;
            double h = dt / ns;
            double ratio = Amt.TotalRatio;
            double eta = Amt.Efficiency * Def.driveline.finalDriveEfficiency;
            double clutchCap = Amt.ClutchCommand * Amt.Def.clutchMaxTorque;
            double invIe = 1.0 / Engine.Inertia;
            double engTorqueAcc = 0, clutchAcc = 0;
            for (int i = 0; i < Wheels.Length; i++) { Wheels[i].Fx = 0; Wheels[i].Fy = 0; Wheels[i].DriveTorque = 0; }
            // Scratch accumulators live in WheelState (no allocation).
            for (int sub = 0; sub < ns; sub++)
            {
                for (int i = 0; i < Wheels.Length; i++)
                {
                    var w = Wheels[i];
                    TireSubstep(w, h, out double fx, out double fy);
                    w.Fx += fx; w.Fy += fy;
                    w.Omega += h * (-fx * w.Radius) / w.Inertia;
                }
                double te = Engine.ComputeTorque(demand, Amt.EngineTargetOmega, h);
                Engine.Omega += h * te * invIe;
                engTorqueAcc += te;

                // Projected Gauss-Seidel on clutch (Coulomb, capacity) and brakes (Coulomb, capacity).
                double lamClutch = 0;
                double capC = clutchCap * h;
                bool coupled = ratio != 0 && capC > 0;
                double effC = coupled ? invIe + ratio * ratio * eta / (_driven.Length * (double)_driven.Length) * _invDrivenInertiaSum : 1;
                for (int i = 0; i < Wheels.Length; i++) Wheels[i].BrakeImpulseAcc = 0;
                for (int it = 0; it < Settings.constraintIterations; it++)
                {
                    if (coupled)
                    {
                        double avg = 0;
                        foreach (int d in _driven) avg += Wheels[d].Omega;
                        avg /= _driven.Length;
                        double slip = Engine.Omega - ratio * avg;
                        double dl = slip / effC;
                        double newLam = MathUtil.Clamp(lamClutch + dl, -capC, capC);
                        dl = newLam - lamClutch;
                        lamClutch = newLam;
                        Engine.Omega -= dl * invIe;
                        double perWheel = dl * ratio * eta / _driven.Length;
                        foreach (int d in _driven) Wheels[d].Omega += perWheel / Wheels[d].Inertia;
                    }
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
                clutchAcc += lamClutch / h;
                if (coupled)
                {
                    double perWheelTorque = lamClutch / h * ratio * eta / _driven.Length;
                    foreach (int d in _driven) Wheels[d].DriveTorque += perWheelTorque;
                }
                Engine.CheckStall();
            }

            EngineTorque = engTorqueAcc / ns;
            ClutchTorque = clutchAcc / ns;

            // ---------------- assemble forces ----------------
            ForceCount = 0;
            Vec3 totalF = Vec3.Zero, totalT = Vec3.Zero;
            double mzTotal = 0;
            for (int i = 0; i < Wheels.Length; i++)
            {
                var w = Wheels[i];
                w.Fx /= ns; w.Fy /= ns; w.DriveTorque /= ns;
                if (!w.Contact) continue;
                Vec3 f = w.Normal * w.Fz + w.Forward * w.Fx + w.Lateral * w.Fy;
                Forces[ForceCount].Force = f;
                Forces[ForceCount].Point = w.ContactPoint;
                ForceCount++;
                totalF += f;
                totalT += Vec3.Cross(w.ContactPoint - chassis.CenterOfMassWorld, f);
                // Aligning torque estimate: trail shrinks to 0 at peak slip.
                double apk = w.Tire.PeakTanAlpha(Math.Max(w.Mu, 0.05), Math.Max(w.Fz, 1) / w.TireCount);
                double trail = w.Tire.Def.pneumaticTrail0 * MathUtil.Clamp01(1 - Math.Abs(Math.Tan(w.SlipAngle)) / apk);
                w.AligningTorque = -trail * w.Fy;
                if (w.Steered) mzTotal += w.AligningTorque;
            }
            AligningTorqueTotal = mzTotal;

            // Aerodynamic drag (still air).
            Vec3 v = chassis.LinearVelocity;
            double speed = v.Magnitude;
            if (speed > 1e-3)
            {
                Vec3 fa = v * (-0.5 * Def.aero.airDensity * Def.aero.dragArea * speed);
                Vec3 pa = chassis.LocalToWorld(Def.aero.center);
                Forces[ForceCount].Force = fa;
                Forces[ForceCount].Point = pa;
                ForceCount++;
                totalF += fa;
                totalT += Vec3.Cross(pa - chassis.CenterOfMassWorld, fa);
            }
            TotalForce = totalF;
            TotalTorque = totalT;

            Cab.Update(LocalAcceleration, dt);
        }

        // ------------------------------------------------------------------------------------------

        void UpdateContact(WheelState w, double dt, in ChassisState c, Vec3 up, IGroundQuery ground)
        {
            var su = w.Axle.suspension;
            w.SteerAngle = w.Steered ? Steering.WheelAngle(w.HardpointLocal.x, w.WheelbaseFromRef) : 0;
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
                // Deflection relaxes when airborne.
                w.Ux *= 0.5; w.Uy *= 0.5;
                w.Compression = w.SStatic - w.S;
                return;
            }

            w.Contact = true;
            w.S = bestS;
            Vec3 center = hp + down * bestS;
            Vec3 normal = bestNormal;
            if (bestIdx != mid || n == 1)
            {
                // Edge / off-centre contact: force acts through the wheel centre.
                Vec3 nc = (center - bestPoint).Normalized;
                if (n > 1 && bestIdx != mid) normal = nc;
            }
            w.ContactPoint = bestPoint;
            w.Normal = normal;
            w.FrictionScale = friction; w.RollingResistanceScale = rrScale; w.SurfaceId = surface;

            // Tire radial compliance in series with the suspension: solve F = f_susp(s_geo + F/k_tire)
            // with Newton (monotonic, converges in a few iterations). Softens curb / bump-stop impacts.
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

        /// <summary>Spring (linear + cubic progression) + bump stop force at centre drop s.</summary>
        static double SpringForce(SuspensionDefinition su, WheelState w, double s)
        {
            double x = w.SStatic - s;
            double f = su.springRate * (w.SpringFree - s) + su.progressiveRate * x * x * x;
            if (s < su.bumpStopClearance)
            {
                double b = su.bumpStopClearance - s;
                f += su.bumpStopRate * b * b;
            }
            return f;
        }

        /// <summary>-dF/ds (positive stiffness) of SpringForce.</summary>
        static double SpringStiffness(SuspensionDefinition su, WheelState w, double s)
        {
            double x = w.SStatic - s;
            double k = su.springRate + 3 * su.progressiveRate * x * x;
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
            for (int ai = 0; ai < Def.axles.Length; ai++)
            {
                var a = Def.axles[ai];
                if (a.suspension.antiRollStiffness <= 0) continue;
                WheelState l = null, r = null;
                foreach (var w in Wheels) if (w.AxleIndex == ai) { if (w.Side < 0) l = w; else r = w; }
                if (l == null || r == null || !l.Contact || !r.Contact) continue;
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

        void TireSubstep(WheelState w, double h, out double fx, out double fy)
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
            double uxOld = w.Ux, uyOld = w.Uy;
            double ux = (uxOld - h * vsx) / (1 + h * vref / sx);
            double uy = (uyOld - h * w.Vy) / (1 + h * vref / sy);

            double mu = w.Tire.PeakMu(w.Fz / w.TireCount, w.FrictionScale);
            double uxMax = sx * 1.0;
            double uyMax = sy * Math.Max(1.0, 4 * w.Tire.PeakTanAlpha(mu, w.Fz / w.TireCount));
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
            // Friction limit.
            double lim = mu * w.Fz;
            double mag = Math.Sqrt(fx * fx + fy * fy);
            if (mag > lim && mag > 0) { double s = lim / mag; fx *= s; fy *= s; }
        }

        /// <summary>ASR engine intervention factor 0..1 (1 = no intervention).</summary>
        public double AsrFactor { get; private set; } = 1;

        void UpdateAsr(double dt)
        {
            var bd = Def.brakes;
            if (!bd.asrEnabled) { AsrFactor = 1; return; }
            double maxSlip = 0;
            foreach (int i in _driven)
            {
                var w = Wheels[i];
                if (!w.Contact) continue;
                // Drive slip in the direction of wheel rotation.
                double slip = w.KinematicSlip * Math.Sign(w.Omega);
                if (slip > maxSlip) maxSlip = slip;
            }
            if (maxSlip > bd.asrSlipThreshold) AsrFactor -= bd.asrReduceRate * dt;
            else AsrFactor += bd.asrRecoverRate * dt;
            AsrFactor = MathUtil.Clamp(AsrFactor, 0.2, 1.0);
        }

        void UpdateBrakes(double dt, in DriverInput input)
        {
            var bd = Def.brakes;
            double demand = MathUtil.Clamp01(input.Brake);

            // Hill start aid: hold pressure after brake release at standstill until drive torque builds up.
            bool stopped = Math.Abs(SpeedForward) < 0.3;
            if (bd.hillStartAid && input.Selector != GearSelector.Neutral)
            {
                if (stopped && demand > 0.1 && Math.Abs(GradeSin) > 0.02) { _hsaArmed = true; _hsaTimer = 0; }
                if (_hsaArmed && demand < 0.05)
                {
                    _hsaTimer += dt;
                    double need = MassProps.Mass * 9.81 * Math.Abs(GradeSin) * _wheelRadiusRef;
                    double have = Math.Abs(ClutchTorque * Amt.TotalRatio * Amt.Efficiency * Def.driveline.finalDriveEfficiency);
                    bool release = (have >= need * 1.05 && input.Throttle > 0.02) || _hsaTimer > bd.hillStartMaxHold;
                    if (release) _hsaArmed = false;
                    else demand = Math.Max(demand, 0.5);
                }
                if (!stopped && _hsaArmed && demand < 0.05 && _hsaTimer > 0.1 && Math.Abs(SpeedForward) > 1.0) _hsaArmed = false;
            }
            else _hsaArmed = false;
            HillHoldActive = _hsaArmed && MathUtil.Clamp01(input.Brake) < 0.05;
            BrakeDemand = demand;

            _parking = MathUtil.FirstOrder(_parking, input.ParkingBrake ? 1 : 0, bd.parkingTimeConstant, dt);
            ParkingBrakeState = _parking;

            for (int i = 0; i < Wheels.Length; i++)
            {
                var w = Wheels[i];
                double tau = demand > w.BrakePressure ? bd.applyTimeConstant : bd.releaseTimeConstant;
                w.BrakePressure = MathUtil.FirstOrder(w.BrakePressure, demand, tau, dt);

                // ABS on kinematic slip (wheel-speed-sensor style).
                if (bd.absEnabled && w.BrakePressure > 0.02 && Math.Abs(w.Vx) > bd.absMinSpeedMs && w.Contact)
                {
                    double slip = w.KinematicSlip * Math.Sign(w.Vx);
                    if (slip < -bd.absSlipRelease) w.AbsFactor -= bd.absReleaseRate * dt;
                    else if (slip > -bd.absSlipReapply) w.AbsFactor += bd.absApplyRate * dt;
                    w.AbsFactor = MathUtil.Clamp(w.AbsFactor, 0.0, 1.0);
                }
                else w.AbsFactor = 1;

                double service = w.BrakePressure * w.AbsFactor * w.Axle.serviceBrakeTorque;
                double park = _parking * w.Axle.parkingBrakeTorque;
                w.BrakeTorque = Math.Max(service, park); // anti-compounding
            }
        }
    }
}
