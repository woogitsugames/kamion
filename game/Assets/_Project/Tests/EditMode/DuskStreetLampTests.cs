using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0062 / review r8 N-20: at dusk the street lamps must read - lamps on, and their pools on the road at least 1.5×
    /// the ambient-lit background. Cause of the r8 FAIL: LP_Dusk had the sun at +1° (~2.4 klx of sky), so a lamp's ~30 lx
    /// pool was ~1 % of the background.
    /// </summary>
    public class DuskStreetLampTests
    {
        [Test]
        public void NightReflectionUsesMappedSkyButPreservesGroundRadiance()
        {
            var night = LightingPreset.CreateNight();
            Cubemap raw = null, mapped = null;
            try
            {
                var model = night.CreateModel();
                raw = model.ReflectionCubemap(night.groundAlbedo, 8);
                mapped = model.ReflectionCubemap(night.groundAlbedo, 8, c => WorldAtmosphere.DisplaySkyFog(night, c));
                var beforeSky = raw.GetPixel(CubemapFace.PositiveY, 4, 4);
                var afterSky = mapped.GetPixel(CubemapFace.PositiveY, 4, 4);
                Assert.Less(afterSky.maxColorComponent, beforeSky.maxColorComponent*0.3f,
                    "Night reflection must not retain the bright twilight sky");
                var beforeGround = raw.GetPixel(CubemapFace.NegativeY, 4, 4);
                var afterGround = mapped.GetPixel(CubemapFace.NegativeY, 4, 4);
                Assert.AreEqual(beforeGround, afterGround, "sky appearance must not dim reflected diffuse ground");
            }
            finally
            {
                if (raw != null) Object.DestroyImmediate(raw);
                if (mapped != null) Object.DestroyImmediate(mapped);
                Object.DestroyImmediate(night);
            }
        }

        [Test]
        public void NightSkyPresentationChangesFogColourWithoutChangingScenePhotometry()
        {
            var night = LightingPreset.CreateNight();
            try
            {
                // Compare genuinely different input grades even after Night's factory defaults were selected.
                night.skyDisplayGain = 1f; night.skyDisplayDesaturation = 0f;
                var before = night.CreateModel();
                night.skyDisplayGain = 0.125f; night.skyDisplayDesaturation = 0.85f;
                var after = night.CreateModel();
                Assert.AreEqual(before.Exposure, after.Exposure);
                Assert.AreEqual(before.HorizontalIlluminanceLux, after.HorizontalIlluminanceLux);
                var fog = before.HorizonColorExposed();
                var display = WorldAtmosphere.DisplaySkyFog(night, fog);
                Assert.Less(display.maxColorComponent, fog.maxColorComponent);
                Assert.AreEqual(fog.a, display.a);
            }
            finally { Object.DestroyImmediate(night); }
        }

        [Test]
        public void LegacyPresetsKeepTheirSkyAndFogPresentation()
        {
            foreach (var preset in new[] { LightingPreset.CreateClear(), LightingPreset.CreateOvercast(), LightingPreset.CreateLowSun(), LightingPreset.CreateDusk() })
                try
                {
                    var fog = preset.CreateModel().HorizonColorExposed();
                    Assert.AreEqual(fog, WorldAtmosphere.DisplaySkyFog(preset, fog));
                    preset.skyDisplayGain = 0f; // missing legacy serialized field
                    Assert.AreEqual(fog, WorldAtmosphere.DisplaySkyFog(preset, fog));
                }
                finally { Object.DestroyImmediate(preset); }
        }

        [Test]
        public void NightSeparatesDarkAmbientFromFixedLampPhotometryWithoutChangingDusk()
        {
            var dusk = LightingPreset.CreateDusk();
            var night = LightingPreset.CreateNight();
            try
            {
                var d = dusk.CreateModel(); var n = night.CreateModel();
                Assert.AreEqual(-5f, dusk.sunElevationDeg, "existing dusk stays intact");
                Assert.AreEqual(0f, dusk.exposureCompensation);
                Assert.AreEqual(0f, n.SunNormalIlluminanceLux);
                Assert.Less(n.SkyHorizontalIlluminanceLux, d.SkyHorizontalIlluminanceLux);
                float ambientRatio = n.HorizontalIlluminanceLux*n.Exposure/(d.HorizontalIlluminanceLux*d.Exposure);
                Assert.That(ambientRatio, Is.InRange(1f/32f, 1f/8f), "night ambient must be clearly darker, not just a renamed dusk");
                Assert.Greater(StreetLamps.DownIntensityCd/n.HorizontalIlluminanceLux,
                    StreetLamps.DownIntensityCd/d.HorizontalIlluminanceLux, "fixed lamp gains contrast against darker sky");
            }
            finally { Object.DestroyImmediate(dusk); Object.DestroyImmediate(night); }
        }

        const float LampHeightM = 8f;   // typical urban road luminaire mounting height (WORKING_VALUE)

        [Test]
        public void TwilightFactor_IsOneAboveHalfDegree_MonotoneAndEndsAtCivilTwilight()
        {
            Assert.AreEqual(1f, SkyModel.TwilightFactorAt(0.5f), 1e-6f);
            Assert.AreEqual(1f, SkyModel.TwilightFactorAt(10f), 1e-6f);
            float prev = 2f;
            for (float el = 0.5f; el >= -6f; el -= 0.25f)
            {
                float f = SkyModel.TwilightFactorAt(el);
                Assert.Less(f, prev + 1e-6f, $"monotone at {el}");
                prev = f;
            }
            var m = new SkyModel(-6f, 300f, 4f, 0f, 5f);
            Assert.AreEqual(SkyModel.CivilTwilightEndLux, m.HorizontalIlluminanceLux, 0.2f, "end of civil twilight");
            Assert.AreEqual(0f, m.SunNormalIlluminanceLux, "sun below the horizon: no direct light");
        }

        [Test]
        public void DuskPreset_IsCivilTwilight_LampsOn_PoolsReadOnTheRoad()
        {
            var dusk = LightingPreset.CreateDusk();
            try
            {
                var m = dusk.CreateModel();
                Assert.Less(m.TrueSunElevationDeg, 0f, "dusk = after sunset");
                Assert.That(m.HorizontalIlluminanceLux, Is.InRange(3.4f, 40f), "civil twilight: 3.4 lx at -6°, ~8 lx at -5°");
                float pool = StreetLamps.DownIntensityCd / (LampHeightM * LampHeightM);
                float ratio = (m.HorizontalIlluminanceLux + pool) / m.HorizontalIlluminanceLux;
                Assert.GreaterOrEqual(ratio, 1.5f, $"pool under the lamp {pool:F0} lx on {m.HorizontalIlluminanceLux:F0} lx (r8 acceptance >= 1.5x)");
                StreetLamps.SetSunElevation(m.TrueSunElevationDeg);
                Assert.AreEqual(1f, StreetLamps.On, 1e-6f, "lamps fully on");
                // The old preset (+1°): the cause of N-20.
                var old = new SkyModel(1f, 300f, 4f, 0.2f, 11f);
                Assert.Less((old.HorizontalIlluminanceLux + pool) / old.HorizontalIlluminanceLux, 1.05f, "+1° sun: pool invisible");
            }
            finally { Object.DestroyImmediate(dusk); }
        }

        [Test]
        public void DuskExposure_FollowsTheTwilight_ScreenBrightnessContinuous()
        {
            // Ambient-lit grey on screen (E·k) at 0.5° and at -4° differs only by the 0.2 EV deepening.
            float e05 = new SkyModel(0.5f, 300f, 4f, 0.2f, 0f).HorizontalIlluminanceLux;
            float e4 = new SkyModel(-4f, 300f, 4f, 0.2f, 0f).HorizontalIlluminanceLux;
            float k05 = SkyModel.ExposureFromEv100(ExposureTable.Ev100(0.5f, 0.2f));
            float k4 = SkyModel.ExposureFromEv100(ExposureTable.Ev100(-4f, 0.2f));
            Assert.AreEqual(-0.2f, Mathf.Log(e4 * k4 / (e05 * k05), 2f), 0.05f);
        }
    }
}
