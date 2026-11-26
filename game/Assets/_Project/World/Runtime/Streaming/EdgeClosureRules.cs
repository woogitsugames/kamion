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
        /// stay closed, and corner neighbours are never needed for a closure. Order: N, E, S, W.
        /// </summary>
        public static string[] QaNeighbourIds(TileGraph graph, int tile, TileSide closedSides)
        {
            if (graph == null || tile < 0 || tile >= graph.Count || closedSides == TileSide.None) return System.Array.Empty<string>();
            var ids = new System.Collections.Generic.List<string>(4);
            foreach (var side in k_EdgeSides)
            {
                if ((closedSides & side) == 0) continue;
                int j = graph.NeighborOn(tile, side);
                if (j >= 0) ids.Add(graph.Tiles[j].id);
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
