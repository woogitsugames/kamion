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
    /// <summary>
    /// Editor A/B of the mirror refresh policy (ADR 0046 addendum): opens the world scene with the TRAKT truck, applies the
    /// tier, and runs N simulated frames per policy with all six mirrors on screen: MirrorRefreshSchedule picks the mirrors,
    /// the picked real mirror cameras render (RenderNow), then the cab-driver control camera renders at the phone size.
    /// Every frame is GPU-synchronised (1-pixel readback). Prints MIRRORBUDGET lines and writes
    /// artifacts/perf/mirrorbudget-&lt;tier&gt;-&lt;ts&gt;.tsv. Desktop editor: ratios only, phone ms UNVERIFIED.
    ///   Unity.exe -batchmode -projectPath game -executeMethod Game.Editor.VisualQA.MirrorBudgetProfiler.Run
    ///     [-mbScene WorldC_High] [-mbTier High] [-mbFrames 240] [-mbWidth 3120 -mbHeight 1440]
    /// </summary>
    public static class MirrorBudgetProfiler
    {
        public static void Run()
        {
            int exit = 1;
            try
            {
                exit = Profile(EditorTools.Arg("-mbScene", "WorldC_High"), EditorTools.Arg("-mbTier", "High"),
                    int.Parse(EditorTools.Arg("-mbFrames", "240")), int.Parse(EditorTools.Arg("-mbWidth", "3120")),
                    int.Parse(EditorTools.Arg("-mbHeight", "1440"))) ? 0 : 1;
            }
            catch (Exception e) { Debug.LogException(e); }
            Debug.Log("MIRRORBUDGET_RESULT: " + (exit == 0 ? "OK" : "FAILED"));
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        static bool Profile(string sceneName, string tierName, int frames, int w, int h)
        {
            string scenePath = AssetDatabase.FindAssets("t:Scene " + sceneName).Select(AssetDatabase.GUIDToAssetPath)
                .FirstOrDefault(p => Path.GetFileNameWithoutExtension(p) == sceneName);
            if (scenePath == null) throw new FileNotFoundException(sceneName);
            QualityTiers.Apply(tierName);
            ShaderUtil.allowAsyncCompilation = false;
            EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
            var env = UnityEngine.Object.FindAnyObjectByType<EnvironmentLighting>();
            if (env != null) { env.SetPreset("overcast"); env.Apply(); }
            var mirrors = UnityEngine.Object.FindObjectsByType<RenderTextureMirror>(FindObjectsSortMode.None).OrderBy(m => m.phase).ToArray();
            if (mirrors.Length == 0) { Debug.LogError("MIRRORBUDGET no mirrors"); return false; }
            var qa = UnityEngine.Object.FindObjectsByType<ControlCamera>(FindObjectsInactive.Include, FindObjectsSortMode.None).FirstOrDefault(c => c.id == "cab-driver");
            if (qa == null) { Debug.LogError("MIRRORBUDGET no cab-driver camera"); return false; }
            qa.gameObject.SetActive(true);
            var cam = qa.GetComponent<Camera>();
            var rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB) { antiAliasing = Mathf.Max(1, QualitySettings.antiAliasing) };
            cam.targetTexture = rt;
            var one = new Texture2D(1, 1, TextureFormat.RGBA32, false);
            void Sync() { RenderTexture.active = rt; one.ReadPixels(new Rect(0, 0, 1, 1), 0, 0); one.Apply(); RenderTexture.active = null; }
            foreach (var m in mirrors) m.RenderNow();   // targets + warm-up
            cam.Render(); Sync();

            var policies = new[] { ("old_cap3", 3, 0), ("new_cap2_main1", 2, 1), ("old_cap3", 3, 0), ("new_cap2_main1", 2, 1) };
            var sb = new StringBuilder();
            sb.AppendLine($"# MirrorBudgetProfiler tier={tierName} scene={sceneName} {w}x{h} msaa={rt.antiAliasing} frames={frames} mirrors={mirrors.Length} gpu={SystemInfo.graphicsDeviceName} (editor estimate, UNVERIFIED on phone)");
            sb.AppendLine("policy\tcap\tmainSlots\tmirror_renders_per_frame\tmirror_ms_p50\tmirror_ms_p95\tframe_ms_p50\tframe_ms_p95\tframe_ms_p99\tmain_interval_max\tconvex_interval_max");
            var entries = new MirrorRefreshSchedule.Entry[mirrors.Length];
            var mirrorMs = new double[frames];
            var frameMs = new double[frames];
            var sw = new System.Diagnostics.Stopwatch();
            foreach (var (name, cap, mainSlots) in policies)
            {
                for (int i = 0; i < mirrors.Length; i++)
                    entries[i] = new MirrorRefreshSchedule.Entry { phase = mirrors[i].phase, main = mirrors[i].main, weight = mirrors[i].weight, candidate = true };
                var last = Enumerable.Repeat(-1, mirrors.Length).ToArray();
                int mainMax = 0, convexMax = 0, renders = 0;
                for (int f = 0; f < frames; f++)
                {
                    sw.Restart();
                    MirrorRefreshSchedule.Step(entries, entries.Length, cap, mainSlots);
                    for (int i = 0; i < mirrors.Length; i++)
                    {
                        if (!entries[i].selected) continue;
                        mirrors[i].RenderNow(); renders++;
                        if (f >= 16 && last[i] >= 0)
                        {
                            if (mirrors[i].main) mainMax = Math.Max(mainMax, f - last[i]); else convexMax = Math.Max(convexMax, f - last[i]);
                        }
                        last[i] = f;
                    }
                    var t = mirrors[0].Texture;
                    if (t != null) { RenderTexture.active = t; one.ReadPixels(new Rect(0, 0, 1, 1), 0, 0); one.Apply(); RenderTexture.active = null; }
                    double mMs = sw.Elapsed.TotalMilliseconds;
                    cam.Render(); Sync();
                    mirrorMs[f] = mMs;
                    frameMs[f] = sw.Elapsed.TotalMilliseconds;
                }
                string line = $"{name}\t{cap}\t{mainSlots}\t{renders / (double)frames:F2}\t{P(mirrorMs, 50):F3}\t{P(mirrorMs, 95):F3}\t{P(frameMs, 50):F3}\t{P(frameMs, 95):F3}\t{P(frameMs, 99):F3}\t{mainMax}\t{convexMax}";
                sb.AppendLine(line);
                Debug.Log("MIRRORBUDGET " + line);
            }
            cam.targetTexture = null;
            rt.Release(); UnityEngine.Object.DestroyImmediate(rt); UnityEngine.Object.DestroyImmediate(one);
            string outDir = Path.Combine(EditorTools.RepoRoot, "artifacts", "perf");
            Directory.CreateDirectory(outDir);
            string file = Path.Combine(outDir, $"mirrorbudget-{tierName}-{DateTime.Now:yyyyMMdd-HHmmss}.tsv");
            File.WriteAllText(file, sb.ToString());
            Debug.Log("MIRRORBUDGET file " + file);
            return true;
        }

        static double P(double[] a, double pct)
        {
            var s = (double[])a.Clone();
            Array.Sort(s);
            int i = Mathf.Clamp(Mathf.CeilToInt((float)(pct / 100.0 * s.Length)) - 1, 0, s.Length - 1);
            return s[i];
        }
    }
}
