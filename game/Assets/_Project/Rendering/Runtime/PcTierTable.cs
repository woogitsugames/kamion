using System;
using System.Collections.Generic;

namespace Game.Rendering
{
    /// <summary>PC graphics tier (ADR 0269). Names equal the Unity quality levels (QualityTiers.Names), so the content tier
    /// (RegionScenes.UsesHighContent), mirror budgets and every name-based policy keep working on PC.</summary>
    public enum PcTier { Low = 0, Medium = 1, High = 2, Ultra = 3 }

    /// <summary>Post anti-aliasing on PC. TAA / STP are deliberately absent (ADR 0269: URP TAA does not run with MSAA, and the
    /// leaf cards / impostors rely on MSAA alpha-to-coverage; history ghosting on markings and wires at speed).</summary>
    public enum PcPostAntialiasing { None = 0, Fxaa = 1, Smaa = 2 }

    /// <summary>Hardware facts used by the first-launch tier choice (filled from SystemInfo by PcGraphicsTiers).</summary>
    [Serializable]
    public struct PcHardwareInfo
    {
        public string gpuName;
        /// <summary>Dedicated video memory (SystemInfo.graphicsMemorySize), MB; ≤ 0 = unknown.</summary>
        public int vramMb;
        /// <summary>System RAM (SystemInfo.systemMemorySize), MB; ≤ 0 = unknown.</summary>
        public int systemRamMb;

        public PcHardwareInfo(string gpuName, int vramMb, int systemRamMb)
        {
            this.gpuName = gpuName;
            this.vramMb = vramMb;
            this.systemRamMb = systemRamMb;
        }
    }

    /// <summary>
    /// One PC tier as data (ADR 0269 table: source of each value). Fields that live on the URP asset (render scale, MSAA,
    /// HDR, shadows, additional lights) are also authored into Resources/PcTiers/URP_PC_&lt;tier&gt;.asset by
    /// Game.Rendering.Editor.PcTierAssetsSetup; an EditMode test keeps the asset and this table equal. Everything else is
    /// applied at run time (QualitySettings, camera, vegetation) only when the tier changes - never per frame.
    /// </summary>
    [Serializable]
    public struct PcTierSettings
    {
        public PcTier tier;
        [UnityEngine.Tooltip("Resources path of the URP asset (Resources/PcTiers/...)")] public string urpAsset;
        // Resolution / AA / post
        public float renderScale;
        public int msaa;
        public PcPostAntialiasing postAntialiasing;
        [UnityEngine.Tooltip("SMAA quality 0 Low, 1 Medium, 2 High (UniversalAdditionalCameraData.antialiasingQuality)")] public int smaaQuality;
        public bool hdr;
        public bool postProcessing;
        // Shadows (main light)
        public float shadowDistance;
        public int shadowResolution;
        public int shadowCascades;
        public float cascade2Split;
        public float cascade3SplitX, cascade3SplitY;
        public float cascade4SplitX, cascade4SplitY, cascade4SplitZ;
        public bool softShadows;
        [UnityEngine.Tooltip("URP SoftShadowQuality: 1 Low, 3 High (2 Medium is not used by any mobile asset -> stripped, ADR 0269)")] public int softShadowQuality;
        public float shadowDepthBias, shadowNormalBias;
        // Geometry / textures
        public float lodBias;
        public int maximumLodLevel;
        [UnityEngine.Tooltip("QualitySettings.globalTextureMipmapLimit: 0 full, 1 half, 2 quarter resolution")] public int textureMipmapLimit;
        [UnityEngine.Tooltip("QualitySettings.anisotropicFiltering: 0 Disable, 1 Enable (per texture), 2 ForceEnable")] public int anisotropicFiltering;
        public int worldTextureAniso;
        public float cameraFarClip;
        public int additionalLightsPerObject;
        public bool ssao;
        // Vegetation (WorldInstances via QualityProfile.Tier)
        public float treeCardLodScale;
        public float treeThinStartM;
        public float treeCullM;
        public int treeShadowLodMask;
        public float forestHlodM;
        [UnityEngine.Tooltip("0 = no limit")] public float forestHlodCullM;
        public float vehicleCullM;
        public bool simpleFoliage;
        public bool forestFast;
        public bool glassFast;
        // Vehicle look / lights / sky
        public int envCaptureSize;
        public int envCaptureInterval;
        public int streetLights;
        public int lampPools;
        public int cloudQuality;
        public float mirrorResolutionScale;
        // Budget (WORKING_VALUE, D74)
        public int targetFps;
        public string status;

        public string Name => PcTierTable.NameOf(tier);
    }

    /// <summary>Pure data and rules of the PC tiers (no UnityEngine calls: unit-testable outside Unity).</summary>
    public static class PcTierTable
    {
        public const int TierCount = 4;
        static readonly string[] k_Names = { "Low", "Medium", "High", "Ultra" };

        public static string NameOf(PcTier t) => k_Names[(int)t];

        public static bool TryParse(string name, out PcTier tier)
        {
            for (int i = 0; i < k_Names.Length; i++)
                if (string.Equals(k_Names[i], name, StringComparison.OrdinalIgnoreCase)) { tier = (PcTier)i; return true; }
            tier = PcTier.High;
            return false;
        }

        // ---- First-launch detection (ADR 0269 §detekcja; thresholds WORKING_VALUE from D74 classes) ----
        /// <summary>Below this dedicated VRAM: Low (D74 minimum class: GTX 660 / RX 460 / HD 630, 2 GB).</summary>
        public const int LowBelowVramMb = 3500;
        /// <summary>Below this: Medium (4 GB class, e.g. GTX 1050 Ti / RX 570 4 GB).</summary>
        public const int MediumBelowVramMb = 5500;
        /// <summary>D74 recommended class (GTX 1660 6 GB) also needs 12 GB RAM; Windows reports a 12 GB machine as ~12 000 MB.</summary>
        public const int HighMinRamMb = 11000;
        /// <summary>Below this RAM: Low (D74 minimum is 8 GB, reported as ~8 000 MB).</summary>
        public const int LowBelowRamMb = 7000;
        /// <summary>Unknown VRAM: Medium (neither the minimum promise nor the recommended one can be checked).</summary>
        public const PcTier UnknownVramTier = PcTier.Medium;
        /// <summary>Auto-detection never picks Ultra (opt-in in the settings; ADR 0261 default High is the ceiling).</summary>
        public const PcTier AutoCeiling = PcTier.High;

        static readonly string[] k_IntegratedMarkers =
        {
            "Intel(R) HD", "Intel(R) UHD", "Intel(R) Iris", "Intel HD", "Intel UHD", "Iris(R) Xe", "Iris Xe",
            "AMD Radeon(TM) Graphics", "AMD Radeon Graphics", "Radeon(TM) Vega", "Radeon Vega", "Radeon(TM) 7", "Radeon 780M", "Radeon 760M",
        };
        static readonly string[] k_SoftwareMarkers = { "Microsoft Basic Render", "llvmpipe", "SwiftShader", "WARP" };

        /// <summary>True for integrated GPUs (shared memory; graphicsMemorySize is not a dedicated-VRAM figure there).</summary>
        public static bool IsIntegrated(string gpu)
        {
            if (string.IsNullOrEmpty(gpu)) return false;
            if (gpu.IndexOf("Arc", StringComparison.OrdinalIgnoreCase) >= 0 && gpu.IndexOf("Intel", StringComparison.OrdinalIgnoreCase) >= 0) return false;
            foreach (var m in k_IntegratedMarkers) if (gpu.IndexOf(m, StringComparison.OrdinalIgnoreCase) >= 0) return true;
            return false;
        }

        public static bool IsSoftware(string gpu)
        {
            if (string.IsNullOrEmpty(gpu)) return false;
            foreach (var m in k_SoftwareMarkers) if (gpu.IndexOf(m, StringComparison.OrdinalIgnoreCase) >= 0) return true;
            return false;
        }

        /// <summary>First-launch tier for a PC (pure function). Order: software / integrated GPU → Low; RAM &lt; 7 GB → Low;
        /// VRAM unknown → Medium; VRAM &lt; 3.5 GB → Low, &lt; 5.5 GB → Medium, else High; High needs ≥ 11 GB RAM (else Medium).
        /// Never Ultra (<see cref="AutoCeiling"/>).</summary>
        public static PcTier DefaultFor(PcHardwareInfo hw, out string reason)
        {
            if (IsSoftware(hw.gpuName)) { reason = "software renderer"; return PcTier.Low; }
            if (IsIntegrated(hw.gpuName)) { reason = "integrated GPU (D74 minimum: Intel HD 630 class)"; return PcTier.Low; }
            if (hw.systemRamMb > 0 && hw.systemRamMb < LowBelowRamMb) { reason = $"RAM {hw.systemRamMb} MB < {LowBelowRamMb}"; return PcTier.Low; }
            PcTier t;
            if (hw.vramMb <= 0) { t = UnknownVramTier; reason = "VRAM unknown"; }
            else if (hw.vramMb < LowBelowVramMb) { t = PcTier.Low; reason = $"VRAM {hw.vramMb} MB < {LowBelowVramMb} (D74 minimum class)"; }
            else if (hw.vramMb < MediumBelowVramMb) { t = PcTier.Medium; reason = $"VRAM {hw.vramMb} MB < {MediumBelowVramMb}"; }
            else { t = PcTier.High; reason = $"VRAM {hw.vramMb} MB (D74 recommended class)"; }
            if (t > PcTier.Medium && hw.systemRamMb > 0 && hw.systemRamMb < HighMinRamMb)
            {
                t = PcTier.Medium;
                reason += $", RAM {hw.systemRamMb} MB < {HighMinRamMb} (D74 recommended 12 GB)";
            }
            if (t > AutoCeiling) t = AutoCeiling;
            return t;
        }

        public static PcTier DefaultFor(PcHardwareInfo hw) => DefaultFor(hw, out _);

        public static PcTierSettings Get(PcTier t) => s_Defaults[(int)t];

        static readonly PcTierSettings[] s_Defaults = Defaults();

        /// <summary>
        /// The PC tiers (ADR 0269 table). All numbers WORKING_VALUE / ESTIMATED until measured on the D74 reference classes
        /// (GTX 660-class Low 1080p 30 fps, GTX 1660-class High 1080p 60 fps). Vegetation and vehicle-look values not listed
        /// here come from the mobile tier of the same name (QualityProfile) unchanged.
        /// </summary>
        public static PcTierSettings[] Defaults() => new[]
        {
            new PcTierSettings
            {
                tier = PcTier.Low, urpAsset = "PcTiers/URP_PC_Low",
                renderScale = 1f, msaa = 2, postAntialiasing = PcPostAntialiasing.None, smaaQuality = 0, hdr = true, postProcessing = true,
                shadowDistance = 60f, shadowResolution = 2048, shadowCascades = 2, cascade2Split = 0.25f,
                cascade3SplitX = 0.1f, cascade3SplitY = 0.3f, cascade4SplitX = 0.067f, cascade4SplitY = 0.2f, cascade4SplitZ = 0.467f,
                softShadows = false, softShadowQuality = 1, shadowDepthBias = 0.4f, shadowNormalBias = 0.3f,
                lodBias = 1.0f, maximumLodLevel = 0, textureMipmapLimit = 1, anisotropicFiltering = 1, worldTextureAniso = 4,
                cameraFarClip = 1500f, additionalLightsPerObject = 4, ssao = false,
                treeCardLodScale = 0.5f, treeThinStartM = 90f, treeCullM = 600f, treeShadowLodMask = 1, forestHlodM = 70f, forestHlodCullM = 1500f,
                vehicleCullM = 200f, simpleFoliage = true, forestFast = true, glassFast = true,
                envCaptureSize = 64, envCaptureInterval = 6, streetLights = 0, lampPools = 6, cloudQuality = 1, mirrorResolutionScale = 1f,
                targetFps = 30, status = "WORKING_VALUE (D74 minimum: GTX 660 2 GB / i5-6400 / 8 GB, 1080p 30 fps) - UNMEASURED",
            },
            new PcTierSettings
            {
                tier = PcTier.Medium, urpAsset = "PcTiers/URP_PC_Medium",
                renderScale = 1f, msaa = 4, postAntialiasing = PcPostAntialiasing.None, smaaQuality = 0, hdr = true, postProcessing = true,
                shadowDistance = 100f, shadowResolution = 2048, shadowCascades = 3, cascade2Split = 0.25f,
                cascade3SplitX = 0.1f, cascade3SplitY = 0.3f, cascade4SplitX = 0.067f, cascade4SplitY = 0.2f, cascade4SplitZ = 0.467f,
                softShadows = true, softShadowQuality = 1, shadowDepthBias = 0.4f, shadowNormalBias = 0.3f,
                lodBias = 1.25f, maximumLodLevel = 0, textureMipmapLimit = 0, anisotropicFiltering = 1, worldTextureAniso = 8,
                cameraFarClip = 2000f, additionalLightsPerObject = 4, ssao = false,
                treeCardLodScale = 0.5f, treeThinStartM = 120f, treeCullM = 800f, treeShadowLodMask = 1, forestHlodM = 90f, forestHlodCullM = 0f,
                vehicleCullM = 300f, simpleFoliage = true, forestFast = false, glassFast = false,
                envCaptureSize = 128, envCaptureInterval = 4, streetLights = 2, lampPools = 8, cloudQuality = 1, mirrorResolutionScale = 1f,
                targetFps = 60, status = "WORKING_VALUE (between D74 classes, 4 GB VRAM) - UNMEASURED",
            },
            new PcTierSettings
            {
                tier = PcTier.High, urpAsset = "PcTiers/URP_PC_High",
                renderScale = 1f, msaa = 4, postAntialiasing = PcPostAntialiasing.None, smaaQuality = 0, hdr = true, postProcessing = true,
                shadowDistance = 150f, shadowResolution = 4096, shadowCascades = 4, cascade2Split = 0.25f,
                cascade3SplitX = 0.1f, cascade3SplitY = 0.3f, cascade4SplitX = 0.067f, cascade4SplitY = 0.2f, cascade4SplitZ = 0.467f,
                softShadows = true, softShadowQuality = 1, shadowDepthBias = 0.6f, shadowNormalBias = 0.6f,
                lodBias = 1.5f, maximumLodLevel = 0, textureMipmapLimit = 0, anisotropicFiltering = 2, worldTextureAniso = 16,
                cameraFarClip = 3000f, additionalLightsPerObject = 8, ssao = true,
                treeCardLodScale = 0.75f, treeThinStartM = 150f, treeCullM = 1000f, treeShadowLodMask = 3, forestHlodM = 150f, forestHlodCullM = 0f,
                vehicleCullM = 400f, simpleFoliage = true, forestFast = false, glassFast = false,
                envCaptureSize = 256, envCaptureInterval = 2, streetLights = 6, lampPools = 8, cloudQuality = 2, mirrorResolutionScale = 1f,
                targetFps = 60, status = "WORKING_VALUE (D74 recommended: GTX 1660 / i5-9600 / 12 GB, 1080p 60 fps) - UNMEASURED",
            },
            new PcTierSettings
            {
                tier = PcTier.Ultra, urpAsset = "PcTiers/URP_PC_Ultra",
                renderScale = 1f, msaa = 8, postAntialiasing = PcPostAntialiasing.None, smaaQuality = 0, hdr = true, postProcessing = true,
                shadowDistance = 250f, shadowResolution = 8192, shadowCascades = 4, cascade2Split = 0.25f,
                cascade3SplitX = 0.1f, cascade3SplitY = 0.3f, cascade4SplitX = 0.04f, cascade4SplitY = 0.12f, cascade4SplitZ = 0.35f,
                softShadows = true, softShadowQuality = 3, shadowDepthBias = 0.6f, shadowNormalBias = 0.6f,
                lodBias = 2.0f, maximumLodLevel = 0, textureMipmapLimit = 0, anisotropicFiltering = 2, worldTextureAniso = 16,
                cameraFarClip = 4000f, additionalLightsPerObject = 8, ssao = true,
                treeCardLodScale = 1.0f, treeThinStartM = 200f, treeCullM = 1500f, treeShadowLodMask = 3, forestHlodM = 200f, forestHlodCullM = 0f,
                vehicleCullM = 600f, simpleFoliage = true, forestFast = false, glassFast = false,
                envCaptureSize = 256, envCaptureInterval = 1, streetLights = 8, lampPools = 8, cloudQuality = 2, mirrorResolutionScale = 1f,
                targetFps = 60, status = "WORKING_VALUE (above D74 recommended; opt-in, never auto-selected) - UNMEASURED",
            },
        };

        static bool Pow2(int v) => v > 0 && (v & (v - 1)) == 0;

        /// <summary>Structural check of a tier table (EditMode test + PcGraphicsTiers on first use). Empty list = valid.</summary>
        public static List<string> Validate(PcTierSettings[] tiers)
        {
            var e = new List<string>();
            if (tiers == null || tiers.Length != TierCount) { e.Add($"expected {TierCount} tiers"); return e; }
            for (int i = 0; i < tiers.Length; i++)
            {
                var t = tiers[i];
                string n = k_Names[i];
                if ((int)t.tier != i) e.Add($"{n}: tier {t.tier} at index {i}");
                if (t.urpAsset != "PcTiers/URP_PC_" + n) e.Add($"{n}: urpAsset '{t.urpAsset}'");
                if (t.renderScale < 0.5f || t.renderScale > 2f) e.Add($"{n}: renderScale {t.renderScale}");
                if (t.msaa != 2 && t.msaa != 4 && t.msaa != 8) e.Add($"{n}: msaa {t.msaa} (leaf alpha-to-coverage needs MSAA 2/4/8)");
                if (t.smaaQuality < 0 || t.smaaQuality > 2) e.Add($"{n}: smaaQuality {t.smaaQuality}");
                if (t.postAntialiasing != PcPostAntialiasing.None && !t.postProcessing) e.Add($"{n}: post AA without post-processing");
                if (!t.postProcessing || !t.hdr) e.Add($"{n}: PC tiers keep HDR + tonemapping (one calibrated look on every tier)");
                if (t.shadowCascades < 1 || t.shadowCascades > 4) e.Add($"{n}: cascades {t.shadowCascades}");
                if (!Pow2(t.shadowResolution) || t.shadowResolution < 256 || t.shadowResolution > 8192) e.Add($"{n}: shadowResolution {t.shadowResolution}");
                if (t.shadowDistance <= 0f || t.cameraFarClip <= t.shadowDistance) e.Add($"{n}: shadow distance {t.shadowDistance} / far clip {t.cameraFarClip}");
                if (!(t.cascade2Split > 0f && t.cascade2Split < 1f)) e.Add($"{n}: cascade2Split");
                if (!(t.cascade3SplitX > 0f && t.cascade3SplitX < t.cascade3SplitY && t.cascade3SplitY < 1f)) e.Add($"{n}: cascade3Split not increasing");
                if (!(t.cascade4SplitX > 0f && t.cascade4SplitX < t.cascade4SplitY && t.cascade4SplitY < t.cascade4SplitZ && t.cascade4SplitZ < 1f)) e.Add($"{n}: cascade4Split not increasing");
                if (t.softShadows && t.softShadowQuality != 1 && t.softShadowQuality != 3) e.Add($"{n}: softShadowQuality {t.softShadowQuality} (only Low/High variants survive stripping)");
                if (t.lodBias <= 0f) e.Add($"{n}: lodBias");
                if (t.maximumLodLevel < 0 || t.maximumLodLevel > 2) e.Add($"{n}: maximumLodLevel {t.maximumLodLevel}");
                if (t.textureMipmapLimit < 0 || t.textureMipmapLimit > 2) e.Add($"{n}: textureMipmapLimit {t.textureMipmapLimit}");
                if (t.anisotropicFiltering < 0 || t.anisotropicFiltering > 2) e.Add($"{n}: anisotropicFiltering {t.anisotropicFiltering}");
                if (t.worldTextureAniso < 1 || t.worldTextureAniso > 16) e.Add($"{n}: worldTextureAniso {t.worldTextureAniso}");
                if (t.additionalLightsPerObject < 0 || t.additionalLightsPerObject > 8) e.Add($"{n}: additionalLightsPerObject {t.additionalLightsPerObject}");
                if (t.treeCullM <= t.treeThinStartM) e.Add($"{n}: treeCullM ≤ treeThinStartM");
                if (t.treeShadowLodMask < 0 || t.treeShadowLodMask > 3) e.Add($"{n}: treeShadowLodMask");
                if (t.forestHlodM <= 0f) e.Add($"{n}: forestHlodM");
                if (t.forestHlodCullM != 0f && t.forestHlodCullM <= t.forestHlodM) e.Add($"{n}: forestHlodCullM ≤ forestHlodM");
                if (t.mirrorResolutionScale < 1f) e.Add($"{n}: mirrors below the tier resolution (mirrors always usable, docs/06)");
                if (!Pow2(t.envCaptureSize)) e.Add($"{n}: envCaptureSize {t.envCaptureSize}");
                if (t.envCaptureInterval < 1) e.Add($"{n}: envCaptureInterval");
                if (t.lampPools < 0 || t.lampPools > 8) e.Add($"{n}: lampPools");
                if (t.cloudQuality < 0 || t.cloudQuality > 2) e.Add($"{n}: cloudQuality");
                if (t.targetFps != 30 && t.targetFps != 60) e.Add($"{n}: targetFps {t.targetFps}");
                if (string.IsNullOrEmpty(t.status)) e.Add($"{n}: status (WORKING_VALUE / measured) missing");
            }
            for (int i = 1; i < tiers.Length; i++)
            {
                var a = tiers[i - 1]; var b = tiers[i];
                string p = k_Names[i - 1] + "→" + k_Names[i];
                void Ge(float lo, float hi, string what) { if (hi < lo) e.Add($"{p}: {what} decreases ({lo} → {hi})"); }
                Ge(a.shadowDistance, b.shadowDistance, "shadowDistance");
                Ge(a.shadowResolution, b.shadowResolution, "shadowResolution");
                Ge(a.shadowCascades, b.shadowCascades, "shadowCascades");
                Ge(a.cameraFarClip, b.cameraFarClip, "cameraFarClip");
                Ge(a.lodBias, b.lodBias, "lodBias");
                Ge(a.msaa, b.msaa, "msaa");
                Ge(a.renderScale, b.renderScale, "renderScale");
                Ge(a.worldTextureAniso, b.worldTextureAniso, "worldTextureAniso");
                Ge(a.anisotropicFiltering, b.anisotropicFiltering, "anisotropicFiltering");
                Ge(a.additionalLightsPerObject, b.additionalLightsPerObject, "additionalLightsPerObject");
                Ge(a.treeCardLodScale, b.treeCardLodScale, "treeCardLodScale");
                Ge(a.treeThinStartM, b.treeThinStartM, "treeThinStartM");
                Ge(a.treeCullM, b.treeCullM, "treeCullM");
                Ge(a.forestHlodM, b.forestHlodM, "forestHlodM");
                Ge(HlodCull(a.forestHlodCullM), HlodCull(b.forestHlodCullM), "forestHlodCullM");
                Ge(a.vehicleCullM, b.vehicleCullM, "vehicleCullM");
                Ge(a.envCaptureSize, b.envCaptureSize, "envCaptureSize");
                Ge(a.streetLights, b.streetLights, "streetLights");
                Ge(a.lampPools, b.lampPools, "lampPools");
                Ge(a.cloudQuality, b.cloudQuality, "cloudQuality");
                Ge(a.mirrorResolutionScale, b.mirrorResolutionScale, "mirrorResolutionScale");
                Ge(-a.textureMipmapLimit, -b.textureMipmapLimit, "texture resolution (mipmap limit increases)");
                Ge(-a.maximumLodLevel, -b.maximumLodLevel, "maximum LOD (maximumLodLevel increases)");
                Ge(-a.envCaptureInterval, -b.envCaptureInterval, "capture refresh (interval increases)");
                Ge(SoftRank(a), SoftRank(b), "soft shadows");
                if (a.ssao && !b.ssao) e.Add($"{p}: SSAO switched off on the higher tier");
            }
            return e;
        }

        static float HlodCull(float v) => v <= 0f ? float.MaxValue : v;
        static int SoftRank(PcTierSettings t) => t.softShadows ? t.softShadowQuality : 0;
    }
}
