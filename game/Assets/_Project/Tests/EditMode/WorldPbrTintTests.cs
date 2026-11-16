using Game.Editor.VisualQA;
using System;
using System.Reflection;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Tests
{
    public class WorldPbrTintTests
    {
        static void SetTint(Material material, Vector3 linear)
        {
            // The project deliberately keeps World.Import.Editor outside this
            // test asmdef. Exercise its real public API without changing asmdefs.
            var type = Type.GetType("Game.World.Import.WorldPbrMaterials, Game.World.Import.Editor", true);
            var method = type.GetMethod("SetLinearTint", BindingFlags.Static | BindingFlags.Public,
                null, new[] { typeof(Material), typeof(Vector3) }, null);
            Assert.NotNull(method);
            method.Invoke(null, new object[] { material, linear });
        }
        [TestCase(0.04f)] [TestCase(0.08f)] [TestCase(0.18f)] [TestCase(0.5f)]
        [TestCase(1f)] [TestCase(1.5f)] [TestCase(2.5f)]
        public void LinearTint_StorageRoundTripsIncludingHdr(float value)
        {
            var shader = Shader.Find("Kamion/World PBR");
            Assert.NotNull(shader);
            var material = new Material(shader);
            try
            {
                var requested = new Vector3(value, value * .8f, value * .5f);
                SetTint(material, requested);
                var decoded = material.GetColor("_Tint").linear;
                Assert.That(decoded.r, Is.EqualTo(requested.x).Within(1e-5));
                Assert.That(decoded.g, Is.EqualTo(requested.y).Within(1e-5));
                Assert.That(decoded.b, Is.EqualTo(requested.z).Within(1e-5));
                Assert.That(material.GetColor("_Tint").a, Is.EqualTo(1f));
            }
            finally { UnityEngine.Object.DestroyImmediate(material); }
        }

        [TestCase(0.04f)] [TestCase(0.08f)] [TestCase(0.18f)] [TestCase(0.5f)]
        [TestCase(1f)] [TestCase(1.5f)] [TestCase(2.5f)]
        public void LinearTint_ActualWorldShaderGpuReceivesLinear(float value)
        {
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null)
                Assert.Ignore("Numeric GPU contract is separately measured with the graphics-enabled tint probe.");
            var shader = WorldPbrTintProbe.BuildProbeShader();
            var material = new Material(shader);
            try
            {
                SetTint(material, new Vector3(value, value, value));
                float encoded = material.GetVector("_Tint").x;
                float actual = WorldPbrTintProbe.Read(shader, encoded, false, false, out _);
                Assert.That(actual, Is.EqualTo(value).Within(2e-5));
            }
            finally { UnityEngine.Object.DestroyImmediate(material); }
        }

        // ADR 0242: manifest "runoff_strength" scales the run-off layer of one material; absent = 1 (other regions unchanged).
        [Test]
        public void RunoffStrengthScale_DefaultsToOneAndClamps()
        {
            var type = Type.GetType("Game.World.Import.WorldPbrMaterials, Game.World.Import.Editor", true);
            var method = type.GetMethod("RunoffStrengthScale", BindingFlags.Static | BindingFlags.Public);
            Assert.NotNull(method);
            Func<object, float> scale = v =>
            {
                var def = new System.Collections.Generic.Dictionary<string, object>();
                if (v != null) def["runoff_strength"] = v;
                return (float)method.Invoke(null, new object[] { def });
            };
            Assert.That(scale(null), Is.EqualTo(1f));
            Assert.That(scale(0.25), Is.EqualTo(0.25f).Within(1e-6));
            Assert.That(scale(0L), Is.EqualTo(0f));
            Assert.That(scale(7.0), Is.EqualTo(2f));
            Assert.That(scale(-1.0), Is.EqualTo(0f));
        }
    }
}
