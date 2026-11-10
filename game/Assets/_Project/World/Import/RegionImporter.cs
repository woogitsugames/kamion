using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using Game.Editor.Build;
using Game.Rendering.Editor;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEngine;
using static Game.World.Import.MiniJson;

namespace Game.World.Import
{
    /// <summary>
    /// Imports a generated region (tools/worldgen roads/build_world.py, schema world-manifest/1 v2) into Unity (ADR 0011,
    /// ADR 0012). The GLBs are read directly (<see cref="GlbReader"/>) and baked into compact meshes per content tier:
    ///   Low  (Low + Medium quality): chunk_*.low.glb → terrain "band" 2 m near roads / 4 m elsewhere, terrain 4 m / 8 m,
    ///        roads, bridges, markings, paved areas, LOD1 buildings, linear furniture;
    ///   High (High + Ultra):         chunk_*.glb → terrain band 1 m near roads / 2 m elsewhere, terrain 2/4/8 m, the same
    ///        layers plus LOD0 buildings (openings, docks).
    /// Collision (identical for both tiers): road_collision split per surface + terrain fallback (2 m in the start-route
    /// corridor, 4 m elsewhere). Point instances (props, signs, signals, trees) → <see cref="InstanceImporter"/>.
    /// Output (gitignored): Assets/_Generated/World/&lt;id&gt;/{Meshes/Low|High, Collision, Materials, Textures,
    /// Instances.asset, WorldC.unity, WorldC_High.unity}.
    /// Batchmode: -executeMethod Game.World.Import.RegionImporter.ImportBatch -region bialystok-industrial-c
    /// (scripts/import-region.ps1). Prints "IMPORT_RESULT: OK|FAILED" and "WORLD_MEMORY: ..." lines.
    /// </summary>
    public static class RegionImporter
    {
        public const string GeneratedRoot = "Assets/_Generated/World";
        public static readonly string[] Tiers = { "Low", "High" };

        public static void ImportBatch()
        {
            int exit = 1;
            try
            {
                string region = EditorTools.Arg("-region", "bialystok-industrial-c");
                string only = EditorTools.Arg("-tiers", "Low,High");
                var r = Import(region, only.Split(','));
                foreach (var t in r.TiersBuilt) WorldSceneBuilder.Build(r, t);
                WorldSkyBake.Bake(region);   // ADR 0064: ground sky visibility + far sun shadows, attached to the scenes
                Game.Editor.Setup.BuildScenes.Apply();
                WriteReport(r);
                exit = 0;
                Debug.Log($"IMPORT_RESULT: OK region={region} chunks={r.Chunks.Count} corridor={r.Chunks.Count(c => c.Corridor)} tiers={string.Join("+", r.TiersBuilt)}");
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Debug.Log("IMPORT_RESULT: FAILED");
            }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        [MenuItem("Kamion/World/Import region bialystok-industrial-c")]
        static void Menu()
        {
            var r = Import("bialystok-industrial-c", Tiers);
            foreach (var t in r.TiersBuilt) WorldSceneBuilder.Build(r, t);
            Game.Editor.Setup.BuildScenes.Apply();
            WriteReport(r);
        }

        // ------------------------------------------------------------------------------------------------- data model
        public sealed class Layer
        {
            public string Node;          // terrain_band, terrain_lod1..3, road, bridge, markings, paved, buildings, buildings_lod1, furniture
            public Mesh Mesh;
            public Material[] Materials;
        }

        public sealed class Chunk
        {
            public string Id;
            public Vector2 Min, Max;     // local E/N
            public bool Corridor;
            public string Sha256;
            public readonly Dictionary<string, List<Layer>> Layers = new Dictionary<string, List<Layer>>();   // tier → layers
            public readonly List<(Mesh mesh, string surface)> Collision = new List<(Mesh, string)>();
            public Mesh TerrainCollision;
            public float FineFractionLow, FineFractionHigh;
        }

        public sealed class Result
        {
            public string Region;
            public string Dir;
            public double AnchorX, AnchorY, AnchorZ;
            public float ChunkSize;
            public readonly List<Chunk> Chunks = new List<Chunk>();
            public readonly Dictionary<string, Material> Materials = new Dictionary<string, Material>();
            public readonly Dictionary<string, Dictionary<string, object>> MaterialDefs = new Dictionary<string, Dictionary<string, object>>();
            public readonly Dictionary<string, string> MaterialSurface = new Dictionary<string, string>();
            public Vector2[] RouteEN = Array.Empty<Vector2>();
            public float[] RouteLimits = Array.Empty<float>();
            public List<object> ControlCameras = new List<object>();
            public float[] LodSwitchM = { 0f, 120f, 300f, 700f };
            public int ShaMismatches;
            public readonly List<string> TiersBuilt = new List<string>();
            public WorldInstanceSet Instances;
            /// <summary>Forest HLOD cells (ADR 0015): node forest_hlod_&lt;cell&gt; of the chunk GLBs (Low variant; same mesh in both).</summary>
            public readonly List<(string cell, GlbReader.MeshNode node, string chunk)> ForestHlod = new List<(string, GlbReader.MeshNode, string)>();
            /// <summary>manifest lod_policy.&lt;Low|High&gt;.forest_hlod_m / forest_hlod_cull_m (cross-checked with QualityProfile).</summary>
            public readonly Dictionary<string, (float switchM, float cullM)> ForestHlodPolicy = new Dictionary<string, (float, float)>();
            public InstanceImporter.Colliders PropColliders;
            public readonly Dictionary<string, long> MemoryBytes = new Dictionary<string, long>();   // "<tier>/<category>"
            public string ScenePath(string tier) => $"{Dir}/{WorldSceneBuilder.SceneNameFor(Region, tier)}.unity";
        }

        /// <summary>Corridor = chunks within this distance of the start route get the 2 m terrain collider.</summary>
        public const float CorridorM = 320f;
        /// <summary>Terrain band: blocks with a road/paved edge closer than this keep the fine spacing (+1 block dilation).</summary>
        public const float TerrainBandM = 15f;
        /// <summary>Low content: tighter band (10 m, no dilation) - the 2 m terrain is the largest Low mesh in the APK.</summary>
        public const float TerrainBandLowM = 10f;
        /// <summary>Low content: chunks closer than this to the start route also get LOD0 buildings.</summary>
        public const float LowBuildingsLod0M = 60f;

        // ------------------------------------------------------------------------------------------------- import
        public static Result Import(string region, string[] tiers)
        {
            string repo = EditorTools.RepoRoot;
            string regionDir = Path.Combine(repo, "Data", "Regions", region);
            var manifest = Obj(Parse(File.ReadAllText(Path.Combine(regionDir, "generated", "world_manifest.json"))));
            var regionYaml = File.ReadAllLines(Path.Combine(regionDir, "region.yaml"));
            var r = new Result { Region = region, Dir = $"{GeneratedRoot}/{region}", ChunkSize = (float)Num(manifest.Get("chunk_size_m")) };
            ReadAnchor(regionYaml, out r.AnchorX, out r.AnchorY, out r.AnchorZ);
            var ox = Obj(manifest.Get("origin_epsg2180"));
            if (Math.Abs(Num(ox.Get("x")) - r.AnchorX) > 0.01 || Math.Abs(Num(ox.Get("y")) - r.AnchorY) > 0.01)
                throw new InvalidOperationException("world_manifest origin != region.yaml origin");
            r.LodSwitchM = Arr(manifest.Get("terrain_lods")).Select(l => (float)Num(Obj(l).Get("suggested_switch_m"))).ToArray();
            if (manifest.Get("lod_policy") is Dictionary<string, object> pol)
                foreach (var kv in pol)
                    if (kv.Value is Dictionary<string, object> pt && pt.Get("forest_hlod_m") != null)
                        r.ForestHlodPolicy[kv.Key] = ((float)Num(pt.Get("forest_hlod_m")),
                            pt.Get("forest_hlod_cull_m") != null ? (float)Num(pt.Get("forest_hlod_cull_m")) : 0f);

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

            // v1 imports copied the GLBs into Assets (glTFast); the bake reads them in place - drop the copies.
            if (AssetDatabase.IsValidFolder($"{r.Dir}/Chunks")) AssetDatabase.DeleteAsset($"{r.Dir}/Chunks");
            foreach (var d in new[] { r.Dir, r.Dir + "/Collision", r.Dir + "/Materials", r.Dir + "/Textures", r.Dir + "/Meshes/Low", r.Dir + "/Meshes/High" })
                Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, d));
            EnsureGitignored();

            // ---- materials (data-driven from the manifest) ----
            if (!WorldTextureGenerator.Exist()) WorldTextureGenerator.GenerateAll();
            LookDevAssets.EnsureAll();
            WorldPbrMaterials.Reset();
            FabMaterials.Reset();
            var roadAsphalt = Obj(manifest.Get("materials")).Get("road_asphalt") as Dictionary<string, object>;
            foreach (var kv in Obj(manifest.Get("materials")))
            {
                var m = Obj(kv.Value);
                r.MaterialDefs[kv.Key] = m;
                r.MaterialSurface[kv.Key] = Str(m.Get("surface"));
            }
            foreach (var kv in r.MaterialDefs.ToList())
            {
                var m = kv.Value;
                if (m.Get("collision") is bool col && col) continue;
                r.Materials[kv.Key] = CreateMaterial(r, kv.Key, m, roadAsphalt);
            }

            // ---- chunks ----
            string srcDir = Path.Combine(repo, "Data", "raw", "derived", region, "world");
            var chunkDefs = Arr(manifest.Get("chunks"));
            int n = 0;
            foreach (var co in chunkDefs)
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
                ch.Corridor = DistanceToRoute(ch, r.RouteEN) <= CorridorM || r.RouteEN.Length == 0;
                EditorUtility.DisplayProgressBar("Import region", ch.Id, (float)n++ / chunkDefs.Count);

                string lowFile = Path.Combine(srcDir, Path.GetFileName(Str(Obj(c.Get("low")).Get("file"))));
                string highFile = Path.Combine(srcDir, Path.GetFileName(Str(c.Get("file"))));
                CheckSha(r, lowFile, Str(Obj(c.Get("low")).Get("sha256")), region);
                var low = GlbReader.Load(lowFile);
                BakeCollision(r, ch, low);
                foreach (var node in low.Nodes)
                    if (node.Name.StartsWith("forest_hlod_") && node.Primitives.Count > 0)
                        r.ForestHlod.Add((node.Extras != null && node.Extras.Get("cell") is string cid ? cid : node.Name.Substring("forest_hlod_".Length), node, ch.Id));
                GlbReader high = null;
                GlbReader High() { if (high == null) { CheckSha(r, highFile, ch.Sha256, region); high = GlbReader.Load(highFile); } return high; }
                foreach (var tier in tiers)
                    BakeVisual(r, ch, tier == "High" ? High() : low, tier,
                        // Low content keeps LOD0 buildings (docks, openings) near the start route: that is where the
                        // player is; elsewhere LOD1 prisms (ADR 0012).
                        tier != "High" && DistanceToRoute(ch, r.RouteEN) <= LowBuildingsLod0M ? High().Find("buildings") : null);
                r.Chunks.Add(ch);
            }
            EditorUtility.ClearProgressBar();
            r.TiersBuilt.AddRange(tiers);

            // ---- point instances (props, trees) ----
            var instFiles = chunkDefs.Select(co => Path.Combine(srcDir, Path.GetFileName(Str(Obj(Obj(co).Get("instances")).Get("file"))))).ToList();
            r.Instances = InstanceImporter.Build(r, instFiles, out r.PropColliders);

            AssetDatabase.SaveAssets();
            Debug.Log($"[IMPORT] {region}: sha256 mismatches vs manifest: {r.ShaMismatches}");
            Debug.Log($"[IMPORT] {region}: {r.Chunks.Count} chunks ({r.Chunks.Count(c => c.Corridor)} in the {CorridorM:F0} m route corridor), {r.Materials.Count} materials, route {r.RouteEN.Length} points");
            return r;
        }

        static void CheckSha(Result r, string file, string expected, string region)
        {
            if (!File.Exists(file))
                throw new FileNotFoundException($"{file} missing - run: uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region {region}");
            string sha = Sha256(file);
            if (sha == expected) return;
            // Not fatal: generator bytes differ between Python environments (float rounding), see WORLD_GENERATION.md.
            Debug.LogWarning($"[IMPORT] {Path.GetFileName(file)}: sha256 {sha.Substring(0, 12)} != manifest {expected.Substring(0, 12)} (regenerated in another environment?)");
            r.ShaMismatches++;
        }

        // ------------------------------------------------------------------------------------------------- materials
        static Material CreateMaterial(Result r, string id, Dictionary<string, object> m, Dictionary<string, object> roadAsphalt)
        {
            var mat = CreateMaterialCore(r, id, m, roadAsphalt);
            // ADR 0060: manifest "sky_occ": [down-facing ambient, horizon reflection] (structures, glazing; 0 = off)
            if (mat != null && m.Get("sky_occ") is List<object> so && so.Count >= 2 && mat.HasProperty("_SkyOcc"))
            {
                mat.SetVector("_SkyOcc", new Vector4((float)Num(so[0]), (float)Num(so[1]), 0f, 0f));
                EditorUtility.SetDirty(mat);
            }
            return mat;
        }

        static Material CreateMaterialCore(Result r, string id, Dictionary<string, object> m, Dictionary<string, object> roadAsphalt)
        {
            var c = Arr(m.Get("color"));
            var albedo = new Color((float)Num(c[0]), (float)Num(c[1]), (float)Num(c[2]));
            float rough = m.Get("rough") != null ? (float)Num(m.Get("rough")) : 0.9f;
            float metal = m.Get("metal") != null ? (float)Num(m.Get("metal")) : 0f;
            string surface = Str(m.Get("surface"));
            string path = $"{r.Dir}/Materials/M_{id}.mat";
            if (id == "curb_concrete" && FabMaterials.Has(id))
            {
                var curb = WorldPbrMaterials.Create(r, id, m, path);
                if (curb != null && FabMaterials.ApplySurfaceBase(r, id, curb)) return curb;
            }
            var fab = FabMaterials.Create(r, id, path);
            if (fab != null) return fab;
            if (m.Get("hlod") is bool hl && hl)
            {
                // Forest HLOD (ADR 0015): shared PNG baked from the LOD0 trees (texture_ref, repo-relative). Edge walls are
                // alpha-masked and double sided; the canopy is opaque. On simpleFoliage tiers WorldInstances swaps the edge
                // walls to Kamion/Vegetation at run time, like leaf cards.
                bool edge = m.Get("alpha_cutoff") != null;
                var t = InstanceImporter.ImportTexture(r, Path.Combine(EditorTools.RepoRoot, Str(m.Get("texture_ref"))), clamp: false);
                // v3.4 (ADR 0023): edge walls with a wall-space normal / sky-visibility map are lit like the trees.
                if (edge && m.Get("normal_ref") is string nref && File.Exists(Path.Combine(EditorTools.RepoRoot, nref)))
                {
                    var vis = InstanceImporter.EdgeVisibility;
                    return InstanceImporter.VegetationMaterial(path, t, InstanceImporter.ImportTexture(r, Path.Combine(EditorTools.RepoRoot, nref), clamp: false, linear: true),
                        "_HLOD_EDGE", new Vector4(1f, vis.x, vis.y, 0f), (float)Num(m.Get("alpha_cutoff")));
                }
                return LitMaterial(path, albedo, rough, metal, t, edge, edge ? (float)Num(m.Get("alpha_cutoff")) : 0.5f, edge, null);
            }
            if (m.Get("shader") as string == "wire") return WireMaterial(path, albedo);
            // Parked-vehicle contact shadow (ADR 0050): shader defaults; InstanceImporter makes one copy per prototype spec.
            if (m.Get("shader") as string == "vehicle_contact") return VehicleContactMaterial(path, null);
            if (m.Get("window_grid") is Dictionary<string, object> grid && m.Get("base") is string baseId)
                return FarFacadeMaterial(r, path, baseId, albedo, rough, grid, m.Get("glass_color") as List<object>);
            // Tinted see-through glazing of prop LOD0 (ADR 0041 par. 7): manifest "blend": true + "alpha".
            if (m.Get("blend") is bool bl && bl && m.Get("alpha") != null)
            {
                // Parked-car glazing (ADR 0041 par. 8): dark tinted sheet with a Fresnel sky reflection and a dust film
                // from UV0. URP Lit blended glass mirrored the whole sky at rough 0.4 and read milky grey on High.
                if (m.Get("shader") as string == "car_glass")
                    return CarGlassMaterial(path, albedo, rough, (float)Num(m.Get("alpha")), m.Get("dust") != null ? (float)Num(m.Get("dust")) : 0f,
                        m.Get("privacy_alpha") != null ? (float)Num(m.Get("privacy_alpha")) : 0.80f,
                        m.Get("reflect") != null ? (float)Num(m.Get("reflect")) : 1f);
                // Optional alpha texture (road film overlays of parked cars): matt, no sky mirror.
                Texture2D bt = null;
                if (m.Get("texture") is string btex)
                    bt = InstanceImporter.ImportTexture(r, Path.Combine(EditorTools.RepoRoot, "art-source", "world", "textures", btex + ".png"), clamp: false);
                var gm = LitMaterial(path, albedo, rough, metal, bt, false, 0.5f, false, null);
                if (bt != null)
                {
                    gm.SetFloat("_SpecularHighlights", 0f);
                    gm.SetFloat("_EnvironmentReflections", 0f);
                    gm.EnableKeyword("_SPECULARHIGHLIGHTS_OFF");
                    gm.EnableKeyword("_ENVIRONMENTREFLECTIONS_OFF");
                }
                var gc = new Color(albedo.r, albedo.g, albedo.b, 1f).gamma;
                gc.a = (float)Num(m.Get("alpha"));
                gm.SetColor("_BaseColor", gc);
                gm.SetFloat("_Surface", 1f);
                gm.SetFloat("_Blend", 0f);
                gm.SetFloat("_SrcBlend", (float)UnityEngine.Rendering.BlendMode.SrcAlpha);
                gm.SetFloat("_DstBlend", (float)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                gm.SetFloat("_ZWrite", 0f);
                gm.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
                gm.SetOverrideTag("RenderType", "Transparent");
                gm.SetShaderPassEnabled("ShadowCaster", false);
                gm.SetShaderPassEnabled("DepthOnly", false);
                gm.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;
                EditorUtility.SetDirty(gm);
                return gm;
            }
            // Generated PBR sets (ADR 0022): ground, facades, props, decals with a set in materials_spec.json.
            var pbr = WorldPbrMaterials.Create(r, id, m, path);
            if (pbr != null) return pbr;
            string tex = m.Get("texture") as string;
            if (tex != null || m.Get("emissive") != null)
            {
                Texture2D t = null;
                if (tex != null) t = InstanceImporter.ImportTexture(r, Path.Combine(EditorTools.RepoRoot, "art-source", "world", "textures", tex + ".png"), clamp: false);
                bool clip = m.Get("alpha_cutoff") != null;
                Color? emission = null;
                if (m.Get("emissive") is List<object> e)
                    // Exposed units (ADR 0010): emissive in the manifest is relative radiance; ×0.25 keeps a lit signal
                    // lamp clearly brighter than daylit surfaces without clipping to white on LDR tiers.
                    emission = new Color((float)Num(e[0]), (float)Num(e[1]), (float)Num(e[2])) * 0.25f;
                return LitMaterial(path, albedo, rough, metal, t, clip, clip ? (float)Num(m.Get("alpha_cutoff")) : 0.5f, clip, emission);
            }
            bool decal = m.Get("decal") is bool dc && dc;
            Color? bg = null;
            if (decal && roadAsphalt != null)
            {
                var rc = Arr(roadAsphalt.Get("color"));
                bg = new Color((float)Num(rc[0]), (float)Num(rc[1]), (float)Num(rc[2]));
            }
            var mat = LookDevAssets.WorldMaterial(path, surface, albedo, rough, metal, decal, bg);
            // Terrain reads the generator's ground masks from COLOR_0 (forest floor, unmown grass, bare soil).
            if (mat.HasProperty("_GroundMasks")) mat.SetFloat("_GroundMasks", id == "terrain_grass" ? 1f : 0f);
            return mat;
        }

        /// <summary>
        /// LOD1 far facade (ADR 0015 §2): the base wall's Kamion/World Surface style + keyword _FAR_FACADE, which draws the
        /// window grid from TEXCOORD_1 (one unit = one bay × one storey; pane rectangle from the manifest window_grid).
        /// </summary>
        static Material FarFacadeMaterial(Result r, string path, string baseId, Color albedo, float rough, Dictionary<string, object> grid, List<object> glass)
        {
            r.MaterialDefs.TryGetValue(baseId, out var baseDef);
            string surface = baseDef != null ? Str(baseDef.Get("surface")) : null;
            var mat = LookDevAssets.WorldMaterial(path, surface, albedo, rough, 0f, false, null);
            float w = (float)Num(grid.Get("win_w")), sill = (float)Num(grid.Get("sill")), head = (float)Num(grid.Get("head"));
            mat.EnableKeyword("_FAR_FACADE");
            mat.SetVector("_WindowGrid", new Vector4(0.5f - w * 0.5f, 0.5f + w * 0.5f, sill, head));
            var g = glass != null ? new Color((float)Num(glass[0]), (float)Num(glass[1]), (float)Num(glass[2])) : new Color(0.03f, 0.035f, 0.04f);
            mat.SetColor("_GlassColor", new Color(g.r, g.g, g.b, 1f).gamma);
            EditorUtility.SetDirty(mat);
            return mat;
        }

        /// <summary>Power-line conductors (generator layer "wires"): camera-facing ribbons >= 1 px with coverage alpha,
        /// faded with the power-pole cull distance (Kamion/World Wire, ADR 0022).</summary>
        static Material WireMaterial(string path, Color albedo)
        {
            var shader = Shader.Find("Kamion/World Wire") ?? throw new InvalidOperationException("Kamion/World Wire not found (compile error?)");
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); }
            mat.shader = shader;
            mat.enableInstancing = true;
            mat.SetVector("_BaseColor", new Vector4(albedo.r, albedo.g, albedo.b, 1f));
            mat.SetFloat("_MinPixels", 1.2f);
            mat.SetFloat("_AAPixels", 1.0f);
            mat.SetFloat("_MaxAlpha", 0.95f);
            mat.SetFloat("_AlphaGamma", 0.5f);   // REVIEW r6 W-P0: far conductors stay readable (WORKING_VALUE)
            EditorUtility.SetDirty(mat);
            return mat;
        }

        /// <summary>Shader property of Kamion/World Vehicle Contact for each key of a generator contact spec (ADR 0050).</summary>
        static readonly (string key, string prop)[] k_ContactProps =
        {
            ("slab0", "_Slab0"), ("slab1", "_Slab1"), ("strength", "_Strength"), ("tyre", "_Tyre"), ("axles", "_Axles"),
            ("sun_box", "_SunBox"), ("sun_z", "_SunZ"), ("patch", "_Patch"),
        };

        /// <summary>
        /// Parked-vehicle contact shadow / AO (Kamion/World Vehicle Contact, ADR 0050): multiplicative ground patch, instanced,
        /// queue Geometry+499. <paramref name="spec"/> = the prototype's LOD0 node extras "contact" (null: shader defaults);
        /// every vector is written, so a reimport always carries the generator's values.
        /// </summary>
        public static Material VehicleContactMaterial(string path, Dictionary<string, object> spec)
        {
            var shader = Shader.Find("Kamion/World Vehicle Contact") ?? throw new InvalidOperationException("Kamion/World Vehicle Contact not found (compile error?)");
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); }
            mat.shader = shader;
            mat.shaderKeywords = Array.Empty<string>();
            mat.enableInstancing = true;
            if (spec != null)
                foreach (var (key, prop) in k_ContactProps)
                {
                    var v = Arr(spec.Get(key));
                    if (v == null || v.Count < 4) throw new InvalidOperationException($"{path}: contact spec '{key}' missing");
                    mat.SetVector(prop, new Vector4((float)Num(v[0]), (float)Num(v[1]), (float)Num(v[2]), (float)Num(v[3])));
                }
            mat.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Geometry + 499;
            EditorUtility.SetDirty(mat);
            return mat;
        }

        /// <summary>Parked-car glass (Kamion/World Car Glass): premultiplied tint + capped Fresnel reflection + UV0 dust.</summary>
        static Material CarGlassMaterial(string path, Color tintLinear, float rough, float opacity, float dust, float privacy, float reflect)
        {
            var shader = Shader.Find("Kamion/World Car Glass") ?? throw new InvalidOperationException("Kamion/World Car Glass not found (compile error?)");
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); }
            mat.shader = shader;
            mat.shaderKeywords = Array.Empty<string>();
            mat.enableInstancing = true;
            mat.SetColor("_Tint", new Color(tintLinear.r, tintLinear.g, tintLinear.b, 1f).gamma);
            mat.SetFloat("_Opacity", opacity);
            mat.SetFloat("_Smoothness", Mathf.Clamp01(1f - rough));
            mat.SetFloat("_Dust", dust);
            // ADR 0041 par. 9: every look constant is written (an existing material asset keeps its saved values, so a
            // changed shader default alone never reaches a reimported world)
            mat.SetFloat("_PrivacyOpacity", privacy);
            mat.SetFloat("_Reflect", reflect);
            mat.SetFloat("_ReflectMax", 0.55f);
            mat.SetFloat("_Horizon", 0.30f);
            mat.SetColor("_DustColor", new Color(0.36f, 0.34f, 0.30f, 1f));
            mat.SetOverrideTag("RenderType", "Transparent");
            mat.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;
            EditorUtility.SetDirty(mat);
            return mat;
        }

        /// <summary>URP Lit material (linear colour in, alpha clip with coverage-preserving mips, optional emission).</summary>
        public static Material LitMaterial(string path, Color linear, float rough, float metal, Texture2D tex, bool alphaClip, float cutoff, bool doubleSided, Color? emission)
        {
            var shader = Shader.Find("Universal Render Pipeline/Lit");
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); }
            mat.shader = shader;
            // Optional scanned materials can fall back at the same asset path on
            // reimport. Clear the scan-only state before restoring plain Lit.
            foreach (var keyword in new[] { "_NORMALMAP", "_OCCLUSIONMAP", "_METALLICSPECGLOSSMAP" }) mat.DisableKeyword(keyword);
            mat.SetTexture("_BumpMap", null);
            mat.SetTexture("_OcclusionMap", null);
            mat.SetTexture("_MetallicGlossMap", null);
            mat.enableInstancing = true;
            mat.SetColor("_BaseColor", new Color(linear.r, linear.g, linear.b, 1f).gamma);
            mat.SetTexture("_BaseMap", tex);
            mat.SetFloat("_Smoothness", Mathf.Clamp01(1f - rough));
            mat.SetFloat("_Metallic", metal);
            mat.SetFloat("_Cull", doubleSided ? 0f : 2f);
            mat.SetFloat("_AlphaClip", alphaClip ? 1f : 0f);
            mat.SetFloat("_Cutoff", cutoff);
            if (alphaClip) { mat.EnableKeyword("_ALPHATEST_ON"); mat.renderQueue = (int)UnityEngine.Rendering.RenderQueue.AlphaTest; }
            else { mat.DisableKeyword("_ALPHATEST_ON"); mat.renderQueue = -1; }
            if (mat.HasProperty("_AlphaToMask")) mat.SetFloat("_AlphaToMask", alphaClip ? 1f : 0f);
            if (emission.HasValue)
            {
                mat.EnableKeyword("_EMISSION");
                mat.SetColor("_EmissionColor", emission.Value);
                mat.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None;
            }
            else mat.DisableKeyword("_EMISSION");
            EditorUtility.SetDirty(mat);
            return mat;
        }

        // ------------------------------------------------------------------------------------------------- meshes
        static readonly string[] k_LowLayers = { "road", "bridge", "markings", "paved", "buildings_lod1", "furniture", "wires" };
        static readonly string[] k_HighLayers = { "road", "bridge", "markings", "paved", "buildings", "buildings_lod1", "furniture", "wires" };

        static void BakeVisual(Result r, Chunk ch, GlbReader g, string tier, GlbReader.MeshNode extraBuildingsLod0 = null)
        {
            string assetPath = $"{r.Dir}/Meshes/{tier}/chunk_{ch.Id}.asset";
            AssetDatabase.DeleteAsset(assetPath);
            var host = new Mesh { name = $"chunk_{ch.Id}_{tier}" };   // empty main asset; layers are sub-assets
            AssetDatabase.CreateAsset(host, assetPath);
            var layers = new List<Layer>();
            ch.Layers[tier] = layers;
            var terrainMat = new[] { r.Materials["terrain_grass"] };

            void Add(string node, Mesh mesh, Material[] mats)
            {
                AssetDatabase.AddObjectToAsset(mesh, host);
                layers.Add(new Layer { Node = node, Mesh = mesh, Materials = mats });
                string cat = node.StartsWith("terrain") ? "terrain" : node.StartsWith("buildings") ? "buildings" : node;
                r.MemoryBytes.TryGetValue($"{tier}/{cat}", out long v);
                r.MemoryBytes[$"{tier}/{cat}"] = v + WorldMeshBake.GpuBytes(mesh);
            }

            // Terrain: band (fine near roads) + coarser LODs.
            string fineNode = tier == "High" ? "terrain_lod0" : "terrain_lod1";
            float spacing = tier == "High" ? 1f : 2f;
            var fineGrid = g.Find(fineNode) ?? throw new InvalidDataException($"{ch.Id}: {fineNode} missing");
            var band = WorldMeshBake.TerrainBand($"{ch.Id}_terrain_band", Merge(fineGrid), spacing, ch.Min, ch.Max, 8,
                tier == "High" ? TerrainBandM : TerrainBandLowM, out float fine, tier == "High" ? 1 : 0);
            if (tier == "High") ch.FineFractionHigh = fine; else ch.FineFractionLow = fine;
            Add("terrain_band", band, terrainMat);
            foreach (var t in tier == "High" ? new[] { "terrain_lod1", "terrain_lod2", "terrain_lod3" } : new[] { "terrain_lod2", "terrain_lod3" })
            {
                var nd = g.Find(t);
                if (nd == null) continue;
                Add(t, WorldMeshBake.Compact($"{ch.Id}_{t}", nd.Primitives, new WorldMeshBake.Options { Colors = true }), terrainMat);
            }

            var layerNames = tier == "High" || extraBuildingsLod0 == null ? (tier == "High" ? k_HighLayers : k_LowLayers) : k_HighLayers;
            foreach (var layer in layerNames)
            {
                var nd = layer == "buildings" && tier != "High" ? extraBuildingsLod0 : g.Find(layer);
                if (nd == null || nd.Primitives.Count == 0) continue;
                var mats = new Material[nd.Primitives.Count];
                bool uv = false, uv1 = false, colors = false;
                for (int i = 0; i < mats.Length; i++)
                {
                    string id = nd.Primitives[i].Material;
                    if (id != null && r.Materials.TryGetValue(id, out var mm)) mats[i] = mm;
                    else Debug.LogWarning($"[IMPORT] {ch.Id}/{layer}: material '{id}' not in manifest");
                    if (id != null && r.MaterialDefs.TryGetValue(id, out var def))
                    {
                        if (def.Get("texture") != null) uv = true;
                        if (def.Get("window_grid") != null && nd.Primitives[i].Uv1 != null) uv1 = true;   // far facades (ADR 0015)
                        // PBR sets (ADR 0022): mesh UV in metres, road wear / decal data in TEXCOORD_1
                        WorldPbrMaterials.Channels(def, id, out bool p0, out bool p1, out bool pc);
                        uv |= p0 && nd.Primitives[i].Uv0 != null;
                        uv1 |= p1 && nd.Primitives[i].Uv1 != null;
                        colors |= pc && nd.Primitives[i].Colors != null;
                    }
                }
                if (layer == "wires") { uv = true; colors = true; }   // side / half width + tangent (Kamion/World Wire)
                Add(layer, WorldMeshBake.Compact($"{ch.Id}_{layer}", nd.Primitives, new WorldMeshBake.Options { Uv0 = uv, Uv1 = uv1, Colors = colors }), mats);
            }
        }

        static GlbReader.Primitive Merge(GlbReader.MeshNode node)
        {
            if (node.Primitives.Count == 1) return node.Primitives[0];
            var pos = new List<Vector3>();
            var col = new List<Color32>();
            foreach (var p in node.Primitives)
            {
                pos.AddRange(p.Positions);
                if (p.Colors != null) col.AddRange(p.Colors);
                else for (int i = 0; i < p.Positions.Length; i++) col.Add(new Color32(255, 0, 0, 0));
            }
            return new GlbReader.Primitive { Positions = pos.ToArray(), Colors = col.ToArray(), Indices = Array.Empty<int>() };
        }

        /// <summary>road_collision (one primitive per surface) → one mesh per surface; terrain fallback 2 m (corridor) / 4 m.</summary>
        static void BakeCollision(Result r, Chunk ch, GlbReader low)
        {
            string path = $"{r.Dir}/Collision/chunk_{ch.Id}_collision.asset";
            AssetDatabase.DeleteAsset(path);
            var host = new Mesh { name = ch.Id + "_collision" };
            AssetDatabase.CreateAsset(host, path);
            long bytes = 0;
            var nd = low.Find("road_collision");
            if (nd != null)
            {
                // Merge primitives of the same surface (several collision_* materials map to one surface kind).
                var bySurface = new Dictionary<string, (List<Vector3> p, List<int> t)>();
                foreach (var prim in nd.Primitives)
                {
                    string surface = prim.Material != null && r.MaterialSurface.TryGetValue(prim.Material, out var sf) && sf != null ? sf : "asphalt";
                    if (!bySurface.TryGetValue(surface, out var acc)) bySurface[surface] = acc = (new List<Vector3>(), new List<int>());
                    var (pos, tris) = WorldMeshBake.Compacted(prim.Positions, prim.Indices);
                    int b0 = acc.p.Count;
                    acc.p.AddRange(pos);
                    foreach (int i in tris) acc.t.Add(i + b0);
                }
                foreach (var kv in bySurface)
                {
                    var m = WorldMeshBake.PositionsOnly($"{ch.Id}_{kv.Key}", kv.Value.p.ToArray(), kv.Value.t.ToArray());
                    AssetDatabase.AddObjectToAsset(m, host);
                    ch.Collision.Add((m, kv.Key));
                    bytes += kv.Value.p.Count * 12L + kv.Value.t.Count * 4L;
                }
            }
            // Terrain fallback: in the route corridor the same band as the Low LOD0 terrain (2 m within 15 m of roads and
            // yards, 4 m elsewhere), elsewhere the 4 m grid. Roads and yards have their own collision on top.
            // APK budget (ADR 0012): the 4 m grid everywhere. Prebaked PhysX data doubles every collision byte, and the
            // 2 m corridor band alone was ~40 MB in the build. Off-road the wheels may sit a few cm off the 2 m visual
            // terrain; roads, yards, kerbs and verges next to roads have their own collision.
            Vector3[] tp = null; int[] tt = null;
            if (low.Find("terrain_lod2") is GlbReader.MeshNode terr)
            {
                var pos = new List<Vector3>();
                var tris = new List<int>();
                foreach (var prim in terr.Primitives)
                {
                    int b0 = pos.Count;
                    pos.AddRange(prim.Positions);
                    foreach (int i in prim.Indices) tris.Add(i + b0);
                }
                tp = pos.ToArray(); tt = tris.ToArray();
            }
            if (tp != null)
            {
                ch.TerrainCollision = WorldMeshBake.PositionsOnly($"{ch.Id}_terrain", tp, tt);
                AssetDatabase.AddObjectToAsset(ch.TerrainCollision, host);
                bytes += tp.Length * 12L + tt.Length * 4L;
            }
            r.MemoryBytes.TryGetValue("collision", out long v);
            r.MemoryBytes["collision"] = v + bytes;
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
                // Fences, guard rails, walls: vertical obstacles; the wheel model only sees them if it climbs one.
                case "steel": return SurfaceKind.Concrete;
                default:
                    Debug.LogWarning($"[IMPORT] unknown collision surface '{surface}' → DryAsphalt");
                    return SurfaceKind.DryAsphalt;
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

        // ------------------------------------------------------------------------------------------------- report
        /// <summary>Mesh memory per tier (GPU vertex+index bytes of non-readable meshes; collision = positions + indices
        /// before PhysX cooking) → log line + artifacts/world/&lt;region&gt;-import.json.</summary>
        static void WriteReport(Result r)
        {
            var ci = CultureInfo.InvariantCulture;
            var sb = new StringBuilder();
            sb.Append("{\n  \"region\": \"").Append(r.Region).Append("\",\n  \"generated\": \"").Append(DateTime.Now.ToString("s", ci)).Append("\",\n  \"bytes\": {\n");
            sb.Append(string.Join(",\n", r.MemoryBytes.OrderBy(k => k.Key).Select(k => $"    \"{k.Key}\": {k.Value}")));
            sb.Append("\n  },\n");
            float lowFine = r.Chunks.Average(c => c.FineFractionLow), highFine = r.Chunks.Average(c => c.FineFractionHigh);
            sb.Append($"  \"terrain_band_fine_fraction\": {{ \"Low\": {lowFine.ToString("F3", ci)}, \"High\": {highFine.ToString("F3", ci)} }},\n");
            var instSet = AssetDatabase.LoadAssetAtPath<WorldInstanceSet>($"{r.Dir}/Instances.asset");
            sb.Append($"  \"pbr_textures_gpu_bytes_astc\": {WorldPbrMaterials.EstimatedGpuBytes()},\n");
            sb.Append($"  \"instances\": {(instSet != null ? instSet.Count : 0)},\n  \"prop_colliders\": {(r.PropColliders != null ? r.PropColliders.Count : 0)}\n}}\n");
            string dir = Path.Combine(EditorTools.RepoRoot, "artifacts", "world");
            Directory.CreateDirectory(dir);
            File.WriteAllText(Path.Combine(dir, r.Region + "-import.json"), sb.ToString());
            foreach (var tier in r.TiersBuilt)
            {
                long render = r.MemoryBytes.Where(k => k.Key.StartsWith(tier + "/")).Sum(k => k.Value);
                long inst = r.MemoryBytes.TryGetValue("instances", out var iv) ? iv : 0;
                long col = r.MemoryBytes.TryGetValue("collision", out var cv) ? cv : 0;
                Debug.Log(string.Format(ci, "WORLD_MEMORY: tier={0} render_meshes={1:F1} MB instances={2:F1} MB collision_src={3:F1} MB total={4:F1} MB [{5}]",
                    tier, render / 1048576.0, inst / 1048576.0, col / 1048576.0, (render + inst + col) / 1048576.0,
                    string.Join(", ", r.MemoryBytes.Where(k => k.Key.StartsWith(tier + "/")).Select(k => $"{k.Key.Substring(tier.Length + 1)} {k.Value / 1048576.0:F1}"))));
            }
            Debug.Log(string.Format(ci, "WORLD_TERRAIN_BAND: fine fraction Low {0:P0} High {1:P0}", lowFine, highFine));
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
