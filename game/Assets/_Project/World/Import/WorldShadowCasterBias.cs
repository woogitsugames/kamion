using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace Game.World.Import
{
    /// <summary>ADR0155: optional normal-bias scale in the existing PBR shadow pass. No global quality override.</summary>
    public static class WorldShadowCasterBias
    {
        public const string Property = "_ShadowNormalBiasScale";
        public const string Keyword = "_SHADOW_NORMAL_BIAS_SCALE";

        public static void ApplyRegionPolicy(Material material, Dictionary<string, object> definition, string region, string materialId)
        {
            string path = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "Data", "Regions", region, "shadow_caster_bias.json"));
            ApplyPolicy(material, definition, materialId, path);
        }

        /// <summary>The optional region file overlays one material field; removing a file/entry restores legacy bias.</summary>
        public static void ApplyPolicy(Material material, Dictionary<string, object> definition, string materialId, string path)
        {
            if (material == null || !material.HasProperty(Property)) return;
            if (File.Exists(path))
            {
                var policy = MiniJson.Parse(File.ReadAllText(path)) as Dictionary<string, object>;
                if (policy == null || !policy.TryGetValue("schema", out var schema) ||
                    schema as string != "kamion/shadow-caster-bias/1" ||
                    !policy.TryGetValue("materials", out var entries) || !(entries is Dictionary<string, object> materials))
                    throw new InvalidDataException("Invalid shadow caster policy: " + path);
                if (materials.TryGetValue(materialId, out var value))
                {
                    if (!TryScale(value, out _)) throw new InvalidDataException("Invalid normal bias scale: " + materialId);
                    definition = definition != null ? new Dictionary<string, object>(definition) : new Dictionary<string, object>();
                    definition["shadow_normal_bias_scale"] = value;
                }
            }
            Apply(material, definition);
        }

        static bool TryScale(object value, out float scale)
        {
            scale = 1f;
            if (!(value is double || value is float || value is int || value is long)) return false;
            double candidate = Convert.ToDouble(value);
            if (double.IsNaN(candidate) || double.IsInfinity(candidate) || candidate < 0 || candidate > 1) return false;
            scale = (float)candidate;
            return true;
        }

        public static void Apply(Material material, Dictionary<string, object> definition)
        {
            if (material == null || !material.HasProperty(Property)) return;
            float scale = 1f;
            if (definition != null && definition.TryGetValue("shadow_normal_bias_scale", out var value)) TryScale(value, out scale);
            bool changed = false;
            // Avoid serializing a new default property into every unrelated cached material.
            if (material.GetFloat(Property) != scale) { material.SetFloat(Property, scale); changed = true; }
            bool enabled = scale < 1f;
            if (material.IsKeywordEnabled(Keyword) != enabled)
            {
                changed = true;
                if (enabled) material.EnableKeyword(Keyword);
                else material.DisableKeyword(Keyword);
            }
            if (changed) UnityEditor.EditorUtility.SetDirty(material);
        }
    }
}
