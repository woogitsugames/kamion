namespace Game.Vehicle.Physics
{
    /// <summary>Result of a ground ray query.</summary>
    public struct GroundHit
    {
        public Vec3 Point;
        /// <summary>Unit surface normal at the hit point.</summary>
        public Vec3 Normal;
        public double Distance;
        /// <summary>Friction scale relative to the tire's reference surface (dry asphalt = 1).</summary>
        public double FrictionScale;
        /// <summary>Rolling-resistance multiplier (asphalt = 1).</summary>
        public double RollingResistanceScale;
        /// <summary>Opaque surface id for telemetry/audio (e.g. index into a surface table).</summary>
        public int SurfaceId;
    }

    /// <summary>
    /// World query used by the wheel contact model. Implementations: analytic ground in the .NET runner,
    /// Physics.Raycast against the smooth road collision mesh in the Unity adapter.
    /// Must not allocate.
    /// </summary>
    public interface IGroundQuery
    {
        /// <summary>Casts a ray; direction is unit length. Returns false when nothing is hit within maxDistance.</summary>
        bool Raycast(Vec3 origin, Vec3 direction, double maxDistance, out GroundHit hit);
    }

    /// <summary>
    /// Read-only snapshot of the chassis rigid body at the start of a fixed step (world frame).
    /// Unity adapter fills it from Rigidbody (position, rotation, velocity, angularVelocity, worldCenterOfMass).
    /// </summary>
    public struct ChassisState
    {
        /// <summary>World position of the vehicle-frame origin.</summary>
        public Vec3 Position;
        public Quat Rotation;
        /// <summary>World position of the centre of mass.</summary>
        public Vec3 CenterOfMassWorld;
        /// <summary>Linear velocity of the centre of mass.</summary>
        public Vec3 LinearVelocity;
        /// <summary>Angular velocity (world frame, rad/s).</summary>
        public Vec3 AngularVelocity;

        public Vec3 PointVelocity(Vec3 worldPoint) =>
            LinearVelocity + Vec3.Cross(AngularVelocity, worldPoint - CenterOfMassWorld);

        public Vec3 LocalToWorld(Vec3 local) => Position + Rotation * local;
    }

    public enum GearSelector { Neutral = 0, Drive = 1, Reverse = 2 }

    /// <summary>Driver commands for one fixed step (already filtered by the input layer).</summary>
    public struct DriverInput
    {
        /// <summary>Accelerator pedal 0..1.</summary>
        public double Throttle;
        /// <summary>Service brake pedal 0..1.</summary>
        public double Brake;
        /// <summary>Normalized steering command -1..1 (positive = right turn).</summary>
        public double Steer;
        public bool ParkingBrake;
        public GearSelector Selector;
        /// <summary>
        /// Endurance brake lever: 0 = off, 1 = engine brake, 2..(1+retarder stages) = engine brake + retarder
        /// at increasing fractions of its maximum torque.
        /// </summary>
        public int RetarderLever;
        /// <summary>Downhill speed control ("brake cruise") set speed [km/h], 0 = off: the endurance brakes are modulated to hold it (no service brake).</summary>
        public double BrakeCruiseKmh;
        /// <summary>AMT manual mode (driver chooses the gear; the AMT still operates the clutch and protects the engine).</summary>
        public bool ManualMode;
        /// <summary>Shift requests (manual mode). Edge-triggered: a request is consumed on the step it turns true.</summary>
        public bool ShiftUp, ShiftDown;
    }

    /// <summary>Force applied at a world point (output of the solver for one fixed step).</summary>
    public struct AppliedForce
    {
        public Vec3 Force;
        public Vec3 Point;
    }
}
