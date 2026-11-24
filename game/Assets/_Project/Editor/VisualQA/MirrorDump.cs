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
