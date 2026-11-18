using System.Globalization;
using UnityEngine;

namespace Game.Controls
{
    /// <summary>Driving HUD on a monitor (ADR 0283). Stored as int; do not renumber.</summary>
    public enum HudDetail
    {
        /// <summary>Speed, gear, air pressure, turn signals, warnings.</summary>
        Minimal = 0,
        /// <summary>Minimal + rev counter, endurance brake, brake cruise, trailer, camera (toggle key, default I).</summary>
        Extended = 1,
    }

    /// <summary>What the screen HUD shows while the camera is in the cab (ADR 0283). Stored as int; do not renumber.</summary>
    public enum CabHudMode
    {
        /// <summary>Live cab instruments present: warnings + turn signals only (the cluster in the dash is the speedometer);
        /// no live instruments (graybox lab truck): the strip.</summary>
        Auto = 0,
        /// <summary>Always the strip, also in the cab.</summary>
        Strip = 1,
        /// <summary>Only warnings + turn signals in the cab.</summary>
        WarningsOnly = 2,
    }

    /// <summary>One copy of every HUD / mirror-window preference: the settings screen edits a pending copy and applies it on
    /// "Zastosuj" (same flow as <c>PcSettingsData</c>). Plain values, compared field by field.</summary>
    public struct HudPrefsData
    {
        public HudDetail Detail;
        public CabHudMode Cab;
        /// <summary>Mirror window height as a fraction of the content height (<see cref="HudPreferences.MirrorSizeMin"/>..Max).</summary>
        public float MirrorSize;
        /// <summary>Vertical position: 0 = top edge, 1 = as low as the free height allows.</summary>
        public float MirrorDrop;
        /// <summary>Horizontal position: 0 = at the outer content edges, 1 = as close to the centre as the clear view allows.</summary>
        public float MirrorInset;
        /// <summary>Main-mirror adjustment outward [deg of the reflected view, negative = inward]: less of the own truck in the window.</summary>
        public float MirrorYawOut;
        /// <summary>Main-mirror adjustment downward [deg of the reflected view] (negative = up).</summary>
        public float MirrorPitchDown;

        public static HudPrefsData Defaults => new HudPrefsData
        {
            Detail = HudDetail.Minimal,
            Cab = CabHudMode.Auto,
            MirrorSize = HudPreferences.MirrorSizeDefault,
            MirrorDrop = 0f,
            MirrorInset = 0f,
            MirrorYawOut = HudPreferences.MirrorYawDefault,
            MirrorPitchDown = 0f,
        };

        /// <summary>Every value into range; unknown enum values and NaN = default (a broken pref never hides the mirrors).</summary>
        public void Sanitize()
        {
            var d = Defaults;
            Detail = Detail == HudDetail.Extended ? HudDetail.Extended : HudDetail.Minimal;
            Cab = Cab == CabHudMode.Strip || Cab == CabHudMode.WarningsOnly ? Cab : CabHudMode.Auto;
            MirrorSize = InRange(MirrorSize, HudPreferences.MirrorSizeMin, HudPreferences.MirrorSizeMax, d.MirrorSize);
            MirrorDrop = InRange(MirrorDrop, 0f, 1f, d.MirrorDrop);
            MirrorInset = InRange(MirrorInset, 0f, 1f, d.MirrorInset);
            MirrorYawOut = InRange(MirrorYawOut, -HudPreferences.MirrorYawMax, HudPreferences.MirrorYawMax, d.MirrorYawOut);
            MirrorPitchDown = InRange(MirrorPitchDown, -HudPreferences.MirrorPitchMax, HudPreferences.MirrorPitchMax, d.MirrorPitchDown);
        }

        static float InRange(float v, float lo, float hi, float def) =>
            float.IsNaN(v) || float.IsInfinity(v) || v < lo - 1e-4f || v > hi + 1e-4f ? def : Mathf.Clamp(v, lo, hi);

        public bool SameAs(in HudPrefsData o) =>
            Detail == o.Detail && Cab == o.Cab && Mathf.Approximately(MirrorSize, o.MirrorSize) && Mathf.Approximately(MirrorDrop, o.MirrorDrop)
            && Mathf.Approximately(MirrorInset, o.MirrorInset) && Mathf.Approximately(MirrorYawOut, o.MirrorYawOut)
            && Mathf.Approximately(MirrorPitchDown, o.MirrorPitchDown);

        /// <summary>Settings-screen step of a slider value (rounded to the step, clamped).</summary>
        public static float Step(float v, int dir, float step, float lo, float hi)
        {
            float n = Mathf.Round((v + dir * step) / step) * step;
            return Mathf.Clamp(n, lo, hi);
        }
    }

    /// <summary>
    /// HUD and mirror-window preferences (ADR 0283), PlayerPrefs like <see cref="UiPreferences"/> (outside the
    /// <see cref="ControlSettings"/> schema; the on / off switch of the mirror windows stays <c>ControlSettings.mirrorInsets</c>,
    /// ADR 0243). Read once and cached; <see cref="Version"/> is bumped on every change so the HUD lays out again with one
    /// int compare per frame (no allocation in the driving loop).
    /// </summary>
    public static class HudPreferences
    {
        public const string PrefDetail = "ui.hudDetail", PrefCab = "ui.hudCab", PrefMirrorSize = "ui.mirrorSize", PrefMirrorDrop = "ui.mirrorDrop",
            PrefMirrorInset = "ui.mirrorInset", PrefMirrorYaw = "ui.mirrorYawOut", PrefMirrorPitch = "ui.mirrorPitchDown";

        /// <summary>Mirror window height range / default as a fraction of the content height. ADR 0265 had a fixed 0.30
        /// ("za małe", D84). WORKING_VALUE.</summary>
        public const float MirrorSizeMin = 0.30f, MirrorSizeMax = 0.60f, MirrorSizeDefault = 0.42f, MirrorSizeStep = 0.02f;
        /// <summary>Player adjustment of the main mirror view [deg], on top of the built aim. Default 0: the TRAKT aim is tuned to
        /// the UN R46 class II fields (ADR 0042, MirrorFieldOfVisionTests) and the graybox lab truck got the same 4.3 deg
        /// outward aim (ADR 0283) - the slider is for the player (seat position / taste). Range WORKING_VALUE.</summary>
        public const float MirrorYawDefault = 0f, MirrorYawMax = 6f, MirrorPitchMax = 3f, MirrorAngleStep = 0.5f;

        static bool s_Loaded;
        static HudPrefsData s_Data;
        public static int Version { get; private set; }

        static void Load()
        {
            if (s_Loaded) return;
            s_Loaded = true;
            var d = HudPrefsData.Defaults;
            s_Data = new HudPrefsData
            {
                Detail = (HudDetail)PlayerPrefs.GetInt(PrefDetail, (int)d.Detail),
                Cab = (CabHudMode)PlayerPrefs.GetInt(PrefCab, (int)d.Cab),
                MirrorSize = PlayerPrefs.GetFloat(PrefMirrorSize, d.MirrorSize),
                MirrorDrop = PlayerPrefs.GetFloat(PrefMirrorDrop, d.MirrorDrop),
                MirrorInset = PlayerPrefs.GetFloat(PrefMirrorInset, d.MirrorInset),
                MirrorYawOut = PlayerPrefs.GetFloat(PrefMirrorYaw, d.MirrorYawOut),
                MirrorPitchDown = PlayerPrefs.GetFloat(PrefMirrorPitch, d.MirrorPitchDown),
            };
            s_Data.Sanitize();
        }

        /// <summary>Tests: drop the cache (the next read goes to PlayerPrefs again).</summary>
        public static void Reload() { s_Loaded = false; Version++; }

        /// <summary>Current values (cached copy; no allocation).</summary>
        public static HudPrefsData Current { get { Load(); return s_Data; } }

        /// <summary>Stores and applies all values (settings screen "Zastosuj"). Sanitised first; no-op when nothing changed.</summary>
        public static void Set(HudPrefsData v)
        {
            Load();
            v.Sanitize();
            if (v.SameAs(s_Data)) return;
            s_Data = v; Version++;
            PlayerPrefs.SetInt(PrefDetail, (int)v.Detail);
            PlayerPrefs.SetInt(PrefCab, (int)v.Cab);
            PlayerPrefs.SetFloat(PrefMirrorSize, v.MirrorSize);
            PlayerPrefs.SetFloat(PrefMirrorDrop, v.MirrorDrop);
            PlayerPrefs.SetFloat(PrefMirrorInset, v.MirrorInset);
            PlayerPrefs.SetFloat(PrefMirrorYaw, v.MirrorYawOut);
            PlayerPrefs.SetFloat(PrefMirrorPitch, v.MirrorPitchDown);
            PlayerPrefs.Save();
            ControlInputLogger.WriteNoStack(LogLine(v));
        }

        /// <summary>
        /// Evidence runs (launch arguments <c>ui_hud</c> / <c>ui_mirror</c>, int-ui-s23): applies <paramref name="v"/> for this
        /// process only, without writing PlayerPrefs (the player's stored HUD / mirror choice stays untouched).
        /// </summary>
        public static void OverrideForSession(HudPrefsData v)
        {
            Load();
            v.Sanitize();
            s_Data = v; Version++;
            ControlInputLogger.WriteNoStack(LogLine(v) + " (session only, not stored)");
        }

        /// <summary>The HUD detail key (default I, rebindable; ADR 0283): minimal &lt;-&gt; extended. A key press, not per frame.</summary>
        public static void ToggleDetail()
        {
            var v = Current;
            v.Detail = v.Detail == HudDetail.Extended ? HudDetail.Minimal : HudDetail.Extended;
            Set(v);
        }

        public static string LogLine(in HudPrefsData v)
        {
            var ci = CultureInfo.InvariantCulture;
            return "[CONTROLS] ui hud=" + (v.Detail == HudDetail.Extended ? "extended" : "minimal")
                + " cab=" + (v.Cab == CabHudMode.Strip ? "strip" : v.Cab == CabHudMode.WarningsOnly ? "warnings" : "auto")
                + " mirror size=" + v.MirrorSize.ToString("F2", ci) + " drop=" + v.MirrorDrop.ToString("F2", ci)
                + " inset=" + v.MirrorInset.ToString("F2", ci) + " yaw=" + v.MirrorYawOut.ToString("F1", ci) + " pitch=" + v.MirrorPitchDown.ToString("F1", ci);
        }
    }
}
