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
                    int nearIdx = stubs.FindIndex(s => SameRoadContinuation(s.start, s.dir, ex.edgeEN, ex.edgeDir));
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
            int farTris = BuildFarField(r, edge, tier, min, max);

            // ---- closures (ADR 0141) ----
            // Physical end of the road: one collider object per closure (unchanged contract, WorldEdgeRecoveryTests).
            for (int i = 0; i < closures.Count; i++)
            {
                var c = closures[i];
                var go = new GameObject($"Closure_{i:00}_{c.road}");
                go.transform.SetParent(edge, false);
                go.transform.localPosition = c.localPos;
                go.transform.localRotation = Quaternion.Euler(0f, c.headingDeg, 0f);
                var bc = go.AddComponent<BoxCollider>();
                bc.center = new Vector3(0f, 1.25f, 0f);
                bc.size = new Vector3(ClosureSpan(c.widthM), 2.5f, 0.6f);
                go.AddComponent<GroundSurface>().kind = SurfaceKind.Concrete;
                go.isStatic = true;
            }
            // Visible part: neighbouring closures share one mesh in region space with two materials (concrete barriers;
            // boards, posts and B-1 faces as linear vertex colours on the far-field paint material), i.e. 2 draws per
            // group instead of 4 per closure. Mesh sub-assets are updated in place so both tier scenes keep references.
            string closurePath = $"{r.Dir}/Meshes/world_edge_closures.asset";
            var host = AssetDatabase.LoadAssetAtPath<Mesh>(closurePath);
            if (host == null) { host = new Mesh { name = "world_edge_closures" }; AssetDatabase.CreateAsset(host, closurePath); }
            var existing = AssetDatabase.LoadAllAssetsAtPath(closurePath).OfType<Mesh>().Where(m => m != host).ToDictionary(m => m.name, m => m);
            var mats = new[]
            {
                Mat(r, "concrete_wall", "concrete_plinth", "road_concrete", "bridge_concrete"),
                Mat(r, "far_field_buildings"),
            };
            // One visible closure per carriageway: a main line and its slip lane reach the edge side by side and the
            // graph closes each of them (colliders above stay per road); their boards and B-1 discs would overlap.
            var visible = MergeOverlappingClosures(closures);
            var groups = ClusterClosures(visible, ClosureGroupLinkM);
            var keep = new HashSet<string>();
            int closureTris = 0;
            for (int k = 0; k < groups.Count; k++)
            {
                string name = $"closure_group_{k:00}";
                keep.Add(name);
                if (!existing.TryGetValue(name, out var cm))
                {
                    cm = new Mesh { name = name };
                    AssetDatabase.AddObjectToAsset(cm, host);
                }
                BuildClosureGroupMesh(cm, groups[k].Select(i => visible[i]).ToList());
                EditorUtility.SetDirty(cm);
                closureTris += (int)((cm.GetIndexCount(0) + cm.GetIndexCount(1)) / 3);
                var go = new GameObject($"ClosureGroup_{k:00}");
                go.transform.SetParent(edge, false);
                go.AddComponent<MeshFilter>().sharedMesh = cm;
                var mr = go.AddComponent<MeshRenderer>();
                mr.sharedMaterials = mats;
                mr.shadowCastingMode = ShadowCastingMode.On;
                mr.lightProbeUsage = LightProbeUsage.Off;
                mr.reflectionProbeUsage = ReflectionProbeUsage.Off;
                go.isStatic = true;
            }
            foreach (var kv in existing)
                if (!keep.Contains(kv.Key)) UnityEngine.Object.DestroyImmediate(kv.Value, true);   // meshes of the per-closure layout
            EditorUtility.SetDirty(host);
            Debug.Log($"[IMPORT] world edge (tier {tier}): bounds E {min.x:F0}..{max.x:F0} N {min.y:F0}..{max.y:F0}, {exits.Count} roads leave the region, " +
                      $"{closures.Count} closures {ClosureSetbackM:F0} m inside, {visible.Count} visible after merging overlaps, in {groups.Count} render groups ({closureTris} tris), {stubs.Count} road stubs, apron {mesh.vertexCount} verts to {ApronReachM:F0} m, far-field {farTris} tris");
        }

        /// <summary>Node of the far-field GLB with the tall ring objects kept visible beyond the far plane (ADR 0141).</summary>
        public const string FarSkylineNode = "far_skyline";

        static int BuildFarField(RegionImporter.Result r, Transform edge, string tier, Vector2 min, Vector2 max)
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
            // Stable hierarchy contract used by recovery/integration checks (ADR 0085).
            // Identity parent: no renderer, collider, material or world-space geometry change.
            var farRoot = new GameObject("WorldFarField").transform;
            farRoot.SetParent(edge, false);
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
                sgo.transform.SetParent(farRoot, false);
                sgo.AddComponent<MeshFilter>().sharedMesh = sm;
                var smr = sgo.AddComponent<MeshRenderer>();
                smr.sharedMaterials = secMats;
                smr.shadowCastingMode = ShadowCastingMode.Off;
                smr.receiveShadows = false;
                smr.lightProbeUsage = LightProbeUsage.Off;
                smr.reflectionProbeUsage = ReflectionProbeUsage.Off;
            }
            // ADR 0141: skyline (tall ring objects + far stand-ins of the region's landmark stacks). One renderer, the
            // sectors' material. Kamion/World Surface holds its flagged vertices in front of the far plane, so the
            // renderer must never be frustum-culled by distance: its bounds are grown over the whole tile (the camera
            // is always inside them). Sibling of WorldFarField, whose 4-sector contract (ADR 0085) stays as it is.
            var sky = g.Find(FarSkylineNode);
            if (sky != null && sky.Primitives.Count > 0)
            {
                var skyMats = new Material[sky.Primitives.Count];
                for (int i = 0; i < skyMats.Length; i++)
                    skyMats[i] = Mat(r, sky.Primitives[i].Material, "far_field_buildings", "plaster_light");
                var sm = WorldMeshBake.Compact($"{FarSkylineNode}_{tier}", sky.Primitives,
                    new WorldMeshBake.Options { Uv0 = true, Uv1 = true, Colors = true });
                sm.bounds = SkylineBounds(sm.bounds, min, max);
                AssetDatabase.AddObjectToAsset(sm, farHost);
                for (int i = 0; i < sm.subMeshCount; i++) totalTris += (int)(sm.GetIndexCount(i) / 3);
                totalBytes += WorldMeshBake.GpuBytes(sm);

                var sgo = new GameObject("FarSkyline");
                sgo.transform.SetParent(edge, false);
                sgo.AddComponent<MeshFilter>().sharedMesh = sm;
                var smr = sgo.AddComponent<MeshRenderer>();
                smr.sharedMaterials = skyMats;
                smr.shadowCastingMode = ShadowCastingMode.Off;
                smr.receiveShadows = false;
                smr.lightProbeUsage = LightProbeUsage.Off;
                smr.reflectionProbeUsage = ReflectionProbeUsage.Off;
            }
            r.MemoryBytes[$"{tier}/far_field"] = totalBytes;
            EditorUtility.SetDirty(farHost);
            return totalTris;
        }

        /// <summary>Skyline mesh bounds grown to contain the whole region tile (public for the EditMode test).</summary>
        public static Bounds SkylineBounds(Bounds mesh, Vector2 min, Vector2 max)
        {
            mesh.Encapsulate(new Vector3(min.x, mesh.min.y, min.y));
            mesh.Encapsulate(new Vector3(max.x, mesh.max.y, max.y));
            return mesh;
        }

        // ADR 0121: the old 30 m radius erased one carriageway at the Andersa and Tysiąclecia exits
        // (measured centreline gaps 12–15 m). Merge only near-coincident source ends with matching headings.
        static bool SameRoadContinuation(Vector3 start, Vector2 direction, Vector2 next, Vector2 nextDirection) =>
            Vector2.Distance(new Vector2(start.x, start.z), next) < 3f &&
            Vector2.Dot(direction.normalized, nextDirection.normalized) > 0.95f; // WORKING_VALUE source-end tolerance

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

        static float[] SmoothPerimeterHeights(List<Vector2> points, float[] heights, out float mean)
        {
            // Corner fans duplicate a position for topology, not extra terrain samples.
            // Match Python BorderElevation's uniformly sampled, circular perimeter.
            var ids = new Dictionary<Vector2, int>(points.Count);
            var unique = new List<float>(points.Count);
            var sample = new int[points.Count];
            mean = 0f;
            for (int i = 0; i < points.Count; i++)
            {
                if (!ids.TryGetValue(points[i], out int id))
                {
                    id = unique.Count;
                    ids.Add(points[i], id);
                    unique.Add(heights[i]);
                    mean += heights[i];
                }
                sample[i] = id;
            }
            var result = new float[points.Count];
            int count = unique.Count;
            if (count == 0) return result;
            mean /= count;
            int win = Mathf.Min(6, Mathf.Max(1, count / 16));
            var smooth = new float[count];
            for (int i = 0; i < count; i++)
            {
                float sum = 0f;
                for (int dj = -win; dj <= win; dj++) sum += unique[(i + dj + count) % count];
                smooth[i] = sum / (2 * win + 1);
            }
            for (int i = 0; i < points.Count; i++) result[i] = smooth[sample[i]];
            return result;
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
            float last = 0f;
            for (int i = 0; i < np; i++)
            {
                Vector2 inside = basePt[i] - normal[i] * 0.75f;
                inside.x = Mathf.Clamp(inside.x, min.x + 0.75f, max.x - 0.75f);
                inside.y = Mathf.Clamp(inside.y, min.y + 0.75f, max.y - 0.75f);
                height[i] = last = TerrainY(root, inside, last);
            }
            var smoothHeight = SmoothPerimeterHeights(basePt, height, out float mean);
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

            // ADR 0121: a diagonal exit crosses several perimeter height profiles. Sampling only the
            // profile at its starting point buried the southbound road under the adjacent apron.
            // Interpolate the actual already-triangulated apron, before adding any road shoulders.
            int apronIndexCount = grass.Count;
            float ApronSurfaceAt(Vector2 p, float fallback)
            {
                for (int t = 0; t < apronIndexCount; t += 3)
                {
                    Vector3 a = pos[grass[t]], b = pos[grass[t + 1]], c = pos[grass[t + 2]];
                    float bx = b.x - a.x, bz = b.z - a.z, cx = c.x - a.x, cz = c.z - a.z;
                    float det = bx * cz - bz * cx;
                    if (Mathf.Abs(det) < 1e-6f) continue;
                    float px = p.x - a.x, pz = p.y - a.z;
                    float u = (px * cz - pz * cx) / det;
                    float v = (bx * pz - bz * px) / det;
                    if (u >= -1e-5f && v >= -1e-5f && u + v <= 1.00001f)
                        return a.y + u * (b.y - a.y) + v * (c.y - a.y);
                }
                return fallback;
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
                    float profileY = ApronHeightAt(start.y, stubZSm, d);
                    float apronY = Mathf.Max(ApronSurfaceAt(c - side * hw, profileY),
                                             ApronSurfaceAt(c + side * hw, profileY));
                    float crownY = Mathf.Lerp(start.y + 0.03f, apronY + 0.14f, Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(d / 120f)));
                    crownY = Mathf.Max(crownY, apronY + 0.04f);
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
                // A coarse asphalt segment can cross a break in the apron slope between its stations.
                // Lift its two station edges just enough to clear that break, retaining the same topology.
                for (int s = 0; s < seg; s++)
                {
                    int a = v0 + s * 4, b = a + 4;
                    float lift = 0f;
                    for (int step = 0; step <= 8; step++)
                        for (int lane = 0; lane <= 2; lane++)
                        {
                            float t = step / 8f, across = lane / 2f;
                            Vector3 p = Vector3.Lerp(Vector3.Lerp(pos[a + 1], pos[a + 2], across),
                                                     Vector3.Lerp(pos[b + 1], pos[b + 2], across), t);
                            lift = Mathf.Max(lift, ApronSurfaceAt(new Vector2(p.x, p.z), p.y - 0.04f) + 0.04f - p.y);
                        }
                    if (lift > 0f)
                        foreach (int index in new[] { a + 1, a + 2, b + 1, b + 2 })
                            pos[index] += Vector3.up * lift;
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
            // WorldPBR _ROADWEAR contract: (-1, 5) means no measured lane-wear data.
            // Missing UV1 becomes (0, 0), incorrectly treating the entire continuation as a dirty gutter.
            mesh.SetUVs(1, Enumerable.Repeat(new Vector2(-1f, 5f), pos.Count).ToList());
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
        /// <summary>Closures closer than this (centre to centre, single linkage) share one render mesh [m]. WORKING_VALUE.</summary>
        public const float ClosureGroupLinkM = 150f;
        /// <summary>Carriageways at least this wide get the B-1 sign on the barrier [m]; narrower service roads only the boards.</summary>
        public const float ClosureSignMinWidthM = 5.5f;

        // Linear albedos (COLOR_0 of Kamion/World Surface _FAR_FACADE; alpha 0 = no window grid), all WORKING_VALUE.
        // Sign sheeting, not weathered chimney paint: the first version reused the far-field chimney bands (linear
        // 0.62 = sRGB 0.81 white, 0.38 red) and on the shaded side of a board the white fell to the tone of the concrete
        // barrier behind it (review s15-0141 P1). White 0.80 linear (sRGB 0.91), red 0.52 linear (sRGB 0.75).
        static readonly Color32 k_Red = Lin(0.52f, 0.035f, 0.030f), k_White = Lin(0.80f, 0.80f, 0.78f);
        static readonly Color32 k_Steel = Lin(0.40f, 0.41f, 0.42f), k_SignBack = Lin(0.30f, 0.31f, 0.32f);
        static Color32 Lin(float r, float g, float b) =>
            new Color32((byte)Mathf.RoundToInt(r * 255f), (byte)Mathf.RoundToInt(g * 255f), (byte)Mathf.RoundToInt(b * 255f), 0);

        /// <summary>Single-linkage groups of closure indices (ordered by their first member), public for the EditMode test.</summary>
        public static List<List<int>> ClusterClosures(IList<WorldBoundary.Closure> closures, float linkM)
        {
            int n = closures.Count;
            var parent = Enumerable.Range(0, n).ToArray();
            int Find(int i) { while (parent[i] != i) i = parent[i] = parent[parent[i]]; return i; }
            for (int i = 0; i < n; i++)
                for (int j = i + 1; j < n; j++)
                {
                    Vector3 a = closures[i].localPos, b = closures[j].localPos;
                    if (Vector2.Distance(new Vector2(a.x, a.z), new Vector2(b.x, b.z)) < linkM) parent[Find(j)] = Find(i);
                }
            var byRoot = new Dictionary<int, List<int>>();
            var order = new List<List<int>>();
            for (int i = 0; i < n; i++)
            {
                int root = Find(i);
                if (!byRoot.TryGetValue(root, out var l)) { byRoot[root] = l = new List<int>(); order.Add(l); }
                l.Add(i);
            }
            return order;
        }

        /// <summary>Closures whose road directions differ by less than this are parallel for the merge [deg]. WORKING_VALUE.</summary>
        public const float ClosureMergeHeadingDeg = 25f;
        /// <summary>... and whose centres are no further apart than this along the road [m]. WORKING_VALUE.</summary>
        public const float ClosureMergeAlongM = 8f;

        /// <summary>
        /// Visible closures (ADR 0141 r6d): parallel closures whose barrier spans overlap - a carriageway and its slip
        /// lane, both cut by the region edge - become one closure over the union of the two spans, in the frame of the
        /// wider road. One barrier row, one pair of boards and one B-1 per carriageway instead of two overlapping sets.
        /// Carriageways separated by a median (spans do not overlap) and crossing roads stay separate. The input list
        /// is not modified. Public for the EditMode test.
        /// </summary>
        public static List<WorldBoundary.Closure> MergeOverlappingClosures(IList<WorldBoundary.Closure> closures)
        {
            var list = closures.ToList();
            for (bool merged = true; merged;)
            {
                merged = false;
                for (int i = 0; i < list.Count && !merged; i++)
                    for (int j = i + 1; j < list.Count && !merged; j++)
                    {
                        // a = the wider road: its frame, name and height are kept.
                        WorldBoundary.Closure a = list[i].widthM >= list[j].widthM ? list[i] : list[j];
                        WorldBoundary.Closure b = list[i].widthM >= list[j].widthM ? list[j] : list[i];
                        if (Mathf.Abs(Mathf.DeltaAngle(a.headingDeg, b.headingDeg)) > ClosureMergeHeadingDeg) continue;
                        float h = a.headingDeg * Mathf.Deg2Rad;
                        Vector2 fwd = new Vector2(Mathf.Sin(h), Mathf.Cos(h)), right = new Vector2(fwd.y, -fwd.x);
                        Vector2 d = new Vector2(b.localPos.x - a.localPos.x, b.localPos.z - a.localPos.z);
                        float lat = Vector2.Dot(d, right), along = Vector2.Dot(d, fwd);
                        float ha = ClosureSpan(a.widthM) * 0.5f, hb = ClosureSpan(b.widthM) * 0.5f;
                        if (Mathf.Abs(along) > ClosureMergeAlongM || Mathf.Abs(lat) >= ha + hb) continue;
                        float lo = Mathf.Min(-ha, lat - hb), hi = Mathf.Max(ha, lat + hb), mid = (lo + hi) * 0.5f;
                        var m = a;
                        m.localPos = a.localPos + new Vector3(right.x, 0f, right.y) * mid;
                        m.widthM = (hi - lo) - ClosureSpan(0f);
                        list[i] = m;
                        list.RemoveAt(j);
                        merged = true;
                    }
            }
            return list;
        }

        /// <summary>
        /// Render mesh of a group of closures in region-root space (ADR 0141). Each closure in its own frame: x across the
        /// road, z along the road towards the region edge, y up, origin on the road surface. A road closed for works:
        /// - a row of concrete barrier elements (2.0 m, 0.60 m base / 0.20 m top / 0.81 m high) - the physical stop,
        /// - in front of it (the side the driver arrives from, -z) a double U-20 road barrier on posts: two boards 0.25 m
        ///   high with 0.5 m red / white fields (board height and field length as ADR 0082; the 0.20 m gap between the
        ///   boards and the 1.20 m top edge are WORKING_VALUE),
        /// - on carriageways >= <see cref="ClosureSignMinWidthM"/> a B-1 "closed to all vehicles" disc (diameter
        ///   0.90 m, red rim 0.09 m, centre 1.85 m above the road: WORKING_VALUE) on the centre post.
        /// Submesh 0: concrete; submesh 1: paint, COLOR_0 = linear albedo.
        /// </summary>
        public static void BuildClosureGroupMesh(Mesh mesh, IList<WorldBoundary.Closure> closures)
        {
            var pos = new List<Vector3>(); var nrm = new List<Vector3>(); var uv = new List<Vector2>(); var col = new List<Color32>();
            var concrete = new List<int>(); var paint = new List<int>();
            void Paint(Color32 c) { while (col.Count < pos.Count) col.Add(c); }
            foreach (var c in closures)
            {
                int first = pos.Count;
                float span = ClosureSpan(c.widthM);
                int n = Mathf.Max(1, Mathf.CeilToInt(span / 2.0f));
                float len = span / n;
                for (int i = 0; i < n; i++)
                {
                    float x0 = -span * 0.5f + i * len + 0.03f, x1 = x0 + len - 0.06f;
                    Prism(pos, nrm, uv, concrete, x0, x1, 0.30f, 0.10f, 0f, 0.81f);
                }
                Paint(new Color32(255, 255, 255, 0));

                const float boardZ = -0.75f, field = 0.5f, boardH = 0.25f, topY = 1.20f, gap = 0.20f;
                int fields = Mathf.Max(2, Mathf.RoundToInt(span / field));
                float fw = span / fields;
                for (int b = 0; b < 2; b++)
                {
                    float y1 = topY - b * (boardH + gap), y0 = y1 - boardH;
                    for (int i = 0; i < fields; i++)
                    {
                        float x0 = -span * 0.5f + i * fw, x1 = x0 + fw;
                        s_Inside = new Vector3((x0 + x1) * 0.5f, (y0 + y1) * 0.5f, boardZ + 1f);
                        Face(pos, nrm, uv, paint, new Vector3(x0, y0, boardZ), new Vector3(x0, y1, boardZ), new Vector3(x1, y1, boardZ), new Vector3(x1, y0, boardZ));
                        Paint(i % 2 == 0 ? k_Red : k_White);
                    }
                    // Back of the board (seen only from beyond the closure): one plain face.
                    s_Inside = new Vector3(0f, (y0 + y1) * 0.5f, boardZ - 1f);
                    Face(pos, nrm, uv, paint, new Vector3(-span * 0.5f, y0, boardZ + 0.03f), new Vector3(-span * 0.5f, y1, boardZ + 0.03f),
                         new Vector3(span * 0.5f, y1, boardZ + 0.03f), new Vector3(span * 0.5f, y0, boardZ + 0.03f));
                    Paint(k_SignBack);
                }
                bool sign = c.widthM >= ClosureSignMinWidthM;
                const float signD = 0.90f, signY = 1.85f, rim = 0.09f;
                int posts = Mathf.Max(2, Mathf.CeilToInt(span / 2.5f) + 1);
                if (sign && posts % 2 == 0) posts++;   // a post on the road axis carries the sign
                for (int i = 0; i < posts; i++)
                {
                    float x = Mathf.Lerp(-span * 0.5f + 0.15f, span * 0.5f - 0.15f, i / (float)(posts - 1));
                    float top = sign && i == posts / 2 ? signY + signD * 0.5f - 0.05f : topY + 0.05f;
                    Vector3 lo = new Vector3(x - 0.03f, 0f, boardZ + 0.03f), hi = new Vector3(x + 0.03f, top, boardZ + 0.09f);
                    s_Inside = (lo + hi) * 0.5f;
                    Face(pos, nrm, uv, paint, new Vector3(lo.x, lo.y, hi.z), new Vector3(lo.x, hi.y, hi.z), new Vector3(hi.x, hi.y, hi.z), new Vector3(hi.x, lo.y, hi.z));   // +z
                    Face(pos, nrm, uv, paint, lo, new Vector3(lo.x, hi.y, lo.z), new Vector3(lo.x, hi.y, hi.z), new Vector3(lo.x, lo.y, hi.z));                             // -x
                    Face(pos, nrm, uv, paint, new Vector3(hi.x, lo.y, hi.z), hi, new Vector3(hi.x, hi.y, lo.z), new Vector3(hi.x, lo.y, lo.z));                             // +x
                    Paint(k_Steel);
                }
                if (sign)
                {
                    const int seg = 16;
                    float z = boardZ - 0.02f, ro = signD * 0.5f, ri = ro - rim;
                    int centre = pos.Count;
                    pos.Add(new Vector3(0f, signY, z)); nrm.Add(Vector3.back); uv.Add(new Vector2(0.5f, 0.5f));
                    for (int i = 0; i < seg; i++)
                    {
                        float a = i * Mathf.PI * 2f / seg;
                        pos.Add(new Vector3(Mathf.Sin(a) * ri, signY + Mathf.Cos(a) * ri, z)); nrm.Add(Vector3.back); uv.Add(Vector2.zero);
                    }
                    Paint(k_White);
                    int ring = pos.Count;
                    for (int i = 0; i < seg; i++)
                    {
                        float a = i * Mathf.PI * 2f / seg;
                        Vector3 d = new Vector3(Mathf.Sin(a), Mathf.Cos(a), 0f);
                        pos.Add(new Vector3(0f, signY, z) + d * ri); nrm.Add(Vector3.back); uv.Add(Vector2.zero);
                        pos.Add(new Vector3(0f, signY, z) + d * ro); nrm.Add(Vector3.back); uv.Add(Vector2.zero);
                    }
                    Paint(k_Red);
                    int back = pos.Count;
                    pos.Add(new Vector3(0f, signY, z + 0.015f)); nrm.Add(Vector3.forward); uv.Add(Vector2.zero);
                    for (int i = 0; i < seg; i++)
                    {
                        float a = i * Mathf.PI * 2f / seg;
                        pos.Add(new Vector3(Mathf.Sin(a) * ro, signY + Mathf.Cos(a) * ro, z + 0.015f)); nrm.Add(Vector3.forward); uv.Add(Vector2.zero);
                    }
                    Paint(k_SignBack);
                    // Seen from -z (the driver, +x to the right) the angle runs clockwise from the top, so
                    // centre, i, i + 1 is a clockwise (front) triangle; the back disc uses the opposite order.
                    for (int i = 0; i < seg; i++)
                    {
                        int j = (i + 1) % seg;
                        paint.Add(centre); paint.Add(centre + 1 + i); paint.Add(centre + 1 + j);
                        int a0 = ring + 2 * i, a1 = ring + 2 * i + 1, b0 = ring + 2 * j, b1 = ring + 2 * j + 1;
                        paint.Add(a0); paint.Add(a1); paint.Add(b1);
                        paint.Add(a0); paint.Add(b1); paint.Add(b0);
                        paint.Add(back); paint.Add(back + 1 + j); paint.Add(back + 1 + i);
                    }
                }
                // Closure frame -> region-root space.
                var trs = Matrix4x4.TRS(c.localPos, Quaternion.Euler(0f, c.headingDeg, 0f), Vector3.one);
                for (int i = first; i < pos.Count; i++) { pos[i] = trs.MultiplyPoint3x4(pos[i]); nrm[i] = trs.MultiplyVector(nrm[i]); }
            }
            mesh.Clear();
            mesh.indexFormat = pos.Count > 65000 ? IndexFormat.UInt32 : IndexFormat.UInt16;
            mesh.SetVertices(pos); mesh.SetNormals(nrm); mesh.SetUVs(0, uv); mesh.SetColors(col);
            mesh.subMeshCount = 2;
            mesh.SetTriangles(concrete, 0); mesh.SetTriangles(paint, 1);
            mesh.RecalculateTangents();
            mesh.RecalculateBounds();
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
