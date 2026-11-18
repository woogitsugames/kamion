using System;
using System.Collections.Generic;
using System.IO;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using EditorTools = Game.Editor.Build.EditorTools;

namespace Game.Editor.Setup
{
    /// <summary>
    /// ADR 0297: veiling-glare halo around the red rear signal lamps (Kamion/Truck Lamp Halo). From the LOD0 lamp emitters
    /// (uv2 'Data': x = light group, y = emissive mask, manifest shader_contract) it builds one quad per emitter cluster:
    /// all four corners at the area-weighted cluster centre, normal = area-weighted lens normal, uv0 = corner, uv1 = (group,
    /// emitter area m^2). The shader expands the quad to a camera-facing halo and reads the lamp state from TruckLights'
    /// global texture, so no runtime component and one draw per vehicle part. Pure function of the exported FBX (rule 7).
    /// </summary>
    public static class TruckLampHaloBuilder
    {
        /// <summary>Red rear signals: tractor tail+stop chamber, rear markers, rear fog, trailer tail / stop chambers.</summary>
        public static readonly int[] HaloGroups =
            { LampPhotometry.TailBrake, LampPhotometry.MarkerRear, LampPhotometry.FogRear, LampPhotometry.Tail, LampPhotometry.Stop };

        public const string ShaderName = "Kamion/Truck Lamp Halo";
        /// <summary>Material values (WORKING_VALUE, judged on renders; = shader defaults, set on every rebuild because an
        /// existing material keeps its serialized values).</summary>
        public const float HaloK = 0.25f, HaloMaxDeg = 2f, HaloCap = 0.5f;

        public struct Cluster
        {
            public int group;
            public Vector3 centre, normal;
            public float area;
        }

        /// <summary>Emitter triangles of <paramref name="groups"/> merged greedily into clusters (same group, centroid within
        /// <paramref name="mergeM"/> of the running cluster centre).</summary>
        public static List<Cluster> Clusters(Mesh mesh, ICollection<int> groups, float mergeM = 0.15f)
        {
            var result = new List<Cluster>();
            if (mesh == null) return result;
            var data = new List<Vector4>();
            mesh.GetUVs(2, data);
            if (data.Count != mesh.vertexCount) return result;
            var v = mesh.vertices;
            var sums = new List<(int g, Vector3 c, Vector3 n, float a)>();
            for (int sm = 0; sm < mesh.subMeshCount; sm++)
            {
                var tri = mesh.GetTriangles(sm);
                for (int t = 0; t + 2 < tri.Length; t += 3)
                {
                    int i0 = tri[t], i1 = tri[t + 1], i2 = tri[t + 2];
                    if (data[i0].y < 0.5f || data[i1].y < 0.5f || data[i2].y < 0.5f) continue;
                    int g = Mathf.RoundToInt(data[i0].x);
                    if (g != Mathf.RoundToInt(data[i1].x) || g != Mathf.RoundToInt(data[i2].x) || !groups.Contains(g)) continue;
                    Vector3 cr = Vector3.Cross(v[i1] - v[i0], v[i2] - v[i0]);
                    float a = cr.magnitude * 0.5f;
                    if (a < 1e-9f) continue;
                    Vector3 c = (v[i0] + v[i1] + v[i2]) / 3f;
                    int best = -1;
                    for (int k = 0; k < sums.Count; k++)
                        if (sums[k].g == g && (sums[k].c / sums[k].a - c).sqrMagnitude < mergeM * mergeM) { best = k; break; }
                    if (best < 0) sums.Add((g, c * a, cr, a));
                    // Double-sided / back-facing lens triangles (the tractor's cab rear markers) cancel in a plain sum: align
                    // each triangle normal with the cluster's running normal first.
                    else sums[best] = (g, sums[best].c + c * a, sums[best].n + (Vector3.Dot(sums[best].n, cr) < 0f ? -cr : cr), sums[best].a + a);
                }
            }
            foreach (var s in sums)
                result.Add(new Cluster { group = s.g, centre = s.c / s.a, normal = s.n.sqrMagnitude > 1e-12f ? s.n.normalized : Vector3.back, area = s.a });
            return result;
        }

        public static Mesh BuildMesh(IList<Cluster> clusters, string name)
        {
            int n = clusters.Count;
            var pos = new Vector3[n * 4];
            var nor = new Vector3[n * 4];
            var uv0 = new Vector2[n * 4];
            var uv1 = new Vector2[n * 4];
            var idx = new int[n * 6];
            var corners = new[] { new Vector2(-1f, -1f), new Vector2(1f, -1f), new Vector2(1f, 1f), new Vector2(-1f, 1f) };
            var b = new Bounds();
            for (int i = 0; i < n; i++)
            {
                var c = clusters[i];
                for (int k = 0; k < 4; k++)
                {
                    pos[i * 4 + k] = c.centre; nor[i * 4 + k] = c.normal; uv0[i * 4 + k] = corners[k];
                    uv1[i * 4 + k] = new Vector2(c.group, c.area);
                }
                idx[i * 6] = i * 4; idx[i * 6 + 1] = i * 4 + 1; idx[i * 6 + 2] = i * 4 + 2;
                idx[i * 6 + 3] = i * 4; idx[i * 6 + 4] = i * 4 + 2; idx[i * 6 + 5] = i * 4 + 3;
                if (i == 0) b = new Bounds(c.centre, Vector3.zero); else b.Encapsulate(c.centre);
            }
            var m = new Mesh { name = name };
            m.vertices = pos; m.normals = nor; m.uv = uv0; m.uv2 = uv1;
            m.SetIndices(idx, MeshTopology.Triangles, 0);
            // The quad grows to a camera-facing halo in the vertex shader (up to ~2 deg x distance): pad the bounds by 1 m
            // so the halo is not frustum-culled with its centre point.
            b.Expand(2f);
            m.bounds = b;
            return m;
        }

        public static Material EnsureMaterial(string matDir)
        {
            Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, matDir));
            string p = $"{matDir}/M_TruckLampHalo.mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(p);
            var sh = Shader.Find(ShaderName);
            if (sh == null) throw new InvalidOperationException($"shader {ShaderName} missing");
            if (m == null) { m = new Material(sh) { name = "M_TruckLampHalo" }; AssetDatabase.CreateAsset(m, p); }
            m.shader = sh;
            m.SetFloat("_HaloK", HaloK); m.SetFloat("_HaloMaxDeg", HaloMaxDeg); m.SetFloat("_HaloCap", HaloCap);
            m.renderQueue = (int)RenderQueue.Transparent + 40;
            EditorUtility.SetDirty(m);
            return m;
        }

        /// <summary>Adds a "LampHalo" child (identity transform) to every LOD0 renderer whose mesh has red rear emitters.
        /// Returns the number of halo quads.</summary>
        public static int Attach(IEnumerable<Renderer> lod0, string meshDir, Material mat, string prefix)
        {
            Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, meshDir));
            int quads = 0;
            var groups = new HashSet<int>(HaloGroups);
            foreach (var r in lod0)
            {
                var mf = r != null ? r.GetComponent<MeshFilter>() : null;
                if (mf == null || mf.sharedMesh == null) continue;
                var cs = Clusters(mf.sharedMesh, groups);
                if (cs.Count == 0) continue;
                var mesh = BuildMesh(cs, $"{prefix}_LampHalo_{r.name}");
                string path = $"{meshDir}/{mesh.name}.asset";
                var old = AssetDatabase.LoadAssetAtPath<Mesh>(path);
                if (old != null) { EditorUtility.CopySerialized(mesh, old); UnityEngine.Object.DestroyImmediate(mesh); EditorUtility.SetDirty(old); mesh = old; }
                else AssetDatabase.CreateAsset(mesh, path);
                var go = new GameObject("LampHalo", typeof(MeshFilter), typeof(MeshRenderer));
                go.layer = r.gameObject.layer;
                go.transform.SetParent(r.transform, false);
                go.GetComponent<MeshFilter>().sharedMesh = mesh;
                var mr = go.GetComponent<MeshRenderer>();
                mr.sharedMaterial = mat;
                mr.shadowCastingMode = ShadowCastingMode.Off;
                mr.receiveShadows = false;
                mr.lightProbeUsage = LightProbeUsage.Off;
                mr.reflectionProbeUsage = ReflectionProbeUsage.Off;
                mr.allowOcclusionWhenDynamic = false;
                quads += cs.Count;
                foreach (var c in cs)
                    Debug.Log($"[LAMP_HALO] {prefix} {r.name} group {c.group} centre {c.centre:F3} normal {c.normal:F2} area {c.area * 1e4f:F1} cm2");
            }
            return quads;
        }
    }
}
