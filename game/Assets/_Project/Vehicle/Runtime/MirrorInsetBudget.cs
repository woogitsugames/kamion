namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Mirror refresh policy while the class II mirrors are shown as fixed on-screen windows (D70, ADR 0243; the HUD insets,
    /// <see cref="RenderTextureMirror.ForceRender"/>). Pure and allocation-free; <see cref="VehicleCameraBudget"/> asks it.
    /// <para>
    /// With the windows on, both class II mirrors are candidates every frame (the window shows them wherever the head looks),
    /// so the Low weighted round-robin of ADR 0042 (cap 1 as a quota) renders exactly one mirror in EVERY frame. Low with
    /// windows therefore uses the due-based step of ADR 0068 with the cap as a limit and no spare fill: class II every
    /// <see cref="LowMainInterval"/> frames (10 Hz at the Low 30 FPS cap = the class II cadence the round-robin already gives
    /// with two convex mirrors on screen), classes IV-VI every <see cref="LowConvexInterval"/> frames (x2 standing). Worst case
    /// (all six on screen) = 2/3 + 4/16 = 0.917 renders per frame &lt; cap 1, so the class II pair is never starved; windows
    /// only = 0.667. WORKING_VALUE until measured on the Galaxy A16 (ADR 0243 "Pomiar").
    /// </para>
    /// Medium, High and Ultra are unchanged (High already due-based, ADR 0068). Without the windows every tier is unchanged.
    /// </summary>
    public static class MirrorInsetBudget
    {
        /// <summary>Quality level that gets the window policy (0 = Low).</summary>
        public const int LowLevel = 0;
        /// <summary>Class II interval on Low with windows [frames]. 3 at 30 FPS = 10 Hz. WORKING_VALUE.</summary>
        public const float LowMainInterval = 3f;
        /// <summary>Classes IV-VI interval on Low with windows while driving [frames]. 16 at 30 FPS = 1.9 Hz. WORKING_VALUE.</summary>
        public const float LowConvexInterval = 16f;
        /// <summary>Convex interval multiplier while the truck stands (image does not move with the truck; ADR 0068). WORKING_VALUE.</summary>
        public const float StandingConvexFactor = 2f;

        /// <summary>The window policy replaces the tier's own schedule.</summary>
        public static bool Applies(int level, bool insets) => insets && level == LowLevel;

        /// <summary>Due-based schedule (ADR 0068): High always, Low with windows; others the round-robin.</summary>
        public static bool DueFor(int level, bool insets) => level == 2 || Applies(level, insets);

        /// <summary>Spare-slot fill of the due-based step: High while driving (ADR 0068); never with the Low window policy
        /// (it would fill the single slot every frame and undo the saving).</summary>
        public static bool FillSpareFor(int level, bool insets, bool standing) => !standing && !Applies(level, insets);

        /// <summary>Refresh interval [frames] of a UN R46 class (2, 4, 5, 6) under the Low window policy.</summary>
        public static float Interval(int r46Class, bool standing)
        {
            if (r46Class == 2) return LowMainInterval;
            return standing ? LowConvexInterval * StandingConvexFactor : LowConvexInterval;
        }

        /// <summary>
        /// Long-run mirror renders per frame under the Low window policy: two class II windows plus
        /// <paramref name="convexCandidates"/> convex mirrors on screen (0-4). Bounded by the cap of 1.
        /// </summary>
        public static float ExpectedRendersPerFrame(int convexCandidates, bool standing)
        {
            if (convexCandidates < 0) convexCandidates = 0;
            float n = 2f / LowMainInterval + convexCandidates / Interval(4, standing);
            return n < 1f ? n : 1f;
        }
    }
}
