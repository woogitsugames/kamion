using System;

namespace Game.Vehicle.Physics
{
    public static class MathUtil
    {
        public const double Deg2Rad = Math.PI / 180.0;
        public const double Rad2Deg = 180.0 / Math.PI;
        public const double RpmToRadS = 2.0 * Math.PI / 60.0;
        public const double RadSToRpm = 60.0 / (2.0 * Math.PI);

        public static double Clamp(double v, double lo, double hi) => v < lo ? lo : (v > hi ? hi : v);
        public static double Clamp01(double v) => v < 0 ? 0 : (v > 1 ? 1 : v);
        public static double Lerp(double a, double b, double t) => a + (b - a) * t;

        /// <summary>Moves current toward target by at most maxDelta.</summary>
        public static double MoveTowards(double current, double target, double maxDelta)
        {
            double d = target - current;
            if (Math.Abs(d) <= maxDelta) return target;
            return current + Math.Sign(d) * maxDelta;
        }

        /// <summary>Exact first-order lag step (stable for any dt).</summary>
        public static double FirstOrder(double current, double target, double tau, double dt)
        {
            if (tau <= 1e-9) return target;
            return target + (current - target) * Math.Exp(-dt / tau);
        }

        public static double SmoothStep01(double t)
        {
            t = Clamp01(t);
            return t * t * (3 - 2 * t);
        }

        /// <summary>Piecewise-linear lookup; xs must be strictly increasing. Clamps at the ends.</summary>
        public static double Lut(double[] xs, double[] ys, double x)
        {
            int n = xs.Length;
            if (x <= xs[0]) return ys[0];
            if (x >= xs[n - 1]) return ys[n - 1];
            int lo = 0, hi = n - 1;
            while (hi - lo > 1)
            {
                int mid = (lo + hi) >> 1;
                if (xs[mid] <= x) lo = mid; else hi = mid;
            }
            double t = (x - xs[lo]) / (xs[hi] - xs[lo]);
            return ys[lo] + (ys[hi] - ys[lo]) * t;
        }
    }
}
