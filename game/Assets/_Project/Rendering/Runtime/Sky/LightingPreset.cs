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

        [Header("Exposure")]
        [Tooltip("Automatic: incident-meter EV100 of the horizontal illuminance (EV = log2(E/2.5)) plus compensation")]
        public bool autoExposure = true;
        public float ev100 = 15f;
        [Tooltip("Exposure compensation in stops (positive = brighter)")]
        public float exposureCompensation = 0.5f;

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
            p.sunElevationDeg = 42f; p.sunAzimuthDeg = 200f; p.turbidity = 2.5f; p.overcast = 0f; p.visibilityKm = 30f;
            return p;
        }

        public static LightingPreset CreateOvercast()
        {
            var p = CreateInstance<LightingPreset>();
            p.name = "LP_Overcast";
            p.sunElevationDeg = 30f; p.sunAzimuthDeg = 200f; p.turbidity = 4f; p.overcast = 1f; p.visibilityKm = 12f;
            p.exposureCompensation = 0.3f;
            return p;
        }
    }
}
