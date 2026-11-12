using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Game.Rendering;
using Game.World;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;
using Object = UnityEngine.Object;

namespace Game.Editor.VisualQA
{
    // Artifact-only, opt-in diagnostic. It substitutes the event dispatch only:
    // invokes the actual compiled OnBeginCamera once, with empty retained buffers.
    // No reimplementation of LOD selection; canonical captures do not enable it.
    [InitializeOnLoad]
    public static class Life5PropLodProbe
    {
        [Serializable] public class Target { public string prototype; public Vector3 localPosition; }
        [Serializable] public class Targets { public Target[] targets; }
        [Serializable] public class Row
        {
            public string camera, prototype;
            public int nativeIndex, prototypeCount;
            public int[] observedLods;
            public long[] meshTriangles;
            public float distance, distanceScale, qualityLodBias;
            public Vector3 localPosition, worldPosition, cameraPosition;
            public int instanceDraws, instanceTriangles, instances;
        }
        [Serializable] public class Dump
        {
            public string schema = "kamion/life5-native-lod-buffer/1";
            public string note = "Actual compiled WorldInstances.OnBeginCamera dispatch, selected-prototype retained batches cleared before each diagnostic camera. CPU submission evidence, not GPU/A16 timing. Compare diagnostic legacy counts and pose with canonical capture.";
            public Row[] rows;
            public string[] errors;
        }
        static readonly string Output;
        static readonly Target[] Selected;
        static readonly List<Row> Rows = new List<Row>();
        static readonly List<string> Errors = new List<string>();
        static readonly BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
        static WorldInstances Current;
        static string LastCamera;
        static Life5PropLodProbe()
        {
            var args = Environment.GetCommandLineArgs();
            string targets = null;
            for (int i = 0; i + 1 < args.Length; i++)
            {
                if (args[i] == "-qaLifeYardLod") Output = args[i + 1];
                if (args[i] == "-qaLifeYardTargets") targets = args[i + 1];
            }
            if (string.IsNullOrEmpty(Output)) return;
            if (string.IsNullOrEmpty(targets)) throw new ArgumentException("Missing yard targets");
            Selected = JsonUtility.FromJson<Targets>(File.ReadAllText(targets)).targets;
            EditorSceneManager.sceneOpened += Opened;
            RenderPipelineManager.beginCameraRendering += Begin;
            RenderPipelineManager.endCameraRendering += End;
            Application.logMessageReceived += Finished;
            EditorApplication.quitting += Cleanup;
        }
        static void Finished(string message, string stack, LogType type)
        {
            if (message.StartsWith("VISUALQA_RESULT: OK", StringComparison.Ordinal)) Cleanup();
        }
        static void Cleanup()
        {
            RenderPipelineManager.beginCameraRendering -= Begin;
            RenderPipelineManager.endCameraRendering -= End;
            Application.logMessageReceived -= Finished;
            if (Current == null) return;
            // Restore the ordinary lifecycle as soon as capture ends. Native
            // resources remain alive until Unity invokes the normal OnDisable;
            // do not DestroyImmediate materials in an editor-quitting callback.
            Current.enabled = true;
        }
        static void Opened(Scene scene, OpenSceneMode mode)
        {
            foreach (var wi in Object.FindObjectsByType<WorldInstances>(FindObjectsSortMode.None))
                wi.enabled = false; // unsubscribe stock event; never save this diagnostic scene
        }
        static T Field<T>(WorldInstances wi, string name) =>
            (T)typeof(WorldInstances).GetField(name, Private).GetValue(wi);
        static void Begin(ScriptableRenderContext context, Camera camera)
        {
            var marker = camera.GetComponent<ControlCamera>();
            if (marker == null || !marker.id.StartsWith("yard_", StringComparison.Ordinal)) return;
            LastCamera = marker.id;
            try
            {
                var all = Object.FindObjectsByType<WorldInstances>(FindObjectsSortMode.None);
                if (all.Length != 1 || all[0].enabled) throw new InvalidOperationException("Expected one unsubscribed WorldInstances");
                Current = all[0];
                var buffers = Field<Matrix4x4[][]>(Current, "m_Batch");
                if (buffers != null)
                {
                    var offsets = Field<int[]>(Current, "m_BatchOffset");
                    foreach (var target in Selected)
                    {
                        int pi = Array.FindIndex(Current.set.prototypes, p => p.name == target.prototype);
                        if (pi < 0) throw new InvalidOperationException("Missing selected prototype " + target.prototype);
                        for (int l = 0; l < Current.set.prototypes[pi].lods.Length; l++)
                        {
                            var buffer = buffers[offsets[pi] + l];
                            Array.Clear(buffer, 0, buffer.Length);
                        }
                    }
                }
                typeof(WorldInstances).GetMethod("OnBeginCamera", Private).Invoke(Current, new object[] { context, camera });
                if (Field<Camera>(Current, "m_Camera") != camera) throw new InvalidOperationException("Native renderer did not process diagnostic camera");
            }
            catch (Exception ex) { Errors.Add(marker.id + ": " + ex); }
        }
        static long Triangles(Mesh mesh)
        {
            long n = 0;
            for (int s = 0; s < mesh.subMeshCount; s++) n += (long)mesh.GetIndexCount(s) / 3;
            return n;
        }
        static void End(ScriptableRenderContext context, Camera camera)
        {
            var marker = camera.GetComponent<ControlCamera>();
            if (marker == null || marker.id != LastCamera || Current == null) return;
            try
            {
                var set = Current.set;
                var buffers = Field<Matrix4x4[][]>(Current, "m_Batch");
                var offsets = Field<int[]>(Current, "m_BatchOffset");
                var matrices = Field<Matrix4x4[]>(Current, "m_World");
                foreach (var target in Selected)
                {
                    if (!marker.id.StartsWith("yard_" + target.prototype + "_", StringComparison.Ordinal)) continue;
                    int pi = Array.FindIndex(set.prototypes, p => p.name == target.prototype);
                    if (pi < 0) throw new InvalidOperationException("Missing prototype " + target.prototype);
                    var proto = set.prototypes[pi];
                    if (proto.count >= 1023) throw new InvalidOperationException("Diagnostic cannot prove all flushed batches");
                    var matches = new List<int>();
                    foreach (var run in set.runs)
                        if (run.prototype == pi)
                            for (int i = run.start; i < run.start + run.count; i++)
                                if (Vector3.Distance(set.LocalPosition(i), target.localPosition) < 0.02f) matches.Add(i);
                    if (matches.Count != 1) throw new InvalidOperationException("Target identity not unique: " + target.prototype);
                    int index = matches[0];
                    var matrix = matrices[index];
                    var position = new Vector3(matrix.m03, matrix.m13, matrix.m23);
                    var lods = new List<int>();
                    for (int l = 0; l < proto.lods.Length; l++)
                        if (buffers[offsets[pi] + l].Any(m => MatrixMatches(m, matrix))) lods.Add(l);
                    if (lods.Count != 1) throw new InvalidOperationException("Expected one native submitted LOD for " + marker.id + ": " + string.Join(",", lods));
                    Rows.RemoveAll(r => r.camera == marker.id && r.prototype == target.prototype);
                    Rows.Add(new Row { camera = marker.id, prototype = target.prototype, nativeIndex = index,
                        prototypeCount = proto.count, observedLods = lods.ToArray(), meshTriangles = proto.lods.Select(Triangles).ToArray(),
                        localPosition = set.LocalPosition(index), worldPosition = position, cameraPosition = camera.transform.position,
                        distance = Vector3.Distance(position, camera.transform.position), distanceScale = Current.distanceScale,
                        qualityLodBias = QualitySettings.lodBias, instanceDraws = WorldInstances.Last.Draws,
                        instanceTriangles = WorldInstances.Last.Triangles, instances = WorldInstances.Last.Instances });
                }
            }
            catch (Exception ex) { Errors.Add(marker.id + ": " + ex); }
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(Output)));
            File.WriteAllText(Output, JsonUtility.ToJson(new Dump { rows = Rows.OrderBy(r => r.camera).ToArray(), errors = Errors.ToArray() }, true));
        }
        static bool MatrixMatches(Matrix4x4 a, Matrix4x4 b)
        {
            for (int i = 0; i < 16; i++) if (Mathf.Abs(a[i] - b[i]) > 0.00001f) return false;
            return true;
        }
    }
}
