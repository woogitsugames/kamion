using System;
using System.Collections;

namespace Game.World.Packs
{
    /// <summary>Result of <see cref="IRegionPackProvider.Prepare"/> / <see cref="IRegionPackProvider.Acquire"/>: the
    /// full region scene name to load (menu), the tile scene name (streaming, ADR 0235/0273; null when the pack has none),
    /// or an error.</summary>
    public readonly struct RegionPackLoadResult
    {
        public readonly string SceneName;
        public readonly string TileSceneName;
        public readonly string Error;
        public RegionPackLoadResult(string sceneName, string error, string tileSceneName = null)
        {
            SceneName = sceneName; Error = error; TileSceneName = tileSceneName;
        }
        public bool Ok => Error == null && !string.IsNullOrEmpty(SceneName);

        /// <summary>Tile scene naming of ADR 0235 (<c>RegionScenes.TileSuffix</c>).</summary>
        public static bool IsTileScene(string sceneName) =>
            sceneName != null && sceneName.EndsWith(RegionScenes.TileSuffix, StringComparison.Ordinal);
    }

    /// <summary>
    /// The seam between region packs (ADR 0234) and the start menu region picker (ADR 0229, PR #104). The menu asks
    /// <see cref="GetInfo"/> for every catalog region when it is built and after a download finishes; pressing start runs
    /// <see cref="Prepare"/> (verify + load the bundles) and then <c>SceneManager.LoadScene(result.SceneName)</c>.
    /// The additive streamer (ADR 0235/0273) uses <see cref="Acquire"/> / <see cref="Release"/> on tile events only
    /// (load / unload of a tile), never per frame.
    /// </summary>
    public interface IRegionPackProvider
    {
        /// <summary>Cheap state (file sizes, no hashing) of a region's pack for a content tier ("Low" / "High").
        /// <paramref name="sceneInBuild"/>: the region scene is in the APK (Application.CanStreamedLevelBeLoaded before
        /// any pack is loaded) - then the result is <see cref="RegionPackState.InBase"/>.</summary>
        RegionPackInfo GetInfo(string region, string tier, bool sceneInBuild);

        /// <summary>True when a download URL is configured (default: none, ADR 0234 §5).</summary>
        bool DownloadEnabled { get; }

        /// <summary>Menu start: <see cref="Acquire"/> under the menu's lease (the previous menu region is released; regions
        /// held by others stay loaded). The menu lease is given back when the active scene leaves the region.</summary>
        IEnumerator Prepare(string region, string tier, Action<RegionPackLoadResult> done);

        /// <summary>
        /// Takes one reference on a region pack (ADR 0273): verifies (SHA-256) and loads the bundles not yet loaded
        /// (common, data, scene bundle), so both the full scene and the tile scene of the region become loadable with
        /// <c>SceneManager.LoadSceneAsync</c>. Several regions may be held at once (streaming). Every successful Acquire
        /// needs exactly one <see cref="Release"/>.
        /// </summary>
        IEnumerator Acquire(string region, string tier, Action<RegionPackLoadResult> done);

        /// <summary>Gives back one reference; bundles no held region uses any more are unloaded with their assets. Call
        /// only after the region's scenes are unloaded.</summary>
        void Release(string region, string tier);

        /// <summary>Downloads the missing bundles of a region pack into incoming/, verifies and installs them. done(null) = ok.</summary>
        IEnumerator Download(string region, string tier, Action<string> done);

        /// <summary>Moves adb-pushed files from incoming/ into the installed set (also run once at start).</summary>
        RegionPackInstallResult InstallIncoming();

        /// <summary>Raised on the main thread after the installed set or a download state changed (menu refresh).</summary>
        event Action Changed;
    }
}
