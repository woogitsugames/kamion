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
    /// <summary>
    /// M34 robustness (docs/04 s6.12 / s6.14): bit-determinism, fixed-dt / substep consistency incl. 1/60 Hz,
    /// fuzz invariant scenarios, and unit tests for the new metrics (energy drift, friction ratio, air floor,
    /// articulation stop, cab angular-velocity spectrum, NaN flag).
    /// </summary>
    public class RobustnessTests
    {
        readonly ITestOutputHelper _out;
        public RobustnessTests(ITestOutputHelper output) { _out = output; }

        /// <summary>Same scenario run twice must be bit-identical (raw IEEE-754 bits of every sample field).</summary>
        [Theory]
        [InlineData("launch_0_80_flat")]
        [InlineData("brake_80_0_dry_abs_comb@laden40")]
        [InlineData("lane_change_80@laden40")]
        [InlineData("fuzz_flat_wet_laden40")]
        public void SameScenario_Twice_IsBitIdentical(string id)
        {
            var r = Suites.BitIdentical(id);
            _out.WriteLine(r.ToString());
            Assert.True(r.Identical, r.ToString());
        }

        /// <summary>s6.12: fixedDeltaTime 1/50, 1/60, 1/100, 1/120 - metric spread within 5% (WORKING_VALUE, was 5% for 50/100/120).</summary>
        [Theory]
        [InlineData("launch_0_80_flat", "time_to_kmh", 80)]
        [InlineData("brake_80_0_dry", "stop_distance_m", 0)]
        [InlineData("circle_r25_20kmh", "lat_accel_ms2", 0)]
        [InlineData("lane_change_80@laden40", "max_articulation_deg", 0)]
        public void DtSweep_50_60_100_120Hz_Within5Percent(string id, string metric, double arg)
        {
            var s = Suites.DtSweep(id, metric, arg, new[] { 1 / 50.0, 1 / 60.0, 1 / 100.0, 1 / 120.0 });
            _out.WriteLine(s.ToString());
            Assert.All(s.Values, v => Assert.False(double.IsNaN(v)));
            Assert.True(s.MaxRelDev <= 0.05, s.ToString());
        }

        /// <summary>Fuzz scenarios in tests/physics/scenarios/fuzz_*: every invariant check must pass.</summary>
        [Fact]
        public void FuzzScenarios_AllInvariantsHold()
        {
            var fuzz = Scenario.LoadAll(RepoPaths.ScenariosDir).Where(s => s.id.StartsWith("fuzz_")).ToList();
            Assert.True(fuzz.Count >= 8, $"expected >= 8 fuzz scenarios, found {fuzz.Count}");
            foreach (var sc in fuzz)
            {
                var r = ScenarioRunner.Run(sc);
                var sb = new StringBuilder();
                foreach (var c in r.Checks) sb.AppendLine(c.ToString());
                _out.WriteLine($"{sc.id}:\n{sb}");
                Assert.True(r.Passed, $"{sc.id} invariant violated:\n{sb}");
            }
        }

        static RunResult Synthetic(int n, double dt, Func<int, Sample> make)
        {
            var r = new RunResult { Dt = dt, SampleDt = dt, ArticulationLimitDeg = 90 };
            for (int i = 0; i < n; i++) r.Samples.Add(make(i));
            return r;
        }

        [Fact]
        public void Metric_EnergyDrift_UsesKEPlusPE()
        {
            var r = Synthetic(3, 0.01, i => new Sample { T = i * 0.01, KineticEnergy = 100 + 10.0 * i, PotentialEnergy = 1000 + 5.0 * i });
            Assert.Equal(30.0, r.Metric("energy_drift_j"), 9);
            Assert.Equal(1130.0, r.Metric("energy_total_j"), 9);
            Assert.Equal(1130.0, r.Metric("max_energy_j"), 9);
        }

        [Fact]
        public void Metric_FrictionRatio_AirFloor_Nan_ArticulationStop()
        {
            var r = Synthetic(2, 0.01, i => new Sample
            {
                T = i * 0.01, MaxFrictionRatio = i == 0 ? 0.5 : 1.0,
                AirSupply = 10, AirFront = 9, AirRear = 8, AirPark = 7, AirTrailer = 6,
                Articulation = i == 0 ? 80 * MathUtil.Deg2Rad : 95 * MathUtil.Deg2Rad,
            });
            r.NanDetected = true;
            Assert.Equal(1.0, r.Metric("max_tire_friction_ratio"), 12);
            Assert.Equal(6.0, r.Metric("min_air_all_bar"), 12);
            Assert.Equal(1.0, r.Metric("nan_detected"), 12);
            Assert.Equal(5.0, r.Metric("articulation_limit_excess_deg"), 9); // 95 deg vs 90 deg stop
        }

        /// <summary>Cab angular-velocity spectrum: a 2 Hz pitch oscillation must peak at 2 Hz with the right amplitude.</summary>
        [Fact]
        public void Metric_CabSpectrum_FindsDominantFrequency()
        {
            double f = 2.0, amp = 0.01, dt = 0.01;
            int n = 1000;
            var r = Synthetic(n, dt, i => new Sample { T = i * dt, CabPitch = amp * Math.Sin(2 * Math.PI * f * i * dt) });
            double peakHz = r.Metric("cab_spectrum_peak_hz", 0);
            double peakAmp = r.Metric("cab_spectrum_peak_amp_dps", 0);
            _out.WriteLine($"peak {peakHz:F3} Hz, amp {peakAmp:F3} deg/s (expected 2 Hz, {amp * 2 * Math.PI * f * MathUtil.Rad2Deg:F3} deg/s)");
            Assert.InRange(peakHz, 1.9, 2.1);
            Assert.InRange(peakAmp, 0.9 * amp * 2 * Math.PI * f * MathUtil.Rad2Deg, 1.1 * amp * 2 * Math.PI * f * MathUtil.Rad2Deg);
        }

        /// <summary>Seeded fuzz is reproducible: two FuzzDrivers with the same seed emit the same input sequence.</summary>
        [Fact]
        public void FuzzDriver_SameSeed_SameInputs()
        {
            var d = new DriverSpec { type = "fuzz", seed = 4242, holdMinS = 0.3, holdMaxS = 1.0 };
            var a = new FuzzDriver(d); var b = new FuzzDriver(d);
            var sc = Suites.Find("fuzz_flat_dry_laden40");
            var s = ScenarioRunner.Setup(sc, new RunOptions());
            for (int i = 0; i < 500; i++)
            {
                double t = i * 0.01;
                var ia = a.Update(t, 0.01, s);
                var ib = b.Update(t, 0.01, s);
                Assert.Equal(ia.Throttle, ib.Throttle);
                Assert.Equal(ia.Brake, ib.Brake);
                Assert.Equal(ia.Steer, ib.Steer);
                Assert.Equal(ia.Selector, ib.Selector);
                Assert.Equal(ia.RetarderLever, ib.RetarderLever);
                Assert.Equal(ia.ParkingBrake, ib.ParkingBrake);
            }
        }

        /// <summary>Smoke: the seeded kerb fuzz finds no NaN / teleport in a small batch.</summary>
        [Fact]
        public void KerbFuzz_SmallBatch_NoNaNNoTeleport()
        {
            var md = Robustness.KerbFuzz(6, 777);
            _out.WriteLine(md);
            Assert.Contains("NaN runs 0", md);
            Assert.Contains("worst: pos_jump", md);
        }
    }
}
