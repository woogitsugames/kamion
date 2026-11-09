using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// A daylight condition (sun position, atmosphere, exposure, fog). Applied by <see cref="EnvironmentLighting"/>.
    /// Values are documented in docs/adr/0010-look-development-sky-exposure-tonemapping.md; all WORKING_VALUE until
    /// compared with owner photos of the same place and time.
    /// </summary>
    [CreateAssetMenu(menuName = "Kamion/Rendering/Lighting Preset", fileName = "LP_New")]
    public sealed class LightingPreset : ScriptableObject
    {
        [Header("Sun")]
        [Range(0.5f, 89.5f)] public float sunElevationDeg = 42f;
        [Tooltip("Compass azimuth, 0 = north, 90 = east (world X = east, Z = north)")]
        [Range(0f, 360f)] public float sunAzimuthDeg = 200f;

        [Header("Atmosphere")]
        [Tooltip("Preetham turbidity: 2 very clear, 3 clear continental, 5 hazy")]
        [Range(1.7f, 8f)] public float turbidity = 2.5f;
        [Tooltip("0 = clear sky (Preetham), 1 = CIE standard overcast (no direct sun)")]
        [Range(0f, 1f)] public float overcast;
        [Tooltip("Meteorological visibility (km); fog density = 3.912 / V (Koschmieder)")]
        public float visibilityKm = 30f;
        [Tooltip("Diffuse albedo of the surrounding ground for the lower hemisphere of the ambient probe")]
        public Color groundAlbedo = new Color(0.16f, 0.17f, 0.12f);
        [Tooltip("Saturation of the sky part of the ambient light (1 = the analytic sky). The probe has no inter-reflections " +
                 "from walls, trees and the truck itself, which grey real shadows; 0.55 removes the cyan shadows of the " +
                 "first renders (visual review r2 #3, docs/06 §2). WORKING_VALUE.")]
        [Range(0f, 1f)] public float ambientSkySaturation = 0.55f;

        [Header("Exposure")]
        [Tooltip("Automatic: incident-meter EV100 of the horizontal illuminance (EV = log2(E/2.5)) plus compensation")]
        public bool autoExposure = true;
        public float ev100 = 15f;
        [Tooltip("Exposure compensation in stops (positive = brighter). D23: a phone exposes ~+1 EV over an incident meter " +
                 "(matrix metering on a dark ground, highlight roll-off by the tone curve) - clear +1.2, overcast +1.0.")]
        public float exposureCompensation = 1.2f;

        [Header("Look (owner decision D23: like a phone photo)")]
        [Tooltip("Colour grading contrast (URP Color Adjustments, -100..100). A phone's global tone curve is flatter than a " +
                 "film S-curve; negative = softer. Applied on every tier that runs post-processing.")]
        [Range(-50f, 20f)] public float lookContrast = -10f;
        [Tooltip("Colour grading saturation (-100..100). Natural colours: 0 or slightly negative (docs/06 §2).")]
        [Range(-30f, 20f)] public float lookSaturation = 0f;
        [Tooltip("Shadow lift (Lift/Gamma/Gain lift offset): phone pipelines raise the black level and open the shadows " +
                 "(multi-frame noise reduction + local tone mapping). 0 = none.")]
        [Range(0f, 0.15f)] public float lookShadowLift = 0.03f;
        [Tooltip("Highlight gain offset (Lift/Gamma/Gain gain): negative pulls bright surfaces and the sky away from clipping.")]
        [Range(-0.2f, 0.1f)] public float lookHighlightGain = 0f;

        public float ResolveEv100(SkyModel probe) => (autoExposure ? SkyModel.IncidentEv100(probe.HorizontalIlluminanceLux) : ev100) - exposureCompensation;

        /// <summary>Builds the sky model with the resolved exposure (two passes: illuminance does not depend on exposure).</summary>
        public SkyModel CreateModel()
        {
            var probe = new SkyModel(sunElevationDeg, sunAzimuthDeg, turbidity, overcast, 0f);
            return new SkyModel(sunElevationDeg, sunAzimuthDeg, turbidity, overcast, ResolveEv100(probe));
        }

        public static LightingPreset CreateClear()
        {
            var p = CreateInstance<LightingPreset>();
            p.name = "LP_Clear";
            p.sunElevationDeg = 42f; p.sunAzimuthDeg = 200f; p.turbidity = 2.5f; p.overcast = 0f; p.visibilityKm = 20f;
            p.exposureCompensation = 1.2f; p.lookContrast = -10f; p.lookSaturation = -3f; p.lookShadowLift = 0.03f;
            return p;
        }

        public static LightingPreset CreateOvercast()
        {
            var p = CreateInstance<LightingPreset>();
            p.name = "LP_Overcast";
            p.sunElevationDeg = 30f; p.sunAzimuthDeg = 200f; p.turbidity = 4f; p.overcast = 1f; p.visibilityKm = 8f;
            p.exposureCompensation = 1.0f; p.lookContrast = -8f; p.lookSaturation = 0f; p.lookShadowLift = 0.025f;
            return p;
        }

        /// <summary>
        /// Low sun (track A7 cab check, visual review r2 A6 #1): 9 deg elevation, azimuth 60 deg (a June morning in
        /// Bialystok, ~05:30). At the WorldC spawn (heading ~209 deg) the sun is behind-left of the cab: the hard case,
        /// windscreen and passenger side in shade. WORKING_VALUE.
        /// </summary>
        public static LightingPreset CreateLowSun()
        {
            var p = CreateInstance<LightingPreset>();
            p.name = "LP_LowSun";
            p.sunElevationDeg = 9f; p.sunAzimuthDeg = 60f; p.turbidity = 3f; p.overcast = 0f; p.visibilityKm = 15f;
            p.exposureCompensation = 1.2f; p.lookContrast = -10f; p.lookSaturation = -3f; p.lookShadowLift = 0.03f;
            return p;
        }

        /// <summary>Dusk (track A7): sun 1 deg above the horizon at azimuth 300 deg (summer evening), hazy. WORKING_VALUE.</summary>
        public static LightingPreset CreateDusk()
        {
            var p = CreateInstance<LightingPreset>();
            p.name = "LP_Dusk";
            p.sunElevationDeg = 1f; p.sunAzimuthDeg = 300f; p.turbidity = 4f; p.overcast = 0.2f; p.visibilityKm = 12f;
            p.exposureCompensation = 1.2f; p.lookContrast = -10f; p.lookSaturation = -3f; p.lookShadowLift = 0.035f;
            return p;
        }
    }
}
