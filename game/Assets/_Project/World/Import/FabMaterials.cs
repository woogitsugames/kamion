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
    /// <summary>ADR 0084. Optional licensed inputs; every copied derivative stays under _Generated.</summary>
    public static class FabMaterials
    {
        static Dictionary<string, object> s_Items, s_Surfaces;
        static readonly Dictionary<string, Material> s_Mats = new Dictionary<string, Material>();
        static string Root => Path.Combine(EditorTools.RepoRoot, "art-source/world/megascans/_generated");
        public static void Reset()
        {
            s_Items = null; s_Surfaces = null; s_Mats.Clear();
            if (!File.Exists(Path.Combine(Root, "manifest.json")) || Environment.GetEnvironmentVariable("KAMION_DISABLE_FAB") == "1")
                Debug.LogWarning("[IMPORT] Optional Fab assets unavailable/disabled; existing world fallback retained");
        }
        static Dictionary<string, object> Read(string file, string key)
        {
            if (Environment.GetEnvironmentVariable("KAMION_DISABLE_FAB") == "1") return new Dictionary<string, object>();
            string path = Path.Combine(Root, file);
            if (!File.Exists(path)) return new Dictionary<string, object>();
            return Obj(Parse(File.ReadAllText(path))).Get(key) as Dictionary<string, object> ?? new Dictionary<string, object>();
        }
        static Dictionary<string, object> Items => s_Items ?? (s_Items = Read("manifest.json", "items"));
        // Confine all source-derived paths to the ignored directory, including malformed local manifests.
        static string Resolve(object value)
        {
            if (!(value is string relative)) return null;
            string p = Path.GetFullPath(Path.Combine(EditorTools.RepoRoot, relative));
            return p.StartsWith(Path.GetFullPath(Root) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase) && File.Exists(p) ? p : null;
        }
        public static string Library(string prototype)
        {
            foreach (var item in Items.Values.OfType<Dictionary<string, object>>())
            {
                if (item.Get("prototype") as string != prototype || item.Get("status") as string != "ready") continue;
                if (!Approved(prototype.Substring(4).Replace('_', '-'), item)) continue;
                if (!(item.Get("models") is List<object> models)) continue;
                var model = models.OfType<Dictionary<string, object>>().FirstOrDefault();
                if (model != null) return Resolve(model.Get("path"));
            }
            return null;
        }
        static bool Approved(string id, Dictionary<string, object> item)
        {
            var reviews = ReadReview();
            string pin = item.Get("source_sha256") as string;
            string sourcePath = Path.Combine(EditorTools.RepoRoot, "Data/SourceManifests/fab-megascans-2026-11-10.json");
            if (pin == null || pin.Length != 64 || !File.Exists(sourcePath)) return false;
            var sources = Arr(Obj(Parse(File.ReadAllText(sourcePath))).Get("items"));
            if (!sources.OfType<Dictionary<string, object>>().Any(src => src.Get("id") as string == id && src.Get("sha256") as string == pin)) return false;
            return reviews.Get(id) is Dictionary<string, object> review &&
                review.Get("status") as string == "approved" &&
                review.Get("source_sha256") as string == item.Get("source_sha256") as string;
        }
        static Dictionary<string, object> ReadReview()
        {
            string path = Path.Combine(EditorTools.RepoRoot, "tools/worldgen/fab/review.json");
            return File.Exists(path) ? Obj(Obj(Parse(File.ReadAllText(path))).Get("items")) : new Dictionary<string, object>();
        }
        static Dictionary<string, object> Maps(string id)
        {
            if (s_Surfaces == null)
            {
                s_Surfaces = Read("surfaces_manifest.json", "materials");
                foreach (var kv in Read("drainage_atlas_manifest.json", "materials")) s_Surfaces[kv.Key] = kv.Value;
                foreach (var kv in Read("grass_surface_manifest.json", "materials")) s_Surfaces[kv.Key] = kv.Value;
            }
            bool billboard = id.EndsWith("_billboard", StringComparison.Ordinal);
            string sourceId = billboard ? id.Substring(0, id.Length - "_billboard".Length) : id;
            Dictionary<string, object> entry = null;
            if (s_Surfaces.Get(id) is Dictionary<string, object> surface)
            {
                if (!(surface.Get("sources") is List<object> sources) || sources.Count == 0) return null;
                foreach (var src in sources.OfType<Dictionary<string, object>>())
                {
                    var source = new Dictionary<string, object> { ["source_sha256"] = src.Get("sha256") };
                    if (!Approved(Str(src.Get("id")), source)) return null;
                }
                entry = surface;
            }
            else if (sourceId.StartsWith("fab_") && Items.Get(sourceId.Substring(4).Replace('_', '-')) is Dictionary<string, object> item && item.Get("status") as string == "ready" && Approved(sourceId.Substring(4).Replace('_', '-'), item)) entry = item;
            if (!(entry?.Get(billboard ? "billboard_textures" : "textures") is Dictionary<string, object> tiers)) return null;
            // Medium consumes the mobile tier as well; never silently promote Low to 1k.
            string tier = EditorTools.Arg("-materialTier", "Medium") == "High" ? "High" : "Low";
            return tiers.Get(tier) as Dictionary<string, object>;
        }
        public static bool Has(string id) => Maps(id) is Dictionary<string, object> m && Resolve(m.Get("basecolor")) != null;
        /// <summary>Only the photographic base is replaced; the existing world PBR contract owns all other channels.</summary>
        public static bool IsBaseSurface(string id) => id == "curb_concrete" || id == "terrain_grass" || id == "verge_grass";

        static void SetSurfaceBase(Material material, Texture2D baseMap, string id)
        {
            material.SetTexture("_BaseMap", baseMap);
            var tileM = id == "terrain_grass" || id == "verge_grass" ? new Vector2(4f, 4f) : new Vector2(2f, 0.5f);
            var tile = material.GetVector("_Tile");
            tile.x = tileM.x; tile.y = tileM.y;
            material.SetVector("_Tile", tile);   // preserve macro/variation components z/w
        }

        public static bool ApplySurfaceBase(RegionImporter.Result r, string id, Material material)
        {
            var maps = Maps(id);
            if (maps == null || Resolve(maps.Get("basecolor")) == null) return false;
            var baseMap = Texture(r, id, "basecolor", Resolve(maps.Get("basecolor")), false, false, false, false);
            // Existing metric UVs, normal/mask/variation maps and macro lighting remain authoritative.
            // Curbs: two 1 m units; photographic grass: its explicit 4 x 4 m tile (WORKING_VALUE).
            SetSurfaceBase(material, baseMap, id);
            EditorUtility.SetDirty(material);
            return true;
        }
        public static Material Create(RegionImporter.Result r, string id, string path)
        {
            // These aliases must never fall through to generic URP Lit, even when their PBR set is absent.
            if (IsBaseSurface(id)) return null;
            var maps = Maps(id);
            if (maps == null || Resolve(maps.Get("basecolor")) == null) return null;
            if (s_Mats.TryGetValue(path, out var cached)) return cached;
            bool foliage = id.Contains("grass") || id.Contains("boxwood") || id.Contains("elderberry");
            bool decal = id.Contains("cover") || id.Contains("drain");
            var tex = Texture(r, id, "basecolor", Resolve(maps.Get("basecolor")), false, false, foliage || decal, decal);
            if (decal) return s_Mats[path] = Decal(r, id, path, maps, tex);
            var mat = RegionImporter.LitMaterial(path, Color.white, 0.85f, decal ? 0.65f : 0f, tex, foliage || decal, 0.5f, foliage, null);
            // Compact world meshes carry no tangent attribute. Never enable URP normal mapping
            // with a missing tangent basis; retain normal products for a later reviewed bake.
            mat.DisableKeyword("_NORMALMAP");
            var ao = Texture(r, id, "ao", Resolve(maps.Get("ao")), true, false, false, decal);
            if (ao != null) { mat.SetTexture("_OcclusionMap", ao); mat.EnableKeyword("_OCCLUSIONMAP"); mat.SetFloat("_OcclusionStrength", 1f); }
            // Generated processor packs roughness as URP smoothness in alpha of metallic_gloss.
            var mask = Texture(r, id, "metallic_gloss", Resolve(maps.Get("metallic_gloss")), true, false, false, decal);
            if (mask != null) { mat.SetTexture("_MetallicGlossMap", mask); mat.EnableKeyword("_METALLICSPECGLOSSMAP"); mat.SetFloat("_Smoothness", 1f); }
            EditorUtility.SetDirty(mat);
            s_Mats[path] = mat;
            return mat;
        }
        /// <summary>ADR 0131: road covers / drains are part of the carriageway, so they take the world lighting model
        /// (Kamion/World PBR: world GI, far shadow, dusk lamp pools, headlamps, Kamion fog). As URP Lit they missed the
        /// analytic lamp pools and headlamp cone that light the asphalt around them and read as black holes at night.
        /// Photographed albedo unchanged (tint 1); alpha-blended like the oil decals, whole-UV (_DecalCells 1).</summary>
        static Material Decal(RegionImporter.Result r, string id, string path, Dictionary<string, object> maps, Texture2D tex)
        {
            var shader = Shader.Find("Kamion/World PBR") ?? throw new InvalidOperationException("Kamion/World PBR missing");
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); }
            mat.shader = shader;
            mat.shaderKeywords = new[] { "_DECAL_ALPHA" };
            mat.enableInstancing = true;
            mat.SetTexture("_BaseMap", tex);
            // metallic_gloss: R metallic (0 on these scans), A smoothness - the World PBR _MaskMap A contract.
            var mask = Texture(r, id, "metallic_gloss", Resolve(maps.Get("metallic_gloss")), true, false, false, true);
            mat.SetTexture("_MaskMap", mask);
            mat.SetTexture("_NormalMap", null);
            mat.SetColor("_Tint", Color.white);
            mat.SetFloat("_AlbedoScale", 1f);
            mat.SetFloat("_SmoothnessScale", 1f);
            mat.SetFloat("_MetallicScale", 0f);
            mat.SetFloat("_DecalAlpha", 1f);
            mat.SetFloat("_DecalCells", 1f);
            mat.SetFloat("_OffsetFactor", -1f);
            mat.SetFloat("_OffsetUnits", -4f);
            mat.SetFloat("_ReceiveShadows", 1f);
            mat.SetFloat("_Cull", 2f);
            mat.SetFloat("_SrcBlend", (float)UnityEngine.Rendering.BlendMode.SrcAlpha);
            mat.SetFloat("_DstBlend", (float)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            mat.SetFloat("_ZWrite", 0f);
            mat.SetOverrideTag("RenderType", "Transparent");
            mat.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Geometry + 20;
            EditorUtility.SetDirty(mat);
            return mat;
        }
        static Texture2D Texture(RegionImporter.Result r, string id, string channel, string source, bool linear, bool normal, bool alpha, bool clamp)
        {
            if (source == null) return null;
            string dir = r.Dir + "/Textures/Fab/" + id;
            Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, dir));
            string dst = dir + "/" + channel + ".png";
            string full = Path.Combine(EditorTools.ProjectRoot, dst);
            if (!File.Exists(full) || !File.ReadAllBytes(full).SequenceEqual(File.ReadAllBytes(source)))
            { File.Copy(source, full, true); AssetDatabase.ImportAsset(dst, ImportAssetOptions.ForceSynchronousImport); }
            var ti = (TextureImporter)AssetImporter.GetAtPath(dst);
            ti.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
            ti.sRGBTexture = !linear;
            ti.mipmapEnabled = true;
            ti.streamingMipmaps = true;
            ti.isReadable = false;
            ti.alphaIsTransparency = alpha;
            ti.mipMapsPreserveCoverage = alpha;
            ti.alphaTestReferenceValue = 0.5f;
            ti.wrapMode = clamp ? TextureWrapMode.Clamp : TextureWrapMode.Repeat;
            ti.filterMode = FilterMode.Trilinear;
            ti.anisoLevel = 2;
            int size = EditorTools.Arg("-materialTier", "Medium") == "High" ? 1024 : 512;
            ti.maxTextureSize = size;
            ti.SetPlatformTextureSettings(new TextureImporterPlatformSettings { name = "Android", overridden = true, maxTextureSize = size, format = normal ? TextureImporterFormat.ASTC_5x5 : TextureImporterFormat.ASTC_6x6, compressionQuality = 50 });
            ti.SaveAndReimport();
            var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(dst);
            WorldPbrMaterials.Imported.Add(texture);
            return texture;
        }
    }
}
