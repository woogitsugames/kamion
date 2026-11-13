using System;
using Game.Vehicle.Physics;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0195: the gate 1-2 straight-run pilot on a kinematic toy plant (point mass with linear resistance + bicycle yaw).
    /// Checks the phase sequence, the metric definitions (same as the .NET runner) against closed-form results, the steering
    /// sign, determinism and zero allocation per step. The real vehicle model is exercised by the runner scenario
    /// straight_0_80_0 and the PlayMode test StraightRunAutopilotTests.
    /// </summary>
    public class StraightRunPilotTests
    {
        const double Dt = 0.01;
        /// <summary>Linear resistance [1/s]: at 80 km/h the toy needs 35 % throttle (the hold controller's feed-forward).</summary>
        const double K = 0.7 / (80 / 3.6);

        /// <summary>Toy plant: a = 2.0 th - 6.0 br - K v (m/s^2, brake only while moving), kinematic bicycle, wheelbase 3.7 m.</summary>
        struct Toy
        {
            public double X, Z, Heading, V;

            public void Step(in DriverInput u, double maxAngle)
            {
                double a = 2.0 * u.Throttle - (V > 0 ? 6.0 * u.Brake : 0) - K * V;
                V = Math.Max(0, V + a * Dt);
                Heading += V / 3.7 * Math.Tan(u.Steer * maxAngle) * Dt;   // + = clockwise from above (turn right)
                X += Math.Sin(Heading) * V * Dt;
                Z += Math.Cos(Heading) * V * Dt;
            }
        }

        static StraightRunPilot Run(ref Toy toy, int maxSteps = 20000)
        {
            var p = new StraightRunPilot { MaxRoadWheelAngle = 0.7, Wheelbase = 3.7 };
            p.Begin(toy.X, toy.Z, Math.Sin(toy.Heading), Math.Cos(toy.Heading), Dt);
            var u = new DriverInput();
            for (int i = 0; i < maxSteps && p.Phase != StraightRunPhase.Stopped; i++)
            {
                p.Step(Dt, toy.X, toy.Z, Math.Sin(toy.Heading), Math.Cos(toy.Heading), toy.V, ref u);
                toy.Step(u, p.MaxRoadWheelAngle);
            }
            return p;
        }

        [Test]
        public void PhaseSequence_And_MetricsMatchClosedForm()
        {
            var toy = new Toy();
            var p = Run(ref toy);
            var r = p.Result;
            Assert.AreEqual(StraightRunPhase.Stopped, p.Phase);
            Assert.IsTrue(r.Complete);
            // Launch from the throttle step (after the 1 s settle): dv/dt = 2 - K v -> t(v) = -ln(1 - K v / 2) / K.
            Func<double, double> tOf = v => -Math.Log(1 - K * v / 2) / K;
            Assert.AreEqual(tOf(60 / 3.6), r.TimeTo60, 0.03);
            Assert.AreEqual(tOf(80 / 3.6), r.TimeTo80, 0.03);
            double t80 = tOf(80 / 3.6);
            Assert.AreEqual(2 / K * (t80 - (1 - Math.Exp(-K * t80)) / K), r.DistanceTo80, 0.5);
            Assert.AreEqual(80.0, r.HoldSpeedMean, 1.5, "hold controller keeps 80 km/h");
            Assert.Less(r.HoldSpeedStd, 1.0);
            // Full brake: dv/dt = -(6 + K v) -> s = v0/K - 6/K^2 ln(1 + K v0 / 6), t = ln(1 + K v0 / 6) / K.
            double v0 = r.BrakeSpeedKmh / 3.6;
            Assert.AreEqual(80.0, r.BrakeSpeedKmh, 1.5);
            Assert.AreEqual(v0 / K - 6 / (K * K) * Math.Log(1 + K * v0 / 6), r.StopDistance, 0.3);
            Assert.AreEqual(Math.Log(1 + K * v0 / 6) / K, r.StopTime, 0.03);
            // MFDD (0.8 v0 .. 0.1 v0) lies between the decelerations at those speeds; the peak is at the onset (6 + K v0).
            Assert.That(r.Mfdd, Is.InRange(6 + K * 0.1 * v0, 6 + K * 0.8 * v0));
            Assert.AreEqual(6 + K * v0, r.MaxDecel, 0.1);
            Assert.Less(r.MaxLateralDeviation, 0.01);
        }

        [Test]
        public void Settle_HoldsBrake_ThenFullThrottle_InDrive_ParkingOff()
        {
            var p = new StraightRunPilot();
            p.Begin(0, 0, 0, 1, Dt);
            var u = new DriverInput { ParkingBrake = true };
            p.Step(Dt, 0, 0, 0, 1, 0, ref u);
            Assert.AreEqual(StraightRunPhase.Settle, p.Phase);
            Assert.AreEqual(1.0, u.Brake);
            Assert.AreEqual(0.0, u.Throttle);
            Assert.IsFalse(u.ParkingBrake);
            Assert.AreEqual(GearSelector.Drive, u.Selector);
            for (int i = 0; i < 100; i++) p.Step(Dt, 0, 0, 0, 1, 0, ref u);
            Assert.AreEqual(StraightRunPhase.Launch, p.Phase);
            Assert.AreEqual(1.0, u.Throttle);
            Assert.AreEqual(0.0, u.Brake);
        }

        [Test]
        public void Steering_ReturnsToTheLine_SignIsRightPositive()
        {
            // Line along +Z (north) from the origin; the vehicle 1 m east = right of it, heading north -> steer left (< 0).
            var p = new StraightRunPilot { MaxRoadWheelAngle = 0.7 };
            p.Begin(0, 0, 0, 1, Dt);
            var u = new DriverInput();
            for (int i = 0; i < 101; i++) p.Step(Dt, 0, 0, 0, 1, 0, ref u);   // through the settle phase
            p.Step(Dt, 1.0, 5.0, 0, 1, 10, ref u);
            Assert.Less(u.Steer, 0.0, "right of the line -> steer left");
            p.Step(Dt, -1.0, 5.2, 0, 1, 10, ref u);
            Assert.Greater(u.Steer, 0.0, "left of the line -> steer right");
            Assert.AreEqual(1.0, p.Lateral(1.0, 7.0), 1e-9, "lateral + = right of the line");

            // Closed loop on the toy: start 1.5 m right of the line; the offset decays during the launch.
            var q = new StraightRunPilot { MaxRoadWheelAngle = 0.7 };
            q.Begin(0, 0, 0, 1, Dt);
            var toy = new Toy { X = 1.5 };
            var v = new DriverInput();
            for (int i = 0; i < 2000; i++)
            {
                q.Step(Dt, toy.X, toy.Z, Math.Sin(toy.Heading), Math.Cos(toy.Heading), toy.V, ref v);
                toy.Step(v, 0.7);
            }
            Assert.Less(Math.Abs(q.Lateral(toy.X, toy.Z)), 0.05, "converges to the line");
        }

        [Test]
        public void Deterministic_AndNoAllocationPerStep()
        {
            var a = new Toy();
            var b = new Toy();
            var pa = Run(ref a);
            var pb = Run(ref b);
            Assert.AreEqual(pa.Result.TimeTo80, pb.Result.TimeTo80);
            Assert.AreEqual(pa.Result.StopDistance, pb.Result.StopDistance);
            Assert.AreEqual(a.X, b.X);
            Assert.AreEqual(a.Z, b.Z);

            var p = new StraightRunPilot();
            var toy = new Toy();
            p.Begin(0, 0, 0, 1, Dt);
            var u = new DriverInput();
            p.Step(Dt, toy.X, toy.Z, 0, 1, toy.V, ref u);   // warm-up (JIT)
            int control = GcAllocCounter.Count(() => GC.KeepAlive(new byte[64]));
            Assert.Greater(control, 0, "control: GC.Alloc recorder must be live");
            int allocs = GcAllocCounter.Count(() =>
            {
                for (int i = 0; i < 5000; i++)
                {
                    p.Step(Dt, toy.X, toy.Z, Math.Sin(toy.Heading), Math.Cos(toy.Heading), toy.V, ref u);
                    toy.Step(u, p.MaxRoadWheelAngle);
                }
            });
            Assert.AreEqual(0, allocs, "StraightRunPilot.Step allocates");
            Assert.AreEqual(StraightRunPhase.Stopped, p.Phase);
        }
    }
}
