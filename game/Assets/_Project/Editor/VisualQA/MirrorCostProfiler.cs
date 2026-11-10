using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using Game.Core;
using Game.Editor.Build;
using Game.Rendering;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Game.Editor.VisualQA
{
    /// <summary>
    /// ADR 0068: editor cost of the fixed passes per configuration - every real truck mirror camera and the reflection-capture
    /// faces, rendered N times each with a GPU sync (1-pixel readback), plus what each view submits (instanced draws /
    /// triangles from WorldInstances, CPU estimate of the regular renderers after LOD selection, SceneStats). Desktop editor:
    /// CPU submit time and the submitted geometry are the evidence; phone ms UNVERIFIED (rq_ab on the device).
    ///   Unity.exe -batchmode -projectPath game -executeMethod Game.Editor.VisualQA.MirrorCostProfiler.Run
    ///     [-mcScene WorldC_High] [-mcTier High] [-mcFrames 60] [-mcOut &lt;dir&gt;] [-mcVariants legacy,new,...]
    /// Variants: legacy (pre-0068), new (shipping), lod035 / lod07 (class II LOD scale, convex 0.6x), far300, res075.
    /// </summary>
    public static class MirrorCostProfiler
    {
        public static void Run()
        {
            int exit = 1;
            try
            {
                exit = Profile(EditorTools.Arg("-mcScene", "WorldC_High"), EditorTools.Arg("-mcTier", "High"),
                    int.Parse(EditorTools.Arg("-mcFrames", "60")), EditorTools.Arg("-mcOut", Path.Combine(EditorTools.RepoRoot, "artifacts", "perf")),
                    EditorTools.Arg("-mcVariants", "legacy,new,lod035,lod07,far300,res075,new,legacy")) ? 0 : 1;
            }
            catch (Exception e) { Debug.LogException(e); }
            finally { MirrorOverrides.Legacy = false; MirrorOverrides.LodScale = null; MirrorOverrides.FarClip = null; MirrorOverrides.Resolution = null; }
            Debug.Log("MIRRORCOST_RESULT: " + (exit == 0 ? "OK" : "FAILED"));
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        static void SetVariant(string v)
        {
            MirrorOverrides.Legacy = v == "legacy";
            MirrorOverrides.LodScale = v == "lod035" ? 0.35f : v == "lod07" ? 0.7f : (float?)null;
            MirrorOverrides.FarClip = v == "far300" ? 300f : (float?)null;
            MirrorOverrides.Resolution = v == "res075" ? 0.75f : (float?)null;
        }

        static bool Profile(string sceneName, string tierName, int frames, string outDir, string variants)
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
            if (mirrors.Length == 0) { Debug.LogError("MIRRORCOST no mirrors"); return false; }
            var one = new Texture2D(1, 1, TextureFormat.RGBA32, false);
            void Sync(RenderTexture r) { RenderTexture.active = r; one.ReadPixels(new Rect(0, 0, 1, 1), 0, 0); one.Apply(); RenderTexture.active = null; }
            float tierBias = QualitySettings.lodBias;
            var urp = UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline as UnityEngine.Rendering.Universal.UniversalRenderPipelineAsset;

            var sb = new StringBuilder();
            sb.AppendLine($"# MirrorCostProfiler tier={tierName} scene={sceneName} frames={frames} lodBias={tierBias} gpu={SystemInfo.graphicsDeviceName} (editor, CPU-bound desktop; phone UNVERIFIED)");
            sb.AppendLine("variant\tview\tclass\tlod_scale\tfar\trt\tcpu_submit_ms\twall_ms\tinst_draws\tinst_tris_k\treg_draws_est\treg_tris_k_est");
            var summary = new List<string>();
            foreach (var v in variants.Split(','))
            {
                SetVariant(v);
                double iiCpu = 0, iiWall = 0, cxCpu = 0, cxWall = 0; long iiTris = 0, cxTris = 0; int iiDraws = 0, cxDraws = 0, nii = 0, ncx = 0;
                foreach (var m in mirrors)
                {
                    var cam = m.GetComponent<Camera>();
                    m.RenderNow(); m.RenderNow(); Sync(m.Texture);   // target + warm-up
                    var wi = Game.World.WorldInstances.Last;
                    var sw = System.Diagnostics.Stopwatch.StartNew();
                    double cpu = 0;
                    for (int k = 0; k < frames; k++)
                    {
                        double c0 = sw.Elapsed.TotalMilliseconds;
                        m.RenderNow();
                        cpu += sw.Elapsed.TotalMilliseconds - c0;
                        if ((k & 7) == 7) Sync(m.Texture);   // keep the GPU from queueing many frames
                    }
                    Sync(m.Texture);
                    double wall = sw.Elapsed.TotalMilliseconds / frames;
                    cpu /= frames;
                    // Regular renderers after LOD selection at the bias the mirror renders with.
                    QualitySettings.lodBias = tierBias * m.LodScale;
                    string est = SceneStats.Estimate(cam, 0f, 1, m.name);
                    QualitySettings.lodBias = tierBias;
                    int regDraws = ParseInt(est, "drawsEst="), regTris = ParseInt(est, "trisK=");
                    int cls = m.Class;
                    sb.AppendLine($"{v}\t{m.name}\t{cls}\t{m.LodScale:F2}\t{cam.farClipPlane:F0}\t{m.Texture.width}x{m.Texture.height}\t{cpu:F3}\t{wall:F3}\t{wi.Draws}\t{wi.Triangles / 1000}\t{regDraws}\t{regTris}");
                    if (cls == 2) { iiCpu += cpu; iiWall += wall; iiTris += wi.Triangles / 1000 + regTris; iiDraws += wi.Draws + regDraws; nii++; }
                    else { cxCpu += cpu; cxWall += wall; cxTris += wi.Triangles / 1000 + regTris; cxDraws += wi.Draws + regDraws; ncx++; }
                }
                // Mirror work per frame at speed with all six on screen (High: one class II + one convex render per frame).
                double fCpu = iiCpu / nii + cxCpu / ncx, fWall = iiWall / nii + cxWall / ncx;
                string line = $"{v}: per frame (1 II + 1 convex) cpu_submit={fCpu:F3} ms wall={fWall:F3} ms; class II mean draws={iiDraws / nii} tris_k={iiTris / nii}; convex mean draws={cxDraws / ncx} tris_k={cxTris / ncx}";
                summary.Add(line);
                Debug.Log("MIRRORCOST " + line);
            }
            SetVariant("new");
            // Where the regular (non-instanced) triangles of each mirror come from: top renderers after LOD selection.
            foreach (var m in mirrors) sb.AppendLine("# top " + m.name + ": " + TopRenderers(m.GetComponent<Camera>(), tierBias * m.LodScale, 12));

            // Reflection-capture faces (ADR 0056): LOD scale 1 vs the shipping 0.25.
            var cap = VehicleReflectionCapture.Active != null ? VehicleReflectionCapture.Active : UnityEngine.Object.FindAnyObjectByType<VehicleReflectionCapture>();
            var tag = Resources.FindObjectsOfTypeAll<ExtraViewTag>().FirstOrDefault(t => t.kind == ExtraViewKind.Capture);
            if (cap != null && cap.Enabled && tag != null)
            {
                foreach (float s in new[] { 1f, 0.25f, 1f, 0.25f })
                {
                    tag.lodScale = s;
                    cap.RenderAllNow();
                    var sw = System.Diagnostics.Stopwatch.StartNew();
                    int n = Math.Max(4, frames / 6);
                    for (int k = 0; k < n; k++) cap.RenderAllNow();
                    var rt = RenderTexture.GetTemporary(1, 1);
                    Graphics.Blit(Texture2D.blackTexture, rt); Sync(rt); RenderTexture.ReleaseTemporary(rt);
                    double face = sw.Elapsed.TotalMilliseconds / (n * 6);
                    string line = $"capture lod_scale={s:F2}: per face wall={face:F3} ms (6 faces + mips per RenderAllNow); {cap.LoadEstimate()}";
                    summary.Add(line);
                    Debug.Log("MIRRORCOST " + line);
                }
                tag.lodScale = cap.captureLodScale;
            }
            else summary.Add("capture: not active in this scene/tier");

            sb.AppendLine();
            foreach (var s in summary) sb.AppendLine("# " + s);
            Directory.CreateDirectory(outDir);
            string file = Path.Combine(outDir, $"mirrorcost-{tierName}-{DateTime.Now:yyyyMMdd-HHmmss}.tsv");
            File.WriteAllText(file, sb.ToString());
            Debug.Log("MIRRORCOST file " + file);
            UnityEngine.Object.DestroyImmediate(one);
            return true;
        }

        /// <summary>Visible regular renderers after LOD selection at <paramref name="bias"/>, grouped by root object, by triangles.</summary>
        static string TopRenderers(Camera cam, float bias, int top)
        {
            var planes = GeometryUtility.CalculateFrustumPlanes(cam);
            var chosen = new HashSet<Renderer>();
            var grouped = new HashSet<Renderer>();
            float tanHalf = Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad);
            foreach (var lg in UnityEngine.Object.FindObjectsByType<LODGroup>(FindObjectsSortMode.None))
            {
                var lods = lg.GetLODs();
                foreach (var l in lods) foreach (var r in l.renderers) if (r != null) grouped.Add(r);
                Vector3 c = lg.transform.TransformPoint(lg.localReferencePoint);
                float h = lg.size / (2f * Mathf.Max(Vector3.Distance(cam.transform.position, c), 0.01f) * tanHalf) * bias;
                for (int i = 0; i < lods.Length; i++)
                {
                    if (h < lods[i].screenRelativeTransitionHeight && i < lods.Length - 1) continue;
                    if (h < lods[i].screenRelativeTransitionHeight) break;
                    foreach (var r in lods[i].renderers) if (r != null) chosen.Add(r);
                    break;
                }
            }
            var byKey = new Dictionary<string, (long tris, int draws)>();
            foreach (var r in UnityEngine.Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            {
                if (!r.enabled || !r.gameObject.activeInHierarchy || (cam.cullingMask & (1 << r.gameObject.layer)) == 0) continue;
                if (grouped.Contains(r) && !chosen.Contains(r)) continue;
                var mf = r.GetComponent<MeshFilter>();
                if (mf == null || mf.sharedMesh == null) continue;
                var b = r.bounds;
                if (Mathf.Sqrt(b.SqrDistance(cam.transform.position)) > cam.farClipPlane || !GeometryUtility.TestPlanesAABB(planes, b)) continue;
                long t = 0;
                for (int s = 0; s < mf.sharedMesh.subMeshCount; s++) t += (long)mf.sharedMesh.GetIndexCount(s) / 3;
                // Key: top-level object / first child under it (e.g. Tractor/Interior, World/chunk_x)
                var tr = r.transform; var parent = tr;
                while (parent.parent != null && parent.parent.parent != null) parent = parent.parent;
                string key = (parent.parent != null ? parent.parent.name + "/" : "") + parent.name;
                if (key.StartsWith("Tractor", StringComparison.Ordinal))
                {
                    // Own truck: one level deeper (LOD / interior / glass groups under CabSuspension)
                    var sub = tr;
                    while (sub.parent != null && sub.parent != parent) sub = sub.parent;
                    if (sub != parent) key += "/" + sub.name;
                    var lg = r.GetComponentInParent<LODGroup>();
                    if (lg != null) key += " [" + lg.name + "]";
                }
                byKey.TryGetValue(key, out var cur);
                byKey[key] = (cur.tris + t, cur.draws + mf.sharedMesh.subMeshCount);
            }
            return string.Join("; ", byKey.OrderByDescending(kv => kv.Value.tris).Take(top).Select(kv => $"{kv.Key} {kv.Value.tris / 1000}k/{kv.Value.draws}d"));
        }

        static int ParseInt(string s, string key)
        {
            int i = s.IndexOf(key, StringComparison.Ordinal);
            if (i < 0) return 0;
            i += key.Length;
            int j = i;
            while (j < s.Length && char.IsDigit(s[j])) j++;
            return int.TryParse(s.Substring(i, j - i), out int v) ? v : 0;
        }
    }
}
