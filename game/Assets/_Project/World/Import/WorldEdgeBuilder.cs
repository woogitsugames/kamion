using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Game.Editor.Build;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using static Game.World.Import.MiniJson;

namespace Game.World.Import
{
    /// <summary>
    /// Edge of the imported region (ADR 0082, ADR 0085). The generated data stop at the region bbox; before this builder
    /// the roads ran into a white void there and the vehicle fell out of the world (owner recording 2026-11-10, 116 s).
    /// Built at import, in region-root space:
    /// - <see cref="WorldBoundary"/> on the region root (drivable rectangle + closures) for the runtime safety net,
    /// - an apron: the terrain border extruded outwards to beyond the far clip plane (no collision; the safety net
    ///   recovers a vehicle that gets there), with ground-mask vertex colours (forest floor, unmown meadow, soil),
    /// - a straight road stub graded onto the apron behind every main road that leaves the region,
    /// - a road closure <see cref="ClosureSetbackM"/> inside the edge on each of those roads: a row of concrete
    ///   barriers with a red/white U-20 board on posts, and a box collider (the physical end of the road),
    /// - a 4-sector far-field backdrop (<c>FarField_far_north</c>, <c>FarField_far_east</c>, <c>FarField_far_south</c>,
    ///   <c>FarField_far_west</c>) built from real GUGiK BDOT10k + LoD1 + OSM ring data (ADR 0085), shadow-free and
    ///   collider-free.
    /// </summary>
    public static class WorldEdgeBuilder
    {
        /// <summary>Closures stand this far inside the region edge, measured along the road [m].</summary>
        public const float ClosureSetbackM = 60f;
        public const float ApronReachM = 2600f;
        public const float ApronEaseM = 600f;
        public const float StubLengthM = 420f;
        const float SampleStepM = 16f;
        static readonly float[] k_RingDist = { -1f, 0f, 30f, 80f, 160f, 280f, 440f, 600f, ApronReachM };
        static readonly string[] k_FarSectors = { "far_north", "far_east", "far_south", "far_west" };

        /// <summary>Batch entry point to rebuild WorldEdge (apron + closures + far-field) in WorldC and WorldC_High in place.</summary>
        public static void RebuildEdgeBatch()
        {
            int exit = 1;
            try
            {
                string region = EditorTools.Arg("-region", "bialystok-industrial-c");
                var r = RegionImporter.LoadForEdge(region);
                foreach (var tier in RegionImporter.Tiers)
                {
                    string scenePath = r.ScenePath(tier);
                    if (!File.Exists(Path.Combine(EditorTools.ProjectRoot, scenePath))) continue;
                    var scene = EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
                    var rootGo = GameObject.Find("Region_" + region);
                    if (rootGo == null) throw new InvalidOperationException($"Region_{region} not found in {scenePath}");
                    foreach (var wb in rootGo.GetComponents<WorldBoundary>()) UnityEngine.Object.DestroyImmediate(wb);
                    var oldEdge = rootGo.transform.Find("WorldEdge");
                    if (oldEdge != null) UnityEngine.Object.DestroyImmediate(oldEdge.gameObject);
                    var mcs = rootGo.GetComponentsInChildren<MeshCollider>(true);
                    foreach (var mc in mcs) mc.enabled = true;
                    Physics.SyncTransforms();
                    Build(r, rootGo.transform, tier);
                    foreach (var mc in mcs) mc.enabled = false;
                    EditorSceneManager.SaveScene(scene);
                }
                AssetDatabase.SaveAssets();
                exit = 0;
                Debug.Log($"REBUILD_EDGE_RESULT: OK region={region}");
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Debug.Log("REBUILD_EDGE_RESULT: FAILED");
            }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        public static void Build(RegionImporter.Result r, Transform root, string tier)
        {
            Vector2 min = new Vector2(float.MaxValue, float.MaxValue), max = new Vector2(float.MinValue, float.MinValue);
            foreach (var ch in r.Chunks) { min = Vector2.Min(min, ch.Min); max = Vector2.Max(max, ch.Max); }
            var boundary = root.gameObject.AddComponent<WorldBoundary>();
            boundary.minEN = min; boundary.maxEN = max;

            var edge = new GameObject("WorldEdge").transform;
            edge.SetParent(root, false);
            Physics.SyncTransforms();

            var exits = ReadExits(r, min, max);
            var closures = new List<WorldBoundary.Closure>();
            var stubs = new List<(Vector3 start, Vector2 dir, float width)>();
            foreach (var ex in exits)
            {
                if (!RoadY(root, ex.closureEN, out float cy)) continue;
                closures.Add(new WorldBoundary.Closure
                {
                    localPos = new Vector3(ex.closureEN.x, cy, ex.closureEN.y),
                    headingDeg = Mathf.Atan2(ex.closureEN == ex.edgeEN ? ex.edgeDir.x : ex.closureDir.x,
                                             ex.closureEN == ex.edgeEN ? ex.edgeDir.y : ex.closureDir.y) * Mathf.Rad2Deg,
                    widthM = ex.width, road = ex.road,
                });
                Vector2 inside = ex.edgeEN - ex.edgeDir * 1.5f;
                if (RoadY(root, inside, out float ey))
                {
                    var cand = new Vector3(ex.edgeEN.x, ey, ex.edgeEN.y);
                    int nearIdx = stubs.FindIndex(s => Vector2.Distance(new Vector2(s.start.x, s.start.z), ex.edgeEN) < 30f);
                    if (nearIdx >= 0)
                    {
                        if (ex.width > stubs[nearIdx].width) stubs[nearIdx] = (cand, ex.edgeDir, ex.width);
                    }
                    else stubs.Add((cand, ex.edgeDir, ex.width));
                }
            }
            boundary.closures = closures.ToArray();

            // ---- apron + road stubs (one mesh asset per region, updated in place so both tier scenes keep the reference) ----
            string meshPath = $"{r.Dir}/Meshes/world_edge.asset";
            var mesh = AssetDatabase.LoadAssetAtPath<Mesh>(meshPath);
            bool created = mesh == null;
            if (created) mesh = new Mesh { name = "world_edge" };
            BuildApron(mesh, root, min, max, stubs);
            if (created) AssetDatabase.CreateAsset(mesh, meshPath); else EditorUtility.SetDirty(mesh);
            var apron = new GameObject("Apron");
            apron.transform.SetParent(edge, false);
            apron.AddComponent<MeshFilter>().sharedMesh = mesh;
            var amr = apron.AddComponent<MeshRenderer>();
            amr.sharedMaterials = new[] { Mat(r, "terrain_grass"), Mat(r, "road_asphalt", "road_asphalt_new", "terrain_grass") };
            amr.shadowCastingMode = ShadowCastingMode.Off;
            amr.lightProbeUsage = LightProbeUsage.Off;
            amr.reflectionProbeUsage = ReflectionProbeUsage.Off;

            // ---- far-field backdrop sectors (ADR 0085) ----
            int farTris = BuildFarField(r, edge, tier);

            // ---- closures ----
            string closurePath = $"{r.Dir}/Meshes/world_edge_closures.asset";
            var host = AssetDatabase.LoadAssetAtPath<Mesh>(closurePath);
            if (host == null) { host = new Mesh { name = "world_edge_closures" }; AssetDatabase.CreateAsset(host, closurePath); }
            var existing = AssetDatabase.LoadAllAssetsAtPath(closurePath).OfType<Mesh>().Where(m => m != host).ToDictionary(m => m.name, m => m);
            var mats = new[]
            {
                Mat(r, "concrete_wall", "concrete_plinth", "road_concrete", "bridge_concrete"),
                Mat(r, "reflector_red", "bridge_fascia_red", "chimney_red"),
                Mat(r, "paint_white_reflective", "marking_white", "chimney_white"),
                Mat(r, "steel_galv", "barrier_steel", "steel_painted_grey"),
            };
            for (int i = 0; i < closures.Count; i++)
            {
                var c = closures[i];
                string name = $"closure_w{Mathf.RoundToInt(c.widthM * 10f)}";
                if (!existing.TryGetValue(name, out var cm))
                {
                    cm = BuildClosureMesh(name, c.widthM);
                    AssetDatabase.AddObjectToAsset(cm, host);
                    existing[name] = cm;
                }
                var go = new GameObject($"Closure_{i:00}_{c.road}");
                go.transform.SetParent(edge, false);
                go.transform.localPosition = c.localPos;
                go.transform.localRotation = Quaternion.Euler(0f, c.headingDeg, 0f);
                go.AddComponent<MeshFilter>().sharedMesh = cm;
                var mr = go.AddComponent<MeshRenderer>();
                mr.sharedMaterials = mats;
                mr.shadowCastingMode = ShadowCastingMode.On;
                mr.lightProbeUsage = LightProbeUsage.Off;
                mr.reflectionProbeUsage = ReflectionProbeUsage.Off;
                var bc = go.AddComponent<BoxCollider>();
                bc.center = new Vector3(0f, 1.25f, 0f);
                bc.size = new Vector3(ClosureSpan(c.widthM), 2.5f, 0.6f);
                go.AddComponent<GroundSurface>().kind = SurfaceKind.Concrete;
                go.isStatic = true;
            }
            EditorUtility.SetDirty(host);
            Debug.Log($"[IMPORT] world edge (tier {tier}): bounds E {min.x:F0}..{max.x:F0} N {min.y:F0}..{max.y:F0}, {exits.Count} roads leave the region, " +
                      $"{closures.Count} closures {ClosureSetbackM:F0} m inside, {stubs.Count} road stubs, apron {mesh.vertexCount} verts to {ApronReachM:F0} m, far-field {farTris} tris");
        }

        static int BuildFarField(RegionImporter.Result r, Transform edge, string tier)
        {
            string glbName = tier == "High" ? "far_field.glb" : "far_field.low.glb";
            string glbPath = Path.Combine(EditorTools.RepoRoot, "Data", "raw", "derived", r.Region, "world", glbName);
            if (!File.Exists(glbPath))
            {
                Debug.LogWarning($"[IMPORT] world edge: {glbPath} missing - skipping far-field backdrop");
                return 0;
            }
            var g = GlbReader.Load(glbPath);
            string assetPath = $"{r.Dir}/Meshes/{tier}/world_edge_far.asset";
            AssetDatabase.DeleteAsset(assetPath);
            var farHost = new Mesh { name = $"world_edge_far_{tier}" };
            AssetDatabase.CreateAsset(farHost, assetPath);

            int totalTris = 0;
            long totalBytes = 0;
            foreach (var secName in k_FarSectors)
            {
                var nd = g.Find(secName);
                if (nd == null || nd.Primitives.Count == 0) continue;
                var secMats = new Material[nd.Primitives.Count];
                for (int i = 0; i < secMats.Length; i++)
                {
                    string mid = nd.Primitives[i].Material;
                    secMats[i] = Mat(r, mid, "far_field_buildings", "plaster_light");
                }
                var sm = WorldMeshBake.Compact($"{secName}_{tier}", nd.Primitives,
                    new WorldMeshBake.Options { Uv0 = true, Uv1 = true, Colors = true });
                AssetDatabase.AddObjectToAsset(sm, farHost);
                totalTris += (int)(sm.GetIndexCount(0) / 3) + (sm.subMeshCount > 1 ? (int)(sm.GetIndexCount(1) / 3) : 0);
                totalBytes += WorldMeshBake.GpuBytes(sm);

                var sgo = new GameObject($"FarField_{secName}");
                sgo.transform.SetParent(edge, false);
                sgo.AddComponent<MeshFilter>().sharedMesh = sm;
                var smr = sgo.AddComponent<MeshRenderer>();
                smr.sharedMaterials = secMats;
                smr.shadowCastingMode = ShadowCastingMode.Off;
                smr.receiveShadows = false;
                smr.lightProbeUsage = LightProbeUsage.Off;
                smr.reflectionProbeUsage = ReflectionProbeUsage.Off;
            }
            r.MemoryBytes[$"{tier}/far_field"] = totalBytes;
            EditorUtility.SetDirty(farHost);
            return totalTris;
        }

        static float ClosureSpan(float roadWidth) => roadWidth + 5f;   // carriageway + shoulders / kerbs on both sides

        static Material Mat(RegionImporter.Result r, params string[] ids)
        {
            foreach (var id in ids) if (r.Materials.TryGetValue(id, out var m) && m != null) return m;
            throw new InvalidDataException("world edge: none of the materials exists: " + string.Join(", ", ids));
        }

        // ------------------------------------------------------------------------------------------------ road exits
        struct Exit
        {
            public Vector2 edgeEN, edgeDir;        // point on the region edge, unit direction of the road leaving the region
            public Vector2 closureEN, closureDir;  // closure centre and the road direction there (towards the edge)
            public float width;
            public string road;
        }

        /// <summary>Roads cut by the region bbox: edges of roads.graph.json with a boundary node (build_region clips them there).</summary>
        static List<Exit> ReadExits(RegionImporter.Result r, Vector2 min, Vector2 max)
        {
            var exits = new List<Exit>();
            string path = Path.Combine(Game.Editor.Build.EditorTools.RepoRoot, "Data", "Regions", r.Region, "roads.graph.json");
            if (!File.Exists(path)) { Debug.LogWarning("[IMPORT] world edge: roads.graph.json missing - no closures"); return exits; }
            var g = Obj(Parse(File.ReadAllText(path)));
            var boundaryNodes = new HashSet<string>();
            foreach (var no in Arr(g.Get("nodes")))
            {
                var n = Obj(no);
                if (n.Get("boundary") is bool b && b) boundaryNodes.Add(Str(n.Get("id")));
            }
            // Edges per node: a boundary edge is often a short piece (the graph splits a road where an attribute
            // changes), so the setback walks on through nodes where the road simply continues (degree 2).
            var edgeList = Arr(g.Get("edges")).Select(Obj).ToList();
            var atNode = new Dictionary<string, List<Dictionary<string, object>>>();
            foreach (var e in edgeList)
                foreach (string key in new[] { Str(e.Get("from")), Str(e.Get("to")) })
                {
                    if (!atNode.TryGetValue(key, out var l)) atNode[key] = l = new List<Dictionary<string, object>>();
                    l.Add(e);
                }
            List<Vector2> Points(Dictionary<string, object> e) =>
                Arr(e.Get("geometry")).Select(p => new Vector2((float)(Num(Arr(p)[0]) - r.AnchorX), (float)(Num(Arr(p)[1]) - r.AnchorY))).ToList();
            foreach (var e in edgeList)
            {
                bool fromB = boundaryNodes.Contains(Str(e.Get("from"))), toB = boundaryNodes.Contains(Str(e.Get("to")));
                if (!fromB && !toB) continue;
                var pts = Points(e);
                if (pts.Count < 2) continue;
                if (fromB) pts.Reverse();            // now the last point is on the region edge
                float have = 0f;
                for (int i = 1; i < pts.Count; i++) have += Vector2.Distance(pts[i - 1], pts[i]);
                var cur = e;
                string inner = Str(e.Get(fromB ? "to" : "from"));
                for (int guard = 0; guard < 16 && have < ClosureSetbackM / 0.8f; guard++)
                {
                    if (boundaryNodes.Contains(inner) || !atNode.TryGetValue(inner, out var l) || l.Count != 2) break;
                    var next = l[0] == cur ? l[1] : l[0];
                    if (next == cur) break;
                    var np = Points(next);
                    if (np.Count < 2) break;
                    bool endsHere = Str(next.Get("to")) == inner;
                    if (!endsHere) np.Reverse();     // now np ends at the shared node
                    for (int i = 1; i < np.Count; i++) have += Vector2.Distance(np[i - 1], np[i]);
                    np.RemoveAt(np.Count - 1);
                    pts.InsertRange(0, np);
                    inner = Str(next.Get(endsHere ? "from" : "to"));
                    cur = next;
                }
                var attrs = e.Get("attrs") as Dictionary<string, object>;
                float width = AttrNum(attrs, "width");
                if (width <= 0f) width = Mathf.Max(1f, AttrNum(attrs, "lanes")) * 3.5f;
                string hw = AttrStr(attrs, "highway") ?? "road";
                string nm = AttrStr(attrs, "name");

                Vector2 edgePt = pts[pts.Count - 1];
                if (WorldBoundary.InsideDistance(min, max, edgePt.x, edgePt.y) > 5f) continue;   // not actually on the edge
                Vector2 edgeDir = (edgePt - pts[pts.Count - 2]).normalized;
                // Walk back along the polyline by the setback (short edges: 80 % of their length).
                float total = 0f;
                for (int i = 1; i < pts.Count; i++) total += Vector2.Distance(pts[i - 1], pts[i]);
                float back = Mathf.Min(ClosureSetbackM, total * 0.8f), acc = 0f;
                Vector2 cp = edgePt, cd = edgeDir;
                for (int i = pts.Count - 1; i > 0; i--)
                {
                    float seg = Vector2.Distance(pts[i - 1], pts[i]);
                    if (acc + seg >= back && seg > 1e-3f)
                    {
                        float t = (back - acc) / seg;
                        cp = Vector2.Lerp(pts[i], pts[i - 1], t);
                        cd = (pts[i] - pts[i - 1]).normalized;
                        break;
                    }
                    acc += seg;
                }
                exits.Add(new Exit { edgeEN = edgePt, edgeDir = edgeDir, closureEN = cp, closureDir = cd, width = Mathf.Clamp(width, 3f, 16f), road = Sanitize(nm ?? hw) });
            }
            return exits;
        }

        static float AttrNum(Dictionary<string, object> attrs, string key)
        {
            if (attrs?.Get(key) is Dictionary<string, object> a && a.Get("v") != null)
            {
                try { return (float)Num(a.Get("v")); } catch (Exception) { return 0f; }
            }
            return 0f;
        }

        static string AttrStr(Dictionary<string, object> attrs, string key) =>
            attrs?.Get(key) is Dictionary<string, object> a ? a.Get("v") as string : null;

        static string Sanitize(string s)
        {
            var chars = s.Where(ch => char.IsLetterOrDigit(ch) || ch == '_').Take(24).ToArray();
            return chars.Length > 0 ? new string(chars) : "road";
        }

        // ------------------------------------------------------------------------------------------------ heights
        /// <summary>Road surface (highest collider) at a region-local point; false when there is no collision there.</summary>
        static bool RoadY(Transform root, Vector2 en, out float localY)
        {
            localY = 0f;
            Vector3 w = root.TransformPoint(new Vector3(en.x, 0f, en.y));
            var hits = Physics.RaycastAll(new Vector3(w.x, root.position.y + 600f, w.z), Vector3.down, 1200f, ~0, QueryTriggerInteraction.Ignore);
            if (hits.Length == 0) return false;
            float best = float.NegativeInfinity;
            foreach (var h in hits) if (h.point.y > best) best = h.point.y;
            localY = root.InverseTransformPoint(new Vector3(w.x, best, w.z)).y;
            return true;
        }

        /// <summary>Terrain height (col_terrain; else the lowest collider) at a region-local point.</summary>
        static float TerrainY(Transform root, Vector2 en, float fallback)
        {
            Vector3 w = root.TransformPoint(new Vector3(en.x, 0f, en.y));
            var hits = Physics.RaycastAll(new Vector3(w.x, root.position.y + 600f, w.z), Vector3.down, 1200f, ~0, QueryTriggerInteraction.Ignore);
            if (hits.Length == 0) return fallback;
            float terrain = float.NaN, lowest = float.PositiveInfinity;
            foreach (var h in hits)
            {
                if (h.collider.name == "col_terrain") terrain = h.point.y;
                if (h.point.y < lowest) lowest = h.point.y;
            }
            float y = float.IsNaN(terrain) ? lowest : terrain;
            return root.InverseTransformPoint(new Vector3(w.x, y, w.z)).y;
        }

        // ------------------------------------------------------------------------------------------------ apron
        static Color32 ApronMask(Vector2 p, float d, bool shoulder = false)
        {
            byte r = shoulder ? (byte)12 : (byte)255;
            float n1 = 0.5f + 0.5f * Mathf.Sin(p.x * 0.013f + p.y * 0.009f) * Mathf.Cos(p.y * 0.017f - p.x * 0.011f);
            float n2 = 0.5f + 0.5f * Mathf.Sin(p.x * 0.031f - p.y * 0.023f);
            // Forest floor needle/leaf litter in the northern/north-western forest belts (Las Pietrasze, Las Bacieczki)
            float forestZone = Mathf.Clamp01((p.y - 320f) / 450f);
            if (p.x < -550f && p.y > -100f) forestZone = Mathf.Max(forestZone, 0.65f * Mathf.Clamp01((p.y + 100f) / 350f));
            float gF = forestZone * Mathf.Lerp(0.45f, 0.88f, n1) * Mathf.Clamp01((d + 15f) / 90f);
            // Unmown dry meadow grass across open verges and outer fields
            float bF = Mathf.Lerp(0.35f, 0.82f, n2) * (1f - 0.45f * gF);
            // Bare soil / urban earth patches in southern & eastern built-up/industrial corridors
            float urbanZone = Mathf.Clamp01((-p.y - 250f) / 500f);
            if (p.x > 550f && p.y < 300f) urbanZone = Mathf.Max(urbanZone, 0.75f);
            float aF = urbanZone * Mathf.Lerp(0.15f, 0.48f, n1 * n2) * Mathf.Clamp01(d / 60f);
            return new Color32(
                r,
                (byte)Mathf.Clamp(Mathf.RoundToInt(gF * 255f), 0, 255),
                (byte)Mathf.Clamp(Mathf.RoundToInt(bF * 255f), 0, 255),
                (byte)Mathf.Clamp(Mathf.RoundToInt(aF * 255f), 0, 255));
        }

        static void BuildApron(Mesh mesh, Transform root, Vector2 min, Vector2 max, List<(Vector3 start, Vector2 dir, float width)> stubs)
        {
            // Perimeter samples, counter-clockwise seen from above: south side (west to east), SE corner fan, east side, ...
            var basePt = new List<Vector2>(); var normal = new List<Vector2>();
            Vector2[] corners = { new Vector2(min.x, min.y), new Vector2(max.x, min.y), new Vector2(max.x, max.y), new Vector2(min.x, max.y) };
            Vector2[] normals = { new Vector2(0f, -1f), new Vector2(1f, 0f), new Vector2(0f, 1f), new Vector2(-1f, 0f) };
            const int fan = 4;
            for (int s = 0; s < 4; s++)
            {
                Vector2 a = corners[s], b = corners[(s + 1) % 4];
                int n = Mathf.Max(1, Mathf.RoundToInt(Vector2.Distance(a, b) / SampleStepM));
                for (int i = 0; i <= n; i++) { basePt.Add(Vector2.Lerp(a, b, i / (float)n)); normal.Add(normals[s]); }
                Vector2 n0 = normals[s], n1 = normals[(s + 1) % 4];
                for (int k = 1; k < fan; k++) { basePt.Add(b); normal.Add(Vector2.Lerp(n0, n1, k / (float)fan).normalized); }
            }
            int np = basePt.Count, nr = k_RingDist.Length;
            var height = new float[np];
            float mean = 0f, last = 0f;
            for (int i = 0; i < np; i++)
            {
                Vector2 inside = basePt[i] - normal[i] * 0.75f;
                inside.x = Mathf.Clamp(inside.x, min.x + 0.75f, max.x - 0.75f);
                inside.y = Mathf.Clamp(inside.y, min.y + 0.75f, max.y - 0.75f);
                height[i] = last = TerrainY(root, inside, last);
                mean += height[i];
            }
            mean /= np;
            var smoothHeight = new float[np];
            const int win = 6;
            for (int i = 0; i < np; i++)
            {
                float s = 0f;
                for (int dj = -win; dj <= win; dj++) s += height[(i + dj + np) % np];
                smoothHeight[i] = s / (2 * win + 1);
            }
            float ApronHeightAt(float z0, float zSm, float d)
            {
                float s1 = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(d / 220f));
                float s2 = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01((d - 220f) / 1400f));
                float zNear = Mathf.Lerp(z0, zSm - 0.15f, s1);
                float zFar = zSm - 0.25f + 0.08f * (mean - zSm);
                return Mathf.Lerp(zNear, zFar, s2);
            }

            var pos = new List<Vector3>(); var nrm = new List<Vector3>(); var uv = new List<Vector2>(); var col = new List<Color32>();
            var grass = new List<int>(); var asphalt = new List<int>();
            for (int i = 0; i < np; i++)
                for (int k = 0; k < nr; k++)
                {
                    float d = k_RingDist[k];
                    Vector2 p = basePt[i] + normal[i] * d;
                    // Inner ring tucked under the terrain border; far rings ease locally without pulling valleys uphill,
                    // matching BorderElevation.z_at_eff in tools/worldgen/streetscape/far_field.py.
                    float y = k == 0
                        ? height[i] - 0.6f
                        : k == 1
                            ? height[i] - 0.04f
                            : ApronHeightAt(height[i], smoothHeight[i], d);
                    pos.Add(new Vector3(p.x, y, p.y));
                    nrm.Add(Vector3.up);
                    uv.Add(p);
                    col.Add(ApronMask(p, Mathf.Max(0f, d)));
                }
            for (int i = 0; i < np; i++)
            {
                int j = (i + 1) % np;
                for (int k = 0; k + 1 < nr; k++)
                {
                    int a = i * nr + k, b = j * nr + k, c = j * nr + k + 1, d = i * nr + k + 1;
                    grass.Add(a); grass.Add(b); grass.Add(d);
                    grass.Add(b); grass.Add(c); grass.Add(d);
                }
            }

            // Road stubs: asphalt strip on a low embankment graded smoothly onto the local apron surface.
            foreach (var (start, dir, width) in stubs)
            {
                Vector2 side = new Vector2(dir.y, -dir.x);   // right of the travel direction
                const int seg = 12;
                float hw = width * 0.5f + 0.75f;             // carriageway + hard strip
                int bestIdx = 0;
                float bestDist = float.MaxValue;
                for (int i = 0; i < np; i++)
                {
                    float dd = Vector2.Distance(basePt[i], new Vector2(start.x, start.z));
                    if (dd < bestDist) { bestDist = dd; bestIdx = i; }
                }
                float stubZSm = smoothHeight[bestIdx];
                int v0 = pos.Count;
                for (int s = 0; s <= seg; s++)
                {
                    float d = StubLengthM * s / seg;
                    Vector2 c = new Vector2(start.x, start.z) + dir * d;
                    float apronY = ApronHeightAt(start.y, stubZSm, d);
                    float crownY = Mathf.Lerp(start.y + 0.03f, apronY + 0.14f, Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(d / 120f)));
                    float toeY = apronY - 0.35f;
                    // cross-section: toe left, edge left, edge right, toe right
                    float[] off = { -hw - 4.5f, -hw, hw, hw + 4.5f };
                    float[] ys = { toeY, crownY, crownY, toeY };
                    for (int q = 0; q < 4; q++)
                    {
                        Vector2 p = c + side * off[q];
                        pos.Add(new Vector3(p.x, ys[q], p.y));
                        nrm.Add(Vector3.up);
                        uv.Add(new Vector2(off[q], d));
                        col.Add(ApronMask(p, d, shoulder: q == 1 || q == 2));
                    }
                }
                for (int s = 0; s < seg; s++)
                {
                    int a = v0 + s * 4, b = v0 + (s + 1) * 4;
                    Quad(grass, a, b, b + 1, a + 1);
                    Quad(asphalt, a + 1, b + 1, b + 2, a + 2);
                    Quad(grass, a + 2, b + 2, b + 3, a + 3);
                }
            }

            mesh.Clear();
            mesh.indexFormat = pos.Count > 65000 ? IndexFormat.UInt32 : IndexFormat.UInt16;
            mesh.SetVertices(pos); mesh.SetNormals(nrm); mesh.SetUVs(0, uv); mesh.SetColors(col);
            mesh.subMeshCount = 2;
            mesh.SetTriangles(grass, 0); mesh.SetTriangles(asphalt, 1);
            mesh.RecalculateNormals();
            mesh.RecalculateTangents();
            mesh.RecalculateBounds();
        }

        /// <summary>Quad a-b-c-d with a→b along the travel direction and a→d to the right: faces up (Unity clockwise front faces).</summary>
        static void Quad(List<int> tris, int a, int b, int c, int d)
        {
            tris.Add(a); tris.Add(b); tris.Add(d);
            tris.Add(b); tris.Add(c); tris.Add(d);
        }

        // ------------------------------------------------------------------------------------------------ closure
        /// <summary>
        /// Closure in its own frame: x across the road, z along the road towards the region edge, y up, origin on the
        /// road surface. Submeshes: 0 concrete barriers, 1 red board fields, 2 white board fields, 3 posts.
        /// </summary>
        static Mesh BuildClosureMesh(string name, float roadWidth)
        {
            var pos = new List<Vector3>(); var nrm = new List<Vector3>(); var uv = new List<Vector2>();
            var subs = new[] { new List<int>(), new List<int>(), new List<int>(), new List<int>() };
            float span = ClosureSpan(roadWidth);
            // Concrete barrier elements, 2.0 m long, profile 0.60 m base / 0.20 m top / 0.81 m high.
            int n = Mathf.Max(1, Mathf.CeilToInt(span / 2.0f));
            float len = span / n;
            for (int i = 0; i < n; i++)
            {
                float x0 = -span * 0.5f + i * len + 0.03f, x1 = x0 + len - 0.06f;
                Prism(pos, nrm, uv, subs[0], x0, x1, 0.30f, 0.10f, 0f, 0.81f);
            }
            // U-20 board in front of the barriers (the side the driver arrives from = −z), on posts.
            const float boardZ = -0.75f, boardY0 = 0.95f, boardY1 = 1.20f, field = 0.5f;
            int fields = Mathf.Max(2, Mathf.RoundToInt(span / field));
            float fw = span / fields;
            for (int i = 0; i < fields; i++)
            {
                float x0 = -span * 0.5f + i * fw, x1 = x0 + fw;
                Box(pos, nrm, uv, subs[i % 2 == 0 ? 1 : 2], new Vector3(x0, boardY0, boardZ - 0.015f), new Vector3(x1, boardY1, boardZ + 0.015f));
            }
            int posts = Mathf.Max(2, Mathf.CeilToInt(span / 2.5f) + 1);
            for (int i = 0; i < posts; i++)
            {
                float x = Mathf.Lerp(-span * 0.5f + 0.15f, span * 0.5f - 0.15f, i / (float)(posts - 1));
                Box(pos, nrm, uv, subs[3], new Vector3(x - 0.03f, 0f, boardZ + 0.015f), new Vector3(x + 0.03f, boardY1 + 0.05f, boardZ + 0.075f));
            }
            var m = new Mesh { name = name };
            m.SetVertices(pos); m.SetNormals(nrm); m.SetUVs(0, uv);
            m.subMeshCount = 4;
            for (int s = 0; s < 4; s++) m.SetTriangles(subs[s], s);
            m.RecalculateTangents();
            m.RecalculateBounds();
            return m;
        }

        /// <summary>Barrier element between x0 and x1: trapezoid cross-section in the y-z plane.</summary>
        static void Prism(List<Vector3> pos, List<Vector3> nrm, List<Vector2> uv, List<int> tris, float x0, float x1, float halfBase, float halfTop, float y0, float y1)
        {
            Vector3 a0 = new Vector3(x0, y0, -halfBase), b0 = new Vector3(x0, y1, -halfTop), c0 = new Vector3(x0, y1, halfTop), d0 = new Vector3(x0, y0, halfBase);
            Vector3 a1 = new Vector3(x1, y0, -halfBase), b1 = new Vector3(x1, y1, -halfTop), c1 = new Vector3(x1, y1, halfTop), d1 = new Vector3(x1, y0, halfBase);
            s_Inside = new Vector3((x0 + x1) * 0.5f, (y0 + y1) * 0.5f, 0f);
            Face(pos, nrm, uv, tris, a1, b1, b0, a0);   // front slope (towards −z)
            Face(pos, nrm, uv, tris, b1, c1, c0, b0);   // top
            Face(pos, nrm, uv, tris, d0, c0, c1, d1);   // back slope
            Face(pos, nrm, uv, tris, a0, b0, c0, d0);   // end x0
            Face(pos, nrm, uv, tris, d1, c1, b1, a1);   // end x1
        }

        static void Box(List<Vector3> pos, List<Vector3> nrm, List<Vector2> uv, List<int> tris, Vector3 lo, Vector3 hi)
        {
            Vector3 p000 = lo, p111 = hi;
            Vector3 p100 = new Vector3(hi.x, lo.y, lo.z), p010 = new Vector3(lo.x, hi.y, lo.z), p001 = new Vector3(lo.x, lo.y, hi.z);
            Vector3 p110 = new Vector3(hi.x, hi.y, lo.z), p101 = new Vector3(hi.x, lo.y, hi.z), p011 = new Vector3(lo.x, hi.y, hi.z);
            s_Inside = (lo + hi) * 0.5f;
            Face(pos, nrm, uv, tris, p100, p110, p010, p000);   // −z
            Face(pos, nrm, uv, tris, p001, p011, p111, p101);   // +z
            Face(pos, nrm, uv, tris, p000, p010, p011, p001);   // −x
            Face(pos, nrm, uv, tris, p101, p111, p110, p100);   // +x
            Face(pos, nrm, uv, tris, p010, p110, p111, p011);   // +y
        }

        /// <summary>Quad with its own vertices and a flat normal; the winding is flipped if it does not match the normal.</summary>
        static Vector3 s_Inside;

        static void Face(List<Vector3> pos, List<Vector3> nrm, List<Vector2> uv, List<int> tris, Vector3 a, Vector3 b, Vector3 c, Vector3 d)
        {
            // Unity front faces are clockwise: normal = (b − a) × (c − a) for a clockwise a-b-c seen from the front.
            Vector3 n = Vector3.Cross(b - a, c - a).normalized;
            if (Vector3.Dot(n, (a + b + c + d) * 0.25f - s_Inside) < 0f) { (b, d) = (d, b); n = -n; }
            int i = pos.Count;
            pos.Add(a); pos.Add(b); pos.Add(c); pos.Add(d);
            for (int k = 0; k < 4; k++) nrm.Add(n);
            uv.Add(new Vector2(0f, 0f)); uv.Add(new Vector2(0f, 1f)); uv.Add(new Vector2(1f, 1f)); uv.Add(new Vector2(1f, 0f));
            tris.Add(i); tris.Add(i + 1); tris.Add(i + 2);
            tris.Add(i); tris.Add(i + 2); tris.Add(i + 3);
        }
    }
}
