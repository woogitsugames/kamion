using System;
using System.IO;
using System.Text.RegularExpressions;
using Game.Editor.Build;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEngine;

namespace Game.Editor.Setup
{
    /// <summary>
    /// D84: the single place every driving scene (DrivingLab, region scenes, streaming hosts, WorldTruckInstaller) takes
    /// its tractor and trailer prefab from. The art TRAKT tractor with the full cab (TruckAssetBuilder) and the art
    /// curtainsider (TrailerAssetBuilder) are the rule; the graybox is an emergency fallback only and is always announced
    /// with a warning ("[VEHICLE] FALLBACK ..."), never silent. The art prefabs live in Assets/_Generated (outside git), so
    /// a checkout that never ran the asset builders has none: <see cref="Tractor"/> / <see cref="Trailer"/> build them on
    /// demand when the Blender exports are present.
    /// </summary>
    public static class DrivingVehiclePrefabs
    {
        public const string FallbackTag = "[VEHICLE] FALLBACK";

        /// <summary>
        /// Fixed asset GUIDs of the generated art prefabs. Assets/_Generated is outside git, while DrivingLab.unity (git)
        /// references these prefabs: without a pinned GUID a fresh checkout would generate a new one and the committed
        /// scene would lose its truck. Values = the GUIDs the prefabs have had since their first build (existing generated
        /// world scenes stay valid).
        /// </summary>
        public const string TractorGuid = "4cd4c98f4f348194ea87e419fbf570d6";
        public const string TrailerGuid = "ab5e5ba631cc6c347bf674dc848945bc";

        /// <summary>Folders whose scenes (outside git) are rewritten when a prefab GUID is re-pinned.</summary>
        public static readonly string[] RemapSceneRoots = { "Assets/_Generated/World" };

        static readonly Regex k_MetaGuid = new Regex(@"^guid: ([0-9a-f]{32})\s*$", RegexOptions.Multiline | RegexOptions.Compiled);

        /// <summary>
        /// Makes the generated prefab at <paramref name="prefabPath"/> carry the pinned <paramref name="guid"/>. The asset
        /// builders call it before AND after saving the prefab:
        /// - no .meta yet: writes one with the pinned GUID (an AssetDatabase.Refresh before the save deletes such an orphan
        ///   .meta, which is why the call after SaveAsPrefabAsset is required);
        /// - .meta with another GUID (fresh checkout: the prefab got a random GUID on its first save/import): rewrites the
        ///   GUID line, refreshes the AssetDatabase and rewrites references to the old GUID in the generated scenes under
        ///   <paramref name="sceneRoots"/> (default <see cref="RemapSceneRoots"/>), so the committed DrivingLab.unity and the
        ///   generated world scenes keep the art truck.
        /// Returns the replaced GUID, or null when the .meta was written fresh or already carried the pinned GUID.
        /// </summary>
        public static string PinGuid(string prefabPath, string guid, string[] sceneRoots = null)
        {
            string meta = Path.Combine(EditorTools.ProjectRoot, prefabPath + ".meta");
            if (!File.Exists(meta))
            {
                Directory.CreateDirectory(Path.GetDirectoryName(meta));
                File.WriteAllText(meta, "fileFormatVersion: 2\nguid: " + guid + "\nPrefabImporter:\n  externalObjects: {}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n");
                return null;
            }
            string text = File.ReadAllText(meta);
            var m = k_MetaGuid.Match(text);
            if (!m.Success) throw new InvalidDataException("no guid line in " + meta);
            string old = m.Groups[1].Value;
            if (old == guid) return null;

            string owner = AssetDatabase.GUIDToAssetPath(guid);
            if (!string.IsNullOrEmpty(owner) && owner != prefabPath && File.Exists(Path.Combine(EditorTools.ProjectRoot, owner)))
                throw new InvalidOperationException($"pinned GUID {guid} for {prefabPath} is already used by {owner}");

            File.WriteAllText(meta, text.Substring(0, m.Groups[1].Index) + guid + text.Substring(m.Groups[1].Index + old.Length));
            int scenes = RemapGuidInScenes(old, guid, sceneRoots ?? RemapSceneRoots);
            // The .meta changed on disk: a synchronous refresh drops the old GUID and registers the pinned one.
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
            string now = AssetDatabase.AssetPathToGUID(prefabPath);
            if (File.Exists(Path.Combine(EditorTools.ProjectRoot, prefabPath)) && now != guid)
                throw new InvalidOperationException($"GUID re-pin of {prefabPath} failed: AssetDatabase reports {now}, want {guid}");
            Debug.LogWarning($"[VEHICLE] GUID re-pinned {prefabPath}: {old} -> {guid} ({scenes} generated scenes rewritten)");
            return old;
        }

        /// <summary>Rewrites "guid: old" to "guid: new" in every .unity file under <paramref name="roots"/> (project-relative);
        /// returns the number of files changed.</summary>
        public static int RemapGuidInScenes(string oldGuid, string newGuid, string[] roots)
        {
            int changed = 0;
            string from = "guid: " + oldGuid, to = "guid: " + newGuid;
            foreach (string root in roots)
            {
                string dir = Path.Combine(EditorTools.ProjectRoot, root);
                if (!Directory.Exists(dir)) continue;
                foreach (string f in Directory.GetFiles(dir, "*.unity", SearchOption.AllDirectories))
                {
                    string t = File.ReadAllText(f);
                    if (t.IndexOf(from, StringComparison.Ordinal) < 0) continue;
                    File.WriteAllText(f, t.Replace(from, to));
                    changed++;
                }
            }
            return changed;
        }

        /// <summary>Builds the art prefabs that are missing (no-op when both exist). Call before creating a scene.</summary>
        public static void EnsureBuilt()
        {
            if (AssetDatabase.LoadAssetAtPath<GameObject>(TruckAssetBuilder.PrefabPath) == null)
                TryBuild("TRAKT tractor", TruckAssetBuilder.Build);
            if (AssetDatabase.LoadAssetAtPath<GameObject>(TrailerAssetBuilder.PrefabPath) == null)
                TryBuild("curtainsider trailer", TrailerAssetBuilder.Build);
        }

        /// <summary>The TRAKT tractor prefab, built when missing; the graybox (with a warning) only when that fails.</summary>
        public static GameObject Tractor(out bool graybox, bool buildIfMissing = true)
        {
            if (buildIfMissing && AssetDatabase.LoadAssetAtPath<GameObject>(TruckAssetBuilder.PrefabPath) == null)
                TryBuild("TRAKT tractor", TruckAssetBuilder.Build);
            return Resolve(TruckAssetBuilder.PrefabPath, DrivingLabSceneBuilder.PrefabPath, "tractor", out graybox);
        }

        /// <summary>The art curtainsider prefab, built when missing; the graybox trailer (with a warning) only when that fails.</summary>
        public static GameObject Trailer(out bool graybox, bool buildIfMissing = true)
        {
            if (buildIfMissing && AssetDatabase.LoadAssetAtPath<GameObject>(TrailerAssetBuilder.PrefabPath) == null)
                TryBuild("curtainsider trailer", TrailerAssetBuilder.Build);
            return Resolve(TrailerAssetBuilder.PrefabPath, DrivingLabSceneBuilder.TrailerPrefabPath, "trailer", out graybox);
        }

        /// <summary>The art prefab at <paramref name="artPath"/>, else the fallback with a warning. Throws when neither exists.</summary>
        public static GameObject Resolve(string artPath, string fallbackPath, string what, out bool fallback)
        {
            var art = AssetDatabase.LoadAssetAtPath<GameObject>(artPath);
            fallback = art == null;
            if (!fallback) return art;
            var gb = AssetDatabase.LoadAssetAtPath<GameObject>(fallbackPath);
            if (gb == null)
                throw new FileNotFoundException($"no {what} prefab: neither {artPath} nor the graybox {fallbackPath} (run Kamion/Setup/Rebuild DrivingLab)");
            Debug.LogWarning($"{FallbackTag} {what}: art prefab {artPath} missing, using the graybox {fallbackPath} " +
                             "(run Kamion/Setup/Rebuild TRAKT truck / Rebuild curtainsider trailer, then rebuild the scene)");
            return gb;
        }

        /// <summary>True when a scene tractor is the full art model (cab interior, TruckVisualRig), not the bare graybox rig.</summary>
        public static bool IsArtTractor(GameObject vehicleRoot) =>
            vehicleRoot != null && vehicleRoot.GetComponentInChildren<TruckVisualRig>(true) != null;

        static void TryBuild(string what, Action build)
        {
            try { build(); AssetDatabase.Refresh(); }
            catch (Exception e) { Debug.LogWarning($"{FallbackTag} {what}: on-demand asset build failed: {e.GetType().Name}: {e.Message}"); }
        }
    }
}
