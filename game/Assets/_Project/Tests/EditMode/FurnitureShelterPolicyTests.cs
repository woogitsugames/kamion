using System;
using Game.World;
using Game.World.Import.Furniture;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Game.Tests
{
    public sealed class FurnitureShelterPolicyTests
    {
        static WorldInstanceSet Make(bool donor = true, bool variant = true)
        {
            var set = ScriptableObject.CreateInstance<WorldInstanceSet>();
            var source = new WorldInstanceSet.Prototype { name = "bus_shelter", lodEndM = new[] {60f, 300f}, shadowLodMask = 1 };
            var target = new WorldInstanceSet.Prototype { name = FurnitureShelterPolicySave.Variant, lods = new Mesh[2], lodEndM = new[] {30f, 120f}, shadowLodMask = 0 };
            set.prototypes = donor && variant ? new[] {source, target} : donor ? new[] {source} : new[] {target};
            return set;
        }

        [Test]
        public void VariantInheritsFullVisibilityAndShadowPolicyWithoutAliasing()
        {
            var set = Make();
            try
            {
                Assert.That(FurnitureShelterPolicySave.Inherit(set), Is.True);
                Assert.That(set.prototypes[1].lodEndM, Is.EqualTo(new[] {60f, 300f}));
                Assert.That(set.prototypes[1].shadowLodMask, Is.EqualTo(1));
                Assert.That(set.prototypes[1].lodEndM, Is.Not.SameAs(set.prototypes[0].lodEndM));
                set.prototypes[1].lodEndM[0] = 55f;
                Assert.That(set.prototypes[0].lodEndM[0], Is.EqualTo(60f));
            }
            finally { UnityEngine.Object.DestroyImmediate(set); }
        }

        [Test]
        public void ReapplyingDoesNotRewriteThePolicy()
        {
            var set = Make();
            try
            {
                FurnitureShelterPolicySave.Inherit(set);
                var ends = set.prototypes[1].lodEndM;
                Assert.That(FurnitureShelterPolicySave.Inherit(set), Is.False);
                Assert.That(set.prototypes[1].lodEndM, Is.SameAs(ends));
            }
            finally { UnityEngine.Object.DestroyImmediate(set); }
        }

        [Test]
        public void GenericOnlySetRemainsUntouched()
        {
            var set = Make(variant: false);
            try
            {
                var ends = set.prototypes[0].lodEndM;
                Assert.That(FurnitureShelterPolicySave.Inherit(set), Is.False);
                Assert.That(set.prototypes[0].lodEndM, Is.SameAs(ends));
            }
            finally { UnityEngine.Object.DestroyImmediate(set); }
        }

        [Test]
        public void MissingFamilyFailsRatherThanKeepingTheShortFallback()
        {
            var set = Make(donor: false);
            try { Assert.Throws<InvalidOperationException>(() => FurnitureShelterPolicySave.Inherit(set)); }
            finally { UnityEngine.Object.DestroyImmediate(set); }
        }

        [Test]
        public void IncompatibleLodCountDoesNotSilentlyRewriteTheVariant()
        {
            var set = Make();
            try
            {
                set.prototypes[1].lods = new Mesh[3];
                Assert.Throws<InvalidOperationException>(() => FurnitureShelterPolicySave.Inherit(set));
                Assert.That(set.prototypes[1].lodEndM, Is.EqualTo(new[] {30f, 120f}));
            }
            finally { UnityEngine.Object.DestroyImmediate(set); }
        }

        [Test]
        public void UnrelatedPrototypePolicyIsPreserved()
        {
            var set = Make();
            try
            {
                var other = new WorldInstanceSet.Prototype {name = "waste_bin", lodEndM = new[] {30f, 120f}, shadowLodMask = 1};
                var ends = other.lodEndM;
                set.prototypes = new[] {set.prototypes[0], set.prototypes[1], other};
                FurnitureShelterPolicySave.Inherit(set);
                Assert.That(other.lodEndM, Is.SameAs(ends));
                Assert.That(other.shadowLodMask, Is.EqualTo(1));
            }
            finally { UnityEngine.Object.DestroyImmediate(set); }
        }

        [Test]
        public void NormalAssetSavePersistsTheInheritedPolicy()
        {
            const string parent = "Assets/_Generated/World";
            var folder = parent + "/FurnitureShelterPolicyTest_" + Guid.NewGuid().ToString("N");
            AssetDatabase.CreateFolder(parent, folder.Substring(parent.Length + 1));
            var path = folder + "/Instances.asset";
            var set = Make();
            try
            {
                AssetDatabase.CreateAsset(set, path);
                EditorUtility.SetDirty(set);
                AssetDatabase.SaveAssets();
                Resources.UnloadAsset(set);
                set = AssetDatabase.LoadAssetAtPath<WorldInstanceSet>(path);
                Assert.That(set.prototypes[1].lodEndM, Is.EqualTo(new[] {60f, 300f}));
                Assert.That(set.prototypes[1].shadowLodMask, Is.EqualTo(1));
            }
            finally { AssetDatabase.DeleteAsset(folder); }
        }
    }
}
