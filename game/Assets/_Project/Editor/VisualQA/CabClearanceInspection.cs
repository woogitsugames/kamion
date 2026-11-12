using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
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
    /// <summary>Temporary section views of imported geometry, not a solid-intersection test or a game camera.</summary>
    public static class CabClearanceInspection
    {
        static readonly string[] Globals = { "_CabInspectOrigin", "_CabInspectRight", "_CabInspectUp", "_CabInspectForward", "_CabInspectMin", "_CabInspectMax" };
        public static void Run()
        {
            int exit = 1;
            var previous = Globals.Select(Shader.GetGlobalVector).ToArray();
            try
            {
                string output = EditorTools.Arg("-cabOutput", Path.Combine(EditorTools.RepoRoot, "artifacts/cab-r2/clearance-inspection"));
                foreach (string pose in new[] { "side", "top" })
                {
                    var flags = new Dictionary<Renderer, bool>();
                    var saved = new Dictionary<Renderer, Material[]>();
                    var palette = new List<Material>();
                    TruckVisualRig rig = null; Transform h = null; bool patched = false; Exception failure = null;
                    void Prepare(Scene scene, OpenSceneMode mode)
                    {
                        rig = UnityEngine.Object.FindFirstObjectByType<TruckVisualRig>();
                        h = rig.GetComponentsInChildren<Transform>(true).Single(t => t.name == "DriverHPoint");
                        var frame = h.parent;
                        var go = new GameObject("cab-clearance-" + pose); go.transform.SetParent(rig.transform, false);
                        var camera = go.AddComponent<Camera>(); camera.enabled = false;
                        Vector3 position = pose == "side" ? h.position - frame.right + frame.up * .30f + frame.forward * .15f : h.position + frame.up * 1.5f + frame.forward * .05f;
                        Vector3 target = h.position + frame.forward * .10f;
                        camera.transform.SetPositionAndRotation(position, Quaternion.LookRotation(target - position, pose == "top" ? frame.forward : frame.up));
                        camera.fieldOfView = 58; camera.nearClipPlane = .03f; camera.farClipPlane = 3;
                        go.AddComponent<ControlCamera>().id = go.name;
                    }
                    void Before(ScriptableRenderContext context, Camera camera)
                    {
                        var control = camera.GetComponent<ControlCamera>();
                        if (patched || control == null || control.id != "cab-clearance-" + pose) return;
                        patched = true;
                        try
                        {
                            var shader = Shader.Find("Hidden/Kamion/Cab Clearance Inspection");
                            if (shader == null || !shader.isSupported) throw new InvalidOperationException("Missing clearance inspection shader");
                            Material Part(Color colour) { var m = new Material(shader); m.SetColor("_Color", colour); palette.Add(m); return m; }
                            var wheel = Part(new Color(.8f, .12f, .07f)); var leather = Part(new Color(.8f, .55f, .12f));
                            var fabric = Part(new Color(.12f, .35f, .7f)); var plastic = Part(new Color(.35f, .38f, .4f));
                            var selected = new HashSet<Renderer>(rig.interiorLods[0].renderers.Where(r => r.name.StartsWith("CAB_Interior", StringComparison.Ordinal) || r.name.StartsWith("STEERING_WHEEL", StringComparison.Ordinal)));
                            foreach (var renderer in rig.GetComponentsInChildren<Renderer>(true))
                            {
                                flags.Add(renderer, renderer.forceRenderingOff);
                                renderer.forceRenderingOff = !selected.Contains(renderer);
                                if (!selected.Contains(renderer)) continue;
                                var original = renderer.sharedMaterials; saved.Add(renderer, original);
                                renderer.sharedMaterials = original.Select(m => renderer.name.StartsWith("STEERING_WHEEL", StringComparison.Ordinal) ? wheel :
                                    m.name.StartsWith("MI_Cab_Leather", StringComparison.Ordinal) ? leather : m.name.StartsWith("MI_Cab_Fabric", StringComparison.Ordinal) ? fabric : plastic).ToArray();
                            }
                            var frame = h.parent;
                            Shader.SetGlobalVector(Globals[0], h.position); Shader.SetGlobalVector(Globals[1], frame.right);
                            Shader.SetGlobalVector(Globals[2], frame.up); Shader.SetGlobalVector(Globals[3], frame.forward);
                            Shader.SetGlobalVector(Globals[4], new Vector4(pose == "side" ? -.30f : -.80f, -.55f, -.60f, 0));
                            Shader.SetGlobalVector(Globals[5], new Vector4(.80f, .50f, .75f, 0));
                            camera.cullingMask = 1 << rig.gameObject.layer; camera.clearFlags = CameraClearFlags.SolidColor;
                            camera.backgroundColor = new Color(.55f, .58f, .61f);
                            Debug.Log($"CAB_CLEARANCE {pose}: H={h.position}, camera={camera.transform.position}; section, unchanged geometry, no solid intersection test");
                        }
                        catch (Exception exception) { failure = exception; }
                    }
                    EditorSceneManager.sceneOpened += Prepare; RenderPipelineManager.beginCameraRendering += Before;
                    try
                    {
                        int count = VisualQaRunner.Render("WorldC_High", 1920, 1080, "High", output, "clear", "cab-clearance-" + pose);
                        if (failure != null) throw failure;
                        if (count != 1 || !patched) throw new InvalidOperationException("Missing clearance section view");
                    }
                    finally
                    {
                        EditorSceneManager.sceneOpened -= Prepare; RenderPipelineManager.beginCameraRendering -= Before;
                        foreach (var pair in saved) if (pair.Key != null) pair.Key.sharedMaterials = pair.Value;
                        foreach (var pair in flags) if (pair.Key != null) pair.Key.forceRenderingOff = pair.Value;
                        foreach (var material in palette) UnityEngine.Object.DestroyImmediate(material);
                    }
                }
                exit = 0;
            }
            catch (Exception exception) { Debug.LogException(exception); }
            finally { for (int i = 0; i < Globals.Length; i++) Shader.SetGlobalVector(Globals[i], previous[i]); }
            Debug.Log("CAB_CLEARANCE_RESULT: " + (exit == 0 ? "OK" : "FAILED"));
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }
    }
}
