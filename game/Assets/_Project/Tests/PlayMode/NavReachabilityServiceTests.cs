using System.Collections.Generic;
using Game.Core.Navigation;
using Game.UI.Navigation;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>M27 / ADR 0150 reachability through <see cref="NavigationService"/> (Game.UI, referenced only by the
    /// PlayMode test assembly - integration r5 moved these from EditMode, where Game.UI is not referenced and the file
    /// did not compile). A tap in an off-reach part snaps the pin to the reachable part and reports
    /// <see cref="PlanStatus.GoalOffReach"/> (HUD: NavText.OffReach) instead of a later "Brak dojazdu".</summary>
    public class NavReachabilityServiceTests
    {
        const string Region = "bialystok-industrial-c";

        //   3 ---- 2            main SCC: two-way square 0-1-2-3
        //   |      |
        //   0 ---- 1 --(oneway)--> 4     spur: own SCC but drivable to - NOT off-reach (integration r5)
        //   5 ---- 6                     off-reach pair (connected only "outside the tile")
        static RouteGraph BuildWithOffReach()
        {
            var nodes = new[] { new Vector2(0, 0), new Vector2(200, 0), new Vector2(200, 200), new Vector2(0, 200),
                                new Vector2(400, 0), new Vector2(600, 0), new Vector2(700, 0) };
            var nodeFlags = new byte[] { 0, 0, 0, 0, 0, RouteGraph.FlagNodeOffReach, RouteGraph.FlagNodeOffReach };
            return Build(nodes, nodeFlags, new (int, int, byte, string)[]
            {
                (0, 1, 0, "Dolna"), (1, 2, 0, "Prawa"), (2, 3, 0, "Gorna"), (3, 0, 0, "Lewa"),
                (1, 4, RouteGraph.FlagOneway, "Slepa"),
                (5, 6, RouteGraph.FlagOffReach, "Buska"), (6, 5, RouteGraph.FlagOffReach, "Buska"),
            });
        }

        /// <summary>Graph from straight edges between nodes (same pattern as NavRoutingTests).</summary>
        static RouteGraph Build(Vector2[] nodes, byte[] nodeFlags, (int a, int b, byte flags, string name)[] edges)
        {
            var g = new RouteGraph();
            var names = new List<string> { "" };
            g.NodePos = nodes; g.NodeFlags = nodeFlags;
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

        [Test]
        public void Synthetic_SetPin_OffReachTap_SnapsToNearestMainNodeAndReports()
        {
            var g = BuildWithOffReach();
            var go = new GameObject("NavReachTest");
            var nav = go.AddComponent<NavigationService>();
            nav.SetGraphForTest(g);
            Assert.IsTrue(nav.SetPin(new Vector2(650, 0)), "tap in the off-reach part still sets the pin");
            Assert.AreEqual(PlanStatus.GoalOffReach, nav.LastStatus, "clear status instead of a later NoPath");
            // Integration r5: the one-way spur end (400, 0) is reachable, so it is the nearest reachable node.
            Assert.AreEqual(new Vector2(400, 0), nav.PinOnRoad, "pin snapped to the nearest reachable node (node 4)");
            Assert.AreEqual(System.Array.IndexOf(g.Names, "Slepa"), nav.PinName, "spur end named from its incoming edge");
            // ...and the route to that node plans fine.
            nav.SetPoseForTest(new Vector2(20, 0), 90f, 0f);
            Assert.AreEqual(PlanStatus.Ok, nav.PlanToPin());
            Assert.IsTrue(nav.Path.HasRoute);
            Object.DestroyImmediate(go);
        }

        [Test]
        public void Synthetic_SetPin_MainPart_Unchanged()
        {
            var g = BuildWithOffReach();
            var go = new GameObject("NavReachTest");
            var nav = go.AddComponent<NavigationService>();
            nav.SetGraphForTest(g);
            Assert.IsTrue(nav.SetPin(new Vector2(100, 5)));
            Assert.AreEqual(PlanStatus.Ok, nav.LastStatus);
            Assert.AreEqual(System.Array.IndexOf(g.Names, "Dolna"), nav.PinName);
            Assert.IsFalse(nav.SetPin(new Vector2(650, 2000)), "no road within reach at all");
            Assert.AreEqual(PlanStatus.GoalOffRoad, nav.LastStatus);
            Object.DestroyImmediate(go);
        }

        /// <summary>ADR 0168: a tap on an outbound carriageway that ends at the region-edge closure (no way back) snaps the
        /// pin out of the no-return zone like an off-reach tap.</summary>
        [Test]
        public void Synthetic_SetPin_NoReturnTap_SnapsOutOfTheZone()
        {
            var nodes = new[] { new Vector2(0, 0), new Vector2(200, 0), new Vector2(200, 200), new Vector2(0, 200),
                                new Vector2(400, 0), new Vector2(600, 0) };
            var g = Build(nodes, new byte[] { 0, 0, 0, 0, 0, RouteGraph.FlagNodeBoundary }, new (int, int, byte, string)[]
            {
                (0, 1, 0, "Dolna"), (1, 2, 0, "Prawa"), (2, 3, 0, "Gorna"), (3, 0, 0, "Lewa"),
                (1, 4, RouteGraph.FlagOneway, "Wylotowa"), (4, 5, RouteGraph.FlagOneway, "Wylotowa"),
            });
            Assert.IsTrue(g.EdgeNoReturn(5));
            var go = new GameObject("NavReachTest");
            var nav = go.AddComponent<NavigationService>();
            nav.SetGraphForTest(g);
            Assert.IsTrue(nav.SetPin(new Vector2(500, 2)));
            Assert.AreEqual(PlanStatus.GoalOffReach, nav.LastStatus);
            Assert.AreEqual(new Vector2(200, 0), nav.PinOnRoad, "nearest node outside the zone (the gate junction)");
            nav.SetPoseForTest(new Vector2(20, 0), 90f, 0f);
            Assert.AreEqual(PlanStatus.Ok, nav.PlanToPin());
            Object.DestroyImmediate(go);
        }

        [Test]
        public void Region_ReachabilityFlags_AndersaRoutable_BuskaSnapped()
        {
            // Works with a .bytes with or without the M27 flags (older files: every node reachable).
            var g = RouteGraph.Load(Region);
            Assert.NotNull(g);
            int offE = 0;
            for (int e = 0; e < g.EdgeCount; e++) if (g.EdgeOffReach(e)) offE++;
            Assert.IsTrue(offE == 0 || offE == 115, "115 off-reach edges after regeneration (forward closure of the main SCC), 0 before: " + offE);
            var go = new GameObject("NavReachTest");
            var nav = go.AddComponent<NavigationService>();
            nav.regionId = Region;
            nav.Init();
            Assert.IsTrue(nav.Ready);
            Assert.IsTrue(nav.SetPin(new Vector2(-172f, -298f)));   // Andersa SE - a main road, never off-reach
            Assert.AreEqual(PlanStatus.Ok, nav.LastStatus);
            Assert.IsTrue(nav.SetPin(new Vector2(-758.6f, -753.6f)));   // Buska (connected only outside the tile)
            Assert.AreEqual(offE > 0 ? PlanStatus.GoalOffReach : PlanStatus.Ok, nav.LastStatus);
            if (offE > 0)
            {
                int n = g.NearestMainNode(nav.PinOnRoad);
                Assert.GreaterOrEqual(n, 0);
                nav.SetPoseForTest(new Vector2(-1.7f, -897.8f), float.NaN, 0f);
                Assert.AreEqual(PlanStatus.Ok, nav.PlanToPin(), "the snapped pin is routable");
            }
            Object.DestroyImmediate(go);
        }
    }
}
