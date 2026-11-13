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
                var names = new[] { "M_viaduct_concrete", "M_bridge_concrete", "M_road_asphalt", "M_bridge_kerb" };
                string selected = EditorTools.Arg("-putryMaterial", "");
                if (Array.IndexOf(names, selected) < 0) throw new ArgumentException("Unknown material diagnostic");
                var log = new List<string>();
                foreach (string name in names)
                {
                    var mat = AssetDatabase.LoadAssetAtPath<Material>($"Assets/_Generated/World/bialystok-industrial-c/Materials/{name}.mat");
                    if (mat == null || !mat.HasProperty(WorldShadowCasterBias.Property)) throw new InvalidOperationException("Unsupported diagnostic material: " + name);
                    var def = new Dictionary<string, object>();
                    if (name == selected) def["shadow_normal_bias_scale"] = 0.0;
                    WorldShadowCasterBias.Apply(mat, def);
                    EditorUtility.SetDirty(mat);
                    log.Add(name + " scale=" + mat.GetFloat(WorldShadowCasterBias.Property) + " keyword=" + mat.IsKeywordEnabled(WorldShadowCasterBias.Keyword));
                }
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
