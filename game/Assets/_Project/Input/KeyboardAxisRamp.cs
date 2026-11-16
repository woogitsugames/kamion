using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// State of the keyboard axis ramps (ADR 0264): keys are digital, so gas, brake and steering rise and fall at
    /// rates from <see cref="PadKeyboardFeel"/> like a foot on a pedal or hands on a wheel. Steering amplitude and rate
    /// shrink with speed (same model as the pad). Pure, allocation-free, tested in EditMode.
    /// </summary>
    public struct KeyboardAxisRamp
    {
        public float Steer, Throttle, Brake;

        /// <summary>One frame. <paramref name="steerDir"/> -1 left / 0 / +1 right; <paramref name="speedMs"/> signed forward speed.</summary>
        public void Step(PadKeyboardFeel feel, in PadUserTuning tuning, int steerDir, bool throttle, bool brake, float speedMs, float dt)
        {
            float kmh = Mathf.Abs(speedMs) * 3.6f;
            float amp = feel.Amplitude(speedMs, tuning.SpeedLimitScale);
            float rate = feel.KeyRate(kmh) * Mathf.Max(0.1f, tuning.KeySteerScale);
            Steer = PadSteeringMath.RampSteer(Steer, steerDir, amp, rate, feel.keyReturnRatePerS, dt);
            Throttle = PadSteeringMath.RampPedal(Throttle, throttle, feel.keyThrottleRise, feel.keyRelease, dt);
            Brake = PadSteeringMath.RampPedal(Brake, brake, feel.keyBrakeRise, feel.keyRelease, dt);
        }

        public void Reset() { Steer = 0f; Throttle = 0f; Brake = 0f; }
    }
}
