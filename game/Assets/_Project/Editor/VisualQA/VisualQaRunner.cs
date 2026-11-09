using System;
using System.IO;
using System.Linq;
using Game.Editor.Build;
using Game.Platform;
using Game.Rendering;
using Game.UI;
using Game.UI.Driving;
using UnityEditor;
using UnityEditor.SceneManagement;
using Game.Vehicle.Runtime;
using UnityEngine;
using UnityEngine.Rendering.Universal;

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

        [MenuItem("Kamion/Visual QA/Render DrivingLab control cameras")]
        static void MenuRenderLab() =>
            Render("DrivingLab", 2340, 1080, "Medium", Path.Combine(EditorTools.RepoRoot, "artifacts", "visual-qa", "DrivingLab"));

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

                // Vehicle mirrors and reversing cameras render into their textures first (LateUpdate does not run here).
                foreach (var m in UnityEngine.Object.FindObjectsByType<RenderTextureMirror>(FindObjectsSortMode.None)) m.RenderNow();

                // UI is rendered in its own pass (UI layer only, transparent clear) and composited over the world
                // image (premultiplied "over"), exactly like the runtime Screen Space - Overlay canvas: world geometry
                // can never draw over the HUD. (A Screen Space - Camera canvas on the world camera let non-static scene
                // objects - signs, cones - draw over HUD buttons, e.g. the "0 m" sign over the gear "−" button.)
                Camera uiCam = null;
                int prevMask = cam.cullingMask;
                bool ui = qa.includeDiagnosticsOverlay || qa.includeDrivingHud;
                if (ui)
                {
                    var uiGo = new GameObject("QA_UICamera");
                    uiGo.transform.SetPositionAndRotation(cam.transform.position, cam.transform.rotation);
                    uiCam = uiGo.AddComponent<Camera>();
                    uiCam.enabled = false;
                    uiCam.fieldOfView = cam.fieldOfView; uiCam.nearClipPlane = 0.05f; uiCam.farClipPlane = 10f;
                    uiCam.cullingMask = 1 << 5;
                    uiCam.clearFlags = CameraClearFlags.SolidColor;
                    uiCam.backgroundColor = new Color(0f, 0f, 0f, 0f);
                    uiCam.allowHDR = false; uiCam.allowMSAA = false;
                    var ud = uiGo.AddComponent<UniversalAdditionalCameraData>();
                    ud.renderPostProcessing = false; ud.renderShadows = false; ud.antialiasing = AntialiasingMode.None;
                    cam.cullingMask = prevMask & ~(1 << 5);
                }

                DiagnosticsOverlay overlay = null;
                if (qa.includeDiagnosticsOverlay)
                {
                    overlay = DiagnosticsOverlay.Create(uiCam, new DefaultPlatformServices(), null);
                    // Simulate the A16 camera cutout in landscape (left edge, ~4 % of width).
                    overlay.OverrideSafeAreaNormalized(new Rect(0.04f, 0f, 0.96f, 1f));
                }

                DrivingHud hud = null;
                if (qa.includeDrivingHud)
                {
                    var ctx = new DrivingHudContext();
                    if (qa.drivingHudReverseCamera)
                    {
                        var trailer = UnityEngine.Object.FindAnyObjectByType<TrailerBody>();
                        var rc = trailer != null ? trailer.GetComponentInChildren<ReversingCamera>(true) : null;
                        if (rc != null)
                        {
                            rc.RenderNow();
                            var revTex = rc.Texture;
                            ctx.ReverseCameraTexture = () => revTex;
                            ctx.ReverseCameraLabel = () => "KAMERA COFANIA (naczepa)";
                        }
                    }
                    if (qa.drivingHudMirrorInsets)
                    {
                        foreach (var mir in UnityEngine.Object.FindObjectsByType<RenderTextureMirror>(FindObjectsSortMode.None))
                        {
                            var mt = mir.Texture;
                            if (mir.phase == 0) ctx.LeftMirrorTexture = () => mt; else ctx.RightMirrorTexture = () => mt;
                        }
                    }
                    hud = DrivingHud.Create(uiCam, ctx);
                    hud.OverrideSafeAreaNormalized(new Rect(0.04f, 0f, 0.96f, 1f));
                    hud.SetTelemetryVisible(qa.drivingHudTelemetry);
                    hud.RefreshNow();
                }

                var prevTarget = cam.targetTexture;
                cam.enabled = true;
                var world = RenderToPixels(cam, width, height, out _);
                Color32[] pixels = world;
                if (ui)
                {
                    // Canvas roots must be on the UI layer for the UI-only camera; the camera must be enabled for canvases.
                    if (hud != null) SetLayer(hud.transform, 5);
                    if (overlay != null) SetLayer(overlay.transform, 5);
                    uiCam.enabled = true;
                    var over = RenderToPixels(uiCam, width, height, out _, () =>
                    {
                        // Lay the canvases out for the capture resolution (the camera now targets the texture).
                        if (overlay != null) overlay.RefreshNow();
                        Canvas.ForceUpdateCanvases();
                    });
                    for (int i = 0; i < pixels.Length; i++)
                    {
                        var u = over[i];
                        int inv = 255 - u.a;
                        pixels[i] = new Color32((byte)Mathf.Min(255, u.r + world[i].r * inv / 255), (byte)Mathf.Min(255, u.g + world[i].g * inv / 255),
                            (byte)Mathf.Min(255, u.b + world[i].b * inv / 255), 255);
                    }
                }
                var tex = new Texture2D(width, height, TextureFormat.RGBA32, false);
                tex.SetPixels32(pixels);
                tex.Apply();

                string file = Path.Combine(outDir, qa.id + ".png");
                File.WriteAllBytes(file, tex.EncodeToPNG());
                Debug.Log($"[VISUALQA] {qa.id} → {file}");
                rendered++;

                cam.targetTexture = prevTarget;
                cam.enabled = wasEnabled;
                cam.cullingMask = prevMask;
                if (uiCam != null) UnityEngine.Object.DestroyImmediate(uiCam.gameObject);
                qa.gameObject.SetActive(wasActive);
                UnityEngine.Object.DestroyImmediate(tex);
                if (hud != null) UnityEngine.Object.DestroyImmediate(hud.gameObject);
                if (overlay != null || hud != null)
                {
                    var es = UnityEngine.Object.FindAnyObjectByType<UnityEngine.EventSystems.EventSystem>();
                    if (es != null) UnityEngine.Object.DestroyImmediate(es.gameObject);
                    if (overlay != null) UnityEngine.Object.DestroyImmediate(overlay.gameObject);
                }
            }
            return rendered;
        }

        static void SetLayer(Transform t, int layer)
        {
            t.gameObject.layer = layer;
            for (int i = 0; i < t.childCount; i++) SetLayer(t.GetChild(i), layer);
        }

        /// <summary>Renders a camera into a temporary sRGB target and reads the pixels back (bottom-up rows).</summary>
        static Color32[] RenderToPixels(Camera cam, int width, int height, out int count, Action beforeRender = null)
        {
            var rt = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB) { antiAliasing = 1 };
            var prev = cam.targetTexture;
            cam.targetTexture = rt;
            beforeRender?.Invoke();
            cam.Render();
            var prevActive = RenderTexture.active;
            RenderTexture.active = rt;
            var tex = new Texture2D(width, height, TextureFormat.RGBA32, false);
            tex.ReadPixels(new Rect(0, 0, width, height), 0, 0);
            tex.Apply();
            RenderTexture.active = prevActive;
            cam.targetTexture = prev;
            var px = tex.GetPixels32();
            count = px.Length;
            UnityEngine.Object.DestroyImmediate(tex);
            rt.Release();
            UnityEngine.Object.DestroyImmediate(rt);
            return px;
        }
    }
}
