using System;
using System.Collections.Generic;
using System.IO;
using Game.Editor.Build;
using UnityEditor;
using UnityEngine;

namespace Game.World.Import
{
    /// <summary>ADR0155 diagnostic native-cache mutation only; final proof always uses generator + import.</summary>
    public static class PutryShadowMaterialAblation
    {
        public static void RunBatch()
        {
            int exit = 1;
            try
            {
                string selected = EditorTools.Arg("-putryMaterial", "");
                string[] targeted;
                switch (selected)
                {
                    case "all-pbr": targeted = null; break;
                    case "deck-pair": targeted = new[] { "M_bridge_concrete", "M_road_asphalt" }; break;
                    case "deck-triple": targeted = new[] { "M_bridge_concrete", "M_road_asphalt", "M_bridge_kerb" }; break;
                    case "bridge-chunk": targeted = new[] { "M_bridge_concrete", "M_road_asphalt", "M_bridge_kerb", "M_barrier_steel", "M_ramp_wall_blocks" }; break;
                    case "M_viaduct_concrete": case "M_bridge_concrete": case "M_road_asphalt": case "M_bridge_kerb": targeted = new[] { selected }; break;
                    default: throw new ArgumentException("Unknown material diagnostic");
                }
                var log = new List<string>();
                int reset = 0;
                foreach (var guid in AssetDatabase.FindAssets("t:Material", new[] { "Assets/_Generated/World/bialystok-industrial-c/Materials" }))
                {
                    string path = AssetDatabase.GUIDToAssetPath(guid);
                    var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
                    if (mat == null || !mat.HasProperty(WorldShadowCasterBias.Property)) continue;
                    var def = new Dictionary<string, object>();
                    bool on = targeted == null || Array.IndexOf(targeted, mat.name) >= 0;
                    if (on) def["shadow_normal_bias_scale"] = 0.0;
                    WorldShadowCasterBias.Apply(mat, def);
                    EditorUtility.SetDirty(mat); reset++;
                    if (on) log.Add(path + " scale=" + mat.GetFloat(WorldShadowCasterBias.Property) + " keyword=" + mat.IsKeywordEnabled(WorldShadowCasterBias.Keyword));
                }
                log.Insert(0, "Reset every supported PBR material, then apply selected subset; reset count=" + reset);
                AssetDatabase.SaveAssets();
                string output = EditorTools.Arg("-putryOutput", "../artifacts/gpt-s16-r3");
                Directory.CreateDirectory(output); File.WriteAllLines(Path.Combine(output, "material-choice-" + selected + ".txt"), log);
                Debug.Log("PUTRY_MATERIAL_ABLATION: OK " + selected); exit = 0;
            }
            catch (Exception e) { Debug.LogException(e); }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }
    }
}
