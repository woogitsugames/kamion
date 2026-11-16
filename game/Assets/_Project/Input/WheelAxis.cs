using System;

namespace Game.Controls
{
    /// <summary>
    /// Calibration of one analogue axis of a PC wheel or pedal set (ADR 0263). Raw values are what the device control
    /// reports (Unity Input System normalises HID axes, but the span and direction differ between devices and driver
    /// modes, so nothing is assumed: min/max/centre come from the profile or from the calibration wizard).
    /// Plain data (JsonUtility-compatible), no Unity dependency.
    /// </summary>
    [Serializable]
    public sealed class AxisCalibration
    {
        /// <summary>Raw value at one end of travel (pedal released / wheel full left before <see cref="invert"/>).</summary>
        public float rawMin = 0f;
        /// <summary>Raw value at the other end of travel (pedal fully pressed / wheel full right before <see cref="invert"/>).</summary>
        public float rawMax = 1f;
        /// <summary>Raw value with the wheel straight ahead (steering only; pedals ignore it).</summary>
        public float rawCentre = 0.5f;
        /// <summary>Reverse the direction (pedals that report 1 when released, wheels whose driver reports left as positive).</summary>
        public bool invert;
        /// <summary>Dead zone at the rest end (pedal) or around the centre (wheel), fraction of travel 0..0.5.</summary>
        public float deadZoneLow = 0f;
        /// <summary>Saturation zone at the far end (pedal reaches 1 before the mechanical stop), fraction 0..0.5.</summary>
        public float deadZoneHigh = 0f;

        public AxisCalibration Clone() => (AxisCalibration)MemberwiseClone();

        public static AxisCalibration Pedal(float rawReleased, float rawPressed, float deadLow = 0f, float deadHigh = 0f)
            => new AxisCalibration { rawMin = rawReleased, rawMax = rawPressed, rawCentre = rawReleased, deadZoneLow = deadLow, deadZoneHigh = deadHigh };

        public static AxisCalibration Steering(float rawLeft, float rawCentre, float rawRight, float dead = 0f)
            => new AxisCalibration { rawMin = rawLeft, rawMax = rawRight, rawCentre = rawCentre, deadZoneLow = dead };

        /// <summary>Clamps every field to a usable range (hand-edited or corrupt saves).</summary>
        public void Sanitize()
        {
            if (float.IsNaN(rawMin) || float.IsInfinity(rawMin)) rawMin = 0f;
            if (float.IsNaN(rawMax) || float.IsInfinity(rawMax)) rawMax = 1f;
            if (float.IsNaN(rawCentre) || float.IsInfinity(rawCentre)) rawCentre = 0.5f * (rawMin + rawMax);
            if (Math.Abs(rawMax - rawMin) < 1e-4f) rawMax = rawMin + 1f;
            deadZoneLow = WheelAxisMath.Clamp(float.IsNaN(deadZoneLow) ? 0f : deadZoneLow, 0f, 0.5f);
            deadZoneHigh = WheelAxisMath.Clamp(float.IsNaN(deadZoneHigh) ? 0f : deadZoneHigh, 0f, 0.5f);
        }
    }

    /// <summary>Pure axis shaping for PC wheels and pedals (unit-tested without hardware). Allocation-free.</summary>
    public static class WheelAxisMath
    {
        public static float Clamp(float x, float lo, float hi) => x < lo ? lo : (x > hi ? hi : x);
        public static float Clamp01(float x) => x < 0f ? 0f : (x > 1f ? 1f : x);

        /// <summary>Raw position as a 0..1 fraction of the calibrated travel (rawMin → 0, rawMax → 1; inverted when asked).</summary>
        public static float Travel(float raw, AxisCalibration c)
        {
            float span = c.rawMax - c.rawMin;
            if (Math.Abs(span) < 1e-6f) return 0f;
            float t = Clamp01((raw - c.rawMin) / span);
            return c.invert ? 1f - t : t;
        }

        /// <summary>Applies a low (rest) and high (saturation) dead zone to a 0..1 value with rescale (no jumps at the edges).</summary>
        public static float PedalDeadZones(float t, float deadLow, float deadHigh)
        {
            float lo = Clamp(deadLow, 0f, 0.5f), hi = Clamp(deadHigh, 0f, 0.5f);
            float usable = 1f - lo - hi;
            if (usable <= 1e-4f) return t > 0.5f ? 1f : 0f;
            return Clamp01((t - lo) / usable);
        }

        /// <summary>Pedal 0 (released) .. 1 (fully pressed) from a raw reading.</summary>
        public static float Pedal(float raw, AxisCalibration c) => PedalDeadZones(Travel(raw, c), c.deadZoneLow, c.deadZoneHigh);

        /// <summary>
        /// Wheel -1 (full left) .. +1 (full right) from a raw reading. Piecewise around <see cref="AxisCalibration.rawCentre"/>
        /// so an off-centre neutral (worn pot, uncalibrated base) still gives exactly 0 straight ahead and ±1 at the stops.
        /// The centre dead zone (fraction of half travel) is rescaled (no step at its edge).
        /// </summary>
        public static float Steer(float raw, AxisCalibration c)
        {
            float lo = c.rawMin, hi = c.rawMax, ce = c.rawCentre;
            bool ascending = hi >= lo;
            // Keep the centre strictly inside the travel.
            float mn = ascending ? lo : hi, mx = ascending ? hi : lo;
            if (ce <= mn || ce >= mx) ce = 0.5f * (lo + hi);
            float s;
            if (ascending ? raw >= ce : raw <= ce) s = (raw - ce) / (hi - ce);
            else s = -(raw - ce) / (lo - ce);
            s = Clamp(s, -1f, 1f);
            if (c.invert) s = -s;
            float dz = Clamp(c.deadZoneLow, 0f, 0.5f);
            float a = Math.Abs(s);
            if (a <= dz) return 0f;
            return Math.Sign(s) * Clamp01((a - dz) / (1f - dz));
        }

        /// <summary>
        /// Combined pedal axis (one axis for throttle and brake, e.g. a wheel in a legacy driver mode): the calibrated
        /// -1..1 value from <see cref="Steer"/> with the centre at "both released"; positive = throttle, negative = brake
        /// (or the reverse when the profile sets <see cref="AxisCalibration.invert"/>). Both pedals pressed are not
        /// distinguishable on such an axis — documented limitation (docs/compat/wheels.md).
        /// </summary>
        public static void SplitCombined(float raw, AxisCalibration c, out float throttle, out float brake)
        {
            float s = Steer(raw, c);
            throttle = s > 0f ? s : 0f;
            brake = s < 0f ? -s : 0f;
        }
    }

    /// <summary>
    /// Captures the calibration of an axis while the player moves it end to end (calibration wizard; allocation-free).
    /// </summary>
    public struct AxisCalibrator
    {
        public float Min, Max, Centre;
        public bool HasSample;

        public void Reset() { HasSample = false; Min = Max = Centre = 0f; }

        public void Observe(float raw)
        {
            if (float.IsNaN(raw)) return;
            if (!HasSample) { Min = Max = raw; HasSample = true; return; }
            if (raw < Min) Min = raw;
            if (raw > Max) Max = raw;
        }

        /// <summary>Call with the wheel held straight ahead.</summary>
        public void MarkCentre(float raw) => Centre = raw;

        /// <summary>Enough travel observed to trust the range (fraction of the expected span).</summary>
        public bool Covers(float expectedSpan, float fraction = 0.8f) => HasSample && (Max - Min) >= Math.Abs(expectedSpan) * fraction;

        /// <summary>Pedal calibration from the observed travel. <paramref name="releasedRaw"/> = reading with the foot off.</summary>
        public AxisCalibration ToPedal(float releasedRaw, float deadLow, float deadHigh)
        {
            bool releasedAtMax = Math.Abs(releasedRaw - Max) < Math.Abs(releasedRaw - Min);
            return releasedAtMax
                ? AxisCalibration.Pedal(Max, Min, deadLow, deadHigh)
                : AxisCalibration.Pedal(Min, Max, deadLow, deadHigh);
        }

        public AxisCalibration ToSteering(float dead) => AxisCalibration.Steering(Min, Centre, Max, dead);
    }

    /// <summary>
    /// Uncalibrated pedal fallback (ADR 0263): the first reading is taken as "released" (feet off when the device is
    /// found), the travel is the larger of the farthest reading seen and <see cref="ExpectedSpan"/> (set it to the
    /// smallest plausible span, so a light touch never reads as a full press). Works for normal and inverted axes
    /// without knowing the direction; the calibration wizard replaces it with a stored <see cref="AxisCalibration"/>.
    /// Allocation-free.
    /// </summary>
    public struct AutoSteer
    {
        public float Centre, FarthestLeft, FarthestRight, ExpectedSpan;
        public bool HasCentre;

        /// <param name="expectedSpan">Smallest plausible raw span of the full lock-to-lock travel (half of it per side).</param>
        public static AutoSteer Create(float expectedSpan) => new AutoSteer { ExpectedSpan = expectedSpan > 1e-3f ? expectedSpan : 1f };

        /// <summary>-1..1: the first reading is the centre (wheel bases self-centre at power-on); each side scales on the
        /// larger of its farthest reading and half the expected span. <paramref name="invert"/> flips the direction.</summary>
        public float Value(float raw, bool invert, float deadZone)
        {
            if (float.IsNaN(raw)) return 0f;
            if (!HasCentre) { Centre = raw; HasCentre = true; return 0f; }
            float d = raw - Centre;
            if (d > FarthestRight) FarthestRight = d;
            if (-d > FarthestLeft) FarthestLeft = -d;
            float half = 0.5f * ExpectedSpan;
            float s = d >= 0f ? d / Math.Max(FarthestRight, half) : d / Math.Max(FarthestLeft, half);
            s = WheelAxisMath.Clamp(s, -1f, 1f);
            if (invert) s = -s;
            float dz = WheelAxisMath.Clamp(deadZone, 0f, 0.5f);
            float a = Math.Abs(s);
            if (a <= dz) return 0f;
            return Math.Sign(s) * WheelAxisMath.Clamp01((a - dz) / (1f - dz));
        }
    }

    /// <summary>Uncalibrated pedal fallback (see <see cref="AutoSteer"/> for the wheel).</summary>
    public struct AutoPedal
    {
        public float Released, FarthestDelta, ExpectedSpan;
        public bool HasRest;

        public static AutoPedal Create(float expectedSpan) => new AutoPedal { ExpectedSpan = expectedSpan > 1e-3f ? expectedSpan : 1f };

        public float Value(float raw, float deadLow, float deadHigh)
        {
            if (float.IsNaN(raw)) return 0f;
            if (!HasRest) { Released = raw; HasRest = true; return 0f; }
            float d = Math.Abs(raw - Released);
            if (d > FarthestDelta) FarthestDelta = d;
            float span = Math.Max(FarthestDelta, ExpectedSpan);
            return WheelAxisMath.PedalDeadZones(WheelAxisMath.Clamp01(d / span), deadLow, deadHigh);
        }
    }
}
