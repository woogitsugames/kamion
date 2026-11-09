using UnityEngine;

namespace Game.Controls
{
    /// <summary>Shared shaping helpers for steering commands (pure functions, unit-tested).</summary>
    public static class SteeringMath
    {
        /// <summary>
        /// Dead zone with rescale: |x| &lt; deadZone → 0, otherwise linear from 0 at the edge to ±1 at ±1
        /// (no jump at the dead-zone edge).
        /// </summary>
        public static float DeadZone(float x, float deadZone)
        {
            float a = Mathf.Abs(x);
            if (a <= deadZone) return 0f;
            return Mathf.Sign(x) * Mathf.Clamp01((a - deadZone) / Mathf.Max(1e-5f, 1f - deadZone));
        }

        /// <summary>Sensitivity curve: blend between linear (0) and cubic (1), sign-preserving.</summary>
        public static float Curve(float x, float cubic)
        {
            x = Mathf.Clamp(x, -1f, 1f);
            return Mathf.Lerp(x, x * x * x, Mathf.Clamp01(cubic));
        }

        /// <summary>Signed angle difference b - a wrapped to (-180, 180].</summary>
        public static float DeltaAngle(float a, float b) => Mathf.DeltaAngle(a, b);

        /// <summary>
        /// Angle of a screen-space vector measured clockwise from screen-up [deg] (screen y up, x right).
        /// Dragging a finger clockwise around the wheel centre increases it.
        /// </summary>
        public static float ClockwiseAngleFromUp(Vector2 fromCentre) => Mathf.Atan2(fromCentre.x, fromCentre.y) * Mathf.Rad2Deg;

        /// <summary>Exponential smoothing factor for a first-order filter with time constant tau.</summary>
        public static float SmoothingAlpha(float dt, float tau) => tau <= 1e-5f ? 1f : 1f - Mathf.Exp(-dt / tau);
    }
}
