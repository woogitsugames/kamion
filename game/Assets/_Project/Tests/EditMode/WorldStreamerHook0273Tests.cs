using System;
using System.Collections.Generic;
using System.Reflection;
using Game.Core;
using Game.World;
using Game.World.Streaming;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0273 §10 (D30, s23): the single hook of the driving scene (<see cref="WorldStreamer.TryInstallFromLaunch"/>) and
    /// zero GC in the streamer's steady frame loop. A streamer is built by hand on a synthetic 3 x 1 tile grid (no scenes):
    /// Init on a start root, safe-pose pinning, the widened safety-net rectangle, the origin listener and the per-frame
    /// Update + safety queries counted with <see cref="GcAllocCounter"/> (Recorder "GC.Alloc", ADR 0244 / PR #118 pattern).
    /// The async load / activation / rebase path with real tile scenes is WorldStreamingPlayModeTests (dk65-03 → 04).
    /// </summary>
    public class WorldStreamerHook0273Tests
    {
        const double Size = 2048.0;
        readonly List<GameObject> m_Objects = new List<GameObject>();

        [TearDown]
        public void TearDown()
        {
            WorldStreamer.EnabledOverride = null;
            foreach (var go in m_Objects) if (go != null) UnityEngine.Object.DestroyImmediate(go);
            m_Objects.Clear();
        }

        /// <summary>Tiles t0, t1, t2 west to east (2048 m), anchors in the tile centres.</summary>
        static TileGraph Row3()
        {
            var tiles = new List<TileData>();
            for (int c = 0; c < 3; c++)
            {
                double x0 = 700000.0 + c * Size, y0 = 600000.0;
                tiles.Add(new TileData
                {
                    id = "t" + c, xmin = x0, ymin = y0, xmax = x0 + Size, ymax = y0 + Size,
                    anchorX = x0 + Size / 2, anchorY = y0 + Size / 2, anchorZ = 120.0, worldMemoryMB = 50f,
                });
            }
            for (int c = 0; c < 3; c++)
            {
                var ns = new List<NeighborData>();
                if (c > 0) ns.Add(new NeighborData { id = "t" + (c - 1), side = "W", seamM = (float)Size });
                if (c < 2) ns.Add(new NeighborData { id = "t" + (c + 1), side = "E", seamM = (float)Size });
                tiles[c].neighbors = ns.ToArray();
            }
            return new TileGraph(new TileGraphData { schema = TileGraph.Schema, tiles = tiles.ToArray() });
        }

        GameObject Make(string name) { var go = new GameObject(name); m_Objects.Add(go); return go; }

        /// <summary>Start root of tile t0 as imported (W = its anchor) with a drivable rectangle 100 m inside the tile.</summary>
        WorldRegionRoot StartRoot(TileGraph g)
        {
            var t = g.Tiles[0];
            var root = Make("Region_t0").AddComponent<WorldRegionRoot>();
            root.regionId = t.id; root.anchorX = t.anchorX; root.anchorY = t.anchorY; root.anchorZ = t.anchorZ;
            var b = root.gameObject.AddComponent<WorldBoundary>();
            b.minEN = new Vector2(-924f, -924f); b.maxEN = new Vector2(924f, 924f);
            return root;
        }

        WorldStreamer HandBuilt(TileGraph g, WorldRegionRoot root, Func<string, bool> inBuild, out Transform vehicle)
        {
            vehicle = Make("Vehicle").transform;
            vehicle.position = new Vector3(0f, 0f, 0f);
            var s = Make("Streamer").AddComponent<WorldStreamer>();
            s.vehicle = vehicle;
            s.decideIntervalS = 0f;   // decide on every Update call
            s.source = new BuildTileSource(inBuild);
            s.Init(g, 0, root);
            return s;
        }

        // ------------------------------------------------------------------ the hook

        [Test]
        public void TryInstallFromLaunch_Off_AddsNothing()
        {
            var host = Make("Host");
            var root = StartRoot(Row3());
            var poses = new SafePoseBuffer(8);
            WorldStreamer.EnabledOverride = null;
            Assert.IsFalse(WorldStreamer.IsRequested(null), "no argument = off (opt-in, ADR 0273 §7)");
            Assert.IsFalse(WorldStreamer.IsRequested("0"));
            Assert.IsTrue(WorldStreamer.IsRequested("1"));
            Assert.IsNull(WorldStreamer.TryInstallFromLaunch(host, root, host.transform, null, null, poses, 2.5f, null));
            Assert.IsNull(WorldStreamer.TryInstallFromLaunch(host, root, host.transform, null, "0", poses, 2.5f, null));
            WorldStreamer.EnabledOverride = false;
            Assert.IsNull(WorldStreamer.TryInstallFromLaunch(host, root, host.transform, null, "1", poses, 2.5f, null), "override wins over the argument");
            Assert.IsNull(host.GetComponent<WorldStreamer>(), "off: no component, the scene is exactly as before");
            var b = root.GetComponent<WorldBoundary>();
            Assert.AreEqual(new Vector2(924f, 924f), b.maxEN, "off: the safety-net rectangle is untouched");
        }

        [Test]
        public void TryInstallFromLaunch_RegionNotInTheShippedGraph_StaysOff()
        {
            var host = Make("Host");
            var root = Make("Region_x").AddComponent<WorldRegionRoot>();
            root.regionId = "no-such-region-0273";
            WorldStreamer.EnabledOverride = true;
            Assert.IsNull(WorldStreamer.TryInstallFromLaunch(host, root, host.transform, null, "1", new SafePoseBuffer(8), 2.5f, null));
            Assert.IsNull(host.GetComponent<WorldStreamer>());
        }

        [Test]
        public void WidenStartBoundary_CoversTheConnectedAvailableTiles_Only()
        {
            var g = Row3();
            var root = StartRoot(g);
            // t1 in the build, t2 not: the union is t0's drivable rectangle + t1 (t2 never loads).
            var s = HandBuilt(g, root, p => p.Contains("/t1/"), out _);
            Assert.IsTrue(s.WidenStartBoundary(root));
            var b = root.GetComponent<WorldBoundary>();
            Assert.AreEqual(-924f, b.minEN.x, 1e-3f, "west: no neighbour, the drivable rectangle stays");
            Assert.AreEqual(-924f, b.minEN.y, 1e-3f);
            Assert.AreEqual(924f, b.maxEN.y, 1e-3f, "N/S: t1's tile rectangle shrunk by the start's 100 m inset = the same drivable edge");
            Assert.AreEqual((float)(2 * Size - Size / 2) - 100f, b.maxEN.x, 1e-3f, "east: to the drivable far edge of t1 (region-local of t0)");
            // The streamer's own tile rectangle was taken before (open-seam logic unchanged): 100 m inside the east edge of t0
            // is inside even with the seam closed.
            Assert.IsTrue(s.TryInsideDistance(new Vector3(824f, 0f, 0f), out float inside));
            Assert.AreEqual(100f, inside, 1e-3f);
        }

        [Test]
        public void LocalUnionBounds_FollowsNeighboursThroughIncludedTilesOnly()
        {
            var g = Row3();
            Assert.IsTrue(g.LocalUnionBounds(0, new[] { true, false, true }, out double minE, out double minN, out double maxE, out double maxN));
            Assert.AreEqual(-Size / 2, minE, 1e-9); Assert.AreEqual(Size / 2, maxE, 1e-9, "t2 is not connected without t1");
            Assert.AreEqual(-Size / 2, minN, 1e-9); Assert.AreEqual(Size / 2, maxN, 1e-9);
            Assert.IsTrue(g.LocalUnionBounds(0, new[] { true, true, true }, out minE, out _, out maxE, out _));
            Assert.AreEqual(2.5 * Size, maxE, 1e-9);
            Assert.IsFalse(g.LocalUnionBounds(0, new[] { true, false, false }, out _, out _, out _, out _, withOrigin: false), "nothing but the origin");
        }

        [Test]
        public void SafePoses_PinTheirTile_AndOriginListenerFollowsTheStreamer()
        {
            var g = Row3();
            var root = StartRoot(g);
            var s = HandBuilt(g, root, p => p.Contains("/t1/"), out _);
            var poses = new SafePoseBuffer(8);
            s.UseSafePoses(poses, 2.5f);
            Assert.IsNotNull(s.recoveryPoint);
            Assert.IsFalse(s.recoveryPoint(out _), "no safe pose yet: the start tile stays pinned");
            poses.Record(Time.time - 10f, new Vector3(1500f, 0f, 0f), 90f);   // in t1 (local east 1500 m of t0)
            Assert.IsTrue(s.recoveryPoint(out Vector3 rp));
            Assert.AreEqual(1, g.TileAt(s.AnchorX + rp.x, s.AnchorY + rp.z));

            Vector3 got = Vector3.zero; int calls = 0;
            s.AddOriginListener(o => { got += o; calls++; });
            FloatingOrigin.Notify(new Vector3(-2048f, 0f, 0f));
            Assert.AreEqual(1, calls); Assert.AreEqual(-2048f, got.x);
            s.RemoveOriginListener();
            FloatingOrigin.Notify(new Vector3(2048f, 0f, 0f));   // restore the process total; the listener is gone
            Assert.AreEqual(1, calls, "unsubscribed with the streamer (OnDestroy)");
            poses.Offset(new Vector3(-2048f, 0f, 0f));
            Assert.IsTrue(poses.TryGet(Time.time, 2.5f, out var pose));
            Assert.AreEqual(1500f - 2048f, pose.position.x, 1e-3f, "rebase moves the safety net's buffer with the world");
        }

        // ------------------------------------------------------------------ zero GC (CLAUDE.md, ADR 0244)

        [Test]
        public void SteadyFrameLoop_UpdateAndSafetyQueries_AllocateNothing()
        {
            var g = Row3();
            var root = StartRoot(g);
            // No neighbour scene in the build: every decision runs (decideIntervalS = 0) and finds nothing to load - the
            // steady state of a long drive inside one tile. Tile events (load, activation, rebase) allocate by design.
            var s = HandBuilt(g, root, _ => false, out var vehicle);
            var poses = new SafePoseBuffer(32);
            poses.Record(Time.time - 10f, new Vector3(10f, 0f, 0f), 0f);
            s.UseSafePoses(poses, 2.5f);
            var update = (Action)Delegate.CreateDelegate(typeof(Action), s,
                typeof(WorldStreamer).GetMethod("Update", BindingFlags.Instance | BindingFlags.NonPublic));
            float sink = 0f;
            int frame = 0;
            Action frames = () =>
            {
                for (int i = 0; i < 600; i++, frame++)
                {
                    vehicle.position = new Vector3(-300f + (frame % 600), 0f, 50f);
                    update();
                    if (s.TryInsideDistance(vehicle.position, out float d)) sink += d;
                    if (s.recoveryPoint(out Vector3 rp)) sink += rp.x;
                }
            };
            GcAllocCounter.AssertZero(frames, warmup: frames, message: "WorldStreamer.Update + TryInsideDistance + recovery point must not allocate per frame");
            Assert.Greater(sink, 0f);
        }
    }
}
