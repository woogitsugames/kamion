using UnityEngine;
using UnityEngine.InputSystem;

namespace Game.Controls
{
    /// <summary>
    /// Gamepad driving (ADR 0261, Windows player): left stick X = steering wheel target (dead zone + progressive curve;
    /// the steering column still limits the hand speed), RT = accelerator, LT = service brake, A = parking brake,
    /// RB / LB = shift up / down, X = D, B = N, Back (Select) = R, d-pad left / right = turn signals, d-pad up = hazard,
    /// d-pad down / left-stick click = retarder stalk one detent more / less.
    /// Y (next camera), Start (menu) and the right stick (look around) are read by the scene bootstrap - not driver commands.
    /// Allocation-free; inactive (no steering authority, pedals 0) when no pad is connected.
    /// </summary>
    public sealed class GamepadDriverInput : IDriverInput
    {
        public string Name => "pad";
        public bool Enabled { get; set; } = true;

        /// <summary>Stick dead zone (WORKING_VALUE: worn pads rest at up to ~0.1).</summary>
        public float DeadZone = 0.12f;
        /// <summary>Exponent of the stick curve: 1 = linear, 2 = fine control around the centre (WORKING_VALUE).</summary>
        public float Curve = 1.8f;
        /// <summary>Trigger travel ignored at rest (WORKING_VALUE).</summary>
        public float TriggerDeadZone = 0.04f;

        /// <summary>Stick deflection -1..1 → steering command -1..1: dead zone removed, rescaled to full range, progressive.</summary>
        public static float ShapeAxis(float raw, float deadZone, float curve)
        {
            float a = Mathf.Abs(raw);
            if (a <= deadZone) return 0f;
            float t = Mathf.Clamp01((a - deadZone) / Mathf.Max(1e-4f, 1f - deadZone));
            return Mathf.Sign(raw) * Mathf.Pow(t, Mathf.Max(1f, curve));
        }

        /// <summary>Trigger 0..1 → pedal 0..1 with a small dead zone at rest.</summary>
        public static float ShapeTrigger(float raw, float deadZone)
        {
            if (raw <= deadZone) return 0f;
            return Mathf.Clamp01((raw - deadZone) / Mathf.Max(1e-4f, 1f - deadZone));
        }

        public void Sample(float dt, in VehicleFeedback fb, ref DriverIntent intent)
        {
            var pad = Gamepad.current;
            if (pad == null) { intent.SteerActive = false; intent.Throttle = 0; intent.Brake = 0; return; }

            float steer = ShapeAxis(pad.leftStick.x.ReadValue(), DeadZone, Curve);
            intent.Steer = steer;
            intent.SteerActive = steer != 0f;
            intent.HandsOn = intent.SteerActive;   // released stick = released wheel (self-centring, ADR 0058)
            intent.Throttle = ShapeTrigger(pad.rightTrigger.ReadValue(), TriggerDeadZone);
            intent.Brake = ShapeTrigger(pad.leftTrigger.ReadValue(), TriggerDeadZone);

            if (pad.buttonSouth.wasPressedThisFrame) intent.ToggleParkingBrake = true;
            if (pad.rightShoulder.wasPressedThisFrame) intent.ShiftDelta += 1;
            if (pad.leftShoulder.wasPressedThisFrame) intent.ShiftDelta -= 1;
            if (pad.buttonWest.wasPressedThisFrame) intent.Selector = SelectorRequest.Drive;
            if (pad.buttonEast.wasPressedThisFrame) intent.Selector = SelectorRequest.Neutral;
            if (pad.selectButton.wasPressedThisFrame) intent.Selector = SelectorRequest.Reverse;
            if (pad.dpad.left.wasPressedThisFrame) intent.TurnSignal = TurnSignalRequest.Left;
            if (pad.dpad.right.wasPressedThisFrame) intent.TurnSignal = TurnSignalRequest.Right;
            if (pad.dpad.up.wasPressedThisFrame) intent.TurnSignal = TurnSignalRequest.Hazard;
            if (pad.dpad.down.wasPressedThisFrame) intent.RetarderDelta += 1;
            if (pad.leftStickButton.wasPressedThisFrame) intent.RetarderDelta -= 1;
        }
    }
}
