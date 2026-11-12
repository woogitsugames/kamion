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
    /// break CI; this test asserts each one still FAILS and prints the failing checks plus the JSON's
    /// "expectedFailReason". When the physics is fixed, move the file back to tests/physics/scenarios/ and remove
    /// the reason.
    /// </summary>
    public class ExpectedFailureTests
    {
        readonly ITestOutputHelper _out;
        public ExpectedFailureTests(ITestOutputHelper output) { _out = output; }

        static string Dir => Path.Combine(RepoPaths.Root, "tests", "physics", "scenarios_expected_fail");

        public static IEnumerable<object[]> ScenarioIds() =>
            Directory.Exists(Dir)
                ? Scenario.LoadAll(Dir).Select(s => new object[] { s.id })
                : Enumerable.Empty<object[]>();

        [Theory]
        [MemberData(nameof(ScenarioIds))]
        public void KnownFailure_StillFails_WithReason(string id)
        {
            var sc = Scenario.LoadAll(Dir).First(s => s.id == id);
            var r = ScenarioRunner.Run(sc);
            var sb = new StringBuilder();
            sb.AppendLine($"expected failure: {sc.expectedFailReason}");
            foreach (var c in r.Checks) sb.AppendLine(c.ToString());
            _out.WriteLine(sb.ToString());
            Assert.False(string.IsNullOrWhiteSpace(sc.expectedFailReason), $"{id}: expected-fail scenario needs expectedFailReason");
            Assert.False(r.Passed, $"{id} unexpectedly passes now — move it back to tests/physics/scenarios/:\n{sb}");
        }
    }
}
