using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// Full gamepad driving (ADR 0264) through the <see cref="DrivingActionCatalog.GamepadMap"/> map: analog gas and
    /// brake on the triggers, the cab wheel on the left stick (dead zone, curve, amplitude and rate limited by speed,
    /// release = self-centring from the physics), gears / selector / indicators / parking brake / retarder / camera /
    /// mirrors on buttons, look-around on the right stick. Rebindable (settings screen); generic &lt;Gamepad&gt; layout
    /// (Xbox- and PlayStation-style pads). Allocation-free per frame.
    /// </summary>
    public sealed class GamepadDriverInput : IDriverInput
    {
        public string Name => "pad";
        public bool Enabled { get; set; } = true;

        readonly DrivingActionSet m_Actions;
        public PadKeyboardFeel Feel;
        public PadUserTuning Tuning;
        PadSteerFilter m_Steer;

        /// <summary>View commands of the last <see cref="Sample"/> (camera, mirrors, look, horn).</summary>
        public ViewCommands View;
        /// <summary>Shaped stick and triggers of the last frame (HUD / logs / tests).</summary>
        public float LastStick, LastThrottle, LastBrake;

        public GamepadDriverInput(DrivingActionSet actions, PadKeyboardFeel feel, PadUserTuning tuning)
        {
            m_Actions = actions;
            Feel = feel ?? PadKeyboardFeel.Defaults();
            Tuning = tuning;
        }

        public void Sample(float dt, in VehicleFeedback fb, ref DriverIntent intent)
        {
            View.Clear();
            if (UnityEngine.InputSystem.Gamepad.current == null)
            {
                m_Steer.Reset();
                intent.SteerActive = false; intent.Throttle = 0f; intent.Brake = 0f;
                return;
            }
            var a = m_Actions;
            LastStick = a.Steer.ReadValue<float>();
            m_Steer.Step(Feel, Tuning, LastStick, fb.ForwardSpeed, fb.RoadWheelAngleNormalized, dt);
            intent.Steer = m_Steer.Steer;
            intent.SteerActive = m_Steer.Active;
            intent.HandsOn = m_Steer.Active;

            LastThrottle = PadSteeringMath.Shape(a.Throttle.ReadValue<float>(), Feel.triggerDeadZone, Feel.triggerOuterDeadZone, Feel.throttleExponent);
            LastBrake = PadSteeringMath.Shape(a.Brake.ReadValue<float>(), Feel.triggerDeadZone, Feel.triggerOuterDeadZone, Feel.brakeExponent);
            intent.Throttle = Mathf.Clamp01(LastThrottle);
            intent.Brake = Mathf.Clamp01(LastBrake);

            a.ReadCommands(ref intent, ref View);
            Vector2 look = a.Look.ReadValue<Vector2>();
            View.LookDegS = new Vector2(
                PadSteeringMath.Shape(look.x, Feel.lookDeadZone, 0.02f, Feel.lookExponent),
                PadSteeringMath.Shape(look.y, Feel.lookDeadZone, 0.02f, Feel.lookExponent)) * Feel.lookRateDegS;
        }
    }
}
