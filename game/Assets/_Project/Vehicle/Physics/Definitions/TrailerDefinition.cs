using System;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// Semi-trailer data. Trailer local frame: X = right, Y = up, Z = forward; origin on the ground plane
    /// directly below the kingpin at design ride height, so the kingpin is at (0, kingpinHeight, 0) and the
    /// axles are at negative Z. Provenance: docs/VEHICLE_REFERENCE_DATA.md.
    /// </summary>
    [Serializable]
    public class TrailerDefinition
    {
        public const int CurrentSchemaVersion = 1;
        public int schemaVersion = CurrentSchemaVersion;
        public string id = "";
        public string description = "";

        /// <summary>Empty trailer mass elements (cargo is added at run time).</summary>
        public MassElement[] massElements = new MassElement[0];
        public double kingpinHeight = 1.15;
        public AxleDefinition[] axles = new AxleDefinition[0];
        public CargoBayDefinition cargoBay = new CargoBayDefinition();
        public LandingGearDefinition landingGear = new LandingGearDefinition();
        public TrailerBrakeDefinition brakes = new TrailerBrakeDefinition();
        /// <summary>Drag area added by the trailer to the coupled combination [m^2], applied at aeroCenter.</summary>
        public double dragArea = 1.5;
        public Vec3 aeroCenter = new Vec3(0, 2.5, -5.0);

        public void Validate()
        {
            if (schemaVersion != CurrentSchemaVersion) throw new FormatException($"TrailerDefinition '{id}': unsupported schemaVersion {schemaVersion}");
            if (massElements.Length == 0) throw new FormatException($"TrailerDefinition '{id}': no mass elements");
            if (axles.Length < 1) throw new FormatException($"TrailerDefinition '{id}': need at least 1 axle");
            foreach (var a in axles)
            {
                a.Validate(id);
                if (a.steered || a.driven) throw new FormatException($"TrailerDefinition '{id}': trailer axles are neither steered nor driven");
                if (a.positionZ >= 0) throw new FormatException($"TrailerDefinition '{id}': axles must be behind the kingpin (z < 0)");
            }
        }
    }

    [Serializable]
    public class CargoBayDefinition
    {
        public double floorHeight = 1.30;
        /// <summary>Front wall position (z) and inner length / width / height [m].</summary>
        public double frontZ = 1.572;
        public double length = 13.512;
        public double width = 2.50;
        public double height = 2.58;
        public double maxPayloadKg = 26000;
    }

    /// <summary>Load case: cargo mass and centre of gravity (trailer frame). Not part of the trailer data file.</summary>
    [Serializable]
    public class CargoDefinition
    {
        public double massKg;
        /// <summary>Cargo CoG height above ground [m]; 0 = floor + half of sizeY.</summary>
        public double cogHeight;
        /// <summary>Cargo CoG longitudinal position in trailer frame [m]; NaN-free default 0 = middle of the cargo bay.</summary>
        public double cogZ;
        public bool cogZSet;
        /// <summary>Lateral CoG offset [m] (off-centre load).</summary>
        public double cogX;
        /// <summary>Cargo block size for inertia [m]; 0 = fill the bay footprint, 2 m high.</summary>
        public Vec3 size;

        public MassElement ToMassElement(CargoBayDefinition bay)
        {
            Vec3 sz = size;
            if (sz.x <= 0) sz.x = bay.width;
            if (sz.z <= 0) sz.z = bay.length;
            if (sz.y <= 0) sz.y = 2.0;
            double y = cogHeight > 0 ? cogHeight : bay.floorHeight + 0.5 * sz.y;
            double z = cogZSet ? cogZ : bay.frontZ - 0.5 * bay.length;
            return new MassElement { name = "cargo", massKg = massKg, center = new Vec3(cogX, y, z), size = sz };
        }
    }

    [Serializable]
    public class LandingGearDefinition
    {
        /// <summary>Leg position: z in trailer frame, half track [m].</summary>
        public double positionZ = -2.2;
        public double halfTrack = 0.95;
        /// <summary>Foot height in trailer frame when lowered (a few cm past ground contact, so the legs lift the nose off the fifth wheel) / raised [m].</summary>
        public double loweredFootY = -0.07;
        public double raisedFootY = 0.45;
        /// <summary>Vertical stiffness and damping per leg [N/m, N s/m]; foot friction coefficient; tangential stick stiffness [N/m].</summary>
        public double stiffness = 4.0e6;
        public double damping = 6.0e4;
        public double friction = 0.6;
        public double tangentialStiffness = 2.0e6;
        /// <summary>Crank speed [m/s] (raising / lowering).</summary>
        public double crankSpeed = 0.05;
    }

    [Serializable]
    public class TrailerBrakeDefinition
    {
        public double maxChamberPressureBar = 8.5;
        public double thresholdPressureBar = 0.4;
        /// <summary>Trailer reservoir volume [L] and the charging check valve conductance [L(free air)/s per bar].</summary>
        public double reservoirVolumeL = 80;
        /// <summary>Emergency function: supply (red) line pressure below this applies the trailer service brakes from the reservoir [bar].</summary>
        public double emergencyApplyBar = 3.5;
        public double emergencyReleaseBar = 4.5;
        public double springReleaseStartBar = 3.0;
        public double springReleaseFullBar = 5.5;
        /// <summary>Gain from control (yellow) line pressure to the relay output: chamber = control * relayGain (clamped to max).</summary>
        public double relayGain = 1.13;
        public bool absEnabled = true;
        /// <summary>ABS layout: true = 2S/2M (one modulator per side controlling the whole side), false = per wheel end.</summary>
        public bool absPerSide = true;
        /// <summary>Index of the sensed axle for 2S/2M (the other axles of a side follow its modulator).</summary>
        public int absSensedAxle = 1;
        public double parkingTimeConstant = 0.6;
    }
}
