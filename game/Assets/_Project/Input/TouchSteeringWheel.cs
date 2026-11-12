using UnityEngine;

namespace Game.Controls
{
    /// <summary>How the finger turns the on-screen wheel (ADR 0135).</summary>
    public enum WheelGrab
    {
        /// <summary>Sideways thumb slide anywhere on the wheel: relative, millimetres of finger travel to wheel degrees,
        /// independent of the radius and of where the wheel was touched. Shipped default (settings schema 4).</summary>
        Drag = 0,
        /// <summary>Finger angle around the wheel centre, 1:1 (ADR 0058; the only mode before ADR 0135).</summary>
        Rotate = 1,
    }

    /// <summary>
    /// On-screen steering wheel (logic; the uGUI widget forwards pointer events here). ADR 0058, ADR 0135.
    /// - Input: <see cref="WheelGrab.Drag"/> = the horizontal finger travel [mm] since the last event times
    ///   <see cref="SteeringFeel.dragScreenDegPerMm"/> turns the on-screen wheel (relative, no jump on touch-down, works
    ///   for a thumb in the screen corner where a circular motion is not possible); <see cref="WheelGrab.Rotate"/> = the
    ///   finger angle around the wheel centre tracked incrementally (clockwise = right), 1:1, hand-over-hand up to
    ///   +-<see cref="HalfRangeDeg"/>.
    /// - Output: the TARGET of the cab wheel, normalised to its lock: on-screen angle / half range, dead zone,
    ///   sensitivity, speed-sensitive gain (<see cref="SteeringFeel.WheelGain"/>: the comfort range reaches full lock
    ///   when manoeuvring; at speed a fixed number of cab-wheel degrees per on-screen degree, i.e. per millimetre).
    ///   The cab wheel itself (<see cref="SteeringColumn"/>) follows with the hand-speed limit and inertia and
    ///   self-centres when released (ADR 0058).
    /// - Released: the on-screen wheel shows the cab wheel (<see cref="FollowColumn"/>), so it returns with it and can
    ///   be grabbed again without a jump. <see cref="ColumnScreenDeg"/> = the cab wheel in on-screen degrees at all
    ///   times (the HUD draws it as a marker, so the lag of the heavy wheel behind the finger is visible).
    /// </summary>
    public sealed class TouchSteeringWheel : IDriverInput
    {
        public string Name => "koło";
        public bool Enabled { get; set; } = true;

        /// <summary>Half lock-to-lock range of the on-screen wheel [deg]; 270 = comfort, 900 = sim (docs/04 section 3).</summary>
        public float HalfRangeDeg = 270f;
        public float DeadZone = 0.01f;
        /// <summary>Output gain (settings menu); 1 = full lock at the full wheel range (at manoeuvring speed).</summary>
        public float Sensitivity = 1f;
        /// <summary>Settings menu: speed-sensitive mapping on (default) / off (fixed comfort gear-up at every speed).</summary>
        public bool SpeedSensitive = true;
        /// <summary>Gesture. The class default is the legacy rotate gesture; the game applies
        /// <see cref="ControlSettings.wheelDragGrab"/> (default: drag) through <see cref="ControlSettings.ApplyTo"/>.</summary>
        public WheelGrab Grab = WheelGrab.Rotate;
        /// <summary>Rotate gesture: a finger closer than this to the centre [canvas units] is ignored (angle ill-defined).</summary>
        public float MinRadiusPx = 24f;
        public SteeringFeel Feel = SteeringFeel.Defaults();

        public float WheelDeg { get; private set; }
        public bool Held { get; private set; }
        /// <summary>Last target (normalised cab-wheel angle) written to the intent.</summary>
        public float Output { get; private set; }
        /// <summary>Gain applied in the last sample (speed-sensitive mapping).</summary>
        public float LastGain { get; private set; } = 1f;
        /// <summary>The cab wheel expressed in on-screen degrees (inverse of <see cref="Target"/>), updated by
        /// <see cref="FollowColumn"/> every fixed step, held or not.</summary>
        public float ColumnScreenDeg { get; private set; }

        float m_LastFingerDeg, m_LastMmX;
        bool m_HasFinger;

        static readonly Vector2 k_NoMm = new Vector2(float.NaN, float.NaN);

        /// <summary>Overload without a physical position (rotate gesture only; tests, legacy callers).</summary>
        public void PointerDown(Vector2 fromCentre) => PointerDown(fromCentre, k_NoMm);

        /// <param name="fromCentre">Finger relative to the wheel centre [canvas units, y up].</param>
        /// <param name="screenMm">Finger on the screen [mm] (pixels / DPI); NaN = unknown (the drag gesture then does nothing).</param>
        public void PointerDown(Vector2 fromCentre, Vector2 screenMm)
        {
            Held = true;
            if (Grab == WheelGrab.Drag)
            {
                m_HasFinger = !float.IsNaN(screenMm.x);
                m_LastMmX = screenMm.x;
                return;
            }
            m_HasFinger = fromCentre.magnitude >= MinRadiusPx;
            if (m_HasFinger) m_LastFingerDeg = SteeringMath.ClockwiseAngleFromUp(fromCentre);
        }

        public void PointerDrag(Vector2 fromCentre) => PointerDrag(fromCentre, k_NoMm);

        public void PointerDrag(Vector2 fromCentre, Vector2 screenMm)
        {
            if (!Held) return;
            if (Grab == WheelGrab.Drag)
            {
                if (float.IsNaN(screenMm.x)) return;
                if (!m_HasFinger) { m_LastMmX = screenMm.x; m_HasFinger = true; return; }
                // Incremental: after the wheel hits its stop, reversing the finger turns it back at once (no dead travel).
                WheelDeg = Mathf.Clamp(WheelDeg + SteeringMath.DragDeg(screenMm.x - m_LastMmX, DragDegPerMm), -HalfRangeDeg, HalfRangeDeg);
                m_LastMmX = screenMm.x;
                return;
            }
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
        /// Drag gesture: on-screen degrees per millimetre for the current range. The comfort range (270 deg) takes
        /// 25 mm; longer ranges take longer, but only with the square root of the range (900 deg sim: ~46 mm instead of
        /// 83 mm, two thumb strokes at standstill) so the sim range stays usable with a thumb (review 0134-0135 P2).
        /// </summary>
        public float DragDegPerMm => Feel.dragScreenDegPerMm * Mathf.Sqrt(Mathf.Max(1f, HalfRangeDeg / 270f));

        /// <summary>Cab-wheel degrees per on-screen degree at speed for the current gesture (see <see cref="SteeringFeel"/>).</summary>
        public float HighSpeedScreenToHandwheel
            => Grab == WheelGrab.Drag ? Feel.dragHighSpeedHandwheelDegPerMm / Mathf.Max(1e-3f, DragDegPerMm) : Feel.highSpeedScreenToHandwheel;

        /// <summary>
        /// Every fixed step: records where the cab wheel is in on-screen degrees (<see cref="ColumnScreenDeg"/>); while
        /// released, also puts the on-screen wheel there (inverse of <see cref="Target"/> at the last gain), so it
        /// self-centres with it; it only ever moves toward centre.
        /// </summary>
        public void FollowColumn(float columnNormalized)
        {
            float u = columnNormalized / Mathf.Max(1e-3f, Sensitivity * LastGain);
            float au = Mathf.Abs(u);
            float x = au < 1e-6f ? 0f : Mathf.Sign(u) * (DeadZone + au * (1f - DeadZone));
            x = Mathf.Clamp(x * HalfRangeDeg, -HalfRangeDeg, HalfRangeDeg);
            ColumnScreenDeg = x;
            if (Held) return;
            // The cab wheel may still lag behind where the finger let go: the on-screen wheel never moves outward to
            // meet it (no jump away from centre), it waits and returns with it.
            WheelDeg = WheelDeg * x <= 0f ? 0f : Mathf.Sign(x) * Mathf.Min(Mathf.Abs(WheelDeg), Mathf.Abs(x));
        }

        public void Sample(float dt, in VehicleFeedback fb, ref DriverIntent intent)
        {
            float lockDeg = fb.HandwheelLockDeg > 0f ? fb.HandwheelLockDeg : Feel.fallbackLockDeg;
            float kmh = fb.ForwardSpeed * 3.6f;
            LastGain = !SpeedSensitive ? 1f
                : Grab == WheelGrab.Drag ? Feel.DragGain(kmh, HalfRangeDeg, lockDeg, HighSpeedScreenToHandwheel) // ADR 0149
                : Feel.WheelGain(kmh, HalfRangeDeg, lockDeg, HighSpeedScreenToHandwheel);
            Output = Target(WheelDeg, LastGain);
            intent.Steer = Output;
            intent.SteerActive = true;
            intent.HandsOn = Held;
        }
    }
}
