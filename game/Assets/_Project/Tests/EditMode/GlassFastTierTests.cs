using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// ADR 0106: the Truck Glass fast path is on for the phone tiers (Low, Medium) and off for High / Ultra, the shipped
    /// asset matches the code defaults, the applier drives the global keyword and rq_glassfast overrides it.
    /// </summary>
    public class GlassFastTierTests
    {
        [Test]
        public void Defaults_PhoneTiersFast_FlagshipFull()
        {
            foreach (var t in QualityProfile.Defaults())
                Assert.That(t.glassFast, Is.EqualTo(t.name == "Low" || t.name == "Medium"), t.name);
        }

        [Test]
        public void ShippedProfile_MatchesGlassDefaults()
        {
            var p = QualityProfile.Load();
            Assert.That(p, Is.Not.Null, "Resources/QualityProfile missing");
            Assert.That(p.revision, Is.GreaterThanOrEqualTo(106), "profile not migrated to ADR 0106");
            foreach (var d in QualityProfile.Defaults())
            {
                Assert.That(p.TryGet(d.name, out var t), Is.True, d.name);
                Assert.That(t.glassFast, Is.EqualTo(d.glassFast), d.name + " glassFast");
            }
        }

        [Test]
        public void Apply_SetsGlobalKeyword_RqOverrides()
        {
            bool was = Shader.IsKeywordEnabled(QualityProfileApplier.GlassFastKeyword);
            UnityEngine.Rendering.Universal.Tonemapping tm = null;
            try
            {
                var low = QualityProfile.Defaults()[0];
                QualityProfileApplier.Apply(low, null, null, null, ref tm);
                Assert.That(Shader.IsKeywordEnabled(QualityProfileApplier.GlassFastKeyword), Is.True, "Low");
                RenderOverrides.GlassFast = false;
                QualityProfileApplier.Apply(RenderOverrides.ApplyTo(low), null, null, null, ref tm);
                Assert.That(Shader.IsKeywordEnabled(QualityProfileApplier.GlassFastKeyword), Is.False, "rq_glassfast 0");
            }
            finally
            {
                RenderOverrides.GlassFast = null;
                if (was) Shader.EnableKeyword(QualityProfileApplier.GlassFastKeyword); else Shader.DisableKeyword(QualityProfileApplier.GlassFastKeyword);
            }
        }

    }
}
