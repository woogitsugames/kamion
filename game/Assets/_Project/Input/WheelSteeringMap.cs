using System;

namespace Game.Controls
{
    /// <summary>How the physical wheel angle maps onto the cab steering wheel of the truck (ADR 0263).</summary>
    public enum WheelSteerMapping : byte
    {
        /// <summary>The in-game rotation range (270-900 deg) spans the truck's full lock: the device end = road wheels at
        /// their lock. Default (a 900 deg device cannot turn the ~1600 deg lock-to-lock of a heavy truck 1:1).</summary>
        ScaledToLock = 0,
        /// <summary>One device degree = one cab-wheel degree; the soft lock is at the smaller of the rotation range and the
        /// truck's lock, so full road-wheel lock may be out of reach (realistic feel at speed, harder in yards).</summary>
        OneToOne = 1,
    }

    /// <summary>
    /// Pure mapping from a calibrated physical wheel position to the cab steering wheel (ADR 0263). All angles in
    /// degrees, positive = clockwise = right (the physics sign convention). Allocation-free, unit-tested.
    /// </summary>
    public static class WheelSteeringMap
    {
        public const float RangeMinDeg = 270f, RangeMaxDeg = 900f;

        /// <summary>Clamps a player rotation range (lock-to-lock, deg) to 270-900 and to what the device can turn.</summary>
        public static float ClampRange(float rangeDeg, float deviceRangeDeg)
        {
            float dev = deviceRangeDeg > 0f ? deviceRangeDeg : RangeMaxDeg;
            float r = float.IsNaN(rangeDeg) ? dev : rangeDeg;
            return WheelAxisMath.Clamp(Math.Min(r, dev), Math.Min(RangeMinDeg, dev), RangeMaxDeg);
        }

        /// <summary>Physical wheel angle [deg] from the calibrated -1..1 axis and the lock-to-lock range the axis spans.</summary>
        public static float DeviceDeg(float steerNorm, float deviceRangeDeg) => WheelAxisMath.Clamp(steerNorm, -1f, 1f) * 0.5f * deviceRangeDeg;

        /// <summary>Physical wheel angle [deg] at which the soft lock starts (half of the in-game range, or the truck lock 1:1).</summary>
        public static float SoftLockDeg(float rangeDeg, float cabLockDeg, WheelSteerMapping mapping)
        {
            float half = 0.5f * rangeDeg;
            return mapping == WheelSteerMapping.OneToOne && cabLockDeg > 0f ? Math.Min(half, cabLockDeg) : half;
        }

        /// <summary>Cab-wheel degrees per device degree (virtual gearing; also scales the force feedback torque).</summary>
        public static float CabPerDeviceDeg(float rangeDeg, float cabLockDeg, WheelSteerMapping mapping)
        {
            if (mapping == WheelSteerMapping.OneToOne || rangeDeg <= 0f || cabLockDeg <= 0f) return 1f;
            return cabLockDeg / (0.5f * rangeDeg);
        }

        /// <summary>Cab steering-wheel angle [deg] for a device angle, clamped at the soft lock and the truck lock.</summary>
        public static float CabDeg(float deviceDeg, float rangeDeg, float cabLockDeg, WheelSteerMapping mapping)
        {
            float soft = SoftLockDeg(rangeDeg, cabLockDeg, mapping);
            float d = WheelAxisMath.Clamp(deviceDeg, -soft, soft);
            float cab = d * CabPerDeviceDeg(rangeDeg, cabLockDeg, mapping);
            return cabLockDeg > 0f ? WheelAxisMath.Clamp(cab, -cabLockDeg, cabLockDeg) : cab;
        }

        /// <summary>Normalised steering command -1..1 (cab angle / lock) for <see cref="DriverIntent.Steer"/>.</summary>
        public static float Command(float deviceDeg, float rangeDeg, float cabLockDeg, WheelSteerMapping mapping)
        {
            if (cabLockDeg <= 0f) return WheelAxisMath.Clamp(deviceDeg / Math.Max(1f, 0.5f * rangeDeg), -1f, 1f);
            return WheelAxisMath.Clamp(CabDeg(deviceDeg, rangeDeg, cabLockDeg, mapping) / cabLockDeg, -1f, 1f);
        }

        /// <summary>How far past the soft lock the device is [deg] (signed, 0 inside) — drives the force feedback wall.</summary>
        public static float PastSoftLockDeg(float deviceDeg, float rangeDeg, float cabLockDeg, WheelSteerMapping mapping)
        {
            float soft = SoftLockDeg(rangeDeg, cabLockDeg, mapping);
            if (deviceDeg > soft) return deviceDeg - soft;
            if (deviceDeg < -soft) return deviceDeg + soft;
            return 0f;
        }
    }
}
