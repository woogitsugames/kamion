using System.Collections.Generic;
using Game.Rendering;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// ADR 0241 (B-113): the GPU A/B launch switches parse, are off unless given (a launch without them leaves every
    /// tier and every shared A/B flag exactly as shipped) and reset when the arguments go away.
    /// </summary>
    public class GpuAbOverridesTests
    {
        static System.Func<string, string> Args(params string[] kv)
        {
            var d = new Dictionary<string, string>();
            for (int i = 0; i + 1 < kv.Length; i += 2) d[kv[i]] = kv[i + 1];
            return k => d.TryGetValue(k, out var v) ? v : null;
        }

        [TearDown]
        public void Reset() => RenderOverrides.Parse(_ => null);

        [Test]
        public void NoArguments_NothingIsOverridden()
        {
            string log = RenderOverrides.Parse(_ => null);
            Assert.IsNull(log, "no launch argument must give no override log line");
            Assert.IsFalse(RenderOverrides.Any);
            Assert.IsFalse(GpuAbOverrides.Any);
            Assert.IsNull(GpuAbOverrides.DepthTexture);
            Assert.IsNull(GpuAbOverrides.OpaqueTexture);
            Assert.IsNull(GpuAbOverrides.Impostors);
            Assert.IsNull(GpuAbOverrides.HlodPart);
            Assert.IsNull(GpuAbOverrides.Tag);
            Assert.IsFalse(RenderOverrides.AbImpostorOff);
            Assert.AreEqual(0, RenderOverrides.AbHlodPart);
            Assert.AreEqual("", GpuAbOverrides.Describe());
        }

        [Test]
        public void NoArguments_EveryDefaultTierIsUnchanged()
        {
            RenderOverrides.Parse(_ => null);
            foreach (var t in QualityProfile.Defaults())
                Assert.AreEqual(JsonUtility.ToJson(t), JsonUtility.ToJson(RenderOverrides.ApplyTo(t)), t.name);
        }

        [Test]
        public void NoArguments_PipelineAssetIsNotWritten()
        {
            var urp = ScriptableObject.CreateInstance<UniversalRenderPipelineAsset>();
            try
            {
                RenderOverrides.Parse(_ => null);
                foreach (bool start in new[] { false, true })
                {
                    urp.supportsCameraDepthTexture = start;
                    urp.supportsCameraOpaqueTexture = start;
                    GpuAbOverrides.ApplyPipeline(urp);
                    Assert.AreEqual(start, urp.supportsCameraDepthTexture);
                    Assert.AreEqual(start, urp.supportsCameraOpaqueTexture);
                }
            }
            finally { Object.DestroyImmediate(urp); }
        }

        [Test]
        public void TagAlone_IsLoggedButChangesNothing()
        {
            RenderOverrides.Parse(Args(GpuAbOverrides.TagKey, "baseline"));
            Assert.AreEqual("baseline", GpuAbOverrides.Tag);
            Assert.IsFalse(GpuAbOverrides.Any);
            Assert.IsFalse(RenderOverrides.Any, "the variant label must not switch the override path on");
            StringAssert.Contains("abtag=baseline", GpuAbOverrides.Describe());
        }

        [TestCase("1", true)]
        [TestCase("true", true)]
        [TestCase("on", true)]
        [TestCase("0", false)]
        [TestCase("off", false)]
        public void DepthAndOpaqueTexture_Parse(string value, bool expected)
        {
            string log = RenderOverrides.Parse(Args(GpuAbOverrides.DepthTextureKey, value, GpuAbOverrides.OpaqueTextureKey, value));
            Assert.AreEqual(expected, GpuAbOverrides.DepthTexture);
            Assert.AreEqual(expected, GpuAbOverrides.OpaqueTexture);
            Assert.IsTrue(RenderOverrides.Any);
            StringAssert.Contains("depthtex=" + expected, log);
            StringAssert.Contains("opaquetex=" + expected, log);
        }

        [Test]
        public void DepthAndOpaqueTexture_AreWrittenToThePipelineAsset_OnlyTheGivenOne()
        {
            var urp = ScriptableObject.CreateInstance<UniversalRenderPipelineAsset>();
            try
            {
                urp.supportsCameraDepthTexture = false;
                urp.supportsCameraOpaqueTexture = false;
                RenderOverrides.Parse(Args(GpuAbOverrides.DepthTextureKey, "1"));
                GpuAbOverrides.ApplyPipeline(urp);
                Assert.IsTrue(urp.supportsCameraDepthTexture);
                Assert.IsFalse(urp.supportsCameraOpaqueTexture);
                RenderOverrides.Parse(Args(GpuAbOverrides.OpaqueTextureKey, "1", GpuAbOverrides.DepthTextureKey, "0"));
                GpuAbOverrides.ApplyPipeline(urp);
                Assert.IsFalse(urp.supportsCameraDepthTexture);
                Assert.IsTrue(urp.supportsCameraOpaqueTexture);
            }
            finally { Object.DestroyImmediate(urp); }
        }

        [Test]
        public void Impostors_Off_SetsTheWorldInstancesFlag_AndResets()
        {
            RenderOverrides.Parse(Args(GpuAbOverrides.ImpostorsKey, "0"));
            Assert.AreEqual(false, GpuAbOverrides.Impostors);
            Assert.IsTrue(RenderOverrides.AbImpostorOff);
            Assert.IsTrue(RenderOverrides.Any);
            RenderOverrides.Parse(Args(GpuAbOverrides.ImpostorsKey, "1"));
            Assert.IsFalse(RenderOverrides.AbImpostorOff);
            RenderOverrides.Parse(Args(GpuAbOverrides.ImpostorsKey, "0"));
            RenderOverrides.Parse(_ => null);
            Assert.IsFalse(RenderOverrides.AbImpostorOff, "flag must return to the shipping state");
        }

        [TestCase("1", 1)]
        [TestCase("2", 2)]
        public void HlodPart_Parses_AndResets(string value, int expected)
        {
            RenderOverrides.Parse(Args(GpuAbOverrides.HlodPartKey, value));
            Assert.AreEqual(expected, GpuAbOverrides.HlodPart);
            Assert.AreEqual(expected, RenderOverrides.AbHlodPart);
            RenderOverrides.Parse(_ => null);
            Assert.AreEqual(0, RenderOverrides.AbHlodPart);
        }

        [TestCase("0")]
        [TestCase("3")]
        [TestCase("-1")]
        [TestCase("canopy")]
        public void HlodPart_OutOfRange_IsIgnored(string value)
        {
            RenderOverrides.Parse(Args(GpuAbOverrides.HlodPartKey, value));
            Assert.IsNull(GpuAbOverrides.HlodPart);
            Assert.AreEqual(0, RenderOverrides.AbHlodPart);
            Assert.IsFalse(GpuAbOverrides.Any);
        }

        [Test]
        public void WithoutTheseKeys_SharedAbFlagsSetElsewhereAreNotTouched()
        {
            // rq_ab (ExtraViewCostMonitor) owns the flags when the ADR 0241 keys are absent.
            RenderOverrides.Parse(_ => null);
            RenderOverrides.AbImpostorOff = true;
            RenderOverrides.AbHlodPart = 2;
            try
            {
                RenderOverrides.Parse(Args("rq_scale", "0.7"));
                Assert.IsTrue(RenderOverrides.AbImpostorOff);
                Assert.AreEqual(2, RenderOverrides.AbHlodPart);
            }
            finally { RenderOverrides.AbImpostorOff = false; RenderOverrides.AbHlodPart = 0; }
        }

        /// <summary>The catalogue variants built from switches that existed before ADR 0241 (tools/perf/gpu-ab-variants.json).</summary>
        [Test]
        public void ExistingSwitches_UsedByTheCatalogue_ChangeOnlyTheirField()
        {
            var low = QualityProfile.Defaults()[0];
            RenderOverrides.Parse(Args("rq_scale", "0.7", "rq_msaa", "1", "rq_shadow", "0", "rq_post", "1", "rq_lod", "0.3",
                                       "rq_thin", "45", "rq_cull", "300", "rq_hlod", "50"));
            var t = RenderOverrides.ApplyTo(low);
            Assert.AreEqual(0.7f, t.renderScale, 1e-6f);
            Assert.AreEqual(1, t.msaa);
            Assert.AreEqual(0f, t.shadowDistance);
            Assert.IsTrue(t.postProcessing);
            Assert.AreEqual(0.3f, t.lodBias, 1e-6f);
            Assert.AreEqual(45f, t.treeThinStartM);
            Assert.AreEqual(300f, t.treeCullM);
            Assert.AreEqual(50f, t.forestHlodM);
            // back to the tier: only those fields differed
            t.renderScale = low.renderScale; t.msaa = low.msaa; t.shadowDistance = low.shadowDistance; t.postProcessing = low.postProcessing;
            t.lodBias = low.lodBias; t.treeThinStartM = low.treeThinStartM; t.treeCullM = low.treeCullM; t.forestHlodM = low.forestHlodM;
            Assert.AreEqual(JsonUtility.ToJson(low), JsonUtility.ToJson(t));
        }
    }
}
