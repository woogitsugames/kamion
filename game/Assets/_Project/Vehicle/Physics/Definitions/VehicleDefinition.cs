using System;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// Authoritative vehicle data (tractor solo for Stage 1). Vehicle local frame:
    /// X = right, Y = up, Z = forward; origin on the ground plane below the rear (drive) axle centre
    /// at design ride height. All values SI. Provenance of every number: docs/VEHICLE_REFERENCE_DATA.md.
    /// </summary>
    [Serializable]
    public class VehicleDefinition
    {
        public const int CurrentSchemaVersion = 1;
        public int schemaVersion = CurrentSchemaVersion;
        public string id = "";
        public string description = "";

        public string engineId = "";
        public string gearboxId = "";

        /// <summary>Lumped mass elements (boxes). Total mass, centre of mass and inertia tensor are computed from them.</summary>
        public MassElement[] massElements = new MassElement[0];
        public AxleDefinition[] axles = new AxleDefinition[0];
        public SteeringDefinition steering = new SteeringDefinition();
        public BrakeSystemDefinition brakes = new BrakeSystemDefinition();
        public DrivelineDefinition driveline = new DrivelineDefinition();
        public AeroDefinition aero = new AeroDefinition();
        public CabSuspensionDefinition cab = new CabSuspensionDefinition();

        public void Validate()
        {
            if (schemaVersion != CurrentSchemaVersion) throw new FormatException($"VehicleDefinition '{id}': unsupported schemaVersion {schemaVersion}");
            if (massElements.Length == 0) throw new FormatException($"VehicleDefinition '{id}': no mass elements");
            if (axles.Length < 2) throw new FormatException($"VehicleDefinition '{id}': need at least 2 axles");
            bool anyDriven = false, anySteered = false;
            foreach (var a in axles)
            {
                if (a.trackWidth <= 0.5) throw new FormatException($"VehicleDefinition '{id}': axle '{a.name}' track too small");
                if (a.tiresPerSide < 1 || a.tiresPerSide > 2) throw new FormatException($"VehicleDefinition '{id}': axle '{a.name}' tiresPerSide must be 1 or 2");
                if (a.suspension.travel <= 0.02) throw new FormatException($"VehicleDefinition '{id}': axle '{a.name}' travel too small");
                anyDriven |= a.driven; anySteered |= a.steered;
            }
            if (!anyDriven) throw new FormatException($"VehicleDefinition '{id}': no driven axle");
            if (!anySteered) throw new FormatException($"VehicleDefinition '{id}': no steered axle");
            if (driveline.finalDriveRatio <= 0) throw new FormatException($"VehicleDefinition '{id}': finalDriveRatio must be > 0");
        }
    }

    [Serializable]
    public class MassElement
    {
        public string name = "";
        public double massKg;
        public Vec3 center;
        /// <summary>Box full extents [m] (x width, y height, z length) for the inertia contribution.</summary>
        public Vec3 size;
    }

    [Serializable]
    public class AxleDefinition
    {
        public string name = "";
        /// <summary>Longitudinal position of the axle in vehicle frame [m].</summary>
        public double positionZ;
        /// <summary>Distance between left and right wheel (or dual-pair) centres [m].</summary>
        public double trackWidth = 2.0;
        public int tiresPerSide = 1;
        public bool steered;
        public bool driven;
        public string tireId = "";
        public SuspensionDefinition suspension = new SuspensionDefinition();
        /// <summary>Service brake torque capacity per wheel end at full pressure [N m].</summary>
        public double serviceBrakeTorque = 18000;
        /// <summary>Spring (parking) brake torque per wheel end [N m]; 0 = no spring brake on this axle.</summary>
        public double parkingBrakeTorque;
    }

    [Serializable]
    public class SuspensionDefinition
    {
        public string type = "";
        /// <summary>Wheel-rate spring stiffness per side [N/m] (linear part).</summary>
        public double springRate = 200000;
        /// <summary>Cubic progression [N/m^3] added on top of linear rate (compression from static).</summary>
        public double progressiveRate;
        /// <summary>Total wheel travel (full bump to full droop) [m].</summary>
        public double travel = 0.20;
        /// <summary>Static position as fraction of travel measured from full bump (0.5 = mid travel).</summary>
        public double staticPositionFraction = 0.5;
        /// <summary>Bump-stop engages this far before full bump [m]; quadratic stiffness [N/m^2].</summary>
        public double bumpStopClearance = 0.03;
        public double bumpStopRate = 3.0e7;
        /// <summary>Damping per side [N s/m] (bump / rebound), linear up to knee velocity, then highSpeedFactor slope.</summary>
        public double damperBump = 8000;
        public double damperRebound = 16000;
        public double damperKneeVelocity = 0.3;
        public double damperHighSpeedFactor = 0.4;
        /// <summary>Anti-roll bar roll stiffness for the axle [N m/rad].</summary>
        public double antiRollStiffness;
    }

    [Serializable]
    public class SteeringDefinition
    {
        /// <summary>Maximum road-wheel angle of the virtual centre wheel [deg] (inner wheel gets more via Ackermann).</summary>
        public double maxRoadWheelAngleDeg = 40;
        /// <summary>Maximum road-wheel angle rate [deg/s].</summary>
        public double maxSteerRateDegS = 30;
        /// <summary>1 = full Ackermann, 0 = parallel steer.</summary>
        public double ackermannFactor = 1.0;
        /// <summary>Overall steering ratio (handwheel angle / road-wheel angle) [-], used for handwheel telemetry and feedback.</summary>
        public double steeringRatio = 20;
    }

    [Serializable]
    public class BrakeSystemDefinition
    {
        public double applyTimeConstant = 0.25;
        public double releaseTimeConstant = 0.30;
        public double parkingTimeConstant = 0.6;
        public bool absEnabled = true;
        /// <summary>ABS releases pressure when slip ratio below -absSlipRelease and re-applies above -absSlipReapply.</summary>
        public double absSlipRelease = 0.18;
        public double absSlipReapply = 0.08;
        public double absReleaseRate = 8.0;
        public double absApplyRate = 4.0;
        public double absMinSpeedMs = 1.5;
        /// <summary>ASR (traction control), engine-torque intervention only in Stage 1.</summary>
        public bool asrEnabled = true;
        public double asrSlipThreshold = 0.15;
        public double asrReduceRate = 3.0;
        public double asrRecoverRate = 1.0;
        public bool hillStartAid = true;
        public double hillStartMaxHold = 2.0;
    }

    [Serializable]
    public class DrivelineDefinition
    {
        public double finalDriveRatio = 3.4;
        public double finalDriveEfficiency = 0.97;
        /// <summary>Legal vehicle speed limiter set speed [km/h].</summary>
        public double speedLimiterKmh = 90;
        public double speedLimiterBand = 2.0;
    }

    [Serializable]
    public class AeroDefinition
    {
        /// <summary>Drag coefficient times frontal area [m^2].</summary>
        public double dragArea = 6.0;
        public double airDensity = 1.2;
        public Vec3 center;
    }

    [Serializable]
    public class CabSuspensionDefinition
    {
        public double pitchFrequencyHz = 1.2;
        public double rollFrequencyHz = 1.4;
        public double dampingRatio = 0.35;
        /// <summary>Angular acceleration per unit chassis acceleration [rad/s^2 per m/s^2] = h / r_g^2
        /// (cab CoG height above mounts over squared radius of gyration).</summary>
        public double accelGain = 0.55;
        public double maxPitchDeg = 4;
        public double maxRollDeg = 4;
    }
}
