using System;
using System.Globalization;
using System.IO;
using Game.Core;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Editor.VisualQA
{
    /// <summary>
    /// ADR 0340 evidence tool (editor only, off unless asked for): the native pixels of the class II mirror render textures
    /// of a visual-QA run, written next to the control-camera frames - the HUD windows minify / frame them, a critic needs
    /// the picture itself.
    /// <list type="bullet">
    /// <item><c>KAMION_MIRROR_DUMP=&lt;dir&gt;</c> (environment): before every view-camera render, each main mirror's texture is saved as
    /// <c>&lt;dir&gt;/mirror_&lt;L|R&gt;.png</c> (overwritten: the last render wins), flipped left-right like the glass shows it.</item>
    /// <item><c>KAMION_MIRROR_RES=&lt;x&gt;</c>: render-texture height multiplier for that run (diagnostic super-sampling, e.g. 3).</item>
    /// <item><c>KAMION_MIRROR_MSAA=&lt;1|2|4|8&gt;</c>, <c>KAMION_MIRROR_SHADOWS=&lt;0|1&gt;</c> (ADR 0342): A/B of the mirror camera quality.</item>
    /// <item><c>KAMION_MIRROR_LOD=&lt;x&gt;</c>: LOD scale of the mirror cameras for that run (1 = main-view LOD).</item>
    /// </list>
    /// </summary>
    static class MirrorDump
    {
        static string s_Dir;
        static bool s_BenchDone;

        /// <summary>
        /// ADR 0342 (<c>KAMION_MIRROR_BENCH=1</c>, once per run): cost of the class II mirror pair per configuration. Each round renders
        /// both main mirrors N times per configuration and waits for the GPU (1-pixel read-back) - rounds are interleaved so a busy
        /// shared GPU hits every configuration alike. Prints <c>MIRROR_BENCH</c> lines (median / min of the rounds, ms per pair).
        /// Editor proxy only - the player measurement is pc-metrics.
        /// </summary>
        public static void BenchOnce()
        {
            if (s_BenchDone || Environment.GetEnvironmentVariable("KAMION_MIRROR_BENCH") != "1") return;
            s_BenchDone = true;
            var mirrors = System.Array.FindAll(UnityEngine.Object.FindObjectsByType<RenderTextureMirror>(FindObjectsSortMode.None), m => m.main);
            if (mirrors.Length == 0) { Debug.Log("MIRROR_BENCH no main mirrors"); return; }
            // mainMin: class II floor height (ADR 0340 addendum 2; -1 = the explicit res multiplier, floor off), post: main-view grading
            var cfg = new (string name, int msaa, bool shadows, float res, int mainMin, bool post)[]
            {
                ("msaa1 (pre-0342)", 1, false, 1f, -1, false), ("msaa4 (0342 High)", 4, false, 1f, -1, false), ("msaa4+shadows", 4, true, 1f, -1, false),
                ("msaa4 res1.5 (0342 Ultra-like)", 4, false, 1.5f, -1, false),
                ("msaa4 post", 4, false, 1f, -1, true), ("msaa4 main1024", 4, false, 0f, 1024, false),
                ("msaa4 main1024 post (0340-2 High)", 4, false, 0f, 1024, true), ("msaa4 main768 post", 4, false, 0f, 768, true),
            };
            var size = new Vector2Int[cfg.Length];
            const int rounds = 5, n = 30;
            var ms = new float[cfg.Length][];
            for (int c = 0; c < cfg.Length; c++) ms[c] = new float[rounds];
            var sw = new System.Diagnostics.Stopwatch();
            var one = new Texture2D(1, 1, TextureFormat.RGB24, false);
            var prevMsaa = MirrorOverrides.Msaa; var prevSh = MirrorOverrides.Shadows; var prevRes = MirrorOverrides.Resolution;
            var prevMain = MirrorOverrides.MainMinHeight; var prevPost = MirrorOverrides.Post; bool prevForce = RenderTextureMirror.ForceRender;
            RenderTextureMirror.ForceRender = true;   // the HUD windows show the pair (grading applies to window pictures only)
            for (int r = 0; r < rounds; r++)
                for (int c = 0; c < cfg.Length; c++)
                {
                    MirrorOverrides.Msaa = cfg[c].msaa; MirrorOverrides.Shadows = cfg[c].shadows;
                    MirrorOverrides.Resolution = cfg[c].mainMin < 0 ? cfg[c].res : (float?)null;
                    MirrorOverrides.MainMinHeight = cfg[c].mainMin < 0 ? 0 : cfg[c].mainMin; MirrorOverrides.Post = cfg[c].post;
                    foreach (var m in mirrors) m.RenderNow();   // (re)creates the target, warm-up
                    size[c] = new Vector2Int(mirrors[0].Texture.width, mirrors[0].Texture.height);
                    Sync(mirrors[0], one);
                    sw.Restart();
                    for (int i = 0; i < n; i++) foreach (var m in mirrors) m.RenderNow();
                    Sync(mirrors[0], one);
                    sw.Stop();
                    ms[c][r] = (float)sw.Elapsed.TotalMilliseconds / n;
                }
            MirrorOverrides.Msaa = prevMsaa; MirrorOverrides.Shadows = prevSh; MirrorOverrides.Resolution = prevRes;
            MirrorOverrides.MainMinHeight = prevMain; MirrorOverrides.Post = prevPost; RenderTextureMirror.ForceRender = prevForce;
            foreach (var m in mirrors) m.RenderNow();   // back to the run's configuration
            UnityEngine.Object.DestroyImmediate(one);
            for (int c = 0; c < cfg.Length; c++)
            {
                var a = (float[])ms[c].Clone(); System.Array.Sort(a);
                Debug.Log(string.Format(CultureInfo.InvariantCulture, "MIRROR_BENCH cfg=\"{0}\" tex={1}x{2} median_ms_per_pair={3:F2} min={4:F2} max={5:F2}",
                    cfg[c].name, size[c].x, size[c].y, a[rounds / 2], a[0], a[rounds - 1]));
            }
        }

        static void Sync(RenderTextureMirror m, Texture2D one)
        {
            var prev = RenderTexture.active;
            RenderTexture.active = m.Texture;
            one.ReadPixels(new Rect(0, 0, 1, 1), 0, 0);
            RenderTexture.active = prev;
        }

        [InitializeOnLoadMethod]
        static void Init()
        {
            s_Dir = Environment.GetEnvironmentVariable("KAMION_MIRROR_DUMP");
            if (float.TryParse(Environment.GetEnvironmentVariable("KAMION_MIRROR_RES"), NumberStyles.Float, CultureInfo.InvariantCulture, out float res) && res > 0.1f)
                MirrorOverrides.Resolution = res;
            if (float.TryParse(Environment.GetEnvironmentVariable("KAMION_MIRROR_LOD"), NumberStyles.Float, CultureInfo.InvariantCulture, out float lod) && lod > 0.01f)
                MirrorOverrides.LodScale = lod;
            if (int.TryParse(Environment.GetEnvironmentVariable("KAMION_MIRROR_MSAA"), NumberStyles.Integer, CultureInfo.InvariantCulture, out int msaa) && msaa >= 1)
                MirrorOverrides.Msaa = msaa;
            string sh = Environment.GetEnvironmentVariable("KAMION_MIRROR_SHADOWS");
            if (!string.IsNullOrEmpty(sh)) MirrorOverrides.Shadows = sh == "1";
            // ADR 0340 addendum 2 A/B: KAMION_MIRROR_MAIN=<min height px, 0 = off>, KAMION_MIRROR_POST=<0|1>
            if (int.TryParse(Environment.GetEnvironmentVariable("KAMION_MIRROR_MAIN"), NumberStyles.Integer, CultureInfo.InvariantCulture, out int mainMin) && mainMin >= 0)
                MirrorOverrides.MainMinHeight = mainMin;
            string po = Environment.GetEnvironmentVariable("KAMION_MIRROR_POST");
            if (!string.IsNullOrEmpty(po)) MirrorOverrides.Post = po == "1";
            if (string.IsNullOrEmpty(s_Dir)) return;
            Directory.CreateDirectory(s_Dir);
            RenderPipelineManager.beginCameraRendering -= OnBegin;
            RenderPipelineManager.beginCameraRendering += OnBegin;
        }

        // A view camera is about to render: every mirror texture it will show is complete (RenderNow / the schedule ran).
        static void OnBegin(ScriptableRenderContext ctx, Camera cam)
        {
            if (cam.cameraType != CameraType.Game || cam.TryGetComponent(out RenderTextureMirror _)) return;
            foreach (var m in UnityEngine.Object.FindObjectsByType<RenderTextureMirror>(FindObjectsSortMode.None))
                if (m.main && m.Texture != null && m.Texture.IsCreated()) Save(m);
        }

        static void Save(RenderTextureMirror m)
        {
            var rt = m.Texture;
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false, false);
            tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
            RenderTexture.active = prev;
            var px = tex.GetPixels32();
            int w = rt.width, h = rt.height;
            for (int y = 0; y < h; y++)
                Array.Reverse(px, y * w, w);
            tex.SetPixels32(px);
            File.WriteAllBytes(Path.Combine(s_Dir, "mirror_" + (m.phase == 0 ? "L" : "R") + ".png"), tex.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(tex);
        }
    }
}
