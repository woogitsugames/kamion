using System;
using Game.Vehicle.Physics;
using PhysicsRunner.Sim;
using Xunit;
using Xunit.Abstractions;

namespace PhysicsRunner.Tests
{
    /// <summary>
    /// ADR 0149: the game's touch chain (drag gesture -> SteeringColumn, same sources as Unity) with the physics core.
    /// Before = ADR 0135 gain curve (dragLatAccelMatchKmh 0), after = shipped steering_feel.json.
    /// </summary>
    public class TouchSteeringTests
    {
        readonly ITestOutputHelper _out;
        public TouchSteeringTests(ITestOutputHelper output) { _out = output; }

        static SimContext Ctx()
        {
            var probe = TouchEvidence.Replay(35, 0);
            probe.baseId = probe.id; probe.variant = probe.combination;
            return ScenarioRunner.Setup(probe, new RunOptions());
        }

        static double LatAccelPerMm(SimContext ctx, double kmh, double match)
        {
            var st = ctx.Tractor.Steering;
            double wb = ctx.Tractor.Def.axles[0].positionZ - ctx.Tractor.Def.axles[1].positionZ, v = kmh / 3.6;
            return TouchEvidence.CabDegPerMm(kmh, match, ctx) / st.Def.steeringRatio * MathUtil.Deg2Rad * v * v / wb;
        }

        [Fact]
        public void GainCurve_UnchangedBelow24_CappedToThe60KmhLateralAccelAbove()
        {
            var ctx = Ctx();
            foreach (double kmh in new[] { 5.0, 15.0, 20.0, 60.0 })
                Assert.Equal(TouchEvidence.CabDegPerMm(kmh, 0, ctx), TouchEvidence.CabDegPerMm(kmh, -1, ctx), 3);
            try
            {
                TouchEvidence.CapAbove = 0; // ADR 0149 r2: fixed 5 deg/mm from 60 km/h
                foreach (double kmh in new[] { 70.0, 80.0, 90.0 })
                    Assert.Equal(5.0, TouchEvidence.CabDegPerMm(kmh, -1, ctx), 2);
            }
            finally { TouchEvidence.CapAbove = -1; }
            double ref60 = LatAccelPerMm(ctx, 60, -1);
            for (double kmh = 20; kmh <= 90; kmh += 2.5)
            {
                double a = LatAccelPerMm(ctx, kmh, -1);
                _out.WriteLine($"{kmh,5:F1} km/h: before {TouchEvidence.CabDegPerMm(kmh, 0, ctx),6:F2} after {TouchEvidence.CabDegPerMm(kmh, -1, ctx),6:F2} cab deg/mm, a_y/mm after {a:F3}");
                Assert.True(a <= ref60 * 1.001, $"{kmh} km/h: {a:F3} > {ref60:F3}");
                Assert.True(TouchEvidence.CabDegPerMm(kmh, -1, ctx) <= TouchEvidence.CabDegPerMm(kmh, 0, ctx) + 1e-4);
            }
            // Owner's video speed: 35 km/h was 23.5 cab deg/mm (1.6x the 60 km/h lateral acceleration per mm).
            Assert.InRange(TouchEvidence.CabDegPerMm(35, 0, ctx), 23.0, 24.0);
            Assert.InRange(TouchEvidence.CabDegPerMm(35, -1, ctx), 14.5, 15.0);
        }

        [Fact]
        public void Replay35_OwnersThumbFlick_TurnsTheCombinationLess()
        {
            var b = TouchEvidence.Measure("b", TouchEvidence.Replay(35, 0), TouchEvidence.Run(TouchEvidence.Replay(35, 0)));
            var a = TouchEvidence.Measure("a", TouchEvidence.Replay(35, -1), TouchEvidence.Run(TouchEvidence.Replay(35, -1)));
            _out.WriteLine($"road wheel {b.PeakRoadWheelDeg:F2} -> {a.PeakRoadWheelDeg:F2} deg, heading at 5 s {b.HeadingAt5s:F2} -> {a.HeadingAt5s:F2} deg, lateral at 5 s {b.LatAt5s:F2} -> {a.LatAt5s:F2} m");
            Assert.True(a.PeakRoadWheelDeg < 0.7 * b.PeakRoadWheelDeg);
            Assert.True(Math.Abs(a.HeadingAt5s) < 0.7 * Math.Abs(b.HeadingAt5s));
            Assert.Equal(0, a.WheelLift);
        }

        /// <summary>Diagnostic (prints only): yaw rate and articulation left after the released flick, per combination.</summary>
        [Fact]
        public void Replay35_ResidualYawAfterRelease_Diagnostic()
        {
            foreach (var combo in new[] { "solo", "empty", "laden40" })
            {
                var sc = TouchEvidence.Replay(35, -1, combo); sc.duration = 20;
                var tr = TouchEvidence.Run(sc);
                int n = tr.T.Count;
                _out.WriteLine($"{combo}: t=8 s yaw {tr.YawRateDps[n * 8 / 20]:F3} deg/s artic {tr.Artic[n * 8 / 20]:F3}; t=20 s yaw {tr.YawRateDps[n - 1]:F3} deg/s artic {tr.Artic[n - 1]:F3} road wheel {tr.RoadWheelDeg[n - 1]:F4}");
            }
        }

        [Fact]
        public void Residual_PlateFrictionSweep_Diagnostic()
        {
            foreach (double mu in new[] { 0.0, 0.25, 0.5, 1.0, 2.0, 4.0 })
            {
                double keep = 0; FifthWheelDefinition def = null;
                var sc = TouchEvidence.Replay(35, -1, "laden40"); sc.duration = 20;
                try
                {
                    var tr = TouchEvidence.Run(sc, s => { def = s.Combo.FifthWheel.Def; keep = def.plateFrictionCreepRateDegS; def.plateFrictionCreepRateDegS = mu; });
                    int n = tr.T.Count;
                    _out.WriteLine($"creep {mu} deg/s: t=5 artic {tr.Artic[n / 4]:F3} yaw {tr.YawRateDps[n / 4]:F3}; t=10 artic {tr.Artic[n / 2]:F3} yaw {tr.YawRateDps[n / 2]:F3}; t=20 artic {tr.Artic[n - 1]:F3} yaw {tr.YawRateDps[n - 1]:F3}");
                }
                finally { if (def != null) def.plateFrictionCreepRateDegS = keep; }
            }
        }

        [Fact]
        public void LaneChange35_ThumbGain4_WeavedBefore_SettlesAfter()
        {
            var sb = TouchEvidence.LaneChange(35, 4, 0); sb.duration = 30;
            var sa = TouchEvidence.LaneChange(35, 4, -1); sa.duration = 30;
            double ib = TouchEvidence.OscillationIndex(TouchEvidence.Run(sb));
            double ia = TouchEvidence.OscillationIndex(TouchEvidence.Run(sa));
            _out.WriteLine($"PIO index (yaw-rate weave RMS, last 8 s): before {ib:F2} deg/s, after {ia:F3} deg/s");
            Assert.True(ib > TouchEvidence.PioThresholdDps, "the ADR 0135 curve must reproduce the weave seen in the video");
            Assert.True(ia < TouchEvidence.PioThresholdDps);
        }

        [Fact]
        public void PioOnset_NoWorseAnywhere_AndAtLeast5MmPerMFrom30To50()
        {
            foreach (double kmh in new[] { 20.0, 30.0, 35.0, 40.0, 50.0, 60.0 })
            {
                double gb = TouchEvidence.PioOnsetGain(kmh, 0), ga = TouchEvidence.PioOnsetGain(kmh, -1);
                _out.WriteLine($"{kmh} km/h: PIO onset thumb gain {gb} -> {ga} mm/m");
                Assert.True(ga >= gb);
                if (kmh >= 30 && kmh <= 50) Assert.True(ga >= 5, $"{kmh} km/h: {ga}");
            }
        }
    }
}
