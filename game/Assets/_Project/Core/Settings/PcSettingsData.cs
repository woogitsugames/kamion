using System;
using System.Collections.Generic;
using UnityEngine;

namespace Game.Core.Settings
{
    /// <summary>Window mode as stored in the settings file (string ids, so the file stays readable and survives enum renames).</summary>
    public static class WindowModes
    {
        public const string Windowed = "windowed", Borderless = "borderless", Exclusive = "exclusive";
        /// <summary>Menu order: okno, okno bez ramki, pełny ekran wyłączny.</summary>
        public static readonly string[] All = { Windowed, Borderless, Exclusive };
        public static bool IsKnown(string id) => Array.IndexOf(All, id) >= 0;
    }

    /// <summary>Graphics tier choice: "auto" or one of the quality levels (Low/Medium/High/Ultra, ADR 0012 / 0261 / H7 0269).</summary>
    public static class TierChoices
    {
        public const string Auto = "auto";
        /// <summary>Menu order. Index 1..4 = Unity quality level names <see cref="QualityLevelNames"/>.</summary>
        public static readonly string[] All = { Auto, "low", "medium", "high", "ultra" };
        /// <summary>Unity quality level names in the same order as <see cref="All"/> (index 0 = auto has none).</summary>
        public static readonly string[] QualityLevelNames = { null, "Low", "Medium", "High", "Ultra" };
        public static bool IsKnown(string id) => Array.IndexOf(All, id) >= 0;

        /// <summary>"Low" / "low" / "LOW" -> "low"; unknown or empty -> null.</summary>
        public static string FromQualityLevel(string name)
        {
            if (string.IsNullOrEmpty(name)) return null;
            for (int i = 1; i < All.Length; i++)
                if (string.Equals(QualityLevelNames[i], name, StringComparison.OrdinalIgnoreCase)) return All[i];
            return null;
        }

        /// <summary>"low" -> "Low"; "auto" / unknown -> null.</summary>
        public static string ToQualityLevel(string id)
        {
            int i = Array.IndexOf(All, id);
            return i > 0 ? QualityLevelNames[i] : null;
        }
    }

    /// <summary>Speed units. The HUD and cab displays only render km/h today (CabDisplayText.KmH): "imperial" is accepted by the
    /// model for a future HUD but the menu offers metric only (ADR 0270 §Jednostki).</summary>
    public static class SpeedUnits
    {
        public const string Metric = "metric", Imperial = "imperial";
        public static readonly string[] All = { Metric, Imperial };
        public static bool IsKnown(string id) => Array.IndexOf(All, id) >= 0;
    }

    /// <summary>Display part of the PC settings. Width/height 0 = the monitor's current (native) resolution.</summary>
    [Serializable]
    public sealed class PcDisplaySettings
    {
        public int width;
        public int height;
        /// <summary>Refresh rate as a ratio (Unity <c>RefreshRate</c>: 60000/1001 = 59.94 Hz). 0/0 = the monitor default.</summary>
        public int refreshNumerator;
        public int refreshDenominator;
        public string mode = WindowModes.Borderless;

        public double RefreshHz => refreshDenominator > 0 ? (double)refreshNumerator / refreshDenominator : 0.0;
        public bool UsesNativeResolution => width <= 0 || height <= 0;

        public PcDisplaySettings Clone() => (PcDisplaySettings)MemberwiseClone();

        public bool SameAs(PcDisplaySettings o) =>
            o != null && width == o.width && height == o.height && refreshNumerator == o.refreshNumerator &&
            refreshDenominator == o.refreshDenominator && mode == o.mode;
    }

    /// <summary>Volume levels 0..1 per channel that exists in the audio code (ADR 0270 §Dźwięk): master = AudioListener,
    /// engine = EngineAudio (loops, turbo, clatter), ambient = AmbientAudio (yard bed, birds), cab signals = ClusterChime.</summary>
    [Serializable]
    public sealed class PcVolumeSettings
    {
        public float master = 1f;
        public float engine = 1f;
        public float ambient = 1f;
        public float ui = 1f;
        /// <summary>GPS voice ("Kamion GPS", ADR 0328) on / off. A field missing in an older file keeps true (schema 1 unchanged).</summary>
        public bool gpsVoice = true;

        public PcVolumeSettings Clone() => (PcVolumeSettings)MemberwiseClone();
    }

    /// <summary>
    /// PC settings (ADR 0270): display, frame pacing, graphics tier, HUD scale, units and volumes. Plain data (JsonUtility):
    /// stored as versioned JSON by <see cref="PcSettingsStore"/>. Ranges and defaults live here; <see cref="Sanitize"/> puts
    /// every out-of-range or unknown value back to its default (never trusts the file).
    /// Not used in the driving loop (menu / startup only), so allocation is fine.
    /// </summary>
    [Serializable]
    public sealed class PcSettingsData
    {
        /// <summary>Current schema. 0 / missing = written before the field existed (pre-release file) or legacy PlayerPrefs.</summary>
        public const int CurrentSchemaVersion = 1;

        /// <summary>Frame-rate caps offered in the menu; 0 = no cap. 60 = desktop default of ADR 0261 (GameBootstrap.DesktopTargetFps).</summary>
        public static readonly int[] FpsCaps = { 30, 60, 75, 120, 144, 0 };
        public const int DefaultFpsCap = 60;

        /// <summary>HUD scale range = HudScaleModel.UserScaleMin/Max of ADR 0265 (#131); same PlayerPrefs key <c>ui.hudScale</c>.</summary>
        public const float HudScaleMin = 0.8f, HudScaleMax = 1.4f, HudScaleStep = 0.1f;
        public const float VolumeStep = 0.05f;

        public int schemaVersion = CurrentSchemaVersion;
        public PcDisplaySettings display = new PcDisplaySettings();
        public bool vsync;
        public int fpsCap = DefaultFpsCap;
        public string graphicsTier = TierChoices.Auto;
        public float hudScale = 1f;
        public string speedUnits = SpeedUnits.Metric;
        public PcVolumeSettings volumes = new PcVolumeSettings();

        public static PcSettingsData Defaults() => new PcSettingsData();

        public PcSettingsData Clone()
        {
            var c = (PcSettingsData)MemberwiseClone();
            c.display = (display ?? new PcDisplaySettings()).Clone();
            c.volumes = (volumes ?? new PcVolumeSettings()).Clone();
            return c;
        }

        public bool SameAs(PcSettingsData o)
        {
            if (o == null) return false;
            var a = volumes ?? new PcVolumeSettings();
            var b = o.volumes ?? new PcVolumeSettings();
            return (display ?? new PcDisplaySettings()).SameAs(o.display ?? new PcDisplaySettings()) && vsync == o.vsync && fpsCap == o.fpsCap &&
                   graphicsTier == o.graphicsTier && Mathf.Approximately(hudScale, o.hudScale) && speedUnits == o.speedUnits &&
                   Mathf.Approximately(a.master, b.master) && Mathf.Approximately(a.engine, b.engine) &&
                   Mathf.Approximately(a.ambient, b.ambient) && Mathf.Approximately(a.ui, b.ui) && a.gpsVoice == b.gpsVoice;
        }

        public static bool IsAllowedFpsCap(int cap) => Array.IndexOf(FpsCaps, cap) >= 0;

        static bool Finite(float v) => !float.IsNaN(v) && !float.IsInfinity(v);
        static bool InRange(float v, float lo, float hi) => Finite(v) && v >= lo - 1e-4f && v <= hi + 1e-4f;

        /// <summary>
        /// Replaces every unknown / out-of-range value with its default and lists the names of the fixed fields in
        /// <paramref name="fixedFields"/> (may be null). Returns this. Out of range means default, not the nearest bound:
        /// a damaged file must not leave e.g. a 0 % master volume or a 2-pixel window behind.
        /// </summary>
        public PcSettingsData Sanitize(List<string> fixedFields = null)
        {
            var d = Defaults();
            if (display == null) { display = new PcDisplaySettings(); fixedFields?.Add("display"); }
            if (volumes == null) { volumes = new PcVolumeSettings(); fixedFields?.Add("volumes"); }

            // Display: 0x0 = native; otherwise a sane window size (Unity minimum is far below; 640x360 keeps the menus usable).
            bool native = display.width == 0 && display.height == 0;
            bool sizeOk = native || (display.width >= 640 && display.height >= 360 && display.width <= 16384 && display.height <= 16384);
            if (!sizeOk)
            {
                display.width = 0; display.height = 0; display.refreshNumerator = 0; display.refreshDenominator = 0;
                fixedFields?.Add("display.size");
            }
            bool refreshOk = (display.refreshNumerator == 0 && display.refreshDenominator == 0) ||
                             (display.refreshNumerator > 0 && display.refreshDenominator > 0 && display.RefreshHz >= 20.0 && display.RefreshHz <= 1000.0);
            if (!refreshOk) { display.refreshNumerator = 0; display.refreshDenominator = 0; fixedFields?.Add("display.refresh"); }
            if (!WindowModes.IsKnown(display.mode)) { display.mode = d.display.mode; fixedFields?.Add("display.mode"); }

            if (!IsAllowedFpsCap(fpsCap)) { fpsCap = d.fpsCap; fixedFields?.Add("fpsCap"); }
            if (!TierChoices.IsKnown(graphicsTier)) { graphicsTier = d.graphicsTier; fixedFields?.Add("graphicsTier"); }
            if (!InRange(hudScale, HudScaleMin, HudScaleMax)) { hudScale = d.hudScale; fixedFields?.Add("hudScale"); }
            if (!SpeedUnits.IsKnown(speedUnits)) { speedUnits = d.speedUnits; fixedFields?.Add("speedUnits"); }

            if (!InRange(volumes.master, 0f, 1f)) { volumes.master = 1f; fixedFields?.Add("volumes.master"); }
            if (!InRange(volumes.engine, 0f, 1f)) { volumes.engine = 1f; fixedFields?.Add("volumes.engine"); }
            if (!InRange(volumes.ambient, 0f, 1f)) { volumes.ambient = 1f; fixedFields?.Add("volumes.ambient"); }
            if (!InRange(volumes.ui, 0f, 1f)) { volumes.ui = 1f; fixedFields?.Add("volumes.ui"); }
            schemaVersion = CurrentSchemaVersion;
            return this;
        }

        /// <summary>One step of a stepper on a grid anchored at 0 (no float drift), clamped to [lo, hi] (menu editing).</summary>
        public static float Step(float v, int dir, float step, float lo, float hi)
        {
            float n = Mathf.Round(v / step) + dir;
            return Mathf.Clamp(Mathf.Round(n * step * 1000f) / 1000f, lo, hi);
        }

        /// <summary>Next / previous entry of a list, clamped at the ends (menu steppers do not wrap).</summary>
        public static int StepIndex(int index, int dir, int count) => count <= 0 ? -1 : Mathf.Clamp(index + dir, 0, count - 1);
    }

    /// <summary>
    /// Frame pacing (ADR 0270): menu choice (vsync, cap) -> Unity's <c>QualitySettings.vSyncCount</c> and
    /// <c>Application.targetFrameRate</c>. On desktop Unity ignores targetFrameRate whenever vSyncCount &gt; 0, so with vsync
    /// the cap is not applied (the menu greys it out) and targetFrameRate is -1. Without vsync: cap N -> N, no cap -> -1.
    /// </summary>
    public static class FramePacing
    {
        public static void Map(bool vsync, int fpsCap, out int vSyncCount, out int targetFrameRate)
        {
            if (vsync) { vSyncCount = 1; targetFrameRate = -1; return; }
            vSyncCount = 0;
            targetFrameRate = fpsCap > 0 ? fpsCap : -1;
        }

        /// <summary>Inverse for keeping the file in sync when something else set the runtime values (start-menu fps buttons,
        /// <c>QualityTiers.SetTargetFrameRate</c>). A rate that is not in <see cref="PcSettingsData.FpsCaps"/> keeps <paramref name="fallbackCap"/>.</summary>
        public static void FromRuntime(int vSyncCount, int targetFrameRate, int fallbackCap, out bool vsync, out int fpsCap)
        {
            vsync = vSyncCount > 0;
            if (targetFrameRate <= 0) fpsCap = 0;
            else fpsCap = PcSettingsData.IsAllowedFpsCap(targetFrameRate) ? targetFrameRate : fallbackCap;
            if (vsync) fpsCap = fallbackCap;
        }
    }
}
