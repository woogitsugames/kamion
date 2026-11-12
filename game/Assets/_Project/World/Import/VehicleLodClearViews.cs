using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Game.Editor.Build;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Game.World.Import
{
    /// <summary>Editor-only supplement: choose real parked instances with static-collider sight lines at LOD boundaries.</summary>
    public static class VehicleLodClearViews
    {
        [Serializable] public class CameraEntry
        {
            public string id, kind = "photo_match", seat = "file", note;
            public float[] pos, look_at;
            public float fov_deg = 60;
            public int clearSamples, totalSamples = 9, nativeIndex;
        }
        [Serializable] public class CameraFile { public CameraEntry[] cameras; }

        public static void RunBatch()
        {
            EditorSceneManager.OpenScene("Assets/_Generated/World/bialystok-industrial-c/WorldC.unity");
            foreach (var c in UnityEngine.Object.FindObjectsByType<WorldCollisionCooker>(FindObjectsInactive.Include, FindObjectsSortMode.None)) c.Cook();
            Physics.SyncTransforms();
            var set = AssetDatabase.LoadAssetAtPath<WorldInstanceSet>("Assets/_Generated/World/bialystok-industrial-c/Instances.asset");
            var cameras = new List<CameraEntry>();
            var families = new[] { "car_hatch_white", "car_suv_black", "tractor_blue", "trailer_curtain_0", "trailer_reefer_0" };
            foreach (string family in families)
            {
                int proto = Array.FindIndex(set.prototypes, p => p.name == family);
                if (proto < 0) throw new InvalidOperationException("Missing prototype " + family);
                bool car = family.StartsWith("car_"), reefer = family == "trailer_reefer_0";
                foreach (string tier in new[] { "Low", "High" })
                {
                    float[] boundaries = car ? (tier == "Low" ? new[] { 16f, 42.5f } : new[] { 37.5f, 127.5f })
                        : (tier == "Low" ? new[] { 20f, 50f } : new[] { 60f, 150f });
                    foreach (float boundary in boundaries)
                    {
                        int bestScore = -1, bestIndex = -1; float bestAngle = 0; Vector3 bestLook = default;
                        foreach (var run in set.runs.Where(r => r.prototype == proto))
                            for (int index = run.start; index < run.start + run.count; index++)
                            {
                                var matrix = set.LocalMatrix(index);
                                var bounds = set.prototypes[proto].lods[0].bounds;
                                Vector3 look = matrix.MultiplyPoint3x4(reefer ? new Vector3(0, 3.32f, 14.025f) : bounds.center);
                                var selfBounds = bounds; selfBounds.Expand(.15f);
                                var inverse = matrix.inverse;
                                for (int a = 0; a < 24; a++)
                                {
                                    float angle = a * Mathf.PI / 12;
                                    if (reefer && Mathf.Sin(angle) < .85f) continue; // front of the condenser, not its culled back face
                                    int score = 0;
                                    foreach (float distance in new[] { boundary - .1f, boundary + .1f })
                                    {
                                        Vector3 pos = Position(set, index, angle, distance);
                                        for (int sample = 0; sample < 9; sample++)
                                        {
                                            Vector3 point = look;
                                            if (sample < 8)
                                            {
                                                Vector3 local = bounds.center + Vector3.Scale(bounds.extents * .65f,
                                                    new Vector3((sample & 1) == 0 ? -1 : 1, (sample & 2) == 0 ? -1 : 1, (sample & 4) == 0 ? -1 : 1));
                                                point = reefer ? look + matrix.MultiplyVector(new Vector3((sample % 3 - 1) * .5f, (sample / 3 - 1) * .2f, 0)) : matrix.MultiplyPoint3x4(local);
                                            }
                                            Vector3 delta = point - pos;
                                            bool blocked = Physics.RaycastAll(pos, delta.normalized, delta.magnitude - .05f, ~0, QueryTriggerInteraction.Ignore)
                                                .Any(h => !selfBounds.Contains(inverse.MultiplyPoint3x4(h.point)));
                                            if (!blocked) score++;
                                        }
                                    }
                                    if (score > bestScore)
                                    { bestScore = score; bestIndex = index; bestAngle = angle; bestLook = look; }
                                }
                            }
                        if (bestIndex < 0) throw new InvalidOperationException("No candidate " + family);
                        foreach (float distance in new[] { boundary - .1f, boundary + .1f })
                        {
                            Vector3 pos = Position(set, bestIndex, bestAngle, distance);
                            cameras.Add(new CameraEntry { id = $"clear_{family}_{tier}_{distance:000.0}".Replace('.', 'p').Replace(',', 'p'),
                                pos = new[] { pos.x, pos.z, pos.y }, look_at = new[] { bestLook.x, bestLook.z, bestLook.y },
                                clearSamples = bestScore, totalSamples = 18, nativeIndex = bestIndex,
                                note = "ADR0153 supplementary static-collider visibility search; actual native instance; source pose WORKING_VALUE. Collider sampling is not visual acceptance." });
                        }
                        Debug.Log($"LOD_CLEAR_VIEW {family} {tier} boundary={boundary} score={bestScore}/18 index={bestIndex}");
                    }
                }
            }
            string output = Path.Combine(EditorTools.RepoRoot, "artifacts/gpt-s16-r1/clear-cameras.json");
            File.WriteAllText(output, JsonUtility.ToJson(new CameraFile { cameras = cameras.ToArray() }, true));
            Debug.Log("LOD_CLEAR_VIEWS: OK cameras=" + cameras.Count);
        }

        static Vector3 Position(WorldInstanceSet set, int index, float angle, float distance)
        {
            float horizontal = Mathf.Sqrt(distance * distance - 1.6f * 1.6f);
            var direction = set.LocalMatrix(index).MultiplyVector(new Vector3(Mathf.Cos(angle), 0, Mathf.Sin(angle))).normalized;
            return set.LocalPosition(index) + direction * horizontal + Vector3.up * 1.6f;
        }

    }
}
