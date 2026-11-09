using System;
using System.Collections.Generic;
using System.Diagnostics;
using Game.Vehicle.Physics;

namespace PhysicsRunner.Sim
{
    public sealed class RunOptions
    {
        public double? Dt;
        public int? Substeps;
        public double? HeadingDeg;
        public string CsvPath;
        public string Commit = "unknown";
        public double? Duration;
    }

    public sealed class CheckResult
    {
        public CheckSpec Spec = null!;
        public double Value;
        public bool Passed;
        public override string ToString() =>
            $"{Spec.metric}{(Spec.arg != 0 ? "(" + Spec.arg + ")" : "")} = {Value:G5} [{(Spec.min.HasValue ? Spec.min.Value.ToString("G5") : "-inf")}, {(Spec.max.HasValue ? Spec.max.Value.ToString("G5") : "+inf")}] {(Passed ? "PASS" : "FAIL")}";
    }

    public sealed class RunResult
    {
        public Scenario Scenario = null!;
        public List<Sample> Samples = new List<Sample>();
        public List<CheckResult> Checks = new List<CheckResult>();
        public Vec3 CircleCenter;
        public double CircleRadius;
        public double Dt;
        public double SampleDt;
        public double MeanStepMicros;
        public double StaticKingpinLoad;
        public double TotalMass;
        public int CouplingEvents, UncouplingEvents, ShiftCount, RejectedShifts;
        public bool Passed { get { foreach (var c in Checks) if (!c.Passed) return false; return true; } }
        public double Metric(string name, double arg = 0, double from = 0, double to = 0) => Metrics.Compute(this, name, arg, from, to);
    }

    /// <summary>Everything a driver / metric / telemetry writer needs about the simulated combination.</summary>
    public sealed class SimContext
    {
        public CombinationModel Combo = null!;
        public RigidBody6Dof Body = null!;
        public RigidBody6Dof TrailerBody;
        public AnalyticGround Ground = null!;
        public VehicleModel Tractor => Combo.Tractor;
        public TrailerModel Trailer => Combo.Trailer;
        public IEnumerable<WheelState> AllWheels
        {
            get
            {
                foreach (var w in Combo.Tractor.Wheels) yield return w;
                if (Combo.Trailer != null) foreach (var w in Combo.Trailer.Wheels) yield return w;
            }
        }
    }

    public static class ScenarioRunner
    {
        static DefinitionSet _defs;
        public static DefinitionSet Defs => _defs ??= DefinitionSet.LoadDirectory(RepoPaths.DefinitionsDir);

        public static Quat LookRotation(Vec3 forward, Vec3 up)
        {
            Vec3 f = forward.Normalized;
            Vec3 r = Vec3.Cross(up, f).Normalized;
            Vec3 u = Vec3.Cross(f, r);
            double m00 = r.x, m01 = u.x, m02 = f.x;
            double m10 = r.y, m11 = u.y, m12 = f.y;
            double m20 = r.z, m21 = u.z, m22 = f.z;
            double tr = m00 + m11 + m22;
            Quat q;
            if (tr > 0)
            {
                double s = Math.Sqrt(tr + 1.0) * 2;
                q = new Quat((m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s, 0.25 * s);
            }
            else if (m00 > m11 && m00 > m22)
            {
                double s = Math.Sqrt(1.0 + m00 - m11 - m22) * 2;
                q = new Quat(0.25 * s, (m01 + m10) / s, (m02 + m20) / s, (m21 - m12) / s);
            }
            else if (m11 > m22)
            {
                double s = Math.Sqrt(1.0 + m11 - m00 - m22) * 2;
                q = new Quat((m01 + m10) / s, 0.25 * s, (m12 + m21) / s, (m02 - m20) / s);
            }
            else
            {
                double s = Math.Sqrt(1.0 + m22 - m00 - m11) * 2;
                q = new Quat((m02 + m20) / s, (m12 + m21) / s, 0.25 * s, (m10 - m01) / s);
            }
            return q.Normalized;
        }

        public static AnalyticGround BuildGround(GroundSpec g)
        {
            var boxes = new GroundBox[g.boxes.Length];
            for (int i = 0; i < boxes.Length; i++)
            {
                var b = g.boxes[i];
                boxes[i] = new GroundBox
                {
                    Min = new Vec3(b.minX, -1.0, b.minZ),
                    Max = new Vec3(b.maxX, b.height, b.maxZ),
                    Surface = SurfaceProps.FromName(b.surface),
                };
            }
            if (boxes.Length > 0 && Math.Abs(g.gradePercent) > 1e-9) throw new NotSupportedException("boxes only on flat ground");
            return new AnalyticGround(g.gradePercent, SurfaceProps.FromName(g.surface), boxes);
        }

        /// <summary>Cargo for a configuration preset (laden40 = 40.0 t gross combination mass).</summary>
        public static CargoDefinition CargoFor(Scenario sc, VehicleModel tractor)
        {
            var c = new CargoDefinition();
            var tdef = Defs.Trailers[sc.trailer];
            double empty = MassProperties.Compute(tdef.massElements).Mass;
            switch (sc.combination)
            {
                case "empty": c.massKg = 0; break;
                case "laden40": c.massKg = 40000 - tractor.MassProps.Mass - empty; break;
                case "cargo24": c.massKg = 24000; break;
                default: throw new ArgumentException($"Unknown combination '{sc.combination}'");
            }
            if (sc.cargo.massKg > 0) c.massKg = sc.cargo.massKg;
            c.cogHeight = sc.cargo.cogHeight;
            if (sc.cargo.cogZ.HasValue) { c.cogZ = sc.cargo.cogZ.Value; c.cogZSet = true; }
            c.cogX = sc.cargo.cogX;
            return c;
        }

        /// <summary>Creates the models and bodies placed at static equilibrium on the ground.</summary>
        public static SimContext Setup(Scenario sc, RunOptions opt)
        {
            var settings = new SolverSettings { substeps = opt.Substeps ?? sc.substeps };
            var tractor = Defs.CreateModel(sc.vehicle, settings);
            TrailerModel trailer = null;
            if (sc.HasTrailer) trailer = Defs.CreateTrailer(sc.trailer, CargoFor(sc, tractor), settings);
            bool coupled = sc.overrides.coupled;
            var combo = new CombinationModel(tractor, trailer, trailer != null && coupled);
            tractor.EnduranceBrakesEnabled = sc.overrides.enduranceBrakes;
            tractor.Air.LoadSensingEnabled = sc.overrides.loadSensing;
            if (trailer != null) trailer.Brakes.LoadSensingEnabled = sc.overrides.loadSensing;
            if (sc.overrides.absEnabled.HasValue) tractor.Air.AbsEnabled = sc.overrides.absEnabled.Value;
            if (trailer != null && sc.overrides.trailerAbsEnabled.HasValue) trailer.Brakes.AbsEnabled = sc.overrides.trailerAbsEnabled.Value;
            else if (trailer != null && sc.overrides.absEnabled.HasValue) trailer.Brakes.AbsEnabled = sc.overrides.absEnabled.Value;
            if (sc.overrides.initialAirBar.HasValue)
            {
                tractor.Air.Charge(sc.overrides.initialAirBar.Value);
                if (trailer != null) trailer.Brakes.Reservoir = Math.Min(sc.overrides.initialAirBar.Value, 8.5);
            }

            var ground = BuildGround(sc.ground);
            var ctx = new SimContext { Combo = combo, Ground = ground };
            var body = new RigidBody6Dof(tractor.MassProps);
            double heading = (opt.HeadingDeg ?? sc.initial.headingDeg) * MathUtil.Deg2Rad;
            Vec3 n = ground.PlaneNormal;
            Vec3 hdir = new Vec3(Math.Sin(heading), 0, Math.Cos(heading));
            Vec3 fwd = Vec3.ProjectOnPlane(hdir, n).Normalized;
            Quat qBase = LookRotation(fwd, n);
            double x0 = sc.initial.x, z0 = sc.initial.z;
            Vec3 basePoint = new Vec3(x0, ground.HeightAt(x0, z0), z0);

            // Tractor: both axles' static contact points on the plane.
            var g = tractor.Group;
            double yF = g.StaticGroundOffset(0), yR = g.StaticGroundOffset(1);
            PlaceTwoPoint(qBase, basePoint, n, new Vec3(0, yR, tractor.Def.axles[1].positionZ), 0,
                new Vec3(0, yF, tractor.Def.axles[0].positionZ), 0, out Quat qK, out Vec3 posK);
            body.Rotation = qK; body.Position = posK;
            double v0 = sc.initial.speedKmh / 3.6;
            body.Velocity = fwd * v0;
            ctx.Body = body;

            if (trailer != null)
            {
                var tb = new RigidBody6Dof(trailer.MassProps);
                double yT = 0, zA = 0;
                for (int i = 0; i < trailer.Def.axles.Length; i++) { yT += trailer.Group.StaticGroundOffset(i); zA += trailer.Def.axles[i].positionZ; }
                yT /= trailer.Def.axles.Length; zA /= trailer.Def.axles.Length;
                Vec3 nUp = n;
                Quat qT0 = Quat.AngleAxis(sc.overrides.articulationDeg * MathUtil.Deg2Rad, nUp) * qBase;
                if (coupled)
                {
                    Vec3 k = body.State.LocalToWorld(tractor.Def.fifthWheel.position);
                    Vec3 kpLocal = trailer.KingpinLocal;
                    // Pitch so that the axle group contact is on the plane while the kingpin sits in the jaw.
                    Vec3 rightT = qT0 * Vec3.Right;
                    Func<double, double> f = phi =>
                    {
                        Quat q = Quat.AngleAxis(phi, rightT) * qT0;
                        Vec3 pos = k - q * kpLocal;
                        return Vec3.Dot(pos + q * new Vec3(0, yT, zA), n);
                    };
                    double phiT = Bisect(f, -0.3, 0.3);
                    tb.Rotation = Quat.AngleAxis(phiT, rightT) * qT0;
                    tb.Position = k - tb.Rotation * kpLocal;
                }
                else
                {
                    // Standing on the landing gear, kingpin trailerGap behind the open jaw.
                    Vec3 k = body.State.LocalToWorld(tractor.Def.fifthWheel.position);
                    Vec3 kGround = k - n * Vec3.Dot(k, n) - fwd * sc.overrides.trailerGap + (qBase * Vec3.Right) * sc.overrides.trailerOffset;
                    var lg = trailer.Def.landingGear;
                    double legLoad = trailer.StaticNoseLoad(false) * 0.5;
                    double pen = legLoad / lg.stiffness;
                    PlaceTwoPoint(qT0, kGround, n, new Vec3(0, yT, zA), 0, new Vec3(0, lg.loweredFootY, lg.positionZ), -pen, out Quat qT, out Vec3 posT);
                    tb.Rotation = qT; tb.Position = posT;
                }
                tb.Velocity = (tb.Rotation * Vec3.Forward) * v0;
                ctx.TrailerBody = tb;
                if (v0 > 0.01) trailer.InitializeMoving(v0);
            }
            if (v0 > 0.01) tractor.InitializeMoving(v0, sc.initial.gear);

            bool park0 = sc.initial.parkingBrake || (sc.driver.type == "timeline" && sc.driver.keys.Length > 0 && sc.driver.keys[0].parkingBrake);
            tractor.InitParking(park0);
            if (trailer != null) trailer.Brakes.InitSpringChambers(trailer.Group);
            return ctx;
        }

        /// <summary>
        /// Rotation about the base right axis and offset along n so that two vehicle-frame points sit at the
        /// given heights above the plane, with the vehicle origin above basePoint.
        /// </summary>
        static void PlaceTwoPoint(Quat qBase, Vec3 basePoint, Vec3 n, Vec3 a, double ha, Vec3 b, double hb, out Quat q, out Vec3 pos)
        {
            Vec3 right = qBase * Vec3.Right;
            Func<double, double> f = phi =>
            {
                Quat qq = Quat.AngleAxis(phi, right) * qBase;
                return Vec3.Dot(qq * b - qq * a, n) - (hb - ha);
            };
            double phiS = Bisect(f, -0.3, 0.3);
            q = Quat.AngleAxis(phiS, right) * qBase;
            double s = ha - Vec3.Dot(q * a, n) - Vec3.Dot(basePoint, n);
            pos = basePoint + n * s;
        }

        static double Bisect(Func<double, double> f, double lo, double hi)
        {
            double flo = f(lo), fhi = f(hi);
            if (flo * fhi > 0) return 0;
            for (int i = 0; i < 80; i++)
            {
                double mid = 0.5 * (lo + hi), fm = f(mid);
                if ((fm < 0) == (flo < 0)) { lo = mid; flo = fm; } else hi = mid;
            }
            return 0.5 * (lo + hi);
        }

        public static IDriver CreateDriver(Scenario sc, SimContext s, out Vec3 center)
        {
            center = Vec3.Zero;
            var d = sc.driver;
            switch (d.type)
            {
                case "timeline": return new TimelineDriver(d.keys);
                case "speedhold": return new SpeedHoldDriver(d);
                case "circle":
                {
                    Vec3 right = s.Body.Rotation * Vec3.Right;
                    right = new Vec3(right.x, 0, right.z).Normalized;
                    int dir = d.direction >= 0 ? 1 : -1;
                    center = s.Body.Position + right * (dir * d.radius);
                    center = new Vec3(center.x, 0, center.z);
                    double wb = s.Tractor.Def.axles[0].positionZ - s.Tractor.Def.axles[1].positionZ;
                    return new CircleDriver(d, dir, center, wb);
                }
                case "lanechange":
                {
                    double wb = s.Tractor.Def.axles[0].positionZ - s.Tractor.Def.axles[1].positionZ;
                    return new LaneChangeDriver(d, s.Body.Position, s.Body.Rotation * Vec3.Forward, wb);
                }
                case "soak":
                {
                    double wb = s.Tractor.Def.axles[0].positionZ - s.Tractor.Def.axles[1].positionZ;
                    return new SoakDriver(d, s.Body.Position, s.Body.Rotation * Vec3.Forward, wb);
                }
                default: throw new ArgumentException($"Unknown driver type '{d.type}'");
            }
        }

        public static RunResult Run(Scenario sc, RunOptions opt = null)
        {
            opt ??= new RunOptions();
            var s = Setup(sc, opt);
            var driver = CreateDriver(sc, s, out Vec3 center);
            double dt = opt.Dt ?? sc.dt;
            double duration = opt.Duration ?? sc.duration;
            int steps = (int)Math.Round(duration / dt);
            int every = Math.Max(1, sc.sampleEvery);
            var res = new RunResult
            {
                Scenario = sc, CircleCenter = center, CircleRadius = sc.driver.radius, Dt = dt, SampleDt = dt * every,
                StaticKingpinLoad = s.Trailer != null ? s.Trailer.StaticNoseLoad(true) : 0, TotalMass = s.Tractor.MassProps.Mass + (s.Trailer?.Mass ?? 0),
            };
            res.Samples.Capacity = steps / every + 2;
            CsvTelemetry csv = opt.CsvPath != null ? new CsvTelemetry(opt.CsvPath, s, sc.id, opt.Commit) : null;
            var events = sc.events;
            int nextEvent = 0;
            var sw = new Stopwatch();
            long ticks = 0;
            double liftTime = -1;
            var tractorState = default(ChassisState);
            var trailerState = default(ChassisState);
            try
            {
                double t = 0;
                for (int i = 0; i < steps; i++)
                {
                    while (nextEvent < events.Length && events[nextEvent].t <= t + 1e-9) ApplyEvent(s, events[nextEvent++]);
                    DriverInput inp = driver.Update(t, dt, s);
                    sw.Restart();
                    tractorState = s.Body.State;
                    if (s.TrailerBody != null) trailerState = s.TrailerBody.State;
                    s.Combo.Step(dt, tractorState, trailerState, inp, s.Ground);
                    s.Body.Integrate(dt, s.Combo.TractorForce, s.Combo.TractorTorque);
                    s.TrailerBody?.Integrate(dt, s.Combo.TrailerForce, s.Combo.TrailerTorque);
                    sw.Stop();
                    ticks += sw.ElapsedTicks;
                    t += dt;
                    double us = sw.ElapsedTicks * 1e6 / Stopwatch.Frequency;
                    csv?.Write(s, inp, us);
                    var smp = MakeSample(t, s, inp);
                    if (i % every == 0 || i == steps - 1) res.Samples.Add(smp);
                    if (double.IsNaN(s.Body.Position.x) || double.IsNaN(s.Body.Velocity.x) || (s.TrailerBody != null && double.IsNaN(s.TrailerBody.Position.x)))
                        throw new InvalidOperationException($"{sc.id}: NaN at t={t}");
                    if (sc.endCondition == "wheel_lift")
                    {
                        if (liftTime < 0 && smp.WheelsOffGround > 0) liftTime = t;
                        if (liftTime >= 0 && t > liftTime + 0.3) break;
                    }
                }
            }
            finally { csv?.Dispose(); }
            res.MeanStepMicros = steps > 0 ? ticks * 1e6 / Stopwatch.Frequency / Math.Max(1, res.Samples.Count * every) : 0;
            res.CouplingEvents = s.Combo.FifthWheel.CouplingEvents;
            res.UncouplingEvents = s.Combo.FifthWheel.UncouplingEvents;
            res.ShiftCount = s.Tractor.Amt.ShiftCount;
            res.RejectedShifts = s.Tractor.Amt.RejectedShiftCount;
            foreach (var c in sc.checks)
            {
                if (!string.IsNullOrEmpty(c.variant) && c.variant != sc.variant) continue;
                double v = Metrics.Compute(res, c.metric, c.arg, c.from, c.to);
                bool ok = !double.IsNaN(v) && (!c.min.HasValue || v >= c.min.Value) && (!c.max.HasValue || v <= c.max.Value);
                res.Checks.Add(new CheckResult { Spec = c, Value = v, Passed = ok });
            }
            return res;
        }

        static double AxleMeanZ(TrailerModel tr)
        {
            double z = 0;
            foreach (var a in tr.Def.axles) z += a.positionZ;
            return z / tr.Def.axles.Length;
        }

        static void ApplyEvent(SimContext s, EventSpec e)
        {
            switch (e.type)
            {
                case "couple_arm": s.Combo.CouplingArmed = true; break;
                case "uncouple": s.Combo.Uncouple(); break;
                case "landing_gear_up": if (s.Trailer != null) s.Trailer.LandingGearDown = false; break;
                case "landing_gear_down": if (s.Trailer != null) s.Trailer.LandingGearDown = true; break;
                case "leak":
                    if (e.circuit >= 0 && e.circuit < 4) s.Tractor.Air.LeakLpm[e.circuit] = e.lpm;
                    else if (e.circuit == 4 && s.Trailer != null) s.Trailer.Brakes.LeakLpm = e.lpm;
                    break;
                default: throw new ArgumentException($"Unknown event '{e.type}'");
            }
        }

        public static Sample MakeSample(double t, SimContext s, in DriverInput inp)
        {
            var m = s.Tractor; var b = s.Body;
            Vec3 fwd = b.Rotation * Vec3.Forward;
            Vec3 right = b.Rotation * Vec3.Right;
            double maxRatio = 0, sumFz = 0, minFz = double.MaxValue, rearSlip = 0;
            int off = 0, bit = 0;
            ulong offMask = 0;
            foreach (var w in m.Wheels)
            {
                sumFz += w.Fz;
                if (w.StaticLoad > 0) maxRatio = Math.Max(maxRatio, w.Fz / w.StaticLoad);
                minFz = Math.Min(minFz, w.Fz);
                if (!w.Contact || w.Fz < 500) { off++; if (bit < 64) offMask |= 1UL << bit; }
                bit++;
                if (w.Driven && Math.Abs(w.Vx) > 2.0) rearSlip = Math.Min(rearSlip, w.KinematicSlip * Math.Sign(w.Vx));
            }
            var smp = new Sample
            {
                T = t, Pos = b.Position, ComPos = b.CenterOfMassWorld, Vel = b.Velocity, Fwd = fwd, Right = right, SpeedFwd = m.SpeedForward, YawRate = m.YawRate,
                Rpm = m.Engine.Rpm, Gear = m.Amt.Gear, SteerAngle = m.Steering.Angle,
                Pitch = Math.Asin(MathUtil.Clamp(fwd.y, -1, 1)), Roll = Math.Asin(MathUtil.Clamp(right.y, -1, 1)),
                LatAccel = m.SpeedForward * m.YawRate, LongAccel = m.LocalAcceleration.z,
                ThrottleIn = inp.Throttle, BrakeIn = inp.Brake, Stalled = m.Engine.Stalled,
                MaxFzRatio = maxRatio, SumFz = sumFz, KineticEnergy = b.KineticEnergy,
                AirFront = m.Air.Front, AirRear = m.Air.Rear, AirPark = m.Air.ParkTrailer, AirSupply = m.Air.Supply,
                LowAirWarning = m.Air.LowPressureWarning,
                ChamberFront = m.Wheels[0].ChamberPressure, ChamberRear = m.Wheels[2].ChamberPressure,
                RearSlip = rearSlip,
                RetarderTorque = m.Retarder.Torque, EngineBrakeTorque = m.Engine.EngineBrakeTorque, BrakeDemand = m.BrakeDemand,
                ClutchTemp = m.Amt.ClutchTempC, AmtState = (int)m.Amt.State,
                CabPitch = m.Cab.Pitch, CabRoll = m.Cab.Roll, CabHeave = m.Cab.Heave,
                ParkingState = m.ParkingBrakeState,
            };
            var tr = s.Trailer;
            if (tr != null)
            {
                var tb = s.TrailerBody; var fw = s.Combo.FifthWheel;
                double tSlip = 0;
                foreach (var w in tr.Wheels)
                {
                    minFz = Math.Min(minFz, w.Fz);
                    if (!w.Contact || w.Fz < 500) { off++; if (bit < 64) offMask |= 1UL << bit; }
                    bit++;
                    if (Math.Abs(w.Vx) > 2.0) tSlip = Math.Min(tSlip, w.KinematicSlip * Math.Sign(w.Vx));
                }
                Vec3 tright = tb.Rotation * Vec3.Right;
                smp.HasTrailer = true; smp.Coupled = fw.Coupled;
                smp.TrailerPos = tb.Position; smp.TrailerAxlePos = tb.State.LocalToWorld(new Vec3(0, 0, AxleMeanZ(tr))); smp.TrailerComPos = tb.CenterOfMassWorld; smp.TrailerVel = tb.Velocity;
                smp.Articulation = fw.Articulation; smp.KingpinFz = fw.KingpinLoadLocal.y; smp.KingpinFx = fw.KingpinLoadLocal.z; smp.KingpinFy = fw.KingpinLoadLocal.x;
                smp.FifthWheelError = fw.Coupled ? fw.PositionError : 0;
                smp.TrailerYawRate = tr.YawRate; smp.TrailerLatAccel = tr.SpeedForward * tr.YawRate;
                smp.TrailerRoll = Math.Asin(MathUtil.Clamp(tright.y, -1, 1));
                smp.AirTrailer = tr.Brakes.Reservoir; smp.TrailerEmergency = tr.Brakes.Emergency;
                smp.ChamberTrailer = tr.Wheels[0].ChamberPressure;
                smp.TrailerSlip = tSlip;
                smp.LandingGearLoad = tr.LandingGearLoad;
                smp.KineticEnergy += tb.KineticEnergy;
            }
            smp.MinFz = minFz;
            smp.WheelsOffGround = off;
            smp.OffMask = offMask;
            smp.TractorWheelCount = m.Wheels.Length;
            return smp;
        }
    }
}
