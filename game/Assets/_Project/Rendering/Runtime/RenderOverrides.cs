using System;
using System.Globalization;

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
        /// shadows, cab shadow lift and street-lamp lights off: A8 before/after in one APK), rq_envcap (capture face px, 0 = off).
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

        public static bool Any => Msaa.HasValue || RenderScale.HasValue || ShadowDistance.HasValue || Post.HasValue || Hdr.HasValue ||
                                  LeafA2C.HasValue || Trees.HasValue || TreeShadowMask.HasValue || TreeCardScale.HasValue ||
                                  TreeCull.HasValue || TreeThin.HasValue || SimpleFoliage.HasValue || ForestHlod.HasValue ||
                                  VehicleLook.HasValue || EnvCapture.HasValue;

        /// <summary>Reads the overrides through a launch-argument getter (platform services). Returns a log line.</summary>
        public static string Parse(Func<string, string> arg)
        {
            Msaa = I(arg("rq_msaa")); RenderScale = F(arg("rq_scale")); ShadowDistance = F(arg("rq_shadow"));
            Post = B(arg("rq_post")); Hdr = B(arg("rq_hdr")); LeafA2C = B(arg("rq_a2c")); Trees = B(arg("rq_trees"));
            TreeShadowMask = I(arg("rq_treeshadow")); TreeCardScale = F(arg("rq_card")); TreeCull = F(arg("rq_cull"));
            TreeThin = F(arg("rq_thin")); SimpleFoliage = B(arg("rq_vegshader")); ForestHlod = F(arg("rq_hlod"));
            VehicleLook = B(arg("rq_a8")); EnvCapture = I(arg("rq_envcap"));
            return Any ? $"msaa={Msaa} scale={RenderScale} shadow={ShadowDistance} post={Post} hdr={Hdr} a2c={LeafA2C} trees={Trees} " +
                         $"treeshadow={TreeShadowMask} card={TreeCardScale} cull={TreeCull} thin={TreeThin} vegshader={SimpleFoliage} hlod={ForestHlod} a8={VehicleLook} envcap={EnvCapture}" : null;
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
            if (VehicleLook == false) { t.clearCoat = false; t.envCaptureSize = 0; t.contactShadows = false; t.cabShadowLift = 0f; t.streetLights = 0; }
            if (EnvCapture.HasValue) t.envCaptureSize = EnvCapture.Value;
            return t;
        }

        static int? I(string s) => int.TryParse(s, NumberStyles.Integer, CultureInfo.InvariantCulture, out int v) ? v : (int?)null;
        static float? F(string s) => float.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out float v) ? v : (float?)null;
        static bool? B(string s) => string.IsNullOrEmpty(s) ? (bool?)null : s == "1" || s.Equals("true", StringComparison.OrdinalIgnoreCase) || s.Equals("on", StringComparison.OrdinalIgnoreCase);
    }
}
