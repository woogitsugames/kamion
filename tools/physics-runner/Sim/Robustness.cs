using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Game.Vehicle.Physics;

namespace PhysicsRunner.Sim
{
    /// <summary>
    /// M34 robustness suite (docs/04 s6.12 / s6.14): soak metrics, bit-determinism, fixed-dt / substep tables,
    /// CPU step profile, cargo-CoG grid, mass x surface matrix, seeded kerb fuzz. Used by the runner's
    /// --robustness mode and by the xUnit robustness tests; emits Markdown tables for the report.
    /// </summary>
    public static class Robustness
    {
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

        static string F(double v) => v.ToString("G6", Inv);

        // ------------------------------------------------------------------ soak
        public static string SoakTable()
        {
            var sb = new StringBuilder();
            sb.AppendLine("## Soak 30 min (docs/04 s6.14)");
            sb.AppendLine();
            sb.AppendLine("| scenario | metric | value |");
            sb.AppendLine("|---|---|---|");
            foreach (var id in new[] { "soak_30min_cycle@laden40", "soak_30min_parked@laden40" })
            {
                var sc = Suites.Find(id);
                var r = ScenarioRunner.Run(sc);
                string[] metrics =
                {
                    "nan_detected", "max_dv_step_ms", "max_pos_jump_m", "max_fifth_wheel_error_mm",
                    "max_articulation_deg", "articulation_limit_excess_deg", "max_tire_friction_ratio",
                    "min_air_all_bar", "max_energy_j",
                };
                foreach (var m in metrics)
                    sb.AppendLine($"| {id} | {m} | {F(r.Metric(m))} |");
                // energy drift over each standstill window of the cycle soak / the parked soak
                if (id.StartsWith("soak_30min_cycle"))
                {
                    double P = sc.driver.cyclePeriod;
                    for (int c = 0; c + 1 < (int)(sc.duration / P); c += 4)
                    {
                        double from = c * P + 0.86 * P, to = (c + 1) * P - 0.05;
                        sb.AppendLine($"| {id} | energy_drift_j [{from:F0}..{to:F0}] s (standstill cycle {c}) | {F(r.Metric("energy_drift_j", 0, from, to))} |");
                    }
                    double lf = (int)(sc.duration / P - 1) * P;
                    sb.AppendLine($"| {id} | energy_drift_j [last standstill {lf + 0.86 * P:F0}..{sc.duration - 0.05:F0}] s | {F(r.Metric("energy_drift_j", 0, lf + 0.86 * P, sc.duration - 0.05))} |");
                }
                else
                {
                    sb.AppendLine($"| {id} | energy_drift_j [5..{sc.duration - 0.05:F0}] s | {F(r.Metric("energy_drift_j", 0, 5, sc.duration - 0.05))} |");
                }
                // cab angular-velocity spectrum over the last 60 s (widmo prędkosci katowej kabiny)
                sb.AppendLine($"| {id} | cab_spectrum_peak_hz (pitch) [last 60 s] | {F(r.Metric("cab_spectrum_peak_hz", 0, sc.duration - 60))} |");
                sb.AppendLine($"| {id} | cab_spectrum_peak_amp_dps (pitch) [last 60 s] | {F(r.Metric("cab_spectrum_peak_amp_dps", 0, sc.duration - 60))} |");
                sb.AppendLine($"| {id} | cab_spectrum_peak_hz (roll) [last 60 s] | {F(r.Metric("cab_spectrum_peak_hz", 1, sc.duration - 60))} |");
                sb.AppendLine($"| {id} | cab_spectrum_peak_amp_dps (roll) [last 60 s] | {F(r.Metric("cab_spectrum_peak_amp_dps", 1, sc.duration - 60))} |");
                sb.AppendLine($"| {id} | max_cab_pitch_rate_dps | {F(r.Metric("max_cab_pitch_rate_dps"))} |");
                sb.AppendLine($"| {id} | max_cab_roll_rate_dps | {F(r.Metric("max_cab_roll_rate_dps"))} |");
                sb.AppendLine($"| {id} | drift_m | {F(r.Metric("drift_m", 0, 5))} |");
                sb.AppendLine($"| {id} | max_speed_after_ms [5..end] | {F(r.Metric("max_speed_after_ms", 0, 5))} |");
            }
            return sb.ToString();
        }

        // ------------------------------------------------------------- determinism
        public static string DeterminismTable(string[] ids)
        {
            var sb = new StringBuilder();
            sb.AppendLine("## Determinism: same scenario run 2x, all sample fields compared as raw IEEE-754 bits");
            sb.AppendLine();
            sb.AppendLine("| scenario | result |");
            sb.AppendLine("|---|---|");
            foreach (var id in ids)
            {
                var r = Suites.BitIdentical(id);
                sb.AppendLine($"| {r.Label} | {(r.Identical ? "BIT-IDENTICAL" : "DIFFERS: " + r.FirstMismatch)} |");
            }
            return sb.ToString();
        }

        // ------------------------------------------------- dt / substep sweep table
        public static string DtTable()
        {
            var sb = new StringBuilder();
            sb.AppendLine("## fixedDeltaTime sweep (substeps scaled to keep ~2.5 ms inner step) + substep sweep (docs/04 s6.12)");
            sb.AppendLine();
            sb.AppendLine("| scenario:metric | 1/50 | 1/60 | 1/100 | 1/120 | max rel dev |");
            sb.AppendLine("|---|---|---|---|---|---|");
            double[] dts = { 1 / 50.0, 1 / 60.0, 1 / 100.0, 1 / 120.0 };
            foreach (var (id, metric, arg) in new[]
            {
                ("launch_0_80_flat", "time_to_kmh", 80.0),
                ("brake_80_0_dry", "stop_distance_m", 0.0),
                ("brake_80_0_dry_abs_comb@laden40", "stop_distance_m", 0.0),
                ("circle_r25_20kmh", "lat_accel_ms2", 0.0),
                ("lane_change_80@laden40", "max_articulation_deg", 0.0),
                ("launch_flat_comb@laden40", "time_to_kmh", 60.0),
            })
            {
                var s = Suites.DtSweep(id, metric, arg, dts);
                sb.AppendLine($"| {id}:{metric}({F(arg)}) | {string.Join(" | ", s.Values.Select(v => F(v)))} | {F(s.MaxRelDev)} |");
            }
            sb.AppendLine();
            sb.AppendLine("| scenario:metric | substeps 1 | 2 | 4 | 8 | max rel dev |");
            sb.AppendLine("|---|---|---|---|---|---|");
            foreach (var (id, metric, arg) in new[]
            {
                ("brake_80_0_dry", "stop_distance_m", 0.0),
                ("brake_80_0_dry_abs_comb@laden40", "stop_distance_m", 0.0),
                ("lane_change_80@laden40", "max_articulation_deg", 0.0),
            })
            {
                var s = Suites.SubstepSweep(id, metric, arg, new[] { 1, 2, 4, 8 });
                sb.AppendLine($"| {id}:{metric}({F(arg)}) | {string.Join(" | ", s.Values.Select(v => F(v)))} | {F(s.MaxRelDev)} |");
            }
            return sb.ToString();
        }

        // ------------------------------------------------------- CPU step profile
        /// <summary>Mean/p50/p99/max us per fixed step (full 40 t combination) for 1/2/4/8 substeps, Release.</summary>
        public static string BenchTable()
        {
            var sb = new StringBuilder();
            sb.AppendLine("## CPU cost per fixed step (dt = 10 ms, full 40 t combination, desktop Release)");
            sb.AppendLine();
            sb.AppendLine("| substeps | mean us | p50 | p99 | max |");
            sb.AppendLine("|---|---|---|---|---|");
            foreach (int sub in new[] { 1, 2, 4, 8 })
            {
                var sc = Suites.Find("lane_change_80@laden40");
                var s = ScenarioRunner.Setup(sc, new RunOptions { Substeps = sub });
                var driver = ScenarioRunner.CreateDriver(sc, s, out _);
                int n = 20000;
                var times = new double[n];
                double t = 0;
                var sw = new Stopwatch();
                for (int i = 0; i < n + 1000; i++)
                {
                    var inp = driver.Update(t, 0.01, s);
                    sw.Restart();
                    s.Combo.Step(0.01, s.Body.State, s.TrailerBody.State, inp, s.Ground);
                    s.Body.Integrate(0.01, s.Combo.TractorForce, s.Combo.TractorTorque);
                    s.TrailerBody.Integrate(0.01, s.Combo.TrailerForce, s.Combo.TrailerTorque);
                    sw.Stop();
                    if (i >= 1000) times[i - 1000] = sw.ElapsedTicks * 1e6 / Stopwatch.Frequency;
                    t += 0.01;
                }
                Array.Sort(times);
                sb.AppendLine($"| {sub} | {F(times.Average())} | {F(times[n / 2])} | {F(times[(int)(n * 0.99)])} | {F(times[n - 1])} |");
            }
            return sb.ToString();
        }

        // ------------------------------------------------------------ CoG 5x5 grid
        /// <summary>docs/04 s6.7: sensitivity to the cargo centre of mass, 5x5 grid of (cogX, cogZ) on a 50 m circle at 35 km/h, laden.</summary>
        public static string CogGrid()
        {
            var sb = new StringBuilder();
            sb.AppendLine("## Cargo CoG grid 5x5 (circle r50 @ 35 km/h, laden40, cogHeight 1.9 m) - docs/04 s6.7");
            sb.AppendLine();
            sb.AppendLine("| cogX m | cogZ m | max_roll_deg | max_trailer_roll_deg | max_lat_accel_ms2 | max_articulation_deg | wheel_lift |");
            sb.AppendLine("|---|---|---|---|---|---|---|");
            double[] xs = { -1.0, -0.5, 0.0, 0.5, 1.0 };
            double[] zs = { -11.0, -7.75, -4.5, -1.25, 1.0 };
            foreach (double z in zs)
                foreach (double x in xs)
                {
                    var sc = Scenario.Load(Path.Combine(RepoPaths.ScenariosDir, "circle_r50_35kmh_comb.json"));
                    sc.variants = Array.Empty<string>();
                    sc.combination = "laden40";
                    sc.cargo.cogX = x; sc.cargo.cogZ = z; sc.cargo.cogHeight = 1.9;
                    var r = ScenarioRunner.Run(sc);
                    sb.AppendLine($"| {F(x)} | {F(z)} | {F(r.Metric("max_abs_roll_deg"))} | {F(r.Metric("max_trailer_roll_deg"))} | {F(r.Metric("max_lat_accel_ms2"))} | {F(r.Metric("max_articulation_deg"))} | {F(r.Metric("wheel_lift"))} |");
                }
            return sb.ToString();
        }

        // ------------------------------------------------------- mass x surface
        /// <summary>Extreme masses (15..44 t gross) x surfaces: 80-0 braking distance with ABS.</summary>
        public static string MassSurfaceTable()
        {
            var sb = new StringBuilder();
            sb.AppendLine("## Gross mass x surface (80-0 km/h, ABS, laden combination)");
            sb.AppendLine();
            double[] massesT = { 15, 20, 30, 40, 44 };
            string[] surfaces = { "dry_asphalt", "wet_asphalt", "concrete", "cobblestone", "gravel" };
            sb.AppendLine("| gross t | " + string.Join(" | ", surfaces.Select(s => s + " stop_m")) + " |");
            sb.AppendLine("|---|" + string.Join("|", surfaces.Select(_ => "---")) + "|");
            var defs = ScenarioRunner.Defs;
            var tractor = defs.CreateModel("tractor_4x2_generic", new SolverSettings());
            double trailerEmpty = MassProperties.Compute(defs.Trailers["curtainsider_tridem_13_6"].massElements).Mass;
            foreach (double mt in massesT)
            {
                var cells = new List<string>();
                foreach (var surf in surfaces)
                {
                    var sc = Scenario.Load(Path.Combine(RepoPaths.ScenariosDir, "brake_80_0_dry_abs_comb.json"));
                    sc.variants = Array.Empty<string>();
                    sc.combination = "laden40";
                    sc.cargo.massKg = Math.Max(0, mt * 1000 - tractor.MassProps.Mass - trailerEmpty);
                    sc.ground.surface = surf;
                    var r = ScenarioRunner.Run(sc);
                    cells.Add(F(r.Metric("stop_distance_m")));
                }
                sb.AppendLine($"| {F(mt)} | " + string.Join(" | ", cells) + " |");
            }
            return sb.ToString();
        }

        // ------------------------------------------------------------- kerb fuzz
        /// <summary>Seeded kerb/bump fuzz (docs/04 s6.11): random kerb heights x speeds, invariant metrics.</summary>
        public static string KerbFuzz(int iterations, long seed)
        {
            var sb = new StringBuilder();
            sb.AppendLine($"## Kerb/bump fuzz: {iterations} seeded runs (seed {seed}), box on the left wheels, 80-0 style straight");
            sb.AppendLine();
            sb.AppendLine("| # | height m | speed km/h | nan | pos_jump m | dv_step m/s | friction ratio | fz ratio | articulation deg | 5th wheel err mm |");
            sb.AppendLine("|---|---|---|---|---|---|---|---|---|---|");
            var rng = new XorShift(seed);
            double worstJump = 0, worstFric = 0, worstDv = 0, worstFz = 0, worstArt = 0;
            int nanCount = 0;
            for (int i = 0; i < iterations; i++)
            {
                double h = 0.02 + 0.28 * rng.Next();
                double v = 10 + 80 * rng.Next();
                var sc = Scenario.Load(Path.Combine(RepoPaths.ScenariosDir, "curb_strike_5cm_50kmh_comb.json"));
                sc.variants = Array.Empty<string>();
                sc.combination = i % 2 == 0 ? "empty" : "laden40";
                sc.ground.boxes[0].height = h;
                sc.ground.boxes[0].minZ = 30; sc.ground.boxes[0].maxZ = 30 + 2 + 4 * rng.Next();
                sc.ground.surface = rng.Next() < 0.5 ? "dry_asphalt" : "wet_asphalt";
                sc.initial.speedKmh = v;
                sc.duration = 6;
                sc.driver.targetKmh = v;
                RunResult r;
                try { r = ScenarioRunner.Run(sc); }
                catch (Exception e) { sb.AppendLine($"| {i} | {F(h)} | {F(v)} | EXCEPTION {e.Message} | | | | | | |"); nanCount++; continue; }
                double nan = r.Metric("nan_detected"), jump = r.Metric("max_pos_jump_m"), dv = r.Metric("max_dv_step_ms"),
                    fric = r.Metric("max_tire_friction_ratio"), fz = r.Metric("max_fz_ratio"),
                    art = r.Metric("max_articulation_deg"), fw = r.Metric("max_fifth_wheel_error_mm");
                if (nan > 0) nanCount++;
                worstJump = Math.Max(worstJump, jump); worstFric = Math.Max(worstFric, fric);
                worstDv = Math.Max(worstDv, dv); worstFz = Math.Max(worstFz, fz); worstArt = Math.Max(worstArt, art);
                sb.AppendLine($"| {i} | {F(h)} | {F(v)} | {F(nan)} | {F(jump)} | {F(dv)} | {F(fric)} | {F(fz)} | {F(art)} | {F(fw)} |");
            }
            sb.AppendLine();
            sb.AppendLine($"worst: pos_jump {F(worstJump)} m, dv_step {F(worstDv)} m/s, friction ratio {F(worstFric)}, fz ratio {F(worstFz)}, articulation {F(worstArt)} deg, NaN runs {nanCount}");
            return sb.ToString();
        }

        /// <summary>Runs the whole robustness suite and returns the Markdown report body.</summary>
        public static string RunAll(int kerbIterations = 40, long kerbSeed = 20261113)
        {
            var sb = new StringBuilder();
            sb.AppendLine("# Physics robustness (M34) - docs/04 s6.12 / s6.14");
            sb.AppendLine();
            sb.AppendLine($"generated {DateTime.Now:yyyy-MM-dd HH:mm} UTC, commit {GitSha()}");
            sb.AppendLine();
            sb.Append(DeterminismTable(new[]
            {
                "launch_0_80_flat", "brake_80_0_dry_abs_comb@laden40", "lane_change_80@laden40",
                "circle_r25_20kmh", "slalom_70_comb@laden40", "jackknife_wet_curve_abs_100@laden40",
            }));
            sb.AppendLine();
            sb.Append(DtTable());
            sb.AppendLine();
            sb.Append(SoakTable());
            sb.AppendLine();
            sb.Append(BenchTable());
            sb.AppendLine();
            sb.Append(CogGrid());
            sb.AppendLine();
            sb.Append(MassSurfaceTable());
            sb.AppendLine();
            sb.Append(KerbFuzz(kerbIterations, kerbSeed));
            return sb.ToString();
        }

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
