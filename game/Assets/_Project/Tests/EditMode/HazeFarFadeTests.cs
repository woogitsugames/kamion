using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>ADR 0332 (haze-s24): far-clip fade of the terrain fog (_KamionFarFade, KamionFogTau).</summary>
    public class HazeFarFadeTests
    {
        // Mirror of the shader ramp: tau += 4 * smoothstep over [x, x + 1/y].
        static float Extra(Vector4 f, float viewDepth)
        {
            float t = Mathf.Clamp01((viewDepth - f.x) * f.y);
            return 4f * t * t * (3f - 2f * t);
        }

        [Test]
        public void OffWithoutFarClip()
        {
            Assert.AreEqual(Vector4.zero, WorldAtmosphere.FarFade(0f));
            Assert.AreEqual(0f, Extra(WorldAtmosphere.FarFade(0f), 5000f), "unset uniform adds no optical depth");
        }

        [Test]
        public void RampCoversLastQuarterOfFarClip()
        {
            foreach (float far in new[] { 900f, 1500f, 3000f, 4000f })
            {
                var f = WorldAtmosphere.FarFade(far);
                Assert.AreEqual(far * 0.75f, f.x, 1e-3f, "start");
                Assert.AreEqual(far, f.x + 1f / f.y, 1e-2f, "end = far clip");
                Assert.AreEqual(0f, Extra(f, far * 0.74f), 1e-6f, "nearer terrain keeps the physical haze");
                // At the far clip the terrain is within 2 % of the horizon colour: exp(-4) = 0.018 extra transmittance.
                Assert.AreEqual(4f, Extra(f, far), 1e-4f);
            }
        }

        [Test]
        public void NearWorldUntouched()
        {
            // Lowest phone far clip 900 m: the fade starts at 675 m, past the tree cull (600 m PC Low) and the driving scene.
            Assert.Greater(WorldAtmosphere.FarFade(900f).x, 600f);
        }
    }
}
