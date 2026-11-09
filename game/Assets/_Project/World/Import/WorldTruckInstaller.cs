using System.Collections.Generic;
using System;
using System.IO;
using System.Linq;
using Game.Editor.Setup;
using Game.Gameplay;
using Game.Rendering;
using Game.Rendering.Editor;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Game.World.Import
{
    /// <summary>
    /// Track A7: puts the TRAKT tractor (TruckAssetBuilder prefab) into the generated world scenes in place of the graybox
    /// (same pose, bootstrap rewired), registers all lighting presets and adds the A7 control cameras. New imports get the
    /// truck from WorldSceneBuilder directly; this updates scenes imported before. Batchmode:
    /// -executeMethod Game.World.Import.WorldTruckInstaller.InstallBatch
    /// </summary>
    public static class WorldTruckInstaller
    {
        public static void InstallBatch()
        {
            int exit = 0;
            try
            {
                TruckAssetBuilder.Build();
                int n = 0;
                foreach (var guid in AssetDatabase.FindAssets("t:Scene WorldC"))
                {
                    string p = AssetDatabase.GUIDToAssetPath(guid);
                    if (!Path.GetFileNameWithoutExtension(p).StartsWith("WorldC", StringComparison.Ordinal)) continue;
                    InstallInScene(p);
                    n++;
                }
                if (n == 0) throw new FileNotFoundException("no WorldC scene (import the region first: scripts/import-region.ps1)");
                Debug.Log("TRUCK_RESULT: OK");
            }
            catch (Exception e) { Debug.LogException(e); Debug.Log("TRUCK_RESULT: FAILED"); exit = 1; }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        [MenuItem("Kamion/Setup/Install TRAKT truck in WorldC")]
        static void Menu() => InstallBatch();

        /// <summary>
        /// Contact shadow under the scene's trailer (review r4 E-N1): one slab over the 13.6 m box at the main-beam
        /// underside, plus the wheel blobs (TruckAssetBuilder.AddContactShadow). Scene override, the shared trailer prefab
        /// is untouched.
        /// </summary>
        static void InstallTrailerContactShadow()
        {
            var trailer = UnityEngine.Object.FindAnyObjectByType<TrailerBody>();
            if (trailer == null) return;
            var tv = trailer.GetComponent<TrailerVisuals>();
            var dims = new TrailerDimensions();
            // Box length from the rear end (bounds also hold the coupler and cables ahead of the front wall).
            TruckAssetBuilder.AddContactShadow(trailer.gameObject, tv != null ? tv.wheelPivots : null, dims.width * 0.5f,
                new[] { (0f, dims.beamBottom + 0.08f, 0.85f, 6) }, dims.length, 0.42f, 0.42f);
        }

        public static void InstallInScene(string scenePath)
        {
            LookDevAssets.EnsureAll();
            var scene = EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(TruckAssetBuilder.PrefabPath);
            if (prefab == null) throw new FileNotFoundException("TRAKT prefab missing", TruckAssetBuilder.PrefabPath);
            var old = UnityEngine.Object.FindObjectsByType<VehicleBody>(FindObjectsSortMode.None).FirstOrDefault();
            if (old == null) throw new InvalidOperationException("no tractor in " + scenePath);
            var pos = old.transform.position;
            var rot = old.transform.rotation;
            var truck = (GameObject)PrefabUtility.InstantiatePrefab(prefab, scene);
            truck.transform.SetPositionAndRotation(pos, rot);
            var boot = UnityEngine.Object.FindAnyObjectByType<DrivingLabBootstrap>();
            if (boot != null) boot.vehicle = truck.GetComponent<VehicleBody>();
            UnityEngine.Object.DestroyImmediate(old.gameObject);
            var env = UnityEngine.Object.FindAnyObjectByType<EnvironmentLighting>();
            if (env != null) { env.presets = LookDevAssets.Presets(); env.Apply(); }
            TruckAssetBuilder.AddControlCameras(truck.transform);
            InstallTrailerContactShadow();
            float heading = Mathf.Repeat(Mathf.Atan2(truck.transform.forward.x, truck.transform.forward.z) * Mathf.Rad2Deg, 360f);
            Debug.Log($"[TRUCK] installed in {scenePath} at {pos}, heading {heading:F1} deg");
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
        }
    }
}
