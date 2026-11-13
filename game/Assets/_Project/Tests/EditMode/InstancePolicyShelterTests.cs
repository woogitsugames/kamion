using System;
using System.Reflection;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>ADR 0162: BKM shelter variants (bus_shelter_5m / _9m / _black) share the shelter LOD policy
    /// (60 / 300 m), not the generic street-furniture fallback (30 / 120 m) that culled them at 60 m on Low.
    /// Mirror of tools/worldgen/roads/build_world.py instance_ends().</summary>
    public class InstancePolicyShelterTests
    {
        static (float[] ends, int shadowMask) Policy(string proto, int lodCount)
        {
            var t = Type.GetType("Game.World.Import.InstanceImporter, Game.World.Import.Editor", true);
            var m = t.GetMethod("Policy", BindingFlags.NonPublic | BindingFlags.Static);
            Assert.IsNotNull(m, "InstanceImporter.Policy not found");
            return ((float[], int))m.Invoke(null, new object[] { proto, lodCount });
        }

        [TestCase("bus_shelter")]
        [TestCase("bus_shelter_5m")]
        [TestCase("bus_shelter_9m")]
        [TestCase("bus_shelter_black")]
        public void ShelterVariants_UseShelterLodEnds(string proto)
        {
            CollectionAssert.AreEqual(new[] { 60f, 300f }, Policy(proto, 2).ends);
        }

        [Test]
        public void GenericFurniture_KeepsFallback()
        {
            CollectionAssert.AreEqual(new[] { 30f, 120f }, Policy("bench", 2).ends);
        }
    }
}
