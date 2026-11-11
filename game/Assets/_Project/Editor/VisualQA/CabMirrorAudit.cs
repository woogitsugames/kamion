using System;
using System.IO;
using System.Linq;
using System.Text;
using Game.Editor.Build;
using Game.Rendering;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Game.Editor.VisualQA
{
    /// <summary>ADR 0104: native mirror pixels and configuration, separate from the minified glass in cab frames.</summary>
    public static class CabMirrorAudit
    {
        public static void Run()
        {
            int exit = 1;
            try
            {
                string tier = EditorTools.Arg("-cabTier", "Low");
                string lighting = EditorTools.Arg("-cabLighting", "overcast");
                string output = EditorTools.Arg("-cabOutput", Path.Combine(EditorTools.RepoRoot, "artifacts/cab-r1/mirrors"));
                Directory.CreateDirectory(output);
                QualityTiers.Apply(tier);
                ShaderUtil.allowAsyncCompilation = false;
                string scene = tier == "High" ? "WorldC_High" : "WorldC";
                string path = AssetDatabase.FindAssets("t:Scene " + scene).Select(AssetDatabase.GUIDToAssetPath)
                    .First(p => Path.GetFileNameWithoutExtension(p) == scene);
                EditorSceneManager.OpenScene(path, OpenSceneMode.Single);
                var env = UnityEngine.Object.FindAnyObjectByType<EnvironmentLighting>();
                if (env == null || !env.SetPreset(lighting)) throw new InvalidOperationException("Missing environment or unknown lighting: " + lighting);
                env.Apply();
                foreach (var rig in UnityEngine.Object.FindObjectsByType<TruckVisualRig>(FindObjectsSortMode.None)) rig.Apply();
                var eye = UnityEngine.Object.FindObjectsByType<ControlCamera>(FindObjectsInactive.Include, FindObjectsSortMode.None)
                    .First(c => c.id == "cab-driver").GetComponent<Camera>();
                foreach (var fill in UnityEngine.Object.FindObjectsByType<CabInteriorLighting>(FindObjectsSortMode.None)) fill.Refresh(eye);
                var report = new StringBuilder();
                var interiorReport = new StringBuilder("mirror\tinteriorPixels\ttotalPixels\n");
                var budgetReport = new StringBuilder("# Editor visibility estimates, not GPU timings. Regular and instanced submissions reported separately.\n");
                report.AppendLine("# Editor mirror audit; cadence is configured, not measured phone Hz. Native RT pixels are unflipped; surface mapping follows the prefab UV/flip contract.");
                report.AppendLine("mirror\tclass\twidth\theight\tfovV\taspect\tnear\tfar\tlodScale\tcap\tintervalDrivingFrames\tintervalStandingFrames");
                var previous = RenderTexture.active;
                var mirrors = UnityEngine.Object.FindObjectsByType<RenderTextureMirror>(FindObjectsSortMode.None).OrderBy(m => m.phase).ToArray();
                if (mirrors.Length != 6) throw new InvalidOperationException("Expected six player mirrors, found " + mirrors.Length);
                try
                {
                    foreach (var mirror in mirrors)
                    {
                        mirror.RenderNow(); mirror.RenderNow();
                        // Capture regular estimates while the actual mirror culling and LOD bias are in force.
                        // SceneStats does not inspect forceRenderingOff, so mask those renderers for the estimate only.
                        string estimate = "UNVERIFIED";
                        void CaptureBudget(UnityEngine.Rendering.ScriptableRenderContext context, Camera camera)
                        {
                            if (camera != mirror.GetComponent<Camera>()) return;
                            var hidden = UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None)
                                .Where(r => r.forceRenderingOff && r.enabled).ToArray();
                            try
                            {
                                foreach (var renderer in hidden) renderer.enabled = false;
                                estimate = SceneStats.Estimate(camera, 0f, 1, mirror.name);
                            }
                            finally { foreach (var renderer in hidden) renderer.enabled = true; }
                        }
                        UnityEngine.Rendering.RenderPipelineManager.beginCameraRendering += CaptureBudget;
                        try { mirror.RenderNow(); }
                        finally { UnityEngine.Rendering.RenderPipelineManager.beginCameraRendering -= CaptureBudget; }
                        var instanceStats = Game.World.WorldInstances.Last;
                        budgetReport.AppendLine(estimate);
                        budgetReport.AppendLine($"  {mirror.name} instanced: draws {instanceStats.Draws}, triangles {instanceStats.Triangles}");
                        var rt = mirror.Texture;
                        if (rt == null || !rt.IsCreated()) throw new InvalidOperationException("Missing mirror texture: " + mirror.name);
                        var cam = mirror.GetComponent<Camera>();
                        var pixels = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
                        try
                        {
                            RenderTexture.active = rt;
                            pixels.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0); pixels.Apply();
                            File.WriteAllBytes(Path.Combine(output, mirror.name + ".png"), pixels.EncodeToPNG());
                        }
                        finally { UnityEngine.Object.DestroyImmediate(pixels); }
                        // ADR 0112: identify own-interior pixels independently of leather colour, lighting and tier.
                        // The material override is diagnostic only; keep the normal RT above as the visual evidence.
                        var interior = UnityEngine.Object.FindObjectsByType<TruckVisualRig>(FindObjectsSortMode.None)
                            .SelectMany(r => r.interiorGroup.GetLODs()).SelectMany(l => l.renderers).Where(r => r != null).Distinct().ToArray();
                        var saved = interior.Select(r => r.sharedMaterials).ToArray();
                        var marker = new Material(Shader.Find("Universal Render Pipeline/Unlit"));
                        marker.SetColor("_BaseColor", Color.magenta);
                        try
                        {
                            for (int i = 0; i < interior.Length; i++)
                                interior[i].sharedMaterials = Enumerable.Repeat(marker, saved[i].Length).ToArray();
                            mirror.RenderNow();
                            RenderTexture.active = rt;
                            var mask = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
                            try
                            {
                                mask.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0); mask.Apply();
                                // Glazing can attenuate the identifier. Detect its chroma, not just full-bright magenta.
                                int count = mask.GetPixels32().Count(p => p.r > 64 && p.b > 64 && p.g * 2 < Math.Min(p.r, p.b));
                                interiorReport.AppendLine($"{mirror.name}\t{count}\t{rt.width * rt.height}");
                                File.WriteAllBytes(Path.Combine(output, mirror.name + "_interior-mask.png"), mask.EncodeToPNG());
                            }
                            finally { UnityEngine.Object.DestroyImmediate(mask); }
                        }
                        finally
                        {
                            for (int i = 0; i < interior.Length; i++) interior[i].sharedMaterials = saved[i];
                            UnityEngine.Object.DestroyImmediate(marker);
                            mirror.RenderNow();
                        }
                        int level = VehicleCameraBudget.Level;
                        report.AppendLine(FormattableString.Invariant($"{mirror.name}\t{mirror.Class}\t{rt.width}\t{rt.height}\t{cam.fieldOfView:F3}\t{cam.aspect:F5}\t{cam.nearClipPlane:F3}\t{cam.farClipPlane:F1}\t{mirror.LodScale:F2}\t{VehicleCameraBudget.MirrorsPerFrame}\t{VehicleCameraBudget.MirrorIntervalFor(level, mirror.Class, false)}\t{VehicleCameraBudget.MirrorIntervalFor(level, mirror.Class, true)}"));
                    }
                }
                finally { RenderTexture.active = previous; }
                File.WriteAllText(Path.Combine(output, "configuration.tsv"), report.ToString());
                File.WriteAllText(Path.Combine(output, "interior-pixels.tsv"), interiorReport.ToString());
                File.WriteAllText(Path.Combine(output, "budgets.txt"), budgetReport.ToString());
                exit = 0;
            }
            catch (Exception e) { Debug.LogException(e); }
            Debug.Log("CABMIRRORAUDIT_RESULT: " + (exit == 0 ? "OK" : "FAILED"));
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }
    }
}
