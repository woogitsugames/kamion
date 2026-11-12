using System;
using System.Collections.Generic;
using System.Reflection;
using Game.World;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>ADR 0132 p. 17: instance records with "tier": "high" (garden trees) are not drawn on Low.</summary>
    public class HighOnlyInstanceTests
    {
        static readonly Type Importer = Type.GetType("Game.World.Import.InstanceImporter, Game.World.Import.Editor", true);

        static T Call<T>(string name, params object[] args)
        {
            var method = Importer.GetMethod(name, BindingFlags.Public | BindingFlags.Static);
            Assert.That(method, Is.Not.Null, name);
            return (T)method.Invoke(null, args);
        }

        [Test]
        public void OnlyLowSkipsHighOnlyRuns()
        {
            Assert.That(WorldInstances.DrawsHighOnly(true, "Low"), Is.False);
            Assert.That(WorldInstances.DrawsHighOnly(true, "low"), Is.False);
            Assert.That(WorldInstances.DrawsHighOnly(true, "Medium"), Is.True);
            Assert.That(WorldInstances.DrawsHighOnly(true, "High"), Is.True);
            Assert.That(WorldInstances.DrawsHighOnly(true, "Ultra"), Is.True);
            Assert.That(WorldInstances.DrawsHighOnly(false, "Low"), Is.True, "no applied tier (edit tools) draws everything");
            Assert.That(WorldInstances.DrawsHighOnly(false, null), Is.True);
        }

        [Test]
        public void TierFieldIsReadFromTheRecord()
        {
            Assert.That(Call<bool>("IsHighOnly", "high"), Is.True);
            Assert.That(Call<bool>("IsHighOnly", "High"), Is.True);
            Assert.That(Call<bool>("IsHighOnly", new object[] { null }), Is.False, "no field = every tier");
            Assert.That(Call<bool>("IsHighOnly", "low"), Is.False);
            Assert.That(Call<bool>("IsHighOnly", 1.0), Is.False);
        }

        [Test]
        public void HighOnlyCellsAreDisjointFromLegacyAndFabCells()
        {
            var legacy = new HashSet<long>();
            for (long n = -2; n <= 32; n++)
                for (long e = -1; e <= 32; e++) legacy.Add((n << 20) | e);
            var fab = new HashSet<long>();
            var high = new HashSet<long>();
            foreach (long key in legacy)
            {
                Assert.That(Call<long>("HighOnlyCellKey", key, false), Is.EqualTo(key));
                fab.Add(Call<long>("DetailCellKey", key, true));
                high.Add(Call<long>("HighOnlyCellKey", key, true));
            }
            Assert.That(high.Count, Is.EqualTo(legacy.Count), "two high-only cells collided");
            Assert.That(high.Overlaps(legacy), Is.False, "a high-only instance would change a legacy cell");
            Assert.That(high.Overlaps(fab), Is.False, "a high-only instance would change a Fab detail cell");
        }

        [Test]
        public void HighOnlyInstancesAreStoredAfterTheLegacyMatrices()
        {
            // legacy 0, 2, 3 keep the order they have without the high-only instance 1 (forest thinning uses the absolute index)
            long[] cells = { 5, Call<long>("HighOnlyCellKey", 3L, true), 3, 4 };
            bool[] forests = { false, false, false, false };
            int[] protos = { 1, 1, 1, 1 };
            var with = Call<int[]>("LegacyStorageOrder", cells, forests, protos, new[] { false, true, false, false });
            Assert.That(with, Is.EqualTo(new[] { 2, 3, 0, 1 }));
        }

        [Test]
        public void RunFlagDefaultsToEveryTier()
        {
            Assert.That(default(WorldInstanceSet.Run).highOnly, Is.False, "sets imported before ADR 0132 p. 17 draw as before");
        }
    }
}
