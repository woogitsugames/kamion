using System;

namespace Game.Vehicle.Physics
{
    [Serializable]
    public class GearboxDefinition
    {
        public const int CurrentSchemaVersion = 1;
        public int schemaVersion = CurrentSchemaVersion;
        public string id = "";
        public string description = "";

        /// <summary>Forward ratios, gear 1..N (index 0 = 1st gear).</summary>
        public double[] forwardRatios = new double[0];
        /// <summary>Reverse ratio magnitude (sign applied internally).</summary>
        public double reverseRatio = 12.0;
        public double efficiency = 0.97;

        /// <summary>Clutch torque capacity when fully engaged [N m].</summary>
        public double clutchMaxTorque = 4000;
        /// <summary>Clutch thermal model: heat capacity of pressure plate + flywheel face [J/K], cooling time constant [s], warning temperature [deg C].</summary>
        public double clutchHeatCapacity = 25000;
        public double clutchCoolingTimeConstant = 300;
        public double clutchWarnTempC = 250;

        // --- AMT shift logic (WORKING_VALUEs, see reference data) ---
        public double shiftTorqueRampTime = 0.12;
        public double shiftNeutralTime = 0.15;
        public double shiftSyncTime = 0.20;
        public double shiftClutchCloseTime = 0.15;
        public double upshiftRpmLight = 1250;
        public double upshiftRpmFull = 1750;
        public double downshiftRpmLight = 850;
        public double downshiftRpmFull = 1100;
        /// <summary>Minimum engine speed after an upshift, light / full throttle.</summary>
        public double minRpmAfterUpshiftLight = 950;
        public double minRpmAfterUpshiftFull = 1250;
        public int maxSkip = 2;
        /// <summary>Hold-off after an upshift before a downshift is allowed (anti-hunting) [s].</summary>
        public double shiftCooldown = 1.0;
        /// <summary>Hold-off between two shifts in the same direction [s] (short, so a light truck does not over-rev).</summary>
        public double sameDirectionCooldown = 0.3;
        /// <summary>Minimum acceleration the truck must still have in the new gear for an upshift (full throttle) [m/s^2].</summary>
        public double minAccelAfterUpshift = 0.10;
        /// <summary>Extra downshift rpm on climbs heavier than gradeDownshiftThreshold (keeps the engine in the torque plateau).</summary>
        public double gradeDownshiftBonusRpm = 200;
        public double gradeDownshiftThreshold = 0.025;
        public double launchRpmLight = 800;
        public double launchRpmFull = 1100;
        /// <summary>Extra launch rpm per unit of required launch force fraction (heavy / uphill starts).</summary>
        public double launchRpmLoadBonus = 250;
        public int maxLaunchGear = 4;
        /// <summary>Creep function: below this pedal the launch clutch holds creepTorqueNm at idle [-, N m].</summary>
        public double creepPedal = 0.15;
        public double creepTorqueNm = 500;
        /// <summary>Engine braking: downshift below / upshift above these engine speeds [rpm].</summary>
        public double engineBrakeDownshiftRpm = 1500;
        public double engineBrakeUpshiftRpm = 2250;
        /// <summary>Manual mode: lowest engine speed accepted after a requested shift and auto-protection downshift speed [rpm].</summary>
        public double manualMinRpmAfterShift = 750;
        public double manualProtectDownshiftRpm = 650;

        public int ForwardGearCount => forwardRatios.Length;

        public void Validate()
        {
            if (schemaVersion != CurrentSchemaVersion) throw new FormatException($"GearboxDefinition '{id}': unsupported schemaVersion {schemaVersion}");
            if (forwardRatios.Length < 1) throw new FormatException($"GearboxDefinition '{id}': no gears");
            for (int i = 1; i < forwardRatios.Length; i++) if (forwardRatios[i] >= forwardRatios[i - 1]) throw new FormatException($"GearboxDefinition '{id}': ratios must decrease");
            if (efficiency <= 0.5 || efficiency > 1) throw new FormatException($"GearboxDefinition '{id}': efficiency out of range");
        }
    }
}
