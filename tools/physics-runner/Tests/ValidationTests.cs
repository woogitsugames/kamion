using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Game.Vehicle.Physics;
using PhysicsRunner.Sim;
using Xunit;
using Xunit.Abstractions;

namespace PhysicsRunner.Tests
{
    /// <summary>docs/04 section 6 scenarios from tests/physics/scenarios/*.json.</summary>
    public class ScenarioTests
    {
        readonly ITestOutputHelper _out;
        public ScenarioTests(ITestOutputHelper output) { _out = output; }

        public static IEnumerable<object[]> ScenarioIds() =>
            Scenario.LoadAll(RepoPaths.ScenariosDir).Select(s => new object[] { s.id });

        [Theory]
        [MemberData(nameof(ScenarioIds))]
        public void ScenarioPasses(string id)
        {
            var sc = Suites.Find(id);
            var r = ScenarioRunner.Run(sc);
            var sb = new StringBuilder();
            foreach (var c in r.Checks) sb.AppendLine(c.ToString());
            _out.WriteLine(sb.ToString());
            Assert.True(r.Checks.Count > 0, "scenario has no checks");
            Assert.True(r.Passed, $"{id} failed:\n{sb}");
        }
    }

    public class MultiRunTests
    {
        readonly ITestOutputHelper _out;
        public MultiRunTests(ITestOutputHelper output) { _out = output; }

        /// <summary>docs/04 s6.3: 0-60 / 0-80 repeatable within +/-3% over 3 runs.</summary>
        [Fact]
        public void Acceleration_IsRepeatable_Within3Percent()
        {
            var res = Suites.Repeatability("launch_0_80_flat", new[] { 0.0, 37.0, 113.0 });
            foreach (var s in res)
            {
                _out.WriteLine(s.ToString());
                Assert.All(s.Values, v => Assert.False(double.IsNaN(v)));
                Assert.True(s.MaxRelDev <= 0.03, s.ToString());
            }
        }

        /// <summary>docs/04 s6.12: different fixed dt -> no qualitative differences (WORKING_VALUE tolerance 5%).</summary>
        [Theory]
        [InlineData("launch_0_80_flat", "time_to_kmh", 80)]
        [InlineData("brake_80_0_dry", "stop_distance_m", 0)]
        [InlineData("brake_80_0_wet", "stop_distance_m", 0)]
        [InlineData("circle_r25_20kmh", "lat_accel_ms2", 0)]
        public void DtVariation_IsConsistent(string id, string metric, double arg)
        {
            var s = Suites.DtSweep(id, metric, arg, new[] { 1 / 50.0, 1 / 100.0, 1 / 120.0 });
            _out.WriteLine(s.ToString());
            Assert.All(s.Values, v => Assert.False(double.IsNaN(v)));
            Assert.True(s.MaxRelDev <= 0.05, s.ToString());
        }

        [Fact]
        public void SubstepVariation_IsConsistent()
        {
            var s = Suites.SubstepSweep("brake_80_0_dry", "stop_distance_m", 0, new[] { 2, 4, 8 });
            _out.WriteLine(s.ToString());
            Assert.True(s.MaxRelDev <= 0.05, s.ToString());
        }

        /// <summary>docs/04 s6.7: steer angle grows with speed on a constant radius (understeer), solo tractor.</summary>
        [Fact]
        public void Circle_ShowsUndersteerWithSpeed()
        {
            var slow = ScenarioRunner.Run(Suites.Find("circle_r25_10kmh")).Metric("steer_vs_ackermann", 3.7, 20);
            var fast = ScenarioRunner.Run(Suites.Find("circle_r25_20kmh")).Metric("steer_vs_ackermann", 3.7, 20);
            _out.WriteLine($"steer/ackermann 10 km/h {slow:F3}, 20 km/h {fast:F3}");
            Assert.True(fast > slow, "expected understeer gradient > 0");
        }
    }

    public class CoreTests
    {
        readonly ITestOutputHelper _out;
        public CoreTests(ITestOutputHelper output) { _out = output; }

        [Fact]
        public void MassProperties_MatchReferenceData()
        {
            var m = ScenarioRunner.Defs.CreateModel("tractor_4x2_generic", new SolverSettings());
            var mp = m.MassProps;
            double front = 0, rear = 0;
            foreach (var w in m.Wheels) if (w.AxleIndex == 0) front += w.StaticLoad; else rear += w.StaticLoad;
            _out.WriteLine($"mass {mp.Mass} kg, CoM {mp.CenterOfMass}, front {front / 9.81:F0} kg, rear {rear / 9.81:F0} kg, Ixx {mp.Inertia.m00:F0} Iyy {mp.Inertia.m11:F0} Izz {mp.Inertia.m22:F0}");
            Assert.InRange(mp.Mass, 7400, 7600);
            Assert.InRange(front / 9.81, 4500, 5500);
            Assert.InRange(mp.CenterOfMass.y, 0.9, 1.3);
            Assert.Equal(mp.Mass * 9.81, m.TotalStaticLoad, 6);
            Assert.True(mp.Inertia.m00 > 0 && mp.Inertia.m11 > 0 && mp.Inertia.m22 > 0);
        }

        [Fact]
        public void Tire_PureSlipPeakEqualsMuFz_AndCombinedIsBounded()
        {
            var tm = new TireModel(ScenarioRunner.Defs.Tires["tire_315_80_r22_5"]);
            double fz = 30000;
            double mu = tm.PeakMu(fz, 1.0);
            tm.CombinedForces(fz, 1, 1.0, tm.PeakKappa(mu, fz), 0, out double fx, out _, out _);
            Assert.InRange(fx, 0.999 * mu * fz, 1.0001 * mu * fz);
            tm.CombinedForces(fz, 1, 1.0, 0, tm.PeakTanAlpha(mu, fz), out _, out double fy, out _);
            Assert.InRange(fy, 0.999 * mu * fz, 1.0001 * mu * fz);
            for (double k = -1; k <= 1; k += 0.05)
                for (double a = -1; a <= 1; a += 0.05)
                {
                    tm.CombinedForces(fz, 1, 1.0, k, a, out fx, out fy, out _);
                    Assert.True(Math.Sqrt(fx * fx + fy * fy) <= mu * fz * 1.0001);
                    Assert.True(Math.Sign(fx) == Math.Sign(k) || Math.Abs(fx) < 1e-6);
                }
            // Small-slip stiffness
            tm.CombinedForces(fz, 1, 1.0, 1e-5, 0, out fx, out _, out _);
            Assert.InRange(fx / 1e-5, 0.99 * 12 * fz, 1.01 * 12 * fz);
        }

        [Fact]
        public void Definitions_RejectWrongSchemaVersion()
        {
            var t = new TireDefinition { id = "x", schemaVersion = 99 };
            Assert.Throws<FormatException>(() => t.Validate());
            var v = new VehicleDefinition { id = "y", schemaVersion = 2 };
            Assert.Throws<FormatException>(() => v.Validate());
        }

        [Fact]
        public void Definitions_AllLoadAndValidate()
        {
            var d = ScenarioRunner.Defs;
            Assert.Contains("tractor_4x2_generic", d.Vehicles.Keys);
            Assert.Equal(12, d.Gearboxes["amt12_od_traxon_class"].ForwardGearCount);
        }

        /// <summary>CLAUDE.md: zero GC allocations in the drive loop (solver step + host integration).</summary>
        [Fact]
        public void Step_DoesNotAllocate()
        {
            foreach (var id in new[] { "circle_r25_20kmh", "lane_change_80@laden40" })
            {
                var sc = Suites.Find(id);
                var s = ScenarioRunner.Setup(sc, new RunOptions());
                var inp = new DriverInput { Throttle = 0.4, Steer = 0.05, Selector = GearSelector.Drive };
                void Step()
                {
                    var ts = s.TrailerBody != null ? s.TrailerBody.State : default;
                    s.Combo.Step(0.01, s.Body.State, ts, inp, s.Ground);
                    s.Body.Integrate(0.01, s.Combo.TractorForce, s.Combo.TractorTorque);
                    s.TrailerBody?.Integrate(0.01, s.Combo.TrailerForce, s.Combo.TrailerTorque);
                }
                for (int i = 0; i < 300; i++) Step();
                long before = GC.GetAllocatedBytesForCurrentThread();
                for (int i = 0; i < 2000; i++)
                {
                    inp.Brake = (i / 500) % 2 == 0 ? 0 : 0.5;
                    inp.Throttle = inp.Brake > 0 ? 0 : 0.6;
                    inp.RetarderLever = (i / 250) % 3;
                    Step();
                }
                long after = GC.GetAllocatedBytesForCurrentThread();
                _out.WriteLine($"{id}: {after - before} bytes");
                Assert.Equal(0, after - before);
            }
        }

        [Fact]
        public void Steering_AckermannInnerWheelTurnsMore()
        {
            var m = ScenarioRunner.Defs.CreateModel("tractor_4x2_generic", new SolverSettings());
            for (int i = 0; i < 200; i++) m.Steering.Update(0.5, 0.01);
            double inner = m.Steering.WheelAngle(+1.025, 3.7);
            double outer = m.Steering.WheelAngle(-1.025, 3.7);
            Assert.True(inner > outer && outer > 0);
            // cot(outer) - cot(inner) = track / wheelbase
            Assert.InRange(1 / Math.Tan(outer) - 1 / Math.Tan(inner), 2.04 / 3.7 - 1e-6, 2.04 / 3.7 + 1e-6);
        }
    }
}
