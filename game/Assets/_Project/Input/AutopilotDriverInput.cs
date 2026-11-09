using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// Scripted driver for device measurements and soak runs: follows a circle (pure pursuit) at a target speed.
    /// Enabled by the launch argument "autopilot" (e.g. <c>adb shell am start ... -e autopilot circle50</c>).
    /// </summary>
    public sealed class AutopilotDriverInput : IDriverInput
    {
        public string Name => "autopilot";
        public bool Enabled { get; set; }

        public Vector3 CircleCenter;
        public float Radius = 50f;
        /// <summary>true = clockwise seen from above (right turn).</summary>
        public bool Clockwise;
        public float TargetSpeedKmh = 40f;
        public float LookAhead = 12f;
        public float Wheelbase = 3.7f;
        public float MaxRoadWheelAngleDeg = 40f;

        public float LastSteer { get; private set; }

        public void Sample(float dt, in VehicleFeedback fb, ref DriverIntent intent)
        {
            Vector3 p = fb.Position; p.y = 0f;
            Vector3 c = CircleCenter; c.y = 0f;
            Vector3 radial = p - c;
            if (radial.sqrMagnitude < 1e-4f) radial = Vector3.forward;
            radial = radial.normalized * Radius;
            float ang = (Clockwise ? -1f : 1f) * LookAhead / Mathf.Max(1f, Radius) * Mathf.Rad2Deg;
            // Rotation about +Y by a positive angle is clockwise seen from above in Unity.
            Vector3 target = c + Quaternion.AngleAxis(Clockwise ? Mathf.Abs(ang) : -Mathf.Abs(ang), Vector3.up) * radial;
            Vector3 to = target - p;
            Vector3 fwd = fb.Forward; fwd.y = 0f;
            float alpha = Vector3.SignedAngle(fwd, to, Vector3.up) * Mathf.Deg2Rad; // + = target to the right
            float ld = Mathf.Max(1f, to.magnitude);
            float delta = Mathf.Atan(2f * Wheelbase * Mathf.Sin(alpha) / ld) * Mathf.Rad2Deg;
            LastSteer = Mathf.Clamp(delta / MaxRoadWheelAngleDeg, -1f, 1f);

            float vKmh = fb.ForwardSpeed * 3.6f;
            float e = TargetSpeedKmh - vKmh;
            intent.Steer = LastSteer;
            intent.SteerActive = true;
            intent.Throttle = Mathf.Clamp01(e * 0.12f);
            intent.Brake = e < -4f ? Mathf.Clamp01(-e * 0.05f) : 0f;
        }
    }
}
