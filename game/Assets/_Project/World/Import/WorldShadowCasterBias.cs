using System;
using System.Collections.Generic;
using UnityEngine;

namespace Game.World.Import
{
    /// <summary>ADR0155: optional normal-bias scale in the existing PBR shadow pass. No global quality override.</summary>
    public static class WorldShadowCasterBias
    {
        public const string Property = "_ShadowNormalBiasScale";
        public const string Keyword = "_SHADOW_NORMAL_BIAS_SCALE";

        public static void Apply(Material material, Dictionary<string, object> definition)
        {
            if (material == null || !material.HasProperty(Property)) return;
            float scale = 1f;
            if (definition != null && definition.TryGetValue("shadow_normal_bias_scale", out var value) &&
                (value is double || value is float || value is int || value is long))
            {
                double candidate = Convert.ToDouble(value);
                if (!double.IsNaN(candidate) && !double.IsInfinity(candidate) && candidate >= 0 && candidate <= 1)
                    scale = (float)candidate;
            }
            // Avoid serializing a new default property into every unrelated cached material.
            if (material.GetFloat(Property) != scale) material.SetFloat(Property, scale);
            bool enabled = scale < 1f;
            if (material.IsKeywordEnabled(Keyword) != enabled)
            {
                if (enabled) material.EnableKeyword(Keyword);
                else material.DisableKeyword(Keyword);
            }
        }
    }
}
