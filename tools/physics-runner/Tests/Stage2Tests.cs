using System;
using System.Collections.Generic;
using System.Linq;
using Game.Vehicle.Physics;
using PhysicsRunner.Sim;
using Xunit;
using Xunit.Abstractions;

namespace PhysicsRunner.Tests
{
    /// <summary>Stage 2: combination, air brakes, endurance brakes, golden telemetry.</summary>
    public class Stage2Tests
    {
        readonly ITestOutputHelper _out;
        public Stage2Tests(ITestOutputHelper output) { _out = output; }

        public static IEnumerable<object[]> GoldenIds() => Golden.Ids.Select(i => new object[] { i });

        /// <summary>Regression against tests/golden (10 Hz subsets, per-column tolerances).</summary>
        [Theory]
        [MemberData(nameof(GoldenIds))]
        public void GoldenTelemetry_Matches(string id)
        {
            string csv = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "physics-golden-" + id.Replace('@', '_') + ".csv");
            ScenarioRunner.Run(Suites.Find(id), new RunOptions { CsvPath = csv });
            var res = Golden.Compare(id, csv);
            foreach (var c in res) _out.WriteLine(c.ToString());
            Assert.NotEmpty(res);
            Assert.All(res, c => Assert.True(c.Passed, c.ToString()));
        }

        /// <summary>40 t preset: total mass and static axle loads (axle limits as commonly quoted from Directive 96/53/EC, UNVERIFIED).</summary>
        [Fact]
        public void Laden40_StaticLoads_AreConsistentAndPlausible()
        {
            var s = ScenarioRunner.Setup(Suites.Find("park_flat_5min_comb@laden40"), new RunOptions());
            double total = s.Tractor.MassProps.Mass + s.Trailer.Mass;
            double front = 0, drive = 0, tridem = 0;
            foreach (var w in s.Tractor.Wheels) if (w.AxleIndex == 0) front += w.StaticLoad; else drive += w.StaticLoad;
            foreach (var w in s.Trailer.Wheels) tridem += w.StaticLoad;
            _out.WriteLine($"GCW {total:F0} kg, front {front / 9.81:F0}, drive {drive / 9.81:F0}, tridem {tridem / 9.81:F0} kg, kingpin {s.Combo.StaticKingpinLoad / 9.81:F0} kg");
            Assert.InRange(total, 39990, 40010);
            Assert.InRange((front + drive + tridem) / 9.81, total - 1, total + 1);
            Assert.True(front / 9.81 <= 7500, "steer axle");
            Assert.True(drive / 9.81 <= 11500, "drive axle 11.5 t");
            Assert.True(tridem / 9.81 <= 24000, "tridem 24 t");
        }

        /// <summary>Kingpin load in a parked combination equals the static nose load (constraint transmits gravity correctly).</summary>
        [Theory]
        [InlineData("park_flat_5min_comb@empty")]
        [InlineData("park_flat_5min_comb@laden40")]
        public void KingpinLoad_EqualsStaticNoseLoad(string id)
        {
            var r = ScenarioRunner.Run(Suites.Find(id), new RunOptions { Duration = 20 });
            double ratio = r.Metric("kingpin_load_vs_static", 0, 10);
            _out.WriteLine($"{id}: kingpin / static = {ratio:F4}");
            Assert.InRange(ratio, 0.97, 1.03);
        }

        /// <summary>docs/04 s6.7: the rollover threshold depends on the cargo CoG height.</summary>
        [Fact]
        public void Rollover_HigherCog_LiftsEarlier()
        {
            double low = ScenarioRunner.Run(Suites.Find("rollover_r50_cog_low@laden40")).Metric("lat_accel_at_first_lift");
            double high = ScenarioRunner.Run(Suites.Find("rollover_r50_cog_high@laden40")).Metric("lat_accel_at_first_lift");
            _out.WriteLine($"first wheel lift: CoG 1.9 m at {low:F3} g, CoG 2.6 m at {high:F3} g");
            Assert.True(low > high + 0.05, $"low {low} high {high}");
        }

        /// <summary>Endurance brake ratings vs the class-reference sources (S1 VEB+ 375 kW at 2300 rpm, S2 Intarder 4000 Nm / 600 kW).</summary>
        [Fact]
        public void EnduranceBrakes_MatchClassReference()
        {
            var m = ScenarioRunner.Defs.CreateModel("tractor_4x2_generic", new SolverSettings());
            double w2300 = 2300 * MathUtil.RpmToRadS;
            double pEb = m.Engine.EngineBrakeTotal(w2300) * w2300 / 1000;
            _out.WriteLine($"engine brake at 2300 rpm: {pEb:F1} kW");
            Assert.InRange(pEb, 370, 380);
            double maxT = 0, maxP = 0;
            for (double rpm = 50; rpm <= 3000; rpm += 25)
            {
                double w = rpm * MathUtil.RpmToRadS;
                double t = m.Retarder.Available(w);
                maxT = Math.Max(maxT, t); maxP = Math.Max(maxP, t * w / 1000);
            }
            _out.WriteLine($"retarder max torque {maxT:F0} Nm, max power {maxP:F0} kW");
            Assert.True(maxT <= 4000.001 && maxT > 3900);
            Assert.True(maxP <= 600.001 && maxP > 590);
        }

        /// <summary>docs/04 s6.12 for the combination: dt and substeps do not change the outcome qualitatively.</summary>
        [Theory]
        [InlineData("brake_80_0_dry_abs_comb@laden40", "stop_distance_m", 0)]
        [InlineData("brake_80_0_wet_abs_comb@laden40", "stop_distance_m", 0)]
        [InlineData("lane_change_80@laden40", "max_articulation_deg", 0)]
        [InlineData("launch_flat_comb@laden40", "time_to_kmh", 60)]
        public void Combination_DtVariation_IsConsistent(string id, string metric, double arg)
        {
            var s = Suites.DtSweep(id, metric, arg, new[] { 1 / 50.0, 1 / 100.0, 1 / 120.0 });
            var sub = Suites.SubstepSweep(id, metric, arg, new[] { 2, 4, 8 });
            _out.WriteLine(s.ToString()); _out.WriteLine(sub.ToString());
            Assert.True(s.MaxRelDev <= 0.05, s.ToString());
            Assert.True(sub.MaxRelDev <= 0.05, sub.ToString());
        }

        /// <summary>Air supply: an empty system charges, releases the spring brakes, and the governor cuts out.</summary>
        [Fact]
        public void AirSystem_ChargesFromEmpty()
        {
            var m = ScenarioRunner.Defs.CreateModel("tractor_4x2_generic", new SolverSettings());
            m.Air.Charge(0);
            m.InitParking(true);
            double t = 0, tRelease = double.NaN, tCutOut = double.NaN;
            for (int i = 0; i < 60000 && double.IsNaN(tCutOut); i++)
            {
                m.Air.Update(0.01, 1200, true, 0, false, false, m.Group);
                m.Air.BeginSubsteps();
                m.Air.UpdateChambers(0.01, m.Group);
                t += 0.01;
                if (double.IsNaN(tRelease) && m.Wheels[2].SpringChamberPressure >= m.Def.air.springReleaseFullBar) tRelease = t;
                if (!m.Air.CompressorLoaded && t > 1) tCutOut = t;
            }
            _out.WriteLine($"1200 rpm, empty system: spring brakes released after {tRelease:F0} s, governor cut-out after {tCutOut:F0} s");
            Assert.False(double.IsNaN(tRelease));
            Assert.False(double.IsNaN(tCutOut));
            Assert.True(tRelease < tCutOut);
            Assert.InRange(tCutOut, 30, 600);
        }
    }
}
