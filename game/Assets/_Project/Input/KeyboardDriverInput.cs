using UnityEngine;
using UnityEngine.InputSystem;

namespace Game.Controls
{
    /// <summary>
    /// Keyboard driving for editor testing. W/↑ throttle, S/↓ brake, A/D/←/→ steer (rate-limited, auto-centre),
    /// 1/2/3 = D/N/R, E/Q = shift +/-, M = auto/manual, Space = parking brake. Analog values ramp so keys behave like pedals.
    /// </summary>
    public sealed class KeyboardDriverInput : IDriverInput
    {
        public string Name => "klawiatura";
        public bool Enabled { get; set; } = true;

        public float SteerRate = 1.2f, SteerReturnRate = 2.0f, ThrottleRate = 2.5f, BrakeRate = 3.0f, ReleaseRate = 5f;

        float m_Steer, m_Throttle, m_Brake;

        /// <summary>Steering state update for a key direction (-1 left, 0 none, +1 right).</summary>
        public static float StepSteer(float current, int direction, float dt, float rate, float returnRate)
        {
            if (direction == 0) return Mathf.MoveTowards(current, 0f, returnRate * dt);
            // Reversing direction returns to centre at the faster of the two rates first.
            float r = Mathf.Sign(current) != direction && current != 0f ? Mathf.Max(rate, returnRate) : rate;
            return Mathf.Clamp(current + direction * r * dt, -1f, 1f);
        }

        public void Sample(float dt, in VehicleFeedback fb, ref DriverIntent intent)
        {
            var kb = Keyboard.current;
            if (kb == null) { intent.SteerActive = false; intent.Throttle = 0; intent.Brake = 0; return; }
            int dir = 0;
            if (kb.aKey.isPressed || kb.leftArrowKey.isPressed) dir -= 1;
            if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) dir += 1;
            m_Steer = StepSteer(m_Steer, dir, dt, SteerRate, SteerReturnRate);
            bool thr = kb.wKey.isPressed || kb.upArrowKey.isPressed;
            bool brk = kb.sKey.isPressed || kb.downArrowKey.isPressed;
            m_Throttle = Mathf.MoveTowards(m_Throttle, thr ? 1f : 0f, (thr ? ThrottleRate : ReleaseRate) * dt);
            m_Brake = Mathf.MoveTowards(m_Brake, brk ? 1f : 0f, (brk ? BrakeRate : ReleaseRate) * dt);

            intent.Steer = m_Steer;
            intent.SteerActive = dir != 0 || Mathf.Abs(m_Steer) > 1e-3f;
            intent.Throttle = m_Throttle;
            intent.Brake = m_Brake;
            if (kb.digit1Key.wasPressedThisFrame) intent.Selector = SelectorRequest.Drive;
            if (kb.digit2Key.wasPressedThisFrame) intent.Selector = SelectorRequest.Neutral;
            if (kb.digit3Key.wasPressedThisFrame) intent.Selector = SelectorRequest.Reverse;
            if (kb.eKey.wasPressedThisFrame) intent.ShiftDelta += 1;
            if (kb.qKey.wasPressedThisFrame) intent.ShiftDelta -= 1;
            if (kb.spaceKey.wasPressedThisFrame) intent.ToggleParkingBrake = true;
            if (kb.mKey.wasPressedThisFrame) intent.ToggleManual = true;
        }
    }
}
