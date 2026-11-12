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
        /// <summary>Informational: the rest gaze is DriverHead.RestPitchDownDeg (same as the A7 control cameras).</summary>
        public float CabPitchDown => DriverHead.RestPitchDownDeg;
        public float headGain = 0.006f;      // m per m/s^2
        public float headMaxOffset = 0.04f;  // m
        public float headFrequency = 1.8f;   // Hz
        public float headDamping = 0.7f;
        public float lookDegPerPixel = 0.12f;
        public float lookReturnDelay = 2f, lookReturnRate = 60f;
        /// <summary>
        /// Driving look limits (ADR 0082, owner recording 2026-11-10 at 69.9 s: a stray drag beside the steering wheel
        /// pitched the view ~30 deg up into the headliner for 2 s at 90 km/h). Above <see cref="drivingLookSpeedKmh"/>
        /// the vertical look range shrinks to what a driver uses with the road in sight (overhead signs, instruments)
        /// and the view returns to the road sooner. Yaw stays free (mirrors, junctions). WORKING_VALUE, feel item.
        /// </summary>
        public float drivingLookSpeedKmh = 20f, drivingPitchUpDeg = 12f, drivingPitchDownDeg = 25f, drivingLookReturnDelay = 0.8f;
        /// <summary>Forward speed of the target [km/h] (from the Rigidbody in FixedUpdate; tests set it directly).</summary>
        public float speedKmh;
        /// <summary>Acceleration fed to the head sway is limited to this [m/s^2] (crash / fall spikes do not throw the head).</summary>
        public float headMaxAccel = 12f;
        /// <summary>
        /// Box (half extents, anchor frame, m) the eye never leaves relative to the seated eye point: neck parallax
        /// (DriverHead.EyeFromNeckPivot, up to ~0.14 m) plus sway. Keeps the camera inside the cab whatever the inputs. WORKING_VALUE.
        /// </summary>
        public Vector3 eyeBoxHalfExtents = new Vector3(0.20f, 0.12f, 0.20f);

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
        public float LookYaw => m_LookYaw;
        public float LookPitch => m_LookPitch;

        public void NextMode()
        {
            mode = (CameraMode)(((int)mode + 1) % 3);
            m_ChaseInit = false;
        }

        public void SetMode(CameraMode m) { mode = m; m_ChaseInit = false; }

        /// <summary>Re-centres the cab view and clears the head sway state (after a vehicle reset / teleport).</summary>
        public void ResetView()
        {
            m_LookYaw = 0f; m_LookPitch = 0f; m_LookIdle = 0f;
            m_HeadPos = Vector3.zero; m_HeadVel = Vector3.zero; m_AccFiltered = Vector3.zero;
            m_HasPrevVel = false;
            m_ChaseInit = false;
        }

        bool Driving => Mathf.Abs(speedKmh) > drivingLookSpeedKmh;

        /// <summary>Look pitch (positive = down) limited to the driving range above the driving speed, else to the neck limits.</summary>
        public float ClampLookPitch(float deg)
        {
            deg = DriverHead.ClampPitch(deg);
            return Driving ? Mathf.Clamp(deg, -drivingPitchUpDeg, drivingPitchDownDeg) : deg;
        }

        /// <summary>Chase / orbit framing for a tractor alone or with a 13.6 m semi-trailer behind it.</summary>
        public void SetCombination(bool withTrailer)
        {
            chaseDistance = withTrailer ? 26f : 13f;
            chaseHeight = withTrailer ? 7.5f : 4.5f;
            orbitDistance = withTrailer ? 26f : 14f;
            m_ChaseInit = false;
        }

        /// <summary>Drag on the free screen area (pixels).</summary>
        public void AddLookDelta(Vector2 px)
        {
            if (mode == CameraMode.Cab)
            {
                m_LookYaw = DriverHead.ClampYaw(m_LookYaw + px.x * lookDegPerPixel);
                m_LookPitch = ClampLookPitch(m_LookPitch - px.y * lookDegPerPixel);
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
            else if (mode == CameraMode.Chase) chaseDistance = Mathf.Clamp(chaseDistance * (1f - delta * 0.1f), 7f, 45f);
        }

        void FixedUpdate()
        {
            m_FixedSteps++;
            if (targetBody == null) return;
            Vector3 v = targetBody.linearVelocity;
            speedKmh = Vector3.Dot(v, targetBody.transform.forward) * 3.6f;
            if (m_HasPrevVel)
            {
                Vector3 aWorld = (v - m_PrevVel) / Time.fixedDeltaTime;
                Vector3 aLocal = Vector3.ClampMagnitude(targetBody.transform.InverseTransformDirection(aWorld), headMaxAccel);
                if (!IsFinite(aLocal)) aLocal = Vector3.zero;
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
            if (PoseLogPath != null) LogPose();
            m_FixedSteps = 0;
        }

        // ---- ADR 0152 diagnostics: per-frame camera pose (launch argument camlog=1), off by default --------------------
        /// <summary>CSV path of the per-frame pose log; null = off. Set by the bootstrap from the launch argument camlog=1.</summary>
        public static string PoseLogPath;
        int m_FixedSteps;
        float[] m_Log;
        int m_LogN;
        Vector3 m_LastTargetPos;
        const int LogCols = 12, LogRows = 200;

        void LogPose()
        {
            if (m_Log == null) { m_Log = new float[LogCols * LogRows]; try { System.IO.File.WriteAllText(PoseLogPath, "t_s,dt_ms,fixed_steps,head_x_mm,head_z_mm,eye_x_mm,eye_y_mm,eye_z_mm,pitch_deg,yaw_deg,roll_deg,target_move_mm\n"); } catch { PoseLogPath = null; return; } m_LastTargetPos = target.position; }
            Vector3 eye = target.InverseTransformPoint(cam.transform.position);
            Vector3 e = (Quaternion.Inverse(target.rotation) * cam.transform.rotation).eulerAngles;
            int o = m_LogN * LogCols;
            m_Log[o] = Time.realtimeSinceStartup; m_Log[o + 1] = Time.deltaTime * 1000f; m_Log[o + 2] = m_FixedSteps;
            m_Log[o + 3] = m_HeadPos.x * 1000f; m_Log[o + 4] = m_HeadPos.z * 1000f;
            m_Log[o + 5] = eye.x * 1000f; m_Log[o + 6] = eye.y * 1000f; m_Log[o + 7] = eye.z * 1000f;
            m_Log[o + 8] = Mathf.DeltaAngle(0f, e.x); m_Log[o + 9] = Mathf.DeltaAngle(0f, e.y); m_Log[o + 10] = Mathf.DeltaAngle(0f, e.z);
            m_Log[o + 11] = (target.position - m_LastTargetPos).magnitude * 1000f;
            m_LastTargetPos = target.position;
            if (++m_LogN == LogRows) FlushPoseLog();
        }

        void FlushPoseLog()
        {
            if (m_Log == null || m_LogN == 0 || PoseLogPath == null) return;
            var sb = new System.Text.StringBuilder(m_LogN * 96);
            var ci = System.Globalization.CultureInfo.InvariantCulture;
            for (int r = 0; r < m_LogN; r++)
            {
                for (int c = 0; c < LogCols; c++) { if (c > 0) sb.Append(','); sb.Append(m_Log[r * LogCols + c].ToString(c == 0 ? "F3" : "F2", ci)); }
                sb.Append('\n');
            }
            try { System.IO.File.AppendAllText(PoseLogPath, sb.ToString()); } catch { }
            m_LogN = 0;
        }

        void OnDisable() => FlushPoseLog();
        void OnApplicationPause(bool paused) { if (paused) FlushPoseLog(); }

        /// <summary>Public for tests; called from LateUpdate in Cab mode.</summary>
        public void UpdateCab(float dt)
        {
            var anchor = eyeAnchor != null ? eyeAnchor : target;
            // Head lags behind the cab: braking (a_z < 0) moves the head forward, cornering moves it outward.
            Vector3 desired = Vector3.ClampMagnitude(new Vector3(-m_AccFiltered.x, 0f, -m_AccFiltered.z) * headGain, headMaxOffset);
            StepHeadSpring(desired, dt, headFrequency, headDamping, ref m_HeadPos, ref m_HeadVel, LegacyHeadIntegration);
            m_HeadPos = Vector3.ClampMagnitude(m_HeadPos, headMaxOffset * 1.5f);
            if (!IsFinite(m_HeadPos) || !IsFinite(m_HeadVel)) { m_HeadPos = Vector3.zero; m_HeadVel = Vector3.zero; }

            m_LookIdle += dt;
            bool driving = Driving;
            if (driving)
            {
                // Picking up speed with the head tilted: ease into the driving range instead of snapping.
                float limited = Mathf.Clamp(m_LookPitch, -drivingPitchUpDeg, drivingPitchDownDeg);
                m_LookPitch = Mathf.MoveTowards(m_LookPitch, limited, lookReturnRate * dt);
            }
            if (m_LookIdle > (driving ? Mathf.Min(lookReturnDelay, drivingLookReturnDelay) : lookReturnDelay))
            {
                m_LookYaw = Mathf.MoveTowards(m_LookYaw, 0f, lookReturnRate * dt);
                m_LookPitch = Mathf.MoveTowards(m_LookPitch, 0f, lookReturnRate * dt);
            }
            // The anchor is a child of the cab-suspension pivot: the head follows the sprung cab. Look-around turns the head
            // about the neck pivot (DriverHead), within neck limits.
            Vector3 eyeLocal = DriverHead.LocalEyePosition(m_LookYaw, m_LookPitch, m_HeadPos);
            eyeLocal = new Vector3(Mathf.Clamp(eyeLocal.x, -eyeBoxHalfExtents.x, eyeBoxHalfExtents.x),
                Mathf.Clamp(eyeLocal.y, -eyeBoxHalfExtents.y, eyeBoxHalfExtents.y),
                Mathf.Clamp(eyeLocal.z, -eyeBoxHalfExtents.z, eyeBoxHalfExtents.z));
            Vector3 eyeWorld = anchor.TransformPoint(eyeLocal);
            Quaternion rot = anchor.rotation * DriverHead.LookRotation(m_LookYaw, m_LookPitch);
            if (!IsFinite(eyeWorld) || float.IsNaN(rot.x + rot.y + rot.z + rot.w)) return;   // never feed a broken pose to the renderer
            cam.transform.SetPositionAndRotation(eyeWorld, rot);
            cam.fieldOfView = CabVerticalFov(cabFov, cam.aspect);
            cam.nearClipPlane = 0.05f;
        }

        /// <summary>
        /// Vertical FOV of the cab camera for the settings FOV and the screen aspect (ADR 0135). Landscape (aspect &gt;= 1):
        /// the setting itself. A portrait window (near-square foldable held upright): the vertical FOV opens so the
        /// horizontal FOV stays what it is on a square screen (= the setting), i.e. the road ahead and the mirrors do not
        /// shrink out of view; capped at 90 deg.
        /// </summary>
        public static float CabVerticalFov(float settingDeg, float aspect)
        {
            if (!(aspect > 0f) || aspect >= 1f) return settingDeg;
            float v = 2f * Mathf.Atan(Mathf.Tan(settingDeg * 0.5f * Mathf.Deg2Rad) / aspect) * Mathf.Rad2Deg;
            return Mathf.Min(v, 90f);
        }

        /// <summary>ADR 0152 A/B only (launch argument cam_legacy=1): the pre-0152 single explicit step per rendered frame.</summary>
        public static bool LegacyHeadIntegration;
        /// <summary>Largest integration step of the head spring (s). ADR 0152: one semi-implicit Euler step per frame is
        /// unstable for w*dt above ~1.1 (1.8 Hz, zeta 0.7: dt &gt; ~0.09 s, i.e. below ~11 FPS) - the eigenvalue goes below -1
        /// and the head offset flips sign every frame up to the clamp (Fold Ultra and A16 High at 8-10 FPS).</summary>
        public const float HeadMaxStepS = 1f / 60f;

        /// <summary>Damped head spring towards <paramref name="desired"/> over <paramref name="dt"/>; sub-stepped so it is
        /// stable at any frame time (allocation-free, at most 12 sub-steps: dt is capped by Time.maximumDeltaTime 0.1 s).</summary>
        public static void StepHeadSpring(Vector3 desired, float dt, float frequencyHz, float damping, ref Vector3 pos, ref Vector3 vel, bool legacy = false)
        {
            float w = 2f * Mathf.PI * frequencyHz;
            int n = legacy ? 1 : Mathf.Clamp(Mathf.CeilToInt(dt / HeadMaxStepS), 1, 12);
            float h = dt / n;
            for (int i = 0; i < n; i++)
            {
                Vector3 acc = w * w * (desired - pos) - 2f * damping * w * vel;
                vel += acc * h;
                pos += vel * h;
            }
        }

        static bool IsFinite(Vector3 v) => !(float.IsNaN(v.x) || float.IsNaN(v.y) || float.IsNaN(v.z) || float.IsInfinity(v.x) || float.IsInfinity(v.y) || float.IsInfinity(v.z));

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
