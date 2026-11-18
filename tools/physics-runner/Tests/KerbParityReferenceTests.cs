using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using PhysicsRunner.Sim;
using Xunit;
using Xunit.Abstractions;

namespace PhysicsRunner.Tests
{
    /// <summary>
    /// The Unity PlayMode test KerbStrikeParityTests (game/Assets/_Project/Tests/PlayMode) compares the Unity adapter with
    /// runner reference numbers written into the test as constants. Those constants went stale once (ADR 0228: the
    /// bump-stop hysteresis changed the kerb strike, nobody re-ran the runner; integration int-h3-s23). This test runs the
    /// same scenarios with the same metrics and the same 6 s window as the Unity test and fails when a constant no longer
    /// matches the runner (rounding to 0.01 only, no tolerance) — so a physics change has to update the parity reference
    /// in the same commit. Metrics: tractor Fz / static, longest single-wheel unload (tractor, all wheels), peak tractor
    /// body pitch asin(fwd.y) (nose up +).
    /// </summary>
    public class KerbParityReferenceTests
    {
        readonly ITestOutputHelper _out;
        public KerbParityReferenceTests(ITestOutputHelper output) { _out = output; }

        const double Window = 6.0; // KerbStrikeParityTests.Run(..., seconds: 6.0, ...)
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

        static string UnityTestSource =>
            File.ReadAllText(Path.Combine(RepoPaths.Root, "game", "Assets", "_Project", "Tests", "PlayMode", "KerbStrikeParityTests.cs"));

        static (double fz, double tractor, double all, double pitch, double pen) Measure(string id, bool bodyContact = true)
        {
            var r = ScenarioRunner.Run(Suites.Find(id), new RunOptions { DisableBodyContact = !bodyContact });
            return (Metrics.Compute(r, "max_fz_ratio", 0, 0, Window),
                    Metrics.Compute(r, "max_wheel_airtime_s", 1, 0, Window),
                    Metrics.Compute(r, "max_wheel_airtime_s", 0, 0, Window),
                    Metrics.Compute(r, "max_pitch_deg", 0, 0, Window),
                    Metrics.Compute(r, "max_body_penetration_m", 0, 0, Window));
        }

        void AssertRef(string what, double expected, double runner)
        {
            _out.WriteLine(string.Format(Inv, "{0}: Unity-test constant {1:F2}, runner {2:F4}", what, expected, runner));
            Assert.True(Math.Abs(expected - runner) <= 0.0051,
                string.Format(Inv, "{0}: KerbStrikeParityTests constant {1:F2} != runner {2:F4} (update the constant from this run)", what, expected, runner));
        }

        [Theory]
        [InlineData("Empty", "curb_strike_14cm_50kmh_comb@empty")]
        [InlineData("Gross40t", "curb_strike_14cm_50kmh_comb@laden40")]
        public void KerbStrike14cm_UnityReference_MatchesRunner(string preset, string id)
        {
            var src = UnityTestSource;
            var rx = new Regex(@"\[TestCase\(CargoPreset\." + preset + @", KerbKind\.(\w+), ([\d.]+), ([\d.]+), ([\d.]+), ([\d.]+),");
            var cases = rx.Matches(src).Cast<Match>().ToList();
            Assert.Equal(2, cases.Count); // Box and Mesh
            // Box case: body colliders may touch the kerb in both Unity and the runner; Unity asserts 0 body contacts,
            // so the runner must not have any either (then the metrics do not depend on the body contact).
            var m = Measure(id);
            _out.WriteLine(string.Format(Inv, "{0}: Fz/static {1:F4}, tractor {2:F2} s, all {3:F2} s, pitch max {4:F4} deg, body pen {5:F4} m", id, m.fz, m.tractor, m.all, m.pitch, m.pen));
            Assert.Equal(0.0, m.pen);
            foreach (var c in cases)
            {
                double P(int g) => double.Parse(c.Groups[g].Value, Inv);
                string k = preset + " " + c.Groups[1].Value;
                AssertRef(k + " Fz/static", P(2), m.fz);
                AssertRef(k + " tractor unload", P(3), m.tractor);
                AssertRef(k + " all-wheel unload", P(4), m.all);
                AssertRef(k + " pitch peak", P(5), m.pitch);
            }
        }

        [Fact]
        public void KerbStep27cm_UnityReference_MatchesRunner()
        {
            var src = UnityTestSource;
            double C(string name)
            {
                var mm = Regex.Match(src, @"\b" + name + @" = ([\d.]+)[,;]");
                Assert.True(mm.Success, name + " not found in KerbStrikeParityTests.cs");
                return double.Parse(mm.Groups[1].Value, Inv);
            }
            // Unity runs this case on a MeshCollider on the WorldKerb layer: wheel rays only, the body colliders never
            // touch the step. The committed runner scenario has the bumper strike on (ADR 0165, D58), so the parity
            // reference is the same scenario without body contact. Both are printed.
            var on = Measure("kerb_step_27cm_42kmh_comb@laden40", true);
            var m = Measure("kerb_step_27cm_42kmh_comb@laden40", false);
            _out.WriteLine(string.Format(Inv, "kerb_step_27cm_42kmh_comb@laden40 body contact ON: Fz/static {0:F4}, tractor {1:F2} s, all {2:F2} s, pitch max {3:F4} deg, body pen {4:F4} m", on.fz, on.tractor, on.all, on.pitch, on.pen));
            _out.WriteLine(string.Format(Inv, "kerb_step_27cm_42kmh_comb@laden40 body contact OFF (Unity mesh parity): Fz/static {0:F4}, tractor {1:F2} s, all {2:F2} s, pitch max {3:F4} deg", m.fz, m.tractor, m.all, m.pitch));
            AssertRef("27 cm Fz/static", C("Step27Fz"), m.fz);
            AssertRef("27 cm tractor unload", C("Step27Tractor"), m.tractor);
            AssertRef("27 cm pitch peak", C("Step27Pitch"), m.pitch);
        }
    }
}
