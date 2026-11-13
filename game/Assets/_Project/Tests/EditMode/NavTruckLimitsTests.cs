using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using Game.Core.Navigation;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>Truck limits in routing (ADR 0150, open item "limity masy/wysokości ciężarówki"): KRTG v2 carries
    /// OSM maxweight / maxaxleload / maxheight / maxlength per edge and the hgv=destination flag; the planner forbids
    /// an edge whose limit is below the truck's parameters (hgv=destination only as the goal edge).</summary>
    public class NavTruckLimitsTests
    {
        const string Region = "bialystok-industrial-c";

        /// <summary>Graph from straight edges between nodes; limits in stored units (0.01 t / cm, 0 = none).</summary>
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

        // Two parallel paths A-B-C (bottom, edges 0/1/5) and A-D-E-C (top, edges 2/3/4).
        //   D(0,200) ---- E(400,200)
        //   |              |
        //   A(0,0) -- B(200,0) -- C(400,0) -- F(600,0)
        static readonly Vector2[] k_Nodes = { new Vector2(0, 0), new Vector2(200, 0), new Vector2(400, 0), new Vector2(0, 200), new Vector2(400, 200), new Vector2(600, 0) };
        static RouteGraph Highway(ushort mw = 0, ushort mal = 0, ushort mh = 0, ushort ml = 0, byte extraFlags = 0) => Build(k_Nodes, new (int, int, byte, string, ushort, ushort, ushort, ushort)[]
        {
            (0, 1, 0, "Dolna", 0, 0, 0, 0), (1, 2, (byte)(0 | extraFlags), "Srodkowa", mw, mal, mh, ml),
            (0, 3, 0, "GornaL", 0, 0, 0, 0), (3, 4, 0, "Gorna", 0, 0, 0, 0), (4, 2, 0, "GornaP", 0, 0, 0, 0),
            (2, 5, 0, "Dalsza", 0, 0, 0, 0),
        });

        [Test]
        public void Synthetic_WeightLimitBelowTruck_ForcesDetour()
        {
            var planner = new RoutePlanner(Highway(mw: 3500));   // maxweight 35.00 t < 40 t
            var p = RoutePath.For(planner.Graph);
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), float.NaN, new Vector2(550, 0), p));
            Assert.Greater(p.Length, 700f, "detours over the top path instead of the 35 t Srodkowa");
            for (int i = 0; i < p.DirectedCount; i++) Assert.AreNotEqual(1, p.Directed[i] >> 1, "the limited edge is not used");

            var free = new RoutePlanner(Highway());
            var q = RoutePath.For(free.Graph);
            Assert.AreEqual(PlanStatus.Ok, free.Plan(new Vector2(50, 0), float.NaN, new Vector2(550, 0), q));
            Assert.Less(q.Length, 700f, "without a limit: straight along the bottom");
        }

        [Test]
        public void Synthetic_HeightLengthAxleLimits_ForceDetour()
        {
            foreach (var (mw, mal, mh, ml) in new (ushort, ushort, ushort, ushort)[] { (0, 0, 350, 0), (0, 0, 0, 1600), (0, 1000, 0, 0) })
            {
                var planner = new RoutePlanner(Highway(mw, mal, mh, ml));
                var p = RoutePath.For(planner.Graph);
                Assert.AreEqual(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), float.NaN, new Vector2(550, 0), p),
                    $"limit w={mw} a={mal} h={mh} l={ml}");
                Assert.Greater(p.Length, 700f, $"detour for w={mw} a={mal} h={mh} l={ml}");
            }
        }

        [Test]
        public void Synthetic_LimitEqualToTruckParameter_IsAllowed()
        {
            // Exactly the truck's parameters (40.00 t, 11.50 t, 4.00 m, 16.47 m): "below" forbids, equal does not.
            var planner = new RoutePlanner(Highway(mw: RoutePlanner.TruckMaxWeightCt, mal: RoutePlanner.TruckMaxAxleLoadCt,
                                                   mh: RoutePlanner.TruckMaxHeightCm, ml: RoutePlanner.TruckMaxLengthCm));
            var p = RoutePath.For(planner.Graph);
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), float.NaN, new Vector2(550, 0), p));
            Assert.Less(p.Length, 700f, "limits equal to the truck's parameters do not block");
        }

        [Test]
        public void Synthetic_LimitOnGoalEdge_NoPath()
        {
            // A weight limit does NOT exempt the goal edge (only hgv=destination does): the only access to Dalsza
            // is the limited Srodkowa, so no route.
            var g = Highway();
            g.EdgeMaxWeightC[5] = 3500;
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.AreEqual(PlanStatus.NoPath, planner.Plan(new Vector2(50, 0), float.NaN, new Vector2(550, 0), p));
        }

        [Test]
        public void Synthetic_HgvDestination_AllowedOnlyAsGoal()
        {
            var g = Highway(extraFlags: RouteGraph.FlagHgvDestination);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            // Through traffic: detour over the top.
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), float.NaN, new Vector2(550, 0), p));
            Assert.Greater(p.Length, 700f, "hgv=destination edge forbidden mid-route");
            for (int i = 0; i < p.DirectedCount; i++) Assert.AreNotEqual(1, p.Directed[i] >> 1);
            // Goal on that edge: allowed.
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(new Vector2(50, 0), float.NaN, new Vector2(350, 0), p));
            Assert.Less(p.Length, 700f);
            Assert.AreEqual(1, p.Directed[p.DirectedCount - 1] >> 1, "the route ends on the hgv=destination edge");
        }

        [Test]
        public void EdgeAllowed_MatchesTruckProfile()
        {
            var g = Highway(mw: 3999);
            Assert.IsFalse(RoutePlanner.EdgeAllowed(g, 1, false));
            Assert.IsFalse(RoutePlanner.EdgeAllowed(g, 1, true), "a numeric limit applies also to the goal edge");
            g.EdgeMaxWeightC[1] = 4000;
            Assert.IsTrue(RoutePlanner.EdgeAllowed(g, 1, true));
            g.EdgeFlags[1] = RouteGraph.FlagHgvDestination;
            g.EdgeMaxWeightC[1] = 0;
            Assert.IsFalse(RoutePlanner.EdgeAllowed(g, 1, false));
            Assert.IsTrue(RoutePlanner.EdgeAllowed(g, 1, true), "hgv=destination allowed as the goal edge");
        }

        /// <summary>Minimal KRTG file written by hand: one edge, optional limit fields (v2).</summary>
        static byte[] KrtgBytes(int version, ushort mw, ushort mal, ushort mh, ushort ml)
        {
            using var ms = new MemoryStream();
            using var w = new BinaryWriter(ms, Encoding.UTF8);
            w.Write((byte)'K'); w.Write((byte)'R'); w.Write((byte)'T'); w.Write((byte)'G');
            w.Write((ushort)version);
            w.Write((ushort)1); w.Write((ushort)0);                       // 1 name: ""
            w.Write((uint)2);                                             // 2 nodes
            w.Write(0f); w.Write(0f); w.Write((byte)0);
            w.Write(100f); w.Write(0f); w.Write((byte)0);
            w.Write((uint)1);                                             // 1 edge
            w.Write((uint)0); w.Write((uint)1); w.Write(100f); w.Write((byte)1); w.Write((byte)0);
            w.Write((ushort)0); w.Write((byte)0); w.Write((byte)0); w.Write((ushort)2);
            if (version >= 2) { w.Write(mw); w.Write(mal); w.Write(mh); w.Write(ml); }
            w.Write(0f); w.Write(0f); w.Write(100f); w.Write(0f);
            w.Write((ushort)0);                                           // no restrictions
            if (version >= 2) w.Write((uint)0);                           // lane section (M22): no lane blocks
            return ms.ToArray();
        }

        [Test]
        public void Parse_V1AndV2_BackwardCompatible()
        {
            var v1 = RouteGraph.Parse(KrtgBytes(1, 0, 0, 0, 0));
            Assert.AreEqual(1, v1.Version);
            Assert.AreEqual(1, v1.EdgeCount);
            Assert.AreEqual(0, v1.EdgeMaxWeightC[0], "v1 file: no limit fields, zeros");
            Assert.AreEqual(0, v1.EdgeMaxHeightCm[0]);

            var v2 = RouteGraph.Parse(KrtgBytes(2, 4000, 1150, 350, 1647));
            Assert.AreEqual(2, v2.Version);
            Assert.AreEqual(4000, v2.EdgeMaxWeightC[0]);
            Assert.AreEqual(1150, v2.EdgeMaxAxleLoadC[0]);
            Assert.AreEqual(350, v2.EdgeMaxHeightCm[0]);
            Assert.AreEqual(1647, v2.EdgeMaxLengthCm[0]);
            Assert.IsTrue(RoutePlanner.EdgeAllowed(v2, 0, false) == false, "3.50 m < 4.00 m truck: forbidden");
            Assert.Throws<FormatException>(() => RouteGraph.Parse(KrtgBytes(3, 0, 0, 0, 0)));
        }

        [Test]
        public void Region_LimitsLoadedAndEmptyForCurrentData()
        {
            // The region graph has no maxweight/maxaxleload/maxlength tags and only maxheight=default (= no limit),
            // so no edge carries a numeric limit - true for the committed v1 file and for a regenerated v2 file.
            var g = RouteGraph.Load(Region);
            Assert.NotNull(g, "Resources/CabDisplay/Nav/" + Region + "_route.bytes");
            Assert.IsTrue(g.Version == 1 || g.Version == 2);
            Assert.AreEqual(g.EdgeCount, g.EdgeMaxWeightC.Length);
            Assert.AreEqual(g.EdgeCount, g.EdgeMaxAxleLoadC.Length);
            Assert.AreEqual(g.EdgeCount, g.EdgeMaxHeightCm.Length);
            Assert.AreEqual(g.EdgeCount, g.EdgeMaxLengthCm.Length);
            int limited = 0, hgvDest = 0;
            for (int e = 0; e < g.EdgeCount; e++)
            {
                if (g.EdgeMaxWeightC[e] != 0 || g.EdgeMaxAxleLoadC[e] != 0 || g.EdgeMaxHeightCm[e] != 0 || g.EdgeMaxLengthCm[e] != 0) limited++;
                if ((g.EdgeFlags[e] & RouteGraph.FlagHgvDestination) != 0) hgvDest++;
            }
            Assert.AreEqual(0, limited, "no numeric truck limits in this region's OSM data (maxheight=default only)");
            Assert.AreEqual(0, hgvDest, "no hgv=destination in this region's OSM data");
            // hgv=no edges (6) plus access=no / emergency_access are no-truck; routing still works on the rest.
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            int sa = g.Snap(new Vector2(-1.7f, -897.8f), RoutePlanner.SnapStartM, out _, out _, out _);
            int sb = g.Snap(new Vector2(-172f, -298f), RoutePlanner.SnapGoalM, out _, out _, out _);
            Assert.GreaterOrEqual(sa, 0); Assert.GreaterOrEqual(sb, 0);
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(new Vector2(-1.7f, -897.8f), float.NaN, new Vector2(-172f, -298f), p));
            for (int i = 0; i < p.DirectedCount; i++)
                Assert.IsTrue(RoutePlanner.EdgeAllowed(g, p.Directed[i] >> 1, false) || p.Directed[i] >> 1 == sb >> 1 || p.Directed[i] >> 1 == sa >> 1,
                    "planned route uses only edges allowed for the truck");
        }
    }
}
