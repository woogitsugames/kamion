using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// Pure shaping helpers for analog pad axes and digital (keyboard) axis ramps (ADR 0264). No Unity runtime state:
    /// every function is deterministic and allocation-free, unit-tested in EditMode and in the .NET harness.
    /// Sign convention as <see cref="DriverIntent"/>: steer &gt; 0 = right.
    /// </summary>
    public static class PadSteeringMath
    {
        /// <summary>
        /// Dead zone with outer saturation and rescale: |x| &lt;= inner gives 0; |x| &gt;= 1 - outer gives ±1; linear in
        /// between, so there is no jump at either edge. NaN gives 0.
        /// </summary>
        public static float DeadZone(float x, float inner, float outer)
        {
            float a = Mathf.Abs(x);
            if (float.IsNaN(a)) return 0f;
            inner = Mathf.Clamp(inner, 0f, 0.9f);
            float hi = 1f - Mathf.Clamp(outer, 0f, 0.5f);
            if (a <= inner) return 0f;
            if (hi <= inner + 1e-4f) return Mathf.Sign(x);
            return Mathf.Sign(x) * Mathf.Clamp01((a - inner) / (hi - inner));
        }

        /// <summary>
        /// Sensitivity curve |x|^exponent, sign-preserving (exponent 1 = linear, 2 = fine control near centre; clamped
        /// to 1..4). Monotonic, f(0) = 0, f(±1) = ±1.
        /// </summary>
        public static float Expo(float x, float exponent)
        {
            if (float.IsNaN(x)) return 0f;
            x = Mathf.Clamp(x, -1f, 1f);
            float e = float.IsNaN(exponent) ? 1f : Mathf.Clamp(exponent, 1f, 4f);
            return Mathf.Sign(x) * Mathf.Pow(Mathf.Abs(x), e);
        }

        /// <summary>Dead zone then curve (the order a stick or trigger is shaped in).</summary>
        public static float Shape(float raw, float inner, float outer, float exponent) => Expo(DeadZone(raw, inner, outer), exponent);

        /// <summary>
        /// Fraction of full steering lock that a full stick (or a held key) may ask for at a speed: the road-wheel angle
        /// that gives <paramref name="maxLatAccel"/> on a kinematic bicycle (tan δ = L·a / v²), over the maximum
        /// road-wheel angle, never below <paramref name="minFraction"/> (evasive margin) nor above 1. At walking speed
        /// the result is 1 (full lock for manoeuvring).
        /// </summary>
        public static float SpeedAmplitude(float speedMs, float wheelbaseM, float maxLatAccel, float maxRoadWheelDeg, float minFraction)
        {
            float v = Mathf.Abs(speedMs);
            if (float.IsNaN(v) || v < 0.5f || wheelbaseM <= 0f || maxLatAccel <= 0f || maxRoadWheelDeg <= 0f) return 1f;
            float delta = Mathf.Atan(wheelbaseM * maxLatAccel / (v * v));
            return Mathf.Clamp(delta / (maxRoadWheelDeg * Mathf.Deg2Rad), Mathf.Clamp01(minFraction), 1f);
        }

        /// <summary>Piecewise-linear lookup, flat outside the table. xs ascending, same length as ys (else ys[0] or 0).</summary>
        public static float Piecewise(float x, float[] xs, float[] ys)
        {
            if (xs == null || ys == null || xs.Length == 0 || ys.Length != xs.Length) return ys != null && ys.Length > 0 ? ys[0] : 0f;
            if (x <= xs[0]) return ys[0];
            for (int i = 1; i < xs.Length; i++)
                if (x <= xs[i]) return Mathf.Lerp(ys[i - 1], ys[i], (x - xs[i - 1]) / Mathf.Max(1e-5f, xs[i] - xs[i - 1]));
            return ys[ys.Length - 1];
        }

        /// <summary>
        /// Rate-limited follow of a target [fraction of lock per second]. Moving towards centre (or across it) uses the
        /// faster of <paramref name="rate"/> and <paramref name="returnRate"/>, so letting go is never slower than turning in.
        /// </summary>
        public static float RateLimit(float current, float target, float rate, float returnRate, float dt)
        {
            if (float.IsNaN(target)) target = 0f;
            if (dt <= 0f) return current;
            float delta = target - current;
            bool towardCentre = delta * current < 0f;
            float r = Mathf.Max(0f, towardCentre ? Mathf.Max(rate, returnRate) : rate);
            return current + Mathf.Clamp(delta, -r * dt, r * dt);
        }

        // ------------------------------------------------------------------ keyboard (digital) ramps

        /// <summary>Pedal ramp for a key: rises at <paramref name="riseRate"/> while held, falls at <paramref name="fallRate"/> when released [1/s].</summary>
        public static float RampPedal(float current, bool pressed, float riseRate, float fallRate, float dt)
        {
            float target = pressed ? 1f : 0f;
            return Mathf.MoveTowards(current, target, Mathf.Max(0f, pressed ? riseRate : fallRate) * Mathf.Max(0f, dt));
        }

        /// <summary>
        /// Steering ramp for keys: direction -1/0/+1 drives towards ±<paramref name="amplitude"/> at <paramref name="rate"/>;
        /// released (0) returns to centre at <paramref name="returnRate"/>; reversing goes through centre at the faster of
        /// the two. Result clamped to ±1.
        /// </summary>
        public static float RampSteer(float current, int direction, float amplitude, float rate, float returnRate, float dt)
        {
            float target = direction == 0 ? 0f : Mathf.Sign(direction) * Mathf.Clamp01(amplitude);
            return Mathf.Clamp(RateLimit(current, target, rate, returnRate, dt), -1f, 1f);
        }
    }
}
