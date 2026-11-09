using System;
using System.IO;
using System.Linq;
using Game.Editor.Build;
using Game.Platform;
using Game.Rendering;
using Game.UI;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Game.Editor.VisualQA
{
    /// <summary>
    /// Renders every <see cref="ControlCamera"/> of a scene to PNG. Batchmode (needs a GPU, so
    /// do NOT pass -nographics — the null device renders nothing):
    ///   Unity.exe -batchmode -quit -projectPath game
    ///     -executeMethod Game.Editor.VisualQA.VisualQaRunner.RenderControlCameras
    ///     -qaScene Boot [-qaWidth 2340 -qaHeight 1080] [-qaOutput dir] [-qaTier Medium]
    /// Output default: artifacts/visual-qa/&lt;scene&gt;/&lt;id&gt;.png. Prints "VISUALQA_RESULT: ...".
    /// </summary>
    public static class VisualQaRunner
    {
        public static void RenderControlCameras()
        {
            int exit = 1;
            try
            {
                string scene = EditorTools.Arg("-qaScene", "Boot");
                int w = int.Parse(EditorTools.Arg("-qaWidth", "2340"));
                int h = int.Parse(EditorTools.Arg("-qaHeight", "1080"));
                string tier = EditorTools.Arg("-qaTier", "Medium");
                string outDir = EditorTools.Arg("-qaOutput", Path.Combine(EditorTools.RepoRoot, "artifacts", "visual-qa", scene));
                int count = Render(scene, w, h, tier, outDir);
                exit = count > 0 ? 0 : 1;
                Debug.Log($"VISUALQA_RESULT: {(exit == 0 ? "OK" : "NO_CAMERAS")} rendered={count} dir={outDir}");
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Debug.Log("VISUALQA_RESULT: FAILED");
            }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        [MenuItem("Kamion/Visual QA/Render Boot control cameras")]
        static void MenuRenderBoot() =>
            Render("Boot", 2340, 1080, "Medium", Path.Combine(EditorTools.RepoRoot, "artifacts", "visual-qa", "Boot"));

        public static int Render(string sceneName, int width, int height, string tier, string outDir)
        {
            string scenePath = AssetDatabase.FindAssets("t:Scene " + sceneName)
                .Select(AssetDatabase.GUIDToAssetPath)
                .FirstOrDefault(p => Path.GetFileNameWithoutExtension(p) == sceneName);
            if (scenePath == null) throw new FileNotFoundException("Scene not found: " + sceneName);

            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                throw new InvalidOperationException("No graphics device (-nographics?) — visual QA needs a GPU.");

            QualityTiers.Apply(tier);
            ShaderUtil.allowAsyncCompilation = false; // avoid cyan placeholder shaders in captures
            EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
            Directory.CreateDirectory(outDir);

            var cams = UnityEngine.Object.FindObjectsByType<ControlCamera>(FindObjectsInactive.Include, FindObjectsSortMode.None)
                .OrderBy(c => c.id, StringComparer.Ordinal).ToArray();
            // Warm-up: the very first Camera.Render after opening a scene in batchmode can draw with
            // stale per-material SRP-batcher data (every object showed the ground material). Render
            // each camera once into a throwaway target before capturing.
            if (cams.Length > 0)
            {
                var warm = new RenderTexture(256, 128, 24);
                foreach (var qa in cams)
                {
                    var c = qa.GetComponent<Camera>();
                    bool active = qa.gameObject.activeSelf;
                    qa.gameObject.SetActive(true);
                    var prev = c.targetTexture;
                    c.targetTexture = warm;
                    c.Render();
                    c.targetTexture = prev;
                    qa.gameObject.SetActive(active);
                }
                warm.Release();
                UnityEngine.Object.DestroyImmediate(warm);
            }

            int rendered = 0;
            foreach (var qa in cams)
            {
                var cam = qa.GetComponent<Camera>();
                bool wasActive = qa.gameObject.activeSelf;
                bool wasEnabled = cam.enabled;
                qa.gameObject.SetActive(true);

                DiagnosticsOverlay overlay = null;
                if (qa.includeDiagnosticsOverlay)
                {
                    overlay = DiagnosticsOverlay.Create(cam, new DefaultPlatformServices(), null);
                    // Simulate the A16 camera cutout in landscape (left edge, ~4 % of width).
                    overlay.OverrideSafeAreaNormalized(new Rect(0.04f, 0f, 0.96f, 1f));
                }

                var rt = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB)
                { antiAliasing = 1 };
                var prevTarget = cam.targetTexture;
                cam.targetTexture = rt;
                cam.enabled = true;
                if (overlay != null)
                {
                    overlay.RefreshNow();
                    Canvas.ForceUpdateCanvases();
                }
                cam.Render();

                var prevActive = RenderTexture.active;
                RenderTexture.active = rt;
                var tex = new Texture2D(width, height, TextureFormat.RGB24, false);
                tex.ReadPixels(new Rect(0, 0, width, height), 0, 0);
                tex.Apply();
                RenderTexture.active = prevActive;

                string file = Path.Combine(outDir, qa.id + ".png");
                File.WriteAllBytes(file, tex.EncodeToPNG());
                Debug.Log($"[VISUALQA] {qa.id} → {file}");
                rendered++;

                cam.targetTexture = prevTarget;
                cam.enabled = wasEnabled;
                qa.gameObject.SetActive(wasActive);
                UnityEngine.Object.DestroyImmediate(tex);
                rt.Release();
                UnityEngine.Object.DestroyImmediate(rt);
                if (overlay != null)
                {
                    var es = UnityEngine.Object.FindAnyObjectByType<UnityEngine.EventSystems.EventSystem>();
                    if (es != null) UnityEngine.Object.DestroyImmediate(es.gameObject);
                    UnityEngine.Object.DestroyImmediate(overlay.gameObject);
                }
            }
            return rendered;
        }
    }
}
