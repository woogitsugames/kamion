using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Budget for the extra cameras of a vehicle (mirrors, reversing camera) per quality level
    /// (0 Low, 1 Medium, 2 High, 3 Ultra). Every extra camera is a full cull + draw on the phone, so mirrors are
    /// low resolution, render on alternating frames and only while the cab view is active. WORKING_VALUE until
    /// measured on the Galaxy A16 (docs/PERFORMANCE_BUDGETS.md).
    /// </summary>
    public static class VehicleCameraBudget
    {
        public static int Level => Mathf.Clamp(QualitySettings.GetQualityLevel(), 0, 3);
        /// <summary>Main-mirror render-texture height in pixels (width follows the glass aspect; convex mirrors scale it).</summary>
        public static int MirrorHeight => Level switch { 0 => 224, 1 => 288, 2 => 384, _ => 512 };
        /// <summary>
        /// Hard cap of mirror camera renders per frame (ADR 0042). All mirrors share it through a weighted round-robin:
        /// main mirrors (UN R46 class II) weight 1, wide-angle / kerb / front (classes IV, V, VI) weight 0.5. With all six
        /// mirrors on screen on Low each main mirror refreshes every 4th frame and each convex mirror every 8th; with only
        /// the left pair on screen, every 2nd / 3rd. Mirror cost per frame is bounded by the cap, not by the mirror count.
        /// WORKING_VALUE until measured on the Galaxy A16.
        /// </summary>
        public static int MirrorsPerFrame => Level switch { 0 => 1, 1 => 2, 2 => 3, _ => 6 };
        public static float MirrorFarClip => Level switch { 0 => 150f, 1 => 250f, _ => 400f };
        /// <summary>Convex mirrors show a small, minified image; their far clip is this fraction of MirrorFarClip.</summary>
        public const float ConvexFarClipScale = 0.5f;
        public static int ReverseCamHeight => Level switch { 0 => 180, 1 => 216, 2 => 288, _ => 360 };
        public static int ReverseCamInterval => Level <= 1 ? 2 : 1;
    }

    /// <summary>
    /// Rear-view / convex mirror: a camera at the mirror image of the design eye point looking along the reflected line
    /// of sight, rendering a low-resolution render texture shown (horizontally flipped) on the glass quad. Convex
    /// mirrors (UN R46 classes IV-VI) get the wider field of view of their radius of curvature (computed by the
    /// builder). Static geometry, not a per-frame reflection of the head position. All mirrors share one per-frame
    /// render budget (VehicleCameraBudget.MirrorsPerFrame, weighted round-robin; ADR 0042).
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public sealed class RenderTextureMirror : MonoBehaviour
    {
        /// <summary>Global switch (the driving lab turns mirrors off outside the cab view).</summary>
        public static bool GlobalEnabled = true;
        /// <summary>Render even when the glass is not on screen (the HUD shows the textures as mirror insets).</summary>
        public static bool ForceRender;

        public Renderer glass;
        /// <summary>Glass width / height (render-texture aspect).</summary>
        public float aspect = 0.55f;
        /// <summary>Order among the mirrors (main left 0, main right 1, then the convex mirrors); ties in the schedule.</summary>
        public int phase;
        /// <summary>Main mirror (class II): HUD inset, full far clip. Convex mirrors (classes IV-VI): false.</summary>
        public bool main = true;
        /// <summary>Share of the shared round-robin budget (main 1, convex 0.5).</summary>
        public float weight = 1f;
        /// <summary>Camera aspect (tan of the horizontal / vertical half field) for convex mirrors; 0 = render-texture aspect.</summary>
        public float fovAspect;
        /// <summary>Render-texture height relative to VehicleCameraBudget.MirrorHeight.</summary>
        public float resolutionScale = 1f;

        static readonly System.Collections.Generic.List<RenderTextureMirror> s_All = new System.Collections.Generic.List<RenderTextureMirror>(8);
        static MirrorScheduler s_Scheduler;
        float m_Debt;
        bool m_Candidate;

        Camera m_Cam;
        RenderTexture m_Rt;
        Material m_Mat;
        int m_Height;

        public RenderTexture Texture => m_Rt;

        Camera Cam
        {
            get
            {
                if (m_Cam == null) { m_Cam = GetComponent<Camera>(); m_Cam.enabled = false; }
                return m_Cam;
            }
        }

        void Awake() { var c = Cam; c.enabled = false; }

        void OnEnable()
        {
            if (!s_All.Contains(this)) s_All.Add(this);
            if (s_Scheduler == null && Application.isPlaying)
            {
                var go = new GameObject("MirrorScheduler") { hideFlags = HideFlags.HideAndDontSave };
                DontDestroyOnLoad(go);
                s_Scheduler = go.AddComponent<MirrorScheduler>();
            }
        }

        void OnDisable()
        {
            s_All.Remove(this);
            if (m_Cam != null) m_Cam.enabled = false;
        }

        void EnsureTarget()
        {
            int h = Mathf.Max(16, Mathf.RoundToInt(VehicleCameraBudget.MirrorHeight * resolutionScale));
            if (m_Rt != null && m_Height == h) return;
            Release();
            m_Height = h;
            int w = Mathf.Max(16, Mathf.RoundToInt(h * aspect));
            m_Rt = new RenderTexture(w, h, 16, RenderTextureFormat.ARGB32) { name = "Mirror_" + name, antiAliasing = 1, useMipMap = false };
            m_Rt.Create();
            var cam = Cam;
            cam.targetTexture = m_Rt;
            if (fovAspect > 0f) cam.aspect = fovAspect; else cam.ResetAspect();
            cam.farClipPlane = VehicleCameraBudget.MirrorFarClip * (main ? 1f : VehicleCameraBudget.ConvexFarClipScale);
            if (glass != null)
            {
                if (m_Mat == null)
                {
                    m_Mat = new Material(glass.sharedMaterial) { name = "MirrorGlass_" + name };
                    glass.sharedMaterial = m_Mat;
                }
                m_Mat.SetTexture("_BaseMap", m_Rt);
                m_Mat.SetTextureScale("_BaseMap", new Vector2(-1f, 1f));   // mirror image
                m_Mat.SetTextureOffset("_BaseMap", new Vector2(1f, 0f));
                m_Mat.SetColor("_BaseColor", new Color(0.92f, 0.93f, 0.95f, 1f)); // glass loses a little light
            }
        }

        void LateUpdate()
        {
            // Candidate this frame: mirrors on, glass on screen (or the main pair shown as HUD insets), or no image yet.
            m_Candidate = GlobalEnabled && glass != null && (main && ForceRender || glass.isVisible || m_Rt == null);
            if (m_Candidate) EnsureTarget();
            else Cam.enabled = false;
        }

        /// <summary>
        /// Picks the mirrors that render this frame (called once per frame after every mirror's LateUpdate): each
        /// candidate accrues its weight, the MirrorsPerFrame largest debts render and are reset. Cameras enabled in
        /// LateUpdate render this frame, before the main camera (they target a texture). No allocation.
        /// </summary>
        internal static void Schedule()
        {
            int cap = Mathf.Max(1, VehicleCameraBudget.MirrorsPerFrame);
            for (int i = 0; i < s_All.Count; i++)
            {
                var m = s_All[i];
                m.m_Debt = m.m_Candidate ? m.m_Debt + Mathf.Max(0.05f, m.weight) : 0f;
                m.Cam.enabled = false;
            }
            for (int k = 0; k < cap; k++)
            {
                RenderTextureMirror best = null;
                for (int i = 0; i < s_All.Count; i++)
                {
                    var m = s_All[i];
                    if (!m.m_Candidate || m.Cam.enabled) continue;
                    if (best == null || m.m_Debt > best.m_Debt || m.m_Debt == best.m_Debt && m.phase < best.phase) best = m;
                }
                if (best == null) break;
                best.Cam.enabled = true;
                best.m_Debt = 0f;
            }
        }

        /// <summary>Renders once now (visual QA in the editor, where LateUpdate does not run).</summary>
        public void RenderNow()
        {
            EnsureTarget();
            Cam.Render();
        }

        void Release()
        {
            if (m_Rt == null) return;
            if (m_Cam != null) m_Cam.targetTexture = null;
            m_Rt.Release();
            if (Application.isPlaying) Destroy(m_Rt); else DestroyImmediate(m_Rt);
            m_Rt = null;
        }

        void OnDestroy()
        {
            Release();
            if (m_Mat != null) { if (Application.isPlaying) Destroy(m_Mat); else DestroyImmediate(m_Mat); }
        }

        /// <summary>Camera settings for a cheap extra view (no shadows, no post, no MSAA, no depth/opaque copies).</summary>
        public static void ConfigureCheapCamera(Camera cam, float fov, float near, float far)
        {
            cam.enabled = false;
            cam.fieldOfView = fov;
            cam.nearClipPlane = near;
            cam.farClipPlane = far;
            cam.cullingMask = ~(1 << 5); // everything except UI
            cam.allowHDR = false;
            cam.allowMSAA = false;
            cam.useOcclusionCulling = false;
            cam.clearFlags = CameraClearFlags.Skybox;
            var urp = cam.GetComponent<UniversalAdditionalCameraData>();
            if (urp == null) urp = cam.gameObject.AddComponent<UniversalAdditionalCameraData>();
            urp.renderShadows = false;
            urp.renderPostProcessing = false;
            urp.antialiasing = AntialiasingMode.None;
            urp.requiresDepthOption = CameraOverrideOption.Off;
            urp.requiresColorOption = CameraOverrideOption.Off;
            urp.SetRenderer(0);
        }
    }

    /// <summary>Runs the shared mirror schedule after every mirror's LateUpdate.</summary>
    [DefaultExecutionOrder(32000)]
    sealed class MirrorScheduler : MonoBehaviour
    {
        void LateUpdate() => RenderTextureMirror.Schedule();
    }
}
