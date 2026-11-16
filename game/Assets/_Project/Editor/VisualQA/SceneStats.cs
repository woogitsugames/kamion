using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Editor.VisualQA
{
    /// <summary>
    /// CPU-side ESTIMATE of what a camera draws (no GPU counters in batchmode): frustum-culled renderers after LOD
    /// selection (QualitySettings.lodBias), submeshes = draw calls before SRP batching, triangles, plus shadow-caster
    /// draws (casters within the shadow distance × cascades). Not a measurement - the phone numbers come from
    /// scripts/device-metrics.ps1. Written to stats.txt next to the visual-QA PNGs.
    /// </summary>
    public static class SceneStats
    {
        public static string Estimate(Camera cam, float shadowDistance, int cascades, string id, string detailPath = null)
        {
            var planes = GeometryUtility.CalculateFrustumPlanes(cam);
            var selected = new HashSet<Renderer>();
            var inLodGroup = new HashSet<Renderer>();
            float tanHalf = Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad);
            foreach (var lg in Object.FindObjectsByType<LODGroup>(FindObjectsSortMode.None))
            {
                var lods = lg.GetLODs();
                foreach (var l in lods) foreach (var r in l.renderers) if (r != null) inLodGroup.Add(r);
                Vector3 c = lg.transform.TransformPoint(lg.localReferencePoint);
                float d = Vector3.Distance(cam.transform.position, c);
                float h = lg.size / (2f * Mathf.Max(d, 0.01f) * tanHalf) * QualitySettings.lodBias;
                for (int i = 0; i < lods.Length; i++)
                {
                    if (h < lods[i].screenRelativeTransitionHeight && i < lods.Length - 1) continue;
                    if (h < lods[i].screenRelativeTransitionHeight) break; // culled
                    foreach (var r in lods[i].renderers) if (r != null) selected.Add(r);
                    break;
                }
            }
            var details = string.IsNullOrEmpty(detailPath) ? null : new StringBuilder("camera\trenderer_path\tmesh\tsubmesh\tmaterial\tshader\ttriangles\tdraws\n");
            int draws = 0, shadowDraws = 0, objects = 0;
            long tris = 0;
            foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            {
                if (!r.enabled || !r.gameObject.activeInHierarchy) continue;
                if (inLodGroup.Contains(r) && !selected.Contains(r)) continue;
                if ((cam.cullingMask & (1 << r.gameObject.layer)) == 0) continue;
                if (Game.World.PlotViewCull.HiddenFor(cam, r)) continue;   // ADR 0124: house plots beyond 70 m in mirror cameras
                var mf = r.GetComponent<MeshFilter>();
                if (mf == null || mf.sharedMesh == null) continue;
                var b = r.bounds;
                float dist = Mathf.Sqrt(b.SqrDistance(cam.transform.position));
                if (dist > cam.farClipPlane) continue;
                bool visible = GeometryUtility.TestPlanesAABB(planes, b);
                var m = mf.sharedMesh;
                if (visible)
                {
                    objects++;
                    draws += m.subMeshCount;
                    var materials = details != null ? r.sharedMaterials : null;
                    for (int s = 0; s < m.subMeshCount; s++)
                    {
                        long count = (long)m.GetIndexCount(s) / 3;
                        tris += count;
                        if (details != null)
                        {
                            var material = s < materials.Length ? materials[s] : null;
                            details.Append(Clean(id)).Append('\t').Append(Clean(PathOf(r.transform))).Append('\t')
                                .Append(Clean(m.name)).Append('\t').Append(s).Append('\t')
                                .Append(Clean(material != null ? material.name : "<missing>" )).Append('\t')
                                .Append(Clean(material != null && material.shader != null ? material.shader.name : "<missing>"))
                                .Append('\t').Append(count).Append("\t1\n");
                        }
                    }
                }
                if (r.shadowCastingMode != ShadowCastingMode.Off && dist < shadowDistance) shadowDraws += m.subMeshCount * Mathf.Max(1, cascades);
            }
            if (details != null)
            {
                string path = Path.GetFullPath(detailPath);
                Directory.CreateDirectory(Path.GetDirectoryName(path));
                File.WriteAllText(path, details.ToString());
            }
            return $"{id}: objects={objects} drawsEst={draws} shadowDrawsEst={shadowDraws} trisK={tris / 1000} trisExact={tris} (estimate, before SRP batching)";
        }

        static string Clean(string value) => (value ?? "").Replace('\t', ' ').Replace('\r', ' ').Replace('\n', ' ');

        static string PathOf(Transform tr)
        {
            string path = tr.name;
            while (tr.parent != null) { tr = tr.parent; path = tr.name + "/" + path; }
            return path;
        }
    }
}
