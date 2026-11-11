using UnityEngine;

namespace Game.Rendering
{
    /// <summary>
    /// A daylight condition (sun position, atmosphere, exposure, fog, look). Applied by <see cref="EnvironmentLighting"/>.
    /// Sky and exposure: docs/adr/0010; exposure table and tone curve ("like a phone photo", D23): docs/adr/0016.
    /// All WORKING_VALUE until compared with owner photos of the same place and time. The assets in
    /// Rendering/Settings/Lighting are rewritten from the Create* factories (LookDevAssets.EnsureAll): edit the code.
    /// </summary>
    [CreateAssetMenu(menuName = "Kamion/Rendering/Lighting Preset", fileName = "LP_New")]
    public sealed class LightingPreset : ScriptableObject
    {
        [Header("Sun")]
        [Tooltip("Sun altitude; below 0.5° the sky keeps its 0.5° shape and dims as civil twilight (SkyModel.TwilightFactorAt, ADR 0062)")]
        [Range(-6f, 89.5f)] public float sunElevationDeg = 42f;
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
        public Color groundAlbedo = new Color(0.15f, 0.155f, 0.135f);   // yard: asphalt/concrete + verge grass (r4 L2: was olive 0.16/0.17/0.12)
        [Tooltip("Saturation of the sky part of the ambient light (1 = the analytic sky). The probe has no inter-reflections " +
                 "from walls, trees and the truck itself, which grey real shadows; 0.55 removes the cyan shadows of the " +
                 "first renders (visual review r2 #3, docs/06 §2). WORKING_VALUE.")]
        [Range(0f, 1f)] public float ambientSkySaturation = 0.55f;
        [Tooltip("Low-sun ambient (review r4 L2): share of the sky probe samples that take the zenith chroma instead of the " +
                 "warm aureole/horizon chroma below 15 deg sun (SkyModel.AmbientProbe lowSunCool). Shade at low sun is lit by " +
                 "the blue dome; only the sun is warm. WORKING_VALUE.")]
        [Range(0f, 1f)] public float lowSunAmbientCool = 0.8f;

        [Header("Overcast structure and atmosphere (ADR 0080)")]
        [Tooltip("Overcast dome brightening toward the sun azimuth (SkyModel.OvercastDirectional; 0 = CIE standard overcast)")]
        [Range(0f, 2f)] public float overcastDirectional;
        [Tooltip("Share of the direct beam passing a thin overcast (soft directional light and faint shadows; taken out of the diffuse)")]
        [Range(0f, 0.3f)] public float overcastSunLeak;
        [Tooltip("Colour temperature of the overcast dome (K; 0 = achromatic D65). Fixed daylight white balance: > 6500 K reads cool (ADR 0080 r11)")]
        [Range(0f, 12000f)] public float overcastCctK;
        [Tooltip("Cloud deck contrast of the overcast dome (0 = flat dome): thick parts darker, thin parts lighter, mean 1")]
        [Range(0f, 0.6f)] public float cloudContrast;
        [Tooltip("ADR 0108: opacity of the photographic clear-cloud mask (0 = analytic blue sky). Sun/ambient metering stay unchanged.")]
        [Range(0f, 1f)] public float clearCloudCover;
        [Tooltip("ADR 0108: opt-in smoother sun-shadow filter on High only; 0 inherits the tier. Low unchanged.")]
        [Range(0, 3)] public int highSunShadowFilter;
        [Tooltip("ADR 0108: display-only blue-sky chroma multiplier above the haze horizon; 0/1 keep the analytic colour.")]
        [Range(1f, 4f)] public float clearSkySaturation = 1f;
        [Tooltip("Cloud texture tiles per unit of the cloud plane (plane at height 1; smaller = larger cloud masses)")]
        public float cloudScale = 0.16f;
        [Tooltip("Cloud drift (plane units per second; ~0.004 = 20 km/h at 1500 m)")]
        public Vector2 cloudWind = new Vector2(0.0035f, 0.0015f);
        [Tooltip("Ground haze layer: extra extinction at the layer base as a multiple of the visibility extinction (0 = uniform fog)")]
        [Range(0f, 4f)] public float hazeGroundFactor;
        [Tooltip("Scale height of the ground haze layer (m)")]
        public float hazeScaleHeightM = 60f;
        [Tooltip("Wet surfaces 0 dry .. 1 soaked (albedo, smoothness; a parameter, not weather simulation)")]
        [Range(0f, 1f)] public float wetness;
        [Tooltip("Share of the low spots holding standing water at wetness 1")]
        [Range(0f, 0.6f)] public float puddles = 0.3f;
        [Tooltip("Lawn variation strength (clumps, scorched patches, flowers, micro shading) of the grass sets")]
        [Range(0f, 1f)] public float grassVariation = 1f;

        [Header("Exposure (ADR 0016)")]
        [Tooltip("On: camera EV100 from the sun-elevation table (ExposureTable), like a phone's scene metering. " +
                 "Off: the fixed ev100 below.")]
        public bool autoExposure = true;
        public float ev100 = 15f;
        [Tooltip("Extra bias in stops on top of the table (positive = brighter). 0 for the reference presets.")]
        public float exposureCompensation;

        [Header("Look (owner decision D23: like a phone photo; ADR 0016)")]
        [Tooltip("Colour grading saturation (-100..100). Natural colours: 0 or slightly negative (docs/06 §2).")]
        [Range(-30f, 20f)] public float lookSaturation = 0f;
        [Tooltip("Phone-style partial white-balance adaptation toward the scene illuminant (0 = fixed daylight WB). ADR 0043 " +
                 "option (c): owner decision D27 = 0.5 in LP_LowSun only.")]
        [Range(0f, 1f)] public float whiteBalanceAdaptation = 0f;
        [Tooltip("Display black level (sRGB 0..1) of an albedo-0 pixel, applied after the tone curve (review r3 G1: ≤ 2 %).")]
        [Range(0f, 0.04f)] public float lookBlackLevel = 0.015f;
        [Tooltip("Scene value (exposed linear) where the tone curve reaches display white and clips. Phones clip an overcast " +
                 "sky (review r3: 20 % of the sky in the reference photo); the old Neutral tonemapper never exceeded ~85 %.")]
        [Range(0.6f, 3f)] public float lookWhiteClip = 0.7f;
        [Tooltip("Highlight desaturation towards white near the clip (0 = none, 1 = grey at the clip): a clipped sky goes " +
                 "white, not yellow (review r3 G5).")]
        [Range(0f, 1f)] public float lookHighlightDesaturation = 0.4f;
        [Tooltip("ADR 0080 contrast variant: toe strength s of LookGrading.Toe (0 = the D23 curve unchanged)")]
        [Range(0f, 0.9f)] public float lookToe;
        [Tooltip("Toe half-point p (scene linear)")]
        [Range(0.02f, 0.4f)] public float lookToeP = 0.12f;
        [Tooltip("Scene value kept fixed by the toe gain (0.18 = mid-grey held; higher = mid-tones slightly darker)")]
        [Range(0.1f, 0.6f)] public float lookTonePivot = 0.3f;

        /// <summary>Camera EV100 of this preset (table from sun elevation and cloud, minus the bias). No per-frame pass.</summary>
        public float ResolveEv100(SkyModel probe) =>
            (autoExposure ? ExposureTable.Ev100(probe.TrueSunElevationDeg, probe.Overcast) : ev100) - exposureCompensation - ExposureBiasOverride;

        /// <summary>ADR 0080 owner A/B renders only (rq_ev): extra exposure bias in stops, 0 = none. Not a default.</summary>
        public static float ExposureBiasOverride;
        /// <summary>ADR 0080 r11 A/B (rq_skycct): overcast dome colour temperature in K, 0 = achromatic; &lt; 0 = the preset's.</summary>
        public static float OvercastCctOverride = -1f;

        /// <summary>Builds the sky model with the resolved exposure (two passes: illuminance does not depend on exposure).</summary>
        public SkyModel CreateModel(float wbOverride = -1f)
        {
            var probe = new SkyModel(sunElevationDeg, sunAzimuthDeg, turbidity, overcast, 0f);
            return new SkyModel(sunElevationDeg, sunAzimuthDeg, turbidity, overcast, ResolveEv100(probe),
                wbOverride >= 0f ? wbOverride : whiteBalanceAdaptation, overcastDirectional, overcastSunLeak,
                OvercastCctOverride >= 0f ? OvercastCctOverride : overcastCctK);
        }

        public static LightingPreset CreateClear()
        {
            var p = CreateInstance<LightingPreset>();
            p.name = "LP_Clear";
            p.sunElevationDeg = 42f; p.sunAzimuthDeg = 200f; p.turbidity = 2.5f; p.overcast = 0f; p.visibilityKm = 20f;
            // ADR 0108 r1 WORKING_VALUE: measured 1.2/1.8 ablation removes the white-van plateau
            // above the fixed asphalt/mid-grey anchors, without changing exposure.
            p.lookWhiteClip = 1.8f;
            // ADR 0108 r1 WORKING_VALUE: the route reference photos show scattered cumulus in blue sky.
            p.clearCloudCover = 1f;
            p.clearSkySaturation = 2f; // ADR 0108: 1/2/3/4 ablation against the daytime reference skies.
            return p;
        }

        public static LightingPreset CreateOvercast()
        {
            var p = CreateInstance<LightingPreset>();
            p.name = "LP_Overcast";
            // ADR 0080: sun at 41 deg / 200 deg (within 3 deg of the baked LP_Clear sun, so the ADR 0064 far ground shadows
            // carry the faint leaked-beam shadows beyond the realtime distance), a thin stratocumulus deck.
            p.sunElevationDeg = 41f; p.sunAzimuthDeg = 200f; p.turbidity = 4f; p.overcast = 1f; p.visibilityKm = 8f;
            p.overcastDirectional = 0.6f; p.overcastSunLeak = 0.05f;
            p.cloudContrast = 0.21f;
            // r11: denser and shallower ground layer (was 1.6 / 60 m): the tree line at 100-500 m lifts toward the sky
            // (15 / 39 / 55 % horizon colour at 100 / 300 / 500 m at eye height) while tall distant objects, above the
            // layer, change little. Ground-level visibility ~2.4 km, a damp overcast day. WORKING_VALUE.
            p.hazeGroundFactor = 2.4f; p.hazeScaleHeightM = 40f;
            // ADR 0080 r11: the dome is slightly cool against the fixed daylight white balance (reference photos: sky
            // B - R +7..+16). WORKING_VALUE, tuned on the control cameras against those photos.
            p.overcastCctK = 6800f;
            // Owner decision 2026-11-10 (ADR 0080): contrast variant 3 "deep" - broad toe about the sky value and -0.2 EV.
            p.lookToe = 0.9f; p.lookToeP = 0.4f; p.lookTonePivot = 0.6f; p.exposureCompensation = -0.2f;
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
            p.highSunShadowFilter = 3;
            p.lookSaturation = -3f;
            p.whiteBalanceAdaptation = 0.5f; // owner decision D27 (2026-11-10): phone-style WB at low sun, ADR 0043
            return p;
        }

        /// <summary>
        /// Dusk (track A7): civil twilight, sun 5 deg below the horizon at azimuth 300 deg (summer evening, ~30 min after
        /// sunset), hazy. ADR 0062 / review r8 N-20: at the old +1 deg the sky still gave ~2.4 klx, so a street lamp's
        /// ~30 lx pool was ~1 % of the background - physically invisible (and real lamps are often still off then). At
        /// -5 deg the sky gives ~8 lx: the lamps are on in every Polish town (astronomical clocks / twilight switches) and
        /// their pools read at 1.5-2.5x the background. Screen brightness of the ambient-lit scene is kept (the exposure
        /// table follows the twilight, like a phone), so the r3 G3 "2-3 EV under overcast noon" still holds. WORKING_VALUE.
        /// </summary>
        public static LightingPreset CreateDusk()
        {
            var p = CreateInstance<LightingPreset>();
            p.name = "LP_Dusk";
            p.sunElevationDeg = -5f; p.sunAzimuthDeg = 300f; p.turbidity = 4f; p.overcast = 0.2f; p.visibilityKm = 12f;
            p.lookSaturation = -3f;
            return p;
        }

        /// <summary>ADR 0108 r2 WORKING_VALUE: a separate night appearance at the existing twilight model's
        /// lower bound. This is not an astronomical night-sky fit. Extra exposure restraint darkens ambient-lit
        /// surfaces while fixed-luminance lamps gain contrast against the dimmer sky; dusk remains unchanged.</summary>
        public static LightingPreset CreateNight()
        {
            var p = CreateDusk();
            p.name = "LP_Night";
            p.sunElevationDeg = SkyModel.MinTwilightElevationDeg;
            p.exposureCompensation = -4f; // provisional; image ablation -2/-3/-4/-5 EV before choosing.
            return p;
        }
    }

    /// <summary>
    /// Camera EV100 by sun elevation and cloud (ADR 0016), replacing the incident meter on the horizontal illuminance
    /// (review r3 G2/G3). Values include the D23 "phone" brightening (+1 EV over an incident meter at high sun):
    /// - high sun: unchanged from ADR 0010 + D23 (clear 42° → 13.9, overcast 30° → 11.1);
    /// - low sun: a phone meters the scene, where sunlit walls are bright, so it exposes ~1.4 EV less than the horizontal
    ///   meter would (9°: 13.1 instead of 11.1 - a 0.6-albedo wall facing the sun ≈ 0.7 linear, ~90 %, instead of 2.8);
    /// - dusk: no compensation of the falling light down to 0.5° - sun 1° hazy lands 2-2.5 EV darker on screen than an
    ///   overcast noon;
    /// - civil twilight (sun below 0.5°, ADR 0062): the exposure follows the dimming sky (a phone lengthens its exposure),
    ///   with the scene 0.2 EV darker by -4° (higher EV100), so the ambient-lit scene stays ~2.9 EV under overcast noon while emissive lamps
    ///   (fixed cd/m²) and their pools gain on the background.
    /// WORKING_VALUE (to be compared with owner photos at the same times).
    /// </summary>
    public static class ExposureTable
    {
        static readonly float[] k_El = { 0f, 5f, 10f, 20f, 30f, 45f, 90f };
        static readonly float[] k_Clear = { 11.5f, 12.5f, 13.3f, 13.5f, 13.7f, 13.9f, 14.0f };
        static readonly float[] k_Overcast = { 10.0f, 10.3f, 10.6f, 10.9f, 11.1f, 11.4f, 11.6f };

        public static float Ev100(float sunElevationDeg, float overcast)
        {
            if (sunElevationDeg < 0.5f)
            {
                float twilight = SkyModel.TwilightFactorAt(sunElevationDeg);
                float deepen = 0.2f * Mathf.Clamp01((0.5f - sunElevationDeg) / 4.5f);
                return Ev100(0.5f, overcast) + Mathf.Log(twilight, 2f) + deepen;
            }
            float el = Mathf.Clamp(sunElevationDeg, k_El[0], k_El[k_El.Length - 1]);
            int i = 0;
            while (i < k_El.Length - 2 && el > k_El[i + 1]) i++;
            float t = (el - k_El[i]) / (k_El[i + 1] - k_El[i]);
            float clear = Mathf.Lerp(k_Clear[i], k_Clear[i + 1], t);
            float over = Mathf.Lerp(k_Overcast[i], k_Overcast[i + 1], t);
            return Mathf.Lerp(clear, over, Mathf.Clamp01(overcast));
        }
    }
}
