// Diagnostic editor entry point, copied to an ignored _Generated/Editor folder by exact-stats.ps1.
// Extends the existing SceneStats definition with unrounded totals; this is not a GPU measurement.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Game.Editor.VisualQA;
using Game.Rendering;
using Game.World;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.FurnitureQA
{
    public static class FurnitureExactStats
    {
        struct Part { public Bounds bounds; public int draws; public long triangles; }
        sealed class Snapshot
        {
            public Camera camera;
            public Matrix4x4 view;
            public float fov, far;
            public List<Part> parts = new List<Part>();
            public WorldInstances.Stats instances;
        }
        [Serializable] public sealed class Row
        {
            public string camera;
            public int mesh_objects, mesh_draws, instance_draws, instances;
            public long mesh_triangles, instance_triangles;
        }
        [Serializable] sealed class Packet
        {
            public string scope = "SceneStats CPU estimate, unrounded; no GPU counters";
            public string phase, tier, lighting;
            public int rendered;
            public Row[] cameras;
        }
        static readonly Dictionary<string, Snapshot> snapshots = new Dictionary<string, Snapshot>();
        static string Arg(string key, string fallback)
        {
            var args = Environment.GetCommandLineArgs();
            int at = Array.IndexOf(args, key);
            return at >= 0 && at + 1 < args.Length ? args[at + 1] : fallback;
        }
        static void Observe(ScriptableRenderContext context, Camera cam)
        {
            var control = cam.GetComponent<ControlCamera>();
            // Exclude the runner's 256x128 warm-up, UI cameras and reflection/mirror cameras.
            if (control == null || cam.targetTexture == null || cam.targetTexture.width <= 256) return;
            var snapshot = new Snapshot { camera = cam, view = cam.worldToCameraMatrix,
                fov = cam.fieldOfView, far = cam.farClipPlane, instances = WorldInstances.Last };
            var selected = new HashSet<Renderer>();
            var inLodGroup = new HashSet<Renderer>();
            float tanHalf = Mathf.Tan(cam.fieldOfView * .5f * Mathf.Deg2Rad);
            foreach (var group in UnityEngine.Object.FindObjectsByType<LODGroup>(FindObjectsSortMode.None))
            {
                var lods = group.GetLODs();
                foreach (var lod in lods) foreach (var renderer in lod.renderers)
                    if (renderer != null) inLodGroup.Add(renderer);
                var centre = group.transform.TransformPoint(group.localReferencePoint);
                float distance = Vector3.Distance(cam.transform.position, centre);
                float height = group.size / (2f * Mathf.Max(distance, .01f) * tanHalf) * QualitySettings.lodBias;
                for (int index = 0; index < lods.Length; index++)
                {
                    if (height < lods[index].screenRelativeTransitionHeight && index < lods.Length - 1) continue;
                    if (height < lods[index].screenRelativeTransitionHeight) break;
                    foreach (var renderer in lods[index].renderers) if (renderer != null) selected.Add(renderer);
                    break;
                }
            }
            foreach (var renderer in UnityEngine.Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            {
                if (!renderer.enabled || !renderer.gameObject.activeInHierarchy) continue;
                if (inLodGroup.Contains(renderer) && !selected.Contains(renderer)) continue;
                if ((cam.cullingMask & (1 << renderer.gameObject.layer)) == 0) continue;
                var filter = renderer.GetComponent<MeshFilter>();
                if (filter == null || filter.sharedMesh == null) continue;
                var bounds = renderer.bounds;
                if (Mathf.Sqrt(bounds.SqrDistance(cam.transform.position)) > cam.farClipPlane) continue;
                var mesh = filter.sharedMesh;
                long triangles = 0;
                for (int submesh = 0; submesh < mesh.subMeshCount; submesh++) triangles += (long)mesh.GetIndexCount(submesh) / 3;
                snapshot.parts.Add(new Part { bounds = bounds, draws = mesh.subMeshCount, triangles = triangles });
            }
            snapshots[control.id] = snapshot;
        }
        public static void Run()
        {
            int exit = 1;
            try
            {
                snapshots.Clear();
                string tier = Arg("-qaTier", "Low"), lighting = Arg("-qaLighting", "overcast");
                string output = Arg("-qaOutput", null);
                if (string.IsNullOrEmpty(output)) throw new ArgumentException("-qaOutput is required");
                RenderPipelineManager.endCameraRendering += Observe;
                int count = VisualQaRunner.Render(Arg("-qaScene", "WorldC"), 2340, 1080, tier, output, lighting);
                if (count == 0 || snapshots.Count != count) throw new InvalidOperationException("Missing camera snapshots");
                var rows = new List<Row>();
                foreach (var pair in snapshots.OrderBy(pair => pair.Key, StringComparer.Ordinal))
                {
                    var snapshot = pair.Value;
                    if (snapshot.camera == null || Mathf.Abs(snapshot.fov - snapshot.camera.fieldOfView) > .00001f ||
                        Mathf.Abs(snapshot.far - snapshot.camera.farClipPlane) > .00001f)
                        throw new InvalidOperationException("Camera projection settings changed: " + pair.Key);
                    // SceneStats runs after RenderToPixels restores the camera's previous target.
                    // Use that restored projection with the frame's captured view and renderer bounds.
                    var planes = GeometryUtility.CalculateFrustumPlanes(snapshot.camera.projectionMatrix * snapshot.view);
                    var row = new Row { camera = pair.Key, instance_draws = snapshot.instances.Draws,
                        instances = snapshot.instances.Instances, instance_triangles = snapshot.instances.Triangles };
                    foreach (var part in snapshot.parts)
                        if (GeometryUtility.TestPlanesAABB(planes, part.bounds))
                        { row.mesh_objects++; row.mesh_draws += part.draws; row.mesh_triangles += part.triangles; }
                    rows.Add(row);
                }
                var packet = new Packet { phase = Arg("-furniturePhase", "after4"), tier = tier,
                    lighting = lighting, rendered = count, cameras = rows.ToArray() };
                File.WriteAllText(Path.Combine(output, "exact-stats.json"), JsonUtility.ToJson(packet, true));
                Debug.Log("FURNITURE_EXACT_STATS_OK cameras=" + count);
                exit = 0;
            }
            catch (Exception error) { Debug.LogException(error); }
            finally { RenderPipelineManager.endCameraRendering -= Observe; snapshots.Clear(); }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }
    }
}
