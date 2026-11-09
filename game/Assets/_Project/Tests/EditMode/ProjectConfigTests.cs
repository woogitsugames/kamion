using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>Guards the Stage 0 project configuration (ADR 0006).</summary>
    public class ProjectConfigTests
    {
        [Test]
        public void QualityLevels_AreTheFourTiers()
        {
            CollectionAssert.AreEqual(QualityTiers.Names, QualitySettings.names);
        }

        [Test]
        public void EveryTier_HasItsOwnUrpAsset()
        {
            var names = QualitySettings.names;
            for (int i = 0; i < names.Length; i++)
            {
                var rp = QualitySettings.GetRenderPipelineAssetAt(i);
                Assert.IsNotNull(rp, names[i]);
                StringAssert.EndsWith(names[i], rp.name);
            }
        }

        [Test]
        public void ColorSpace_IsLinear()
        {
            Assert.AreEqual(ColorSpace.Linear, QualitySettings.activeColorSpace);
        }
    }
}
