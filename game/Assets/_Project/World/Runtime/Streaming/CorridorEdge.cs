using System;

namespace Game.World.Streaming
{
    /// <summary>Axis-aligned rectangle in a common horizontal frame [m] (e = east, n = north). Plain data, no Unity types.</summary>
    [Serializable]
    public struct EdgeRect
    {
        public float minE, minN, maxE, maxN;

        public EdgeRect(float minE, float minN, float maxE, float maxN)
        {
            this.minE = minE; this.minN = minN; this.maxE = maxE; this.maxN = maxN;
        }
    }

    /// <summary>
    /// Outer edge of the streamed corridor for the world safety net (ADR 0082, ADR 0273 §10 pkt 5). The drivable world
    /// while streaming is the union of the Ready tiles' drivable rectangles; a side of a Ready tile counts as an edge
    /// ("Koniec mapy", stop) unless it is a seam with a cardinal neighbour from tile_graph.json that is Ready or on its way
    /// (Loading / Activating: the streamer is bringing it in, the closures still stand - a loading stall, not the end of
    /// the map). An Unloaded / Unloading neighbour (left behind, not in the build, over budget) turns its seam back into an
    /// outer edge. A corner whose two sides are open but whose diagonal tile is absent or not open (inner corner of an L)
    /// counts as a point. Pure logic over caller-owned arrays (indexed like <see cref="TileGraph.Tiles"/>); no allocations,
    /// no Unity calls.
    /// </summary>
    public static class CorridorEdge
    {
        /// <summary>
        /// An open side reaches the tile rectangle (the seam) plus this tolerance [m], so a point on the seam - or in the
        /// gap between two drivable rectangles inset from their tiles - is inside one of the two tiles. WORKING_VALUE.
        /// </summary>
        public const float SeamToleranceM = 0.5f;

        static readonly TileSide[] k_Corners = { TileSide.NE, TileSide.SE, TileSide.SW, TileSide.NW };

        static bool IsCardinal(TileSide s) => s == TileSide.N || s == TileSide.E || s == TileSide.S || s == TileSide.W;

        /// <summary>A neighbour in this state keeps the seam open: Ready, or being loaded / activated by the streamer.</summary>
        public static bool KeepsSeamOpen(TileState s) => s == TileState.Ready || s == TileState.Loading || s == TileState.Activating;

        /// <summary>Sides of tile <paramref name="i"/> that are seams with an open cardinal neighbour (None when i is not Ready).</summary>
        public static TileSide OpenSides(TileGraph graph, TileState[] state, int i)
        {
            if (state[i] != TileState.Ready) return TileSide.None;
            TileSide open = TileSide.None;
            var nb = graph.Neighbors[i];
            var ns = graph.NeighborSides[i];
            for (int k = 0; k < nb.Length; k++)
                if (IsCardinal(ns[k]) && nb[k] < state.Length && KeepsSeamOpen(state[nb[k]])) open |= ns[k];
            return open;
        }

        /// <summary>
        /// Corner mask (<see cref="EdgeSides.CornerBit"/>) of the corners of tile <paramref name="i"/> whose two sides are
        /// open but whose diagonal tile is missing or does not keep its seams open (<see cref="KeepsSeamOpen"/>).
        /// </summary>
        public static int MissingCorners(TileGraph graph, TileState[] state, int i, TileSide open)
        {
            int mask = 0;
            for (int c = 0; c < k_Corners.Length; c++)
            {
                var corner = k_Corners[c];
                if ((open & corner) != corner) continue;
                int j = graph.NeighborOn(i, corner);
                if (j < 0 || j >= state.Length || !KeepsSeamOpen(state[j])) mask |= EdgeSides.CornerBit(corner);
            }
            return mask;
        }

        /// <summary>
        /// Distance from (e, n) to the outer edge of the union of the Ready tiles [m]: positive inside, negative outside
        /// (same convention as WorldBoundary.InsideDistance).
        /// <paramref name="drivable"/> = drivable rectangle of each tile (WorldBoundary of its scene), <paramref name="tile"/> =
        /// its tile rectangle from the graph, both in the frame of (e, n). Entries of tiles that are not Ready are ignored.
        /// False when no tile is Ready.
        /// </summary>
        public static bool InsideDistance(TileGraph graph, TileState[] state, EdgeRect[] drivable, EdgeRect[] tile, float e, float n, out float inside)
        {
            inside = float.MinValue;
            bool any = false, contained = false;
            int count = Math.Min(graph.Count, Math.Min(state.Length, Math.Min(drivable.Length, tile.Length)));
            for (int i = 0; i < count; i++)
            {
                if (state[i] != TileState.Ready) continue;
                any = true;
                var d = drivable[i];
                var t = tile[i];
                var open = OpenSides(graph, state, i);
                float minE = (open & TileSide.W) != 0 ? Math.Min(d.minE, t.minE) - SeamToleranceM : d.minE;
                float maxE = (open & TileSide.E) != 0 ? Math.Max(d.maxE, t.maxE) + SeamToleranceM : d.maxE;
                float minN = (open & TileSide.S) != 0 ? Math.Min(d.minN, t.minN) - SeamToleranceM : d.minN;
                float maxN = (open & TileSide.N) != 0 ? Math.Max(d.maxN, t.maxN) + SeamToleranceM : d.maxN;
                if (e >= minE && e <= maxE && n >= minN && n <= maxN)
                {
                    float v = EdgeSides.UnionInsideDistance(e, n, minE, minN, maxE, maxN, open, 0);
                    // Inner corner of an L: both sides open, diagonal missing -> the tile corner on the seams is an edge point.
                    int missing = MissingCorners(graph, state, i, open);
                    if ((missing & EdgeSides.CornerBit(TileSide.NE)) != 0) v = Math.Min(v, Dist(e, n, t.maxE, t.maxN));
                    if ((missing & EdgeSides.CornerBit(TileSide.SE)) != 0) v = Math.Min(v, Dist(e, n, t.maxE, t.minN));
                    if ((missing & EdgeSides.CornerBit(TileSide.SW)) != 0) v = Math.Min(v, Dist(e, n, t.minE, t.minN));
                    if ((missing & EdgeSides.CornerBit(TileSide.NW)) != 0) v = Math.Min(v, Dist(e, n, t.minE, t.maxN));
                    inside = contained ? Math.Max(inside, v) : v;
                    contained = true;
                }
                else if (!contained)
                {
                    // Outside every tile so far: Euclidean distance to this rectangle, negative; the nearest tile wins.
                    float ox = Math.Max(0f, Math.Max(minE - e, e - maxE));
                    float oz = Math.Max(0f, Math.Max(minN - n, n - maxN));
                    float v = -(float)Math.Sqrt(ox * ox + oz * oz);
                    if (v > inside) inside = v;
                }
            }
            return any;
        }

        static float Dist(float e, float n, float ce, float cn)
        {
            float a = e - ce, b = n - cn;
            return (float)Math.Sqrt(a * a + b * b);
        }
    }
}
