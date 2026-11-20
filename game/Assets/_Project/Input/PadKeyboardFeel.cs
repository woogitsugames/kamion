using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// Shipped tuning of the gamepad and keyboard driving inputs (ADR 0264), loaded from
    /// <c>Resources/Controls/pad_keyboard_feel.json</c> (same values as these C# defaults). Every number is a
    /// WORKING_VALUE until the owner's feel test on PC; the vehicle numbers cite their source.
    /// The player's own adjustments (dead zone, curve, speed limit) live in <see cref="InputBindingsStore"/>, not here.
    /// </summary>
    [System.Serializable]
    public sealed class PadKeyboardFeel
    {
        public const string ResourcePath = "Controls/pad_keyboard_feel";

        // ---------------------------------------------------------------- pad: steering stick
        /// <summary>Inner dead zone of the steering stick (fraction of travel). WORKING_VALUE (worn sticks rest at ~0.05-0.1, UNVERIFIED).</summary>
        public float stickDeadZone = 0.12f;
        /// <summary>Outer saturation: the last fraction of travel already gives full output (sticks rarely reach 1.0 on the diagonal). WORKING_VALUE.</summary>
        public float stickOuterDeadZone = 0.03f;
        /// <summary>Curve exponent of the stick (1 linear .. 4). WORKING_VALUE.</summary>
        public float stickExponent = 1.8f;
        /// <summary>
        /// true = when the stick is back in its dead zone the driver lets go and the cab wheel self-centres from the
        /// aligning torque of the physics (SteeringColumn, ADR 0058); false = the target follows the stick back to centre
        /// at <see cref="padReturnRatePerS"/> with hands on.
        /// </summary>
        public bool padReleaseToPhysics = true;
        /// <summary>Return rate of the target when not released to physics [fraction of lock / s]. WORKING_VALUE.</summary>
        public float padReturnRatePerS = 2.5f;

        // ---------------------------------------------------------------- pad: triggers (pedals)
        public float triggerDeadZone = 0.04f;
        public float triggerOuterDeadZone = 0.02f;
        /// <summary>Trigger curves (1 = linear; the touch pedals use 1.6 / 1.4 when "progressive", ControlSettings). WORKING_VALUE.</summary>
        public float throttleExponent = 1.0f;
        public float brakeExponent = 1.0f;

        // ---------------------------------------------------------------- speed-dependent steering (pad + keyboard)
        /// <summary>Speed breakpoints [km/h] of the steering rate tables (piecewise linear, flat outside).</summary>
        public float[] rateSpeedsKmh = { 0f, 10f, 30f, 50f, 80f, 100f };
        /// <summary>Highest rate of the steering target from the pad [fraction of lock / s]. At 0 km/h 1.2/s = 960 deg/s of an
        /// 800 deg lock, above the column's hand limit (720 deg/s, steering_feel.json) so the column stays the physical limit
        /// when manoeuvring; at speed it is the tighter one. WORKING_VALUE.</summary>
        public float[] padRatePerS = { 1.2f, 1.0f, 0.5f, 0.25f, 0.12f, 0.1f };
        /// <summary>Same for held keys (1.2/s at standstill = the previous KeyboardDriverInput.SteerRate). WORKING_VALUE.</summary>
        public float[] keyRatePerS = { 1.2f, 1.0f, 0.5f, 0.25f, 0.12f, 0.1f };
        /// <summary>Keyboard return to centre when the key is released [fraction of lock / s] (previous SteerReturnRate 2.0).</summary>
        public float keyReturnRatePerS = 2.0f;
        /// <summary>
        /// Progressive key onset (drive-feel-s24, ADR 0312): a freshly pressed steering key turns the wheel at this fraction of
        /// <see cref="keyRatePerS"/>, rising linearly to the full rate over <see cref="keyOnsetS"/> of holding - a short tap is
        /// a fine correction, a held key still reaches the speed amplitude. 1 = off (the ADR 0264 constant rate). WORKING_VALUE
        /// from the runner tap evidence (physics-runner --input-feel: 0.1 s tap at 50 km/h moved the 40 t combination 0.70 m in 4 s).
        /// </summary>
        public float keyOnsetFraction = 0.35f;
        /// <summary>Holding time after which a steering key turns at the full <see cref="keyRatePerS"/> [s]. WORKING_VALUE.</summary>
        public float keyOnsetS = 0.4f;
        /// <summary>
        /// Amplitude limit at speed: full stick / a held key asks at most for the road-wheel angle giving this lateral
        /// acceleration on a kinematic bicycle [m/s²]. WORKING_VALUE. drive-feel-s24 (ADR 0312): 4.0 -> 2.5. At 4.0 a held key / full
        /// stick tipped the 40 t combination with the cargo CoG at 2.6 m (static rollover threshold 0.339 g = 3.3 m/s² in the
        /// runner, rollover_r50_cog_high) at every speed from 30 to 80 km/h (physics-runner --input-feel, wheel lift; 80 km/h
        /// rolled over). 2.5 keeps the tractor and trailer peaks below 0.8 x that threshold; the player can widen it 2x
        /// (<see cref="PadUserTuning.SpeedLimitScale"/>).
        /// </summary>
        public float maxLatAccelMs2 = 2.5f;
        /// <summary>Wheelbase used for the amplitude limit [m]: art-source/truck/dims.json wheelbase_m 3.70 (WORKING_VALUE there).</summary>
        public float wheelbaseM = 3.70f;
        /// <summary>Maximum road-wheel angle [deg]: tractor_4x2_generic.vehicle.json maxRoadWheelAngleDeg 40.</summary>
        public float maxRoadWheelDeg = 40f;
        /// <summary>Floor of the amplitude limit (evasive steering always possible), fraction of lock. WORKING_VALUE. ADR 0312: 0.05 -> 0.02 (0.05 = 2 deg
        /// road wheel overrode the lateral-acceleration limit from ~70 km/h and tipped the high-CoG 40 t combination; 0.02 binds above ~95 km/h).</summary>
        public float minAmplitude = 0.02f;

        // ---------------------------------------------------------------- keyboard pedals
        /// <summary>Key ramps [1/s] (same as the previous KeyboardDriverInput: 2.5 / 3.0 / 5.0).</summary>
        public float keyThrottleRise = 2.5f;
        public float keyBrakeRise = 3.0f;
        public float keyRelease = 5.0f;

        // ---------------------------------------------------------------- look (right stick)
        public float lookDeadZone = 0.15f;
        public float lookExponent = 1.5f;
        /// <summary>Look rate at full right stick [deg/s]. WORKING_VALUE.</summary>
        public float lookRateDegS = 120f;

        public static PadKeyboardFeel Defaults() => new PadKeyboardFeel();

        /// <summary>Repairs broken tables and clamps scalars (a hand-edited file cannot make the truck undriveable).</summary>
        public void Sanitize()
        {
            var d = Defaults();
            if (!ValidTable(rateSpeedsKmh, padRatePerS) || !ValidTable(rateSpeedsKmh, keyRatePerS))
            { rateSpeedsKmh = d.rateSpeedsKmh; padRatePerS = d.padRatePerS; keyRatePerS = d.keyRatePerS; }
            stickDeadZone = Safe(stickDeadZone, 0f, 0.5f, d.stickDeadZone);
            stickOuterDeadZone = Safe(stickOuterDeadZone, 0f, 0.3f, d.stickOuterDeadZone);
            stickExponent = Safe(stickExponent, 1f, 4f, d.stickExponent);
            padReturnRatePerS = Safe(padReturnRatePerS, 0.1f, 20f, d.padReturnRatePerS);
            triggerDeadZone = Safe(triggerDeadZone, 0f, 0.5f, d.triggerDeadZone);
            triggerOuterDeadZone = Safe(triggerOuterDeadZone, 0f, 0.3f, d.triggerOuterDeadZone);
            throttleExponent = Safe(throttleExponent, 1f, 4f, d.throttleExponent);
            brakeExponent = Safe(brakeExponent, 1f, 4f, d.brakeExponent);
            keyReturnRatePerS = Safe(keyReturnRatePerS, 0.1f, 20f, d.keyReturnRatePerS);
            keyOnsetFraction = Safe(keyOnsetFraction, 0.05f, 1f, d.keyOnsetFraction);
            keyOnsetS = Safe(keyOnsetS, 0f, 2f, d.keyOnsetS);
            maxLatAccelMs2 = Safe(maxLatAccelMs2, 0.5f, 10f, d.maxLatAccelMs2);
            wheelbaseM = Safe(wheelbaseM, 2f, 8f, d.wheelbaseM);
            maxRoadWheelDeg = Safe(maxRoadWheelDeg, 10f, 60f, d.maxRoadWheelDeg);
            minAmplitude = Safe(minAmplitude, 0f, 1f, d.minAmplitude);
            keyThrottleRise = Safe(keyThrottleRise, 0.1f, 50f, d.keyThrottleRise);
            keyBrakeRise = Safe(keyBrakeRise, 0.1f, 50f, d.keyBrakeRise);
            keyRelease = Safe(keyRelease, 0.1f, 50f, d.keyRelease);
            lookDeadZone = Safe(lookDeadZone, 0f, 0.5f, d.lookDeadZone);
            lookExponent = Safe(lookExponent, 1f, 4f, d.lookExponent);
            lookRateDegS = Safe(lookRateDegS, 10f, 720f, d.lookRateDegS);
        }

        static bool ValidTable(float[] x, float[] y)
        {
            if (x == null || y == null || x.Length == 0 || x.Length != y.Length) return false;
            for (int i = 0; i < x.Length; i++)
            {
                if (float.IsNaN(x[i]) || float.IsNaN(y[i]) || y[i] < 0f) return false;
                if (i > 0 && x[i] <= x[i - 1]) return false;
            }
            return true;
        }

        static float Safe(float v, float lo, float hi, float fallback) => float.IsNaN(v) || float.IsInfinity(v) ? fallback : Mathf.Clamp(v, lo, hi);

        /// <summary>Pad steering rate at a speed [fraction of lock / s].</summary>
        public float PadRate(float speedKmh) => PadSteeringMath.Piecewise(Mathf.Abs(speedKmh), rateSpeedsKmh, padRatePerS);
        /// <summary>Keyboard steering rate at a speed [fraction of lock / s].</summary>
        public float KeyRate(float speedKmh) => PadSteeringMath.Piecewise(Mathf.Abs(speedKmh), rateSpeedsKmh, keyRatePerS);
        /// <summary>Fraction of the key steering rate after holding a key for <paramref name="heldS"/> seconds (progressive onset).</summary>
        public float KeyOnset(float heldS) => keyOnsetS <= 1e-4f ? 1f : Mathf.Lerp(Mathf.Clamp01(keyOnsetFraction), 1f, heldS / keyOnsetS);
        /// <summary>Amplitude limit at a speed [m/s] with a player scale of the lateral acceleration (1 = shipped).</summary>
        public float Amplitude(float speedMs, float latAccelScale = 1f) =>
            PadSteeringMath.SpeedAmplitude(speedMs, wheelbaseM, maxLatAccelMs2 * Mathf.Max(0.1f, latAccelScale), maxRoadWheelDeg, minAmplitude);

#if UNITY_5_3_OR_NEWER
        public static PadKeyboardFeel FromJson(string json)
        {
            var f = Defaults();
            if (string.IsNullOrWhiteSpace(json)) return f;
            try { JsonUtility.FromJsonOverwrite(json, f); }
            catch { return Defaults(); }
            f.Sanitize();
            return f;
        }

        static PadKeyboardFeel s_Loaded;

        /// <summary>The shipped tuning (Resources), cached. Not in the driving loop.</summary>
        public static PadKeyboardFeel LoadDefault()
        {
            if (s_Loaded == null) s_Loaded = FromJson(Resources.Load<TextAsset>(ResourcePath)?.text);
            return s_Loaded;
        }
#endif
    }
}
