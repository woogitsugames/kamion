using System.Linq;
using Game.Rendering;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Game.Tests
{
    public class LightPostPolicyTests
    {
        [Test]
        public void HighRcasRestoresLegacyZeroButHonoursExplicitZeroAndOtherTiers()
        {
            var saved = RenderOverrides.FsrSharpness;
            try
            {
                RenderOverrides.FsrSharpness = null;
                foreach (var tier in QualityProfile.Defaults())
                {
                    var resolved = QualityProfileApplier.ApplyLightPolicy(tier);
                    Assert.AreEqual(tier.name == "High" ? 0.75f : tier.fsrSharpness, resolved.fsrSharpness, tier.name);
                    Assert.AreEqual(tier.renderScale, resolved.renderScale);
                    Assert.AreEqual(tier.postProcessing, resolved.postProcessing);
                }
                var high = QualityProfile.Defaults().Single(t => t.name == "High");
                foreach (float sharpness in new[] { 0f, 0.25f, 0.5f, 0.75f })
                {
                    RenderOverrides.FsrSharpness = sharpness;
                    Assert.AreEqual(sharpness,
                        QualityProfileApplier.ApplyLightPolicy(RenderOverrides.ApplyTo(high)).fsrSharpness,
                        "diagnostic zero must still disable RCAS");
                }
                RenderOverrides.FsrSharpness = null;
                high.upscalingFilter = UpscalingFilterSelection.Linear;
                Assert.AreEqual(0f, QualityProfileApplier.ApplyLightPolicy(high).fsrSharpness);
            }
            finally { RenderOverrides.FsrSharpness = saved; }
        }

        [Test]
        public void ClearShoulderPreservesAsphaltAndMidGreyAnchors()
        {
            var preset = LightingPreset.CreateClear();
            try
            {
                var before = new AnimationCurve(LookGrading.MasterCurveKeys(preset.lookBlackLevel, 0.7f));
                var after = new AnimationCurve(LookGrading.MasterCurveKeys(preset.lookBlackLevel, preset.lookWhiteClip));
                foreach (float scene in new[] { 0.01f, 0.03f, 0.05f, 0.08f, 0.12f, 0.18f })
                    Assert.AreEqual(LookGrading.Display(before, scene), LookGrading.Display(after, scene), 0.001f, $"scene {scene}: asphalt/mid-grey preserved");
                Assert.Less(LookGrading.Display(after, 0.8f), LookGrading.Display(before, 0.8f), "bright wall compresses without changing exposure");
                Assert.AreEqual(0f, preset.exposureCompensation);
            }
            finally { Object.DestroyImmediate(preset); }
        }

        [TestCase("Low", 0f), TestCase("Medium", 0.08f), TestCase("High", 0.08f), TestCase("Ultra", 0f)]
        public void GlassReceiverScopeAndWorkingValueBound(string name, float expected)
        {
            var tier = QualityProfile.Defaults().Single(t => t.name == name);
            Assert.AreEqual(expected, QualityProfileApplier.ArchitecturalGlassBias(tier));
            Assert.AreEqual(0f, QualityProfileApplier.ArchitecturalGlassBias(tier, -1f));
            Assert.AreEqual(0.08f, QualityProfileApplier.ArchitecturalGlassBias(tier, 1f));
        }

        [TestCase("Low"), TestCase("Medium"), TestCase("High")]
        public void SerializedPolicyAndActualPipelineAgreeWithoutOverrides(string name)
        {
            var profile = QualityProfile.Load();
            Assert.IsNotNull(profile);
            Assert.IsTrue(profile.TryGet(name, out var tier));
            var factory = QualityProfile.Defaults().Single(t => t.name == name);
            var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>($"Assets/_Project/Rendering/Settings/URP_{name}.asset");
            Assert.IsNotNull(pipeline);
            Assert.AreEqual(factory.shadowDepthBias, tier.shadowDepthBias);
            Assert.AreEqual(factory.shadowNormalBias, tier.shadowNormalBias);
            Assert.AreEqual(tier.shadowDepthBias, pipeline.shadowDepthBias);
            Assert.AreEqual(tier.shadowNormalBias, pipeline.shadowNormalBias);
            Assert.AreEqual(tier.shadowResolution, pipeline.mainLightShadowmapResolution);
            Assert.AreEqual(tier.shadowCascades, pipeline.shadowCascadeCount);
            if (name == "High")
            {
                Assert.IsTrue(pipeline.fsrOverrideSharpness, "zero must not select URP's default sharpening");
                Assert.AreEqual(0f, pipeline.fsrSharpness);
                Assert.AreEqual(new Vector2(tier.cascade4Split.x, tier.cascade4Split.y), pipeline.cascade3Split);
            }
            if (name == "Low")
            {
                Assert.AreEqual(35f, pipeline.shadowDistance);
                Assert.AreEqual(1024, pipeline.mainLightShadowmapResolution);
                Assert.AreEqual(1, pipeline.shadowCascadeCount);
                Assert.AreEqual(1f, pipeline.shadowDepthBias);
                Assert.AreEqual(1f, pipeline.shadowNormalBias);
                Assert.IsFalse(tier.postProcessing);
            }
        }

        [Test]
        public void ImportedGlassSemanticIsRestrictedAndStillReceivesShadows()
        {
            const string directory = "Assets/_Generated/World/bialystok-industrial-c/Materials";
            var flagged = AssetDatabase.FindAssets("t:Material", new[] { directory })
                .Select(AssetDatabase.GUIDToAssetPath).Select(AssetDatabase.LoadAssetAtPath<Material>)
                .Where(m => m != null && m.HasProperty("_ArchitecturalGlass") && m.GetFloat("_ArchitecturalGlass") > 0.5f).ToArray();
            Assert.AreEqual(1, flagged.Length, "canonical importer must flag only the actual hero pane material");
            Assert.AreEqual("M_kp_glass_block", flagged[0].name);
            Assert.AreEqual("Kamion/World Surface", flagged[0].shader.name);
            Assert.AreEqual(1f, flagged[0].GetFloat("_ReceiveShadows"), "frame/structure shadows remain enabled");
        }
    }
}
