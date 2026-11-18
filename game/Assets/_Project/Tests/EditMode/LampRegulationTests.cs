using System;
using System.IO;
using System.Text.RegularExpressions;
using Game.Editor.Build;
using Game.Editor.VisualQA;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering;
using P = Game.Vehicle.Runtime.LampPhotometry;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// ADR 0197: rear lamps vs UN R148 / R48 (Dz.U. UE L 347, 30.9.2021; quotes in research P16-035, -090..094, -111/112).
    /// (1) stop : tail >= 5 : 1 AFTER the ADR 0178 display limiter (CPU mirror + GPU readback of the production shader),
    /// (2) TruckLights drives separate trailer tail / stop chambers (16 / 17) and the limiter reference (state alpha),
    /// (3) amber / red against the R48 2.11.1 areas (sRGB -> XYZ -> xy), (4) plate >= 2.5 cd/m^2 at every measuring circle.
    /// The same arithmetic runs without Unity in tools/lamp-check (dotnet test).
    /// </summary>
    public sealed class LampRegulationTests
    {
        static string F(double v) => v.ToString("R", System.Globalization.CultureInfo.InvariantCulture);

        // ------------------------------------------------------------------ 1. stop : tail after the limiter (CPU)
        [TestCase(1e-6)] [TestCase(1e-5)] [TestCase(1e-4)] [TestCase(1e-3)] [TestCase(2e-3)] [TestCase(1e-2)] [TestCase(1e-1)]
        public void StopToTail_AfterLimiter_AtLeastFiveToOne(double exposure)
        {
            foreach (double hdr in new[] { 1.0, 0.05 })
                Assert.That(P.StopToTailRatioAfterLimiter(exposure, hdr), Is.GreaterThanOrEqualTo(P.MinStopToTailRatio),
                    $"E {exposure} hdr {hdr} (R148 4.8.11)");
            Assert.That(P.DisplayedMax(P.BrakeNits, P.Stop, exposure) / P.DisplayedMax(P.TailNits, P.Tail, exposure),
                Is.GreaterThanOrEqualTo(P.MinStopToTailRatio), "trailer: stop chamber vs tail chamber");
        }

        [Test]
        public void LegacyPerPixelLimiter_ReproducesTheMeasuredOneToOne()
        {
            // ADR 0181 r2 P2-5: after6 High dusk tail 201 vs stop 202 (sRGB). Guard that the fix is the reference, not luck.
            Assert.That(P.StopToTailRatioAfterLimiter(1e-2, 1.0, useReference: false), Is.LessThan(1.1));
        }

        // ------------------------------------------------------------------ 1b. the same on the GPU (production shader code)
        [TestCase(1e-3)] [TestCase(1e-2)] [TestCase(1e-4)]
        public void Shader_HueLimitRef_KeepsStopToTail_AndCeiling(double exposure)
        {
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null) Assert.Ignore("GPU readback requires a graphics device");
            double refMax = P.BrakeNits * exposure;
            float tail = ReadRef(P.TailNits * exposure, refMax), stop = ReadRef(P.BrakeNits * exposure, refMax);
            Assert.That(stop, Is.LessThanOrEqualTo(P.HueCeiling + 1e-4f));
            Assert.That(tail, Is.EqualTo((float)P.DisplayedMax(P.TailNits, P.TailBrake, exposure)).Within(1e-4f), "GPU = LampPhotometry");
            Assert.That(stop / tail, Is.GreaterThanOrEqualTo(P.MinStopToTailRatio));
            // reference 0 = the ADR 0178 limiter unchanged
            float legacy = TruckPaintProbe.Read(TruckPaintProbe.BuildProbeShader(
                $"TruckLampHueLimitRef(float3({F(P.TailNits * exposure)},0,0), 0.0, _LampHueKnee, _LampHueCeiling).rrr"), 1f, false, true, out _);
            float old = TruckPaintProbe.Read(TruckPaintProbe.BuildProbeShader(
                $"TruckLampHueLimit(float3({F(P.TailNits * exposure)},0,0), _LampHueKnee, _LampHueCeiling).rrr"), 1f, false, true, out _);
            Assert.That(legacy, Is.EqualTo(old).Within(1e-5f));
        }

        static float ReadRef(double m, double refMax) => TruckPaintProbe.Read(TruckPaintProbe.BuildProbeShader(
            $"TruckLampHueLimitRef(float3({F(m)},0,0), {F(refMax)}, _LampHueKnee, _LampHueCeiling).rrr"), 1f, false, true, out _);

        // ------------------------------------------------------------------ 2. TruckLights state texture
        GameObject m_Sun, m_Lamp;
        Light m_OldSun;
        Texture m_OldTex;
        float m_OldScale, m_OldExposure;
        TruckLights m_Lights;

        [SetUp]
        public void Create()
        {
            m_OldSun = RenderSettings.sun; m_OldTex = Shader.GetGlobalTexture("_TruckLightState");
            m_OldScale = Shader.GetGlobalFloat("_TruckLightNitsScale"); m_OldExposure = Shader.GetGlobalFloat("_KamionExposure");
            m_Sun = new GameObject("Lamp regulation test sun");
            var sun = m_Sun.AddComponent<Light>(); sun.type = LightType.Directional; sun.transform.rotation = Quaternion.Euler(-5f, 0, 0);
            RenderSettings.sun = sun;   // below the auto low-beam threshold: tail lamps on
            m_Lamp = new GameObject("Lamp regulation test state"); m_Lights = m_Lamp.AddComponent<TruckLights>();
        }

        [TearDown]
        public void Restore()
        {
            UnityEngine.Object.DestroyImmediate(m_Lamp); UnityEngine.Object.DestroyImmediate(m_Sun); RenderSettings.sun = m_OldSun;
            Shader.SetGlobalTexture("_TruckLightState", m_OldTex); Shader.SetGlobalFloat("_TruckLightNitsScale", m_OldScale);
            Shader.SetGlobalFloat("_KamionExposure", m_OldExposure);
        }

        float Nits(int group) => m_Lights.StateTexture.GetPixel(group, 0).r * TruckLights.NitsPerEncodedUnit;
        float RefNits(int group) => m_Lights.StateTexture.GetPixel(group, 0).a * TruckLights.NitsPerEncodedUnit;

        [Test]
        public void TruckLights_TrailerChambers_AndLimiterReference()
        {
            Assert.That(m_Lights.StateTexture.width, Is.EqualTo(P.StateTexels));
            m_Lights.Refresh();
            Assert.That(m_Lights.LowBeamOn, Is.True);
            Assert.That(Nits(P.Tail), Is.EqualTo(P.TailNits).Within(2f), "tail chamber at tail level");
            Assert.That(Nits(P.Stop), Is.EqualTo(0f), "stop chamber dark without braking");
            Assert.That(Nits(P.TailBrake), Is.EqualTo(P.TailNits).Within(2f));
            m_Lights.forceBrake = true; m_Lights.Refresh();
            Assert.That(Nits(P.Stop), Is.EqualTo(P.BrakeNits).Within(20f), "stop chamber lit");
            Assert.That(Nits(P.Tail), Is.EqualTo(P.TailNits).Within(2f), "tail chamber unchanged while braking");
            Assert.That(Nits(P.TailBrake), Is.EqualTo(P.BrakeNits).Within(20f));
            for (int g = 0; g < P.StateTexels; g++)
                Assert.That(RefNits(g), Is.EqualTo(P.LimiterReferenceNits(g)).Within(20f), $"limiter reference of group {g}");
            foreach (int g in new[] { P.TailBrake, P.Tail, P.Stop, P.MarkerRear })
                Assert.That(RefNits(g), Is.EqualTo(P.BrakeNits).Within(20f));
            foreach (int g in new[] { P.Drl, P.IndL, P.IndR, P.Plate, P.FogRear, P.Reverse })
                Assert.That(RefNits(g), Is.EqualTo(0f), "no reference: ADR 0178 per-pixel limit");
        }

        [TestCase(1e-3f)] [TestCase(1e-2f)]
        public void Shader_DecodedStateTexture_StopToTail_AtLeastFiveToOne(float exposure)
        {
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null) Assert.Ignore("GPU readback requires a graphics device");
            Shader.SetGlobalFloat("_KamionExposure", exposure);
            float tail = ReadGroup(P.TailBrake);
            m_Lights.forceBrake = true; m_Lights.Refresh();
            float stop = ReadGroup(P.TailBrake);
            Assert.That(stop, Is.LessThanOrEqualTo(P.HueCeiling + 1e-4f));
            Assert.That(stop / tail, Is.GreaterThanOrEqualTo(P.MinStopToTailRatio), $"stop {stop} tail {tail}");
        }

        float ReadGroup(int group)
        {
            string u = F((group + 0.5) / P.StateTexels);
            string s = $"SAMPLE_TEXTURE2D_LOD(_TruckLightState, sampler_point_clamp, float2({u},0.5),0)";
            string expr = $"TruckLampHueLimitRef(TruckLampRadiance({s}.rgb), TruckLampRadiance({s}.aaa).x, _LampHueKnee, _LampHueCeiling).rrr";
            return TruckPaintProbe.Read(TruckPaintProbe.BuildProbeShader(expr), 1f, false, true, out _);
        }

        // ------------------------------------------------------------------ 3. colours vs R48 2.11.1
        [Test]
        public void Amber_MeetsGreenAndRedLimits_NearestToTheR48Area()
        {
            P.Chromaticity(TruckLights.Amber.r, TruckLights.Amber.g, TruckLights.Amber.b, out double x, out double y);
            Assert.That(P.AmberGreenLimit(x, y), "R48 2.11.1.3 towards green: y <= x - 0.120");
            Assert.That(P.AmberRedLimit(x, y), "R48 2.11.1.3 towards red: y >= 0.390");
            P.NearestRedGreenEdgeG(P.R48AmberCorners, out double best);
            Assert.That(P.DistanceToPolygon(x, y, P.R48AmberCorners), Is.LessThanOrEqualTo(best + 0.001));
            P.Chromaticity(1, 0.28, 0, out x, out y);
            Assert.That(P.AmberGreenLimit(x, y), Is.False, "the old (1, 0.28, 0) is beyond the green limit");
        }

        [Test]
        public void R48AmberAndRed_AreOutsideSrgb_RedIsTheNearestPrimary()
        {
            for (int i = 0; i <= 1000; i++)
            {
                P.Chromaticity(1, i / 1000.0, 0, out double x, out double y);
                Assert.That(P.InR48Amber(x, y), Is.False);
            }
            P.Chromaticity(TruckLights.Red.r, TruckLights.Red.g, TruckLights.Red.b, out double rx, out double ry);
            Assert.That(P.RedYellowLimit(rx, ry), "R48 2.11.1.4 towards yellow: y <= 0.335");
            Assert.That(rx + ry, Is.EqualTo(0.970).Within(1e-3), "x + y = 0.970, 0.010 short of the purple limit (unreachable in sRGB)");
        }

        // ------------------------------------------------------------------ 4. number plate (R148 5.11.3)
        [TestCase(520, 114)] [TestCase(520, 120)]
        public void Plate_EveryMeasuringCircle_AtLeast2_5cdm2_GradientBelowTwoB0(double w, double h)
        {
            double b0 = P.PlateMinCircleLuminance(w, h);
            Assert.That(b0, Is.GreaterThanOrEqualTo(P.PlateMinLuminance), "R148 5.11.3 (a)");
            Assert.That(P.PlateMaxGradientPerCm(w, h), Is.LessThanOrEqualTo(2.0 * b0), "R148 5.11.3: gradient <= 2 x B0 / cm");
            Assert.That(Game.Editor.Setup.TruckAssetBuilder.PlateIllum, Is.EqualTo(P.PlateIllum), "materials get the checked value");
        }

        [Test]
        public void ShaderSource_MatchesLampPhotometry()
        {
            string sh = File.ReadAllText(Path.Combine(EditorTools.ProjectRoot, "Assets/_Project/Rendering/Shaders/TruckExterior.shader"));
            Assert.That(Num(sh, @"#define KAMION_LAMP_TEXELS ([0-9.]+)"), Is.EqualTo(P.StateTexels));
            Assert.That(Num(sh, @"_LampHueKnee \(""[^""]*"", Range\([^)]*\)\) = ([0-9.]+)"), Is.EqualTo(P.HueKnee).Within(1e-6));
            Assert.That(Num(sh, @"_LampHueCeiling \(""[^""]*"", Range\([^)]*\)\) = ([0-9.]+)"), Is.EqualTo(P.HueCeiling).Within(1e-6));
            Assert.That(Num(sh, @"_PlateIllum \(""[^""]*"", Range\([^)]*\)\) = ([0-9.]+)"), Is.EqualTo(P.PlateIllum).Within(1e-6));
            Assert.That(Num(sh, @"_PlateDisplayMax \(""[^""]*"", Range\([^)]*\)\) = ([0-9.]+)"), Is.EqualTo(P.PlateDisplayMax).Within(1e-6), "ADR 0297");
            string lens = File.ReadAllText(Path.Combine(EditorTools.ProjectRoot, "Assets/_Project/Rendering/Shaders/KamionLampLens.hlsl"));
            Assert.That(Num(lens, @"abs\(p\.x\) - ([0-9.]+) \* W"), Is.EqualTo(P.PlateStripHalfWidthFraction).Within(1e-6));
            Assert.That(Num(lens, @"hs\.y - p\.y \+ ([0-9.]+);"), Is.EqualTo(P.PlateLampAboveTopMm).Within(1e-6));
            Assert.That(Num(lens, @"\(x \* x \+ y \* y\) / \(([0-9.]+) \*"), Is.EqualTo(P.PlateFalloffMm).Within(1e-6));
        }

        static double Num(string text, string pattern)
        {
            var m = Regex.Match(text, pattern);
            Assert.That(m.Success, "pattern not found: " + pattern);
            return double.Parse(m.Groups[1].Value, System.Globalization.CultureInfo.InvariantCulture);
        }
    }
}
