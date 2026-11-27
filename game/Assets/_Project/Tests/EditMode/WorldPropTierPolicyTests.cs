using Game.Rendering;
using Game.World;
using NUnit.Framework;

namespace Game.Tests
{
    public sealed class WorldPropTierPolicyTests
    {
        [TestCase(PcTier.Low, "car_hatch_v2", 150f, 0.8f, true)]
        [TestCase(PcTier.Low, "van_delivery", 150f, 0.8f, true)]
        [TestCase(PcTier.Low, "tractor_yard", 150f, 1f, false)]
        [TestCase(PcTier.Low, "trailer_box", 150f, 1f, false)]
        [TestCase(PcTier.Low, "contact_a1b2c3", 150f, 1f, false)]
        [TestCase(PcTier.Low, "fab_elderberry", 50f, 1f, true)]
        [TestCase(PcTier.Medium, "car_hatch_v2", 225f, 0.9f, false)]
        [TestCase(PcTier.Medium, "van_delivery", 225f, 0.9f, false)]
        [TestCase(PcTier.Medium, "tractor_yard", 225f, 1f, false)]
        [TestCase(PcTier.Medium, "trailer_box", 225f, 1f, false)]
        [TestCase(PcTier.Medium, "contact_a1b2c3", 225f, 1f, false)]
        [TestCase(PcTier.Medium, "fab_elderberry", 70f, 1f, false)]
        public void SelectedPrefixesHaveTierSpecificRules(PcTier tier, string prototype, float cull, float lodScale, bool noShadow)
        {
            var rule = WorldPropTierPolicy.For(tier, prototype);
            Assert.That(rule.CullM, Is.EqualTo(cull));
            Assert.That(rule.CullLimit(0.5f), Is.EqualTo(cull * 0.5f));
            Assert.That(rule.LodScale, Is.EqualTo(lodScale));
            Assert.That(rule.SuppressShadows, Is.EqualTo(noShadow));
        }

        [TestCase(PcTier.High, "car_hatch_v2")]
        [TestCase(PcTier.Ultra, "fab_elderberry")]
        [TestCase(PcTier.Low, "tree_alder")]
        [TestCase(PcTier.Low, "sign_B_20")]
        [TestCase(PcTier.Low, "propcontact_a1b2c3")]
        [TestCase(PcTier.Low, "bus_shelter_black")]
        [TestCase(PcTier.Medium, "landmark_depot")]
        [TestCase(PcTier.Medium, "lamp_led")]
        [TestCase(PcTier.Medium, "carpet")]
        public void OtherPrototypesOrTiersUseBakedPolicy(PcTier tier, string prototype)
        {
            var rule = WorldPropTierPolicy.For(tier, prototype);
            Assert.That(rule.CullLimit(1f), Is.EqualTo(float.PositiveInfinity));
            Assert.That(rule.LodScale, Is.EqualTo(1f));
            Assert.That(rule.SuppressShadows, Is.False);
        }

        [TestCase(true, "low", true)]
        [TestCase(true, "Medium", true)]
        [TestCase(true, "High", false)]
        [TestCase(true, "Ultra", false)]
        [TestCase(true, null, false)]
        [TestCase(false, "Low", false)]
        [TestCase(false, "Medium", false)]
        public void OnlyAppliedPcLowOrMediumEnablesRules(bool pcEnabled, string tierName, bool expected) =>
            Assert.That(WorldPropTierPolicy.TryGetTier(pcEnabled, tierName, out _), Is.EqualTo(expected));

        [Test]
        public void LowCarKeepsNearLodAndContactEndsAtSameDistance()
        {
            var car = WorldPropTierPolicy.For(PcTier.Low, "car_hatch_v2");
            var contact = WorldPropTierPolicy.For(PcTier.Low, "contact_a1b2c3");
            float[] carEnds = { 25f, 85f, WorldInstances.VehicleCullM };
            float[] contactEnds = { WorldInstances.VehicleCullM };
            float cullScale = PcTierTable.Get(PcTier.Low).vehicleCullM / WorldInstances.VehicleCullM;
            float carCap = car.CullLimit(1f), contactCap = contact.CullLimit(1f);
            int CarLod(float distance, float bias) =>
                WorldInstances.LodAt(carEnds, distance, bias * car.LodScale, cullScale, WorldInstances.VehicleLod0MinM, carCap);

            Assert.That(CarLod(15.9f, 0.5f), Is.Zero);
            Assert.That(CarLod(21f, 1f), Is.EqualTo(1));
            Assert.That(CarLod(69f, 1f), Is.EqualTo(2));
            Assert.That(CarLod(149.9f, 1f), Is.EqualTo(2));
            Assert.That(WorldInstances.LodAt(contactEnds, 149.9f, 1f, cullScale, cullCap: contactCap), Is.Zero);
            Assert.That(CarLod(150f, 1f), Is.EqualTo(-1));
            Assert.That(CarLod(150f, 10f), Is.EqualTo(-1));
            Assert.That(WorldInstances.LodAt(contactEnds, 150f, 1f, cullScale, cullCap: contactCap), Is.EqualTo(-1));
        }

        [Test]
        public void CapCannotExtendBakedCullForExtraViews()
        {
            var rule = WorldPropTierPolicy.For(PcTier.Low, "fab_elderberry");
            float[] ends = { 12f, 30f, 65f };
            Assert.That(WorldInstances.LodAt(ends, 40f, 0.5f, 0.5f, cullCap: rule.CullLimit(1f)), Is.EqualTo(-1));
        }
    }
}
