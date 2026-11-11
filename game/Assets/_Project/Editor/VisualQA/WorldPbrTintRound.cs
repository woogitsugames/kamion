using System;
using System.IO;
using Game.Editor.Build;
using UnityEditor;
using UnityEngine;

namespace Game.Editor.VisualQA
{
    /// <summary>ADR0086 identical camera/geometry matrix, four conditions in one editor process.</summary>
    public static class WorldPbrTintRound
    {
        public const string FocusCameras = "driver-andersa-to-putry,kwadrat-park-gate,stretch-05-docks,fire-station-ref7197,g3b-eye-s1482,photo-biezenstwa-ground,r10_house_2,r10_block_3,r10_fence_2,truck-at-gate,route-putry-entry-signs";
        public static void RunBatch()
        {
            string round = EditorTools.Arg("-tintRound", "before");
            // Default is ALL registered cameras: a global material fix needs a
            // full-world regression matrix, even when the ROI table uses a subset.
            string cameras = EditorTools.Arg("-tintCameras", null);
            int rendered = 0;
            foreach (string tier in new[] { "Low", "High" })
                foreach (string lighting in new[] { "overcast", "clear" })
                {
                    string output = Path.Combine(EditorTools.RepoRoot, "artifacts/tint-gamma-r1", round, tier + "-" + lighting);
                    string scene = tier == "High" ? "WorldC_High" : "WorldC";
                    int count = VisualQaRunner.Render(scene, 2340, 1080, tier, output, lighting, cameras);
                    if (count <= 0 || (cameras != null && count != cameras.Split(',').Length))
                        throw new InvalidOperationException($"Missing tint cameras: {count} in {tier}-{lighting}");
                    rendered += count;
                    Debug.Log($"TINT_ROUND_CONDITION: OK {round} {tier}-{lighting} rendered={count}");
                }
            Debug.Log($"TINT_ROUND_RESULT: OK {round} rendered={rendered}");
            if (Application.isBatchMode) EditorApplication.Exit(0);
        }
    }
}
