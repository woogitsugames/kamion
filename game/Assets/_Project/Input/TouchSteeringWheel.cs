using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// On-screen steering wheel (logic; the uGUI widget forwards pointer events here). ADR 0058.
    /// - Rotation: the finger's angle around the wheel centre is tracked incrementally (clockwise = right), so the
    ///   on-screen wheel follows the finger 1:1 and can be turned hand-over-hand up to ±<see cref="HalfRangeDeg"/>.
    /// - Output: the TARGET of the cab wheel, normalised to its lock: on-screen angle / half range → dead zone →
    ///   sensitivity → speed-sensitive gain (<see cref="SteeringFeel.WheelGain"/>: the comfort range reaches full lock
    ///   when manoeuvring, but at speed one on-screen degree is one cab-wheel degree). The cab wheel itself
    ///   (<see cref="SteeringColumn"/>) follows with the hand-speed limit and inertia, and self-centres when released.
    /// - Released: the on-screen wheel shows the cab wheel (<see cref="FollowColumn"/>), so it returns with it and can
    ///   be grabbed again without a jump.
    /// </summary>
    public sealed class TouchSteeringWheel : IDriverInput
    {
        public string Name => "koło";
        public bool Enabled { get; set; } = true;

        /// <summary>Half lock-to-lock range of the on-screen wheel [deg]; 270 = comfort, 900 = sim (docs/04 §3).</summary>
        public float HalfRangeDeg = 270f;
        public float DeadZone = 0.01f;
        /// <summary>Output gain (settings menu); 1 = full lock at the full wheel range (at manoeuvring speed).</summary>
        public float Sensitivity = 1f;
        /// <summary>Settings menu: speed-sensitive mapping on (default) / off (fixed comfort gear-up at every speed).</summary>
        public bool SpeedSensitive = true;
        /// <summary>Finger closer than this to the centre [px] is ignored (angle is ill-defined).</summary>
        public float MinRadiusPx = 24f;
        public SteeringFeel Feel = SteeringFeel.Defaults();

        public float WheelDeg { get; private set; }
        public bool Held { get; private set; }
        /// <summary>Last target (normalised cab-wheel angle) written to the intent.</summary>
        public float Output { get; private set; }
        /// <summary>Gain applied in the last sample (speed-sensitive mapping).</summary>
        public float LastGain { get; private set; } = 1f;

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

        /// <summary>Target (normalised to the cab-wheel lock) for an on-screen angle at a gain.</summary>
        public float Target(float wheelDeg, float gain)
            => Mathf.Clamp(SteeringMath.DeadZone(wheelDeg / Mathf.Max(1f, HalfRangeDeg), DeadZone) * Sensitivity * gain, -1f, 1f);

        /// <summary>
        /// While released, puts the on-screen wheel where the cab wheel is (inverse of <see cref="Target"/> at the last
        /// gain), so it self-centres with it; it only ever moves toward centre.
        /// </summary>
        public void FollowColumn(float columnNormalized)
        {
            if (Held) return;
            float u = columnNormalized / Mathf.Max(1e-3f, Sensitivity * LastGain);
            float au = Mathf.Abs(u);
            float x = au < 1e-6f ? 0f : Mathf.Sign(u) * (DeadZone + au * (1f - DeadZone));
            x = Mathf.Clamp(x * HalfRangeDeg, -HalfRangeDeg, HalfRangeDeg);
            // The cab wheel may still lag behind where the finger let go: the on-screen wheel never moves outward to
            // meet it (no jump away from centre), it waits and returns with it.
            WheelDeg = WheelDeg * x <= 0f ? 0f : Mathf.Sign(x) * Mathf.Min(Mathf.Abs(WheelDeg), Mathf.Abs(x));
        }

        public void Sample(float dt, in VehicleFeedback fb, ref DriverIntent intent)
        {
            float lockDeg = fb.HandwheelLockDeg > 0f ? fb.HandwheelLockDeg : Feel.fallbackLockDeg;
            LastGain = SpeedSensitive ? Feel.WheelGain(fb.ForwardSpeed * 3.6f, HalfRangeDeg, lockDeg) : 1f;
            Output = Target(WheelDeg, LastGain);
            intent.Steer = Output;
            intent.SteerActive = true;
            intent.HandsOn = Held;
        }
    }
}
