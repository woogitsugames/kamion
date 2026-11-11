using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.World.Import
{
    /// <summary>
    /// Builds the meshes the player ships (ADR 0012):
    /// - <see cref="Compact"/>: one Unity mesh from glTF primitives (one submesh per primitive) with compact vertex
    ///   formats: position float32×3 (absolute region metres: half precision would be 6–12 cm at 128–256 m), normal
    ///   SNorm8×4 (or float16×4 where the device/editor rejects SNorm8), COLOR_0 UNorm8×4 only where a shader reads it
    ///   (terrain ground masks), TEXCOORD_0 float16×2 only where a material samples a texture. TEXCOORD_1 is dropped except for
    ///   far facades (window grid, ADR 0015). Meshes are not readable at run time.
    /// - <see cref="TerrainBand"/>: "fine near roads, coarse elsewhere" terrain from a chunk's terrain grid.
    /// - <see cref="PositionsOnly"/>: collision meshes.
    /// </summary>
    public static class WorldMeshBake
    {
        public struct Options
        {
            public bool Uv0;
            /// <summary>TEXCOORD_1 float16×2: LOD1 far-facade window grid (ADR 0015). Zero where a primitive has none.</summary>
            public bool Uv1;
            /// <summary>Road-only missing data: preserve the shader no-lane sentinel; other layers keep zero defaults.</summary>
            public bool RoadWearSentinel;
            public bool Colors;
        }

        static bool? s_SNorm8Normals;

        /// <summary>SNorm8×4 normals where Unity accepts them for the active build target, otherwise float16×4.</summary>
        static VertexAttributeFormat NormalFormat()
        {
            if (s_SNorm8Normals == null)
            {
                var m = new Mesh();
                try
                {
                    m.SetVertexBufferParams(3, new VertexAttributeDescriptor(VertexAttribute.Position), new VertexAttributeDescriptor(VertexAttribute.Normal, VertexAttributeFormat.SNorm8, 4));
                    s_SNorm8Normals = true;
                }
                catch (Exception) { s_SNorm8Normals = false; }
                UnityEngine.Object.DestroyImmediate(m);
                Debug.Log($"[BAKE] normal vertex format: {(s_SNorm8Normals.Value ? "SNorm8x4" : "Float16x4")}");
            }
            return s_SNorm8Normals.Value ? VertexAttributeFormat.SNorm8 : VertexAttributeFormat.Float16;
        }

        /// <summary>Merges primitives into one mesh (submesh per primitive) with compact formats.</summary>
        public static Mesh Compact(string name, IList<GlbReader.Primitive> prims, Options o)
        {
            int nv = 0;
            foreach (var p in prims) nv += p.Positions.Length;
            var pos = new Vector3[nv];
            var nrm = new Vector3[nv];
            var uv = o.Uv0 ? new Vector2[nv] : null;
            var uv1 = o.Uv1 ? new Vector2[nv] : null;
            var col = o.Colors ? new Color32[nv] : null;
            var subs = new List<int[]>();
            int b = 0;
            foreach (var p in prims)
            {
                Array.Copy(p.Positions, 0, pos, b, p.Positions.Length);
                if (p.Normals != null) Array.Copy(p.Normals, 0, nrm, b, p.Normals.Length);
                else for (int i = 0; i < p.Positions.Length; i++) nrm[b + i] = Vector3.up;
                if (uv != null && p.Uv0 != null) Array.Copy(p.Uv0, 0, uv, b, p.Uv0.Length);
                if (uv1 != null)
                {
                    if (p.Uv1 != null) Array.Copy(p.Uv1, 0, uv1, b, p.Uv1.Length);
                    else if (o.RoadWearSentinel)
                        for (int i = 0; i < p.Positions.Length; i++) uv1[b + i] = new Vector2(-1f, 5f);
                }
                if (col != null)
                {
                    if (p.Colors != null) Array.Copy(p.Colors, 0, col, b, p.Colors.Length);
                    else for (int i = 0; i < p.Positions.Length; i++) col[b + i] = new Color32(255, 0, 0, 0);
                }
                var idx = new int[p.Indices.Length];
                for (int i = 0; i < idx.Length; i++) idx[i] = p.Indices[i] + b;
                subs.Add(idx);
                b += p.Positions.Length;
            }
            return Build(name, pos, nrm, uv, col, subs, uv1);
        }

        public static Mesh Build(string name, Vector3[] pos, Vector3[] nrm, Vector2[] uv, Color32[] col, List<int[]> subs, Vector2[] uv1 = null)
        {
            int nv = pos.Length;
            var nf = NormalFormat();
            int nsize = nf == VertexAttributeFormat.SNorm8 ? 4 : 8;
            var attrs = new List<VertexAttributeDescriptor>
            {
                new VertexAttributeDescriptor(VertexAttribute.Position, VertexAttributeFormat.Float32, 3),
                new VertexAttributeDescriptor(VertexAttribute.Normal, nf, 4),
            };
            int stride = 12 + nsize;
            if (col != null) { attrs.Add(new VertexAttributeDescriptor(VertexAttribute.Color, VertexAttributeFormat.UNorm8, 4)); stride += 4; }
            if (uv != null) { attrs.Add(new VertexAttributeDescriptor(VertexAttribute.TexCoord0, VertexAttributeFormat.Float16, 2)); stride += 4; }
            if (uv1 != null) { attrs.Add(new VertexAttributeDescriptor(VertexAttribute.TexCoord1, VertexAttributeFormat.Float16, 2)); stride += 4; }

            var data = new byte[nv * stride];
            for (int i = 0; i < nv; i++)
            {
                int o = i * stride;
                WriteF(data, o, pos[i].x); WriteF(data, o + 4, pos[i].y); WriteF(data, o + 8, pos[i].z);
                o += 12;
                Vector3 n = nrm[i].sqrMagnitude > 1e-12f ? nrm[i].normalized : Vector3.up;
                if (nsize == 4)
                {
                    data[o] = S8(n.x); data[o + 1] = S8(n.y); data[o + 2] = S8(n.z); data[o + 3] = 0;
                }
                else
                {
                    WriteH(data, o, n.x); WriteH(data, o + 2, n.y); WriteH(data, o + 4, n.z); WriteH(data, o + 6, 0f);
                }
                o += nsize;
                if (col != null) { var c = col[i]; data[o] = c.r; data[o + 1] = c.g; data[o + 2] = c.b; data[o + 3] = c.a; o += 4; }
                if (uv != null) { WriteH(data, o, uv[i].x); WriteH(data, o + 2, uv[i].y); o += 4; }
                if (uv1 != null) { WriteH(data, o, uv1[i].x); WriteH(data, o + 2, uv1[i].y); }
            }

            var m = new Mesh { name = name };
            m.SetVertexBufferParams(nv, attrs.ToArray());
            m.SetVertexBufferData(data, 0, 0, data.Length, 0, MeshUpdateFlags.DontValidateIndices | MeshUpdateFlags.DontRecalculateBounds);
            int ni = 0;
            foreach (var s in subs) ni += s.Length;
            var fmt = nv > 65535 ? IndexFormat.UInt32 : IndexFormat.UInt16;
            m.SetIndexBufferParams(ni, fmt);
            m.subMeshCount = subs.Count;
            int start = 0;
            if (fmt == IndexFormat.UInt16)
            {
                var all = new ushort[ni];
                foreach (var s in subs) { for (int i = 0; i < s.Length; i++) all[start + i] = (ushort)s[i]; start += s.Length; }
                m.SetIndexBufferData(all, 0, 0, ni, MeshUpdateFlags.DontValidateIndices | MeshUpdateFlags.DontRecalculateBounds);
            }
            else
            {
                var all = new int[ni];
                foreach (var s in subs) { Array.Copy(s, 0, all, start, s.Length); start += s.Length; }
                m.SetIndexBufferData(all, 0, 0, ni, MeshUpdateFlags.DontValidateIndices | MeshUpdateFlags.DontRecalculateBounds);
            }
            start = 0;
            Vector3 mn = Vector3.positiveInfinity, mx = Vector3.negativeInfinity;
            foreach (var p in pos) { mn = Vector3.Min(mn, p); mx = Vector3.Max(mx, p); }
            var bounds = nv > 0 ? new Bounds((mn + mx) * 0.5f, mx - mn) : new Bounds();
            for (int s = 0; s < subs.Count; s++)
            {
                m.SetSubMesh(s, new SubMeshDescriptor(start, subs[s].Length, MeshTopology.Triangles), MeshUpdateFlags.DontRecalculateBounds | MeshUpdateFlags.DontValidateIndices);
                start += subs[s].Length;
            }
            m.bounds = bounds;
            m.RecalculateBounds(MeshUpdateFlags.DontValidateIndices);
            m.UploadMeshData(true);   // not readable in the player: CPU copy freed after upload
            return m;
        }

        /// <summary>Position-only mesh for MeshColliders (readable: PhysX cooks it at load, WorldCollisionCooker).</summary>
        public static Mesh PositionsOnly(string name, Vector3[] pos, int[] tris)
        {
            var m = new Mesh { name = name, indexFormat = pos.Length > 65535 ? IndexFormat.UInt32 : IndexFormat.UInt16 };
            m.SetVertices(pos);
            m.SetTriangles(tris, 0, true);
            // Cooked at load by WorldCollisionCooker (Physics.BakeMesh on worker threads), so the CPU copy must stay
            // readable in the player (prebaked PhysX data cost ~17 MB of APK; ADR 0012 §6).
            m.UploadMeshData(false);
            return m;
        }

        /// <summary>Collects one primitive's triangles as a compact vertex set.</summary>
        public static (Vector3[] pos, int[] tris) Compacted(Vector3[] positions, int[] indices)
        {
            var map = new Dictionary<int, int>();
            var v2 = new List<Vector3>();
            var t = new int[indices.Length];
            for (int i = 0; i < indices.Length; i++)
            {
                if (!map.TryGetValue(indices[i], out int ni)) { ni = v2.Count; map[indices[i]] = ni; v2.Add(positions[indices[i]]); }
                t[i] = ni;
            }
            return (v2.ToArray(), t);
        }

        static void WriteF(byte[] d, int o, float v)
        {
            var b = BitConverter.GetBytes(v);
            d[o] = b[0]; d[o + 1] = b[1]; d[o + 2] = b[2]; d[o + 3] = b[3];
        }

        static void WriteH(byte[] d, int o, float v)
        {
            ushort h = Mathf.FloatToHalf(v);
            d[o] = (byte)(h & 0xFF); d[o + 1] = (byte)(h >> 8);
        }

        static byte S8(float v) => (byte)(sbyte)Mathf.Clamp(Mathf.RoundToInt(v * 127f), -127, 127);

        /// <summary>GPU-side bytes of a mesh (vertex streams + indices) - the run-time cost of a non-readable mesh.</summary>
        public static long GpuBytes(Mesh m)
        {
            if (m == null) return 0;
            long v = 0;
            for (int s = 0; s < m.vertexBufferCount; s++) v += (long)m.GetVertexBufferStride(s) * m.vertexCount;
            long i = 0;
            for (int s = 0; s < m.subMeshCount; s++) i += (long)m.GetSubMesh(s).indexCount;
            return v + i * (m.indexFormat == IndexFormat.UInt16 ? 2 : 4);
        }

        // ================================================================================== terrain band
        /// <summary>
        /// Rebuilds a chunk terrain from its grid (spacing <paramref name="s"/>, skirts dropped): blocks of
        /// <paramref name="block"/>×<paramref name="block"/> cells keep spacing s where any vertex lies within
        /// <paramref name="bandM"/> of a road or paved area (COLOR_0.R = distance / 20 m), dilated by one block; all other
        /// blocks use spacing 2s. Watertight without skirts inside the chunk: the odd vertices on every fine-coarse block
        /// edge are moved onto the coarse edge (linear interpolation). On the chunk border the odd vertices are always
        /// interpolated (both neighbours do the same, whatever their own blocks are), and a 1.5 m skirt hides cracks
        /// against a neighbour drawn at another LOD. Normals from central differences of the grid.
        /// </summary>
        public static Mesh TerrainBand(string name, GlbReader.Primitive grid, float s, Vector2 minEN, Vector2 maxEN, int block, float bandM, out float fineFraction, int dilation = 1)
        {
            var (pos, nrm, col, tris) = TerrainBandData(name, grid, s, minEN, maxEN, block, bandM, out fineFraction, dilation);
            return Build(name, pos, nrm, null, col, new List<int[]> { tris });
        }

        /// <summary>Raw arrays of <see cref="TerrainBand"/> (also used for the terrain collider).</summary>
        public static (Vector3[] pos, Vector3[] nrm, Color32[] col, int[] tris) TerrainBandData(string name, GlbReader.Primitive grid, float s, Vector2 minEN, Vector2 maxEN, int block, float bandM, out float fineFraction, int dilation = 1)
        {
            int nx = Mathf.RoundToInt((maxEN.x - minEN.x) / s) + 1, nz = Mathf.RoundToInt((maxEN.y - minEN.y) / s) + 1;
            var H = new float[nx * nz];
            var C = new Color32[nx * nz];
            for (int i = 0; i < H.Length; i++) H[i] = float.NegativeInfinity;
            var pp = grid.Positions;
            for (int i = 0; i < pp.Length; i++)
            {
                float fx = (pp[i].x - minEN.x) / s, fz = (pp[i].z - minEN.y) / s;
                int gx = Mathf.RoundToInt(fx), gz = Mathf.RoundToInt(fz);
                if (gx < 0 || gz < 0 || gx >= nx || gz >= nz || Mathf.Abs(fx - gx) > 0.01f || Mathf.Abs(fz - gz) > 0.01f) continue;
                int k = gz * nx + gx;
                if (pp[i].y > H[k]) { H[k] = pp[i].y; C[k] = grid.Colors != null ? grid.Colors[i] : new Color32(255, 0, 0, 0); }
            }
            for (int i = 0; i < H.Length; i++)
                if (float.IsNegativeInfinity(H[i])) throw new InvalidOperationException($"{name}: terrain grid hole at {i % nx},{i / nx} (spacing {s} m)");

            int cellsX = nx - 1, cellsZ = nz - 1;
            int bx = cellsX / block, bz = cellsZ / block;
            if (bx * block != cellsX || bz * block != cellsZ || block % 2 != 0) throw new InvalidOperationException($"{name}: grid {cellsX}x{cellsZ} not divisible into {block}-cell blocks");
            byte rLimit = (byte)Mathf.Clamp(Mathf.RoundToInt(bandM / 20f * 255f), 1, 254);
            var near = new bool[bx * bz];
            for (int j = 0; j < bz; j++)
            for (int i = 0; i < bx; i++)
            {
                bool f = false;
                for (int z = j * block; z <= (j + 1) * block && !f; z++)
                for (int x = i * block; x <= (i + 1) * block && !f; x++)
                    f = C[z * nx + x].r < rLimit;
                near[j * bx + i] = f;
            }
            var fine = new bool[bx * bz];
            int fineCount = 0;
            for (int j = 0; j < bz; j++)
            for (int i = 0; i < bx; i++)
            {
                bool f = false;
                for (int dj = -dilation; dj <= dilation && !f; dj++)
                for (int di = -dilation; di <= dilation && !f; di++)
                {
                    int a = i + di, c = j + dj;
                    if (a >= 0 && c >= 0 && a < bx && c < bz) f = near[c * bx + a];
                }
                fine[j * bx + i] = f;
                if (f) fineCount++;
            }
            fineFraction = (float)fineCount / (bx * bz);

            // Adjusted heights: odd vertices on fine/coarse block edges and on the chunk border lie on the coarse edge.
            var A = (float[])H.Clone();
            void InterpX(int z, int x0, int x1) { for (int x = x0 + 1; x < x1; x += 2) A[z * nx + x] = 0.5f * (H[z * nx + x - 1] + H[z * nx + x + 1]); }
            void InterpZ(int x, int z0, int z1) { for (int z = z0 + 1; z < z1; z += 2) A[z * nx + x] = 0.5f * (H[(z - 1) * nx + x] + H[(z + 1) * nx + x]); }
            for (int j = 0; j < bz; j++)
            for (int i = 0; i < bx; i++)
            {
                if (fine[j * bx + i]) continue;
                int x0 = i * block, x1 = x0 + block, z0 = j * block, z1 = z0 + block;
                InterpX(z0, x0, x1); InterpX(z1, x0, x1); InterpZ(x0, z0, z1); InterpZ(x1, z0, z1);
            }
            InterpX(0, 0, cellsX); InterpX(cellsZ, 0, cellsX); InterpZ(0, 0, cellsZ); InterpZ(cellsX, 0, cellsZ);

            var map = new int[nx * nz];
            for (int i = 0; i < map.Length; i++) map[i] = -1;
            var pos = new List<Vector3>();
            var nrm = new List<Vector3>();
            var col = new List<Color32>();
            var tris = new List<int>();
            int V(int x, int z, int step)
            {
                int k = z * nx + x;
                if (map[k] >= 0) return map[k];
                map[k] = pos.Count;
                pos.Add(new Vector3(minEN.x + x * s, A[k], minEN.y + z * s));
                int xa = Mathf.Max(0, x - step), xb = Mathf.Min(nx - 1, x + step), za = Mathf.Max(0, z - step), zb = Mathf.Min(nz - 1, z + step);
                float dx = (A[z * nx + xb] - A[z * nx + xa]) / ((xb - xa) * s), dz = (A[zb * nx + x] - A[za * nx + x]) / ((zb - za) * s);
                nrm.Add(new Vector3(-dx, 1f, -dz).normalized);
                col.Add(C[k]);
                return map[k];
            }
            void Quad(int x, int z, int st)
            {
                int a = V(x, z, st), b = V(x + st, z, st), c = V(x + st, z + st, st), d = V(x, z + st, st);
                // Unity is left-handed with Y up: clockwise seen from above (+Y) = front face.
                tris.Add(a); tris.Add(d); tris.Add(c);
                tris.Add(a); tris.Add(c); tris.Add(b);
            }
            for (int j = 0; j < bz; j++)
            for (int i = 0; i < bx; i++)
            {
                int st = fine[j * bx + i] ? 1 : 2;
                for (int z = j * block; z < (j + 1) * block; z += st)
                for (int x = i * block; x < (i + 1) * block; x += st)
                    Quad(x, z, st);
            }

            // Skirt along the chunk border (vertices of the top border, hanging 1.5 m), facing outwards.
            void Skirt(int x0, int z0, int dx, int dz, int n, bool flip)
            {
                for (int t = 0; t < n; t++)
                {
                    int xa = x0 + dx * t, za = z0 + dz * t, xb = xa + dx, zb = za + dz;
                    int a = V(xa, za, 1), b = V(xb, zb, 1);
                    int a2 = pos.Count; pos.Add(pos[a] - new Vector3(0f, 1.5f, 0f)); nrm.Add(nrm[a]); col.Add(col[a]);
                    int b2 = pos.Count; pos.Add(pos[b] - new Vector3(0f, 1.5f, 0f)); nrm.Add(nrm[b]); col.Add(col[b]);
                    if (flip) { tris.Add(a); tris.Add(b2); tris.Add(b); tris.Add(a); tris.Add(a2); tris.Add(b2); }
                    else { tris.Add(a); tris.Add(b); tris.Add(b2); tris.Add(a); tris.Add(b2); tris.Add(a2); }
                }
            }
            Skirt(0, 0, 1, 0, cellsX, false);        // south edge
            Skirt(0, cellsZ, 1, 0, cellsX, true);    // north edge
            Skirt(0, 0, 0, 1, cellsZ, true);         // west edge
            Skirt(cellsX, 0, 0, 1, cellsZ, false);   // east edge

            return (pos.ToArray(), nrm.ToArray(), col.ToArray(), tris.ToArray());
        }
    }
}
