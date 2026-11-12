using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Game.Editor.Build;
using Game.Rendering;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

namespace Game.Editor.VisualQA
{
    /// <summary>Read-only eye-to-glass geometry audit. Opaque triangle rays are not GPU visibility or R46 acceptance.</summary>
    public static class CabMirrorOcclusionAudit
    {
        sealed class Owner
        {
            public string renderer, material, asset;
            public int slot;
        }
        sealed class Counts { public int total, central; }
        static string F(float value) => value.ToString("F6", CultureInfo.InvariantCulture);

        public static void Run()
        {
            int exit = 1;
            bool oldBackfaces = Physics.queriesHitBackfaces;
            int oldQuality = QualitySettings.GetQualityLevel();
            var report = new StringBuilder("# Geometric rays on imported near LODs; not GPU pixels. Alpha decals and transparent glazing excluded. Central region: UV 0.05..0.95.\n");
            report.AppendLine("tier\tmirror\tbackfaces\tsamples\tcentralSamples\tblocked\tcentralBlocked\texteriorLod\tinteriorLod");
            var ownersReport = new StringBuilder("tier\tmirror\tbackfaces\trenderer\tmaterial\tslot\tblocked\tcentralBlocked\tmeshAsset\n");
            var sampleReport = new StringBuilder("tier\tmirror\tbackfaces\trenderer\tmaterial\tslot\ttriangle\tu\tv\tcentral\tworldX\tworldY\tworldZ\tcabX\tcabY\tcabZ\n");
            try
            {
                string output = EditorTools.Arg("-cabOutput", Path.Combine(EditorTools.RepoRoot, "artifacts/cab-r3/occlusion-preflight"));
                Directory.CreateDirectory(output);
                foreach (string tier in new[] { "Low", "High" })
                {
                    QualityTiers.Apply(tier);
                    string sceneName = tier == "High" ? "WorldC_High" : "WorldC";
                    string path = AssetDatabase.FindAssets("t:Scene " + sceneName).Select(AssetDatabase.GUIDToAssetPath)
                        .First(p => Path.GetFileNameWithoutExtension(p) == sceneName);
                    EditorSceneManager.OpenScene(path, OpenSceneMode.Single);
                    var mirrors = UnityEngine.Object.FindObjectsByType<RenderTextureMirror>(FindObjectsSortMode.None).OrderBy(m => m.phase).ToArray();
                    if (mirrors.Length != 6) throw new InvalidOperationException("Expected six player mirrors");
                    var rig = mirrors[0].GetComponentInParent<TruckVisualRig>();
                    rig.Apply();
                    var eye = rig.GetComponentsInChildren<Transform>(true).Single(t => t.name == "DriverEyePoint");
                    var cabLight = rig.GetComponent<CabInteriorLighting>();
                    Transform frame = cabLight != null && cabLight.cab != null ? cabLight.cab : rig.transform;
                    int exteriorLod = TruckVisualRig.ExteriorChainFor(tier, rig.screenSizes)[0].lod;
                    int interiorLod = TruckVisualRig.InteriorLodFor(tier);
                    var selected = new HashSet<Renderer>(rig.exteriorLods[exteriorLod].renderers);
                    selected.UnionWith(rig.interiorLods[interiorLod].renderers);
                    selected.UnionWith(rig.glassLods[0].renderers);
                    var mirrorSurfaces = new HashSet<Renderer>(mirrors.Select(m => m.glass));
                    selected.UnionWith(mirrorSurfaces);
                    // Runtime local-physics scene creation is unavailable in EditMode. Reserve an unused query layer
                    // in an unsaved additive editor scene, and reject any hit outside our collider registry.
                    var usedLayers = new HashSet<int>(UnityEngine.Object.FindObjectsByType<Collider>(FindObjectsInactive.Include,
                        FindObjectsSortMode.None).Select(c => c.gameObject.layer));
                    int isolationLayer = Enumerable.Range(0, 32).Reverse().First(layer => !usedLayers.Contains(layer));
                    int queryMask = 1 << isolationLayer;
                    var temporary = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Additive);
                    var physics = Physics.defaultPhysicsScene;
                    var root = new GameObject("CabMirrorOcclusionTemporary");
                    SceneManager.MoveGameObjectToScene(root, temporary);
                    var meshes = new List<Mesh>();
                    var owners = new Dictionary<int, Owner>();
                    try
                    {
                        foreach (var renderer in selected.Where(r => r != null && r.gameObject.activeInHierarchy && !r.forceRenderingOff))
                        {
                            var filter = renderer.GetComponent<MeshFilter>();
                            if (filter == null || filter.sharedMesh == null) continue;
                            var source = filter.sharedMesh;
                            var materials = renderer.sharedMaterials;
                            var worldVertices = source.vertices.Select(v => renderer.localToWorldMatrix.MultiplyPoint3x4(v)).ToArray();
                            for (int slot = 0; slot < source.subMeshCount; slot++)
                            {
                                var material = slot < materials.Length ? materials[slot] : null;
                                if (material == null || material.shader == null) continue;
                                if (!mirrorSurfaces.Contains(renderer) && (material.renderQueue >= 2500 ||
                                    material.shader.name.IndexOf("Glass", StringComparison.OrdinalIgnoreCase) >= 0 ||
                                    material.IsKeywordEnabled("_KAMION_CAB_DECAL"))) continue;
                                if (source.GetTopology(slot) != MeshTopology.Triangles) continue;
                                var indices = source.GetTriangles(slot);
                                if (indices.Length == 0) continue;
                                if (renderer.localToWorldMatrix.determinant < 0f)
                                    for (int i = 0; i < indices.Length; i += 3) { int swap = indices[i]; indices[i] = indices[i+1]; indices[i+1] = swap; }
                                var mesh = new Mesh { name = "TemporaryOcclusion_" + renderer.name, indexFormat = IndexFormat.UInt32 };
                                mesh.vertices = worldVertices; mesh.SetTriangles(indices, 0); meshes.Add(mesh);
                                var go = new GameObject(renderer.name + "_slot" + slot);
                                SceneManager.MoveGameObjectToScene(go, temporary); go.transform.SetParent(root.transform, false);
                                go.layer = isolationLayer;
                                var collider = go.AddComponent<MeshCollider>(); collider.sharedMesh = mesh;
                                owners.Add(collider.GetInstanceID(), new Owner { renderer = renderer.name, material = material.name,
                                    slot = slot, asset = AssetDatabase.GetAssetPath(source) });
                            }
                        }
                        Physics.SyncTransforms();
                        foreach (var mirror in mirrors.Where(m => m.phase < 4))
                        {
                            var glassMesh = mirror.glass.GetComponent<MeshFilter>().sharedMesh;
                            var vertices = glassMesh.vertices;
                            var uv = glassMesh.uv;
                            var triangles = glassMesh.triangles;
                            if (uv.Length != vertices.Length) throw new InvalidOperationException("Missing mirror UVs");
                            foreach (bool backfaces in new[] { false, true })
                            {
                                Physics.queriesHitBackfaces = backfaces;
                                int samples = 0, centralSamples = 0, blocked = 0, centralBlocked = 0;
                                var counts = new Dictionary<int, Counts>();
                                for (int i = 0; i < 40; i++) for (int j = 0; j < 60; j++)
                                {
                                    var point = new Vector2((i+.5f)/40f, (j+.5f)/60f);
                                    if (!SurfacePoint(vertices, uv, triangles, point, out var local)) continue;
                                    Vector3 target = mirror.glass.localToWorldMatrix.MultiplyPoint3x4(local);
                                    Vector3 ray = target - eye.position;
                                    bool central = point.x >= .05f && point.x <= .95f && point.y >= .05f && point.y <= .95f;
                                    samples++; if (central) centralSamples++;
                                    if (!physics.Raycast(eye.position, ray.normalized, out var hit, ray.magnitude-.002f, queryMask, QueryTriggerInteraction.Ignore)) continue;
                                    if (!owners.TryGetValue(hit.collider.GetInstanceID(), out var owner)) throw new InvalidOperationException("Foreign collider in isolated audit");
                                    blocked++; if (central) centralBlocked++;
                                    if (!counts.TryGetValue(hit.collider.GetInstanceID(), out var count)) counts.Add(hit.collider.GetInstanceID(), count = new Counts());
                                    count.total++; if (central) count.central++;
                                    if (count.total <= 8)
                                    {
                                        Vector3 cab = frame.InverseTransformPoint(hit.point);
                                        sampleReport.AppendLine($"{tier}\t{mirror.name}\t{backfaces}\t{owner.renderer}\t{owner.material}\t{owner.slot}\t{hit.triangleIndex}\t{F(point.x)}\t{F(point.y)}\t{central}\t{F(hit.point.x)}\t{F(hit.point.y)}\t{F(hit.point.z)}\t{F(cab.x)}\t{F(cab.y)}\t{F(cab.z)}");
                                    }
                                }
                                if (samples == 0) throw new InvalidOperationException("No valid UV targets on " + mirror.name);
                                report.AppendLine($"{tier}\t{mirror.name}\t{backfaces}\t{samples}\t{centralSamples}\t{blocked}\t{centralBlocked}\t{exteriorLod}\t{interiorLod}");
                                foreach (var pair in counts.OrderByDescending(p => p.Value.total))
                                {
                                    var owner = owners[pair.Key];
                                    ownersReport.AppendLine($"{tier}\t{mirror.name}\t{backfaces}\t{owner.renderer}\t{owner.material}\t{owner.slot}\t{pair.Value.total}\t{pair.Value.central}\t{owner.asset}");
                                }
                                Debug.Log($"CAB_MIRROR_OCCLUSION {tier} {mirror.name} backfaces={backfaces}: {blocked}/{samples}, central={centralBlocked}/{centralSamples}");
                            }
                        }
                    }
                    finally
                    {
                        UnityEngine.Object.DestroyImmediate(root);
                        foreach (var mesh in meshes) UnityEngine.Object.DestroyImmediate(mesh);
                        EditorSceneManager.CloseScene(temporary, true);
                    }
                }
                File.WriteAllText(Path.Combine(output, "occlusion.tsv"), report.ToString());
                File.WriteAllText(Path.Combine(output, "owners.tsv"), ownersReport.ToString());
                File.WriteAllText(Path.Combine(output, "hit-samples.tsv"), sampleReport.ToString());
                exit = 0;
            }
            catch (Exception exception) { Debug.LogException(exception); }
            finally { Physics.queriesHitBackfaces = oldBackfaces; QualitySettings.SetQualityLevel(oldQuality, true); }
            Debug.Log("CAB_MIRROR_OCCLUSION_RESULT: " + (exit == 0 ? "OK" : "FAILED"));
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        static bool SurfacePoint(Vector3[] vertices, Vector2[] uv, int[] triangles, Vector2 point, out Vector3 local)
        {
            for (int t = 0; t < triangles.Length; t += 3)
            {
                int a = triangles[t], b = triangles[t+1], c = triangles[t+2];
                Vector2 p = uv[b]-uv[a], q = uv[c]-uv[a], r = point-uv[a];
                float determinant = p.x*q.y-p.y*q.x;
                if (Mathf.Abs(determinant) < 1e-10f) continue;
                float x = (r.x*q.y-r.y*q.x)/determinant, y = (p.x*r.y-p.y*r.x)/determinant;
                if (x < -1e-5f || y < -1e-5f || x+y > 1.00001f) continue;
                local = vertices[a] + x*(vertices[b]-vertices[a]) + y*(vertices[c]-vertices[a]); return true;
            }
            local = default; return false;
        }
    }
}
