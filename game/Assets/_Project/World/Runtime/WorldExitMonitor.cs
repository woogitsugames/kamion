using UnityEngine;

namespace Game.World
{
    public enum WorldExitReason { None = 0, OutOfBounds = 1, NoGround = 2, Falling = 3 }

    /// <summary>
    /// Decides when the player's vehicle has left the drivable world (ADR 0082): beyond the region rectangle, over a
    /// hole in the collision, or in free fall. Pure logic (no scene access), fed once per check by WorldSafetyNet;
    /// no allocations. Debounced so a wheel in the air over a kerb or a crest never triggers it.
    /// All thresholds are WORKING_VALUE (gameplay safety net, not vehicle data).
    /// </summary>
    public sealed class WorldExitMonitor
    {
        /// <summary>The vehicle origin may come this close to the region edge [m] (the terrain skirt starts at the edge).</summary>
        public float edgeMarginM = 3f;
        /// <summary>No collision under the vehicle within the probe depth for this long [s] = hole / void.</summary>
        public float noGroundTime = 0.35f;
        /// <summary>Sink rate that no road in the region can produce [m/s] (20 m/s = 2 s of free fall), held for fallTime.</summary>
        public float fallSpeed = 18f;
        public float fallTime = 0.25f;

        float m_NoGround, m_Falling;

        public void Reset() { m_NoGround = 0f; m_Falling = 0f; }

        /// <param name="insideDistance">WorldBoundary.InsideDistance of the vehicle origin [m] (negative = outside).</param>
        /// <param name="groundBelow">A ground collider was found under the vehicle within the probe depth.</param>
        /// <param name="verticalSpeed">World vertical speed of the body [m/s] (negative = sinking).</param>
        public WorldExitReason Step(float dt, float insideDistance, bool groundBelow, float verticalSpeed)
        {
            if (insideDistance < edgeMarginM) return WorldExitReason.OutOfBounds;
            m_NoGround = groundBelow ? 0f : m_NoGround + dt;
            if (m_NoGround >= noGroundTime) return WorldExitReason.NoGround;
            m_Falling = verticalSpeed < -fallSpeed ? m_Falling + dt : 0f;
            if (m_Falling >= fallTime) return WorldExitReason.Falling;
            return WorldExitReason.None;
        }
    }

    /// <summary>
    /// Ring buffer of recent poses at which the vehicle stood safely on a road (ADR 0082). The safety net puts the
    /// combination back on the newest pose that is old enough (so a pose recorded on the way out is not restored).
    /// Fixed capacity, no allocations after construction.
    /// </summary>
    public sealed class SafePoseBuffer
    {
        public struct Pose { public Vector3 position; public float yawDeg; public float time; }

        readonly Pose[] m_Poses;
        int m_Head, m_Count;

        public SafePoseBuffer(int capacity = 32) { m_Poses = new Pose[Mathf.Max(2, capacity)]; }

        public int Count => m_Count;
        public void Clear() { m_Head = 0; m_Count = 0; }

        public void Record(float time, Vector3 position, float yawDeg)
        {
            m_Poses[m_Head] = new Pose { position = position, yawDeg = yawDeg, time = time };
            m_Head = (m_Head + 1) % m_Poses.Length;
            if (m_Count < m_Poses.Length) m_Count++;
        }

        /// <summary>Newest pose recorded at least <paramref name="minAge"/> seconds before <paramref name="now"/>.</summary>
        public bool TryGet(float now, float minAge, out Pose pose)
        {
            for (int k = 1; k <= m_Count; k++)
            {
                int i = (m_Head - k + m_Poses.Length * 2) % m_Poses.Length;
                if (now - m_Poses[i].time >= minAge) { pose = m_Poses[i]; return true; }
            }
            pose = default;
            return false;
        }
    }
}
