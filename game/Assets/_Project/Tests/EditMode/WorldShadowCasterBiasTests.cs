using System;
using System.Collections.Generic;
using System.Reflection;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Game.Tests
{
    public class WorldShadowCasterBiasTests
    {
        const string Property = "_ShadowNormalBiasScale", Keyword = "_SHADOW_NORMAL_BIAS_SCALE";
        static void Apply(Material m, Dictionary<string, object> d)
        {
            var type = Type.GetType("Game.World.Import.WorldShadowCasterBias, Game.World.Import.Editor", true);
            type.GetMethod("Apply", BindingFlags.Public | BindingFlags.Static).Invoke(null, new object[] { m, d });
        }
        static Material NewMaterial() => new Material(Shader.Find("Kamion/World PBR"));

        [Test]
        public void LegacyMaterialWithoutFlagHasNoSerializedChange()
        {
            var m = NewMaterial();
            try
            {
                var before = EditorJsonUtility.ToJson(m);
                Apply(m, new Dictionary<string, object>());
                Assert.That(EditorJsonUtility.ToJson(m), Is.EqualTo(before));
                Assert.That(m.GetFloat(Property), Is.EqualTo(1));
                Assert.That(m.IsKeywordEnabled(Keyword), Is.False);
            }
            finally { UnityEngine.Object.DestroyImmediate(m); }
        }

        [Test]
        public void OptInAndRemovalPreserveOtherMaterialStateAndPasses()
        {
            var m = NewMaterial();
            try
            {
                m.SetFloat("_SmoothnessScale", .37f); m.EnableKeyword("_UV_MESH0");
                int passes = m.passCount;
                Apply(m, new Dictionary<string, object> { ["shadow_normal_bias_scale"] = 0.0 });
                Assert.That(m.GetFloat(Property), Is.Zero); Assert.That(m.IsKeywordEnabled(Keyword), Is.True);
                Assert.That(m.passCount, Is.EqualTo(passes));
                Apply(m, new Dictionary<string, object>());
                Assert.That(m.GetFloat(Property), Is.EqualTo(1)); Assert.That(m.IsKeywordEnabled(Keyword), Is.False);
                Assert.That(m.GetFloat("_SmoothnessScale"), Is.EqualTo(.37f));
                Assert.That(m.IsKeywordEnabled("_UV_MESH0"), Is.True); Assert.That(m.passCount, Is.EqualTo(passes));
            }
            finally { UnityEngine.Object.DestroyImmediate(m); }
        }

        [TestCase(double.NaN)] [TestCase(double.PositiveInfinity)] [TestCase(-.1)] [TestCase(1.1)]
        public void MalformedOptInCannotLeakIntoReusedMaterial(double value)
        {
            var m = NewMaterial();
            try
            {
                Apply(m, new Dictionary<string, object> { ["shadow_normal_bias_scale"] = 0.0 });
                Apply(m, new Dictionary<string, object> { ["shadow_normal_bias_scale"] = value });
                Assert.That(m.GetFloat(Property), Is.EqualTo(1)); Assert.That(m.IsKeywordEnabled(Keyword), Is.False);
            }
            finally { UnityEngine.Object.DestroyImmediate(m); }
        }

        [Test]
        public void NativeWorldOnlyViaductConcreteUsesBiasVariant()
        {
            const string dir = "Assets/_Generated/World/bialystok-industrial-c/Materials";
            var opted = new List<string>();
            foreach (var guid in AssetDatabase.FindAssets("t:Material", new[] { dir }))
            {
                var m = AssetDatabase.LoadAssetAtPath<Material>(AssetDatabase.GUIDToAssetPath(guid));
                if (m.IsKeywordEnabled(Keyword))
                {
                    opted.Add(m.name); Assert.That(m.GetFloat(Property), Is.Zero);
                    Assert.That(m.shader.name, Is.EqualTo("Kamion/World PBR"));
                }
                else if (m.HasProperty(Property)) Assert.That(m.GetFloat(Property), Is.EqualTo(1), m.name);
            }
            Assert.That(opted, Is.EquivalentTo(new[] { "M_viaduct_concrete" }));
        }
    }
}
