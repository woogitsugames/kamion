using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Editor.VisualQA
{
    /// <summary>Explicit editor-only diagnostics. Property blocks are transient and never saved to materials.</summary>
    [InitializeOnLoad]
    public static class AsphaltAblationProbe
    {
        static bool applied;
        static readonly string mode = Environment.GetEnvironmentVariable("KAMION_ASPHALT_QA_ABLATION");
        [Serializable] sealed class Evidence
        {
            public string mode;
            public string[] targets, matchedAssetPaths;
            public int materialSlots;
            public string note = "Transient renderer property blocks; asset uniforms stay unchanged. Diagnostic draw counts are not final budget evidence.";
        }

        static AsphaltAblationProbe()
        {
            if (!string.IsNullOrEmpty(mode)) RenderPipelineManager.beginCameraRendering += Apply;
        }

        static void Apply(ScriptableRenderContext context, Camera camera)
        {
            if (applied || !camera.name.StartsWith("QA_", StringComparison.Ordinal) || camera.name == "QA_UICamera") return;
            applied = true;
            if (mode != "cracks_off" && mode != "photo_off" && mode != "grime_off")
                throw new InvalidOperationException($"Unknown asphalt ablation: {mode}");
            string requested = Environment.GetEnvironmentVariable("KAMION_ASPHALT_QA_ABLATION_MATERIALS") ?? "road_asphalt";
            var ids = new HashSet<string>(requested.Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries));
            var paths = new HashSet<string>();
            foreach (string id in ids) paths.Add($"Assets/_Generated/World/bialystok-industrial-c/Materials/M_{id}.mat");
            var matched = new HashSet<string>();
            int slots = 0;
            foreach (var renderer in UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsInactive.Exclude, FindObjectsSortMode.None))
            {
                var materials = renderer.sharedMaterials;
                for (int i = 0; i < materials.Length; i++)
                {
                    var material = materials[i];
                    if (material == null) continue;
                    string path = AssetDatabase.GetAssetPath(material);
                    if (!paths.Contains(path)) continue;
                    string keyword = mode == "cracks_off" ? "_CRACKS" : mode == "photo_off" ? "_PHOTO_DETAIL" : "_GRIME";
                    if (!material.IsKeywordEnabled(keyword)) continue;
                    var block = new MaterialPropertyBlock();
                    renderer.GetPropertyBlock(block, i);
                    if (mode == "cracks_off") block.SetFloat("_CrackStrength", 0f);
                    else if (mode == "photo_off") block.SetFloat("_DetailFade", 0.001f);
                    else block.SetVector("_Grime", Vector4.zero);
                    renderer.SetPropertyBlock(block, i);
                    matched.Add(path); slots++;
                }
            }
            string directory = Environment.GetEnvironmentVariable("KAMION_ASPHALT_QA_DIRECTORY");
            if (string.IsNullOrEmpty(directory)) throw new InvalidOperationException("Ablation output directory missing");
            Directory.CreateDirectory(directory);
            File.WriteAllText(Path.Combine(directory, "ablation-state.json"), JsonUtility.ToJson(new Evidence {
                mode = mode, targets = new List<string>(ids).ToArray(), matchedAssetPaths = new List<string>(matched).ToArray(), materialSlots = slots
            }, true));
            Debug.Log($"[ASPHALT_ABLATION] mode={mode} materialSlots={slots}");
        }
    }
}
