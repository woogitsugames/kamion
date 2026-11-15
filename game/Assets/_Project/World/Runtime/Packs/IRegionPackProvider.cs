using System;
using System.Collections;

namespace Game.World.Packs
{
    /// <summary>Result of <see cref="IRegionPackProvider.Prepare"/>: the scene name to load, or an error.</summary>
    public readonly struct RegionPackLoadResult
    {
        public readonly string SceneName;
        public readonly string Error;
        public RegionPackLoadResult(string sceneName, string error) { SceneName = sceneName; Error = error; }
        public bool Ok => Error == null && !string.IsNullOrEmpty(SceneName);
    }

    /// <summary>
    /// The seam between region packs (ADR 0234) and the start menu region picker (ADR 0229, PR #104). The menu asks
    /// <see cref="GetInfo"/> for every catalog region when it is built and after a download finishes; pressing start runs
    /// <see cref="Prepare"/> (verify + load the bundles) and then <c>SceneManager.LoadScene(result.SceneName)</c>.
    /// Everything here runs in the menu; nothing is called from the driving loop.
    /// </summary>
    public interface IRegionPackProvider
    {
        /// <summary>Cheap state (file sizes, no hashing) of a region's pack for a content tier ("Low" / "High").
        /// <paramref name="sceneInBuild"/>: the region scene is in the APK (Application.CanStreamedLevelBeLoaded before
        /// any pack is loaded) - then the result is <see cref="RegionPackState.InBase"/>.</summary>
        RegionPackInfo GetInfo(string region, string tier, bool sceneInBuild);

        /// <summary>True when a download URL is configured (default: none, ADR 0234 §5).</summary>
        bool DownloadEnabled { get; }

        /// <summary>Verifies (SHA-256) and loads the region bundle and its dependencies; unloads packs of another region first.</summary>
        IEnumerator Prepare(string region, string tier, Action<RegionPackLoadResult> done);

        /// <summary>Downloads the missing bundles of a region pack into incoming/, verifies and installs them. done(null) = ok.</summary>
        IEnumerator Download(string region, string tier, Action<string> done);

        /// <summary>Moves adb-pushed files from incoming/ into the installed set (also run once at start).</summary>
        RegionPackInstallResult InstallIncoming();

        /// <summary>Raised on the main thread after the installed set or a download state changed (menu refresh).</summary>
        event Action Changed;
    }
}
