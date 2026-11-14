using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>ADR 0199: twilight illuminance table, glow colour toward the sun, street-lamp switch-on, lit-window shares by
    /// sun and clock, far night floor.</summary>
    public class DuskCalibrationTests
    {
        // Schlyter radfaq "Solar illumination on horizontal surface" (research/cloud/p17-dusk-lighting C60-001…007), lx.
        static readonly float[] k_El = { 0f, -1f, -2f, -3f, -4f, -5f, -6f, -7f, -8f };
        static readonly float[] k_Lux = { 759f, 405f, 189f, 79.1f, 29.9f, 10.4f, 3.41f, 1.09f, 0.348f };

        [Test]
        public void TwilightFactor_MatchesTheTableAtEveryNode_NoStepAtHalfDegree()
        {
            Assert.AreEqual(1f, SkyModel.TwilightFactorAt(0.5f), 1e-6f, "the model's own 0.5° dome");
            Assert.AreEqual(1f, SkyModel.TwilightFactorAt(0.5001f), 1e-6f);
            Assert.AreEqual(1f, SkyModel.TwilightFactorAt(0.4999f), 1e-3f, "continuous at 0.5°");
            for (int i = 0; i < k_El.Length; i++)
            {
                // the model's clear dome at 0.5° × factor (below 0° there is no direct sun: SkyModel E = this, −6° checked
                // through the model in DuskStreetLampTests)
                float e = SkyModel.TwilightFactorAt(k_El[i]) * SkyModel.ModelSkyLuxAtHalfDegree;
                if (k_El[i] < 0f) Assert.AreEqual(e, new SkyModel(k_El[i], 300f, 4f, 0f, 5f).HorizontalIlluminanceLux, e * 0.01f, $"model at {k_El[i]}°");
                Assert.That(e / k_Lux[i], Is.InRange(0.98f, 1.02f), $"E at {k_El[i]}°: {e:F3} lx vs table {k_Lux[i]} lx");
            }
            Assert.AreEqual(SkyModel.CivilTwilightEndLux, SkyModel.TwilightTableLuxAt(-6f), 1e-4f, "−6° node = the civil twilight constant");
        }

        [Test]
        public void TwilightFactor_SunsetNoLongerTooBright_Monotone_ClampedAtMinus8()
        {
            float e05 = SkyModel.ModelSkyLuxAtHalfDegree;
            // review s20 cloud M60 §4.1: the old log-linear curve gave 1366 lx at 0° and 503 lx at −1°
            Assert.Less(SkyModel.TwilightFactorAt(0f) * e05, 800f, "0°: 759 lx, not ~1366");
            Assert.Less(SkyModel.TwilightFactorAt(-1f) * e05, 430f, "−1°: 405 lx, not ~503");
            // the −3…−5° nodes were 12-16 % too dark
            Assert.Greater(SkyModel.TwilightFactorAt(-4f) * e05, 28f, "−4°: 29.9 lx, not ~25");
            float prev = 2f;
            for (float el = 0.5f; el >= -10f; el -= 0.1f)
            {
                float f = SkyModel.TwilightFactorAt(el);
                Assert.LessOrEqual(f, prev + 1e-7f, $"monotone at {el:F1}");
                Assert.Greater(f, 0f);
                prev = f;
            }
            Assert.AreEqual(SkyModel.TwilightFactorAt(-8f), SkyModel.TwilightFactorAt(-12f), 1e-9f, "model floor −8°");
            // log-linear inside a node interval: −0.5° between 759 and 405 (table 562)
            Assert.That(SkyModel.TwilightTableLuxAt(-0.5f), Is.InRange(540f, 580f));
        }

        [Test]
        public void DuskGlow_TowardTheSun_PaleYellowLow_FaintPinkAbove_NoCoral()
        {
            var p = LightingPreset.CreateDusk();
            try
            {
                var m = p.CreateModel();
                for (float elev = 0.5f; elev <= 20f; elev += 0.5f)
                {
                    for (float g = 0f; g <= 60f; g += 5f)
                    {
                        // the azimuth offset from the sun at this elevation: γ ≥ elevation-difference; use ChromaAt directly
                        var c = m.ChromaAt(Mathf.Sin(elev * Mathf.Deg2Rad), Mathf.Max(g, elev) * Mathf.Deg2Rad);
                        float mx = Mathf.Max(c.r, Mathf.Max(c.g, c.b)), mn = Mathf.Min(c.r, Mathf.Min(c.g, c.b));
                        // saturation of the display colour (gamma ~1/2.2 on the linear ratio): the coral of ADR 0192 was
                        // 0.40-0.53 with R / max(G, B) 2.0-3.5 (probe-before.tsv, 2-6° toward the sun)
                        float sat = 1f - Mathf.Pow(mn / mx, 1f / 2.2f);
                        if (c.r > c.b)
                        {
                            Assert.Less(sat, 0.4f, $"warm glow too saturated at elev {elev} γ {g}: {c}");
                            Assert.Less(c.r / Mathf.Max(c.g, c.b), 1.7f, $"coral (red over green and blue) at elev {elev} γ {g}: {c}");
                        }
                        Assert.LessOrEqual(Mathf.Min(c.r, c.b) - c.g, 0.06f, $"magenta at elev {elev} γ {g}: {c}");
                    }
                }
                var low = m.ChromaAt(Mathf.Sin(2f * Mathf.Deg2Rad), 2f * Mathf.Deg2Rad);
                Assert.Greater(low.r, low.g, $"low band toward the sun warm: {low}");
                Assert.Greater(low.g, low.b, $"low band yellowish (G > B): {low}");
                var high = m.ChromaAt(Mathf.Sin(4f * Mathf.Deg2Rad), 4f * Mathf.Deg2Rad);
                Assert.Greater(high.r, high.g * 1.03f, $"faint pink above the yellow band: {high}");
                Assert.GreaterOrEqual(high.b, high.g * 0.97f, $"pink, not orange (B ≈ G): {high}");
                Assert.Greater(low.g / low.b, high.g / high.b, "yellower low, pinker high");
                var zenith = m.ChromaAt(1f, 90f * Mathf.Deg2Rad);
                Assert.Greater(zenith.b, zenith.r * 2f, $"zenith blue: {zenith}");
            }
            finally { Object.DestroyImmediate(p); }
        }

        [Test]
        public void StreetLamps_FadeOnBetweenMinus2AndMinus3Point5()
        {
            Assert.AreEqual(0f, StreetLamps.SwitchOn(5f), 1e-6f);
            Assert.AreEqual(0f, StreetLamps.SwitchOn(0f), 1e-6f, "sunset: still off");
            Assert.AreEqual(0f, StreetLamps.SwitchOn(-2f), 1e-6f);
            Assert.AreEqual(0.5f, StreetLamps.SwitchOn(-2.75f), 1e-4f);
            Assert.AreEqual(1f, StreetLamps.SwitchOn(-3.5f), 1e-6f);
            Assert.AreEqual(1f, StreetLamps.SwitchOn(LightingPreset.DuskSunElevationDeg), 1e-6f, "dusk preset lamps fully on");
            float prev = -1f;
            for (float e = 2f; e >= -10f; e -= 0.1f)
            {
                float s = StreetLamps.SwitchOn(e);
                Assert.GreaterOrEqual(s, prev - 1e-6f, $"monotone at {e:F1}");
                prev = s;
            }
        }

        [Test]
        public void Windows_FlatSharesLuminance_OfficesFollowTheClock()
        {
            Assert.AreEqual(0.25f, NightWindows.BaseShares(-6f, 12f).x, 1e-4f);
            Assert.AreEqual(0.28f, NightWindows.BaseShares(-16f, 12f).x, 1e-4f);
            Assert.AreEqual(0.28f, NightWindows.BaseShares(-25f, 12f).x, 1e-4f);
            Assert.AreEqual(8f, NightWindows.MeanLuminance, 1e-6f, "6 cd/m² measured (Novak 2025) + small-screen margin");
            Assert.AreEqual(0.4f, NightWindows.OfficeShareAtHour(LightingPreset.DuskClockHour), 1e-4f, "November 16:10: working time");
            Assert.AreEqual(0.25f, NightWindows.OfficeShareAtHour(18f), 1e-4f);
            Assert.AreEqual(0.1f, NightWindows.OfficeShareAtHour(19f), 1e-4f);
            Assert.AreEqual(0.05f, NightWindows.OfficeShareAtHour(LightingPreset.NightClockHour), 1e-4f);
            Assert.AreEqual(0.05f, NightWindows.OfficeShareAtHour(3f), 1e-4f);
            // offices do not depend on the sun
            Assert.AreEqual(NightWindows.BaseShares(-6f, 18f).y, NightWindows.BaseShares(-16f, 18f).y, 1e-6f);
            var dusk = LightingPreset.CreateDusk();
            var night = LightingPreset.CreateNight();
            try
            {
                Assert.AreEqual(LightingPreset.DuskClockHour, dusk.clockHour, 1e-6f);
                Assert.AreEqual(LightingPreset.NightClockHour, night.clockHour, 1e-6f);
            }
            finally { Object.DestroyImmediate(dusk); Object.DestroyImmediate(night); }
        }

        [Test]
        public void NightFloor_BeyondReach_ClearAndOvercastLevels()
        {
            Assert.AreEqual(0.03f, StreetLamps.FarFloorLux(0f), 1e-6f);
            Assert.AreEqual(0.2f, StreetLamps.FarFloorLux(1f), 1e-6f);
            try
            {
                StreetLamps.SetSunElevation(-8f, 1f);
                Assert.AreEqual(0.2f / StreetLamps.NightFloorLux, StreetLamps.FarFloorShare, 1e-6f);
                StreetLamps.SetSunElevation(-8f, 0f);
                Assert.AreEqual(0.03f / StreetLamps.NightFloorLux, StreetLamps.FarFloorShare, 1e-6f);
            }
            finally { StreetLamps.SetSunElevation(30f); }
            Assert.Less(StreetLamps.FarFloorLux(1f), StreetLamps.NightFloorLux, "far floor below the near floor");
            string hlsl = System.IO.File.ReadAllText("Assets/_Project/Rendering/Shaders/KamionLampPools.hlsl");
            StringAssert.Contains("lerp(_KamionLampColor.w, 1.0, fade * fade)", hlsl);
        }
    }
}
