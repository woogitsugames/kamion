using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using PhysicsRunner.Sim;

namespace PhysicsRunner
{
    /// <summary>
    /// Runs every scenario in tests/physics/scenarios, writes telemetry CSVs and a summary to
    /// artifacts/physics/&lt;timestamp&gt;/.
    /// Usage: dotnet run -c Release --project tools/physics-runner/Runner [-- options]
    ///   --only &lt;id|baseId&gt;   run one scenario (all variants when a base id is given)
    ///   --out &lt;dir&gt;          output folder
    ///   --scenarios &lt;dir&gt;    scenario folder (default tests/physics/scenarios)
    ///   --no-multi           skip the multi-run checks (repeatability, dt / substep sweeps)
    ///   --update-golden      rewrite tests/golden/*.csv from this run (then review the diff!)
    ///   --bench              cost per step of the full 40 t combination (no CSV)
    /// </summary>
    public static class Program
    {
        public static int Main(string[] args)
        {
            CultureInfo.DefaultThreadCurrentCulture = CultureInfo.InvariantCulture;
            CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
            string only = null, outDir = null, scenDir = RepoPaths.ScenariosDir;
            bool multi = true, updateGolden = false, bench = false;
            for (int i = 0; i < args.Length; i++)
            {
                if (args[i] == "--only" && i + 1 < args.Length) only = args[++i];
                else if (args[i] == "--out" && i + 1 < args.Length) outDir = args[++i];
                else if (args[i] == "--scenarios" && i + 1 < args.Length) scenDir = args[++i];
                else if (args[i] == "--no-multi") multi = false;
                else if (args[i] == "--update-golden") updateGolden = true;
                else if (args[i] == "--bench") bench = true;
            }
            if (bench) { Bench(); return 0; }
            // ADR 0149: finger-in-the-loop evidence (touch drag gesture -> column -> physics), before/after CSVs + summary.
            for (int i = 0; i < args.Length; i++)
                if (args[i] == "--touch-evidence")
                    return TouchEvidence.WriteAll(Path.GetFullPath(i + 1 < args.Length ? args[i + 1] : Path.Combine(RepoPaths.Root, "artifacts", "steer-r2", "evidence"), RepoPaths.Root));
            string commit = GitSha();
            outDir ??= Path.Combine(RepoPaths.ArtifactsDir, DateTime.Now.ToString("yyyyMMdd-HHmmss"));
            outDir = Path.GetFullPath(outDir, RepoPaths.Root);
            Directory.CreateDirectory(outDir);
            Console.WriteLine($"physics-runner  commit={commit}  out={outDir}");

            var md = new StringBuilder();
            md.AppendLine($"# Physics validation run {DateTime.Now:yyyy-MM-dd HH:mm}  (commit {commit})");
            md.AppendLine();
            md.AppendLine("| scenario | metric | value | min | max | status | source |");
            md.AppendLine("|---|---|---|---|---|---|---|");
            int failed = 0, run = 0, checks = 0;
            foreach (var sc in Scenario.LoadAll(scenDir))
            {
                if (only != null && sc.id != only && sc.baseId != only) continue;
                var sw = Stopwatch.StartNew();
                var r = ScenarioRunner.Run(sc, new RunOptions { CsvPath = Path.Combine(outDir, sc.id + ".csv"), Commit = commit });
                sw.Stop();
                run++;
                Console.WriteLine($"[{(r.Passed ? "PASS" : "FAIL")}] {sc.id}  ({sw.Elapsed.TotalSeconds:F1}s wall)");
                foreach (var c in r.Checks)
                {
                    checks++;
                    Console.WriteLine("    " + c);
                    md.AppendLine($"| {sc.id} | {c.Spec.metric}{(c.Spec.arg != 0 ? "(" + c.Spec.arg + ")" : "")}{(c.Spec.from != 0 || c.Spec.to != 0 ? $" [{c.Spec.from}..{(c.Spec.to > 0 ? c.Spec.to.ToString() : "end")} s]" : "")} | {c.Value:G4} | {Fmt(c.Spec.min)} | {Fmt(c.Spec.max)} | {(c.Passed ? "PASS" : "**FAIL**")} | {c.Spec.status}: {c.Spec.source} |");
                }
                if (!r.Passed) failed++;
                if (updateGolden && Golden.Ids.Contains(sc.id))
                {
                    Golden.Write(sc.id, Path.Combine(outDir, sc.id + ".csv"));
                    Console.WriteLine($"    golden updated: tests/golden/{sc.id}.csv");
                }
            }

            if (only == null && multi && scenDir == RepoPaths.ScenariosDir)
            {
                md.AppendLine();
                md.AppendLine("## Multi-run checks");
                var rep = Suites.Repeatability("launch_0_80_flat", new[] { 0.0, 37.0, 113.0 },
                    i => Path.Combine(outDir, $"repeatability_run{i + 1}.csv"));
                foreach (var s in rep) { Console.WriteLine("  repeatability " + s); md.AppendLine($"- repeatability {s}"); }
                var sweeps = new List<Suites.SpreadResult>
                {
                    Suites.DtSweep("launch_0_80_flat", "time_to_kmh", 80, new[] { 1 / 50.0, 1 / 100.0, 1 / 120.0 }),
                    Suites.DtSweep("brake_80_0_dry", "stop_distance_m", 0, new[] { 1 / 50.0, 1 / 100.0, 1 / 120.0 }),
                    Suites.DtSweep("circle_r25_20kmh", "lat_accel_ms2", 0, new[] { 1 / 50.0, 1 / 100.0, 1 / 120.0 }),
                    Suites.DtSweep("brake_80_0_dry_abs_comb@laden40", "stop_distance_m", 0, new[] { 1 / 50.0, 1 / 100.0, 1 / 120.0 }),
                    Suites.DtSweep("lane_change_80@laden40", "max_articulation_deg", 0, new[] { 1 / 50.0, 1 / 100.0, 1 / 120.0 }),
                    Suites.DtSweep("launch_flat_comb@laden40", "time_to_kmh", 60, new[] { 1 / 50.0, 1 / 100.0, 1 / 120.0 }),
                    Suites.SubstepSweep("brake_80_0_dry", "stop_distance_m", 0, new[] { 2, 4, 8 }),
                    Suites.SubstepSweep("brake_80_0_dry_abs_comb@laden40", "stop_distance_m", 0, new[] { 2, 4, 8 }),
                };
                foreach (var s in sweeps) { Console.WriteLine("  " + s); md.AppendLine($"- {s}"); }
                var b = Bench();
                md.AppendLine($"- cost: {b}");
            }

            File.WriteAllText(Path.Combine(outDir, "summary.md"), md.ToString());
            Console.WriteLine(failed == 0 ? $"ALL {run} SCENARIOS PASSED ({checks} checks)" : $"{failed} OF {run} SCENARIO(S) FAILED");
            return failed == 0 ? 0 : 1;
        }

        /// <summary>Mean / p99 cost of one fixed step (models + constraint + integration), full 40 t combination, Release.</summary>
        static string Bench()
        {
            var sc = Suites.Find("lane_change_80@laden40");
            var s = ScenarioRunner.Setup(sc, new RunOptions());
            var driver = ScenarioRunner.CreateDriver(sc, s, out _);
            int n = 30000;
            var times = new double[n];
            double t = 0;
            var sw = new Stopwatch();
            for (int i = 0; i < n + 2000; i++)
            {
                var inp = driver.Update(t, 0.01, s);
                sw.Restart();
                s.Combo.Step(0.01, s.Body.State, s.TrailerBody.State, inp, s.Ground);
                s.Body.Integrate(0.01, s.Combo.TractorForce, s.Combo.TractorTorque);
                s.TrailerBody.Integrate(0.01, s.Combo.TrailerForce, s.Combo.TrailerTorque);
                sw.Stop();
                if (i >= 2000) times[i - 2000] = sw.ElapsedTicks * 1e6 / Stopwatch.Frequency;
                t += 0.01;
            }
            Array.Sort(times);
            string r = $"full 40 t combination (10 wheel ends x 15 rays, 4 substeps, fifth wheel 8 it.), desktop Release: mean {times.Average():F1} us/step, p50 {times[n / 2]:F1}, p99 {times[(int)(n * 0.99)]:F1}, max {times[n - 1]:F1} us";
            Console.WriteLine("  bench " + r);
            return r;
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
