using System;

namespace Game.Vehicle.Physics
{
    [Serializable]
    public class EngineDefinition
    {
        public const int CurrentSchemaVersion = 1;
        public int schemaVersion = CurrentSchemaVersion;
        public string id = "";
        public string description = "";

        /// <summary>Full-load torque curve: engine speed [rpm] -> torque [N m].</summary>
        public double[] torqueCurveRpm = new double[0];
        public double[] torqueCurveNm = new double[0];
        /// <summary>Motoring (friction + pumping) drag torque, positive magnitude [N m] vs rpm.</summary>
        public double[] dragCurveRpm = new double[0];
        public double[] dragCurveNm = new double[0];

        /// <summary>Rotating inertia of crankshaft + flywheel + clutch pressure plate [kg m^2].</summary>
        public double inertia = 3.5;
        public double idleRpm = 600;
        /// <summary>Governor cut-off: torque fades from governorStartRpm to maxRpm.</summary>
        public double governorStartRpm = 1900;
        public double maxRpm = 2100;
        public double stallRpm = 350;

        /// <summary>Turbo lag: fraction of full-load torque available without boost, and boost time constant [s].</summary>
        public double naturallyAspiratedFraction = 0.45;
        public double boostTimeConstant = 0.35;

        public void Validate()
        {
            if (schemaVersion != CurrentSchemaVersion) throw new FormatException($"EngineDefinition '{id}': unsupported schemaVersion {schemaVersion}");
            if (torqueCurveRpm.Length < 2 || torqueCurveRpm.Length != torqueCurveNm.Length) throw new FormatException($"EngineDefinition '{id}': bad torque curve");
            if (dragCurveRpm.Length < 2 || dragCurveRpm.Length != dragCurveNm.Length) throw new FormatException($"EngineDefinition '{id}': bad drag curve");
            for (int i = 1; i < torqueCurveRpm.Length; i++) if (torqueCurveRpm[i] <= torqueCurveRpm[i - 1]) throw new FormatException($"EngineDefinition '{id}': torque rpm must increase");
            for (int i = 1; i < dragCurveRpm.Length; i++) if (dragCurveRpm[i] <= dragCurveRpm[i - 1]) throw new FormatException($"EngineDefinition '{id}': drag rpm must increase");
            if (inertia <= 0) throw new FormatException($"EngineDefinition '{id}': inertia must be > 0");
        }
    }
}
