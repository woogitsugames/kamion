using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using Game.Editor.Setup;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>
    /// D84: every driving scene (DrivingLab, the generated region scenes incl. the streaming hosts) carries the art TRAKT
    /// tractor with the full cab, installed through DrivingVehiclePrefabs; the graybox is a warned fallback only.
    /// Scenes are checked as text (prefab-instance source GUIDs): opening every world scene here would take minutes.
    /// </summary>
    public class DrivingScenesFullTruckTests
    {
        static readonly Regex k_Source = new Regex(@"m_SourcePrefab: \{fileID: \d+, guid: ([0-9a-f]{32})", RegexOptions.Compiled);

        static HashSet<string> SourcePrefabGuids(string assetPath)
        {
            var set = new HashSet<string>();
            foreach (var line in File.ReadLines(Path.Combine(Game.Editor.Build.EditorTools.ProjectRoot, assetPath)))
            {
                if (line.IndexOf("m_SourcePrefab", System.StringComparison.Ordinal) < 0) continue;
                var m = k_Source.Match(line);
                if (m.Success) set.Add(m.Groups[1].Value);
            }
            return set;
        }

        /// <summary>DrivingLab plus every generated world scene that hosts a vehicle (tile scenes have none, ADR 0235).</summary>
        static IEnumerable<string> DrivingScenes()
        {
            yield return DrivingLabSceneBuilder.ScenePath;
            if (!AssetDatabase.IsValidFolder("Assets/_Generated/World")) yield break;
            foreach (var guid in AssetDatabase.FindAssets("t:Scene", new[] { "Assets/_Generated/World" }))
            {
                string p = AssetDatabase.GUIDToAssetPath(guid);
                string n = Path.GetFileNameWithoutExtension(p);
                if (n.StartsWith("World", System.StringComparison.Ordinal) && !n.EndsWith("_Tile", System.StringComparison.Ordinal)) yield return p;
            }
        }

        [Test]
        public void ArtPrefabs_HavePinnedGuids()
        {
            string t = AssetDatabase.AssetPathToGUID(TruckAssetBuilder.PrefabPath);
            if (string.IsNullOrEmpty(t)) Assert.Ignore("TRAKT prefab not built in this checkout (Kamion/Setup/Rebuild TRAKT truck)");
            Assert.AreEqual(DrivingVehiclePrefabs.TractorGuid, t, "DrivingLab.unity (git) references the TRAKT prefab by this GUID");
            string tr = AssetDatabase.AssetPathToGUID(TrailerAssetBuilder.PrefabPath);
            if (!string.IsNullOrEmpty(tr)) Assert.AreEqual(DrivingVehiclePrefabs.TrailerGuid, tr);
        }

        [Test]
        public void TraktPrefab_IsTheFullModel_WithCabInterior()
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(TruckAssetBuilder.PrefabPath);
            if (prefab == null) Assert.Ignore("TRAKT prefab not built in this checkout");
            Assert.IsTrue(DrivingVehiclePrefabs.IsArtTractor(prefab), "TruckVisualRig on the TRAKT prefab");
            Assert.IsFalse(DrivingVehiclePrefabs.IsArtTractor(AssetDatabase.LoadAssetAtPath<GameObject>(DrivingLabSceneBuilder.PrefabPath)), "the graybox is not the art model");
            var names = prefab.GetComponentsInChildren<Transform>(true).Select(x => x.name).ToArray();
            Assert.IsTrue(names.Any(n => n == "DriverEyePoint"), "driver eye point");
            foreach (string d in TruckAssetBuilder.DisplayObjects)
                Assert.IsTrue(names.Any(n => n.StartsWith(d, System.StringComparison.Ordinal)), "cab display " + d);
        }

        [Test]
        public void EveryDrivingScene_InstallsTheFullTruck_NotTheGraybox()
        {
            string grayTractor = AssetDatabase.AssetPathToGUID(DrivingLabSceneBuilder.PrefabPath);
            string grayTrailer = AssetDatabase.AssetPathToGUID(DrivingLabSceneBuilder.TrailerPrefabPath);
            Assert.IsNotEmpty(grayTractor, "graybox fallback prefab (git)");
            var bad = new List<string>();
            int n = 0;
            foreach (string scene in DrivingScenes())
            {
                var guids = SourcePrefabGuids(scene);
                n++;
                if (!guids.Contains(DrivingVehiclePrefabs.TractorGuid)) bad.Add(scene + ": no TRAKT tractor instance");
                if (guids.Contains(grayTractor)) bad.Add(scene + ": graybox tractor instance");
                if (guids.Contains(grayTrailer)) bad.Add(scene + ": graybox trailer instance");
            }
            Assert.GreaterOrEqual(n, 1);
            Assert.IsEmpty(bad, $"{bad.Count} problems in {n} driving scenes:\n" + string.Join("\n", bad));
        }

        [Test]
        public void Resolver_ReturnsArt_WhenBuilt()
        {
            if (AssetDatabase.LoadAssetAtPath<GameObject>(TruckAssetBuilder.PrefabPath) == null) Assert.Ignore("TRAKT prefab not built in this checkout");
            var p = DrivingVehiclePrefabs.Tractor(out bool graybox, buildIfMissing: false);
            Assert.IsFalse(graybox);
            Assert.AreEqual(TruckAssetBuilder.PrefabPath, AssetDatabase.GetAssetPath(p));
        }

        [Test]
        public void Resolver_FallsBackToGraybox_WithWarning()
        {
            LogAssert.Expect(LogType.Warning, new Regex(Regex.Escape(DrivingVehiclePrefabs.FallbackTag) + " tractor"));
            var p = DrivingVehiclePrefabs.Resolve("Assets/_Generated/Truck/__missing__.prefab", DrivingLabSceneBuilder.PrefabPath, "tractor", out bool fallback);
            Assert.IsTrue(fallback);
            Assert.AreEqual(DrivingLabSceneBuilder.PrefabPath, AssetDatabase.GetAssetPath(p));
            Assert.Throws<FileNotFoundException>(() => DrivingVehiclePrefabs.Resolve("Assets/__a__.prefab", "Assets/__b__.prefab", "tractor", out _));
        }
    }
}
