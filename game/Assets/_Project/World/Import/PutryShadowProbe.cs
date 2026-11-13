using System;
using System.Collections.Generic;
using System.IO;
using Game.Editor.Build;
using Game.Rendering;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.World.Import
{
    /// <summary>Read-only Editor ADR0155 diagnostic; never saves or modifies a scene.</summary>
    public static class PutryShadowProbe
    {
        [Serializable] public class Caster { public string path, mode, shader; public string[] materials; public Vector3 min, max; public int submeshes, triangles; }
        [Serializable] public class SceneRecord { public string tier; public float distance, depthBias, normalBias, sunBias, sunNormalBias; public int resolution, cascades; public Caster[] casters, heroLods; }
        [Serializable] public class Report { public string mode; public SceneRecord[] scenes; }
        public static void RunBatch()
        {
            int exit = 1;
            try
            {
                string mode = EditorTools.Arg("-putryMode", "report");
                if (mode != "report") throw new ArgumentException("Read-only diagnostic supports report only");
                var report = new Report { mode = mode };
                var scenes = new List<SceneRecord>();
                foreach (string tier in new[] { "Low", "High" })
                {
                    var scene = EditorSceneManager.OpenScene($"Assets/_Generated/World/bialystok-industrial-c/{WorldSceneBuilder.SceneNameFor("bialystok-industrial-c", tier)}.unity", OpenSceneMode.Single);
                    var root = UnityEngine.Object.FindFirstObjectByType<WorldRegionRoot>();
                    if (root == null) throw new InvalidOperationException("Missing world root");
                    var list = new List<Caster>();
                    foreach (var mr in root.GetComponentsInChildren<MeshRenderer>(true))
                    {
                        if (mr.name != "bridge") continue;
                        var b = mr.bounds;
                        if (b.max.x < 500 || b.min.x > 600 || b.max.z < -750 || b.min.z > -650) continue;
                        var mesh = mr.GetComponent<MeshFilter>().sharedMesh;
                        var mats = mr.sharedMaterials;
                        var names = new string[mats.Length]; for (int i = 0; i < mats.Length; i++) names[i] = mats[i] != null ? mats[i].name : "MISSING";
                        list.Add(new Caster { path = mr.transform.parent.name + "/" + mr.name, mode = mr.shadowCastingMode.ToString(), shader = mats.Length > 0 && mats[0] != null ? mats[0].shader.name : "MISSING", materials = names, min = b.min, max = b.max, submeshes = mesh.subMeshCount, triangles = mesh.triangles.Length / 3 });
                    }
                    if (list.Count == 0) throw new InvalidOperationException("No Putry bridge casters found");
                    var heroLods = new List<Caster>();
                    var set = root.GetComponent<WorldInstances>().set;
                    foreach (var proto in set.prototypes)
                    {
                        if (!proto.name.StartsWith("landmark_viaduct_biezenstwa", StringComparison.Ordinal)) continue;
                        for (int lod = 0; lod < proto.lods.Length; lod++)
                        {
                            var mesh = proto.lods[lod]; if (mesh == null) continue;
                            int start = proto.materialStart[lod];
                            var names = new string[mesh.subMeshCount];
                            for (int i = 0; i < names.Length; i++)
                            {
                                int mi = start + i;
                                names[i] = set.materials[mi].name + (Array.IndexOf(set.noShadowMaterials, mi) >= 0 ? " [no shadows]" : "");
                            }
                            heroLods.Add(new Caster { path = proto.name + "/lod" + lod, mode = (proto.shadowLodMask & (1 << lod)) != 0 ? "On" : "Off", materials = names, min = mesh.bounds.min, max = mesh.bounds.max, submeshes = mesh.subMeshCount, triangles = mesh.triangles.Length / 3 });
                        }
                    }
                    var profile = QualityProfile.Load();
                    if (profile == null || !profile.TryGet(tier, out var t)) throw new InvalidOperationException("Missing quality tier");
                    var sun = GameObject.Find("Sun").GetComponent<Light>();
                    scenes.Add(new SceneRecord { tier = tier, distance = t.shadowDistance, resolution = t.shadowResolution, cascades = t.shadowCascades, depthBias = t.shadowDepthBias, normalBias = t.shadowNormalBias, sunBias = sun.shadowBias, sunNormalBias = sun.shadowNormalBias, casters = list.ToArray(), heroLods = heroLods.ToArray() });
                }
                report.scenes = scenes.ToArray();
                string output = EditorTools.Arg("-putryOutput", "../artifacts/gpt-s16-r3");
                Directory.CreateDirectory(output);
                File.WriteAllText(Path.Combine(output, "diagnostic-" + mode + ".json"), JsonUtility.ToJson(report, true));
                Debug.Log("PUTRY_SHADOW_PROBE: OK mode=" + mode);
                exit = 0;
            }
            catch (Exception e) { Debug.LogException(e); }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }
    }
}
