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
        public static IEnumerable<string> Libraries()
        {
            var paths = new SortedSet<string>(StringComparer.Ordinal);
            foreach (var item in Items.Values.OfType<Dictionary<string, object>>())
            {
                if (item.Get("status") as string != "ready" || !Approved(Str(item.Get("prototype")).Substring(4).Replace('_', '-'), item)) continue;
                if (!(item.Get("models") is List<object> models)) continue;
                // Placement currently selects the first variant. Load one combined
                // LOD library instead of every individual LOD and unused variant.
                var model = models.OfType<Dictionary<string, object>>().FirstOrDefault();
                if (model == null) continue;
                string path = Resolve(model.Get("path"));
                if (path != null) paths.Add(path);
            }
            return paths;
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
            }
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
            else if (id.StartsWith("fab_") && Items.Get(id.Substring(4).Replace('_', '-')) is Dictionary<string, object> item && item.Get("status") as string == "ready" && Approved(id.Substring(4).Replace('_', '-'), item)) entry = item;
            if (!(entry?.Get("textures") is Dictionary<string, object> tiers)) return null;
            // Medium consumes the mobile tier as well; never silently promote Low to 1k.
            string tier = EditorTools.Arg("-materialTier", "Medium") == "High" ? "High" : "Low";
            return tiers.Get(tier) as Dictionary<string, object>;
        }
        public static bool Has(string id) => Maps(id) is Dictionary<string, object> m && Resolve(m.Get("basecolor")) != null;
        public static Material Create(RegionImporter.Result r, string id, string path)
        {
            var maps = Maps(id);
            if (maps == null || Resolve(maps.Get("basecolor")) == null) return null;
            if (s_Mats.TryGetValue(path, out var cached)) return cached;
            bool foliage = id.Contains("grass") || id.Contains("boxwood") || id.Contains("elderberry");
            bool decal = id.Contains("cover") || id.Contains("drain");
            var tex = Texture(r, id, "basecolor", Resolve(maps.Get("basecolor")), false, false, foliage || decal, decal);
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
