using System;
using System.Linq;
using System.Reflection;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    public class FabSurfaceBaseTests
    {
        [TestCase("terrain_grass", 4f, 4f)]
        [TestCase("verge_grass", 4f, 4f)]
        [TestCase("curb_concrete", 2f, 0.5f)]
        public void PhotographicBasePreservesWorldPbrLightingAndAuxiliaryMaps(string id, float tileX, float tileY)
        {
            var shader = Shader.Find("Kamion/World PBR");
            Assert.That(shader, Is.Not.Null);
            var material = new Material(shader);
            var original = new Texture2D(2, 2);
            var replacement = new Texture2D(2, 2);
            try
            {
                foreach (string property in new[] { "_BaseMap", "_Tile", "_Tint", "_MacroStrength" })
                    Assert.That(material.HasProperty(property), Is.True, property);
                var slots = new[] { "_NormalMap", "_MaskMap", "_MacroMap", "_VarMap" };
                foreach (string slot in slots)
                {
                    Assert.That(material.HasProperty(slot), Is.True, slot);
                    material.SetTexture(slot, original);
                }
                material.SetTexture("_BaseMap", original);
                material.SetVector("_Tile", new Vector4(8f, 9f, 32f, 0.75f));
                material.SetVector("_Tint", new Vector4(0.9f, 0.8f, 0.7f, 1f));
                material.SetFloat("_MacroStrength", 0.17f);
                material.EnableKeyword("_UV_MESH0");
                string[] keywords = material.shaderKeywords.OrderBy(k => k).ToArray();
                var importer = Type.GetType("Game.World.Import.FabMaterials, Game.World.Import.Editor", true);
                // Look up the actual policy contract, not any overload with the same name.
                // A regression to Vector2 would fail this assertion before Invoke receives a string.
                var method = importer.GetMethod("SetSurfaceBase", BindingFlags.NonPublic | BindingFlags.Static,
                    null, new[] { typeof(Material), typeof(Texture2D), typeof(string) }, null);
                Assert.That(method, Is.Not.Null, "Expected SetSurfaceBase(Material, Texture2D, string id)");
                method.Invoke(null, new object[] { material, replacement, id });
                Assert.That(material.shader, Is.SameAs(shader));
                Assert.That(material.GetTexture("_BaseMap"), Is.SameAs(replacement));
                foreach (string slot in slots) Assert.That(material.GetTexture(slot), Is.SameAs(original), slot);
                Assert.That(material.GetVector("_Tile"), Is.EqualTo(new Vector4(tileX, tileY, 32f, 0.75f)));
                Assert.That(material.GetVector("_Tint"), Is.EqualTo(new Vector4(0.9f, 0.8f, 0.7f, 1f)));
                Assert.That(material.GetFloat("_MacroStrength"), Is.EqualTo(0.17f));
                CollectionAssert.AreEqual(keywords, material.shaderKeywords.OrderBy(k => k));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(material);
                UnityEngine.Object.DestroyImmediate(original);
                UnityEngine.Object.DestroyImmediate(replacement);
            }
        }
    }
}
