using System.IO;
using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>ADR 0216 (owner D65 p.7-8) and 0216b (D68): summer and white LED as per-region data; tile C and Dojlidy since 0216b.</summary>
    public class RegionLightingProfileTests
    {
        static RegionLightingProfiles Load() =>
            RegionLightingProfiles.Parse(File.ReadAllText(Path.Combine(Application.dataPath, "../../Data/Regions/lighting_profiles.json")));

        static EnvironmentLighting NewEnv(out GameObject go)
        {
            go = new GameObject("env-test") { hideFlags = HideFlags.HideAndDontSave };
            go.SetActive(false);
            return go.AddComponent<EnvironmentLighting>();
        }

        [Test]
        public void Knyszyn_GetsSummerDuskClockAndWhiteLed()
        {
            var env = NewEnv(out var go);
            try
            {
                Assert.AreEqual("summer-dk65-knyszyn,led-white-4000k", Load().ApplyTo(env, "knyszyn"));
                Assert.AreEqual("summer", env.season);
                var dusk = LightingPreset.CreateDusk(); var night = LightingPreset.CreateNight(); var clear = LightingPreset.CreateClear();
                Assert.AreEqual(21f, env.ClockHourOf(dusk), 1e-6f, "D65 p.7: dusk about 21:00");
                Assert.AreEqual(LightingPreset.NightClockHour, env.ClockHourOf(night), 1e-6f);
                Assert.AreEqual(clear.clockHour, env.ClockHourOf(clear), 1e-6f);
                Assert.AreEqual(300f, dusk.sunAzimuthDeg, 1e-6f, "D65 p.7: azimuth about 300 deg (the preset's sun is not changed)");
                Assert.AreEqual(1f, env.ledColour.a);
                Assert.Greater(env.ledColour.b, StreetLamps.DefaultLedColour.b, "whiter than the global warm-white default");
                Assert.AreEqual(1f, Mathf.Max(env.ledColour.r, env.ledColour.g, env.ledColour.b), 1e-6f);
            }
            finally { Object.DestroyImmediate(go); }
        }

        [Test]
        public void CorridorTile_GetsSummerOnly_AndOtherBialystokTilesNothing()
        {
            var env = NewEnv(out var go);
            try
            {
                Assert.AreEqual("summer-dk65-knyszyn", Load().ApplyTo(env, "dk65-03"));
                Assert.AreEqual(0f, env.ledColour.a, "no LED override on the unlit corridor tiles");
                foreach (string keep in new[] { "bialystok-maczka", "bialystok-kleeberga" })
                {
                    var e2 = NewEnv(out var g2);
                    try
                    {
                        Assert.AreEqual("", Load().ApplyTo(e2, keep));
                        Assert.AreEqual(LightingPreset.DuskClockHour, e2.ClockHourOf(LightingPreset.CreateDusk()), 1e-6f);
                        Assert.AreEqual(0f, e2.ledColour.a);
                    }
                    finally { Object.DestroyImmediate(g2); }
                }
            }
            finally { Object.DestroyImmediate(go); }
        }

        [Test]
        public void TileCAndDojlidy_GetSummerDuskClockAndTheKnyszynLedColour()
        {
            // ADR 0216b (owner D68 p.2): summer also in tile C and Dojlidy; LED colour = the ADR 0216 value
            var k = NewEnv(out var gk);
            try
            {
                Load().ApplyTo(k, "knyszyn");
                foreach (string rid in new[] { "bialystok-industrial-c", "bialystok-dojlidy" })
                {
                    var env = NewEnv(out var go);
                    try
                    {
                        Assert.AreEqual("summer-bialystok-cd,led-white-4000k-bialystok", Load().ApplyTo(env, rid));
                        Assert.AreEqual("summer", env.season);
                        var dusk = LightingPreset.CreateDusk();
                        Assert.AreEqual(21f, env.ClockHourOf(dusk), 1e-6f, "D68: dusk about 21:00");
                        Assert.AreEqual(300f, dusk.sunAzimuthDeg, 1e-6f, "D68 p.1: azimuth 300 deg (preset unchanged)");
                        Assert.AreEqual(LightingPreset.NightClockHour, env.ClockHourOf(LightingPreset.CreateNight()), 1e-6f);
                        Assert.AreEqual(k.ledColour, env.ledColour);
                        Assert.Greater(env.ledColour.b, StreetLamps.DefaultLedColour.b);
                    }
                    finally { Object.DestroyImmediate(go); }
                }
            }
            finally { Object.DestroyImmediate(gk); }
        }

        [Test]
        public void LedColourOverride_KeepsSodiumChromaticity_AndResets()
        {
            Color sodium = StreetLamps.SodiumLightColor;
            try
            {
                StreetLamps.SetLedColour(new Color(1f, 0.96f, 0.9f, 1f));
                Assert.AreEqual(0.9f, StreetLamps.LedColour.b, 1e-6f);
                Color s2 = StreetLamps.SodiumLightColor;
                // same chromaticity; the level follows the LED luminance at max channel 1 (equal-luminance rule of ADR 0191)
                Assert.AreEqual(sodium.g / sodium.r, s2.g / s2.r, 1e-5f); Assert.AreEqual(sodium.b / sodium.r, s2.b / s2.r, 1e-5f);
                Assert.AreEqual(1f, s2.r / sodium.r, 0.05f);
            }
            finally { StreetLamps.SetLedColour(new Color(0f, 0f, 0f, 0f)); }
            Assert.AreEqual(StreetLamps.DefaultLedColour, StreetLamps.LedColour);
        }
    }
}
