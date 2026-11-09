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
        /// <summary>Static load of the current configuration (solo / coupled) [N].</summary>
        public double StaticLoad;
        /// <summary>Load at which the wheel sits at the static (design) suspension position [N].</summary>
        public double ReferenceLoad;
        public double SStatic;
        public double WheelbaseFromRef;

        // Suspension / contact (per fixed step)
        public bool Contact;
        public double S, SPrev;
        public bool HasPrev;
        public double Compression;      // m, positive = compressed relative to static
        public double CompressionRate;  // m/s
        public double SuspensionForce;  // N along suspension axis
        /// <summary>Spring force at the static position [N]: constant for steel springs, levelled bellows force for air springs.</summary>
        public double Preload;
        public double TireDeflection;   // m, radial tire deflection
        public Vec3 ContactPoint, Normal, Forward, Lateral;
        public double FrictionScale = 1, RollingResistanceScale = 1;
        public int SurfaceId;
        public double Fz;               // N normal load (along contact normal)

        // Tire / wheel dynamics
        public double SteerAngle;       // rad
        public double Omega;            // rad/s, positive = rolling forward
        public double OmegaPrevStep;
        /// <summary>Tread acceleration (omega rate * R) over the last fixed step [m/s^2] (ABS signal).</summary>
        public double TreadAccel;
        public double Ux, Uy;           // contact patch deflection states [m]
        public double Vx, Vy;           // contact point velocity in tire frame [m/s]
        public double Fx, Fy;           // N, averaged over substeps (tire frame)
        public double SlipRatio;        // transient kappa'
        public double SlipAngle;        // transient alpha' [rad]
        public double KinematicSlip;    // (omega R - vx)/max(|vx|, 0.5) for ABS / telemetry
        public double Mu;               // available peak mu
        public double AligningTorque;   // N m (estimate, steering feedback)

        // Brakes
        /// <summary>Service brake chamber pressure [bar] (second lag stage = the chamber).</summary>
        public double ChamberPressure;
        /// <summary>First lag stage pressure (line / relay) [bar] for axles with a cascaded lag.</summary>
        public double LinePressure;
        /// <summary>Spring brake chamber pressure [bar] (0 = spring fully applied).</summary>
        public double SpringChamberPressure;
        /// <summary>ABS modulator mode: 0 = pass/apply, 1 = hold, 2 = dump, 3 = slow re-apply.</summary>
        public int AbsMode;
        public bool AbsActive;
        /// <summary>Normalised brake pressure (chamber / max) for telemetry and Stage 1 compatibility.</summary>
        public double BrakePressure;
        /// <summary>Kept for Stage 1 telemetry: 1 when ABS is not modulating, else the modulated fraction of demand.</summary>
        public double AbsFactor = 1;
        public double LoadSensingFactor = 1;
        public double BrakeTorque;      // N m capacity applied this step (service/parking)
        public double DriveTorque;      // N m from driveline (averaged)
        public double BrakeImpulseAcc;  // PGS accumulator (internal)
        /// <summary>Explicit retarder torque on this wheel this step [N m] (opposes rotation).</summary>
        public double RetarderTorque;
    }
}
