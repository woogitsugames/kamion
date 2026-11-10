using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>ADR 0080: contrast toe (owner variant 3 for overcast), its inverse used by the cab view, ground haze.</summary>
    public class LookToeTests
    {
        const float S = 0.9f, P = 0.4f, Pivot = 0.6f;

        [Test]
        public void Toe_PivotFixed_Monotone_ShadowsDown()
        {
            Assert.AreEqual(Pivot, LookGrading.Toe(Pivot, S, P, Pivot), 1e-5f, "pivot unchanged");
            Assert.AreEqual(0f, LookGrading.Toe(0f, S, P, Pivot), 1e-7f);
            Assert.AreEqual(0.3f, LookGrading.Toe(0.3f, 0f, P, Pivot), 1e-7f, "s = 0 is the identity");
            float prev = -1f;
            for (float c = 0f; c < 3f; c += 0.005f)
            {
                float y = LookGrading.Toe(c, S, P, Pivot);
                Assert.That(y, Is.GreaterThan(prev), $"monotone at {c}");
                if (c > 0f && c < Pivot - 0.01f) Assert.That(y, Is.LessThan(c), $"below the pivot darker at {c}");
                if (c > Pivot + 0.01f) Assert.That(y, Is.GreaterThan(c), $"above the pivot brighter at {c}");
                prev = y;
            }
            // deep shadow gain tends to g (1 - s)
            float g = LookGrading.ToeGain(S, P, Pivot);
            Assert.AreEqual(g * (1f - S), LookGrading.Toe(1e-5f, S, P, Pivot) / 1e-5f, 1e-3f);
        }

        [Test]
        public void InverseToe_RoundTrip_AndClosedFormOfTheCabShader()
        {
            float g = LookGrading.ToeGain(S, P, Pivot);
            foreach (float c in new[] { 0.0005f, 0.004f, 0.02f, 0.1f, 0.3f, 0.6f, 1.2f })
            {
                float y = LookGrading.Toe(c, S, P, Pivot);
                Assert.AreEqual(c, LookGrading.InverseToe(y, S, P, Pivot), 1e-4f + c * 1e-3f, $"bisection at {c}");
                // KamionCabToeInverse (KamionToeParity.hlsl): root of g c^2 + (g (1 - s) p - y) c - y p = 0
                float b = y - g * (1f - S) * P;
                float inv = (b + Mathf.Sqrt(b * b + 4f * g * P * y)) / (2f * g);
                Assert.AreEqual(c, inv, 1e-5f + c * 1e-4f, $"closed form at {c}");
            }
        }

        [Test]
        public void OvercastPreset_IsOwnerVariant3_ClearHasNoToe()
        {
            var over = LightingPreset.CreateOvercast();
            var clear = LightingPreset.CreateClear();
            try
            {
                Assert.AreEqual(0.9f, over.lookToe, 1e-6f);
                Assert.AreEqual(0.4f, over.lookToeP, 1e-6f);
                Assert.AreEqual(0.6f, over.lookTonePivot, 1e-6f);
                Assert.AreEqual(-0.2f, over.exposureCompensation, 1e-6f);
                Assert.AreEqual(0f, over.wetness, 1e-6f, "wetness stays off (ADR 0080: failed the self-review)");
                Assert.AreEqual(0f, clear.lookToe, 1e-6f);
                Assert.AreEqual(0f, clear.exposureCompensation, 1e-6f);
                // master curve with the toe: still monotone, black floor kept, sky clips
                var c = new AnimationCurve(LookGrading.MasterCurveKeys(over.lookBlackLevel, over.lookWhiteClip, over.lookToe, over.lookToeP, over.lookTonePivot));
                Assert.That(LookGrading.Display(c, 0f), Is.InRange(0.005f, 0.02f));
                Assert.That(LookGrading.Display(c, over.lookWhiteClip + 0.1f), Is.GreaterThan(0.985f));
                float prev = -1f;
                for (float x = 0f; x < 3f; x += 0.01f)
                {
                    float d = LookGrading.Display(c, x);
                    Assert.That(d, Is.GreaterThanOrEqualTo(prev - 1e-4f), $"monotone at {x}");
                    prev = d;
                }
            }
            finally { Object.DestroyImmediate(over); Object.DestroyImmediate(clear); }
        }

        [Test]
        public void FogTau_UniformLimit_LayerThickerNearGround_ContinuousAcrossLevelRays()
        {
            const float beta = 4e-4f, a = 1.6f, h = 60f;
            // no layer: Beer-Lambert of the uniform fog
            Assert.AreEqual(beta * 500f, WorldAtmosphere.FogTau(beta, 0f, h, 0f, 2f, 30f, 500f), 1e-7f);
            // level ray at the layer base: (1 + a) x uniform
            Assert.AreEqual(beta * 500f * (1f + a), WorldAtmosphere.FogTau(beta, a, h, 0f, 0f, 0f, 500f), 1e-6f);
            // higher ray = thinner haze; far above the layer -> uniform
            float low = WorldAtmosphere.FogTau(beta, a, h, 0f, 2f, 2f, 500f), high = WorldAtmosphere.FogTau(beta, a, h, 0f, 200f, 200f, 500f);
            Assert.That(low, Is.GreaterThan(high));
            Assert.AreEqual(beta * 500f, WorldAtmosphere.FogTau(beta, a, h, 0f, 2000f, 2000f, 500f), beta * 500f * 1e-3f);
            // the level-ray branch (|dh| <= 0.02) joins the general one
            float below = WorldAtmosphere.FogTau(beta, a, h, 0f, 2f, 2f + 0.019f * h, 500f), above = WorldAtmosphere.FogTau(beta, a, h, 0f, 2f, 2f + 0.021f * h, 500f);
            Assert.AreEqual(below, above, below * 0.02f);
            Assert.AreEqual(0f, WorldAtmosphere.FogTau(beta, a, h, 0f, 2f, 2f, -5f), 0f, "negative depth clamps");
        }
    }
}
