using System.Globalization;
using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// Player-tunable control settings (touch wheel, gyro, pedal curves). Plain data: serialised as one JSON string in
    /// PlayerPrefs (<see cref="PrefKey"/>) with a schema version so older saves migrate instead of resetting.
    /// Every value is clamped on load, so a hand-edited or corrupt save cannot produce an unusable wheel.
    /// <see cref="LogLine"/> is the single-line form written to logcat (tag Unity, prefix [CONTROLS]) so the owner's
    /// choice can be read back with <c>adb logcat -d | grep CONTROLS</c>.
    /// </summary>
    [System.Serializable]
    public sealed class ControlSettings
    {
        public const string PrefKey = "controls.settings";
        /// <summary>Pre-settings-menu key: 0 = wheel 270, 1 = wheel 900, 2 = gyro (Stage 1/2 builds).</summary>
        public const string LegacySteerModeKey = "controls.steerMode";
        public const int CurrentSchema = 4;

        public const float RangeMin = 180f, RangeMax = 900f;
        public const float GainMin = 0.5f, GainMax = 2f;
        public const float CentreMin = 0f, CentreMax = 2f;
        public const float DeadMin = 0f, DeadMax = 0.15f;
        public const float LookMin = 0.5f, LookMax = 2f;
        public const float FovMin = 45f, FovMax = 75f;
        /// <summary>CameraRig defaults the camera settings scale (Game.Cameras.CameraRig lookDegPerPixel, headGain).</summary>
        public const float BaseLookDegPerPixel = 0.12f, BaseHeadGain = 0.006f;

        public int schema = CurrentSchema;
        /// <summary>On-screen wheel half range [deg]: 270 comfort, 900 simulator (docs/04 section 3).</summary>
        public float wheelRangeDeg = 270f;
        /// <summary>Output gain of the wheel (1 = full lock at the full range).</summary>
        public float wheelSensitivity = 1f;
        /// <summary>Multiplier of the self-centring speed of the cab wheel when released (0 = stays where left; ADR 0058).</summary>
        public float centreStrength = 1f;
        /// <summary>Steering dead zone, fraction of full lock.</summary>
        public float wheelDeadZone = 0.01f;
        /// <summary>Steer by tilting the phone instead of the on-screen wheel.</summary>
        public bool gyroEnabled;
        /// <summary>Flip the tilt direction (for a sensor whose sign is opposite on the device).</summary>
        public bool gyroInvert;
        /// <summary>Gain of the tilt: 2 = half the tilt for full lock.</summary>
        public float gyroSensitivity = 1f;
        /// <summary>false = linear, true = progressive (fine modulation at small pedal travel).</summary>
        public bool throttleProgressive = true;
        public bool brakeProgressive = true;
        /// <summary>Schema 2: gain of the look-around drag in the cab view.</summary>
        public float lookSensitivity = 1f;
        /// <summary>Schema 2: field of view of the cab camera [deg] (vertical).</summary>
        public float cabFov = 55f;
        /// <summary>Schema 2: head sway from accelerations (limited, see CameraRig); off for motion-sickness-prone players.</summary>
        public bool headMotion = true;
        /// <summary>
        /// Schema 3 (ADR 0058): speed-sensitive steering. On = the comfort range reaches full lock when manoeuvring but at
        /// speed one on-screen degree is one cab-wheel degree (gyro: less lock at full tilt); off = the old fixed mapping.
        /// </summary>
        public bool speedSensitiveSteering = true;
        /// <summary>
        /// Schema 4 (ADR 0135): touch-wheel gesture. true = sideways thumb slide (relative, mm of travel, anywhere on the
        /// wheel); false = finger angle around the centre (ADR 0058). The rotate gesture could not reach full lock with a
        /// thumb in the screen corner (owner, Fold, 2026-11-12: "ciężko, nieprzyjemnie się kieruje").
        /// </summary>
        public bool wheelDragGrab = true;

        public const float ProgressiveThrottleExponent = 1.6f, ProgressiveBrakeExponent = 1.4f;
        public const float BaseGyroMaxTiltDeg = 35f;

        public float ThrottleExponent => throttleProgressive ? ProgressiveThrottleExponent : 1f;
        public float BrakeExponent => brakeProgressive ? ProgressiveBrakeExponent : 1f;
        public float GyroMaxTiltDeg => BaseGyroMaxTiltDeg / Mathf.Max(GainMin, gyroSensitivity);

        public static ControlSettings Defaults() => new ControlSettings();

        public ControlSettings Clone() => (ControlSettings)MemberwiseClone();

        public void ResetToDefaults()
        {
            var d = Defaults();
            wheelRangeDeg = d.wheelRangeDeg; wheelSensitivity = d.wheelSensitivity; centreStrength = d.centreStrength;
            wheelDeadZone = d.wheelDeadZone; gyroEnabled = d.gyroEnabled; gyroInvert = d.gyroInvert;
            gyroSensitivity = d.gyroSensitivity; throttleProgressive = d.throttleProgressive; brakeProgressive = d.brakeProgressive;
            lookSensitivity = d.lookSensitivity; cabFov = d.cabFov; headMotion = d.headMotion;
            speedSensitiveSteering = d.speedSensitiveSteering;
            wheelDragGrab = d.wheelDragGrab;
            schema = CurrentSchema;
        }

        /// <summary>Clamps every value into its valid range (NaN falls back to the default).</summary>
        public void Clamp()
        {
            var d = Defaults();
            wheelRangeDeg = Safe(wheelRangeDeg, RangeMin, RangeMax, d.wheelRangeDeg);
            wheelSensitivity = Safe(wheelSensitivity, GainMin, GainMax, d.wheelSensitivity);
            centreStrength = Safe(centreStrength, CentreMin, CentreMax, d.centreStrength);
            wheelDeadZone = Safe(wheelDeadZone, DeadMin, DeadMax, d.wheelDeadZone);
            gyroSensitivity = Safe(gyroSensitivity, GainMin, GainMax, d.gyroSensitivity);
            lookSensitivity = Safe(lookSensitivity, LookMin, LookMax, d.lookSensitivity);
            cabFov = Safe(cabFov, FovMin, FovMax, d.cabFov);
        }

        static float Safe(float v, float lo, float hi, float fallback) => float.IsNaN(v) || float.IsInfinity(v) ? fallback : Mathf.Clamp(v, lo, hi);

        // ------------------------------------------------------------------ persistence

        public string ToJson() => JsonUtility.ToJson(this);

        /// <summary>Parses a saved JSON string; empty/corrupt input gives defaults. Older schemas are migrated.</summary>
        public static ControlSettings FromJson(string json)
        {
            var s = Defaults();
            if (string.IsNullOrWhiteSpace(json)) return s;
            try { JsonUtility.FromJsonOverwrite(json, s); }
            catch { return Defaults(); }
            Migrate(s);
            s.Clamp();
            return s;
        }

        /// <summary>
        /// Schema migrations. v0 (no "schema" field), v1 (no camera fields) and v2 (no speed-sensitive steering) need no
        /// value conversion: JsonUtility leaves the missing fields at their defaults, so only the version is raised and
        /// the owner's other choices are kept. v3 to v4 switches the touch wheel to the drag gesture (ADR 0135, same reasoning:
        /// the old gesture was the cause of the report). v2 to v3 explicitly switches speed-sensitive steering on: the v2 mapping
        /// was the cause of the "wheel turns far too fast" feel report (ADR 0058), so an old save gets the new feel.
        /// </summary>
        static void Migrate(ControlSettings s)
        {
            if (s.schema < 1) s.schema = 1;
            if (s.schema < 2) s.schema = 2;   // v2: lookSensitivity, cabFov, headMotion
            if (s.schema < 3) { s.speedSensitiveSteering = true; s.schema = 3; }   // v3: ADR 0058 steering column
            if (s.schema < 4) { s.wheelDragGrab = true; s.schema = 4; }            // v4: ADR 0135 drag gesture (owner report)
            if (s.schema > CurrentSchema) s.schema = CurrentSchema;   // saved by a newer build: keep known fields
        }

        /// <summary>Settings from the Stage 1/2 key only: 0 wheel 270, 1 wheel 900, 2 gyro.</summary>
        public static ControlSettings FromLegacySteerMode(int mode)
        {
            var s = Defaults();
            s.gyroEnabled = mode == 2;
            s.wheelRangeDeg = mode == 1 ? 900f : 270f;
            return s;
        }

        public static ControlSettings Load(string key = PrefKey, string legacyKey = LegacySteerModeKey)
        {
            if (PlayerPrefs.HasKey(key)) return FromJson(PlayerPrefs.GetString(key, ""));
            if (legacyKey != null && PlayerPrefs.HasKey(legacyKey)) return FromLegacySteerMode(PlayerPrefs.GetInt(legacyKey, 0));
            return Defaults();
        }

        public void Save(string key = PrefKey)
        {
            Clamp();
            schema = CurrentSchema;
            PlayerPrefs.SetString(key, ToJson());
            PlayerPrefs.Save();   // the process may be killed at any time on Android
        }

        // ------------------------------------------------------------------ apply

        /// <summary>Copies the settings into the input sources (the sources hold no other tuning state).</summary>
        public void ApplyTo(TouchSteeringWheel wheel, GyroSteering gyro, TouchControls touch, SteeringColumn column = null)
        {
            if (column != null) column.CentreStrength = centreStrength;
            if (wheel != null)
            {
                wheel.HalfRangeDeg = wheelRangeDeg;
                wheel.Sensitivity = wheelSensitivity;
                wheel.SpeedSensitive = speedSensitiveSteering;
                wheel.DeadZone = wheelDeadZone;
                wheel.Grab = wheelDragGrab ? WheelGrab.Drag : WheelGrab.Rotate;
                wheel.Enabled = !gyroEnabled;
                wheel.SetWheelDeg(wheel.WheelDeg);   // re-clamp to a shorter range
            }
            if (gyro != null)
            {
                gyro.Enabled = gyroEnabled;
                gyro.Invert = gyroInvert;
                gyro.SpeedSensitive = speedSensitiveSteering;
                gyro.MaxTiltDeg = GyroMaxTiltDeg;
            }
            if (touch != null)
            {
                touch.ThrottleExponent = ThrottleExponent;
                touch.BrakeExponent = BrakeExponent;
            }
        }

        // ------------------------------------------------------------------ log

        public string LogLine(string reason)
        {
            var ci = CultureInfo.InvariantCulture;
            return "[CONTROLS] " + reason + " v" + schema.ToString(ci)
                + " steer=" + (gyroEnabled ? "gyro" : "wheel")
                + " wheelRange=" + wheelRangeDeg.ToString("F0", ci)
                + " wheelSens=" + wheelSensitivity.ToString("F2", ci)
                + " centre=" + centreStrength.ToString("F2", ci)
                + " deadZone=" + wheelDeadZone.ToString("F3", ci)
                + " gyroInvert=" + (gyroInvert ? "on" : "off")
                + " gyroSens=" + gyroSensitivity.ToString("F2", ci)
                + " throttle=" + (throttleProgressive ? "progressive" : "linear")
                + " brake=" + (brakeProgressive ? "progressive" : "linear")
                + " lookSens=" + lookSensitivity.ToString("F2", ci)
                + " cabFov=" + cabFov.ToString("F0", ci)
                + " headMotion=" + (headMotion ? "on" : "off")
                + " speedSteer=" + (speedSensitiveSteering ? "on" : "off")
                + " grab=" + (wheelDragGrab ? "drag" : "rotate");
        }

        /// <summary>Writes <see cref="LogLine"/> without a stack trace (one logcat line per entry).</summary>
        public void Log(string reason) => ControlInputLogger.WriteNoStack(LogLine(reason));
    }
}
