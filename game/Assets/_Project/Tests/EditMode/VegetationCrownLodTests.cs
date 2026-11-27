using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using Game.Rendering;
using Game.World;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>crown-lod-s24 (critic build #10 TOP 3): tree card distance on High, LOD1 -> impostor cross-fade, leaf fill.</summary>
    public class VegetationCrownLodTests
    {
        static string ReadShader() =>
            File.ReadAllText(Path.Combine(Application.dataPath, "_Project/Rendering/Shaders/Vegetation.shader"));

        // Cross-fade only for tree prototypes whose last LOD is an impostor.
        [TestCase("tree_maple_0", 3, "M_impostor_tree_maple_0", 60f)]
        [TestCase("tree_shrub_0", 3, "M_impostor_tree_shrub_0", 40f)]
        [TestCase("tree_floor_0", 2, "M_leaves_floor", 0f)]
        [TestCase("tree_maple_0", 3, "M_bark_maple", 0f)]
        [TestCase("lamp_a", 3, "M_impostor_x", 0f)]
        public void FadeEndOnlyForImpostorTrees(string name, int lods, string lastMat, float expected)
        {
            float[] ends = name.StartsWith("tree_shrub") ? new[] { 12f, 40f, 300f } : new[] { 20f, 60f, 1000f };
            Assert.That(WorldInstances.FadeEndOf(name, ends, lods, lastMat), Is.EqualTo(expected));
        }

        [Test]
        public void FadeEndNeedsAllLodEnds()
        {
            Assert.That(WorldInstances.FadeEndOf("tree_maple_0", new[] { 20f, 60f }, 3, "M_impostor_tree_maple_0"), Is.EqualTo(0f));
            Assert.That(WorldInstances.FadeEndOf(null, new[] { 20f, 60f, 1000f }, 3, "M_impostor_x"), Is.EqualTo(0f));
        }

        [Test]
        public void HighKeepsCardsToNinetyMetres()
        {
            // The "melting blob" of build #10 was an impostor at 60-90 m: High keeps the leaf cards to 90 m (60 m x 1.5).
            var high = PcTierTable.Defaults()[(int)PcTier.High];
            Assert.That(Mathf.Min(high.lodBias, high.treeCardLodScale) * 60f, Is.GreaterThanOrEqualTo(90f));
            Assert.That(high.treeLodFade, Is.True);
            Assert.That(PcTierTable.Defaults()[(int)PcTier.Low].treeLodFade, Is.False);   // GTX 660 class: no double draw
        }

        [Test]
        public void TierTableStaysValid() => Assert.That(PcTierTable.Validate(PcTierTable.Defaults()), Is.Empty);

        [Test]
        public void FadeBandAndFillAreModest()
        {
            Assert.That(WorldInstances.TreeFadeBand, Is.InRange(0.1f, 0.35f));
            Assert.That(WorldInstances.LeafMipFill, Is.InRange(0f, 0.35f));   // cutoff 0.5 -> >= 0.15 at most
        }

        [Test]
        public void ShaderHasFadeAndFill()
        {
            Assert.That(Shader.Find("Kamion/Vegetation"), Is.Not.Null);
            string src = ReadShader();
            StringAssert.Contains("_KamionTreeFade", src);
            StringAssert.Contains("_LodFadeEndM", src);
            StringAssert.Contains("VegCutoffFill", src);
        }

        [Test]
        public void ShaderAlphaClippingUsesSharedCoverage()
        {
            string src = Regex.Replace(ReadShader(), @"/\*[\s\S]*?\*/|//[^\r\n]*", "");
            const string sharedClip = @"\bVegClipCoverage\s*\(";
            const string clip = @"\bclip\s*\(";
            var coverage = Regex.Match(src, @"\bhalf\s+VegClipCoverage\s*\([^)]*\)\s*\{[\s\S]*?^ {8}\}",
                RegexOptions.Multiline);
            Assert.That(coverage.Success, Is.True);
            StringAssert.Contains("VegCutoffFill(", coverage.Value);
            StringAssert.Contains("CoverageAlpha(", coverage.Value);
            Assert.That(coverage.Value, Does.Match(clip));
            Assert.That(Regex.Matches(src, clip).Count, Is.EqualTo(Regex.Matches(coverage.Value, clip).Count));

            var checkedPasses = new List<string>();
            foreach (Match pass in Regex.Matches(src, @"\bPass\s*\{\s*Name\s*""([^""]+)""([\s\S]*?)HLSLPROGRAM([\s\S]*?)ENDHLSL"))
            {
                string name = pass.Groups[1].Value;
                string program = pass.Groups[3].Value;
                Assert.That(program, Does.Not.Match(clip), name);
                if (!Regex.IsMatch(program, sharedClip)) continue;

                bool shadow = name == "ShadowCaster";
                Assert.That(program, Does.Match(sharedClip + @"[^;]+,\s*" + (shadow ? "false" : "true") + @"\s*\)"), name);
                if (!shadow)
                {
                    Assert.That(pass.Groups[2].Value, Does.Match(@"AlphaToMask\s+\[_AlphaToMask\]"), name);
                    Assert.That(program, Does.Match(@"return\s+half4\s*\([^;]+,\s*alpha\s*\)"), name);
                }
                checkedPasses.Add(name);
            }
            foreach (string name in new[] { "VegetationDepth", "ForwardLit", "ShadowCaster", "DepthOnly" })
                CollectionAssert.Contains(checkedPasses, name);
        }
    }
}
