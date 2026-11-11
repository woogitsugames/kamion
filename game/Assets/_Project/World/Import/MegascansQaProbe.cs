using System;
using System.Globalization;
using System.IO;
using Game.Editor.Build;
using Game.Gameplay;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Game.World.Import
{
    /// <summary>Artifact-only driver-camera proof; never edits or saves a production scene.</summary>
    public static class MegascansQaProbe
    {
        public static void ValidateDetailCameras()
        {
            int exit = 1;
            try
            {
                string region = EditorTools.Arg("-region", "bialystok-industrial-c");
                string file = EditorTools.Arg("-qaGate3", null);
                string output = EditorTools.Arg("-qaProof", Path.Combine(EditorTools.RepoRoot, "artifacts/megascans-r1/detail-ground-proof.csv"));
                EditorSceneManager.OpenScene($"Assets/_Generated/World/{region}/WorldC.unity");
                foreach (var cooker in UnityEngine.Object.FindObjectsByType<WorldCollisionCooker>(FindObjectsInactive.Include, FindObjectsSortMode.None)) cooker.Cook();
                Physics.SyncTransforms();
                var root = UnityEngine.Object.FindAnyObjectByType<WorldRegionRoot>();
                var cameras = Gate3Cameras.Parse(File.ReadAllText(file));
                if (root == null || cameras?.cameras == null) throw new InvalidOperationException("World root / detail camera input missing");
                Directory.CreateDirectory(Path.GetDirectoryName(output));
                int failures = 0;
                using (var writer = new StreamWriter(output))
                {
                    writer.WriteLine("camera,hit,eye_height_m,expected_eye_m,status");
                    foreach (var camera in cameras.cameras)
                    {
                        Vector3 position = root.LocalToUnity(camera.pos[0], camera.pos[1], camera.pos[2]);
                        bool hit = Gate3Cameras.TryGroundY(position.x, position.z, position.y + 4f, null, out float ground);
                        float height = position.y - ground;
                        bool pass = hit && Mathf.Abs(height - 2.3f) <= 0.03f;
                        if (!pass) failures++;
                        writer.WriteLine($"{camera.id},{hit},{height.ToString("F6", CultureInfo.InvariantCulture)},2.3,{(pass ? "PASS" : "FAIL")}");
                    }
                }
                if (failures != 0) throw new InvalidOperationException($"{failures} detail cameras fail the road-collision eye-height check: {output}");
                Debug.Log("MEGASCANS_CAMERA_PROOF: OK " + output);
                exit = 0;
            }
            catch (Exception e) { Debug.LogException(e); }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }
    }
}
