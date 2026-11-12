using Game.Core;
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
        /// <summary>ADR 0068: the complete pre-0068 configuration (launch argument rq_mirror_legacy / pass A/B toggler).</summary>
        static bool Legacy => MirrorOverrides.Legacy;
        /// <summary>Main-mirror render-texture height in pixels (width follows the glass aspect; convex mirrors scale it).</summary>
        public static int MirrorHeight => Mathf.RoundToInt(MirrorHeightFor(Level) * (Legacy ? 1f : MirrorOverrides.Resolution ?? MirrorOverrides.TierResolution));
        public static int MirrorHeightFor(int level) => level switch { 0 => 224, 1 => 288, 2 => 384, _ => 512 };
        /// <summary>
        /// Hard cap of mirror camera renders per frame (ADR 0042). All mirrors share it through a weighted round-robin:
        /// main mirrors (UN R46 class II) weight 1, wide-angle / kerb / front (classes IV, V, VI) weight 0.5. With all six
        /// mirrors on screen on Low each main mirror refreshes every 4th frame and each convex mirror every 8th; with only
        /// the left pair on screen, every 2nd / 3rd. Mirror cost per frame is bounded by the cap, not by the mirror count.
        /// WORKING_VALUE until measured on the Galaxy A16.
        /// </summary>
        /// <remarks>High 3 -> 2 (ADR 0046 addendum): one slot reserved for the class II pair (MainMirrorSlots), one rotating
        /// through the convex mirrors. Editor proxy: 3 mirror renders cost more CPU than the main view.</remarks>
        public static int MirrorsPerFrame => Legacy ? MirrorsPerFrameFor(Level) : Mathf.Max(1, MirrorOverrides.Cap ?? MirrorsPerFrameFor(Level));
        public static int MirrorsPerFrameFor(int level) => level switch { 0 => 1, 1 => 2, 2 => 2, _ => 6 };
        /// <summary>
        /// Slots of MirrorsPerFrame reserved for the main (class II) mirrors; the rest go to the convex mirrors first
        /// (MirrorRefreshSchedule). 0 = plain weighted round-robin (Low / Medium / Ultra unchanged). High 1: each class II
        /// mirror refreshes every 2nd frame at a steady interval, each convex mirror every 4th (all six on screen).
        /// </summary>
        public static int MainMirrorSlots => MainMirrorSlotsFor(Level);
        public static int MainMirrorSlotsFor(int level) => level == 2 ? 1 : 0;
        /// <summary>
        /// ADR 0068: High uses the due-based schedule (MirrorRefreshSchedule.StepDue) with the same cadence as ADR 0046 while
        /// driving, longer intervals for the convex mirrors when the truck stands. Low / Medium / Ultra keep the weighted
        /// round-robin (unchanged, no device measurement yet). rq_mirror_rate 0/1 overrides.
        /// </summary>
        public static bool DueSchedule => !Legacy && (MirrorOverrides.DueSchedule ?? DueScheduleFor(Level));
        public static bool DueScheduleFor(int level) => level == 2;
        /// <summary>
        /// Target refresh interval in frames per UN R46 class (2 = class II, 4 = IV, 5 = V, 6 = VI) for the due-based schedule.
        /// While driving: II 2, IV 4, V/VI 4 (= ADR 0046 High at 60 FPS: 30 / 15 / 15 Hz). Standing (speed &lt; 0.5 m/s and yaw
        /// rate &lt; 3 deg/s for 0.5 s): the mirror image does not move with the truck, IV x2, V/VI x4 (7.5 / 3.75 Hz); class
        /// II keeps 30 Hz (the mirrors checked before pulling out). Other levels follow their round-robin cadence.
        /// WORKING_VALUE (ADR 0068); the frame cost of the worst case (driving, all six on screen) is unchanged by it.
        /// </summary>
        public static float MirrorIntervalFor(int level, int r46Class, bool standing)
        {
            float b = level switch { 0 => r46Class == 2 ? 4f : 8f, 1 => r46Class == 2 ? 2f : 4f, 2 => r46Class == 2 ? 2f : 4f, _ => 1f };
            if (!standing) return b;
            return r46Class == 2 ? b : r46Class == 4 ? 2f * b : 4f * b;
        }
        /// <summary>
        /// ADR 0068: LOD-bias multiplier while a mirror camera renders (Game.Core.ExtraViewLod; LODGroups and the instanced
        /// world). A High class II texture is 384 px over 35-44 deg (≈ 9-11 px/deg) against ≈ 25 px/deg in the main view, so
        /// the pixel-equivalent multiplier is ≈ 0.35; 0.5 keeps a margin (the HUD inset shows the class II texture at about
        /// 1:1). Convex mirrors (classes IV-VI, 0.43-0.6 of the height over 60-97 deg, ≈ 3-5 px/deg): 0.3.
        /// Low / Medium / Ultra: 1 (unchanged, no device measurement). rq_mirror_lod overrides (convex = 0.6 × it).
        /// </summary>
        public static float MirrorLodScale(bool main)
        {
            if (Legacy) return 1f;
            if (MirrorOverrides.LodScale.HasValue) return Mathf.Max(0.05f, MirrorOverrides.LodScale.Value * (main ? 1f : 0.6f));
            return MirrorLodScaleFor(Level, main);
        }
        public static float MirrorLodScaleFor(int level, bool main) => level == 2 ? (main ? 0.5f : 0.3f) : 1f;
        public static float MirrorFarClip => !Legacy && MirrorOverrides.FarClip.HasValue ? Mathf.Max(20f, MirrorOverrides.FarClip.Value) : MirrorFarClipFor(Level);
        public static float MirrorFarClipFor(int level) => level switch { 0 => 150f, 1 => 250f, _ => 400f };
        /// <summary>Convex mirrors show a small, minified image; their far clip is this fraction of MirrorFarClip.</summary>
        public const float ConvexFarClipScale = 0.5f;
        public static int ReverseCamHeight => Level switch { 0 => 180, 1 => 216, 2 => 288, _ => 360 };
        public static int ReverseCamInterval => Level <= 1 ? 2 : 1;
    }

    /// <summary>
    /// Rear-view / convex mirror: a camera at the mirror image of the design eye point looking along the reflected line
    /// of sight, rendering a low-resolution texture mapped by the authored glass UVs (legacy flip is configurable). Convex
    /// mirrors (UN R46 classes IV-VI) get the wider field of view of their radius of curvature (computed by the
    /// builder). Static geometry, not a per-frame reflection of the head position. All mirrors share one per-frame
    /// render budget (VehicleCameraBudget.MirrorsPerFrame; ADR 0042 weighted round-robin, ADR 0068 due-based on High).
    /// ADR 0068: the camera renders at a lower LOD bias than the main view (<see cref="IExtraViewCamera.LodScale"/>,
    /// Game.Core.ExtraViewLod) - the field of view, position and aim are untouched (R46 fields, MirrorFieldOfVisionTests).
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public sealed class RenderTextureMirror : MonoBehaviour, IExtraViewCamera
    {
        /// <summary>Global switch (the driving lab turns mirrors off outside the cab view).</summary>
        public static bool GlobalEnabled = true;
        /// <summary>Render even when the glass is not on screen (the HUD shows the textures as mirror insets).</summary>
        public static bool ForceRender;
        /// <summary>Total mirror renders scheduled since start (telemetry: renders per frame).</summary>
        public static long RendersScheduled { get; private set; }
        /// <summary>The truck stands (ADR 0068 due-based intervals): speed &lt; 0.5 m/s and yaw rate &lt; 3 deg/s for 0.5 s.</summary>
        public static bool Standing { get; private set; }

        public Renderer glass;
        /// <summary>Glass width / height (render-texture aspect).</summary>
        public float aspect = 0.55f;
        /// <summary>Order among the mirrors (main left 0, main right 1, then the convex mirrors); ties in the schedule.</summary>
        public int phase;
        /// <summary>Main mirror (class II): HUD inset, full far clip. Convex mirrors (classes IV-VI): false.</summary>
        public bool main = true;
        /// <summary>Legacy graybox UVs need a flip. TRAKT quads already map the reflected-eye camera correctly (ADR 0104).</summary>
        public bool flipHorizontally = true;
        /// <summary>Share of the shared round-robin budget (main 1, convex 0.5).</summary>
        public float weight = 1f;
        /// <summary>Camera aspect (tan of the horizontal / vertical half field) for convex mirrors; 0 = render-texture aspect.</summary>
        public float fovAspect;
        /// <summary>Render-texture height relative to VehicleCameraBudget.MirrorHeight.</summary>
        public float resolutionScale = 1f;
        /// <summary>UN R46 class (2, 4, 5, 6) for the due-based schedule; 0 = from main / the camera name (Wide, Kerb, Front).</summary>
        public int r46Class;

        static readonly System.Collections.Generic.List<RenderTextureMirror> s_All = new System.Collections.Generic.List<RenderTextureMirror>(8);
        static MirrorRefreshSchedule.Entry[] s_Entries = new MirrorRefreshSchedule.Entry[8];
        static MirrorScheduler s_Scheduler;
        // Shared motion state (all mirrors move with the cab): sampled by the first mirror each frame.
        static int s_MotionFrame = -1;
        static float s_StandingFor;
        float m_Debt;
        bool m_Started;
        bool m_Candidate;
        Vector3 m_LastPos, m_LastFwd;
        bool m_HasLast;
        /// <summary>Frame count of the last scheduled render (diagnostics; -1 = never).</summary>
        public int LastRenderFrame { get; private set; } = -1;

        // ADR 0068 / 0112: own-cab interior renderers are omitted in every mirror. Downward views retain the exterior
        // roof through the close near plane instead of showing the seats through a clipped roof. null = not looked up yet.
        Renderer[] m_HideInMirror;
        bool[] m_PreviousHidden;
        static RenderTextureMirror s_Hiding;
        static bool s_Hooked;

        Camera m_Cam;
        RenderTexture m_Rt;
        Material m_Mat;
        int m_Height;

        public RenderTexture Texture => m_Rt;
        public ExtraViewKind Kind => ExtraViewKind.Mirror;
        public float LodScale => VehicleCameraBudget.MirrorLodScale(main);
        /// <summary>UN R46 class used by the schedule (explicit, or main = II, camera name Kerb = V, Front = VI, else IV).</summary>
        public int Class => r46Class > 0 ? r46Class : main ? 2 : name.Contains("Kerb") ? 5 : name.Contains("Front") ? 6 : 4;

        Camera Cam
        {
            get
            {
                if (m_Cam == null) { m_Cam = GetComponent<Camera>(); m_Cam.enabled = false; }
                return m_Cam;
            }
        }

        void Awake() { var c = Cam; c.enabled = false; }

        static void HookCulling()
        {
            ExtraViewLod.Hook();
            if (s_Hooked) return;
            s_Hooked = true;
            UnityEngine.Rendering.RenderPipelineManager.beginCameraRendering += OnBeginCamera;
            UnityEngine.Rendering.RenderPipelineManager.endCameraRendering += OnEndCamera;
        }

        static void OnBeginCamera(UnityEngine.Rendering.ScriptableRenderContext ctx, Camera cam)
        {
            if (s_Hiding != null) s_Hiding.SetHidden(false);
            if (!cam.TryGetComponent(out RenderTextureMirror m) || MirrorOverrides.Legacy) return;
            // The old V/VI exception exposed the dashboard and seats (review K1). The exterior shell remains visible.
            m.SetHidden(true);
        }

        static void OnEndCamera(UnityEngine.Rendering.ScriptableRenderContext ctx, Camera cam)
        {
            if (s_Hiding != null) s_Hiding.SetHidden(false);
        }

        void SetHidden(bool hide)
        {
            if (m_HideInMirror == null)
            {
                m_HideInMirror = FindInterior();
                m_PreviousHidden = new bool[m_HideInMirror.Length];
            }
            for (int i = 0; i < m_HideInMirror.Length; i++)
            {
                var renderer = m_HideInMirror[i];
                if (renderer == null) continue;
                if (hide) { m_PreviousHidden[i] = renderer.forceRenderingOff; renderer.forceRenderingOff = true; }
                else renderer.forceRenderingOff = m_PreviousHidden[i];
            }
            s_Hiding = hide ? this : null;
        }

        /// <summary>Interior renderers of the own truck (TruckVisualRig.interiorGroup), looked up once.</summary>
        Renderer[] FindInterior()
        {
            var rig = GetComponentInParent<TruckVisualRig>();
            if (rig == null || rig.interiorGroup == null) return new Renderer[0];
            var list = new System.Collections.Generic.List<Renderer>();
            foreach (var lod in rig.interiorGroup.GetLODs()) foreach (var r in lod.renderers) if (r != null && !list.Contains(r)) list.Add(r);
            return list.ToArray();
        }

        void OnEnable()
        {
            HookCulling();
            if (!s_All.Contains(this)) s_All.Add(this);
            if (s_Entries.Length < s_All.Count) System.Array.Resize(ref s_Entries, s_All.Count * 2);   // on enable only, never per frame
            if (r46Class <= 0) r46Class = Class;   // name lookup once, not per frame
            m_Started = false; m_HasLast = false;
            if (s_Scheduler == null && Application.isPlaying)
            {
                var go = new GameObject("MirrorScheduler") { hideFlags = HideFlags.HideAndDontSave };
                DontDestroyOnLoad(go);
                s_Scheduler = go.AddComponent<MirrorScheduler>();
            }
        }

        void OnDisable()
        {
            if (s_Hiding == this) SetHidden(false);
            s_All.Remove(this);
            if (m_Cam != null) m_Cam.enabled = false;
        }

        void EnsureTarget()
        {
            int h = Mathf.Max(16, Mathf.RoundToInt(VehicleCameraBudget.MirrorHeight * resolutionScale));
            var cam = Cam;
            // Also applies to existing generated prefabs, before their next TruckAssetBuilder rebuild.
            int cls = Class;
            if ((cls == 5 || cls == 6) && glass != null)
                cam.nearClipPlane = MirrorOptics.NearClipFor(cls,
                    Vector3.Distance(cam.transform.position, glass.bounds.center), MirrorOverrides.Legacy);
            // Far clip every time (cheap): the A/B toggler (rq_ab mirrorcfg) switches configurations at run time.
            cam.farClipPlane = VehicleCameraBudget.MirrorFarClip * (main ? 1f : VehicleCameraBudget.ConvexFarClipScale);
            if (m_Rt != null && m_Height == h) return;
            Release();
            m_Height = h;
            int w = Mathf.Max(16, Mathf.RoundToInt(h * aspect));
            m_Rt = new RenderTexture(w, h, 16, RenderTextureFormat.ARGB32) { name = "Mirror_" + name, antiAliasing = 1, useMipMap = false };
            m_Rt.Create();
            cam.targetTexture = m_Rt;
            if (fovAspect > 0f) cam.aspect = fovAspect; else cam.ResetAspect();
            if (glass != null)
            {
                if (m_Mat == null)
                {
                    m_Mat = new Material(glass.sharedMaterial) { name = "MirrorGlass_" + name };
                    glass.sharedMaterial = m_Mat;
                }
                m_Mat.SetTexture("_BaseMap", m_Rt);
                m_Mat.SetTextureScale("_BaseMap", new Vector2(flipHorizontally ? -1f : 1f, 1f));
                m_Mat.SetTextureOffset("_BaseMap", new Vector2(flipHorizontally ? 1f : 0f, 0f));
                m_Mat.SetColor("_BaseColor", new Color(0.92f, 0.93f, 0.95f, 1f)); // glass loses a little light
            }
        }

        void LateUpdate()
        {
            SampleMotion();
            // Candidate this frame: mirrors on, glass on screen (or the main pair shown as HUD insets), or no image yet.
            m_Candidate = GlobalEnabled && !MirrorOverrides.Suspended && glass != null && (main && ForceRender || glass.isVisible || m_Rt == null);
            if (m_Candidate) EnsureTarget();
            else Cam.enabled = false;
        }

        /// <summary>Standing detection from the mirror camera's own motion (no vehicle reference; once per frame).</summary>
        void SampleMotion()
        {
            Vector3 p = transform.position, f = transform.forward;
            float dt = Time.deltaTime;
            if (m_HasLast && dt > 1e-4f && s_MotionFrame != Time.frameCount)
            {
                s_MotionFrame = Time.frameCount;
                float speed = (p - m_LastPos).magnitude / dt;
                float yawRate = Vector3.Angle(m_LastFwd, f) / dt;
                s_StandingFor = speed < 0.5f && yawRate < 3f ? s_StandingFor + dt : 0f;
                Standing = s_StandingFor >= 0.5f;
            }
            m_LastPos = p; m_LastFwd = f; m_HasLast = true;
        }

        /// <summary>
        /// Picks the mirrors that render this frame (called once per frame after every mirror's LateUpdate) through
        /// MirrorRefreshSchedule: MirrorsPerFrame cap; High the due-based step (ADR 0068), other tiers the weighted
        /// round-robin with MainMirrorSlots reserved for class II. Cameras enabled in LateUpdate render this frame, before
        /// the main camera (they target a texture). No allocation.
        /// </summary>
        internal static void Schedule()
        {
            int count = s_All.Count;
            if (s_Entries.Length < count) System.Array.Resize(ref s_Entries, count * 2);   // safety; normally sized in OnEnable
            bool due = VehicleCameraBudget.DueSchedule;
            int level = VehicleCameraBudget.Level;
            for (int i = 0; i < count; i++)
            {
                var m = s_All[i];
                int cls = m.r46Class > 0 ? m.r46Class : m.main ? 2 : 4;
                s_Entries[i].debt = m.m_Debt;
                s_Entries[i].started = m.m_Started;
                s_Entries[i].weight = m.weight;
                s_Entries[i].phase = m.phase;
                s_Entries[i].main = m.main;
                s_Entries[i].candidate = m.m_Candidate;
                s_Entries[i].interval = VehicleCameraBudget.MirrorIntervalFor(level, cls, Standing);
                s_Entries[i].fill = cls <= 4;
            }
            int n = due
                ? MirrorRefreshSchedule.StepDue(s_Entries, count, VehicleCameraBudget.MirrorsPerFrame, !Standing)
                : MirrorRefreshSchedule.Step(s_Entries, count, VehicleCameraBudget.MirrorsPerFrame, VehicleCameraBudget.MainMirrorSlots);
            RendersScheduled += n;
            int frame = Time.frameCount;
            for (int i = 0; i < count; i++)
            {
                var m = s_All[i];
                m.m_Debt = s_Entries[i].debt;
                m.m_Started = s_Entries[i].started;
                bool on = s_Entries[i].selected;
                m.Cam.enabled = on;
                if (on) m.LastRenderFrame = frame;
            }
        }

        /// <summary>Renders once now (visual QA in the editor, where LateUpdate does not run).</summary>
        public void RenderNow()
        {
            HookCulling();
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
