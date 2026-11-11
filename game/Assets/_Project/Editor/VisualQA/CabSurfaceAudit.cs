using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Game.Editor.Build;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Game.Editor.VisualQA
{
    /// <summary>In-memory ablations of cab plastic. Detail-off removes all detail modulation, not just normals. No asset writes.</summary>
    public static class CabSurfaceAudit
    {
        public static void Run()
        {
            int exit = 1;
            try
            {
                string output = EditorTools.Arg("-cabOutput", Path.Combine(EditorTools.RepoRoot, "artifacts/cab-r1/surface-audit"));
                foreach (string mode in new[] { "baseline", "roughness-flat", "detail-off", "wear-flat", "ao-flat", "tint-flat" })
                {
                    var copies = new List<Mesh>();
                    void Prepare(Scene scene, OpenSceneMode openMode)
                    {
                        if (mode == "baseline") return;
                        var rig = UnityEngine.Object.FindFirstObjectByType<TruckVisualRig>();
                        int selected = 0;
                        foreach (var renderer in rig.interiorLods[0].renderers)
                        {
                            var filter = renderer.GetComponent<MeshFilter>();
                            if (filter == null) continue;
                            var source = filter.sharedMesh;
                            var indices = new HashSet<int>();
                            for (int sub = 0; sub < source.subMeshCount; ++sub)
                                if (renderer.sharedMaterials[sub].name.StartsWith("MI_Cab_Plastic", StringComparison.Ordinal))
                                    indices.UnionWith(source.GetTriangles(sub));
                            if (indices.Count == 0) continue;
                            Mesh mesh = UnityEngine.Object.Instantiate(source); copies.Add(mesh);
                            var colors = mesh.colors;
                            var ao = mesh.uv2;
                            var data = mesh.uv3;
                            Color mean = Color.clear;
                            foreach (int i in indices) mean += colors[i];
                            mean /= indices.Count;
                            foreach (int i in indices)
                            {
                                if (mode == "roughness-flat") colors[i].a = .8f;
                                if (mode == "detail-off") data[i].y = 0f;
                                if (mode == "wear-flat") data[i].x = 0f;
                                if (mode == "ao-flat") ao[i] = new Vector2(.999f, .999f);
                                if (mode == "tint-flat") { colors[i].r = mean.r; colors[i].g = mean.g; colors[i].b = mean.b; }
                            }
                            mesh.colors = colors; mesh.uv2 = ao; mesh.uv3 = data;
                            filter.sharedMesh = mesh; selected += indices.Count;
                        }
                        if (selected == 0) throw new InvalidOperationException("No plastic vertices selected for " + mode);
                        Debug.Log("CAB_SURFACE_AUDIT " + mode + " plasticVertices=" + selected);
                    }
                    EditorSceneManager.sceneOpened += Prepare;
                    try
                    {
                        int rendered = VisualQaRunner.Render("WorldC", 1920, 1080, "Low", Path.Combine(output, mode), "overcast", "cab-grain,cab-dash");
                        if (rendered != 2) throw new InvalidOperationException("Expected two surface audit views, got " + rendered);
                    }
                    finally
                    {
                        EditorSceneManager.sceneOpened -= Prepare;
                        foreach (var mesh in copies) UnityEngine.Object.DestroyImmediate(mesh);
                    }
                }
                exit = 0;
            }
            catch (Exception exception) { Debug.LogException(exception); }
            Debug.Log("CAB_SURFACE_AUDIT_RESULT: " + (exit == 0 ? "OK" : "FAILED"));
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }
    }
}
