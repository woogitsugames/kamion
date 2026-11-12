using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Game.Platform;
using Game.Rendering;
using Game.World;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

namespace Game.Editor.VisualQA
{
    // Optional life-domain QA only. No runtime path or change to the common QA logger.
    // The consumer must match every legacy stats row before using the integer counts.
    [InitializeOnLoad]
    public static class LifeExactStats
    {
        [Serializable] public class Row
        {
            public string id;
            public long worldTriangles, instanceTriangles;
            public int worldDraws, objects, instanceDraws, instances, cells, hlodCells;
            public float aspect, fov;
        }
        [Serializable] public class Payload { public bool present; public int vertices; public float heightError, axleError; }
        [Serializable] public class Model { public string name; public long[] triangles; public Payload[] payloads; }
        [Serializable] public class PaintMaterial
        {
            public string name, shader, baseMap;
            public bool carPaint, carPlate;
            public int passes;
            public Vector4 flake, tile;
        }
        [Serializable] public class Dump
        {
            public string schema = "kamion/life-exact-cpu/1";
            public string note = "CPU estimates before SRP batching; not GPU counters. Validate against legacy stats.";
            public Row[] rows;
            public Model[] models;
            public PaintMaterial[] materials;
            public string[] errors;
        }
        static readonly string Output;
        static readonly Dictionary<string, Camera> Cameras = new Dictionary<string, Camera>();
        static readonly Dictionary<string, WorldInstances.Stats> Instances = new Dictionary<string, WorldInstances.Stats>();
        static readonly Dictionary<string, Row> Rows = new Dictionary<string, Row>();
        static readonly List<string> Errors = new List<string>();
        static Model[] Models;
        static PaintMaterial[] Materials;
        static LifeExactStats()
        {
            var args = Environment.GetCommandLineArgs();
            for (int i = 0; i + 1 < args.Length; i++) if (args[i] == "-qaLifeExact") Output = args[i + 1];
            if (string.IsNullOrEmpty(Output)) return;
            RenderPipelineManager.endCameraRendering += EndCamera;
            Application.logMessageReceived += Log;
        }
        static void EndCamera(ScriptableRenderContext context, Camera camera)
        {
            var marker = camera.GetComponent<ControlCamera>();
            if (marker == null || string.IsNullOrEmpty(marker.id)) return;
            Cameras[marker.id] = camera;
            Instances[marker.id] = WorldInstances.Last;
        }
        static void Log(string message, string stack, LogType type)
        {
            const string prefix = "[VISUALQA] ";
            if (!message.StartsWith(prefix, StringComparison.Ordinal)) return;
            int arrow = message.IndexOf(" → ", StringComparison.Ordinal);
            if (arrow < prefix.Length) return;
            string id = message.Substring(prefix.Length, arrow - prefix.Length);
            try
            {
                if (!Cameras.TryGetValue(id, out var camera) || camera == null || !Instances.TryGetValue(id, out var wi))
                    throw new InvalidOperationException("No rendered control-camera snapshot for " + id);
                var row = World(camera);
                row.id = id; row.instanceTriangles = wi.Triangles; row.instanceDraws = wi.Draws;
                row.instances = wi.Instances; row.cells = wi.VisibleCells; row.hlodCells = wi.HlodCells;
                row.aspect = camera.aspect; row.fov = camera.fieldOfView;
                Rows[id] = row;
                if (Models == null) ReadModels();
            }
            catch (Exception ex) { Errors.Add(id + ": " + ex.Message); }
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(Output)));
                var dump = new Dump { rows = Rows.Values.OrderBy(r => r.id, StringComparer.Ordinal).ToArray(), models = Models, materials = Materials, errors = Errors.ToArray() };
                File.WriteAllText(Output, JsonUtility.ToJson(dump, true));
            }
            catch (Exception ex) { Debug.LogError("[LIFE_EXACT] " + ex.Message); }
        }
        static void ReadModels()
        {
            var instances = Object.FindObjectsByType<WorldInstances>(FindObjectsSortMode.None);
            if (instances.Length != 1) throw new InvalidOperationException("Expected exactly one WorldInstances component");
            var field = typeof(WorldInstances).GetField("set", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
            var set = field?.GetValue(instances[0]) as WorldInstanceSet;
            if (set == null) throw new InvalidOperationException("WorldInstanceSet unavailable");
            Models = set.prototypes.Where(p => p.name.StartsWith("tractor_", StringComparison.Ordinal) || p.name.StartsWith("trailer_", StringComparison.Ordinal))
                .Select(p => new Model { name = p.name, triangles = p.lods.Select(m => Enumerable.Range(0, m.subMeshCount).Sum(s => (long)m.GetIndexCount(s) / 3)).ToArray(),
                    payloads = p.name.StartsWith("tractor_", StringComparison.Ordinal) ? Enumerable.Range(0, p.lods.Length).Select(l => ReadPayload(set, p, l)).ToArray() : Array.Empty<Payload>() }).ToArray();
            Materials = set.materials.Where(m => m != null && (m.name.Contains("car_paint_") || m.name.Contains("tractor_paint_") || m.name.Contains("trailer_curtain_") || m.name.Contains("car_plate")))
                .Distinct().OrderBy(m => m.name, StringComparer.Ordinal).Select(m => new PaintMaterial {
                    name = m.name, shader = m.shader.name, carPaint = m.IsKeywordEnabled("_CARPAINT"), carPlate = m.IsKeywordEnabled("_CARPLATE"), passes = m.passCount,
                    flake = m.HasProperty("_CarFlake") ? m.GetVector("_CarFlake") : Vector4.zero,
                    tile = m.HasProperty("_Tile") ? m.GetVector("_Tile") : Vector4.zero,
                    baseMap = m.HasProperty("_BaseMap") && m.GetTexture("_BaseMap") != null ? m.GetTexture("_BaseMap").name : ""
                }).ToArray();
        }
        static Payload ReadPayload(WorldInstanceSet set, WorldInstanceSet.Prototype prototype, int lod)
        {
            var mesh = prototype.lods[lod];
            var result = new Payload { present = mesh.HasVertexAttribute(VertexAttribute.TexCoord1) };
            if (!result.present) return result;
            if (mesh.GetVertexAttributeStream(VertexAttribute.TexCoord1) != 0 || mesh.GetVertexAttributeFormat(VertexAttribute.TexCoord1) != VertexAttributeFormat.Float16)
                throw new InvalidOperationException("Unexpected native cab UV1 format");
            using (var snapshot = MeshUtility.AcquireReadOnlyMeshData(mesh))
            {
                var data = snapshot[0];
                var selected = new HashSet<int>();
                for (int sub = 0; sub < mesh.subMeshCount; sub++)
                {
                    if (!set.materials[prototype.materialStart[lod] + sub].name.Contains("tractor_paint_")) continue;
                    var range = mesh.GetSubMesh(sub);
                    if (mesh.indexFormat == IndexFormat.UInt16)
                    {
                        var indices = data.GetIndexData<ushort>();
                        for (int i = 0; i < range.indexCount; i++) selected.Add(indices[range.indexStart + i] + range.baseVertex);
                    }
                    else
                    {
                        var indices = data.GetIndexData<int>();
                        for (int i = 0; i < range.indexCount; i++) selected.Add(indices[range.indexStart + i] + range.baseVertex);
                    }
                }
                byte[] bytes = data.GetVertexData<byte>(0).ToArray();
                int stride = mesh.GetVertexBufferStride(0), pos = mesh.GetVertexAttributeOffset(VertexAttribute.Position), uv = mesh.GetVertexAttributeOffset(VertexAttribute.TexCoord1);
                foreach (int vertex in selected)
                {
                    int start = vertex * stride;
                    float height = BitConverter.ToSingle(bytes, start + pos + 4), longitudinal = BitConverter.ToSingle(bytes, start + pos + 8);
                    float h = Mathf.HalfToFloat(BitConverter.ToUInt16(bytes, start + uv)), a = Mathf.HalfToFloat(BitConverter.ToUInt16(bytes, start + uv + 2));
                    result.heightError = Mathf.Max(result.heightError, Mathf.Abs(h - (height - 1.05f)));
                    result.axleError = Mathf.Max(result.axleError, Mathf.Abs(a - (longitudinal + .55f) / 3.70f));
                }
                result.vertices = selected.Count;
            }
            return result;
        }
        static Row World(Camera camera)
        {
            // Keep the selection policy equal to SceneStats.Estimate. The consumer
            // cross-checks objects/draws and both rounded triangle components.
            var planes = GeometryUtility.CalculateFrustumPlanes(camera);
            var selected = new HashSet<Renderer>();
            var grouped = new HashSet<Renderer>();
            float tanHalf = Mathf.Tan(camera.fieldOfView * .5f * Mathf.Deg2Rad);
            foreach (var group in Object.FindObjectsByType<LODGroup>(FindObjectsSortMode.None))
            {
                var lods = group.GetLODs();
                foreach (var lod in lods) foreach (var renderer in lod.renderers) if (renderer != null) grouped.Add(renderer);
                float distance = Vector3.Distance(camera.transform.position, group.transform.TransformPoint(group.localReferencePoint));
                float height = group.size / (2f * Mathf.Max(distance, .01f) * tanHalf) * QualitySettings.lodBias;
                for (int i = 0; i < lods.Length; i++)
                {
                    if (height < lods[i].screenRelativeTransitionHeight && i < lods.Length - 1) continue;
                    if (height < lods[i].screenRelativeTransitionHeight) break;
                    foreach (var renderer in lods[i].renderers) if (renderer != null) selected.Add(renderer);
                    break;
                }
            }
            var result = new Row();
            foreach (var renderer in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            {
                if (!renderer.enabled || !renderer.gameObject.activeInHierarchy || (grouped.Contains(renderer) && !selected.Contains(renderer))) continue;
                if ((camera.cullingMask & (1 << renderer.gameObject.layer)) == 0) continue;
                var filter = renderer.GetComponent<MeshFilter>();
                if (filter == null || filter.sharedMesh == null) continue;
                if (Mathf.Sqrt(renderer.bounds.SqrDistance(camera.transform.position)) > camera.farClipPlane) continue;
                if (!GeometryUtility.TestPlanesAABB(planes, renderer.bounds)) continue;
                var mesh = filter.sharedMesh;
                result.objects++; result.worldDraws += mesh.subMeshCount;
                for (int s = 0; s < mesh.subMeshCount; s++) result.worldTriangles += (long)mesh.GetIndexCount(s) / 3;
            }
            return result;
        }
    }
}
