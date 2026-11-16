using System.IO;
using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>night-pc-s23: R112 class B shape of the dipped beam, PC night fields, shader / C# parity markers.</summary>
    public sealed class PcNightLightingTests
    {
        const float Peak = 20000f;   // LP_* projectedHeadlampPeakCd (WORKING_VALUE)

        // UN R112 Annex 3, class B column (UN_R112.pdf p. 23): (up deg, right deg, min cd, max cd).
        [TestCase("B50L", 0.57f, -3.43f, 0f, 350f)]
        [TestCase("BR", 1.0f, 2.5f, 0f, 1750f)]
        [TestCase("75R", -0.57f, 1.15f, 10100f, float.MaxValue)]
        [TestCase("75L", -0.57f, -3.43f, 0f, 10600f)]
        [TestCase("50L", -0.86f, -3.43f, 0f, 13200f)]
        [TestCase("50R", -0.86f, 1.72f, 10100f, float.MaxValue)]
        [TestCase("50V", -0.86f, 0f, 5100f, float.MaxValue)]
        [TestCase("25L", -1.72f, -9f, 1700f, float.MaxValue)]
        [TestCase("25R", -1.72f, 9f, 1700f, float.MaxValue)]
        public void Beam_MeetsR112ClassBPoints(string point, float up, float right, float min, float max)
        {
            float cd = HeadlampBeam.R112PointCd(up, right, Peak);
            Assert.That(cd, Is.InRange(min, max), $"{point}: {cd:F0} cd");
        }

        [Test]
        public void Beam_ZoneIV_AboveMinimum_ZoneIII_BelowMaximum()
        {
            for (float r = -5.15f; r <= 5.15f; r += 0.25f)
                foreach (float u in new[] { -0.86f, -1.2f, -1.72f })
                    Assert.GreaterOrEqual(HeadlampBeam.R112PointCd(u, r, Peak), 2500f, $"zone IV {u} / {r}");
            // Zone III: bounded by 8L 1U - 8L 4U - 8R 4U - 8R 2U - 6R 1.5U - 1.5R 1.5U - HV (R112 Annex 3).
            for (float r = -8f; r <= 8f; r += 0.1f)
            {
                float lo = r <= 0f ? -r / 8f : r <= 1.5f ? r : r <= 6f ? 1.5f : 1.5f + (r - 6f) * 0.25f;
                for (float u = lo; u <= 4f; u += 0.1f)
                    Assert.LessOrEqual(HeadlampBeam.R112PointCd(u, r, Peak), 625f, $"zone III {u} / {r}");
            }
        }

        [Test]
        public void Beam_IsAsymmetric_RightShoulderBrighterAboveTheLeftCutOff()
        {
            // 0.3 deg above the horizontal cut-off: lit right of the elbow (15 deg rise), dark to the left (oncoming).
            float v = -HeadlampBeam.AimSlope + 0.005f;
            Assert.Greater(HeadlampBeam.RelI(0.08f, v), 10f * HeadlampBeam.RelI(-0.08f, v));
            Assert.Less(HeadlampBeam.RelI(0f, 0.05f), 0.02f, "nothing but stray light well above the cut-off");
        }

        [Test]
        public void PcTiers_NightFields_AreMonotonic_AndWithinTheShaderArray()
        {
            int prev = 0;
            foreach (PcTier t in System.Enum.GetValues(typeof(PcTier)))
            {
                var s = PcNightLighting.Get(t);
                Assert.That(s.lampPools, Is.InRange(prev, StreetLamps.MaxPools), t.ToString());
                Assert.IsTrue(s.projectedHeadlamps, t + ": dipped beam lights the road on every PC tier");
                prev = s.lampPools;
            }
            Assert.AreEqual(16, StreetLamps.MaxPools);
            Assert.AreEqual(30f, StreetLamps.PoolFocusAhead(8), 1e-4f, "phones: focus unchanged");
            Assert.AreEqual(60f, StreetLamps.PoolFocusAhead(16), 1e-4f);
        }

        [Test]
        public void PcOverlay_AppliesNightFields_PhonesKeepTheirs()
        {
            var high = System.Array.Find(QualityProfile.Defaults(), x => x.name == "High");
            Assert.AreEqual("High", high.name);
            Assert.IsFalse(high.projectedHeadlamps, "phone High: no projected beam (preset opt-in only)");
            Assert.LessOrEqual(high.lampPools, 8, "phone tiers stay within the old array");
            var pc = PcGraphicsTiers.Overlay(high);
            Assert.IsTrue(pc.projectedHeadlamps);
            Assert.AreEqual(16, pc.lampPools);
            Assert.IsTrue(pc.lampPoolSpecular);
        }

        [Test]
        public void Shader_ArraysAndConstants_MatchTheCSharpTwin()
        {
            string src = File.ReadAllText(Path.Combine(Application.dataPath, "_Project/Rendering/Shaders/KamionLampPools.hlsl"));
            StringAssert.Contains("float4 _KamionLampPos[16];", src);
            StringAssert.Contains("float4 _KamionLampAxis[16];", src);
            StringAssert.Contains("#define KAMION_BEAM_AIM 0.015", src);
            StringAssert.Contains("#define KAMION_BEAM_RISE 0.0274", src);
            StringAssert.Contains("#define KAMION_BEAM_HOT 0.02", src);
            StringAssert.Contains("0.75 * exp(-hc * hc * 138.89) + 0.25 * exp(-h * h * 6.3776)", src);
            StringAssert.Contains("smoothstep(-0.002, 0.003, below)", src);
            StringAssert.Contains("0.05 + 0.95 * exp(-max(below - 0.008, 0.0) * 25.0)", src);
            StringAssert.Contains("0.012 * saturate(1.0 + below * 20.0) * (0.3 + 0.7 * hs)", src);
        }
    }
}
