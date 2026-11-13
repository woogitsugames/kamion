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
                string lighting = EditorTools.Arg("-qaLighting", null);
                string only = EditorTools.Arg("-qaCameras", null);
                // ADR 0043 option (c) A/B: phone-style white-balance adaptation strength (not a default).
                string wb = EditorTools.Arg("-qaWbAdapt", null);
                if (!string.IsNullOrEmpty(wb)) EnvironmentLighting.WhiteBalanceOverride = float.Parse(wb, System.Globalization.CultureInfo.InvariantCulture);
                int count = Render(scene, w, h, tier, outDir, lighting, only);
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

        [MenuItem("Kamion/Visual QA/Render WorldC control cameras")]
        static void MenuRenderWorld() =>
            Render("WorldC", 2340, 1080, "Medium", Path.Combine(EditorTools.RepoRoot, "artifacts", "visual-qa", "WorldC"));

        [MenuItem("Kamion/Visual QA/Render DrivingLab control cameras")]
        static void MenuRenderLab() =>
            Render("DrivingLab", 2340, 1080, "Medium", Path.Combine(EditorTools.RepoRoot, "artifacts", "visual-qa", "DrivingLab"));

        public static int Render(string sceneName, int width, int height, string tier, string outDir, string lighting = null, string onlyCameras = null)
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

            // Look development (ADR 0010): lighting preset and the tier's camera-side settings (post, AA, far clip).
            var env = UnityEngine.Object.FindAnyObjectByType<EnvironmentLighting>();
            if (env != null)
            {
                if (!string.IsNullOrEmpty(lighting) && !env.SetPreset(lighting)) throw new ArgumentException("unknown lighting preset " + lighting);
                env.Apply();
            }
            var profile = QualityProfile.Load();
            QualityProfile.Tier tierSettings = default;
            bool hasTier = profile != null && profile.TryGet(tier, out tierSettings);
            // Ablation renders in the editor (same keys as the phone launch overrides): -qaRq "rq_hlod=0,rq_trees=0".
            string rq = EditorTools.Arg("-qaRq", null);

            if (hasTier && !string.IsNullOrEmpty(rq))
            {
                var kv = rq.Split(',').Select(s => s.Split('=')).Where(p => p.Length == 2).ToDictionary(p => p[0].Trim(), p => p[1].Trim());
                Debug.Log("[VISUALQA] overrides: " + RenderOverrides.Parse(k => kv.TryGetValue(k, out var v) ? v : null));
                tierSettings = RenderOverrides.ApplyTo(tierSettings);
            }
            // The world volume carries the tonemapper; EnvironmentLighting adds a runtime look-grading volume (D23).
            var volume = UnityEngine.Object.FindObjectsByType<UnityEngine.Rendering.Volume>(FindObjectsSortMode.None)
                .FirstOrDefault(v => v.sharedProfile != null && v.sharedProfile.Has<UnityEngine.Rendering.Universal.Tonemapping>());
            var applier = UnityEngine.Object.FindAnyObjectByType<QualityProfileApplier>(FindObjectsInactive.Include);
            var worldTextures = applier != null ? applier.worldTextures : null;
            string[] filter = string.IsNullOrEmpty(onlyCameras) ? null : onlyCameras.Split(',');

            // -qaGate3 <gate3_cameras.json>: adds the Stage 3 gate cameras (same code as the phone's qacam_set=gate3,
            // re-seated on the road collision) so scripts/gate3-evidence.ps1 can render them in the editor.
            string gate3Json = EditorTools.Arg("-qaGate3", null);
            // Colliders are saved disabled and cooked by the player at load; do the same so the gate cameras seat and the
            // contact shadows ray-cast onto the road like on the phone (r5 E-N1: the edit-mode wheel-plane fallback hid the
            // trailer patch under the asphalt).
            foreach (var ck in UnityEngine.Object.FindObjectsByType<Game.World.WorldCollisionCooker>(FindObjectsInactive.Include, FindObjectsSortMode.None)) ck.Cook();
            Physics.SyncTransforms();
            if (!string.IsNullOrEmpty(gate3Json))
            {
                Game.Gameplay.Gate3Cameras.CreateAll(UnityEngine.Object.FindAnyObjectByType<Game.World.WorldRegionRoot>(), null, File.ReadAllText(gate3Json));
            }
            var cams = UnityEngine.Object.FindObjectsByType<ControlCamera>(FindObjectsInactive.Include, FindObjectsSortMode.None)
                .Where(c => filter == null || filter.Any(f => Game.Gameplay.Gate3Cameras.Norm(f) == Game.Gameplay.Gate3Cameras.Norm(c.id)))
                .OrderBy(c => c.id, StringComparer.Ordinal).ToArray();
            int msaa = 1; float scale = 1f;
            if (hasTier)
            {
                UnityEngine.Rendering.Universal.Tonemapping tm = null;
                foreach (var qa in cams)
                {
                    // Keep the authored far clip of lab cameras when it is shorter than the tier's.
                    var c = qa.GetComponent<Camera>();
                    float far = c.farClipPlane;
                    QualityProfileApplier.Apply(tierSettings, c, volume, worldTextures, ref tm);
                    c.farClipPlane = Mathf.Min(far, tierSettings.cameraFarClip);
                }
                // ADR 0010 A/B: -qaTonemap Neutral|ACES|None overrides the tier's tonemapper for comparison renders.
                string tmArg = EditorTools.Arg("-qaTonemap", null);
                if (tm != null && !string.IsNullOrEmpty(tmArg) && Enum.TryParse(tmArg, true, out UnityEngine.Rendering.Universal.TonemappingMode tmMode))
                {
                    tm.mode.value = tmMode;
                    tm.active = tmMode != UnityEngine.Rendering.Universal.TonemappingMode.None;
                }
                msaa = Mathf.Max(1, tierSettings.msaa);
                scale = tierSettings.renderScale;
                // -qaRenderScale 0.80: render at another scale than the tier's (ADR 0046 adaptive floor, wire / AA checks)
                if (float.TryParse(EditorTools.Arg("-qaRenderScale", ""), System.Globalization.NumberStyles.Float,
                        System.Globalization.CultureInfo.InvariantCulture, out float rsArg) && rsArg > 0.1f && rsArg <= 2f)
                    scale = rsArg;
            }
            var stats = new System.Text.StringBuilder();
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
                // Art truck (A7): tier binding, lamp state and the cab fill for this camera (LateUpdate does not run here).
                foreach (var rig in UnityEngine.Object.FindObjectsByType<TruckVisualRig>(FindObjectsSortMode.None)) rig.Apply();
                // ADR 0175 evidence: -qaTruckLamps rearfog,hazard,low forces lamp groups on for the render (default: solver state).
                // ADR 0178 lamp-hue check: "brake" lights the stop lamps; KAMION_QA_LAMPS (env) is accepted as the same list.
                string lampSet = EditorTools.Arg("-qaTruckLamps", "") + "," + (System.Environment.GetEnvironmentVariable("KAMION_QA_LAMPS") ?? "");
                foreach (var tl in UnityEngine.Object.FindObjectsByType<TruckLights>(FindObjectsSortMode.None))
                {
                    if (lampSet.Contains("low") || lampSet.Contains("rearfog")) tl.forceLowBeam = true;
                    if (lampSet.Contains("rearfog")) tl.rearFog = true;
                    if (lampSet.Contains("brake")) tl.forceBrake = true;
                    if (lampSet.Contains("hazard")) { tl.indicatorLever = 2; tl.flasherLit = true; }
                    tl.Refresh();
                }
                // ADR 0181 r2 (review s20 P1-3): camera ids ending in "-bobtail" show the tractor without its trailer (the
                // tractor's rear plate and plate lamp sit under the coupled trailer); its renderers are restored after the frame.
                var bobtailHidden = new System.Collections.Generic.List<Renderer>();
                if (qa.id.EndsWith("-bobtail", StringComparison.Ordinal))
                    foreach (var tb in UnityEngine.Object.FindObjectsByType<TrailerBody>(FindObjectsSortMode.None))
                        foreach (var r in tb.GetComponentsInChildren<Renderer>())
                            if (r.enabled) { r.enabled = false; bobtailHidden.Add(r); }
                // Live cab screens (cluster, navigation, DIN) drawn from the (parked) vehicle state for this light.
                foreach (var vb in UnityEngine.Object.FindObjectsByType<VehicleBody>(FindObjectsSortMode.None))
                {
                    var screens = Game.Gameplay.CabScreensInstaller.Install(vb);
                    if (screens == null) continue;
                    screens.RenderNow();
                    Debug.Log($"[VISUALQA] cab screens {vb.name}: refresh {screens.LastCpuMs:F3} ms CPU, cluster {screens.Cluster.VertexCount} verts, nav {screens.Nav.VertexCount} verts, night={screens.State.Night}, clock={screens.State.ClockMinutes / 60:D2}:{screens.State.ClockMinutes % 60:D2}");
                }
                // A8: contact shadows, the vehicle reflection capture and the dusk street-lamp lights (no LateUpdate here).
                ContactShadowCaster.RefreshAll();
                for (int ci = 0; ci < ContactShadowCaster.Count; ci++)
                {
                    var csc = ContactShadowCaster.Get(ci);
                    Debug.Log($"[QA] contact shadow {csc.name}: {csc.LastVertices} vertices, {csc.LastHits} ground hits; {csc.LastDiagnostics}");
                }
                if (VehicleReflectionCapture.Active != null) VehicleReflectionCapture.Active.RenderAllNow();
                // StreetLamps is added with HideFlags.DontSave, which FindObjectsByType skips (ADR 0062: the QA frames never
                // refreshed the lamp lights / pools before): take it from the EnvironmentLighting object.
                var lampsHost = UnityEngine.Object.FindAnyObjectByType<EnvironmentLighting>();
                var lamps = lampsHost != null ? lampsHost.GetComponent<StreetLamps>() : null;
                if (lamps != null) lamps.RefreshLights(cam);
                Debug.Log("[QA] street lamps: " + StreetLamps.Diagnostics);
                // -qaCabFill off: A/B frames without the cab fill and the cab-view lift (A7 before/after).
                if (EditorTools.Arg("-qaCabFill", "on") == "off")
                {
                    Shader.SetGlobalVector("_CabFill", Vector4.zero);
                    Shader.SetGlobalFloat("_CabGain", 1f);
                }
                else foreach (var cl in UnityEngine.Object.FindObjectsByType<CabInteriorLighting>(FindObjectsSortMode.None))
                {
                    // -qaCabView none: the phone path before ADR 0044 r9 (Camera.main null under qacam -> no cab-view
                    // state, A/B of the phone/editor mismatch). The build's per-frame path is RefreshForView (EditMode
                    // CabViewCameraTests); here the camera is passed explicitly.
                    if (EditorTools.Arg("-qaCabView", "explicit") == "none") cl.Refresh(null);
                    else cl.Refresh(cam);
                    Debug.Log($"[QA] cab light {qa.id}: fill {cl.LastFill.ToString("F4")} gain {cl.LastGain:F2} (meter {cl.LastMeterEv:F2} EV)");
                }
                // REVIEW r6 W-P0 measurement: -qaWires off hides the power-line conductors, -qaWires solid draws them at
                // full opacity in black (alpha = coverage of the >= 1.2 px core only); the differences of the three
                // renders give the expected wire path and the drawn wire (gaps per 100 px, wires-streaks-v2 evidence).
                string wiresArg = EditorTools.Arg("-qaWires", "on");
                if (wiresArg == "off" || wiresArg == "solid")
                    foreach (var r in UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                    {
                        var mats = r.sharedMaterials;
                        bool any = false;
                        for (int mi = 0; mi < mats.Length; mi++)
                        {
                            if (mats[mi] == null || mats[mi].shader == null || mats[mi].shader.name != "Kamion/World Wire") continue;
                            var g = new Material(mats[mi]) { hideFlags = HideFlags.DontSave };
                            if (wiresArg == "off") g.SetFloat("_MaxAlpha", 0f);
                            else { g.SetFloat("_MaxAlpha", 1f); g.SetFloat("_AlphaGamma", 0f); g.SetVector("_BaseColor", Vector4.zero); }
                            mats[mi] = g; any = true;
                        }
                        if (any) r.sharedMaterials = mats;
                    }
                // Parapet run-off A/B: -qaRunoff off renders the hall walls without the _RUNOFF streak layer.
                if (EditorTools.Arg("-qaRunoff", "on") == "off")
                    foreach (var r in UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                    {
                        var mats = r.sharedMaterials;
                        bool any = false;
                        for (int mi = 0; mi < mats.Length; mi++)
                        {
                            if (mats[mi] == null || !mats[mi].IsKeywordEnabled("_RUNOFF")) continue;
                            var g = new Material(mats[mi]) { hideFlags = HideFlags.DontSave };
                            g.DisableKeyword("_RUNOFF");
                            mats[mi] = g; any = true;
                        }
                        if (any) r.sharedMaterials = mats;
                    }
                // ADR 0043 diagnostic: -qaNoGlass leaves only the grey Fresnel loss of the glazing (no body absorption,
                // grime, film or interior reflection), so sky-through-glass can be compared with the real glass in one frame.
                if (EditorTools.Arg("-qaNoGlass", null) == "1")
                    foreach (var r in UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                    {
                        var mats = r.sharedMaterials;
                        bool any = false;
                        for (int mi = 0; mi < mats.Length; mi++)
                        {
                            if (mats[mi] == null || mats[mi].shader == null || mats[mi].shader.name != "Kamion/Truck Glass") continue;
                            var g = new Material(mats[mi]) { hideFlags = HideFlags.DontSave };
                            g.SetFloat("_Opacity", 0f); g.SetFloat("_Grime", 0f); g.SetFloat("_Wiper", 0f);
                            g.SetVector("_InteriorAlbedo", Vector4.zero);
                            mats[mi] = g; any = true;
                        }
                        if (any) { r.sharedMaterials = mats; Debug.Log($"[QA] no-glass: {r.name} enabled={r.enabled} visible={r.isVisible} layer={r.gameObject.layer}"); }
                    }

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
                            if (!mir.main) continue;
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
                var world = RenderToPixels(cam, width, height, out _, null, msaa, scale);
                stats.AppendLine(SceneStats.Estimate(cam, hasTier ? tierSettings.shadowDistance : QualitySettings.shadowDistance,
                    hasTier ? tierSettings.shadowCascades : 1, qa.id));
                // -qaTimeFrames N: N more renders of this camera at the tier's size / MSAA, wall time with a 1-pixel readback
                // at the end (GPU-synchronised): an editor-GPU estimate of the frame cost for A/B comparisons (ADR 0023).
                int timeN = int.Parse(EditorTools.Arg("-qaTimeFrames", "0"));
                if (timeN > 0)
                {
                    int tw = Mathf.RoundToInt(width * scale), th = Mathf.RoundToInt(height * scale);
                    var trt = new RenderTexture(tw, th, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB) { antiAliasing = msaa };
                    var one = new Texture2D(1, 1, TextureFormat.RGBA32, false);
                    cam.targetTexture = trt;
                    void Sync() { RenderTexture.active = trt; one.ReadPixels(new Rect(0, 0, 1, 1), 0, 0); one.Apply(); RenderTexture.active = null; }
                    cam.Render(); Sync();
                    var sw = System.Diagnostics.Stopwatch.StartNew();
                    for (int k = 0; k < timeN; k++) cam.Render();
                    Sync();
                    double ms = sw.Elapsed.TotalMilliseconds / timeN;
                    cam.targetTexture = null;
                    trt.Release(); UnityEngine.Object.DestroyImmediate(trt); UnityEngine.Object.DestroyImmediate(one);
                    stats.AppendLine($"  {qa.id} editor frame time: {ms:F2} ms over {timeN} renders ({tw}x{th}, msaa {msaa}, {SystemInfo.graphicsDeviceName})");
                    Debug.Log($"VISUALQA_TIMING {qa.id} {ms:F3}");
                }
                var wi = Game.World.WorldInstances.Last;
                if (wi.Draws > 0)
                    stats.AppendLine($"  {qa.id} instanced (props+trees): draws {wi.Draws}, instances {wi.Instances}, triangles {wi.Triangles / 1000}k, cells {wi.VisibleCells}, forest HLOD cells {wi.HlodCells}, trianglesExact {wi.Triangles}");
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
                        if (hud != null) hud.RefreshNow();   // adaptive layout (ADR 0079) follows the capture size
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
                // -qaEnvDump 1 (ADR 0056): the vehicle reflection cube used for this frame -> <id>_envcube.png (6 faces).
                if (EditorTools.Arg("-qaEnvDump", "0") == "1" && VehicleReflectionCapture.Active != null)
                    VehicleReflectionCapture.Active.DumpStrip(Path.Combine(outDir, qa.id + "_envcube.png"));
                // -qaMask <renderer>[:<slot>][;...]: one more render of the same camera with the matching renderer slots
                // drawn flat magenta (depth and every other surface unchanged) -> <id>_mask.png, so a measurement script
                // can select exactly e.g. the steering-wheel rim (STEERING_WHEEL:MI_Cab_Leather) instead of a hand box.
                string maskSpec = EditorTools.Arg("-qaMask", null);
                if (!string.IsNullOrEmpty(maskSpec)) WriteMask(cam, width, height, msaa, scale, maskSpec, Path.Combine(outDir, qa.id + "_mask.png"));

                cam.targetTexture = prevTarget;
                cam.enabled = wasEnabled;
                foreach (var r in bobtailHidden) r.enabled = true;
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
            string lightName = lighting ?? "scene";
            if (stats.Length > 0) File.WriteAllText(Path.Combine(outDir, "stats.txt"), $"tier={tier} lighting={lightName} msaa={msaa} renderScale={scale.ToString(System.Globalization.CultureInfo.InvariantCulture)}" + System.Environment.NewLine + stats);
            return rendered;
        }

        static void WriteMask(Camera cam, int width, int height, int msaa, float scale, string spec, string file)
        {
            var sh = Shader.Find("Universal Render Pipeline/Unlit");
            var flat = new Material(sh) { hideFlags = HideFlags.DontSave };
            flat.SetColor("_BaseColor", new Color(1f, 0f, 1f, 1f));
            var saved = new System.Collections.Generic.List<(Renderer r, Material[] m)>();
            int slots = 0;
            foreach (var part in spec.Split(';'))
            {
                var kv = part.Split(':');
                string rn = kv[0], sn = kv.Length > 1 ? kv[1] : null;
                foreach (var r in UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                {
                    if (!r.name.Contains(rn)) continue;
                    var mats = r.sharedMaterials;
                    var copy = (Material[])mats.Clone();
                    bool any = false;
                    for (int i = 0; i < mats.Length; i++)
                        if (mats[i] != null && (sn == null || mats[i].name.Contains(sn))) { mats[i] = flat; any = true; slots++; }
                    if (!any) continue;
                    saved.Add((r, copy));
                    r.sharedMaterials = mats;
                }
            }
            var px = RenderToPixels(cam, width, height, out _, null, msaa, scale);
            foreach (var (r, m) in saved) r.sharedMaterials = m;
            var tex = new Texture2D(width, height, TextureFormat.RGBA32, false);
            tex.SetPixels32(px);
            tex.Apply();
            File.WriteAllBytes(file, tex.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(tex);
            UnityEngine.Object.DestroyImmediate(flat);
            Debug.Log($"[VISUALQA] mask '{spec}': {slots} slots on {saved.Count} renderers ({string.Join(", ", saved.Select(x => x.r.name))}) → {file}");
        }

        static void SetLayer(Transform t, int layer)
        {
            t.gameObject.layer = layer;
            for (int i = 0; i < t.childCount; i++) SetLayer(t.GetChild(i), layer);
        }

        /// <summary>Renders a camera into a temporary sRGB target and reads the pixels back (bottom-up rows).</summary>
        /// <summary>
        /// Renders like the phone: at render scale (URP ignores the asset's render scale for render-texture targets) with
        /// the tier's MSAA on the target, then bilinear upscale to the output size (what URP's final blit does on device).
        /// </summary>
        static Color32[] RenderToPixels(Camera cam, int width, int height, out int count, Action beforeRender = null, int msaa = 1, float scale = 1f)
        {
            int sw = Mathf.Max(16, Mathf.RoundToInt(width * scale)), sh = Mathf.Max(16, Mathf.RoundToInt(height * scale));
            var src = new RenderTexture(sw, sh, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB) { antiAliasing = msaa };
            var prev = cam.targetTexture;
            cam.targetTexture = src;
            beforeRender?.Invoke();
            cam.Render();
            var rt = src;
            if (sw != width || sh != height || msaa > 1)
            {
                rt = new RenderTexture(width, height, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB) { antiAliasing = 1, filterMode = FilterMode.Bilinear };
                src.filterMode = FilterMode.Bilinear;
                Graphics.Blit(src, rt);
            }
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
            if (src != rt) { src.Release(); UnityEngine.Object.DestroyImmediate(src); }
            return px;
        }
    }
}
