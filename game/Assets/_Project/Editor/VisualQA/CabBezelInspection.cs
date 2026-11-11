using System;
using System.IO;
using System.Linq;
using Game.Editor.Build;
using Game.Rendering;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Game.Editor.VisualQA
{
    /// <summary>Uncropped, matched driver-eye rim ablation. Temporary cameras and mesh references are never saved.</summary>
    public static class CabBezelInspection
    {
        public static void Run()
        {
            int exit = 1;
            try
            {
                string tier = EditorTools.Arg("-cabTier", "High"), light = EditorTools.Arg("-cabLighting", "clear");
                string output = EditorTools.Arg("-cabOutput", Path.Combine(EditorTools.RepoRoot, "artifacts/cab-r1/bezel-inspection"));
                foreach (bool before in new[] { true, false })
                {
                    void Prepare(Scene scene, OpenSceneMode mode)
                    {
                        var mirrors = UnityEngine.Object.FindObjectsByType<RenderTextureMirror>(FindObjectsSortMode.None).ToDictionary(m => m.phase);
                        var rig = mirrors[0].GetComponentInParent<TruckVisualRig>();
                        if (before)
                            foreach (var lod in rig.exteriorLods)
                                foreach (var renderer in lod.renderers.Where(r => r != null && r.name.StartsWith("CAB_Body", StringComparison.Ordinal)))
                                {
                                    var filter = renderer.GetComponent<MeshFilter>();
                                    string path = AssetDatabase.GetAssetPath(filter.sharedMesh);
                                    const string suffix = "_MirrorBezel.asset";
                                    if (!path.EndsWith(suffix, StringComparison.Ordinal)) throw new InvalidOperationException("Expected generated rim mesh: " + path);
                                    string original = path.Substring(0, path.Length - suffix.Length) + ".asset";
                                    filter.sharedMesh = AssetDatabase.LoadAssetAtPath<Mesh>(original);
                                    if (filter.sharedMesh == null) throw new FileNotFoundException(original);
                                }
                        var eye = rig.GetComponentsInChildren<Transform>(true).Single(t => t.name == "DriverEyePoint");
                        foreach (var item in new[] { ("left", 0, 2), ("right", 1, 3) })
                        {
                            Bounds bounds = mirrors[item.Item2].glass.bounds;
                            bounds.Encapsulate(mirrors[item.Item3].glass.bounds); bounds.Expand(.08f);
                            var go = new GameObject("cab-bezel-inspection-" + item.Item1);
                            var camera = go.AddComponent<Camera>();
                            camera.transform.SetPositionAndRotation(eye.position, Quaternion.LookRotation(bounds.center - eye.position, rig.transform.up));
                            camera.fieldOfView = 2f * Mathf.Atan(bounds.size.y / (1.7f * Vector3.Distance(bounds.center, eye.position))) * Mathf.Rad2Deg;
                            camera.nearClipPlane = .03f; camera.farClipPlane = 1400f; camera.enabled = false;
                            var control = go.AddComponent<ControlCamera>(); control.id = go.name;
                        }
                    }
                    EditorSceneManager.sceneOpened += Prepare;
                    try
                    {
                        VisualQaRunner.Render(tier == "High" ? "WorldC_High" : "WorldC", 1920, 1080, tier,
                            Path.Combine(output, before ? "before" : "after"), light,
                            "cab-bezel-inspection-left,cab-bezel-inspection-right");
                    }
                    finally { EditorSceneManager.sceneOpened -= Prepare; }
                }
                exit = 0;
            }
            catch (Exception exception) { Debug.LogException(exception); }
            Debug.Log("CAB_BEZEL_INSPECTION_RESULT: " + (exit == 0 ? "OK" : "FAILED"));
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }
    }
}
