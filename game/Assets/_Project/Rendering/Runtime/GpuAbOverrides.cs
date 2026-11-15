using System;
using System.Globalization;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering
{
    /// <summary>
    /// ADR 0241 (B-113, A16 Low GPU A/B): the launch-argument switches that <see cref="RenderOverrides"/> did not have yet,
    /// kept in their own file so that parallel work on RenderOverrides / QualityProfile only meets three one-line hooks.
    /// Nothing here is a player setting or a tier default: every switch is null / off unless its argument is given, and
    /// then it only changes run-time state (URP asset in memory, static A/B flags), never a saved asset.
    /// Keys: rq_depthtex 0|1 (URP camera depth texture of the main view), rq_opaquetex 0|1 (URP camera opaque / colour
    /// copy), rq_impostors 0 (no tree impostor LOD for the whole run), rq_hlodpart 1|2 (forest HLOD without the canopy /
    /// without the edge walls for the whole run), rq_abtag &lt;text&gt; (label of the variant, logged only).
    /// The whole-run switches use the same WorldInstances hooks as the interleaved rq_ab keys impostor / hlodcanopy /
    /// hlodedge (ADR 0106) - do not combine them with those rq_ab keys in one launch.
    /// The switches that already existed (rq_scale, rq_msaa, rq_post, rq_shadow, rq_lod, rq_thin, rq_cull, rq_card,
    /// rq_hlod, ...) stay in RenderOverrides; the variant catalogue is scripts/gpu-ab-variants.json.
    /// </summary>
    public static class GpuAbOverrides
    {
        public const string DepthTextureKey = "rq_depthtex", OpaqueTextureKey = "rq_opaquetex", ImpostorsKey = "rq_impostors",
                            HlodPartKey = "rq_hlodpart", TagKey = "rq_abtag";

        public static bool? DepthTexture;
        public static bool? OpaqueTexture;
        public static bool? Impostors;
        /// <summary>0 / null = whole forest HLOD, 1 = no canopy submeshes, 2 = no edge-wall submeshes.</summary>
        public static int? HlodPart;
        /// <summary>Variant label of the run (scripts/gpu-ab-a16.ps1); log only, never changes rendering.</summary>
        public static string Tag;

        static bool s_OwnsImpostorFlag, s_OwnsHlodPart;

        /// <summary>True when a switch that changes rendering was given (the tag alone does not count).</summary>
        public static bool Any => DepthTexture.HasValue || OpaqueTexture.HasValue || Impostors.HasValue || HlodPart.HasValue;

        /// <summary>Reads the switches; called from <see cref="RenderOverrides.Parse"/>. A getter that returns null for
        /// every key restores the shipping state (also of the WorldInstances flags this class set earlier).</summary>
        public static void Parse(Func<string, string> arg)
        {
            DepthTexture = B(arg(DepthTextureKey));
            OpaqueTexture = B(arg(OpaqueTextureKey));
            Impostors = B(arg(ImpostorsKey));
            int? part = I(arg(HlodPartKey));
            HlodPart = part.HasValue && part.Value >= 1 && part.Value <= 2 ? part : null;   // anything else = shipping
            string tag = arg(TagKey);
            Tag = string.IsNullOrEmpty(tag) ? null : tag;
            // The flags are shared with the rq_ab toggles (ExtraViewCostMonitor): only touch them when this class set
            // them or sets them now, so a launch without these keys never writes to them.
            if (Impostors.HasValue || s_OwnsImpostorFlag)
            {
                RenderOverrides.AbImpostorOff = Impostors == false;
                s_OwnsImpostorFlag = Impostors.HasValue;
            }
            if (HlodPart.HasValue || s_OwnsHlodPart)
            {
                RenderOverrides.AbHlodPart = HlodPart ?? 0;
                s_OwnsHlodPart = HlodPart.HasValue;
            }
        }

        /// <summary>Suffix of the RenderOverrides log line ("" when nothing was given).</summary>
        public static string Describe() =>
            Any || Tag != null ? $" depthtex={DepthTexture} opaquetex={OpaqueTexture} impostors={Impostors} hlodpart={HlodPart} abtag={Tag}" : "";

        /// <summary>Run-time only write to the active URP asset (QualityProfileApplier.ApplyPipelineOverrides); the
        /// value of a switch that was not given is left as baked by ProjectSetup.</summary>
        public static void ApplyPipeline(UniversalRenderPipelineAsset urp)
        {
            if (urp == null) return;
            if (DepthTexture.HasValue) urp.supportsCameraDepthTexture = DepthTexture.Value;
            if (OpaqueTexture.HasValue) urp.supportsCameraOpaqueTexture = OpaqueTexture.Value;
        }

        static int? I(string s) => int.TryParse(s, NumberStyles.Integer, CultureInfo.InvariantCulture, out int v) ? v : (int?)null;
        static bool? B(string s) => string.IsNullOrEmpty(s) ? (bool?)null : s == "1" || s.Equals("true", StringComparison.OrdinalIgnoreCase) || s.Equals("on", StringComparison.OrdinalIgnoreCase);
    }
}
