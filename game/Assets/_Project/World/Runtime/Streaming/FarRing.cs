using System;
using UnityEngine;

namespace Game.World.Streaming
{
    /// <summary>
    /// ADR 0354: the far field (ADR 0085 backdrop, compressed into &lt;= ~660 m beyond each tile) drawn as a ring BEYOND the
    /// set of loaded tiles instead of being switched off per direction. Every far-field sector stays on; the shader
    /// (<c>KamionFarRing.hlsl</c>) drops a far-field pixel when
    /// <list type="bullet">
    /// <item>it lies inside a loaded tile (Activating / Ready: real geometry is there), or</item>
    /// <item>another loaded tile is strictly nearer to it than the tile that owns the far field (nearest-rectangle
    ///   ownership: two loaded tiles never both draw the same backdrop spot, the nearer, less compressed one wins).</item>
    /// </list>
    /// The rectangles of the loaded tiles go to the shader as a global array (<see cref="RectsProperty"/>, Unity world
    /// XZ, refreshed by <see cref="WorldStreamer"/> on every state change and origin rebase). Far-field renderers are
    /// marked with <see cref="UserValue"/> (Renderer user value: per draw, SRP-Batcher compatible); a renderer without
    /// the mark is never clipped. Whole sectors that the rule hides everywhere are switched off on the CPU
    /// (<see cref="SectorVisible"/>, conservative) to save their vertex work.
    /// This class is the C# twin of the shader rule (tests) plus the sector cull; pure, no allocations.
    /// </summary>
    public static class FarRing
    {
        /// <summary>Size of the global rectangle array in the shader (<c>_KamionFarRects[16]</c>).</summary>
        public const int MaxRects = 16;
        /// <summary>Renderer user value of a far-field sector ("FARR"); must match KAMION_FAR_RING_USER_VALUE.</summary>
        public const uint UserValue = 0x46415252u;
        /// <summary>Local keyword of the Kamion/World Surface far-field clone with the pixel clip (opaque path only:
        /// the tile's own LOD1 far facades keep the variant without discard / early-Z loss).</summary>
        public const string ClipKeyword = "_FAR_RING_CLIP";
        public const string RectsProperty = "_KamionFarRects";
        public const string CountProperty = "_KamionFarRectCount";
        /// <summary>Half size of a tile rectangle when the owner is not among the loaded rectangles (far_field.py half).</summary>
        public const float DefaultHalfM = 1024f;
        /// <summary>Ownership tie tolerance [m]: on an exact tie both far fields draw (a line, no gap).</summary>
        public const float TieEpsM = 0.001f;

        /// <summary>A/B switch: false = the old per-direction rule (ADR 0311: sectors toward every graph neighbour off).
        /// Player / editor: <c>-farRing off</c> or environment <c>KAMION_FAR_RING=off</c>.</summary>
        public static bool Enabled { get; set; } = ReadSwitch(Environment.GetCommandLineArgs(), Environment.GetEnvironmentVariable("KAMION_FAR_RING"));

        public static bool ReadSwitch(string[] args, string env)
        {
            if (args != null)
                for (int i = 0; i + 1 < args.Length; i++)
                    if (string.Equals(args[i], "-farRing", StringComparison.OrdinalIgnoreCase)) return !IsOff(args[i + 1]);
            return !IsOff(env);
        }

        static bool IsOff(string v) =>
            v != null && (v.Equals("off", StringComparison.OrdinalIgnoreCase) || v == "0" || v.Equals("false", StringComparison.OrdinalIgnoreCase));

        /// <summary>Distance from (x, z) to rectangle r = (minX, minZ, maxX, maxZ); 0 inside.</summary>
        public static float RectDistance(float x, float z, Vector4 r)
        {
            float dx = Math.Max(Math.Max(r.x - x, x - r.z), 0f);
            float dz = Math.Max(Math.Max(r.y - z, z - r.w), 0f);
            return (float)Math.Sqrt(dx * dx + dz * dz);
        }

        public static bool Contains(Vector4 r, float x, float z) => x >= r.x && x <= r.z && z >= r.y && z <= r.w;

        /// <summary>
        /// Shader rule (KamionFarRingHidden): is a far-field pixel at (px, pz) of the tile centred at (cx, cz) hidden?
        /// The owner's rectangle is the loaded one containing its centre, else centre +- <see cref="DefaultHalfM"/>.
        /// </summary>
        public static bool Hidden(float px, float pz, float cx, float cz, Vector4[] rects, int count)
        {
            if (rects == null || count <= 0) return false;
            float dOwn = RectDistance(px, pz, new Vector4(cx - DefaultHalfM, cz - DefaultHalfM, cx + DefaultHalfM, cz + DefaultHalfM));
            float dOther = float.MaxValue;
            for (int i = 0; i < count && i < rects.Length; i++)
            {
                float d = RectDistance(px, pz, rects[i]);
                if (Contains(rects[i], cx, cz)) dOwn = d;
                else if (d < dOther) dOther = d;
            }
            return dOther < dOwn - TieEpsM;
        }

        /// <summary>
        /// Is any part of a far-field sector with world XZ bounds <paramref name="box"/> (minX, minZ, maxX, maxZ) possibly
        /// drawn? Conservative (true when unsure): false only when the box is split into
        /// <paramref name="cells"/> x <paramref name="cells"/> cells and every cell is either inside one loaded rectangle or
        /// owned by another loaded tile with a margin that holds over the whole cell (the ownership difference
        /// d_own - d_other is 2-Lipschitz, so a margin of twice the cell half-diagonal covers the cell).
        /// </summary>
        public static bool SectorVisible(Vector4 box, float cx, float cz, Vector4[] rects, int count, int cells = 16)
        {
            if (rects == null || count <= 0) return true;
            if (box.z < box.x || box.w < box.y) return false;   // empty mesh
            cells = Math.Max(1, cells);
            float sx = (box.z - box.x) / cells, sz = (box.w - box.y) / cells;
            float margin = (float)Math.Sqrt(sx * sx + sz * sz) + TieEpsM;   // 2 x half-diagonal
            for (int iz = 0; iz < cells; iz++)
                for (int ix = 0; ix < cells; ix++)
                {
                    float x0 = box.x + ix * sx, z0 = box.y + iz * sz;
                    var cell = new Vector4(x0, z0, x0 + sx, z0 + sz);
                    if (InsideOther(cell, cx, cz, rects, count)) continue;
                    float px = x0 + 0.5f * sx, pz = z0 + 0.5f * sz;
                    if (!OwnedElsewhere(px, pz, cx, cz, rects, count, margin)) return true;
                }
            return false;
        }

        // Cell inside a loaded rectangle other than the owner's own (geometry inside the owner tile is never clipped).
        static bool InsideOther(Vector4 cell, float cx, float cz, Vector4[] rects, int count)
        {
            for (int i = 0; i < count && i < rects.Length; i++)
            {
                var r = rects[i];
                if (Contains(r, cx, cz)) continue;
                if (cell.x >= r.x && cell.z <= r.z && cell.y >= r.y && cell.w <= r.w) return true;
            }
            return false;
        }

        static bool OwnedElsewhere(float px, float pz, float cx, float cz, Vector4[] rects, int count, float margin)
        {
            float dOwn = RectDistance(px, pz, new Vector4(cx - DefaultHalfM, cz - DefaultHalfM, cx + DefaultHalfM, cz + DefaultHalfM));
            float dOther = float.MaxValue;
            for (int i = 0; i < count && i < rects.Length; i++)
            {
                float d = RectDistance(px, pz, rects[i]);
                if (Contains(rects[i], cx, cz)) dOwn = d;
                else if (d < dOther) dOther = d;
            }
            return dOwn - dOther > margin;
        }
    }
}
