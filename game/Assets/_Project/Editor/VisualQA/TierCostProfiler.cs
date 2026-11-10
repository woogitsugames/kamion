using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using Game.Editor.Build;
using Game.Rendering;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Editor.VisualQA
{
    /// <summary>
    /// Editor cost ablation of one quality tier on the Stage 3 gate cameras (ADR 0046). Opens the world scene, applies the
    /// tier, then times N synchronised renders per camera for each variant (one setting changed at a time) at the phone's
    /// screen size. Prints TIERCOST lines and writes artifacts/perf/tiercost-&lt;tier&gt;.tsv. Editor GPU (desktop,
    /// immediate mode) - only the RATIOS between variants are evidence; phone ms are estimates (UNVERIFIED).
    ///   Unity.exe -batchmode -projectPath game -executeMethod Game.Editor.VisualQA.TierCostProfiler.Run
    ///     [-tcScene WorldC_High] [-tcTier High] [-tcWidth 3120 -tcHeight 1440] [-tcFrames 12] [-tcCameras a,b] [-tcVariants v1,v2]
    /// URP asset changes are made in memory and restored; nothing is saved.
    /// </summary>
    public static class TierCostProfiler
    {
        struct Variant
        {
            public string name;
            public Func<QualityProfile.Tier, QualityProfile.Tier> tier;   // tier-field edits (HLOD, trees, far clip, post...)
            public Action<SerializedObject> urp;                           // URP asset edits
            public float lodBias;                                          // 0 = tier value
        }

        static readonly Dictionary<string, Variant> s_Variants = new Dictionary<string, Variant>();
        static void V(string n, Func<QualityProfile.Tier, QualityProfile.Tier> t = null, Action<SerializedObject> u = null, float lod = 0f) =>
            s_Variants[n] = new Variant { name = n, tier = t, urp = u, lodBias = lod };

        static void SetF(SerializedObject so, string p, float v) => so.FindProperty(p).floatValue = v;
        static void SetI(SerializedObject so, string p, int v) => so.FindProperty(p).intValue = v;
        static void SetB(SerializedObject so, string p, bool v) => so.FindProperty(p).boolValue = v;

        static void Define()
        {
            s_Variants.Clear();
            V("base");
            V("scale085", t => { t.renderScale = 0.85f; return t; });
            V("scale075", t => { t.renderScale = 0.75f; return t; });
            V("msaa1", t => { t.msaa = 1; return t; });
            V("hdr0", t => { t.hdr = false; return t; }, u => SetB(u, "m_SupportsHDR", false));
            V("post0", t => { t.postProcessing = false; return t; });
            V("shadow0", null, u => SetF(u, "m_ShadowDistance", 0f));
            V("shadow60c2", null, u => { SetF(u, "m_ShadowDistance", 60f); SetI(u, "m_ShadowCascadeCount", 2); });
            V("shadow80c3", null, u => SetF(u, "m_ShadowDistance", 80f));
            V("softOff", null, u => SetB(u, "m_SoftShadowsSupported", false));
            V("softLow", null, u => SetI(u, "m_SoftShadowQuality", 1));
            V("shadowRes1024", null, u => SetI(u, "m_MainLightShadowmapResolution", 1024));
            V("treeShadowLod0", t => { t.treeShadowLodMask = 1; return t; });
            V("hlod70", t => { t.forestHlodM = 70f; return t; });
            V("hlod90", t => { t.forestHlodM = 90f; return t; });
            V("trees0", t => { t.treeCullM = 0.01f; t.forestHlodM = -1f; return t; });
            V("lod10", null, null, 1.0f);
            V("lod12", null, null, 1.2f);
            V("far1400", t => { t.cameraFarClip = 1400f; return t; });
            V("addl0", null, u => SetI(u, "m_AdditionalLightsRenderingMode", 0));
            V("detail0", t => { t.worldDetail = false; return t; });
            V("aniso4", t => { t.worldTextureAniso = 4; return t; });
            // Candidate set (ADR 0046): filled in after the ablation, every change measured above.
            V("proposed", t => { t.renderScale = 0.85f; t.treeShadowLodMask = 1; return t; },
                u => { SetI(u, "m_SoftShadowQuality", 1); });
            V("proposedB", t => { t.renderScale = 0.80f; t.treeShadowLodMask = 1; return t; },
                u => { SetI(u, "m_SoftShadowQuality", 1); SetF(u, "m_ShadowDistance", 80f); });
        }

        public static void Run()
        {
            int exit = 1;
            try
            {
                string scene = EditorTools.Arg("-tcScene", "WorldC_High");
                string tier = EditorTools.Arg("-tcTier", "High");
                int w = int.Parse(EditorTools.Arg("-tcWidth", "3120"));
                int h = int.Parse(EditorTools.Arg("-tcHeight", "1440"));
                int frames = int.Parse(EditorTools.Arg("-tcFrames", "12"));
                string camArg = EditorTools.Arg("-tcCameras", null);
                string varArg = EditorTools.Arg("-tcVariants", null);
                string lighting = EditorTools.Arg("-tcLighting", "clear");
                exit = Profile(scene, tier, w, h, frames, camArg, varArg, lighting) ? 0 : 1;
            }
            catch (Exception e) { Debug.LogException(e); }
            Debug.Log("TIERCOST_RESULT: " + (exit == 0 ? "OK" : "FAILED"));
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        static bool Profile(string sceneName, string tierName, int w, int h, int frames, string camArg, string varArg, string lighting)
        {
            Define();
            string scenePath = AssetDatabase.FindAssets("t:Scene " + sceneName).Select(AssetDatabase.GUIDToAssetPath)
                .FirstOrDefault(p => Path.GetFileNameWithoutExtension(p) == sceneName);
            if (scenePath == null) throw new FileNotFoundException(sceneName);
            QualityTiers.Apply(tierName);
            ShaderUtil.allowAsyncCompilation = false;
            EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
            var env = UnityEngine.Object.FindAnyObjectByType<EnvironmentLighting>();
            if (env != null) { env.SetPreset(lighting); env.Apply(); }
            foreach (var ck in UnityEngine.Object.FindObjectsByType<Game.World.WorldCollisionCooker>(FindObjectsInactive.Include, FindObjectsSortMode.None)) ck.Cook();
            Physics.SyncTransforms();
            string json = Path.Combine(EditorTools.RepoRoot, "Data/Regions/bialystok-industrial-c/gate3_cameras.json");
            Game.Gameplay.Gate3Cameras.CreateAll(UnityEngine.Object.FindAnyObjectByType<Game.World.WorldRegionRoot>(), null, File.ReadAllText(json));
            var all = UnityEngine.Object.FindObjectsByType<ControlCamera>(FindObjectsInactive.Include, FindObjectsSortMode.None)
                .Where(c => c.id.StartsWith("g3", StringComparison.Ordinal)).OrderBy(c => c.id, StringComparer.Ordinal).ToList();
            if (!string.IsNullOrEmpty(camArg)) { var f = camArg.Split(','); all = all.Where(c => f.Contains(c.id)).ToList(); }
            if (all.Count == 0) { Debug.LogError("TIERCOST no gate cameras"); return false; }

            var profile = QualityProfile.Load();
            if (!profile.TryGet(tierName, out var baseTier)) throw new ArgumentException(tierName);
            var volume = UnityEngine.Object.FindObjectsByType<Volume>(FindObjectsSortMode.None)
                .FirstOrDefault(v => v.sharedProfile != null && v.sharedProfile.Has<Tonemapping>());
            var applier = UnityEngine.Object.FindAnyObjectByType<QualityProfileApplier>(FindObjectsInactive.Include);
            var urpAsset = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
            if (urpAsset == null) throw new InvalidOperationException("no URP asset");
            string urpBackup = EditorJsonUtility.ToJson(urpAsset);
            float lodBackup = QualitySettings.lodBias;

            var names = string.IsNullOrEmpty(varArg) ? s_Variants.Keys.ToList() : varArg.Split(',').ToList();
            if (!names.Contains("base")) names.Insert(0, "base");
            names.Add("base");   // repeat at the end: drift / noise of the shared desktop GPU
            var sb = new StringBuilder();
            sb.AppendLine($"# tier={tierName} scene={sceneName} {w}x{h} frames={frames} lighting={lighting} gpu={SystemInfo.graphicsDeviceName} cameras={all.Count}");
            sb.AppendLine("variant\tcamera\twall_ms\tcpu_submit_ms\tmirror3_ms\tdraws_est\ttris_k_est");
            var totals = new List<(string name, double wall, double cpu, double mirror)>();
            var one = new Texture2D(1, 1, TextureFormat.RGBA32, false);
            Tonemapping tm = null;
            int run = 0;
            foreach (var vn in names)
            {
                if (!s_Variants.TryGetValue(vn, out var v)) { Debug.LogWarning("TIERCOST unknown variant " + vn); continue; }
                EditorJsonUtility.FromJsonOverwrite(urpBackup, urpAsset);
                QualitySettings.lodBias = lodBackup;
                var t = baseTier;
                if (v.tier != null) t = v.tier(t);
                var so = new SerializedObject(urpAsset);
                SetF(so, "m_RenderScale", 1f);   // render scale is applied through the target size below
                SetI(so, "m_MSAA", Mathf.Max(1, t.msaa));
                v.urp?.Invoke(so);
                so.ApplyModifiedPropertiesWithoutUndo();
                if (v.lodBias > 0f) QualitySettings.lodBias = v.lodBias;
                double sumWall = 0, sumCpu = 0, sumMirror = 0;
                int tw = Mathf.RoundToInt(w * t.renderScale), th = Mathf.RoundToInt(h * t.renderScale);
                var rt = new RenderTexture(tw, th, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB) { antiAliasing = Mathf.Max(1, t.msaa) };
                // Mirror proxy: High mirror budget = 3 main-mirror renders/frame, 384 px high, aspect 0.45, far 400 m, no shadows/post/MSAA (ADR 0042).
                var mrt = new RenderTexture(173, 384, 16, RenderTextureFormat.ARGB32) { antiAliasing = 1 };
                foreach (var qa in all)
                {
                    var cam = qa.GetComponent<Camera>();
                    qa.gameObject.SetActive(true);
                    QualityProfileApplier.Apply(t, cam, volume, applier != null ? applier.worldTextures : null, ref tm);
                    cam.farClipPlane = t.cameraFarClip;
                    cam.targetTexture = rt;
                    void Sync(RenderTexture r) { RenderTexture.active = r; one.ReadPixels(new Rect(0, 0, 1, 1), 0, 0); one.Apply(); RenderTexture.active = null; }
                    cam.Render(); cam.Render(); Sync(rt);
                    var sw = System.Diagnostics.Stopwatch.StartNew();
                    double cpu = 0;
                    for (int k = 0; k < frames; k++)
                    {
                        var c0 = sw.Elapsed.TotalMilliseconds;
                        cam.Render();
                        cpu += sw.Elapsed.TotalMilliseconds - c0;
                    }
                    Sync(rt);
                    double wall = sw.Elapsed.TotalMilliseconds / frames;
                    cpu /= frames;
                    // mirror proxy on the same camera pose
                    var data = cam.GetUniversalAdditionalCameraData();
                    bool post = data.renderPostProcessing, shadows = data.renderShadows; float far = cam.farClipPlane, fov = cam.fieldOfView;
                    data.renderPostProcessing = false; data.renderShadows = false; cam.allowMSAA = false;
                    cam.farClipPlane = 400f; cam.fieldOfView = 25f; cam.targetTexture = mrt;
                    cam.Render(); Sync(mrt);
                    sw.Restart();
                    for (int k = 0; k < frames; k++) { cam.Render(); cam.Render(); cam.Render(); }
                    Sync(mrt);
                    double mirror = sw.Elapsed.TotalMilliseconds / frames;
                    data.renderPostProcessing = post; data.renderShadows = shadows; cam.farClipPlane = far; cam.fieldOfView = fov;
                    cam.allowMSAA = t.msaa > 1;
                    cam.targetTexture = null;
                    string est = run == 0 ? SceneStats.Estimate(cam, urpAsset.shadowDistance, urpAsset.shadowCascadeCount, qa.id).Replace('\n', ' ') : "";
                    var wi = Game.World.WorldInstances.Last;
                    sb.AppendLine($"{vn}\t{qa.id}\t{wall:F3}\t{cpu:F3}\t{mirror:F3}\tinst_draws={wi.Draws} inst_tris_k={wi.Triangles / 1000} hlod={wi.HlodCells}\t{est}");
                    sumWall += wall; sumCpu += cpu; sumMirror += mirror;
                    qa.gameObject.SetActive(false);
                }
                rt.Release(); UnityEngine.Object.DestroyImmediate(rt); mrt.Release(); UnityEngine.Object.DestroyImmediate(mrt);
                double n = all.Count;
                totals.Add((vn, sumWall / n, sumCpu / n, sumMirror / n));
                Debug.Log($"TIERCOST {vn} wall={sumWall / n:F3} cpu={sumCpu / n:F3} mirror3={sumMirror / n:F3} ({tw}x{th} msaa {t.msaa})");
                run++;
            }
            EditorJsonUtility.FromJsonOverwrite(urpBackup, urpAsset);
            QualitySettings.lodBias = lodBackup;
            double b0 = totals.Where(x => x.name == "base").Average(x => x.wall);
            sb.AppendLine();
            sb.AppendLine("variant\tmean_wall_ms\tmean_cpu_submit_ms\tmean_mirror3_ms\twall_vs_base_%");
            foreach (var x in totals) sb.AppendLine($"{x.name}\t{x.wall:F3}\t{x.cpu:F3}\t{x.mirror:F3}\t{100.0 * (x.wall / b0 - 1.0):+0.0;-0.0}");
            string outDir = Path.Combine(EditorTools.RepoRoot, "artifacts", "perf");
            Directory.CreateDirectory(outDir);
            string file = Path.Combine(outDir, $"tiercost-{tierName}-{DateTime.Now:yyyyMMdd-HHmmss}.tsv");
            File.WriteAllText(file, sb.ToString());
            Debug.Log("TIERCOST file " + file);
            return true;
        }
    }
}
