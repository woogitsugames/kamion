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

        public Camera targetCamera;
        public Volume volume;
        [Tooltip("World surface textures whose anisotropy / mip bias follow the tier")]
        public Texture[] worldTextures;

        int m_AppliedLevel = -1;
        Tonemapping m_Tonemapping;

        public static QualityProfile.Tier Current { get; private set; }

        void OnEnable() => ApplyNow();

        void LateUpdate()
        {
            if (QualitySettings.GetQualityLevel() != m_AppliedLevel) ApplyNow();
        }

        public void ApplyNow()
        {
            m_AppliedLevel = QualitySettings.GetQualityLevel();
            var profile = QualityProfile.Load();
            if (profile == null || !profile.TryGet(QualityTiers.Current, out var t)) return;
            Current = t;
            Apply(t, targetCamera != null ? targetCamera : Camera.main, volume, worldTextures, ref m_Tonemapping);
        }

        /// <summary>Static entry for editor tools (visual QA) that render without entering play mode.</summary>
        public static void Apply(QualityProfile.Tier t, Camera cam, Volume volume, Texture[] worldTextures, ref Tonemapping tonemapping)
        {
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
            if (worldTextures != null)
                foreach (var tex in worldTextures)
                {
                    if (tex == null) continue;
                    tex.anisoLevel = t.worldTextureAniso;
                    tex.mipMapBias = t.worldMipBias;
                }
        }
    }
}
