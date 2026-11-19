using System;

namespace Game.World.Streaming
{
    /// <summary>Content tier and world memory budget the streamer runs with (ADR 0273 §6, dopisek D44).</summary>
    public readonly struct StreamingContent
    {
        /// <summary><see cref="RegionScenes.LowTier"/> or <see cref="RegionScenes.HighTier"/> (tile scenes World_&lt;id&gt;[_High]_Tile).</summary>
        public readonly string contentTier;
        /// <summary>Sum of WORLD_MEMORY of resident tiles [MB] (<see cref="StreamingSettings.BudgetForTier(string, bool)"/>).</summary>
        public readonly float budgetMB;
        /// <summary>True when High was wanted (desktop High / Ultra) but no High tile scene of a neighbour is available.</summary>
        public readonly bool highFallback;
        /// <summary>One-line reason for the log ("desktop tier High", "fallback: ...").</summary>
        public readonly string reason;

        public StreamingContent(string contentTier, float budgetMB, bool highFallback, string reason)
        {
            this.contentTier = contentTier;
            this.budgetMB = budgetMB;
            this.highFallback = highFallback;
            this.reason = reason;
        }

        public bool IsHigh => contentTier == RegionScenes.HighTier;
    }

    /// <summary>
    /// Which content tier the streamed tiles use and with which memory budget (ADR 0273 §6 table; dopisek D44 2026-11-16).
    /// Pure: platform, quality tier name, start scene tier and "is a High tile of a neighbour available" in, decision out.
    /// <list type="bullet">
    /// <item><b>Desktop</b> (ADR 0269 PC tiers): the PC quality tier decides, not the start scene name. Low / Medium = Low
    /// content (850 / 800 MB, owner 18.11 ADR 0290); High / Ultra = High content (2000 / 2000 MB) when at least one neighbour has a
    /// <c>World_&lt;id&gt;_High_Tile</c> scene in the build or an installed pack, else an explicit Low fallback (logged) with the
    /// tier's budget unchanged. A start scene that is already High keeps High content also on Low / Medium (the start tile is
    /// counted with its High memory; the budget stays the tier's).</item>
    /// <item><b>Phone</b> (ADR 0235 §4): unchanged - content follows the start scene (<c>_High</c> suffix), budget per tier
    /// 200 / 400 / 600 MB.</item>
    /// </list>
    /// Install time only (allocates the reason string once); nothing per frame.
    /// </summary>
    public static class StreamingContentChoice
    {
        /// <param name="highTilesAvailable">High content is usable for the whole graph (<see cref="HighCoversLow"/>).</param>
        /// <param name="highMissing">For the log: the first tile that has a Low tile scene but no High one (null = none / unknown).</param>
        public static StreamingContent Choose(bool desktop, string qualityTier, bool startSceneHigh, bool highTilesAvailable, string highMissing = null)
        {
            float budget = StreamingSettings.BudgetForTier(qualityTier, desktop);
            string q = string.IsNullOrEmpty(qualityTier) ? "?" : qualityTier;
            if (!desktop)
                return new StreamingContent(startSceneHigh ? RegionScenes.HighTier : RegionScenes.LowTier, budget, false,
                    "phone tier " + q + ", content of the start scene");
            bool wantHigh = RegionScenes.UsesHighContent(qualityTier) || startSceneHigh;
            if (!wantHigh)
                return new StreamingContent(RegionScenes.LowTier, budget, false, "desktop tier " + q);
            if (highTilesAvailable)
                return new StreamingContent(RegionScenes.HighTier, budget, false,
                    "desktop tier " + q + (startSceneHigh ? "" : ", start scene Low (no _High scene of the start region)"));
            return new StreamingContent(RegionScenes.LowTier, budget, true,
                "desktop tier " + q + " FALLBACK Low: " + (string.IsNullOrEmpty(highMissing)
                    ? "no neighbour _High_Tile scene in the build or packs"
                    : "tile " + highMissing + " has a Low tile scene but no _High_Tile (High would close its seams)")
                + " (build without -WorldLow, import -Tiers Low,High)");
        }

        /// <summary>
        /// Review #168 P1-1 / P1-2 (int-ui-s23): High content may be chosen only when it loses no tile - the start region and
        /// every tile of the graph whose Low tile scene is available also have a High tile scene, and at least one
        /// neighbour of the start has one. Otherwise a tile reachable in Low (on main) would be marked unavailable in High
        /// and its seam would stay closed (the start tile after unpinning, or a Low-only import further along).
        /// <paramref name="missing"/> = first tile that blocks High (null when High covers Low). Install time only.
        /// </summary>
        public static bool HighCoversLow(TileGraph graph, string startRegionId, ITileSceneSource source, out string missing)
        {
            missing = null;
            if (graph == null || source == null) return false;
            if (graph.IndexOf(startRegionId) < 0) return false;
            if (!source.IsAvailable(startRegionId, RegionScenes.HighTier)) { missing = startRegionId; return false; }
            for (int i = 0; i < graph.Count; i++)
            {
                string id = graph.Tiles[i].id;
                if (source.IsAvailable(id, RegionScenes.LowTier) && !source.IsAvailable(id, RegionScenes.HighTier)) { missing = id; return false; }
            }
            return AnyNeighbourAvailable(graph, startRegionId, source, RegionScenes.HighTier);
        }

        /// <summary>True when at least one neighbour of <paramref name="regionId"/> has its tile scene of
        /// <paramref name="tier"/> available from <paramref name="source"/>.</summary>
        public static bool AnyNeighbourAvailable(TileGraph graph, string regionId, ITileSceneSource source, string tier)
        {
            if (graph == null || source == null) return false;
            int idx = graph.IndexOf(regionId);
            if (idx < 0) return false;
            foreach (int j in graph.Neighbors[idx])
                if (source.IsAvailable(graph.Tiles[j].id, tier)) return true;
            return false;
        }

        /// <summary>Start scene name is the High content variant (World_&lt;id&gt;_High, WorldC_High).</summary>
        public static bool IsHighScene(string sceneName) =>
            sceneName != null && sceneName.EndsWith("_High", StringComparison.Ordinal);
    }
}
