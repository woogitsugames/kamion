using System;
using UnityEngine;

namespace Game.World
{
    /// <summary>ADR0088: local pine-canopy scattering; healthy broadleaf materials retain the baseline.</summary>
    public static class VegetationCanopyPolicy
    {
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
