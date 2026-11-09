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
            k_FogColor = Shader.PropertyToID("_SkyFogColor"), k_Chroma = Shader.PropertyToID("_SkyChroma");
        Texture2D m_ChromaTex;
        static readonly int k_Exposure = Shader.PropertyToID("_KamionExposure");

        void OnEnable()
        {
            Instance = this;
            Apply();
        }

        void OnDisable()
        {
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
            Model = p.CreateModel();
            var m = Model;
            // Display value per cd/m^2: emissive surfaces (truck lamps, A7) are authored in physical luminance.
            Shader.SetGlobalFloat(k_Exposure, m.Exposure);

            // ---- sun ----
            if (sun == null) sun = RenderSettings.sun;
            if (sun != null)
            {
                sun.transform.rotation = Quaternion.LookRotation(-m.SunDirection, Vector3.up);
                Color c = m.SunColor;
                float max = Mathf.Max(c.r, Mathf.Max(c.g, c.b));
                sun.color = (c / max).gamma;
                sun.intensity = m.SunLightIntensity * max;
                sun.enabled = m.SunNormalIlluminanceLux > 1f;
                sun.shadows = LightShadows.Soft;   // URP asset decides whether soft filtering is supported per tier
                RenderSettings.sun = sun;
            }

            // ---- sky ----
            Color fog = m.HorizonColorExposed();
            if (skyMaterial != null)
            {
                m.GetShaderParameters(out var py, out var px, out var pyc, out var pe, out var zen, out var misc);
                skyMaterial.SetVector(k_PerezY, py); skyMaterial.SetVector(k_PerezX, px); skyMaterial.SetVector(k_PerezYc, pyc);
                skyMaterial.SetVector(k_PerezE, pe); skyMaterial.SetVector(k_Zenith, zen); skyMaterial.SetVector(k_Misc, misc);
                skyMaterial.SetVector(k_SunDir, m.SunDirection);
                skyMaterial.SetVector(k_SunColor, (Vector4)m.SunColor);
                skyMaterial.SetVector(k_FogColor, (Vector4)fog);
                if (m_ChromaTex != null) { if (Application.isPlaying) Destroy(m_ChromaTex); else DestroyImmediate(m_ChromaTex); }
                m_ChromaTex = m.CreateChromaTexture();
                skyMaterial.SetTexture(k_Chroma, m_ChromaTex);
                RenderSettings.skybox = skyMaterial;
            }

            // ---- ambient (L2 SH of sky + ground) ----
            RenderSettings.ambientMode = AmbientMode.Custom;
            RenderSettings.ambientProbe = m.AmbientProbe(p.groundAlbedo, 24, p.ambientSkySaturation);
            RenderSettings.ambientIntensity = 1f;

            // ---- specular environment ----
            if (m_Reflection != null) { if (Application.isPlaying) Destroy(m_Reflection); else DestroyImmediate(m_Reflection); }
            m_Reflection = m.ReflectionCubemap(p.groundAlbedo);
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
            var fogClamped = new Color(Mathf.Min(fog.r, 1f), Mathf.Min(fog.g, 1f), Mathf.Min(fog.b, 1f), 1f);
            RenderSettings.fogColor = fogClamped.gamma;
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
            m_Master = new TextureCurve(LookGrading.MasterCurveKeys(p.lookBlackLevel, p.lookWhiteClip), 0f, false, new Vector2(0f, 1f));
            m_LumSat = new TextureCurve(LookGrading.HighlightDesaturationKeys(p.lookHighlightDesaturation, p.lookWhiteClip), 0.5f, false, new Vector2(0f, 1f));
            m_Curves.master.Override(m_Master);
            m_Curves.lumVsSat.Override(m_LumSat);
        }
    }
}
