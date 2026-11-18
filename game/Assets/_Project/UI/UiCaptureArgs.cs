using System;
using System.Globalization;
using Game.Controls;
using UnityEngine;

namespace Game.UI
{
    /// <summary>
    /// Evidence runs of the desktop player without a person at the keyboard (int-ui-s23, ADR 0283 screenshots): launch
    /// arguments that set the UI state for THIS process only, never stored in PlayerPrefs (the player's own choices stay):
    /// <c>-ui_touch auto|always|never</c>, <c>-ui_hud minimal|extended</c>,
    /// <c>-ui_mirror size,drop,inset,yawOut,pitchDown</c> (fractions 0..1 and degrees, invariant culture),
    /// <c>-ui_settings_tab N</c> (menu: opens the tabbed settings screen on tab N, 0-based). Nothing happens without them.
    /// </summary>
    public static class UiCaptureArgs
    {
        static bool s_Applied;

        /// <summary>Tab requested by <c>ui_settings_tab</c> (-1 = none). Valid after <see cref="Apply"/>.</summary>
        public static int SettingsTab { get; private set; } = -1;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void ResetProcess() { s_Applied = false; SettingsTab = -1; }

        /// <summary>Reads the arguments once per process and applies the session overrides.</summary>
        public static void Apply(Func<string, string> arg)
        {
            if (s_Applied || arg == null) return;
            s_Applied = true;
            var ci = CultureInfo.InvariantCulture;

            string touch = arg("ui_touch");
            if (!string.IsNullOrEmpty(touch))
                UiPreferences.OverrideForSession(touch == "always" ? TouchControlsMode.Always : touch == "never" ? TouchControlsMode.Never : TouchControlsMode.Auto);

            string hud = arg("ui_hud"), mirror = arg("ui_mirror");
            if (!string.IsNullOrEmpty(hud) || !string.IsNullOrEmpty(mirror))
            {
                var v = HudPreferences.Current;
                if (hud == "extended") v.Detail = HudDetail.Extended;
                else if (hud == "minimal") v.Detail = HudDetail.Minimal;
                if (!string.IsNullOrEmpty(mirror))
                {
                    var p = mirror.Split(',');
                    float F(int i, float d) => i < p.Length && float.TryParse(p[i], NumberStyles.Float, ci, out float f) ? f : d;
                    v.MirrorSize = F(0, v.MirrorSize); v.MirrorDrop = F(1, v.MirrorDrop); v.MirrorInset = F(2, v.MirrorInset);
                    v.MirrorYawOut = F(3, v.MirrorYawOut); v.MirrorPitchDown = F(4, v.MirrorPitchDown);
                }
                HudPreferences.OverrideForSession(v);
            }

            if (int.TryParse(arg("ui_settings_tab"), NumberStyles.Integer, ci, out int tab) && tab >= 0) SettingsTab = tab;
        }
    }
}
