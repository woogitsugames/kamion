using System;
using System.IO;
using Game.Editor.Build;
using Game.Editor.Setup;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// D84 / build-fix-s24: DrivingVehiclePrefabs.PinGuid must force the pinned GUID also when the generated prefab already
    /// has a .meta with a random GUID (fresh checkout: first save before pinning, or the orphan .meta dropped by a Refresh),
    /// and rewrite the generated scenes that reference the old GUID.
    /// </summary>
    public class PinGuidTests
    {
        const string Folder = "Assets/_Generated/__PinGuidTest";
        const string SceneRoot = "Temp/__PinGuidTestScenes";   // outside Assets: the fake scene is never imported

        [SetUp]
        public void SetUp()
        {
            TearDown();
            Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, Folder));
            Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, SceneRoot));
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
        }

        [TearDown]
        public void TearDown()
        {
            if (AssetDatabase.IsValidFolder(Folder)) AssetDatabase.DeleteAsset(Folder);
            string f = Path.Combine(EditorTools.ProjectRoot, Folder);
            if (Directory.Exists(f)) Directory.Delete(f, true);
            if (File.Exists(f + ".meta")) File.Delete(f + ".meta");
            string s = Path.Combine(EditorTools.ProjectRoot, SceneRoot);
            if (Directory.Exists(s)) Directory.Delete(s, true);
        }

        static void SavePrefab(string path)
        {
            var go = new GameObject("PinGuidTest");
            try { PrefabUtility.SaveAsPrefabAsset(go, path); }
            finally { UnityEngine.Object.DestroyImmediate(go); }
        }

        [Test]
        public void ExistingMetaWithRandomGuid_IsRepinned_AndScenesRemapped()
        {
            string path = Folder + "/Tractor.prefab";
            SavePrefab(path);
            string random = AssetDatabase.AssetPathToGUID(path);
            Assert.IsNotEmpty(random);
            string pinned = Guid.NewGuid().ToString("N");
            string scene = Path.Combine(EditorTools.ProjectRoot, SceneRoot, "World_test.unity");
            File.WriteAllText(scene, $"  m_SourcePrefab: {{fileID: 100100000, guid: {random}, type: 3}}\n");

            Assert.AreEqual(random, DrivingVehiclePrefabs.PinGuid(path, pinned, new[] { SceneRoot }));
            Assert.AreEqual(pinned, AssetDatabase.AssetPathToGUID(path), "AssetDatabase sees the pinned GUID");
            Assert.AreEqual(path, AssetDatabase.GUIDToAssetPath(pinned));
            Assert.IsNotNull(AssetDatabase.LoadAssetAtPath<GameObject>(path), "prefab still loads");
            string sceneText = File.ReadAllText(scene);
            StringAssert.Contains("guid: " + pinned, sceneText);
            StringAssert.DoesNotContain(random, sceneText);

            Assert.IsNull(DrivingVehiclePrefabs.PinGuid(path, pinned, new[] { SceneRoot }), "second call is a no-op");
        }

        [Test]
        public void MetaWrittenBeforeSave_SurvivesRefresh_OrIsRepinnedAfterSave()
        {
            // The asset builders' order: PinGuid -> CopySources (AssetDatabase.Refresh) -> SaveAsPrefabAsset -> PinGuid.
            string path = Folder + "/Trailer.prefab";
            string pinned = Guid.NewGuid().ToString("N");
            Assert.IsNull(DrivingVehiclePrefabs.PinGuid(path, pinned, new[] { SceneRoot }));
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            SavePrefab(path);
            DrivingVehiclePrefabs.PinGuid(path, pinned, new[] { SceneRoot });
            Assert.AreEqual(pinned, AssetDatabase.AssetPathToGUID(path));
        }

        [Test]
        public void PinnedGuidOwnedByAnotherAsset_Throws()
        {
            string a = Folder + "/A.prefab", b = Folder + "/B.prefab";
            SavePrefab(a);
            SavePrefab(b);
            string guidOfA = AssetDatabase.AssetPathToGUID(a);
            Assert.Throws<InvalidOperationException>(() => DrivingVehiclePrefabs.PinGuid(b, guidOfA, new[] { SceneRoot }));
            Assert.AreEqual(guidOfA, AssetDatabase.AssetPathToGUID(a), "the other asset keeps its GUID");
        }
    }
}
