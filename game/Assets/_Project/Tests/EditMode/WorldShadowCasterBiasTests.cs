using System;
using System.Collections.Generic;
using System.IO;
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

        static void ApplyPolicy(Material m, string id, string path)
        {
            var type = Type.GetType("Game.World.Import.WorldShadowCasterBias, Game.World.Import.Editor", true);
            type.GetMethod("ApplyPolicy", BindingFlags.Public | BindingFlags.Static).Invoke(null,
                new object[] { m, new Dictionary<string, object>(), id, path });
        }

        [Test]
        public void RegionPolicyEntryAndFileRemovalRestoreLegacyWithoutAffectingOtherIds()
        {
            var m = NewMaterial();
            string temp = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Temp")); Directory.CreateDirectory(temp);
            string path = Path.Combine(temp, "shadow-policy-" + Guid.NewGuid().ToString("N") + ".json");
            try
            {
                File.WriteAllText(path, "{\"schema\":\"kamion/shadow-caster-bias/1\",\"materials\":{\"deck\":0}}");
                ApplyPolicy(m, "other", path); Assert.That(m.GetFloat(Property), Is.EqualTo(1));
                ApplyPolicy(m, "deck", path); Assert.That(m.IsKeywordEnabled(Keyword), Is.True); Assert.That(m.GetFloat(Property), Is.Zero);
                File.WriteAllText(path, "{\"schema\":\"kamion/shadow-caster-bias/1\",\"materials\":{}}");
                ApplyPolicy(m, "deck", path); Assert.That(m.GetFloat(Property), Is.EqualTo(1)); Assert.That(m.IsKeywordEnabled(Keyword), Is.False);
                File.WriteAllText(path, "{\"schema\":\"kamion/shadow-caster-bias/1\",\"materials\":{\"deck\":0}}");
                ApplyPolicy(m, "deck", path); File.Delete(path);
                ApplyPolicy(m, "deck", path); Assert.That(m.GetFloat(Property), Is.EqualTo(1)); Assert.That(m.IsKeywordEnabled(Keyword), Is.False);
            }
            finally { if (File.Exists(path)) File.Delete(path); UnityEngine.Object.DestroyImmediate(m); }
        }

        [Test]
        public void InvalidPolicySchemaStopsImportInsteadOfSilentlyIgnoringIt()
        {
            var m = NewMaterial();
            string temp = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Temp")); Directory.CreateDirectory(temp);
            string path = Path.Combine(temp, "shadow-policy-" + Guid.NewGuid().ToString("N") + ".json");
            try
            {
                File.WriteAllText(path, "{\"schema\":\"unsupported\",\"materials\":{}}");
                var failure = Assert.Throws<TargetInvocationException>(() => ApplyPolicy(m, "deck", path));
                Assert.That(failure.InnerException, Is.InstanceOf<InvalidDataException>());
            }
            finally { if (File.Exists(path)) File.Delete(path); UnityEngine.Object.DestroyImmediate(m); }
        }

        [Test]
        public void NativeWorldOnlyThreeDeckMaterialsUseBiasVariant()
        {
            const string dir = "Assets/_Generated/World/bialystok-industrial-c/Materials";
            if (!AssetDatabase.IsValidFolder(dir)) Assert.Ignore("Region not imported (run scripts/import-region.ps1 -Region bialystok-industrial-c): " + dir);
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
            Assert.That(opted, Is.EquivalentTo(new[] { "M_bridge_concrete", "M_bridge_kerb", "M_road_asphalt" }));
        }
    }
}
