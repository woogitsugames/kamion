using System;
using System.Collections.Generic;
using System.Linq;

namespace PhysicsRunner.Sim
{
    /// <summary>Multi-run validations shared by the console runner and the xUnit tests.</summary>
    public static class Suites
    {
        public static Scenario Find(string id)
        {
            foreach (var s in Scenario.LoadAll(RepoPaths.ScenariosDir)) if (s.id == id) return s;
            throw new ArgumentException($"Scenario '{id}' not found");
        }

        public sealed class SpreadResult
        {
            public string Label = "";
            public double[] Values = Array.Empty<double>();
            public double Mean => Values.Average();
            /// <summary>Max deviation from the mean, relative [-].</summary>
            public double MaxRelDev => Values.Max(v => Math.Abs(v - Mean)) / Mean;
            public override string ToString() => $"{Label}: [{string.Join(", ", Values.Select(v => v.ToString("F3")))}] mean {Mean:F3}, max dev {MaxRelDev * 100:F2}%";
        }

        /// <summary>
        /// Repeatability of 0-60 / 0-80: three runs with different headings (world-frame orientation,
        /// i.e. different floating-point paths) — docs/04 section 6 item 3.
        /// </summary>
        public static SpreadResult[] Repeatability(string scenarioId, double[] headings, Func<int, string> csvPath = null)
        {
            var sc = Find(scenarioId);
            var t60 = new double[headings.Length];
            var t80 = new double[headings.Length];
            for (int i = 0; i < headings.Length; i++)
            {
                var r = ScenarioRunner.Run(sc, new RunOptions { HeadingDeg = headings[i], CsvPath = csvPath?.Invoke(i) });
                t60[i] = r.Metric("time_to_kmh", 60);
                t80[i] = r.Metric("time_to_kmh", 80);
            }
            return new[]
            {
                new SpreadResult { Label = "0-60 km/h [s]", Values = t60 },
                new SpreadResult { Label = "0-80 km/h [s]", Values = t80 },
            };
        }

        /// <summary>Same scenario at several fixed steps (substeps scaled to keep ~2.5 ms inner step) — item 12.</summary>
        public static SpreadResult DtSweep(string scenarioId, string metric, double arg, double[] dts)
        {
            var sc = Find(scenarioId);
            var vals = new double[dts.Length];
            for (int i = 0; i < dts.Length; i++)
            {
                int sub = Math.Max(1, (int)Math.Round(dts[i] / 0.0025));
                var r = ScenarioRunner.Run(sc, new RunOptions { Dt = dts[i], Substeps = sub });
                vals[i] = r.Metric(metric, arg);
            }
            return new SpreadResult { Label = $"{scenarioId}:{metric}({arg}) @dt {string.Join("/", dts.Select(d => (1 / d).ToString("F0") + "Hz"))}", Values = vals };
        }

        /// <summary>Same scenario at a fixed dt with different substep counts — item 12 (substep consistency).</summary>
        public static SpreadResult SubstepSweep(string scenarioId, string metric, double arg, int[] substeps)
        {
            var sc = Find(scenarioId);
            var vals = new double[substeps.Length];
            for (int i = 0; i < substeps.Length; i++)
            {
                var r = ScenarioRunner.Run(sc, new RunOptions { Substeps = substeps[i] });
                vals[i] = r.Metric(metric, arg);
            }
            return new SpreadResult { Label = $"{scenarioId}:{metric}({arg}) @substeps {string.Join("/", substeps)}", Values = vals };
        }
    }
}
