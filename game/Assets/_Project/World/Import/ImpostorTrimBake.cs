using System.IO;
using Game.Editor.Build;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.World.Import
{
    /// <summary>
    /// ADR 0136: writes the tight impostor polygon (<see cref="ImpostorTrim"/>) into a tree's ".lod2" mesh. Called by
    /// <see cref="InstanceImporter"/> for every tree impostor (survives reimport) and by <see cref="RunBatch"/> for an already
    /// imported region (rewrites the sub-assets of Instances.asset in place, GUIDs and references unchanged).
    /// Batch: Unity -batchmode -executeMethod Game.World.Import.ImpostorTrimBake.RunBatch [-region bialystok-industrial-c]
    /// </summary>
    public static class ImpostorTrimBake
    {
        /// <summary>Rewrites <paramref name="mesh"/> from the source quad <paramref name="quad"/> and the impostor material's atlas.
        /// Returns the polygon's share of the quad, or -1 when left unchanged.</summary>
        public static float Apply(Mesh mesh, GlbReader.MeshNode quad, Material mat)
        {
            if (mesh == null || quad == null || mat == null || !mat.IsKeywordEnabled("_IMPOSTOR")) return -1f;
            var tex = mat.GetTexture("_BaseMap");
            string path = tex != null ? AssetDatabase.GetAssetPath(tex) : null;
            if (string.IsNullOrEmpty(path) || !File.Exists(path)) return -1f;
            if (quad.Primitives.Count != 1 || quad.Primitives[0].Uv0 == null) return -1f;
            var prim = quad.Primitives[0];
            // Source quad: half width and the linear map uv.y -> y (two corners of different height).
            float hw = 0f;
            foreach (var p in prim.Positions) hw = Mathf.Max(hw, Mathf.Abs(p.x));
            int a = 0, b = -1;
            for (int i = 1; i < prim.Positions.Length; i++)
                if (Mathf.Abs(prim.Positions[i].y - prim.Positions[a].y) > 1e-3f && Mathf.Abs(prim.Uv0[i].y - prim.Uv0[a].y) > 1e-3f) { b = i; break; }
            if (b < 0 || hw <= 0f) return -1f;
            float k = (prim.Positions[b].y - prim.Positions[a].y) / (prim.Uv0[b].y - prim.Uv0[a].y);
            float yAtV0 = prim.Positions[a].y - k * prim.Uv0[a].y, yAtV1 = yAtV0 + k;

            var img = new Texture2D(2, 2, TextureFormat.RGBA32, false, true);
            if (!img.LoadImage(File.ReadAllBytes(path))) { Object.DestroyImmediate(img); return -1f; }
            var px = img.GetPixels32();   // row 0 = bottom (v = 0), as ImpostorTrim expects
            int w = img.width, h = img.height;
            Object.DestroyImmediate(img);
            var alpha = new byte[px.Length];
            for (int i = 0; i < px.Length; i++) alpha[i] = px[i].a;
            int views = Mathf.Max(1, Mathf.RoundToInt(mat.GetVector("_Impostor").x));
            var fit = ImpostorTrim.Fit(alpha, w, h, views);
            if (fit == null) return -1f;
            var poly = fit.Value;

            var pos = ImpostorTrim.Positions(poly, hw, yAtV0, yAtV1);
            Vector3 n = prim.Normals != null && prim.Normals.Length > 0 ? prim.Normals[0] : Vector3.back;
            var nrm = new Vector3[pos.Length];
            for (int i = 0; i < nrm.Length; i++) nrm[i] = n;
            string name = mesh.name;
            mesh.Clear();
            mesh.name = name;
            mesh.SetVertexBufferParams(pos.Length,
                new VertexAttributeDescriptor(VertexAttribute.Position, VertexAttributeFormat.Float32, 3),
                new VertexAttributeDescriptor(VertexAttribute.Normal, VertexAttributeFormat.Float32, 3),
                new VertexAttributeDescriptor(VertexAttribute.TexCoord0, VertexAttributeFormat.Float32, 2));
            mesh.SetVertices(pos);
            mesh.SetNormals(nrm);
            mesh.SetUVs(0, poly.Uv);
            mesh.SetIndexBufferParams(poly.Triangles.Length, IndexFormat.UInt16);
            mesh.SetTriangles(poly.Triangles, 0, false);
            // The billboard turns about its up axis: bounds of the full turn (instanced draws cull by cell bounds anyway).
            float y0 = Mathf.Min(yAtV0, yAtV1), y1 = Mathf.Max(yAtV0, yAtV1);
            mesh.bounds = new Bounds(new Vector3(0f, (y0 + y1) * 0.5f, 0f), new Vector3(2f * hw, y1 - y0, 2f * hw));
            mesh.UploadMeshData(true);
            return poly.Area;
        }

        public static void RunBatch()
        {
            string region = "bialystok-industrial-c";
            var args = System.Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length - 1; i++) if (args[i] == "-region") region = args[i + 1];
            string setPath = $"Assets/_Generated/World/{region}/Instances.asset";
            var set = AssetDatabase.LoadAssetAtPath<WorldInstanceSet>(setPath);
            if (set == null) { Debug.LogError($"[IMPTRIM] no {setPath}"); EditorApplication.Exit(2); return; }
            var lib = GlbReader.Load(Path.Combine(EditorTools.RepoRoot, "art-source", "world", "vegetation", "trees_lod2.glb"));
            int done = 0, skipped = 0;
            float sum = 0f;
            foreach (var p in set.prototypes)
            {
                if (p == null || p.lods == null || !p.name.StartsWith("tree_")) continue;
                var quad = lib.Find(p.name + ".lod2");
                if (quad == null) continue;
                int l = p.lods.Length - 1;
                var mat = set.materials[p.materialStart[l]];
                float area = Apply(p.lods[l], quad, mat);
                if (area < 0f) { skipped++; Debug.LogWarning($"[IMPTRIM] {p.name}: unchanged"); continue; }
                done++; sum += area;
                Debug.Log($"[IMPTRIM] {p.name}.lod2 {p.lods[l].vertexCount} verts, area {area:P0} of the quad ({mat.name})");
                EditorUtility.SetDirty(p.lods[l]);
            }
            EditorUtility.SetDirty(set);
            AssetDatabase.SaveAssets();
            Debug.Log($"[IMPTRIM] done {done} impostors (mean area {(done > 0 ? sum / done : 0f):P0}), skipped {skipped}");
            if (Application.isBatchMode) EditorApplication.Exit(done > 0 && skipped == 0 ? 0 : 1);
        }
    }
}
