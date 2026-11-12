using System;
using System.Reflection;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Tests
{
    public class CarPaintMaterialTests
    {
        static void ApplyPearl(Material material, Vector3 linear)
        {
            var type = Type.GetType("Game.World.Import.WorldPbrMaterials, Game.World.Import.Editor", true);
            var method = type.GetMethod("SetLinearPearlTint", BindingFlags.Static | BindingFlags.Public);
            Assert.NotNull(method);
            method.Invoke(null, new object[] { material, linear });
        }

        [TestCase(1f)] [TestCase(1.6f)] [TestCase(1.9f)] [TestCase(3.2f)]
        public void PearlRatio_ColorStoragePreservesLinearHdr(float value)
        {
            var shader = Shader.Find("Kamion/World PBR");
            Assert.NotNull(shader);
            Assert.That(shader.GetPropertyType(shader.FindPropertyIndex("_PearlTint")), Is.EqualTo(ShaderPropertyType.Color));
            var material = new Material(shader);
            try
            {
                ApplyPearl(material, Vector3.one * value);
                var decoded = material.GetColor("_PearlTint").linear;
                Assert.That(decoded.r, Is.EqualTo(value).Within(1e-5));
                Assert.That(decoded.g, Is.EqualTo(value).Within(1e-5));
                Assert.That(decoded.b, Is.EqualTo(value).Within(1e-5));
                Assert.That(material.GetColor("_PearlTint").a, Is.EqualTo(1f));
            }
            finally { UnityEngine.Object.DestroyImmediate(material); }
        }

        [Test]
        public void BlackPearl_ChannelRatiosSurviveEncoding()
        {
            var material = new Material(Shader.Find("Kamion/World PBR"));
            try
            {
                ApplyPearl(material, new Vector3(1.6f, 1.9f, 3.2f));
                var decoded = material.GetColor("_PearlTint").linear;
                Assert.That(decoded.g / decoded.r, Is.EqualTo(1.9f / 1.6f).Within(1e-5));
                Assert.That(decoded.b / decoded.r, Is.EqualTo(2f).Within(1e-5));
            }
            finally { UnityEngine.Object.DestroyImmediate(material); }
        }
    }
}
