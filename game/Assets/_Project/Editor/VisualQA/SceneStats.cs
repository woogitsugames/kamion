using System.Collections.Generic;
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
        public static string Estimate(Camera cam, float shadowDistance, int cascades, string id)
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
            int draws = 0, shadowDraws = 0, objects = 0;
            long tris = 0;
            foreach (var r in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
            {
                if (!r.enabled || !r.gameObject.activeInHierarchy) continue;
                if (inLodGroup.Contains(r) && !selected.Contains(r)) continue;
                if ((cam.cullingMask & (1 << r.gameObject.layer)) == 0) continue;
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
                    for (int s = 0; s < m.subMeshCount; s++) tris += (long)m.GetIndexCount(s) / 3;
                }
                if (r.shadowCastingMode != ShadowCastingMode.Off && dist < shadowDistance) shadowDraws += m.subMeshCount * Mathf.Max(1, cascades);
            }
            return $"{id}: objects={objects} drawsEst={draws} shadowDrawsEst={shadowDraws} trisK={tris / 1000} (estimate, before SRP batching)";
        }
    }
}
