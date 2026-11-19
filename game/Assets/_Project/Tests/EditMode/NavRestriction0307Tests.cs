using System.Collections.Generic;
using Game.Controls;
using Game.Core.Navigation;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0307 (D91): the game warns about a road limit below the combination (height / weight from the routing graph =
    /// OSM maxheight, maxweight:hgv) and never blocks the drive. Synthetic graphs for the logic, the shipped graph of
    /// tile `tykocin` for the DW671 bridge over the Narew (maxheight 3.7 m, maxweight:hgv 12 t).
    /// </summary>
    public class NavRestriction0307Tests
    {
        static RouteGraph Build(Vector2[] nodes, (int a, int b, string name, ushort mw, ushort mal, ushort mh, ushort ml)[] edges)
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
                var (a, b, nm, mw, mal, mh, ml) = edges[i];
                g.EdgeFrom[i] = a; g.EdgeTo[i] = b; g.EdgeClass[i] = 1;
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

        // West-east road with a bridge 700..900 m (two edges with the same limits) and a side road north at the west abutment:
        //                 S(700,300)
        //                 |
        //   A(0,0) ------ B(700,0) == M(800,0) == C(900,0) ------ D(1500,0)
        static readonly Vector2[] k_Nodes =
        {
            new Vector2(0, 0), new Vector2(700, 0), new Vector2(800, 0), new Vector2(900, 0), new Vector2(1500, 0), new Vector2(700, 300),
        };

        static RouteGraph Road(ushort mh = 370, ushort mw = 1200, ushort mal = 0, ushort ml = 0) => Build(k_Nodes, new (int, int, string, ushort, ushort, ushort, ushort)[]
        {
            (0, 1, "Dojazd", 0, 0, 0, 0), (1, 2, "Most", mw, mal, mh, ml), (2, 3, "Most", mw, mal, mh, ml),
            (3, 4, "Miasto", 0, 0, 0, 0), (1, 5, "Boczna", 0, 0, 0, 0),
        });

        static RoutePath PlanAcross(RouteGraph g, out RoutePlanner planner, TruckLimits? truck = null)
        {
            planner = new RoutePlanner(g) { RelaxTruckLimits = true };
            if (truck.HasValue) planner.Truck = truck.Value;
            var p = RoutePath.For(g);
            Assert.AreEqual(PlanStatus.Ok, planner.Plan(new Vector2(10, 0), 90f, new Vector2(1400, 0), p));
            return p;
        }

        [Test]
        public void StrictPlanRefusesTheBridge_RelaxedPlanCarriesTheRestriction()
        {
            var g = Road();
            var strict = new RoutePlanner(g);
            var p0 = RoutePath.For(g);
            Assert.AreEqual(PlanStatus.NoPath, strict.Plan(new Vector2(10, 0), 90f, new Vector2(1400, 0), p0), "limits still forbid the edge");
            var p = PlanAcross(g, out var planner);
            Assert.IsTrue(planner.LastUsedRelaxed);
            Assert.AreEqual(1, p.RestrCount, "two bridge edges with the same limits = one stretch");
            var r = p.Restr[0];
            Assert.AreEqual(690f, r.S0, 0.5f); Assert.AreEqual(890f, r.S1, 0.5f);
            Assert.AreEqual(370, r.MaxHeightCm); Assert.AreEqual(1200, r.MaxWeightC);
            Assert.AreEqual(LimitKind.Height | LimitKind.Weight, r.Exceeded);
            Assert.AreEqual(700f, r.Pos.x, 0.5f);
            Assert.AreEqual("Most", g.Names[r.Name]);
            p.Clear();
            Assert.AreEqual(0, p.RestrCount);
        }

        [Test]
        public void OnRoute_WarnsFrom500mBefore_ToTheEndOfTheStretch()
        {
            var p = PlanAcross(Road(), out _);
            Assert.IsFalse(RestrictionScout.OnRoute(p, 100f, RestrictionScout.WarnM, out _, out _), "590 m before: silent");
            Assert.IsTrue(RestrictionScout.OnRoute(p, 200f, RestrictionScout.WarnM, out var r, out float d), "490 m before: warns");
            Assert.AreEqual(490f, d, 1f);
            Assert.AreEqual(370, r.MaxHeightCm);
            Assert.IsTrue(RestrictionScout.OnRoute(p, 800f, RestrictionScout.WarnM, out _, out d));
            Assert.AreEqual(0f, d, "on the bridge");
            Assert.IsFalse(RestrictionScout.OnRoute(p, 895f, RestrictionScout.WarnM, out _, out _), "past it");
            Assert.AreEqual(500f, RestrictionScout.WarnM, "D91: about 500 m before the bridge");
        }

        [Test]
        public void OnlyTheLimitsTheCombinationExceedsAreReported()
        {
            // 11 t rigid, 3.5 m high: nothing; 11 t and 4 m: height only; a limit equal to the value is allowed
            var light = new TruckLimits { WeightCt = 1100, AxleLoadCt = 800, HeightCm = 350, LengthCm = 900 };
            var g = Road();
            Assert.AreEqual(LimitKind.None, light.Exceeded(g, 1));
            light.HeightCm = 400;
            Assert.AreEqual(LimitKind.Height, light.Exceeded(g, 1));
            light.HeightCm = 370; light.WeightCt = 1200;
            Assert.AreEqual(LimitKind.None, light.Exceeded(g, 1));
            var d = TruckLimits.Default;
            Assert.AreEqual(4000, d.WeightCt); Assert.AreEqual(400, d.HeightCm);
            Assert.AreEqual(LimitKind.Height | LimitKind.Weight, d.Exceeded(g, 1));
            Assert.AreEqual(LimitKind.AxleLoad | LimitKind.Length, d.Exceeded(Road(0, 0, 1000, 1200), 1));
            var p = PlanAcross(g, out _, new TruckLimits { WeightCt = 1100, AxleLoadCt = 800, HeightCm = 400, LengthCm = 900 });
            Assert.AreEqual(1, p.RestrCount);
            Assert.AreEqual(LimitKind.Height, p.Restr[0].Exceeded, "a light, tall truck: the height sign only");
        }

        [Test]
        public void WithoutARoute_TheRoadAheadIsScouted_StraightOnOnly()
        {
            var g = Road();
            var t = TruckLimits.Default;
            Assert.IsTrue(RestrictionScout.OnRoad(g, new Vector2(250, 2), 90f, t, RestrictionScout.WarnM, out var r, out float d), "eastbound, 450 m before");
            Assert.AreEqual(450f, d, 1f);
            Assert.AreEqual(LimitKind.Height | LimitKind.Weight, r.Exceeded);
            Assert.AreEqual(700f, r.Pos.x, 0.5f);
            Assert.IsFalse(RestrictionScout.OnRoad(g, new Vector2(150, 2), 90f, t, RestrictionScout.WarnM, out _, out _), "550 m before");
            Assert.IsFalse(RestrictionScout.OnRoad(g, new Vector2(250, 2), 270f, t, RestrictionScout.WarnM, out _, out _), "driving away");
            Assert.IsTrue(RestrictionScout.OnRoad(g, new Vector2(1300, -2), 270f, t, RestrictionScout.WarnM, out _, out d), "westbound from the town");
            Assert.AreEqual(400f, d, 1f);
            Assert.IsTrue(RestrictionScout.OnRoad(g, new Vector2(820, 0), 90f, t, RestrictionScout.WarnM, out _, out d));
            Assert.AreEqual(0f, d, "on the bridge");
            // the side road meets the bridge road at 90 deg: the bridge is a turn away, not ahead
            Assert.IsFalse(RestrictionScout.OnRoad(g, new Vector2(700, 200), 180f, t, RestrictionScout.WarnM, out _, out _));
            Assert.IsFalse(RestrictionScout.OnRoad(g, new Vector2(250, 200), 90f, t, RestrictionScout.WarnM, out _, out _), "off the road network");
            var low = new TruckLimits { WeightCt = 1100, AxleLoadCt = 800, HeightCm = 350, LengthCm = 900 };
            Assert.IsFalse(RestrictionScout.OnRoad(g, new Vector2(250, 2), 90f, low, RestrictionScout.WarnM, out _, out _), "fits: no warning");
        }

        [Test]
        public void ScoutAllocatesNothing()
        {
            var g = Road();
            var p = PlanAcross(g, out _);
            var t = TruckLimits.Default;
            bool any = false;
            void Run()
            {
                for (int i = 0; i < 200; i++)
                {
                    any |= RestrictionScout.OnRoad(g, new Vector2(100 + i * 3f, 1f), 90f, t, RestrictionScout.WarnM, out _, out _);
                    any |= RestrictionScout.OnRoute(p, i * 5f, RestrictionScout.WarnM, out _, out _);
                }
            }
            GcAllocCounter.AssertZero(Run, warmup: Run, message: "restriction scout runs every frame / 4 Hz in the drive loop");
            Assert.IsTrue(any);
        }

        [Test]
        public void HudTiles_ShowTheSignValues_AfterTheRedTiles()
        {
            var buf = new HudWarning[HudWarnings.MaxShown];
            var s = new HudWarningInput { RoadLimitHeightCm = 370, RoadLimitWeightC = 1200 };
            Assert.AreEqual(2, HudWarnings.Collect(s, buf));
            Assert.AreEqual(HudWarning.RoadLimitHeight, buf[0]); Assert.AreEqual(HudWarning.RoadLimitWeight, buf[1]);
            Assert.AreEqual("WYS. 3,7 m", HudTexts.Warning(buf[0], s));
            Assert.AreEqual("MASA 12 t", HudTexts.Warning(buf[1], s));
            Assert.IsFalse(HudWarnings.IsRed(buf[0]), "amber: caution, the drive is not blocked");
            Assert.AreSame(HudTexts.RoadLimitHeight(370), HudTexts.RoadLimitHeight(370), "label built once per value (no per-frame allocation)");
            s.AirLow = true; s.AbsFault = true;
            Assert.AreEqual(3, HudWarnings.Collect(s, buf));
            Assert.AreEqual(HudWarning.AirLow, buf[0]); Assert.AreEqual(HudWarning.RoadLimitHeight, buf[1]); Assert.AreEqual(HudWarning.RoadLimitWeight, buf[2]);
            var other = new HudWarningInput { RoadLimitOther = true };
            Assert.AreEqual(1, HudWarnings.Collect(other, buf));
            Assert.AreEqual("OGRANICZENIE", HudTexts.Warning(buf[0], other));
            Assert.AreEqual(0, HudWarnings.Collect(default, buf));
            Assert.AreEqual("ABS", HudTexts.Warning(HudWarning.AbsActive, s), "other tiles unchanged");
        }

        [Test]
        public void TykocinGraph_HasTheNarewBridgeLimits()
        {
            var g = RouteGraph.Load("tykocin");
            Assert.NotNull(g, "Resources/CabDisplay/Nav/tykocin_route.bytes");
            var t = TruckLimits.Default;
            int bridge = 0; float len = 0f;
            for (int e = 0; e < g.EdgeCount; e++)
            {
                if (g.EdgeMaxHeightCm[e] == 0) continue;
                Assert.AreEqual(370, g.EdgeMaxHeightCm[e], "OSM w96942026 maxheight=3.7");
                Assert.AreEqual(1200, g.EdgeMaxWeightC[e], "OSM w96942026 maxweight:hgv=12");
                Assert.AreEqual(LimitKind.Height | LimitKind.Weight, t.Exceeded(g, e));
                StringAssert.Contains("Puchalskiego", g.Names[g.EdgeName[e]]);
                bridge++; len += g.GeomLength(e);
            }
            Assert.GreaterOrEqual(bridge, 1, "the bridge edge carries its limits (KRTG v2)");
            Assert.AreEqual(194.8f, len, 3f, "bridge length in the graph (roads.graph.json: 194.8 m)");
        }
    }
}
