using System;
using System.Collections.Generic;
using System.Reflection;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>ADR 0194: matt oil stains are data-gated (manifest "oil_look") and the legacy response stays exact.</summary>
    public class OilStainLookTests
    {
        static Type Importer => Type.GetType("Game.World.Import.WorldPbrMaterials, Game.World.Import.Editor", true);

        static Vector4 Look(Dictionary<string, object> def) =>
            (Vector4)Importer.GetMethod("OilLook", BindingFlags.Public | BindingFlags.Static).Invoke(null, new object[] { def });

        [Test]
        public void NoBlockKeepsLegacyOil()
        {
            Assert.AreEqual(new Vector4(0f, 0f, 1f, 0f), Look(new Dictionary<string, object> { ["decal"] = true }));
        }

        [Test]
        public void BlockIsReadAndClamped()
        {
            var def = new Dictionary<string, object>
            {
                ["oil_look"] = new Dictionary<string, object> { ["smooth_aged"] = 0.1d, ["smooth_fresh"] = 0.22d, ["coverage_gamma"] = 0.7d }
            };
            var v = Look(def);
            Assert.That(v.x, Is.EqualTo(0.1f).Within(1e-6f));
            Assert.That(v.y, Is.EqualTo(0.22f).Within(1e-6f));
            Assert.That(v.z, Is.EqualTo(0.7f).Within(1e-6f));
            Assert.AreEqual(1f, v.w);
            ((Dictionary<string, object>)def["oil_look"])["coverage_gamma"] = 99d;
            Assert.AreEqual(4f, Look(def).z);
        }

        [Test]
        public void WorldPbrCompilesWithStainInclude()
        {
            var shader = Shader.Find("Kamion/World PBR");
            Assert.NotNull(shader);
            Assert.IsFalse(ShaderUtil.ShaderHasError(shader));
            var mat = new Material(shader);
            try { Assert.AreEqual(new Vector4(0f, 0f, 1f, 0f), mat.GetVector("_OilLook")); }
            finally { UnityEngine.Object.DestroyImmediate(mat); }
        }
    }
}
