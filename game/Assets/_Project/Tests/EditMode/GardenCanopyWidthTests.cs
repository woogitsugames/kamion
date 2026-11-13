using System;
using System.Reflection;
using Game.World;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    public class GardenCanopyWidthTests
    {
        static Matrix4x4 Apply(Matrix4x4 source, bool highOnly, float width)
        {
            var type = Type.GetType("Game.World.Import.InstanceImporter, Game.World.Import.Editor", true);
            return (Matrix4x4)type.GetMethod("ApplyGardenCanopyWidth", BindingFlags.Public | BindingFlags.Static)
                .Invoke(null, new object[] { source, highOnly, width });
        }

        [TestCase(false, 1.35f)]
        [TestCase(true, 1f)]
        [TestCase(true, 0f)]
        [TestCase(true, -1f)]
        [TestCase(true, 1.51f)]
        [TestCase(true, float.NaN)]
        [TestCase(true, float.PositiveInfinity)]
        public void LegacyOrInvalidWidthKeepsExactMatrix(bool highOnly, float width)
        {
            var source = Matrix4x4.TRS(new Vector3(51f, 140f, -90f), Quaternion.Euler(2f, 73f, -1f), Vector3.one * 1.123f);
            Assert.That(Apply(source, highOnly, width), Is.EqualTo(source));
        }

        [Test]
        public void BroaderCrownKeepsVerticalAxisAndCompactInstanceStorage()
        {
            var source = Matrix4x4.TRS(new Vector3(51f, 140f, -90f), Quaternion.Euler(2f, 73f, -1f), Vector3.one * 1.123f);
            var changed = Apply(source, true, 1.35f);
            Assert.That(changed.GetColumn(3), Is.EqualTo(source.GetColumn(3)), "origin");
            Assert.That(changed.GetColumn(1), Is.EqualTo(source.GetColumn(1)), "height and lean");
            Assert.That(((Vector3)changed.GetColumn(0)).magnitude / ((Vector3)source.GetColumn(0)).magnitude, Is.EqualTo(1.35f).Within(1e-5f));
            Assert.That(((Vector3)changed.GetColumn(2)).magnitude / ((Vector3)source.GetColumn(2)).magnitude, Is.EqualTo(1.35f).Within(1e-5f));
            var set = ScriptableObject.CreateInstance<WorldInstanceSet>();
            try
            {
                Assert.That(set.Pack(new[] { source, changed }), Is.True, "do not expand every instance to full matrices");
                Assert.That(set.LocalPosition(1), Is.EqualTo(new Vector3(51f, 140f, -90f)));
                var roundTrip = set.LocalMatrix(1);
                for (int i = 0; i < 16; i++)
                    Assert.That(roundTrip[i], Is.EqualTo(changed[i]).Within(0.002f));
                Assert.That(WorldInstances.DrawsHighOnly(true, "Low"), Is.False);
            }
            finally { UnityEngine.Object.DestroyImmediate(set); }
        }
    }
}
