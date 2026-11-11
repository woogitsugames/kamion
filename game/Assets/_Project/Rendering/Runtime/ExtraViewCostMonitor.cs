using System;
using System.Diagnostics;
using Game.Core;
using UnityEngine;
using UnityEngine.Profiling;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Debug = UnityEngine.Debug;

namespace Game.Rendering
{
    /// <summary>
    /// ADR 0068: cost of the fixed passes (vehicle mirrors, reflection-capture faces, main-light shadow map) per frame for
    /// the [DIAG] line (<see cref="ExtraViewStats"/>), and an interleaved on-device A/B of one pass (launch argument
    /// <c>rq_ab</c>), so a single run on the phone decides whether a change pays off.
    /// <para>
    /// CPU: main-thread time between beginCameraRendering and endCameraRendering of each camera (culling, render-graph
    /// record, submit), classified by <see cref="IExtraViewCamera"/>; works in release players. GPU per pass: a
    /// CustomSampler around the extra views and URP's "Draw Main Light Shadowmap" pass read through Recorder - Unity
    /// collects these only in development players, release players print "-". The release-player GPU number is the A/B:
    /// <c>rq_ab &lt;key&gt;</c> alternates the shipping configuration (A) and a variant (B) every <c>rq_ab_period</c> s
    /// (default 4) and logs FrameTimingManager GPU / CPU-main percentiles per window ([PASSAB] lines, CSV column ab).
    /// Keys: mirrors (B = no mirror renders), mirrorcfg (B = pre-0068 mirror configuration), mirrorlod (B = mirrors at the
    /// main-view LOD), envcap (B = no capture faces), shadows (B = shadow distance 0), shadowcasc (B = one cascade fewer).
    /// Use with a fixed render scale (rq_scale) and rq_pacing 0, otherwise the adaptive controller reacts to the toggling.
    /// </para>
    /// No allocation per frame (log lines only at window ends). Added by <see cref="QualityProfileApplier"/> in play mode.
    /// </summary>
    [DefaultExecutionOrder(1001)]
    public sealed class ExtraViewCostMonitor : MonoBehaviour
    {
        public const float WindowS = 2f;
        const string ShadowPassName = "Draw Main Light Shadowmap";

        // ---- per-camera timing ----
        long m_CamStart;
        int m_CamKind = -1;          // ExtraViewKind or -1 = main/other camera
        int m_CountFrame = -1;
        int m_FrameMirrors;
        long m_MirrorTicks, m_CaptureTicks, m_MainTicks;
        int m_MirrorRenders, m_CaptureFaces;
        int m_WindowStartFrame;
        float m_WindowStart;
        CommandBuffer m_Cmd;
        CustomSampler m_MirrorSampler, m_CaptureSampler;
        Recorder m_MirrorRec, m_CaptureRec, m_ShadowRec;
        double m_MirrorGpuNs, m_CaptureGpuNs, m_ShadowGpuNs;
        int m_GpuFrames;

        // ---- A/B ----
        string m_AbKey;
        float m_AbPeriod = 4f, m_AbSwitchAt, m_AbSettleUntil;
        bool m_AbB;
        float m_SavedShadowDistance = -1f;
        int m_SavedCascades = -1;
        float m_SavedLod = -1f, m_SavedScale = -1f, m_SavedFar = -1f;   // ADR 0106 A/B keys
        int m_SavedMask;
        Camera m_AbCam;
        Canvas[] m_Canvases;
        readonly float[] m_Gpu = new float[2048], m_Cpu = new float[2048], m_Dt = new float[2048];
        int m_N;
        readonly float[][] m_WinGpu = { new float[64], new float[64] }, m_WinCpu = { new float[64], new float[64] };
        readonly int[] m_WinCount = new int[2];
        readonly FrameTiming[] m_Timing = new FrameTiming[1];
        int m_Windows;

        void OnEnable()
        {
            RenderPipelineManager.beginCameraRendering += OnBegin;
            RenderPipelineManager.endCameraRendering += OnEnd;
            m_WindowStart = Time.realtimeSinceStartup;
            m_WindowStartFrame = Time.frameCount;
            if (Debug.isDebugBuild && SystemInfo.supportsGpuRecorder)
            {
                m_Cmd = new CommandBuffer { name = "ExtraViewCost" };
                m_MirrorSampler = CustomSampler.Create("Kamion.MirrorViews", true);
                m_CaptureSampler = CustomSampler.Create("Kamion.CaptureFaces", true);
                m_MirrorRec = m_MirrorSampler.GetRecorder();
                m_CaptureRec = m_CaptureSampler.GetRecorder();
                m_ShadowRec = Recorder.Get(ShadowPassName);
                if (m_MirrorRec.isValid) m_MirrorRec.enabled = true;
                if (m_CaptureRec.isValid) m_CaptureRec.enabled = true;
                if (m_ShadowRec.isValid) m_ShadowRec.enabled = true;
            }
            m_AbKey = RenderOverrides.Ab;
            if (!string.IsNullOrEmpty(m_AbKey))
            {
                m_AbPeriod = Mathf.Clamp(RenderOverrides.AbPeriod ?? 4f, 1f, 60f);
                m_AbB = false;
                m_AbSwitchAt = Time.realtimeSinceStartup + m_AbPeriod;
                m_AbSettleUntil = Time.realtimeSinceStartup + 0.75f;
                ExtraViewStats.AbIndex = 0;
                ExtraViewStats.AbState = m_AbKey + ":A";
                Debug.Log($"[PASSAB] start key={m_AbKey} period={m_AbPeriod:F1}s (A = shipping, B = {Describe(m_AbKey)}); " +
                          (RenderOverrides.RenderScale.HasValue && RenderOverrides.Pacing == false ? "fixed scale" : "WARNING: pass rq_scale <s> rq_pacing 0 or the adaptive scale reacts to the toggle"));
            }
        }

        void OnDisable()
        {
            RenderPipelineManager.beginCameraRendering -= OnBegin;
            RenderPipelineManager.endCameraRendering -= OnEnd;
            if (m_AbKey != null) SetB(false);
            m_Cmd?.Release();
            m_Cmd = null;
            ExtraViewStats.AbIndex = -1;
            ExtraViewStats.AbState = null;
        }

        static string Describe(string key) => key switch
        {
            "mirrors" => "no mirror renders",
            "mirrorcfg" => "pre-ADR 0068 mirrors",
            "mirrorlod" => "mirrors at main-view LOD",
            "envcap" => "no reflection-capture faces",
            "shadows" => "shadow distance 0",
            "shadowcasc" => "one shadow cascade fewer",
            // ADR 0106 (A16 Low GPU breakdown)
            "lod" => "LOD bias x0.6",
            "scale" => "render scale -0.1",
            "far" => "main camera far clip x0.5",
            "props" => "no instanced props / parked vehicles",
            "trees" => "no instanced trees / forest HLOD",
            "truck" => "main camera without the Vehicle layer (own truck, cab)",
            "hud" => "no screen-space canvases",
            "glass" => "no Kamion/Truck Glass renderers",
            "cabint" => "no Kamion/Cab Interior renderers",
            "truckext" => "no Kamion/Truck Exterior renderers",
            "cabdisp" => "no Kamion/Cab Display renderers",
            "mirrorlow" => "mirror LOD scale 0.5 (convex 0.3) as on High",
            "far80" => "main camera far clip x0.8",
            "scale5" => "render scale -0.05",
            "hlodcanopy" => "no forest HLOD canopy (URP Lit) submeshes",
            "hlodedge" => "no forest HLOD edge-wall submeshes",
            "hlod" => "no forest HLOD meshes",
            "impostor" => "no tree impostor LOD",
            "treeshadow" => "instanced trees cast no shadows",
            "treethin" => "tree thinning starts at half the distance",
            "treecard" => "tree card LOD distances x0.5",
            "glassdbg" => "Kamion/Truck Glass debug level rq_glassdbg (1 constant, 2 no film/env/spec, 3 no film, 4 no spec, 5 no fog)",
            "glassfast" => "Kamion/Truck Glass fast path toggled (_KAMION_GLASS_FAST)",
            _ => "unknown key (no change)",
        };

        void OnBegin(ScriptableRenderContext ctx, Camera cam)
        {
            int f = Time.frameCount;
            if (f != m_CountFrame) { ExtraViewStats.LastFrameMirrorRenders = m_FrameMirrors; m_FrameMirrors = 0; m_CountFrame = f; }
            m_CamKind = cam.TryGetComponent(out IExtraViewCamera ev) ? (int)ev.Kind : -1;
            if (m_CamKind == (int)ExtraViewKind.Mirror) { m_MirrorRenders++; m_FrameMirrors++; }
            else if (m_CamKind == (int)ExtraViewKind.Capture) m_CaptureFaces++;
            if (m_Cmd != null && m_CamKind >= 0)
            {
                var s = m_CamKind == (int)ExtraViewKind.Capture ? m_CaptureSampler : m_MirrorSampler;
                m_Cmd.BeginSample(s);
                ctx.ExecuteCommandBuffer(m_Cmd);
                m_Cmd.Clear();
            }
            m_CamStart = Stopwatch.GetTimestamp();
        }

        void OnEnd(ScriptableRenderContext ctx, Camera cam)
        {
            long dt = Stopwatch.GetTimestamp() - m_CamStart;
            if (m_CamKind == (int)ExtraViewKind.Mirror) m_MirrorTicks += dt;
            else if (m_CamKind == (int)ExtraViewKind.Capture) m_CaptureTicks += dt;
            else if (cam.cameraType == CameraType.Game) m_MainTicks += dt;
            if (m_Cmd != null && m_CamKind >= 0)
            {
                var s = m_CamKind == (int)ExtraViewKind.Capture ? m_CaptureSampler : m_MirrorSampler;
                m_Cmd.EndSample(s);
                ctx.ExecuteCommandBuffer(m_Cmd);
                m_Cmd.Clear();
            }
            m_CamKind = -1;
        }

        void Update()
        {
            // GPU recorders hold the previous frame's sums (development players only).
            if (m_MirrorRec != null && m_MirrorRec.isValid)
            {
                m_MirrorGpuNs += m_MirrorRec.gpuElapsedNanoseconds;
                if (m_CaptureRec.isValid) m_CaptureGpuNs += m_CaptureRec.gpuElapsedNanoseconds;
                if (m_ShadowRec.isValid) m_ShadowGpuNs += m_ShadowRec.gpuElapsedNanoseconds;
                m_GpuFrames++;
            }
            float now = Time.realtimeSinceStartup;
            if (m_AbKey != null) AbUpdate(now);
            if (now - m_WindowStart < WindowS) return;
            if (RenderOverrides.Hud == false) SetHud(false);   // ADR 0106: rq_hud 0 (canvases created later are caught here)
            int frames = Mathf.Max(1, Time.frameCount - m_WindowStartFrame);
            double msPerTick = 1000.0 / Stopwatch.Frequency;
            ExtraViewStats.MirrorRendersPerFrame = m_MirrorRenders / (float)frames;
            ExtraViewStats.MirrorCpuMs = (float)(m_MirrorTicks * msPerTick / frames);
            ExtraViewStats.CaptureFacesPerFrame = m_CaptureFaces / (float)frames;
            ExtraViewStats.CaptureCpuMs = (float)(m_CaptureTicks * msPerTick / frames);
            ExtraViewStats.MainCpuMs = (float)(m_MainTicks * msPerTick / frames);
            bool gpu = m_GpuFrames > 0;
            ExtraViewStats.MirrorGpuMs = gpu ? (float)(m_MirrorGpuNs / m_GpuFrames * 1e-6) : -1f;
            ExtraViewStats.CaptureGpuMs = gpu && m_CaptureRec.isValid ? (float)(m_CaptureGpuNs / m_GpuFrames * 1e-6) : -1f;
            ExtraViewStats.ShadowGpuMs = gpu && m_ShadowRec.isValid ? (float)(m_ShadowGpuNs / m_GpuFrames * 1e-6) : -1f;
            m_MirrorRenders = m_CaptureFaces = 0;
            m_MirrorTicks = m_CaptureTicks = m_MainTicks = 0;
            m_MirrorGpuNs = m_CaptureGpuNs = m_ShadowGpuNs = 0;
            m_GpuFrames = 0;
            m_WindowStart = now;
            m_WindowStartFrame = Time.frameCount;
        }

        // ---------------- A/B ----------------

        void AbUpdate(float now)
        {
            if (now >= m_AbSettleUntil && m_N < m_Gpu.Length)
            {
                FrameTimingManager.CaptureFrameTimings();
                float g = 0f, c = 0f;
                if (FrameTimingManager.GetLatestTimings(1, m_Timing) > 0) { g = (float)m_Timing[0].gpuFrameTime; c = (float)m_Timing[0].cpuMainThreadFrameTime; }
                m_Gpu[m_N] = g; m_Cpu[m_N] = c; m_Dt[m_N] = Time.unscaledDeltaTime * 1000f;
                m_N++;
            }
            if (now < m_AbSwitchAt) return;
            CloseWindow();
            SetB(!m_AbB);
            m_AbSwitchAt = now + m_AbPeriod;
            m_AbSettleUntil = now + 0.75f;   // pipelined frames of the previous state, RT reallocation
        }

        void CloseWindow()
        {
            int st = m_AbB ? 1 : 0;
            if (m_N >= 10)
            {
                float gp50 = P(m_Gpu, m_N, 0.5f), gp90 = P(m_Gpu, m_N, 0.9f), cp50 = P(m_Cpu, m_N, 0.5f), cp90 = P(m_Cpu, m_N, 0.9f), dp50 = P(m_Dt, m_N, 0.5f);
                Debug.Log(string.Format(System.Globalization.CultureInfo.InvariantCulture,
                    "[PASSAB] key={0} state={1} n={2} gpu_p50={3:F2} gpu_p90={4:F2} cpu_p50={5:F2} cpu_p90={6:F2} dt_p50={7:F2} mir={8:F2}/{9:F2}ms cap={10:F2}/{11:F2}ms",
                    m_AbKey, st == 0 ? "A" : "B", m_N, gp50, gp90, cp50, cp90, dp50, ExtraViewStats.MirrorRendersPerFrame, ExtraViewStats.MirrorCpuMs,
                    ExtraViewStats.CaptureFacesPerFrame, ExtraViewStats.CaptureCpuMs));
                int k = m_WinCount[st] % 64;
                m_WinGpu[st][k] = gp50; m_WinCpu[st][k] = cp50;
                m_WinCount[st]++;
                if (st == 1 && ++m_Windows % 3 == 0 && m_WinCount[0] > 0)
                {
                    int na = Mathf.Min(64, m_WinCount[0]), nb = Mathf.Min(64, m_WinCount[1]);
                    float ga = Median(m_WinGpu[0], na), gb = Median(m_WinGpu[1], nb), ca = Median(m_WinCpu[0], na), cb = Median(m_WinCpu[1], nb);
                    Debug.Log(string.Format(System.Globalization.CultureInfo.InvariantCulture,
                        "[PASSAB] summary key={0} windows A={1} B={2} gpu_p50 A={3:F2} B={4:F2} (A-B {5:+0.00;-0.00}) cpu_p50 A={6:F2} B={7:F2} (A-B {8:+0.00;-0.00})",
                        m_AbKey, na, nb, ga, gb, ga - gb, ca, cb, ca - cb));
                }
            }
            m_N = 0;
        }

        /// <summary>ADR 0106: shows / hides every screen-space overlay canvas (HUD, menus) for the GPU A/B.</summary>
        void SetHud(bool visible)
        {
            if (!visible || m_Canvases == null) m_Canvases = FindObjectsByType<Canvas>(FindObjectsInactive.Exclude, FindObjectsSortMode.None);
            foreach (var c in m_Canvases)
                if (c != null && c.isRootCanvas && c.renderMode == RenderMode.ScreenSpaceOverlay) c.enabled = visible;
        }

        /// <summary>ADR 0106: disables (B) / re-enables (A) the enabled renderers whose first material uses the shader (GPU A/B
        /// per vehicle shader). Renderer.enabled, not forceRenderingOff: the mirrors toggle the latter on the cab interior.</summary>
        readonly System.Collections.Generic.List<Renderer> m_AbOff = new System.Collections.Generic.List<Renderer>();
        bool m_AbLogged;
        int m_GlassShip = -1;

        /// <summary>ADR 0106: which renderers of the A/B shader the main camera drew last frame, and their screen share.</summary>
        static void LogRenderer(Renderer r)
        {
            var cam = ViewCameraResolver.Resolve(null);
            float share = 0f;
            if (cam != null && r.isVisible)
            {
                var b = r.bounds;
                Vector2 mn = new Vector2(1e9f, 1e9f), mx = new Vector2(-1e9f, -1e9f);
                bool behind = false;
                for (int k = 0; k < 8; k++)
                {
                    var c = b.center + Vector3.Scale(b.extents, new Vector3((k & 1) == 0 ? -1 : 1, (k & 2) == 0 ? -1 : 1, (k & 4) == 0 ? -1 : 1));
                    var v = cam.WorldToViewportPoint(c);
                    if (v.z <= 0f) behind = true;
                    mn = Vector2.Min(mn, v); mx = Vector2.Max(mx, v);
                }
                mn = Vector2.Max(mn, Vector2.zero); mx = Vector2.Min(mx, Vector2.one);
                share = behind ? -1f : Mathf.Max(0f, mx.x - mn.x) * Mathf.Max(0f, mx.y - mn.y);
            }
            var lg = r.GetComponentInParent<LODGroup>();
            Debug.Log($"[PASSAB] renderer '{r.name}' visible={r.isVisible} bboxShare={share:F2} layer={r.gameObject.layer} lodGroup={(lg != null ? lg.name : "-")} mats={r.sharedMaterials.Length}");
        }

        void SetShaderRenderers(string shader, bool off)
        {
            if (!off) { foreach (var r in m_AbOff) if (r != null) r.enabled = true; m_AbOff.Clear(); return; }
            foreach (var r in FindObjectsByType<Renderer>(FindObjectsInactive.Exclude, FindObjectsSortMode.None))
            {
                var m = r.sharedMaterial;
                if (r.enabled && m != null && m.shader != null && m.shader.name == shader)
                {
                    if (!m_AbLogged) LogRenderer(r);
                    r.enabled = false; m_AbOff.Add(r);
                }
            }
            m_AbLogged = true;
        }

        static readonly float[] s_Tmp = new float[2048];

        static float P(float[] a, int n, float q)
        {
            Array.Copy(a, s_Tmp, n);
            Array.Sort(s_Tmp, 0, n);
            return s_Tmp[Mathf.Clamp(Mathf.CeilToInt(q * n) - 1, 0, n - 1)];
        }

        static float Median(float[] a, int n) => P(a, n, 0.5f);

        void SetB(bool b)
        {
            m_AbB = b;
            ExtraViewStats.AbIndex = b ? 1 : 0;
            ExtraViewStats.AbState = m_AbKey + (b ? ":B" : ":A");
            var urp = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
            switch (m_AbKey)
            {
                case "mirrors": MirrorOverrides.Suspended = b; break;
                case "mirrorcfg": MirrorOverrides.Legacy = b; break;
                case "mirrorlod": MirrorOverrides.LodScale = b ? 1f : (float?)null; break;
                case "envcap": VehicleReflectionCapture.Paused = b; break;
                case "shadows":
                    if (urp == null) break;
                    if (b) { m_SavedShadowDistance = urp.shadowDistance; urp.shadowDistance = 0f; }
                    else if (m_SavedShadowDistance >= 0f) { urp.shadowDistance = m_SavedShadowDistance; m_SavedShadowDistance = -1f; }
                    break;
                case "lod":
                    if (b) { m_SavedLod = QualitySettings.lodBias; QualitySettings.lodBias = m_SavedLod * 0.6f; }
                    else if (m_SavedLod > 0f) { QualitySettings.lodBias = m_SavedLod; m_SavedLod = -1f; }
                    break;
                case "scale":
                    if (urp == null) break;
                    if (b) { m_SavedScale = urp.renderScale; urp.renderScale = Mathf.Max(0.3f, m_SavedScale - 0.1f); }
                    else if (m_SavedScale > 0f) { urp.renderScale = m_SavedScale; m_SavedScale = -1f; }
                    break;
                case "far":
                    if (b) { m_AbCam = ViewCameraResolver.Resolve(null); if (m_AbCam != null) { m_SavedFar = m_AbCam.farClipPlane; m_AbCam.farClipPlane = m_SavedFar * 0.5f; } }
                    else if (m_AbCam != null && m_SavedFar > 0f) { m_AbCam.farClipPlane = m_SavedFar; m_SavedFar = -1f; }
                    break;
                case "truck":
                    if (b) { m_AbCam = ViewCameraResolver.Resolve(null); if (m_AbCam != null) { m_SavedMask = m_AbCam.cullingMask; m_AbCam.cullingMask &= ~(1 << LayerMask.NameToLayer("Vehicle")); } }
                    else if (m_AbCam != null && m_SavedMask != 0) { m_AbCam.cullingMask = m_SavedMask; m_SavedMask = 0; }
                    break;
                case "props": RenderOverrides.AbPropsOff = b; break;
                case "trees": RenderOverrides.AbTreesOff = b; break;
                case "hud": SetHud(!b); break;
                case "glass": SetShaderRenderers("Kamion/Truck Glass", b); break;
                case "cabint": SetShaderRenderers("Kamion/Cab Interior", b); break;
                case "truckext": SetShaderRenderers("Kamion/Truck Exterior", b); break;
                case "cabdisp": SetShaderRenderers("Kamion/Cab Display", b); break;
                case "mirrorlow": MirrorOverrides.LodScale = b ? 0.5f : (float?)null; break;
                case "far80":
                    if (b) { m_AbCam = ViewCameraResolver.Resolve(null); if (m_AbCam != null) { m_SavedFar = m_AbCam.farClipPlane; m_AbCam.farClipPlane = m_SavedFar * 0.8f; } }
                    else if (m_AbCam != null && m_SavedFar > 0f) { m_AbCam.farClipPlane = m_SavedFar; m_SavedFar = -1f; }
                    break;
                case "scale5":
                    if (urp == null) break;
                    if (b) { m_SavedScale = urp.renderScale; urp.renderScale = Mathf.Max(0.3f, m_SavedScale - 0.05f); }
                    else if (m_SavedScale > 0f) { urp.renderScale = m_SavedScale; m_SavedScale = -1f; }
                    break;
                case "hlodcanopy": RenderOverrides.AbHlodPart = b ? 1 : 0; break;
                case "hlodedge": RenderOverrides.AbHlodPart = b ? 2 : 0; break;
                case "hlod": RenderOverrides.AbHlodOff = b; break;
                case "impostor": RenderOverrides.AbImpostorOff = b; break;
                case "treeshadow": RenderOverrides.AbTreeShadowOff = b; break;
                case "treethin": RenderOverrides.AbTreeThinScale = b ? 0.5f : 1f; break;
                case "treecard": RenderOverrides.AbTreeCardScale = b ? 0.5f : 1f; break;
                case "glassdbg": Shader.SetGlobalFloat("_KamionGlassDebug", b ? (RenderOverrides.GlassDebug ?? 1) : 0f); break;
                case "glassfast":
                    if (m_GlassShip < 0) m_GlassShip = Shader.IsKeywordEnabled("_KAMION_GLASS_FAST") ? 1 : 0;
                    if ((m_GlassShip == 1) ^ b) Shader.EnableKeyword("_KAMION_GLASS_FAST"); else Shader.DisableKeyword("_KAMION_GLASS_FAST");
                    break;
                case "shadowcasc":
                    if (urp == null) break;
                    if (b) { m_SavedCascades = urp.shadowCascadeCount; urp.shadowCascadeCount = Mathf.Max(1, m_SavedCascades - 1); }
                    else if (m_SavedCascades > 0) { urp.shadowCascadeCount = m_SavedCascades; m_SavedCascades = -1; }
                    break;
            }
        }
    }
}
