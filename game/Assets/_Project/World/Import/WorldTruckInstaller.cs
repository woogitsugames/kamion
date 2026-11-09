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
    /// Track A7: puts the TRAKT tractor (TruckAssetBuilder prefab) and the art curtainsider (TrailerAssetBuilder prefab) into
    /// the generated world scenes in place of the graybox (same pose, bootstrap rewired), registers all lighting presets and
    /// adds the A7 control cameras. New imports get both from WorldSceneBuilder directly; this updates scenes imported before. Batchmode:
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
                TrailerAssetBuilder.Build();
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
            var trailerPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(TrailerAssetBuilder.PrefabPath);
            var oldTrailer = UnityEngine.Object.FindObjectsByType<TrailerBody>(FindObjectsSortMode.None).FirstOrDefault();
            if (trailerPrefab != null && oldTrailer != null)
            {
                var trailer = (GameObject)PrefabUtility.InstantiatePrefab(trailerPrefab, scene);
                trailer.transform.SetPositionAndRotation(oldTrailer.transform.position, oldTrailer.transform.rotation);
                if (boot != null) boot.trailer = trailer.GetComponent<TrailerBody>();
                UnityEngine.Object.DestroyImmediate(oldTrailer.gameObject);
            }
            var env = UnityEngine.Object.FindAnyObjectByType<EnvironmentLighting>();
            if (env != null) { env.presets = LookDevAssets.Presets(); env.Apply(); }
            TruckAssetBuilder.AddControlCameras(truck.transform);
            float heading = Mathf.Repeat(Mathf.Atan2(truck.transform.forward.x, truck.transform.forward.z) * Mathf.Rad2Deg, 360f);
            Debug.Log($"[TRUCK] installed in {scenePath} at {pos}, heading {heading:F1} deg");
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
        }
    }
}
