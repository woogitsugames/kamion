using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Rear-view (reversing) camera: on the trailer's rear portal, or behind the cab looking at the fifth wheel
    /// (coupling aid). Renders into a small render texture shown by the HUD only while <see cref="Active"/>.
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public sealed class ReversingCamera : MonoBehaviour
    {
        public bool Active;
        Camera m_Cam;
        RenderTexture m_Rt;
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
            int h = VehicleCameraBudget.ReverseCamHeight;
            if (m_Rt != null && m_Height == h) return;
            Release();
            m_Height = h;
            m_Rt = new RenderTexture(Mathf.RoundToInt(h * 16f / 9f), h, 16, RenderTextureFormat.ARGB32) { name = "ReverseCam_" + name, antiAliasing = 1, useMipMap = false };
            m_Rt.Create();
            Cam.targetTexture = m_Rt;
        }

        void LateUpdate()
        {
            var cam = Cam;
            if (!Active) { cam.enabled = false; return; }
            EnsureTarget();
            int n = Mathf.Max(1, VehicleCameraBudget.ReverseCamInterval);
            cam.enabled = Time.frameCount % n == 0;
        }

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

        void OnDestroy() => Release();
    }
}
