using System;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// Authoritative tractor data. Vehicle local frame:
    /// X = right, Y = up, Z = forward; origin on the ground plane below the rear (drive) axle centre
    /// at design ride height. All values SI unless the field name says otherwise (bar, L, kW, rpm).
    /// Provenance of every number: docs/VEHICLE_REFERENCE_DATA.md.
    /// Schema v1 is extended additively (Stage 2 blocks have defaults), so Stage 1 files still load.
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
        public AirSystemDefinition air = new AirSystemDefinition();
        public RetarderDefinition retarder = new RetarderDefinition();
        public DrivelineDefinition driveline = new DrivelineDefinition();
        public AeroDefinition aero = new AeroDefinition();
        public CabSuspensionDefinition cab = new CabSuspensionDefinition();
        public FifthWheelDefinition fifthWheel = new FifthWheelDefinition();

        public void Validate()
        {
            if (schemaVersion != CurrentSchemaVersion) throw new FormatException($"VehicleDefinition '{id}': unsupported schemaVersion {schemaVersion}");
            if (massElements.Length == 0) throw new FormatException($"VehicleDefinition '{id}': no mass elements");
            if (axles.Length != 2) throw new FormatException($"VehicleDefinition '{id}': the tractor solver supports exactly 2 axles");
            bool anyDriven = false, anySteered = false;
            foreach (var a in axles)
            {
                a.Validate(id);
                anyDriven |= a.driven; anySteered |= a.steered;
            }
            if (!anyDriven) throw new FormatException($"VehicleDefinition '{id}': no driven axle");
            if (!anySteered) throw new FormatException($"VehicleDefinition '{id}': no steered axle");
            if (driveline.finalDriveRatio <= 0) throw new FormatException($"VehicleDefinition '{id}': finalDriveRatio must be > 0");
            if (air.cutInBar >= air.cutOutBar) throw new FormatException($"VehicleDefinition '{id}': air cut-in must be below cut-out");
            if (brakes.maxChamberPressureBar <= brakes.thresholdPressureBar) throw new FormatException($"VehicleDefinition '{id}': bad brake pressures");
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
        /// <summary>Service brake torque capacity per wheel end at maximum chamber pressure [N m].</summary>
        public double serviceBrakeTorque = 18000;
        /// <summary>Spring (parking) brake torque per wheel end with the spring chamber exhausted [N m]; 0 = no spring brake.</summary>
        public double parkingBrakeTorque;
        /// <summary>Service brake chamber swept volume per wheel end [L] (air consumption per application).</summary>
        public double brakeChamberVolumeL = 0.8;
        /// <summary>Tractor: air circuit feeding the service chamber (1 = front circuit, 2 = rear circuit). Trailer: ignored.</summary>
        public int brakeCircuit = 1;
        /// <summary>First-order pressure build-up time constant of this axle's chambers [s].</summary>
        public double brakeApplyTimeConstant = 0.20;
        /// <summary>Second cascaded lag [s] (long lines to the trailer) — gives the S-shaped, delayed build-up. 0 = none.</summary>
        public double brakeApplySecondTimeConstant;
        public double brakeReleaseTimeConstant = 0.30;
        /// <summary>EBS load sensing: service pressure is scaled by axleLoad / ladenAxleLoadN (clamped to [minLoadSensingFactor, 1]). 0 = off.</summary>
        public double ladenAxleLoadN;
        public double minLoadSensingFactor = 0.3;

        public void Validate(string owner)
        {
            if (trackWidth <= 0.5) throw new FormatException($"'{owner}': axle '{name}' track too small");
            if (tiresPerSide < 1 || tiresPerSide > 2) throw new FormatException($"'{owner}': axle '{name}' tiresPerSide must be 1 or 2");
            if (suspension.travel <= 0.02) throw new FormatException($"'{owner}': axle '{name}' travel too small");
            if (brakeApplyTimeConstant <= 0 || brakeReleaseTimeConstant <= 0) throw new FormatException($"'{owner}': axle '{name}' brake time constants must be > 0");
        }
    }

    [Serializable]
    public class SuspensionDefinition
    {
        public string type = "";
        /// <summary>Wheel-rate spring stiffness per side [N/m] (linear part) at the reference load.</summary>
        public double springRate = 200000;
        /// <summary>Cubic progression [N/m^3] added on top of linear rate (compression from static).</summary>
        public double progressiveRate;
        /// <summary>Total wheel travel (full bump to full droop) [m].</summary>
        public double travel = 0.20;
        /// <summary>Static position as fraction of travel measured from full bump (0.5 = mid travel) at the reference load.</summary>
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
        /// <summary>
        /// Load per side [N] at which the wheel sits at the static position. 0 = the static load of the
        /// vehicle's own definition (solo tractor / empty trailer).
        /// </summary>
        public double referenceLoadN;
        /// <summary>
        /// Air spring with height levelling (ECAS / levelling valve): the bellows force at the static position
        /// tracks the load slowly; the spring rate scales with bellows pressure (constant natural frequency).
        /// </summary>
        public bool airLevelling;
        public double levellingTimeConstant = 8.0;
        public double levellingDeadband = 0.008;
        /// <summary>Axles with the same non-zero group id share bellows pressure (interconnected bellows, load equalisation).</summary>
        public int levellingGroup;
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
        /// <summary>Stage 1 single lag (kept for reference; Stage 2 uses the per-axle lags).</summary>
        public double applyTimeConstant = 0.25;
        public double releaseTimeConstant = 0.30;
        /// <summary>Spring brake chamber fill / exhaust time constant [s].</summary>
        public double parkingTimeConstant = 0.6;
        /// <summary>Chamber pressure at full service demand [bar] and the pressure where the pads start to produce torque.</summary>
        public double maxChamberPressureBar = 8.5;
        public double thresholdPressureBar = 0.4;

        public bool absEnabled = true;
        /// <summary>Slip (positive while braking) above which the modulator dumps pressure.</summary>
        public double absSlipRelease = 0.16;
        /// <summary>Slip below which re-application starts.</summary>
        public double absSlipReapply = 0.06;
        /// <summary>Wheel deceleration (m/s^2 at the tread) that signals impending lock -> hold.</summary>
        public double absDecelThreshold = 12.0;
        /// <summary>Wheel re-acceleration (m/s^2) that ends the dump phase.</summary>
        public double absReaccelThreshold = 4.0;
        /// <summary>ABS modulator exhaust time constant [s] and slow (pulsed) re-apply factor on the build-up time constant.</summary>
        public double absDumpTimeConstant = 0.045;
        public double absSlowApplyFactor = 3.0;
        public double absMinSpeedMs = 1.5;
        /// <summary>Kept for Stage 1 files (unused by the Stage 2 modulator).</summary>
        public double absReleaseRate = 8.0;
        public double absApplyRate = 4.0;

        /// <summary>ASR (traction control), engine-torque intervention.</summary>
        public bool asrEnabled = true;
        public double asrSlipThreshold = 0.15;
        public double asrReduceRate = 3.0;
        public double asrRecoverRate = 1.0;
        public bool hillStartAid = true;
        public double hillStartMaxHold = 2.0;

        /// <summary>Brake blending: the first part of the pedal travel requests the endurance brakes (engine brake, retarder) before the service brake.</summary>
        public bool brakeBlending = true;
        /// <summary>Pedal travel used for endurance braking only; service braking starts here.</summary>
        public double blendingPedalTravel = 0.15;
    }

    /// <summary>Tractor compressed-air supply (docs/04 section 2.8).</summary>
    [Serializable]
    public class AirSystemDefinition
    {
        /// <summary>Compressor free-air delivery [L/min] at compressorRatedRpm and 0 bar back-pressure; linear in engine speed.</summary>
        public double compressorFlowLpm = 450;
        public double compressorRatedRpm = 2000;
        /// <summary>Relative delivery loss per bar of back pressure (volumetric efficiency).</summary>
        public double compressorPressureLossPerBar = 0.03;
        /// <summary>Governor (air processing unit) cut-out / cut-in [bar gauge].</summary>
        public double cutOutBar = 12.5;
        public double cutInBar = 11.0;
        /// <summary>Reservoir volumes [L]: supply (wet), service circuit 1 (front), circuit 2 (rear), circuit 3 (trailer supply + parking).</summary>
        public double supplyVolumeL = 30;
        public double frontVolumeL = 20;
        public double rearVolumeL = 30;
        public double parkTrailerVolumeL = 20;
        /// <summary>Multi-circuit protection valve opening pressure [bar]: circuits are filled only while the supply is above this.</summary>
        public double protectionOpeningBar = 7.0;
        /// <summary>Flow conductance supply -> circuit [L(free air)/s per bar].</summary>
        public double circuitConductance = 20;
        /// <summary>Red (supply) line conductance to the trailer reservoir [L(free air)/s per bar].</summary>
        public double redLineConductance = 6;
        /// <summary>Pressure limiter on the trailer supply and spring-brake supply [bar].</summary>
        public double trailerSupplyLimitBar = 8.5;
        /// <summary>Maximum trailer control (yellow) line pressure at full service demand [bar].</summary>
        public double trailerControlMaxBar = 7.5;
        /// <summary>
        /// Trailer control line pressure with the parking lever in the park position [bar], 0 = trailer not braked
        /// by the tractor parking brake. European hand control valves with a trailer-control function brake the
        /// trailer through the yellow line in park (the "test" position releases it to check the tractor alone);
        /// WORKING_VALUE, UNVERIFIED (ADR 0004 addendum 2026-11-10).
        /// </summary>
        public double trailerControlParkBar = 7.5;
        public double lowPressureWarningBar = 5.5;
        /// <summary>Spring brake chamber: releasing starts / complete [bar].</summary>
        public double springReleaseStartBar = 3.0;
        public double springReleaseFullBar = 5.5;
        /// <summary>Background consumption (air suspension, gearbox actuators, leaks) [L free air / min].</summary>
        public double baselineConsumptionLpm = 8;
    }

    /// <summary>Secondary hydrodynamic retarder on the gearbox output (Intarder class).</summary>
    [Serializable]
    public class RetarderDefinition
    {
        public bool present = true;
        /// <summary>Maximum braking torque at the gearbox output [N m] and power limit [kW].</summary>
        public double maxTorqueNm = 4000;
        public double maxPowerKW = 600;
        /// <summary>Propshaft speed above which the full torque is available [rpm]; below it torque ~ n^2 (hydrodynamic).</summary>
        public double fullTorqueShaftRpm = 900;
        /// <summary>Number of retarder lever stages (stage 1 of the lever is the engine brake, stages 2.. are retarder fractions).</summary>
        public int stages = 4;
        public double fillTimeConstant = 0.4;
        public double drainTimeConstant = 0.3;
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
        /// <summary>Drag coefficient times frontal area [m^2] (solo).</summary>
        public double dragArea = 6.0;
        /// <summary>Tractor share of the drag area when a semi-trailer is coupled [m^2] (0 = same as solo).</summary>
        public double dragAreaWithTrailer;
        public double airDensity = 1.2;
        public Vec3 center;
    }

    [Serializable]
    public class CabSuspensionDefinition
    {
        public double pitchFrequencyHz = 1.2;
        public double rollFrequencyHz = 1.4;
        public double heaveFrequencyHz = 1.8;
        public double dampingRatio = 0.35;
        /// <summary>Angular acceleration per unit chassis acceleration [rad/s^2 per m/s^2] = h / r_g^2
        /// (cab CoG height above mounts over squared radius of gyration).</summary>
        public double accelGain = 0.55;
        /// <summary>Soft stop: beyond these angles / heave the mount stiffness rises steeply (no hard clamp).</summary>
        public double maxPitchDeg = 4;
        public double maxRollDeg = 4;
        public double maxHeaveM = 0.05;
        /// <summary>Cab mount centre in vehicle frame (pivot of pitch/roll) [m].</summary>
        public Vec3 mountCenter = new Vec3(0, 1.15, 3.925);
    }

    /// <summary>Fifth wheel (tractor side) and coupling constraint parameters.</summary>
    [Serializable]
    public class FifthWheelDefinition
    {
        /// <summary>Kingpin lock point (jaw centre) in tractor frame [m].</summary>
        public Vec3 position = new Vec3(0, 1.15, 0.68);
        /// <summary>Fore/aft plate oscillation limit [deg].</summary>
        public double pitchLimitDeg = 12;
        /// <summary>Roll coupling: torsional stiffness [N m/rad] and damping [N m s/rad] between tractor and trailer, plus a hard limit.</summary>
        public double rollStiffness = 1.0e7;
        public double rollDamping = 2.0e5;
        public double rollLimitDeg = 4;
        /// <summary>Articulation (yaw) stop: trailer front corner meets the cab / frame [deg].</summary>
        public double yawLimitDeg = 90;
        /// <summary>Stop compliance: natural frequency of the pitch/roll stops and of the articulation (cab contact) stop [Hz].</summary>
        public double stopFrequencyHz = 10;
        public double yawStopFrequencyHz = 3;
        /// <summary>Plate friction (greased): Coulomb yaw torque = coeff * kingpin vertical load * radius.</summary>
        public double plateFrictionCoeff = 0.08;
        public double plateFrictionRadius = 0.35;
        /// <summary>Coupling capture window: horizontal / vertical distance [m] and max relative speed [m/s].</summary>
        public double captureDistance = 0.05;
        public double captureHeight = 0.12;
        public double captureMaxSpeed = 1.5;
        /// <summary>
        /// Coupling throat (R5): the plate slot is a funnel opening to the rear. Its mouth is +/- captureThroatHalfWidth wide
        /// at captureThroatLength behind the jaw centre and narrows linearly to +/- captureDistance at the jaw (the lead-in ramps).
        /// A kingpin that enters the mouth while the jaw is open is pushed to the centre line by the ramp (spring-damper contact,
        /// force capped at captureGuideMaxForce, applied equally to both bodies); one that is wider than the mouth misses.
        /// WORKING_VALUE (+/- 0.18 m, 0.40 m, ~18 deg ramps): typical lead-in of a 2" fifth wheel plate, not measured on a specific model.
        /// </summary>
        public double captureThroatHalfWidth = 0.18;
        public double captureThroatLength = 0.40;
        /// <summary>Ramp contact stiffness [N/m], damping [N s/m] and force cap [N] (what the trailer feet / tractor tires can give sideways).</summary>
        public double captureGuideStiffness = 3.0e6;
        public double captureGuideDamping = 1.5e5;
        public double captureGuideMaxForce = 80000;
        /// <summary>Position error feedback (fraction per step) and its speed cap [m/s].</summary>
        public double positionCorrection = 0.2;
        public double maxCorrectionSpeed = 0.5;
        public int iterations = 8;
        /// <summary>Jaw engagement phase after locking [s] and its compliance (natural frequency, critically damped) [Hz].</summary>
        public double engageTime = 0.4;
        public double engageFrequencyHz = 4;
    }
}
