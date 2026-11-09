using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using Game.Editor.Build;
using Game.Rendering.Editor;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using static Game.World.Import.MiniJson;

namespace Game.World.Import
{
    /// <summary>
    /// Imports a generated region (tools/worldgen roads/build_world.py) into Unity:
    ///   Data/Regions/&lt;id&gt;/generated/world_manifest.json + Data/raw/derived/&lt;id&gt;/world/chunk_*.glb
    ///   → Assets/_Generated/World/&lt;id&gt;/ (gitignored): Chunks/*.glb (imported by glTFast, ADR 0011),
    ///     Collision/*.asset (one mesh per surface type), Materials/*.mat, and the scene (see <see cref="WorldSceneBuilder"/>).
    /// Batchmode: -executeMethod Game.World.Import.RegionImporter.ImportBatch -region bialystok-industrial-c
    /// (scripts/import-region.ps1). Prints "IMPORT_RESULT: OK|FAILED".
    /// </summary>
    public static class RegionImporter
    {
        public const string GeneratedRoot = "Assets/_Generated/World";

        public static void ImportBatch()
        {
            int exit = 1;
            try
            {
                string region = EditorTools.Arg("-region", "bialystok-industrial-c");
                bool skipCopy = EditorTools.HasArg("-skipCopy");
                var r = Import(region, !skipCopy);
                WorldSceneBuilder.Build(r);
                exit = 0;
                Debug.Log($"IMPORT_RESULT: OK region={region} chunks={r.Chunks.Count} corridor={r.Chunks.Count(c => c.Corridor)} scene={r.ScenePath}");
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Debug.Log("IMPORT_RESULT: FAILED");
            }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        [MenuItem("Kamion/World/Import region bialystok-industrial-c")]
        static void Menu() => WorldSceneBuilder.Build(Import("bialystok-industrial-c", true));

        // ------------------------------------------------------------------------------------------------- data model
        public sealed class Chunk
        {
            public string Id;
            public string GlbAssetPath;
            public Vector2 Min, Max;     // local E/N
            public bool Corridor;
            public string Sha256;
            public GameObject Model;     // glTFast-imported asset root
            public Mesh CollisionHost;   // container asset with the per-surface collision meshes
            public readonly List<(Mesh mesh, string surface)> Collision = new List<(Mesh, string)>();
            public readonly List<(string node, Mesh mesh, Material[] materials)> Visual = new List<(string, Mesh, Material[])>();
        }

        public sealed class Result
        {
            public string Region;
            public string Dir;
            public string ScenePath;
            public double AnchorX, AnchorY, AnchorZ;
            public float ChunkSize;
            public readonly List<Chunk> Chunks = new List<Chunk>();
            public readonly Dictionary<string, Material> Materials = new Dictionary<string, Material>();
            public readonly Dictionary<string, string> MaterialSurface = new Dictionary<string, string>();
            public Vector2[] RouteEN = Array.Empty<Vector2>();
            public float[] RouteLimits = Array.Empty<float>();
            public List<object> ControlCameras = new List<object>();
            public float[] LodSwitchM = { 0f, 120f, 300f, 700f };
            public int ShaMismatches;
        }

        /// <summary>Corridor = chunks within this distance of the start route get full LODs, markings and collision.</summary>
        public const float CorridorM = 320f;

        // ------------------------------------------------------------------------------------------------- import
        public static Result Import(string region, bool copyGlb)
        {
            string repo = EditorTools.RepoRoot;
            string regionDir = Path.Combine(repo, "Data", "Regions", region);
            var manifest = Obj(Parse(File.ReadAllText(Path.Combine(regionDir, "generated", "world_manifest.json"))));
            var regionYaml = File.ReadAllLines(Path.Combine(regionDir, "region.yaml"));
            var r = new Result { Region = region, Dir = $"{GeneratedRoot}/{region}", ChunkSize = (float)Num(manifest.Get("chunk_size_m")) };
            ReadAnchor(regionYaml, out r.AnchorX, out r.AnchorY, out r.AnchorZ);
            r.ScenePath = $"{r.Dir}/{WorldSceneBuilder.SceneNameFor(region)}.unity";
            var ox = Obj(manifest.Get("origin_epsg2180"));
            if (Math.Abs(Num(ox.Get("x")) - r.AnchorX) > 0.01 || Math.Abs(Num(ox.Get("y")) - r.AnchorY) > 0.01)
                throw new InvalidOperationException("world_manifest origin != region.yaml origin");
            var lods = Arr(manifest.Get("terrain_lods"));
            r.LodSwitchM = lods.Select(l => (float)Num(Obj(l).Get("suggested_switch_m"))).ToArray();

            // Route (scripts/export-route.py) and control cameras (worldgen).
            string routePath = Path.Combine(regionDir, "route_start.json");
            if (File.Exists(routePath))
            {
                var route = Obj(Parse(File.ReadAllText(routePath)));
                r.RouteEN = Arr(route.Get("points_en")).Select(p => new Vector2((float)Num(Arr(p)[0]), (float)Num(Arr(p)[1]))).ToArray();
                r.RouteLimits = Arr(route.Get("maxspeed_kmh")).Select(v => v == null ? 0f : (float)Num(v)).ToArray();
            }
            else Debug.LogWarning($"[IMPORT] {routePath} missing: run `uv run --project tools/worldgen python scripts/export-route.py --region {region}`");
            string camPath = Path.Combine(regionDir, "generated", "control_cameras.json");
            if (File.Exists(camPath)) r.ControlCameras = Arr(Obj(Parse(File.ReadAllText(camPath))).Get("cameras"));

            foreach (var d in new[] { r.Dir, r.Dir + "/Chunks", r.Dir + "/Collision", r.Dir + "/Materials" })
                Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, d));
            EnsureGitignored();

            // ---- materials (data-driven from the manifest) ----
            if (!WorldTextureGenerator.Exist()) WorldTextureGenerator.GenerateAll();
            LookDevAssets.EnsureAll();
            foreach (var kv in Obj(manifest.Get("materials")))
            {
                var m = Obj(kv.Value);
                string surface = Str(m.Get("surface"));
                r.MaterialSurface[kv.Key] = surface;
                if (m.Get("collision") is bool col && col) continue;
                var c = Arr(m.Get("color"));
                var albedo = new Color((float)Num(c[0]), (float)Num(c[1]), (float)Num(c[2]));
                float rough = m.Get("rough") != null ? (float)Num(m.Get("rough")) : 0.9f;
                float metal = m.Get("metal") != null ? (float)Num(m.Get("metal")) : 0f;
                bool decal = m.Get("decal") is bool dc && dc;
                Color? bg = null;
                if (decal && Obj(manifest.Get("materials")).Get("road_asphalt") is Dictionary<string, object> ra)
                {
                    var rc = Arr(ra.Get("color"));
                    bg = new Color((float)Num(rc[0]), (float)Num(rc[1]), (float)Num(rc[2]));
                }
                r.Materials[kv.Key] = LookDevAssets.WorldMaterial($"{r.Dir}/Materials/M_{kv.Key}.mat", surface, albedo, rough, metal, decal, bg);
            }

            // ---- chunks: copy GLB (verified against the manifest sha256) and let glTFast import them ----
            string srcDir = Path.Combine(repo, "Data", "raw", "derived", region, "world");
            var chunks = Arr(manifest.Get("chunks"));
            AssetDatabase.StartAssetEditing();
            try
            {
                foreach (var co in chunks)
                {
                    var c = Obj(co);
                    var b = Obj(c.Get("bounds_local_m"));
                    var ch = new Chunk
                    {
                        Id = Str(c.Get("id")),
                        Min = new Vector2((float)Num(b.Get("e_min")), (float)Num(b.Get("n_min"))),
                        Max = new Vector2((float)Num(b.Get("e_max")), (float)Num(b.Get("n_max"))),
                        Sha256 = Str(c.Get("sha256")),
                    };
                    string file = Path.GetFileName(Str(c.Get("file")));
                    ch.GlbAssetPath = $"{r.Dir}/Chunks/{file}";
                    ch.Corridor = DistanceToRoute(ch, r.RouteEN) <= CorridorM || r.RouteEN.Length == 0;
                    string dst = Path.Combine(EditorTools.ProjectRoot, ch.GlbAssetPath);
                    if (copyGlb || !File.Exists(dst))
                    {
                        string src = Path.Combine(srcDir, file);
                        if (!File.Exists(src))
                            throw new FileNotFoundException($"{src} missing - run: uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region {region}");
                        string srcSha = Sha256(src);
                        if (srcSha != ch.Sha256)
                        {
                            // Not fatal: the generator output differs in float rounding between Python environments
                            // (seen 2026-11-09: 10 of 64 chunks after a fresh uv venv). Reported to world-builder.
                            Debug.LogWarning($"[IMPORT] {file}: sha256 {srcSha.Substring(0, 12)} != manifest {ch.Sha256.Substring(0, 12)} (regenerated in another environment?)");
                            r.ShaMismatches++;
                        }
                        if (!File.Exists(dst) || Sha256(dst) != srcSha) File.Copy(src, dst, true);
                    }
                    r.Chunks.Add(ch);
                }
            }
            finally { AssetDatabase.StopAssetEditing(); }
            AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);

            // ---- read the imported models ----
            foreach (var ch in r.Chunks)
            {
                ch.Model = AssetDatabase.LoadAssetAtPath<GameObject>(ch.GlbAssetPath);
                if (ch.Model == null) throw new InvalidOperationException($"glTFast did not import {ch.GlbAssetPath}");
                CollectMeshes(ch, r);
                BuildCollision(ch, r);
            }
            AssetDatabase.SaveAssets();
            Debug.Log($"[IMPORT] {region}: sha256 mismatches vs manifest: {r.ShaMismatches}");
            Debug.Log($"[IMPORT] {region}: {r.Chunks.Count} chunks ({r.Chunks.Count(c => c.Corridor)} in the {CorridorM:F0} m route corridor), {r.Materials.Count} materials, route {r.RouteEN.Length} points");
            return r;
        }

        static readonly string[] k_Nodes = { "terrain_lod0", "terrain_lod1", "terrain_lod2", "terrain_lod3", "road", "bridge", "markings", "road_collision" };

        /// <summary>Walks the glTFast hierarchy: (glTF node name, mesh, material per submesh mapped to our materials).</summary>
        static void CollectMeshes(Chunk ch, Result r)
        {
            foreach (var mf in ch.Model.GetComponentsInChildren<MeshFilter>(true))
            {
                string node = NodeName(mf.transform);
                if (node == null) { Debug.LogWarning($"[IMPORT] {ch.Id}: unknown node {mf.name}"); continue; }
                var mr = mf.GetComponent<MeshRenderer>();
                var src = mr != null ? mr.sharedMaterials : Array.Empty<Material>();
                var mats = new Material[src.Length];
                for (int i = 0; i < src.Length; i++)
                {
                    string id = src[i] != null ? src[i].name : null;
                    if (id != null && r.Materials.TryGetValue(id, out var m)) mats[i] = m;
                    else if (node != "road_collision") Debug.LogWarning($"[IMPORT] {ch.Id}/{node}: material '{id}' not in manifest");
                }
                ch.Visual.Add((node, mf.sharedMesh, mats));
            }
        }

        static string NodeName(Transform t)
        {
            for (; t != null; t = t.parent)
                foreach (var n in k_Nodes)
                    if (t.name == n) return n;
            return null;
        }

        /// <summary>Splits the road_collision submeshes (one per surface) into separate meshes for MeshColliders.</summary>
        static void BuildCollision(Chunk ch, Result r)
        {
            string path = $"{r.Dir}/Collision/{Path.GetFileNameWithoutExtension(ch.GlbAssetPath)}_collision.asset";
            AssetDatabase.DeleteAsset(path);
            var host = new Mesh { name = ch.Id + "_collision" };
            AssetDatabase.CreateAsset(host, path);
            ch.CollisionHost = host;
            foreach (var (node, mesh, _) in ch.Visual)
            {
                if (node != "road_collision") continue;
                var mr = FindRenderer(ch.Model, mesh);
                var srcMats = mr != null ? mr.sharedMaterials : Array.Empty<Material>();
                var verts = mesh.vertices;
                for (int s = 0; s < mesh.subMeshCount; s++)
                {
                    string matName = s < srcMats.Length && srcMats[s] != null ? srcMats[s].name : "collision_asphalt";
                    string surface = r.MaterialSurface.TryGetValue(matName, out var sf) ? sf : "asphalt";
                    var tris = mesh.GetTriangles(s);
                    // Compact the vertex set of this surface.
                    var map = new Dictionary<int, int>();
                    var v2 = new List<Vector3>();
                    for (int i = 0; i < tris.Length; i++)
                    {
                        if (!map.TryGetValue(tris[i], out int ni)) { ni = v2.Count; map[tris[i]] = ni; v2.Add(verts[tris[i]]); }
                        tris[i] = ni;
                    }
                    var m = new Mesh { name = $"{ch.Id}_{surface}" };
                    m.indexFormat = v2.Count > 65000 ? IndexFormat.UInt32 : IndexFormat.UInt16;
                    m.SetVertices(v2);
                    m.SetTriangles(tris, 0);
                    m.RecalculateBounds();
                    AssetDatabase.AddObjectToAsset(m, host);
                    ch.Collision.Add((m, surface));
                }
            }
        }

        static MeshRenderer FindRenderer(GameObject root, Mesh mesh)
        {
            foreach (var mf in root.GetComponentsInChildren<MeshFilter>(true))
                if (mf.sharedMesh == mesh) return mf.GetComponent<MeshRenderer>();
            return null;
        }

        public static SurfaceKind SurfaceKindOf(string surface)
        {
            switch (surface)
            {
                case "asphalt": return SurfaceKind.DryAsphalt;
                case "concrete": case "concrete_kerb": return SurfaceKind.Concrete;
                case "paving_stones": case "sett": return SurfaceKind.Cobbles;
                case "gravel": return SurfaceKind.Gravel;
                case "grass": return SurfaceKind.Grass;
                default: return SurfaceKind.DryAsphalt;
            }
        }

        static float DistanceToRoute(Chunk ch, Vector2[] route)
        {
            float best = float.MaxValue;
            foreach (var p in route)
            {
                float dx = Mathf.Max(ch.Min.x - p.x, 0f, p.x - ch.Max.x);
                float dy = Mathf.Max(ch.Min.y - p.y, 0f, p.y - ch.Max.y);
                best = Mathf.Min(best, Mathf.Sqrt(dx * dx + dy * dy));
            }
            return best;
        }

        static void ReadAnchor(string[] yaml, out double x, out double y, out double z)
        {
            x = y = z = double.NaN;
            bool inOrigin = false;
            foreach (var line in yaml)
            {
                if (line.StartsWith("origin:")) { inOrigin = true; continue; }
                if (inOrigin && !line.StartsWith("  ")) break;
                if (!inOrigin) continue;
                var t = line.Trim();
                if (t.StartsWith("x:")) x = double.Parse(t.Substring(2), CultureInfo.InvariantCulture);
                else if (t.StartsWith("y:")) y = double.Parse(t.Substring(2), CultureInfo.InvariantCulture);
                else if (t.StartsWith("z:")) z = double.Parse(t.Substring(2), CultureInfo.InvariantCulture);
            }
            if (double.IsNaN(x) || double.IsNaN(y) || double.IsNaN(z)) throw new InvalidDataException("region.yaml: origin x/y/z missing");
        }

        static string Sha256(string file)
        {
            using (var s = File.OpenRead(file))
            using (var h = SHA256.Create())
                return BitConverter.ToString(h.ComputeHash(s)).Replace("-", "").ToLowerInvariant();
        }

        static void EnsureGitignored()
        {
            string gi = Path.Combine(EditorTools.RepoRoot, ".gitignore");
            string text = File.Exists(gi) ? File.ReadAllText(gi) : "";
            if (!text.Contains("game/Assets/_Generated/"))
                Debug.LogWarning("[IMPORT] .gitignore does not exclude game/Assets/_Generated/ - imported chunks would bloat git");
        }
    }
}
