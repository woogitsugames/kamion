using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using System.Text.RegularExpressions;
using Game.Core;
using Game.World;
using Game.World.Streaming;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

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

        /// <summary>Tile root as imported (W = its anchor) with a drivable rectangle 100 m inside the tile.</summary>
        WorldRegionRoot StartRoot(TileGraph g) => TileRoot(g.Tiles[0]);

        WorldRegionRoot TileRoot(TileData t)
        {
            var root = Make("Region_" + t.id).AddComponent<WorldRegionRoot>();
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

        sealed class ThrowingTileSource : ITileSceneSource
        {
            public readonly HashSet<string> HeldLeases = new HashSet<string>();
            public readonly List<string> ReleaseAttempts = new List<string>();

            public bool IsAvailable(string region, string tier) => true;
            public bool FromPack(string region, string tier) => true;

            public IEnumerator Acquire(string region, string tier, Action<bool> done)
            {
                done(HeldLeases.Add(region));
                yield break;
            }

            public void Release(string region, string tier)
            {
                ReleaseAttempts.Add(region);
                if (region == "t1") throw new InvalidOperationException("Synthetic t1 release failure");
                HeldLeases.Remove(region);
            }
        }

        [Test]
        public void DestroyStreamer_CleansAllTilesAfterClearAndLeaseReleaseFailure()
        {
            var shader = Shader.Find("Kamion/World Surface");
            Assert.That(shader, Is.Not.Null);
            var original = new Material(shader);
            bool farRingWasEnabled = FarRing.Enabled;
            var clones = new Material[3];
            try
            {
                FarRing.Enabled = true;
                original.EnableKeyword("_FAR_FACADE");
                var graph = Row3();
                var roots = new[] { StartRoot(graph), TileRoot(graph.Tiles[1]), TileRoot(graph.Tiles[2]) };

                MeshRenderer AddFarSector(WorldRegionRoot root)
                {
                    var edge = Make("WorldEdge").transform;
                    edge.SetParent(root.transform, false);
                    var far = Make("WorldFarField").transform;
                    far.SetParent(edge, false);
                    var sector = Make("FarField_far_north").AddComponent<MeshRenderer>();
                    sector.transform.SetParent(far, false);
                    sector.sharedMaterial = original;
                    return sector;
                }

                var sectors = Array.ConvertAll<WorldRegionRoot, MeshRenderer>(roots, AddFarSector);
                var streamer = HandBuilt(graph, roots[0], _ => true, out _);
                streamer.AdoptVisualQaTile(roots[1]);
                streamer.AdoptVisualQaTile(roots[2]);
                for (int i = 0; i < clones.Length; i++) clones[i] = sectors[i].sharedMaterial;

                Assert.That(Array.FindAll(clones, m => m != null && m != original).Length, Is.EqualTo(3));
                CollectionAssert.AllItemsAreUnique(clones);
                foreach (var clone in clones)
                    Assert.That(clone.IsKeywordEnabled(FarRing.ClipKeyword), Is.True);

                // The synthetic scenes were adopted without loading. Set up post-Acquire lease state explicitly.
                var source = new ThrowingTileSource();
                var tiles = (Array)typeof(WorldStreamer).GetField("m_Tiles", BindingFlags.Instance | BindingFlags.NonPublic)
                    .GetValue(streamer);
                var leased = tiles.GetValue(0).GetType().GetField("leased");
                for (int i = 0; i < tiles.Length; i++)
                {
                    bool acquired = false;
                    var acquire = source.Acquire(graph.Tiles[i].id, streamer.contentTier, ok => acquired = ok);
                    Assert.That(acquire.MoveNext(), Is.False);
                    Assert.That(acquired, Is.True);
                    leased.SetValue(tiles.GetValue(i), true);
                }
                streamer.source = source;

                // Reproduce Clear during unload, before the lease is returned by scene unload completion.
                typeof(WorldStreamer).GetMethod("Clear", BindingFlags.Static | BindingFlags.NonPublic)
                    .Invoke(null, new[] { tiles.GetValue(0) });
                Assert.That(clones[0] == null, Is.True);
                Assert.That(Array.FindAll(clones, m => m != null).Length, Is.EqualTo(2));
                Assert.That(source.ReleaseAttempts, Is.Empty);

                LogAssert.Expect(LogType.Exception, new Regex(@"\[STREAM\].*failed to release tile lease"));
                UnityEngine.Object.DestroyImmediate(streamer.gameObject);

                Assert.That(Array.FindAll(clones, m => m != null).Length, Is.Zero);
                CollectionAssert.AreEqual(new[] { "t0", "t1", "t2" }, source.ReleaseAttempts);
                CollectionAssert.AreEquivalent(new[] { "t1" }, source.HeldLeases);
                Assert.That(original != null, Is.True);
            }
            finally
            {
                FarRing.Enabled = farRingWasEnabled;
                foreach (var clone in clones)
                    if (clone != null && clone != original) UnityEngine.Object.DestroyImmediate(clone);
                UnityEngine.Object.DestroyImmediate(original);
            }
        }

        [Test]
        public void StaticQa_RealNeighbourOpensBothClosuresAndRemovesStubAprons()
        {
            var graph = Row3();
            var a = StartRoot(graph);
            GameObject Edge(WorldRegionRoot r, TileSide side)
            {
                var boundary = r.GetComponent<WorldBoundary>();
                boundary.closures = new[] { new WorldBoundary.Closure { exitSide = side, widthM = 8f } };
                var edge = Make("WorldEdge"); edge.transform.SetParent(r.transform, false);
                foreach (string name in new[] { "Closure_00_test", "Apron", "Apron_E", "Apron_W" })
                    Make(name).transform.SetParent(edge.transform, false);
                return edge;
            }
            var ea = Edge(a, TileSide.E);
            var s = HandBuilt(graph, a, _ => false, out _);
            s.enabled = false;
            Assert.IsTrue(ea.transform.Find("Closure_00_test").gameObject.activeSelf);
            var b = Make("Region_t1").AddComponent<WorldRegionRoot>();
            b.regionId = "t1";
            b.anchorX = graph.Tiles[1].anchorX; b.anchorY = graph.Tiles[1].anchorY; b.anchorZ = graph.Tiles[1].anchorZ;
            var bb = b.gameObject.AddComponent<WorldBoundary>();
            bb.minEN = new Vector2(-924f, -924f); bb.maxEN = new Vector2(924f, 924f);
            var eb = Edge(b, TileSide.W);
            s.AdoptVisualQaTile(b);
            Assert.AreEqual(TileState.Ready, s.Policy.StateOf(1));
            Assert.AreEqual(0, s.Policy.Current, "context must not move the start tile");
            Assert.AreEqual((float)Size, b.transform.position.x);
            foreach (var edge in new[] { ea, eb })
            {
                Assert.IsFalse(edge.transform.Find("Closure_00_test").gameObject.activeSelf);
                Assert.IsFalse(edge.transform.Find("Apron").gameObject.activeSelf);
            }
            Assert.IsFalse(ea.transform.Find("Apron_E").gameObject.activeSelf);
            Assert.IsFalse(eb.transform.Find("Apron_W").gameObject.activeSelf);
            Assert.IsTrue(ea.transform.Find("Apron_W").gameObject.activeSelf, "outer edges remain closed");
            Assert.IsTrue(eb.transform.Find("Apron_E").gameObject.activeSelf);
        }

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
            // The streamer's own tile rectangle was taken before (the widening does not move it). Before the first decision
            // the available t1 counts as Loading, so the t0/t1 seam is not an outer edge (ADR 0273 §10 pkt 5, D36): the
            // nearest outer edge of a point 100 m inside the east side of t0 is north / south (924 m).
            Assert.IsTrue(s.TryInsideDistance(new Vector3(824f, 0f, 0f), out float inside));
            Assert.AreEqual(924f, inside, 1e-3f);
            // t1 not coming (e.g. left behind / unloaded after a decision): the seam is an outer edge again, 100 m away.
            s.Policy.SetState(1, TileState.Unloading);
            Assert.IsTrue(s.TryInsideDistance(new Vector3(824f, 0f, 0f), out inside));
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
            s.routePath = new FakeRoute { pts = new[] { new Vector3(5000f, 0f, 0f), new Vector3(5100f, 0f, 0f) } };   // ends nowhere near a tile route
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

        // ------------------------------------------------------------------ route continuation across seams (int-stream-s23)

        sealed class FakeRoute : IStreamedRoute
        {
            public Vector3[] pts;
            public int appends;
            public bool TryGetPathEnd(out Vector3 worldEnd)
            {
                if (pts == null || pts.Length < 2) { worldEnd = default; return false; }
                worldEnd = pts[pts.Length - 1];
                return true;
            }
            public void AppendPath(Vector3[] worldPoints, float[] speedLimitsKmh)
            {
                var n = new Vector3[pts.Length + worldPoints.Length];
                pts.CopyTo(n, 0); worldPoints.CopyTo(n, pts.Length);
                pts = n; appends++;
            }
        }

        static void CallUpdate(WorldStreamer s) =>
            typeof(WorldStreamer).GetMethod("Update", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(s, null);

        [Test]
        public void RouteContinuation_AppendsTheReadyTileRouteStartingAtThePathEnd_Once()
        {
            var g = Row3();
            var root = StartRoot(g);
            var wr = Make("Route_t0").AddComponent<WorldRoute>();
            wr.points = new[] { new Vector3(0f, 0f, 0f), new Vector3(100f, 0f, 0f), new Vector3(200f, 0f, 0f) };
            wr.distances = new[] { 0f, 100f, 200f };
            wr.speedLimitsKmh = new[] { 50f, 50f, 50f };
            var s = HandBuilt(g, root, _ => false, out _);
            Vector3 first = wr.transform.TransformPoint(wr.points[0]);   // after Init placed the route (world anchor + height)

            var far = new FakeRoute { pts = new[] { first + new Vector3(-80f, 0f, 0f), first + new Vector3(-10f, 0f, 0f) } };
            s.routePath = far;
            CallUpdate(s);
            Assert.AreEqual(0, far.appends, "10 m gap > routeJoinM: not the same road, never chained");

            var near = new FakeRoute { pts = new[] { first + new Vector3(-80f, 0f, 0f), first + new Vector3(-1f, 3f, 0.5f) } };
            s.routePath = near;
            CallUpdate(s);
            Assert.AreEqual(1, near.appends, "the Ready tile's route begins at the path end (height ignored): appended");
            Assert.AreEqual(5, near.pts.Length);
            Assert.AreEqual(wr.transform.TransformPoint(wr.points[2]), near.pts[4], "world-space points of the tile route");
            CallUpdate(s);
            Assert.AreEqual(1, near.appends, "a tile route is appended once");
        }

        [Test]
        public void PathFollower_PathEnd_OnlyWhileDrivingWithoutAnExplicitEnd()
        {
            var d = new Game.Controls.PathFollowerDriverInput();
            Assert.IsFalse(d.TryGetPathEnd(out _), "no path");
            d.SetPath(new[] { Vector3.zero, new Vector3(0f, 0f, 100f) });
            Assert.IsFalse(d.TryGetPathEnd(out _), "disabled (not the active autopilot)");
            d.Enabled = true;
            Assert.IsTrue(d.TryGetPathEnd(out Vector3 e));
            Assert.AreEqual(100f, e.z, 1e-4f);
            d.AppendPath(new[] { new Vector3(0f, 0f, 100.2f), new Vector3(0f, 0f, 300f) }, null);
            Assert.AreEqual(300f, d.Length, 0.01f, "the repeated seam point is merged");
            Assert.IsTrue(d.TryGetPathEnd(out e)); Assert.AreEqual(300f, e.z, 1e-4f);
            d.EndS = 150f;
            Assert.IsFalse(d.TryGetPathEnd(out _), "route_end: a measured segment stops where asked, never continued");
        }
    }
}
