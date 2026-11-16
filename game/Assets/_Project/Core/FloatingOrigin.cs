using System;
using UnityEngine;

namespace Game.Core
{
    /// <summary>
    /// Floating-origin notification hub (ADR 0003, ADR 0235). The world streamer (Game.World.Streaming.WorldStreamer)
    /// moves every scene root and rigidbody by <c>offset</c> in one safe moment of the step and then raises
    /// <see cref="Moved"/>, so components that keep world-space positions outside the transform hierarchy (camera smoothing,
    /// autopilot paths, safe-pose buffers, trails) add the same offset. Lives in Game.Core because every assembly
    /// references it; it holds no world data itself. Raising it allocates nothing (the delegate list is built at subscribe).
    /// </summary>
    public static class FloatingOrigin
    {
        /// <summary>Raised after a shift with the offset every world position was moved by (new = old + offset).</summary>
        public static event Action<Vector3> Moved;

        /// <summary>Sum of all offsets since the process started (diagnostics only; the double origin is kept by the streamer).</summary>
        public static Vector3 TotalOffset { get; private set; }

        /// <summary>Number of shifts since the process started (diagnostics, tests).</summary>
        public static int ShiftCount { get; private set; }

        /// <summary>Called by the shifter after it moved the scene; never call it without moving the scene.</summary>
        public static void Notify(Vector3 offset)
        {
            TotalOffset += offset;
            ShiftCount++;
            Moved?.Invoke(offset);
        }
    }
}
