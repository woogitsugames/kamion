using System.Linq;
using Game.Rendering;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// ADR 0240 (B-088): thin world casters cast no main-light shadow on Low, the Low tier uses the reviewed 0.4 / 0.3
    /// shadow bias, map / cascades / distance per tier stay where the budgets put them. Bounding boxes below are the LOD0
    /// boxes of street_props.glb measured by tools/rendering/thin_shadow_audit.py (x, y up, z; metres).
    /// </summary>
    public class ThinShadowCasterTests
    {
        // Thin by category: mean ground-shadow width 0.03-0.23 m, < 80 % of it at least two Low texels wide.
        [TestCase("lamp_10m", 0.50f, 10.12f, 2.41f)]
        [TestCase("lamp_arc_9m_double", 0.56f, 9.15f, 5.84f)]
        [TestCase("lamp_old_concrete_9m", 0.34f, 9.41f, 2.68f)]
        [TestCase("signal_pole", 0.13f, 4.10f, 0.14f)]
        [TestCase("sign_post", 0.06f, 1.03f, 0.06f)]
        [TestCase("sign_g3_G302fbfd35", 0.90f, 2.86f, 0.10f)]
        [TestCase("sign_gantry_26_61", 26.70f, 5.90f, 0.92f)]
        [TestCase("sign_cantilever_L8_86", 8.38f, 8.65f, 0.82f)]
        [TestCase("pylon", 8.72f, 32.03f, 4.77f)]
        [TestCase("bollard", 0.12f, 1.00f, 0.12f)]
        [TestCase("bollard_rw_chain", 2.01f, 1.26f, 0.06f)]
        [TestCase("bollard_hoop", 0.96f, 1.33f, 0.06f)]
        [TestCase("railing_u12a", 2.00f, 1.15f, 0.06f)]
        [TestCase("fence_u12", 2.54f, 1.00f, 0.06f)]
        [TestCase("sliding_gate", 8.52f, 2.10f, 0.12f)]
        [TestCase("barrier_arm_raised", 6.43f, 6.93f, 0.60f)]
        [TestCase("barrier_boom", 6.16f, 0.13f, 0.10f)]
        public void ThinFamilies_DoNotCastOnLow(string proto, float x, float y, float z)
        {
            Assert.That(ThinShadowCasterPolicy.IsThin(proto, new Vector3(x, y, z)), Is.True, proto);
        }

        // Resolvable on Low (>= 90 % of the shadow two texels wide) or bodies: keep casting.
        [TestCase("signal_mast", 0.25f, 6.58f, 6.13f)]
        [TestCase("signal_head_red", 0.85f, 1.39f, 0.65f)]
        [TestCase("signal_ped_green", 0.28f, 0.56f, 0.50f)]
        [TestCase("plate_B-33_70", 0.80f, 0.80f, 0.10f)]
        [TestCase("plate_D-6", 0.60f, 0.60f, 0.10f)]
        [TestCase("board_OB_4e2b750e", 6.10f, 1.80f, 0.07f)]
        [TestCase("power_pole", 1.80f, 12.50f, 0.32f)]
        [TestCase("pylon_u5a", 0.30f, 0.90f, 0.30f)]
        [TestCase("lift_gate", 5.41f, 1.00f, 0.34f)]
        [TestCase("cantilever_gate", 10.37f, 2.30f, 0.77f)]
        [TestCase("waste_bin", 0.44f, 1.20f, 0.44f)]
        [TestCase("street_cabinet", 0.90f, 1.40f, 0.40f)]
        [TestCase("bus_shelter_5m", 5.00f, 3.75f, 2.04f)]
        [TestCase("cone", 0.40f, 0.75f, 0.40f)]
        // Bodies (illustrative sizes, not from the audit): never thin.
        [TestCase("car_sedan_grey", 1.80f, 1.45f, 4.60f)]
        [TestCase("trailer_curtain_0", 2.55f, 4.00f, 13.60f)]
        [TestCase("landmark_viaduct_a", 30f, 8f, 12f)]
        public void SolidFamilies_KeepCasting(string proto, float x, float y, float z)
        {
            Assert.That(ThinShadowCasterPolicy.IsThin(proto, new Vector3(x, y, z)), Is.False, proto);
        }

        [Test]
        public void UnknownPrototype_FallsBackToTheBoundingBox()
        {
            // A rod (two small dimensions) is thin whatever it is called; a plate or a box is not.
            Assert.That(ThinShadowCasterPolicy.IsThin("new_marker_post", new Vector3(0.08f, 1.2f, 0.08f)), Is.True);
            Assert.That(ThinShadowCasterPolicy.IsThin("new_rail", new Vector3(4f, 0.1f, 0.05f)), Is.True);
            Assert.That(ThinShadowCasterPolicy.IsThin("new_plate", new Vector3(0.9f, 0.9f, 0.05f)), Is.False);
            Assert.That(ThinShadowCasterPolicy.IsThin("new_box", new Vector3(0.6f, 0.8f, 0.4f)), Is.False);
            Assert.That(ThinShadowCasterPolicy.IsThin("new_empty", Vector3.zero), Is.False, "no bounds = no opinion");
            Assert.That(ThinShadowCasterPolicy.IsThin(null, new Vector3(1f, 1f, 1f)), Is.False);
            // Exactly at the threshold: not thin (strict <).
            float w = ThinShadowCasterPolicy.MaxRodWidthM;
            Assert.That(ThinShadowCasterPolicy.IsThin("edge", new Vector3(w, 3f, w)), Is.False);
            Assert.That(ThinShadowCasterPolicy.IsThin("edge", new Vector3(w - 0.01f, 3f, w - 0.01f)), Is.True);
        }

        [Test]
        public void RodWidth_IsTheMiddleDimension_InAnyAxisOrder()
        {
            Assert.That(ThinShadowCasterPolicy.RodWidth(new Vector3(0.1f, 5f, 0.3f)), Is.EqualTo(0.3f).Within(1e-6f));
            Assert.That(ThinShadowCasterPolicy.RodWidth(new Vector3(5f, 0.3f, 0.1f)), Is.EqualTo(0.3f).Within(1e-6f));
            Assert.That(ThinShadowCasterPolicy.RodWidth(new Vector3(0.3f, 0.1f, 5f)), Is.EqualTo(0.3f).Within(1e-6f));
            Assert.That(ThinShadowCasterPolicy.RodWidth(new Vector3(2f, 2f, 2f)), Is.EqualTo(2f).Within(1e-6f));
        }

        [Test]
        public void Trees_AreNeverThinCasters_TheyHaveTheirOwnMask()
        {
            Assert.That(ThinShadowCasterPolicy.IsThin("tree_birch_a", new Vector3(0.1f, 12f, 0.1f)), Is.False);
        }

        [TestCase("fence_galv", true)]
        [TestCase("fence_green_mesh", false)]   // ADR 0239 (FenceMeshCoverage) owns the welded mesh on every tier
        [TestCase("fence_galv_mesh", false)]
        [TestCase("fence_anthracite", true)]
        [TestCase("barrier_post", true)]
        [TestCase("chain_bollard", true)]
        [TestCase("concrete_fence", false)]
        [TestCase("barrier_housing", false)]
        [TestCase("noise_panel", false)]
        [TestCase("bridge_concrete", false)]
        [TestCase("road_asphalt", false)]
        [TestCase("", false)]
        public void ChunkMaterials_ThinFurnitureOnly(string id, bool thin)
        {
            Assert.That(ThinShadowCasterPolicy.IsThinMaterial(id), Is.EqualTo(thin), id);
        }

        [Test]
        public void Defaults_OnlyLowDropsThinCasters()
        {
            foreach (var t in QualityProfile.Defaults())
                Assert.That(t.thinCasterShadowsOff, Is.EqualTo(t.name == "Low"), t.name);
        }

        // Shadow policy per tier (ADR 0010 / 0046 / 0098 / 0240): distance m, map px, cascades, soft, depth bias, normal bias.
        [TestCase("Low", 35f, 1024, 1, false, 0.4f, 0.3f)]
        [TestCase("Medium", 60f, 1024, 2, false, 0.4f, 0.3f)]
        [TestCase("High", 100f, 2048, 3, true, 0.4f, 0.3f)]
        [TestCase("Ultra", 150f, 4096, 4, true, 0.6f, 0.6f)]
        public void Defaults_ShadowPolicyPerTier(string name, float distance, int resolution, int cascades, bool soft, float depthBias, float normalBias)
        {
            var t = QualityProfile.Defaults().Single(x => x.name == name);
            Assert.That(t.shadowDistance, Is.EqualTo(distance));
            Assert.That(t.shadowResolution, Is.EqualTo(resolution));
            Assert.That(t.shadowCascades, Is.EqualTo(cascades));
            Assert.That(t.softShadows, Is.EqualTo(soft));
            Assert.That(t.shadowDepthBias, Is.EqualTo(depthBias).Within(1e-6f));
            Assert.That(t.shadowNormalBias, Is.EqualTo(normalBias).Within(1e-6f));
        }

        [Test]
        public void Defaults_LowNormalBiasLeavesAThinArmItsShadow()
        {
            // Silhouette loss = 2 x normal bias x texel. With ~8 cm per texel (ESTIMATED) a 0.24 m signal arm keeps
            // >= 75 % of its width at 0.3 and only a third at the old 1.0.
            const float texelM = 0.078f, armM = 0.24f;
            var low = QualityProfile.Defaults().Single(x => x.name == "Low");
            Assert.That(armM - 2f * low.shadowNormalBias * texelM, Is.GreaterThanOrEqualTo(0.75f * armM));
        }

        [Test]
        public void ShippedProfile_MatchesThinCasterDefaults()
        {
            var p = QualityProfile.Load();
            Assert.That(p, Is.Not.Null, "Resources/QualityProfile missing");
            Assert.That(p.revision, Is.GreaterThanOrEqualTo(240), "profile not migrated to ADR 0240 (pwsh scripts/setup-project.ps1)");
            foreach (var d in QualityProfile.Defaults())
            {
                Assert.That(p.TryGet(d.name, out var t), Is.True, d.name);
                Assert.That(t.thinCasterShadowsOff, Is.EqualTo(d.thinCasterShadowsOff), d.name + " thinCasterShadowsOff");
                Assert.That(t.shadowDepthBias, Is.EqualTo(d.shadowDepthBias).Within(1e-6f), d.name + " shadowDepthBias");
                Assert.That(t.shadowNormalBias, Is.EqualTo(d.shadowNormalBias).Within(1e-6f), d.name + " shadowNormalBias");
            }
        }

        [Test]
        public void RqThinShadow_OverridesTheTierBothWays()
        {
            var tiers = QualityProfile.Defaults();
            var low = tiers.Single(x => x.name == "Low");
            var high = tiers.Single(x => x.name == "High");
            try
            {
                RenderOverrides.ThinShadows = true;
                Assert.That(RenderOverrides.ApplyTo(low).thinCasterShadowsOff, Is.False, "rq_thinshadow 1 on Low");
                RenderOverrides.ThinShadows = false;
                Assert.That(RenderOverrides.ApplyTo(high).thinCasterShadowsOff, Is.True, "rq_thinshadow 0 on High");
                RenderOverrides.ThinShadows = null;
                Assert.That(RenderOverrides.ApplyTo(low).thinCasterShadowsOff, Is.True, "no override = tier value");
                Assert.That(RenderOverrides.ApplyTo(high).thinCasterShadowsOff, Is.False);
            }
            finally { RenderOverrides.ThinShadows = null; }
        }
    }
}
