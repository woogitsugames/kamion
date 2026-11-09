using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// Layout of the DrivingLab test pad (metres, X east, Z north, pad centre at origin). Shared by the editor
    /// scene generator and the runtime (spawn, autopilot). Change here and regenerate the scene.
    /// </summary>
    public static class DrivingLabLayout
    {
        public const string SceneName = "DrivingLab";
        public const float PadHalfSize = 200f;

        // Acceleration / braking lane along +Z; distance 0 at the spawn line.
        public static readonly Vector3 Spawn = new Vector3(0f, 0f, -180f);
        public const float LaneHalfWidth = 6f;
        public const float LaneEndZ = 190f;

        // Constant-radius circles (docs/04 §6.7).
        public static readonly Vector3 CircleR50Center = new Vector3(-110f, 0f, -95f);
        public const float CircleR50 = 50f;
        public static readonly Vector3 CircleR25Center = new Vector3(-110f, 0f, 95f);
        public const float CircleR25 = 25f;
        // Figure-eight: two R20 loops touching at FigureEightCenter (north-south axis).
        public static readonly Vector3 FigureEightCenter = new Vector3(-40f, 0f, 120f);
        public const float FigureEightR = 20f;

        // Ramps (rise 1.5 m, plateau 20 m) running north from RampStartZ.
        public const float RampHeight = 1.5f, RampPlateau = 20f, RampWidth = 6f, RampStartZ = -150f;
        public const float Ramp6X = 40f, Ramp12X = 58f;

        // Obstacle lane (x 92..108): 8 cm and 15 cm platforms, speed bump, ruts.
        public const float ObstacleX = 100f, ObstacleHalfWidth = 8f;
        public const float Curb8Z = -150f, Curb15Z = -115f, BumpZ = -80f, RutsStartZ = -55f, RutsLength = 30f;
        public const float PlatformLength = 10f;
        // Long side curbs to mount with one side (x of the curb strip, from z -150 for 40 m).
        public const float SideCurb8X = 125f, SideCurb15X = 140f;

        // Surface patches: 20 m wide, 40 m long, west to east, z 20..60.
        public const float PatchZ0 = 20f, PatchZ1 = 60f, PatchX0 = 30f, PatchWidth = 20f;

        // ---------------- Stage 2 ----------------
        /// <summary>Coupling bay: parked trailer with its kingpin above this point, heading north. Solo spawn: the tractor
        /// stands aligned ahead of it with the jaw <see cref="CouplingGap"/> in front of the kingpin (runner trailerGap).</summary>
        public static readonly Vector3 CouplingKingpin = new Vector3(70f, 0f, 112f);
        public const float CouplingGap = 2.0f;

        /// <summary>Loading dock on the north edge: dock face at z = DockFaceZ facing south, dock floor 1.20 m
        /// (WORKING_VALUE, typical EU dock height 1.1–1.3 m), bays every 4 m from DockBay0X, rubber bumpers.</summary>
        public const float DockFaceZ = 184f, DockHeight = 1.20f, DockBay0X = 100f, DockBayPitch = 4.0f;
        public const int DockBays = 5;
        public const float DockGuideLength = 34f;

        /// <summary>Hill road east of the pad: climbs at 7 % from x = HillStartX (z = HillZ), plateau for turning, then the
        /// same road is the 7 % descent (docs/04 §6.6 retarder / engine brake test).</summary>
        public const float HillZ = 130f, HillStartX = 200f, HillGrade = 0.07f, HillLength = 600f, HillRoadWidth = 12f, HillPlateau = 120f;
        public static float HillTopHeight => HillGrade * HillLength;

        /// <summary>Wet skid pad south-east of the pad (jackknife demo, docs/04 §6.9) with an R100 guide circle.</summary>
        public const float WetX0 = 200f, WetX1 = 460f, WetZ0 = -230f, WetZ1 = -10f;
        public static readonly Vector3 WetCircleCenter = new Vector3(345f, 0f, -120f);
        public const float WetCircleR = 100f;

        /// <summary>Autopilot start: on the R50 circle, heading north, centre to the west (counter-clockwise, left turn).</summary>
        public static Vector3 AutopilotStart => CircleR50Center + new Vector3(CircleR50, 0f, 0f);
    }
}
