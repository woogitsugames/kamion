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
        public static int MirrorHeight
        {
            get
            {
                int h = Mathf.RoundToInt(MirrorHeightFor(Level) * (Legacy ? 1f : MirrorOverrides.Resolution ?? MirrorOverrides.TierResolution));
                if (Legacy || MirrorOverrides.Resolution.HasValue) return h;
                return HeightForWindow(h, MirrorOverrides.WindowPixelHeight, MirrorOverrides.TierWindowTexelsPerPixel);
            }
        }
        /// <summary>Largest class II mirror texture height [px] (ADR 0342: a 4K window x 1.5 stays inside it).</summary>
        public const int MaxMirrorHeight = 1024;
        /// <summary>
        /// ADR 0342: texture height following the on-screen window. <paramref name="tierHeight"/> is the floor (never below the tier);
        /// <paramref name="windowPx"/> x <paramref name="texelsPerPixel"/> raises it so the glass is not magnified on a large monitor
        /// (1 = 1:1, 1.5 = supersampled). Off (returns the tier height) when either is 0. Pure.
        /// </summary>
        public static int HeightForWindow(int tierHeight, float windowPx, float texelsPerPixel)
        {
            if (windowPx <= 0f || texelsPerPixel <= 0f) return tierHeight;
            return Mathf.Clamp(Mathf.Max(tierHeight, Mathf.RoundToInt(windowPx * texelsPerPixel)), tierHeight, Mathf.Max(tierHeight, MaxMirrorHeight));
        }
        /// <summary>Largest class II texture height the tier floor may ask for (a 0.4-wide glass at 512 px width).</summary>
        public const int MaxMainMirrorHeight = 1280;
        /// <summary>
        /// ADR 0340 addendum 2: height of a class II (main) mirror texture of glass aspect <paramref name="aspect"/> (width /
        /// height): <see cref="MirrorHeight"/>, raised to the tier floor (PC High / Ultra: at least 512 x 1024 px - the
        /// critic read the 171 x 384 picture as blurred). rq_mirror_res (an explicit multiplier) and rq_mirror_legacy switch
        /// the floor off; rq_mirror_main overrides it.
        /// </summary>
        public static int MainMirrorHeight(float aspect)
        {
            int h = MirrorHeight;
            if (Legacy || MirrorOverrides.Resolution.HasValue) return h;
            if (MirrorOverrides.MainMinHeight.HasValue)
                return MainHeightFor(h, aspect, MirrorOverrides.MainMinHeight.Value / 2, MirrorOverrides.MainMinHeight.Value);
            return MainHeightFor(h, aspect, MirrorOverrides.TierMainMinWidth, MirrorOverrides.TierMainMinHeight);
        }
        /// <summary>Texture height that is at least <paramref name="height"/>, <paramref name="minHeight"/> and tall enough for
        /// <paramref name="minWidth"/> at the glass aspect; the floor itself never asks for more than
        /// <see cref="MaxMainMirrorHeight"/>. 0 / 0 = <paramref name="height"/>. Pure.</summary>
        public static int MainHeightFor(int height, float aspect, int minWidth, int minHeight)
        {
            if (minWidth <= 0 && minHeight <= 0) return height;
            int need = Mathf.Max(minHeight, aspect > 0.05f ? Mathf.CeilToInt(minWidth / aspect) : 0);
            return Mathf.Max(height, Mathf.Min(need, MaxMainMirrorHeight));
        }
        /// <summary>ADR 0340 addendum 2: the main-view grading (HDR + post-processing volume) in the mirror cameras whose
        /// picture a HUD window shows.</summary>
        public static bool MirrorPost => !Legacy && (MirrorOverrides.Post ?? MirrorOverrides.TierPost);
        /// <summary>ADR 0342: MSAA samples of the mirror textures (1 = none).</summary>
        public static int MirrorMsaa => Legacy ? 1 : NormalizeMsaa(MirrorOverrides.Msaa ?? MirrorOverrides.TierMsaa);
        public static int NormalizeMsaa(int v) => v >= 8 ? 8 : v >= 4 ? 4 : v >= 2 ? 2 : 1;
        /// <summary>ADR 0342: shadows in the mirror cameras.</summary>
        public static bool MirrorShadows => !Legacy && (MirrorOverrides.Shadows ?? MirrorOverrides.TierShadows);
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
        /// ADR 0243 (D70): with the class II mirrors shown as fixed on-screen windows (<see cref="RenderTextureMirror.ForceRender"/>)
        /// Low also uses the due-based step, without spare fill (<see cref="MirrorInsetBudget"/>). rq_mirror_rate 0 = the old
        /// round-robin (A/B), rq_mirror_legacy = the pre-0068 configuration.
        /// </summary>
        public static bool DueScheduleWith(bool insets) => !Legacy && (MirrorOverrides.DueSchedule ?? MirrorInsetBudget.DueFor(Level, insets));
        /// <summary>Spare-slot fill of the due-based step (ADR 0068 High while driving; never under the ADR 0243 Low window policy).</summary>
        public static bool FillSpare(int level, bool insets, bool standing) => MirrorInsetBudget.FillSpareFor(level, insets, standing);
        /// <summary>ADR 0243: <see cref="MirrorIntervalFor(int,int,bool)"/>, or the Low window policy (<see cref="MirrorInsetBudget"/>).</summary>
        public static float MirrorIntervalFor(int level, int r46Class, bool standing, bool insets) =>
            MirrorInsetBudget.Applies(level, insets) ? MirrorInsetBudget.Interval(r46Class, standing) : MirrorIntervalFor(level, r46Class, standing);
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
        /// <summary>ADR 0340 addendum: the class IV (wide-angle) mirrors are shown in the HUD mirror heads too, so they render
        /// although their modelled glass is off screen. Same per-frame cap and schedule as before (MirrorsPerFrame; class
        /// IV keeps its longer interval) - on the due-based tiers they take the spare slots the main pair used to fill.</summary>
        public static bool ForceWide;
        /// <summary>
        /// ADR 0283 (D84 "lusterka złe"): player adjustment of both main (class II) mirrors - the reflected view turned
        /// outward / downward by these angles [deg] (set from the HUD preferences). Like turning the glass by half the
        /// angle: less of the own cab / trailer side in the image. 0 / 0 = the built aim (TruckAssetBuilder, graybox).
        /// The 3D glass in the cab shows the same texture (no extra render).
        /// </summary>
        public static float AdjustYawOutDeg, AdjustPitchDownDeg;

        /// <summary>Local Euler offset (x = pitch down, y = yaw) of a main-mirror camera that looks back along the vehicle
        /// side. <paramref name="phase"/> 0 = left mirror (outward = vehicle -X), otherwise right (+X). The camera faces -Z,
        /// so its own +X is the vehicle -X: +yaw turns the view to the vehicle's left. Pure (EditMode test).</summary>
        public static Vector3 AdjustEuler(int phase, float yawOutDeg, float pitchDownDeg) =>
            new Vector3(pitchDownDeg, phase == 0 ? yawOutDeg : -yawOutDeg, 0f);

        /// <summary>
        /// ADR 0312 (drive-feel-s24): articulation of the coupled trailer [deg], + = trailer rear swung to the vehicle's left
        /// (a left turn); 0 = solo / straight. Set every frame by the scene (DrivingLabBootstrap).
        /// </summary>
        public static float TrailerArticulationLeftDeg;
        /// <summary>
        /// ADR 0312: the class II mirror on the inside of a turn pans outward with the articulation so the trailer's last
        /// axle stays in the main mirror (as the HUD insets show only class II, D70). Pure static geometry from the R46 fields
        /// (MirrorTrailerVisibilityTests): without it the inside wheel of the last trailer axle leaves the class II field
        /// from 25-30 deg of articulation (roundabouts) and is only in the class IV glass. Off = the fixed R46 aim.
        /// WORKING_VALUE (gain 0.7 / start 20 deg / max 25 deg: the smallest pan that reaches the wheel + 3.5-5 deg margin, from
        /// MirrorTrailerVisibilityTests; owner feel test). Camera-monitor systems with trailer panning exist (UNVERIFIED).
        /// </summary>
        public static bool TrailerPanEnabled = true;
        public static float TrailerPanGain = 0.7f, TrailerPanStartDeg = 20f, TrailerPanMaxDeg = 25f;

        /// <summary>Outward pan [deg] of a main mirror (<paramref name="phase"/> 0 = left) for an articulation (+ = left turn):
        /// only the inside mirror moves, nothing below <paramref name="startDeg"/>, capped at <paramref name="maxDeg"/>. Pure.</summary>
        public static float TrailerPanDeg(int phase, float articulationLeftDeg, float gain, float startDeg, float maxDeg)
        {
            float inside = phase == 0 ? articulationLeftDeg : -articulationLeftDeg;
            if (float.IsNaN(inside) || gain <= 0f || inside <= startDeg) return 0f;
            return Mathf.Min(Mathf.Max(0f, maxDeg), gain * (inside - startDeg));
        }

        /// <summary>
        /// ADR 0340 addendum 2: where the modelled arms of the TRAKT mirror head meet the cab, relative to the centre of
        /// the class II glass in vehicle axes [m]: towards the centre line, up, forward. From
        /// tools/blender/truck/exterior/body.py mirrors(): glass centre (1.478, 1.018, 2.597), A-pillar inner face at the
        /// door's front edge (1.106, 1.156, 2.72) (Blender x right, y forward, z up). The HUD mirror head hangs its
        /// bracket on this point. Other tractors (graybox): the same offsets, an approximation.
        /// </summary>
        public static readonly Vector3 CabMountOffset = new Vector3(0.372f, 0.123f, 0.138f);

        Transform m_VehicleRoot;

        /// <summary>World position of the cab point the mirror head hangs on (<see cref="CabMountOffset"/>). No allocation.</summary>
        public Vector3 CabMountWorld()
        {
            if (m_VehicleRoot == null)
            {
                var rig = GetComponentInParent<TruckVisualRig>();
                m_VehicleRoot = rig != null ? rig.transform : transform.root;
            }
            Vector3 g = glass != null ? glass.bounds.center : transform.position;
            float side = m_VehicleRoot.InverseTransformPoint(g).x < 0f ? 1f : -1f;   // towards the centre line
            return g + m_VehicleRoot.TransformVector(new Vector3(side * CabMountOffset.x, CabMountOffset.y, CabMountOffset.z));
        }

        /// <summary>Viewport position (x, y in 0..1 of the frame, z = distance in front of the camera, &lt;= 0 behind it) of a
        /// world point for a perspective camera rendering at <paramref name="aspect"/> (width / height) - independent of
        /// the camera's current target (visual QA renders the HUD after the view). Pure.</summary>
        public static Vector3 ViewportOf(Camera cam, Vector3 world, float aspect)
        {
            Vector3 c = cam.worldToCameraMatrix.MultiplyPoint3x4(world);
            float depth = -c.z;
            if (depth <= 1e-4f) return new Vector3(0.5f, 0.5f, 0f);
            float ty = Mathf.Tan(0.5f * cam.fieldOfView * Mathf.Deg2Rad), tx = ty * Mathf.Max(0.01f, aspect);
            return new Vector3(0.5f + 0.5f * c.x / (depth * tx), 0.5f + 0.5f * c.y / (depth * ty), depth);
        }

        Quaternion m_BaseLocalRotation;
        bool m_HasBaseRotation;
        float m_AppliedYaw = float.NaN, m_AppliedPitch = float.NaN;

        /// <summary>Applies <see cref="AdjustYawOutDeg"/> / <see cref="AdjustPitchDownDeg"/> and the trailer pan to a main
        /// mirror (only on a change of more than 0.05 deg; no allocation).</summary>
        void ApplyAdjustment()
        {
            if (!main) return;
            if (!m_HasBaseRotation) { m_BaseLocalRotation = transform.localRotation; m_HasBaseRotation = true; }
            float yaw = AdjustYawOutDeg + (TrailerPanEnabled ? TrailerPanDeg(phase, TrailerArticulationLeftDeg, TrailerPanGain, TrailerPanStartDeg, TrailerPanMaxDeg) : 0f);
            if (Mathf.Abs(yaw - m_AppliedYaw) < 0.05f && AdjustPitchDownDeg == m_AppliedPitch) return;
            m_AppliedYaw = yaw; m_AppliedPitch = AdjustPitchDownDeg;
            transform.localRotation = m_BaseLocalRotation * Quaternion.Euler(AdjustEuler(phase, yaw, AdjustPitchDownDeg));
        }

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
        int m_Height, m_Msaa;
        bool m_Mips;

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
            ApplyAdjustment();
            int tierH = VehicleCameraBudget.MirrorHeight;
            int baseH = main ? VehicleCameraBudget.MainMirrorHeight(aspect) : tierH;
            int h = Mathf.Max(16, Mathf.RoundToInt(baseH * resolutionScale));
            // ADR 0340 addendum 2: a texture raised above the tier / window height is minified on screen - mip chain + trilinear.
            bool mips = main && baseH > tierH;
            var cam = Cam;
            // Also applies to existing generated prefabs, before their next TruckAssetBuilder rebuild.
            int cls = Class;
            if ((cls == 5 || cls == 6) && glass != null)
                cam.nearClipPlane = MirrorOptics.NearClipFor(cls,
                    Vector3.Distance(cam.transform.position, glass.bounds.center), MirrorOverrides.Legacy);
            else if (glass != null && !MirrorOverrides.Legacy)
                // ADR 0340: past the own glass rim (it showed as a dark rounded outline in the picture).
                cam.nearClipPlane = MirrorOptics.NearClipBeyondGlass(cam.transform.position, cam.transform.forward, glass.bounds);
            // Far clip every time (cheap): the A/B toggler (rq_ab mirrorcfg) switches configurations at run time.
            cam.farClipPlane = VehicleCameraBudget.MirrorFarClip * (main ? 1f : VehicleCameraBudget.ConvexFarClipScale);
            // ADR 0342: MSAA and shadows of the mirror camera follow the tier (PC High / Ultra); Low / Medium and phones stay 1 / off.
            int msaa = VehicleCameraBudget.MirrorMsaa;
            cam.allowMSAA = msaa > 1;
            var urpData = cam.GetComponent<UniversalAdditionalCameraData>();
            if (urpData != null) urpData.renderShadows = VehicleCameraBudget.MirrorShadows;
            // ADR 0340 addendum 2: a picture shown in a HUD window is drawn after the main view's grading, so it is graded here
            // (HDR + the look volume) - ungraded it was paler and flatter than the scene around it ("too bright / misty").
            // The 3D glass alone (no window) keeps the ungraded picture: the main view grades it once.
            bool post = VehicleCameraBudget.MirrorPost && (main ? ForceRender : ForceWide && cls == 4);
            if (cam.allowHDR != post) cam.allowHDR = post;
            if (urpData != null && urpData.renderPostProcessing != post) urpData.renderPostProcessing = post;
            if (m_Rt != null && m_Height == h && m_Msaa == msaa && m_Mips == mips) return;
            Release();
            m_Height = h; m_Msaa = msaa; m_Mips = mips;
            int w = Mathf.Max(16, Mathf.RoundToInt(h * aspect));
            m_Rt = new RenderTexture(w, h, 16, RenderTextureFormat.ARGB32)
            {
                name = "Mirror_" + name, antiAliasing = msaa, useMipMap = mips, autoGenerateMips = mips,
                filterMode = mips ? FilterMode.Trilinear : FilterMode.Bilinear,
            };
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
            m_Candidate = GlobalEnabled && !MirrorOverrides.Suspended && glass != null && (main && ForceRender || !main && ForceWide && Class == 4 || glass.isVisible || m_Rt == null);
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
            bool insets = ForceRender;   // ADR 0243: class II shown as HUD windows (D70)
            bool due = VehicleCameraBudget.DueScheduleWith(insets);
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
                s_Entries[i].interval = VehicleCameraBudget.MirrorIntervalFor(level, cls, Standing, insets);
                s_Entries[i].fill = cls <= 4;
            }
            int n = due
                ? MirrorRefreshSchedule.StepDue(s_Entries, count, VehicleCameraBudget.MirrorsPerFrame, VehicleCameraBudget.FillSpare(level, insets, Standing))
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

        /// <summary>Camera settings for a cheap extra view (no shadows, no post, no MSAA, no depth/opaque copies; ADR 0342: EnsureTarget turns MSAA / shadows on per tier).</summary>
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
