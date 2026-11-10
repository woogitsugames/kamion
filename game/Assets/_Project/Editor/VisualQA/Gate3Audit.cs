using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using Game.Rendering;
using Game.World;
using Unity.Collections;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using Game.Editor.Build;

namespace Game.Editor.VisualQA
{
    /// <summary>
    /// Gate 3 automatic checks data (docs/06 section 5 point 5), batchmode export. Writes ONE JSON with raw measurements; the
    /// verdicts (PASS/FAIL) are decided by scripts/gate3_evidence.py so thresholds live in one readable place.
    ///   Unity.exe -batchmode -quit -projectPath game -executeMethod Game.Editor.VisualQA.Gate3Audit.Run
    ///     -auditScene WorldC -auditOut file.json [-auditS "12-450,1232-1718"] [-auditCorridorM 30]
    /// Measures (all inside the route corridor: chunks and instances within -auditCorridorM of the route polyline, s ranges
    /// from -auditS, default the whole route): materials + base maps, texel density per material, texture import settings
    /// and Android memory estimate, mesh normals / UV0 / NaN, and height above / below the terrain + road collision for every
    /// scene renderer and every prop/tree instance. Editor only; this is not a phone measurement.
    /// </summary>
    public static class Gate3Audit
    {
        const float k_CellM = 8f;

        public static void Run()
        {
            int exit = 1;
            try
            {
                string scene = EditorTools.Arg("-auditScene", "WorldC");
                System.Threading.Thread.CurrentThread.CurrentCulture = System.Globalization.CultureInfo.InvariantCulture;
                string outFile = EditorTools.Arg("-auditOut", Path.Combine(EditorTools.RepoRoot, "artifacts", "gate3", "evidence", "audit_raw.json"));
                float corridor = float.Parse(EditorTools.Arg("-auditCorridorM", "30"), System.Globalization.CultureInfo.InvariantCulture);
                string sRanges = EditorTools.Arg("-auditS", null);
                Directory.CreateDirectory(Path.GetDirectoryName(outFile));
                var json = Audit(scene, outFile, corridor, sRanges);
                File.WriteAllText(outFile, json);
                Debug.Log("GATE3_AUDIT_RESULT: OK " + outFile);
                exit = 0;
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Debug.Log("GATE3_AUDIT_RESULT: FAILED");
            }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        // ------------------------------------------------------------------ data
        sealed class MatAcc
        {
            public Material mat; public string path, shader, baseMap; public Vector2 tiling = Vector2.one;
            public double areaM2, texelWeighted; public float minDensity = float.MaxValue, maxDensity;
            public int renderers, instances; public bool hasBaseMap; public int texW, texH;
        }
        sealed class Offender { public string kind, name, detail; public float dy; public Vector3 pos; }

        static string Audit(string sceneName, string outFile, float corridorM, string sRanges)
        {
            string scenePath = AssetDatabase.FindAssets("t:Scene " + sceneName).Select(AssetDatabase.GUIDToAssetPath)
                .FirstOrDefault(p => Path.GetFileNameWithoutExtension(p) == sceneName);
            if (scenePath == null) throw new FileNotFoundException("Scene not found: " + sceneName);
            EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
            // The scene saves the world MeshColliders disabled; the player cooks + enables them in Awake (WorldCollisionCooker).
            foreach (var ck in UnityEngine.Object.FindObjectsByType<WorldCollisionCooker>(FindObjectsInactive.Include, FindObjectsSortMode.None)) ck.Cook();
            Physics.SyncTransforms();

            var root = UnityEngine.Object.FindAnyObjectByType<WorldRegionRoot>();
            var route = UnityEngine.Object.FindAnyObjectByType<WorldRoute>();
            if (root == null || route == null) throw new InvalidOperationException("scene has no WorldRegionRoot/WorldRoute");
            var wp = route.WorldPoints();
            var dist = route.distances;
            var ranges = ParseRanges(sRanges);
            var cells = new HashSet<long>();
            int usedPts = 0;
            int rc = Mathf.CeilToInt(corridorM / k_CellM);
            for (int i = 0; i < wp.Length; i++)
            {
                float s = dist != null && i < dist.Length ? dist[i] : 0f;
                if (ranges.Count > 0 && !ranges.Any(r => s >= r.x && s <= r.y)) continue;
                usedPts++;
                int cx = Mathf.FloorToInt(wp[i].x / k_CellM), cz = Mathf.FloorToInt(wp[i].z / k_CellM);
                for (int dx = -rc; dx <= rc; dx++)
                    for (int dz = -rc; dz <= rc; dz++)
                        if (dx * dx + dz * dz <= rc * rc) cells.Add(Key(cx + dx, cz + dz));
            }
            bool InCorridor(Vector3 p) => cells.Contains(Key(Mathf.FloorToInt(p.x / k_CellM), Mathf.FloorToInt(p.z / k_CellM)));

            var mats = new Dictionary<Material, MatAcc>();
            var meshInfo = new Dictionary<Mesh, MeshStat>();
            var offenders = new List<Offender>();
            int objMerged = 0, objChecked = 0, objNoGround = 0, objFloating = 0, objSunk = 0;
            int instChecked = 0, instNoGround = 0, instFloating = 0, instSunk = 0, instCorridor = 0;
            var instByProto = new Dictionary<string, int>();

            MatAcc Acc(Material m)
            {
                if (m == null) return null;
                if (!mats.TryGetValue(m, out var a))
                {
                    a = new MatAcc { mat = m, path = AssetDatabase.GetAssetPath(m), shader = m.shader != null ? m.shader.name : "" };
                    Texture bm = null;
                    foreach (var prop in new[] { "_BaseMap", "_MainTex" })
                        if (m.HasProperty(prop)) { bm = m.GetTexture(prop); a.tiling = m.GetTextureScale(prop); if (bm != null) break; }
                    if (bm != null) { a.hasBaseMap = true; a.baseMap = AssetDatabase.GetAssetPath(bm); a.texW = bm.width; a.texH = bm.height; }
                    mats[m] = a;
                }
                return a;
            }

            // Ground = terrain + road surface + kerb colliders only (not buildings / steel), highest surface below the probe.
            var ground = new List<Collider>();
            foreach (var col in UnityEngine.Object.FindObjectsByType<Collider>(FindObjectsInactive.Exclude, FindObjectsSortMode.None))
            {
                string n = col.gameObject.name;
                // kerb tops / raised island tops are ground a pole stands on (C-9 posts on splitter islands, lamps behind a kerb)
                if (n == "col_terrain" || n == "col_asphalt" || n == "col_paving_stones" || n == "col_grass" || n == "col_concrete" || n == "col_concrete_kerb") ground.Add(col);
            }
            var groundSet = new HashSet<Collider>(ground);
            Physics.queriesHitBackfaces = true;   // the cooked collision meshes may be wound for the road normal; accept either side
            string probe = "";
            if (wp.Length > 0)
            {
                var ph = Physics.RaycastAll(new Vector3(wp[0].x, wp[0].y + 50f, wp[0].z), Vector3.down, 200f, ~0, QueryTriggerInteraction.Ignore);
                probe = $"route point 0 ({wp[0].x:F1},{wp[0].y:F1},{wp[0].z:F1}): {ph.Length} hits: " + string.Join(", ", ph.Take(6).Select(h => h.collider.gameObject.name + "@" + h.point.y.ToString("F2")));
                var sample = ground.Take(1).Select(c => c.GetType().Name + " " + c.bounds.center + " " + c.bounds.size + (c is MeshCollider mc ? " mesh=" + (mc.sharedMesh != null ? mc.sharedMesh.name : "null") : "")).FirstOrDefault();
                probe += " | first ground collider: " + sample;
            }
            Debug.Log("[AUDIT] ground probe " + probe);
            // What an object at (x, z) with its lowest point at `bottom` stands on: highest ground surface at or below bottom + 0.15 m
            // ("below", so a viaduct deck above a lamp is not mistaken for its ground) and the nearest surface 0.15..3 m above the
            // bottom ("above", i.e. the object is buried). Ray starts 3 m above the bottom, so overpasses with >= 4.5 m clearance never count.
            bool Probe(float x, float z, float bottom, out float below, out float above)
            {
                below = float.NegativeInfinity; above = float.PositiveInfinity;
                var hits = Physics.RaycastAll(new Vector3(x, bottom + 3f, z), Vector3.down, 120f, ~0, QueryTriggerInteraction.Ignore);
                foreach (var h in hits)
                {
                    if (!groundSet.Contains(h.collider)) continue;
                    float y = h.point.y;
                    if (y <= bottom + 0.15f) { if (y > below) below = y; }
                    else if (y < above) above = y;
                }
                return !float.IsNegativeInfinity(below) || !float.IsPositiveInfinity(above);
            }
            var protoRows = new Dictionary<string, ProtoRow>();

            // ---- scene renderers in the corridor
            int rendererCount = 0, rendererAll = 0;
            foreach (var r in UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsInactive.Exclude, FindObjectsSortMode.None))
            {
                rendererAll++;
                if (!(r is MeshRenderer) && !(r is SkinnedMeshRenderer)) continue;
                var b = r.bounds;
                if (!InCorridor(b.center) && !InCorridor(new Vector3(b.min.x, 0, b.min.z)) && !InCorridor(new Vector3(b.max.x, 0, b.max.z))) continue;
                string path = HierarchyName(r.transform);
                bool isVehicle = path.IndexOf("tractor", StringComparison.OrdinalIgnoreCase) >= 0 || path.IndexOf("trailer", StringComparison.OrdinalIgnoreCase) >= 0 || path.IndexOf("truck", StringComparison.OrdinalIgnoreCase) >= 0 || path.StartsWith("QA_") || path.Contains("/QA_");
                if (isVehicle) continue;
                rendererCount++;
                var mf = r.GetComponent<MeshFilter>();
                var mesh = mf != null ? mf.sharedMesh : null;
                var sm = r.sharedMaterials;
                if (mesh != null)
                {
                    var st = Stat(meshInfo, mesh);
                    Vector3 sc = r.transform.lossyScale; float area2 = Mathf.Abs(sc.x * sc.z) * 0.5f + Mathf.Abs(sc.x * sc.y) * 0.25f + Mathf.Abs(sc.y * sc.z) * 0.25f;
                    float lin = Mathf.Sqrt(Mathf.Max(1e-8f, area2));
                    for (int si = 0; si < mesh.subMeshCount && si < sm.Length; si++)
                        AccTexel(Acc(sm[si]), st, si, lin, 1);
                }
                else foreach (var m in sm) { var a = Acc(m); if (a != null) a.renderers++; }

                // floating / sunk (terrain, collision-backed chunks only)
                string nameLc = r.gameObject.name;
                bool surface = nameLc.StartsWith("terrain") || nameLc == "road" || nameLc == "markings" || nameLc == "paved" || nameLc.StartsWith("col_") || nameLc == "wires";
                if (surface) continue;
                if (Mathf.Max(b.size.x, b.size.z) > 60f) { objMerged++; continue; }   // chunk-wide merged mesh: 5 probes say nothing about its buildings
                objChecked++;
                float bottom = b.min.y, minFloat = float.PositiveInfinity; int got = 0, buried = 0;
                foreach (var q in new[] { b.center, new Vector3(b.min.x, 0, b.min.z), new Vector3(b.max.x, 0, b.min.z), new Vector3(b.min.x, 0, b.max.z), new Vector3(b.max.x, 0, b.max.z) })
                {
                    if (!Probe(q.x, q.z, bottom, out float below, out float above)) continue;
                    got++;
                    if (!float.IsNegativeInfinity(below)) minFloat = Mathf.Min(minFloat, bottom - below);
                    if (float.IsNegativeInfinity(below) && above <= b.max.y + 1f && above - bottom > 0.6f) buried++;
                }
                if (got == 0) { objNoGround++; continue; }
                if (minFloat > 0.30f && minFloat < 1000f) { objFloating++; offenders.Add(new Offender { kind = "renderer_floating", name = path, dy = minFloat, pos = b.center, detail = $"bounds.min.y {bottom:F2}: lowest probe is {minFloat:F2} m above the surface below it" }); }
                else if (buried == got) { objSunk++; offenders.Add(new Offender { kind = "renderer_sunk", name = path, dy = -(b.max.y - bottom), pos = b.center, detail = "every probe point has ground above the bottom and nothing below it" }); }
            }

            // ---- instances (props, trees) in the corridor
            var setAsset = AssetDatabase.FindAssets("t:WorldInstanceSet", new[] { Path.GetDirectoryName(scenePath).Replace('\\', '/') })
                .Select(AssetDatabase.GUIDToAssetPath).Select(AssetDatabase.LoadAssetAtPath<WorldInstanceSet>).FirstOrDefault();
            if (setAsset != null)
            {
                var l2w = root.transform.localToWorldMatrix;
                foreach (var run in setAsset.runs)
                {
                    var proto = setAsset.prototypes[run.prototype];
                    int corridorCount = 0;
                    var rng = new System.Random(run.prototype * 7919 + 1);
                    float firstScale = 1f; bool haveScale = false;
                    for (int k = 0; k < run.count; k++)
                    {
                        var m = l2w * setAsset.LocalMatrix(run.start + k);   // compact TRS or full matrices (ADR 0025)
                        Vector3 p = m.GetColumn(3);
                        if (!InCorridor(p)) continue;
                        corridorCount++; instCorridor++;
                        if (!haveScale) { firstScale = m.lossyScale.x; haveScale = true; }
                        if (run.forest || rng.NextDouble() < 0.25 || corridorCount < 50) // probe a sample of the big runs (trees), all of the props
                        {
                            instChecked++;
                            float bottom = BottomY(proto.lods.Length > 0 ? proto.lods[0] : null, m, p.y);
                            if (!Probe(p.x, p.z, bottom, out float below, out float above)) { instNoGround++; continue; }
                            if (!protoRows.TryGetValue(proto.name, out var row)) protoRows[proto.name] = row = new ProtoRow { name = proto.name };
                            row.n++;
                            if (!float.IsNegativeInfinity(below))
                            {
                                float dy = bottom - below; row.sumDy += dy; row.maxDy = Mathf.Max(row.maxDy, dy);
                                if (dy > 0.30f) { row.floating++; instFloating++; offenders.Add(new Offender { kind = "instance_floating", name = proto.name, dy = dy, pos = p, detail = "lowest point above the surface below" }); }
                            }
                            else if (above - bottom > 0.6f) { row.sunk++; row.maxSunkDepth = Mathf.Max(row.maxSunkDepth, above - bottom); instSunk++; offenders.Add(new Offender { kind = "instance_sunk", name = proto.name, dy = -(above - bottom), pos = p, detail = "lowest point below the surface above, nothing under it" }); }
                        }
                    }
                    if (corridorCount == 0) continue;
                    instByProto.TryGetValue(proto.name, out int cur); instByProto[proto.name] = cur + corridorCount;
                    // meshes of lod0 (stats + texel density), materials by materialStart
                    for (int li = 0; li < proto.lods.Length; li++)
                    {
                        var mesh = proto.lods[li]; if (mesh == null) continue;
                        var st = Stat(meshInfo, mesh);
                        int ms = proto.materialStart != null && li < proto.materialStart.Length ? proto.materialStart[li] : 0;
                        for (int si = 0; si < mesh.subMeshCount; si++)
                        {
                            int mi = ms + si; if (mi < 0 || mi >= setAsset.materials.Length) continue;
                            AccTexel(Acc(setAsset.materials[mi]), st, si, Mathf.Max(0.001f, firstScale), li == 0 ? corridorCount : 0);
                        }
                    }
                }
                foreach (var h in setAsset.hlods) if (h != null && h.mesh != null) Stat(meshInfo, h.mesh);
            }

            // ---- textures (unique base/normal/mask maps of corridor materials) + import settings
            var texSet = new Dictionary<string, TexStat>();
            foreach (var a in mats.Values)
            {
                var m = a.mat;
                foreach (var pname in m.GetTexturePropertyNames())
                {
                    var t = m.GetTexture(pname); if (t == null) continue;
                    string tp = AssetDatabase.GetAssetPath(t);
                    if (string.IsNullOrEmpty(tp) || texSet.ContainsKey(tp)) continue;
                    var ts = new TexStat { path = tp, prop = pname, w = t.width, h = t.height };
                    if (AssetImporter.GetAtPath(tp) is TextureImporter ti)
                    {
                        var ps = ti.GetPlatformTextureSettings("Android");
                        ts.override_android = ps.overridden; ts.maxSize = ps.overridden ? ps.maxTextureSize : ti.maxTextureSize;
                        ts.format = ps.overridden ? ps.format.ToString() : "Automatic(" + ti.GetAutomaticFormat("Android") + ")";
                        string fmt = ps.overridden ? ps.format.ToString() : ti.GetAutomaticFormat("Android").ToString();
                        ts.mips = ti.mipmapEnabled; ts.srgb = ti.sRGBTexture; ts.readable = ti.isReadable;
                        int ew = Mathf.Min(t.width, ts.maxSize), eh = Mathf.Min(t.height, ts.maxSize);
                        ts.effW = ew; ts.effH = eh;
                        ts.bytes = (long)(ew * (double)eh * Bpp(fmt) / 8.0 * (ti.mipmapEnabled ? 4.0 / 3.0 : 1.0));
                    }
                    else { ts.bytes = Profiler_Size(t); ts.effW = t.width; ts.effH = t.height; ts.format = t.graphicsFormat.ToString(); }
                    texSet[tp] = ts;
                }
            }

            // ---- quality profile budgets
            var prof = QualityProfile.Load();
            var tiers = new List<string>();
            if (prof != null)
                foreach (var t in prof.tiers)
                    tiers.Add($"{{\"name\":{J(t.name)},\"budgetTextureMB\":{t.budgetTextureMB},\"budgetDrawCalls\":{t.budgetDrawCalls},\"budgetTrianglesK\":{t.budgetTrianglesK}}}");

            // ---- JSON
            var sb = new StringBuilder(1 << 20);
            sb.Append("{\n");
            sb.Append($"\"schema\":\"truck-sim-pl/gate3-audit-raw/1\",\"scene\":{J(sceneName)},\"unity\":{J(Application.unityVersion)},\"corridor_m\":{F(corridorM)},\"s_ranges\":{J(sRanges ?? "all")},\"route_points_used\":{usedPts},\n");
            sb.Append($"\"counts\":{{\"renderers_in_scene\":{rendererAll},\"renderers_in_corridor\":{rendererCount},\"instances_in_corridor\":{instCorridor},\"materials\":{mats.Count},\"textures\":{texSet.Count},\"meshes\":{meshInfo.Count}}},\n");
            sb.Append("\"tiers\":[" + string.Join(",", tiers) + "],\n");
            sb.Append("\"materials\":[\n");
            sb.Append(string.Join(",\n", mats.Values.OrderBy(a => a.mat.name).Select(a =>
            {
                Color c = a.mat.HasProperty("_BaseColor") ? a.mat.GetColor("_BaseColor") : a.mat.HasProperty("_Color") ? a.mat.GetColor("_Color") : Color.white;
                Color sc2 = c; // material colours are stored as authored (sRGB-encoded); the shader linearises them
                double dens = a.areaM2 > 0 ? a.texelWeighted / a.areaM2 : 0;
                return $"{{\"name\":{J(a.mat.name)},\"path\":{J(a.path)},\"shader\":{J(a.shader)},\"base_map\":{J(a.baseMap ?? "")},\"base_color_srgb\":[{F(sc2.r * 255)},{F(sc2.g * 255)},{F(sc2.b * 255)}],\"tiling\":[{F(a.tiling.x)},{F(a.tiling.y)}],\"area_m2\":{F(a.areaM2)},\"texel_per_m_mean\":{F(dens)},\"texel_per_m_min\":{F(a.minDensity == float.MaxValue ? 0 : a.minDensity)},\"texel_per_m_max\":{F(a.maxDensity)},\"tex_w\":{a.texW},\"tex_h\":{a.texH},\"renderers\":{a.renderers}}}";
            })));
            sb.Append("\n],\n\"textures\":[\n");
            sb.Append(string.Join(",\n", texSet.Values.OrderBy(t => t.path).Select(t =>
                $"{{\"path\":{J(t.path)},\"prop\":{J(t.prop)},\"w\":{t.w},\"h\":{t.h},\"max_size\":{t.maxSize},\"eff_w\":{t.effW},\"eff_h\":{t.effH},\"format\":{J(t.format ?? "")},\"override_android\":{(t.override_android ? "true" : "false")},\"mips\":{(t.mips ? "true" : "false")},\"srgb\":{(t.srgb ? "true" : "false")},\"readable\":{(t.readable ? "true" : "false")},\"est_android_bytes\":{t.bytes}}}")));
            sb.Append("\n],\n\"meshes\":[\n");
            sb.Append(string.Join(",\n", meshInfo.Select(kv => kv.Value).Where(s => s.problem).Select(s =>
                $"{{\"name\":{J(s.name)},\"path\":{J(s.path)},\"vertices\":{s.verts},\"submeshes\":{s.subs},\"has_normals\":{(s.normals ? "true" : "false")},\"has_uv0\":{(s.uv0 ? "true" : "false")},\"nan_vertices\":{s.nan},\"textured_without_uv0\":{(s.texturedNoUv ? "true" : "false")},\"degenerate_tris\":{s.degenerate}}}")));
            sb.Append($"\n],\n\"mesh_summary\":{{\"checked\":{meshInfo.Count},\"missing_normals\":{meshInfo.Values.Count(s => !s.normals)},\"missing_uv0\":{meshInfo.Values.Count(s => !s.uv0)},\"nan\":{meshInfo.Values.Count(s => s.nan > 0)},\"unreadable_by_api\":{meshInfo.Values.Count(s => s.apiFailed)}}},\n");
            sb.Append($"\"ground_check\":{{\"probe\":{J(probe)},\"ground_colliders\":{ground.Count},\"renderers_checked\":{objChecked},\"renderers_merged_skipped\":{objMerged},\"renderers_no_ground\":{objNoGround},\"renderers_floating\":{objFloating},\"renderers_sunk\":{objSunk},\"instances_probed\":{instChecked},\"instances_no_ground\":{instNoGround},\"instances_floating\":{instFloating},\"instances_sunk\":{instSunk},\"tolerance\":{{\"float_m\":0.30,\"sunk_m\":0.60,\"note\":\"WORKING_VALUE; ground = terrain+road surface colliders; floating = lowest point above the surface below it (renderers: all 5 probes); sunk = ground above the lowest point and nothing below\"}}}},\n");
            sb.Append("\"offenders\":[\n" + string.Join(",\n", offenders.GroupBy(o => o.name).SelectMany(g => g.OrderByDescending(o => Mathf.Abs(o.dy)).Take(6)).OrderByDescending(o => Mathf.Abs(o.dy)).Take(150).Select(o =>
                $"{{\"kind\":{J(o.kind)},\"name\":{J(o.name)},\"dy_m\":{F(o.dy)},\"pos\":[{F(o.pos.x)},{F(o.pos.y)},{F(o.pos.z)}],\"detail\":{J(o.detail)}}}")) + "\n],\n");
            sb.Append("\"prototype_ground\":[" + string.Join(",", protoRows.Values.OrderByDescending(r => r.floating + r.sunk).Select(r => $"{{\"name\":{J(r.name)},\"probed\":{r.n},\"floating\":{r.floating},\"sunk\":{r.sunk},\"mean_bottom_above_ground_m\":{F(r.n > 0 ? r.sumDy / r.n : 0)},\"max_bottom_above_ground_m\":{F(r.maxDy)},\"max_sunk_depth_m\":{F(r.maxSunkDepth)}}}")) + "],\n");
            sb.Append("\"instances_by_prototype\":{" + string.Join(",", instByProto.OrderByDescending(kv => kv.Value).Select(kv => $"{J(kv.Key)}:{kv.Value}")) + "}\n}\n");
            return sb.ToString();
        }

        // ------------------------------------------------------------------ mesh stats
        sealed class MeshStat
        {
            public string name, path; public int verts, subs, nan, degenerate; public bool normals, uv0, problem, apiFailed, texturedNoUv;
            public float[] worldArea, uvArea; // per submesh, unit scale
        }
        sealed class TexStat { public string path, prop, format; public int w, h, maxSize, effW, effH; public bool override_android, mips, srgb, readable; public long bytes; }

        static MeshStat Stat(Dictionary<Mesh, MeshStat> cache, Mesh mesh)
        {
            if (cache.TryGetValue(mesh, out var s)) return s;
            s = new MeshStat { name = mesh.name, path = AssetDatabase.GetAssetPath(mesh), verts = mesh.vertexCount, subs = mesh.subMeshCount };
            s.normals = mesh.HasVertexAttribute(VertexAttribute.Normal);
            s.uv0 = mesh.HasVertexAttribute(VertexAttribute.TexCoord0);
            s.worldArea = new float[mesh.subMeshCount]; s.uvArea = new float[mesh.subMeshCount];
            try
            {
                using (var data = Mesh.AcquireReadOnlyMeshData(mesh))
                {
                    var d = data[0];
                    var v = new NativeArray<Vector3>(d.vertexCount, Allocator.Temp);
                    d.GetVertices(v);
                    var uv = new NativeArray<Vector2>(d.vertexCount, Allocator.Temp);
                    if (s.uv0) d.GetUVs(0, uv);
                    for (int i = 0; i < v.Length; i++) if (float.IsNaN(v[i].x) || float.IsNaN(v[i].y) || float.IsNaN(v[i].z) || float.IsInfinity(v[i].x)) s.nan++;
                    for (int si = 0; si < d.subMeshCount; si++)
                    {
                        var idx = new NativeArray<int>((int)d.GetSubMesh(si).indexCount, Allocator.Temp);
                        d.GetIndices(idx, si);
                        double wa = 0, ua = 0;
                        for (int t = 0; t + 2 < idx.Length; t += 3)
                        {
                            Vector3 a = v[idx[t]], b = v[idx[t + 1]], c = v[idx[t + 2]];
                            float ar = Vector3.Cross(b - a, c - a).magnitude * 0.5f;
                            if (ar < 1e-9f) { s.degenerate++; continue; }
                            wa += ar;
                            if (s.uv0)
                            {
                                Vector2 ua0 = uv[idx[t]], ub = uv[idx[t + 1]], uc = uv[idx[t + 2]];
                                ua += Mathf.Abs((ub.x - ua0.x) * (uc.y - ua0.y) - (uc.x - ua0.x) * (ub.y - ua0.y)) * 0.5f;
                            }
                        }
                        s.worldArea[si] = (float)wa; s.uvArea[si] = (float)ua;
                        idx.Dispose();
                    }
                    v.Dispose(); uv.Dispose();
                }
            }
            catch (Exception e) { s.apiFailed = true; Debug.LogWarning("[AUDIT] mesh data failed for " + mesh.name + ": " + e.Message); }
            s.problem = !s.normals || !s.uv0 || s.nan > 0 || s.apiFailed;
            cache[mesh] = s;
            return s;
        }

        // texels per metre of one submesh: sqrt(uvArea * W * H * tiling / worldArea * scale^-2); weighted by world area * count
        static void AccTexel(MatAcc a, MeshStat st, int si, float linScale, int count)
        {
            if (a == null) return;
            a.renderers += count == 0 ? 0 : 1; a.instances += count;
            // World Surface always, and World PBR unless _UV_MESH0/_UV_MESH1 is on, project planar in world space (no UV0 read)
            bool worldPlanar = a.shader == "Kamion/World Surface" || (a.shader == "Kamion/World PBR" && !a.mat.IsKeywordEnabled("_UV_MESH0") && !a.mat.IsKeywordEnabled("_UV_MESH1"));
            if (a.hasBaseMap && !st.uv0 && !worldPlanar) st.texturedNoUv = true;
            if (!a.hasBaseMap || st.worldArea == null || si >= st.worldArea.Length) return;
            float wa = st.worldArea[si] * linScale * linScale, ua = st.uvArea[si] * Mathf.Abs(a.tiling.x * a.tiling.y);
            if (wa < 1e-4f || ua < 1e-9f) return;
            float dens = Mathf.Sqrt(ua * a.texW * a.texH / wa);
            double weight = wa * Math.Max(1, count);
            a.areaM2 += weight; a.texelWeighted += dens * weight;
            a.minDensity = Mathf.Min(a.minDensity, dens); a.maxDensity = Mathf.Max(a.maxDensity, dens);
        }

        sealed class ProtoRow { public string name; public int n, floating, sunk; public double sumDy; public float maxDy, maxSunkDepth; }

        static float BottomY(Mesh mesh, Matrix4x4 m, float fallback)
        {
            if (mesh == null) return fallback;
            var bb = mesh.bounds; float lo = float.MaxValue;
            for (int i = 0; i < 8; i++)
            {
                var c = bb.center + new Vector3(((i & 1) == 0 ? -1 : 1) * bb.extents.x, ((i & 2) == 0 ? -1 : 1) * bb.extents.y, ((i & 4) == 0 ? -1 : 1) * bb.extents.z);
                lo = Mathf.Min(lo, m.MultiplyPoint3x4(c).y);
            }
            return lo;
        }

        // ------------------------------------------------------------------ helpers
        static double Bpp(string f)
        {
            // Names are shared by TextureFormat and TextureImporterFormat. ASTC NxN = 128 bit per block.
            var m = System.Text.RegularExpressions.Regex.Match(f, @"ASTC_(?:HDR_)?(\d+)x(\d+)");
            if (m.Success) return 128.0 / (int.Parse(m.Groups[1].Value) * int.Parse(m.Groups[2].Value));
            switch (f)
            {
                case "ETC2_RGBA8": case "ETC2_RGBA8Crunched": case "DXT5": case "DXT5Crunched": case "BC7": return 8;
                case "ETC2_RGB": case "ETC2_RGBA1": case "DXT1": case "DXT1Crunched": case "ETC_RGB4": case "ETC_RGB4Crunched": case "BC4": return 4;
                case "RGB24": return 24; case "R8": case "Alpha8": case "BC5": return 8;
                case "RGBAHalf": return 64;
                default: return 32;   // RGBA32 / ARGB32 / BGRA32 / unknown: worst case
            }
        }
        static long Profiler_Size(Texture t) => UnityEngine.Profiling.Profiler.GetRuntimeMemorySizeLong(t);

        static long Key(int x, int z) => ((long)x << 32) ^ (uint)z;
        static List<Vector2> ParseRanges(string s)
        {
            var l = new List<Vector2>();
            if (string.IsNullOrEmpty(s)) return l;
            foreach (var part in s.Split(','))
            {
                var ab = part.Split('-'); if (ab.Length != 2) continue;
                l.Add(new Vector2(float.Parse(ab[0], System.Globalization.CultureInfo.InvariantCulture), float.Parse(ab[1], System.Globalization.CultureInfo.InvariantCulture)));
            }
            return l;
        }
        static string HierarchyName(Transform t)
        {
            var sb = new StringBuilder(t.name);
            for (var p = t.parent; p != null; p = p.parent) sb.Insert(0, p.name + "/");
            return sb.ToString();
        }
        static string F(double v) => double.IsNaN(v) || double.IsInfinity(v) ? "0" : v.ToString("0.###", System.Globalization.CultureInfo.InvariantCulture);
        static string J(string s)
        {
            if (s == null) return "\"\"";
            var sb = new StringBuilder("\"");
            foreach (char c in s)
            {
                if (c == '"' || c == '\\') sb.Append('\\').Append(c);
                else if (c < 32) sb.Append(' ');
                else sb.Append(c);
            }
            return sb.Append('"').ToString();
        }
    }
}
