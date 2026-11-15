using System;
using System.Collections.Generic;

namespace Game.World.Packs
{
    /// <summary>
    /// Reference counting of loaded pack bundles (ADR 0273, review s22 #112 P1-2). Several holders may keep regions open
    /// at once - the menu start (one full region scene) and the additive streamer (up to 4 tile scenes of different
    /// regions) - so loading region B must never unload the bundles of region A. A holder takes a lease on a key
    /// ("&lt;region&gt;|&lt;tier&gt;") with the bundle ids that key needs in load order (dependencies first: common, data, scene
    /// bundle); every bundle carries a count of the leases that include it. <see cref="Acquire"/> returns the bundles whose
    /// count went 0 -&gt; 1 (to load, in order), <see cref="Release"/> those whose count went 1 -&gt; 0 (to unload, reverse
    /// order): <c>common</c> is unloaded only when no region of the set is held any more.
    /// Pure C# (EditMode tests without Unity objects). Not thread-safe: main thread only (the service serialises loads).
    /// </summary>
    public sealed class RegionPackLeases
    {
        readonly Dictionary<string, int> m_KeyLeases = new Dictionary<string, int>(StringComparer.Ordinal);
        readonly Dictionary<string, string[]> m_KeyBundles = new Dictionary<string, string[]>(StringComparer.Ordinal);
        readonly Dictionary<string, int> m_BundleRefs = new Dictionary<string, int>(StringComparer.Ordinal);

        public static string Key(string region, string tier) => (region ?? "") + "|" + (tier ?? "");

        public bool IsHeld(string key) => key != null && m_KeyLeases.ContainsKey(key);
        public int LeaseCount(string key) => key != null && m_KeyLeases.TryGetValue(key, out int n) ? n : 0;
        public int BundleRefs(string bundleId) => bundleId != null && m_BundleRefs.TryGetValue(bundleId, out int n) ? n : 0;
        public int HeldKeyCount => m_KeyLeases.Count;
        public int LoadedBundleCount => m_BundleRefs.Count;
        public IEnumerable<string> HeldKeys => m_KeyLeases.Keys;

        /// <summary>Bundle ids of a held key in load order (empty when not held).</summary>
        public IReadOnlyList<string> BundlesOf(string key) =>
            key != null && m_KeyBundles.TryGetValue(key, out var b) ? b : Array.Empty<string>();

        /// <summary>
        /// Takes one lease on <paramref name="key"/>. The first lease of a key records <paramref name="bundleIdsInLoadOrder"/>
        /// (dependencies first, the scene bundle last; duplicates ignored) and returns the bundles not loaded by any other
        /// key, in that order. Further leases of a held key only count (the recorded bundles win; returns empty).
        /// </summary>
        public List<string> Acquire(string key, IReadOnlyList<string> bundleIdsInLoadOrder)
        {
            if (string.IsNullOrEmpty(key)) throw new ArgumentException("empty key", nameof(key));
            var toLoad = new List<string>();
            if (m_KeyLeases.TryGetValue(key, out int n)) { m_KeyLeases[key] = n + 1; return toLoad; }
            var unique = new List<string>();
            if (bundleIdsInLoadOrder != null)
                foreach (var id in bundleIdsInLoadOrder)
                    if (!string.IsNullOrEmpty(id) && !unique.Contains(id)) unique.Add(id);
            m_KeyLeases[key] = 1;
            m_KeyBundles[key] = unique.ToArray();
            foreach (var id in unique)
            {
                m_BundleRefs.TryGetValue(id, out int r);
                m_BundleRefs[id] = r + 1;
                if (r == 0) toLoad.Add(id);
            }
            return toLoad;
        }

        /// <summary>
        /// Gives back one lease. When it was the last lease of the key, returns the bundles no other held key uses, in
        /// reverse load order (scene bundle first, common last). Releasing a key that is not held returns empty.
        /// </summary>
        public List<string> Release(string key)
        {
            var toUnload = new List<string>();
            if (key == null || !m_KeyLeases.TryGetValue(key, out int n)) return toUnload;
            if (n > 1) { m_KeyLeases[key] = n - 1; return toUnload; }
            m_KeyLeases.Remove(key);
            var bundles = m_KeyBundles[key];
            m_KeyBundles.Remove(key);
            for (int i = bundles.Length - 1; i >= 0; i--)
            {
                string id = bundles[i];
                int r = m_BundleRefs[id] - 1;
                if (r > 0) m_BundleRefs[id] = r;
                else { m_BundleRefs.Remove(id); toUnload.Add(id); }
            }
            return toUnload;
        }

        /// <summary>Drops every lease (all bundles unloaded at once); returns every loaded bundle id.</summary>
        public List<string> Clear()
        {
            var all = new List<string>(m_BundleRefs.Keys);
            m_KeyLeases.Clear();
            m_KeyBundles.Clear();
            m_BundleRefs.Clear();
            return all;
        }
    }
}
