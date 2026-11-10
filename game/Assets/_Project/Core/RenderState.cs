namespace Game.Core
{
    /// <summary>
    /// Run-time rendering state that telemetry reports without referencing the rendering assembly (ADR 0062): the
    /// current render scale written by the adaptive controller (Game.Rendering.AdaptiveFrameDriver) and which frame-cap
    /// fallback is active. Plain static fields, written at most once per frame, no allocation.
    /// </summary>
    public static class RenderState
    {
        /// <summary>Render scale of the main camera's pipeline asset (1 = native).</summary>
        public static float RenderScale = 1f;
        /// <summary>The thermal 30 FPS fallback is active (ADR 0046).</summary>
        public static bool ThermalFallback;
        /// <summary>The frame-pacing 30 FPS fallback is active (ADR 0062).</summary>
        public static bool PacingFallback;
    }
}
