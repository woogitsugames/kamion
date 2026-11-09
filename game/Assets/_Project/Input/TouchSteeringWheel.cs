using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// On-screen steering wheel v0 (logic; the uGUI widget forwards pointer events here).
    /// - Rotation: the finger's angle around the wheel centre is tracked incrementally (clockwise = right), so the
    ///   wheel can be turned hand-over-hand through several turns up to ±<see cref="HalfRangeDeg"/>.
    /// - Output: wheel angle / half range → dead zone → light smoothing (τ = <see cref="SmoothingTau"/>, 20 ms default).
    /// - Self-centre when released: angular speed toward 0 from vehicle speed and the model's aligning torque
    ///   (<see cref="SelfCentreRate"/>); no centring at standstill (as on a real truck with power steering at rest).
    ///   This is a documented approximation, not a force-feedback model: the finger cannot be pushed.
    /// </summary>
    public sealed class TouchSteeringWheel : IDriverInput
    {
        public string Name => "koło";
        public bool Enabled { get; set; } = true;

        /// <summary>Half lock-to-lock range of the on-screen wheel [deg]; 270 = comfort, 900 = sim (docs/04 §3).</summary>
        public float HalfRangeDeg = 270f;
        public float DeadZone = 0.01f;
        /// <summary>Output gain (settings menu); 1 = full lock at the full wheel range.</summary>
        public float Sensitivity = 1f;
        /// <summary>Multiplier of the self-centring speed (settings menu); 0 = the wheel stays where it was left.</summary>
        public float CentreStrength = 1f;
        public float SmoothingTau = 0.02f;
        /// <summary>Centring speed limit [deg/s of the on-screen wheel].</summary>
        public float CentreRateMaxDegS = 540f;
        /// <summary>Speed at which the speed term saturates [m/s].</summary>
        public float CentreSpeedRef = 8f;
        /// <summary>Aligning torque at which the torque term saturates [N m].</summary>
        public float AligningTorqueRef = 800f;
        /// <summary>Finger closer than this to the centre [px] is ignored (angle is ill-defined).</summary>
        public float MinRadiusPx = 24f;

        public float WheelDeg { get; private set; }
        public bool Held { get; private set; }
        public float Output { get; private set; }

        float m_LastFingerDeg;
        bool m_HasFinger;

        public void PointerDown(Vector2 fromCentre)
        {
            Held = true;
            m_HasFinger = fromCentre.magnitude >= MinRadiusPx;
            if (m_HasFinger) m_LastFingerDeg = SteeringMath.ClockwiseAngleFromUp(fromCentre);
        }

        public void PointerDrag(Vector2 fromCentre)
        {
            if (!Held) return;
            if (fromCentre.magnitude < MinRadiusPx) { m_HasFinger = false; return; }
            float a = SteeringMath.ClockwiseAngleFromUp(fromCentre);
            if (!m_HasFinger) { m_LastFingerDeg = a; m_HasFinger = true; return; }
            float d = SteeringMath.DeltaAngle(m_LastFingerDeg, a);
            m_LastFingerDeg = a;
            WheelDeg = Mathf.Clamp(WheelDeg + d, -HalfRangeDeg, HalfRangeDeg);
        }

        public void PointerUp() { Held = false; m_HasFinger = false; }

        /// <summary>Sets the wheel angle directly (tests, reset).</summary>
        public void SetWheelDeg(float deg) => WheelDeg = Mathf.Clamp(deg, -HalfRangeDeg, HalfRangeDeg);

        /// <summary>Centring speed [deg/s] for a released wheel.</summary>
        public static float SelfCentreRate(float forwardSpeed, float aligningTorque, float maxRate, float speedRef, float torqueRef)
        {
            float k = 0.6f * Mathf.Clamp01(Mathf.Abs(forwardSpeed) / Mathf.Max(speedRef, 0.1f))
                    + 0.4f * Mathf.Clamp01(Mathf.Abs(aligningTorque) / Mathf.Max(torqueRef, 1f));
            return maxRate * Mathf.Clamp01(k);
        }

        public void Sample(float dt, in VehicleFeedback fb, ref DriverIntent intent)
        {
            if (!Held)
            {
                float rate = SelfCentreRate(fb.ForwardSpeed, fb.AligningTorque, CentreRateMaxDegS, CentreSpeedRef, AligningTorqueRef);
                WheelDeg = Mathf.MoveTowards(WheelDeg, 0f, rate * Mathf.Max(0f, CentreStrength) * dt);
            }
            float target = Mathf.Clamp(SteeringMath.DeadZone(WheelDeg / Mathf.Max(1f, HalfRangeDeg), DeadZone) * Sensitivity, -1f, 1f);
            Output = Mathf.Lerp(Output, target, SteeringMath.SmoothingAlpha(dt, SmoothingTau));
            intent.Steer = Output;
            intent.SteerActive = true;
        }
    }
}
