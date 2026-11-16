using System;
using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// Player settings for a PC wheel (ADR 0263): rotation range, mapping, force feedback, calibration overrides.
    /// One JSON string in PlayerPrefs (<see cref="PrefKey"/>) with a schema version (migrations, like
    /// <see cref="ControlSettings"/>). Calibrations are stored per profile id so swapping wheels keeps both.
    /// </summary>
    [Serializable]
    public sealed class WheelSettings
    {
        public const string PrefKey = "controls.wheel";
        public const int CurrentSchema = 1;

        public int schema = CurrentSchema;
        /// <summary>Use a detected wheel at all (off = keyboard/touch only).</summary>
        public bool enabled = true;
        /// <summary>Force a profile id ("" = automatic by vendor/product).</summary>
        public string profileOverride = "";
        /// <summary>In-game rotation range lock-to-lock [deg], 270-900; 0 = profile default.</summary>
        public float rangeDeg;
        public WheelSteerMapping mapping = WheelSteerMapping.ScaledToLock;
        public bool forceFeedbackEnabled = true;
        public ForceFeedbackSettings forceFeedback = new ForceFeedbackSettings();
        /// <summary>Wizard results (replace the profile guesses for that profile id).</summary>
        public WheelCalibrationRecord[] calibrations = new WheelCalibrationRecord[0];

        public static WheelSettings Defaults() => new WheelSettings();

        public WheelCalibrationRecord CalibrationFor(string profileId)
        {
            if (calibrations == null || string.IsNullOrEmpty(profileId)) return null;
            for (int i = 0; i < calibrations.Length; i++)
                if (calibrations[i] != null && calibrations[i].profileId == profileId) return calibrations[i];
            return null;
        }

        public void SetCalibration(WheelCalibrationRecord rec)
        {
            if (rec == null || string.IsNullOrEmpty(rec.profileId)) return;
            if (calibrations == null) calibrations = new WheelCalibrationRecord[0];
            for (int i = 0; i < calibrations.Length; i++)
                if (calibrations[i] != null && calibrations[i].profileId == rec.profileId) { calibrations[i] = rec; return; }
            Array.Resize(ref calibrations, calibrations.Length + 1);
            calibrations[calibrations.Length - 1] = rec;
        }

        /// <summary>Parses a saved JSON string; empty/corrupt input gives defaults; older schemas are migrated; values clamped.</summary>
        public static WheelSettings FromJson(string json)
        {
            var s = Defaults();
            if (!string.IsNullOrWhiteSpace(json))
            {
                try { JsonUtility.FromJsonOverwrite(json, s); }
                catch (Exception) { s = Defaults(); }
                if (!json.Contains("\"schema\"")) s.schema = 0;
            }
            Migrate(s);
            s.Sanitize();
            return s;
        }

        /// <summary>v0 = no schema field (never shipped; treated as v1 with defaults for missing fields).</summary>
        static void Migrate(WheelSettings s)
        {
            if (s.schema < 1) s.schema = 1;
            if (s.schema > CurrentSchema) s.schema = CurrentSchema;   // newer build: keep known fields
        }

        public void Sanitize()
        {
            if (rangeDeg != 0f) rangeDeg = WheelSteeringMap.ClampRange(rangeDeg, WheelSteeringMap.RangeMaxDeg);
            if (mapping != WheelSteerMapping.ScaledToLock && mapping != WheelSteerMapping.OneToOne) mapping = WheelSteerMapping.ScaledToLock;
            if (forceFeedback == null) forceFeedback = new ForceFeedbackSettings();
            forceFeedback.Sanitize();
            if (profileOverride == null) profileOverride = "";
            if (calibrations == null) calibrations = new WheelCalibrationRecord[0];
            for (int i = 0; i < calibrations.Length; i++) calibrations[i]?.Sanitize();
        }

        public string ToJson() { schema = CurrentSchema; return JsonUtility.ToJson(this); }

        public static WheelSettings Load(string key = PrefKey) => FromJson(PlayerPrefs.GetString(key, ""));

        public void Save(string key = PrefKey)
        {
            PlayerPrefs.SetString(key, ToJson());
            PlayerPrefs.Save();
        }
    }

    /// <summary>Stored wizard calibration of one profile (only the axes the wizard measured are flagged).</summary>
    [Serializable]
    public sealed class WheelCalibrationRecord
    {
        public string profileId = "";
        public bool hasSteer, hasThrottle, hasBrake, hasClutch;
        public AxisCalibration steer = new AxisCalibration();
        public AxisCalibration throttle = new AxisCalibration();
        public AxisCalibration brake = new AxisCalibration();
        public AxisCalibration clutch = new AxisCalibration();
        /// <summary>Lock-to-lock rotation the steering axis spans as measured/entered in the wizard [deg]; 0 = profile value.</summary>
        public float deviceRangeDeg;

        public void Sanitize()
        {
            (steer ??= new AxisCalibration()).Sanitize();
            (throttle ??= new AxisCalibration()).Sanitize();
            (brake ??= new AxisCalibration()).Sanitize();
            (clutch ??= new AxisCalibration()).Sanitize();
            if (float.IsNaN(deviceRangeDeg) || deviceRangeDeg < 0f) deviceRangeDeg = 0f;
            else if (deviceRangeDeg > 0f) deviceRangeDeg = Mathf.Clamp(deviceRangeDeg, 90f, 2520f);
        }
    }

    /// <summary>Loads the shipped profiles (<c>Resources/Controls/wheel_profiles.json</c>), cached; never null.</summary>
    public static class WheelProfiles
    {
        public const string ResourcePath = "Controls/wheel_profiles";
        static WheelProfileSet s_Loaded;

        public static WheelProfileSet FromJson(string json)
        {
            var set = new WheelProfileSet();
            if (!string.IsNullOrWhiteSpace(json))
            {
                try { JsonUtility.FromJsonOverwrite(json, set); }
                catch (Exception) { set = new WheelProfileSet(); }
            }
            set.Sanitize();
            if (set.ById("generic") == null)
            {
                Array.Resize(ref set.profiles, set.profiles.Length + 1);
                set.profiles[set.profiles.Length - 1] = new WheelDeviceProfile { id = "generic", steer = new WheelAxisBinding { control = "stick/x" } };
            }
            return set;
        }

        public static WheelProfileSet LoadDefault()
        {
            if (s_Loaded == null) s_Loaded = FromJson(Resources.Load<TextAsset>(ResourcePath)?.text);
            return s_Loaded;
        }
    }
}
