// ADR 0197: plain .NET (xunit) checks of game/Assets/_Project/Vehicle/Runtime/LampPhotometry.cs - runnable without Unity:
//   dotnet test tools/lamp-check
// The Unity EditMode twin is game/Assets/_Project/Tests/EditMode/LampRegulationTests.cs (+ GPU readback of the shader).
using System;
using System.IO;
using System.Text.RegularExpressions;
using Game.Vehicle.Runtime;
using Xunit;
using Xunit.Abstractions;
using P = Game.Vehicle.Runtime.LampPhotometry;

namespace LampCheck
{
    public class LampPhotometryTests
    {
        readonly ITestOutputHelper m_Out;
        public LampPhotometryTests(ITestOutputHelper output) { m_Out = output; }

        static string Repo
        {
            get
            {
                var d = new DirectoryInfo(AppContext.BaseDirectory);
                while (d != null && !Directory.Exists(Path.Combine(d.FullName, "game", "Assets"))) d = d.Parent;
                Assert.NotNull(d);
                return d.FullName;
            }
        }
        static string Read(string rel) => File.ReadAllText(Path.Combine(Repo, rel));

        // Exposure grid: 1e-7 (bright day: brake 0.002 exposed) .. 1 (far beyond any night preset), 8 per decade.
        public static TheoryData<double> Exposures()
        {
            var d = new TheoryData<double>();
            for (int i = 0; i <= 56; i++) d.Add(Math.Pow(10.0, -7.0 + i / 8.0));
            return d;
        }

        // ------------------------------------------------------------------ 1. stop : tail after the limiter (R148 4.8.11)
        [Theory, MemberData(nameof(Exposures))]
        public void CombinedChamber_StopToTail_AtLeastFiveToOne_AfterLimiter(double exposure)
        {
            foreach (double hdr in new[] { 1.0, 0.05 })   // ADR 0181: emitter (1) and the space between emitters (~5 %)
            {
                double ratio = P.StopToTailRatioAfterLimiter(exposure, hdr);
                Assert.True(ratio >= P.MinStopToTailRatio, $"E {exposure:E2} hdr {hdr}: stop/tail {ratio:F2} < 5");
                Assert.Equal(P.BrakeNits / P.TailNits, ratio, 6);   // linear: the nits ratio survives the limiter exactly
            }
        }

        [Fact]
        public void HueLimitScale_IsIdentityBelowKnee_EvenForTinyRadiance()
        {
            // Review O1 (2026-11-15): r < 1e-6 used to return r / 1e-6 instead of 1.
            foreach (double m in new[] { 0.0, 1e-9, 1e-7, 1e-6, 0.5 * P.HueKnee, P.HueKnee })
                Assert.Equal(1.0, P.HueLimitScale(m, 0.0), 12);
        }

        [Fact]
        public void LegacyPerPixelLimiter_CollapsesStopToTail_AtDusk()
        {
            // ADR 0181 r2 P2-5 measured tail 201 vs stop 202 (sRGB). The per-pixel ADR 0178 limiter: both at the ceiling.
            double legacy = P.StopToTailRatioAfterLimiter(1e-2, 1.0, useReference: false);
            m_Out.WriteLine($"legacy ratio at E 1e-2: {legacy:F3}");
            Assert.True(legacy < 1.1, "legacy limiter should reproduce the measured ~1:1");
        }

        [Theory, MemberData(nameof(Exposures))]
        public void TrailerSeparateChambers_StopToTail_AtLeastFiveToOne(double exposure)
        {
            double tail = P.DisplayedMax(P.TailNits, P.Tail, exposure);
            double stop = P.DisplayedMax(P.BrakeNits, P.Stop, exposure);
            Assert.True(stop / tail >= P.MinStopToTailRatio, $"E {exposure:E2}: {stop / tail:F2}");
        }

        [Theory, MemberData(nameof(Exposures))]
        public void Limiter_KeepsEveryLampUnderCeiling_AndIdentityBelowKnee(double exposure)
        {
            float[] nits = { P.TailNits, P.BrakeNits, P.MarkerNits, P.IndicatorNits, P.RearFogNits, P.ReverseNits };
            for (int group = 2; group < P.StateTexels; group++)
                foreach (float n in nits)
                {
                    if (P.LimiterReferenceNits(group) > 0f && n > P.LimiterReferenceNits(group)) continue;   // not a state of the group
                    double m = n * exposure, outMax = P.DisplayedMax(n, group, exposure);
                    Assert.True(outMax <= P.HueCeiling + 1e-9, $"group {group} {n} nits E {exposure:E2}: {outMax}");
                    double reference = Math.Max(P.LimiterReferenceNits(group) * exposure, m);
                    if (reference <= P.HueKnee) Assert.Equal(m, outMax, 9);   // day look unchanged below the knee
                }
        }

        [Fact]
        public void DuskNumbers_ForTheAdr()
        {
            foreach (double e in new[] { 1e-4, 1e-3, 2e-3, 1e-2, 5e-2 })
            {
                double tail = P.DisplayedMax(P.TailNits, P.TailBrake, e), stop = P.DisplayedMax(P.BrakeNits, P.TailBrake, e);
                double marker = P.DisplayedMax(P.MarkerNits, P.MarkerRear, e);
                m_Out.WriteLine($"E {e:E1}: tail {tail:F4} ({P.LinearToSrgb8(tail)}), stop {stop:F4} ({P.LinearToSrgb8(stop)}), " +
                                $"rear marker {marker:F4} ({P.LinearToSrgb8(marker)}), ratio {stop / tail:F2}; legacy tail " +
                                $"{P.DisplayedMax(P.TailNits, P.TailBrake, e, 1, 1, false):F3}");
            }
        }

        // ------------------------------------------------------------------ 2. colours vs R48 2.11.1
        [Fact]
        public void CitedCorners_LieOnTheirCitedLimitLines()
        {
            var a = P.R48AmberCorners;   // A1 green & white, A2 green, A3 red, A4 red & white
            Assert.Equal(a[0] - 0.120, a[1], 3); Assert.Equal(0.790 - 0.670 * a[0], a[1], 3);
            Assert.Equal(a[2] - 0.120, a[3], 3);
            Assert.Equal(0.390, a[5], 3); Assert.Equal(0.390, a[7], 3); Assert.Equal(0.790 - 0.670 * a[6], a[7], 3);
            var r = P.R48RedCorners;     // R1 yellow & purple, R2 yellow, R4 purple
            Assert.Equal(0.335, r[1], 3); Assert.Equal(0.980 - r[0], r[1], 3); Assert.Equal(0.335, r[3], 3);
            Assert.Equal(0.980 - r[6], r[7], 3);
        }

        [Fact]
        public void Amber_MeetsGreenAndRedLimits_AndIsNearlyTheNearestSrgbPointToTheR48Area()
        {
            var c = P.AmberLinear;
            P.Chromaticity(c[0], c[1], c[2], out double x, out double y);
            double d = P.DistanceToPolygon(x, y, P.R48AmberCorners);
            double gBest = P.NearestRedGreenEdgeG(P.R48AmberCorners, out double dBest);
            m_Out.WriteLine($"amber ({c[0]}, {c[1]}, {c[2]}): x {x:F4} y {y:F4}; green margin {(x - 0.120 - y):F4}, red margin " +
                            $"{(y - 0.390):F4}, white limit at x: {0.790 - 0.670 * x:F4}; distance to area {d:F4}; nearest edge g {gBest:F4} at {dBest:F4}");
            Assert.True(P.AmberGreenLimit(x, y), "towards green: y <= x - 0.120");
            Assert.True(P.AmberRedLimit(x, y), "towards red: y >= 0.390");
            Assert.True(d <= dBest + 0.001, $"amber {d:F4} xy from the R48 area, the best sRGB point is {dBest:F4}");
            Assert.True(d < 0.016);
        }

        [Fact]
        public void OldAmber_028_IsBeyondTheGreenLimit()
        {
            P.Chromaticity(1, 0.28, 0, out double x, out double y);
            Assert.False(P.AmberGreenLimit(x, y));
            P.Chromaticity(1, 0.25, 0, out x, out y);   // r1 of ADR 0178
            Assert.False(P.AmberGreenLimit(x, y));
        }

        [Fact]
        public void R48AmberAndRedAreas_LieOutsideTheSrgbGamut()
        {
            double maxSum = 0;
            for (int ri = 0; ri <= 40; ri++)
                for (int gi = 0; gi <= 40; gi++)
                    for (int bi = 0; bi <= 40; bi++)
                    {
                        if (ri + gi + bi == 0) continue;
                        P.Chromaticity(ri / 40.0, gi / 40.0, bi / 40.0, out double x, out double y);
                        Assert.False(P.InR48Amber(x, y), $"sRGB ({ri},{gi},{bi})/40 inside R48 amber");
                        Assert.False(P.InR48Red(x, y), $"sRGB ({ri},{gi},{bi})/40 inside R48 red");
                        maxSum = Math.Max(maxSum, x + y);
                    }
            for (int i = 0; i <= 10000; i++)
            {
                P.Chromaticity(1, i * 1e-4, 0, out double x, out double y);
                Assert.False(P.InR48Amber(x, y), $"(1, {i * 1e-4}, 0) inside R48 amber");
            }
            Assert.True(maxSum < 0.980, $"max x + y in sRGB {maxSum:F4}");
        }

        [Fact]
        public void Red_IsThePrimary_YellowLimitMet_AndMaximalTowardsPurple()
        {
            var c = P.RedLinear;
            P.Chromaticity(c[0], c[1], c[2], out double x, out double y);
            Assert.Equal(0.640, x, 3); Assert.Equal(0.330, y, 3);
            Assert.True(P.RedYellowLimit(x, y));
            Assert.Equal(0.970, x + y, 3);   // 0.010 short of the purple limit; nothing in sRGB gets closer
            for (int gi = 0; gi <= 20; gi++)
                for (int bi = 0; bi <= 20; bi++)
                {
                    P.Chromaticity(1, gi / 20.0, bi / 20.0, out double xx, out double yy);
                    Assert.True(xx + yy <= x + y + 1e-9);
                }
        }

        // ------------------------------------------------------------------ 3. number plate (R148 5.11.3)
        [Theory]
        [InlineData(520, 114)]   // PL plate in the game (ADR 0181 lens frame 520 x 114 mm)
        [InlineData(520, 120)]   // R148 category 1b
        public void Plate_EveryMeasuringCircle_AtLeast2_5cdm2(double w, double h)
        {
            double min = P.PlateMinCircleLuminance(w, h);
            double top = P.PlateLuminance(0, 0, w);
            m_Out.WriteLine($"{w}x{h}: min circle {min:F2} cd/m2, top centre {top:F2}, old 0.005 min {P.PlateMinCircleLuminance(w, h, 0.005):F2}");
            Assert.True(min >= P.PlateMinLuminance, $"{w}x{h}: {min:F2} cd/m2 < 2.5");
        }

        [Fact]
        public void Plate_Old0005_FailsTheConservativeCheck()
        {
            Assert.True(P.PlateMinCircleLuminance(520, 114, 0.005) < P.PlateMinLuminance);
        }

        [Theory]
        [InlineData(520, 114)]
        [InlineData(520, 120)]
        public void Plate_GradientBelowTwiceB0PerCm(double w, double h)
        {
            double b0 = P.PlateMinCircleLuminance(w, h), grad = P.PlateMaxGradientPerCm(w, h);
            m_Out.WriteLine($"{w}x{h}: max gradient {grad:F3} cd/m2/cm, limit {2 * b0:F2}");
            Assert.True(grad <= 2.0 * b0);
        }

        // ------------------------------------------------------------------ 4. the shader / exporters use the same numbers
        static double Num(string text, string pattern)
        {
            var m = Regex.Match(text, pattern);
            Assert.True(m.Success, "pattern not found: " + pattern);
            return double.Parse(m.Groups[1].Value, System.Globalization.CultureInfo.InvariantCulture);
        }

        [Fact]
        public void Shader_Defaults_And_PlateFalloff_MatchLampPhotometry()
        {
            string sh = Read("game/Assets/_Project/Rendering/Shaders/TruckExterior.shader");
            Assert.Equal(P.HueKnee, Num(sh, @"_LampHueKnee \(""[^""]*"", Range\([^)]*\)\) = ([0-9.]+)"), 6);
            Assert.Equal(P.HueCeiling, Num(sh, @"_LampHueCeiling \(""[^""]*"", Range\([^)]*\)\) = ([0-9.]+)"), 6);
            Assert.Equal(P.PlateIllum, Num(sh, @"_PlateIllum \(""[^""]*"", Range\([^)]*\)\) = ([0-9.]+)"), 6);
            Assert.Equal(P.StateTexels, Num(sh, @"#define KAMION_LAMP_TEXELS ([0-9.]+)"), 6);
            Assert.Contains("TruckLampHueLimitRef(", sh);
            string lens = Read("game/Assets/_Project/Rendering/Shaders/KamionLampLens.hlsl");
            Assert.Equal(P.PlateStripHalfWidthFraction, Num(lens, @"abs\(p\.x\) - ([0-9.]+) \* W"), 6);
            Assert.Equal(P.PlateLampAboveTopMm, Num(lens, @"hs\.y - p\.y \+ ([0-9.]+);"), 6);
            Assert.Equal(P.PlateFalloffMm, Num(lens, @"\(x \* x \+ y \* y\) / \(([0-9.]+) \*"), 6);
        }

        [Fact]
        public void Exporters_SplitTrailerTailAndStop_IntoGroups16And17()
        {
            string a6 = Read("tools/blender/truck/exterior/a6_export.py");
            var m = Regex.Match(a6, @"LIGHT_GROUPS = \[([^\]]*)\]", RegexOptions.Singleline);
            Assert.True(m.Success);
            var names = Regex.Matches(m.Groups[1].Value, @"""([A-Z_]+)""");
            Assert.Equal("TAIL", names[P.Tail].Groups[1].Value);
            Assert.Equal("STOP", names[P.Stop].Groups[1].Value);
            Assert.Equal("TAIL_BRAKE", names[P.TailBrake].Groups[1].Value);
            Assert.True(names.Count <= P.StateTexels);
            string trl = Read("tools/blender/truck/trailer/trailer_export.py");
            Assert.Matches(@"if ""_tail_"" in n:\s*\n\s*return ""TAIL""", trl);
            Assert.Matches(@"if ""_stop_"" in n:\s*\n\s*return ""STOP""", trl);
        }
    }
}
