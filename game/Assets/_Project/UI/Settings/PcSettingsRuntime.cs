using System.Collections.Generic;
using Game.Core;
using Game.Core.Settings;
using Game.Rendering;
using UnityEngine;

namespace Game.UI.Settings
{
    /// <summary>Applies a graphics tier (ADR 0270 adapter until H7 / ADR 0269 <c>PcGraphicsTiers</c> is merged).</summary>
    public interface IGraphicsTierApplier
    {
        /// <summary>Applies a Unity quality level by name ("Low" .. "Ultra"); false when unknown.</summary>
        bool Apply(string qualityLevelName);
        /// <summary>Name of the active level.</summary>
        string Current { get; }
    }

    /// <summary>
    /// Default tier applier: Unity quality level by name (<see cref="QualityTiers.Apply"/>, persisted in the same PlayerPrefs
    /// key the start menu and <c>-tier</c> use, so GameBootstrap agrees on the next start).
    /// After H7 (ADR 0269) is merged replace the body of <see cref="Apply"/> with ONE line:
    /// <c>PcGraphicsTiers.Apply((PcTier)System.Array.IndexOf(QualityTiers.Names, qualityLevelName)); return true;</c>
    /// (PcTier {Low, Medium, High, Ultra} has the order of <see cref="QualityTiers.Names"/>).
    /// </summary>
    public sealed class QualityLevelTierApplier : IGraphicsTierApplier
    {
        public bool Apply(string qualityLevelName) => QualityTiers.Apply(qualityLevelName, persist: true);
        public string Current => QualityTiers.Current;
    }

    /// <summary>
    /// Runtime side of the PC settings (ADR 0270): owns the store, applies a <see cref="PcSettingsData"/> to Unity
    /// (Screen, QualitySettings / Application frame pacing, tier, AudioListener + <see cref="AudioMixLevels"/>, HUD scale
    /// key) and keeps the file in sync when the start-menu quick buttons change tier / fps. Startup and menu only.
    /// Display, tier and frame pacing are applied only in a desktop player (phones keep their own tier rules and 30/60 fps;
    /// the editor keeps the editor window). Volumes and HUD scale apply everywhere.
    /// </summary>
    public static class PcSettingsRuntime
    {
        public static IGraphicsTierApplier TierApplier = new QualityLevelTierApplier();
        /// <summary>Tier used for "Auto": ADR 0261 desktop default (High). H7 may replace it with a hardware-based pick.</summary>
        public static System.Func<string> AutoTier = () => "High";

        static PcSettingsStore s_Store;
        static PcSettingsData s_Current;
        static PcSettingsLoadReport.Origin s_LoadedFrom = PcSettingsLoadReport.Origin.Defaults;

        public static PcSettingsStore Store => s_Store ??= new PcSettingsStore(Application.persistentDataPath, new PlayerPrefsLegacySource());

        /// <summary>The applied (= saved) settings; loaded on first access.</summary>
        public static PcSettingsData Current
        {
            get
            {
                if (s_Current == null)
                {
                    s_Current = Store.Load(out var report);
                    s_LoadedFrom = report.Source;
                    Debug.Log("[SETTINGS] pc load " + report + " path=" + Store.FilePath);
                }
                return s_Current;
            }
        }

        public static bool IsDesktopPlayer =>
            Application.platform == RuntimePlatform.WindowsPlayer || Application.platform == RuntimePlatform.OSXPlayer ||
            Application.platform == RuntimePlatform.LinuxPlayer;

        /// <summary>Called once by GameBootstrap after its own tier / fps choice. A launch argument (<c>-tier</c>, <c>-fps</c>)
        /// wins over the file for this run (measurements, ADR 0261), without changing the file.</summary>
        public static void ApplyAtStartup(bool tierFromArgument, bool fpsFromArgument)
        {
            var s = Current;
            bool desktop = IsDesktopPlayer;
            bool fromFile = s_LoadedFrom == PcSettingsLoadReport.Origin.File || s_LoadedFrom == PcSettingsLoadReport.Origin.Backup;
            if (desktop && StartupDisplayPolicy.ShouldApply(fromFile, System.Environment.GetCommandLineArgs())) ApplyDisplay(s.display);
            if (desktop && !fpsFromArgument) ApplyFramePacing(s);
            if (desktop && !tierFromArgument) ApplyTier(s.graphicsTier);
            ApplyAudio(s.volumes);
            ApplyHudScale(s.hudScale);
            Debug.Log("[SETTINGS] pc apply startup desktop=" + desktop + " " + Describe(s));
        }

        /// <summary>Saves and applies a new set (menu "Zastosuj"). Display is applied by the caller (it needs the countdown).</summary>
        public static void Commit(PcSettingsData s, bool applyDisplay)
        {
            s = s.Clone().Sanitize();
            try { Store.Save(s); }
            catch (System.Exception e) { Debug.LogWarning("[SETTINGS] pc save failed: " + e.Message); }
            s_Current = s;
            bool desktop = IsDesktopPlayer || Application.isEditor;
            if (applyDisplay && IsDesktopPlayer) ApplyDisplay(s.display);
            if (desktop) { ApplyFramePacing(s); ApplyTier(s.graphicsTier); }
            ApplyAudio(s.volumes);
            ApplyHudScale(s.hudScale);
            Debug.Log("[SETTINGS] pc commit " + Describe(s));
        }

        /// <summary>Start-menu quick buttons (StartMenuOptions) changed the tier: keep the file in step.</summary>
        public static void NoteTierChanged(string qualityLevelName)
        {
            string id = TierChoices.FromQualityLevel(qualityLevelName);
            if (id == null || Current.graphicsTier == id) return;
            var s = Current.Clone(); s.graphicsTier = id;
            SaveOnly(s);
        }

        /// <summary>Start-menu quick buttons changed the frame cap (QualityTiers.SetTargetFrameRate switches vsync off).</summary>
        public static void NoteFrameRateChanged(int fps)
        {
            FramePacing.FromRuntime(0, fps, Current.fpsCap, out bool vsync, out int cap);
            if (Current.vsync == vsync && Current.fpsCap == cap) return;
            var s = Current.Clone(); s.vsync = vsync; s.fpsCap = cap;
            SaveOnly(s);
        }

        static void SaveOnly(PcSettingsData s)
        {
            try { Store.Save(s); s_Current = s.Sanitize(); }
            catch (System.Exception e) { Debug.LogWarning("[SETTINGS] pc save failed: " + e.Message); }
        }

        // ------------------------------------------------------------------ apply

        public static FullScreenMode ToUnity(string mode) =>
            mode == WindowModes.Windowed ? FullScreenMode.Windowed :
            mode == WindowModes.Exclusive ? FullScreenMode.ExclusiveFullScreen : FullScreenMode.FullScreenWindow;

        public static string FromUnity(FullScreenMode m) =>
            m == FullScreenMode.Windowed ? WindowModes.Windowed :
            m == FullScreenMode.ExclusiveFullScreen ? WindowModes.Exclusive : WindowModes.Borderless;

        /// <summary>Monitor modes for the menu, de-duplicated and sorted (<see cref="ResolutionList"/>).</summary>
        public static List<DisplayMode> AvailableModes()
        {
            var raw = new List<DisplayMode>();
            foreach (var r in Screen.resolutions)
                raw.Add(new DisplayMode(r.width, r.height, r.refreshRateRatio.numerator, r.refreshRateRatio.denominator));
            var list = ResolutionList.Build(raw);
            if (list.Count == 0)   // editor / unusual drivers: offer at least the current mode
            {
                var c = Screen.currentResolution;
                list.Add(new DisplayMode(c.width, c.height, c.refreshRateRatio.numerator, c.refreshRateRatio.denominator));
            }
            return list;
        }

        /// <summary>What the window shows now (for the countdown's "go back" and for "native").</summary>
        public static PcDisplaySettings ReadCurrentDisplay()
        {
            var rr = Screen.currentResolution.refreshRateRatio;
            return new PcDisplaySettings
            {
                width = Screen.width, height = Screen.height,
                refreshNumerator = (int)rr.numerator, refreshDenominator = (int)rr.denominator,
                mode = FromUnity(Screen.fullScreenMode),
            };
        }

        public static void ApplyDisplay(PcDisplaySettings d)
        {
            var mode = ToUnity(d.mode);
            int w = d.width, h = d.height;
            if (d.UsesNativeResolution)
            {
                // Native = the desktop mode of the monitor the window is on (Screen.currentResolution in a window = desktop).
                var main = Screen.mainWindowDisplayInfo;
                w = main.width > 0 ? main.width : Screen.currentResolution.width;
                h = main.height > 0 ? main.height : Screen.currentResolution.height;
            }
            if (w <= 0 || h <= 0) return;
            if (d.refreshDenominator > 0 && d.refreshNumerator > 0 && mode == FullScreenMode.ExclusiveFullScreen)
                Screen.SetResolution(w, h, mode, new RefreshRate { numerator = (uint)d.refreshNumerator, denominator = (uint)d.refreshDenominator });
            else
                Screen.SetResolution(w, h, mode);
            Debug.Log("[SETTINGS] display " + w + "x" + h + " " + d.mode + " refresh=" + d.RefreshHz.ToString("0.##", System.Globalization.CultureInfo.InvariantCulture));
        }

        public static void ApplyFramePacing(PcSettingsData s)
        {
            FramePacing.Map(s.vsync, s.fpsCap, out int vsc, out int target);
            QualitySettings.vSyncCount = vsc;
            Application.targetFrameRate = target;
        }

        public static void ApplyTier(string tierChoice)
        {
            string name = tierChoice == TierChoices.Auto ? AutoTier?.Invoke() : TierChoices.ToQualityLevel(tierChoice);
            if (string.IsNullOrEmpty(name)) return;
            if (TierApplier.Current == name) return;
            if (!TierApplier.Apply(name)) Debug.LogWarning("[SETTINGS] unknown tier " + name);
        }

        public static void ApplyAudio(PcVolumeSettings v)
        {
            AudioMixLevels.Set(v.master, v.engine, v.ambient, v.ui);
            AudioListener.volume = AudioMixLevels.Master;
        }

        /// <summary>HUD scale goes to the PlayerPrefs key of ADR 0265 (#131 <c>UiPreferences.PrefHudScale</c>). After #131 is
        /// merged also call <c>UiPreferences.Reload()</c> here so the HUD picks it up at once.</summary>
        public static void ApplyHudScale(float scale)
        {
            if (PlayerPrefs.HasKey(PcSettingsJson.HudScaleKey) && Mathf.Approximately(PlayerPrefs.GetFloat(PcSettingsJson.HudScaleKey), scale)) return;
            PlayerPrefs.SetFloat(PcSettingsJson.HudScaleKey, scale);
            PlayerPrefs.Save();
        }

        static string Describe(PcSettingsData s)
        {
            var ci = System.Globalization.CultureInfo.InvariantCulture;
            return "mode=" + s.display.mode + " size=" + s.display.width + "x" + s.display.height + " vsync=" + s.vsync + " cap=" + s.fpsCap +
                   " tier=" + s.graphicsTier + " hud=" + s.hudScale.ToString("0.##", ci) + " units=" + s.speedUnits +
                   " vol=" + s.volumes.master.ToString("0.##", ci) + "/" + s.volumes.engine.ToString("0.##", ci) + "/" +
                   s.volumes.ambient.ToString("0.##", ci) + "/" + s.volumes.ui.ToString("0.##", ci);
        }
    }
}
