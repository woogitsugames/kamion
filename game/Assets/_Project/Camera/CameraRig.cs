using UnityEngine;

namespace Game.Cameras
{
    public enum CameraMode { Cab = 0, Chase = 1, Orbit = 2 }

    /// <summary>
    /// One camera, three modes:
    /// - Cab: at the driver eye point (a transform on the cab-suspension pivot, so cab pitch/roll moves the head),
    ///   plus a small acceleration-driven head offset through a damped spring (limited amplitude and acceleration,
    ///   to avoid motion sickness), and look-around by dragging (returns to centre after a pause).
    /// - Chase: behind/above the truck, smoothed, follows heading.
    /// - Orbit: free orbit for debugging (drag = rotate, scroll/pinch = zoom).
    /// Runs in LateUpdate after the interpolated Rigidbody pose is written.
    /// </summary>
    [DefaultExecutionOrder(200)]
    public sealed class CameraRig : MonoBehaviour
    {
        public Camera cam;
        public Transform target;
        public Rigidbody targetBody;
        public Transform eyeAnchor;
        public CameraMode mode = CameraMode.Cab;

        [Header("Cab")]
        public float cabFov = 55f;
        public float headGain = 0.006f;      // m per m/s^2
        public float headMaxOffset = 0.04f;  // m
        public float headFrequency = 1.8f;   // Hz
        public float headDamping = 0.7f;
        public float lookDegPerPixel = 0.12f;
        public float lookReturnDelay = 2f, lookReturnRate = 60f;

        [Header("Chase")]
        public float chaseDistance = 13f, chaseHeight = 4.5f, chaseFov = 50f, chaseSmooth = 0.25f;

        [Header("Orbit")]
        public float orbitDistance = 14f, orbitFov = 50f;

        float m_LookYaw, m_LookPitch, m_LookIdle;
        Vector3 m_HeadPos, m_HeadVel, m_AccFiltered, m_PrevVel;
        bool m_HasPrevVel;
        Vector3 m_ChasePos, m_ChaseVel;
        bool m_ChaseInit;
        float m_OrbitYaw = 210f, m_OrbitPitch = 18f;

        public Vector3 HeadOffset => m_HeadPos;

        public void NextMode()
        {
            mode = (CameraMode)(((int)mode + 1) % 3);
            m_ChaseInit = false;
        }

        public void SetMode(CameraMode m) { mode = m; m_ChaseInit = false; }

        /// <summary>Drag on the free screen area (pixels).</summary>
        public void AddLookDelta(Vector2 px)
        {
            if (mode == CameraMode.Cab)
            {
                m_LookYaw = Mathf.Clamp(m_LookYaw + px.x * lookDegPerPixel, -130f, 130f);
                m_LookPitch = Mathf.Clamp(m_LookPitch - px.y * lookDegPerPixel, -35f, 25f);
                m_LookIdle = 0f;
            }
            else if (mode == CameraMode.Orbit)
            {
                m_OrbitYaw += px.x * 0.25f;
                m_OrbitPitch = Mathf.Clamp(m_OrbitPitch - px.y * 0.2f, -5f, 85f);
            }
        }

        public void AddZoom(float delta)
        {
            if (mode == CameraMode.Orbit) orbitDistance = Mathf.Clamp(orbitDistance * (1f - delta * 0.1f), 4f, 80f);
            else if (mode == CameraMode.Chase) chaseDistance = Mathf.Clamp(chaseDistance * (1f - delta * 0.1f), 7f, 30f);
        }

        void FixedUpdate()
        {
            if (targetBody == null) return;
            Vector3 v = targetBody.linearVelocity;
            if (m_HasPrevVel)
            {
                Vector3 aWorld = (v - m_PrevVel) / Time.fixedDeltaTime;
                Vector3 aLocal = targetBody.transform.InverseTransformDirection(aWorld);
                m_AccFiltered = Vector3.Lerp(m_AccFiltered, aLocal, 1f - Mathf.Exp(-Time.fixedDeltaTime / 0.12f));
            }
            m_PrevVel = v;
            m_HasPrevVel = true;
        }

        void LateUpdate()
        {
            if (cam == null || target == null) return;
            float dt = Mathf.Max(Time.deltaTime, 1e-4f);
            switch (mode)
            {
                case CameraMode.Cab: UpdateCab(dt); break;
                case CameraMode.Chase: UpdateChase(dt); break;
                default: UpdateOrbit(); break;
            }
        }

        void UpdateCab(float dt)
        {
            var anchor = eyeAnchor != null ? eyeAnchor : target;
            // Head lags behind the cab: braking (a_z < 0) moves the head forward, cornering moves it outward.
            Vector3 desired = Vector3.ClampMagnitude(new Vector3(-m_AccFiltered.x, 0f, -m_AccFiltered.z) * headGain, headMaxOffset);
            float w = 2f * Mathf.PI * headFrequency;
            Vector3 acc = w * w * (desired - m_HeadPos) - 2f * headDamping * w * m_HeadVel;
            m_HeadVel += acc * dt;
            m_HeadPos += m_HeadVel * dt;
            m_HeadPos = Vector3.ClampMagnitude(m_HeadPos, headMaxOffset * 1.5f);

            m_LookIdle += dt;
            if (m_LookIdle > lookReturnDelay)
            {
                m_LookYaw = Mathf.MoveTowards(m_LookYaw, 0f, lookReturnRate * dt);
                m_LookPitch = Mathf.MoveTowards(m_LookPitch, 0f, lookReturnRate * dt);
            }
            cam.transform.SetPositionAndRotation(anchor.TransformPoint(m_HeadPos), anchor.rotation * Quaternion.Euler(m_LookPitch, m_LookYaw, 0f));
            cam.fieldOfView = cabFov;
            cam.nearClipPlane = 0.05f;
        }

        void UpdateChase(float dt)
        {
            Vector3 fwd = target.forward; fwd.y = 0f;
            if (fwd.sqrMagnitude < 1e-4f) fwd = Vector3.forward;
            fwd.Normalize();
            Vector3 desired = target.position - fwd * chaseDistance + Vector3.up * chaseHeight;
            if (!m_ChaseInit) { m_ChasePos = desired; m_ChaseVel = Vector3.zero; m_ChaseInit = true; }
            m_ChasePos = Vector3.SmoothDamp(m_ChasePos, desired, ref m_ChaseVel, chaseSmooth, Mathf.Infinity, dt);
            Vector3 look = target.position + Vector3.up * 2.0f + fwd * 3f;
            cam.transform.SetPositionAndRotation(m_ChasePos, Quaternion.LookRotation(look - m_ChasePos, Vector3.up));
            cam.fieldOfView = chaseFov;
            cam.nearClipPlane = 0.3f;
        }

        void UpdateOrbit()
        {
            Vector3 pivot = target.position + Vector3.up * 1.8f + target.forward * 2f;
            Quaternion rot = Quaternion.Euler(m_OrbitPitch, m_OrbitYaw, 0f);
            cam.transform.SetPositionAndRotation(pivot - rot * Vector3.forward * orbitDistance, rot);
            cam.fieldOfView = orbitFov;
            cam.nearClipPlane = 0.3f;
        }
    }
}
