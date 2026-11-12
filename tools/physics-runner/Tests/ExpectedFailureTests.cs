using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using PhysicsRunner.Sim;
using Xunit;
using Xunit.Abstractions;

namespace PhysicsRunner.Tests
{
    /// <summary>
    /// Known-failure scenarios (tests/physics/scenarios_expected_fail/*.json, docs/04 s6 requirements the physics
    /// does not meet yet). The console runner and ScenarioTests only scan tests/physics/scenarios, so these do not
    /// break CI. For every scenario the JSON must list "expectedFailMetrics": this test asserts that exactly those
    /// checks FAIL and all other checks PASS, and prints the failing checks plus the JSON's "expectedFailReason".
    /// When an expected-failure metric starts passing, the test fails with "naprawione? zdejmij expectedFail" —
    /// move the file back to tests/physics/scenarios/ and remove expectedFailReason / expectedFailMetrics.
    /// </summary>
    public class ExpectedFailureTests
    {
        readonly ITestOutputHelper _out;
        public ExpectedFailureTests(ITestOutputHelper output) { _out = output; }

        static string Dir => Path.Combine(RepoPaths.Root, "tests", "physics", "scenarios_expected_fail");

        [Fact]
        public void KnownFailures_FailExactlyTheExpectedMetrics()
        {
            if (!Directory.Exists(Dir)) return;
            var scenarios = Scenario.LoadAll(Dir);
            if (scenarios.Count == 0) { _out.WriteLine("no known-failure scenarios"); return; }
            foreach (var sc in scenarios)
            {
                var r = ScenarioRunner.Run(sc);
                var sb = new StringBuilder();
                sb.AppendLine($"{sc.id} — expected failure: {sc.expectedFailReason}");
                sb.AppendLine($"expectedFailMetrics: [{string.Join(", ", sc.expectedFailMetrics)}]");
                foreach (var c in r.Checks) sb.AppendLine(c.ToString());
                _out.WriteLine(sb.ToString());

                Assert.False(string.IsNullOrWhiteSpace(sc.expectedFailReason), $"{sc.id}: expected-fail scenario needs expectedFailReason");
                Assert.True(sc.expectedFailMetrics.Length > 0, $"{sc.id}: expected-fail scenario needs a non-empty expectedFailMetrics list");

                var expected = new HashSet<string>(sc.expectedFailMetrics);
                foreach (var m in expected)
                    Assert.Contains(r.Checks, c => c.Spec.metric == m);

                var fixedMetrics = string.Join(", ", r.Checks
                    .Where(c => expected.Contains(c.Spec.metric) && c.Passed)
                    .Select(c => c.Spec.metric).Distinct());
                Assert.True(fixedMetrics.Length == 0,
                    $"{sc.id}: naprawione? zdejmij expectedFail — metryki [{fixedMetrics}] już przechodzą, a są na liście expectedFailMetrics (przenieś plik do tests/physics/scenarios/ i usuń expectedFailReason):\n{sb}");

                var strayMetrics = string.Join(", ", r.Checks
                    .Where(c => !expected.Contains(c.Spec.metric) && !c.Passed)
                    .Select(c => c.Spec.metric).Distinct());
                Assert.True(strayMetrics.Length == 0,
                    $"{sc.id}: poza expectedFailMetrics padają też [{strayMetrics}] — to albo regresja, albo brakująca pozycja na liście expectedFailMetrics z uzasadnieniem:\n{sb}");

                var failing = r.Checks.Where(c => expected.Contains(c.Spec.metric) && !c.Passed).ToList();
                Assert.True(failing.Count > 0, $"{sc.id}: żadna z expectedFailMetrics nie pada — zdejmij expectedFail:\n{sb}");
            }
        }
    }
}
