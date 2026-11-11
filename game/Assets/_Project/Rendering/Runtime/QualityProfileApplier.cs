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
        static readonly int k_ClearCoatOff = Shader.PropertyToID("_KamionClearCoatOff");
        static readonly int k_GrimeDetailOff = Shader.PropertyToID("_KamionGrimeDetailOff");

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
                ApplyPipelineOverrides(t);
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
            if (RenderOverrides.Hdr.HasValue) urp.supportsHDR = t.hdr;
            if (RenderOverrides.Upscale != null) urp.upscalingFilter = t.upscalingFilter;   // ADR 0062 A/B
            if (RenderOverrides.FsrSharpness.HasValue) { urp.fsrOverrideSharpness = true; urp.fsrSharpness = t.fsrSharpness; }
            if (RenderOverrides.LodBias.HasValue && Application.isPlaying) QualitySettings.lodBias = t.lodBias;   // ADR 0106
        }

        /// <summary>Raised after a tier was applied (vegetation reads <see cref="Current"/>).</summary>
        public static event System.Action<QualityProfile.Tier> Applied;

        /// <summary>Static entry for editor tools (visual QA) that render without entering play mode.</summary>
        public static void Apply(QualityProfile.Tier t, Camera cam, Volume volume, Texture[] worldTextures, ref Tonemapping tonemapping)
        {
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
                data.dithering = t.postProcessing;
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
