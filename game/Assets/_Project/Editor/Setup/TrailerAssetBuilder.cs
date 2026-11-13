using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using EditorTools = Game.Editor.Build.EditorTools;
using Json = Game.Editor.Setup.TruckAssetBuilder.Json;

namespace Game.Editor.Setup
{
    /// <summary>
    /// Builds the art curtainsider trailer prefab from art-source/truck/trailer/export/trailer_manifest.json (regenerate,
    /// never hand-edit), the same way <see cref="TruckAssetBuilder"/> builds the TRAKT tractor:
    /// 1. copies the FBX (LOD0-2) and the per-tier C/N/M atlases into Assets/_Generated/Trailer (outside git, ADR 0011);
    /// 2. import settings: scale 1, convert units, no axis bake, no animation, MikkT; ASTC per tier (manifest tiers);
    /// 3. materials per tier on Kamion/Truck Exterior (Paint and Curtain are tinted slots, livery "szary"; Lights reads the
    ///    tractor's lamp-state texture, so brake/tail/reverse follow the combination) in TruckMaterialSet assets;
    /// 4. the prefab: the graybox trailer provides the physics root (Rigidbody, TrailerBody, TrailerVisuals, the same box
    ///    colliders and the reversing camera: physics unchanged); its visuals are replaced by the art: wheels under the
    ///    physics wheel spinners (suspension travel and spin from the solver), the tyre flattened at the physics rolling
    ///    radius in the shader (rendering layer bit 9), landing-gear legs under the TrailerVisuals leg transforms (foot height
    ///    from the solver), the crank turned from the leg travel, rear doors on their hinge pivots (TrailerVisualRig.doorsOpen).
    /// Entry points: Kamion/Setup/Rebuild curtainsider trailer, batchmode -executeMethod Game.Editor.Setup.TrailerAssetBuilder.BuildBatch
    /// (Game.World.Import.WorldTruckInstaller.InstallBatch puts it into the WorldC scenes).
    /// </summary>
    public static class TrailerAssetBuilder
    {
        public const string Root = "Assets/_Generated/Trailer";
        public const string PrefabPath = Root + "/Trailer_Curtainsider_Art.prefab";
        const string Src = Root + "/Source";
        const string MatDir = Root + "/Materials";
        const string ResDir = Root + "/Resources/TRAILER";
        const string Manifest = "art-source/truck/trailer/export/trailer_manifest.json";
        const string Livery = "szary";
        static readonly string[] Tiers = { "High", "Medium", "Low" };
        static readonly string[] Slots = { "Paint", "Curtain", "Trim", "Metal", "Lights" };

        public static void BuildBatch()
        {
            int exit = 0;
            try { Build(); Debug.Log("TRAILER_RESULT: OK"); }
            catch (Exception e) { Debug.LogException(e); Debug.Log("TRAILER_RESULT: FAILED"); exit = 1; }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        [MenuItem("Kamion/Setup/Rebuild curtainsider trailer")]
        public static void Build()
        {
            var man = Json.Obj(Json.Parse(File.ReadAllText(Path.Combine(EditorTools.RepoRoot, Manifest))));
            CopySources(man);
            ConfigureImporters();
            var sets = BuildMaterials(man);
            BuildPrefab(man, sets);
            AssetDatabase.SaveAssets();
        }

        // ------------------------------------------------------------------ 1. sources

        static void CopySources(Dictionary<string, object> man)
        {
            var copies = new List<(string src, string dst)>();
            foreach (var lod in Json.Obj(man["lods"]))
            {
                string f = Json.Str(Json.Obj(lod.Value)["file"]);
                copies.Add((f, $"{Src}/{Path.GetFileName(f)}"));
            }
            foreach (var t in Tiers)
                foreach (var slot in Slots)
                    foreach (var k in new[] { "C", "N", "M" })
                    {
                        string f = $"art-source/truck/trailer/export/textures/{t}/T_Trl_{slot}_{k}.png";
                        copies.Add((f, $"{Src}/Textures/{t}/{Path.GetFileName(f)}"));
                    }
            int copied = 0;
            foreach (var (src, dst) in copies)
            {
                string s = Path.Combine(EditorTools.RepoRoot, src);
                string d = Path.Combine(EditorTools.ProjectRoot, dst);
                if (!File.Exists(s)) throw new FileNotFoundException("missing trailer source " + src, s);
                var fs = new FileInfo(s);
                if (fs.Length < 1024 && File.ReadAllText(s).StartsWith("version https://git-lfs", StringComparison.Ordinal))
                    throw new InvalidDataException("LFS pointer, not the file (git lfs pull): " + src);
                var fd = new FileInfo(d);
                if (fd.Exists && fd.Length == fs.Length && fd.LastWriteTimeUtc >= fs.LastWriteTimeUtc) continue;
                Directory.CreateDirectory(Path.GetDirectoryName(d));
                File.Copy(s, d, true);
                copied++;
            }
            Debug.Log($"[TRAILER] sources: {copies.Count} files, {copied} copied");
            AssetDatabase.Refresh();
        }

        // ------------------------------------------------------------------ 2. importers

        static void ConfigureImporters()
        {
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { Src }))
            {
                if (!(AssetImporter.GetAtPath(AssetDatabase.GUIDToAssetPath(guid)) is ModelImporter mi)) continue;
                bool dirty = false;
                void Set<T>(T cur, T want, Action<T> apply) { if (!EqualityComparer<T>.Default.Equals(cur, want)) { apply(want); dirty = true; } }
                Set(mi.globalScale, 1f, v => mi.globalScale = v);
                Set(mi.useFileUnits, true, v => mi.useFileUnits = v);
                Set(mi.bakeAxisConversion, false, v => mi.bakeAxisConversion = v);
                Set(mi.importCameras, false, v => mi.importCameras = v);
                Set(mi.importLights, false, v => mi.importLights = v);
                Set(mi.importVisibility, false, v => mi.importVisibility = v);
                Set(mi.importAnimation, false, v => mi.importAnimation = v);
                Set(mi.animationType, ModelImporterAnimationType.None, v => mi.animationType = v);
                Set(mi.importBlendShapes, false, v => mi.importBlendShapes = v);
                Set(mi.materialImportMode, ModelImporterMaterialImportMode.ImportStandard, v => mi.materialImportMode = v);
                Set(mi.materialLocation, ModelImporterMaterialLocation.InPrefab, v => mi.materialLocation = v);
                Set(mi.meshCompression, ModelImporterMeshCompression.Off, v => mi.meshCompression = v);
                Set(mi.isReadable, false, v => mi.isReadable = v);
                Set(mi.importNormals, ModelImporterNormals.Import, v => mi.importNormals = v);
                Set(mi.importTangents, ModelImporterTangents.CalculateMikk, v => mi.importTangents = v);
                Set(mi.generateSecondaryUV, false, v => mi.generateSecondaryUV = v);
                Set(mi.addCollider, false, v => mi.addCollider = v);
                if (dirty) mi.SaveAndReimport();
            }
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { Src }))
            {
                string p = AssetDatabase.GUIDToAssetPath(guid);
                if (!(AssetImporter.GetAtPath(p) is TextureImporter ti)) continue;
                string n = Path.GetFileNameWithoutExtension(p);
                bool high = p.Contains("/High/");
                bool normal = n.EndsWith("_N", StringComparison.Ordinal);
                bool srgb = n.EndsWith("_C", StringComparison.Ordinal);
                // manifest tiers.texture_compression: C 6x6 (High) / 8x8, N 5x5 (High) / 6x6, M 8x8.
                var fmt = normal ? (high ? TextureImporterFormat.ASTC_5x5 : TextureImporterFormat.ASTC_6x6)
                    : n.EndsWith("_M", StringComparison.Ordinal) ? TextureImporterFormat.ASTC_8x8
                    : high ? TextureImporterFormat.ASTC_6x6 : TextureImporterFormat.ASTC_8x8;
                bool dirty = false;
                var type = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                if (ti.textureType != type) { ti.textureType = type; dirty = true; }
                if (!normal && ti.sRGBTexture != srgb) { ti.sRGBTexture = srgb; dirty = true; }
                if (!ti.mipmapEnabled) { ti.mipmapEnabled = true; dirty = true; }
                if (ti.anisoLevel != 2) { ti.anisoLevel = 2; dirty = true; }
                if (ti.maxTextureSize != 2048) { ti.maxTextureSize = 2048; dirty = true; }
                if (ti.alphaSource != TextureImporterAlphaSource.FromInput) { ti.alphaSource = TextureImporterAlphaSource.FromInput; dirty = true; }
                if (ti.alphaIsTransparency) { ti.alphaIsTransparency = false; dirty = true; }
                var a = ti.GetPlatformTextureSettings("Android");
                if (!a.overridden || a.format != fmt || a.maxTextureSize != 2048)
                {
                    a.overridden = true; a.format = fmt; a.maxTextureSize = 2048; a.compressionQuality = 50;
                    ti.SetPlatformTextureSettings(a);
                    dirty = true;
                }
                if (dirty) ti.SaveAndReimport();
            }
        }

        // ------------------------------------------------------------------ 3. materials

        static Color Col(object o) { var a = Json.Arr(o); return new Color((float)Json.Num(a[0]), (float)Json.Num(a[1]), (float)Json.Num(a[2]), 1f); }

        static Dictionary<string, TruckMaterialSet> BuildMaterials(Dictionary<string, object> man)
        {
            var shader = Shader.Find("Kamion/Truck Exterior");
            if (shader == null) throw new InvalidOperationException("Kamion/Truck Exterior not compiled");
            var liv = Json.Obj(Json.Obj(man["liveries"])[Livery]);
            var dirtColor = Col(Json.Obj(man["shader_contract"])["_DirtColor"]);
            Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, ResDir));
            var sets = new Dictionary<string, TruckMaterialSet>();
            foreach (var tier in Tiers)
            {
                string dir = $"{MatDir}/{tier}";
                Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, dir));
                var entries = new List<TruckMaterialSet.Entry>();
                foreach (var slot in Slots)
                {
                    string name = "MI_Trl_" + slot;
                    string p = $"{dir}/{name}.mat";
                    var m = AssetDatabase.LoadAssetAtPath<Material>(p);
                    if (m == null) { m = new Material(shader) { name = name }; AssetDatabase.CreateAsset(m, p); }
                    m.shader = shader;
                    m.shaderKeywords = new string[0];
                    string t = $"{Src}/Textures/{tier}/T_Trl_{slot}_";
                    m.SetTexture("_CMap", Load(t + "C.png"));
                    m.SetTexture("_NMap", Load(t + "N.png"));
                    m.SetTexture("_MMap", Load(t + "M.png"));
                    m.SetTexture("_DecalMap", Texture2D.blackTexture);   // uv1 unused on the trailer (manifest)
                    m.SetFloat("_Dirt", 0.5f);
                    m.SetColor("_DirtColor", dirtColor);
                    // ADR 0038: coated base lobe, orange peel, procedural road grime (vehicle frame from ContactShadowCaster). WORKING_VALUE.
                    m.SetFloat("_CoatedBaseRoughness", 0.6f); m.SetFloat("_OrangePeel", 0.012f);
                    m.SetFloat("_GrimeHeight", 0.8f); m.SetFloat("_GrimeChassis", 1.3f);
                    // Paint / Curtain: the tint slots (M.b = tint mask): albedo = C.rgb * colour where the mask is set.
                    bool tinted = slot == "Paint" || slot == "Curtain";
                    m.SetFloat("_IsPaint", tinted ? 1f : 0f);
                    m.SetFloat("_PaintMetallic", 0f);
                    if (slot == "Paint")
                    {
                        m.SetColor("_PaintColor", Col(liv["_PaintColor"]));
                        m.SetFloat("_PaintRoughness", (float)Json.Num(liv["_PaintRoughness"]));
                    }
                    else if (slot == "Curtain")
                    {
                        m.SetColor("_PaintColor", Col(liv["_CurtainColor"]));
                        // Kamion/Truck Exterior replaces the roughness under the tint mask: PVC-coated polyester curtain, the
                        // mean C.a of the curtain atlas under the mask (0.58, measured on the Medium atlas). WORKING_VALUE.
                        m.SetFloat("_PaintRoughness", 0.58f);
                        // ADR 0038: a PVC curtain has no lacquer layer (lowsun r4: the curtain shone like a painted panel).
                        m.SetFloat("_ClearCoat", 0f);
                    }
                    // Review r6 T-N1: the curtain's soiling comes from the spray / wake / post-runoff model in the shader
                    // (trailer frame: curtain bottom = floor 1.30 m + 1 cm, top under the top rail, rear z, axles from
                    // dims.json), not from the baked mask (dark blotches on the rear third). Posts every 3.4 m from the rear
                    // portal: WORKING_VALUE.
                    m.SetVector("_CurtainGrime", slot == "Curtain" ? new Vector4(1f, 1.31f, 3.88f, -12.0f) : Vector4.zero);
                    m.SetVector("_CurtainAxles", new Vector4(-6.39f, -7.70f, -9.01f, 0f));
                    m.SetVector("_CurtainPosts", new Vector4(3.4f, 0f, 0.22f, 0.7f));
                    // ADR 0182 (review s18 0175 P2): the rear doors, portal posts and contour tapes take their dirt from the
                    // rear-face soiling model (wake film, hinge posts / centre seal, header and hinge runoff, per-leaf seeds)
                    // instead of the baked mask (one noise cloud, identical on both leaves; Low atlas 4x smaller = paler).
                    // Trailer object frame (trailer_build.py): rear face z -12.0, doors 1.335-3.865 m, half width = portal post
                    // inner edge 1.135 m; door leaves (rendering layer bit 11) pivot on the hinge at |x| 1.147, y 2.6,
                    // z -12.014. Amount 0.85, non-paint (tapes, posts, lamps) x0.6. WORKING_VALUE.
                    m.SetVector("_RearGrime", slot == "Curtain" ? Vector4.zero : new Vector4(1f, -12.0f, 1.335f, 3.865f));
                    // r5 (review s19 P1-1/P1-2): non-paint parts (sill, posts, RUPD beam, tapes) x0.8 - they are the dirtiest,
                    // lamp lenses x0.35 (emission untouched); deposit = dried road spray, warm grey-brown sRGB ~(115,100,79),
                    // max coverage 0.7 on paint (0.9 on bare metal / trim, shader). WORKING_VALUE.
                    m.SetVector("_RearGrime2", new Vector4(1.135f, 0.85f, slot == "Lights" ? 0.35f : 0.8f, 0f));
                    m.SetColor("_RearGrimeColor", new Color(0.17f, 0.13f, 0.08f, 0.7f));
                    m.SetVector("_RearGrime3", new Vector4(1.147f, 2.6f, -12.014f, 0f));
                    m.SetFloat("_Lamps", slot == "Lights" ? 1f : 0f);
                    if (slot == "Lights") m.EnableKeyword("_KAMION_TRUCK_LAMPS");
                    TruckAssetBuilder.ApplyLensSettings(m);   // ADR 0181
                    EditorUtility.SetDirty(m);
                    entries.Add(new TruckMaterialSet.Entry { slot = name, material = m });
                }
                string setPath = $"{ResDir}/TrailerMaterials_{tier}.asset";
                var set = AssetDatabase.LoadAssetAtPath<TruckMaterialSet>(setPath);
                if (set == null) { set = ScriptableObject.CreateInstance<TruckMaterialSet>(); AssetDatabase.CreateAsset(set, setPath); }
                set.entries = entries.ToArray();
                EditorUtility.SetDirty(set);
                sets[tier] = set;
            }
            AssetDatabase.SaveAssets();
            return sets;
        }

        static Texture2D Load(string p)
        {
            var t = AssetDatabase.LoadAssetAtPath<Texture2D>(p);
            if (t == null) throw new FileNotFoundException("texture not imported: " + p);
            return t;
        }

        // ------------------------------------------------------------------ 4. prefab

        static Vector3 V3(object o) { var a = Json.Arr(o); return new Vector3((float)Json.Num(a[0]), (float)Json.Num(a[1]), (float)Json.Num(a[2])); }

        static Transform Child(Transform parent, string name, Vector3 localPos)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            return go.transform;
        }

        static Transform FindDeep(Transform t, string name)
        {
            if (t.name == name) return t;
            foreach (Transform c in t) { var r = FindDeep(c, name); if (r != null) return r; }
            return null;
        }

        static void BuildPrefab(Dictionary<string, object> man, Dictionary<string, TruckMaterialSet> sets)
        {
            var data = AssetDatabase.LoadAssetAtPath<VehicleDataAsset>("Assets/_Project/Vehicle/Runtime/Resources/" + VehicleDataAsset.DefaultResourcePath + ".asset");
            if (data == null) throw new FileNotFoundException("VehicleData asset missing: run Kamion/Setup/Rebuild DrivingLab");
            var gbMats = GrayboxMaterials.CreateRuntime();
            var body = GrayboxTrailerBuilder.Build(data, new TrailerDimensions(), gbMats);
            var root = body.gameObject;
            root.name = "Trailer_Curtainsider";
            var visuals = root.GetComponent<TrailerVisuals>();
            var probe = data.CreateTrailer();
            var def = data.Trailer;
            int layer = UnityGroundQuery.ResolveVehicleLayer();
            try
            {
                // ---- strip the graybox visuals (physics, colliders, wheel pivots, leg transforms and the reversing camera stay) ----
                UnityEngine.Object.DestroyImmediate(root.transform.Find("Body").gameObject);
                foreach (var spin in visuals.wheelSpinners)
                    for (int i = spin.childCount - 1; i >= 0; i--) UnityEngine.Object.DestroyImmediate(spin.GetChild(i).gameObject);
                foreach (var leg in visuals.legs)
                    for (int i = leg.childCount - 1; i >= 0; i--) UnityEngine.Object.DestroyImmediate(leg.GetChild(i).gameObject);

                var art = Child(root.transform, "Art", Vector3.zero);
                var lods = Json.Obj(man["lods"]);
                var lod0Objs = Json.Obj(Json.Obj(lods["LOD0"])["objects"]);
                Transform Pivot(string name, string role) => Child(root.transform, name, V3(Json.Obj(lod0Objs[role + "_LOD0"])["pivot_unity_vehicle"]));
                var crank = Pivot("CrankPivot", "CRANK");
                var doorL = Pivot("DoorPivot_RL", "DOOR_RL");
                var doorR = Pivot("DoorPivot_RR", "DOOR_RR");

                // Physics wheel per art wheel role (nearest hardpoint in x/z; the manifest physics_crosscheck says they coincide).
                var wheels = probe.Wheels;
                Transform SpinFor(Vector3 artPivot, string role)
                {
                    int best = -1; float bd = float.MaxValue;
                    for (int i = 0; i < wheels.Length; i++)
                    {
                        var hp = wheels[i].HardpointLocal.ToUnity();
                        float d = new Vector2(hp.x - artPivot.x, hp.z - artPivot.z).magnitude;
                        if (d < bd) { bd = d; best = i; }
                    }
                    if (bd > 0.02f) Debug.LogWarning($"[TRAILER] {role}: art wheel centre {artPivot} is {bd:F3} m from the nearest physics wheel");
                    return visuals.wheelSpinners[best];
                }
                Transform LegFor(Vector3 artPivot) => visuals.legs.OrderBy(l => Mathf.Abs(l.localPosition.x - artPivot.x)).First();

                var lodRenderers = new List<Renderer>[3];
                var slots = new List<TruckVisualRig.RendererSlots>();
                for (int lod = 0; lod < 3; lod++)
                {
                    lodRenderers[lod] = new List<Renderer>();
                    var L = Json.Obj(lods["LOD" + lod]);
                    var asset = AssetDatabase.LoadAssetAtPath<GameObject>($"{Src}/{Path.GetFileName(Json.Str(L["file"]))}");
                    if (asset == null) throw new FileNotFoundException("trailer model not imported: " + Json.Str(L["file"]));
                    var model = UnityEngine.Object.Instantiate(asset, root.transform, false);
                    model.transform.localPosition = Vector3.zero; model.transform.localRotation = Quaternion.identity; model.transform.localScale = Vector3.one;
                    foreach (var kv in Json.Obj(L["objects"]))
                    {
                        var o = Json.Obj(kv.Value);
                        string role = Json.Str(o["role"]);
                        var t = FindDeep(model.transform, kv.Key);
                        if (t == null) { Debug.LogWarning($"[TRAILER] {kv.Key} not in the FBX"); continue; }
                        Vector3 pivot = V3(o["pivot_unity_vehicle"]);
                        bool wheel = role.StartsWith("WHEEL_", StringComparison.Ordinal);
                        Transform parent = wheel ? SpinFor(pivot, role)
                            : role.StartsWith("LEG_", StringComparison.Ordinal) ? LegFor(pivot)
                            : role == "CRANK" ? crank : role == "DOOR_RL" ? doorL : role == "DOOR_RR" ? doorR : art;
                        t.SetParent(parent, true);
                        // Moving parts: the FBX object origin is the part pivot; put it on the rig transform (wheel centre = physics
                        // wheel centre, leg origin = foot, crank / door on the hinge). Static parts keep the modelled pose.
                        if (parent != art) t.localPosition = Vector3.zero;
                        var r = t.GetComponent<Renderer>();
                        if (r == null) continue;
                        var slotNames = r.sharedMaterials.Select(m => m != null ? m.name.Replace(" (Instance)", "") : "MI_Trl_Trim").ToArray();
                        foreach (var s in slotNames) if (sets["Low"].Get(s) == null) Debug.LogWarning($"[TRAILER] {kv.Key}: unknown material slot {s}");
                        r.sharedMaterials = slotNames.Select(s => sets["Low"].Get(s) ?? sets["Low"].Get("MI_Trl_Trim")).ToArray();
                        slots.Add(new TruckVisualRig.RendererSlots { renderer = r, slots = slotNames });
                        r.shadowCastingMode = ShadowCastingMode.On;
                        r.receiveShadows = true;
                        if (wheel) r.renderingLayerMask |= TrailerVisualRig.TyreRenderingLayer;
                        // ADR 0182: rear door leaves - Kamion/Truck Exterior maps their hinge-origin object space back to the
                        // trailer frame for the rear-face soiling model.
                        if (role == "DOOR_RL" || role == "DOOR_RR") r.renderingLayerMask |= TrailerVisualRig.RearDoorRenderingLayer;
                        lodRenderers[lod].Add(r);
                    }
                    if (lod == 0)
                    {
                        var kp = V3(Json.Obj(Json.Obj(L["empties"])["KINGPIN"])["position_unity_vehicle"]);
                        if (Mathf.Abs(kp.y - (float)def.kingpinHeight) > 0.005f || new Vector2(kp.x, kp.z).magnitude > 0.005f)
                            Debug.LogWarning($"[TRAILER] KINGPIN {kp} != physics kingpin (0, {def.kingpinHeight}, 0)");
                    }
                    UnityEngine.Object.DestroyImmediate(model);   // the remaining children are the empties (sockets, lamps): not needed at runtime
                }

                var group = root.AddComponent<LODGroup>();
                group.fadeMode = LODFadeMode.None;
                var rig = root.AddComponent<TrailerVisualRig>();
                rig.group = group;
                rig.lods = lodRenderers.Select(l => new TruckVisualRig.RendererList { renderers = l.ToArray() }).ToArray();
                rig.slots = slots.ToArray();
                rig.residentSet = sets["Low"];
                rig.tyreFlatRadius = (float)probe.Wheels[0].Radius;
                var sz = Json.Obj(man["lod_screen_size_suggestion"]);
                rig.screenSizes = new[] { (float)Json.Num(sz["LOD0"]), (float)Json.Num(sz["LOD1"]), (float)Json.Num(sz["LOD2"]), (float)Json.Num(sz["cull"]) };
                rig.leg = visuals.legs[0];
                rig.raisedFootY = (float)def.landingGear.raisedFootY;
                rig.crank = crank;
                rig.doorLeft = doorL; rig.doorRight = doorR;
                rig.forceLevel = 0;
                rig.Apply();
                rig.forceLevel = -1;

                foreach (var t in root.GetComponentsInChildren<Transform>(true)) t.gameObject.layer = layer;
                foreach (var r in root.GetComponentsInChildren<Renderer>(true)) { r.lightProbeUsage = LightProbeUsage.BlendProbes; r.reflectionProbeUsage = ReflectionProbeUsage.BlendProbes; }
                int Tris(IEnumerable<Renderer> rs) => rs.Sum(r => { var mf = r.GetComponent<MeshFilter>(); return mf != null && mf.sharedMesh != null ? (int)(mf.sharedMesh.triangles.Length / 3) : 0; });
                Debug.Log($"[TRAILER] tris LOD0 {Tris(lodRenderers[0])} LOD1 {Tris(lodRenderers[1])} LOD2 {Tris(lodRenderers[2])}; renderers {lodRenderers[0].Count}/{lodRenderers[1].Count}/{lodRenderers[2].Count}; " +
                          $"tyre flat radius {rig.tyreFlatRadius:F3} m; wheels {wheels.Length}");
                Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, Root));
                PrefabUtility.SaveAsPrefabAsset(root, PrefabPath);
                Debug.Log("[TRAILER] prefab " + PrefabPath);
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(root);
                foreach (var f in typeof(GrayboxMaterials).GetFields())
                    if (f.GetValue(gbMats) is Material m && m != null) UnityEngine.Object.DestroyImmediate(m);
            }
        }
    }
}
