using System;
using Game.Vehicle.Physics;
using PhysicsRunner.Sim;
using Xunit;
using Xunit.Abstractions;

namespace PhysicsRunner.Tests
{
    /// <summary>
    /// ADR 0195: the game's straight-run autopilot (StraightRunPilot, autopilot=straight080) on the real vehicle model.
    /// Gate 1 repeatability 0-80 x3 within +/-3 %, its online results equal the runner metrics, fixed-step independence.
    /// </summary>
    public class StraightRunTests
    {
        readonly ITestOutputHelper _out;
        public StraightRunTests(ITestOutputHelper output) { _out = output; }

        [Fact]
        public void Solo_0_80_IsRepeatable_Within3Percent()
        {
            foreach (var s in Suites.Repeatability("straight_0_80_0@solo", new[] { 0.0, 37.0, 113.0 }))
            {
                _out.WriteLine(s.ToString());
                Assert.All(s.Values, v => Assert.False(double.IsNaN(v)));
                Assert.True(s.MaxRelDev <= 0.03, s.ToString());
            }
        }

        [Theory]
        [InlineData("straight_0_80_0@solo")]
        [InlineData("straight_0_80_0@empty")]
        [InlineData("straight_0_80_0@laden40")]
        public void PilotOnlineResults_MatchRunnerMetrics(string id)
        {
            var r = ScenarioRunner.Run(Suites.Find(id));
            var p = ((StraightRunDriver)r.Driver).Pilot;
            var q = p.Result;
            _out.WriteLine($"{id}: t60 {q.TimeTo60:F2} t80 {q.TimeTo80:F2} s80 {q.DistanceTo80:F1} hold {q.HoldSpeedMean:F2}+-{q.HoldSpeedStd:F2} " +
                           $"vb {q.BrakeSpeedKmh:F2} stop {q.StopDistance:F2} m {q.StopTime:F2} s mfdd {q.Mfdd:F2} maxdec {q.MaxDecel:F2} lat {q.MaxLateralDeviation:F4}");
            Assert.True(q.Complete, "run reached the stop");
            Assert.Equal(StraightRunPhase.Stopped, p.Phase);
            Assert.InRange(q.TimeTo60, r.Metric("time_to_kmh", 60) - 0.025, r.Metric("time_to_kmh", 60) + 0.025);
            Assert.InRange(q.TimeTo80, r.Metric("time_to_kmh", 80) - 0.025, r.Metric("time_to_kmh", 80) + 0.025);
            Assert.InRange(q.StopDistance, r.Metric("stop_distance_m") - 0.3, r.Metric("stop_distance_m") + 0.3);
            Assert.InRange(q.Mfdd, r.Metric("mfdd_ms2") - 0.15, r.Metric("mfdd_ms2") + 0.15);
            Assert.InRange(q.BrakeSpeedKmh, 78.5, 81.5);
            Assert.InRange(q.HoldSpeedStd, 0, 1.0);
            Assert.InRange(q.MaxDecel, 5.0, 9.0);
        }

        [Fact]
        public void DtVariation_IsConsistent()
        {
            foreach (var (metric, arg) in new[] { ("time_to_kmh", 80.0), ("stop_distance_m", 0.0) })
            {
                var s = Suites.DtSweep("straight_0_80_0@solo", metric, arg, new[] { 1 / 50.0, 1 / 100.0, 1 / 120.0 });
                _out.WriteLine(s.ToString());
                Assert.All(s.Values, v => Assert.False(double.IsNaN(v)));
                Assert.True(s.MaxRelDev <= 0.05, s.ToString());
            }
        }
    }
}
