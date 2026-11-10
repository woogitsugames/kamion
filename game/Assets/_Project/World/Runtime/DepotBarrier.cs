using UnityEngine;

namespace Game.World
{
    /// <summary>
    /// Automatic boom barrier of a depot gate (map audit MA-003, ADR 0071 r10). Lives on the boom: the transform origin
    /// is the hinge, the boom runs along local +x, the lane crosses it along local z.
    ///
    /// Behaviour (all in FixedUpdate, no allocations after Awake):
    ///  * presence loop: a box over the lane from <see cref="approachM"/> before the boom to <see cref="exitM"/> behind
    ///    it (travel direction = <see cref="travelSign"/> x local z). Any non-kinematic rigidbody in it (tractor,
    ///    trailer, a car) keeps the boom open, so it never comes down on a trailer; it closes
    ///    <see cref="closeDelayS"/> after the loop is free and re-opens when something enters while it is closing.
    ///  * the boom is a kinematic rigidbody rotated about the hinge (MoveRotation, eased), so a closed or moving boom
    ///    is a solid obstacle for slow contacts.
    ///  * break-away: when a body is about to hit (or hits) the boom with a closing speed above
    ///    <see cref="breakSpeedMps"/>, the boom is released as a free dynamic body of <see cref="boomMassKg"/> just
    ///    before the contact, so the impact is solved by the physics engine between the vehicle and a light boom
    ///    (no immovable wall at speed, no teleport). A released boom stays where it falls; the drive stops.
    /// Timing and masses are WORKING_VALUE (typical 6 m boom drives open in 3-6 s; aluminium boom ~2.3 kg/m).
    /// </summary>
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Rigidbody))]
    public sealed class DepotBarrier : MonoBehaviour
    {
        public enum BarrierState { Closed, Opening, Open, Closing, Broken }

        [Tooltip("Boom length from the hinge (m)")]
        public float boomLengthM = 5.85f;
        [Tooltip("Raised angle (deg)")]
        public float openAngleDeg = 85f;
        [Tooltip("Time to raise the boom (s). WORKING_VALUE: 6 m boom drives 3-6 s")]
        public float openTimeS = 3.5f;
        [Tooltip("Time to lower the boom (s). WORKING_VALUE")]
        public float closeTimeS = 4f;
        [Tooltip("Presence loop: length before the boom, against the travel direction (m)")]
        public float approachM = 25f;
        [Tooltip("Presence loop: length behind the boom (m); the boom closes when the whole combination is past it")]
        public float exitM = 6f;
        [Tooltip("+1: traffic runs along local +z, -1: along local -z")]
        public float travelSign = 1f;
        [Tooltip("Delay between the loop becoming free and the boom starting down (s). WORKING_VALUE")]
        public float closeDelayS = 1.5f;
        [Tooltip("Closing speed above which the boom breaks away instead of blocking (m/s). WORKING_VALUE")]
        public float breakSpeedMps = 1.5f;
        [Tooltip("Mass of the released boom (kg). WORKING_VALUE")]
        public float boomMassKg = 14f;
        [Tooltip("false: the drive ignores the loop (tests, a locked gate)")]
        public bool automatic = true;

        public BarrierState State { get; private set; } = BarrierState.Closed;
        /// <summary>Boom angle above horizontal (deg).</summary>
        public float AngleDeg { get; private set; }
        /// <summary>True while a body occupies the presence loop (last sensor pass).</summary>
        public bool Occupied { get; private set; }
        /// <summary>Colliders returned by the last loop query (static world included); must stay below the buffer size.</summary>
        public int LoopColliders { get; private set; }
        public const int LoopBufferSize = 128;

        const float LoopHalfHeight = 2.5f;
        const float LoopSideMargin = 0.4f;

        // The loop box also returns the static world under it (road, kerbs, yard, props); WorldCBarrierTests reports the count.
        readonly Collider[] m_Hits = new Collider[LoopBufferSize];
        Rigidbody m_Body;
        Collider m_BoomCollider;
        Quaternion m_BaseRotation;
        Vector3 m_HingePosition;
        float m_Progress;          // 0 closed .. 1 open
        float m_FreeTime;

        void Awake()
        {
            m_Body = GetComponent<Rigidbody>();
            m_Body.isKinematic = true;
            m_Body.useGravity = false;
            m_Body.interpolation = RigidbodyInterpolation.Interpolate;
            m_BoomCollider = GetComponent<Collider>();
            m_BaseRotation = transform.rotation;
            m_HingePosition = transform.position;
        }

        void FixedUpdate()
        {
            // Script mode (tests stepping Physics.Simulate themselves): the owner calls Tick before every step, as for VehicleBody.
            if (Physics.simulationMode != SimulationMode.FixedUpdate) return;
            Tick(Time.fixedDeltaTime);
        }

        /// <summary>One drive + sensor step. Called from FixedUpdate; by the owner of the loop when Physics.simulationMode is Script.</summary>
        public void Tick(float dt)
        {
            if (State == BarrierState.Broken) return;
            Sense(dt);
            if (State == BarrierState.Broken) return;
            if (automatic)
            {
                if (Occupied)
                {
                    m_FreeTime = 0f;
                    if (State == BarrierState.Closed || State == BarrierState.Closing) State = BarrierState.Opening;
                }
                else if (State == BarrierState.Open)
                {
                    m_FreeTime += dt;
                    if (m_FreeTime >= closeDelayS) State = BarrierState.Closing;
                }
            }
            if (State == BarrierState.Opening)
            {
                m_Progress = Mathf.Min(1f, m_Progress + dt / Mathf.Max(0.1f, openTimeS));
                if (m_Progress >= 1f) { State = BarrierState.Open; m_FreeTime = 0f; }
            }
            else if (State == BarrierState.Closing)
            {
                m_Progress = Mathf.Max(0f, m_Progress - dt / Mathf.Max(0.1f, closeTimeS));
                if (m_Progress <= 0f) State = BarrierState.Closed;
            }
            // eased drive (soft start / soft stop of the gear motor)
            float s = m_Progress * m_Progress * (3f - 2f * m_Progress);
            AngleDeg = openAngleDeg * s;
            m_Body.MoveRotation(m_BaseRotation * Quaternion.AngleAxis(AngleDeg, Vector3.forward));
        }

        /// <summary>Opens / closes the boom by hand (tests, scripted gates). Ignored once the boom is broken.</summary>
        public void Command(bool open)
        {
            if (State == BarrierState.Broken) return;
            if (open && State != BarrierState.Open) State = BarrierState.Opening;
            else if (!open && State != BarrierState.Closed) State = BarrierState.Closing;
        }

        void Sense(float dt)
        {
            // loop box in the frame of the closed boom
            float zc = travelSign * (exitM - approachM) * 0.5f;
            var half = new Vector3(boomLengthM * 0.5f + LoopSideMargin, LoopHalfHeight, (approachM + exitM) * 0.5f);
            Vector3 centre = m_HingePosition + m_BaseRotation * new Vector3(boomLengthM * 0.5f, LoopHalfHeight - 0.9f, zc);
            int n = Physics.OverlapBoxNonAlloc(centre, half, m_Hits, m_BaseRotation, ~0, QueryTriggerInteraction.Ignore);
            LoopColliders = n;
            bool any = false;
            Vector3 mid = m_Body.worldCenterOfMass;
            for (int i = 0; i < n; i++)
            {
                var c = m_Hits[i];
                m_Hits[i] = null;
                var rb = c.attachedRigidbody;
                if (rb == null || rb == m_Body || rb.isKinematic) continue;
                any = true;
                if (m_BoomCollider == null) continue;
                // imminent hit at speed: release the boom before the contact (see class summary)
                if (c is MeshCollider mc && !mc.convex) continue;
                Vector3 onBody = c.ClosestPoint(mid);
                Vector3 onBoom = m_BoomCollider.ClosestPoint(onBody);
                onBody = c.ClosestPoint(onBoom);
                Vector3 gap = onBoom - onBody;
                float d = gap.magnitude;
                if (d < 1e-4f) continue;            // already touching: OnCollisionEnter decides
                float closing = Vector3.Dot(rb.GetPointVelocity(onBody), gap / d);
                if (closing > breakSpeedMps && d < Mathf.Max(0.3f, closing * dt * 3f)) { Release(); break; }
            }
            Occupied = any;
        }

        void OnCollisionEnter(Collision collision)
        {
            if (State == BarrierState.Broken) return;
            var rb = collision.rigidbody;
            if (rb == null || rb.isKinematic) return;
            if (collision.relativeVelocity.magnitude > breakSpeedMps) Release();
        }

        void Release()
        {
            State = BarrierState.Broken;
            m_Body.interpolation = RigidbodyInterpolation.None;
            m_Body.isKinematic = false;
            m_Body.mass = boomMassKg;
            m_Body.useGravity = true;
            m_Body.linearDamping = 0.05f;
            m_Body.angularDamping = 0.3f;
            m_Body.WakeUp();
        }
    }
}
