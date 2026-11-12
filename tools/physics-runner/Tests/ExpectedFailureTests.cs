using System.IO;
using System.Text;
using PhysicsRunner.Sim;
using Xunit;
using Xunit.Abstractions;

namespace PhysicsRunner.Tests
{
    /// <summary>
    /// Known-failure scenarios (tests/physics/scenarios_expected_fail/*.json, docs/04 s6 requirements the physics
    /// does not meet yet). The console runner and ScenarioTests only scan tests/physics/scenarios, so these do not
    /// break CI; this test asserts each one still FAILS and prints the failing checks plus the JSON's
    /// "expectedFailReason". When the physics is fixed, move the file back to tests/physics/scenarios/ and remove
    /// the reason.
    /// </summary>
    public class ExpectedFailureTests
    {
        readonly ITestOutputHelper _out;
        public ExpectedFailureTests(ITestOutputHelper output) { _out = output; }

        static string Dir => Path.Combine(RepoPaths.Root, "tests", "physics", "scenarios_expected_fail");

        [Fact]
        public void KnownFailures_StillFail_WithReason()
        {
            if (!Directory.Exists(Dir)) return;
            var scenarios = Scenario.LoadAll(Dir);
            if (scenarios.Count == 0) { _out.WriteLine("no known-failure scenarios"); return; }
            foreach (var sc in scenarios)
            {
                var r = ScenarioRunner.Run(sc);
                var sb = new StringBuilder();
                sb.AppendLine($"{sc.id} — expected failure: {sc.expectedFailReason}");
                foreach (var c in r.Checks) sb.AppendLine(c.ToString());
                _out.WriteLine(sb.ToString());
                Assert.False(string.IsNullOrWhiteSpace(sc.expectedFailReason), $"{sc.id}: expected-fail scenario needs expectedFailReason");
                Assert.False(r.Passed, $"{sc.id} unexpectedly passes now — move it back to tests/physics/scenarios/:\n{sb}");
            }
        }
    }
}
