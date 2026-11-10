using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    public class FabLegacyStorageTests
    {
        static int[] Order(long[] cells, bool[] forests, int[] prototypes, bool[] fab)
        {
            var importer = Type.GetType("Game.World.Import.InstanceImporter, Game.World.Import.Editor", true);
            var method = importer.GetMethod("LegacyStorageOrder", BindingFlags.Public | BindingFlags.Static);
            Assert.That(method, Is.Not.Null);
            return (int[])method.Invoke(null, new object[] { cells, forests, prototypes, fab });
        }

        [Test]
        public void FabCellsAreDisjointEvenForActualNegativeBoundaryGridKeys()
        {
            var importer = Type.GetType("Game.World.Import.InstanceImporter, Game.World.Import.Editor", true);
            var method = importer.GetMethod("DetailCellKey", BindingFlags.Public | BindingFlags.Static);
            Assert.That(method, Is.Not.Null);
            var legacy = new HashSet<long>();
            // Current exported region: E cells -1..32, N cells -2..32. Include
            // negative signed keys: OR-ing a reserved bit would leave those shared.
            for (long n = -2; n <= 32; n++)
                for (long e = -1; e <= 32; e++) legacy.Add((n << 20) | e);
            var details = new HashSet<long>();
            foreach (long key in legacy)
            {
                Assert.That((long)method.Invoke(null, new object[] { key, false }), Is.EqualTo(key));
                long detail = (long)method.Invoke(null, new object[] { key, true });
                Assert.That(detail, Is.Not.EqualTo(key));
                Assert.That((long)method.Invoke(null, new object[] { key, true }), Is.EqualTo(detail));
                details.Add(detail);
            }
            Assert.That(details.Count, Is.EqualTo(legacy.Count), "Two detail cells collided");
            Assert.That(details.Overlaps(legacy), Is.False, "A detail would expand a legacy cell's bounds");
        }

        [TestCase(0)]
        [TestCase(1)]
        [TestCase(2)]
        [TestCase(16)]
        [TestCase(17)]
        [TestCase(31)]
        [TestCase(64)]
        [TestCase(129)]
        [TestCase(257)]
        [TestCase(2000)]
        public void AddingFabPreservesExactLegacySortAndThinningPhase(int count)
        {
            // Equal keys deliberately exercise List.Sort's unstable partitioning.
            // Use the former importer tuple type and comparison as the oracle,
            // rather than assuming insertion order for equal-key matrices.
            var baseline = new List<(long cell, bool forest, int proto, Matrix4x4 m)>();
            var mixed = new List<(long cell, bool forest, int proto, Matrix4x4 m)>();
            var fab = new List<bool>();
            var random = new System.Random(147);
            for (int i = 0; i < count; i++)
            {
                if (i % 3 == 0)
                {
                    mixed.Add((random.Next(4), false, random.Next(5) * 2 + 1,
                        Matrix4x4.Translate(new Vector3(-100 - i, 0, 0))));
                    fab.Add(true);
                }
                var item = ((long)random.Next(4), i % 4 == 0, random.Next(5) * 2,
                    Matrix4x4.Translate(new Vector3(i + 1, 0, 0)));
                baseline.Add(item);
                mixed.Add(item);
                fab.Add(false);
            }
            baseline.Sort((a, b) => a.cell != b.cell ? a.cell.CompareTo(b.cell)
                : a.forest != b.forest ? a.forest.CompareTo(b.forest) : a.proto.CompareTo(b.proto));
            var order = Order(mixed.Select(it => it.cell).ToArray(), mixed.Select(it => it.forest).ToArray(),
                mixed.Select(it => it.proto).ToArray(), fab.ToArray());
            Assert.That(order.Length, Is.EqualTo(mixed.Count));
            CollectionAssert.AreEquivalent(Enumerable.Range(0, mixed.Count), order);
            Assert.That(order.Take(count).All(i => !fab[i]), Is.True);
            Assert.That(order.Skip(count).All(i => fab[i]), Is.True);
            var actual = order.Take(count).Select(i => mixed[i].m.m03).ToArray();
            var expected = baseline.Select(it => it.m.m03).ToArray();
            CollectionAssert.AreEqual(expected, actual, "A legacy matrix moved or equal-key order changed");
            foreach (int stride in new[] { 1, 2, 4, 8 })
                CollectionAssert.AreEqual(expected.Where((_, i) => (i & (stride - 1)) == 0),
                    actual.Where((_, i) => (i & (stride - 1)) == 0), "Forest thinning phase changed");
        }

        [Test]
        public void LegacyOnlyStorageIsExactlyTheFormerImporterOrder()
        {
            var random = new System.Random(672);
            var items = new List<(long cell, bool forest, int proto, Matrix4x4 m)>();
            for (int i = 0; i < 513; i++)
                items.Add((random.Next(7), i % 3 == 0, random.Next(6), Matrix4x4.Translate(new Vector3(i, 0, 0))));
            var old = new List<(long cell, bool forest, int proto, Matrix4x4 m)>(items);
            old.Sort((a, b) => a.cell != b.cell ? a.cell.CompareTo(b.cell)
                : a.forest != b.forest ? a.forest.CompareTo(b.forest) : a.proto.CompareTo(b.proto));
            var order = Order(items.Select(it => it.cell).ToArray(), items.Select(it => it.forest).ToArray(),
                items.Select(it => it.proto).ToArray(), new bool[items.Count]);
            CollectionAssert.AreEqual(old.Select(it => it.m.m03), order.Select(i => items[i].m.m03));
        }
    }
}
