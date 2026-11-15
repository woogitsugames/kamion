using System;
using System.Collections;
using Game.World.Packs;
using UnityEngine.SceneManagement;

namespace Game.World.Streaming
{
    /// <summary>
    /// Where the streamer gets a tile scene from (ADR 0273 §3): the player build (<c>-Regions</c>) or an installed region
    /// pack (ADR 0234). Called only on tile events (install, load, unload), never per frame.
    /// </summary>
    public interface ITileSceneSource
    {
        /// <summary>The tile scene of the region and content tier can be opened in this installation.</summary>
        bool IsAvailable(string region, string tier);

        /// <summary>Makes the tile scene loadable. done(true) = <c>SceneManager.LoadSceneAsync(tileScene)</c> may run now; a
        /// pack keeps one lease until <see cref="Release"/>. A scene in the player build needs nothing (done(true) at once).</summary>
        IEnumerator Acquire(string region, string tier, Action<bool> done);

        /// <summary>Gives back what <see cref="Acquire"/> took (call after the tile scene is unloaded). No-op for the build.</summary>
        void Release(string region, string tier);

        /// <summary>True when the scene comes from a pack (Acquire / Release matter; for the log).</summary>
        bool FromPack(string region, string tier);
    }

    /// <summary>
    /// Default source: the player build first, then the region pack service if it already exists (the start menu creates it,
    /// ADR 0234 annex A; the streamer never creates it - that would install incoming/ and hash bundles mid-drive).
    /// "In the build" = a build index for the scene path (<see cref="SceneUtility.GetBuildIndexByScenePath"/>), not
    /// <c>Application.CanStreamedLevelBeLoaded</c>, which is also true for scenes of bundles another holder loaded - the
    /// streamer must take its own lease on those.
    /// </summary>
    public sealed class BuildOrPackTileSource : ITileSceneSource
    {
        readonly IRegionPackProvider m_Packs;
        readonly Func<string, bool> m_InBuild;

        /// <param name="packs">Pack provider or null (packs off).</param>
        /// <param name="inBuild">Scene path -&gt; in the player build (tests); default = build index &gt;= 0.</param>
        public BuildOrPackTileSource(IRegionPackProvider packs, Func<string, bool> inBuild = null)
        {
            m_Packs = packs;
            m_InBuild = inBuild ?? (path => SceneUtility.GetBuildIndexByScenePath(path) >= 0);
        }

        public bool InBuild(string region, string tier) => m_InBuild(RegionScenes.TileScenePathFor(region, tier));

        public bool FromPack(string region, string tier) => !InBuild(region, tier) && PackUsable(region, tier);

        bool PackUsable(string region, string tier)
        {
            if (m_Packs == null) return false;
            var s = m_Packs.GetInfo(region, tier, false).State;
            return s == RegionPackState.Installed || s == RegionPackState.Loaded;
        }

        public bool IsAvailable(string region, string tier) => InBuild(region, tier) || PackUsable(region, tier);

        public IEnumerator Acquire(string region, string tier, Action<bool> done)
        {
            if (InBuild(region, tier) || m_Packs == null) { done?.Invoke(InBuild(region, tier)); yield break; }
            RegionPackLoadResult result = default;
            yield return m_Packs.Acquire(region, tier, r => result = r);
            if (!result.Ok) { done?.Invoke(false); yield break; }
            if (result.TileSceneName != RegionScenes.TileSceneNameFor(region, tier))
            {
                // Pack without the tile scene (built before ADR 0273 / import before ADR 0235): give the lease back.
                m_Packs.Release(region, tier);
                done?.Invoke(false);
                yield break;
            }
            done?.Invoke(true);
        }

        public void Release(string region, string tier)
        {
            if (m_Packs != null && !InBuild(region, tier)) m_Packs.Release(region, tier);
        }
    }
}
