using UnityEngine;
using UnityEngine.InputSystem;

namespace Game.Controls
{
    /// <summary>Player setting "Kontrolki dotykowe" (ADR 0265). The values are stored; do not renumber.</summary>
    public enum TouchControlsMode
    {
        /// <summary>Phone / tablet build: shown. PC: shown only once a touch screen was actually touched.</summary>
        Auto = 0,
        Always = 1,
        Never = 2,
    }

    /// <summary>
    /// Whether the on-screen touch controls (wheel, pedals, R/N/D, stalk, turn-signal buttons) are shown, and with that
    /// whether the UI uses the touch or the monitor form factor (<see cref="HudScaleModel"/>). ADR 0265: on a PC without
    /// a touch screen they are hidden - the truck is driven with keyboard / pad / wheel (ADR 0261, 0263, 0264); on
    /// Android / iOS nothing changes. A Windows touch laptop shows them after the first touch (Auto), so a mouse user is
    /// not covered by pedals he cannot use. <see cref="Resolve"/> is pure (unit-tested); <see cref="Current"/> reads the
    /// device once per frame without allocation.
    /// </summary>
    public static class TouchControlsPolicy
    {
        /// <summary>Pure decision.</summary>
        /// <param name="handheldBuild">Android / iOS player (or the editor with that build target).</param>
        /// <param name="touchscreenPresent">Input System reports a touch screen.</param>
        /// <param name="touchSeen">A touch was registered on it in this session.</param>
        public static bool Resolve(TouchControlsMode mode, bool handheldBuild, bool touchscreenPresent, bool touchSeen)
        {
            switch (mode)
            {
                case TouchControlsMode.Always: return true;
                case TouchControlsMode.Never: return false;
                default: return handheldBuild || (touchscreenPresent && touchSeen);
            }
        }

        /// <summary>Phone / tablet build. The editor follows its active build target (UNITY_ANDROID is defined there too),
        /// so Android captures keep the touch HUD and Windows captures show the monitor HUD - the build decides.</summary>
        public static bool HandheldBuild
        {
            get
            {
#if UNITY_ANDROID || UNITY_IOS
                return true;
#else
                return Application.isMobilePlatform;
#endif
            }
        }

        static bool s_TouchSeen;
        static int s_Frame = -1;
        static bool s_Current;

        /// <summary>Tests: forget the touch seen in this session.</summary>
        public static void ResetSession() { s_TouchSeen = false; s_Frame = -1; }

        /// <summary>Resolved for this frame with the stored mode (<see cref="UiPreferences.TouchControls"/>). No allocation.</summary>
        public static bool Current
        {
            get
            {
                int f = Time.frameCount;
                if (f == s_Frame) return s_Current;
                s_Frame = f;
                var ts = Touchscreen.current;
                if (!s_TouchSeen && ts != null && ts.primaryTouch.press.isPressed) s_TouchSeen = true;
                s_Current = Resolve(UiPreferences.TouchControls, HandheldBuild, ts != null, s_TouchSeen);
                return s_Current;
            }
        }

        /// <summary>Polish label for the settings segment.</summary>
        public static string Label(TouchControlsMode m) => m == TouchControlsMode.Always ? "zawsze" : m == TouchControlsMode.Never ? "nigdy" : "auto";
    }

    /// <summary>
    /// UI preferences that are not control tuning (kept outside <see cref="ControlSettings"/> so its schema does not move
    /// while the wheel / pad tasks change it): touch-control visibility and the monitor HUD scale. PlayerPrefs, read once
    /// and cached; every value sanitised on load.
    /// </summary>
    public static class UiPreferences
    {
        public const string PrefTouchControls = "ui.touchControls";
        public const string PrefHudScale = "ui.hudScale";
        /// <summary>D85: version of the one-time touch-controls migration already applied to this save (0 = none).</summary>
        public const string PrefTouchMigration = "ui.touchControls.migration";
        /// <summary>D85: current migration version. Bump only with a new migration step; never reuse a number.</summary>
        public const int TouchMigrationVersion = 1;

        /// <summary>Tests: replaces the device probe of the migration (true = PC without a touch screen). Null = real device.</summary>
        public static bool? TouchlessPcOverride;

        static bool s_Loaded;
        static TouchControlsMode s_Touch;
        static float s_HudScale = 1f;
        /// <summary>Bumped on every change: canvases compare it to lay out again.</summary>
        public static int Version { get; private set; }

        /// <summary>Stored int to a valid mode (unknown values = Auto).</summary>
        public static TouchControlsMode ParseTouchControls(int v) => v == 1 ? TouchControlsMode.Always : v == 2 ? TouchControlsMode.Never : TouchControlsMode.Auto;

        /// <summary>
        /// D85 (pure): one-time migration of the stored touch-controls value. A PC without a touch screen that stored
        /// "zawsze" (1) - the old default of the pre-ADR 0283 HUD - goes to "auto" (0) once, so the monitor HUD shows.
        /// Phone / tablet builds and touch PCs keep the value; "nigdy" and "auto" are never changed. Returns the value to
        /// store; <paramref name="migrated"/> = the stored value changed. The caller writes <see cref="TouchMigrationVersion"/>
        /// regardless, so the step runs once and a later explicit "zawsze" in the settings screen survives.
        /// </summary>
        public static int MigrateTouchControls(int stored, int doneVersion, bool touchlessPc, out bool migrated)
        {
            migrated = false;
            if (doneVersion >= TouchMigrationVersion) return stored;
            if (touchlessPc && stored == (int)TouchControlsMode.Always) { migrated = true; return (int)TouchControlsMode.Auto; }
            return stored;
        }

        /// <summary>PC (not a handheld build) with no touch screen reported by the Input System. The legacy
        /// <c>Input.touchSupported</c> is not used: the project runs the new Input System only (activeInputHandler 1).</summary>
        static bool TouchlessPc() => TouchlessPcOverride ?? (!TouchControlsPolicy.HandheldBuild && Touchscreen.current == null);

        static void Load()
        {
            if (s_Loaded) return;
            s_Loaded = true;
            int done = PlayerPrefs.GetInt(PrefTouchMigration, 0);
            if (done < TouchMigrationVersion)
            {
                int stored = PlayerPrefs.GetInt(PrefTouchControls, 0);
                int now = MigrateTouchControls(stored, done, TouchlessPc(), out bool migrated);
                if (migrated) PlayerPrefs.SetInt(PrefTouchControls, now);
                PlayerPrefs.SetInt(PrefTouchMigration, TouchMigrationVersion);
                PlayerPrefs.Save();
                if (migrated) ControlInputLogger.WriteNoStack("[CONTROLS] ui touchControls zawsze->auto (D85 migration, PC without touch screen)");
            }
            s_Touch = ParseTouchControls(PlayerPrefs.GetInt(PrefTouchControls, 0));
            s_HudScale = HudScaleModel.SanitizeUserScale(PlayerPrefs.GetFloat(PrefHudScale, 1f));
        }

        /// <summary>Tests: drop the cache (the next read goes to PlayerPrefs again).</summary>
        public static void Reload() { s_Loaded = false; Version++; }

        public static TouchControlsMode TouchControls
        {
            get { Load(); return s_Touch; }
            set
            {
                Load();
                var v = ParseTouchControls((int)value);
                if (v == s_Touch) return;
                s_Touch = v; Version++;
                PlayerPrefs.SetInt(PrefTouchControls, (int)v);
                PlayerPrefs.Save();
                ControlInputLogger.WriteNoStack("[CONTROLS] ui touchControls=" + TouchControlsPolicy.Label(v));
            }
        }

        /// <summary>
        /// Evidence runs (launch argument <c>ui_touch</c>, int-ui-s23): use <paramref name="mode"/> for this process only,
        /// without writing PlayerPrefs - the player's stored choice stays untouched. A later change in the settings screen
        /// stores as usual.
        /// </summary>
        public static void OverrideForSession(TouchControlsMode mode)
        {
            Load();
            s_Touch = ParseTouchControls((int)mode); Version++;
            ControlInputLogger.WriteNoStack("[CONTROLS] ui touchControls=" + TouchControlsPolicy.Label(s_Touch) + " (session only, not stored)");
        }

        /// <summary>Monitor HUD scale (0.8 .. 1.4).</summary>
        public static float HudScale
        {
            get { Load(); return s_HudScale; }
            set
            {
                Load();
                float v = HudScaleModel.SanitizeUserScale(value);
                if (Mathf.Approximately(v, s_HudScale)) return;
                s_HudScale = v; Version++;
                PlayerPrefs.SetFloat(PrefHudScale, v);
                PlayerPrefs.Save();
                ControlInputLogger.WriteNoStack("[CONTROLS] ui hudScale=" + Mathf.RoundToInt(v * 100f) + "%");
            }
        }
    }
}
