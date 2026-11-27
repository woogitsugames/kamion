using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Game.Editor.VisualQA
{
    /// <summary>far-forest-look-s24 diagnostic: distance / angular size of the far-field forest curtains seen from a QA
    /// camera of a tile scene (no render). Args: -probeScene World_x_High -probeCamera edge-north -probeOut file.txt</summary>
    public static class FarFieldProbe
    {
        static string Arg(string name, string def)
        {
            var a = System.Environment.GetCommandLineArgs();
            int i = System.Array.IndexOf(a, name);
            return i >= 0 && i + 1 < a.Length ? a[i + 1] : def;
        }

        public static void Run()
        {
            var inv = CultureInfo.InvariantCulture;
            string sceneName = Arg("-probeScene", "World_dw671-tykocin-03_High");
            string camId = Arg("-probeCamera", "edge-north");
            string outPath = Arg("-probeOut", "far-probe.txt");
            string path = AssetDatabase.FindAssets("t:Scene " + sceneName).Select(AssetDatabase.GUIDToAssetPath)
                .First(p => Path.GetFileNameWithoutExtension(p) == sceneName);
            EditorSceneManager.OpenScene(path, OpenSceneMode.Single);
            var sb = new StringBuilder();
            foreach (var id in camId.Split(','))
            {
                var camGo = GameObject.Find("QA_" + id);
                if (camGo == null) { sb.AppendLine($"camera {id}: missing"); continue; }
                var cam = camGo.GetComponent<Camera>();
                var planes = GeometryUtility.CalculateFrustumPlanes(cam);
                Vector3 c = cam.transform.position;
                sb.AppendLine($"camera {id} pos {c.ToString("F2")} fov {cam.fieldOfView} far {cam.farClipPlane}");
                foreach (var mr in Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
                {
                    if (!mr.name.StartsWith("FarField_")) continue;
                    var mf = mr.GetComponent<MeshFilter>();
                    var m = mf != null ? mf.sharedMesh : null;
                    if (m == null) continue;
                    var v = m.vertices; var uv2 = new System.Collections.Generic.List<Vector2>(); m.GetUVs(1, uv2);
                    var l2w = mr.transform.localToWorldMatrix;
                    for (int s = 0; s < m.subMeshCount; s++)
                    {
                        var mat = s < mr.sharedMaterials.Length ? mr.sharedMaterials[s] : null;
                        var idx = m.GetTriangles(s);
                        var dist = new System.Collections.Generic.List<float>();
                        var elev = new System.Collections.Generic.List<float>();
                        var dex = new System.Collections.Generic.List<float>();
                        var seen = new System.Collections.Generic.HashSet<int>(idx);
                        foreach (int k in seen)
                        {
                            Vector3 w = l2w.MultiplyPoint3x4(v[k]);
                            bool inside = planes.All(p => p.GetDistanceToPoint(w) > -2f);
                            if (!inside) continue;
                            Vector3 d = w - c;
                            float h = new Vector2(d.x, d.z).magnitude;
                            dist.Add(h); elev.Add(Mathf.Atan2(d.y, h) * Mathf.Rad2Deg);
                            if (uv2.Count > k) dex.Add(uv2[k].x);
                        }
                        if (dist.Count == 0) continue;
                        if (mat != null && mat.IsKeywordEnabled("_HLOD_EDGE"))
                        {
                            // UV Jacobian on the wall plane (s horizontal, y up) of every visible triangle: shear of iso-v
                            // lines and of iso-u lines (trunks), texels from the atlas size.
                            var uv0 = new System.Collections.Generic.List<Vector2>(); m.GetUVs(0, uv0);
                            var tex = mat.GetTexture("_BaseMap");
                            float tw = tex != null ? tex.width : 1024f, th = tex != null ? tex.height : 4096f;
                            var shU = new System.Collections.Generic.List<float>(); var shV = new System.Collections.Generic.List<float>();
                            var areaPx = new System.Collections.Generic.List<float>();
                            for (int t = 0; t < idx.Length; t += 3)
                            {
                                Vector3 a = l2w.MultiplyPoint3x4(v[idx[t]]), b = l2w.MultiplyPoint3x4(v[idx[t + 1]]), cc = l2w.MultiplyPoint3x4(v[idx[t + 2]]);
                                Vector3 mid = (a + b + cc) / 3f;
                                if (!planes.All(p => p.GetDistanceToPoint(mid) > -2f)) continue;
                                Vector3 e1 = b - a, e2 = cc - a;
                                Vector2 hdir = new Vector2(e1.x, e1.z).sqrMagnitude > new Vector2(e2.x, e2.z).sqrMagnitude ? new Vector2(e1.x, e1.z) : new Vector2(e2.x, e2.z);
                                if (hdir.sqrMagnitude < 1e-6f) continue;
                                hdir.Normalize();
                                float s1 = e1.x * hdir.x + e1.z * hdir.y, s2 = e2.x * hdir.x + e2.z * hdir.y;
                                float y1 = e1.y, y2 = e2.y, det = s1 * y2 - s2 * y1;
                                if (Mathf.Abs(det) < 1e-4f) continue;
                                Vector2 ua = uv0[idx[t]], d1 = uv0[idx[t + 1]] - ua, d2 = uv0[idx[t + 2]] - ua;
                                float duds = (d1.x * y2 - d2.x * y1) / det * tw, dudy = (-d1.x * s2 + d2.x * s1) / det * tw;
                                float dvds = (d1.y * y2 - d2.y * y1) / det * th, dvdy = (-d1.y * s2 + d2.y * s1) / det * th;
                                shU.Add(Mathf.Atan2(Mathf.Abs(dudy), Mathf.Abs(duds)) * Mathf.Rad2Deg);
                                shV.Add(Mathf.Atan2(Mathf.Abs(dvds), Mathf.Abs(dvdy)) * Mathf.Rad2Deg);
                            }
                            if (shU.Count > 0)
                            {
                                shU.Sort(); shV.Sort();
                                float Q(System.Collections.Generic.List<float> a, float q) => a[Mathf.Clamp((int)(q * (a.Count - 1)), 0, a.Count - 1)];
                                sb.AppendLine(string.Format(inv, "    uv shear (deg) of {0} visible tris: iso-u (trunk tilt) p50/p95/max {1:F1}/{2:F1}/{3:F1}; iso-v p50/p95/max {4:F1}/{5:F1}/{6:F1}; tex {7}x{8}",
                                    shU.Count, Q(shU, .5f), Q(shU, .95f), shU[shU.Count - 1], Q(shV, .5f), Q(shV, .95f), shV[shV.Count - 1], tw, th));
                            }
                        }
                        dist.Sort(); elev.Sort(); dex.Sort();
                        float P(System.Collections.Generic.List<float> a, float q) => a[Mathf.Clamp((int)(q * (a.Count - 1)), 0, a.Count - 1)];
                        sb.AppendLine(string.Format(inv, "  {0} sub{1} {2}: verts in view {3}; horiz dist p1/p10/p50/p90 {4:F0}/{5:F0}/{6:F0}/{7:F0} m; elev deg p50/p99/max {8:F2}/{9:F2}/{10:F2}; uv1.x p10/p50/p90 {11:F0}/{12:F0}/{13:F0}",
                            mr.name, s, mat != null ? mat.name + " [" + mat.shader.name + " " + string.Join(" ", mat.shaderKeywords) + "]" : "null",
                            dist.Count, P(dist, .01f), P(dist, .1f), P(dist, .5f), P(dist, .9f), P(elev, .5f), P(elev, .99f), elev[elev.Count - 1],
                            dex.Count > 0 ? P(dex, .1f) : -1, dex.Count > 0 ? P(dex, .5f) : -1, dex.Count > 0 ? P(dex, .9f) : -1));
                    }
                }
            }
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outPath)));
            File.WriteAllText(outPath, sb.ToString());
            Debug.Log("[PROBE]\n" + sb);
        }
    }
}
