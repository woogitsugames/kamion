using System;
using System.IO;
using Game.Editor.Build;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;
using Game.Rendering;
using UnityEngine;

namespace Game.Editor.VisualQA
{
    public static class TruckPaintRound
    {
        public const string Cameras = "chase,truck-front,truck-34,truck-34r,truck-side,truck-rear34,truck-at-gate,trailer-34,trailer-side,cab-dash,cab-driver,cab-gate,cab-left,cab-right,cab-mirror-front,cab-mirrors-left,cab-mirrors-right";
        static bool noPane, noCoat;
        static void OnTier(QualityProfile.Tier ignored)
        {
            if (noCoat) Shader.SetGlobalFloat("_KamionClearCoatOff", 1f);
        }
        static void OnScene(Scene scene, OpenSceneMode mode)
        {
            if (!noPane) return;
            int count=0;
            foreach (var renderer in UnityEngine.Object.FindObjectsByType<MeshRenderer>(FindObjectsInactive.Include, FindObjectsSortMode.None))
                if (renderer.name.StartsWith("GLASS_", StringComparison.Ordinal)) { renderer.enabled=false; count++; }
            if (count==0) throw new InvalidOperationException("No cab panes found for actual no-pane reference");
            Debug.Log("TRUCK_NO_PANE: disabled="+count+" (lamp lenses retained)");
        }
        public static void RunBatch()
        {
            string round = EditorTools.Arg("-truckRound", "before");
            string cameras = EditorTools.Arg("-truckCameras", Cameras);
            noPane=EditorTools.Arg("-truckNoPane", "0")=="1";
            noCoat=EditorTools.Arg("-truckCoatOff", "0")=="1";
            EditorSceneManager.sceneOpened += OnScene;
            QualityProfileApplier.Applied += OnTier;
            int total = 0;
            try
            {
            foreach (string tier in new[] { "Low", "High" })
                foreach (string light in new[] { "overcast", "clear", "lowsun" })
                {
                    string target = Path.Combine(EditorTools.RepoRoot, "artifacts/truck-paint-r1", round, tier + "-" + light);
                    int count = VisualQaRunner.Render(tier == "High" ? "WorldC_High" : "WorldC", 2340, 1080, tier, target, light, cameras);
                    if (count != cameras.Split(',').Length) throw new InvalidOperationException("Missing truck cameras " + target + " count=" + count);
                    total += count;
                    Debug.Log("TRUCK_ROUND_CONDITION: OK " + round + " " + tier + "-" + light + " count=" + count);
                }
            }
            finally
            {
                EditorSceneManager.sceneOpened -= OnScene;
                QualityProfileApplier.Applied -= OnTier;
            }
            Debug.Log("TRUCK_ROUND_RESULT: OK " + round + " count=" + total);
            if (Application.isBatchMode) EditorApplication.Exit(0);
        }
    }
}
