// Port of game/Assets/_Project/Tests/EditMode/NavTruckLimitsTests.cs (NUnit -> xUnit) for tools/nav-runner (M35).
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using Game.Core.Navigation;
using UnityEngine;
using Xunit;

namespace NavRunner.Tests
{
    public class NavTruckLimitsTests
    {
        const string Region = "bialystok-industrial-c";

        static RouteGraph Build(Vector2[] nodes, (int a, int b, byte flags, string name, ushort mw, ushort mal, ushort mh, ushort ml)[] edges)
        {
            var g = new RouteGraph { Version = 2 };
            var names = new List<string> { "" };
            g.NodePos = nodes; g.NodeFlags = new byte[nodes.Length];
            int n = edges.Length;
            g.EdgeFrom = new int[n]; g.EdgeTo = new int[n]; g.EdgeLength = new float[n]; g.EdgeClass = new byte[n]; g.EdgeFlags = new byte[n];
            g.EdgeName = new ushort[n]; g.EdgeMaxSpeed = new byte[n]; g.EdgeMaxSpeedOsm = new bool[n]; g.EdgeStart = new int[n + 1];
            g.EdgeMaxWeightC = new ushort[n]; g.EdgeMaxAxleLoadC = new ushort[n]; g.EdgeMaxHeightCm = new ushort[n]; g.EdgeMaxLengthCm = new ushort[n];
            var pts = new List<Vector2>();
            for (int i = 0; i < n; i++)
            {
                var (a, b, f, nm, mw, mal, mh, ml) = edges[i];
                g.EdgeFrom[i] = a; g.EdgeTo[i] = b; g.EdgeFlags[i] = f; g.EdgeClass[i] = 1;
                g.EdgeMaxWeightC[i] = mw; g.EdgeMaxAxleLoadC[i] = mal; g.EdgeMaxHeightCm[i] = mh; g.EdgeMaxLengthCm[i] = ml;
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

        static readonly Vector2[] k_Nodes = { new Vector2(0, 0), new Vector2(200, 0), new Vector2(400, 0), new Vector2(0, 200), new Vector2(400, 200), new Vector2(600, 0) };
        static RouteGraph Highway(ushort mw = 0, ushort mal = 0, ushort mh = 0, ushort ml = 0, byte extraFlags = 0) => Build(k_Nodes, new (int, int, byte, string, ushort, ushort, ushort, ushort)[]
        {
            (0, 1, 0, "Dolna", 0, 0, 0, 0), (1, 2, (byte)(0 | extraFlags), "Srodkowa", mw, mal, mh, ml),
            (0, 3, 0, "GornaL", 0, 0, 0, 0), (3, 4, 0, "Gorna", 0, 0, 0, 0), (4, 2, 0, "GornaP", 0, 0, 0, 0),
            (2, 5, 0, "Dalsza", 0, 0, 0, 0),
        });

        [Fact]
        public void Synthetic_WeightLimitBelowTruck_ForcesDetour()
        {
            var planner = new RoutePlanner(Highway(mw: 3500));
            var p = RoutePath.For(planner.Graph);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), float.NaN, new Vector2(550, 0), p));
            Assert.True(p.Length > 700f, "detours over the top path instead of the 35 t Srodkowa");
            for (int i = 0; i < p.DirectedCount; i++) Assert.NotEqual(1, p.Directed[i] >> 1);

            var free = new RoutePlanner(Highway());
            var q = RoutePath.For(free.Graph);
            Assert.Equal(PlanStatus.Ok, free.Plan(new Vector2(50, 0), float.NaN, new Vector2(550, 0), q));
            Assert.True(q.Length < 700f, "without a limit: straight along the bottom");
        }

        [Fact]
        public void Synthetic_HeightLengthAxleLimits_ForceDetour()
        {
            foreach (var (mw, mal, mh, ml) in new (ushort, ushort, ushort, ushort)[] { (0, 0, 350, 0), (0, 0, 0, 1600), (0, 1000, 0, 0) })
            {
                var planner = new RoutePlanner(Highway(mw, mal, mh, ml));
                var p = RoutePath.For(planner.Graph);
                var st = planner.Plan(new Vector2(50, 0), float.NaN, new Vector2(550, 0), p);
                Assert.True(st == PlanStatus.Ok, $"limit w={mw} a={mal} h={mh} l={ml}: {st}");
                Assert.True(p.Length > 700f, $"detour for w={mw} a={mal} h={mh} l={ml}");
            }
        }

        [Fact]
        public void Synthetic_LimitEqualToTruckParameter_IsAllowed()
        {
            var planner = new RoutePlanner(Highway(mw: RoutePlanner.TruckMaxWeightCt, mal: RoutePlanner.TruckMaxAxleLoadCt,
                                                   mh: RoutePlanner.TruckMaxHeightCm, ml: RoutePlanner.TruckMaxLengthCm));
            var p = RoutePath.For(planner.Graph);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), float.NaN, new Vector2(550, 0), p));
            Assert.True(p.Length < 700f, "limits equal to the truck's parameters do not block");
        }

        [Fact]
        public void Synthetic_LimitOnGoalEdge_NoPath()
        {
            var g = Highway();
            g.EdgeMaxWeightC[5] = 3500;
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.NoPath, planner.Plan(new Vector2(50, 0), float.NaN, new Vector2(550, 0), p));
        }

        [Fact]
        public void Synthetic_HgvDestination_AllowedOnlyAsGoal()
        {
            var g = Highway(extraFlags: RouteGraph.FlagHgvDestination);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), float.NaN, new Vector2(550, 0), p));
            Assert.True(p.Length > 700f, "hgv=destination edge forbidden mid-route");
            for (int i = 0; i < p.DirectedCount; i++) Assert.NotEqual(1, p.Directed[i] >> 1);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), float.NaN, new Vector2(350, 0), p));
            Assert.True(p.Length < 700f);
            Assert.Equal(1, p.Directed[p.DirectedCount - 1] >> 1);
        }

        [Fact]
        public void EdgeAllowed_MatchesTruckProfile()
        {
            var g = Highway(mw: 3999);
            Assert.False(RoutePlanner.EdgeAllowed(g, 1, false));
            Assert.False(RoutePlanner.EdgeAllowed(g, 1, true));
            g.EdgeMaxWeightC[1] = 4000;
            Assert.True(RoutePlanner.EdgeAllowed(g, 1, true));
            g.EdgeFlags[1] = RouteGraph.FlagHgvDestination;
            g.EdgeMaxWeightC[1] = 0;
            Assert.False(RoutePlanner.EdgeAllowed(g, 1, false));
            Assert.True(RoutePlanner.EdgeAllowed(g, 1, true));
        }

        static byte[] KrtgBytes(int version, ushort mw, ushort mal, ushort mh, ushort ml)
        {
            using var ms = new MemoryStream();
            using var w = new BinaryWriter(ms, Encoding.UTF8);
            w.Write((byte)'K'); w.Write((byte)'R'); w.Write((byte)'T'); w.Write((byte)'G');
            w.Write((ushort)version);
            w.Write((ushort)1); w.Write((ushort)0);
            w.Write((uint)2);
            w.Write(0f); w.Write(0f); w.Write((byte)0);
            w.Write(100f); w.Write(0f); w.Write((byte)0);
            w.Write((uint)1);
            w.Write((uint)0); w.Write((uint)1); w.Write(100f); w.Write((byte)1); w.Write((byte)0);
            w.Write((ushort)0); w.Write((byte)0); w.Write((byte)0); w.Write((ushort)2);
            if (version >= 2) { w.Write(mw); w.Write(mal); w.Write(mh); w.Write(ml); }
            w.Write(0f); w.Write(0f); w.Write(100f); w.Write(0f);
            w.Write((ushort)0);
            if (version >= 2) w.Write((uint)0);
            return ms.ToArray();
        }

        [Fact]
        public void Parse_V1AndV2_BackwardCompatible()
        {
            var v1 = RouteGraph.Parse(KrtgBytes(1, 0, 0, 0, 0));
            Assert.Equal(1, v1.Version);
            Assert.Equal(1, v1.EdgeCount);
            Assert.Equal(0, v1.EdgeMaxWeightC[0]);
            Assert.Equal(0, v1.EdgeMaxHeightCm[0]);

            var v2 = RouteGraph.Parse(KrtgBytes(2, 4000, 1150, 350, 1647));
            Assert.Equal(2, v2.Version);
            Assert.Equal(4000, v2.EdgeMaxWeightC[0]);
            Assert.Equal(1150, v2.EdgeMaxAxleLoadC[0]);
            Assert.Equal(350, v2.EdgeMaxHeightCm[0]);
            Assert.Equal(1647, v2.EdgeMaxLengthCm[0]);
            Assert.False(RoutePlanner.EdgeAllowed(v2, 0, false), "3.50 m < 4.00 m truck: forbidden");
            Assert.Throws<FormatException>(() => RouteGraph.Parse(KrtgBytes(3, 0, 0, 0, 0)));
        }

        [Fact]
        public void Synthetic_AxleLoad10Blocks_11_5Allowed_ADR0164()
        {
            // Szosa Knyszynska / Szosa Elcka style maxaxleload=10: the 11.5 t drive axle must detour; the 11.5 t roads of the tile pass.
            var blocked = new RoutePlanner(Highway(mal: 1000));
            var p = RoutePath.For(blocked.Graph);
            Assert.Equal(PlanStatus.Ok, blocked.Plan(new Vector2(50, 0), float.NaN, new Vector2(550, 0), p));
            Assert.True(p.Length > 700f, "detour around the 10 t axle limit");
            for (int i = 0; i < p.DirectedCount; i++) Assert.NotEqual(1, p.Directed[i] >> 1);
            var ok = new RoutePlanner(Highway(mal: 1150));
            var q = RoutePath.For(ok.Graph);
            Assert.Equal(PlanStatus.Ok, ok.Plan(new Vector2(50, 0), float.NaN, new Vector2(550, 0), q));
            Assert.True(q.Length < 700f, "11.5 t axle limit equals the truck: straight");
        }

        [Fact]
        public void Synthetic_HgvTimedFlag_IsInformationalOnly_ADR0164()
        {
            Assert.Equal(128, RouteGraph.FlagHgvTimed);
            Assert.Equal(0, RouteGraph.FlagHgvTimed & (RouteGraph.FlagOneway | RouteGraph.FlagRoundabout | RouteGraph.FlagNoTruck | RouteGraph.FlagRestricted
                | RouteGraph.FlagLink | RouteGraph.FlagHgvDestination | RouteGraph.FlagOffReach));
            var planner = new RoutePlanner(Highway(extraFlags: RouteGraph.FlagHgvTimed));
            var p = RoutePath.For(planner.Graph);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), float.NaN, new Vector2(550, 0), p));
            Assert.True(p.Length < 700f, "a timed hgv ban is not a block (no clock in the planner)");
            Assert.True(RoutePlanner.EdgeAllowed(planner.Graph, 1, false));
        }

        [Fact]
        public void TruckAxleLoad_MatchesVehicleData_ADR0164()
        {
            // Drive axle laden load of the player's tractor (EBS design value, docs/VEHICLE_REFERENCE_DATA.md, WORKING_VALUE):
            // 112 800 N / 9.80665 = 11.50 t = RoutePlanner.TruckMaxAxleLoadCt (also the Directive 96/53/EC drive-axle limit, UNVERIFIED).
            const string rel = "game/Assets/_Project/Vehicle/Physics/Definitions/Data/tractor_4x2_generic.vehicle.json";
            string file = null;
            foreach (var start in new[] { AppContext.BaseDirectory, Directory.GetCurrentDirectory() })
                for (var d = new DirectoryInfo(start); d != null && file == null; d = d.Parent)
                    if (File.Exists(Path.Combine(d.FullName, rel))) file = Path.Combine(d.FullName, rel);
            Assert.NotNull(file);
            using var doc = System.Text.Json.JsonDocument.Parse(File.ReadAllText(file));
            double rearN = 0;
            foreach (var a in doc.RootElement.GetProperty("axles").EnumerateArray())
                if (a.GetProperty("name").GetString() == "rear") rearN = a.GetProperty("ladenAxleLoadN").GetDouble();
            Assert.True(rearN > 0);
            Assert.Equal(RoutePlanner.TruckMaxAxleLoadCt, (int)Math.Round(rearN / 9.80665 / 10.0));
        }

        [Fact]
        public void Region_LimitsLoadedAndEmptyForCurrentData()
        {
            var g = RouteGraph.Load(Region);
            Assert.NotNull(g);
            Assert.True(g.Version == 1 || g.Version == 2);
            Assert.Equal(g.EdgeCount, g.EdgeMaxWeightC.Length);
            int limited = 0, hgvDest = 0;
            for (int e = 0; e < g.EdgeCount; e++)
            {
                if (g.EdgeMaxWeightC[e] != 0 || g.EdgeMaxAxleLoadC[e] != 0 || g.EdgeMaxHeightCm[e] != 0 || g.EdgeMaxLengthCm[e] != 0) limited++;
                if ((g.EdgeFlags[e] & RouteGraph.FlagHgvDestination) != 0) hgvDest++;
            }
            // ADR 0164: the only numeric limit in the region is maxaxleload=11.5 (= the truck's own axle limit, no route effect);
            // before the tag pass-through (roads.graph.json / .bytes regenerated) there are none.
            for (int e = 0; e < g.EdgeCount; e++)
            {
                Assert.Equal(0, g.EdgeMaxWeightC[e]); Assert.Equal(0, g.EdgeMaxHeightCm[e]); Assert.Equal(0, g.EdgeMaxLengthCm[e]);
                Assert.True(g.EdgeMaxAxleLoadC[e] == 0 || g.EdgeMaxAxleLoadC[e] == RoutePlanner.TruckMaxAxleLoadCt, $"edge {e}: axle {g.EdgeMaxAxleLoadC[e]}");
                Assert.True(RoutePlanner.EdgeAllowed(g, e, true) || (g.EdgeFlags[e] & RouteGraph.FlagHgvDestination) != 0);
            }
            Assert.True(limited == 0 || limited == 89, $"limit-tagged edges: 0 (old data) or 89 (maxaxleload=11.5), got {limited}");
            Assert.Equal(0, hgvDest);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            int sa = g.Snap(new Vector2(-1.7f, -897.8f), RoutePlanner.SnapStartM, out _, out _, out _);
            int sb = g.Snap(new Vector2(-172f, -298f), RoutePlanner.SnapGoalM, out _, out _, out _);
            Assert.True(sa >= 0); Assert.True(sb >= 0);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(-1.7f, -897.8f), float.NaN, new Vector2(-172f, -298f), p));
            for (int i = 0; i < p.DirectedCount; i++)
                Assert.True(RoutePlanner.EdgeAllowed(g, p.Directed[i] >> 1, false) || p.Directed[i] >> 1 == sb >> 1 || p.Directed[i] >> 1 == sa >> 1);
        }
    }
}
