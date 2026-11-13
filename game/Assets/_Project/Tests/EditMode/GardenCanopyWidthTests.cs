using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Game.World;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Game.Tests
{
    public class GardenCanopyWidthTests
    {
        [Serializable] class InstanceRows { public GardenRecord[] instances; }
        [Serializable] class GardenRecord
        {
            public string p, tier;
            public int v;
            public float e, n, z, garden_canopy_width;
        }

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

        [Test]
        public void ImportedGardenWidthMatchesEverySerializedOptInRecord()
        {
            var set = AssetDatabase.LoadAssetAtPath<WorldInstanceSet>("Assets/_Generated/World/bialystok-industrial-c/Instances.asset");
            string repo = Path.GetFullPath(Path.Combine(Application.dataPath, "../.."));
            string folder = Path.Combine(repo, "Data/raw/derived/bialystok-industrial-c/world");
            if (set == null || !Directory.Exists(folder)) Assert.Ignore("Import the generated candidate world for this integration check");
            var records = new List<GardenRecord>();
            foreach (string file in Directory.GetFiles(folder, "instances_*.json"))
                records.AddRange(JsonUtility.FromJson<InstanceRows>(File.ReadAllText(file)).instances
                    .Where(r => r.tier == "high" && r.garden_canopy_width > 0f));
            if (records.Count == 0) Assert.Ignore("Baseline has no garden width opt-in; candidate integration check requires ADR 0154 enabled");
            Assert.That(set.Compact, Is.True, "new garden shapes must keep compact storage for every instance");
            foreach (var record in records)
            {
                int prototype = Array.FindIndex(set.prototypes, p => p.name == record.p + "_" + record.v);
                Assert.That(prototype, Is.GreaterThanOrEqualTo(0), record.p);
                var expected = new Vector3(record.e, record.z - 0.15f, record.n);
                int found = -1;
                foreach (var run in set.runs.Where(r => r.highOnly && r.prototype == prototype))
                    for (int i = run.start; i < run.start + run.count; i++)
                        if ((set.LocalPosition(i) - expected).sqrMagnitude < 0.0004f) found = i;
                Assert.That(found, Is.GreaterThanOrEqualTo(0), record.p + " at " + expected);
                var matrix = set.LocalMatrix(found);
                float height = ((Vector3)matrix.GetColumn(1)).magnitude;
                Assert.That(((Vector3)matrix.GetColumn(0)).magnitude / height,
                    Is.EqualTo(record.garden_canopy_width).Within(0.003f), record.p + " native width X");
                Assert.That(((Vector3)matrix.GetColumn(2)).magnitude / height,
                    Is.EqualTo(record.garden_canopy_width).Within(0.003f), record.p + " native width Z");
            }
        }
    }
}
