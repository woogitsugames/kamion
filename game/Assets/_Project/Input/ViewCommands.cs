using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// Per-frame view and cab commands from the PC input sources that are not driver intents of the vehicle (ADR 0264):
    /// camera, mirror insets, look-around, horn. Kept out of <see cref="DriverIntent"/> so the physics-facing struct is
    /// unchanged; the gameplay bridge applies them to the camera rig, mirrors and audio.
    /// </summary>
    public struct ViewCommands
    {
        /// <summary>One-shot: next camera mode (cab / chase / orbit).</summary>
        public bool CycleCamera;
        /// <summary>One-shot: mirror insets on / off (D70).</summary>
        public bool ToggleMirrorInsets;
        /// <summary>Horn held.</summary>
        public bool Horn;
        /// <summary>Look-around rate this frame [deg/s], x = yaw right, y = pitch up (already shaped).</summary>
        public Vector2 LookDegS;

        public void Clear() { CycleCamera = false; ToggleMirrorInsets = false; Horn = false; LookDegS = Vector2.zero; }
    }
}
