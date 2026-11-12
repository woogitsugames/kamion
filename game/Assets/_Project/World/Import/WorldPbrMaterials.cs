using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using Game.Editor.Build;
using Game.Rendering.Editor;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using static Game.World.Import.MiniJson;

namespace Game.World.Import
{
    /// <summary>
    /// Generated PBR texture sets of the world (ADR 0022) → <c>Kamion/World PBR</c> materials.
    /// Source: art-source/world/materials/materials_spec.json + PNGs built by _src/build_all.py (not in git; the import
    /// script builds them when missing). A manifest material with <c>texture_set</c> naming a set of the spec gets a PBR
    /// material: "tiling_set" (calibrated albedo, world-planar or mesh UV), "modulation_set" (neutral map × manifest
    /// colour, mesh UV0 in metres), "decal_atlas" (oil). Layers: macro_variation (every material), asphalt_cracks_layer
    /// and asphalt_detail_photo (asphalt). Unknown sets fall back to the previous Kamion/World Surface path.
    /// Textures are copied into Assets/_Generated/World/&lt;id&gt;/Textures/PBR/ (gitignored) with ASTC per the spec
    /// (tier -materialTier, default Medium: 1024 px for 4 m tiles = 3.9 mm/texel).
    /// </summary>
    public static class WorldPbrMaterials
    {
        public const string ShaderName = "Kamion/World PBR";
        static Dictionary<string, object> s_Spec;
        static string s_Tier;
        static readonly Dictionary<string, Texture2D> s_Tex = new Dictionary<string, Texture2D>();
        public static readonly List<Texture> Imported = new List<Texture>();

        static string SpecPath => Path.Combine(EditorTools.RepoRoot, "art-source", "world", "materials", "materials_spec.json");
        static string SetRoot => Path.Combine(EditorTools.RepoRoot, "art-source", "world", "materials");

        public static void Reset()
        {
            s_Spec = null;
            s_Tex.Clear();
            Imported.Clear();
            s_Tier = EditorTools.Arg("-materialTier", "Medium");
        }

        /// <summary>ADR0086: all authored tint values are linear multipliers. ShaderLab Color properties
        /// are decoded from sRGB on GPU upload even with SetVector; encode once for storage so the shader
        /// receives the original linear value. Verified by WorldPbrTintProbe, including HDR ratios > 1.</summary>
        public static void SetLinearTint(Material material, Vector3 linear)
        {
            material.SetColor("_Tint", new Color(linear.x, linear.y, linear.z, 1f).gamma);
        }

        /// <summary>ADR0089: pearl ratios are linear HDR multipliers. The Color property has the same
        /// upload decode as Tint; actual GPU readback showed raw 3.2 becoming 12.922 instead of 3.2.</summary>
        public static void SetLinearPearlTint(Material material, Vector3 linear)
        {
            material.SetColor("_PearlTint", new Color(linear.x, linear.y, linear.z, 1f).gamma);
        }

        static Dictionary<string, object> Spec()
        {
            if (s_Spec == null)
            {
                if (s_Tier == null) s_Tier = EditorTools.Arg("-materialTier", "Medium");
                s_Spec = File.Exists(SpecPath) ? Obj(Obj(Parse(File.ReadAllText(SpecPath))).Get("sets")) : new Dictionary<string, object>();
            }
            return s_Spec;
        }

        static Dictionary<string, object> Set(string name) => name != null && Spec().Get(name) is Dictionary<string, object> s ? s : null;

        /// <summary>True when the manifest material has a generated set whose files exist for the tier.</summary>
        public static bool Has(Dictionary<string, object> def, string id)
        {
            if (id == "decal_tyre") return true;   // procedural strip profile, no set
            if (def.Get("procedural") as string == "grate") return true;   // gully grates (drain_grate)
            if (Stripes(def) != null) return true;                         // painted bands (boom, hazard)
            var s = Set(def.Get("texture_set") as string);
            return s != null && FilesFor(s) != null;
        }

        // ADR 0122: static cab paint is opt-in data, never a blanket extension to yard props.
        static bool YardPaint(Dictionary<string, object> def, string id) =>
            id != null && id.StartsWith("tractor_paint_", StringComparison.Ordinal)
            && def.Get("yard_paint") is bool enabled && enabled
            && def.Get("texture_set") as string == "car_grime_clean"
            && def.Get("paint") is List<object> paint && paint.Count >= 4;

        /// <summary>Vertex channels the material needs (mesh baking keeps TEXCOORD_0 / TEXCOORD_1 only where read).</summary>
        public static void Channels(Dictionary<string, object> def, string id, out bool uv0, out bool uv1, out bool colors)
        {
            uv0 = uv1 = colors = false;
            // ADR0120: the existing World Surface material reads a byte-stable board marker, not UVs.
            if (id == "concrete_plinth" && def.Get("furniture_plinth_detail") is Dictionary<string, object>) { colors = true; return; }
            if (def.Get("furniture_sign_face") is string) { uv0 = true; return; }
            if (id != null && id.StartsWith("fab_", StringComparison.Ordinal) && FabMaterials.Has(id)) { uv0 = true; return; }
            if (!Has(def, id)) return;
            var s = Set(def.Get("texture_set") as string);
            string kind = s != null ? Str(s.Get("kind")) : "decal";
            string uv = s != null ? Str(s.Get("uv")) ?? "" : "";
            if ((kind == "modulation_set" || uv.StartsWith("mesh_uv0")) && def.Get("uv") as string != "planar") uv0 = true;
            if (def.Get("uv1") as string == "along_m") uv1 = true;
            if ((id.StartsWith("car_paint_") && def.Get("paint") is List<object>) || YardPaint(def, id)) uv1 = true; // source deposition payload
            if (id == "road_asphalt" || id == "road_asphalt_new") uv1 = true;           // _ROADWEAR
            if ((id.StartsWith("hall_wall") || Runoff(def) || (def.Get("runoff") is bool ro && ro)) && Set("parapet_runoff") != null) uv1 = true;   // _RUNOFF (wall-top space): 0071 `weather` + 0081 `runoff`
            if (id == "decal_patch" || id == "decal_oil" || id == "decal_tyre") { uv0 = true; uv1 = true; }
            if (def.Get("paint") is Dictionary<string, object>) uv1 = true;              // _DECAL_PAINT wear data (ADR 0049)
            if (def.Get("procedural") as string == "grate" || Stripes(def) != null) uv0 = true;
            if (id == "terrain_grass") colors = true;
        }

        /// <summary>ADR 0071 r11: manifest "weather": true = wall material of an authored asset that carries the splash
        /// zone (UV0.y = metres above ground) and run-off space (TEXCOORD_1) of the generated hall walls.</summary>
        static bool Runoff(Dictionary<string, object> def) => def.Get("weather") is bool b && b;

        /// <summary>Procedural stripe sets: (direction in UV metres, period m, colour A, colour B), linear colours.</summary>
        static (Vector2 dir, float period, Color a, Color b)? Stripes(Dictionary<string, object> def)
        {
            switch (def.Get("texture_set") as string)
            {
                // boom arm: 0.5 m red / white bands along the arm (UV u = metres, life_props.barrier_arm)
                case "boom_red_white": return (new Vector2(1f, 0f), 1.0f, new Color(0.45f, 0.025f, 0.02f), new Color(0.68f, 0.68f, 0.66f));
                // dock leveller edges: yellow / black 45 deg, 0.1 m bands (WORKING_VALUE)
                case "hazard_stripes_45deg": return (new Vector2(0.7071f, 0.7071f), 0.2f, new Color(0.55f, 0.40f, 0.03f), new Color(0.02f, 0.02f, 0.02f));
                // ADR 0092: condenser grille of a transport refrigeration unit - horizontal slats, 60 mm pitch, dark
                // gaps (UV v = metres up, life_props.trailer; WORKING_VALUE)
                case "louvre_slats": return (new Vector2(0f, 1f), 0.06f, new Color(0.012f, 0.012f, 0.012f), new Color(0.085f, 0.088f, 0.09f));
            }
            return null;
        }

        static Dictionary<string, object> FilesFor(Dictionary<string, object> set)
        {
            if (!(set.Get("files") is Dictionary<string, object> f)) return null;
            foreach (var t in new[] { s_Tier ?? "Medium", "Medium", "High", "Low" })
                if (f.Get(t) is Dictionary<string, object> info)
                {
                    string dir = Path.Combine(SetRoot, Str(info.Get("dir")));
                    if (Arr(info.Get("files")).All(x => File.Exists(Path.Combine(dir, Str(x))))) return info;
                }
            return null;
        }

        /// <summary>PBR material for a manifest material, or null when its set is missing (caller falls back).</summary>
        public static Material Create(RegionImporter.Result r, string id, Dictionary<string, object> def, string path)
        {
            if (id == "plate_back" && def.Get("furniture_sign_fronts") is Dictionary<string, object> fronts)
                FurnitureSignFronts(r, fronts);
            if (def.Get("furniture_sign_face") is string face) return FurnitureSign(r, id, def, face, path);
            // ADR0120 additive, data-gated route: retain the original World Surface factory and material identity.
            if (id == "concrete_plinth")
            {
                if (def.Get("furniture_plinth_detail") is Dictionary<string, object> detail)
                    return FurniturePlinth(r, def, detail, path);
                var previous = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (previous != null && previous.IsKeywordEnabled("_FURNITURE_PLINTH"))
                {
                    previous.DisableKeyword("_FURNITURE_PLINTH");
                    previous.SetTexture("_FurnitureMap", null);
                    EditorUtility.SetDirty(previous);
                }
            }
            if (!Has(def, id)) return null;
            var shader = Shader.Find(ShaderName) ?? throw new InvalidOperationException(ShaderName + " not found (compile error?)");
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); }
            mat.shader = shader;
            mat.shaderKeywords = Array.Empty<string>();
            mat.enableInstancing = true;
            var c = Arr(def.Get("color"));
            var col = new Vector3((float)Num(c[0]), (float)Num(c[1]), (float)Num(c[2]));
            string setName = def.Get("texture_set") as string;
            var set = Set(setName);
            string kind = set != null ? Str(set.Get("kind")) : "decal";

            // textures
            var macro = Layer(r, "macro_variation", "T_macro_variation.png", false, false);
            mat.SetTexture("_MacroMap", macro);
            Vector4 tile = new Vector4(4, 4, 16, 1);
            if (set != null)
            {
                var info = FilesFor(set);
                string dir = Str(info.Get("dir"));
                foreach (var fo in Arr(info.Get("files")))
                {
                    string f = Str(fo);
                    if (f.Contains("_late_autumn")) continue;
                    string slot = f.EndsWith("_BaseColor.png") ? "_BaseMap" : f.EndsWith("_Normal.png") ? "_NormalMap" :
                        f.EndsWith("_MaskMap.png") ? "_MaskMap" : f.EndsWith("_Var.png") ? "_VarMap" : null;
                    if (slot == null) continue;
                    mat.SetTexture(slot, Import(r, setName, dir, f, info, slot));
                }
                var tm = Arr(set.Get("tile_m"));
                tile.x = (float)Num(tm[0]); tile.y = (float)Num(tm[1]);
            }
            // ADR 0067: `tile` was never written to the material (every set is sampled at the shader default 4 x 4 m,
            // whatever tile_m says). Strip atlases (non-square, UV0 in atlas metres) need the real size; the other sets
            // keep the 4 m look they were reviewed with until the lead decides (see ADR 0067, "znane").
            // ADR 0071 r11 (review 2026-11-10, P0 "kostka 0,4-0,5 m"): sets segmented into physical elements (CC0 scans of
            // behaton / 20x10 paving / 35 cm slabs, `source.elements_per_tile`) are 1.9-3.1 m of real surface; sampled at
            // the 4 m default every block came out 1.3-2.1x too large (behaton 0.42 m instead of 0.20 m). Their element
            // size is a scale cue, so they always get their real tile.
            bool elementScan = set != null && set.Get("source") is Dictionary<string, object> esrc && esrc.Get("elements_per_tile") != null;
            // ADR 0070: authored atlases ("atlas": true in materials_spec.json: viaduct, fire station) address the atlas in
            // metres through mesh UV0, so they also need the set's own tile size.
            bool isAtlasSet = set != null && set.Get("atlas") is bool isAtlas && isAtlas;
            if ((def.Get("set_tile") is bool stl && stl) || elementScan || isAtlasSet) mat.SetVector("_Tile", tile);

            float scale = 1f;
            Vector3 tint = Vector3.one;
            if (kind == "modulation_set")
            {
                scale = 2f; tint = col;
                // ADR0081's tint_linear flag is accepted as legacy metadata, but conversion now applies
                // to every set/path. Already-correct building colours retain their exact GPU values.
            }
            else if (set != null && set.Get("albedo") is Dictionary<string, object> alb && alb.Get("mean_rgb_linear") is List<object> mean)
            {
                // calibrated set: grey tint = manifest luminance / set mean luminance (1 when the generator uses the set
                // mean); the hue always comes from the set (a per-channel ratio turned the grass magenta)
                float lm = 0.2126f * (float)Num(mean[0]) + 0.7152f * (float)Num(mean[1]) + 0.0722f * (float)Num(mean[2]);
                float lc = 0.2126f * col.x + 0.7152f * col.y + 0.0722f * col.z;
                float t = Mathf.Clamp(lc / Mathf.Max(lm, 1e-3f), 0.4f, 2.5f);
                tint = new Vector3(t, t, t);
            }
            SetLinearTint(mat, tint);
            mat.SetFloat("_AlbedoScale", scale);
            mat.SetFloat("_NormalStrength", 1f);
            mat.SetFloat("_SmoothnessScale", 1f);
            // Parked-car paint (ADR 0073): the car_grime set carries clean paint at roughness 0.32 (smoothness 0.68) plus
            // film / dust; the manifest "rough" of the colour is the CLEAN clear coat, so scale the set to it. Before, the
            // manifest value was ignored and every paint rendered at 0.59 mean smoothness ("primer", REVIEW r8).
            if ((id.StartsWith("car_paint_") || YardPaint(def, id)) && def.Get("rough") != null)
                mat.SetFloat("_SmoothnessScale", Mathf.Clamp((1f - (float)Num(def.Get("rough"))) / 0.68f, 0.5f, 1.4f));
            // ADR 0092 (review s9 par. 4, "firanka odbija jak polerowana blacha"): the curtain set carried smoothness 0.36
            // whatever the manifest said; in the shade of the hall the grazing-angle environment term (smoothness + F0)
            // then outshone the dark PVC and drew a horizon line across the tarpaulin. The manifest "rough" of a
            // curtain is the mean roughness of matt PVC-coated fabric: the set is scaled to it. Metallic stays 0.
            if (id.StartsWith("trailer_curtain_") && def.Get("rough") != null && set != null && FilesFor(set) is Dictionary<string, object> cinfo
                && cinfo.Get("smoothness_mean") != null)
                mat.SetFloat("_SmoothnessScale", Mathf.Clamp((1f - (float)Num(def.Get("rough"))) / Mathf.Max(0.05f, (float)Num(cinfo.Get("smoothness_mean"))), 0.2f, 1.2f));
            mat.SetFloat("_MetallicScale", 0f);
            // Parked-car paint r10 (ADR 0078): clear coat over a base coat. Manifest "paint": [base metal, flake tilt,
            // pearl, base-coat roughness] (+ optional "pearl_tint"); solid colours have metal 0 and no flake.
            if ((id.StartsWith("car_paint_") || YardPaint(def, id)) && def.Get("paint") is List<object> cp && cp.Count >= 4)
            {
                mat.EnableKeyword("_CARPAINT");
                mat.SetVector("_CarPaint", new Vector4((float)Num(cp[0]), (float)Num(cp[1]), (float)Num(cp[2]), (float)Num(cp[3])));
                mat.SetVector("_CarFlake", new Vector4(400f, 1f, 0.08f, YardPaint(def, id) ? 2f : 1f)); // w: 1 legacy car, 2 static cab; existing paint pass
                var pt = def.Get("pearl_tint") as List<object>;
                SetLinearPearlTint(mat, pt != null && pt.Count >= 3
                    ? new Vector3((float)Num(pt[0]), (float)Num(pt[1]), (float)Num(pt[2])) : Vector3.one);
            }
            mat.SetFloat("_MacroSize", 64f);
            mat.SetFloat("_MacroStrength", kind == "modulation_set" ? 0.06f : 0.16f);
            mat.SetFloat("_MacroWear", kind == "modulation_set" ? 0.05f : 0.2f);
            mat.SetFloat("_ElementJitter", 0f);
            mat.SetFloat("_ReceiveShadows", 1f);
            SetBlend(mat, false);
            mat.SetFloat("_OffsetFactor", 0f);
            mat.SetFloat("_OffsetUnits", 0f);
            mat.SetFloat("_Cull", (float)CullMode.Back);
            mat.renderQueue = -1;

            string uv = set != null ? Str(set.Get("uv")) ?? "" : "";
            if ((kind == "modulation_set" || uv.StartsWith("mesh_uv0")) && def.Get("uv") as string != "planar") mat.EnableKeyword("_UV_MESH0");
            if (def.Get("uv1") as string == "along_m") mat.EnableKeyword("_UV_MESH1");
            if (setName == "behaton_i_grey" || setName == "paving_20x10_grey") { mat.SetFloat("_ElementJitter", 0.12f); mat.SetFloat("_ElementSize", 0.17f); }
            if (setName == "concrete_cast_5m_joints" || setName == "concrete_slab_3x1.5") { mat.SetFloat("_ElementJitter", 0.07f); mat.SetFloat("_ElementSize", 2.0f); }
            if (setName == "large_panel_joints" || setName == "brick") { mat.SetFloat("_ElementJitter", 0.05f); mat.SetFloat("_ElementSize", setName == "brick" ? 0.25f : 2.8f); }
            // CC0 scan sets (ADR 0063): the photo already carries per-element tone; jitter only where the scan was
            // segmented into elements (Var.G ids). A scan without ids would get one tone step per tile (visible grid).
            if (set != null && set.Get("source") is Dictionary<string, object> src && !Str(src.Get("mode") ?? "").StartsWith("hybrid")
                && src.Get("elements_per_tile") == null)
                mat.SetFloat("_ElementJitter", 0f);
            else if (set != null && set.Get("source") is Dictionary<string, object> src2 && src2.Get("elements_per_tile") != null)
                mat.SetFloat("_ElementJitter", mat.GetFloat("_ElementJitter") * 0.5f);   // scan tone + half the jitter

            // ADR0118: explicit opt-in data. Reset on every import so removing a block is idempotent.
            mat.SetVector("_AsphaltWear", new Vector4(1f, 0f, 0f, 0f));
            if (def.Get("asphalt_wear") is Dictionary<string, object> aw)
            {
                float A(string key, float fallback) => aw.Get(key) != null ? (float)Num(aw.Get(key)) : fallback;
                mat.SetVector("_AsphaltWear", new Vector4(A("tone", 1f), A("wheel_darkening", 0f),
                    A("low_cracks", 0f), A("low_photo_detail", 0f)));
                if (def.Get("paint") is Dictionary<string, object> underlayDef
                    && underlayDef.Get("asphalt_underlay") is bool underlayEnabled && underlayEnabled)
                {
                    mat.EnableKeyword("_ROADWEAR");
                    mat.SetFloat("_WheelPolish", A("wheel_polish", 0.5f));
                    mat.SetFloat("_DripBand", A("drip_band", 0f));
                }
            }
            mat.SetVector("_PatchSeam", new Vector4(0f, 0f, 1f, 1f));
            if (id == "decal_patch" && def.Get("asphalt_patch_seam") is Dictionary<string, object> ps)
            {
                float P(string key, float fallback) => ps.Get(key) != null ? (float)Num(ps.Get(key)) : fallback;
                mat.SetVector("_PatchSeam", new Vector4(P("width_m", 0f), P("darkening", 0f),
                    P("fresh_tone", 1f), P("aged_tone", 1f)));
            }
            bool asphalt = setName == "asphalt_worn" || setName == "asphalt_sma_fresh" || setName == "asphalt_patch";
            if (id == "road_asphalt" || id == "road_asphalt_new")
            {
                mat.EnableKeyword("_ROADWEAR");
                mat.SetFloat("_WheelPolish", id == "road_asphalt" ? 0.6f : 0.25f);
                mat.SetFloat("_GutterDirt", id == "road_asphalt" ? 0.55f : 0.3f);
                // ADR 0060: oil / soot band between the wheel paths of aged roads (resurfaced SMA: barely)
                mat.SetFloat("_DripBand", id == "road_asphalt" ? 0.22f : 0.06f);
            }
            // ADR 0060 (review r7 N-2): dirty joints and damp / oily hollows on yards and footways (not on carriageways:
            // their wear comes from _ROADWEAR). WORKING_VALUE, judged against the CC0 Bieżeństwa / Andersa photos.
            if (setName == "behaton_i_grey" || setName == "paving_20x10_grey" || setName == "concrete_cast_5m_joints"
                || setName == "concrete_slab_3x1.5" || (setName == "asphalt_worn" && id != "road_asphalt"))
            {
                bool blocks = setName == "behaton_i_grey" || setName == "paving_20x10_grey";
                mat.EnableKeyword("_GRIME");
                // x damp darkening, y macro-pool threshold (~0.62 = 16 % of the area), z joint dirt, w damp gloss
                mat.SetVector("_Grime", new Vector4(blocks ? 0.42f : 0.38f, 0.62f, blocks ? 0.45f : 0.3f, 0.5f));
            }
            // ADR 0071 r11: manifest "cracks": strength = the 16 m crack layer on a non-asphalt set (worn dock apron)
            if (setName == "asphalt_worn" || def.Get("cracks") != null)
            {
                var cm = Layer(r, "asphalt_cracks_layer", "T_asphalt_cracks_layer_Mask.png", false, false);
                var cn = Layer(r, "asphalt_cracks_layer", "T_asphalt_cracks_layer_Normal.png", false, true);
                if (cm != null && cn != null)
                {
                    mat.SetTexture("_CrackMap", cm); mat.SetTexture("_CrackNormal", cn);
                    mat.EnableKeyword("_CRACKS");
                    mat.SetFloat("_CrackStrength", def.Get("cracks") != null ? (float)Num(def.Get("cracks")) : id == "yard_asphalt" ? 0.9f : 0.75f);
                }
            }
            if (asphalt)
            {
                var da = Layer(r, "asphalt_detail_photo", "T_asphalt_detail_photo_DetailAlbedo.png", true, false);
                var dn = Layer(r, "asphalt_detail_photo", "T_asphalt_detail_photo_DetailNormal.png", false, true);
                if (da != null && dn != null)
                {
                    mat.SetTexture("_DetailAlbedo", da); mat.SetTexture("_DetailNormal", dn);
                    mat.EnableKeyword("_PHOTO_DETAIL");
                    mat.SetFloat("_DetailFade", 25f);
                }
            }
            if (id == "terrain_grass") { mat.EnableKeyword("_GROUNDMASKS"); mat.SetFloat("_GroundTint", 1f); }
            if (id == "terrain_grass" || id == "verge_grass" || id == "plot_lawn")   // plot_lawn: ADR 0114
            {
                // Review r5 W-N3: macro-masked bare soil + rotated second sample (ADR 0042). Refill = linear mean of
                // the grass_verge texels without bare soil (Var.B < 0.1), measured from the Medium BaseColor.
                mat.EnableKeyword("_GRASS_DETILE");
                // D38 (ADR 0060): grass chroma x1.45 in the set -> refill re-measured (Medium, Var.B < 0.1)
                mat.SetVector("_GrassFill", new Vector4(0.072f, 0.114f, 0.011f, 1f));   // linear, no sRGB conversion
            }
            // ADR 0091: manifest "splash_h" (m) puts the splash zone on any wall material (plinths) with its own height
            bool splashH = def.Get("splash_h") != null;
            if (id.StartsWith("hall_wall") || id.StartsWith("plaster_") || id == "panel_concrete" || id == "brick_red" || id == "hall_plinth" || Runoff(def) || splashH)
            {
                mat.EnableKeyword("_SPLASH");
                mat.SetFloat("_SplashHeight", splashH ? (float)Num(def.Get("splash_h")) : id == "hall_plinth" ? 0.35f : 0.6f);
            }
            if (Runoff(def)) mat.SetFloat("_MacroStrength", 0.12f);   // panel-to-panel tone drift of a 600 m facade (0071)
            // ADR 0091: manifest "macro": [size m, strength] overrides the macro tone drift (brick: firing lots)
            if (def.Get("macro") is List<object> mc && mc.Count >= 2)
            {
                mat.SetFloat("_MacroSize", (float)Num(mc[0]));
                mat.SetFloat("_MacroStrength", (float)Num(mc[1]));
            }
            // ADR 0092: manifest "panel_m": [length, course] (metres of the texture set) = the drift above is quantised to
            // the cladding module instead of a smooth noise. The set is sampled at `tile` (4 m unless _Tile is written),
            // so the course on the wall is the set's course x applied tile / set tile.
            if (def.Get("panel_m") is List<object> pm && pm.Count >= 2 && set != null)
            {
                var tmS = Arr(set.Get("tile_m"));
                Vector4 applied = mat.GetVector("_Tile");
                // only the course height follows the texture (its shadow-gap joints); the panel length is physical
                float ky = applied.y / Mathf.Max(1e-3f, (float)Num(tmS[1]));
                mat.EnableKeyword("_PANELTONE");
                mat.SetVector("_PanelTone", new Vector4((float)Num(pm[0]), (float)Num(pm[1]) * ky, 0.35f, 0.3f));
            }
            bool plasterRunoff = def.Get("runoff") is bool pr && pr;   // ADR 0081: plaster / panel walls of flat-roofed blocks and offices
            if (id.StartsWith("hall_wall") || Runoff(def) || plasterRunoff)
            {
                // parapet run-off streaks (zacieki pod attyką): TEXCOORD_1 = (u m, 1 + metres below the fascia / length
                // scale) from buildings_mesh.py hall walls; one RGB sample on all tiers
                var ro = Layer(r, "parapet_runoff", "T_parapet_runoff.png", false, false);
                if (ro != null)
                {
                    mat.SetTexture("_RunoffMap", ro);
                    mat.EnableKeyword("_RUNOFF");
                    // light cladding shows run-off most; dark graphite / accent sheet hides soot (rust still shows)
                    float lum = 0.2126f * col.x + 0.7152f * col.y + 0.0722f * col.z;
                    // mineral render soaks the dirt in: softer than on coated sheet (WORKING_VALUE, judged on the r10 renders)
                    mat.SetFloat("_RunoffStrength", Mathf.Lerp(0.55f, 0.9f, Mathf.InverseLerp(0.08f, 0.5f, lum)) * (plasterRunoff ? 0.6f : 1f));
                }
            }

            if (Stripes(def) is var st && st != null)
            {
                mat.EnableKeyword("_STRIPES");
                mat.EnableKeyword("_UV_MESH0");
                mat.SetVector("_Stripe", new Vector4(st.Value.dir.x, st.Value.dir.y, st.Value.period, 0f));
                mat.SetVector("_StripeA", (Vector4)st.Value.a);
                mat.SetVector("_StripeB", (Vector4)st.Value.b);
            }
            if (setName == "behaton_i_grey" || setName == "paving_20x10_grey" || setName == "concrete_cast_5m_joints" || setName == "concrete_slab_3x1.5")
            {
                // yards and footways: soiling and wear patches stronger than on carriageways (r4 W-H1: "too clean")
                mat.SetFloat("_MacroStrength", 0.2f);
                mat.SetFloat("_MacroWear", 0.38f);
            }

            // decals (markings layer): polygon offset like the markings, later queue
            if (def.Get("decal") is bool dc && dc)
            {
                mat.SetFloat("_OffsetFactor", -1f);
                mat.SetFloat("_OffsetUnits", -4f);
                mat.SetFloat("_ReceiveShadows", 1f);
                mat.renderQueue = (int)RenderQueue.Geometry + 10;
                if (id == "decal_patch")
                {
                    mat.EnableKeyword("_DECAL_PATCH");
                    var worn = Set("asphalt_worn");
                    float ratio = 2.0f;
                    if (worn != null && set != null && worn.Get("albedo") is Dictionary<string, object> wa && set.Get("albedo") is Dictionary<string, object> pa)
                        ratio = (float)(Num(wa.Get("mean_lum_linear")) / Math.Max(1e-3, Num(pa.Get("mean_lum_linear"))));
                    mat.SetFloat("_AgeTint", ratio);
                }
                else if (id == "decal_oil")
                {
                    mat.EnableKeyword("_DECAL_ALPHA");
                    mat.SetFloat("_DecalAlpha", 0.85f);
                    SetLinearTint(mat, Vector3.one);
                    SetBlend(mat, true);
                    mat.renderQueue = (int)RenderQueue.Geometry + 20;
                }
                else if (def.Get("procedural") as string == "grate")
                {
                    mat.EnableKeyword("_DECAL_GRATE");
                    mat.renderQueue = (int)RenderQueue.Geometry + 15;
                }
                else if (def.Get("paint") is Dictionary<string, object> pd)
                {
                    // road markings (ADR 0049): paint film over the road's own asphalt set (calibrated, tint 1)
                    mat.EnableKeyword("_DECAL_PAINT");
                    SetLinearTint(mat, Vector3.one);
                    float rough = def.Get("rough") != null ? (float)Num(def.Get("rough")) : 0.65f;
                    mat.SetVector("_PaintColor", new Vector4(col.x, col.y, col.z, Mathf.Clamp01(1f - rough)));
                    float P(string k, float d) => pd.Get(k) != null ? (float)Num(pd.Get(k)) : d;
                    // ADR0099 WORKING_VALUE: narrower contact wear remains legible on P8/P10.
                    // Always calibrate fresh metadata, never the existing material (reimports must be idempotent).
                    float wheelWear = P("wheel_wear", 0.85f); // ADR0118: strength belongs to material data
                    mat.SetVector("_PaintWear", new Vector4(wheelWear, P("age_wear", 0.25f), P("dirt", 0.3f), P("line_w_m", 0.12f)));
                    mat.SetVector("_PaintFreshWear", new Vector4(P("fresh_wheel_scale", 1f), P("fresh_age_scale", 1f),
                        P("fresh_dirt_scale", 1f), P("fresh_underlay_scale", 1f)));
                }
                else if (id == "decal_tyre")
                {
                    mat.EnableKeyword("_DECAL_TYRE");
                    SetLinearTint(mat, col);
                    mat.SetFloat("_DecalAlpha", 0.45f);
                    SetBlend(mat, true);
                    mat.renderQueue = (int)RenderQueue.Geometry + 20;
                }
            }
            EditorUtility.SetDirty(mat);
            return mat;
        }

        static void SetBlend(Material mat, bool alpha)
        {
            mat.SetFloat("_SrcBlend", alpha ? (float)BlendMode.SrcAlpha : (float)BlendMode.One);
            mat.SetFloat("_DstBlend", alpha ? (float)BlendMode.OneMinusSrcAlpha : (float)BlendMode.Zero);
            mat.SetFloat("_ZWrite", alpha ? 0f : 1f);
            mat.SetOverrideTag("RenderType", alpha ? "Transparent" : "Opaque");
        }

        static Texture2D Layer(RegionImporter.Result r, string setName, string file, bool srgb, bool normal)
        {
            var set = Set(setName);
            if (set == null) return null;
            var info = FilesFor(set);
            if (info == null) return null;
            string slot = normal ? "_NormalMap" : srgb ? "_BaseMap" : "_MaskMap";
            return Import(r, setName, Str(info.Get("dir")), file, info, slot);
        }

        /// <summary>Copies one PNG of a set into the generated folder and applies the import settings of its slot.</summary>
        static Texture2D Import(RegionImporter.Result r, string setName, string dir, string file, Dictionary<string, object> info, string slot)
        {
            string key = setName + "/" + file;
            if (s_Tex.TryGetValue(key, out var cached)) return cached;
            string src = Path.Combine(SetRoot, dir, file);
            if (!File.Exists(src)) return null;
            string dstDir = $"{r.Dir}/Textures/PBR/{setName}";
            Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, dstDir));
            string dst = $"{dstDir}/{file}";
            string full = Path.Combine(EditorTools.ProjectRoot, dst);
            bool copy = !File.Exists(full) || new FileInfo(full).Length != new FileInfo(src).Length || !File.ReadAllBytes(full).SequenceEqual(File.ReadAllBytes(src));
            if (copy)
            {
                File.Copy(src, full, true);
                AssetDatabase.ImportAsset(dst, ImportAssetOptions.ForceSynchronousImport);
            }
            var ti = (TextureImporter)AssetImporter.GetAtPath(dst);
            bool normal = slot == "_NormalMap" || file.Contains("Normal");
            bool srgb = slot == "_BaseMap" && !file.Contains("_Mask") && !file.Contains("macro");
            bool var = file.EndsWith("_Var.png");
            bool hasAlpha = file.Contains("oil_stain") && file.EndsWith("_BaseColor.png") || file.EndsWith("_MaskMap.png") || var || file.Contains("cracks_layer_Mask") || file.Contains("macro");
            var res = Arr(info.Get("res"));
            int maxRes = Mathf.NextPowerOfTwo(Mathf.Max((int)Num(res[0]), (int)Num(res[1])));
            string astc = "6x6";
            if (info.Get("astc") is Dictionary<string, object> a)
            {
                string k = file.EndsWith("_BaseColor.png") ? "BaseColor" : normal ? "Normal" : file.EndsWith("_MaskMap.png") ? "MaskMap" : var ? "Var" :
                    file.Contains("Detail") ? "DetailAlbedo" : file.Contains("cracks_layer_Mask") ? "Mask" : "Macro";
                if (a.Get(k) is string s) astc = s;
                else if (a.Get("MaskMap") is string s2) astc = s2;
            }
            // APK size (gate 3 E6, ADR 0025): MaskMap (metallic/occlusion/detail/smoothness) and Var (height/id/joint/convexity)
            // carry low-frequency data; on Android they ship at half the BaseColor/Normal resolution (= mip 1 of the same
            // tier, so the Toksvig-adjusted smoothness of the tier is kept). BaseColor, Normal, crack and detail layers keep
            // the full tier size. -fullPbrMasks restores the old behaviour (comparison builds).
            bool lowFreq = (file.EndsWith("_MaskMap.png") || var) && !EditorTools.HasArg("-fullPbrMasks");
            int apkMax = Mathf.Max(lowFreq ? maxRes / 2 : maxRes, 32);
            string sig = $"pbr3|{normal}|{srgb}|{var}|{hasAlpha}|{maxRes}|{astc}|{apkMax}";
            if (copy || ti.userData != sig)
            {
                ti.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                ti.sRGBTexture = srgb;
                ti.mipmapEnabled = !var;
                ti.mipmapFilter = srgb ? TextureImporterMipFilter.KaiserFilter : TextureImporterMipFilter.BoxFilter;
                ti.alphaSource = hasAlpha ? TextureImporterAlphaSource.FromInput : TextureImporterAlphaSource.None;
                ti.alphaIsTransparency = false;
                ti.wrapMode = TextureWrapMode.Repeat;
                ti.filterMode = var ? FilterMode.Point : FilterMode.Trilinear;
                ti.anisoLevel = 4;
                ti.maxTextureSize = Mathf.Max(maxRes, 32);
                ti.textureCompression = TextureImporterCompression.CompressedHQ;
                ti.SetPlatformTextureSettings(new TextureImporterPlatformSettings
                {
                    name = "Android", overridden = true, maxTextureSize = apkMax,
                    format = AstcFormat(astc), compressionQuality = 50,
                });
                ti.userData = sig;
                ti.SaveAndReimport();
            }
            var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(dst);
            s_Tex[key] = tex;
            if (tex != null && !var) Imported.Add(tex);
            return tex;
        }

        static TextureImporterFormat AstcFormat(string b)
        {
            switch (b)
            {
                case "4x4": return TextureImporterFormat.ASTC_4x4;
                case "5x5": return TextureImporterFormat.ASTC_5x5;
                case "8x8": return TextureImporterFormat.ASTC_8x8;
                case "10x10": return TextureImporterFormat.ASTC_10x10;
                default: return TextureImporterFormat.ASTC_6x6;
            }
        }

        /// <summary>All PBR textures under the region's generated folder (for the tier's aniso / mip bias).</summary>
        public static Texture[] LoadAll(string regionDir)
        {
            string dir = $"{regionDir}/Textures/PBR";
            if (!AssetDatabase.IsValidFolder(dir)) return Array.Empty<Texture>();
            return AssetDatabase.FindAssets("t:Texture2D", new[] { dir }).Select(AssetDatabase.GUIDToAssetPath)
                .Where(p => !p.EndsWith("_Var.png")).Select(AssetDatabase.LoadAssetAtPath<Texture>).Where(t => t != null).ToArray();
        }

        // A plate assembly's explicit data flag registers only its actual front IDs. RegionImporter
        // iterates a ToList snapshot of MaterialDefs before importing prototypes, so these additions
        // safely provide their existing texture/UV path without editing the generic prototype importer.
        static void FurnitureSignFronts(RegionImporter.Result r, Dictionary<string, object> settings)
        {
            string meta = Path.Combine(EditorTools.RepoRoot, "art-source", "world", "props", "props_meta.json");
            var prototypes = Obj(Obj(Parse(File.ReadAllText(meta))).Get("prototypes"));
            var faces = new HashSet<string>(StringComparer.Ordinal);
            foreach (var proto in prototypes.Values)
                foreach (var material in Arr(Obj(proto).Get("materials")))
                    if (material is string name && name.StartsWith("sign_", StringComparison.Ordinal)
                        && !name.StartsWith("sign_facade_", StringComparison.Ordinal)) faces.Add(name);
            foreach (string name in faces.OrderBy(x => x, StringComparer.Ordinal))
            {
                // An explicitly authored material definition from another domain retains ownership.
                if (r.MaterialDefs.ContainsKey(name)) continue;
                var face = new Dictionary<string, object> {
                    { "color", new List<object> { 1.0, 1.0, 1.0 } }, { "rough", 0.45 },
                    { "furniture_sign_face", name.Substring(5) },
                    { "furniture_sign_retro", new Dictionary<string, object> { { "gain", Num(settings.Get("gain")) } } }
                };
                r.MaterialDefs[name] = face;
                r.Materials[name] = FurnitureSign(r, name, face, name.Substring(5), $"{r.Dir}/Materials/M_{name}.mat");
            }
        }

        // ADR0120 r2: explicit face data preserves the original Lit texture/UV path. The optional
        // retro block selects the additive forward shader; removing it restores ordinary URP Lit.
        static Material FurnitureSign(RegionImporter.Result r, string id, Dictionary<string, object> def,
            string face, string path)
        {
            if (id != "sign_" + face || !System.Text.RegularExpressions.Regex.IsMatch(face, @"^[A-Z][A-Za-z0-9_-]*$"))
                throw new InvalidOperationException("Invalid explicitly flagged furniture sign face");
            string png = Path.Combine(EditorTools.RepoRoot, "art-source", "world", "signs", face + ".png");
            if (!File.Exists(png)) throw new FileNotFoundException("Flagged furniture sign texture missing", png);
            var tex = InstanceImporter.ImportTexture(r, png, clamp: true);
            var c = Arr(def.Get("color"));
            var color = new Color((float)Num(c[0]), (float)Num(c[1]), (float)Num(c[2]));
            float rough = def.Get("rough") != null ? (float)Num(def.Get("rough")) : 0.45f;
            var mat = RegionImporter.LitMaterial(path, color, rough, 0f, tex, true, 0.5f, false, null);
            if (def.Get("furniture_sign_retro") is Dictionary<string, object> retro)
            {
                var shader = Shader.Find("Kamion/Furniture Sign") ?? throw new InvalidOperationException("Furniture sign shader missing");
                mat.shader = shader;
                mat.shaderKeywords = new[] { "_ALPHATEST_ON", "_FURNITURE_RETRO" };
                float gain = Mathf.Max(0f, (float)Num(retro.Get("gain")));
                // HDR Lit property: actual GPU readback receives this linear value directly.
                // This is not the plain _Tint contract (which continues to use SetLinearTint).
                mat.SetColor("_EmissionColor", new Color(gain, gain, gain, 1f));
            }
            else
            {
                mat.shaderKeywords = new[] { "_ALPHATEST_ON" };
                mat.SetColor("_EmissionColor", Color.black);
            }
            EditorUtility.SetDirty(mat);
            return mat;
        }

        static Material FurniturePlinth(RegionImporter.Result r, Dictionary<string, object> def,
            Dictionary<string, object> detail, string path)
        {
            var c = Arr(def.Get("color"));
            var albedo = new Color((float)Num(c[0]), (float)Num(c[1]), (float)Num(c[2]));
            float rough = def.Get("rough") != null ? (float)Num(def.Get("rough")) : 0.9f;
            float metal = def.Get("metal") != null ? (float)Num(def.Get("metal")) : 0f;
            var mat = LookDevAssets.WorldMaterial(path, Str(def.Get("surface")), albedo, rough, metal, false);
            mat.SetFloat("_GroundMasks", 0f); // same final state as RegionImporter's original fallback
            string texture = detail.Get("texture") as string ?? "furniture_plinth";
            if (texture != "furniture_plinth") throw new InvalidOperationException("Unexpected furniture plinth texture");
            var scan = InstanceImporter.ImportTexture(r,
                Path.Combine(EditorTools.RepoRoot, "art-source", "world", "textures", texture + ".png"), clamp: false);
            mat.SetTexture("_FurnitureMap", scan);
            mat.SetVector("_FurnitureDetail", new Vector4(
                Mathf.Max(0.01f, (float)Num(detail.Get("tile_m"))),
                Mathf.Max(0.01f, (float)Num(detail.Get("dirt_h"))),
                Mathf.Clamp01((float)Num(detail.Get("dirt_strength"))), 0f));
            mat.EnableKeyword("_FURNITURE_PLINTH");
            EditorUtility.SetDirty(mat); // persisted scene material retains the build-time variant reference
            return mat;
        }

        /// <summary>Estimated GPU bytes of the imported PBR textures (Android ASTC with mips, from the spec).</summary>
        public static long EstimatedGpuBytes()
        {
            long sum = 0;
            var seen = new HashSet<string>(s_Tex.Keys.Select(k => k.Split('/')[0]));
            foreach (var name in seen)
                if (Set(name) is Dictionary<string, object> s && FilesFor(s) is Dictionary<string, object> info && info.Get("gpu_bytes_astc_mips") != null)
                    sum += (long)Num(info.Get("gpu_bytes_astc_mips"));
            return sum;
        }
    }
}
