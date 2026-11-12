using System;
using UnityEngine;

namespace Game.World
{
    /// <summary>
    /// ADR 0136: tight impostor billboard. The baked impostor views (tools/blender/world/make_trees.py, 6 views of 256 x 384)
    /// cover only 6-13 % of their quad, so ~90 % of the impostor fragments (depth pass with discard + colour pass) were
    /// rasterised only to be clipped; on the A16 (Mali-G57, Low) the impostors cost up to 6.6 ms GPU in the stand along
    /// G3-B. This replaces the quad with a polygon of <see cref="Bands"/> horizontal bands whose left / right edges enclose
    /// the union of the alpha of ALL views (one mesh serves every view and the cross-fade of two views), dilated by
    /// <see cref="DilatePx"/> texels for the alpha mips. Every texel above <see cref="AlphaFloor"/> lies inside the polygon,
    /// so the image is unchanged (the clipped area was transparent); the fragments drop to ~1/3 of the quad.
    ///
    /// Vertex convention of Kamion/Vegetation _IMPOSTOR (Impostor() in Vegetation.shader): the billboard's side offset is
    /// (uv.x * 2 - 1) * |positionOS.x| and its height positionOS.y, so every vertex carries |x| = the quad half width and
    /// y mapped linearly from uv.y exactly as on the source quad. Pure math (no editor API) so EditMode tests reach it.
    /// </summary>
    public static class ImpostorTrim
    {
        public const int Bands = 6;
        public const int DilatePx = 6;          // 2.3 % of a 256 px view: covers the coverage-preserving alpha mips to mip 2
        public const byte AlphaFloor = 4;       // texels at or below are transparent at any cutoff in use (0.5)

        public struct Polygon
        {
            public Vector2[] Uv;                // per vertex (u in [0, 1] of one view, v in [0, 1]); pairs left, right per band edge
            public int[] Triangles;
            public float Area;                  // share of the unit quad covered by the polygon
        }

        /// <summary>
        /// Fit the band polygon to an atlas of <paramref name="views"/> side-by-side views. <paramref name="alpha"/> is row-major,
        /// row 0 = v 0 (Unity texture convention, bottom row). Returns null when the atlas has no opaque texel.
        /// </summary>
        public static Polygon? Fit(byte[] alpha, int width, int height, int views, int bands = Bands, int dilate = DilatePx)
        {
            if (alpha == null || views < 1 || width < views || height < 2 || alpha.Length < width * height) throw new ArgumentException("bad atlas");
            int w = width / views;
            // Union of the views' coverage per row: [min, max] texel column (view-local), -1 when empty.
            var rowMin = new int[height];
            var rowMax = new int[height];
            for (int y = 0; y < height; y++)
            {
                int mn = int.MaxValue, mx = -1;
                int row = y * width;
                for (int k = 0; k < views; k++)
                {
                    int o = row + k * w;
                    for (int x = 0; x < w; x++)
                        if (alpha[o + x] > AlphaFloor) { if (x < mn) mn = x; if (x > mx) mx = x; }
                }
                rowMin[y] = mx < 0 ? -1 : mn;
                rowMax[y] = mx;
            }
            int y0 = -1, y1 = -1;
            for (int y = 0; y < height; y++) if (rowMax[y] >= 0) { if (y0 < 0) y0 = y; y1 = y; }
            if (y0 < 0) return null;
            // Dilation: rows grow by `dilate`, columns by `dilate` (square structuring element, conservative).
            int r0 = Math.Max(0, y0 - dilate), r1 = Math.Min(height - 1, y1 + dilate);
            bands = Math.Max(1, Math.Min(bands, r1 - r0 + 1));
            var edge = new int[bands + 1];
            for (int b = 0; b <= bands; b++) edge[b] = r0 + (int)Math.Round((r1 + 1 - r0) * (double)b / bands);
            var bl = new int[bands];
            var br = new int[bands];
            for (int b = 0; b < bands; b++)
            {
                int mn = int.MaxValue, mx = -1;
                // Rows of the band plus the dilation reach of the neighbouring rows.
                int ya = Math.Max(0, edge[b] - dilate), yb = Math.Min(height - 1, edge[b + 1] - 1 + dilate);
                for (int y = ya; y <= yb; y++)
                    if (rowMax[y] >= 0) { mn = Math.Min(mn, rowMin[y]); mx = Math.Max(mx, rowMax[y]); }
                if (mx < 0) { mn = w / 2; mx = w / 2; }   // empty band (dilated margin): degenerate width, still a valid edge
                bl[b] = Math.Max(0, mn - dilate);
                br[b] = Math.Min(w, mx + 1 + dilate);   // exclusive texel edge
            }
            var uv = new Vector2[(bands + 1) * 2];
            float area = 0f;
            float pl = 0f, pr = 0f, pv = 0f;
            for (int j = 0; j <= bands; j++)
            {
                // A band edge takes the wider of the two bands it separates: each trapezoid then encloses its band.
                int l = j == 0 ? bl[0] : j == bands ? bl[bands - 1] : Math.Min(bl[j - 1], bl[j]);
                int r = j == 0 ? br[0] : j == bands ? br[bands - 1] : Math.Max(br[j - 1], br[j]);
                float v = edge[j] / (float)height, ul = l / (float)w, ur = r / (float)w;
                uv[2 * j] = new Vector2(ul, v);
                uv[2 * j + 1] = new Vector2(ur, v);
                if (j > 0) area += ((pr - pl) + (ur - ul)) * 0.5f * (v - pv);
                pl = ul; pr = ur; pv = v;
            }
            var tri = new int[bands * 6];
            for (int b = 0; b < bands; b++)
            {
                int a = 2 * b, c = a + 2;
                // left-bottom, right-bottom, right-top / left-bottom, right-top, left-top (same winding as the source quad;
                // the impostor material is double sided anyway)
                tri[6 * b + 0] = a; tri[6 * b + 1] = a + 1; tri[6 * b + 2] = c + 1;
                tri[6 * b + 3] = a; tri[6 * b + 4] = c + 1; tri[6 * b + 5] = c;
            }
            return new Polygon { Uv = uv, Triangles = tri, Area = area };
        }

        /// <summary>
        /// Object-space vertices of the polygon for a source quad with half width <paramref name="halfWidth"/> and height
        /// y = <paramref name="yAtV0"/> + v * (<paramref name="yAtV1"/> - <paramref name="yAtV0"/>) (read off the source quad).
        /// </summary>
        public static Vector3[] Positions(Polygon p, float halfWidth, float yAtV0, float yAtV1)
        {
            var pos = new Vector3[p.Uv.Length];
            for (int i = 0; i < pos.Length; i++)
                // |x| must stay the full half width: the shader places the vertex at (uv.x * 2 - 1) * |x| (the sign only
                // keeps a plain mesh preview on the right side).
                pos[i] = new Vector3(p.Uv[i].x < 0.5f ? -halfWidth : halfWidth, yAtV0 + p.Uv[i].y * (yAtV1 - yAtV0), 0f);
            return pos;
        }

        /// <summary>True when every texel above <see cref="AlphaFloor"/> of every view lies inside the polygon (test helper).</summary>
        public static bool Encloses(Polygon p, byte[] alpha, int width, int height, int views)
        {
            int w = width / views;
            for (int y = 0; y < height; y++)
                for (int k = 0; k < views; k++)
                    for (int x = 0; x < w; x++)
                    {
                        if (alpha[y * width + k * w + x] <= AlphaFloor) continue;
                        float u = (x + 0.5f) / w, v = (y + 0.5f) / height;
                        if (!Inside(p, u, v)) return false;
                    }
            return true;
        }

        static bool Inside(Polygon p, float u, float v)
        {
            int n = p.Uv.Length / 2;
            for (int j = 0; j < n - 1; j++)
            {
                Vector2 l0 = p.Uv[2 * j], r0 = p.Uv[2 * j + 1], l1 = p.Uv[2 * j + 2], r1 = p.Uv[2 * j + 3];
                if (v < l0.y || v > l1.y) continue;
                float t = l1.y > l0.y ? (v - l0.y) / (l1.y - l0.y) : 0f;
                float ul = Mathf.Lerp(l0.x, l1.x, t), ur = Mathf.Lerp(r0.x, r1.x, t);
                if (u >= ul && u <= ur) return true;
            }
            return false;
        }
    }
}
