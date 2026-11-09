using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering
{
    /// <summary>
    /// Local environment reflection for the player truck (review r3/r4 E1, E2: paint like grey plastic, glass without the
    /// sky). A small cube render texture is re-rendered around the truck from a camera that excludes the vehicle layer,
    /// one face every <see cref="QualityProfile.Tier.envCaptureInterval"/> frames (time-sliced, box-filtered mips), and
    /// handed to a Custom-mode <see cref="ReflectionProbe"/> that follows the truck (world-axis aligned, box around the
    /// tractor and trailer). The truck paint clear coat, the glass and anything else inside the box pick it as
    /// unity_SpecCube0; outside the box the analytic sky cubemap (EnvironmentLighting) stays the default.
    /// Off on the tiers with <c>envCaptureSize = 0</c> (Low, Medium): there the sky + ground cubemap is the static
    /// environment, at zero per-frame cost. The capture renders no shadows and no post-processing (blurred reflections),
    /// 1 m resolution is irrelevant at 128 px. Realtime reflection probes stay disabled in the quality settings: the
    /// capture is our own camera, so the cost is explicit and per tier.
    /// </summary>
    [ExecuteAlways]
    [DefaultExecutionOrder(900)]
    public sealed class VehicleReflectionCapture : MonoBehaviour
    {
        [Tooltip("Capture point relative to this transform (m): above the chassis, mid-cab height")]
        public Vector3 captureOffset = new Vector3(0f, 2.2f, 0f);
        [Tooltip("Probe box size (m): tractor + 13.6 m trailer, both inside at any articulation angle")]
        public Vector3 boxSize = new Vector3(30f, 12f, 40f);
        [Tooltip("Box centre relative to this transform, in the truck's frame (m): between tractor and trailer")]
        public Vector3 boxCentre = new Vector3(0f, 2f, -4f);
        [Tooltip("Layers excluded from the capture (the vehicles themselves, UI)")]
        public LayerMask excludeLayers = (1 << 8) | (1 << 5);
        [Tooltip("Upper limit of the capture far clip (m); the tier value is clamped to it")] public float maxFarClip = 200f;

        static readonly Quaternion[] k_Face =
        {
            Quaternion.LookRotation(Vector3.right, Vector3.up),     // +X
            Quaternion.LookRotation(Vector3.left, Vector3.up),      // -X
            Quaternion.LookRotation(Vector3.up, Vector3.back),      // +Y
            Quaternion.LookRotation(Vector3.down, Vector3.forward), // -Y
            Quaternion.LookRotation(Vector3.forward, Vector3.up),   // +Z
            Quaternion.LookRotation(Vector3.back, Vector3.up),      // -Z
        };

        GameObject m_Root;
        Camera m_Cam;
        ReflectionProbe m_Probe;
        RenderTexture m_Cube;
        int m_Face, m_FrameCounter, m_Size, m_Interval = 1;
        float m_Far = 300f;
        UniversalRenderPipeline.SingleCameraRequest m_Request;

        public static VehicleReflectionCapture Active { get; private set; }
        public RenderTexture Cube => m_Cube;
        public bool Enabled => m_Size > 0 && m_Cube != null;

        void OnEnable()
        {
            Active = this;
            QualityProfileApplier.Applied += OnTier;
            if (QualityProfileApplier.HasCurrent) OnTier(QualityProfileApplier.Current);
        }

        void OnDisable()
        {
            QualityProfileApplier.Applied -= OnTier;
            if (Active == this) Active = null;
            Release();
        }

        void OnTier(QualityProfile.Tier t)
        {
            m_Interval = Mathf.Max(1, t.envCaptureInterval);
            m_Far = t.envCaptureFarClip > 10f ? t.envCaptureFarClip : 300f;
            if (t.envCaptureSize != m_Size) { Release(); m_Size = t.envCaptureSize; }
            if (m_Size > 0) Ensure();
        }

        void Ensure()
        {
            if (m_Root == null)
            {
                m_Root = new GameObject("VehicleReflectionCapture (runtime)") { hideFlags = HideFlags.DontSave };
                var camGo = new GameObject("CaptureCamera") { hideFlags = HideFlags.DontSave };
                camGo.transform.SetParent(m_Root.transform, false);
                m_Cam = camGo.AddComponent<Camera>();
                m_Cam.enabled = false;
                m_Cam.fieldOfView = 90f;
                m_Cam.aspect = 1f;
                m_Cam.nearClipPlane = 0.3f;
                m_Cam.clearFlags = CameraClearFlags.Skybox;
                m_Cam.allowMSAA = false;
                m_Cam.allowHDR = true;
                m_Cam.useOcclusionCulling = false;
                // Reflection camera type: WorldInstances (instanced props, trees) skips it - S24+ High measured +4 ms CPU
                // main thread per frame with the instanced forest submitted for every capture face (A8 run 1).
                m_Cam.cameraType = CameraType.Reflection;
                var data = camGo.AddComponent<UniversalAdditionalCameraData>();
                data.renderShadows = false;
                data.renderPostProcessing = false;
                data.antialiasing = AntialiasingMode.None;
                data.requiresColorOption = CameraOverrideOption.Off;
                data.requiresDepthOption = CameraOverrideOption.Off;
                data.SetRenderer(0);
                m_Probe = m_Root.AddComponent<ReflectionProbe>();
                m_Probe.mode = ReflectionProbeMode.Custom;
                m_Probe.importance = 10;
                m_Probe.boxProjection = false;
                m_Probe.blendDistance = 0f;
                m_Probe.intensity = 1f;
            }
            if (m_Cube == null)
            {
                m_Cube = new RenderTexture(m_Size, m_Size, 16, RenderTextureFormat.ARGBHalf)
                {
                    name = "VehicleReflection", dimension = TextureDimension.Cube, useMipMap = true, autoGenerateMips = false,
                    filterMode = FilterMode.Trilinear, wrapMode = TextureWrapMode.Clamp, hideFlags = HideFlags.DontSave,
                };
                m_Cube.Create();
                m_Probe.customBakedTexture = m_Cube;
                m_Face = 0;
                m_Request = new UniversalRenderPipeline.SingleCameraRequest { destination = m_Cube };
                RenderAllNow();   // first frame: complete cube, no half-black faces
            }
            m_Root.SetActive(true);
        }

        void Release()
        {
            if (m_Probe != null) m_Probe.customBakedTexture = null;
            if (m_Cube != null) { m_Cube.Release(); DestroySafe(m_Cube); m_Cube = null; }
            if (m_Root != null) { DestroySafe(m_Root); m_Root = null; m_Cam = null; m_Probe = null; }
        }

        static void DestroySafe(Object o) { if (Application.isPlaying) Destroy(o); else DestroyImmediate(o); }

        void Place()
        {
            var t = transform;
            m_Root.transform.SetPositionAndRotation(t.TransformPoint(captureOffset), Quaternion.identity);
            // Probe box: world-axis aligned (the cube is captured in world axes), centred between tractor and trailer and
            // large enough for any heading.
            float r = Mathf.Max(boxSize.x, boxSize.z);
            m_Probe.center = t.TransformPoint(boxCentre) - m_Root.transform.position;
            m_Probe.size = new Vector3(r, boxSize.y, r);
            m_Cam.cullingMask = ~excludeLayers.value;
            m_Cam.farClipPlane = Mathf.Min(m_Far, maxFarClip);
        }

        void LateUpdate()
        {
            if (!Application.isPlaying || m_Size <= 0 || m_Cube == null) return;
            if (++m_FrameCounter < m_Interval) return;
            m_FrameCounter = 0;
            Place();
            RenderFace(m_Face);
            m_Face = (m_Face + 1) % 6;
            m_Cube.GenerateMips();
        }

        void RenderFace(int face)
        {
            m_Cam.transform.rotation = k_Face[face];
            m_Request.face = (CubemapFace)face;
            m_Request.mipLevel = 0;
            if (RenderPipeline.SupportsRenderRequest(m_Cam, m_Request))
                RenderPipeline.SubmitRenderRequest(m_Cam, m_Request);
        }

        /// <summary>Renders all six faces now (first frame, visual QA in edit mode).</summary>
        public void RenderAllNow()
        {
            if (m_Size <= 0) return;
            if (m_Cube == null) { Ensure(); return; }
            Place();
            for (int f = 0; f < 6; f++) RenderFace(f);
            m_Cube.GenerateMips();
        }
    }
}
