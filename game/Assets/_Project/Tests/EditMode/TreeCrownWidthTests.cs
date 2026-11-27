using System;
using System.Reflection;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>ADR 0352: per-instance crown width of the library trees (InstanceImporter.TreeCrownWidth / ApplyTreeCrownWidth).</summary>
    public class TreeCrownWidthTests
    {
        static readonly Type Importer = Type.GetType("Game.World.Import.InstanceImporter, Game.World.Import.Editor", true);

        static float Width(float e, float n) =>
            (float)Importer.GetMethod("TreeCrownWidth", BindingFlags.Public | BindingFlags.Static).Invoke(null, new object[] { e, n });

        static Matrix4x4 Apply(Matrix4x4 m, float w) =>
            (Matrix4x4)Importer.GetMethod("ApplyTreeCrownWidth", BindingFlags.Public | BindingFlags.Static).Invoke(null, new object[] { m, w });

        [Test]
        public void WidthIsDeterministicNeverWiderThanTheModelAndSpread()
        {
            float min = 2f, max = 0f, sum = 0f;
            int count = 0;
            for (int i = 0; i < 40; i++)
                for (int j = 0; j < 40; j++)
                {
                    float e = -900f + i * 46.13f, n = -950f + j * 47.71f;
                    float w = Width(e, n);
                    Assert.That(w, Is.EqualTo(Width(e, n)), "same position, same width");
                    Assert.That(w, Is.InRange(0.84f, 1f), "ADR 0347 clearance is measured on the unscaled mesh");
                    min = Mathf.Min(min, w); max = Mathf.Max(max, w); sum += w; count++;
                }
            Assert.That(min, Is.LessThan(0.86f));
            Assert.That(max, Is.GreaterThan(0.98f));
            Assert.That(sum / count, Is.EqualTo(0.92f).Within(0.01f), "uniform over the range");
            // neighbours of one row (3 m apart) do not share a width
            Assert.That(Mathf.Abs(Width(100f, 200f) - Width(103f, 200f)), Is.GreaterThan(1e-4f));
        }

        [Test]
        public void NarrowerCrownKeepsHeightOriginLeanAndYaw()
        {
            var source = Matrix4x4.TRS(new Vector3(51f, 140f, -90f), Quaternion.Euler(2f, 73f, -1f), Vector3.one * 1.123f);
            var changed = Apply(source, 0.87f);
            Assert.That(changed.GetColumn(3), Is.EqualTo(source.GetColumn(3)), "origin");
            Assert.That(changed.GetColumn(1), Is.EqualTo(source.GetColumn(1)), "height and lean");
            Assert.That(((Vector3)changed.GetColumn(0)).magnitude / ((Vector3)source.GetColumn(0)).magnitude, Is.EqualTo(0.87f).Within(1e-5f));
            Assert.That(((Vector3)changed.GetColumn(2)).magnitude / ((Vector3)source.GetColumn(2)).magnitude, Is.EqualTo(0.87f).Within(1e-5f));
            Assert.That(Vector3.Angle(changed.GetColumn(0), source.GetColumn(0)), Is.LessThan(1e-3f), "yaw");
        }

        [TestCase(1f)]
        [TestCase(1.2f)]
        [TestCase(0.3f)]
        [TestCase(float.NaN)]
        public void OutOfRangeWidthKeepsExactMatrix(float width)
        {
            var source = Matrix4x4.TRS(new Vector3(5f, 1f, -9f), Quaternion.Euler(0f, 20f, 0f), Vector3.one * 0.8f);
            Assert.That(Apply(source, width), Is.EqualTo(source));
        }
    }
}
