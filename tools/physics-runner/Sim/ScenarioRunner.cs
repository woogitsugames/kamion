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
        public double MeanStepMicros;
        public bool Passed { get { foreach (var c in Checks) if (!c.Passed) return false; return true; } }
        public double Metric(string name, double arg = 0, double from = 0) => Metrics.Compute(this, name, arg, from);
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
            // Rotation matrix columns r,u,f -> quaternion
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

        /// <summary>Creates model + body placed at static ride height on the ground.</summary>
        public static (VehicleModel model, RigidBody6Dof body, AnalyticGround ground) Setup(Scenario sc, RunOptions opt)
        {
            var settings = new SolverSettings { substeps = opt.Substeps ?? sc.substeps };
            var model = Defs.CreateModel(sc.vehicle, settings);
            var ground = BuildGround(sc.ground);
            var body = new RigidBody6Dof(model.MassProps);
            double heading = (opt.HeadingDeg ?? sc.initial.headingDeg) * MathUtil.Deg2Rad;
            Vec3 n = ground.PlaneNormal;
            Vec3 hdir = new Vec3(Math.Sin(heading), 0, Math.Cos(heading));
            Vec3 fwd = Vec3.ProjectOnPlane(hdir, n).Normalized;
            body.Rotation = LookRotation(fwd, n);
            double x0 = sc.initial.x, z0 = sc.initial.z;
            body.Position = new Vec3(x0, ground.HeightAt(x0, z0), z0);
            double v0 = sc.initial.speedKmh / 3.6;
            body.Velocity = fwd * v0;
            if (v0 > 0.01) model.InitializeMoving(v0, sc.initial.gear);
            return (model, body, ground);
        }

        public static IDriver CreateDriver(Scenario sc, VehicleModel model, RigidBody6Dof body, out Vec3 center)
        {
            center = Vec3.Zero;
            switch (sc.driver.type)
            {
                case "timeline": return new TimelineDriver(sc.driver.keys);
                case "speedhold": return new SpeedHoldDriver(sc.driver.targetKmh, sc.driver.steer, sc.driver.selector);
                case "circle":
                {
                    Vec3 right = body.Rotation * Vec3.Right;
                    right = new Vec3(right.x, 0, right.z).Normalized;
                    int dir = sc.driver.direction >= 0 ? 1 : -1;
                    center = body.Position + right * (dir * sc.driver.radius);
                    center = new Vec3(center.x, 0, center.z);
                    double wb = model.Def.axles[0].positionZ - model.Def.axles[1].positionZ;
                    return new CircleDriver(sc.driver.targetKmh, sc.driver.radius, dir, center, wb);
                }
                default: throw new ArgumentException($"Unknown driver type '{sc.driver.type}'");
            }
        }

        public static RunResult Run(Scenario sc, RunOptions opt = null)
        {
            opt ??= new RunOptions();
            var (model, body, ground) = Setup(sc, opt);
            var driver = CreateDriver(sc, model, body, out Vec3 center);
            double dt = opt.Dt ?? sc.dt;
            double duration = opt.Duration ?? sc.duration;
            int steps = (int)Math.Round(duration / dt);
            var res = new RunResult { Scenario = sc, CircleCenter = center, CircleRadius = sc.driver.radius, Dt = dt };
            res.Samples.Capacity = steps + 1;
            CsvTelemetry csv = opt.CsvPath != null ? new CsvTelemetry(opt.CsvPath, model, sc.vehicle, opt.Commit) : null;
            var sw = new Stopwatch();
            long ticks = 0;
            try
            {
                double t = 0;
                for (int i = 0; i < steps; i++)
                {
                    DriverInput inp = driver.Update(t, dt, model, body);
                    sw.Restart();
                    ChassisState st = body.State;
                    model.Step(dt, st, inp, ground);
                    body.Integrate(dt, model.TotalForce, model.TotalTorque);
                    sw.Stop();
                    ticks += sw.ElapsedTicks;
                    t += dt;
                    double us = sw.ElapsedTicks * 1e6 / Stopwatch.Frequency;
                    csv?.Write(model, body, inp, us);
                    res.Samples.Add(MakeSample(t, model, body, inp));
                    if (double.IsNaN(body.Position.x) || double.IsNaN(body.Velocity.x))
                        throw new InvalidOperationException($"{sc.id}: NaN at t={t}");
                }
            }
            finally { csv?.Dispose(); }
            res.MeanStepMicros = steps > 0 ? ticks * 1e6 / Stopwatch.Frequency / steps : 0;
            foreach (var c in sc.checks)
            {
                double v = Metrics.Compute(res, c.metric, c.arg, c.from);
                bool ok = !double.IsNaN(v) && (!c.min.HasValue || v >= c.min.Value) && (!c.max.HasValue || v <= c.max.Value);
                res.Checks.Add(new CheckResult { Spec = c, Value = v, Passed = ok });
            }
            return res;
        }

        static Sample MakeSample(double t, VehicleModel m, RigidBody6Dof b, in DriverInput inp)
        {
            Vec3 fwd = b.Rotation * Vec3.Forward;
            Vec3 right = b.Rotation * Vec3.Right;
            double maxRatio = 0, sumFz = 0;
            foreach (var w in m.Wheels)
            {
                sumFz += w.Fz;
                if (w.StaticLoad > 0) maxRatio = Math.Max(maxRatio, w.Fz / w.StaticLoad);
            }
            return new Sample
            {
                T = t, Pos = b.Position, ComPos = b.CenterOfMassWorld, Vel = b.Velocity, SpeedFwd = m.SpeedForward, YawRate = m.YawRate,
                Rpm = m.Engine.Rpm, Gear = m.Amt.Gear, SteerAngle = m.Steering.Angle,
                Pitch = Math.Asin(MathUtil.Clamp(fwd.y, -1, 1)), Roll = Math.Asin(MathUtil.Clamp(right.y, -1, 1)),
                LatAccel = m.SpeedForward * m.YawRate, LongAccel = m.LocalAcceleration.z,
                ThrottleIn = inp.Throttle, BrakeIn = inp.Brake, Stalled = m.Engine.Stalled,
                MaxFzRatio = maxRatio, SumFz = sumFz,
            };
        }
    }
}
