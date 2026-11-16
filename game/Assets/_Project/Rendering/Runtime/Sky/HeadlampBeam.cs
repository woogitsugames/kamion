using System;

namespace Game.Rendering
{
    /// <summary>
    /// night-pc-s23: C# twin of KamionHeadlampRelI (KamionLampPools.hlsl) - the dipped beam's relative intensity I / Ipk
    /// for a direction given as slopes (tan) in the cab frame: h to the right, v up. Right-hand traffic. Shape fitted to the
    /// UN R112 class B passing-beam table (Annex 3, test points in degrees relative to the lamp's H-H / V-V with the cut-off
    /// elbow at 0.57 deg down; source: UN Regulation No. 112, mlit.go.jp/jidosha/un/UN_R112.pdf p. 23). In the vehicle the
    /// cut-off sits <see cref="AimSlope"/> below the horizon (WORKING_VALUE; UN R48 6.2.6.1.1 initial-aim range for lamps
    /// above 1 m UNVERIFIED). Ipk (preset projectedHeadlampPeakCd, 20 000 cd) is WORKING_VALUE.
    /// Pure math, no UnityEngine (testable).
    /// </summary>
    public static class HeadlampBeam
    {
        public const float AimSlope = 0.015f, Rise = 0.0274f, HotSpot = 0.02f;
        /// <summary>R112 lamp-test frame: the horizontal cut-off at 0.57 deg below H-H.</summary>
        public static readonly float R112CutSlope = (float)Math.Tan(0.57 * Math.PI / 180.0);

        /// <summary>I / Ipk in the vehicle frame (slopes).</summary>
        public static float RelI(float h, float v)
        {
            float cut = -AimSlope + Math.Min(Math.Max(h, 0f) * 0.267949f, Rise);
            float below = cut - v;
            float hc = h - HotSpot;
            float hs = 0.75f * (float)Math.Exp(-hc * hc * 138.89f) + 0.25f * (float)Math.Exp(-h * h * 6.3776f);
            float edge = SmoothStep(-0.002f, 0.003f, below);
            float core = 0.05f + 0.95f * (float)Math.Exp(-Math.Max(below - 0.008f, 0f) * 25f);
            float stray = 0.012f * Sat(1f + below * 20f) * (0.3f + 0.7f * hs);
            float lower = Sat((v + 0.35f) * 10f);
            return Math.Max(hs * core * edge, stray) * lower * Sat(1f - Math.Abs(h) * 0.9f);
        }

        /// <summary>
        /// Intensity (cd) at an R112 test point given in degrees (up positive, right positive) relative to H-H / V-V of the
        /// lamp on the goniometer, i.e. with the cut-off at 0.57 deg down - converted into the vehicle frame.
        /// </summary>
        public static float R112PointCd(float upDeg, float rightDeg, float peakCd)
        {
            float v = (float)Math.Tan(upDeg * Math.PI / 180.0) + R112CutSlope - AimSlope;
            float h = (float)Math.Tan(rightDeg * Math.PI / 180.0);
            return peakCd * RelI(h, v);
        }

        static float Sat(float x) => x < 0f ? 0f : x > 1f ? 1f : x;
        static float SmoothStep(float a, float b, float x) { float t = Sat((x - a) / (b - a)); return t * t * (3f - 2f * t); }
    }
}
