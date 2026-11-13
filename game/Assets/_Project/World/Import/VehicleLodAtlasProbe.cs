using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Game.Editor.Build;
using Game.Rendering;
using UnityEditor;
using UnityEngine;
using static Game.World.Import.MiniJson;

namespace Game.World.Import
{
    /// <summary>ADR0153 editor-only measurement of actual native instances and authored transition-camera projections.</summary>
    public static class VehicleLodAtlasProbe
    {
        [Serializable] public class Entry { public string id; public float[] pos, look_at; public float fov_deg; }
        [Serializable] public class CameraFile { public Entry[] cameras; }
        [Serializable] public class Row
        {
            public string camera, prototype, tier;
            public float originDistanceM, lodBias, renderScale;
            public int selectedLod, submeshes, triangles;
            public bool lod1Lod2SameMesh, behindCamera;
            public float[] projectedRectTopLeft;
        }
        [Serializable] public class Report
        {
            public string source = "Unity editor native InstanceSet + Camera projection; no occlusion test, no GPU/device timing";
            public int width = 2340, height = 1080;
            public List<Row> rows = new List<Row>();
        }

        public static void RunBatch()
        {
            string repo = EditorTools.RepoRoot;
            string folder = Path.Combine(repo, "artifacts/gpt-s16-r1");
            var cameras = JsonUtility.FromJson<CameraFile>(File.ReadAllText(Path.Combine(folder, "qa-cameras.json"))).cameras;
            var targets = Arr(Parse(File.ReadAllText(Path.Combine(folder, "qa-targets.json"))))
                .Select(Obj).ToDictionary(t => Str(t.Get("p")));
            var set = AssetDatabase.LoadAssetAtPath<WorldInstanceSet>("Assets/_Generated/World/bialystok-industrial-c/Instances.asset");
            if (set == null) throw new InvalidOperationException("Import the candidate region first");
            var profile = QualityProfile.Load();
            var report = new Report();
            var go = new GameObject("VehicleLodProjectionProbe");
            try
            {
                var camera = go.AddComponent<Camera>();
                camera.enabled = false; camera.aspect = (float)report.width / report.height;
                foreach (var target in targets)
                {
                    int proto = Array.FindIndex(set.prototypes, p => p.name == target.Key);
                    var p = set.prototypes[proto];
                    var expected = new Vector3((float)Num(target.Value.Get("e")), (float)Num(target.Value.Get("z")), (float)Num(target.Value.Get("n")));
                    int index = -1; float best = float.MaxValue;
                    foreach (var run in set.runs.Where(r => r.prototype == proto))
                        for (int i = run.start; i < run.start + run.count; i++)
                        {
                            float d = (set.LocalPosition(i) - expected).sqrMagnitude;
                            if (d < best) { best = d; index = i; }
                        }
                    if (index < 0 || best > .01f) throw new InvalidOperationException("Native target mismatch: " + target.Key);
                    var matrix = set.LocalMatrix(index);
                    foreach (var entry in cameras.Where(c => c.id.StartsWith("lod_" + target.Key + "_", StringComparison.Ordinal)))
                    {
                        camera.transform.position = new Vector3(entry.pos[0], entry.pos[2], entry.pos[1]);
                        camera.transform.LookAt(new Vector3(entry.look_at[0], entry.look_at[2], entry.look_at[1]));
                        camera.fieldOfView = entry.fov_deg;
                        float distance = Vector3.Distance(camera.transform.position, set.LocalPosition(index));
                        foreach (string tierName in new[] { "Low", "High" })
                        {
                            if (!profile.TryGet(tierName, out var tier)) throw new InvalidOperationException("Missing tier " + tierName);
                            float cullScale = (tier.vehicleCullM > 0 ? tier.vehicleCullM : WorldInstances.VehicleCullM) / WorldInstances.VehicleCullM;
                            int lod = WorldInstances.LodAt(p.lodEndM, distance, tier.lodBias, cullScale, WorldInstances.VehicleLod0MinM);
                            var mesh = p.lods[Mathf.Max(lod, 0)];
                            var bounds = mesh.bounds;
                            var projection = camera.projectionMatrix * camera.worldToCameraMatrix * matrix;
                            Vector2 lo = new Vector2(float.MaxValue, float.MaxValue), hi = -lo;
                            bool behind = false;
                            for (int corner = 0; corner < 8; corner++)
                            {
                                Vector3 v = bounds.center + Vector3.Scale(bounds.extents,
                                    new Vector3((corner & 1) == 0 ? -1 : 1, (corner & 2) == 0 ? -1 : 1, (corner & 4) == 0 ? -1 : 1));
                                Vector4 clip = projection * new Vector4(v.x, v.y, v.z, 1);
                                behind |= clip.w <= 0;
                                var screen = new Vector2((clip.x / clip.w * .5f + .5f) * report.width,
                                    (.5f - clip.y / clip.w * .5f) * report.height);
                                lo = Vector2.Min(lo, screen); hi = Vector2.Max(hi, screen);
                            }
                            report.rows.Add(new Row { camera = entry.id, prototype = p.name, tier = tierName,
                                originDistanceM = distance, lodBias = tier.lodBias, renderScale = tier.renderScale,
                                selectedLod = lod, submeshes = lod < 0 ? 0 : mesh.subMeshCount,
                                triangles = lod < 0 ? 0 : Enumerable.Range(0, mesh.subMeshCount).Sum(s => (int)mesh.GetIndexCount(s) / 3),
                                lod1Lod2SameMesh = p.lods[1] == p.lods[2], behindCamera = behind,
                                projectedRectTopLeft = new[] { lo.x, lo.y, hi.x - lo.x, hi.y - lo.y } });
                        }
                    }
                }
                File.WriteAllText(Path.Combine(folder, "projection-probe.json"), JsonUtility.ToJson(report, true));
                Debug.Log("VEHICLE_LOD_PROBE: OK rows=" + report.rows.Count);
            }
            finally { UnityEngine.Object.DestroyImmediate(go); }
        }
    }
}
