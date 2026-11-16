using System.IO;
using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// s20 night-int-0191-0192 (review REVIEW-2026-11-14-s20-0191-0192): ADR 0191 pools + ADR 0192 glare integrated -
    /// glare colour per luminaire (P1-6), glare out of the vehicle reflection capture (P1-7), soft pool rim (P1-3),
    /// night floor (P1-2), High lights as downward spots (P1-4).
    /// </summary>
    public class NightIntegrationTests
    {
        [Test]
        public void Glare_TakesTheColourOfEachLuminaire()
        {
            try
            {
                var heads = new[] { new Vector3(0, 8, 0), new Vector3(30, 8, 0) };
                var axes = new[] { new Vector4(1, 0, 0, 1), new Vector4(1, 0, 1, 1) };   // LED, sodium
                LampGlare.Sync(heads, axes, 2, 1f, 0.06f, new Color(1f, 0.93f, 0.82f), StreetLamps.SodiumLightColor);
                var c = LampGlare.MeshForTests.colors32;
                Assert.AreEqual(8, c.Length);
                Color led = c[0], sod = c[4];
                Assert.AreEqual(1f, led.r, 0.01f); Assert.Greater(led.g, 0.85f);           // white-warm LED
                Assert.AreEqual(1f, sod.r, 0.01f); Assert.Less(sod.g, 0.75f); Assert.Less(sod.b, 0.4f);   // sodium orange
                for (int k = 1; k < 4; k++) { Assert.AreEqual(c[0], c[k]); Assert.AreEqual(c[4], c[4 + k]); }
            }
            finally { LampGlare.Dispose(); }
        }

        [Test]
        public void SodiumLight_HasTheLedLuminance_AndIsOrange()
        {
            Color s = StreetLamps.SodiumLightColor, l = new Color(1f, 0.93f, 0.82f);
            float ys = 0.2126f * s.r + 0.7152f * s.g + 0.0722f * s.b, yl = 0.2126f * l.r + 0.7152f * l.g + 0.0722f * l.b;
            Assert.AreEqual(yl, ys, 1e-3f);
            Assert.Greater(s.r, s.g); Assert.Greater(s.g, s.b);
        }

        [Test]
        public void GlareShader_IsSkippedInTheVehicleReflectionCapture_AndUsesVertexColour()
        {
            string src = File.ReadAllText("Assets/_Project/Rendering/Shaders/LampGlare.shader");
            StringAssert.Contains("_KamionSkyCapOff > 0.5", src);
            StringAssert.Contains("COLOR", src);
            string cap = File.ReadAllText("Assets/_Project/Rendering/Runtime/Truck/VehicleReflectionCapture.cs");
            StringAssert.Contains("_KamionSkyCapOff", cap);
            StringAssert.Contains("SetGlobalVector(k_WindowsLum, Vector4.zero)", cap);   // P1-7: no lit windows in the cube
        }

        [Test]
        public void Pool_RimIsSoft_FluxKept()
        {
            // F(0) = NadirFactor, F at the old rim (rho 1) a few % of the centre, 0 at the tail radius
            Assert.AreEqual(StreetLampOptics.NadirFactor, StreetLampOptics.Footprint(0f), 1e-6f);
            float rim = StreetLampOptics.Footprint(1f) / StreetLampOptics.NadirFactor;
            Assert.That(rim, Is.InRange(0.02f, 0.06f));
            Assert.AreEqual(0f, StreetLampOptics.Footprint(StreetLampOptics.TailRadius * StreetLampOptics.TailRadius), 1e-7f);
            // integral over the plane (2 pi rho drho) equals that of the old (1 - rho²)² = pi / 3
            double sum = 0; const int n = 4000; float rmax = StreetLampOptics.TailRadius;
            for (int i = 0; i < n; i++) { float r = (i + 0.5f) * rmax / n; sum += StreetLampOptics.Footprint(r * r) * 2 * Mathf.PI * r * rmax / n; }
            Assert.AreEqual(Mathf.PI / 3f, (float)sum, 2e-3f);
        }

        [Test]
        public void NightFloor_IsAFewPercentOfAPool_AndHasATierSwitch()
        {
            float nadir8m = StreetLamps.DownIntensityCd / 64f;
            Assert.That(StreetLamps.NightFloorLux / nadir8m, Is.InRange(0.01f, 0.05f), "floor vs pool nadir at 8 m");
            Assert.That(StreetLamps.NightFloorReachM, Is.InRange(25f, 80f));
            var t = new QualityProfile.Tier();
            Assert.IsFalse(t.lampFloorOff, "inverted flag: tiers saved before s20 keep the floor");
            string hlsl = File.ReadAllText("Assets/_Project/Rendering/Shaders/KamionLampPools.hlsl");
            StringAssert.Contains("_KamionLampFloor", hlsl);
        }

        [Test]
        public void HighLights_AreDownwardSpots_WithTheLuminaireCutoff()
        {
            Assert.That(StreetLamps.SpotOuterDeg, Is.InRange(130f, 160f), "outer cone ~ cut-off 65-80 deg from the axis");
            // behind the column (against the tilt) the cone ends near the pool's house-side reach (0.7 h x tail 1.5 -> 46 deg)
            float house = StreetLamps.SpotOuterDeg * 0.5f - StreetLamps.SpotTiltDeg;
            Assert.That(house, Is.InRange(40f, 55f));
            float along = Mathf.Acos(Mathf.Cos(StreetLamps.SpotOuterDeg * 0.5f * Mathf.Deg2Rad) / Mathf.Cos(StreetLamps.SpotTiltDeg * Mathf.Deg2Rad)) * Mathf.Rad2Deg;
            Assert.That(along, Is.InRange(60f, 75f), "along the road the cone reaches the pool (~67-74 deg)");
            Assert.Less(StreetLamps.SpotInnerDeg, StreetLamps.SpotOuterDeg);
            string src = File.ReadAllText("Assets/_Project/Rendering/Runtime/Sky/StreetLamps.cs");
            StringAssert.Contains("l.type = LightType.Spot;", src);
            StringAssert.Contains("Quaternion.LookRotation(Vector3.down", src);
        }
    }
}
