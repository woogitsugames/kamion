using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Game.Editor.Build;
using UnityEditor;
using UnityEngine;
using static Game.World.Import.MiniJson;

namespace Game.World.Import
{
    /// <summary>
    /// Bakes the point instances of a region (instances_*.json) and their prototype libraries
    /// (art-source/world/props/street_props.glb, art-source/world/vegetation/trees.glb + trees_lod2.glb impostors) into a
    /// <see cref="WorldInstanceSet"/> drawn by <see cref="WorldInstances"/> (GPU instancing, ADR 0012).
    ///
    /// Frames (docs/WORLD_GENERATION.md): props are authored "x right, y front, z up" and written as glTF (−x, z, y), so
    /// in Unity (after the reader's x mirror) local = (x, z, y): +Z is the front. yaw turns the prototype's front onto the
    /// direction (−sin yaw, cos yaw) in (E, N) → Unity rotation Euler(0, −yaw°, 0); sz scales the vertical axis.
    /// Trees come from Blender (export_yup: glTF = (bx, bz, −by)), so Unity local = (−bx, bz, −by); the instance rotation
    /// is Blender's Euler XYZ (lean cos 3yaw, lean sin 3yaw, yaw) about (E, N, U) as in tools/blender/world/render_control.py,
    /// scale h / href_m, base sunk 0.15 m.
    /// </summary>
    public static class InstanceImporter
    {
        public const float CellM = 64f;

        /// <summary>
        /// Fab details have independent bounds/culling cells, so their new geometry cannot change a legacy
        /// forest cell's frustum, near/far LOD band or HLOD switch. Bit 50 is outside the region grid domain.
        /// Toggle rather than OR: negative boundary cells already have that bit set by signed grid encoding.
        /// Legacy keys, matrix storage and collider placement are unchanged.
        /// </summary>
        public static long DetailCellKey(long cellKey, bool fab) => fab ? cellKey ^ (1L << 50) : cellKey;


        /// <summary>
        /// Keep every pre-Fab matrix at its legacy sorted index. Runtime forest thinning uses the absolute
        /// matrix index, so inserting licensed details into the old sort changes the selected trees. Sort the
        /// unchanged legacy input separately with precisely the old comparison (including its equal-key order),
        /// then append the separately sorted Fab matrices. Cell runs may point into either storage partition.
        /// This pure helper also permits an asset-free regression test without importing editor assemblies.
        /// </summary>
        public static int[] LegacyStorageOrder(long[] cells, bool[] forests, int[] prototypes, bool[] fab)
        {
            if (cells == null || forests == null || prototypes == null || fab == null)
                throw new ArgumentNullException("Instance sort keys");
            int count = cells.Length;
            if (forests.Length != count || prototypes.Length != count || fab.Length != count)
                throw new ArgumentException("Instance sort key lengths differ");
            var legacy = new List<int>();
            var details = new List<int>();
            for (int i = 0; i < count; i++) (fab[i] ? details : legacy).Add(i);
            int Compare(int a, int b) => cells[a] != cells[b] ? cells[a].CompareTo(cells[b])
                : forests[a] != forests[b] ? forests[a].CompareTo(forests[b]) : prototypes[a].CompareTo(prototypes[b]);
            legacy.Sort(Compare);
            details.Sort(Compare);
            legacy.AddRange(details);
            return legacy.ToArray();
        }

        public sealed class Colliders
        {
            public readonly List<(string proto, Matrix4x4 m, Bounds local)> Items = new List<(string, Matrix4x4, Bounds)>();
            public int Count => Items.Count;
            /// <summary>Automatic boom barriers (instances "barrier_boom" with a "barrier" object; DepotBarrier, MA-003).</summary>
            public readonly List<Barrier> Barriers = new List<Barrier>();
        }

        /// <summary>One boom of a depot gate: transform of the hinge (region-root space), boom mesh + materials, drive data.</summary>
        public sealed class Barrier
        {
            public Matrix4x4 M;
            public Mesh Mesh;
            public Material[] Materials;
            public float Length = 5.85f, OpenDeg = 85f, Travel = 1f;
        }

        /// <summary>LOD end distances (m at lodBias 1; last = cull) and shadow mask per prototype family. WORKING_VALUE.</summary>
        static (float[] ends, int shadowMask) Policy(string proto, int lodCount)
        {
            float[] e;
            // Trees: the forest along DK8 is the worst view - with 30/100 m it drew 0.78 M instanced triangles on
            // Medium (budget 0.55 M for everything); 20/60 m keeps Medium at ~0.3 M there.
            if (proto.StartsWith("tree_shrub")) e = new[] { 12f, 40f, 300f };
            else if (proto.StartsWith("tree_")) e = new[] { 20f, 60f, 1000f };
            else if (proto.StartsWith("fab_")) e = new[] { 12f, 30f, 65f };
            else if (proto.StartsWith("lamp_")) e = new[] { 60f, 400f };
            else if (proto == "pylon" || proto == "power_pole") e = new[] { 80f, 1500f };
            else if (proto.StartsWith("plate_") || proto.StartsWith("board_") || proto.StartsWith("sign_") || proto.StartsWith("signal_")) e = new[] { 50f, 250f };
            else if (proto == "bus_shelter" || proto.EndsWith("_gate")) e = new[] { 60f, 300f };
            // Hero depot hall segments (ADR 0071, art-source/world/landmarks): LOD0 / LOD1 / silhouette, never culled.
            else if (proto.StartsWith("landmark_depot")) e = new[] { 100f, 400f, 20000f };
            // Hero viaduct segments (ADR 0067, art-source/world/landmarks): LOD0 / LOD1 / silhouette, never culled.
            else if (proto.StartsWith("landmark_viaduct")) e = new[] { 90f, 300f, 20000f };
            // Landmarks (chimneys): visible across the district, never culled inside the far plane.
            else if (proto.StartsWith("landmark_")) e = new[] { 650f, 20000f };
            // Vehicles (ADR 0041 v4, REVIEW r6 W-N6): LOD switches x lodBias, cull FIXED at VehicleCullM on every tier
            // (WorldInstances.IsVehicle), so Low shows the same parked cars and truck rigs as High.
            // Cars / vans: LOD0 detail, LOD1 simple wheels, LOD2 profile prism (~55 tris). Low (lodBias 0.5): 16 / 42.5 / 300 m
            // (LOD0 floor WorldInstances.VehicleLod0MinM, ADR 0041 r8; 12.5 m without it). LOD1 end 90 -> 85 m with the richer r8 LOD1: keeps the stretch_04 High
            // frame estimate under 2.0 M (build_world.mesh_budget).
            else if (proto.StartsWith("car_") || proto.StartsWith("van_")) e = new[] { 25f, 85f, WorldInstances.VehicleCullM };
            else if (proto.StartsWith("tractor_") || proto.StartsWith("trailer_")) e = new[] { 40f, WorldInstances.VehicleCullM };
            else e = new[] { 30f, 120f };   // bench, bollard, waste bin, street cabinet, pallets, containers
            // Mirror: tools/worldgen/roads/build_world.py instance_ends() (frame estimate) - keep the two in sync.
            if (e.Length > lodCount) e = new[] { e[0] }.Concat(e.Skip(e.Length - lodCount + 1)).ToArray();
            // A hall shades the yard in front of it, a viaduct the road under it: LOD1 keeps casting (no pop at the LOD switch).
            int shadows = proto.StartsWith("tree_") || proto.StartsWith("landmark_depot") || proto.StartsWith("landmark_viaduct") ? 0b011 : 0b001;
            return (e.Take(lodCount).ToArray(), shadows);
        }

        public static WorldInstanceSet Build(RegionImporter.Result r, List<string> instanceFiles, out Colliders colliders)
        {
            string art = Path.Combine(EditorTools.RepoRoot, "art-source", "world");
            var props = GlbReader.Load(Path.Combine(art, "props", "street_props.glb"));
            var trees = GlbReader.Load(Path.Combine(art, "vegetation", "trees.glb"));
            var impostors = GlbReader.Load(Path.Combine(art, "vegetation", "trees_lod2.glb"));
            // Authored landmark assets (ADR 0067 / 0071): art-source/world/landmarks/<asset>/<asset>.glb, prototypes
            // "landmark_<...>" (+ .lod1 / .lod2) in the same frame as street_props.glb.
            var landmarkLibs = new List<GlbReader>();
            string lmDir = Path.Combine(art, "landmarks");
            if (Directory.Exists(lmDir))
                foreach (var f in Directory.GetFiles(lmDir, "*.glb", SearchOption.AllDirectories).OrderBy(x => x, StringComparer.Ordinal))
                    landmarkLibs.Add(GlbReader.Load(f));
            var treeMeta = Obj(Obj(Parse(File.ReadAllText(Path.Combine(art, "vegetation", "trees_meta.json")))).Get("trees"));

            string path = $"{r.Dir}/Instances.asset";
            AssetDatabase.DeleteAsset(path);
            var set = ScriptableObject.CreateInstance<WorldInstanceSet>();
            set.name = "Instances_" + r.Region;
            AssetDatabase.CreateAsset(set, path);
            Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, r.Dir, "Materials", "Proto"));

            var protoIndex = new Dictionary<string, int>();
            var protos = new List<WorldInstanceSet.Prototype>();
            var materials = new List<Material>();
            var colMeshes = new Dictionary<string, Bounds?>();
            var contactOf = new Dictionary<int, int>();   // vehicle prototype -> its contact patch prototype (ADR 0050)
            long bytes = 0;

            int Proto(string name)
            {
                if (protoIndex.TryGetValue(name, out int idx)) return idx;
                bool tree = name.StartsWith("tree_");
                var lodNodes = new List<(GlbReader g, GlbReader.MeshNode n)>();
                var src = tree ? trees : props;
                var n0 = src.Find(name);
                if (n0 == null && !tree)
                    foreach (var lib in landmarkLibs)
                        if (lib.Find(name) is GlbReader.MeshNode ln) { src = lib; n0 = ln; break; }
                if (n0 == null && name.StartsWith("fab_") && FabMaterials.Library(name) is string fabPath)
                {
                    src = GlbReader.Load(fabPath);
                    n0 = src.Find(name);
                }
                if (n0 == null) { Debug.LogWarning($"[IMPORT] prototype '{name}' not in the library - instances skipped"); protoIndex[name] = -1; return -1; }
                lodNodes.Add((src, n0));
                var n1 = src.Find(name + ".lod1");
                if (n1 != null) lodNodes.Add((src, n1));
                if (tree && impostors.Find(name + ".lod2") is GlbReader.MeshNode n2) lodNodes.Add((impostors, n2));
                else if (!tree && n1 != null && src.Find(name + ".lod2") is GlbReader.MeshNode p2) lodNodes.Add((src, p2));
                var p = new WorldInstanceSet.Prototype { name = name };
                var lods = new List<Mesh>();
                var starts = new List<int>();
                foreach (var (g, n) in lodNodes)
                {
                    starts.Add(materials.Count);
                    bool uv = false;
                    foreach (var prim in n.Primitives)
                    {
                        var mat = ProtoMaterial(r, g, prim.Material, out bool textured);
                        materials.Add(mat);
                        uv |= textured;
                    }
                    var mesh = WorldMeshBake.Compact(n.Name, n.Primitives, new WorldMeshBake.Options { Uv0 = uv });
                    AssetDatabase.AddObjectToAsset(mesh, set);
                    bytes += WorldMeshBake.GpuBytes(mesh);
                    lods.Add(mesh);
                }
                p.lods = lods.ToArray();
                p.materialStart = starts.ToArray();
                var (ends, mask) = Policy(name, p.lods.Length);
                p.lodEndM = ends;
                p.shadowLodMask = mask;
                // Prop collider = box around the part of the .col mesh below 2.6 m (the post / foot), extended to 2.6 m.
                // The whole .col bounds of a lamp or signal mast include the arm over the carriageway: a box around it
                // was a wall across the lane (route test stuck at s = 613 m, S24+ autopilot stopped). Gates (lift,
                // sliding) get none for now: they are open in gameplay and their boom crosses the access road.
                var col = !tree && !name.EndsWith("_gate") ? props.Find(name + ".col") : null;
                if (col != null)
                {
                    const float h = 2.6f;
                    Bounds? b = null;
                    foreach (var prim in col.Primitives)
                        foreach (var v in prim.Positions)
                            if (v.y <= h) { if (b == null) b = new Bounds(v, Vector3.zero); else { var bb = b.Value; bb.Encapsulate(v); b = bb; } }
                    if (b != null)
                    {
                        var bv = b.Value;
                        bv.SetMinMax(bv.min, new Vector3(bv.max.x, h, bv.max.z));
                        colMeshes[name] = bv;
                    }
                }
                idx = protos.Count;
                protos.Add(p);
                protoIndex[name] = idx;
                // Contact shadow / AO patch of a vehicle (ADR 0050): node "<name>.contact"; every vehicle instance also
                // becomes an instance of the patch prototype of its spec (one instanced draw per spec for all vehicles).
                if (!tree && props.Find(name + ".contact") is GlbReader.MeshNode cn)
                    contactOf[idx] = ContactProto(cn, name);
                return idx;
            }

            // One prototype per distinct contact spec: a single LOD (the patch quad) culled with the vehicles, no shadows.
            int ContactProto(GlbReader.MeshNode cn, string vehicle)
            {
                var spec = cn.Extras != null ? cn.Extras.Get("contact") as Dictionary<string, object> : null;
                var mat = ContactMaterial(r, spec, vehicle, out string id);
                if (protoIndex.TryGetValue(id, out int ci)) return ci;
                var mesh = WorldMeshBake.Compact(id, cn.Primitives, new WorldMeshBake.Options());
                AssetDatabase.AddObjectToAsset(mesh, set);
                bytes += WorldMeshBake.GpuBytes(mesh);
                var cp = new WorldInstanceSet.Prototype
                {
                    name = id, lods = new[] { mesh }, materialStart = new[] { materials.Count },
                    lodEndM = new[] { WorldInstances.VehicleCullM }, shadowLodMask = 0,
                };
                materials.Add(mat);
                ci = protos.Count;
                protos.Add(cp);
                protoIndex[id] = ci;
                return ci;
            }

            // ---- instances ----
            var items = new List<(long cell, bool forest, int proto, Matrix4x4 m)>();
            colliders = new Colliders();
            var corridor = r.Chunks.Where(c => c.Corridor).ToList();
            float minE = r.Chunks.Min(c => c.Min.x), minN = r.Chunks.Min(c => c.Min.y);
            long CellKey(float e, float n) => ((long)Mathf.Floor((n - minN) / CellM) << 20) | (long)Mathf.Floor((e - minE) / CellM);

            // ---- forest HLOD cells (ADR 0015): one mesh per 64 m cell; its trees ("fc") go into that instance cell ----
            var hlods = new List<WorldInstanceSet.Hlod>();
            var hlodKey = new Dictionary<string, long>();
            var hlodOfKey = new Dictionary<long, int>();
            var hlodChunk = new List<string>();
            var hlodSrc = new List<int>();
            int srcIndex = -1;
            foreach (var (cid, node, chunkId) in r.ForestHlod)
            {
                srcIndex++;
                if (hlodKey.ContainsKey(cid)) { Debug.LogWarning($"[IMPORT] forest HLOD cell {cid} appears twice"); continue; }
                var h = new WorldInstanceSet.Hlod { id = cid, materialStart = materials.Count };
                if (node.Extras != null && node.Extras.Get("trees") != null) h.trees = (int)Num(node.Extras.Get("trees"));
                foreach (var prim in node.Primitives)
                {
                    Material hm = null;
                    if (prim.Material == null || !r.Materials.TryGetValue(prim.Material, out hm))
                        Debug.LogWarning($"[IMPORT] forest HLOD {cid}: material '{prim.Material}' not in manifest");
                    materials.Add(hm);
                }
                h.mesh = WorldMeshBake.Compact("forest_hlod_" + cid, node.Primitives, new WorldMeshBake.Options { Uv0 = true });
                AssetDatabase.AddObjectToAsset(h.mesh, set);
                bytes += WorldMeshBake.GpuBytes(h.mesh);
                var c = h.mesh.bounds.center;
                long key = CellKey(c.x, c.z);
                if (hlodOfKey.ContainsKey(key)) { Debug.LogWarning($"[IMPORT] forest HLOD {cid}: instance cell already has an HLOD"); continue; }
                hlodKey[cid] = key;
                hlodOfKey[key] = hlods.Count;
                hlods.Add(h);
                hlodChunk.Add(chunkId);
                hlodSrc.Add(srcIndex);
            }
            // Per-chunk merge of the HLOD cells (one submesh per material): drawn instead of the cells when the whole
            // chunk is beyond the switch distance - a cell draw per material cost 550 draws in the truck-34 view on High.
            var groups = new List<WorldInstanceSet.HlodGroup>();
            foreach (var g in Enumerable.Range(0, hlods.Count).GroupBy(i => hlodChunk[i]))
            {
                var byMat = new Dictionary<string, List<GlbReader.Primitive>>();
                foreach (int hi in g)
                {
                    hlods[hi].group = groups.Count;
                    foreach (var prim in r.ForestHlod[hlodSrc[hi]].node.Primitives)
                    {
                        string mk = prim.Material ?? "";
                        if (!byMat.TryGetValue(mk, out var list)) byMat[mk] = list = new List<GlbReader.Primitive>();
                        list.Add(prim);
                    }
                }
                var grp = new WorldInstanceSet.HlodGroup { id = g.Key, materialStart = materials.Count };
                var merged = new List<GlbReader.Primitive>();
                foreach (var kv in byMat.OrderBy(k => k.Key, StringComparer.Ordinal))
                {
                    merged.Add(MergePrimitives(kv.Value));
                    r.Materials.TryGetValue(kv.Key, out var gm);
                    materials.Add(gm);
                }
                grp.mesh = WorldMeshBake.Compact("forest_hlod_chunk_" + g.Key, merged, new WorldMeshBake.Options { Uv0 = true });
                AssetDatabase.AddObjectToAsset(grp.mesh, set);
                bytes += WorldMeshBake.GpuBytes(grp.mesh);
                groups.Add(grp);
            }
            int forestTrees = 0, forestOrphans = 0;
            foreach (var f in instanceFiles)
            {
                if (!File.Exists(f)) throw new FileNotFoundException(f + " missing - rerun build_world.py");
                foreach (var io in Arr(Obj(Parse(File.ReadAllText(f))).Get("instances")))
                {
                    var it = Obj(io);
                    string p = Str(it.Get("p"));
                    float e = (float)Num(it.Get("e")), n = (float)Num(it.Get("n")), z = (float)Num(it.Get("z")), yaw = (float)Num(it.Get("yaw"));
                    long cellKey = CellKey(e, n);
                    bool forest = false;
                    if (it.Get("fc") is string fc)
                    {
                        if (hlodKey.TryGetValue(fc, out long hk)) { cellKey = hk; forest = true; forestTrees++; }
                        else forestOrphans++;
                    }
                    Matrix4x4 m;
                    if (p.StartsWith("tree_"))
                    {
                        p = $"{p}_{(int)Num(it.Get("v"))}";
                        float href = treeMeta.Get(p) is Dictionary<string, object> tm ? (float)Num(tm.Get("href_m")) : 0f;
                        if (href <= 0f) { Debug.LogWarning($"[IMPORT] {p}: no href_m in trees_meta.json"); continue; }
                        float lean = it.Get("lean") != null ? (float)Num(it.Get("lean")) : 0f;
                        m = TreeMatrix(new Vector3(e, z - 0.15f, n), yaw, lean * Mathf.Cos(yaw * 3f), lean * Mathf.Sin(yaw * 3f), (float)Num(it.Get("h")) / href);
                    }
                    else
                    {
                        float sz = it.Get("sz") != null ? (float)Num(it.Get("sz")) : 1f;
                        m = Matrix4x4.TRS(new Vector3(e, z, n), Quaternion.Euler(0f, -yaw * Mathf.Rad2Deg, 0f), new Vector3(1f, sz, 1f));
                    }
                    int pi = Proto(p);
                    if (pi < 0) continue;
                    // Boom of an automatic barrier: a GameObject with DepotBarrier (WorldSceneBuilder), not a static instance.
                    if (it.Get("barrier") is Dictionary<string, object> bd)
                    {
                        var bp = protos[pi];
                        var bar = new Barrier { M = m, Mesh = bp.lods[0], Materials = materials.Skip(bp.materialStart[0]).Take(bp.lods[0].subMeshCount).ToArray() };
                        if (bd.Get("L") != null) bar.Length = (float)Num(bd.Get("L"));
                        if (bd.Get("open_deg") != null) bar.OpenDeg = (float)Num(bd.Get("open_deg"));
                        if (bd.Get("travel") != null) bar.Travel = (float)Num(bd.Get("travel"));
                        colliders.Barriers.Add(bar);
                        continue;
                    }
                    long drawCellKey = DetailCellKey(cellKey, p.StartsWith("fab_", StringComparison.Ordinal));
                    items.Add((drawCellKey, forest, pi, m));
                    if (contactOf.TryGetValue(pi, out int cpi)) items.Add((cellKey, false, cpi, m));
                    if (colMeshes.TryGetValue(p, out var cb) && cb.HasValue && corridor.Any(c => e >= c.Min.x && e < c.Max.x && n >= c.Min.y && n < c.Max.y))
                        colliders.Items.Add((p, m, cb.Value));
                }
            }

            var storageOrder = LegacyStorageOrder(items.Select(it => it.cell).ToArray(), items.Select(it => it.forest).ToArray(),
                items.Select(it => it.proto).ToArray(), items.Select(it => protos[it.proto].name.StartsWith("fab_", StringComparison.Ordinal)).ToArray());
            var stored = storageOrder.Select(i => items[i]).ToArray();
            var mats = stored.Select(it => it.m).ToArray();
            // Each partition is already sorted. Record its contiguous runs before merging the run order;
            // sorting individual matrices again would reintroduce the unstable equal-key permutation.
            var orderedRuns = new List<(long cell, bool forest, int proto, int start, int count)>();
            for (int i = 0; i < stored.Length;)
            {
                int start = i;
                var first = stored[i++];
                while (i < stored.Length && stored[i].cell == first.cell && stored[i].forest == first.forest && stored[i].proto == first.proto) i++;
                orderedRuns.Add((first.cell, first.forest, first.proto, start, i - start));
            }
            orderedRuns.Sort((a, b) => a.cell != b.cell ? a.cell.CompareTo(b.cell) : a.forest != b.forest ? a.forest.CompareTo(b.forest) : a.proto.CompareTo(b.proto));
            var cells = new List<WorldInstanceSet.Cell>();
            var runs = new List<WorldInstanceSet.Run>();
            var hlodUsed = new bool[hlods.Count];
            for (int ri = 0; ri < orderedRuns.Count;)
            {
                long cell = orderedRuns[ri].cell;
                var c = new WorldInstanceSet.Cell { runStart = runs.Count };
                bool first = true;
                while (ri < orderedRuns.Count && orderedRuns[ri].cell == cell)
                {
                    var run = orderedRuns[ri++];
                    int pr = run.proto;
                    for (int i = run.start; i < run.start + run.count; i++)
                    {
                        var wb = Transform(protos[pr].lods[0].bounds, mats[i]);
                        if (first) { c.bounds = wb; first = false; } else c.bounds.Encapsulate(wb);
                    }
                    runs.Add(new WorldInstanceSet.Run { prototype = pr, start = run.start, count = run.count, forest = run.forest });
                    protos[pr].count += run.count;
                }
                c.runCount = runs.Count - c.runStart;
                if (hlodOfKey.TryGetValue(cell, out int hi))
                {
                    c.hlod = hi + 1;
                    c.bounds.Encapsulate(hlods[hi].mesh.bounds);
                    hlodUsed[hi] = true;
                }
                cells.Add(c);
            }
            for (int hi = 0; hi < hlods.Count; hi++)   // an HLOD cell without instances (cannot happen with MIN_TREES ≥ 8; kept for safety)
                if (!hlodUsed[hi]) cells.Add(new WorldInstanceSet.Cell { bounds = hlods[hi].mesh.bounds, runStart = runs.Count, runCount = 0, hlod = hi + 1 });
            set.prototypes = protos.ToArray();
            set.materials = materials.ToArray();
            set.cells = cells.ToArray();
            set.runs = runs.ToArray();
            // compact TRS in the asset (26 B instead of 64 B per instance, ADR 0025); full matrices only when a matrix does not round-trip
            if (!set.Pack(mats)) Debug.LogWarning("[IMPORT] instances: a matrix does not round-trip as compact TRS, full matrices kept");
            set.hlods = hlods.ToArray();
            set.hlodGroups = groups.ToArray();
            Debug.Log($"[IMPORT] forest HLOD: {hlods.Count} cells, {hlods.Sum(h => Enumerable.Range(0, h.mesh.subMeshCount).Sum(k => (long)h.mesh.GetIndexCount(k) / 3))} triangles, " +
                      $"{forestTrees} forest trees switchable, {forestOrphans} with an unknown fc cell");
            EditorUtility.SetDirty(set);
            bytes += mats.Length * 64L;
            r.MemoryBytes["instances"] = bytes;
            Debug.Log($"[IMPORT] instances: {mats.Length} in {cells.Count} cells, {protos.Count} prototypes " +
                      $"({string.Join(", ", protos.OrderByDescending(q => q.count).Take(8).Select(q => $"{q.name} {q.count}"))}…), " +
                      $"{colliders.Count} prop colliders in the corridor, prototype meshes + matrices {bytes / 1048576.0:F1} MB");
            return set;
        }

        static GlbReader.Primitive MergePrimitives(List<GlbReader.Primitive> prims)
        {
            if (prims.Count == 1) return prims[0];
            var pos = new List<Vector3>(); var nrm = new List<Vector3>(); var uv = new List<Vector2>(); var idx = new List<int>();
            foreach (var p in prims)
            {
                int b = pos.Count;
                pos.AddRange(p.Positions);
                if (p.Normals != null) nrm.AddRange(p.Normals); else nrm.AddRange(Enumerable.Repeat(Vector3.up, p.Positions.Length));
                if (p.Uv0 != null) uv.AddRange(p.Uv0); else uv.AddRange(new Vector2[p.Positions.Length]);
                foreach (int i in p.Indices) idx.Add(i + b);
            }
            return new GlbReader.Primitive { Material = prims[0].Material, Positions = pos.ToArray(), Normals = nrm.ToArray(), Uv0 = uv.ToArray(), Indices = idx.ToArray() };
        }

        /// <summary>Blender Euler XYZ (rx, ry, yaw) about (E, N, U), tree local from the export_yup GLB, uniform scale.</summary>
        static Matrix4x4 TreeMatrix(Vector3 pos, float yaw, float rx, float ry, float scale)
        {
            Matrix4x4 Rz(float a) { var m = Matrix4x4.identity; float c = Mathf.Cos(a), s = Mathf.Sin(a); m.m00 = c; m.m01 = -s; m.m10 = s; m.m11 = c; return m; }
            Matrix4x4 Ry(float a) { var m = Matrix4x4.identity; float c = Mathf.Cos(a), s = Mathf.Sin(a); m.m00 = c; m.m02 = s; m.m20 = -s; m.m22 = c; return m; }
            Matrix4x4 Rx(float a) { var m = Matrix4x4.identity; float c = Mathf.Cos(a), s = Mathf.Sin(a); m.m11 = c; m.m12 = -s; m.m21 = s; m.m22 = c; return m; }
            var rb = Rz(yaw) * Ry(ry) * Rx(rx);
            // P: Blender (x, y, z) → Unity (x, z, y). B: Unity tree local (ux, uy, uz) → Blender local (−ux, −uz, uy).
            var P = Matrix4x4.zero; P.m00 = 1; P.m12 = 1; P.m21 = 1; P.m33 = 1;
            var B = Matrix4x4.zero; B.m00 = -1; B.m12 = -1; B.m21 = 1; B.m33 = 1;
            var m3 = P * rb * B * Matrix4x4.Scale(Vector3.one * scale);
            m3.m03 = pos.x; m3.m13 = pos.y; m3.m23 = pos.z;
            return m3;
        }

        static Bounds Transform(Bounds b, Matrix4x4 m)
        {
            var c = m.MultiplyPoint3x4(b.center);
            var e = b.extents;
            var ext = new Vector3(
                Mathf.Abs(m.m00) * e.x + Mathf.Abs(m.m01) * e.y + Mathf.Abs(m.m02) * e.z,
                Mathf.Abs(m.m10) * e.x + Mathf.Abs(m.m11) * e.y + Mathf.Abs(m.m12) * e.z,
                Mathf.Abs(m.m20) * e.x + Mathf.Abs(m.m21) * e.y + Mathf.Abs(m.m22) * e.z);
            return new Bounds(c, ext * 2f);
        }

        // ------------------------------------------------------------------------------------------------- materials
        static readonly Dictionary<string, Material> s_ProtoMats = new Dictionary<string, Material>();

        /// <summary>
        /// Kamion/World Vehicle Contact material for a prototype's contact spec (ADR 0050). Prototypes with the same spec
        /// (one body in six colours) share one asset, named after a hash of the spec so a reimport overwrites it in place.
        /// </summary>
        static Material ContactMaterial(RegionImporter.Result r, Dictionary<string, object> spec, string proto, out string id)
        {
            if (spec == null) Debug.LogWarning($"[IMPORT] {proto}: vehicle_contact patch without a contact spec - shader defaults");
            var key = new System.Text.StringBuilder();
            if (spec != null)
                foreach (var k in spec.Keys.OrderBy(k => k, StringComparer.Ordinal))
                {
                    key.Append(k).Append('=');
                    foreach (var x in Arr(spec[k])) key.Append(((float)Num(x)).ToString("R", System.Globalization.CultureInfo.InvariantCulture)).Append(',');
                    key.Append(';');
                }
            string hash;
            using (var sha = System.Security.Cryptography.SHA256.Create())
                hash = BitConverter.ToString(sha.ComputeHash(System.Text.Encoding.UTF8.GetBytes(key.ToString()))).Replace("-", "").ToLowerInvariant();
            id = "contact_" + hash.Substring(0, 10);
            if (s_ProtoMats.TryGetValue(id, out var cached) && cached != null) return cached;
            var mat = RegionImporter.VehicleContactMaterial($"{r.Dir}/Materials/Proto/M_{id}.mat", spec);
            s_ProtoMats[id] = mat;
            return mat;
        }

        /// <summary>
        /// Material of a prototype primitive: region materials (manifest) for plain parts; URP Lit with the library's own
        /// textures (art-source PNG, imported with mobile settings) for sign faces, bark, leaves and impostors.
        /// Leaves / impostors: alpha clip 0.5 with coverage-preserving mips and alpha-to-coverage under MSAA, double sided
        /// (glTF BLEND would need sorting per instance). Sign faces: alpha clip, back faces culled (the plate back hides
        /// them from behind, as in the Blender renders).
        /// </summary>
        static Material ProtoMaterial(RegionImporter.Result r, GlbReader g, string name, out bool textured)
        {
            textured = false;
            if (name == null) return null;
            var fab = FabMaterials.Create(r, name, $"{r.Dir}/Materials/Proto/M_{name}.mat");
            if (fab != null) { textured = true; return fab; }
            if (r.Materials.TryGetValue(name, out var regionMat))
            {
                textured = r.MaterialDefs.TryGetValue(name, out var d) && d.Get("texture") != null;
                if (d != null)
                {
                    WorldPbrMaterials.Channels(d, name, out bool pbrUv0, out _, out _);   // ADR 0022: mesh UV in metres
                    textured |= pbrUv0;
                }
                return regionMat;
            }
            var info = g.Materials.FirstOrDefault(m => m.Name == name);
            textured = info != null && info.HasBaseColorTexture;
            if (s_ProtoMats.TryGetValue(name, out var cached) && cached != null) return cached;
            string art = Path.Combine(EditorTools.RepoRoot, "art-source", "world");
            string png = null;
            bool sign = name.StartsWith("sign_");
            if (sign) png = Path.Combine(art, "signs", name.Substring(5) + ".png");
            else if (info?.BaseColorImageName != null) png = Path.Combine(art, "vegetation", info.BaseColorImageName + ".png");
            Texture2D tex = null;
            if (png != null)
            {
                if (File.Exists(png)) tex = ImportTexture(r, png, clamp: sign || name.StartsWith("impostor_"));
                else Debug.LogWarning($"[IMPORT] {name}: texture {png} missing");
            }
            // Impostors (ADR 0023): N views + view-space normal / sky visibility, drawn by Kamion/Vegetation _IMPOSTOR.
            if (name.StartsWith("impostor_") && png != null)
            {
                string npng = Path.Combine(Path.GetDirectoryName(png), Path.GetFileNameWithoutExtension(png) + "_n.png");
                var tm = Obj(Obj(Parse(File.ReadAllText(Path.Combine(art, "vegetation", "trees_meta.json")))).Get("trees"));
                float views = tm.Get(name.Substring("impostor_".Length)) is Dictionary<string, object> e && e.Get("impostor_views") != null
                    ? (float)Num(e.Get("impostor_views")) : 1f;
                if (File.Exists(npng) && views > 1f)
                {
                    var vm = VegetationMaterial($"{r.Dir}/Materials/Proto/M_{name}.mat", tex, ImportTexture(r, npng, clamp: true, linear: true),
                        "_IMPOSTOR", new Vector4(views, ImpostorVisibility.x, ImpostorVisibility.y, 0f), info != null ? info.AlphaCutoff : 0.5f);
                    s_ProtoMats[name] = vm;
                    return vm;
                }
                Debug.LogWarning($"[IMPORT] {name}: no multi-view bake ({npng}) - drawn as a flat card");
            }
            bool foliage = name.StartsWith("leaves_") || name.StartsWith("impostor_");
            bool clip = foliage || sign || (info != null && info.AlphaMode != "OPAQUE");
            bool twoSided = foliage || name == "bark_twig";
            float rough = foliage ? 0.75f : sign ? 0.45f : 0.9f;
            var baseCol = info != null ? info.BaseColorFactor.linear : Color.white;   // glTF factors are linear
            var mat = RegionImporter.LitMaterial($"{r.Dir}/Materials/Proto/M_{name}.mat", new Color(baseCol.r, baseCol.g, baseCol.b), rough, 0f, tex, clip,
                info != null ? info.AlphaCutoff : 0.5f, twoSided, null);
            s_ProtoMats[name] = mat;
            return mat;
        }

        /// <summary>
        /// Sky-visibility strength of the impostor bake (Kamion/Vegetation _Impostor.y ambient, .z sun). Chosen so that the
        /// impostor crown matches the LOD1 cards (no occlusion term) in mean luminance at the switch distance:
        /// WORKING_VALUE, measured in artifacts/vqa (ADR 0023 table).
        /// </summary>
        public static readonly Vector2 ImpostorVisibility = new Vector2(0.45f, 0.25f);
        /// <summary>HLOD edge walls: the stand interior is dark only through the visibility map, so it applies fully.</summary>
        public static readonly Vector2 EdgeVisibility = new Vector2(1.0f, 0.6f);

        /// <summary>Kamion/Vegetation material asset (impostor / HLOD edge variant), alpha-to-coverage, double sided, instanced.</summary>
        public static Material VegetationMaterial(string path, Texture2D tex, Texture2D normalOcc, string keyword, Vector4 impostor, float cutoff)
        {
            var shader = Shader.Find("Kamion/Vegetation");
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); }
            mat.shader = shader;
            mat.shaderKeywords = new string[0];
            mat.EnableKeyword(keyword);
            mat.EnableKeyword("_ALPHATEST_ON");      // WorldInstances.IsFoliage / SetLeafAlphaToCoverage
            mat.enableInstancing = true;
            mat.SetTexture("_BaseMap", tex);
            mat.SetTexture("_NormalOcc", normalOcc);
            mat.SetColor("_BaseColor", Color.white);
            mat.SetVector("_Impostor", impostor);
            mat.SetFloat("_Cutoff", cutoff);
            mat.SetFloat("_Cull", 0f);
            mat.SetFloat("_AlphaToMask", 1f);
            mat.renderQueue = (int)UnityEngine.Rendering.RenderQueue.AlphaTest;
            EditorUtility.SetDirty(mat);
            return mat;
        }

        /// <summary>Copies an art-source PNG into the generated textures folder with mobile import settings.</summary>
        public static Texture2D ImportTexture(RegionImporter.Result r, string png, bool clamp, bool linear = false)
        {
            string file = Path.GetFileName(png);
            string dst = $"{r.Dir}/Textures/{file}";
            string full = Path.Combine(EditorTools.ProjectRoot, dst);
            if (!File.Exists(full) || !File.ReadAllBytes(full).SequenceEqual(File.ReadAllBytes(png)))
            {
                File.Copy(png, full, true);
                AssetDatabase.ImportAsset(dst, ImportAssetOptions.ForceSynchronousImport);
            }
            var ti = (TextureImporter)AssetImporter.GetAtPath(dst);
            bool alpha = !linear && (file.StartsWith("leaves_") || file.StartsWith("impostor_") || file.StartsWith("fence_") || file.StartsWith("dock_") || !file.StartsWith("bark_"));
            bool text = file.StartsWith("dock_") || file.Contains("-");   // sign faces (A-7, B-33_30, E-2_*) and dock numbers: legible
            ti.textureType = TextureImporterType.Default;
            ti.sRGBTexture = !linear;          // normal / visibility maps (_n.png) are data
            ti.mipmapEnabled = true;
            ti.alphaSource = TextureImporterAlphaSource.FromInput;
            ti.alphaIsTransparency = alpha;
            ti.mipMapsPreserveCoverage = alpha;
            ti.alphaTestReferenceValue = 0.5f;
            ti.wrapMode = clamp ? TextureWrapMode.Clamp : TextureWrapMode.Repeat;
            // Forest HLOD edge walls tile along the edge (u) but not vertically: with v repeating, the filter / mips at the
            // wall top (v = 1) fetched the opaque bottom rows (trunks, floor) and drew dotted arcs along every wall top in
            // the sky (review r4 / v3.3 README "kropkowane łuki"; ADR 0023).
            if (file.StartsWith("forest_edge")) { ti.wrapModeU = TextureWrapMode.Repeat; ti.wrapModeV = TextureWrapMode.Clamp; }
            ti.filterMode = FilterMode.Trilinear;
            ti.anisoLevel = text ? 4 : 2;
            ti.maxTextureSize = 2048;
            // explicit: NPOT impostor atlases (1536 x 384) with npotScale None are stored uncompressed (3 MB each; ADR 0025)
            ti.npotScale = TextureImporterNPOTScale.ToNearest;
            ti.textureCompression = TextureImporterCompression.Compressed;
            ti.SetPlatformTextureSettings(new TextureImporterPlatformSettings
            {
                // impostor atlases are 6 views x 256 px wide (1536): keep them whole on the phone (ADR 0023)
                name = "Android", overridden = true, maxTextureSize = file.StartsWith("impostor_") && !linear ? 2048 : 1024,
                format = text ? TextureImporterFormat.ASTC_4x4 : TextureImporterFormat.ASTC_6x6,
                compressionQuality = 50,
            });
            ti.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Texture2D>(dst);
        }
    }
}
