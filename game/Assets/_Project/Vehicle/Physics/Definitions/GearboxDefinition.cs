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
        public double shiftCooldown = 1.0;
        public double launchRpmLight = 800;
        public double launchRpmFull = 1100;
        public int maxLaunchGear = 4;

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
