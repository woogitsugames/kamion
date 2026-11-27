using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering
{
    /// <summary>
    /// PC graphics tiers (ADR 0269, D74). Public API for the settings menu (ADR 0270):
    /// <see cref="Apply(PcTier, bool)"/>, <see cref="Current"/>, <see cref="DefaultFor(PcHardwareInfo)"/>.
    ///
    /// A PC tier is the Unity quality level of the same name (content tier, mirror budgets, name-based policies stay as on
    /// the phone) plus, on desktop only: the tier's own URP asset (Resources/PcTiers/URP_PC_*, set as the quality level's
    /// render pipeline at run time - ProjectSettings untouched), QualitySettings fields (LOD bias, maximum LOD, texture
    /// mipmap limit, anisotropic filtering) and the camera / vegetation fields that <see cref="QualityProfileApplier"/>
    /// reads from <see cref="Overlay"/>. Every path that changes the quality level (QualityTiers.Apply: launch argument
    /// -tier, saved choice, diagnostics button, menu) ends here, so the PC values cannot be bypassed. Called only when the
    /// tier changes; nothing runs per frame (no GC in the driving loop).
    /// Phones and the editor are unchanged unless <see cref="ForceEnabled"/> is set (editor preview / tests); in the
    /// editor <see cref="RestoreEditorState"/> undoes the run-time QualitySettings changes so ProjectSettings stay clean.
    /// </summary>
    public static class PcGraphicsTiers
    {
        /// <summary>null = automatic (desktop player only); true = also in the editor (visual QA preview); false = off.</summary>
        public static bool? ForceEnabled;

        public static bool IsDesktopPlayer(RuntimePlatform p) =>
            p == RuntimePlatform.WindowsPlayer || p == RuntimePlatform.OSXPlayer || p == RuntimePlatform.LinuxPlayer;

        public static bool Enabled => ForceEnabled ?? (IsDesktopPlayer(Application.platform) && !DisabledByArgument());

        static int s_ArgOff = -1;
        /// <summary>A/B: launch argument "-pc_tiers 0" runs a desktop player on the mobile URP assets / values (measurement only).</summary>
        static bool DisabledByArgument()
        {
            if (s_ArgOff < 0)
            {
                s_ArgOff = 0;
                var args = Environment.GetCommandLineArgs();
                for (int i = 0; i < args.Length - 1; i++)
                    if (string.Equals(args[i], "-pc_tiers", StringComparison.OrdinalIgnoreCase) && args[i + 1] == "0") s_ArgOff = 1;
            }
            return s_ArgOff == 1;
        }

        static bool s_HasCurrent;
        static PcTier s_Current = PcTier.High;

        /// <summary>The PC tier in effect (last applied; before the first apply: the quality level's name, else High).</summary>
        public static PcTier Current
        {
            get
            {
                if (s_HasCurrent) return s_Current;
                return PcTierTable.TryParse(QualityTiers.Current, out var t) ? t : PcTier.High;
            }
        }

        /// <summary>Raised after a PC tier was applied (desktop / preview only).</summary>
        public static event Action<PcTier> Changed;

        public static PcTierSettings Settings(PcTier tier) => PcTierTable.Get(tier);

        /// <summary>First-launch tier for this hardware (pure; ADR 0269 §detekcja).</summary>
        public static PcTier DefaultFor(PcHardwareInfo hw) => PcTierTable.DefaultFor(hw);
        public static PcTier DefaultFor(PcHardwareInfo hw, out string reason) => PcTierTable.DefaultFor(hw, out reason);

        /// <summary>SystemInfo of this machine (graphicsMemorySize = dedicated VRAM on Windows, MB).</summary>
        public static PcHardwareInfo DetectHardware() =>
            new PcHardwareInfo(SystemInfo.graphicsDeviceName, SystemInfo.graphicsMemorySize, SystemInfo.systemMemorySize);

        /// <summary>Applies a PC tier (quality level + PC overrides). <paramref name="persist"/> saves the choice like the
        /// mobile tier (PlayerPrefs, read by GameBootstrap on the next start). Returns false if the quality level is missing.</summary>
        public static bool Apply(PcTier tier, bool persist = false) => QualityTiers.Apply(PcTierTable.NameOf(tier), persist);

        /// <summary>Called by QualityTiers.Apply after the quality level changed.</summary>
        internal static void OnQualityLevelApplied(string levelName)
        {
            if (!Enabled || !PcTierTable.TryParse(levelName, out var tier)) return;
            ApplyPlatformSettings(tier);
        }

        static readonly Dictionary<string, UniversalRenderPipelineAsset> s_Assets = new Dictionary<string, UniversalRenderPipelineAsset>();

        public static UniversalRenderPipelineAsset LoadAsset(PcTier tier)
        {
            var s = PcTierTable.Get(tier);
            if (!s_Assets.TryGetValue(s.urpAsset, out var a) || a == null)
            {
                a = Resources.Load<UniversalRenderPipelineAsset>(s.urpAsset);
                s_Assets[s.urpAsset] = a;
            }
            return a;
        }

        struct LevelState
        {
            public RenderPipelineAsset pipeline;
            public float lodBias;
            public int maxLod, mipLimit;
            public AnisotropicFiltering aniso;
        }
        static readonly Dictionary<int, LevelState> s_EditorRestore = new Dictionary<int, LevelState>();

        static void ApplyPlatformSettings(PcTier tier)
        {
            var s = PcTierTable.Get(tier);
            if (Application.isEditor)
            {
                int level = QualitySettings.GetQualityLevel();
                if (!s_EditorRestore.ContainsKey(level))
                    s_EditorRestore[level] = new LevelState
                    {
                        pipeline = QualitySettings.renderPipeline, lodBias = QualitySettings.lodBias, maxLod = QualitySettings.maximumLODLevel,
                        mipLimit = QualitySettings.globalTextureMipmapLimit, aniso = QualitySettings.anisotropicFiltering,
                    };
            }
            var asset = LoadAsset(tier);
            if (asset != null)
            {
                if (QualitySettings.renderPipeline != asset) QualitySettings.renderPipeline = asset;   // run-time override of this level
            }
            else Debug.LogWarning($"[PC_TIER] missing Resources/{s.urpAsset}; keeping the quality level's URP asset");
            QualitySettings.lodBias = s.lodBias;
            QualitySettings.maximumLODLevel = s.maximumLodLevel;
            QualitySettings.globalTextureMipmapLimit = s.textureMipmapLimit;
            QualitySettings.anisotropicFiltering = (AnisotropicFiltering)s.anisotropicFiltering;
            s_Current = tier;
            s_HasCurrent = true;
            Debug.Log($"[PC_TIER] {s.Name} urp={(asset != null ? asset.name : "none")} scale={s.renderScale} msaa={s.msaa} " +
                      $"shadows={s.shadowDistance}m/{s.shadowCascades}c/{s.shadowResolution} lodBias={s.lodBias} mipLimit={s.textureMipmapLimit} " +
                      $"far={s.cameraFarClip} ssao={s.ssao} ({s.status})");
            Changed?.Invoke(tier);
        }

        /// <summary>Editor only: puts back the quality levels' URP assets and QualitySettings fields changed by a preview,
        /// so QualitySettings.asset is not left modified (AGENT-RULES §2). No-op in players.</summary>
        public static void RestoreEditorState()
        {
            if (!Application.isEditor || s_EditorRestore.Count == 0) return;
            int current = QualitySettings.GetQualityLevel();
            foreach (var kv in s_EditorRestore)
            {
                QualitySettings.SetQualityLevel(kv.Key, false);
                QualitySettings.renderPipeline = kv.Value.pipeline;
                QualitySettings.lodBias = kv.Value.lodBias;
                QualitySettings.maximumLODLevel = kv.Value.maxLod;
                QualitySettings.globalTextureMipmapLimit = kv.Value.mipLimit;
                QualitySettings.anisotropicFiltering = kv.Value.aniso;
            }
            QualitySettings.SetQualityLevel(current, false);
            s_EditorRestore.Clear();
            s_HasCurrent = false;
        }

        public static AntialiasingMode ToUrp(PcPostAntialiasing aa)
        {
            switch (aa)
            {
                case PcPostAntialiasing.Fxaa: return AntialiasingMode.FastApproximateAntialiasing;
                case PcPostAntialiasing.Smaa: return AntialiasingMode.SubpixelMorphologicalAntiAliasing;
                default: return AntialiasingMode.None;
            }
        }

        /// <summary>
        /// The mobile tier of the same name with the PC values on top (used by QualityProfileApplier when <see cref="Enabled"/>).
        /// Fields not in <see cref="PcTierSettings"/> (vehicle look, lamps, baked lighting, sky flags) stay as on the phone.
        /// Adaptive render scale and thermal / pacing fallbacks are off on PC (fixed native resolution, no thermal API).
        /// </summary>
        public static QualityProfile.Tier Overlay(QualityProfile.Tier t)
        {
            if (!PcTierTable.TryParse(t.name, out var tier)) return t;
            var s = PcTierTable.Get(tier);
            t.renderScale = s.renderScale;
            t.msaa = s.msaa;
            t.postAntialiasing = ToUrp(s.postAntialiasing);
            t.hdr = s.hdr;
            t.postProcessing = s.postProcessing;
            if (s.postProcessing && t.tonemapping == TonemappingMode.None) t.tonemapping = TonemappingMode.Neutral;
            t.shadowDistance = s.shadowDistance;
            t.shadowResolution = s.shadowResolution;
            t.shadowCascades = s.shadowCascades;
            t.cascade2Split = s.cascade2Split;
            t.cascade4Split = new Vector3(s.cascade4SplitX, s.cascade4SplitY, s.cascade4SplitZ);
            t.softShadows = s.softShadows;
            t.softShadowQuality = (SoftShadowQuality)s.softShadowQuality;
            t.shadowDepthBias = s.shadowDepthBias;
            t.shadowNormalBias = s.shadowNormalBias;
            t.anisotropic = s.anisotropicFiltering;
            t.worldTextureAniso = s.worldTextureAniso;
            t.lodBias = s.lodBias;
            t.cameraFarClip = s.cameraFarClip;
            t.adaptiveScaleMin = 0f;
            t.thermalFallbackFps = 0;
            t.pacingFallbackFps = 0;
            t.upscalingFilter = UpscalingFilterSelection.Auto;
            t.fsrSharpness = 0f;
            t.additionalLightsPerObject = s.additionalLightsPerObject;
            t.ssao = s.ssao;
            t.treeCardLodScale = s.treeCardLodScale;
            t.treeThinStartM = s.treeThinStartM;
            t.treeCullM = s.treeCullM;
            t.treeShadowLodMask = s.treeShadowLodMask;
            t.forestHlodM = s.forestHlodM;
            t.forestHlodCullM = s.forestHlodCullM;
            t.vehicleCullM = s.vehicleCullM;
            t.simpleFoliage = s.simpleFoliage;
            t.leafAlphaToCoverage = s.msaa > 1;
            t.treeLodFade = s.treeLodFade;
            t.forestFast = s.forestFast;
            t.glassFast = s.glassFast;
            t.windscreenLayersOff = s.windscreenLayersOff;   // ADR 0341
            t.envCaptureSize = s.envCaptureSize;
            t.envCaptureInterval = s.envCaptureInterval;
            t.streetLights = s.streetLights;
            t.lampPools = s.lampPools;
            t.cloudQuality = s.cloudQuality;
            t.mirrorResolutionScale = s.mirrorResolutionScale;
            t.mirrorMsaa = s.mirrorMsaa;
            t.mirrorShadows = s.mirrorShadows;
            t.mirrorWindowTexelsPerPixel = s.mirrorWindowTexelsPerPixel;
            t.budgetStatus = s.status;
            return PcNightLighting.Overlay(tier, t);   // night-pc-s23: dusk / night fields (pools, highlight, headlamps)
        }
    }
}
