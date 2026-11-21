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
    /// stream-gaps-s23: the corridor Bialystok -> Knyszyn -> Tykocin is one chain of tiles joined by routes and route links
    /// (Resources/WorldStreaming/route_links.json, tools/worldgen/streaming/route_links.py), and the streamer continues the
    /// route autopilot with a link of the chosen destination (replacing the knyszyn control route that ends at Rynek).
    /// </summary>
    public class WorldStreamerRouteLinksTests
    {
        const double Size = 2048.0;
        readonly List<GameObject> m_Objects = new List<GameObject>();

        [TearDown]
        public void TearDown()
        {
            foreach (var go in m_Objects) if (go != null) UnityEngine.Object.DestroyImmediate(go);
            m_Objects.Clear();
        }

        GameObject Make(string name) { var go = new GameObject(name); m_Objects.Add(go); return go; }

        // ------------------------------------------------------------------ shipped data

        static RouteCorridorData Corridor(RouteLinks l, string id)
        {
            foreach (var c in l.Corridors) if (c.id == id) return c;
            return null;
        }

        [Test]
        public void ShippedLinks_LoadThroughJsonUtility_AndJoinTheCorridorToTykocin()
        {
            var g = TileGraph.LoadDefault();
            var l = RouteLinks.LoadDefault(g);
            Assert.Greater(l.Count, 0, "Resources/" + RouteLinks.ResourcePath);
            var c = Corridor(l, "bialystok-tykocin");
            Assert.IsNotNull(c);
            Assert.AreEqual("bialystok-industrial-c", c.tiles[0]);
            int kw = Array.IndexOf(c.tiles, "knyszyn-w"), k = Array.IndexOf(c.tiles, "knyszyn"), ty = Array.IndexOf(c.tiles, "dw671-tykocin-01");
            Assert.IsTrue(k > 0 && kw == k + 1 && ty == kw + 1, string.Join(",", c.tiles));
            Assert.AreEqual(c.tiles.Length - 1, c.joins.Length);
            for (int i = 0; i < c.joins.Length; i++)
            {
                var j = c.joins[i];
                Assert.AreEqual(c.tiles[i], j.from); Assert.AreEqual(c.tiles[i + 1], j.to);
                var side = g.SideOf(g.IndexOf(j.from), g.IndexOf(j.to));
                Assert.IsTrue(side == TileSide.N || side == TileSide.E || side == TileSide.S || side == TileSide.W, $"{j.from}|{j.to}: edge neighbours (a corner never opens a seam)");
                Assert.LessOrEqual(j.gapM, 2.0f, $"{j.from}|{j.to}: route join (closed = no continuation)");
            }
            // the knyszyn control route (Rynek, dead end) is replaced for Tykocin and for Monki, never otherwise
            int kt = g.IndexOf("knyszyn");
            Assert.IsTrue(l.IsRouteReplaced(kt, "tykocin"));
            Assert.IsTrue(l.IsRouteReplaced(kt, "monki"));
            Assert.IsFalse(l.IsRouteReplaced(kt, "rynek"));
            for (int i = 0; i < l.Count; i++)
            {
                Assert.GreaterOrEqual(l.TileOf[i], 0, l.Links[i].id);
                Assert.AreEqual(l.Links[i].e.Length, l.Links[i].n.Length);
                Assert.AreEqual(l.Links[i].e.Length, l.Links[i].maxspeedKmh.Length);
                var t = g.Tiles[l.TileOf[i]];
                for (int p = 0; p < l.Links[i].e.Length; p++)       // a link stays in its tile (0.5 m: lane points on the seam)
                    Assert.IsTrue(g.Contains(l.TileOf[i], t.anchorX + l.Links[i].e[p], t.anchorY + l.Links[i].n[p], 3.0), $"{l.Links[i].id} point {p}");
            }
        }

        [Test]
        public void ShippedLinks_ChainEndToStart_AtTheNewSeams()
        {
            var g = TileGraph.LoadDefault();
            var l = RouteLinks.LoadDefault(g);
            RouteLinkData a = null, b = null;
            foreach (var x in l.Links) { if (x.id == "knyszyn-dk65-to-dw671-w") a = x; if (x.id == "knyszyn-w-dw671") b = x; }
            Assert.IsNotNull(a); Assert.IsNotNull(b);
            double gap = Math.Sqrt((a.endX - b.startX) * (a.endX - b.startX) + (a.endY - b.startY) * (a.endY - b.startY));
            Assert.LessOrEqual(gap, 0.05, "knyszyn | knyszyn-w on DW671");
            // knyszyn-w link ends on the dw671-tykocin-01 route entry (ADR 0212: 760129.2, 611583 boundary node)
            Assert.AreEqual(760129.2, b.endX, 2.0); Assert.AreEqual(611583.0, b.endY, 2.0);
            Assert.AreEqual(0, string.Compare(RouteLinks.DefaultDestination, "tykocin", StringComparison.Ordinal));
        }

        /// <summary>seams-fix-s23: a drive started in knyszyn (-scene knyszyn) has the control route to Rynek as its path; per
        /// destination one link `afterRoute: knyszyn` continues it (no replacement: the start route is already driven) and
        /// ends where the corridor link of that destination ends, so the next link / route joins it.</summary>
        [Test]
        public void ShippedLinks_KnyszynStart_ContinuesFromRynek_ToTheSameSeam()
        {
            var g = TileGraph.LoadDefault();
            var l = RouteLinks.LoadDefault(g);
            foreach (var dest in new[] { "tykocin", "monki" })
            {
                RouteLinkData after = null, corridor = null;
                int nAfter = 0;
                foreach (var x in l.Links)
                {
                    if (!RouteLinks.Applies(x.destination, dest) || x.tile != "knyszyn") continue;
                    if (x.afterRoute == "knyszyn") { after = x; nAfter++; }
                    if (x.replacesRoute == "knyszyn") corridor = x;
                }
                Assert.AreEqual(1, nAfter, dest);
                Assert.IsNotNull(corridor, dest);
                Assert.IsTrue(string.IsNullOrEmpty(after.replacesRoute), after.id);
                Assert.AreEqual(corridor.endX, after.endX, 0.05, after.id);
                Assert.AreEqual(corridor.endY, after.endY, 0.05, after.id);
            }
            RouteLinkData rt = null, w = null;
            foreach (var x in l.Links) { if (x.id == "knyszyn-rynek-to-dw671-w") rt = x; if (x.id == "knyszyn-w-dw671") w = x; }
            Assert.IsNotNull(rt); Assert.IsNotNull(w);
            Assert.AreEqual(rt.endX, w.startX, 0.05); Assert.AreEqual(rt.endY, w.startY, 0.05);
        }

        [Test]
        public void DestinationFromArgs_DefaultTykocin_DashAndEqualsForms()
        {
            Assert.AreEqual("tykocin", RouteLinks.DestinationFromArgs(null));
            Assert.AreEqual("tykocin", RouteLinks.DestinationFromArgs(new[] { "Kamion.exe", "-scene", "knyszyn", "-stream", "1" }));
            Assert.AreEqual("monki", RouteLinks.DestinationFromArgs(new[] { "Kamion.exe", "-route_to", "monki" }));
            Assert.AreEqual("monki", RouteLinks.DestinationFromArgs(new[] { "route_to=monki" }));
            Assert.AreEqual("tykocin", RouteLinks.DestinationFromArgs(new[] { "-route_to" }), "missing value");
            Assert.IsTrue(RouteLinks.Applies("any", "monki"));
            Assert.IsTrue(RouteLinks.Applies("Tykocin", "tykocin"));
            Assert.IsFalse(RouteLinks.Applies("monki", "tykocin"));
        }

        // ------------------------------------------------------------------ streamer: continuation by links

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

        static TileGraph Row3()
        {
            var tiles = new List<TileData>();
            for (int c = 0; c < 3; c++)
            {
                double x0 = 700000.0 + c * Size, y0 = 600000.0;
                tiles.Add(new TileData { id = "t" + c, xmin = x0, ymin = y0, xmax = x0 + Size, ymax = y0 + Size,
                                         anchorX = x0 + Size / 2, anchorY = y0 + Size / 2, anchorZ = 120.0, worldMemoryMB = 50f });
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

        static RouteLinkData Link(string id, string tile, string dest, string replaces, TileData t, double x0, double y0, double x1, double y1)
        {
            return new RouteLinkData
            {
                id = id, tile = tile, destination = dest, replacesRoute = replaces, lengthM = (float)(x1 - x0),
                e = new[] { (float)(x0 - t.anchorX), (float)((x0 + x1) / 2 - t.anchorX), (float)(x1 - t.anchorX) },
                n = new[] { (float)(y0 - t.anchorY), (float)((y0 + y1) / 2 - t.anchorY), (float)(y1 - t.anchorY) },
                maxspeedKmh = new[] { 50f, 50f, 50f }, startX = x0, startY = y0, endX = x1, endY = y1,
            };
        }

        static void CallUpdate(WorldStreamer s) =>
            typeof(WorldStreamer).GetMethod("Update", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(s, null);

        [Test]
        public void Links_OfTheChosenDestination_ContinueThePath_WhenTheirTileIsReady_Once()
        {
            var g = Row3();
            var t0 = g.Tiles[0];
            var root = Make("Region_t0").AddComponent<WorldRegionRoot>();
            root.regionId = t0.id; root.anchorX = t0.anchorX; root.anchorY = t0.anchorY; root.anchorZ = t0.anchorZ;
            var b = root.gameObject.AddComponent<WorldBoundary>();
            b.minEN = new Vector2(-924f, -924f); b.maxEN = new Vector2(924f, 924f);
            var vehicle = Make("Vehicle").transform;
            var s = Make("Streamer").AddComponent<WorldStreamer>();
            s.vehicle = vehicle; s.decideIntervalS = 0f;
            s.source = new BuildTileSource(_ => false);
            s.Init(g, 0, root);
            // seam t0 | t1 at x = 702048; t1 link (replaces t1's route) to the seam t1 | t2, then a t2 link
            double ys = 601000.0, seam1 = 700000.0 + Size, seam2 = 700000.0 + 2 * Size;
            var data = new RouteLinksData
            {
                links = new[]
                {
                    Link("t1-monki", "t1", "monki", "t1", g.Tiles[1], seam1, ys, seam2, ys + 500.0),
                    Link("t1-tyk", "t1", "tykocin", "t1", g.Tiles[1], seam1, ys, seam2, ys),
                    Link("t2-tyk", "t2", "tykocin", "", g.Tiles[2], seam2, ys, seam2 + 900.0, ys),
                },
            };
            s.SetRouteLinks(new RouteLinks(data, g));
            s.routeDestination = "tykocin";
            Vector3 seamW = new Vector3((float)(seam1 - s.AnchorX), 0f, (float)(ys - s.AnchorY));
            var path = new FakeRoute { pts = new[] { seamW + new Vector3(-300f, 0f, 0f), seamW + new Vector3(-0.5f, 0f, 1f) } };
            s.routePath = path;
            vehicle.position = seamW + new Vector3(-100f, 0f, 0f);   // near the seam: t1 never unloaded as "far"

            CallUpdate(s);
            Assert.AreEqual(0, path.appends, "t1 not Ready: its link waits (the seam is still closed)");
            s.Policy.SetState(1, TileState.Ready);
            CallUpdate(s);
            Assert.AreEqual(1, path.appends, "t1 Ready: the tykocin link (not the monki one) continues the path");
            Assert.AreEqual(seam2 - s.AnchorX, path.pts[path.pts.Length - 1].x, 0.01);
            Assert.AreEqual(ys - s.AnchorY, path.pts[path.pts.Length - 1].z, 0.01, "tykocin link end (monki would end 500 m north)");
            CallUpdate(s);
            Assert.AreEqual(1, path.appends, "t2 not Ready");
            vehicle.position = new Vector3((float)(seam2 - s.AnchorX) - 100f, 0f, (float)(ys - s.AnchorY));
            s.Policy.SetState(2, TileState.Ready);
            CallUpdate(s);
            Assert.AreEqual(2, path.appends, "chained link in the next tile");
            CallUpdate(s);
            Assert.AreEqual(2, path.appends, "each link once");
        }

        // ------------------------------------------------------------------ route-start-s24: start tile replaced

        sealed class FakeReplaceableRoute : IReplaceableStreamedRoute
        {
            public Vector3[] pts;
            public int appends, replaces;
            public bool accept = true;
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
            public bool TryReplacePath(Vector3[] worldPoints, float[] speedLimitsKmh, float maxOffsetM)
            {
                if (!accept) return false;
                pts = worldPoints; replaces++;
                return true;
            }
        }

        /// <summary>Start tile t0 with a control route from its centre 500 m east (the C case: the route goes on north,
        /// the trip turns off) and three links replacing that route: any (to the south), tykocin (to the north), monki.</summary>
        (WorldStreamer s, FakeReplaceableRoute path) StartInT0(string destination, bool accept = true)
        {
            var g = Row3();
            var t0 = g.Tiles[0];
            var root = Make("Region_t0").AddComponent<WorldRegionRoot>();
            root.regionId = t0.id; root.anchorX = t0.anchorX; root.anchorY = t0.anchorY; root.anchorZ = t0.anchorZ;
            var b = root.gameObject.AddComponent<WorldBoundary>();
            b.minEN = new Vector2(-924f, -924f); b.maxEN = new Vector2(924f, 924f);
            var route = Make("Route_t0").AddComponent<WorldRoute>();
            route.points = new[] { new Vector3(0f, 0f, 0f), new Vector3(250f, 0f, 0f), new Vector3(500f, 0f, 0f) };
            route.speedLimitsKmh = new[] { 50f, 50f, 50f };
            var vehicle = Make("Vehicle").transform;
            var s = Make("Streamer").AddComponent<WorldStreamer>();
            s.vehicle = vehicle; s.decideIntervalS = 0f;
            s.source = new BuildTileSource(_ => false);
            s.Init(g, 0, root);
            Vector3 first = route.transform.TransformPoint(route.points[0]);
            double x0 = s.AnchorX + first.x, y0 = s.AnchorY + first.z;
            var data = new RouteLinksData
            {
                links = new[]
                {
                    Link("t0-any", "t0", "any", "t0", t0, x0, y0, x0 + 600.0, y0 - 300.0),
                    Link("t0-tyk", "t0", "tykocin", "t0", t0, x0, y0, x0 + 600.0, y0 + 300.0),
                    Link("t0-monki", "t0", "monki", "t0", t0, x0, y0, x0 + 600.0, y0 + 600.0),
                },
            };
            s.SetRouteLinks(new RouteLinks(data, g));
            s.routeDestination = destination;
            var path = new FakeReplaceableRoute { pts = route.WorldPoints(), accept = accept };
            s.routePath = path;
            vehicle.position = first;
            return (s, path);
        }

        [Test]
        public void StartTile_RouteReplaced_ByTheLinkOfTheChosenDestination_OverAny()
        {
            var (s, path) = StartInT0("tykocin");
            CallUpdate(s);
            Assert.AreEqual(1, path.replaces, "the start route is the autopilot path: replaced, not appended to");
            Assert.AreEqual(0, path.appends);
            Assert.AreEqual(300f, path.pts[path.pts.Length - 1].z - path.pts[0].z, 0.01f, "tykocin link (any would end 300 m south)");
            CallUpdate(s);
            Assert.AreEqual(1, path.replaces, "once");
            Assert.AreEqual(0, path.appends, "no other link joins the new end");
        }

        [Test]
        public void StartTile_RouteReplaced_ByTheAnyLink_WhenTheDestinationHasNone()
        {
            var (s, path) = StartInT0("maczka");
            CallUpdate(s);
            Assert.AreEqual(1, path.replaces);
            Assert.AreEqual(-300f, path.pts[path.pts.Length - 1].z - path.pts[0].z, 0.01f, "any link");
        }

        [Test]
        public void StartTile_RouteKept_WhenTheDriverRefuses()
        {
            var (s, path) = StartInT0("tykocin", accept: false);
            CallUpdate(s);
            CallUpdate(s);
            Assert.AreEqual(0, path.replaces);
            Assert.AreEqual(0, path.appends, "a replacing link never continues the end of the route it replaces");
        }

        [Test]
        public void ShippedLinks_C_EveryTripReplacesTheStartRoute_DestinationLinkFirst()
        {
            // build #3 P2: c-dk8-to-maczka is `replaces_route` (no U-turn over the DK8 median); dojlidy / wasilkow have their own
            var g = TileGraph.LoadDefault();
            var l = RouteLinks.LoadDefault(g);
            int c = g.IndexOf("bialystok-industrial-c");
            foreach (var dest in new[] { "tykocin", "s8", "maczka", "dojlidy", "wasilkow" })
                Assert.IsTrue(l.IsRouteReplaced(c, dest), dest);
            foreach (var x in l.Links)
                if (x.tile == "bialystok-industrial-c")
                {
                    Assert.AreEqual("bialystok-industrial-c", x.replacesRoute, x.id);
                    Assert.IsTrue(string.IsNullOrEmpty(x.afterRoute), x.id + ": nothing continues the C control route end");
                }
        }

        // ------------------------------------------------------------------ policy along the new seams at 90 km/h

        [Test]
        public void ShippedKnyszynCorner_DrivenAt90KmH_NeverEntersATileThatIsNotReady()
        {
            // knyszyn-s -> knyszyn -> knyszyn-w -> dw671-tykocin-01: four tiles meet at (760587, 611583); the DW671 link cuts
            // the south-east corner of knyszyn-w 380-460 m from that point (worst case of maxTiles = 4, one load at a time).
            var g = TileGraph.LoadDefault();
            var l = RouteLinks.LoadDefault(g);
            var pts = new List<double[]>();
            int ks = g.IndexOf("knyszyn-s");
            pts.Add(new[] { g.Tiles[ks].anchorX, g.Tiles[ks].anchorY });
            foreach (string id in new[] { "knyszyn-dk65-to-dw671-w", "knyszyn-w-dw671" })
                for (int i = 0; i < l.Count; i++)
                    if (l.Links[i].id == id)
                    {
                        var t = g.Tiles[l.TileOf[i]];
                        for (int k = 0; k < l.Links[i].e.Length; k += 5) pts.Add(new[] { t.anchorX + l.Links[i].e[k], t.anchorY + l.Links[i].n[k] });
                    }
            int ty = g.IndexOf("dw671-tykocin-01");
            pts.Add(new[] { g.Tiles[ty].anchorX, g.Tiles[ty].anchorY });
            Assert.Greater(pts.Count, 100);

            foreach (string tier in new[] { "Low", "Medium" })
            {
                foreach (bool desktop in new[] { false, true })
                {
                    var p = new StreamingPolicy(g, new StreamingSettings { memoryBudgetMB = StreamingSettings.BudgetForTier(tier, desktop) });
                    p.InitResident(ks);
                    float readyAfter = p.Settings.loadTimeS + p.Settings.activationTimeS + p.Settings.cookTimeS;
                    var done = new float[g.Count];
                    var cmd = new StreamCommand[8];
                    float t = 0f, v = 25f, dt = 0.25f;
                    int loads = 0, maxRes = 0;
                    for (int i = 1; i < pts.Count; i++)
                    {
                        double ex = pts[i][0] - pts[i - 1][0], ey = pts[i][1] - pts[i - 1][1], len = Math.Sqrt(ex * ex + ey * ey);
                        if (len < 1e-6) continue;
                        float vx = (float)(ex / len * v), vy = (float)(ey / len * v);
                        for (double s = 0; s < len; s += v * dt, t += dt)
                        {
                            double x = pts[i - 1][0] + ex / len * s, y = pts[i - 1][1] + ey / len * s;
                            for (int j = 0; j < g.Count; j++)
                            {
                                var st = p.StateOf(j);
                                if (st == TileState.Loading && t >= done[j]) p.SetState(j, TileState.Ready);
                                if (st == TileState.Unloading && t >= done[j]) p.SetState(j, TileState.Unloaded);
                            }
                            int n = p.Decide(x, y, vx, vy, cmd);
                            for (int k = 0; k < n; k++)
                            {
                                if (cmd[k].op == StreamOp.Load) { loads++; done[cmd[k].tile] = t + readyAfter; }
                                else done[cmd[k].tile] = t + 1f;
                            }
                            maxRes = Math.Max(maxRes, p.ResidentCount());
                            for (int j = 0; j < g.Count; j++)
                                if (g.Contains(j, x, y, -0.5))
                                    Assert.AreEqual(TileState.Ready, p.StateOf(j), $"[{tier} desktop={desktop}] t={t:F1}s at ({x:F0},{y:F0}) in {g.Tiles[j].id} before ready");
                        }
                    }
                    Assert.LessOrEqual(maxRes, p.Settings.maxTiles);
                    TestContext.WriteLine($"[{tier} desktop={desktop}] loads {loads}, max resident {maxRes}, drive {t:F0} s");
                }
            }
        }
    }
}
