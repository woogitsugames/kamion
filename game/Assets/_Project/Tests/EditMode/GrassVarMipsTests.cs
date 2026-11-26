using System;
using System.Reflection;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>bank-smear-s24 (ADR 0311 dopisek): the Var map of a grass set (B = bare-soil coverage read by the
    /// _GRASS_DETILE refill) is imported with mips; paving / asphalt Var maps (id / joint channels read at LOD 0 with a
    /// point sampler) stay without.</summary>
    public class GrassVarMipsTests
    {
        static bool GrassSoilSet(string setName)
        {
            // World.Import.Editor stays outside this test asmdef (see BlockPavingSetTests): call the public API by name.
            var type = Type.GetType("Game.World.Import.WorldPbrMaterials, Game.World.Import.Editor", true);
            var method = type.GetMethod("GrassSoilSet", BindingFlags.Static | BindingFlags.Public, null, new[] { typeof(string) }, null);
            Assert.NotNull(method);
            return (bool)method.Invoke(null, new object[] { setName });
        }

        [Test]
        public void GrassVergeSet_GetsVarMips() => Assert.IsTrue(GrassSoilSet("grass_verge"));

        [TestCase("paving_20x10_grey")]
        [TestCase("asphalt_worn")]
        [TestCase("no_such_set")]
        [TestCase(null)]
        public void OtherSets_KeepPointVar(string setName) => Assert.IsFalse(GrassSoilSet(setName));
    }
}
