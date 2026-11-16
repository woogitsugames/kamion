using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// State of the pad steering stick shaping (ADR 0264): dead zone + curve, amplitude limited by speed, rate-limited
    /// target, release to the physics self-centring (or a ramped return). Pure, allocation-free, tested in EditMode.
    /// </summary>
    public struct PadSteerFilter
    {
        /// <summary>Current steering target, fraction of lock (-1..1).</summary>
        public float Steer;
        /// <summary>True while the stick is outside its dead zone (hands on the wheel).</summary>
        public bool Held;
        /// <summary>True when this source asks for steering authority this frame.</summary>
        public bool Active;

        /// <summary>
        /// One frame. <paramref name="raw"/> stick -1..1; <paramref name="wheelNow"/> = the cab wheel's current position
        /// (fraction of lock, from the feedback) so taking the wheel again continues from where the physics left it.
        /// </summary>
        public void Step(PadKeyboardFeel feel, in PadUserTuning tuning, float raw, float speedMs, float wheelNow, float dt)
        {
            float shaped = PadSteeringMath.Shape(raw, tuning.StickDeadZone, feel.stickOuterDeadZone, tuning.StickExponent);
            bool held = shaped != 0f;
            float kmh = Mathf.Abs(speedMs) * 3.6f;
            if (held && !Held && feel.padReleaseToPhysics) Steer = Mathf.Clamp(wheelNow, -1f, 1f);   // re-grab where the wheel is
            Held = held;
            if (!held && feel.padReleaseToPhysics)
            {
                Active = false;   // hands off: SteeringColumn self-centres from the aligning torque (ADR 0058)
                Steer = Mathf.Clamp(wheelNow, -1f, 1f);
                return;
            }
            float target = shaped * feel.Amplitude(speedMs, tuning.SpeedLimitScale);
            Steer = Mathf.Clamp(PadSteeringMath.RateLimit(Steer, target, feel.PadRate(kmh), feel.padReturnRatePerS, dt), -1f, 1f);
            Active = held || Mathf.Abs(Steer) > 1e-3f;
        }

        public void Reset() { Steer = 0f; Held = false; Active = false; }
    }
}
