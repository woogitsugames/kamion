using System.Diagnostics;
using Game.Vehicle.Physics;
using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Unity adapter for the pure C# <see cref="VehicleModel"/> (docs/PHYSICS_VALIDATION.md §2).
    /// PhysX owns the rigid body (integration, gravity, chassis–world collisions); the model owns wheels,
    /// suspension, tires, driveline and brakes and returns forces at world contact points, which are applied
    /// here with <see cref="Rigidbody.AddForceAtPosition(Vector3, Vector3, ForceMode)"/>.
    ///
    /// - The GameObject origin is the vehicle-frame origin: ground below the rear-axle centre at design ride height.
    /// - Mass, centre of mass and inertia tensor come from the definition (never from colliders).
    /// - Fixed step: called from FixedUpdate (project fixedDeltaTime = 0.01 s). When
    ///   <see cref="UnityEngine.Physics.simulationMode"/> is Script, the owner calls <see cref="Tick"/> before Physics.Simulate.
    /// - Rendering uses Rigidbody interpolation; wheels/cab are interpolated by <see cref="VehicleVisuals"/>.
    /// - Zero GC allocations per step (verified by a PlayMode test).
    /// </summary>
    [DefaultExecutionOrder(-50)]
    [RequireComponent(typeof(Rigidbody))]
    public sealed class VehicleBody : MonoBehaviour
    {
        [SerializeField] VehicleDataAsset data;
        [SerializeField, Range(1, 8)] int substeps = 4;
        [SerializeField, Range(1, 31)] int contactRays = 15;

        Rigidbody m_Rb;
        UnityGroundQuery m_Ground;
        long m_StepTicks;
        double m_StepMicrosAvg;

        public VehicleModel Model { get; private set; }
        public Rigidbody Body => m_Rb;
        public VehicleDataAsset Data => data;
        public bool Initialized => Model != null;
        public UnityGroundQuery Ground => m_Ground;

        /// <summary>Driver command used for the next fixed step (set by the input bridge or by tests).</summary>
        public DriverInput Input;

        /// <summary>Wall-clock cost of the last solver step + force application [µs].</summary>
        public double LastStepMicros { get; private set; }
        /// <summary>Exponential moving average (≈1 s) of <see cref="LastStepMicros"/>.</summary>
        public double AverageStepMicros => m_StepMicrosAvg;
        public long StepCount { get; private set; }
        /// <summary>Simulation time of the vehicle [s] (sum of fixed steps).</summary>
        public double SimTime => Model != null ? Model.Time : 0;

        public float SpeedKmh => Model != null ? (float)(Model.SpeedForward * 3.6) : 0f;

        /// <summary>Assigns the data asset without initialising (editor prefab builder; Awake initialises at play).</summary>
        public void SetDataForBuilder(VehicleDataAsset d) => data = d;

        void Awake()
        {
            if (data != null) Initialize(data);
        }

        /// <summary>Builds the solver and configures the Rigidbody. Safe to call again (resets the vehicle state).</summary>
        public void Initialize(VehicleDataAsset d)
        {
            data = d;
            m_Rb = GetComponent<Rigidbody>();
            Model = data.CreateModel(new SolverSettings { substeps = substeps, contactRays = contactRays });
            m_Ground = new UnityGroundQuery(UnityGroundQuery.ResolveVehicleLayer());
            Model.Gravity = UnityEngine.Physics.gravity.ToCore();   // the model's predictors must use the host's gravity
            Model.InitParking(true);                      // spawn parked: spring brakes applied, no initial lag

            var mp = Model.MassProps;
            m_Rb.mass = (float)mp.Mass;
            m_Rb.automaticCenterOfMass = false;
            m_Rb.automaticInertiaTensor = false;
            m_Rb.centerOfMass = mp.CenterOfMass.ToUnity();
            InertiaUtil.Diagonalize(mp.Inertia, out Vector3 principal, out Quaternion rot);
            m_Rb.inertiaTensor = principal;
            m_Rb.inertiaTensorRotation = rot;
            m_Rb.useGravity = true;
            m_Rb.linearDamping = 0f;
            m_Rb.angularDamping = 0f;
            m_Rb.maxAngularVelocity = 50f;
            m_Rb.sleepThreshold = 0f; // the solver holds the truck on brakes; never let PhysX sleep-snap it
            m_Rb.interpolation = RigidbodyInterpolation.Interpolate;
            m_Rb.collisionDetectionMode = CollisionDetectionMode.Discrete;
            Input = new DriverInput { Selector = GearSelector.Drive, ParkingBrake = true };
            StepCount = 0;
            m_StepMicrosAvg = 0;
        }

        /// <summary>Moves the vehicle (at rest) to a new pose and resets the solver state.</summary>
        public void ResetPose(Vector3 position, Quaternion rotation)
        {
            if (m_Rb == null) m_Rb = GetComponent<Rigidbody>();
            m_Rb.linearVelocity = Vector3.zero;
            m_Rb.angularVelocity = Vector3.zero;
            m_Rb.position = position;
            m_Rb.rotation = rotation;
            transform.SetPositionAndRotation(position, rotation);
            var input = Input;
            Initialize(data);
            Input = input;
        }

        void FixedUpdate()
        {
            if (UnityEngine.Physics.simulationMode != SimulationMode.FixedUpdate) return;
            Tick(Time.fixedDeltaTime);
        }

        /// <summary>One solver step: read the rigid body, run the model, apply forces at contact points.</summary>
        public void Tick(float dt)
        {
            if (Model == null) return;
            long t0 = Stopwatch.GetTimestamp();

            var state = new ChassisState
            {
                Position = m_Rb.position.ToCore(),
                Rotation = m_Rb.rotation.ToCore(),
                CenterOfMassWorld = m_Rb.worldCenterOfMass.ToCore(),
                LinearVelocity = m_Rb.linearVelocity.ToCore(),
                AngularVelocity = m_Rb.angularVelocity.ToCore(),
            };
            Model.Step(dt, state, Input, m_Ground);
            // Shift requests are edge-triggered in the core: deliver each pulse to exactly one step.
            Input.ShiftUp = false;
            Input.ShiftDown = false;
            var forces = Model.Forces;
            for (int i = 0; i < Model.ForceCount; i++)
                m_Rb.AddForceAtPosition(forces[i].Force.ToUnity(), forces[i].Point.ToUnity(), ForceMode.Force);

            m_StepTicks = Stopwatch.GetTimestamp() - t0;
            LastStepMicros = m_StepTicks * 1e6 / Stopwatch.Frequency;
            m_StepMicrosAvg = StepCount == 0 ? LastStepMicros : m_StepMicrosAvg + (LastStepMicros - m_StepMicrosAvg) * 0.01;
            StepCount++;
        }
    }
}
