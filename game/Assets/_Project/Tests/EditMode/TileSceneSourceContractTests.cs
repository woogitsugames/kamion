using System;
using System.Collections;
using System.Collections.Generic;
using Game.World;
using Game.World.Streaming;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0234 §9 / ADR 0273 §10: the region-pack CONTRACT kept from PR #112 without the pack system. The base game streams
    /// tile scenes only from the player build (<see cref="BuildTileSource"/>); a future pack source (DLC, phone) must be a
    /// drop-in <see cref="ITileSceneSource"/> that passes the same contract as <see cref="PackDouble"/> here:
    /// <list type="number">
    /// <item>scene naming: a pack carries the tile scene under <see cref="RegionScenes.TileSceneNameFor"/> (format below);</item>
    /// <item>availability: IsAvailable false ⇒ Acquire gives false and holds nothing (the seam stays closed);</item>
    /// <item>Acquire calls done exactly once; done(true) ⇒ the tile scene name is loadable and one lease is held;</item>
    /// <item>leases are ref-counted (two holders, two releases) and every successful Acquire is balanced by one Release;</item>
    /// <item>a pack without the tile scene (built before ADR 0273) or a failed load is refused and holds no lease;</item>
    /// <item>a scene in the player build never takes a lease (build first, then pack).</item>
    /// </list>
    /// Out of the game (on branch regionpacks-0234 / PR #112 for later): manifest + SHA-256, install from incoming/,
    /// download, AssetBundle build commands, Win64/Android pack targets.
    /// </summary>
    public class TileSceneSourceContractTests
    {
        /// <summary>
        /// Test double of a region pack source (ADR 0234 §4, leases as RegionPackLeases of #112): asynchronous Acquire (one
        /// yielded frame), per-(region, tier) reference count, contract violations counted instead of thrown.
        /// </summary>
        sealed class PackDouble : ITileSceneSource
        {
            public readonly HashSet<string> Installed = new HashSet<string>();
            public readonly Func<string, bool> InBuild;
            public bool WithTileScene = true, FailLoad;
            public int ReleaseWithoutLease;
            /// <summary>Scene name the "bundle" exposes after a successful Acquire (what the streamer then loads).</summary>
            public string LastLoadableScene;
            readonly Dictionary<string, int> m_Leases = new Dictionary<string, int>();

            public PackDouble(Func<string, bool> inBuild = null) { InBuild = inBuild ?? (_ => false); }

            static string Key(string region, string tier) => region + "|" + tier;
            bool Built(string region, string tier) => InBuild(RegionScenes.TileScenePathFor(region, tier));
            bool Usable(string region, string tier) => Installed.Contains(Key(region, tier));

            public int Leases(string region, string tier) => m_Leases.TryGetValue(Key(region, tier), out int n) ? n : 0;
            public int TotalLeases { get { int n = 0; foreach (var v in m_Leases.Values) n += v; return n; } }

            public bool IsAvailable(string region, string tier) => Built(region, tier) || Usable(region, tier);
            public bool FromPack(string region, string tier) => !Built(region, tier) && Usable(region, tier);

            public IEnumerator Acquire(string region, string tier, Action<bool> done)
            {
                if (Built(region, tier)) { done?.Invoke(true); yield break; }
                if (!Usable(region, tier)) { done?.Invoke(false); yield break; }
                yield return null;   // bundle load is asynchronous
                if (FailLoad) { done?.Invoke(false); yield break; }
                string key = Key(region, tier);
                m_Leases[key] = Leases(region, tier) + 1;
                if (!WithTileScene)
                {
                    m_Leases[key]--;   // pack built before ADR 0273: no tile scene - the lease goes back at once
                    done?.Invoke(false);
                    yield break;
                }
                LastLoadableScene = RegionScenes.TileSceneNameFor(region, tier);
                done?.Invoke(true);
            }

            public void Release(string region, string tier)
            {
                if (Built(region, tier)) return;
                string key = Key(region, tier);
                int n = Leases(region, tier);
                if (n <= 0) { ReleaseWithoutLease++; return; }
                m_Leases[key] = n - 1;
            }
        }

        /// <summary>Runs a coroutine to the end without Unity (nested IEnumerators are entered).</summary>
        static void Drain(IEnumerator e)
        {
            var stack = new Stack<IEnumerator>();
            stack.Push(e);
            int guard = 0;
            while (stack.Count > 0 && guard++ < 10000)
            {
                var top = stack.Peek();
                if (!top.MoveNext()) { stack.Pop(); continue; }
                if (top.Current is IEnumerator inner) stack.Push(inner);
            }
        }

        static readonly string InBuildPath = RegionScenes.TileScenePathFor("dk65-06", RegionScenes.LowTier);

        static IEnumerable<TestCaseData> Sources()
        {
            yield return new TestCaseData((Func<ITileSceneSource>)(() => new BuildTileSource(p => p == InBuildPath))).SetName("Contract_Build");
            yield return new TestCaseData((Func<ITileSceneSource>)(() =>
            {
                var d = new PackDouble(p => p == InBuildPath);
                d.Installed.Add("dk65-07|Low");
                return d;
            })).SetName("Contract_PackDouble");
        }

        // ------------------------------------------------------------------ format

        [Test]
        public void Format_TileSceneNamesAndPaths_AreWhatAPackMustCarry()
        {
            Assert.AreEqual("World_dk65-04_Tile", RegionScenes.TileSceneNameFor("dk65-04"));
            Assert.AreEqual("World_knyszyn_High_Tile", RegionScenes.TileSceneNameFor("knyszyn", RegionScenes.HighTier));
            Assert.AreEqual(RegionScenes.SceneNameFor("bialystok-industrial-c") + "_Tile", RegionScenes.TileSceneNameFor("bialystok-industrial-c"));
            Assert.AreEqual("Assets/_Generated/World/dk65-04/World_dk65-04_Tile.unity", RegionScenes.TileScenePathFor("dk65-04"));
            Assert.AreEqual("Low", RegionScenes.LowTier, "content tiers are part of the pack key (region, tier)");
            Assert.AreEqual("High", RegionScenes.HighTier);
        }

        // ------------------------------------------------------------------ contract (every source)

        [TestCaseSource(nameof(Sources))]
        public void UnavailableTile_AcquireGivesFalse_AndHoldsNothing(Func<ITileSceneSource> make)
        {
            var src = make();
            Assert.IsFalse(src.IsAvailable("dk65-08", "Low"));
            Assert.IsFalse(src.FromPack("dk65-08", "Low"));
            int calls = 0; bool ok = true;
            Drain(src.Acquire("dk65-08", "Low", r => { calls++; ok = r; }));
            Assert.AreEqual(1, calls, "done is called exactly once");
            Assert.IsFalse(ok);
            if (src is PackDouble d) Assert.AreEqual(0, d.TotalLeases);
        }

        [TestCaseSource(nameof(Sources))]
        public void TileInTheBuild_IsAvailable_NeverFromPack_AndAcquiresAtOnce(Func<ITileSceneSource> make)
        {
            var src = make();
            Assert.IsTrue(src.IsAvailable("dk65-06", "Low"));
            Assert.IsFalse(src.FromPack("dk65-06", "Low"), "a region in the player build never takes a pack lease");
            int calls = 0; bool ok = false;
            var e = src.Acquire("dk65-06", "Low", r => { calls++; ok = r; });
            Assert.IsFalse(e.MoveNext(), "build scene: no frame to wait");
            Assert.AreEqual(1, calls); Assert.IsTrue(ok);
            src.Release("dk65-06", "Low");
            if (src is PackDouble d) { Assert.AreEqual(0, d.TotalLeases); Assert.AreEqual(0, d.ReleaseWithoutLease); }
        }

        // ------------------------------------------------------------------ contract (pack)

        [Test]
        public void Pack_LeasesAreRefCounted_AndBalancedByRelease()
        {
            var d = new PackDouble();
            d.Installed.Add("dk65-07|Low");
            Assert.IsTrue(d.IsAvailable("dk65-07", "Low"));
            Assert.IsTrue(d.FromPack("dk65-07", "Low"));
            bool ok = false;
            Drain(d.Acquire("dk65-07", "Low", r => ok = r));
            Assert.IsTrue(ok);
            Assert.AreEqual(RegionScenes.TileSceneNameFor("dk65-07"), d.LastLoadableScene, "done(true) => the tile scene is loadable by its RegionScenes name");
            Drain(d.Acquire("dk65-07", "Low", r => ok = r));   // second holder (e.g. menu + streamer)
            Assert.AreEqual(2, d.Leases("dk65-07", "Low"));
            d.Release("dk65-07", "Low");
            Assert.AreEqual(1, d.Leases("dk65-07", "Low"), "one release does not unload the bundles of the other holder");
            d.Release("dk65-07", "Low");
            Assert.AreEqual(0, d.TotalLeases);
            d.Release("dk65-07", "Low");
            Assert.AreEqual(1, d.ReleaseWithoutLease, "the double counts an unbalanced release (contract violation)");
        }

        [Test]
        public void Pack_WithoutTileScene_OrFailedLoad_IsRefused_AndHoldsNoLease()
        {
            var d = new PackDouble { WithTileScene = false };
            d.Installed.Add("knyszyn|High");
            bool ok = true; int calls = 0;
            Drain(d.Acquire("knyszyn", "High", r => { calls++; ok = r; }));
            Assert.AreEqual(1, calls);
            Assert.IsFalse(ok, "old pack (before ADR 0273) has no tile scene");
            Assert.AreEqual(0, d.TotalLeases, "its lease is given back at once");
            d.WithTileScene = true; d.FailLoad = true; ok = true;
            Drain(d.Acquire("knyszyn", "High", r => ok = r));
            Assert.IsFalse(ok);
            Assert.AreEqual(0, d.TotalLeases);
        }

        // ------------------------------------------------------------------ base game

        [Test]
        public void BuildTileSource_IsTheOnlyRuntimeSource_AndNeverHoldsLeases()
        {
            var src = new BuildTileSource(p => p == InBuildPath);
            Assert.IsTrue(src.IsAvailable("dk65-06", RegionScenes.LowTier));
            Assert.IsFalse(src.IsAvailable("dk65-06", RegionScenes.HighTier), "the High tile scene is a different build entry");
            Assert.IsFalse(src.FromPack("dk65-06", RegionScenes.LowTier));
            Assert.IsFalse(src.FromPack("dk65-07", RegionScenes.LowTier));
            Assert.DoesNotThrow(() => src.Release("dk65-07", RegionScenes.LowTier), "Release is a no-op for the build");
            Assert.IsNull(Type.GetType("Game.World.Packs.RegionPackService, Game.World"),
                "ADR 0273 §10: the pack runtime (#112) is not in the base game; only this contract is");
        }
    }
}
