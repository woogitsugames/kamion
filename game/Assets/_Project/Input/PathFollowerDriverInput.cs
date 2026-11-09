using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// Scripted driver along a polyline (pure pursuit on the horizontal plane) for route measurements and the WorldC
    /// route test. Speed: min(target, per-point limit, curvature limit v = sqrt(a_lat · R)), brakes to a stop at the end.
    /// Allocation-free; the path is set once.
    /// </summary>
    public sealed class PathFollowerDriverInput : IDriverInput
    {
        public string Name => "route";
        public bool Enabled { get; set; }

        public float TargetSpeedKmh = 50f;
        public float MaxLateralAccel = 1.5f;     // m/s², comfortable for a loaded artic (WORKING_VALUE)
        public float Wheelbase = 3.7f;
        public float MaxRoadWheelAngleDeg = 40f;
        public float MinLookAhead = 7f;
        public float LookAheadTime = 0.9f;
        public float StopDistance = 25f;

        Vector3[] m_Points = System.Array.Empty<Vector3>();
        float[] m_S = System.Array.Empty<float>();
        float[] m_LimitKmh = System.Array.Empty<float>();
        int m_Seg;

        public float Progress { get; private set; }
        public float Length => m_S.Length > 0 ? m_S[m_S.Length - 1] : 0f;
        public bool Finished { get; private set; }
        public float LastSteer { get; private set; }
        public float CrossTrackError { get; private set; }
        public float CommandedSpeedKmh { get; private set; }

        public void SetPath(Vector3[] worldPoints, float[] speedLimitsKmh = null)
        {
            m_Points = worldPoints ?? System.Array.Empty<Vector3>();
            m_S = new float[m_Points.Length];
            for (int i = 1; i < m_Points.Length; i++)
            {
                Vector3 d = m_Points[i] - m_Points[i - 1]; d.y = 0f;
                m_S[i] = m_S[i - 1] + d.magnitude;
            }
            m_LimitKmh = speedLimitsKmh != null && speedLimitsKmh.Length == m_Points.Length ? speedLimitsKmh : new float[m_Points.Length];
            m_Seg = 0; Progress = 0f; Finished = false;
        }

        public void Sample(float dt, in VehicleFeedback fb, ref DriverIntent intent)
        {
            if (m_Points.Length < 2) return;
            Vector3 p = fb.Position; p.y = 0f;

            // Advance the closest segment monotonically (window of 20 segments).
            float best = float.MaxValue; int bestSeg = m_Seg; float bestT = 0f;
            for (int i = m_Seg; i < Mathf.Min(m_Points.Length - 1, m_Seg + 20); i++)
            {
                Vector3 a = Flat(m_Points[i]), b = Flat(m_Points[i + 1]);
                Vector3 ab = b - a;
                float t = Mathf.Clamp01(Vector3.Dot(p - a, ab) / Mathf.Max(ab.sqrMagnitude, 1e-6f));
                float d = (a + ab * t - p).sqrMagnitude;
                if (d < best) { best = d; bestSeg = i; bestT = t; }
            }
            m_Seg = bestSeg;
            Progress = Mathf.Lerp(m_S[m_Seg], m_S[m_Seg + 1], bestT);
            CrossTrackError = Mathf.Sqrt(best);

            float v = Mathf.Max(0f, fb.ForwardSpeed);
            float ld = Mathf.Max(MinLookAhead, v * LookAheadTime);
            Vector3 target = Flat(PointAt(Progress + ld));
            Vector3 to = target - p;
            Vector3 fwd = fb.Forward; fwd.y = 0f;
            float alpha = Vector3.SignedAngle(fwd, to, Vector3.up) * Mathf.Deg2Rad;
            float delta = Mathf.Atan(2f * Wheelbase * Mathf.Sin(alpha) / Mathf.Max(1f, to.magnitude)) * Mathf.Rad2Deg;
            LastSteer = Mathf.Clamp(delta / MaxRoadWheelAngleDeg, -1f, 1f);

            // Speed: preview curvature over the next 60 m and the posted limit.
            float vMax = TargetSpeedKmh / 3.6f;
            for (float s = 0f; s <= 60f; s += 6f)
            {
                float k = Curvature(Progress + s);
                if (k > 1e-4f)
                {
                    float vc = Mathf.Sqrt(MaxLateralAccel / k);
                    // allow braking at ~1.2 m/s² to reach vc at distance s
                    vMax = Mathf.Min(vMax, Mathf.Sqrt(vc * vc + 2f * 1.2f * s));
                }
                float lim = LimitAt(Progress + s) / 3.6f;
                if (lim > 0f) vMax = Mathf.Min(vMax, Mathf.Sqrt(lim * lim + 2f * 1.2f * s));
            }
            float remaining = Length - Progress;
            if (remaining < StopDistance) vMax = Mathf.Min(vMax, Mathf.Max(0f, remaining - 3f) / StopDistance * 6f);
            Finished = remaining < 4f;
            CommandedSpeedKmh = vMax * 3.6f;

            float e = CommandedSpeedKmh - v * 3.6f;
            intent.Steer = LastSteer;
            intent.SteerActive = true;
            intent.Throttle = Finished ? 0f : Mathf.Clamp01(e * 0.12f);
            intent.Brake = Finished ? 0.6f : e < -3f ? Mathf.Clamp01(-e * 0.06f) : 0f;
        }

        static Vector3 Flat(Vector3 v) { v.y = 0f; return v; }

        int SegmentAt(float s)
        {
            int i = Mathf.Clamp(m_Seg, 0, m_S.Length - 2);
            while (i < m_S.Length - 2 && m_S[i + 1] < s) i++;
            return i;
        }

        Vector3 PointAt(float s)
        {
            if (s >= Length) return m_Points[m_Points.Length - 1];
            int i = SegmentAt(s);
            float t = Mathf.InverseLerp(m_S[i], m_S[i + 1], s);
            return Vector3.Lerp(m_Points[i], m_Points[i + 1], t);
        }

        float LimitAt(float s) => m_LimitKmh.Length == 0 ? 0f : m_LimitKmh[Mathf.Min(SegmentAt(s), m_LimitKmh.Length - 1)];

        /// <summary>Curvature (1/m) from three points 8 m apart.</summary>
        float Curvature(float s)
        {
            Vector3 a = Flat(PointAt(s - 8f)), b = Flat(PointAt(s)), c = Flat(PointAt(s + 8f));
            float ab = (b - a).magnitude, bc = (c - b).magnitude, ca = (a - c).magnitude;
            float area2 = Mathf.Abs((b.x - a.x) * (c.z - a.z) - (b.z - a.z) * (c.x - a.x));
            float den = ab * bc * ca;
            return den > 1e-3f ? 2f * area2 / den : 0f;
        }
    }
}
