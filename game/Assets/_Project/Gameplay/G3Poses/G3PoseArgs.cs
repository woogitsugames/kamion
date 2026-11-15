using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Game.Gameplay
{
    /// <summary>
    /// Launch arguments of the photo-pair capture mode (ADR 0246), adb: <c>am start ... -e scene WorldC -e g3pose 1
    /// -e g3pose_run 20261115-120000 [-e g3pose_only 1-5,cm924] [-e lighting overcast]</c>. Parsing only; the runner
    /// (<see cref="G3PoseRunner"/>) does the work. Every timing below is a WORKING_VALUE (ADR 0246), not a measurement.
    /// </summary>
    public sealed class G3PoseArgs
    {
        public const string KeyEnable = "g3pose";
        public const string KeyRun = "g3pose_run";
        public const string KeyOnly = "g3pose_only";
        public const string KeyWidth = "g3pose_width";
        public const string KeyWarmup = "g3pose_warmup_s";
        public const string KeySettle = "g3pose_settle_s";
        public const string KeySettleFrames = "g3pose_settle_frames";
        public const string KeyMaxWait = "g3pose_wait_s";
        /// <summary>Read for the file names only; DrivingLabBootstrap applies the preset (launch argument "lighting").</summary>
        public const string KeyLighting = "lighting";

        /// <summary>Same output width as the editor pairs (scripts/sbs-gate3.ps1 $width = 1280).</summary>
        public const int DefaultWidth = 1280;
        public const int MinWidth = 64, MaxWidth = 4096;
        public const float DefaultWarmupSeconds = 8f;      // WORKING_VALUE: scene load, PsoWarmup, lighting preset
        public const float DefaultSettleSeconds = 1.5f;    // WORKING_VALUE: minimum time at a pose before the capture
        public const int DefaultSettleFrames = 20;         // WORKING_VALUE: minimum rendered frames at a pose
        public const float DefaultMaxWaitSeconds = 20f;    // WORKING_VALUE: capture anyway after this, flagged settled=timeout

        public bool Enabled;
        public string RunId = "run";
        public string Filter = "";
        public int Width = DefaultWidth;
        public float WarmupSeconds = DefaultWarmupSeconds;
        public float SettleSeconds = DefaultSettleSeconds;
        public int SettleFrames = DefaultSettleFrames;
        public float MaxWaitSeconds = DefaultMaxWaitSeconds;
        public string Lighting = "";

        /// <summary>Parses the arguments from <paramref name="get"/> (key → value or null). Bad values fall back to the
        /// defaults with a warning; nothing throws.</summary>
        public static G3PoseArgs Parse(Func<string, string> get, List<string> warnings = null)
        {
            var a = new G3PoseArgs();
            if (get == null) return a;
            string en = Safe(get, KeyEnable);
            a.Enabled = en == "1" || string.Equals(en, "true", StringComparison.OrdinalIgnoreCase);
            if (!a.Enabled) return a;

            string run = Safe(get, KeyRun);
            if (!string.IsNullOrEmpty(run))
            {
                string s = SanitizeToken(run, 64);
                if (s.Length == 0) warnings?.Add($"{KeyRun}='{run}' has no usable characters, using '{a.RunId}'");
                else { if (s != run) warnings?.Add($"{KeyRun}='{run}' sanitised to '{s}'"); a.RunId = s; }
            }
            a.Filter = (Safe(get, KeyOnly) ?? "").Trim();
            a.Lighting = SanitizeToken(Safe(get, KeyLighting) ?? "", 32);

            a.Width = ReadInt(get, KeyWidth, DefaultWidth, MinWidth, MaxWidth, warnings);
            a.WarmupSeconds = ReadFloat(get, KeyWarmup, DefaultWarmupSeconds, 0f, 300f, warnings);
            a.SettleSeconds = ReadFloat(get, KeySettle, DefaultSettleSeconds, 0f, 60f, warnings);
            a.SettleFrames = ReadInt(get, KeySettleFrames, DefaultSettleFrames, 1, 3600, warnings);
            a.MaxWaitSeconds = ReadFloat(get, KeyMaxWait, DefaultMaxWaitSeconds, 0.1f, 600f, warnings);
            if (a.MaxWaitSeconds < a.SettleSeconds)
            {
                warnings?.Add($"{KeyMaxWait}={a.MaxWaitSeconds} < {KeySettle}={a.SettleSeconds}: raised to the settle time");
                a.MaxWaitSeconds = a.SettleSeconds;
            }
            return a;
        }

        /// <summary>
        /// The mode runs only when asked for AND in a Development build (ADR 0246): a release APK given the argument logs
        /// the refusal and renders nothing. <paramref name="reason"/> is the log text in both cases.
        /// </summary>
        public static bool ShouldRun(G3PoseArgs a, bool isDevelopmentBuild, out string reason)
        {
            if (a == null || !a.Enabled) { reason = "not requested"; return false; }
            if (!isDevelopmentBuild) { reason = "REFUSED: not a Development build (build with -Development)"; return false; }
            reason = "enabled";
            return true;
        }

        public override string ToString() => string.Format(CultureInfo.InvariantCulture,
            "run={0} only='{1}' width={2} warmup_s={3} settle_s={4} settle_frames={5} wait_s={6} lighting={7}",
            RunId, Filter, Width, WarmupSeconds, SettleSeconds, SettleFrames, MaxWaitSeconds, Lighting.Length > 0 ? Lighting : "default");

        /// <summary>Keeps [A-Za-z0-9._-], drops the rest, at most <paramref name="max"/> characters, no leading dot.</summary>
        public static string SanitizeToken(string s, int max)
        {
            if (string.IsNullOrEmpty(s)) return "";
            var sb = new StringBuilder(Math.Min(s.Length, max));
            foreach (char c in s)
            {
                if (sb.Length >= max) break;
                bool ok = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.';
                if (ok) sb.Append(c);
            }
            return sb.ToString().TrimStart('.');
        }

        static string Safe(Func<string, string> get, string key)
        {
            try { return get(key); } catch (Exception) { return null; }
        }

        static int ReadInt(Func<string, string> get, string key, int def, int min, int max, List<string> warnings)
        {
            string v = Safe(get, key);
            if (string.IsNullOrEmpty(v)) return def;
            if (int.TryParse(v, NumberStyles.Integer, CultureInfo.InvariantCulture, out int x) && x >= min && x <= max) return x;
            warnings?.Add($"{key}='{v}' not an integer in [{min}, {max}], using {def}");
            return def;
        }

        static float ReadFloat(Func<string, string> get, string key, float def, float min, float max, List<string> warnings)
        {
            string v = Safe(get, key);
            if (string.IsNullOrEmpty(v)) return def;
            if (float.TryParse(v, NumberStyles.Float, CultureInfo.InvariantCulture, out float x) && !float.IsNaN(x) && x >= min && x <= max) return x;
            warnings?.Add($"{key}='{v}' not a number in [{min.ToString(CultureInfo.InvariantCulture)}, {max.ToString(CultureInfo.InvariantCulture)}], using {def.ToString(CultureInfo.InvariantCulture)}");
            return def;
        }
    }
}
