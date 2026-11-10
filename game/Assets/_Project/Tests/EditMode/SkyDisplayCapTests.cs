using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// Review r6 L4: the sky dome is compressed to the exposed value that the D23 tone curve maps to 98 % (horizon) and
    /// 87.5 % (towards the zenith), so the overcast sky on the post-processing tiers no longer clips to 254.
    /// </summary>
    public class SkyDisplayCapTests
    {
        [TestCase(0.7f), TestCase(1.0f)]
        public void InverseDisplay_RoundTrips_AndZenithCapBelowHorizonCap(float whiteClip)
        {
            var curve = new AnimationCurve(LookGrading.MasterCurveKeys(0.015f, whiteClip));
            float h = EnvironmentLighting.InverseDisplay(curve, EnvironmentLighting.SkyCapHorizonDisplay, whiteClip);
            float z = EnvironmentLighting.InverseDisplay(curve, EnvironmentLighting.SkyCapZenithDisplay, whiteClip);
            Assert.AreEqual(EnvironmentLighting.SkyCapHorizonDisplay, LookGrading.Display(curve, h), 0.003f);
            Assert.AreEqual(EnvironmentLighting.SkyCapZenithDisplay, LookGrading.Display(curve, z), 0.003f);
            Assert.That(z, Is.LessThan(h), "the cap darkens towards the zenith");
            Assert.That(h, Is.LessThan(whiteClip), "the horizon cap stays below the white clip (no 254 dome)");
        }
    }
}
