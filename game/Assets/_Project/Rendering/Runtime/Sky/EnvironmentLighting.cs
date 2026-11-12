using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering
{
    /// <summary>
    /// Applies a <see cref="LightingPreset"/> to the scene from one <see cref="SkyModel"/>: sun light direction, colour and
    /// intensity, sky material parameters, ambient SH (sky + ground), reflection cubemap and exponential fog. Everything is
    /// in exposed display units (fixed exposure from the preset), so no auto-exposure pass is needed on mobile.
    /// Runs in edit mode too (scene builders and visual QA call <see cref="Apply"/> directly).
    /// </summary>
    [ExecuteAlways]
    public sealed class EnvironmentLighting : MonoBehaviour
    {
        public LightingPreset[] presets;
        public int activeIndex;
        public Light sun;
        public Material skyMaterial;
        [Tooltip("Fog density multiplier on top of Koschmieder (1 = physical extinction of the preset's visibility)")]
        public float fogDensityScale = 1f;

        public static EnvironmentLighting Instance { get; private set; }
        /// <summary>ADR 0043 option (c) A/B renders only: &lt; 0 = the preset's value (0 for every preset). Not a default.</summary>
        public static float WhiteBalanceOverride = -1f;
        public SkyModel Model { get; private set; }
        public LightingPreset Active => presets != null && presets.Length > 0 ? presets[Mathf.Clamp(activeIndex, 0, presets.Length - 1)] : null;

        Cubemap m_Reflection;
        // Look grading (D23): a runtime-only global volume with this preset's colour adjustments; never saved, so the
        // shared world profile (tonemapper only) stays untouched.
        Volume m_LookVolume;
        VolumeProfile m_LookProfile;
        ColorAdjustments m_ColorAdj;
        Tonemapping m_Tonemap;
        ColorCurves m_Curves;
        TextureCurve m_Master, m_LumSat;

        static readonly int k_PerezY = Shader.PropertyToID("_SkyPerezY"), k_PerezX = Shader.PropertyToID("_SkyPerezX"),
            k_PerezYc = Shader.PropertyToID("_SkyPerezYc"), k_PerezE = Shader.PropertyToID("_SkyPerezE"),
            k_Zenith = Shader.PropertyToID("_SkyZenith"), k_Misc = Shader.PropertyToID("_SkyMisc"),
            k_SunDir = Shader.PropertyToID("_SkySunDir"), k_SunColor = Shader.PropertyToID("_SkySunColor"),
            k_FogColor = Shader.PropertyToID("_SkyFogColor"), k_OvercastColor = Shader.PropertyToID("_SkyOvercastColor"), k_Chroma = Shader.PropertyToID("_SkyChroma");
        Texture2D m_ChromaTex;
        static readonly int k_Exposure = Shader.PropertyToID("_KamionExposure");

        void OnEnable()
        {
            Instance = this;
            // Dusk street lighting (review r4 L3) lives next to the sun that switches it.
            if (GetComponent<StreetLamps>() == null) gameObject.AddComponent<StreetLamps>().hideFlags = HideFlags.DontSave;
            QualityProfileApplier.Applied += OnTierApplied;
            RenderPipelineManager.beginContextRendering += OnBeginRendering;
            Apply();
        }

        // ADR 0080: atmosphere globals before every frame; a changed owner A/B override (exposure bias, look variant)
        // rebuilds the model / curve once.
        Color m_FogExposed;
        float m_AppliedEvBias, m_AppliedCct = -1f;
        int m_AppliedLook = -1;
        void OnBeginRendering(ScriptableRenderContext ctx, System.Collections.Generic.List<Camera> cams)
        {
            if (m_AppliedEvBias != LightingPreset.ExposureBiasOverride || m_AppliedLook != WorldAtmosphere.LookVariant ||
                m_AppliedCct != LightingPreset.OvercastCctOverride) Apply();
            WorldAtmosphere.Push(this, m_FogExposed);
        }

        void OnDisable()
        {
            KamionHeadlamps.Reset();
            Shader.SetGlobalFloat("_KamionDimColourDesaturation",0f);
            QualityProfileApplier.Applied -= OnTierApplied;
            RenderPipelineManager.beginContextRendering -= OnBeginRendering;
            if (Instance == this) Instance = null;
        }

        void OnDestroy()
        {
            m_Master?.Release(); m_LumSat?.Release();
            if (m_LookProfile != null) { if (Application.isPlaying) Destroy(m_LookProfile); else DestroyImmediate(m_LookProfile); }
            if (m_LookVolume != null) { if (Application.isPlaying) Destroy(m_LookVolume.gameObject); else DestroyImmediate(m_LookVolume.gameObject); }
            if (m_ChromaTex != null) { if (Application.isPlaying) Destroy(m_ChromaTex); else DestroyImmediate(m_ChromaTex); }
            if (m_Reflection != null) { if (Application.isPlaying) Destroy(m_Reflection); else DestroyImmediate(m_Reflection); }
        }

        public bool SetPreset(string presetName)
        {
            if (presets == null) return false;
            for (int i = 0; i < presets.Length; i++)
            {
                if (presets[i] == null) continue;
                string n = presets[i].name;
                if (string.Equals(n, presetName, System.StringComparison.OrdinalIgnoreCase) ||
                    string.Equals(n, "LP_" + presetName, System.StringComparison.OrdinalIgnoreCase))
                {
                    activeIndex = i;
                    Apply();
                    return true;
                }
            }
            return false;
        }

        public void Apply()
        {
            var p = Active;
            if (p == null) return;
            Model = p.CreateModel(WhiteBalanceOverride);
            var m = Model;
            m_AppliedEvBias = LightingPreset.ExposureBiasOverride;
            m_AppliedLook = WorldAtmosphere.LookVariant;
            m_AppliedCct = LightingPreset.OvercastCctOverride;
            // Display value per cd/m^2: emissive surfaces (truck lamps, A7) are authored in physical luminance.
            Shader.SetGlobalFloat(k_Exposure, m.Exposure);
            StreetLamps.SetSunElevation(m.TrueSunElevationDeg);

            // ---- sun ----
            if (sun == null) sun = RenderSettings.sun;
            if (sun != null)
            {
                // True direction (below the horizon in twilight; the light is then off): cab clock, auto low beam.
                sun.transform.rotation = Quaternion.LookRotation(-m.TrueSunDirection, Vector3.up);
                Color c = m.SunColor;
                float max = Mathf.Max(c.r, Mathf.Max(c.g, c.b));
                sun.color = (c / max).gamma;
                sun.intensity = m.SunLightIntensity * max;
                sun.enabled = m.SunNormalIlluminanceLux > 1f;
                sun.shadows = LightShadows.Soft;   // URP asset decides whether soft filtering is supported per tier
                ApplySunShadowFilter();
                RenderSettings.sun = sun;
            }

            // ---- sky ----
            Color fog = m.HorizonColorExposed();
            m_FogExposed = fog;
            if (skyMaterial != null)
            {
                m.GetShaderParameters(out var py, out var px, out var pyc, out var pe, out var zen, out var misc);
                skyMaterial.SetVector(k_PerezY, py); skyMaterial.SetVector(k_PerezX, px); skyMaterial.SetVector(k_PerezYc, pyc);
                skyMaterial.SetVector(k_PerezE, pe); skyMaterial.SetVector(k_Zenith, zen); skyMaterial.SetVector(k_Misc, misc);
                skyMaterial.SetVector(k_SunDir, m.SunDirection);
                skyMaterial.SetVector(k_SunColor, (Vector4)m.SunColor);
                skyMaterial.SetVector(k_FogColor, (Vector4)fog);
                var ow = m.AdaptedWhite; skyMaterial.SetVector(k_OvercastColor, new Vector4(ow.r, ow.g, ow.b, 1f));
                if (m_ChromaTex != null) { if (Application.isPlaying) Destroy(m_ChromaTex); else DestroyImmediate(m_ChromaTex); }
                m_ChromaTex = m.CreateChromaTexture();
                skyMaterial.SetTexture(k_Chroma, m_ChromaTex);
                RenderSettings.skybox = skyMaterial;
            }

            // ---- ambient (L2 SH of sky + ground) ----
            RenderSettings.ambientMode = AmbientMode.Custom;
            RenderSettings.ambientProbe = m.AmbientProbe(p.groundAlbedo, 24, p.ambientSkySaturation, p.lowSunAmbientCool);
            RenderSettings.ambientIntensity = 1f;

            // ---- specular environment ----
            if (m_Reflection != null) { if (Application.isPlaying) Destroy(m_Reflection); else DestroyImmediate(m_Reflection); }
            bool gradeReflectedSky = (p.skyDisplayGain > 0f && p.skyDisplayGain < 1f) || p.skyDisplayDesaturation > 0f;
            m_Reflection = gradeReflectedSky
                ? m.ReflectionCubemap(p.groundAlbedo, skyPresentation: c => WorldAtmosphere.DisplaySkyFog(p, c))
                : m.ReflectionCubemap(p.groundAlbedo);
            m_Reflection.hideFlags = HideFlags.DontSave;
            RenderSettings.defaultReflectionMode = DefaultReflectionMode.Custom;
            RenderSettings.customReflectionTexture = m_Reflection;
            RenderSettings.reflectionIntensity = 1f;

            ApplyLook(p);

            // ---- aerial perspective: Beer-Lambert extinction with horizon in-scatter colour ----
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.Exponential;
            RenderSettings.fogDensity = 3.912f / Mathf.Max(0.5f, p.visibilityKm * 1000f) * fogDensityScale;
            // RenderSettings.fogColor is specified in sRGB like other colours and linearised by Unity.
            var displayFog = WorldAtmosphere.DisplaySkyFog(p, fog);
            var fogClamped = new Color(Mathf.Min(displayFog.r, 1f), Mathf.Min(displayFog.g, 1f), Mathf.Min(displayFog.b, 1f), 1f);
            RenderSettings.fogColor = fogClamped.gamma;

            // ---- vehicle reflections (r6 E1/E2, KamionVehicleEnv.hlsl): ground plane + horizon for the analytic env ----
            Color g = p.groundAlbedo * m.AdaptedWhite * (m.HorizontalIlluminanceLux * m.Exposure / Mathf.PI);
            Shader.SetGlobalVector(k_GroundEnv, new Vector4(g.r, g.g, g.b, RenderSettings.fogDensity));
            Shader.SetGlobalVector(k_HorizonEnv, new Vector4(displayFog.r, displayFog.g, displayFog.b, 1f));
            ApplySkyCap();
            WorldAtmosphere.Push(this, m_FogExposed);
        }

        static readonly int k_GroundEnv = Shader.PropertyToID("_KamionGroundEnv"), k_HorizonEnv = Shader.PropertyToID("_KamionHorizonEnv"),
            k_SkyCap = Shader.PropertyToID("_KamionSkyCap");

        /// <summary>Display caps of the sky dome at the horizon and towards the zenith (review r6 L4: phone local tone mapping).</summary>
        public const float SkyCapHorizonDisplay = 0.98f, SkyCapZenithDisplay = 0.875f;

        void OnTierApplied(QualityProfile.Tier t)
        {
            ApplySkyCap();
            ApplySunShadowFilter();
        }

        /// <summary>ADR 0108: the preset explicitly opts High into a smoother filter, without raising atlas size.
        /// Returning to another preset/tier restores pipeline inheritance, including Low's disabled soft shadows.</summary>
        public static SoftShadowQuality SunShadowFilter(LightingPreset preset, string tier) =>
            preset != null && tier == "High" && preset.highSunShadowFilter > 0
                ? (SoftShadowQuality)Mathf.Clamp(preset.highSunShadowFilter, 1, 3)
                : SoftShadowQuality.UsePipelineSettings;

        void ApplySunShadowFilter()
        {
            if (sun != null)
                sun.GetUniversalAdditionalLightData().softShadowQuality = SunShadowFilter(Active,
                    QualityProfileApplier.HasCurrent ? QualityProfileApplier.Current.name : null);
        }

        /// <summary>
        /// Review r6 L4: the overcast dome clipped to 254/254/254 on the post-processing tiers (the D23 curve clips at
        /// lookWhiteClip = 0.7 and the overcast sky is &gt; 0.7 above ~5 deg). A phone keeps the cloud deck's tone with local
        /// tone mapping: here the sky shader compresses the dome (soft knee) to the exposed value that the active tone curve
        /// maps to 98 % at the horizon and 87.5 % towards the zenith. Low (no post): the same display targets through plain
        /// sRGB. The surfaces, fog and reflection cubes keep the physical radiance (D23/D27 unchanged for everything else).
        /// </summary>
        void ApplySkyCap()
        {
            var p = Active;
            if (p == null) return;
            bool post = QualityProfileApplier.HasCurrent && QualityProfileApplier.Current.postProcessing;
            WorldAtmosphere.ResolveLook(p, out float toe, out float toeP, out float pivot);   // ADR 0080 contrast variant
            float h, z;
            if (post)
            {
                var caps = GradedSkyCaps(p);
                h = caps.x; z = caps.y;
            }
            else
            {
                // no LUT: the shaders apply the toe themselves (KamionTone), so the cap is the toe's pre-image
                h = LookGrading.InverseToe(LookGrading.SrgbToLinear(SkyCapHorizonDisplay), toe, toeP, pivot);
                z = LookGrading.InverseToe(LookGrading.SrgbToLinear(SkyCapZenithDisplay), toe, toeP, pivot);
            }
            Shader.SetGlobalVector(k_SkyCap, new Vector4(h, z, 1f, 0f));
        }

        /// <summary>The actual pre-grading sky inputs of the post-processing tiers. A Low grade comparison must use
        /// these same inputs, rather than independently chasing a display target the sampled LUT may not reach.</summary>
        public static Vector2 GradedSkyCaps(LightingPreset preset)
        {
            WorldAtmosphere.ResolveLook(preset, out float toe, out float toeP, out float pivot);
            var curve = new AnimationCurve(LookGrading.MasterCurveKeys(preset.lookBlackLevel, preset.lookWhiteClip, toe, toeP, pivot));
            return new Vector2(InverseDisplay(curve, SkyCapHorizonDisplay, preset.lookWhiteClip),
                InverseDisplay(curve, SkyCapZenithDisplay, preset.lookWhiteClip));
        }

        /// <summary>Exposed scene value that the D23 master curve maps to <paramref name="display"/> (sRGB), by bisection.</summary>
        public static float InverseDisplay(AnimationCurve master, float display, float whiteClip)
        {
            float lo = 0f, hi = Mathf.Max(whiteClip, 0.75f) + 0.05f;
            for (int i = 0; i < 40; i++)
            {
                float mid = 0.5f * (lo + hi);
                if (LookGrading.Display(master, mid) < display) lo = mid; else hi = mid;
            }
            return 0.5f * (lo + hi);
        }

        void ApplyLook(LightingPreset p)
        {
            if (m_LookVolume == null)
            {
                const string name = "LookVolume (runtime)";
                var t = transform.Find(name);
                var go = t != null ? t.gameObject : new GameObject(name);
                go.hideFlags = HideFlags.DontSave | HideFlags.NotEditable;
                go.transform.SetParent(transform, false);
                m_LookVolume = go.GetComponent<Volume>();
                if (m_LookVolume == null) m_LookVolume = go.AddComponent<Volume>();
                m_LookVolume.isGlobal = true;
                m_LookVolume.priority = 10f;
            }
            if (m_LookProfile == null)
            {
                m_LookProfile = ScriptableObject.CreateInstance<VolumeProfile>();
                m_LookProfile.name = "VP_Look (runtime)";
                m_LookProfile.hideFlags = HideFlags.DontSave;
                m_ColorAdj = m_LookProfile.Add<ColorAdjustments>(true);
                m_Tonemap = m_LookProfile.Add<Tonemapping>(true);
                m_Curves = m_LookProfile.Add<ColorCurves>(true);
            }
            m_LookVolume.sharedProfile = m_LookProfile;
            m_ColorAdj.contrast.Override(0f);
            m_ColorAdj.saturation.Override(p.lookSaturation);
            m_ColorAdj.postExposure.Override(0f);   // exposure is pre-multiplied into the lights (also on LDR tiers)
            // ADR 0016: the phone tone curve replaces the Neutral tonemapper (VP_World) on the post-processing tiers.
            m_Tonemap.mode.Override(TonemappingMode.None);
            m_Master?.Release();
            m_LumSat?.Release();
            WorldAtmosphere.ResolveLook(p, out float toe, out float toeP, out float pivot);   // ADR 0080 contrast variant
            m_Master = new TextureCurve(LookGrading.MasterCurveKeys(p.lookBlackLevel, p.lookWhiteClip, toe, toeP, pivot), 0f, false, new Vector2(0f, 1f));
            m_LumSat = new TextureCurve(LookGrading.HighlightDesaturationKeys(p.lookHighlightDesaturation, p.lookWhiteClip), 0.5f, false, new Vector2(0f, 1f));
            m_Curves.master.Override(m_Master);
            m_Curves.lumVsSat.Override(m_LumSat);
        }
    }
}
