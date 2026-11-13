// Port of game/Assets/_Project/Tests/EditMode/NavRoutingTests.cs (NUnit -> xUnit) so the same cases run without Unity
// (M35, tools/nav-runner). The EditMode originals stay. Region graph is loaded from the real
// game/Assets/_Project/UI/Resources/CabDisplay/Nav/<region>_route.bytes via the Resources shim.
using System.Collections.Generic;
using System.IO;
using System.Text;
using Game.Core.Navigation;
using UnityEngine;
using Xunit;

namespace NavRunner.Tests
{
    public class NavRoutingTests
    {
        const string Region = "bialystok-industrial-c";

        static RouteGraph Region_() { var g = RouteGraph.Load(Region); Assert.NotNull(g); return g; }

        static void AssertValid(RouteGraph g, RoutePath p)
        {
            for (int i = 0; i < p.DirectedCount; i++)
            {
                int d = p.Directed[i], e = d >> 1;
                if (RouteGraph.Reversed(d)) Assert.False(g.IsOneway(e), "one-way edge " + e + " driven backwards");
                if (i == 0) continue;
                int prev = p.Directed[i - 1];
                Assert.Equal(g.EndNode(prev), g.StartNode(d));
                Assert.True(g.TurnAllowed(prev >> 1, g.StartNode(d), e), "turn restriction respected");
            }
            for (int i = 1; i < p.Count; i++) Assert.True(Vector2.Distance(p.Points[i - 1], p.Points[i]) < 400f, "no jumps in the polyline");
            Assert.Equal(Maneuver.Arrive, p.ManType[p.ManCount - 1]);
        }

        [Fact]
        public void Region_GraphLoads()
        {
            var g = Region_();
            Assert.Equal(550, g.NodeCount);
            Assert.Equal(646, g.EdgeCount);
            Assert.Equal(7, g.RestrFrom.Length);
            int oneway = 0;
            for (int e = 0; e < g.EdgeCount; e++) if (g.IsOneway(e)) oneway++;
            Assert.Equal(277, oneway);
            Assert.Contains("Generała Władysława Andersa", g.Names);
        }

        static readonly Vector2 k_Kombatantow = new Vector2(-1.7f, -897.8f);
        static readonly Vector2 k_AndersaSE = new Vector2(-172f, -298f);
        static readonly Vector2 k_AndersaNW = new Vector2(-320f, -162f);

        [Fact]
        public void Region_KnownRoute_KombatantowToAndersa_SouthEastCarriageway()
        {
            var g = Region_();
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(k_Kombatantow, float.NaN, k_AndersaSE, p));
            AssertValid(g, p);
            Assert.True(p.Length > Vector2.Distance(k_Kombatantow, k_AndersaSE));
            Assert.True(p.Length < 2000f, "via al. Tysiaclecia and Rondo Putry, no loop");
            Assert.True(Vector2.Distance(p.Points[p.Count - 1], p.Destination) < 0.5f);
            Assert.Equal("Generała Władysława Andersa", g.Names[p.DestinationName]);
            bool tysiaclecia = false;
            for (int k = 0; k < p.ManCount; k++) tysiaclecia |= g.Names[p.ManName[k]] == "Aleja Tysiąclecia Państwa Polskiego";
            Assert.True(tysiaclecia, "turns onto al. Tysiaclecia");

            var q = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(k_AndersaSE, float.NaN, k_Kombatantow, q));
            AssertValid(g, q);
        }

        [Fact]
        public void Region_KnownRoute_OtherCarriageway_TurnsAtRoundabout()
        {
            var g = Region_();
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(k_Kombatantow, float.NaN, k_AndersaNW, p));
            AssertValid(g, p);
            bool turnRound = false;
            for (int k = 0; k < p.ManCount; k++) turnRound |= p.ManType[k] == Maneuver.Roundabout && Mathf.Abs(p.ManTurn[k]) > 150f;
            Assert.True(turnRound, "turns round at a roundabout");
        }

        [Fact]
        public void Region_ManyPairs_RespectOnewayAndRestrictions()
        {
            var g = Region_();
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            int seed = g.EdgeFrom[307];
            bool[] fwd = Reach(g, seed, true), bwd = Reach(g, seed, false);
            var rnd = new System.Random(150);
            int ok = 0, tried = 0, core = 0, coreOk = 0;
            var byStatus = new int[8];
            for (int i = 0; i < 300; i++)
            {
                int ea = rnd.Next(g.EdgeCount), eb = rnd.Next(g.EdgeCount);
                if ((g.EdgeFlags[ea] & (RouteGraph.FlagNoTruck | RouteGraph.FlagRestricted)) != 0) continue;
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
                if (st == PlanStatus.Ok || st == PlanStatus.AlreadyThere) coreOk++;
            }
            Assert.True(core > 100);
            Assert.True(coreOk >= core * 0.95f, $"nearly every pair of the truck core is routable ({coreOk}/{core})");
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
                    if ((g.EdgeFlags[e] & RouteGraph.FlagNoTruck) != 0) continue;
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

        static Vector2 Mid(RouteGraph g, int e) => g.PointAlong(e * 2, g.GeomLength(e) * 0.5f);

        [Fact]
        public void Region_HeadingSelectsDirection()
        {
            var g = Region_();
            int e = -1;
            for (int i = 0; i < g.EdgeCount; i++)
                if (!g.IsOneway(i) && g.EdgeClass[i] >= 1 && g.GeomLength(i) > 100f && (g.EdgeFlags[i] & RouteGraph.FlagNoTruck) == 0) { e = i; break; }
            Assert.True(e >= 0);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Vector2 at = Mid(g, e), dir = g.DirectionAt(e * 2, g.GeomLength(e) * 0.5f, 5f);
            float heading = Mathf.Atan2(dir.x, dir.y) * Mathf.Rad2Deg;
            Vector2 behind = g.PointAlong(e * 2, 5f);
            Assert.Equal(PlanStatus.Ok, planner.Plan(at, heading, behind, p));
            AssertValid(g, p);
            Assert.Equal(e * 2, p.Directed[0]);
        }

        // ------------------------------------------------------------------ synthetic graphs

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

        [Fact]
        public void Synthetic_OnewayForcesDetour()
        {
            var g = Square(RouteGraph.FlagOneway);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(200, 100), 180f, new Vector2(20, 0), p));
            AssertValid(g, p);
            Assert.True(p.Length > 400f, "goes round via Górna and Lewa, not back along the one-way Dolna");
            var two = Square(0);
            var planner2 = new RoutePlanner(two);
            Assert.Equal(PlanStatus.Ok, planner2.Plan(new Vector2(200, 100), 180f, new Vector2(20, 0), p));
            Assert.True(p.Length < 300f, "two-way: direct");
        }

        [Fact]
        public void Synthetic_TurnRestriction()
        {
            var g = Square(0);
            g.RestrFrom = new[] { 0 }; g.RestrVia = new[] { 1 }; g.RestrTo = new[] { 1 }; g.RestrKind = new byte[] { 0 };
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(100, 0), 90f, new Vector2(200, 150), p));
            AssertValid(g, p);
            Assert.True(p.Length > 350f, "goes round via node 0 instead of the forbidden right turn");
            g.RestrKind = new byte[] { 1 }; g.RestrTo = new[] { 4 };
            Assert.False(g.TurnAllowed(0, 1, 1));
            Assert.True(g.TurnAllowed(0, 1, 4));
        }

        [Fact]
        public void Synthetic_ManeuverLeftTurnAtJunction()
        {
            var g = Square(0);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), 90f, new Vector2(200, 150), p));
            Assert.Equal(2, p.ManCount);
            Assert.Equal(Maneuver.Left, p.ManType[0]);
            Assert.Equal("Prawa", g.Names[p.ManName[0]]);
            Assert.Equal(150f, p.S[p.ManPoint[0]], 0.5);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), 90f, new Vector2(350, 0), p));
            Assert.Equal(1, p.ManCount);
            Assert.Equal(Maneuver.Arrive, p.ManType[0]);
        }

        [Fact]
        public void Synthetic_RoundaboutExitNumber()
        {
            float r = 30f;
            var nodes = new[]
            {
                new Vector2(-r, 0), new Vector2(0, -r), new Vector2(r, 0), new Vector2(0, r),
                new Vector2(-200, 0), new Vector2(0, -200), new Vector2(200, 0), new Vector2(0, 200),
            };
            byte rb = RouteGraph.FlagRoundabout | RouteGraph.FlagOneway;
            var g = Build(nodes, new (int, int, byte, string)[]
            {
                (0, 1, rb, "Rondo"), (1, 2, rb, "Rondo"), (2, 3, rb, "Rondo"), (3, 0, rb, "Rondo"),
                (4, 0, 0, "Zachodnia"), (1, 5, 0, "Południowa"), (2, 6, 0, "Wschodnia"), (3, 7, 0, "Północna"),
            });
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(-150, 0), 90f, new Vector2(0, 150), p));
            AssertValid(g, p);
            Assert.Equal(Maneuver.Roundabout, p.ManType[0]);
            Assert.Equal(3, p.ManExit[0]);
            Assert.Equal("Północna", g.Names[p.ManName[0]]);
            Assert.True(p.ManTurn[0] < -45f, "north from an eastbound entry is a left turn overall");
        }

        [Fact]
        public void Tracker_OffRouteTriggersReplan()
        {
            var g = Region_();
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Vector2 a = k_Kombatantow, b = k_AndersaSE;
            Assert.Equal(PlanStatus.Ok, planner.Plan(a, float.NaN, b, p));
            var tr = new RouteTracker();
            var gd = new NavGuidance();
            Vector2 at = p.Points[p.Count / 3];
            Vector2 dir = (p.Points[p.Count / 3 + 1] - at).normalized;
            float heading = Mathf.Atan2(dir.x, dir.y) * Mathf.Rad2Deg;
            tr.Update(p, at, heading, 10f, 0.1f, ref gd);
            Assert.True(gd.OnRoute);
            Assert.True(gd.OffRouteM < 0.5f);
            Assert.True(gd.Next >= 0);
            Assert.True(gd.RemainingM > 0f);
            Assert.True(gd.RemainingM < p.Length);

            Vector2 off = at + new Vector2(dir.y, -dir.x) * 40f;
            for (int i = 0; i < 20; i++) tr.Update(p, off, heading, 10f, 0.1f, ref gd);
            Assert.False(gd.NeedsReroute, "hold time not over yet (2 s < 2.5 s)");
            for (int i = 0; i < 10; i++) tr.Update(p, off, heading, 10f, 0.1f, ref gd);
            Assert.True(gd.NeedsReroute);

            int v = p.Version;
            var st = planner.Plan(off, heading, p.Destination, p);
            Assert.True(st == PlanStatus.Ok || st == PlanStatus.StartOffRoad);
            if (st != PlanStatus.Ok) Assert.True(p.HasRoute && p.Version == v, "a failed re-plan keeps the current route");
            if (st == PlanStatus.Ok)
            {
                Assert.NotEqual(v, p.Version);
                Assert.True(Vector2.Distance(p.Points[0], off) < RoutePlanner.SnapStartM + 1f);
                tr.Update(p, p.Points[0], heading, 10f, 0.1f, ref gd);
                Assert.False(gd.NeedsReroute, "new route: timer re-armed");
            }

            Assert.True(p.HasRoute);
            tr.Update(p, p.Points[p.Count - 1], heading, 1f, 0.1f, ref gd);
            Assert.True(gd.Arrived);
        }

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
                if (version >= 2) { w.Write((ushort)0); w.Write((ushort)0); w.Write((ushort)0); w.Write((ushort)0); }
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

        [Fact]
        public void Parse_KrtgV2LaneBlocks_V1Empty_V3Rejected()
        {
            var g = Square(0);
            var fwd = new byte[g.EdgeCount][]; var bwd = new byte[g.EdgeCount][];
            fwd[0] = new byte[] { RouteGraph.LaneLeft | RouteGraph.LaneThrough, RouteGraph.LaneThrough, RouteGraph.LaneRight };
            bwd[0] = new byte[] { RouteGraph.LaneThrough };
            var g2 = RouteGraph.Parse(SerializeKrtg(g, 2, fwd, bwd));
            Assert.Equal(3, g2.LaneCount(0, false));
            Assert.Equal(1, g2.LaneCount(0, true));
            Assert.Equal(RouteGraph.LaneLeft | RouteGraph.LaneThrough, g2.LaneMask(0, false, 0));
            Assert.Equal(RouteGraph.LaneRight, g2.LaneMask(0, false, 2));
            Assert.Equal(RouteGraph.LaneThrough, g2.LaneMask(0, true, 0));
            Assert.Equal(0, g2.LaneCount(1, false));
            Assert.Equal(550, Region_().NodeCount);
            var g1 = RouteGraph.Parse(SerializeKrtg(g, 1, fwd, bwd));
            Assert.Equal(0, g1.LaneCount(0, false));
            Assert.Throws<System.FormatException>(() => RouteGraph.Parse(SerializeKrtg(g, 3, fwd, bwd)));
        }

        [Fact]
        public void LaneGuidance_ClassBit()
        {
            Assert.Equal(RouteGraph.LaneThrough, LaneGuidance.ClassBit(0f));
            Assert.Equal(RouteGraph.LaneThrough, LaneGuidance.ClassBit(-24f));
            Assert.Equal(RouteGraph.LaneSlightRight, LaneGuidance.ClassBit(30f));
            Assert.Equal(RouteGraph.LaneSlightLeft, LaneGuidance.ClassBit(-45f));
            Assert.Equal(RouteGraph.LaneRight, LaneGuidance.ClassBit(90f));
            Assert.Equal(RouteGraph.LaneLeft, LaneGuidance.ClassBit(-135f));
            Assert.Equal(RouteGraph.LaneRight, LaneGuidance.ClassBit(140f));
            Assert.Equal(RouteGraph.LaneReverse, LaneGuidance.ClassBit(178f));
        }

        [Fact]
        public void Synthetic_LaneGuidanceForNextManeuver()
        {
            var g = Square(0);
            var fwd = new byte[g.EdgeCount][];
            fwd[0] = new byte[] { RouteGraph.LaneLeft | RouteGraph.LaneThrough, RouteGraph.LaneThrough, RouteGraph.LaneRight };
            g.BuildLaneIndex(fwd, null);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), 90f, new Vector2(200, 150), p));
            Assert.Equal(2, p.ManCount);
            Assert.Equal(Maneuver.Left, p.ManType[0]);
            Assert.Equal(3, p.ManLaneCount[0]);
            Assert.Equal(RouteGraph.LaneLeft, p.ManLaneCls[0]);
            Assert.Equal(0b001u, p.ManLanesAllowed[0]);
            Assert.Equal(0b001u, p.ManLanesRec[0]);
            Assert.Equal(0, p.ManIn[0]);
            var tr = new RouteTracker();
            var gd = new NavGuidance();
            tr.Update(p, new Vector2(50, 0), 90f, 0f, 0.02f, ref gd);
            Assert.Equal(0, gd.Next);
            Assert.Equal(3, gd.NextLaneCount);
            Assert.Equal(0b001u, gd.NextLanesAllowed);
            Assert.Equal(0b001u, gd.NextLanesRec);
            Assert.Equal(0, gd.NextLaneSrc);
            p.SetLaneGuidance(g, 0, p.ManIn[0], 0f);
            Assert.Equal(RouteGraph.LaneThrough, p.ManLaneCls[0]);
            Assert.Equal(0b011u, p.ManLanesAllowed[0]);
            Assert.Equal(0b010u, p.ManLanesRec[0]);
        }

        [Fact]
        public void ZeroGc_LaneGuidanceInDrivingLoop()
        {
            var g = Square(0);
            var fwd = new byte[g.EdgeCount][];
            fwd[0] = new byte[] { RouteGraph.LaneLeft | RouteGraph.LaneThrough, RouteGraph.LaneThrough, RouteGraph.LaneRight };
            g.BuildLaneIndex(fwd, null);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), 90f, new Vector2(200, 150), p));
            var tr = new RouteTracker();
            var gd = new NavGuidance();
            tr.Update(p, new Vector2(50, 0), 90f, 5f, 0.02f, ref gd);
            Assert.Equal(0b001u, gd.NextLanesAllowed);
            GcAllocCounter.AssertZero(() =>
            {
                for (int i = 0; i < 10; i++) planner.Plan(new Vector2(50, 0), 90f, new Vector2(200, 150), p);
                for (int i = 0; i < 2000; i++) tr.Update(p, p.Points[i % p.Count], 90f, 10f, 0.02f, ref gd);
            }, message: "planning with lane guidance + tracking allocate nothing");
        }

        [Fact]
        public void ZeroGc_PlanAndTrack()
        {
            var g = Region_();
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            var tr = new RouteTracker();
            var gd = new NavGuidance();
            Vector2 a = k_Kombatantow, b = k_AndersaSE;
            Assert.Equal(PlanStatus.Ok, planner.Plan(a, 0f, b, p));
            for (int i = 0; i < 50; i++) tr.Update(p, p.Points[i % p.Count], 0f, 10f, 0.02f, ref gd);
            GcAllocCounter.AssertZero(() =>
            {
                for (int i = 0; i < 10; i++) planner.Plan(i % 2 == 0 ? a : b, float.NaN, i % 2 == 0 ? b : a, p);
                for (int i = 0; i < 2000; i++) tr.Update(p, p.Points[(i / 3) % p.Count] + new Vector2(1f, 0f), i * 0.5f, 10f, 0.02f, ref gd);
            }, message: "routing / re-planning and guidance allocate nothing");

            var sw = System.Diagnostics.Stopwatch.StartNew();
            for (int i = 0; i < 20; i++) planner.Plan(i % 2 == 0 ? a : b, float.NaN, i % 2 == 0 ? b : a, p);
            Debug.Log($"[NAV] plan Kombatantow <-> Andersa: {sw.Elapsed.TotalMilliseconds / 20.0:F3} ms per plan, expanded {planner.LastExpanded}");
        }
    }
}
