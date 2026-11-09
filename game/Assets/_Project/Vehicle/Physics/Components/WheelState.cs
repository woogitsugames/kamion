namespace Game.Vehicle.Physics
{
    /// <summary>Runtime state of one wheel end (a single wheel or a dual-tire pair).</summary>
    public sealed class WheelState
    {
        public string Name = "";
        public int AxleIndex;
        /// <summary>-1 = left, +1 = right.</summary>
        public int Side;
        public AxleDefinition Axle = null!;
        public TireModel Tire = null!;
        public int TireCount;
        public bool Steered, Driven;

        // Geometry (vehicle frame)
        public Vec3 HardpointLocal;
        public double Radius;
        public double Inertia;
        public double StaticLoad;
        public double SStatic, SpringFree;
        public double WheelbaseFromRef;

        // Suspension / contact (per fixed step)
        public bool Contact;
        public double S, SPrev;
        public bool HasPrev;
        public double Compression;      // m, positive = compressed relative to static
        public double CompressionRate;  // m/s
        public double SuspensionForce;  // N along suspension axis
        public double TireDeflection;   // m, radial tire deflection
        public Vec3 ContactPoint, Normal, Forward, Lateral;
        public double FrictionScale = 1, RollingResistanceScale = 1;
        public int SurfaceId;
        public double Fz;               // N normal load (along contact normal)

        // Tire / wheel dynamics
        public double SteerAngle;       // rad
        public double Omega;            // rad/s, positive = rolling forward
        public double Ux, Uy;           // contact patch deflection states [m]
        public double Vx, Vy;           // contact point velocity in tire frame [m/s]
        public double Fx, Fy;           // N, averaged over substeps (tire frame)
        public double SlipRatio;        // transient kappa'
        public double SlipAngle;        // transient alpha' [rad]
        public double KinematicSlip;    // (omega R - vx)/max(|vx|, 0.5) for ABS / telemetry
        public double Mu;               // available peak mu
        public double AligningTorque;   // N m (estimate, steering feedback)

        // Brakes
        public double BrakePressure;    // 0..1 normalized service pressure
        public double AbsFactor = 1;    // 0..1 ABS modulation
        public double BrakeTorque;      // N m capacity applied this step (service/parking)
        public double DriveTorque;      // N m from driveline (averaged)
        public double BrakeImpulseAcc;  // PGS accumulator (internal)
    }
}
