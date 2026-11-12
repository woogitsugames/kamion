using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using Game.Vehicle.Physics;
using PhysicsRunner.Sim;
using Xunit;
using Xunit.Abstractions;

namespace PhysicsRunner.Tests
{
    /// <summary>
    /// Comparison runs for docs/proposals/PHYSICS-PARAMS-2026-11-12-mistral.md: the production definition
    /// JSONs are loaded, mutated IN MEMORY per variant (test data only — no production file is changed), and
    /// the same scenarios are re-run with each variant. Results go to the test output and to
    /// artifacts/physics/param-comparison-2026-11-12/summary.md (picked up by CI as a physics-results artifact).
    /// </summary>
    public class ParamComparisonTests
    {
        readonly ITestOutputHelper _out;
        public ParamComparisonTests(ITestOutputHelper output) { _out = output; }

        public sealed class Variant
        {
            public string Id = "";
            public string Label = "";
            public Action<DefinitionSet> Mutate;
        }

        public static Variant[] Variants() => new[]
        {
            new Variant { Id = "current", Label = "current (produkcyjne JSON-y)", Mutate = d => { } },
            new Variant { Id = "p1", Label = "P1: skok zawieszenia naczepy 0.20 -> 0.15 m", Mutate = d =>
            {
                foreach (var a in d.Trailers["curtainsider_tridem_13_6"].axles) a.suspension.travel = 0.15;
            } },
            new Variant { Id = "p3", Label = "P3: lowPressureWarningBar 5.5 -> 6.5 bar", Mutate = d =>
            {
                d.Vehicles["tractor_4x2_generic"].air.lowPressureWarningBar = 6.5;
            } },
            new Variant { Id = "p4", Label = "P4: promien opony 315/80 R22.5 0.510 -> 0.546 m (srednica 1092 mm)", Mutate = d =>
            {
                d.Tires["tire_315_80_r22_5"].radius = 0.546;
            } },
            new Variant { Id = "p5", Label = "P5: clutchMaxTorque 4000 -> 3400 Nm", Mutate = d =>
            {
                d.Gearboxes["amt12_od_traxon_class"].clutchMaxTorque = 3400;
            } },
            new Variant { Id = "p10", Label = "P10: maxLaunchGear 4 -> 2", Mutate = d =>
            {
                d.Gearboxes["amt12_od_traxon_class"].maxLaunchGear = 2;
            } },
        };

        sealed class RunDef
        {
            public string Id = "";
            public string Label = "";
            public Func<Scenario> Make;
            public (string metric, double arg, string unit)[] Metrics = Array.Empty<(string, double, string)>();
        }

        static Scenario Clone(Scenario s, string id, string combination = null, double? duration = null, double? speedKmh = null)
        {
            var c = JsonSerializer.Deserialize<Scenario>(JsonSerializer.Serialize(s, DefinitionSet.Json), DefinitionSet.Json);
            c.id = id;
            if (combination != null) { c.combination = combination; c.variant = combination; }
            if (duration.HasValue) c.duration = duration.Value;
            if (speedKmh.HasValue) c.initial.speedKmh = speedKmh.Value;
            return c;
        }

        static RunDef[] Runs() => new[]
        {
            new RunDef { Id = "launch@cargo24", Label = "0-50/0-80 km/h, 24 t, płasko",
                Make = () => Clone(Suites.Find("launch_flat_comb@empty"), "cmp_launch_cargo24", "cargo24", 70),
                Metrics = new[] { ("time_to_kmh", 50.0, "s"), ("time_to_kmh", 80.0, "s"), ("shift_count", 0.0, "-") } },
            new RunDef { Id = "launch@laden40", Label = "0-50/0-80 km/h, 40 t, płasko",
                Make = () => Suites.Find("launch_flat_comb@laden40"),
                Metrics = new[] { ("time_to_kmh", 50.0, "s"), ("time_to_kmh", 80.0, "s"), ("shift_count", 0.0, "-"), ("max_shift_eye_pitch_swing_deg", 0.0, "deg") } },
            new RunDef { Id = "launch6pct@laden40", Label = "ruszanie 6% pod górę, 40 t (sprzęgło)",
                Make = () => Suites.Find("launch_6pct_uphill_comb@laden40"),
                Metrics = new[] { ("time_to_kmh", 30.0, "s"), ("max_clutch_temp_c", 0.0, "°C"), ("stalled", 0.0, "0/1"), ("shift_count", 0.0, "-") } },
            new RunDef { Id = "brake80@solo", Label = "hamowanie 80-0 suche, solo",
                Make = () => Suites.Find("brake_80_0_dry"),
                Metrics = new[] { ("stop_distance_m", 0.0, "m"), ("mfdd_ms2", 0.0, "m/s²"), ("max_cab_pitch_deg", 0.0, "deg") } },
            new RunDef { Id = "brake80@laden40", Label = "hamowanie 80-0 suche ABS, 40 t",
                Make = () => Suites.Find("brake_80_0_dry_abs_comb@laden40"),
                Metrics = new[] { ("stop_distance_m", 0.0, "m"), ("mfdd_ms2", 0.0, "m/s²"), ("max_articulation_deg", 0.0, "deg"), ("max_cab_pitch_deg", 0.0, "deg") } },
            new RunDef { Id = "brake50@laden40", Label = "hamowanie 50-0 suche ABS, 40 t",
                Make = () => Clone(Suites.Find("brake_80_0_dry_abs_comb@laden40"), "cmp_brake_50_laden40", null, 12, 50),
                Metrics = new[] { ("stop_distance_m", 0.0, "m"), ("mfdd_ms2", 0.0, "m/s²") } },
            new RunDef { Id = "lane80@laden40", Label = "zmiana pasa 80 km/h, 40 t",
                Make = () => Suites.Find("lane_change_80@laden40"),
                Metrics = new[] { ("rearward_amplification", 0.0, "-"), ("max_articulation_deg", 0.0, "deg") } },
            new RunDef { Id = "bump@laden40", Label = "próg 7 cm @15 km/h, 40 t (kabina/zawieszenie)",
                Make = () => Suites.Find("speed_bump_comb@laden40"),
                Metrics = new[] { ("max_cab_heave_mm", 0.0, "mm"), ("max_cab_pitch_deg", 0.0, "deg"), ("max_wheel_airtime_s", 0.0, "s") } },
            new RunDef { Id = "curb_left@laden40", Label = "krawężnik 15 cm lewą stroną, 40 t (skok zawieszenia naczepy)",
                Make = () => Suites.Find("curb_15cm_left_comb@laden40"),
                Metrics = new[] { ("max_wheel_airtime_s", 0.0, "s"), ("max_trailer_roll_deg", 0.0, "deg"), ("max_fz_ratio", 0.0, "-") } },
            new RunDef { Id = "leak@laden40", Label = "wyciek obwodu tylnego (ostrzeżenie niskiego ciśnienia)",
                Make = () => Suites.Find("air_leak_rear_circuit@laden40"),
                Metrics = new[] { ("time_low_air_warning", 0.0, "s"), ("min_air_service_bar", 0.0, "bar") } },
        };

        [Fact]
        public void PhysicsParams_Comparison_2026_11_12()
        {
            var variants = Variants();
            var runs = Runs();
            var sb = new StringBuilder();
            sb.AppendLine("# Porównanie parametrów fizyki — 2026-11-12 (mistral/8-physics-params)");
            sb.AppendLine();
            sb.AppendLine($"Warianty = produkcyjne JSON-y zmutowane w pamięci (tylko dane testu). Scenariusze z `tests/physics/scenarios`, model z `game/Assets/_Project/Vehicle/Physics`.");
            sb.AppendLine();
            var header = "| Bieg | Metryka | Jedn. | " + string.Join(" | ", variants.Select(v => v.Id)) + " |";
            sb.AppendLine(header);
            sb.AppendLine("|" + string.Join("|", Enumerable.Repeat("---", variants.Length + 3)) + "|");
            var values = new Dictionary<string, double[]>(); // runId|metric|arg -> per-variant value
            foreach (var run in runs)
            {
                foreach (var (metric, arg, unit) in run.Metrics)
                {
                    var vals = new double[variants.Length];
                    for (int i = 0; i < variants.Length; i++)
                    {
                        var defs = DefinitionSet.LoadDirectory(RepoPaths.DefinitionsDir);
                        variants[i].Mutate(defs);
                        var r = ScenarioRunner.Run(run.Make(), new RunOptions(), defs);
                        vals[i] = r.Metric(metric, arg);
                    }
                    values[run.Id + "|" + metric + "|" + arg] = vals;
                    sb.AppendLine($"| {run.Label} | {metric}{(arg != 0 ? "(" + arg + ")" : "")} | {unit} | " +
                        string.Join(" | ", vals.Select(v => double.IsNaN(v) ? "NaN" : v.ToString("F3"))) + " |");
                }
            }
            sb.AppendLine();
            sb.AppendLine("## Warianty");
            foreach (var v in variants) sb.AppendLine($"- `{v.Id}` — {v.Label}");
            var report = sb.ToString();
            _out.WriteLine(report);

            // Sanity: the comparison must not be garbage (current production values reproduce the audited ones).
            double T(RunDef r, string m, double a, int vi) => values[r.Id + "|" + m + "|" + a][vi];
            var launch40 = runs.First(r => r.Id == "launch@laden40");
            var brake80 = runs.First(r => r.Id == "brake80@laden40");
            Assert.InRange(T(launch40, "time_to_kmh", 80, 0), 40, 95);   // docs/04 walidacja 40-95 s @40 t
            Assert.InRange(T(brake80, "stop_distance_m", 0, 0), 30, 61.2); // limit UN R13 typ-0 przy 80 km/h
            Assert.All(values.Values.SelectMany(v => v), v => Assert.False(double.IsNaN(v), "NaN w wynikach porównania"));

            string dir = Path.Combine(RepoPaths.ArtifactsDir, "param-comparison-2026-11-12");
            Directory.CreateDirectory(dir);
            File.WriteAllText(Path.Combine(dir, "summary.md"), report);
        }
    }
}
