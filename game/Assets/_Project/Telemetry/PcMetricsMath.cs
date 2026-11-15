using System;
using System.Globalization;

namespace Game.Telemetry
{
    /// <summary>
    /// Pure logic of the PC frame-metrics run (ADR 0266): nearest-rank percentiles and threshold counts over a sorted
    /// buffer, and parsing of the player command line (<c>-metrics &lt;dir&gt; -metricsSeconds 90 ...</c>).
    /// No UnityEngine dependency, so EditMode tests cover it and <c>tools/pcperf/pc_metrics.py</c> mirrors it exactly
    /// (same nearest-rank definition as <see cref="Game.Core.FrameTimeStats"/> and scripts/device-metrics.ps1).
    /// </summary>
    public static class PcMetricsMath
    {
        /// <summary>Nearest-rank percentile of the first <paramref name="count"/> values of an ascending-sorted array.
        /// rank = ceil(p·n), clamped to [1, n]; returns 0 for an empty buffer.</summary>
        public static float NearestRank(float[] sorted, int count, double p)
        {
            if (sorted == null || count <= 0) return 0f;
            if (count > sorted.Length) count = sorted.Length;
            int rank = (int)Math.Ceiling(p * count - 1e-9);
            if (rank < 1) rank = 1;
            if (rank > count) rank = count;
            return sorted[rank - 1];
        }

        /// <summary>Number of values strictly greater than <paramref name="thresholdMs"/> (any order).</summary>
        public static int CountOver(float[] values, int count, float thresholdMs)
        {
            if (values == null) return 0;
            if (count > values.Length) count = values.Length;
            int n = 0;
            for (int i = 0; i < count; i++) if (values[i] > thresholdMs) n++;
            return n;
        }

        /// <summary>Capacity of the preallocated frame buffer: seconds × max expected FPS, clamped to [1 000, 2 000 000].</summary>
        public static int FrameCapacity(float seconds, int maxFps)
        {
            double c = Math.Ceiling(Math.Max(seconds, 1f) * Math.Max(maxFps, 1));
            if (c < 1000) c = 1000;
            if (c > 2000000) c = 2000000;
            return (int)c;
        }
    }

    /// <summary>When the PC metrics window starts.</summary>
    public enum PcMetricsStart
    {
        /// <summary>Right after the Boot scene loads (empty-scene / menu measurement).</summary>
        Boot,
        /// <summary>At the first frame of the first scene loaded after Boot (region / DrivingLab), i.e. after the load hitch.</summary>
        Region,
    }

    /// <summary>Command-line options of <see cref="PcFrameMetricsRecorder"/>. Disabled unless <c>-metrics &lt;dir&gt;</c> is given.</summary>
    public sealed class PcMetricsOptions
    {
        /// <summary>Default measurement window [s] (same as device-metrics.ps1 -DurationSeconds 90 in docs/03).</summary>
        public const float DefaultSeconds = 90f;
        /// <summary>Default warm-up [s] stored in run.json for the parser (frames are recorded from 0, the parser drops the warm-up).</summary>
        public const float DefaultWarmup = 5f;
        /// <summary>Default wait for the first region frame before giving up [s].</summary>
        public const float DefaultTimeout = 300f;
        /// <summary>Default upper bound of FPS for sizing the frame buffer (uncapped runs on fast GPUs).</summary>
        public const int DefaultMaxFps = 1000;

        public bool Enabled;
        public string OutputDirectory;
        public float Seconds = DefaultSeconds;
        public float WarmupSeconds = DefaultWarmup;
        public float TimeoutSeconds = DefaultTimeout;
        public PcMetricsStart Start = PcMetricsStart.Boot;
        /// <summary>-1 = leave the quality level's vSyncCount alone; 0/1 = force for the measurement.</summary>
        public int VSync = -1;
        public bool QuitWhenDone = true;
        public int MaxFps = DefaultMaxFps;
        public string Label = "";

        /// <summary>Parses <c>-metrics &lt;dir&gt;</c> [<c>-metricsSeconds s</c>] [<c>-metricsWarmup s</c>] [<c>-metricsStart boot|region</c>]
        /// [<c>-metricsTimeout s</c>] [<c>-metricsVsync 0|1</c>] [<c>-metricsQuit 0|1</c>] [<c>-metricsMaxFps n</c>] [<c>-metricsLabel text</c>].
        /// Without <c>-metricsStart</c>, a <c>-scene</c> argument implies <c>region</c>. Flags are case-insensitive.</summary>
        public static PcMetricsOptions Parse(string[] args)
        {
            var o = new PcMetricsOptions();
            if (args == null) return o;
            bool startGiven = false, sceneGiven = false;
            var ci = CultureInfo.InvariantCulture;
            for (int i = 0; i < args.Length; i++)
            {
                string a = args[i];
                if (string.IsNullOrEmpty(a) || a[0] != '-') continue;
                string v = i + 1 < args.Length ? args[i + 1] : null;
                switch (a.ToLowerInvariant())
                {
                    case "-metrics":
                        if (!string.IsNullOrEmpty(v) && v[0] != '-') { o.Enabled = true; o.OutputDirectory = v; }
                        break;
                    case "-metricsseconds":
                        if (float.TryParse(v, NumberStyles.Float, ci, out float s) && s > 0f) o.Seconds = s;
                        break;
                    case "-metricswarmup":
                        if (float.TryParse(v, NumberStyles.Float, ci, out float w) && w >= 0f) o.WarmupSeconds = w;
                        break;
                    case "-metricstimeout":
                        if (float.TryParse(v, NumberStyles.Float, ci, out float t) && t > 0f) o.TimeoutSeconds = t;
                        break;
                    case "-metricsstart":
                        if (string.Equals(v, "region", StringComparison.OrdinalIgnoreCase)) { o.Start = PcMetricsStart.Region; startGiven = true; }
                        else if (string.Equals(v, "boot", StringComparison.OrdinalIgnoreCase)) { o.Start = PcMetricsStart.Boot; startGiven = true; }
                        break;
                    case "-metricsvsync":
                        if (v == "0") o.VSync = 0; else if (v == "1") o.VSync = 1;
                        break;
                    case "-metricsquit":
                        if (v == "0") o.QuitWhenDone = false; else if (v == "1") o.QuitWhenDone = true;
                        break;
                    case "-metricsmaxfps":
                        if (int.TryParse(v, NumberStyles.Integer, ci, out int m) && m > 0) o.MaxFps = m;
                        break;
                    case "-metricslabel":
                        if (v != null) o.Label = v;
                        break;
                    case "-scene":
                        if (!string.IsNullOrEmpty(v)) sceneGiven = true;
                        break;
                }
            }
            if (!startGiven && sceneGiven) o.Start = PcMetricsStart.Region;
            if (o.WarmupSeconds >= o.Seconds) o.WarmupSeconds = 0f;
            return o;
        }
    }
}
