namespace Game.World
{
    /// <summary>
    /// Scene naming of the imported world regions (ADR 0011, ADR 0229) - the one rule shared by the importer
    /// (<c>WorldSceneBuilder</c>), the build (<c>BuildCommands -Regions</c>) and the start menu. Region C keeps its historic
    /// name <c>WorldC</c>; every other region is <c>World_&lt;id&gt;</c>; the High content tier adds <c>_High</c> (ADR 0012).
    /// Scenes live in <c>Assets/_Generated/World/&lt;id&gt;/</c> (gitignored, made by scripts/import-region.ps1).
    /// Pure string functions, no Unity objects.
    /// </summary>
    public static class RegionScenes
    {
        public const string GeneratedRoot = "Assets/_Generated/World/";
        /// <summary>The first imported region; its scenes are WorldC / WorldC_High.</summary>
        public const string RegionC = "bialystok-industrial-c";
        public const string LowTier = "Low", HighTier = "High";

        /// <summary>Scene name (no path, no extension) of a region's content tier: "Low" (Low + Medium quality) or "High".</summary>
        public static string SceneNameFor(string region, string tier = LowTier)
        {
            string b = region == RegionC ? "WorldC" : "World_" + region;
            return tier == HighTier ? b + "_High" : b;
        }

        /// <summary>
        /// Streamed tile scene of a region (ADR 0235): only the region root and the start route, loaded additively next to a
        /// running world scene. "World_dk65-04_Tile", "WorldC_Tile", "World_knyszyn_High_Tile".
        /// </summary>
        public const string TileSuffix = "_Tile";
        public static string TileSceneNameFor(string region, string tier = LowTier) => SceneNameFor(region, tier) + TileSuffix;
        public static string TileScenePathFor(string region, string tier = LowTier) =>
            GeneratedRoot + region + "/" + TileSceneNameFor(region, tier) + ".unity";

        /// <summary>Project-relative scene path, e.g. Assets/_Generated/World/knyszyn/World_knyszyn.unity.</summary>
        public static string ScenePathFor(string region, string tier = LowTier) =>
            GeneratedRoot + region + "/" + SceneNameFor(region, tier) + ".unity";

        /// <summary>Quality tiers that use the High content scene when it is in the build (ADR 0012).</summary>
        public static bool UsesHighContent(string qualityTier) => qualityTier == "High" || qualityTier == "Ultra";
    }
}
