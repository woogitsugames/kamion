using System;
using System.Collections.Generic;
using Game.Vehicle.Physics;
using PhysicsRunner.Sim;
using Xunit;
using Xunit.Abstractions;

namespace PhysicsRunner.Tests
{
    /// <summary>
    /// ADR 0280: swept-path metrics (swept_outer/inner_radius_m, swept_ring_width_m, swept_fit_rms_m) against
    /// closed-form kinematics, and the geometry what-if overrides (trailerAxlePositionsZ, fifthWheelZ).
    /// </summary>
    public class SweptPathTests
    {
        readonly ITestOutputHelper _out;
        public SweptPathTests(ITestOutputHelper output) { _out = output; }

        /// <summary>Rigid steady-state combination on a clockwise circle (rear axle radius R about centre c).</summary>
        static RunResult Synthetic(double R, double cx, double cz, double lead, double L, bool trailer)
        {
            var sc = new Scenario { combination = trailer ? "laden40" : "solo" };
            var r = new RunResult { Scenario = sc, SampleDt = 0.1 };
            double rk = Math.Sqrt(R * R + lead * lead), ra = Math.Sqrt(rk * rk - L * L);
            for (int i = 0; i < 720; i++)
            {
                double th = i * Math.PI / 360;   // one full lap
                var pos = new Vec3(cx - R * Math.Cos(th), 0, cz + R * Math.Sin(th));
                var fwd = new Vec3(Math.Sin(th), 0, Math.Cos(th));
                var smp = new Sample { T = i * 0.1, Pos = pos, Fwd = fwd, Right = new Vec3(fwd.z, 0, -fwd.x) };
                if (trailer)
                {
                    Vec3 k = pos + fwd * lead;
                    // axle-centre point A: |A - c| = ra, |K - A| = L (right angle at A); pick the one behind the kingpin
                    double ux = (k.x - cx) / rk, uz = (k.z - cz) / rk, phi = Math.Acos(ra / rk);
                    Vec3 best = default; double bestDot = double.MinValue;
                    foreach (double sg in new[] { 1.0, -1.0 })
                    {
                        double c = Math.Cos(sg * phi), s = Math.Sin(sg * phi);
                        var a = new Vec3(cx + ra * (ux * c - uz * s), 0, cz + ra * (ux * s + uz * c));
                        double d = Vec3.Dot(k - a, fwd);
                        if (d > bestDot) { bestDot = d; best = a; }
                    }
                    Vec3 tf = (k - best) / L;
                    smp.HasTrailer = true; smp.Coupled = true;
                    smp.TrailerPos = k; smp.TrailerFwd = tf; smp.TrailerRight = new Vec3(tf.z, 0, -tf.x);
                }
                r.Samples.Add(smp);
            }
            return r;
        }

        /// <summary>Independent reference: densely sampled rectangle outlines (outer / inner distance to the centre).</summary>
        static (double outer, double inner) BruteForce(RunResult r, double cx, double cz)
        {
            var e = r.Scenario.envelope;
            double outer = 0, inner = double.MaxValue;
            void Rect(Vec3 o, Vec3 f, double front, double rear, double hw)
            {
                var rt = new Vec3(f.z, 0, -f.x);
                const int n = 400;
                for (int j = 0; j <= n; j++)
                {
                    double z = rear + (front - rear) * j / n, x = -hw + 2 * hw * j / n;
                    foreach (var p in new[] { o + f * z + rt * hw, o + f * z - rt * hw, o + f * front + rt * x, o + f * rear + rt * x })
                    {
                        double d = Math.Sqrt((p.x - cx) * (p.x - cx) + (p.z - cz) * (p.z - cz));
                        outer = Math.Max(outer, d); inner = Math.Min(inner, d);
                    }
                }
            }
            foreach (var s in r.Samples)
            {
                Rect(s.Pos, s.Fwd, e.tractorFrontZ, e.tractorRearZ, e.tractorHalfWidth);
                if (s.HasTrailer) Rect(s.TrailerPos, s.TrailerFwd, e.trailerFrontZ, e.trailerRearZ, e.trailerHalfWidth);
            }
            return (outer, inner);
        }

        [Fact]
        public void TractorOnly_MatchesClosedForm()
        {
            const double R = 10.0;
            var r = Synthetic(R, 3.0, -2.0, 0.68, 7.70, trailer: false);
            var e = r.Scenario.envelope;
            var fit = Metrics.FitCircle(r.Samples, 0, r.Samples.Count - 1);
            Assert.InRange(fit.cx, 3.0 - 1e-9, 3.0 + 1e-9);
            Assert.InRange(fit.cz, -2.0 - 1e-9, -2.0 + 1e-9);
            Assert.InRange(fit.radius, R - 1e-9, R + 1e-9);
            Assert.True(fit.rms < 1e-9);
            double outer = r.Metric("swept_outer_radius_m"), inner = r.Metric("swept_inner_radius_m");
            double expOuter = Math.Sqrt((R + e.tractorHalfWidth) * (R + e.tractorHalfWidth) + e.tractorFrontZ * e.tractorFrontZ);
            _out.WriteLine($"outer {outer:F6} (closed form {expOuter:F6}), inner {inner:F6} (closed form {R - e.tractorHalfWidth:F6})");
            Assert.Equal(expOuter, outer, 9);
            Assert.Equal(R - e.tractorHalfWidth, inner, 9);
            Assert.Equal(outer - inner, r.Metric("swept_ring_width_m"), 12);
        }

        [Fact]
        public void RigidCombination_MatchesKinematicsAndBruteForce()
        {
            const double R = 10.20, lead = 0.68, L = 7.70;
            var r = Synthetic(R, 0, 0, lead, L, trailer: true);
            var e = r.Scenario.envelope;
            double ra = Math.Sqrt(R * R + lead * lead - L * L);
            double inner = r.Metric("swept_inner_radius_m"), outer = r.Metric("swept_outer_radius_m");
            var bf = BruteForce(r, 0, 0);
            _out.WriteLine($"inner {inner:F6} (kinematic {ra - e.trailerHalfWidth:F6}, brute {bf.inner:F6}); outer {outer:F6} (brute {bf.outer:F6})");
            // trailer side tangent at the axle-centre foot point: inner = sqrt(Rk^2 - L^2) - half width
            Assert.Equal(ra - e.trailerHalfWidth, inner, 6);
            Assert.InRange(outer - bf.outer, -1e-9, 1e-4);   // brute force samples the corners exactly
            Assert.InRange(bf.inner - inner, -1e-9, 2e-3);   // brute-force grid spacing 2.9 cm along the side
        }

        [Fact]
        public void GeometryOverrides_ApplyToARunCopyOnly()
        {
            var sc = Scenario.Load(System.IO.Path.Combine(RepoPaths.ScenariosDir, "ring_96_53_comb_rwb760.json"));
            sc.combination = "laden40";
            sc.overrides.fifthWheelZ = 0.70;
            var defs = ScenarioRunner.ApplyGeometry(ScenarioRunner.Defs, sc);
            Assert.NotSame(ScenarioRunner.Defs, defs);
            var t = defs.Trailers[sc.trailer];
            Assert.Equal(new[] { -6.29, -7.60, -8.91 }, new[] { t.axles[0].positionZ, t.axles[1].positionZ, t.axles[2].positionZ });
            Assert.Equal(0.70, defs.Vehicles[sc.vehicle].fifthWheel.position.z, 12);
            double massZ = 0, prodMassZ = 0;
            foreach (var m in t.massElements) if (m.name == "tridem_axles_wheels_brakes") massZ = m.center.z;
            var prod = ScenarioRunner.Defs.Trailers[sc.trailer];
            foreach (var m in prod.massElements) if (m.name == "tridem_axles_wheels_brakes") prodMassZ = m.center.z;
            Assert.Equal(prodMassZ + 0.10, massZ, 9);          // axle group mass moves with the mean axle position
            // production set untouched
            Assert.Equal(-7.70, prod.axles[1].positionZ, 12);
            Assert.Equal(0.68, ScenarioRunner.Defs.Vehicles[sc.vehicle].fifthWheel.position.z, 12);
        }

        [Fact]
        public void ShorterKingpinToTridem_WidensTheInnerRadius()
        {
            // Same driver radius, only the axle positions differ (7.70 -> 7.60 m): inner radius must grow by roughly
            // dRa/dL = L_eff / Ra ~ 1.1-1.2 cm per cm (ADR 0280 sensitivity), outer unchanged (tractor bumper corner).
            var after = Scenario.Load(System.IO.Path.Combine(RepoPaths.ScenariosDir, "ring_96_53_comb_rwb760.json"));
            after.combination = "laden40"; after.duration = 150;
            var before = Scenario.Load(System.IO.Path.Combine(RepoPaths.ScenariosDir, "ring_96_53_comb_rwb760.json"));
            before.combination = "laden40"; before.duration = 150; before.overrides.trailerAxlePositionsZ = null;
            var ra = ScenarioRunner.Run(after); var rb = ScenarioRunner.Run(before);
            double ia = ra.Metric("swept_inner_radius_m", 0, 100), ib = rb.Metric("swept_inner_radius_m", 0, 100);
            double oa = ra.Metric("swept_outer_radius_m", 0, 100), ob = rb.Metric("swept_outer_radius_m", 0, 100);
            _out.WriteLine($"inner {ib:F4} -> {ia:F4} m, outer {ob:F4} -> {oa:F4} m");
            Assert.InRange((ia - ib) / 0.10, 0.9, 1.4);
            Assert.InRange(Math.Abs(oa - ob), 0, 0.005);
        }
    }
}
