using System.Collections.Generic;
using Game.Core.Navigation;
using Game.UI.Navigation;
using Game.World.Streaming;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0307 (D91): the trip to the Rynek of Tykocin stays over the DW671 bridge on the Narew (OSM maxheight 3.7 m,
    /// maxweight:hgv 12 t; the combination is 4.0 m / 40 t) and the GPS warns about 500 m before it. Shipped data:
    /// nav_trips.json, the tile graph, the routing graphs of `dw671-tykocin-09` and `tykocin`.
    /// </summary>
    public class NavRestrictionWarning0307Tests
    {
        const string T9 = "dw671-tykocin-09", TY = "tykocin";
        // north end of the bridge edge w96942026 in roads.graph.json (EPSG:2180)
        const double BridgeNX = 751871.169, BridgeNY = 600508.557;
        readonly List<GameObject> m_Go = new List<GameObject>();

        [TearDown]
        public void TearDown()
        {
            foreach (var go in m_Go) if (go != null) Object.DestroyImmediate(go);
            m_Go.Clear();
            PlayerPrefs.DeleteKey(NavigationService.TripPref);
        }

        GameObject New(string n) { var g = new GameObject(n); m_Go.Add(g); return g; }

        static (bool, double, double) Anchor(TileGraph g, string id)
        {
            int i = g.IndexOf(id);
            return i >= 0 ? (true, g.Tiles[i].anchorX, g.Tiles[i].anchorY) : (false, 0.0, 0.0);
        }

        /// <summary>The last two tiles of the shipped Tykocin trip; the truck stands in `dw671-tykocin-09`, 300 m before the seam.</summary>
        NavigationService Setup(out TileGraph g, out NavTrip trip, out NavTripJoin seam)
        {
            g = TileGraph.LoadDefault();
            Assert.NotNull(g);
            var src = NavTripsData.LoadDefault().Find("tykocin");
            Assert.NotNull(src);
            int n = src.tiles.Length;
            Assert.AreEqual(T9, src.tiles[n - 2]); Assert.AreEqual(TY, src.tiles[n - 1]);
            seam = src.joins[n - 2];
            var data = new NavTripData
            {
                id = "bridge", label = "Tykocin", tiles = new[] { T9, TY }, joins = new[] { seam },
                goalTile = TY, goalX = src.goalX, goalY = src.goalY,
            };
            var tg = g;
            trip = new NavTrip(data, id => Anchor(tg, id));
            Assert.IsFalse(trip.Failed, trip.FailReason);
            var t9 = g.Tiles[g.IndexOf(T9)];
            Vector2 s = new Vector2((float)(seam.x - t9.anchorX), (float)(seam.y - t9.anchorY)) - NavTrip.SideDir(seam.side) * 300f;
            var nav = NavigationService.Install(New("nav"), null, null, New("root9").transform, T9);
            Assert.IsTrue(nav.Ready);
            var graph = nav.Graph;
            Assert.GreaterOrEqual(graph.Snap(s, 200f, out _, out Vector2 on, out _), 0, "DW671 near the start point");
            Vector2 d = NavTrip.SideDir(seam.side);
            nav.SetPoseForTest(on, Mathf.Atan2(d.x, d.y) * Mathf.Rad2Deg, 0f);
            nav.StartTrip(trip, t9.anchorX, t9.anchorY, remember: false);
            nav.StepTripForTest();
            Assert.IsTrue(trip.PlanDone);
            Assert.IsFalse(trip.Failed, trip.FailReason);
            return nav;
        }

        static void PoseAt(NavigationService nav, RoutePath p, float s)
        {
            int i = 1;
            while (i < p.Count - 1 && p.S[i] < s) i++;
            Vector2 a = p.Points[i - 1], b = p.Points[i];
            float t = Mathf.Clamp01((s - p.S[i - 1]) / Mathf.Max(1e-3f, p.S[i] - p.S[i - 1]));
            Vector2 dir = (b - a).normalized;
            nav.SetPoseForTest(Vector2.Lerp(a, b, t), Mathf.Atan2(dir.x, dir.y) * Mathf.Rad2Deg, 12f);
            nav.UpdateRestrictionForTest();
        }

        [Test]
        public void TripToTheRynekCrossesTheBridge_AndCarriesItsLimits()
        {
            var nav = Setup(out var g, out var trip, out _);
            Assert.AreEqual(1, trip.RelaxedCount, "D91: the route stays over the bridge (leg planned with the limits relaxed)");
            var p = nav.Path;
            Assert.AreEqual(1, p.RestrCount, "one limited stretch on the route: the bridge");
            var r = p.Restr[0];
            Assert.AreEqual(370, r.MaxHeightCm); Assert.AreEqual(1200, r.MaxWeightC);
            Assert.AreEqual(LimitKind.Height | LimitKind.Weight, r.Exceeded);
            Assert.AreEqual(194.8f, r.S1 - r.S0, 3f, "length of the bridge edge");
            var t9 = g.Tiles[g.IndexOf(T9)];
            var north = new Vector2((float)(BridgeNX - t9.anchorX), (float)(BridgeNY - t9.anchorY));
            Assert.Less(Vector2.Distance(north, r.Pos), 2f, "the stretch begins at the north abutment, in the frame of the truck's tile");
            StringAssert.Contains("Puchalskiego", nav.NameOf(r.Name));
            StringAssert.Contains("wysokość do 3,7 m, masa do 12 t", NavText.Describe(r));
            // the truck is 300 m before the seam and the bridge 835 m after it: too far for a warning
            nav.UpdateRestrictionForTest();
            Assert.IsFalse(nav.Restriction.Active);
            Debug.Log($"[TEST] bridge restriction at route S {r.S0:F0}..{r.S1:F0} m of {p.Length:F0} m");
        }

        [Test]
        public void WarningStarts500mBeforeTheBridge_AndEndsBehindIt()
        {
            var nav = Setup(out _, out _, out _);
            var p = nav.Path;
            var r = p.Restr[0];
            PoseAt(nav, p, r.S0 - 560f);
            Assert.IsFalse(nav.Restriction.Active, "560 m before");
            int before = nav.RestrictionWarnings;
            PoseAt(nav, p, r.S0 - 480f);
            var w = nav.Restriction;
            Assert.IsTrue(w.Active && w.OnRoute, "480 m before");
            Assert.AreEqual(480f, w.DistM, 3f);
            Assert.AreEqual(before + 1, nav.RestrictionWarnings);
            Assert.AreEqual(370, w.R.MaxHeightCm); Assert.AreEqual(1200, w.R.MaxWeightC);
            PoseAt(nav, p, r.S0 - 100f);
            Assert.AreEqual(100f, nav.Restriction.DistM, 3f);
            Assert.AreEqual(before + 1, nav.RestrictionWarnings, "one warning per approach");
            PoseAt(nav, p, r.S0 + 60f);
            Assert.IsTrue(nav.Restriction.Active);
            Assert.AreEqual(0f, nav.Restriction.DistM, "on the bridge");
            PoseAt(nav, p, r.S1 + 15f);
            Assert.IsFalse(nav.Restriction.Active, "behind the bridge");
            Assert.IsTrue(nav.Guidance.HasRoute, "the route is still there: nothing was blocked or re-planned");
            Assert.AreEqual(0, nav.RerouteCount);
        }

        [Test]
        public void WithoutARoute_TheBridgeAheadStillWarns_FromBothSides()
        {
            var nav = Setup(out var g, out _, out _);
            var p = nav.Path;
            var r = p.Restr[0];
            // positions on the route in the frame of tile 09, re-expressed in tile `tykocin`
            var t9 = g.Tiles[g.IndexOf(T9)]; var ty = g.Tiles[g.IndexOf(TY)];
            var off = new Vector2((float)(t9.anchorX - ty.anchorX), (float)(t9.anchorY - ty.anchorY));
            Vector2 At(float s, out float heading)
            {
                int i = 1;
                while (i < p.Count - 1 && p.S[i] < s) i++;
                Vector2 a = p.Points[i - 1], b = p.Points[i];
                Vector2 dir = (b - a).normalized;
                heading = Mathf.Atan2(dir.x, dir.y) * Mathf.Rad2Deg;
                return Vector2.Lerp(a, b, Mathf.Clamp01((s - p.S[i - 1]) / Mathf.Max(1e-3f, p.S[i] - p.S[i - 1]))) + off;
            }
            Vector2 north = At(r.S0 - 150f, out float hn);
            Vector2 south = At(r.S1 + 40f, out float hs);
            var free = NavigationService.Install(New("nav2"), null, null, New("rootTy").transform, TY);
            Assert.IsTrue(free.Ready);
            Assert.IsFalse(free.HasPin);
            free.SetPoseForTest(north, hn, 10f);
            free.UpdateRestrictionForTest();
            var w = free.Restriction;
            Assert.IsTrue(w.Active && !w.OnRoute, "no route: the road ahead is scouted");
            Assert.AreEqual(150f, w.DistM, 8f);
            Assert.AreEqual(LimitKind.Height | LimitKind.Weight, w.R.Exceeded);
            free.SetPoseForTest(south, hs + 180f, 10f);     // from the town, northbound
            free.UpdateRestrictionForTest();
            Assert.IsTrue(free.Restriction.Active, "southern entry");
            Assert.AreEqual(40f, free.Restriction.DistM, 8f);
            free.SetPoseForTest(south, hs, 10f);            // driving away from the bridge
            free.UpdateRestrictionForTest();
            Assert.IsFalse(free.Restriction.Active);
            // a lighter, lower vehicle gets no warning
            free.Truck = new TruckLimits { WeightCt = 1100, AxleLoadCt = 800, HeightCm = 350, LengthCm = 900 };
            free.SetPoseForTest(north, hn, 10f);
            free.UpdateRestrictionForTest();
            Assert.IsFalse(free.Restriction.Active, "3.5 m / 11 t fits under 3.7 m / 12 t");
        }

        [Test]
        public void TextsArePolishWithDecimalComma()
        {
            var b = new Game.UI.CabDisplays.TextBuffer(32);
            NavDraw.AppendLimit(b.Clear(), LimitKind.Height, 370, true); Assert.AreEqual("3,7 m", b.ToString());
            NavDraw.AppendLimit(b.Clear(), LimitKind.Weight, 1200, true); Assert.AreEqual("12 t", b.ToString());
            NavDraw.AppendLimit(b.Clear(), LimitKind.AxleLoad, 1150, false); Assert.AreEqual("11,5t", b.ToString());
            NavDraw.AppendLimit(b.Clear(), LimitKind.Height, 379, true); Assert.AreEqual("3,7 m", b.ToString(), "cut, never rounded above the sign");
            var r = new RouteRestriction { MaxHeightCm = 370, MaxWeightC = 1200, Exceeded = LimitKind.Height | LimitKind.Weight };
            Assert.AreEqual("wysokość do 3,7 m, masa do 12 t", NavText.Describe(r));
            r.Exceeded = LimitKind.Weight;
            Assert.AreEqual("masa do 12 t", NavText.Describe(r));
            foreach (char c in NavText.Restriction + NavText.RestrictionIn + NavText.RestrictionHere + NavText.Metres + NavText.Tonnes)
            {
                Assert.GreaterOrEqual(NavText.Charset.IndexOf(c), 0, "GPS charset has '" + c + "'");
                Assert.GreaterOrEqual(Game.UI.CabDisplays.CabDisplayText.Charset.IndexOf(c), 0, "cab screen charset has '" + c + "'");
            }
        }
    }
}
