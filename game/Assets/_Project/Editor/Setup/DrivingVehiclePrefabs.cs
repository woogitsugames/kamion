using System;
using System.IO;
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

        /// <summary>Writes the .meta with the pinned GUID when the generated prefab has none yet (the asset builders call
        /// this before saving the prefab). An existing .meta is never rewritten.</summary>
        public static void PinGuid(string prefabPath, string guid)
        {
            string meta = Path.Combine(EditorTools.ProjectRoot, prefabPath + ".meta");
            if (File.Exists(meta)) return;
            Directory.CreateDirectory(Path.GetDirectoryName(meta));
            File.WriteAllText(meta, "fileFormatVersion: 2\nguid: " + guid + "\nPrefabImporter:\n  externalObjects: {}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n");
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
