using Game.Vehicle.Physics;
using UnityEngine;

namespace Game.Vehicle.Runtime
{
    /// <summary>Load cases offered in the driving lab (docs/03 Stage 2: empty / 24 t; plus the 40 t gross combination of the validation set).</summary>
    public enum CargoPreset { Empty = 0, Cargo24t = 1, Gross40t = 2 }

    public static class CargoPresets
    {
        /// <summary>
        /// Cargo for a preset, identical to the .NET runner (ScenarioRunner.CargoFor): Gross40t = 40.0 t gross
        /// combination mass (cargo = 40 000 kg − tractor − empty trailer), CoG height 0 = floor + 1 m (2 m block);
        /// Cargo24t = 24 000 kg with the same default CoG.
        /// </summary>
        public static CargoDefinition Create(CargoPreset preset, double tractorMassKg, TrailerDefinition trailer)
        {
            var c = new CargoDefinition();
            switch (preset)
            {
                case CargoPreset.Cargo24t: c.massKg = 24000; break;
                case CargoPreset.Gross40t: c.massKg = 40000 - tractorMassKg - MassProperties.Compute(trailer.massElements).Mass; break;
                default: c.massKg = 0; break;
            }
            return c;
        }

        public static string DisplayNamePl(CargoPreset p) =>
            p == CargoPreset.Cargo24t ? "24 t ładunku" : p == CargoPreset.Gross40t ? "zestaw 40 t" : "pusta";
    }

    /// <summary>
    /// Unity side of a semi-trailer (docs/PHYSICS_VALIDATION.md §2, ADR 0008 / 0009): one PhysX Rigidbody whose mass,
    /// centre of mass and inertia come from <see cref="TrailerModel.MassProps"/> (cargo included). The trailer has
    /// no FixedUpdate of its own: the tractor's <see cref="VehicleBody"/> steps the whole <see cref="CombinationModel"/>
    /// (both bodies + fifth wheel) and applies the force/torque pair to this body. There is NO PhysX joint.
    /// GameObject origin = trailer frame origin: ground below the kingpin at design ride height, +Z forward.
    /// </summary>
    [DefaultExecutionOrder(-49)]
    [RequireComponent(typeof(Rigidbody))]
    public sealed class TrailerBody : MonoBehaviour
    {
        [SerializeField] VehicleDataAsset data;

        Rigidbody m_Rb;

        public TrailerModel Model { get; private set; }
        public Rigidbody Body => m_Rb != null ? m_Rb : (m_Rb = GetComponent<Rigidbody>());
        public VehicleDataAsset Data => data;
        public bool Initialized => Model != null;
        public CargoDefinition Cargo { get; private set; }
        public CargoPreset Preset { get; private set; }

        public void SetDataForBuilder(VehicleDataAsset d) => data = d;

        void Awake()
        {
            if (data != null && Model == null) Initialize(data, CargoPreset.Empty, 0);
        }

        /// <summary>(Re)builds the trailer solver for a load case and configures the Rigidbody. Resets the trailer state.</summary>
        public void Initialize(VehicleDataAsset d, CargoPreset preset, double tractorMassKg, SolverSettings settings = null)
        {
            data = d;
            Preset = preset;
            Cargo = CargoPresets.Create(preset, tractorMassKg > 0 ? tractorMassKg : MassProperties.Compute(data.Vehicle.massElements).Mass, data.Trailer);
            Model = data.CreateTrailer(Cargo, settings);
            var rb = Body;
            var mp = Model.MassProps;
            rb.mass = (float)mp.Mass;
            rb.automaticCenterOfMass = false;
            rb.automaticInertiaTensor = false;
            rb.centerOfMass = mp.CenterOfMass.ToUnity();
            InertiaUtil.Diagonalize(mp.Inertia, out Vector3 principal, out Quaternion rot);
            rb.inertiaTensor = principal;
            rb.inertiaTensorRotation = rot;
            rb.useGravity = true;
            rb.linearDamping = 0f;
            rb.angularDamping = 0f;
            rb.maxAngularVelocity = 50f;
            rb.sleepThreshold = 0f;
            rb.interpolation = RigidbodyInterpolation.Interpolate;
            rb.collisionDetectionMode = CollisionDetectionMode.Discrete;
        }

        /// <summary>Teleports the trailer (at rest) to a pose. Call <see cref="Physics.SyncTransforms"/> before raycasting.</summary>
        public void SetPose(Vector3 position, Quaternion rotation)
        {
            var rb = Body;
            rb.linearVelocity = Vector3.zero;
            rb.angularVelocity = Vector3.zero;
            rb.position = position;
            rb.rotation = rotation;
            transform.SetPositionAndRotation(position, rotation);
        }

        /// <summary>Gives the trailer (at its current pose) a forward speed and spinning wheels (scripted starts).</summary>
        public void SetMoving(float speed)
        {
            Body.linearVelocity = transform.forward * speed;
            Model.InitializeMoving(speed);
        }

        public ChassisState State
        {
            get
            {
                var rb = Body;
                return new ChassisState
                {
                    Position = rb.position.ToCore(),
                    Rotation = rb.rotation.ToCore(),
                    CenterOfMassWorld = rb.worldCenterOfMass.ToCore(),
                    LinearVelocity = rb.linearVelocity.ToCore(),
                    AngularVelocity = rb.angularVelocity.ToCore(),
                };
            }
        }
    }
}
