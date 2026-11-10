using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Game.Editor.Build;
using Game.Rendering.Editor;
using static Game.Rendering.Editor.GroundSkyBakeMath;
using Game.Rendering;
using Unity.Collections;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Debug = UnityEngine.Debug;

namespace Game.World.Import
{
    /// <summary>
    /// ADR 0064 - bakes the ground lighting map of an imported region (<see cref="WorldSkyVisibility"/>):
    /// 1. rasterises the High content scene (chunk meshes + instanced vehicles / trees) into region-root XZ grids at 1 m:
    ///    ground height (lowest walkable surface: terrain, road, paved; near-vertical skirts skipped), solid top height
    ///    (buildings, bridges, walls, containers, parked vehicles) and porous crowns (trees, hedges: bottom / top);
    /// 2. R = cosine-weighted sky visibility at ground level: 16 azimuths, horizon marched to 120 m,
    ///    vis = mean cos²(horizon); crowns let <see cref="GroundSkyBakeMath.CrownSkyTransmittance"/> of the sky they cover through;
    /// 3. G, B = ground sun visibility for the sun of LP_LowSun and LP_Clear (ray march to 300 m, crowns attenuate
    ///    exp(-<see cref="GroundSkyBakeMath.CrownSunExtinction"/> · path)), 3x3 box (penumbra);
    /// 4. A = ground height, 8 bit (base + A · step).
    /// Output (gitignored, next to the scenes): WorldGI_1m.asset (WorldC_High), WorldGI_2m.asset (WorldC: Low + Medium,
    /// 2x2 average), both RGBA32 linear with mips; a <see cref="WorldSkyVisibility"/> on the region root of each scene.
    /// Evidence: artifacts/bake-r8/maps/&lt;region&gt;_{vis,sun_lowsun,sun_clear,height}.png + bake.json.
    /// Batch: -executeMethod Game.World.Import.WorldSkyBake.BakeBatch -region &lt;id&gt; (also run by ImportBatch).
    /// </summary>
    public static class WorldSkyBake
    {
        public const float TexelM = 1f;

        static readonly string[] k_SunPresets = { "LP_LowSun", "LP_Clear" };

        public static void BakeBatch()
        {
            int exit = 1;
            try
            {
                string region = EditorTools.Arg("-region", "bialystok-industrial-c");
                Bake(region);
                exit = 0;
                Debug.Log("SKYBAKE_RESULT: OK region=" + region);
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Debug.Log("SKYBAKE_RESULT: FAILED");
            }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        [MenuItem("Kamion/World/Bake ground sky visibility (ADR 0064)")]
        static void Menu() => Bake("bialystok-industrial-c");


        public static void Bake(string region)
        {
            var sw = Stopwatch.StartNew();
            string dir = $"{RegionImporter.GeneratedRoot}/{region}";
            string highScene = $"{dir}/{WorldSceneBuilder.SceneNameFor(region, "High")}.unity";
            string lowScene = $"{dir}/{WorldSceneBuilder.SceneNameFor(region, "Low")}.unity";
            string src = File.Exists(highScene) ? highScene : lowScene;
            if (!File.Exists(src)) throw new FileNotFoundException("no world scene to bake from: " + src);

            EditorSceneManager.OpenScene(src, OpenSceneMode.Single);
            var root = UnityEngine.Object.FindFirstObjectByType<WorldRegionRoot>();
            if (root == null) throw new InvalidOperationException("WorldRegionRoot missing in " + src);
            Vector2 mn = new Vector2(float.MaxValue, float.MaxValue), mx = new Vector2(float.MinValue, float.MinValue);
            foreach (var c in root.chunks) { mn = Vector2.Min(mn, c.minEN); mx = Vector2.Max(mx, c.maxEN); }
            int w = Mathf.CeilToInt((mx.x - mn.x) / TexelM), h = Mathf.CeilToInt((mx.y - mn.y) / TexelM);
            if (w % 2 == 1) w++;
            if (h % 2 == 1) h++;
            var g = new BakeGrid(mn.x, mn.y, w, h, TexelM);
            var stats = new StringBuilder();
            var kinds = new Dictionary<string, Kind>();

            // ---- rasterise chunk meshes (region-root space)
            Matrix4x4 toRoot = root.transform.worldToLocalMatrix;
            long tris = 0;
            foreach (Transform chunk in root.transform)
            {
                if (!chunk.name.StartsWith("Chunk_", StringComparison.Ordinal)) continue;
                var nodes = new Dictionary<string, MeshRenderer>();
                foreach (Transform t in chunk)
                    if (t.TryGetComponent(out MeshRenderer mr) && t.TryGetComponent(out MeshFilter mf) && mf.sharedMesh != null) nodes[t.name] = mr;
                string terrain = new[] { "terrain_band", "terrain", "terrain_lod1", "terrain_lod2", "terrain_lod3" }.FirstOrDefault(nodes.ContainsKey);
                string buildings = nodes.ContainsKey("buildings") ? "buildings" : "buildings_lod1";
                foreach (var kv in nodes)
                {
                    string n = kv.Key;
                    Kind nodeKind;
                    if (n == "road") nodeKind = Kind.Road;
                    else if (n == terrain || n == "paved") nodeKind = Kind.Ground;
                    else if (n == buildings || n == "bridge" || n == "furniture") nodeKind = Kind.Solid;
                    else continue;   // other terrain LODs, LOD1 when LOD0 exists, markings, wires
                    var mesh = kv.Value.GetComponent<MeshFilter>().sharedMesh;
                    var mats = kv.Value.sharedMaterials;
                    Matrix4x4 m = toRoot * kv.Value.transform.localToWorldMatrix;
                    using (var arr = Mesh.AcquireReadOnlyMeshData(mesh))
                    {
                        var md = arr[0];
                        var verts = new NativeArray<Vector3>(md.vertexCount, Allocator.TempJob);
                        md.GetVertices(verts);
                        var p = new Vector3[verts.Length];
                        for (int i = 0; i < p.Length; i++) p[i] = m.MultiplyPoint3x4(verts[i]);
                        verts.Dispose();
                        for (int s = 0; s < md.subMeshCount; s++)
                        {
                            Kind k = nodeKind;
                            if (nodeKind == Kind.Solid)
                            {
                                string mat = s < mats.Length && mats[s] != null ? mats[s].name : "";
                                k = Classify(mat);
                                kinds[mat] = k;
                            }
                            if (k == Kind.Skip) continue;
                            var idx = new NativeArray<int>(md.GetSubMesh(s).indexCount, Allocator.TempJob);
                            md.GetIndices(idx, s);
                            for (int i = 0; i + 2 < idx.Length; i += 3)
                                Splat(g, p[idx[i]], p[idx[i + 1]], p[idx[i + 2]], k);
                            tris += idx.Length / 3;
                            idx.Dispose();
                        }
                    }
                }
            }

            // ---- instances: parked vehicles, trailers, bins, shelters solid; trees crowns
            int instSolid = 0, instCrown = 0;
            var wi = root.GetComponent<WorldInstances>();
            var set = wi != null ? wi.set : null;
            if (set != null)
            {
                var meshPts = new Dictionary<Mesh, (Vector3[] v, int[] i)>();
                foreach (var run in set.runs)
                {
                    var proto = set.prototypes[run.prototype];
                    if (proto.lods == null || proto.lods.Length == 0 || proto.lods[0] == null) continue;
                    string n = proto.name;
                    bool crown = n.StartsWith("tree_", StringComparison.Ordinal);
                    // Parked vehicles are not occluders: ADR 0050 contact patches already darken under them (no double AO).
                    bool solid = n.StartsWith("bus_shelter") || n.StartsWith("bin_1100");
                    if (!crown && !solid) continue;
                    var lodMesh = crown ? proto.lods[0] : proto.lods[proto.lods.Length - 1];
                    if (lodMesh == null) lodMesh = proto.lods[0];
                    Bounds b = proto.lods[0].bounds;
                    (Vector3[] v, int[] i) data = default;
                    if (solid && !meshPts.TryGetValue(lodMesh, out data))
                    {
                        using (var arr = Mesh.AcquireReadOnlyMeshData(lodMesh))
                        {
                            var md = arr[0];
                            var verts = new NativeArray<Vector3>(md.vertexCount, Allocator.TempJob);
                            md.GetVertices(verts);
                            var all = new List<int>();
                            for (int s = 0; s < md.subMeshCount; s++)
                            {
                                var idx = new NativeArray<int>(md.GetSubMesh(s).indexCount, Allocator.TempJob);
                                md.GetIndices(idx, s);
                                all.AddRange(idx);
                                idx.Dispose();
                            }
                            data = (verts.ToArray(), all.ToArray());
                            verts.Dispose();
                        }
                        meshPts[lodMesh] = data;
                    }
                    for (int k = run.start; k < run.start + run.count; k++)
                    {
                        Matrix4x4 m = set.LocalMatrix(k);
                        if (crown)
                        {
                            // crown = ellipse of the LOD0 bounds; trees from 35 % of their height, shrubs from the ground
                            Vector3 c = m.MultiplyPoint3x4(b.center);
                            Vector3 ex = m.MultiplyVector(new Vector3(b.extents.x, 0, 0)), ez = m.MultiplyVector(new Vector3(0, 0, b.extents.z));
                            float r = Mathf.Max(new Vector2(ex.x, ex.z).magnitude, new Vector2(ez.x, ez.z).magnitude) * 0.85f;
                            float y0 = m.MultiplyPoint3x4(b.min).y, y1 = m.MultiplyPoint3x4(b.max).y;
                            float bot = n.StartsWith("tree_shrub") ? y0 : y0 + 0.35f * (y1 - y0);
                            Disc(g, c.x, c.z, r, bot, y1);
                            instCrown++;
                        }
                        else
                        {
                            var pts = new Vector3[data.v.Length];
                            for (int q = 0; q < pts.Length; q++) pts[q] = m.MultiplyPoint3x4(data.v[q]);
                            for (int q = 0; q + 2 < data.i.Length; q += 3) Splat(g, pts[data.i[q]], pts[data.i[q + 1]], pts[data.i[q + 2]], Kind.Solid);
                            instSolid++;
                        }
                    }
                }
            }
            double tRaster = sw.Elapsed.TotalSeconds;

            // ---- fill ground holes (no walkable surface rasterised) from the neighbours; top >= ground
            FillHoles(g);
            for (int i = 0; i < g.Ground.Length; i++) g.Top[i] = Mathf.Max(g.Top[i], g.Ground[i]);

            // ---- sky visibility and sun visibility at ground level
            var vis = SkyVisibility(g);
            float visRoad = NormaliseToRoads(g, vis);
            double tVis = sw.Elapsed.TotalSeconds;
            var presets = LookDevAssets.Presets();
            var sunDirs = new Vector3[2];
            var sun = new float[2][];
            for (int c = 0; c < 2; c++)
            {
                var pr = presets.FirstOrDefault(x => x != null && x.name == k_SunPresets[c]);
                if (pr == null) { sun[c] = Enumerable.Repeat(1f, w * h).ToArray(); continue; }
                float el = Mathf.Clamp(pr.sunElevationDeg, 0.5f, 89.5f) * Mathf.Deg2Rad, az = pr.sunAzimuthDeg * Mathf.Deg2Rad;
                var dWorld = new Vector3(Mathf.Cos(el) * Mathf.Sin(az), Mathf.Sin(el), Mathf.Cos(el) * Mathf.Cos(az)).normalized;
                sunDirs[c] = root.transform.InverseTransformDirection(dWorld).normalized;
                sun[c] = Box3(g, SunVisibility(g, sunDirs[c]));
            }
            double tSun = sw.Elapsed.TotalSeconds;

            // ---- pack
            float gMin = float.MaxValue, gMax = float.MinValue;
            foreach (float y in g.Ground) { gMin = Mathf.Min(gMin, y); gMax = Mathf.Max(gMax, y); }
            float hBase = Mathf.Floor(gMin) - 1f;
            float hStep = Mathf.Max(0.1f, Mathf.Ceil((gMax - hBase + 1f) / 255f * 100f) / 100f);
            var px = new Color32[w * h];
            for (int i = 0; i < px.Length; i++)
                px[i] = new Color32(B(vis[i]), B(sun[0][i]), B(sun[1][i]), (byte)Mathf.Clamp(Mathf.RoundToInt((g.Ground[i] - hBase) / hStep), 0, 255));

            var tex1 = MakeTexture(px, w, h, "WorldGI_1m");
            var px2 = Downsample(px, w, h);
            var tex2 = MakeTexture(px2, w / 2, h / 2, "WorldGI_2m");
            string p1 = $"{dir}/WorldGI_1m.asset", p2 = $"{dir}/WorldGI_2m.asset";
            SaveTexture(tex1, p1);
            SaveTexture(tex2, p2);
            AssetDatabase.SaveAssets();
            tex1 = AssetDatabase.LoadAssetAtPath<Texture2D>(p1);
            tex2 = AssetDatabase.LoadAssetAtPath<Texture2D>(p2);

            // ---- evidence
            string evDir = Path.Combine(EditorTools.RepoRoot, "artifacts", "bake-r8", "maps");
            Directory.CreateDirectory(evDir);
            WritePng(Path.Combine(evDir, region + "_vis.png"), px, w, h, 0);
            WritePng(Path.Combine(evDir, region + "_sun_lowsun.png"), px, w, h, 1);
            WritePng(Path.Combine(evDir, region + "_sun_clear.png"), px, w, h, 2);
            WritePng(Path.Combine(evDir, region + "_height.png"), px, w, h, 3);
            double visMean = vis.Average();
            var ci = CultureInfo.InvariantCulture;
            string kindList = string.Join(", ", kinds.OrderBy(k => k.Key).Select(k => $"\"{k.Key}\": \"{k.Value}\""));
            File.WriteAllText(Path.Combine(evDir, region + "_bake.json"), string.Format(ci,
                "{{\n \"region\": \"{0}\", \"source\": \"{1}\", \"texel_m\": {2}, \"size\": [{3}, {4}],\n \"origin_local\": [{5}, {6}],\n" +
                " \"height_base\": {7}, \"height_step\": {8}, \"triangles\": {9}, \"instances_solid\": {10}, \"instances_crown\": {11},\n" +
                " \"seconds\": {{\"raster\": {12:F1}, \"sky\": {13:F1}, \"sun\": {14:F1}, \"total\": {15:F1}}},\n" +
                " \"vis_mean\": {16:F3}, \"vis_road_median_before_normalise\": {26:F3}, \"bytes_1m_with_mips\": {17}, \"bytes_2m_with_mips\": {18},\n" +
                " \"sun_dirs_local\": [[{19:F4}, {20:F4}, {21:F4}], [{22:F4}, {23:F4}, {24:F4}]],\n \"material_kinds\": {{{25}}}\n}}\n",
                region, src, TexelM, w, h, mn.x, mn.y, hBase, hStep, tris, instSolid, instCrown, tRaster, tVis - tRaster, tSun - tVis,
                sw.Elapsed.TotalSeconds, visMean, MipBytes(w, h), MipBytes(w / 2, h / 2),
                sunDirs[0].x, sunDirs[0].y, sunDirs[0].z, sunDirs[1].x, sunDirs[1].y, sunDirs[1].z, kindList, visRoad));

            // ---- attach to the scenes
            foreach (var (scene, tex, texel) in new[] { (highScene, tex1, TexelM), (lowScene, tex2, TexelM * 2f) })
            {
                if (!File.Exists(scene)) continue;
                var sc = EditorSceneManager.OpenScene(scene, OpenSceneMode.Single);
                var rr = UnityEngine.Object.FindFirstObjectByType<WorldRegionRoot>();
                if (rr == null) continue;
                var c = rr.GetComponent<WorldSkyVisibility>() ?? rr.gameObject.AddComponent<WorldSkyVisibility>();
                c.map = tex; c.originLocal = mn; c.texelM = texel; c.heightBase = hBase; c.heightStep = hStep;
                c.sunDirs = sunDirs; c.sunPresets = k_SunPresets.ToArray();
                EditorUtility.SetDirty(c);
                EditorSceneManager.SaveScene(sc);
            }
            Debug.Log(string.Format(ci, "SKYBAKE: region={0} size={1}x{2} texel={3} m raster={4:F1}s sky={5:F1}s sun={6:F1}s total={7:F1}s " +
                "vis_mean={8:F3} vis_road={14:F3} tris={9} solid_inst={10} crowns={11} bytes1m={12} bytes2m={13}", region, w, h, TexelM, tRaster, tVis - tRaster,
                tSun - tVis, sw.Elapsed.TotalSeconds, visMean, tris, instSolid, instCrown, MipBytes(w, h), MipBytes(w / 2, h / 2), visRoad));
        }

        /// <summary>Furniture / building sub-mesh material → occluder kind (thin or see-through parts do not occlude at 1 m).</summary>
        static Kind Classify(string mat)
        {
            string m = mat.ToLowerInvariant();
            if (m.Contains("hedge")) return Kind.Crown;
            if (m.EndsWith("concrete_fence")) return Kind.Solid;   // 2 m precast panel fences: opaque
            string[] skip = { "fence", "wire", "glass", "lamp", "luminaire", "signal", "insulator", "marking", "decal", "reflective",
                              "paint_yellow", "reflector", "plate", "barrier_", "pole", "post", "gate_boom", "downpipe", "gutter", "cone_",
                              "dock_light", "dock_digits", "contact", "strap", "insulator", "cycle_" };
            foreach (var s in skip) if (m.Contains(s)) return Kind.Skip;
            return Kind.Solid;
        }

        static byte B(float v) => (byte)Mathf.Clamp(Mathf.RoundToInt(v * 255f), 0, 255);

        static Color32[] Downsample(Color32[] px, int w, int h)
        {
            int w2 = w / 2, h2 = h / 2;
            var o = new Color32[w2 * h2];
            for (int z = 0; z < h2; z++)
                for (int x = 0; x < w2; x++)
                {
                    int r = 0, gg = 0, b = 0, a = 0;
                    for (int dz = 0; dz < 2; dz++)
                        for (int dx = 0; dx < 2; dx++)
                        {
                            var c = px[(z * 2 + dz) * w + x * 2 + dx];
                            r += c.r; gg += c.g; b += c.b; a += c.a;
                        }
                    o[z * w2 + x] = new Color32((byte)((r + 2) / 4), (byte)((gg + 2) / 4), (byte)((b + 2) / 4), (byte)((a + 2) / 4));
                }
            return o;
        }

        static Texture2D MakeTexture(Color32[] px, int w, int h, string name)
        {
            var t = new Texture2D(w, h, TextureFormat.RGBA32, true, true) { name = name, wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear, anisoLevel = 1 };
            t.SetPixels32(px);
            t.Apply(true, true);   // non-readable: GPU copy only at run time
            return t;
        }

        static void SaveTexture(Texture2D t, string path)
        {
            var old = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
            if (old != null)
            {
                EditorUtility.CopySerialized(t, old);
                EditorUtility.SetDirty(old);
            }
            else AssetDatabase.CreateAsset(t, path);
        }

        static long MipBytes(int w, int h)
        {
            long s = 0;
            while (true) { s += (long)w * h * 4; if (w == 1 && h == 1) break; w = Math.Max(1, w / 2); h = Math.Max(1, h / 2); }
            return s;
        }

        static void WritePng(string path, Color32[] px, int w, int h, int ch)
        {
            // north up (z grows upwards in the image)
            var t = new Texture2D(w, h, TextureFormat.RGB24, false, true);
            var o = new Color32[px.Length];
            for (int i = 0; i < px.Length; i++)
            {
                byte v = ch == 0 ? px[i].r : ch == 1 ? px[i].g : ch == 2 ? px[i].b : px[i].a;
                o[i] = new Color32(v, v, v, 255);
            }
            t.SetPixels32(o);
            t.Apply(false);
            File.WriteAllBytes(path, t.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(t);
        }
    }
}
