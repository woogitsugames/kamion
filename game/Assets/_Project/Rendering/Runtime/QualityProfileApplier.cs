using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering
{
    /// <summary>
    /// Applies the camera-side part of the active tier from <see cref="QualityProfile"/> (URP asset settings are baked by
    /// the editor): post-processing on/off, tonemapping mode on the scene volume, post AA, dithering, far clip, the world
    /// detail shader keyword and anisotropy / mip bias of the world surface textures. Re-applies when the quality level
    /// changes (tier button in the diagnostics overlay, launch argument). Allocation-free after the first frame.
    /// </summary>
    [DefaultExecutionOrder(-500)]
    public sealed class QualityProfileApplier : MonoBehaviour
    {
        public const string WorldDetailKeyword = "_KAMION_WORLD_DETAIL";
        public const float MaxArchitecturalGlassReceiverBias = 0.08f; // ADR0098 WORKING_VALUE, smallest tested acceptable.
        public const float HighRcasSharpness = 0.75f; // ADR 0108 r1: measured ablation 0 / .25 / .5 / .75.

        /// <summary>Restore the High FSR detail lost by ADR0098 without changing other tiers or explicit A/B values.
        /// This resolves the legacy serialized zero at the camera boundary; no new QualityProfile field/migration.</summary>
        public static QualityProfile.Tier ApplyLightPolicy(QualityProfile.Tier t)
        {
            if (t.name == "High" && t.upscalingFilter == UpscalingFilterSelection.FSR &&
                t.fsrSharpness <= 0f && !RenderOverrides.FsrSharpness.HasValue)
                t.fsrSharpness = HighRcasSharpness;
            return t;
        }

        public static float ArchitecturalGlassBias(QualityProfile.Tier t, float? requested = null)
        {
            float policy = t.name == "Medium" || t.name == "High" ? MaxArchitecturalGlassReceiverBias : 0f;
            return Mathf.Clamp(requested ?? policy, 0f, MaxArchitecturalGlassReceiverBias);
        }
        public const string GlassFastKeyword = "_KAMION_GLASS_FAST";   // ADR 0106
        static readonly int k_ClearCoatOff = Shader.PropertyToID("_KamionClearCoatOff");
        static readonly int k_GrimeDetailOff = Shader.PropertyToID("_KamionGrimeDetailOff");
        static readonly int k_SkyDitherOff = Shader.PropertyToID("_KamionSkyDitherOff");
        static readonly int k_GlassShadowBias = Shader.PropertyToID("_KamionGlassShadowBias");

        public Camera targetCamera;
        public Volume volume;
        [Tooltip("World surface textures whose anisotropy / mip bias follow the tier")]
        public Texture[] worldTextures;

        int m_AppliedLevel = -1;
        Tonemapping m_Tonemapping;

        public static QualityProfile.Tier Current { get; private set; }
        public static bool HasCurrent { get; private set; }

        void OnEnable()
        {
            // ADR 0046: adaptive render scale + thermal fallback (only tiers that enable them; play mode / player only).
            if (Application.isPlaying && GetComponent<AdaptiveFrameDriver>() == null) gameObject.AddComponent<AdaptiveFrameDriver>();
            // ADR 0068: per-pass cost for the [DIAG] line and the rq_ab on-device A/B.
            if (Application.isPlaying && GetComponent<ExtraViewCostMonitor>() == null) gameObject.AddComponent<ExtraViewCostMonitor>();
            ApplyNow();
        }

        void LateUpdate()
        {
            if (QualitySettings.GetQualityLevel() != m_AppliedLevel) ApplyNow();
        }

        public void ApplyNow()
        {
            m_AppliedLevel = QualitySettings.GetQualityLevel();
            var profile = QualityProfile.Load();
            if (profile == null || !profile.TryGet(QualityTiers.Current, out var t)) return;
            if (RenderOverrides.Any)
            {
                t = RenderOverrides.ApplyTo(t);
            }
            var cam = targetCamera != null ? targetCamera : ViewCameraResolver.Resolve(null);
            Apply(t, cam, volume, worldTextures, ref m_Tonemapping);
            if (cam != null && RenderOverrides.CullMask.HasValue && Application.isPlaying) cam.cullingMask &= RenderOverrides.CullMask.Value;   // ADR 0106
        }

        /// <summary>
        /// Profiling overrides that live on the URP asset (baked per tier by the editor): written to the active asset at
        /// run time only (player builds / play mode with launch arguments), never saved.
        /// </summary>
        static void ApplyPipelineOverrides(QualityProfile.Tier t)
        {
            if (!(GraphicsSettings.currentRenderPipeline is UniversalRenderPipelineAsset urp)) return;
            if (RenderOverrides.Msaa.HasValue) urp.msaaSampleCount = t.msaa;
            if (RenderOverrides.RenderScale.HasValue) urp.renderScale = t.renderScale;
            if (RenderOverrides.ShadowDistance.HasValue) urp.shadowDistance = t.shadowDistance;
            if (RenderOverrides.ShadowCascades.HasValue) urp.shadowCascadeCount = t.shadowCascades;   // ADR 0068 A/B
            if (RenderOverrides.ShadowResolution.HasValue) urp.mainLightShadowmapResolution = t.shadowResolution;
            if (RenderOverrides.ShadowDepthBias.HasValue) urp.shadowDepthBias = t.shadowDepthBias;
            if (RenderOverrides.ShadowNormalBias.HasValue) urp.shadowNormalBias = t.shadowNormalBias;
            if (RenderOverrides.ShadowSplit1.HasValue || RenderOverrides.ShadowSplit2.HasValue)
            {
                urp.cascade2Split = t.cascade2Split;
                urp.cascade3Split = new Vector2(t.cascade4Split.x, t.cascade4Split.y);
                urp.cascade4Split = t.cascade4Split;
            }
            if (RenderOverrides.Hdr.HasValue) urp.supportsHDR = t.hdr;
            if (RenderOverrides.Upscale != null) urp.upscalingFilter = t.upscalingFilter;   // ADR 0062 A/B
            if (RenderOverrides.FsrSharpness.HasValue || (t.name == "High" && t.upscalingFilter == UpscalingFilterSelection.FSR))
            { urp.fsrOverrideSharpness = true; urp.fsrSharpness = t.fsrSharpness; }
            if (RenderOverrides.LodBias.HasValue && Application.isPlaying) QualitySettings.lodBias = t.lodBias;   // ADR 0106
        }

        /// <summary>Raised after a tier was applied (vegetation reads <see cref="Current"/>).</summary>
        public static event System.Action<QualityProfile.Tier> Applied;

        /// <summary>Static entry for editor tools (visual QA) that render without entering play mode.</summary>
        public static void Apply(QualityProfile.Tier t, Camera cam, Volume volume, Texture[] worldTextures, ref Tonemapping tonemapping)
        {
            // Both the player and editor QA resolve the legacy High zero here. Other tiers retain baked policy.
            t = ApplyLightPolicy(t);
            if (RenderOverrides.Any || (t.name == "High" && t.upscalingFilter == UpscalingFilterSelection.FSR))
                ApplyPipelineOverrides(t);
#if UNITY_EDITOR
            if (GraphicsSettings.currentRenderPipeline is UniversalRenderPipelineAsset pipeline)
                Debug.Log($"[RQ_PIPELINE] scale={pipeline.renderScale} fsrSharpness={pipeline.fsrSharpness} fsrOverride={pipeline.fsrOverrideSharpness} cascades={pipeline.shadowCascadeCount} shadowResolution={pipeline.mainLightShadowmapResolution} shadowDistance={pipeline.shadowDistance} bias={pipeline.shadowDepthBias}/{pipeline.shadowNormalBias} splits={pipeline.cascade3Split}");
#endif
            Current = t;
            HasCurrent = true;
            if (cam != null)
            {
                cam.farClipPlane = t.cameraFarClip;
                cam.allowMSAA = t.msaa > 1;
                cam.allowHDR = t.hdr;
                var data = cam.GetUniversalAdditionalCameraData();
                data.renderPostProcessing = t.postProcessing;
                data.antialiasing = t.postProcessing ? t.postAntialiasing : AntialiasingMode.None;
                // ADR 0108: High RCAS uses a final pass whose dither raises clean-sky RMS above the review limit.
                // Measured native PNG A/B: sky 0.64 -> 0.14, asphalt detail retained. Other tiers keep their policy.
                data.dithering = RenderOverrides.Dither ?? (t.postProcessing && t.name != "High");
            }
            if (volume != null)
            {
                var prof = Application.isPlaying ? volume.profile : volume.sharedProfile;
                if (tonemapping == null && prof != null) prof.TryGet(out tonemapping);
                if (tonemapping != null)
                {
                    tonemapping.active = t.tonemapping != TonemappingMode.None;
                    tonemapping.mode.overrideState = true;
                    tonemapping.mode.value = t.tonemapping;
                }
            }
            if (t.worldDetail) Shader.EnableKeyword(WorldDetailKeyword); else Shader.DisableKeyword(WorldDetailKeyword);
            // Pre-LUT sky noise is amplified by grading/RCAS; post tiers keep the final URP dither instead.
            bool skyDither = RenderOverrides.SkyDither ?? !t.postProcessing;
            Shader.SetGlobalFloat(k_SkyDitherOff, skyDither ? 0f : 1f);
            Shader.SetGlobalFloat(k_GlassShadowBias, ArchitecturalGlassBias(t, RenderOverrides.GlassShadowBias));
#if UNITY_EDITOR
            Debug.Log($"[QUALITY_STATE] tier={t.name} cameraDither={(cam != null ? cam.GetUniversalAdditionalCameraData().dithering.ToString() : "none")} skyDitherOff={Shader.GetGlobalFloat(k_SkyDitherOff)} glassShadowBias={Shader.GetGlobalFloat(k_GlassShadowBias)}");
            if (RenderOverrides.GlassShadowBias.HasValue)
                foreach (var m in Resources.FindObjectsOfTypeAll<Material>())
                    if (m.name == "M_kp_glass_block") Debug.Log($"[RQ_GLASS] name={m.name} shader={m.shader.name} flag={m.GetFloat("_ArchitecturalGlass")} receive={m.GetFloat("_ReceiveShadows")}");
#endif
            if (t.glassFast) Shader.EnableKeyword(GlassFastKeyword); else Shader.DisableKeyword(GlassFastKeyword);
            ForestFastPath.Apply(t.forestFast);   // ADR 0113
            // A8: truck paint clear coat switch (Kamion/Truck Exterior reads 0 = on, so an unset global keeps it on).
            Shader.SetGlobalFloat(k_ClearCoatOff, t.clearCoat ? 0f : 1f);
            Shader.SetGlobalFloat(k_GrimeDetailOff, t.vehicleGrimeDetail ? 0f : 1f);   // ADR 0038
            if (worldTextures != null)
                foreach (var tex in worldTextures)
                {
                    if (tex == null) continue;
                    tex.anisoLevel = t.worldTextureAniso;
                    tex.mipMapBias = t.worldMipBias;
                }
            Applied?.Invoke(t);
        }
    }
}
