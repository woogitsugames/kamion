using System;
using UnityEngine;

namespace Game.World
{
    /// <summary>ADR0088: local pine-canopy scattering; healthy broadleaf materials retain the baseline.</summary>
    public static class VegetationCanopyPolicy
    {
        /// <summary>
        /// ADR 0352 (critic s24 wave 11 # 10): Kamion/Vegetation _TreeVar of an instanced tree material - x brightness
        /// +-, y hue +- of the whole tree (seed = its instance matrix), z strength of the lit / shaded foliage clumps on
        /// the leaf cards, w their frequency (rad per model metre). Zero for everything that is not a library tree
        /// (Fab plants, hedges, forest HLOD walls: not instanced per tree). Conifers vary less (needles of one stand
        /// are one green) and keep a weaker clump term. WORKING_VALUE, read off the control cameras.
        /// </summary>
        public static Vector4 TreeVariation(string materialName)
        {
            bool leaves = materialName.IndexOf("leaves_", StringComparison.Ordinal) >= 0;
            bool impostor = materialName.IndexOf("impostor_tree_", StringComparison.Ordinal) >= 0;
            if (!leaves && !impostor) return new Vector4(0f, 0f, 0f, 1.5f);
            bool conifer = materialName.IndexOf("pine", StringComparison.Ordinal) >= 0 ||
                           materialName.IndexOf("spruce", StringComparison.Ordinal) >= 0;
            return conifer ? new Vector4(0.07f, 0.02f, 0.18f, 1.5f) : new Vector4(0.11f, 0.05f, 0.30f, 1.5f);
        }

        public static void Apply(Material material)
        {
            if (material == null || !material.HasProperty("_AmbientTransmission")) return;
            string name = material.name;
            bool pine = name.IndexOf("leaves_pine", StringComparison.Ordinal) >= 0 ||
                        name.IndexOf("impostor_tree_pine", StringComparison.Ordinal) >= 0;
            bool conifer = name.IndexOf("forest_edge_conifer", StringComparison.Ordinal) >= 0;
            bool mixed = name.IndexOf("forest_edge_mixed", StringComparison.Ordinal) >= 0;
            // WORKING_VALUE: the direct-only bake omits transmitted / multiply scattered light.
            // No emission or albedo floor; no global sky, exposure or tint change.
            material.SetFloat("_AmbientTransmission", pine || conifer ? 0.40f : mixed ? 0.32f : 0.25f);
            material.SetFloat("_CrownShade", pine ? 0.25f : 0.50f);
            if (material.HasProperty("_TreeVar")) material.SetVector("_TreeVar", TreeVariation(name));
            if (material.HasProperty("_Impostor"))
            {
                Vector4 visibility = material.GetVector("_Impostor");
                if (material.IsKeywordEnabled("_IMPOSTOR") && pine) visibility.y = 0.30f;
                if (material.IsKeywordEnabled("_HLOD_EDGE"))
                    visibility.y = conifer ? 0.65f : mixed ? 0.85f : 1.0f;
                material.SetVector("_Impostor", visibility);
            }
        }
    }
}
