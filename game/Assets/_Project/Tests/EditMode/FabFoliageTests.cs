using System.Reflection;
using Game.World;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    public class FabFoliageTests
    {
        [TestCase("M_fab_boxwood", true, true, true)]
        [TestCase("M_fab_elderberry_billboard", true, true, true)]
        [TestCase("M_fab_wild_grass_billboard", true, true, true)]
        [TestCase("M_fab_drainage", true, false, false)]
        [TestCase("M_fab_trash_bag_pack", false, false, false)]
        [TestCase("M_bark_birch", false, false, false)]
        public void OnlyAlphaClippedDoubleSidedFoliageUsesMobilePath(string name, bool clipped, bool doubleSided, bool expected)
        {
            var shader = Shader.Find("Universal Render Pipeline/Lit");
            Assert.That(shader, Is.Not.Null);
            var material = new Material(shader) { name = name };
            try
            {
                material.SetFloat("_Cull", doubleSided ? 0 : 2);
                if (clipped) material.EnableKeyword("_ALPHATEST_ON");
                var selector = typeof(WorldInstances).GetMethod("IsFoliage", BindingFlags.NonPublic | BindingFlags.Static);
                Assert.That(selector, Is.Not.Null);
                Assert.That((bool)selector.Invoke(null, new object[] { material }), Is.EqualTo(expected));
            }
            finally { Object.DestroyImmediate(material); }
        }
    }
}
