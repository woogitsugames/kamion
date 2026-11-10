using Game.World;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>Compact instance TRS (ADR 0025): round trip within 1 mm, fallback to full matrices for shear / mirror.</summary>
    public class WorldInstancePackTests
    {
        [Test]
        public void Pack_RoundTripsYawStretchAndTilt()
        {
            var mats = new[]
            {
                Matrix4x4.TRS(new Vector3(1234.567f, 131.25f, -987.125f), Quaternion.Euler(0f, 37.3f, 0f), new Vector3(1f, 1.37f, 1f)),
                Matrix4x4.TRS(new Vector3(-12.5f, 140f, 2047.75f), Quaternion.Euler(3.1f, 211f, -2.4f), Vector3.one * 14.2f),
                Matrix4x4.identity,
            };
            var set = ScriptableObject.CreateInstance<WorldInstanceSet>();
            Assert.IsTrue(set.Pack(mats));
            Assert.AreEqual(3, set.Count);
            Assert.AreEqual(0, set.matrices.Length);
            for (int i = 0; i < mats.Length; i++)
            {
                var d = set.LocalMatrix(i);
                Assert.AreEqual(mats[i].GetColumn(3), d.GetColumn(3), "translation is stored exactly");
                for (int c = 0; c < 3; c++)
                    Assert.Less(((Vector3)(d.GetColumn(c) - mats[i].GetColumn(c))).magnitude, 1e-3f * Mathf.Max(1f, ((Vector3)mats[i].GetColumn(c)).magnitude));
                Assert.AreEqual(new Vector3(mats[i].m03, mats[i].m13, mats[i].m23), set.LocalPosition(i));
            }
            Object.DestroyImmediate(set);
        }

        [Test]
        public void Pack_KeepsFullMatricesForMirror()
        {
            var mats = new[] { Matrix4x4.TRS(Vector3.one, Quaternion.identity, new Vector3(-1f, 1f, 1f)) };
            var set = ScriptableObject.CreateInstance<WorldInstanceSet>();
            Assert.IsFalse(set.Pack(mats));
            Assert.AreEqual(1, set.Count);
            Assert.AreEqual(mats[0], set.LocalMatrix(0));
            Object.DestroyImmediate(set);
        }
    }
}
