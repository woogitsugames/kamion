using System.Collections.Generic;
using Game.Core.Navigation;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>GPS routing (ADR 0150): region graph, A* with one-way streets and OSM turn restrictions, manoeuvres,
    /// off-route detection and re-planning, zero GC in the driving loop.</summary>
    public class NavRoutingTests
    {
        const string Region = "bialystok-industrial-c";

        static RouteGraph Region_() { var g = RouteGraph.Load(Region); Assert.NotNull(g, "Resources/CabDisplay/Nav/" + Region + "_route.bytes"); return g; }

        static void AssertValid(RouteGraph g, RoutePath p)
        {
            for (int i = 0; i < p.DirectedCount; i++)
            {
                int d = p.Directed[i], e = d >> 1;
                if (RouteGraph.Reversed(d)) Assert.IsFalse(g.IsOneway(e), "one-way edge " + e + " driven backwards");
                if (i == 0) continue;
                int prev = p.Directed[i - 1];
                Assert.AreEqual(g.EndNode(prev), g.StartNode(d), "route is connected");
                Assert.IsTrue(g.TurnAllowed(prev >> 1, g.StartNode(d), e), "turn restriction respected");
            }
            for (int i = 1; i < p.Count; i++) Assert.Less(Vector2.Distance(p.Points[i - 1], p.Points[i]), 400f, "no jumps in the polyline");
            Assert.AreEqual(Maneuver.Arrive, p.ManType[p.ManCount - 1]);
        }

        [Test]
        public void Region_GraphLoads()
        {
            var g = Region_();
            Assert.AreEqual(550, g.NodeCount);
            Assert.AreEqual(646, g.EdgeCount);
            Assert.AreEqual(7, g.RestrFrom.Length, "OSM turn restrictions (turn_restrictions.json)");
            int oneway = 0;
            for (int e = 0; e < g.EdgeCount; e++) if (g.IsOneway(e)) oneway++;
            Assert.AreEqual(277, oneway);
            Assert.Contains("Generała Władysława Andersa", g.Names);
        }

        [Test]
        public void Region_KnownRoute_KombatantowToAndersa()
        {
            var g = Region_();
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Vector2 a = new Vector2(-1.7f, -897.8f), b = new Vector2(-457.95f, -55.97f);
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(a, float.NaN, b, p));
            AssertValid(g, p);
            float straight = Vector2.Distance(a, b);
            Assert.Greater(p.Length, straight * 0.95f);
            Assert.Less(p.Length, straight * 2.5f, "no absurd detour");
            Assert.Less(Vector2.Distance(p.Points[p.Count - 1], p.Destination), 0.5f);
            Assert.AreEqual("Generała Władysława Andersa", g.Names[p.DestinationName]);
            Assert.GreaterOrEqual(p.ManCount, 2, "at least one junction manoeuvre + arrival");
            Debug.Log($"[NAV] Kombatantów -> Andersa: {p.Length:F0} m, {p.CostSeconds:F0} s, {p.DirectedCount} edges, {p.ManCount} manoeuvres, expanded {planner.LastExpanded}");
            for (int k = 0; k < p.ManCount; k++)
                Debug.Log($"[NAV]   {p.ManType[k]} {p.ManTurn[k]:F0}° exit {p.ManExit[k]} at {p.S[p.ManPoint[k]]:F0} m -> {g.Names[p.ManName[k]]}");

            // And back (one-way pairs differ: the way back is a different set of directed edges).
            var q = RoutePath.For(g);
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(b, float.NaN, a, q));
            AssertValid(g, q);
        }

        [Test]
        public void Region_ManyPairs_RespectOnewayAndRestrictions()
        {
            var g = Region_();
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            var rnd = new System.Random(150);
            int ok = 0, tried = 0;
            for (int i = 0; i < 150; i++)
            {
                int ea = rnd.Next(g.EdgeCount), eb = rnd.Next(g.EdgeCount);
                if ((g.EdgeFlags[ea] & (RouteGraph.FlagNoTruck | RouteGraph.FlagRestricted)) != 0) continue;
                tried++;
                var st = planner.Plan(Mid(g, ea), float.NaN, Mid(g, eb), p);
                if (st == PlanStatus.Ok) { ok++; AssertValid(g, p); }
            }
            Debug.Log($"[NAV] random pairs: {ok}/{tried} planned");
            Assert.GreaterOrEqual(ok, tried * 0.7f, "most of the region is reachable (dead-end boundary stubs are not)");
        }

        static Vector2 Mid(RouteGraph g, int e) => g.PointAlong(e * 2, g.GeomLength(e) * 0.5f);

        [Test]
        public void Region_HeadingSelectsDirection()
        {
            // On a two-way street the truck facing one way is not routed backwards (no U-turn with a 16.5 m combination).
            var g = Region_();
            int e = -1;
            for (int i = 0; i < g.EdgeCount; i++)
                if (!g.IsOneway(i) && g.EdgeClass[i] >= 1 && g.GeomLength(i) > 100f && (g.EdgeFlags[i] & RouteGraph.FlagNoTruck) == 0) { e = i; break; }
            Assert.GreaterOrEqual(e, 0);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Vector2 at = Mid(g, e), dir = g.DirectionAt(e * 2, g.GeomLength(e) * 0.5f, 5f);
            float heading = Mathf.Atan2(dir.x, dir.y) * Mathf.Rad2Deg;
            Vector2 behind = g.PointAlong(e * 2, 5f);   // goal behind the truck on the same street
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(at, heading, behind, p));
            AssertValid(g, p);
            Assert.AreEqual(e * 2, p.Directed[0], "starts in the heading direction");
        }

        // ------------------------------------------------------------------ synthetic graphs

        /// <summary>Graph from straight edges between nodes: (from, to, flags, name).</summary>
        static RouteGraph Build(Vector2[] nodes, (int a, int b, byte flags, string name)[] edges)
        {
            var g = new RouteGraph();
            var names = new List<string> { "" };
            g.NodePos = nodes; g.NodeFlags = new byte[nodes.Length];
            int n = edges.Length;
            g.EdgeFrom = new int[n]; g.EdgeTo = new int[n]; g.EdgeLength = new float[n]; g.EdgeClass = new byte[n]; g.EdgeFlags = new byte[n];
            g.EdgeName = new ushort[n]; g.EdgeMaxSpeed = new byte[n]; g.EdgeMaxSpeedOsm = new bool[n]; g.EdgeStart = new int[n + 1];
            var pts = new List<Vector2>();
            for (int i = 0; i < n; i++)
            {
                var (a, b, f, nm) = edges[i];
                g.EdgeFrom[i] = a; g.EdgeTo[i] = b; g.EdgeFlags[i] = f; g.EdgeClass[i] = 1;
                if (!names.Contains(nm)) names.Add(nm);
                g.EdgeName[i] = (ushort)names.IndexOf(nm);
                g.EdgeStart[i] = pts.Count;
                pts.Add(nodes[a]); pts.Add(nodes[b]);
                g.EdgeLength[i] = Vector2.Distance(nodes[a], nodes[b]);
            }
            g.EdgeStart[n] = pts.Count;
            g.Points = pts.ToArray();
            g.Names = names.ToArray();
            g.BuildAdjacency();
            return g;
        }

        //   3 ---- 2
        //   |      |
        //   0 ---- 1 ---- 4
        static RouteGraph Square(byte flags01)
        {
            var nodes = new[] { new Vector2(0, 0), new Vector2(200, 0), new Vector2(200, 200), new Vector2(0, 200), new Vector2(400, 0) };
            return Build(nodes, new (int, int, byte, string)[]
            {
                (0, 1, flags01, "Dolna"), (1, 2, 0, "Prawa"), (2, 3, 0, "Górna"), (3, 0, 0, "Lewa"), (1, 4, 0, "Dalsza"),
            });
        }

        [Test]
        public void Synthetic_OnewayForcesDetour()
        {
            var g = Square(RouteGraph.FlagOneway);   // Dolna only 0 -> 1
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            // From the middle of Prawa (heading south, towards 1) to node 0's side of Dolna: 1 -> 0 is forbidden.
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(new Vector2(200, 100), 180f, new Vector2(20, 0), p));
            AssertValid(g, p);
            Assert.Greater(p.Length, 400f, "goes round via Górna and Lewa, not back along the one-way Dolna");
            var two = Square(0);
            var planner2 = new RoutePlanner(two);
            Assert.AreEqual(PlanStatus.Ok, planner2.Plan(new Vector2(200, 100), 180f, new Vector2(20, 0), p));
            Assert.Less(p.Length, 300f, "two-way: direct");
        }

        [Test]
        public void Synthetic_TurnRestriction()
        {
            var g = Square(0);
            // No turn from Dolna (edge 0) at node 1 onto Prawa (edge 1).
            g.RestrFrom = new[] { 0 }; g.RestrVia = new[] { 1 }; g.RestrTo = new[] { 1 }; g.RestrKind = new byte[] { 0 };
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(new Vector2(100, 0), 90f, new Vector2(200, 150), p));
            AssertValid(g, p);
            Assert.Greater(p.Length, 350f, "goes round via node 0 instead of the forbidden right turn");
            // only_straight_on from Dolna at 1 -> onto Dalsza only.
            g.RestrKind = new byte[] { 1 }; g.RestrTo = new[] { 4 };
            Assert.IsFalse(g.TurnAllowed(0, 1, 1));
            Assert.IsTrue(g.TurnAllowed(0, 1, 4));
        }

        [Test]
        public void Synthetic_ManeuverLeftTurnAtJunction()
        {
            var g = Square(0);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            // Heading east on Dolna, turn left (north) onto Prawa at node 1 (Dalsza continues straight).
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), 90f, new Vector2(200, 150), p));
            Assert.AreEqual(2, p.ManCount);
            Assert.AreEqual(Maneuver.Left, p.ManType[0]);
            Assert.AreEqual("Prawa", g.Names[p.ManName[0]]);
            Assert.AreEqual(150f, p.S[p.ManPoint[0]], 0.5f);
            // Straight on through node 1 onto Dalsza: the obvious way, no manoeuvre.
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), 90f, new Vector2(350, 0), p));
            Assert.AreEqual(1, p.ManCount);
            Assert.AreEqual(Maneuver.Arrive, p.ManType[0]);
        }

        [Test]
        public void Synthetic_RoundaboutExitNumber()
        {
            // Roundabout of 4 nodes (counter-clockwise, as in Poland), arms west (entry), south, east, north.
            float r = 30f;
            var nodes = new[]
            {
                new Vector2(-r, 0), new Vector2(0, -r), new Vector2(r, 0), new Vector2(0, r),          // ring 0..3
                new Vector2(-200, 0), new Vector2(0, -200), new Vector2(200, 0), new Vector2(0, 200),  // arms 4..7
            };
            byte rb = RouteGraph.FlagRoundabout | RouteGraph.FlagOneway;
            var g = Build(nodes, new (int, int, byte, string)[]
            {
                (0, 1, rb, "Rondo"), (1, 2, rb, "Rondo"), (2, 3, rb, "Rondo"), (3, 0, rb, "Rondo"),
                (4, 0, 0, "Zachodnia"), (1, 5, 0, "Południowa"), (2, 6, 0, "Wschodnia"), (3, 7, 0, "Północna"),
            });
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(new Vector2(-150, 0), 90f, new Vector2(0, 150), p));
            AssertValid(g, p);
            Assert.AreEqual(Maneuver.Roundabout, p.ManType[0]);
            Assert.AreEqual(3, p.ManExit[0], "south = 1st, east = 2nd, north = 3rd exit");
            Assert.AreEqual("Północna", g.Names[p.ManName[0]]);
            Assert.Less(p.ManTurn[0], -45f, "north from an eastbound entry is a left turn overall");
        }

        // ------------------------------------------------------------------ tracking, re-planning, GC

        [Test]
        public void Tracker_OffRouteTriggersReplan()
        {
            var g = Region_();
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Vector2 a = new Vector2(-1.7f, -897.8f), b = new Vector2(-457.95f, -55.97f);
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(a, float.NaN, b, p));
            var tr = new RouteTracker();
            var gd = new NavGuidance();
            Vector2 at = p.Points[p.Count / 3];
            Vector2 dir = (p.Points[p.Count / 3 + 1] - at).normalized;
            float heading = Mathf.Atan2(dir.x, dir.y) * Mathf.Rad2Deg;
            tr.Update(p, at, heading, 10f, 0.1f, ref gd);
            Assert.IsTrue(gd.OnRoute);
            Assert.Less(gd.OffRouteM, 0.5f);
            Assert.GreaterOrEqual(gd.Next, 0);
            Assert.Greater(gd.RemainingM, 0f);
            Assert.Less(gd.RemainingM, p.Length);

            Vector2 off = at + new Vector2(dir.y, -dir.x) * 60f;   // 60 m beside the route
            for (int i = 0; i < 20; i++) tr.Update(p, off, heading, 10f, 0.1f, ref gd);
            Assert.IsFalse(gd.NeedsReroute, "hold time not over yet (2 s < 2.5 s)");
            for (int i = 0; i < 10; i++) tr.Update(p, off, heading, 10f, 0.1f, ref gd);
            Assert.IsTrue(gd.NeedsReroute);

            int v = p.Version;
            var st = planner.Plan(off, heading, p.Destination, p);
            Assert.That(st == PlanStatus.Ok || st == PlanStatus.StartOffRoad);
            if (st == PlanStatus.Ok)
            {
                Assert.AreNotEqual(v, p.Version);
                Assert.Less(Vector2.Distance(p.Points[0], off), RoutePlanner.SnapStartM + 1f);
                tr.Update(p, p.Points[0], heading, 10f, 0.1f, ref gd);
                Assert.IsFalse(gd.NeedsReroute, "new route: timer re-armed");
            }

            // Arrival.
            tr.Update(p, p.Points[p.Count - 1], heading, 1f, 0.1f, ref gd);
            Assert.IsTrue(gd.Arrived);
        }

        [Test]
        public void ZeroGc_PlanAndTrack()
        {
            var g = Region_();
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            var tr = new RouteTracker();
            var gd = new NavGuidance();
            Vector2 a = new Vector2(-1.7f, -897.8f), b = new Vector2(-457.95f, -55.97f);
            planner.Plan(a, 0f, b, p);   // warm-up (JIT)
            for (int i = 0; i < 50; i++) tr.Update(p, p.Points[i % p.Count], 0f, 10f, 0.02f, ref gd);
            long before = System.GC.GetAllocatedBytesForCurrentThread();
            for (int i = 0; i < 10; i++) planner.Plan(i % 2 == 0 ? a : b, float.NaN, i % 2 == 0 ? b : a, p);
            for (int i = 0; i < 2000; i++) tr.Update(p, p.Points[(i / 3) % p.Count] + new Vector2(1f, 0f), i * 0.5f, 10f, 0.02f, ref gd);
            long bytes = System.GC.GetAllocatedBytesForCurrentThread() - before;
            Assert.AreEqual(0, bytes, "routing / re-planning and guidance allocate nothing");

            var sw = System.Diagnostics.Stopwatch.StartNew();
            for (int i = 0; i < 20; i++) planner.Plan(i % 2 == 0 ? a : b, float.NaN, i % 2 == 0 ? b : a, p);
            Debug.Log($"[NAV] plan Kombatantów <-> Andersa: {sw.Elapsed.TotalMilliseconds / 20.0:F3} ms per plan (editor), expanded {planner.LastExpanded}");
        }
    }
}
