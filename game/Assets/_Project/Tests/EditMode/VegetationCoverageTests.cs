using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>crown-lod-s24: leaf coverage snapped to whole MSAA samples (no GPU alpha-to-coverage dither pattern).</summary>
    public class VegetationCoverageTests
    {
        [Test]
        public void SnapGivesWholeSamplesOnly()
        {
            foreach (int s in new[] { 1, 2, 4, 8 })
                for (float c = 0f; c <= 1f; c += 0.01f)
                {
                    float q = VegetationCoverage.Snap(c, s) * s;
                    Assert.That(q, Is.EqualTo(Mathf.Round(q)).Within(1e-4f), $"S={s} c={c}");
                    Assert.That(Mathf.Abs(VegetationCoverage.Snap(c, s) - c), Is.LessThanOrEqualTo(0.5f / s + 1e-4f));
                }
        }

        [Test]
        public void OneSampleIsAPlainHalfAlphaTest()
        {
            Assert.That(VegetationCoverage.Snap(0.49f, 1), Is.EqualTo(0f));
            Assert.That(VegetationCoverage.Snap(0.51f, 1), Is.EqualTo(1f));
        }

        [Test]
        public void ZeroSamplesKeepsTheHardwarePath()
        {
            Assert.That(VegetationCoverage.Snap(0.37f, 0f), Is.EqualTo(0.37f));
            Assert.That(VegetationCoverage.ShaderValue(4, false), Is.EqualTo(0f));
            Assert.That(VegetationCoverage.ShaderValue(4, true), Is.EqualTo(4f));
            Assert.That(VegetationCoverage.ShaderValue(0, true), Is.EqualTo(1f));
        }

        [Test]
        public void ShaderDeclaresTheGlobal()
        {
            var sh = Shader.Find("Kamion/Vegetation");
            Assert.That(sh, Is.Not.Null);
            string src = System.IO.File.ReadAllText(System.IO.Path.Combine(Application.dataPath, "_Project/Rendering/Shaders/Vegetation.shader"));
            StringAssert.Contains("_KamionVegMsaa", src);
        }
    }
}
