using UnityEngine;
using UnityEngine.Experimental.Rendering;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering
{
    /// <summary>
    /// Local environment reflection for the player truck (review r3/r4 E1, E2; r7 / D30-D31, ADR 0056). A small cube
    /// render texture is re-rendered around the truck from a camera that excludes the vehicle layer, one face every
    /// <see cref="QualityProfile.Tier.envCaptureInterval"/> frames (time-sliced, box-filtered mips), and bound as the global
    /// <c>_KamionVehicleEnvCube</c> that <c>KamionVehicleEnv.hlsl</c> samples for the paint clear coat and the glass of every
    /// vehicle drawn with Kamion/Truck Exterior and Kamion/Truck Glass. World axes, no box projection: the content that the
    /// coat and glass mirror is mostly far (horizon, halls, sky), the near ground is in the cube at the capture height.
    /// ADR 0056 (r7): the earlier version handed the cube to a Custom-mode ReflectionProbe. That never reached the truck
    /// (editor proof: a cube cleared to red changed 0 px of truck-34; the renderers listed the probe with weight 1 but
    /// sampled the default sky cube), and every face rendered without a depth buffer (URP's cube path, see RenderFace), so
    /// the cube held only the skybox anyway. Since ADR 0021 the High "capture" was therefore the analytic sky.
    /// Tiers: one face every envCaptureInterval frames (Low 64 px / 10, Medium 64 / 6, High 128 / 3, Ultra 256 / 2), only while
    /// the truck moves more than <see cref="QualityProfile.Tier.envCaptureMinMove"/> (Low/Medium 2 m, High/Ultra 0.5 m) or the cube is older than
    /// <see cref="QualityProfile.Tier.envCaptureMaxAge"/>; envCaptureSize 0 = off (analytic sky + ground in the shader).
    /// No shadows, no post-processing, no MSAA, Reflection camera type (WorldInstances skips it: no instanced forest/props).
    /// </summary>
    [ExecuteAlways]
    [DefaultExecutionOrder(900)]
    public sealed class VehicleReflectionCapture : MonoBehaviour
    {
        [Tooltip("Capture point relative to this transform (m): above the chassis, mid-cab height")]
        public Vector3 captureOffset = new Vector3(0f, 2.2f, 0f);
        [Tooltip("Unused since ADR 0056 (no reflection probe); kept for serialized prefabs")]
        public Vector3 boxSize = new Vector3(30f, 12f, 40f);
        [Tooltip("Unused since ADR 0056 (no reflection probe); kept for serialized prefabs")]
        public Vector3 boxCentre = new Vector3(0f, 2f, -4f);
        [Tooltip("Layers excluded from the capture (the vehicles themselves, UI)")]
        public LayerMask excludeLayers = (1 << 8) | (1 << 5);
        [Tooltip("Upper limit of the capture far clip (m); the tier value is clamped to it")] public float maxFarClip = 200f;
        [Tooltip("ADR 0068: LOD-bias multiplier while a capture face renders (128 px over 90 deg = 1.4 px/deg vs ~25 in the main view)")]
        public float captureLodScale = 0.25f;

        /// <summary>ADR 0068 A/B (rq_ab envcap): no faces are rendered while true; the last cube stays bound.</summary>
        public static bool Paused;

        static readonly Quaternion[] k_Face =
        {
            Quaternion.LookRotation(Vector3.right, Vector3.up),     // +X
            Quaternion.LookRotation(Vector3.left, Vector3.up),      // -X
            Quaternion.LookRotation(Vector3.up, Vector3.back),      // +Y
            Quaternion.LookRotation(Vector3.down, Vector3.forward), // -Y
            Quaternion.LookRotation(Vector3.forward, Vector3.up),   // +Z
            Quaternion.LookRotation(Vector3.back, Vector3.up),      // -Z
        };

        static readonly int k_Capture = Shader.PropertyToID("_KamionVehicleCapture"),
            k_SkyCapOff = Shader.PropertyToID("_KamionSkyCapOff"),
            k_EnvCube = Shader.PropertyToID("_KamionVehicleEnvCube"),
            k_EnvParams = Shader.PropertyToID("_KamionVehicleEnvParams"),
            k_Tone = Shader.PropertyToID("_KamionTone");

        GameObject m_Root;
        Camera m_Cam;
        RenderTexture m_Cube, m_FaceRT;
        Vector3 m_LastCubePos;
        float m_LastCubeTime, m_MinMove, m_MaxAge;
        bool m_Idle;
        int m_Face, m_FrameCounter, m_Size, m_Interval = 1, m_FacesRendered;
        float m_Far = 300f;
        UniversalRenderPipeline.SingleCameraRequest m_Request;

        public static VehicleReflectionCapture Active { get; private set; }
        public RenderTexture Cube => m_Cube;
        public bool Enabled => m_Size > 0 && m_Cube != null;
        /// <summary>True while the cube is complete and the schedule renders no faces (parked truck, ADR 0056).</summary>
        public bool Idle => m_Idle;
        /// <summary>Faces rendered since enable (QA / profiling counter).</summary>
        public int FacesRendered => m_FacesRendered;

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
            m_MinMove = Mathf.Max(0f, t.envCaptureMinMove);
            m_MaxAge = t.envCaptureMaxAge > 0f ? t.envCaptureMaxAge : 30f;
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
                // ADR 0068: lower LOD for the 128 px faces (LODGroups; the instanced world already skips Reflection cameras).
                var tag = camGo.AddComponent<ExtraViewTag>();
                tag.kind = Game.Core.ExtraViewKind.Capture;
                tag.lodScale = RenderOverrides.EnvCaptureLod ?? captureLodScale;
                Game.Core.ExtraViewLod.Hook();
            }
            if (m_Cube == null)
            {
                m_Cube = new RenderTexture(m_Size, m_Size, 0, RenderTextureFormat.ARGBHalf)
                {
                    name = "VehicleReflection", dimension = TextureDimension.Cube, useMipMap = true, autoGenerateMips = false,
                    filterMode = FilterMode.Trilinear, wrapMode = TextureWrapMode.Clamp, hideFlags = HideFlags.DontSave,
                };
                m_Cube.Create();
                // ADR 0056: every face renders into a 2D target WITH a depth buffer and is copied into the cube. A request
                // straight into the cube goes through URP's own temporary 2D RT, which it builds from a default descriptor
                // without depth (UniversalRenderPipeline.ProcessRenderRequests); the render graph then warns "the output
                // Render Texture must have a depth buffer" and the opaque pass draws nothing (skybox only). Default-
                // constructed descriptor as URP's (no vertical-flip flag), so the copied face has the orientation URP's
                // own cube path produces.
                var fd = new RenderTextureDescriptor
                {
                    width = m_Size, height = m_Size, volumeDepth = 1, msaaSamples = 1, dimension = TextureDimension.Tex2D,
                    graphicsFormat = m_Cube.graphicsFormat, depthStencilFormat = GraphicsFormat.D24_UNorm_S8_UInt,
                };
                m_FaceRT = new RenderTexture(fd) { name = "VehicleReflectionFace", hideFlags = HideFlags.DontSave };
                m_FaceRT.Create();
                m_Face = 0;
                m_Request = new UniversalRenderPipeline.SingleCameraRequest { destination = m_FaceRT };
                RenderAllNow();   // first frame: complete cube, no half-black faces
            }
            m_Root.SetActive(true);
            Bind();
        }

        void Bind()
        {
            Shader.SetGlobalTexture(k_EnvCube, m_Cube);
            // ADR0087 box-mip footprint: x maximum sampled mip, y actual face size (not a GGX probe).
            Shader.SetGlobalVector(k_EnvParams, new Vector4(Mathf.Min(6f, m_Cube.mipmapCount - 1), m_Size, 0f, 0f));
            Shader.SetGlobalFloat(k_Capture, 1f);   // KamionVehicleEnv.hlsl samples _KamionVehicleEnvCube
        }

        void Release()
        {
            Shader.SetGlobalFloat(k_Capture, 0f);
            Shader.SetGlobalTexture(k_EnvCube, null);
            if (m_Cube != null) { m_Cube.Release(); DestroySafe(m_Cube); m_Cube = null; }
            if (m_FaceRT != null) { m_FaceRT.Release(); DestroySafe(m_FaceRT); m_FaceRT = null; }
            if (m_Root != null) { DestroySafe(m_Root); m_Root = null; m_Cam = null; }
        }

        static void DestroySafe(Object o) { if (Application.isPlaying) Destroy(o); else DestroyImmediate(o); }

        void Place()
        {
            m_Root.transform.SetPositionAndRotation(transform.TransformPoint(captureOffset), Quaternion.identity);
            m_Cam.cullingMask = ~excludeLayers.value;
            m_Cam.farClipPlane = Mathf.Min(m_Far, maxFarClip);
        }

        void LateUpdate()
        {
            if (!Application.isPlaying || m_Size <= 0 || m_Cube == null || Paused) return;
            // ADR 0152: after the app returns from the background (Fold, Vulkan/Adreno) the targets can come back released;
            // a request into a released face RT fails every face ("RenderPass: Fake or uninitialized surface ...",
            // "EndRenderPass: Not inside a Renderpass", 216 error lines/min on the owner's Fold) and the cube stays stale.
            if (!m_Cube.IsCreated() || m_FaceRT == null || !m_FaceRT.IsCreated())
            {
                m_Cube.Create();
                if (m_FaceRT != null) m_FaceRT.Create();
                Debug.Log("[ENVCAP] capture targets were released (app resumed) - recreated, full cube re-rendered");
                RenderAllNow();
                return;
            }
            if (++m_FrameCounter < m_Interval) return;
            m_FrameCounter = 0;
            // ADR 0056 (Low/Medium): a complete cube is kept while the capture point stays within envCaptureMinMove of
            // where it was rendered and it is younger than envCaptureMaxAge (sky / sun drift): a parked or slowly
            // manoeuvring truck renders no faces at all. Driving refreshes one face every envCaptureInterval frames.
            if (m_Face == 0 && m_MinMove > 0f)
            {
                Vector3 p = transform.TransformPoint(captureOffset);
                m_Idle = (p - m_LastCubePos).sqrMagnitude < m_MinMove * m_MinMove && Time.time - m_LastCubeTime < m_MaxAge;
                if (m_Idle) return;
            }
            Place();
            RenderFace(m_Face);
            m_Face = (m_Face + 1) % 6;
            m_Cube.GenerateMips();
            if (m_Face == 0) { m_LastCubePos = m_Root.transform.position; m_LastCubeTime = Time.time; }
        }

        void RenderFace(int face)
        {
            m_Cam.transform.rotation = k_Face[face];
            m_Request.mipLevel = 0;
            if (!RenderPipeline.SupportsRenderRequest(m_Cam, m_Request)) return;
            // r6 L4: the reflection sees the physical sky radiance, not the phone-compressed dome of the main view.
            float skyCapOff = Shader.GetGlobalFloat(k_SkyCapOff), capture = Shader.GetGlobalFloat(k_Capture);
            Vector4 tone = Shader.GetGlobalVector(k_Tone);
            try
            {
                Shader.SetGlobalFloat(k_SkyCapOff, 1f);
                // Capture physical scene radiance. Low world surfaces otherwise bake their look into the cube,
                // then TruckExterior/Glass apply it again. Physical sky already bypasses its display cap.
                Shader.SetGlobalVector(k_Tone, Vector4.zero);
                Shader.SetGlobalFloat(k_Capture, 0f);
                RenderPipeline.SubmitRenderRequest(m_Cam, m_Request);
            }
            finally
            {
                Shader.SetGlobalFloat(k_Capture, capture);
                Shader.SetGlobalFloat(k_SkyCapOff, skyCapOff);
                Shader.SetGlobalVector(k_Tone, tone);
            }
            Graphics.CopyTexture(m_FaceRT, 0, 0, m_Cube, face, 0);
            m_FacesRendered++;
        }

        /// <summary>QA: writes the cube as a horizontal strip (+X -X +Y -Y +Z -Z), mip 0, linear x exposure -> sRGB, clipped.</summary>
        public void DumpStrip(string path)
        {
            if (m_Cube == null) return;
            int s = m_Size;
            var rt = RenderTexture.GetTemporary(s, s, 0, RenderTextureFormat.ARGBHalf);
            var tex = new Texture2D(s * 6, s, TextureFormat.RGBAHalf, false, true);
            var prev = RenderTexture.active;
            for (int f = 0; f < 6; f++)
            {
                Graphics.CopyTexture(m_Cube, f, 0, rt, 0, 0);
                RenderTexture.active = rt;
                tex.ReadPixels(new Rect(0, 0, s, s), f * s, 0);
            }
            RenderTexture.active = prev;
            RenderTexture.ReleaseTemporary(rt);
            var px = tex.GetPixels();
            var outTex = new Texture2D(s * 6, s, TextureFormat.RGB24, false);
            for (int i = 0; i < px.Length; i++) { var c = px[i]; c.a = 1f; px[i] = c.gamma; }
            outTex.SetPixels(px);
            System.IO.File.WriteAllBytes(path, outTex.EncodeToPNG());
            DestroySafe(tex); DestroySafe(outTex);
        }

        /// <summary>Renders all six faces now (first frame, visual QA in edit mode).</summary>
        public void RenderAllNow()
        {
            if (m_Size <= 0) return;
            if (m_Cube == null) { Ensure(); return; }
            Place();
            for (int f = 0; f < 6; f++) RenderFace(f);
            m_Cube.GenerateMips();
            Bind();
            m_Face = 0; m_FrameCounter = 0;
            m_LastCubePos = m_Root.transform.position; m_LastCubeTime = Application.isPlaying ? Time.time : 0f;
            if (!Application.isPlaying) Debug.Log("[ENVCAP] " + LoadEstimate());
        }

        /// <summary>
        /// QA / budget evidence (ADR 0056): per face, the MeshRenderers inside the capture frustum (far clip, culling mask)
        /// and their triangles - a CPU-side upper bound of what one face submits (no occlusion, LOD chain counted at the
        /// level its LODGroup would pick is not modelled: every active renderer counts). Editor diagnostics only.
        /// </summary>
        public string LoadEstimate()
        {
            if (m_Cam == null) return "off";
            var planes = new Plane[6];
            var rs = Object.FindObjectsByType<MeshRenderer>(FindObjectsInactive.Exclude, FindObjectsSortMode.None);
            var sb = new System.Text.StringBuilder();
            sb.Append($"size={m_Size} interval={m_Interval} far={m_Cam.farClipPlane:F0} minMove={m_MinMove:F1} faces:");
            long totalTris = 0; int totalDraws = 0;
            for (int f = 0; f < 6; f++)
            {
                m_Cam.transform.rotation = k_Face[f];
                GeometryUtility.CalculateFrustumPlanes(m_Cam, planes);
                int draws = 0; long tris = 0;
                foreach (var r in rs)
                {
                    if (!r.enabled || ((1 << r.gameObject.layer) & m_Cam.cullingMask) == 0) continue;
                    if (!GeometryUtility.TestPlanesAABB(planes, r.bounds)) continue;
                    var mf = r.GetComponent<MeshFilter>();
                    if (mf == null || mf.sharedMesh == null) continue;
                    var m = mf.sharedMesh;
                    for (int sm = 0; sm < m.subMeshCount; sm++) tris += (long)m.GetIndexCount(sm) / 3;
                    draws += m.subMeshCount;
                }
                sb.Append($" [{f}] {draws} draws {tris / 1000}k tris");
                totalTris += tris; totalDraws += draws;
            }
            sb.Append($"; mean/face {totalDraws / 6} draws {totalTris / 6000}k tris");
            return sb.ToString();
        }
    }
}
