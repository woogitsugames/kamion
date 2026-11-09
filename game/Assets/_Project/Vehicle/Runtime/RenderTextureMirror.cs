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
        /// <summary>Mirror render-texture height in pixels (width follows the glass aspect).</summary>
        public static int MirrorHeight => Level switch { 0 => 224, 1 => 288, 2 => 384, _ => 512 };
        /// <summary>Render each mirror every N frames (mirrors are phase-shifted, so N = 2 means one mirror per frame).</summary>
        public static int MirrorInterval => Level switch { 0 => 4, 1 => 2, _ => 1 };
        public static float MirrorFarClip => Level switch { 0 => 150f, 1 => 250f, _ => 400f };
        public static int ReverseCamHeight => Level switch { 0 => 180, 1 => 216, 2 => 288, _ => 360 };
        public static int ReverseCamInterval => Level <= 1 ? 2 : 1;
    }

    /// <summary>
    /// Flat rear-view mirror: a camera at the mirror head looking along the reflection of the driver's line of sight,
    /// rendering a low-resolution render texture shown (horizontally flipped) on the glass quad. Static geometry
    /// (computed for the design eye point by the builder), not a per-frame reflection of the head position.
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
        /// <summary>Frame phase so that two mirrors alternate.</summary>
        public int phase;

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

        void EnsureTarget()
        {
            int h = VehicleCameraBudget.MirrorHeight;
            if (m_Rt != null && m_Height == h) return;
            Release();
            m_Height = h;
            int w = Mathf.Max(16, Mathf.RoundToInt(h * aspect));
            m_Rt = new RenderTexture(w, h, 16, RenderTextureFormat.ARGB32) { name = "Mirror_" + name, antiAliasing = 1, useMipMap = false };
            m_Rt.Create();
            var cam = Cam;
            cam.targetTexture = m_Rt;
            cam.farClipPlane = VehicleCameraBudget.MirrorFarClip;
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
            var cam = Cam;
            if (!GlobalEnabled || glass == null || !ForceRender && !glass.isVisible && m_Rt != null)
            {
                cam.enabled = false;
                return;
            }
            EnsureTarget();
            int n = Mathf.Max(1, VehicleCameraBudget.MirrorInterval);
            // Cameras enabled in LateUpdate render this frame, before the main camera (they target a texture).
            cam.enabled = Time.frameCount % n == phase % n;
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
}
