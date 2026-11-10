using System.Globalization;
using Game.Vehicle.Runtime;
using Game.World;
using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// World-edge safety net of a world scene (ADR 0082; owner recording 2026-11-10: the combination drove off the end
    /// of the region at 105 km/h and fell through the void). Every <see cref="checkInterval"/> in the fixed step it
    /// - remembers poses at which the tractor stood upright on a paved surface, well inside the region
    ///   (<see cref="SafePoseBuffer"/>),
    /// - warns once when the vehicle approaches the region edge,
    /// - and when <see cref="WorldExitMonitor"/> reports that the vehicle left the world (beyond the edge, no collision
    ///   below, free fall) puts the combination back, parked, on the last safe pose and tells the driver why.
    /// The reset is a recovery after a failure of the world, not a way of moving the vehicle: driving is never touched
    /// while the monitor reports None. No allocations in the fixed step (the log line and status only on an event).
    /// </summary>
    [DefaultExecutionOrder(-150)]
    public sealed class WorldSafetyNet : MonoBehaviour
    {
        public DrivingLabBootstrap bootstrap;
        public VehicleBody vehicle;
        public WorldRegionRoot region;
        public WorldBoundary boundary;

        [Tooltip("Seconds between checks (fixed-step time)")] public float checkInterval = 0.1f;
        [Tooltip("Collision probe depth under the vehicle origin [m]")] public float probeDepth = 60f;
        [Tooltip("Safe poses are only recorded this far inside the region edge [m] (closures stand 60 m inside)")]
        public float safeEdgeDistance = 120f;
        [Tooltip("Seconds between recorded safe poses")] public float safeRecordInterval = 1f;
        [Tooltip("A restored pose must be at least this old [s]")] public float safeMinAge = 2.5f;
        [Tooltip("Distance to the region edge at which the driver is warned [m]")] public float warnDistance = 260f;

        public const string MsgEdgeAhead = "Koniec mapy za ok. 250 m: droga zamknięta, zwolnij";
        public const string MsgOutOfBounds = "Koniec mapy: zestaw ustawiony z powrotem na drodze";
        public const string MsgFell = "Zestaw wypadł poza świat: ustawiony z powrotem na drodze";

        public readonly WorldExitMonitor Monitor = new WorldExitMonitor();
        public readonly SafePoseBuffer SafePoses = new SafePoseBuffer(32);
        /// <summary>Number of recoveries since the scene started and the reason of the last one (tests, telemetry).</summary>
        public int ResetCount { get; private set; }
        public WorldExitReason LastReason { get; private set; }
        public float LastInsideDistance { get; private set; }
        public bool EdgeWarningShown { get; private set; }

        Vector2 m_Min, m_Max;
        bool m_HasBounds;
        float m_Accum, m_SinceRecord, m_PrevInside = float.MaxValue;
        int m_Mask;
        Collider m_LastCollider;
        bool m_LastPaved;

        void Start()
        {
            if (region == null) region = FindAnyObjectByType<WorldRegionRoot>();
            if (boundary == null && region != null) boundary = region.GetComponent<WorldBoundary>();
            if (boundary != null && boundary.maxEN.x > boundary.minEN.x) { m_Min = boundary.minEN; m_Max = boundary.maxEN; m_HasBounds = true; }
            else m_HasBounds = WorldBoundary.TryChunkBounds(region, out m_Min, out m_Max);
            int mask = Physics.DefaultRaycastLayers;
            int vl = UnityGroundQuery.ResolveVehicleLayer();
            if (vl >= 0) mask &= ~(1 << vl);
            m_Mask = mask;
            if (!m_HasBounds) Debug.LogWarning("[SAFETY] no region bounds: only the fall / no-ground checks are active");
        }

        void FixedUpdate()
        {
            if (vehicle == null || !vehicle.Initialized) return;
            m_Accum += Time.fixedDeltaTime;
            if (m_Accum < checkInterval) return;
            float dt = m_Accum;
            m_Accum = 0f;
            Check(dt);
        }

        /// <summary>One check (public for tests that step physics themselves).</summary>
        public void Check(float dt)
        {
            var tr = vehicle.transform;
            Vector3 p = tr.position;
            float inside = float.MaxValue;
            if (m_HasBounds && region != null)
            {
                Vector3 l = region.transform.InverseTransformPoint(p);
                inside = WorldBoundary.InsideDistance(m_Min, m_Max, l.x, l.z);
            }
            LastInsideDistance = inside;
            bool ground = Physics.Raycast(p + Vector3.up * 2.5f, Vector3.down, out RaycastHit hit, probeDepth + 2.5f, m_Mask, QueryTriggerInteraction.Ignore);
            var rb = vehicle.Body;
            float vy = rb != null ? rb.linearVelocity.y : 0f;

            var reason = Monitor.Step(dt, inside, ground, vy);
            if (reason != WorldExitReason.None) { Recover(reason, p); return; }

            // Edge warning: once per approach, only while closing in.
            if (inside < warnDistance && inside < m_PrevInside - 0.05f && !EdgeWarningShown && Mathf.Abs(vehicle.SpeedKmh) > 15f)
            {
                EdgeWarningShown = true;
                if (bootstrap != null) bootstrap.ShowStatus(MsgEdgeAhead, 6f);
            }
            else if (inside > warnDistance + 60f) EdgeWarningShown = false;
            m_PrevInside = inside;

            // Safe pose: upright, on a paved collider, close to the ground, well inside the region.
            m_SinceRecord += dt;
            if (m_SinceRecord < safeRecordInterval || !ground || inside < safeEdgeDistance) return;
            if (tr.up.y < 0.94f || hit.distance > 4f || Mathf.Abs(vy) > 2f) return;
            if (!IsPaved(hit.collider)) return;
            m_SinceRecord = 0f;
            SafePoses.Record(Time.time, hit.point, tr.eulerAngles.y);
        }

        bool IsPaved(Collider c)
        {
            if (c == m_LastCollider) return m_LastPaved;
            m_LastCollider = c;
            m_LastPaved = !c.TryGetComponent(out GroundSurface gs) || gs.kind != SurfaceKind.Grass;
            return m_LastPaved;
        }

        void Recover(WorldExitReason reason, Vector3 from)
        {
            ResetCount++;
            LastReason = reason;
            Monitor.Reset();
            m_PrevInside = float.MaxValue;
            m_SinceRecord = 0f;
            string msg = reason == WorldExitReason.OutOfBounds ? MsgOutOfBounds : MsgFell;
            var ci = CultureInfo.InvariantCulture;
            if (SafePoses.TryGet(Time.time, safeMinAge, out var pose))
            {
                Debug.Log(string.Format(ci, "[SAFETY] reset #{0} reason={1} from=({2:F1},{3:F1},{4:F1}) speed={5:F0} km/h -> safe pose ({6:F1},{7:F1},{8:F1}) yaw={9:F0} age={10:F1} s",
                    ResetCount, reason, from.x, from.y, from.z, vehicle.SpeedKmh, pose.position.x, pose.position.y, pose.position.z, pose.yawDeg, Time.time - pose.time));
                if (bootstrap != null) bootstrap.RecoverTo(pose.position, Quaternion.Euler(0f, pose.yawDeg, 0f), msg);
            }
            else
            {
                Debug.Log(string.Format(ci, "[SAFETY] reset #{0} reason={1} from=({2:F1},{3:F1},{4:F1}) speed={5:F0} km/h -> scene spawn (no safe pose yet)",
                    ResetCount, reason, from.x, from.y, from.z, vehicle.SpeedKmh));
                if (bootstrap != null) bootstrap.RecoverToSpawn(msg);
            }
        }
    }
}
