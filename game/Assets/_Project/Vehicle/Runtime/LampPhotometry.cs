// ADR 0197: lamp numbers without UnityEngine. This file must compile outside Unity (tools/lamp-check links it into a plain
// .NET test project): System only, no UnityEngine / Unity.Mathematics types, C# 9 at most (Unity 6 compiler).
using System;

namespace Game.Vehicle.Runtime
{
    /// <summary>
    /// Pure lamp arithmetic shared by <see cref="TruckLights"/>, the Kamion/Truck Exterior shader (mirrored in HLSL) and the
    /// tests: lamp luminances, light-group ids, the ADR 0178 hue-preserving display limiter and its ADR 0197 reference
    /// level (stop : tail ratio after the limiter, UN R148 4.8.11), linear sRGB -> CIE xy and the UN R48 2.11.1 colour
    /// areas, and the number-plate illumination of ADR 0181 against UN R148 5.11.3.
    /// Sources: Dz.U. UE L 347 of 30.9.2021 (R48 series 07 s. 1, R148 s. 123), quoted in research/mistral/p16-truck-lamps
    /// manifest rows P16-035, P16-090..094, P16-110..112 (review docs/reports/REVIEW-2026-11-14-s20-mistral-m59.md).
    /// </summary>
    public static class LampPhotometry
    {
        // ------------------------------------------------------------------ light groups (manifest shader_contract.light_groups)
        public const int None = 0, Drl = 1, LowBeam = 2, HighBeam = 3, IndL = 4, IndR = 5, TailBrake = 6, Reverse = 7,
            MarkerFront = 8, MarkerSide = 9, MarkerRear = 10, Fog = 11, Work = 12, Plate = 13, FogRear = 14, Reflex = 15,
            // ADR 0197: separate chambers of the trailer combination lamp (trailer_export.light_group "_tail_" / "_stop_").
            Tail = 16, Stop = 17;
        /// <summary>Width of the 1-row lamp-state texture (texel x = group id). Must match TruckExterior.shader KAMION_LAMP_TEXELS.</summary>
        public const int StateTexels = 32;

        // ------------------------------------------------------------------ lamp luminances, cd/m^2
        // WORKING_VALUEs retained from ADR 0087 (display calibrations, not measured lamp photometry). The stop : tail
        // ratio 20 000 / 1 300 = 15.4 : 1 is the R148 4.8.11 quantity (>= 5 : 1) once the limiter keeps it (ADR 0197).
        public const float DrlNits = 1.6e5f, LowNits = 5e4f, HighNits = 8e4f, TailNits = 1.3e3f, BrakeNits = 2.0e4f,
            ReverseNits = 3e4f, MarkerNits = 2e3f, IndicatorNits = 2.5e4f, RearFogNits = 1.5e4f;
        /// <summary>UN R148 4.8.11: (stop + tail) : tail at least 5 : 1 inside +-5 V / +-10 H (P16-035, SOURCED).</summary>
        public const float MinStopToTailRatio = 5f;

        // ------------------------------------------------------------------ colours (linear sRGB, D65)
        // Red (1, 0, 0): CIE x 0.640, y 0.330. The R48 2.11.1.4 red area (y <= 0.335, y >= 0.980 - x) lies outside the sRGB
        // gamut (max x + y in sRGB = 0.970 at the red primary), so the primary is the nearest reachable point.
        public static readonly float[] RedLinear = { 1f, 0f, 0f };
        // Amber (1, 0.22, 0): x 0.542, y 0.408. ADR 0197: the R48 2.11.1.3 amber area also lies outside sRGB (white limit
        // y >= 0.790 - 0.670 x is above the sRGB red-green edge for every x of the area). (1, g, 0) is the gamut edge facing
        // it; g = 0.22 meets the green (y <= x - 0.120) and red (y >= 0.390) limits and is 0.0159 xy from the area (the
        // nearest edge point, g = 0.24, is 0.0153 but only 0.0017 inside the green limit). Was (1, 0.28, 0): y 0.422, beyond
        // the green limit (review M59 G3).
        public static readonly float[] AmberLinear = { 1f, 0.22f, 0f };
        public static readonly float[] WhiteLinear = { 1f, 0.97f, 0.92f };

        // ------------------------------------------------------------------ ADR 0178 limiter + ADR 0197 reference
        /// <summary>Material defaults of TruckExterior.shader _LampHueKnee / _LampHueCeiling (WORKING_VALUE, ADR 0178).</summary>
        public const float HueKnee = 0.4f, HueCeiling = 0.8f;

        /// <summary>ADR 0178 shoulder of the max channel: identity to the knee, then knee + o / (1 + o / (ceiling - knee)).</summary>
        public static double HueLimit(double m, double knee = HueKnee, double ceiling = HueCeiling)
        {
            if (ceiling <= 0.0 || ceiling <= knee) return m;
            double over = Math.Max(m - knee, 0.0);
            return Math.Min(m, knee) + over / (1.0 + over / (ceiling - knee));
        }

        /// <summary>
        /// Common RGB scale of the limiter. ADR 0197: the scale is taken at r = max(reference, m) instead of m, so every lamp
        /// state of a group shares the gain of its brightest state and keeps its linear ratio to it after the limit.
        /// reference = 0 reproduces ADR 0178 (per-pixel). The output max channel is still below the ceiling (scale(r) * m
        /// &lt;= scale(r) * r = HueLimit(r)). Mirrors TruckExterior.shader TruckLampHueLimitRef.
        /// </summary>
        public static double HueLimitScale(double m, double reference, double knee = HueKnee, double ceiling = HueCeiling)
        {
            if (ceiling <= 0.0 || ceiling <= knee) return 1.0;
            double r = Math.Max(reference, m);
            return HueLimit(r, knee, ceiling) / Math.Max(r, 1e-6);
        }

        /// <summary>
        /// Limiter reference of a group in cd/m^2, written to the alpha of its state texel (0 = per-pixel, ADR 0178).
        /// Rear red signal lamps share the stop level: tail / stop / top rear marker keep their R148 intensity ratios at dusk
        /// instead of all reaching the ceiling (ADR 0181 r2 P2-5: tail 201 vs stop 202 sRGB). Other groups unchanged.
        /// </summary>
        public static float LimiterReferenceNits(int group) =>
            group == TailBrake || group == Tail || group == Stop || group == MarkerRear ? BrakeNits : 0f;

        /// <summary>Displayed max channel of a red lamp (max channel = nits) of <paramref name="group"/>: the shader path
        /// radiance * hdr -> limiter -> * disp (ADR 0181 lens structure factors, both 0..1).</summary>
        public static double DisplayedMax(double nits, int group, double exposure, double hdr = 1.0, double disp = 1.0,
            bool useReference = true)
        {
            double m = nits * exposure * hdr;
            double reference = useReference ? LimiterReferenceNits(group) * exposure * hdr : 0.0;
            return m * HueLimitScale(m, reference) * disp;
        }

        /// <summary>Displayed (stop + tail) : tail of a combined chamber (TAIL_BRAKE) after the limiter.</summary>
        public static double StopToTailRatioAfterLimiter(double exposure, double hdr = 1.0, bool useReference = true)
        {
            double tail = DisplayedMax(TailNits, TailBrake, exposure, hdr, 1.0, useReference);
            double stop = DisplayedMax(Math.Max(TailNits, BrakeNits), TailBrake, exposure, hdr, 1.0, useReference);
            return stop / Math.Max(tail, 1e-12);
        }

        // ------------------------------------------------------------------ colourimetry
        /// <summary>Linear sRGB (D65) -> CIE 1931 xy (IEC 61966-2-1 matrix).</summary>
        public static void Chromaticity(double r, double g, double b, out double x, out double y)
        {
            double X = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b;
            double Y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b;
            double Z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b;
            double s = X + Y + Z;
            if (s <= 0.0) { x = y = 0.0; return; }
            x = X / s; y = Y / s;
        }

        /// <summary>R48 2.11.1.3 amber (P16-111): corners A1-A4; A2-A3 runs along the spectral locus.</summary>
        public static readonly double[] R48AmberCorners = { 0.545, 0.425, 0.560, 0.440, 0.609, 0.390, 0.597, 0.390 };
        /// <summary>R48 2.11.1.4 red (P16-112): corners R1-R4; R2-R3 runs along the spectral locus.</summary>
        public static readonly double[] R48RedCorners = { 0.645, 0.335, 0.665, 0.335, 0.735, 0.265, 0.721, 0.259 };

        public static bool AmberGreenLimit(double x, double y) => y <= x - 0.120;          // towards green
        public static bool AmberRedLimit(double x, double y) => y >= 0.390;                // towards red
        public static bool AmberWhiteLimit(double x, double y) => y >= 0.790 - 0.670 * x;  // towards white
        /// <summary>Inside the R48 amber area (the fourth limit, the spectral locus, holds for every real colour).</summary>
        public static bool InR48Amber(double x, double y) => AmberGreenLimit(x, y) && AmberRedLimit(x, y) && AmberWhiteLimit(x, y);

        public static bool RedYellowLimit(double x, double y) => y <= 0.335;               // towards yellow
        public static bool RedPurpleLimit(double x, double y) => y >= 0.980 - x;           // towards purple
        public static bool InR48Red(double x, double y) => RedYellowLimit(x, y) && RedPurpleLimit(x, y);

        /// <summary>Euclidean xy distance from a point to a convex polygon given as x0,y0,x1,y1,... (0 inside).</summary>
        public static double DistanceToPolygon(double x, double y, double[] poly)
        {
            int n = poly.Length / 2;
            bool inside = true;
            double best = double.MaxValue;
            double sign = 0.0;
            for (int i = 0; i < n; i++)
            {
                double ax = poly[2 * i], ay = poly[2 * i + 1];
                double bx = poly[2 * ((i + 1) % n)], by = poly[2 * ((i + 1) % n) + 1];
                double ex = bx - ax, ey = by - ay;
                double cross = ex * (y - ay) - ey * (x - ax);
                if (cross != 0.0)
                {
                    if (sign == 0.0) sign = Math.Sign(cross);
                    else if (Math.Sign(cross) != sign) inside = false;
                }
                double t = Math.Max(0.0, Math.Min(1.0, ((x - ax) * ex + (y - ay) * ey) / (ex * ex + ey * ey)));
                double dx = x - (ax + t * ex), dy = y - (ay + t * ey);
                best = Math.Min(best, Math.Sqrt(dx * dx + dy * dy));
            }
            return inside ? 0.0 : best;
        }

        /// <summary>Nearest point of the sRGB red-green gamut edge (1, g, 0) to a polygon, g in [0, 1] (step 1e-4).</summary>
        public static double NearestRedGreenEdgeG(double[] poly, out double distance)
        {
            double bestG = 0.0; distance = double.MaxValue;
            for (int i = 0; i <= 10000; i++)
            {
                double g = i * 1e-4;
                Chromaticity(1.0, g, 0.0, out double x, out double y);
                double d = DistanceToPolygon(x, y, poly);
                if (d < distance) { distance = d; bestG = g; }
            }
            return bestG;
        }

        // ------------------------------------------------------------------ number plate (ADR 0181 / R148 5.11)
        /// <summary>Plate luminance at reflectance 1 / plate-lamp luminance (material _PlateIllum, WORKING_VALUE). ADR 0197:
        /// 0.005 -> 0.006 so the minimum over every possible R148 measuring circle is >= 2.5 cd/m^2 with margin.</summary>
        public const float PlateIllum = 0.006f;
        /// <summary>Plate lamp luminance: TruckLights writes MarkerNits (white) to group 13.</summary>
        public const float PlateLampNits = MarkerNits;
        /// <summary>R148 5.11.3 (a): minimum B in every measuring point, categories 1a/1b/1c/2a/2b (P16-090, SOURCED).</summary>
        public const float PlateMinLuminance = 2.5f;
        /// <summary>R148 5.11.2: a measuring point is a 25 mm circle (P16-094, SOURCED) -> centres >= 12.5 mm inside the plate.</summary>
        public const float PlateMeasuringCircleMm = 25f;
        // KamionLampLens.hlsl KamionLensEval, style PLATE: lamp strip over the top edge, 0.22 W either side of the centre,
        // 15 mm above it; falloff 1 / (1 + d^2 / 100^2), d in mm. WORKING_VALUEs of ADR 0181.
        public const double PlateStripHalfWidthFraction = 0.22, PlateLampAboveTopMm = 15.0, PlateFalloffMm = 100.0;

        /// <summary>Falloff 0..1 at (xMm from the plate centre, dyMm down from the top edge) of a plate wMm wide.</summary>
        public static double PlateFalloff(double xMm, double dyMm, double wMm)
        {
            double x = Math.Max(Math.Abs(xMm) - PlateStripHalfWidthFraction * wMm, 0.0);
            double y = dyMm + PlateLampAboveTopMm;
            return 1.0 / (1.0 + (x * x + y * y) / (PlateFalloffMm * PlateFalloffMm));
        }

        /// <summary>Plate luminance in cd/m^2 at reflectance 1.0 (R148 5.11.2 corrects to diffuse reflectance 1).</summary>
        public static double PlateLuminance(double xMm, double dyMm, double wMm, double plateIllum = PlateIllum) =>
            PlateLampNits * plateIllum * PlateFalloff(xMm, dyMm, wMm);

        /// <summary>
        /// Minimum luminance over every possible measuring circle (centres inset by 12.5 mm, mean over the 25 mm disc) of a
        /// wMm x hMm plate. Conservative superset of the R148 Annex 3 points: whatever their positions, they are inside.
        /// </summary>
        public static double PlateMinCircleLuminance(double wMm, double hMm, double plateIllum = PlateIllum, double stepMm = 2.0)
        {
            double r = 0.5 * PlateMeasuringCircleMm, best = double.MaxValue;
            for (double cy = r; cy <= hMm - r + 1e-9; cy += stepMm)
                for (double cx = -0.5 * wMm + r; cx <= 0.5 * wMm - r + 1e-9; cx += stepMm)
                    best = Math.Min(best, DiscMean(cx, cy, wMm, plateIllum));
            // the far corners are the minimum of a monotone falloff: evaluate them exactly too
            best = Math.Min(best, DiscMean(0.5 * wMm - r, hMm - r, wMm, plateIllum));
            return best;
        }

        static double DiscMean(double cx, double cy, double wMm, double plateIllum)
        {
            const int n = 9;
            double r = 0.5 * PlateMeasuringCircleMm, sum = 0.0; int count = 0;
            for (int j = 0; j < n; j++)
                for (int i = 0; i < n; i++)
                {
                    double u = (i + 0.5) / n * 2.0 - 1.0, v = (j + 0.5) / n * 2.0 - 1.0;
                    if (u * u + v * v > 1.0) continue;
                    sum += PlateLuminance(cx + u * r, cy + v * r, wMm, plateIllum); count++;
                }
            return sum / count;
        }

        /// <summary>Largest luminance gradient on the plate in cd/m^2 per cm (R148 5.11.3: &lt;= 2 x B0 / cm).</summary>
        public static double PlateMaxGradientPerCm(double wMm, double hMm, double plateIllum = PlateIllum, double stepMm = 1.0)
        {
            double best = 0.0, h = 0.5;
            for (double y = 0.0; y <= hMm; y += stepMm)
                for (double x = -0.5 * wMm; x <= 0.5 * wMm; x += stepMm)
                {
                    double gx = (PlateLuminance(x + h, y, wMm, plateIllum) - PlateLuminance(x - h, y, wMm, plateIllum)) / (2 * h);
                    double gy = (PlateLuminance(x, y + h, wMm, plateIllum) - PlateLuminance(x, y - h, wMm, plateIllum)) / (2 * h);
                    best = Math.Max(best, Math.Sqrt(gx * gx + gy * gy) * 10.0);
                }
            return best;
        }

        // ------------------------------------------------------------------ display helpers
        /// <summary>Linear -> sRGB 8-bit (IEC 61966-2-1), for reporting expected pixel values.</summary>
        public static int LinearToSrgb8(double v)
        {
            v = Math.Max(0.0, Math.Min(1.0, v));
            double s = v <= 0.0031308 ? 12.92 * v : 1.055 * Math.Pow(v, 1.0 / 2.4) - 0.055;
            return (int)Math.Round(s * 255.0);
        }
    }
}
