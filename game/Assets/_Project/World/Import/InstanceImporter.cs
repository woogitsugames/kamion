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

        public sealed class Colliders
        {
            public readonly List<(string proto, Matrix4x4 m, Bounds local)> Items = new List<(string, Matrix4x4, Bounds)>();
            public int Count => Items.Count;
        }

        /// <summary>LOD end distances (m at lodBias 1; last = cull) and shadow mask per prototype family. WORKING_VALUE.</summary>
        static (float[] ends, int shadowMask) Policy(string proto, int lodCount)
        {
            float[] e;
            if (proto.StartsWith("tree_shrub")) e = new[] { 15f, 50f, 300f };
            else if (proto.StartsWith("tree_")) e = new[] { 30f, 100f, 1000f };
            else if (proto.StartsWith("lamp_")) e = new[] { 60f, 400f };
            else if (proto == "pylon" || proto == "power_pole") e = new[] { 80f, 1500f };
            else if (proto.StartsWith("plate_") || proto.StartsWith("board_") || proto.StartsWith("sign_") || proto.StartsWith("signal_")) e = new[] { 50f, 250f };
            else if (proto == "bus_shelter" || proto.EndsWith("_gate")) e = new[] { 60f, 300f };
            else e = new[] { 30f, 120f };   // bench, bollard, waste bin, street cabinet
            if (e.Length > lodCount) e = new[] { e[0] }.Concat(e.Skip(e.Length - lodCount + 1)).ToArray();
            int shadows = proto.StartsWith("tree_") ? 0b011 : 0b001;
            return (e.Take(lodCount).ToArray(), shadows);
        }

        public static WorldInstanceSet Build(RegionImporter.Result r, List<string> instanceFiles, out Colliders colliders)
        {
            string art = Path.Combine(EditorTools.RepoRoot, "art-source", "world");
            var props = GlbReader.Load(Path.Combine(art, "props", "street_props.glb"));
            var trees = GlbReader.Load(Path.Combine(art, "vegetation", "trees.glb"));
            var impostors = GlbReader.Load(Path.Combine(art, "vegetation", "trees_lod2.glb"));
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
            long bytes = 0;

            int Proto(string name)
            {
                if (protoIndex.TryGetValue(name, out int idx)) return idx;
                bool tree = name.StartsWith("tree_");
                var lodNodes = new List<(GlbReader g, GlbReader.MeshNode n)>();
                var src = tree ? trees : props;
                var n0 = src.Find(name);
                if (n0 == null) { Debug.LogWarning($"[IMPORT] prototype '{name}' not in the library - instances skipped"); protoIndex[name] = -1; return -1; }
                lodNodes.Add((src, n0));
                var n1 = src.Find(name + ".lod1");
                if (n1 != null) lodNodes.Add((src, n1));
                if (tree && impostors.Find(name + ".lod2") is GlbReader.MeshNode n2) lodNodes.Add((impostors, n2));
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
                var col = !tree ? props.Find(name + ".col") : null;
                if (col != null)
                {
                    var b = new Bounds(col.Primitives[0].Positions[0], Vector3.zero);
                    foreach (var prim in col.Primitives) foreach (var v in prim.Positions) b.Encapsulate(v);
                    colMeshes[name] = b;
                }
                idx = protos.Count;
                protos.Add(p);
                protoIndex[name] = idx;
                return idx;
            }

            // ---- instances ----
            var items = new List<(long cell, int proto, Matrix4x4 m)>();
            colliders = new Colliders();
            var corridor = r.Chunks.Where(c => c.Corridor).ToList();
            float minE = r.Chunks.Min(c => c.Min.x), minN = r.Chunks.Min(c => c.Min.y);
            foreach (var f in instanceFiles)
            {
                if (!File.Exists(f)) throw new FileNotFoundException(f + " missing - rerun build_world.py");
                foreach (var io in Arr(Obj(Parse(File.ReadAllText(f))).Get("instances")))
                {
                    var it = Obj(io);
                    string p = Str(it.Get("p"));
                    float e = (float)Num(it.Get("e")), n = (float)Num(it.Get("n")), z = (float)Num(it.Get("z")), yaw = (float)Num(it.Get("yaw"));
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
                    long cx = (long)Mathf.Floor((e - minE) / CellM), cz = (long)Mathf.Floor((n - minN) / CellM);
                    items.Add(((cz << 20) | cx, pi, m));
                    if (colMeshes.TryGetValue(p, out var cb) && cb.HasValue && corridor.Any(c => e >= c.Min.x && e < c.Max.x && n >= c.Min.y && n < c.Max.y))
                        colliders.Items.Add((p, m, cb.Value));
                }
            }

            items.Sort((a, b) => a.cell != b.cell ? a.cell.CompareTo(b.cell) : a.proto.CompareTo(b.proto));
            var cells = new List<WorldInstanceSet.Cell>();
            var runs = new List<WorldInstanceSet.Run>();
            var mats = new Matrix4x4[items.Count];
            for (int i = 0; i < items.Count;)
            {
                long cell = items[i].cell;
                var c = new WorldInstanceSet.Cell { runStart = runs.Count };
                bool first = true;
                while (i < items.Count && items[i].cell == cell)
                {
                    int pr = items[i].proto, start = i;
                    while (i < items.Count && items[i].cell == cell && items[i].proto == pr)
                    {
                        mats[i] = items[i].m;
                        var wb = Transform(protos[pr].lods[0].bounds, items[i].m);
                        if (first) { c.bounds = wb; first = false; } else c.bounds.Encapsulate(wb);
                        i++;
                    }
                    runs.Add(new WorldInstanceSet.Run { prototype = pr, start = start, count = i - start });
                    protos[pr].count += i - start;
                }
                c.runCount = runs.Count - c.runStart;
                cells.Add(c);
            }
            set.prototypes = protos.ToArray();
            set.materials = materials.ToArray();
            set.cells = cells.ToArray();
            set.runs = runs.ToArray();
            set.matrices = mats;
            EditorUtility.SetDirty(set);
            bytes += mats.Length * 64L;
            r.MemoryBytes["instances"] = bytes;
            Debug.Log($"[IMPORT] instances: {mats.Length} in {cells.Count} cells, {protos.Count} prototypes " +
                      $"({string.Join(", ", protos.OrderByDescending(q => q.count).Take(8).Select(q => $"{q.name} {q.count}"))}…), " +
                      $"{colliders.Count} prop colliders in the corridor, prototype meshes + matrices {bytes / 1048576.0:F1} MB");
            return set;
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
            if (r.Materials.TryGetValue(name, out var regionMat))
            {
                textured = r.MaterialDefs.TryGetValue(name, out var d) && d.Get("texture") != null;
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

        /// <summary>Copies an art-source PNG into the generated textures folder with mobile import settings.</summary>
        public static Texture2D ImportTexture(RegionImporter.Result r, string png, bool clamp)
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
            bool alpha = file.StartsWith("leaves_") || file.StartsWith("impostor_") || file.StartsWith("fence_") || file.StartsWith("dock_") || !file.StartsWith("bark_");
            bool text = file.StartsWith("dock_") || file.Contains("-");   // sign faces (A-7, B-33_30, E-2_*) and dock numbers: legible
            ti.textureType = TextureImporterType.Default;
            ti.sRGBTexture = true;
            ti.mipmapEnabled = true;
            ti.alphaSource = TextureImporterAlphaSource.FromInput;
            ti.alphaIsTransparency = alpha;
            ti.mipMapsPreserveCoverage = alpha;
            ti.alphaTestReferenceValue = 0.5f;
            ti.wrapMode = clamp ? TextureWrapMode.Clamp : TextureWrapMode.Repeat;
            ti.filterMode = FilterMode.Trilinear;
            ti.anisoLevel = text ? 4 : 2;
            ti.maxTextureSize = 2048;
            ti.textureCompression = TextureImporterCompression.Compressed;
            ti.SetPlatformTextureSettings(new TextureImporterPlatformSettings
            {
                name = "Android", overridden = true, maxTextureSize = 1024,
                format = text ? TextureImporterFormat.ASTC_4x4 : TextureImporterFormat.ASTC_6x6,
                compressionQuality = 50,
            });
            ti.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Texture2D>(dst);
        }
    }
}
