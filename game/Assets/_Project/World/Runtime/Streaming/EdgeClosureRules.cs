using System;

namespace Game.World.Streaming
{
    /// <summary>Import/streaming rules for a single road closure. Heights are region-local absolute elevations.</summary>
    public static class EdgeClosureRules
    {
        /// <summary>Authored region metadata exported to the tile graph; missing metadata defaults to standalone.</summary>
        public static bool NeedsNeighbourContext(TileGraph graph, string region)
        {
            int i = graph != null ? graph.IndexOf(region) : -1;
            return i >= 0 && graph.Tiles[i].needsNeighbourContext;
        }

        /// <summary>
        /// Static capture context (visual-qa, world-edge-s24): the edge neighbours of <paramref name="tile"/> on the sides
        /// where the tile closes at least one road (<paramref name="closedSides"/>). In the game those seams open as soon as
        /// both tiles are Ready (the neighbour is Ready ~380 m before the seam on PC), so a single-tile render that keeps
        /// them closed shows a barrier the driver never sees. Sides without a graph neighbour (outer edge of the world)
        /// stay closed. Order: N, E, S, W, then the camera-radius neighbours in graph order.
        /// Second rule (the same as <see cref="StreamingPolicy"/>): any graph neighbour (edge or corner) whose rectangle is
        /// within <paramref name="loadRadiusM"/> of a camera position (absolute EPSG:2180 east / north) is loaded too - the
        /// game would have it resident with the vehicle there, so its seams with the ring-1 tiles are open as well (a spawn
        /// near a tile corner otherwise still shows the closure of the corner seam far down the road).
        /// </summary>
        public static string[] QaNeighbourIds(TileGraph graph, int tile, TileSide closedSides,
            double[] camE = null, double[] camN = null, double loadRadiusM = 0.0)
        {
            if (graph == null || tile < 0 || tile >= graph.Count) return System.Array.Empty<string>();
            var ids = new System.Collections.Generic.List<string>(8);
            foreach (var side in k_EdgeSides)
            {
                if ((closedSides & side) == 0) continue;
                int j = graph.NeighborOn(tile, side);
                if (j >= 0) ids.Add(graph.Tiles[j].id);
            }
            int cams = camE != null && camN != null ? System.Math.Min(camE.Length, camN.Length) : 0;
            foreach (int j in graph.Neighbors[tile])
            {
                if (ids.Contains(graph.Tiles[j].id)) continue;
                for (int c = 0; c < cams; c++)
                    if (graph.DistanceTo(j, camE[c], camN[c]) <= loadRadiusM) { ids.Add(graph.Tiles[j].id); break; }
            }
            return ids.ToArray();
        }

        static readonly TileSide[] k_EdgeSides = { TileSide.N, TileSide.E, TileSide.S, TileSide.W };

        public static bool StreamingRequested(string argument, string region, bool desktop, bool? enabledOverride, TileGraph graph = null) =>
            enabledOverride ?? (argument == "1" ||
                (string.IsNullOrEmpty(argument) && desktop && NeedsNeighbourContext(graph, region)));

        public static bool IsOpen(TileSide side, TileSide openSides) =>
            side != TileSide.None && (openSides & side) == side;

        public static bool SeamReady(TileState owner, TileState neighbour, bool neighbourPresent, bool leaving) =>
            owner == TileState.Ready && neighbour == TileState.Ready && neighbourPresent && !leaving;

        /// <summary>
        /// Road collision is exported as asphalt even for concrete roads (roads/meshing.py).
        /// col_concrete also contains building roofs: it must never be a road-height source.
        /// Terrain is a fallback; a cooked road above it wins (including bridge decks).
        /// </summary>
        public static int HeightPriority(string colliderName, bool belongsToRegion, float normalY)
        {
            if (!belongsToRegion || normalY < 0.5f) return 0;
            switch (colliderName)
            {
                case "col_asphalt": case "col_paving_stones": case "col_sett": case "col_gravel": return 2;
                case "col_terrain": return 1;
                default: return 0;
            }
        }

        /// <summary>Order-independent hit reduction; never substitutes a roof, obstacle or another tile.</summary>
        public static void ConsiderHeight(int priority, float localY, ref int bestPriority, ref float bestY)
        {
            if (priority <= 0 || float.IsNaN(localY) || float.IsInfinity(localY)) return;
            if (priority > bestPriority || (priority == bestPriority && localY > bestY))
            { bestPriority = priority; bestY = localY; }
        }
    }
}
