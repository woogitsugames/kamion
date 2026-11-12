using System;
using System.Collections.Generic;
using System.IO;
using Game.Editor.Build;
using Game.Rendering;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Editor.VisualQA
{
    /// <summary>Editor material ablations: AO mip or diffuse fill recovery. No saved material/texture changes.</summary>
    public static class CabAoMipAudit
    {
        public static void Run()
        {
            int exit = 1;
            try
            {
                string tier = EditorTools.Arg("-cabTier", "High"), lighting = EditorTools.Arg("-cabLighting", "clear");
                string output = EditorTools.Arg("-cabOutput", Path.Combine(EditorTools.RepoRoot, "artifacts/cab-r2/ao-mip-audit"));
                string ablation = EditorTools.Arg("-cabAblation", "ao-mip0");
                if (ablation != "ao-mip0" && ablation != "fill-recovery") throw new ArgumentException("Unknown cab material ablation");
                foreach (bool mip0 in new[] { false, true })
                {
                    Exception failure = null;
                    var saved = new Dictionary<Renderer, Material[]>();
                    var materials = new Dictionary<Material, Material>();
                    var textures = new Dictionary<Texture, Texture2D>();
                    void Restore()
                    {
                        foreach (var pair in saved) if (pair.Key != null) pair.Key.sharedMaterials = pair.Value;
                        saved.Clear();
                    }
                    void Before(ScriptableRenderContext context, Camera camera)
                    {
                        var control = camera.GetComponent<ControlCamera>();
                        if (!mip0 || control == null || (control.id != "cab-grain" && control.id != "cab-dash")) return;
                        try
                        {
                        Restore();
                        foreach (var renderer in UnityEngine.Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
                        {
                            var original = renderer.sharedMaterials;
                            Material[] changed = null;
                            for (int slot = 0; slot < original.Length; slot++)
                            {
                                var material = original[slot];
                                if (material == null || !material.name.StartsWith("MI_Cab_Plastic", StringComparison.Ordinal)) continue;
                                if (!materials.TryGetValue(material, out var copy))
                                {
                                    if (ablation == "fill-recovery")
                                    {
                                        if (!material.HasProperty("_CabFillOcclusionRecovery")) throw new InvalidOperationException("Missing diffuse recovery property");
                                        copy = new Material(material) { name = material.name + "_FillRecoveryAudit" };
                                        copy.EnableKeyword("_KAMION_CAB_FILL_RECOVERY"); copy.SetFloat("_CabFillOcclusionRecovery", 1);
                                        materials.Add(material, copy);
                                    }
                                    else
                                    {
                                    var ao = material.GetTexture("_AO");
                                    if (ao == null) throw new InvalidOperationException("Missing cab AO atlas");
                                    if (!textures.TryGetValue(ao, out var texture))
                                    {
                                        var previous = RenderTexture.active;
                                        var target = RenderTexture.GetTemporary(ao.width, ao.height, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Linear);
                                        try
                                        {
                                            Graphics.Blit(ao, target);
                                            RenderTexture.active = target;
                                            texture = new Texture2D(ao.width, ao.height, TextureFormat.RGBA32, false, true)
                                            { name = "CabAo_Mip0_Only", filterMode = ao.filterMode, wrapMode = ao.wrapMode };
                                            texture.ReadPixels(new Rect(0, 0, ao.width, ao.height), 0, 0);
                                            texture.Apply(false, false);
                                            textures.Add(ao, texture);
                                            Debug.Log($"CAB_AO_MIP_AUDIT copied {ao.name} {ao.width}x{ao.height}, mips={texture.mipmapCount}");
                                        }
                                        finally { RenderTexture.active = previous; RenderTexture.ReleaseTemporary(target); }
                                    }
                                    copy = new Material(material) { name = material.name + "_AoMip0Audit" };
                                    copy.SetTexture("_AO", texture); materials.Add(material, copy);
                                    }
                                }
                                if (changed == null) changed = (Material[])original.Clone();
                                changed[slot] = copy;
                            }
                            if (changed != null) { saved.Add(renderer, original); renderer.sharedMaterials = changed; }
                        }
                        }
                        catch (Exception exception) { failure = exception; Restore(); }
                    }
                    void After(ScriptableRenderContext context, Camera camera)
                    {
                        var control = camera.GetComponent<ControlCamera>();
                        if (control != null && (control.id == "cab-grain" || control.id == "cab-dash")) Restore();
                    }
                    RenderPipelineManager.beginCameraRendering += Before;
                    RenderPipelineManager.endCameraRendering += After;
                    try
                    {
                        int rendered = VisualQaRunner.Render(tier == "High" ? "WorldC_High" : "WorldC", 1920, 1080, tier,
                            Path.Combine(output, mip0 ? ablation : "baseline"), lighting, "cab-grain,cab-dash");
                        if (failure != null) throw failure;
                        if (rendered != 2) throw new InvalidOperationException("Expected two AO audit views");
                        if (mip0 && materials.Count == 0) throw new InvalidOperationException("Material ablation did not run");
                        if (mip0 && ablation == "ao-mip0" && textures.Count == 0) throw new InvalidOperationException("AO mip ablation did not run");
                    }
                    finally
                    {
                        RenderPipelineManager.beginCameraRendering -= Before; RenderPipelineManager.endCameraRendering -= After;
                        Restore();
                        foreach (var material in materials.Values) UnityEngine.Object.DestroyImmediate(material);
                        foreach (var texture in textures.Values) UnityEngine.Object.DestroyImmediate(texture);
                    }
                }
                exit = 0;
            }
            catch (Exception exception) { Debug.LogException(exception); }
            Debug.Log("CAB_AO_MIP_AUDIT_RESULT: " + (exit == 0 ? "OK" : "FAILED"));
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }
    }
}
