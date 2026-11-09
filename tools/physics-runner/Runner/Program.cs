using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Text;
using PhysicsRunner.Sim;

namespace PhysicsRunner
{
    /// <summary>
    /// Runs every scenario in tests/physics/scenarios, writes telemetry CSVs and a summary to
    /// artifacts/physics/&lt;timestamp&gt;/. Usage: dotnet run --project tools/physics-runner/Runner [-- --only id] [--out dir]
    /// </summary>
    public static class Program
    {
        public static int Main(string[] args)
        {
            CultureInfo.DefaultThreadCurrentCulture = CultureInfo.InvariantCulture;
            CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
            string only = null, outDir = null;
            for (int i = 0; i < args.Length; i++)
            {
                if (args[i] == "--only" && i + 1 < args.Length) only = args[++i];
                else if (args[i] == "--out" && i + 1 < args.Length) outDir = args[++i];
            }
            string commit = GitSha();
            outDir ??= Path.Combine(RepoPaths.ArtifactsDir, DateTime.Now.ToString("yyyyMMdd-HHmmss"));
            Directory.CreateDirectory(outDir);
            Console.WriteLine($"physics-runner  commit={commit}  out={outDir}");

            var md = new StringBuilder();
            md.AppendLine($"# Physics validation run {DateTime.Now:yyyy-MM-dd HH:mm}  (commit {commit})");
            md.AppendLine();
            md.AppendLine("| scenario | metric | value | min | max | status | source |");
            md.AppendLine("|---|---|---|---|---|---|---|");
            int failed = 0;
            foreach (var sc in Scenario.LoadAll(RepoPaths.ScenariosDir))
            {
                if (only != null && sc.id != only) continue;
                var sw = Stopwatch.StartNew();
                var r = ScenarioRunner.Run(sc, new RunOptions { CsvPath = Path.Combine(outDir, sc.id + ".csv"), Commit = commit });
                sw.Stop();
                Console.WriteLine($"[{(r.Passed ? "PASS" : "FAIL")}] {sc.id}  ({sw.Elapsed.TotalSeconds:F1}s wall, {r.MeanStepMicros:F1} us/step)");
                foreach (var c in r.Checks)
                {
                    Console.WriteLine("    " + c);
                    md.AppendLine($"| {sc.id} | {c.Spec.metric}{(c.Spec.arg != 0 ? "(" + c.Spec.arg + ")" : "")} | {c.Value:G4} | {Fmt(c.Spec.min)} | {Fmt(c.Spec.max)} | {(c.Passed ? "PASS" : "**FAIL**")} | {c.Spec.status}: {c.Spec.source} |");
                }
                if (!r.Passed) failed++;
            }

            if (only == null)
            {
                md.AppendLine();
                md.AppendLine("## Multi-run checks");
                var rep = Suites.Repeatability("launch_0_80_flat", new[] { 0.0, 37.0, 113.0 },
                    i => Path.Combine(outDir, $"repeatability_run{i + 1}.csv"));
                foreach (var s in rep) { Console.WriteLine("  repeatability " + s); md.AppendLine($"- repeatability {s}"); }
                var dtA = Suites.DtSweep("launch_0_80_flat", "time_to_kmh", 80, new[] { 1 / 50.0, 1 / 100.0, 1 / 120.0 });
                var dtB = Suites.DtSweep("brake_80_0_dry", "stop_distance_m", 0, new[] { 1 / 50.0, 1 / 100.0, 1 / 120.0 });
                var dtC = Suites.DtSweep("circle_r25_20kmh", "lat_accel_ms2", 0, new[] { 1 / 50.0, 1 / 100.0, 1 / 120.0 });
                var subA = Suites.SubstepSweep("brake_80_0_dry", "stop_distance_m", 0, new[] { 2, 4, 8 });
                foreach (var s in new[] { dtA, dtB, dtC, subA }) { Console.WriteLine("  " + s); md.AppendLine($"- {s}"); }
            }

            File.WriteAllText(Path.Combine(outDir, "summary.md"), md.ToString());
            Console.WriteLine(failed == 0 ? "ALL SCENARIOS PASSED" : $"{failed} SCENARIO(S) FAILED");
            return failed == 0 ? 0 : 1;
        }

        static string Fmt(double? v) => v.HasValue ? v.Value.ToString("G4") : "";

        static string GitSha()
        {
            try
            {
                var psi = new ProcessStartInfo("git", "rev-parse --short HEAD")
                {
                    RedirectStandardOutput = true, UseShellExecute = false, WorkingDirectory = RepoPaths.Root,
                };
                using var p = Process.Start(psi);
                string s = p!.StandardOutput.ReadToEnd().Trim();
                p.WaitForExit();
                return string.IsNullOrEmpty(s) ? "unknown" : s;
            }
            catch { return "unknown"; }
        }
    }
}
