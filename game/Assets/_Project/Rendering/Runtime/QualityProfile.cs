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
            [Tooltip("Adaptive render scale floor (ADR 0046; GPU p90 driven, 0 = fixed renderScale)")] public float adaptiveScaleMin;
            [Tooltip("Frame cap after thermal status >= 2 for 30 s (ADR 0046; 0 = off)")] public int thermalFallbackFps;
            [Tooltip("ADR 0062: frame cap when the scale is at its floor and > 10 % of frames still miss vsync for 6 s (0 = off)")] public int pacingFallbackFps;
            [Tooltip("ADR 0062: upscaler when the render scale is below 1 (URP asset; FSR 1.0 = EASU + RCAS, spatial, keeps MSAA)")] public UpscalingFilterSelection upscalingFilter;
            [Tooltip("ADR 0062: FSR RCAS sharpness 0..1 (URP default 0.92 halos on markings and wires)")] public float fsrSharpness;
            [Tooltip("Enable the world surface detail layer (second albedo scale + macro variation)")] public bool worldDetail;
            public int additionalLightsPerObject;
            [Header("Vegetation (WorldInstances; device-measured, DK8 forest)")]
            [Tooltip("Upper limit of the LOD-bias factor for tree card LODs (LOD0/LOD1 leaf cards)")] public float treeCardLodScale;
            [Tooltip("Trees beyond this distance (m × LOD bias) are thinned: every 2nd, every 4th beyond 2.5×")] public float treeThinStartM;
            [Tooltip("Cull distance of trees and shrubs (m × LOD bias), caps the baked impostor distance")] public float treeCullM;
            [Tooltip("Tree LODs that cast shadows: bit 0 = LOD0, bit 1 = LOD1 (impostors never)")] public int treeShadowLodMask;
            [Tooltip("Alpha-to-coverage on leaf cards / impostors (needs MSAA; smooth edges, costs coverage work on the GPU)")] public bool leafAlphaToCoverage;
            [Tooltip("Leaf cards / impostors use Kamion/Vegetation (depth pass + ZTest Equal colour pass, Lambert) instead of URP Lit. " +
                     "A16 DK8 forest: the Lit leaves were fragment bound (ADR 0013)")] public bool simpleFoliage;
            [Tooltip("Forest HLOD (ADR 0015): beyond this distance (m, camera to the 64 m cell bounds) a cell's forest trees are " +
                     "replaced by its canopy + edge-wall mesh. Same as the generator's lod_policy.<content tier>.forest_hlod_m")] public float forestHlodM;
            [Tooltip("Forest HLOD cells beyond this distance are not drawn (0 = no limit)")] public float forestHlodCullM;
            [Header("Vehicle look (A8: clear coat, reflections, contact shadows, cab shadows, dusk lights)")]
            [Tooltip("Clear-coat layer on the truck paint (Kamion/Truck Exterior: one extra env sample + GGX on paint pixels)")] public bool clearCoat;
            [Tooltip("Procedural road grime detail on the vehicles (ADR 0038: wheel-arch spray + streak noise; off = height gradient only)")] public bool vehicleGrimeDetail;
            [Tooltip("Vehicle reflection capture: cube face size in px (0 = off, the analytic sky cubemap is used)")] public int envCaptureSize;
            [Tooltip("Render one capture face every N frames (6 faces = one full refresh)")] public int envCaptureInterval;
            [Tooltip("Far clip of the capture camera (m)")] public float envCaptureFarClip;
            [Tooltip("ADR 0056: keep a complete cube while the truck moved less than this (m) since it was rendered (0 = always refresh)")] public float envCaptureMinMove;
            [Tooltip("ADR 0056: ... and while the cube is younger than this (s; sky / sun drift)")] public float envCaptureMaxAge;
            [Tooltip("Contact shadow / ambient occlusion blobs under the tractor, trailer and wheels (one draw per vehicle)")] public bool contactShadows;
            [Tooltip("Cab-view local shadow lift strength (CabInteriorLighting, review r4 L1; 0 = off)")] public float cabShadowLift;
            [Tooltip("Real point lights at the nearest street lamps at dusk (0 = emission only); they light vehicles and props")] public int streetLights;
            [Tooltip("ADR 0062: analytic light pools of the N lamps nearest the view on Kamion/World Surface at dusk (no lights, " +
                     "a uniform-branch loop in the world shader; 0 = off, max 8)")] public int lampPools;
            [Tooltip("ADR 0192: Off = no lit windows at dusk / night (facade atlas, LOD1 rows, far facades). Inverted so tiers saved " +
                     "before ADR 0192 keep them; cost: a uniform branch by day, one point load + one sample on window pixels by night")]
            public bool nightWindowsOff;
            [Tooltip("ADR 0192: Off = no glare halo around the street-lamp lenses at dusk (one additive billboard per lamp head, one draw)")]
            public bool lampGlareOff;
            [Header("Baked world lighting (ADR 0064)")]
            [Tooltip("Off = no baked sky visibility (ambient / reflection occlusion) on the world surfaces. Inverted so tiers saved before ADR 0064 keep it on")]
            public bool worldSkyVisOff;
            [Tooltip("Off = no baked ground sun shadows beyond the realtime shadow distance (ADR 0064)")]
            public bool worldBakedSunOff;
            [Header("Sky and atmosphere (ADR 0080)")]
            [Tooltip("Cloud deck of the overcast sky: 0 = 2 texture fetches per sky pixel, 1 = + fine detail (3), 2 = + relief toward the sun (5)")]
            public int cloudQuality;
            [Tooltip("Off = flat overcast dome. Inverted so tiers saved before ADR 0080 keep the clouds")] public bool cloudsOff;
            [Tooltip("Off = uniform fog only, no ground haze layer (the per-vertex optical depth costs the same either way)")] public bool groundHazeOff;
            [Tooltip("Screen-space ambient occlusion after opaques (URP SSAO, depth source; needs the renderer feature - Ultra's renderer only)")]
            public bool ssao;
            [Header("Vehicle glass (ADR 0106)")]
            [Tooltip("Kamion/Truck Glass fast path (_KAMION_GLASS_FAST): Fresnel, body absorption, film phase, ambient and fog per vertex, " +
                     "wiper sweeps in half precision. A16 Low: the windscreen covers ~80 % of the cab view and cost 3.6-4.3 ms GPU")]
            public bool glassFast;
            [Header("Forest fast path (ADR 0113)")]
            [Tooltip("Forest HLOD and impostors on the cheap path: HLOD canopy on Kamion/Forest Canopy instead of URP Lit, HLOD edge " +
                     "walls in one pass (ZWrite + alpha-to-coverage, no depth pre-pass), L2 SH per vertex on the walls and no shadow-map " +
                     "fetch past the shadow fade on every vegetation pixel (_KAMION_VEG_FAST). A16 Low: forest HLOD + impostors 4.3 ms")]
            public bool forestFast;
            [Tooltip("ADR 0136 r2: cull distance (m) of parked vehicles and their contact patches on this tier; 0 = the common " +
                     "WorldInstances.VehicleCullM (300 m). A16 Low G3-A: ~370 parked cars within 300 m, 7-12 submeshes each - the " +
                     "instanced submission cost (CPU +2.4 ms, GPU +0.35 ms beyond 150 m) is not worth ~20 px cars")]
            public float vehicleCullM;
            [Tooltip("ADR 0136 r2: mirror render-texture height multiplier on this tier (0 = 1). Low 0.75 follows the Low main-view " +
                     "render scale (224 -> 168 px class II); A16 G3-A A/B: mirrors 1.46 ms GPU, x0.75 saves 0.47 ms")]
            public float mirrorResolutionScale;
            [Header("Budget assumptions (UNMEASURED until the phone is measured)")]
            public int budgetDrawCalls;
            public int budgetTrianglesK;
            public int budgetTextureMB;
            public float budgetShadowMs;
            public string budgetStatus;
        }

        public Tier[] tiers = Defaults();
        [Tooltip("Migration revision (ProjectSetup.LoadTiers applies the changes of later revisions to an existing asset)")]
        public int revision;
        /// <summary>ADR 0062: High floor 0.70, FSR upscaling, pacing fallback, lamp pools.</summary>
        public const int CurrentRevision = 113;   // ADR 0080: cloudQuality, ssao; ADR0098: shadow receiver stability and post noise; ADR 0106: glassFast; ADR 0113: forestFast

        /// <summary>
        /// First-launch tier by device (no launch argument, nothing saved by the player). Rules are checked in order; a rule
        /// matches when every non-empty condition holds (case-insensitive substring of SystemInfo.graphicsDeviceName /
        /// deviceModel, RAM ≤ maxRamMb when > 0). Medium stays selectable in the settings on every device.
        /// Measured basis: docs/reports/device/DEVICE-RUN-2026-11-09.md (A16 DK8 forest: Low 30 FPS, Medium 13-17 FPS).
        /// </summary>
        [Serializable]
        public struct DeviceRule
        {
            public string gpuContains;
            public string modelContains;
            [Tooltip("Match when SystemInfo.systemMemorySize ≤ this (MB); 0 = ignore")] public int maxRamMb;
            public string tier;
            public string note;
        }

        public DeviceRule[] deviceRules = DefaultDeviceRules();
        [Tooltip("Template for leaf cards / impostors on tiers with simpleFoliage (Kamion/Vegetation, GPU instancing on). A material " +
                 "asset, not just the shader: without an instanced material in the build Unity strips the INSTANCING_ON variants " +
                 "and Graphics.RenderMeshInstanced draws nothing (A16, 2026-11-09)")]
        public Material foliageMaterial;
        [Tooltip("ADR 0113: template of the forest HLOD canopy on tiers with forestFast (Kamion/Forest Canopy, M_ForestCanopy); " +
                 "keeps the shader in the build")]
        public Material canopyMaterial;
        [Tooltip("Tier when no device rule matches")] public string fallbackTier = "Medium";

        public static DeviceRule[] DefaultDeviceRules() => new[]
        {
            // Galaxy A16 4G/5G class: Mali-G57 MC2 (Helio G99) / 4 GB. Measured: Medium 13-17 FPS in the DK8 forest.
            new DeviceRule { gpuContains = "Mali-G57", tier = "Low", note = "Galaxy A16 (Helio G99): measured, Low holds 30 FPS" },
            new DeviceRule { gpuContains = "Mali-G52", tier = "Low", note = "older entry-level Mali (same class or below the A16)" },
            new DeviceRule { gpuContains = "Mali-G68", tier = "Low", note = "Mali-G68 MC4 entry 5G (Dimensity 6xxx) - UNMEASURED" },
            new DeviceRule { gpuContains = "Adreno (TM) 6", tier = "Low", note = "Adreno 6xx entry/mid - UNMEASURED" },
            new DeviceRule { maxRamMb = 4200, tier = "Low", note = "≤ 4 GB RAM: world PSS ~0.5 GB, keep the Low content budget" },
            // Flagships: Galaxy S24+ (Xclipse 940) measured; Adreno 7xx/8xx and Immortalis are the same class (UNMEASURED).
            new DeviceRule { gpuContains = "Xclipse 9", tier = "High", note = "Galaxy S24+ (Exynos 2400): measured, High ~60 FPS" },
            new DeviceRule { gpuContains = "Adreno (TM) 7", tier = "High", note = "Snapdragon 8 Gen 1-3 - UNMEASURED" },
            new DeviceRule { gpuContains = "Adreno (TM) 8", tier = "High", note = "Galaxy Z Fold (Adreno 840, 5.65 Mpx inner): measured, High/30 GPU p95 29 ms; Ultra/60 ~25 FPS (ADR 0152)" },
            new DeviceRule { gpuContains = "Immortalis", tier = "High", note = "Dimensity 9xxx - UNMEASURED" },
        };

        /// <summary>The first-launch tier for a device (see <see cref="DeviceRule"/>).</summary>
        public string TierForDevice(string gpu, string model, int ramMb, out string reason)
        {
            if (deviceRules != null)
                foreach (var r in deviceRules)
                {
                    if (string.IsNullOrEmpty(r.tier)) continue;
                    bool any = false;
                    if (!string.IsNullOrEmpty(r.gpuContains)) { any = true; if (gpu == null || gpu.IndexOf(r.gpuContains, StringComparison.OrdinalIgnoreCase) < 0) continue; }
                    if (!string.IsNullOrEmpty(r.modelContains)) { any = true; if (model == null || model.IndexOf(r.modelContains, StringComparison.OrdinalIgnoreCase) < 0) continue; }
                    if (r.maxRamMb > 0) { any = true; if (ramMb <= 0 || ramMb > r.maxRamMb) continue; }
                    if (!any) continue;
                    reason = r.note;
                    return r.tier;
                }
            reason = "no device rule matched";
            return fallbackTier;
        }

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
        /// Medium is MSAA 2×, not 4×: A16 DK8 forest with HDR, GPU p50 64.7 ms at 4× vs 36.9 ms at 2× (Kamion/Vegetation
        /// foliage; with URP Lit 61.6 vs 50.4). Cause UNVERIFIED (no GPU counters yet): likely 4× HDR samples exceeding the G57 tile buffer (ADR 0013).
        /// High is MSAA 2× too: S24+ DK8 forest, cool phone, 38.7 ms at 4× vs 21.6 ms at 2× (Lit), no visible edge difference
        /// on native crops (ADR 0013 addendum r4, review r3 §7; accepted on condition of a 10 s motion recording).
        /// High gate 3 (ADR 0046): adaptive render scale 0.80-1.00 (GPU p90, 2 s windows) and a thermal 30 FPS fallback -
        /// S24+ GPU p50 14.8 ms at the 60 FPS cap left no vsync margin. ADR 0062 (owner D36): floor 0.70, FSR 1.0 upscaling
        /// below 1.0 (High/Ultra; Low/Medium keep bilinear - Low has no post pass, Medium is unmeasured on the A16), a
        /// frame-pacing 30 FPS fallback when 0.70 is still not enough, analytic lamp pools on all tiers at dusk.
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
                treeCardLodScale = 0.5f, treeThinStartM = 90f, treeCullM = 600f, treeShadowLodMask = 1, leafAlphaToCoverage = true, simpleFoliage = true,
                forestHlodM = 70f, forestHlodCullM = 1000f,
                clearCoat = true, vehicleGrimeDetail = false /* ADR 0136 r2: A16 G3-A -0.68 ms GPU */, envCaptureSize = 64, envCaptureInterval = 10, envCaptureFarClip = 150f, envCaptureMinMove = 2f, envCaptureMaxAge = 20f, contactShadows = true, cabShadowLift = 8f, streetLights = 0, lampPools = 4,
                glassFast = true, forestFast = true, vehicleCullM = 150f, mirrorResolutionScale = 0.75f,
                budgetDrawCalls = 250, budgetTrianglesK = 350, budgetTextureMB = 64, budgetShadowMs = 1.0f, budgetStatus = "UNMEASURED",
            },
            new Tier
            {
                name = "Medium", renderScale = 0.85f, msaa = 2, postAntialiasing = AntialiasingMode.None, hdr = true,
                postProcessing = true, tonemapping = TonemappingMode.Neutral,
                shadowDistance = 60f, shadowResolution = 1024, shadowCascades = 2, cascade2Split = 0.25f,
                cascade4Split = new Vector3(0.067f, 0.2f, 0.467f), softShadows = false, softShadowQuality = SoftShadowQuality.Low,
                shadowDepthBias = 0.4f, shadowNormalBias = 0.3f,
                anisotropic = 1, worldTextureAniso = 4, worldMipBias = 0f, lodBias = 0.8f, cameraFarClip = 1400f,
                worldDetail = true, additionalLightsPerObject = 4,
                treeCardLodScale = 0.5f, treeThinStartM = 90f, treeCullM = 600f, treeShadowLodMask = 1, leafAlphaToCoverage = true, simpleFoliage = true,
                forestHlodM = 70f, forestHlodCullM = 1000f,
                clearCoat = true, vehicleGrimeDetail = true, envCaptureSize = 64, envCaptureInterval = 6, envCaptureFarClip = 150f, envCaptureMinMove = 2f, envCaptureMaxAge = 20f, contactShadows = true, cabShadowLift = 8f, streetLights = 0, lampPools = 6,
                cloudQuality = 1, glassFast = true,
                budgetDrawCalls = 350, budgetTrianglesK = 550, budgetTextureMB = 96, budgetShadowMs = 1.5f, budgetStatus = "UNMEASURED",
            },
            new Tier
            {
                name = "High", renderScale = 1.0f, msaa = 2, postAntialiasing = AntialiasingMode.None, hdr = true,
                postProcessing = true, tonemapping = TonemappingMode.Neutral,
                shadowDistance = 100f, shadowResolution = 2048, shadowCascades = 3, cascade2Split = 0.25f,
                cascade4Split = new Vector3(0.2f, 0.55f, 0.8f), softShadows = true, softShadowQuality = SoftShadowQuality.Low,
                shadowDepthBias = 0.4f, shadowNormalBias = 0.3f,
                anisotropic = 1, worldTextureAniso = 8, worldMipBias = 0f, lodBias = 1.5f, cameraFarClip = 2500f, adaptiveScaleMin = 0.70f, thermalFallbackFps = 30, pacingFallbackFps = 30,
                upscalingFilter = UpscalingFilterSelection.FSR, fsrSharpness = 0f,
                worldDetail = true, additionalLightsPerObject = 4,
                treeCardLodScale = 0.5f, treeThinStartM = 90f, treeCullM = 600f, treeShadowLodMask = 1, leafAlphaToCoverage = true, simpleFoliage = true,
                forestHlodM = 120f, forestHlodCullM = 0f,
                clearCoat = true, vehicleGrimeDetail = true, envCaptureSize = 128, envCaptureInterval = 3, envCaptureFarClip = 200f, envCaptureMinMove = 0.5f, envCaptureMaxAge = 10f, contactShadows = true, cabShadowLift = 8f, streetLights = 4, lampPools = 8,
                cloudQuality = 1,
                budgetDrawCalls = 800, budgetTrianglesK = 1500, budgetTextureMB = 256, budgetShadowMs = 2.0f, budgetStatus = "UNMEASURED (no flagship attached)",
            },
            new Tier
            {
                name = "Ultra", renderScale = 1.0f, msaa = 4, postAntialiasing = AntialiasingMode.None, hdr = true,
                postProcessing = true, tonemapping = TonemappingMode.Neutral,
                shadowDistance = 150f, shadowResolution = 4096, shadowCascades = 4, cascade2Split = 0.25f,
                cascade4Split = new Vector3(0.05f, 0.18f, 0.45f), softShadows = true, softShadowQuality = SoftShadowQuality.High,
                shadowDepthBias = 0.6f, shadowNormalBias = 0.6f,
                anisotropic = 2, worldTextureAniso = 16, worldMipBias = 0f, lodBias = 2.0f, cameraFarClip = 3500f, adaptiveScaleMin = 0.70f, thermalFallbackFps = 30, pacingFallbackFps = 30 /* ADR 0152: Fold Ultra/60 had no safety net */,
                worldDetail = true, additionalLightsPerObject = 8,
                treeCardLodScale = 0.5f, treeThinStartM = 90f, treeCullM = 600f, treeShadowLodMask = 3, leafAlphaToCoverage = true, simpleFoliage = true,
                forestHlodM = 120f, forestHlodCullM = 0f,
                clearCoat = true, vehicleGrimeDetail = true, envCaptureSize = 256, envCaptureInterval = 2, envCaptureFarClip = 300f, envCaptureMinMove = 0.5f, envCaptureMaxAge = 10f, contactShadows = true, cabShadowLift = 8f, streetLights = 6, lampPools = 8,
                cloudQuality = 2, ssao = true,
                budgetDrawCalls = 1000, budgetTrianglesK = 2000, budgetTextureMB = 384, budgetShadowMs = 3.0f, budgetStatus = "UNMEASURED (no flagship attached)",
            },
        };
    }
}
