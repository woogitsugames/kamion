using System;

namespace Game.Vehicle.Physics
{
    /// <summary>
    /// Tire parameters (per single tire). Combined-slip "normalized Magic Formula" model with
    /// first-order relaxation (contact-patch deflection states). See docs/VEHICLE_REFERENCE_DATA.md.
    /// Plain public fields so the class is both UnityEngine.JsonUtility and System.Text.Json compatible.
    /// </summary>
    [Serializable]
    public class TireDefinition
    {
        public const int CurrentSchemaVersion = 1;
        public int schemaVersion = CurrentSchemaVersion;
        public string id = "";
        public string size = "";

        /// <summary>Geometric radius [m] of the contact model (rigid disc): used for the contact rays and the suspension
        /// hardpoint. The tire's radial deflection is added in series (WheelGroup: hardpoint height = radius + SStatic -
        /// refLoad / radialStiffness), so the static wheel-centre height is radius minus the static deflection (ADR 0201).
        /// Also the contact-patch plane of the visual wheel (tyreFlatRadius).</summary>
        public double radius = 0.51;
        /// <summary>Effective rolling radius [m] = rolling circumference / 2π: wheel speed ↔ road speed and tire force ↔ wheel
        /// torque (drive, brake, rolling resistance). 0 = use <see cref="radius"/> (pre-ADR 0201 data).</summary>
        public double rollingRadius = 0;
        public double EffectiveRollingRadius => rollingRadius > 0 ? rollingRadius : radius;
        public double widthM = 0.315;
        /// <summary>Rotational inertia of tire+rim+hub+brake rotor per single wheel [kg m^2].</summary>
        public double wheelInertia = 20.0;

        /// <summary>Radial (vertical) stiffness per tire [N/m], in series with the suspension.</summary>
        public double radialStiffness = 1.0e6;
        /// <summary>
        /// Radial (vertical) damping per tire [N s/m] on the tyre deflection rate (ADR 0228; 0 = undamped tyre, before ADR 0228).
        /// WORKING_VALUE: no measured value for this tyre; see ADR 0228 for the range used.
        /// </summary>
        public double radialDamping;

        /// <summary>Nominal vertical load per tire [N] used for load sensitivity.</summary>
        public double nominalLoadN = 30000;
        /// <summary>Peak friction coefficient at nominal load on reference surface (dry asphalt).</summary>
        public double peakMu = 0.80;
        /// <summary>Relative peak-mu change per unit (Fz/Fz0 - 1). Negative = mu drops with load.</summary>
        public double muLoadSensitivity = -0.08;

        /// <summary>Longitudinal slip stiffness divided by Fz [1/unit slip] at nominal load.</summary>
        public double longitudinalStiffnessPerLoad = 12.0;
        /// <summary>Cornering stiffness divided by Fz [1/rad] at nominal load.</summary>
        public double corneringStiffnessPerLoad = 7.0;
        /// <summary>Load exponents p of slip stiffness K ~ Fz^p (1 = proportional, &lt;1 = degressive).</summary>
        public double longitudinalLoadExponent = 0.85;
        public double corneringLoadExponent = 0.7;

        /// <summary>Magic Formula shape factors.</summary>
        public double shapeCx = 1.65;
        public double curvatureEx = 0.0;
        public double shapeCy = 1.35;
        public double curvatureEy = -0.5;

        /// <summary>Relaxation lengths [m].</summary>
        public double relaxationLengthX = 0.30;
        public double relaxationLengthY = 0.50;

        /// <summary>Low-speed contact damping time constant [s] (damping = stiffness * tau), faded out above lowSpeedFadeMs.</summary>
        public double lowSpeedDampingTau = 0.010;
        public double lowSpeedFadeMs = 3.0;

        /// <summary>Rolling resistance coefficient [-].</summary>
        public double rollingResistanceCoeff = 0.0055;

        /// <summary>Pneumatic trail at zero slip [m] (aligning torque estimate for steering feedback).</summary>
        public double pneumaticTrail0 = 0.06;

        public void Validate()
        {
            if (schemaVersion != CurrentSchemaVersion) throw new FormatException($"TireDefinition '{id}': unsupported schemaVersion {schemaVersion}");
            if (radius <= 0.1 || radius > 1.0) throw new FormatException($"TireDefinition '{id}': radius out of range");
            if (rollingRadius != 0 && (rollingRadius < radius || rollingRadius > radius * 1.15)) throw new FormatException($"TireDefinition '{id}': rollingRadius must be in [radius, 1.15 radius]");
            if (peakMu <= 0 || peakMu > 2) throw new FormatException($"TireDefinition '{id}': peakMu out of range");
            if (shapeCx <= 1 || shapeCx >= 2 || shapeCy <= 1 || shapeCy >= 2) throw new FormatException($"TireDefinition '{id}': shape factor C must be in (1,2)");
            if (relaxationLengthX <= 0 || relaxationLengthY <= 0) throw new FormatException($"TireDefinition '{id}': relaxation length must be > 0");
        }
    }
}
