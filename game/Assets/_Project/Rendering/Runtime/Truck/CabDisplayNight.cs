using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// ADR 0299: night mode of the cab screens as one global, eased state. Real truck cluster / navigation screens switch to a
    /// dark palette and dim their backlight with the light sensor (the same sensor as the automatic dipped beam); the switch
    /// fades over a few seconds instead of jumping. CabScreens (Game.UI) feeds the sensor state, Kamion/Cab Display reads
    /// <c>_KamionCabDisplayNight</c> (cap _NightMaxDisplay), CabInteriorLighting lowers the screens' spill with it.
    /// No allocation; Set is called at most once per frame.
    /// </summary>
    public static class CabDisplayNight
    {
        static readonly int k_Night = Shader.PropertyToID("_KamionCabDisplayNight");

        /// <summary>Seconds of a full day / night transition of the backlight. WORKING_VALUE.</summary>
        public const float FadeSeconds = 3f;

        /// <summary>Current night factor (0 day .. 1 night).</summary>
        public static float Value { get; private set; }

        /// <summary>Mean linear value of the live navigation image (0..1) for the spill, or a negative value to keep the
        /// baked texture mean (CabInteriorLighting.SpillSource.meanEmission). Written by NavLayout on every draw.</summary>
        public static float NavMeanEmission = -1f;

        /// <summary>One easing step toward the sensor state; <paramref name="dt"/> &lt;= 0 jumps (visual QA, first frame).</summary>
        public static float Step(float current, bool night, float dt)
        {
            float target = night ? 1f : 0f;
            return dt <= 0f ? target : Mathf.MoveTowards(current, target, dt / FadeSeconds);
        }

        public static void Set(float v)
        {
            Value = Mathf.Clamp01(v);
            Shader.SetGlobalFloat(k_Night, Value);
        }

        /// <summary>Display ceiling after the night dimming (Kamion/Cab Display: lerp(max, min(max, nightMax), night)).</summary>
        public static float Cap(float maxDisplay, float nightMaxDisplay, float night)
        {
            float nightCap = nightMaxDisplay > 0f ? Mathf.Min(maxDisplay, nightMaxDisplay) : maxDisplay;
            return Mathf.Lerp(maxDisplay, nightCap, Mathf.Clamp01(night));
        }
    }
}
