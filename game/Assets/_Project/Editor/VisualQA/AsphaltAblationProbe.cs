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
            public string referenceMaterialPath;
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
            if (mode != "cracks_off" && mode != "photo_off" && mode != "grime_off" && mode != "behaton_preview")
                throw new InvalidOperationException($"Unknown asphalt ablation: {mode}");
            string referencePath = mode == "behaton_preview"
                ? "Assets/_Generated/World/bialystok-industrial-c/Materials/M_yard_behaton.mat" : null;
            var reference = referencePath != null ? AssetDatabase.LoadAssetAtPath<Material>(referencePath) : null;
            if (referencePath != null && reference == null) throw new InvalidOperationException("Behaton reference material missing");
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
                    else if (mode == "grime_off") block.SetVector("_Grime", Vector4.zero);
                    else
                    {
                        if (material.shader != reference.shader) throw new InvalidOperationException("Preview shader mismatch");
                        foreach (string property in new[] { "_BaseMap", "_NormalMap", "_MaskMap", "_VarMap", "_MacroMap" })
                        {
                            if (!reference.HasProperty(property) || reference.GetTexture(property) == null)
                                throw new InvalidOperationException($"Preview reference texture absent: {property}");
                            block.SetTexture(property, reference.GetTexture(property));
                        }
                        foreach (string property in new[] { "_Tint", "_Tile", "_Grime", "_GroundGrimeBase", "_GroundWearExclude", "_AsphaltWear" })
                            block.SetVector(property, reference.GetVector(property));
                        foreach (string property in new[] { "_NormalStrength", "_SmoothnessScale", "_MetallicScale", "_AlbedoScale",
                            "_ElementJitter", "_ElementSize", "_MacroSize", "_MacroStrength", "_MacroWear" })
                            block.SetFloat(property, reference.GetFloat(property));
                        block.SetFloat("_CrackStrength", 0f);
                        block.SetFloat("_DetailFade", 0.001f);
                    }
                    renderer.SetPropertyBlock(block, i);
                    matched.Add(path); slots++;
                }
            }
            string directory = Environment.GetEnvironmentVariable("KAMION_ASPHALT_QA_DIRECTORY");
            if (string.IsNullOrEmpty(directory)) throw new InvalidOperationException("Ablation output directory missing");
            Directory.CreateDirectory(directory);
            File.WriteAllText(Path.Combine(directory, "ablation-state.json"), JsonUtility.ToJson(new Evidence {
                mode = mode, targets = new List<string>(ids).ToArray(), matchedAssetPaths = new List<string>(matched).ToArray(),
                referenceMaterialPath = referencePath, materialSlots = slots,
                note = mode == "behaton_preview"
                    ? "Transient property-block family preview from M_yard_behaton; target UV path retained. No asset writes, fitted pose, orientation acceptance or final draw-budget evidence."
                    : "Transient renderer property blocks; asset uniforms stay unchanged. Diagnostic draw counts are not final budget evidence."
            }, true));
            Debug.Log($"[ASPHALT_ABLATION] mode={mode} materialSlots={slots}");
        }
    }
}
