using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// Keyboard driving with rebindable keys (ADR 0264) through the <see cref="DrivingActionCatalog.KeyboardMap"/> map
    /// and <see cref="KeyboardAxisRamp"/> (gas, brake and steering ramp up and down; steering amplitude and rate shrink
    /// with speed). Supersedes the fixed-key <see cref="KeyboardDriverInput"/> when installed (same default keys).
    /// Allocation-free per frame.
    /// </summary>
    public sealed class KeyboardBindingsDriverInput : IDriverInput, IMenuGatedInput
    {
        public string Name => "klawiatura";
        public bool Enabled { get; set; } = true;

        readonly DrivingActionSet m_Actions;
        public PadKeyboardFeel Feel;
        public PadUserTuning Tuning;
        KeyboardAxisRamp m_Ramp;
        public ViewCommands View;

        public KeyboardBindingsDriverInput(DrivingActionSet actions, PadKeyboardFeel feel, PadUserTuning tuning)
        {
            m_Actions = actions;
            Feel = feel ?? PadKeyboardFeel.Defaults();
            Tuning = tuning;
        }

        /// <summary>Menu open (review #131 P1-1): no view commands, key ramps at rest (the arrows navigate the menu).</summary>
        public void SampleBlocked(float dt, in VehicleFeedback fb)
        {
            View.Clear();
            m_Ramp.Reset();
        }

        public void Sample(float dt, in VehicleFeedback fb, ref DriverIntent intent)
        {
            View.Clear();
            if (UnityEngine.InputSystem.Keyboard.current == null)
            {
                m_Ramp.Reset();
                intent.SteerActive = false; intent.Throttle = 0f; intent.Brake = 0f;
                return;
            }
            var a = m_Actions;
            float s = a.Steer.ReadValue<float>();
            int dir = s > 0.5f ? 1 : s < -0.5f ? -1 : 0;   // both keys held = composite 0 = no steering
            m_Ramp.Step(Feel, Tuning, dir, a.Throttle.ReadValue<float>() > 0.5f, a.Brake.ReadValue<float>() > 0.5f, fb.ForwardSpeed, dt);
            intent.Steer = m_Ramp.Steer;
            intent.SteerActive = dir != 0 || Mathf.Abs(m_Ramp.Steer) > 1e-3f;
            intent.HandsOn = intent.SteerActive;   // the key ramp has its own return to centre
            intent.Throttle = m_Ramp.Throttle;
            intent.Brake = m_Ramp.Brake;
            a.ReadCommands(ref intent, ref View);
        }
    }
}
