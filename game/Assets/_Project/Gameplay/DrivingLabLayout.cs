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

        /// <summary>Autopilot start: on the R50 circle, heading north, centre to the west (counter-clockwise, left turn).</summary>
        public static Vector3 AutopilotStart => CircleR50Center + new Vector3(CircleR50, 0f, 0f);
    }
}
