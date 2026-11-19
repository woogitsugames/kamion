using System;

namespace Game.World.Streaming
{
    /// <summary>Import/streaming rules for a single road closure. Heights are region-local absolute elevations.</summary>
    public static class EdgeClosureRules
    {
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
