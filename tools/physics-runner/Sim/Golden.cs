using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;

namespace PhysicsRunner.Sim
{
    /// <summary>
    /// Golden telemetry (tests/golden/): small CSV subsets (10 Hz, selected columns) of key scenarios, compared
    /// with per-column tolerances from tests/golden/tolerances.json. A column passes when at most
    /// maxOutlierFraction of the samples differ by more than abs + rel * |golden| (shift timing can move a
    /// single step). Regenerate with `physics-runner --update-golden` and review the diff.
    /// </summary>
    public static class Golden
    {
        public static readonly string[] Ids =
        {
            "launch_6pct_uphill_comb@laden40",
            "brake_80_0_dry_abs_comb@laden40",
            "brake_80_0_wet_abs_comb@laden40",
            "brake_80_0_wet_noabs_comb@empty",
            "downhill_7pct_brake_cruise_60@laden40",
            "lane_change_80@laden40",
            "jackknife_wet_curve_noabs@empty",
            "brake_80_0_dry",
            "launch_0_80_flat",
        };

        public static readonly string[] Columns =
        {
            "t", "speed_kmh", "rpm", "gear", "a_long", "a_lat", "yaw_rate_dps", "articulation_deg", "kingpin_fz",
            "air_front_bar", "air_rear_bar", "air_trailer_res_bar", "retarder_torque", "engine_brake_torque",
            "front_L_p_bar", "rear_L_p_bar", "front_L_fz", "rear_L_fz",
        };

        public static string Dir => Path.Combine(RepoPaths.Root, "tests", "golden");
        static string FileFor(string id) => Path.Combine(Dir, id.Replace('@', '_') + ".csv");
        /// <summary>Decimation: 10 Hz for short runs, 2 Hz for runs longer than 40 s (keeps the files small).</summary>
        static int EveryFor(string id) => Suites.Find(id).duration > 40 ? 50 : 10;
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

        public static void Write(string id, string telemetryCsv)
        {
            var (header, rows) = Read(telemetryCsv);
            int Every = EveryFor(id);
            var idx = Columns.Select(c => Array.IndexOf(header, c)).ToArray();
            var sb = new StringBuilder();
            sb.AppendLine(string.Join(",", Columns));
            for (int i = Every - 1; i < rows.Count; i += Every)
            {
                var r = rows[i];
                sb.AppendLine(string.Join(",", idx.Select(j => j >= 0 ? double.Parse(r[j], Inv).ToString("G6", Inv) : "0")));
            }
            Directory.CreateDirectory(Dir);
            File.WriteAllText(FileFor(id), sb.ToString());
        }

        public sealed class ColumnResult
        {
            public string Column = "";
            public double MaxDiff;
            public double OutlierFraction;
            public bool Passed;
            public override string ToString() => $"{Column}: max |diff| {MaxDiff:G4}, outliers {OutlierFraction * 100:F1}% {(Passed ? "ok" : "FAIL")}";
        }

        /// <summary>Compares a fresh telemetry CSV with the golden file. Returns per-column results.</summary>
        public static List<ColumnResult> Compare(string id, string telemetryCsv)
        {
            var tol = LoadTolerances();
            var (gh, grows) = Read(FileFor(id));
            var (h, rows) = Read(telemetryCsv);
            var res = new List<ColumnResult>();
            int Every = EveryFor(id);
            int n = Math.Min(grows.Count, rows.Count / Every);
            foreach (var col in Columns)
            {
                if (col == "t") continue;
                int gi = Array.IndexOf(gh, col), ci = Array.IndexOf(h, col);
                if (gi < 0) continue;
                var (abs, rel) = tol.Columns.TryGetValue(col, out var tv) ? (tv[0], tv[1]) : (tol.DefaultAbs, tol.DefaultRel);
                int outliers = 0; double maxd = 0;
                for (int k = 0; k < n; k++)
                {
                    double g = double.Parse(grows[k][gi], Inv);
                    double v = ci >= 0 ? double.Parse(rows[k * Every + Every - 1][ci], Inv) : 0;
                    double d = Math.Abs(v - g);
                    maxd = Math.Max(maxd, d);
                    if (d > abs + rel * Math.Abs(g)) outliers++;
                }
                double frac = n > 0 ? outliers / (double)n : 1;
                res.Add(new ColumnResult { Column = col, MaxDiff = maxd, OutlierFraction = frac, Passed = frac <= tol.MaxOutlierFraction && grows.Count * Every <= rows.Count + Every });
            }
            return res;
        }

        sealed class Tolerances
        {
            public double DefaultAbs = 0.1, DefaultRel = 0.02, MaxOutlierFraction = 0.03;
            public Dictionary<string, double[]> Columns = new Dictionary<string, double[]>();
        }

        static Tolerances LoadTolerances()
        {
            var t = new Tolerances();
            string p = Path.Combine(Dir, "tolerances.json");
            if (!File.Exists(p)) return t;
            using var doc = JsonDocument.Parse(File.ReadAllText(p), new JsonDocumentOptions { CommentHandling = JsonCommentHandling.Skip });
            var root = doc.RootElement;
            if (root.TryGetProperty("defaultAbs", out var a)) t.DefaultAbs = a.GetDouble();
            if (root.TryGetProperty("defaultRel", out var r)) t.DefaultRel = r.GetDouble();
            if (root.TryGetProperty("maxOutlierFraction", out var m)) t.MaxOutlierFraction = m.GetDouble();
            if (root.TryGetProperty("columns", out var cols))
                foreach (var c in cols.EnumerateObject())
                    t.Columns[c.Name] = new[] { c.Value[0].GetDouble(), c.Value[1].GetDouble() };
            return t;
        }

        static (string[] header, List<string[]> rows) Read(string path)
        {
            var lines = File.ReadAllLines(path);
            var header = lines[0].Split(',');
            var rows = new List<string[]>(lines.Length);
            for (int i = 1; i < lines.Length; i++) if (lines[i].Length > 0) rows.Add(lines[i].Split(','));
            return (header, rows);
        }
    }
}
