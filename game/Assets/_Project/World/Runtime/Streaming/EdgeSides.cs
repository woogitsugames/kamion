using System;

namespace Game.World.Streaming
{
    /// <summary>
    /// Which side of a region rectangle the edge objects belong to (ADR 0235), so the streamer can open exactly the
    /// seam between two ready tiles: the road closures (collider + boards, ADR 0169), the apron pieces and the far-field
    /// sector on that side. Pure geometry in region-local metres (e = east, n = north), no allocations.
    /// </summary>
    public static class EdgeSides
    {
        /// <summary>
        /// Side of the region edge a closure guards: the edge its road reaches when followed along the closure heading
        /// (degrees clockwise from north, towards the edge) - not simply the nearest edge, so a closure near a corner
        /// opens only with the neighbour its road actually leads into.
        /// </summary>
        public static TileSide ClosureSide(float e, float n, float headingDeg, float minE, float minN, float maxE, float maxN)
        {
            double h = headingDeg * Math.PI / 180.0;
            double de = Math.Sin(h), dn = Math.Cos(h);
            double tBest = double.MaxValue;
            TileSide best = TileSide.None;
            if (de > 1e-6) Try((maxE - e) / de, TileSide.E, ref tBest, ref best);
            if (de < -1e-6) Try((minE - e) / de, TileSide.W, ref tBest, ref best);
            if (dn > 1e-6) Try((maxN - n) / dn, TileSide.N, ref tBest, ref best);
            if (dn < -1e-6) Try((minN - n) / dn, TileSide.S, ref tBest, ref best);
            return best != TileSide.None ? best : NearestSide(e, n, minE, minN, maxE, maxN);
        }

        static void Try(double t, TileSide s, ref double tBest, ref TileSide best)
        {
            if (t >= 0.0 && t < tBest) { tBest = t; best = s; }
        }

        /// <summary>Nearest edge of the rectangle to a point (ties: N, E, S, W).</summary>
        public static TileSide NearestSide(float e, float n, float minE, float minN, float maxE, float maxN)
        {
            float dN = Math.Abs(maxN - n), dE = Math.Abs(maxE - e), dS = Math.Abs(n - minN), dW = Math.Abs(e - minE);
            float m = Math.Min(Math.Min(dN, dE), Math.Min(dS, dW));
            if (m == dN) return TileSide.N;
            if (m == dE) return TileSide.E;
            if (m == dS) return TileSide.S;
            return TileSide.W;
        }

        /// <summary>
        /// Side of an apron triangle (centroid outside the rectangle): the side it lies beyond; in a corner quadrant the
        /// side it lies further beyond (diagonal split; ties go to N / S). None for a centroid inside the rectangle.
        /// </summary>
        public static TileSide ApronSide(float e, float n, float minE, float minN, float maxE, float maxN)
        {
            float oe = Math.Max(Math.Max(minE - e, e - maxE), 0f);
            float on = Math.Max(Math.Max(minN - n, n - maxN), 0f);
            if (oe <= 0f && on <= 0f) return TileSide.None;
            if (on >= oe) return n > maxN ? TileSide.N : TileSide.S;
            return e > maxE ? TileSide.E : TileSide.W;
        }

        /// <summary>
        /// Corner quadrant of an apron triangle (ADR 0308): NE / SE / SW / NW when the centroid lies beyond the rectangle
        /// on both axes, else None. The corner quadrants are the only apron ground that covers a DIAGONAL neighbour tile.
        /// </summary>
        public static TileSide ApronCorner(float e, float n, float minE, float minN, float maxE, float maxN)
        {
            TileSide a = n > maxN ? TileSide.N : n < minN ? TileSide.S : TileSide.None;
            TileSide b = e > maxE ? TileSide.E : e < minE ? TileSide.W : TileSide.None;
            return a != TileSide.None && b != TileSide.None ? a | b : TileSide.None;
        }

        /// <summary>Bit of a diagonal side in a corner mask (NE 1, SE 2, SW 4, NW 8); 0 for anything else.</summary>
        public static int CornerBit(TileSide corner)
        {
            switch (corner)
            {
                case TileSide.NE: return 1;
                case TileSide.SE: return 2;
                case TileSide.SW: return 4;
                case TileSide.NW: return 8;
                default: return 0;
            }
        }

        /// <summary>True when one of the corners in <paramref name="cornerMask"/> (<see cref="CornerBit"/>) touches side <paramref name="side"/>.</summary>
        public static bool CornerMaskTouches(int cornerMask, TileSide side)
        {
            if ((cornerMask & 1) != 0 && (side & TileSide.NE) != 0) return true;
            if ((cornerMask & 2) != 0 && (side & TileSide.SE) != 0) return true;
            if ((cornerMask & 4) != 0 && (side & TileSide.SW) != 0) return true;
            if ((cornerMask & 8) != 0 && (side & TileSide.NW) != 0) return true;
            return false;
        }

        /// <summary>
        /// Should an apron piece be drawn (ADR 0235 + 0308)? <paramref name="piece"/>: N / E / S / W or a corner (NE ...),
        /// <paramref name="open"/>: sides with a ready neighbour, <paramref name="readyCorners"/>: ready DIAGONAL neighbours
        /// (<see cref="CornerBit"/> mask), <paramref name="hasCornerPieces"/>: the scene was imported with corner pieces.
        /// A corner piece hides when either of its sides is open or its diagonal tile is ready (owner s24: tile A's corner
        /// apron lay as a green sheet over the road of the diagonal tile on the DK65 staircase 06 - 07 - 08). A scene
        /// without corner pieces (older import: the corner quadrants are halves of the side pieces) hides the whole side
        /// piece next to a ready diagonal tile instead.
        /// </summary>
        public static bool ApronPieceVisible(TileSide piece, TileSide open, int readyCorners, bool hasCornerPieces)
        {
            if (open == TileSide.None && readyCorners == 0) return false;      // the undivided apron is shown
            if ((open & piece) != 0) return false;
            if (CornerBit(piece) != 0) return (readyCorners & CornerBit(piece)) == 0;
            return hasCornerPieces || !CornerMaskTouches(readyCorners, piece);
        }

        /// <summary>Should a far-field sector be drawn? Hidden when its side is open or a ready diagonal tile touches it
        /// (the sector reaches into that tile; the diagonal tile's own sectors show the horizon beyond).</summary>
        public static bool FarSectorVisible(TileSide sector, TileSide open, int readyCorners)
            => (open & sector) == 0 && !CornerMaskTouches(readyCorners, sector);

        /// <summary>Far-field sector names of the importer (WorldEdgeBuilder k_FarSectors, ADR 0085) → side.</summary>
        public static TileSide FarSectorSide(string objectName)
        {
            if (objectName == null) return TileSide.None;
            if (objectName.EndsWith("far_north", StringComparison.Ordinal)) return TileSide.N;
            if (objectName.EndsWith("far_east", StringComparison.Ordinal)) return TileSide.E;
            if (objectName.EndsWith("far_south", StringComparison.Ordinal)) return TileSide.S;
            if (objectName.EndsWith("far_west", StringComparison.Ordinal)) return TileSide.W;
            return TileSide.None;
        }

        /// <summary>Apron piece names written by the importer for streaming (Apron_N / _E / _S / _W) → side.</summary>
        public static TileSide ApronPieceSide(string objectName)
        {
            switch (objectName)
            {
                case "Apron_N": return TileSide.N;
                case "Apron_E": return TileSide.E;
                case "Apron_S": return TileSide.S;
                case "Apron_W": return TileSide.W;
                case "Apron_NE": return TileSide.NE;     // ADR 0308 corner quadrants
                case "Apron_SE": return TileSide.SE;
                case "Apron_SW": return TileSide.SW;
                case "Apron_NW": return TileSide.NW;
                default: return TileSide.None;
            }
        }

        /// <summary>
        /// Distance from a point inside the rectangle to the edge of the drivable union of ready tiles [m]: edges with a
        /// ready neighbour (<paramref name="openSides"/>) do not count; a corner whose two sides are open but whose
        /// diagonal tile is not ready (<paramref name="missingCorners"/>, NE / SE / SW / NW bits as pairs) counts as a
        /// point. Negative when the point is outside a closed side (same convention as WorldBoundary.InsideDistance).
        /// </summary>
        public static float UnionInsideDistance(float e, float n, float minE, float minN, float maxE, float maxN,
                                                TileSide openSides, int missingCornerMask)
        {
            float d = float.MaxValue;
            bool outside = false;
            float ox = 0f, oz = 0f;
            if ((openSides & TileSide.N) == 0) { float v = maxN - n; d = Math.Min(d, v); if (v < 0f) { outside = true; oz = Math.Max(oz, -v); } }
            if ((openSides & TileSide.S) == 0) { float v = n - minN; d = Math.Min(d, v); if (v < 0f) { outside = true; oz = Math.Max(oz, -v); } }
            if ((openSides & TileSide.E) == 0) { float v = maxE - e; d = Math.Min(d, v); if (v < 0f) { outside = true; ox = Math.Max(ox, -v); } }
            if ((openSides & TileSide.W) == 0) { float v = e - minE; d = Math.Min(d, v); if (v < 0f) { outside = true; ox = Math.Max(ox, -v); } }
            if (outside) return -(float)Math.Sqrt(ox * ox + oz * oz);
            if ((missingCornerMask & CornerBit(TileSide.NE)) != 0) d = Math.Min(d, Dist(e, n, maxE, maxN));
            if ((missingCornerMask & CornerBit(TileSide.SE)) != 0) d = Math.Min(d, Dist(e, n, maxE, minN));
            if ((missingCornerMask & CornerBit(TileSide.SW)) != 0) d = Math.Min(d, Dist(e, n, minE, minN));
            if ((missingCornerMask & CornerBit(TileSide.NW)) != 0) d = Math.Min(d, Dist(e, n, minE, maxN));
            return d;
        }

        /// <summary>Bit of a corner in the missing-corner mask (NE 1, SE 2, SW 4, NW 8; 0 for a non-corner).</summary>
        public static int CornerBit(TileSide corner)
        {
            switch (corner)
            {
                case TileSide.NE: return 1;
                case TileSide.SE: return 2;
                case TileSide.SW: return 4;
                case TileSide.NW: return 8;
                default: return 0;
            }
        }

        static float Dist(float e, float n, float ce, float cn)
        {
            float a = e - ce, b = n - cn;
            return (float)Math.Sqrt(a * a + b * b);
        }

        /// <summary>
        /// A closure render group (several closures in one mesh) may be hidden only when every closure whose centre lies in
        /// its bounds (+ <paramref name="padM"/>) is open. False when no closure lies in it (unknown group: keep it).
        /// </summary>
        public static bool GroupMayHide(float gMinE, float gMinN, float gMaxE, float gMaxN, float[] closureE, float[] closureN,
                                        bool[] closureOpen, int count, float padM = 5f)
        {
            int inside = 0;
            for (int i = 0; i < count; i++)
            {
                if (closureE[i] < gMinE - padM || closureE[i] > gMaxE + padM || closureN[i] < gMinN - padM || closureN[i] > gMaxN + padM) continue;
                inside++;
                if (!closureOpen[i]) return false;
            }
            return inside > 0;
        }
    }
}
