using System.Collections.Generic;
using System.IO;
using System.Text;
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

        // Known places (region metres): Kombatantów (two-way, south), Andersa = dual carriageway (two one-way edges).
        static readonly Vector2 k_Kombatantow = new Vector2(-1.7f, -897.8f);
        static readonly Vector2 k_AndersaSE = new Vector2(-172f, -298f);       // south-east-bound carriageway (edge 307)
        static readonly Vector2 k_AndersaNW = new Vector2(-457.95f, -55.97f);  // north-west-bound carriageway at Rondo Putry (edge 49)

        [Test]
        public void Region_KnownRoute_KombatantowToAndersa_SouthEastCarriageway()
        {
            var g = Region_();
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(k_Kombatantow, float.NaN, k_AndersaSE, p));
            Dump(g, p, "route_kombatantow_andersa_se");
            AssertValid(g, p);
            Log(g, p, planner, "Kombatantów -> Andersa SE");
            Assert.Greater(p.Length, Vector2.Distance(k_Kombatantow, k_AndersaSE));
            Assert.Less(p.Length, 2000f, "via al. Tysiąclecia and Rondo Putry, no loop");
            Assert.Less(Vector2.Distance(p.Points[p.Count - 1], p.Destination), 0.5f);
            Assert.AreEqual("Generała Władysława Andersa", g.Names[p.DestinationName]);
            bool tysiaclecia = false;
            for (int k = 0; k < p.ManCount; k++) tysiaclecia |= g.Names[p.ManName[k]] == "Aleja Tysiąclecia Państwa Polskiego";
            Assert.IsTrue(tysiaclecia, "turns onto al. Tysiąclecia");

            var q = RoutePath.For(g);
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(k_AndersaSE, float.NaN, k_Kombatantow, q));
            AssertValid(g, q);
        }

        [Test]
        public void Region_KnownRoute_OtherCarriageway_TurnsAtRoundabout()
        {
            // The goal lies on the opposite (north-west-bound) carriageway: no U-turn across the median, so the route
            // must turn round at a roundabout (Rondo Pamięci Bieżeństwa) and come back.
            var g = Region_();
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(k_Kombatantow, float.NaN, k_AndersaNW, p));
            Dump(g, p, "route_kombatantow_andersa_nw");
            AssertValid(g, p);
            Log(g, p, planner, "Kombatantów -> Andersa NW");
            bool turnRound = false;
            for (int k = 0; k < p.ManCount; k++) turnRound |= p.ManType[k] == Maneuver.Roundabout && Mathf.Abs(p.ManTurn[k]) > 150f;
            Assert.IsTrue(turnRound, "turns round at a roundabout");
        }

        static void Log(RouteGraph g, RoutePath p, RoutePlanner planner, string what)
        {
            Debug.Log($"[NAV] {what}: {p.Length:F0} m, {p.CostSeconds:F0} s, {p.DirectedCount} edges, {p.ManCount} manoeuvres, expanded {planner.LastExpanded}");
            for (int k = 0; k < p.ManCount; k++)
                Debug.Log($"[NAV]   {p.ManType[k]} {p.ManTurn[k]:F0}° exit {p.ManExit[k]} at {p.S[p.ManPoint[k]]:F0} m -> {g.Names[p.ManName[k]]}");
        }

        [Test]
        public void Region_ManyPairs_RespectOnewayAndRestrictions()
        {
            var g = Region_();
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            // Strongly connected truck core around a node on Andersa: forward and backward reachable (one-way aware node graph
            // without no-truck edges).
            // The 2 km clip leaves parts connected only outside the region (e.g. Olsztyńska / Buska, 55 nodes): not routable.
            int seed = g.EdgeFrom[307];
            bool[] fwd = Reach(g, seed, true), bwd = Reach(g, seed, false);
            var rnd = new System.Random(150);
            int ok = 0, tried = 0, core = 0, coreOk = 0;
            var byStatus = new int[8];
            for (int i = 0; i < 300; i++)
            {
                int ea = rnd.Next(g.EdgeCount), eb = rnd.Next(g.EdgeCount);
                if ((g.EdgeFlags[ea] & (RouteGraph.FlagNoTruck | RouteGraph.FlagRestricted)) != 0) continue;
                // Core test on the edges the points actually snap to (short spurs overlap other edges).
                int sa = g.Snap(Mid(g, ea), RoutePlanner.SnapStartM, out _, out _, out _);
                int sb = g.Snap(Mid(g, eb), RoutePlanner.SnapGoalM, out _, out _, out _);
                bool inCore = sa >= 0 && sb >= 0 && InCore(g, sa, fwd, bwd) && InCore(g, sb, fwd, bwd)
                              && (g.EdgeFlags[sa] & RouteGraph.FlagNoTruck) == 0;
                tried++;
                var st = planner.Plan(Mid(g, ea), float.NaN, Mid(g, eb), p);
                byStatus[(int)st]++;
                if (st == PlanStatus.Ok) { ok++; AssertValid(g, p); }
                if (!inCore) continue;
                core++;
                // Node reachability ignores the no-U-turn rule and the OSM turn restrictions, so a few core pairs are
                // legitimately unreachable (checked by hand in a line-graph model: e.g. 412 -> 141 needs a U-turn).
                if (st == PlanStatus.Ok || st == PlanStatus.AlreadyThere) coreOk++;
                else Debug.Log($"[NAV] core pair not planned: {ea} (snapped {sa}) -> {eb} (snapped {sb}): {st}");
            }
            Debug.Log($"[NAV] random pairs: {ok}/{tried} planned, {coreOk}/{core} core pairs planned; by status ok/startOff/goalOff/noPath/already = {byStatus[0]}/{byStatus[1]}/{byStatus[2]}/{byStatus[3]}/{byStatus[4]}");
            Assert.Greater(core, 100);
            Assert.GreaterOrEqual(coreOk, core * 0.95f, "nearly every pair of the truck core is routable");
        }

        static bool InCore(RouteGraph g, int e, bool[] fwd, bool[] bwd) =>
            fwd[g.EdgeFrom[e]] && bwd[g.EdgeFrom[e]] && fwd[g.EdgeTo[e]] && bwd[g.EdgeTo[e]];

        static bool[] Reach(RouteGraph g, int start, bool forward)
        {
            var seen = new bool[g.NodeCount];
            var stack = new Stack<int>();
            stack.Push(start); seen[start] = true;
            while (stack.Count > 0)
            {
                int n = stack.Pop();
                for (int e = 0; e < g.EdgeCount; e++)
                {
                    if ((g.EdgeFlags[e] & RouteGraph.FlagNoTruck) != 0) continue;   // trucks may not use it (access / hgv = no)
                    bool ow = g.IsOneway(e);
                    int a = g.EdgeFrom[e], b = g.EdgeTo[e];
                    if (forward)
                    {
                        if (a == n && !seen[b]) { seen[b] = true; stack.Push(b); }
                        if (!ow && b == n && !seen[a]) { seen[a] = true; stack.Push(a); }
                    }
                    else
                    {
                        if (b == n && !seen[a]) { seen[a] = true; stack.Push(a); }
                        if (!ow && a == n && !seen[b]) { seen[b] = true; stack.Push(b); }
                    }
                }
            }
            return seen;
        }

        /// <summary>Route polyline + manoeuvres as JSON in artifacts/gps-map/ (plotted by tools/worldgen/navgraph/plot_route.py).</summary>
        static void Dump(RouteGraph g, RoutePath p, string name)
        {
            var sb = new System.Text.StringBuilder();
            var ci = System.Globalization.CultureInfo.InvariantCulture;
            sb.Append("{\"points\":[");
            for (int i = 0; i < p.Count; i++) sb.Append(i > 0 ? "," : "").Append('[').Append(p.Points[i].x.ToString("F2", ci)).Append(',').Append(p.Points[i].y.ToString("F2", ci)).Append(']');
            sb.Append("],\"maneuvers\":[");
            for (int k = 0; k < p.ManCount; k++)
                sb.Append(k > 0 ? "," : "").Append("{\"type\":\"").Append(p.ManType[k]).Append("\",\"turn\":").Append(p.ManTurn[k].ToString("F0", ci))
                  .Append(",\"exit\":").Append(p.ManExit[k]).Append(",\"s\":").Append(p.S[p.ManPoint[k]].ToString("F1", ci))
                  .Append(",\"name\":\"").Append(g.Names[p.ManName[k]]).Append("\"}");
            sb.Append("],\"length\":").Append(p.Length.ToString("F1", ci)).Append(",\"cost_s\":").Append(p.CostSeconds.ToString("F1", ci)).Append('}');
            string dir = System.IO.Path.GetFullPath(System.IO.Path.Combine(Application.dataPath, "..", "..", "artifacts", "gps-map"));
            System.IO.Directory.CreateDirectory(dir);
            System.IO.File.WriteAllText(System.IO.Path.Combine(dir, name + ".json"), sb.ToString());
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
            g.EdgeMaxWeightC = new ushort[n]; g.EdgeMaxAxleLoadC = new ushort[n]; g.EdgeMaxHeightCm = new ushort[n]; g.EdgeMaxLengthCm = new ushort[n];
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
            Vector2 a = k_Kombatantow, b = k_AndersaSE;
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

            Vector2 off = at + new Vector2(dir.y, -dir.x) * 40f;   // 40 m beside the route
            for (int i = 0; i < 20; i++) tr.Update(p, off, heading, 10f, 0.1f, ref gd);
            Assert.IsFalse(gd.NeedsReroute, "hold time not over yet (2 s < 2.5 s)");
            for (int i = 0; i < 10; i++) tr.Update(p, off, heading, 10f, 0.1f, ref gd);
            Assert.IsTrue(gd.NeedsReroute);

            int v = p.Version;
            var st = planner.Plan(off, heading, p.Destination, p);
            Assert.That(st == PlanStatus.Ok || st == PlanStatus.StartOffRoad);
            if (st != PlanStatus.Ok) Assert.IsTrue(p.HasRoute && p.Version == v, "a failed re-plan keeps the current route");
            if (st == PlanStatus.Ok)
            {
                Assert.AreNotEqual(v, p.Version);
                Assert.Less(Vector2.Distance(p.Points[0], off), RoutePlanner.SnapStartM + 1f);
                tr.Update(p, p.Points[0], heading, 10f, 0.1f, ref gd);
                Assert.IsFalse(gd.NeedsReroute, "new route: timer re-armed");
            }

            // Arrival.
            Assert.IsTrue(p.HasRoute);
            tr.Update(p, p.Points[p.Count - 1], heading, 1f, 0.1f, ref gd);
            Assert.IsTrue(gd.Arrived);
        }

        // ------------------------------------------------------------------ lanes (KRTG v2, OSM turn:lanes)

        /// <summary>Serializes a graph to KRTG bytes (v1/v2) the way the Python generator does - for parser tests.</summary>
        static byte[] SerializeKrtg(RouteGraph g, int version, byte[][] fwdLanes, byte[][] bwdLanes)
        {
            var ms = new MemoryStream();
            var w = new BinaryWriter(ms, Encoding.UTF8);
            w.Write((byte)'K'); w.Write((byte)'R'); w.Write((byte)'T'); w.Write((byte)'G');
            w.Write((ushort)version);
            w.Write((ushort)g.Names.Length);
            foreach (var n in g.Names) { var b = Encoding.UTF8.GetBytes(n); w.Write((ushort)b.Length); w.Write(b); }
            w.Write((uint)g.NodeCount);
            for (int i = 0; i < g.NodeCount; i++) { w.Write(g.NodePos[i].x); w.Write(g.NodePos[i].y); w.Write(g.NodeFlags[i]); }
            w.Write((uint)g.EdgeCount);
            for (int e = 0; e < g.EdgeCount; e++)
            {
                w.Write((uint)g.EdgeFrom[e]); w.Write((uint)g.EdgeTo[e]); w.Write(g.EdgeLength[e]); w.Write(g.EdgeClass[e]);
                w.Write(g.EdgeFlags[e]); w.Write(g.EdgeName[e]); w.Write(g.EdgeMaxSpeed[e]); w.Write((byte)(g.EdgeMaxSpeedOsm[e] ? 1 : 0));
                w.Write((ushort)(g.EdgeStart[e + 1] - g.EdgeStart[e]));
                for (int k = g.EdgeStart[e]; k < g.EdgeStart[e + 1]; k++) { w.Write(g.Points[k].x); w.Write(g.Points[k].y); }
            }
            w.Write((ushort)g.RestrFrom.Length);
            for (int i = 0; i < g.RestrFrom.Length; i++)
            { w.Write((uint)g.RestrFrom[i]); w.Write((uint)g.RestrVia[i]); w.Write((uint)g.RestrTo[i]); w.Write(g.RestrKind[i]); }
            if (version >= 2)
            {
                int blocks = 0;
                for (int e = 0; e < g.EdgeCount; e++) if ((fwdLanes?[e]?.Length ?? 0) + (bwdLanes?[e]?.Length ?? 0) > 0) blocks++;
                w.Write((uint)blocks);
                for (int e = 0; e < g.EdgeCount; e++)
                {
                    var f = fwdLanes?[e]; var b = bwdLanes?[e];
                    if ((f?.Length ?? 0) + (b?.Length ?? 0) == 0) continue;
                    w.Write((uint)e); w.Write((byte)(f?.Length ?? 0)); w.Write((byte)(b?.Length ?? 0));
                    if (f != null) foreach (var m in f) w.Write(m);
                    if (b != null) foreach (var m in b) w.Write(m);
                }
            }
            w.Flush();
            return ms.ToArray();
        }

        [Test]
        public void Parse_KrtgV2LaneBlocks_V1Empty_V3Rejected()
        {
            var g = Square(0);
            var fwd = new byte[g.EdgeCount][]; var bwd = new byte[g.EdgeCount][];
            fwd[0] = new byte[] { RouteGraph.LaneLeft | RouteGraph.LaneThrough, RouteGraph.LaneThrough, RouteGraph.LaneRight };
            bwd[0] = new byte[] { RouteGraph.LaneThrough };
            var g2 = RouteGraph.Parse(SerializeKrtg(g, 2, fwd, bwd));
            Assert.AreEqual(3, g2.LaneCount(0, false));
            Assert.AreEqual(1, g2.LaneCount(0, true));
            Assert.AreEqual(RouteGraph.LaneLeft | RouteGraph.LaneThrough, g2.LaneMask(0, false, 0));
            Assert.AreEqual(RouteGraph.LaneRight, g2.LaneMask(0, false, 2));
            Assert.AreEqual(RouteGraph.LaneThrough, g2.LaneMask(0, true, 0));
            Assert.AreEqual(0, g2.LaneCount(1, false), "edges without a lane block have no lanes");
            Assert.AreEqual(550, Region_().NodeCount, "the committed v1 file still loads");
            var g1 = RouteGraph.Parse(SerializeKrtg(g, 1, fwd, bwd));
            Assert.AreEqual(0, g1.LaneCount(0, false), "v1 file: no lane section");
            Assert.Throws<System.FormatException>(() => RouteGraph.Parse(SerializeKrtg(g, 3, fwd, bwd)));
        }

        [Test]
        public void LaneGuidance_ClassBit()
        {
            Assert.AreEqual(RouteGraph.LaneThrough, LaneGuidance.ClassBit(0f));
            Assert.AreEqual(RouteGraph.LaneThrough, LaneGuidance.ClassBit(-24f));
            Assert.AreEqual(RouteGraph.LaneSlightRight, LaneGuidance.ClassBit(30f));
            Assert.AreEqual(RouteGraph.LaneSlightLeft, LaneGuidance.ClassBit(-45f));
            Assert.AreEqual(RouteGraph.LaneRight, LaneGuidance.ClassBit(90f));
            Assert.AreEqual(RouteGraph.LaneLeft, LaneGuidance.ClassBit(-135f));
            Assert.AreEqual(RouteGraph.LaneRight, LaneGuidance.ClassBit(140f), "sharp right maps to right (OSM has no sharp)");
            Assert.AreEqual(RouteGraph.LaneReverse, LaneGuidance.ClassBit(178f));
        }

        [Test]
        public void Synthetic_LaneGuidanceForNextManeuver()
        {
            var g = Square(0);
            var fwd = new byte[g.EdgeCount][];
            fwd[0] = new byte[] { RouteGraph.LaneLeft | RouteGraph.LaneThrough, RouteGraph.LaneThrough, RouteGraph.LaneRight };
            g.BuildLaneIndex(fwd, null);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            // Left turn at node 1 onto Prawa: only the "left;through" lane leads left.
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), 90f, new Vector2(200, 150), p));
            Assert.AreEqual(2, p.ManCount);
            Assert.AreEqual(Maneuver.Left, p.ManType[0]);
            Assert.AreEqual(3, p.ManLaneCount[0]);
            Assert.AreEqual(RouteGraph.LaneLeft, p.ManLaneCls[0]);
            Assert.AreEqual(0b001u, p.ManLanesAllowed[0]);
            Assert.AreEqual(0b001u, p.ManLanesRec[0], "left;through is dedicated enough (through is compatible)");
            Assert.AreEqual(0, p.ManIn[0], "incoming directed edge = edge 0 forward");
            // The tracker exposes it in the guidance state.
            var tr = new RouteTracker();
            var gd = new NavGuidance();
            tr.Update(p, new Vector2(50, 0), 90f, 0f, 0.02f, ref gd);
            Assert.AreEqual(0, gd.Next);
            Assert.AreEqual(3, gd.NextLaneCount);
            Assert.AreEqual(0b001u, gd.NextLanesAllowed);
            Assert.AreEqual(0b001u, gd.NextLanesRec);
            Assert.AreEqual(0, gd.NextLaneSrc);
            // Straight through the same junction: both through lanes allowed, only the pure through lane recommended.
            p.SetLaneGuidance(g, 0, p.ManIn[0], 0f);
            Assert.AreEqual(RouteGraph.LaneThrough, p.ManLaneCls[0]);
            Assert.AreEqual(0b011u, p.ManLanesAllowed[0]);
            Assert.AreEqual(0b010u, p.ManLanesRec[0]);
        }

        [Test]
        public void ZeroGc_LaneGuidanceInDrivingLoop()
        {
            var g = Square(0);
            var fwd = new byte[g.EdgeCount][];
            fwd[0] = new byte[] { RouteGraph.LaneLeft | RouteGraph.LaneThrough, RouteGraph.LaneThrough, RouteGraph.LaneRight };
            g.BuildLaneIndex(fwd, null);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), 90f, new Vector2(200, 150), p));
            var tr = new RouteTracker();
            var gd = new NavGuidance();
            tr.Update(p, new Vector2(50, 0), 90f, 5f, 0.02f, ref gd);   // warm-up (JIT)
            Assert.AreEqual(0b001u, gd.NextLanesAllowed);
            long before = System.GC.GetAllocatedBytesForCurrentThread();
            for (int i = 0; i < 10; i++) planner.Plan(new Vector2(50, 0), 90f, new Vector2(200, 150), p);
            for (int i = 0; i < 2000; i++) tr.Update(p, p.Points[i % p.Count], 90f, 10f, 0.02f, ref gd);
            long bytes = System.GC.GetAllocatedBytesForCurrentThread() - before;
            Assert.AreEqual(0, bytes, "planning with lane guidance + tracking allocate nothing");
        }

        [Test]
        public void ZeroGc_PlanAndTrack()
        {
            var g = Region_();
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            var tr = new RouteTracker();
            var gd = new NavGuidance();
            Vector2 a = k_Kombatantow, b = k_AndersaSE;
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(a, 0f, b, p), "heading north");   // warm-up (JIT)
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
