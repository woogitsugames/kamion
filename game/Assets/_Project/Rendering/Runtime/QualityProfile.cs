using System;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering
{
    /// <summary>
    /// Single source of truth for the per-tier rendering settings. The editor (ProjectSetup) writes the URP assets and
    /// quality levels from it; at run time <see cref="QualityProfileApplier"/> applies the camera-side settings (post,
    /// AA, far clip, dithering) and global shader keywords. Rationale and budgets: docs/adr/0010 and
    /// docs/PERFORMANCE_BUDGETS.md. Every number is a WORKING_VALUE until measured on the Galaxy A16 / S24+.
    /// </summary>
    [CreateAssetMenu(menuName = "Kamion/Rendering/Quality Profile", fileName = "QualityProfile")]
    public sealed class QualityProfile : ScriptableObject
    {
        public const string ResourcePath = "QualityProfile";

        [Serializable]
        public struct Tier
        {
            public string name;
            [Header("Resolution / AA")]
            public float renderScale;
            [Tooltip("1, 2, 4, 8")] public int msaa;
            public AntialiasingMode postAntialiasing;
            public bool hdr;
            public bool postProcessing;
            public TonemappingMode tonemapping;
            [Header("Shadows")]
            public float shadowDistance;
            public int shadowResolution;
            [Range(1, 4)] public int shadowCascades;
            public float cascade2Split;
            public Vector3 cascade4Split;
            public bool softShadows;
            public SoftShadowQuality softShadowQuality;
            public float shadowDepthBias;
            public float shadowNormalBias;
            [Header("Textures / geometry")]
            [Tooltip("QualitySettings.anisotropicFiltering: 0 off, 1 per texture, 2 forced on")] public int anisotropic;
            [Tooltip("Aniso level written on world surface textures (asphalt, markings, grass)")] public int worldTextureAniso;
            [Tooltip("Mip bias on world surface textures (negative = sharper; aliasing risk)")] public float worldMipBias;
            public float lodBias;
            public float cameraFarClip;
            [Tooltip("Enable the world surface detail layer (second albedo scale + macro variation)")] public bool worldDetail;
            public int additionalLightsPerObject;
            [Header("Budget assumptions (UNMEASURED until the phone is measured)")]
            public int budgetDrawCalls;
            public int budgetTrianglesK;
            public int budgetTextureMB;
            public float budgetShadowMs;
            public string budgetStatus;
        }

        public Tier[] tiers = Defaults();

        public bool TryGet(string tierName, out Tier tier)
        {
            foreach (var t in tiers)
                if (string.Equals(t.name, tierName, StringComparison.OrdinalIgnoreCase)) { tier = t; return true; }
            tier = default;
            return false;
        }

        static QualityProfile s_Loaded;
        public static QualityProfile Load()
        {
            if (s_Loaded == null) s_Loaded = Resources.Load<QualityProfile>(ResourcePath);
            return s_Loaded;
        }

        /// <summary>
        /// Defaults (docs/adr/0010 §tiers). Mali-G57 MC2 is tile-based: MSAA resolves on tile memory, so 4× is the
        /// cheapest AA that also fixes geometric aliasing of kerbs and the 0.12 m markings mesh; FXAA/SMAA would add a
        /// full-screen pass and TAA needs motion vectors + history (bandwidth, ghosting) - flagship only, later.
        /// </summary>
        public static Tier[] Defaults() => new[]
        {
            new Tier
            {
                name = "Low", renderScale = 0.75f, msaa = 2, postAntialiasing = AntialiasingMode.None, hdr = false,
                postProcessing = false, tonemapping = TonemappingMode.None,
                shadowDistance = 35f, shadowResolution = 1024, shadowCascades = 1, cascade2Split = 0.25f,
                cascade4Split = new Vector3(0.067f, 0.2f, 0.467f), softShadows = false, softShadowQuality = SoftShadowQuality.Low,
                shadowDepthBias = 1.0f, shadowNormalBias = 1.0f,
                anisotropic = 1, worldTextureAniso = 2, worldMipBias = 0f, lodBias = 0.5f, cameraFarClip = 900f,
                worldDetail = false, additionalLightsPerObject = 2,
                budgetDrawCalls = 250, budgetTrianglesK = 350, budgetTextureMB = 64, budgetShadowMs = 1.0f, budgetStatus = "UNMEASURED",
            },
            new Tier
            {
                name = "Medium", renderScale = 0.85f, msaa = 4, postAntialiasing = AntialiasingMode.None, hdr = true,
                postProcessing = true, tonemapping = TonemappingMode.Neutral,
                shadowDistance = 60f, shadowResolution = 1024, shadowCascades = 2, cascade2Split = 0.25f,
                cascade4Split = new Vector3(0.067f, 0.2f, 0.467f), softShadows = false, softShadowQuality = SoftShadowQuality.Low,
                shadowDepthBias = 1.0f, shadowNormalBias = 1.0f,
                anisotropic = 1, worldTextureAniso = 4, worldMipBias = 0f, lodBias = 0.8f, cameraFarClip = 1400f,
                worldDetail = true, additionalLightsPerObject = 4,
                budgetDrawCalls = 350, budgetTrianglesK = 550, budgetTextureMB = 96, budgetShadowMs = 1.5f, budgetStatus = "UNMEASURED",
            },
            new Tier
            {
                name = "High", renderScale = 1.0f, msaa = 4, postAntialiasing = AntialiasingMode.None, hdr = true,
                postProcessing = true, tonemapping = TonemappingMode.Neutral,
                shadowDistance = 100f, shadowResolution = 2048, shadowCascades = 3, cascade2Split = 0.25f,
                cascade4Split = new Vector3(0.08f, 0.25f, 0.55f), softShadows = true, softShadowQuality = SoftShadowQuality.Medium,
                shadowDepthBias = 0.8f, shadowNormalBias = 0.8f,
                anisotropic = 1, worldTextureAniso = 8, worldMipBias = 0f, lodBias = 1.5f, cameraFarClip = 2500f,
                worldDetail = true, additionalLightsPerObject = 4,
                budgetDrawCalls = 800, budgetTrianglesK = 1500, budgetTextureMB = 256, budgetShadowMs = 2.0f, budgetStatus = "UNMEASURED (no flagship attached)",
            },
            new Tier
            {
                name = "Ultra", renderScale = 1.0f, msaa = 4, postAntialiasing = AntialiasingMode.None, hdr = true,
                postProcessing = true, tonemapping = TonemappingMode.Neutral,
                shadowDistance = 150f, shadowResolution = 4096, shadowCascades = 4, cascade2Split = 0.25f,
                cascade4Split = new Vector3(0.05f, 0.18f, 0.45f), softShadows = true, softShadowQuality = SoftShadowQuality.High,
                shadowDepthBias = 0.6f, shadowNormalBias = 0.6f,
                anisotropic = 2, worldTextureAniso = 16, worldMipBias = 0f, lodBias = 2.0f, cameraFarClip = 3500f,
                worldDetail = true, additionalLightsPerObject = 8,
                budgetDrawCalls = 1000, budgetTrianglesK = 2000, budgetTextureMB = 384, budgetShadowMs = 3.0f, budgetStatus = "UNMEASURED (no flagship attached)",
            },
        };
    }
}
