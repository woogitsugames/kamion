using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// State of the keyboard axis ramps (ADR 0264): keys are digital, so gas, brake and steering rise and fall at
    /// rates from <see cref="PadKeyboardFeel"/> like a foot on a pedal or hands on a wheel. Steering amplitude and rate
    /// shrink with speed (same model as the pad); a fresh steering key starts slower and reaches the full rate after
    /// <see cref="PadKeyboardFeel.keyOnsetS"/> (taps = fine corrections, ADR 0312). Pure, allocation-free, tested in EditMode.
    /// </summary>
    public struct KeyboardAxisRamp
    {
        public float Steer, Throttle, Brake;
        /// <summary>How long the current steering key has been held [s] (progressive onset, ADR 0312); 0 = none held.</summary>
        public float SteerHeldS;
        int m_LastDir;

        /// <summary>One frame. <paramref name="steerDir"/> -1 left / 0 / +1 right; <paramref name="speedMs"/> signed forward speed.</summary>
        public void Step(PadKeyboardFeel feel, in PadUserTuning tuning, int steerDir, bool throttle, bool brake, float speedMs, float dt)
        {
            float kmh = Mathf.Abs(speedMs) * 3.6f;
            float amp = feel.Amplitude(speedMs, tuning.SpeedLimitScale);
            SteerHeldS = steerDir == 0 ? 0f : steerDir == m_LastDir ? SteerHeldS + Mathf.Max(0f, dt) : Mathf.Max(0f, dt);
            m_LastDir = steerDir;
            float rate = feel.KeyRate(kmh) * Mathf.Max(0.1f, tuning.KeySteerScale) * feel.KeyOnset(SteerHeldS);
            Steer = PadSteeringMath.RampSteer(Steer, steerDir, amp, rate, feel.keyReturnRatePerS, dt);
            Throttle = PadSteeringMath.RampPedal(Throttle, throttle, feel.keyThrottleRise, feel.keyRelease, dt);
            Brake = PadSteeringMath.RampPedal(Brake, brake, feel.keyBrakeRise, feel.keyRelease, dt);
        }

        public void Reset() { Steer = 0f; Throttle = 0f; Brake = 0f; SteerHeldS = 0f; m_LastDir = 0; }
    }
}
