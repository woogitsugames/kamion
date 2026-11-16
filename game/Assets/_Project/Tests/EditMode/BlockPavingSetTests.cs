using System;
using System.Reflection;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>ADR 0237: the footway surface types (red blocks, 35 cm slabs) take the block-paving look of the
    /// grey 20 x 10 blocks (element jitter, joint dirt, footway soiling) instead of the bare default.</summary>
    public class BlockPavingSetTests
    {
        static float ElementSize(string setName)
        {
            // World.Import.Editor stays outside this test asmdef (see WorldPbrTintTests): call the public API by name.
            var type = Type.GetType("Game.World.Import.WorldPbrMaterials, Game.World.Import.Editor", true);
            var method = type.GetMethod("BlockPavingElementSize", BindingFlags.Static | BindingFlags.Public,
                null, new[] { typeof(string) }, null);
            Assert.NotNull(method);
            return (float)method.Invoke(null, new object[] { setName });
        }

        [TestCase("behaton_i_grey", 0.17f)]
        [TestCase("paving_20x10_grey", 0.17f)]
        [TestCase("paving_20x10_tint", 0.17f)]
        [TestCase("sidewalk_slab_35", 0.35f)]
        public void BlockPavingSets_HaveAnElementSize(string setName, float expected)
        {
            Assert.That(ElementSize(setName), Is.EqualTo(expected).Within(1e-6f));
        }

        [TestCase("asphalt_worn")]
        [TestCase("asphalt_tint")]
        [TestCase("kerb_concrete_1m")]
        [TestCase("concrete_slab_3x1.5")]
        [TestCase(null)]
        public void OtherSets_AreNotBlockPaving(string setName)
        {
            Assert.That(ElementSize(setName), Is.EqualTo(0f));
        }
    }
}
