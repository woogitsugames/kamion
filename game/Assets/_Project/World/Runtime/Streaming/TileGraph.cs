using System;
using UnityEngine;

namespace Game.World.Streaming
{
    /// <summary>Side of a tile (bit flags; a corner neighbour is two bits, e.g. NE = N | E).</summary>
    [Flags]
    public enum TileSide { None = 0, N = 1, E = 2, S = 4, W = 8, NE = N | E, SE = S | E, SW = S | W, NW = N | W }

    /// <summary>JsonUtility shape of tile_graph.json (tools/worldgen/streaming/tile_graph.py, ADR 0235).</summary>
    [Serializable]
    public sealed class TileGraphData
    {
        public string schema;
        public TileData[] tiles = Array.Empty<TileData>();
        public PortalData[] portals = Array.Empty<PortalData>();
        public CorridorData[] corridors = Array.Empty<CorridorData>();
    }

    [Serializable]
    public sealed class TileData
    {
        public string id;
        /// <summary>Desktop starts need neighbouring scenes by default (streaming.authored.json; absent = false).</summary>
        public bool needsNeighbourContext;
        /// <summary>Tile rectangle, EPSG:2180 (x east, y north).</summary>
        public double xmin, ymin, xmax, ymax;
        /// <summary>Floating-origin anchor of the region import (region.yaml origin): Unity (0,0,0) of the region scene.</summary>
        public double anchorX, anchorY, anchorZ;
        /// <summary>WORLD_MEMORY Low of the region import [MB] (ESTIMATED, ADR 0229 table).</summary>
        public float worldMemoryMB;
        /// <summary>WORLD_MEMORY High of the region import [MB] (ESTIMATED, ADR 0234 §7 table; ADR 0273). 0 in an old graph.</summary>
        public float worldMemoryHighMB;
        public string memorySource;
        public NeighborData[] neighbors = Array.Empty<NeighborData>();
    }

    [Serializable]
    public sealed class NeighborData { public string id; public string side; public float seamM; }

    [Serializable]
    public sealed class PortalData { public string from, to, side; public double x, y; public float gapM; }

    [Serializable]
    public sealed class CorridorData { public string id; public string[] tiles = Array.Empty<string>(); }

    /// <summary>
    /// Tile adjacency graph with integer indices (built once; lookups allocate nothing). Pure C#: no scene access.
    /// </summary>
    public sealed class TileGraph
    {
        public const string ResourcePath = "WorldStreaming/tile_graph";
        public const string Schema = "truck-sim-pl/tile-graph/1";

        public readonly TileData[] Tiles;
        /// <summary>Neighbour tile indices of each tile (edges and corners).</summary>
        public readonly int[][] Neighbors;
        /// <summary>Side of tile i on which Neighbors[i][k] touches it.</summary>
        public readonly TileSide[][] NeighborSides;
        public readonly CorridorData[] Corridors;
        public readonly PortalData[] Portals;

        public int Count => Tiles.Length;

        public TileGraph(TileGraphData data)
        {
            if (data == null || data.tiles == null) throw new ArgumentNullException(nameof(data));
            Tiles = data.tiles;
            Corridors = data.corridors ?? Array.Empty<CorridorData>();
            Portals = data.portals ?? Array.Empty<PortalData>();
            Neighbors = new int[Tiles.Length][];
            NeighborSides = new TileSide[Tiles.Length][];
            for (int i = 0; i < Tiles.Length; i++)
            {
                var ns = Tiles[i].neighbors ?? Array.Empty<NeighborData>();
                int valid = 0;
                for (int k = 0; k < ns.Length; k++) if (IndexOf(ns[k].id) >= 0 && ParseSide(ns[k].side) != TileSide.None) valid++;
                Neighbors[i] = new int[valid];
                NeighborSides[i] = new TileSide[valid];
                int w = 0;
                for (int k = 0; k < ns.Length; k++)
                {
                    int j = IndexOf(ns[k].id);
                    var s = ParseSide(ns[k].side);
                    if (j < 0 || s == TileSide.None) continue;
                    Neighbors[i][w] = j; NeighborSides[i][w] = s; w++;
                }
            }
        }

        public static TileGraph FromJson(string json) => new TileGraph(JsonUtility.FromJson<TileGraphData>(json));

        /// <summary>The graph shipped in Resources (null when missing).</summary>
        public static TileGraph LoadDefault()
        {
            var ta = Resources.Load<TextAsset>(ResourcePath);
            return ta != null ? FromJson(ta.text) : null;
        }

        public int IndexOf(string id)
        {
            if (string.IsNullOrEmpty(id)) return -1;
            for (int i = 0; i < Tiles.Length; i++) if (Tiles[i].id == id) return i;
            return -1;
        }

        public static TileSide ParseSide(string s)
        {
            switch (s)
            {
                case "N": return TileSide.N; case "E": return TileSide.E; case "S": return TileSide.S; case "W": return TileSide.W;
                case "NE": return TileSide.NE; case "SE": return TileSide.SE; case "SW": return TileSide.SW; case "NW": return TileSide.NW;
                default: return TileSide.None;
            }
        }

        public static TileSide Opposite(TileSide s)
        {
            TileSide o = TileSide.None;
            if ((s & TileSide.N) != 0) o |= TileSide.S;
            if ((s & TileSide.S) != 0) o |= TileSide.N;
            if ((s & TileSide.E) != 0) o |= TileSide.W;
            if ((s & TileSide.W) != 0) o |= TileSide.E;
            return o;
        }

        /// <summary>True when (x, y) lies in tile i expanded by <paramref name="marginM"/> (negative = shrunk).</summary>
        public bool Contains(int i, double x, double y, double marginM = 0.0)
        {
            var t = Tiles[i];
            return x >= t.xmin - marginM && x <= t.xmax + marginM && y >= t.ymin - marginM && y <= t.ymax + marginM;
        }

        /// <summary>Index of the tile containing (x, y), -1 when none (first match on a shared edge).</summary>
        public int TileAt(double x, double y)
        {
            for (int i = 0; i < Tiles.Length; i++) if (Contains(i, x, y)) return i;
            return -1;
        }

        /// <summary>Distance from (x, y) to the rectangle of tile i [m], 0 inside.</summary>
        public double DistanceTo(int i, double x, double y)
        {
            var t = Tiles[i];
            double dx = Math.Max(Math.Max(t.xmin - x, 0.0), x - t.xmax);
            double dy = Math.Max(Math.Max(t.ymin - y, 0.0), y - t.ymax);
            return Math.Sqrt(dx * dx + dy * dy);
        }

        /// <summary>Distance between the segment (x0,y0)-(x1,y1) and the rectangle of tile i [m], 0 when they meet.</summary>
        public double SegmentDistanceTo(int i, double x0, double y0, double x1, double y1)
        {
            var t = Tiles[i];
            if (SegmentHitsRect(x0, y0, x1, y1, t.xmin, t.ymin, t.xmax, t.ymax)) return 0.0;
            double d = Math.Min(DistanceTo(i, x0, y0), DistanceTo(i, x1, y1));
            d = Math.Min(d, PointSegment(t.xmin, t.ymin, x0, y0, x1, y1));
            d = Math.Min(d, PointSegment(t.xmax, t.ymin, x0, y0, x1, y1));
            d = Math.Min(d, PointSegment(t.xmax, t.ymax, x0, y0, x1, y1));
            d = Math.Min(d, PointSegment(t.xmin, t.ymax, x0, y0, x1, y1));
            return d;
        }

        static double PointSegment(double px, double py, double x0, double y0, double x1, double y1)
        {
            double vx = x1 - x0, vy = y1 - y0;
            double l2 = vx * vx + vy * vy;
            double u = l2 > 1e-12 ? Math.Max(0.0, Math.Min(1.0, ((px - x0) * vx + (py - y0) * vy) / l2)) : 0.0;
            double dx = x0 + u * vx - px, dy = y0 + u * vy - py;
            return Math.Sqrt(dx * dx + dy * dy);
        }

        /// <summary>Liang-Barsky clip: does the segment touch the rectangle?</summary>
        static bool SegmentHitsRect(double x0, double y0, double x1, double y1, double xmin, double ymin, double xmax, double ymax)
        {
            double t0 = 0.0, t1 = 1.0, dx = x1 - x0, dy = y1 - y0;
            return Clip(-dx, x0 - xmin, ref t0, ref t1) && Clip(dx, xmax - x0, ref t0, ref t1) &&
                   Clip(-dy, y0 - ymin, ref t0, ref t1) && Clip(dy, ymax - y0, ref t0, ref t1);
        }

        static bool Clip(double p, double q, ref double t0, ref double t1)
        {
            if (Math.Abs(p) < 1e-12) return q >= 0.0;
            double r = q / p;
            if (p < 0.0) { if (r > t1) return false; if (r > t0) t0 = r; }
            else { if (r < t0) return false; if (r < t1) t1 = r; }
            return true;
        }

        /// <summary>
        /// Bounding rectangle of the tiles reachable from <paramref name="origin"/> through neighbours with
        /// <paramref name="include"/>[i] == true, in the region-local frame of the origin tile: east = x − origin.anchorX,
        /// north = y − origin.anchorY [m]. The origin's own rectangle counts only with <paramref name="withOrigin"/> (the
        /// streamer uses the origin's drivable WorldBoundary rectangle instead). ADR 0273 §10: the safety-net rectangle of the
        /// start region while streaming. Allocates two small arrays (install time only). False when nothing was added.
        /// </summary>
        public bool LocalUnionBounds(int origin, bool[] include, out double minE, out double minN, out double maxE, out double maxN, bool withOrigin = true)
        {
            minE = minN = double.MaxValue; maxE = maxN = double.MinValue;
            if (origin < 0 || origin >= Tiles.Length) return false;
            var seen = new bool[Tiles.Length];
            var queue = new int[Tiles.Length];
            int head = 0, tail = 0;
            seen[origin] = true; queue[tail++] = origin;
            double ax = Tiles[origin].anchorX, ay = Tiles[origin].anchorY;
            while (head < tail)
            {
                int i = queue[head++];
                var t = Tiles[i];
                if (i != origin || withOrigin)
                {
                    minE = Math.Min(minE, t.xmin - ax); maxE = Math.Max(maxE, t.xmax - ax);
                    minN = Math.Min(minN, t.ymin - ay); maxN = Math.Max(maxN, t.ymax - ay);
                }
                var nb = Neighbors[i];
                for (int k = 0; k < nb.Length; k++)
                {
                    int j = nb[k];
                    if (seen[j] || include == null || j >= include.Length || !include[j]) continue;
                    seen[j] = true; queue[tail++] = j;
                }
            }
            return maxE > minE && maxN > minN;
        }

        /// <summary>Side of tile i on which tile j touches it (None when not neighbours).</summary>
        public TileSide SideOf(int i, int j)
        {
            var n = Neighbors[i];
            for (int k = 0; k < n.Length; k++) if (n[k] == j) return NeighborSides[i][k];
            return TileSide.None;
        }

        /// <summary>Neighbour of tile i on side s (-1 when there is none).</summary>
        public int NeighborOn(int i, TileSide s)
        {
            var n = Neighbors[i];
            for (int k = 0; k < n.Length; k++) if (NeighborSides[i][k] == s) return n[k];
            return -1;
        }
    }
}
