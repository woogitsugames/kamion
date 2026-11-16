using System;
using System.Collections;
using UnityEngine.SceneManagement;

namespace Game.World.Streaming
{
    /// <summary>
    /// Where the streamer gets a tile scene from (ADR 0273 §3, §10). The base game has ONE implementation: the player build
    /// (<see cref="BuildTileSource"/>, scenes added by <c>-Regions</c>). A region pack (ADR 0234: AssetBundle with the tile
    /// scene, ref-counted lease) is a FUTURE second implementation for DLC / the phone - its contract is fixed here and checked
    /// by <c>TileSceneSourceContractTests</c> with a test double; the pack runtime itself is not in the game (ADR 0234 §9).
    /// Called only on tile events (install, load, unload), never per frame.
    /// </summary>
    public interface ITileSceneSource
    {
        /// <summary>The tile scene of the region and content tier can be opened in this installation.</summary>
        bool IsAvailable(string region, string tier);

        /// <summary>Makes the tile scene loadable. Calls <paramref name="done"/> exactly once: done(true) =
        /// <c>SceneManager.LoadSceneAsync(RegionScenes.TileSceneNameFor(region, tier))</c> may run now and the source holds
        /// one lease until <see cref="Release"/>; done(false) = nothing is held (the seam stays closed). A scene in the player
        /// build needs nothing (done(true) at once).</summary>
        IEnumerator Acquire(string region, string tier, Action<bool> done);

        /// <summary>Gives back one lease taken by a successful <see cref="Acquire"/> (after the tile scene is unloaded, or when
        /// the streamer no longer wants the tile). No-op for the build.</summary>
        void Release(string region, string tier);

        /// <summary>True when Acquire / Release matter (the streamer then loads through a coroutine and balances leases).</summary>
        bool FromPack(string region, string tier);
    }

    /// <summary>
    /// Default and only runtime source of the base game: tile scenes in the player build. "In the build" = a build index for
    /// the scene path (<see cref="SceneUtility.GetBuildIndexByScenePath"/>), not <c>Application.CanStreamedLevelBeLoaded</c>,
    /// which is also true for scenes of AssetBundles another holder loaded.
    /// </summary>
    public sealed class BuildTileSource : ITileSceneSource
    {
        readonly Func<string, bool> m_InBuild;

        /// <param name="inBuild">Scene path -&gt; in the player build (tests); default = build index &gt;= 0.</param>
        public BuildTileSource(Func<string, bool> inBuild = null)
        {
            m_InBuild = inBuild ?? (path => SceneUtility.GetBuildIndexByScenePath(path) >= 0);
        }

        public bool IsAvailable(string region, string tier) => m_InBuild(RegionScenes.TileScenePathFor(region, tier));

        public bool FromPack(string region, string tier) => false;

        public IEnumerator Acquire(string region, string tier, Action<bool> done)
        {
            done?.Invoke(IsAvailable(region, tier));
            yield break;
        }

        public void Release(string region, string tier) { }
    }
}
