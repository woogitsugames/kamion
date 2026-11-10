using UnityEngine;
using UnityEngine.InputSystem;

namespace Game.Controls
{
    /// <summary>Pure math for tilt steering (unit-tested).</summary>
    public static class GyroMath
    {
        /// <summary>
        /// Tilt angle of the screen about its normal [deg] from a gravity vector in SCREEN coordinates
        /// (x right, y up). Clockwise rotation of the phone (right edge down) gives a positive angle.
        /// Works for both "gravity-pointing" and "reaction" sensor conventions once a neutral is subtracted,
        /// because negating the vector is a 180° in-plane rotation (see <see cref="Relative"/>).
        /// </summary>
        public static float TiltAngleDeg(Vector3 gScreen) => Mathf.Atan2(gScreen.x, -gScreen.y) * Mathf.Rad2Deg;

        /// <summary>Angle relative to the calibrated neutral, wrapped to (-180, 180].</summary>
        public static float Relative(float rawDeg, float neutralDeg) => Mathf.DeltaAngle(neutralDeg, rawDeg);

        /// <summary>
        /// Maps a vector from the device's natural (portrait) frame to the current screen frame, for when the
        /// Input System does not compensate for orientation. LandscapeLeft = device rotated 90° counter-clockwise.
        /// </summary>
        public static Vector3 DeviceToScreen(Vector3 d, ScreenOrientation o)
        {
            switch (o)
            {
                case ScreenOrientation.LandscapeLeft: return new Vector3(-d.y, d.x, d.z);
                case ScreenOrientation.LandscapeRight: return new Vector3(d.y, -d.x, d.z);
                case ScreenOrientation.PortraitUpsideDown: return new Vector3(-d.x, -d.y, d.z);
                default: return d;
            }
        }

        public static float SteerFromTilt(float relDeg, float maxTiltDeg, float deadZoneDeg, bool invert)
            => SteerFromTilt(relDeg, maxTiltDeg, deadZoneDeg) * (invert ? -1f : 1f);

        public static float SteerFromTilt(float relDeg, float maxTiltDeg, float deadZoneDeg)
        {
            float x = relDeg / Mathf.Max(1f, maxTiltDeg);
            return Mathf.Clamp(SteeringMath.DeadZone(x, deadZoneDeg / Mathf.Max(1f, maxTiltDeg)), -1f, 1f);
        }
    }

    /// <summary>
    /// Gyro (tilt) steering v0: tilt the phone like a wheel. Gravity sensor (fallback: accelerometer) →
    /// tilt angle about the screen normal → minus calibrated neutral → 1€ filter → dead zone → ±<see cref="MaxTiltDeg"/>.
    /// The output is the TARGET of the cab wheel (normalised to its lock), scaled at speed by
    /// <see cref="SteeringFeel.GyroGain"/>; the cab wheel (<see cref="SteeringColumn"/>) follows it rate-limited (ADR 0058).
    /// Disabled while the app is paused; recalibrates (and outputs 0 briefly) on screen-orientation change.
    /// On-device sign/axis behaviour is UNVERIFIED until tested on the Galaxy A16 (see docs/reports/GATE-1-draft.md).
    /// </summary>
    public sealed class GyroSteering : IDriverInput
    {
        public string Name => "gyro";
        public bool Enabled { get; set; }

        public float MaxTiltDeg = 35f;
        public float DeadZoneDeg = 1.0f;
        /// <summary>Flips the steering direction (settings menu), for a sensor whose sign is opposite on the device.</summary>
        public bool Invert;
        /// <summary>Settings menu: speed-sensitive gain on (default) / off.</summary>
        public bool SpeedSensitive = true;
        public SteeringFeel Feel = SteeringFeel.Defaults();
        public readonly OneEuroFilter Filter = new OneEuroFilter(minCutoff: 1.0f, beta: 0.02f, derivativeCutoff: 1.0f);

        float m_Neutral;
        bool m_Calibrated, m_CalibrateRequested = true;
        float m_HoldTimer;
        ScreenOrientation m_Orientation;

        public bool HasSensor => GravitySensor.current != null || Accelerometer.current != null;
        public float RelativeTiltDeg { get; private set; }
        public float Output { get; private set; }

        /// <summary>Uses the current tilt as neutral on the next sample.</summary>
        public void Calibrate() => m_CalibrateRequested = true;

        /// <summary>Called on application pause: output 0, recalibrate on resume.</summary>
        public void Suspend()
        {
            m_CalibrateRequested = true;
            m_HoldTimer = 0.3f;
            Output = 0f;
            Filter.Reset();
        }

        public static void EnableSensors()
        {
            if (GravitySensor.current != null && !GravitySensor.current.enabled) InputSystem.EnableDevice(GravitySensor.current);
            if (Accelerometer.current != null && !Accelerometer.current.enabled) InputSystem.EnableDevice(Accelerometer.current);
        }

        bool ReadScreenGravity(out Vector3 g)
        {
            g = default;
            if (GravitySensor.current != null && GravitySensor.current.enabled) g = GravitySensor.current.gravity.ReadValue();
            else if (Accelerometer.current != null && Accelerometer.current.enabled) g = Accelerometer.current.acceleration.ReadValue();
            else return false;
            if (g.sqrMagnitude < 1e-6f) return false;
            if (!InputSystem.settings.compensateForScreenOrientation) g = GyroMath.DeviceToScreen(g, Screen.orientation);
            return true;
        }

        public void Sample(float dt, in VehicleFeedback fb, ref DriverIntent intent)
        {
            intent.SteerActive = false;
            if (Screen.orientation != m_Orientation) { m_Orientation = Screen.orientation; Suspend(); }
            if (!ReadScreenGravity(out Vector3 g)) return;
            float raw = GyroMath.TiltAngleDeg(g);
            if (m_CalibrateRequested) { m_Neutral = raw; m_Calibrated = true; m_CalibrateRequested = false; Filter.Reset(); }
            if (!m_Calibrated) return;
            RelativeTiltDeg = Filter.Filter(GyroMath.Relative(raw, m_Neutral), dt);
            if (m_HoldTimer > 0f) { m_HoldTimer -= dt; Output = 0f; }
            else Output = GyroMath.SteerFromTilt(RelativeTiltDeg, MaxTiltDeg, DeadZoneDeg, Invert) * (SpeedSensitive ? Feel.GyroGain(fb.ForwardSpeed * 3.6f) : 1f);
            intent.Steer = Output;
            intent.SteerActive = true;
            intent.HandsOn = true;   // tilt = hands on the wheel; level phone = straight ahead
        }
    }
}
