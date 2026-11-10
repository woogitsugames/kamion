using System;
using System.Globalization;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering
{
    /// <summary>
    /// Profiling overrides on top of the active quality tier, from launch arguments (adb: <c>-e rq_msaa 1</c>). Used to
    /// find the GPU bottleneck on the phone by ablation (one feature off at a time, uncapped frame rate, same control
    /// camera) when no vendor GPU profiler is available. Not a player setting; ignored unless an argument is given.
    /// Keys: rq_msaa (1/2/4), rq_scale (render scale), rq_shadow (shadow distance m, 0 = off), rq_post (0/1),
    /// rq_hdr (0/1), rq_a2c (0/1 leaf alpha-to-coverage), rq_trees (0 = no instanced trees), rq_treeshadow (LOD mask),
    /// rq_card (tree card LOD scale), rq_cull (tree cull m), rq_thin (tree thinning start m), rq_vegshader (0/1 simple foliage),
    /// rq_hlod (forest HLOD switch distance m, 0 = off; ADR 0015), rq_a8 (0 = clear coat, reflection capture, contact
    /// shadows, cab shadow lift and street-lamp lights off: A8 before/after in one APK), rq_envcap (capture face px, 0 = off),
    /// ADR 0062: rq_scalemin (adaptive render-scale floor, e.g. 0.8 vs 0.7 A/B), rq_upscale (linear / fsr / stp / auto / point),
    /// rq_fsrsharp (FSR RCAS sharpness 0..1), rq_pacing (0 = no frame-pacing 30 FPS fallback), rq_lamppools (analytic
    /// street-lamp pools on world surfaces, 0 = off).
    /// ADR 0068: rq_mirror_cap (mirror renders per frame), rq_mirror_lod (class II mirror LOD scale, 1 = main-view LOD),
    /// rq_mirror_far (class II far clip m), rq_mirror_res (mirror texture height multiplier), rq_mirror_rate (0 = ADR 0046
    /// fill schedule, 1 = due-based), rq_mirror_legacy (1 = whole pre-0068 mirror configuration), rq_mirror_off (1 = no
    /// mirror renders), rq_envcap_iv (capture: one face every N frames), rq_envcap_lod (capture LOD scale), rq_shadowcasc
    /// (cascade count), rq_shadowres (main-light shadow map px), rq_ab (interleaved A/B of one pass: mirrors, mirrorcfg,
    /// mirrorlod, envcap, shadows, shadowcasc; ExtraViewCostMonitor) with rq_ab_period (s).
    /// </summary>
    public static class RenderOverrides
    {
        public static int? Msaa;
        public static float? RenderScale;
        public static float? ShadowDistance;
        public static bool? Post;
        public static bool? Hdr;
        public static bool? LeafA2C;
        public static bool? Trees;
        public static int? TreeShadowMask;
        public static float? TreeCardScale;
        public static float? TreeCull;
        public static float? TreeThin;
        public static bool? SimpleFoliage;
        public static float? ForestHlod;
        public static bool? VehicleLook;
        public static int? EnvCapture;
        public static float? ScaleMin;
        public static string Upscale;
        public static float? FsrSharpness;
        public static bool? Pacing;
        public static int? LampPools;
        public static bool? WorldGi;
        public static bool? WorldSun;
        public static int? EnvCaptureInterval;
        public static float? EnvCaptureLod;
        public static int? ShadowCascades;
        public static int? ShadowResolution;
        public static int? Clouds;       // ADR 0080: rq_clouds -1 flat dome, 0..2 quality
        public static bool? GroundHaze;  // rq_haze
        public static bool? Ssao;        // rq_ssao
        public static bool Look;         // any of rq_look / rq_ev / rq_wet / rq_grassvar given
        public static string Ab;
        public static float? AbPeriod;

        public static bool Any => Msaa.HasValue || RenderScale.HasValue || ShadowDistance.HasValue || Post.HasValue || Hdr.HasValue ||
                                  LeafA2C.HasValue || Trees.HasValue || TreeShadowMask.HasValue || TreeCardScale.HasValue ||
                                  TreeCull.HasValue || TreeThin.HasValue || SimpleFoliage.HasValue || ForestHlod.HasValue ||
                                  VehicleLook.HasValue || EnvCapture.HasValue || ScaleMin.HasValue || Upscale != null ||
                                  FsrSharpness.HasValue || Pacing.HasValue || LampPools.HasValue || EnvCaptureInterval.HasValue ||
                                  EnvCaptureLod.HasValue || ShadowCascades.HasValue || ShadowResolution.HasValue || Ab != null ||
                                  Game.Core.MirrorOverrides.Any ||
                                  WorldGi.HasValue || WorldSun.HasValue ||
                                  Clouds.HasValue || GroundHaze.HasValue || Ssao.HasValue || Look;

        /// <summary>Reads the overrides through a launch-argument getter (platform services). Returns a log line.</summary>
        public static string Parse(Func<string, string> arg)
        {
            Msaa = I(arg("rq_msaa")); RenderScale = F(arg("rq_scale")); ShadowDistance = F(arg("rq_shadow"));
            Post = B(arg("rq_post")); Hdr = B(arg("rq_hdr")); LeafA2C = B(arg("rq_a2c")); Trees = B(arg("rq_trees"));
            TreeShadowMask = I(arg("rq_treeshadow")); TreeCardScale = F(arg("rq_card")); TreeCull = F(arg("rq_cull"));
            TreeThin = F(arg("rq_thin")); SimpleFoliage = B(arg("rq_vegshader")); ForestHlod = F(arg("rq_hlod"));
            VehicleLook = B(arg("rq_a8")); EnvCapture = I(arg("rq_envcap"));
            WorldGi = B(arg("rq_worldgi")); WorldSun = B(arg("rq_worldsun"));   // ADR 0064
            ScaleMin = F(arg("rq_scalemin")); FsrSharpness = F(arg("rq_fsrsharp")); Pacing = B(arg("rq_pacing")); LampPools = I(arg("rq_lamppools"));
            EnvCaptureInterval = I(arg("rq_envcap_iv")); EnvCaptureLod = F(arg("rq_envcap_lod"));
            ShadowCascades = I(arg("rq_shadowcasc")); ShadowResolution = I(arg("rq_shadowres"));
            // ADR 0080: sky / atmosphere switches and the owner A/B look overrides (rq_look 0|1|2 contrast variant A|B|C,
            // rq_ev exposure bias in stops, rq_wet wetness 0..1, rq_grassvar lawn variation 0..1).
            Clouds = I(arg("rq_clouds")); GroundHaze = B(arg("rq_haze")); Ssao = B(arg("rq_ssao"));
            int? look = I(arg("rq_look")); float? ev = F(arg("rq_ev")); float? wet = F(arg("rq_wet")); float? gvar = F(arg("rq_grassvar"));
            Look = look.HasValue || ev.HasValue || wet.HasValue || gvar.HasValue;
            WorldAtmosphere.LookVariant = look ?? -1;
            LightingPreset.ExposureBiasOverride = ev ?? 0f;
            WorldAtmosphere.WetOverride = wet;
            WorldAtmosphere.GrassOverride = gvar;
            string ab = arg("rq_ab");
            Ab = string.IsNullOrEmpty(ab) ? null : ab.ToLowerInvariant();
            AbPeriod = F(arg("rq_ab_period"));
            Game.Core.MirrorOverrides.Cap = I(arg("rq_mirror_cap"));
            Game.Core.MirrorOverrides.LodScale = F(arg("rq_mirror_lod"));
            Game.Core.MirrorOverrides.FarClip = F(arg("rq_mirror_far"));
            Game.Core.MirrorOverrides.Resolution = F(arg("rq_mirror_res"));
            Game.Core.MirrorOverrides.DueSchedule = B(arg("rq_mirror_rate"));
            Game.Core.MirrorOverrides.Legacy = B(arg("rq_mirror_legacy")) == true;
            Game.Core.MirrorOverrides.Suspended = B(arg("rq_mirror_off")) == true;
            string up = arg("rq_upscale");
            Upscale = string.IsNullOrEmpty(up) ? null : up.ToLowerInvariant();
            return Any ? $"msaa={Msaa} scale={RenderScale} shadow={ShadowDistance} post={Post} hdr={Hdr} a2c={LeafA2C} trees={Trees} " +
                         $"treeshadow={TreeShadowMask} card={TreeCardScale} cull={TreeCull} thin={TreeThin} vegshader={SimpleFoliage} hlod={ForestHlod} a8={VehicleLook} envcap={EnvCapture} " +
                         $"scalemin={ScaleMin} upscale={Upscale} fsrsharp={FsrSharpness} pacing={Pacing} lamppools={LampPools} " +
                         $"envcap_iv={EnvCaptureInterval} envcap_lod={EnvCaptureLod} shadowcasc={ShadowCascades} shadowres={ShadowResolution} ab={Ab} ab_period={AbPeriod} " +
                         $"mirror_cap={Game.Core.MirrorOverrides.Cap} mirror_lod={Game.Core.MirrorOverrides.LodScale} mirror_far={Game.Core.MirrorOverrides.FarClip} " +
                         $"mirror_res={Game.Core.MirrorOverrides.Resolution} mirror_rate={Game.Core.MirrorOverrides.DueSchedule} mirror_legacy={Game.Core.MirrorOverrides.Legacy} " +
                         $"mirror_off={Game.Core.MirrorOverrides.Suspended} worldgi={WorldGi} worldsun={WorldSun} " +
                         $"clouds={Clouds} haze={GroundHaze} ssao={Ssao} look={WorldAtmosphere.LookVariant} ev={LightingPreset.ExposureBiasOverride} wet={WorldAtmosphere.WetOverride}" : null;
        }

        /// <summary>The tier with the overrides applied (vegetation + camera fields; URP asset fields by the applier).</summary>
        public static QualityProfile.Tier ApplyTo(QualityProfile.Tier t)
        {
            if (Msaa.HasValue) t.msaa = Msaa.Value;
            if (RenderScale.HasValue) t.renderScale = RenderScale.Value;
            if (ShadowDistance.HasValue) t.shadowDistance = ShadowDistance.Value;
            if (Post.HasValue) t.postProcessing = Post.Value;
            if (Hdr.HasValue) t.hdr = Hdr.Value;
            if (LeafA2C.HasValue) t.leafAlphaToCoverage = LeafA2C.Value;
            if (TreeShadowMask.HasValue) t.treeShadowLodMask = TreeShadowMask.Value;
            if (TreeCardScale.HasValue) t.treeCardLodScale = TreeCardScale.Value;
            if (TreeCull.HasValue) t.treeCullM = TreeCull.Value;
            if (TreeThin.HasValue) t.treeThinStartM = TreeThin.Value;
            if (SimpleFoliage.HasValue) t.simpleFoliage = SimpleFoliage.Value;
            if (ForestHlod.HasValue) t.forestHlodM = ForestHlod.Value > 0f ? ForestHlod.Value : -1f;   // -1 = off
            if (VehicleLook == false) { t.clearCoat = false; t.vehicleGrimeDetail = false; t.envCaptureSize = 0; t.contactShadows = false; t.cabShadowLift = 0f; t.streetLights = 0; }
            if (EnvCapture.HasValue) t.envCaptureSize = EnvCapture.Value;
            if (ScaleMin.HasValue) t.adaptiveScaleMin = ScaleMin.Value;
            if (FsrSharpness.HasValue) t.fsrSharpness = FsrSharpness.Value;
            if (Pacing.HasValue && !Pacing.Value) t.pacingFallbackFps = 0;
            if (LampPools.HasValue) t.lampPools = LampPools.Value;
            if (EnvCaptureInterval.HasValue) t.envCaptureInterval = Math.Max(1, EnvCaptureInterval.Value);
            if (ShadowCascades.HasValue) t.shadowCascades = Math.Max(1, Math.Min(4, ShadowCascades.Value));
            if (ShadowResolution.HasValue) t.shadowResolution = ShadowResolution.Value;
            if (Upscale != null)
            {
                switch (Upscale)
                {
                    case "linear": case "bilinear": t.upscalingFilter = UpscalingFilterSelection.Linear; break;
                    case "fsr": t.upscalingFilter = UpscalingFilterSelection.FSR; break;
                    case "stp": t.upscalingFilter = UpscalingFilterSelection.STP; break;
                    case "point": t.upscalingFilter = UpscalingFilterSelection.Point; break;
                    default: t.upscalingFilter = UpscalingFilterSelection.Auto; break;
                }
            }
            if (WorldGi.HasValue) t.worldSkyVisOff = !WorldGi.Value;
            if (WorldSun.HasValue) t.worldBakedSunOff = !WorldSun.Value;
            if (Clouds.HasValue) { t.cloudsOff = Clouds.Value < 0; t.cloudQuality = Math.Max(0, Math.Min(2, Clouds.Value)); }
            if (GroundHaze.HasValue) t.groundHazeOff = !GroundHaze.Value;
            if (Ssao.HasValue) t.ssao = Ssao.Value;
            return t;
        }

        static int? I(string s) => int.TryParse(s, NumberStyles.Integer, CultureInfo.InvariantCulture, out int v) ? v : (int?)null;
        static float? F(string s) => float.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out float v) ? v : (float?)null;
        static bool? B(string s) => string.IsNullOrEmpty(s) ? (bool?)null : s == "1" || s.Equals("true", StringComparison.OrdinalIgnoreCase) || s.Equals("on", StringComparison.OrdinalIgnoreCase);
    }
}
