using System.Collections.Generic;
using System.Linq;
using Game.Gameplay;
using Game.UI.Navigation;
using Game.World.Streaming;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0302: GPS route over several streamed tiles. Before it the route was planned in one tile's graph and the
    /// destination was dropped at the first seam (ADR 0300 "open"). Checks on the shipped data (nav_trips.json, the tile
    /// graph, the per-tile routing graphs): a 3-tile trip kleeberga -> knyszynska -> dk65-01 is one continuous route through
    /// the corridor seams; a tile switch keeps the goal and the remaining distance; an origin rebase moves nothing; a
    /// re-route re-plans only the truck's leg; the tracking loop on the long route allocates nothing; the whole Tykocin trip.
    /// </summary>
    public class NavTripTests
    {
        const string A = "bialystok-kleeberga", B = "bialystok-knyszynska", C = "dk65-01";
        readonly List<GameObject> m_Go = new List<GameObject>();

        [TearDown]
        public void TearDown()
        {
            foreach (var go in m_Go) if (go != null) Object.DestroyImmediate(go);
            m_Go.Clear();
            PlayerPrefs.DeleteKey(NavigationService.TripPref);
        }

        GameObject New(string n) { var g = new GameObject(n); m_Go.Add(g); return g; }

        static TileGraph Graph() { var g = TileGraph.LoadDefault(); Assert.NotNull(g); return g; }

        static (bool, double, double) Anchor(TileGraph g, string id)
        {
            int i = g.IndexOf(id);
            return i >= 0 ? (true, g.Tiles[i].anchorX, g.Tiles[i].anchorY) : (false, 0.0, 0.0);
        }

        /// <summary>The tykocin trip cut to kleeberga .. dk65-01, goal = the dk65-01 -> dk65-02 seam.</summary>
        static NavTripData ThreeTiles()
        {
            var t = NavTripsData.LoadDefault().Find("tykocin");
            Assert.NotNull(t, "Resources/Nav/nav_trips.json (tools/ui/build_nav_trips.py)");
            int a = System.Array.IndexOf(t.tiles, A);
            Assert.GreaterOrEqual(a, 0);
            Assert.AreEqual(B, t.tiles[a + 1]); Assert.AreEqual(C, t.tiles[a + 2]);
            var exit = t.joins[a + 2];   // dk65-01 -> dk65-02
            return new NavTripData
            {
                id = "test3", label = "Test", tiles = new[] { A, B, C },
                joins = new[] { t.joins[a], t.joins[a + 1] }, goalTile = C, goalX = exit.x, goalY = exit.y,
            };
        }

        static Vector2 Local(TileGraph g, string tile, double x, double y)
        {
            var t = g.Tiles[g.IndexOf(tile)];
            return new Vector2((float)(x - t.anchorX), (float)(y - t.anchorY));
        }

        static float DistToPath(Game.Core.Navigation.RoutePath p, Vector2 q)
        {
            float best = float.MaxValue;
            for (int i = 1; i < p.Count; i++)
            {
                Vector2 a = p.Points[i - 1], ab = p.Points[i] - a;
                float t = ab.sqrMagnitude > 1e-8f ? Mathf.Clamp01(Vector2.Dot(q - a, ab) / ab.sqrMagnitude) : 0f;
                best = Mathf.Min(best, (q - (a + ab * t)).magnitude);
            }
            return best;
        }

        /// <summary>Truck standing at the kleeberga entry (seam with maczka) heading west, GPS in kleeberga (frame = A root).</summary>
        NavigationService Setup(TileGraph g, out Transform rootA, out Transform rootB, out Transform truck, out Vector2 start)
        {
            var src = NavTripsData.LoadDefault().Find("tykocin");
            var entry = src.joins[System.Array.IndexOf(src.tiles, A) - 1];   // maczka -> kleeberga
            start = Local(g, A, entry.x, entry.y) + NavTrip.SideDir(entry.side) * 10f;
            rootA = New("A").transform;
            rootB = New("B").transform;
            var ta = g.Tiles[g.IndexOf(A)]; var tb = g.Tiles[g.IndexOf(B)];
            rootB.position = new Vector3((float)(tb.anchorX - ta.anchorX), 0f, (float)(tb.anchorY - ta.anchorY));
            truck = New("truck").transform;
            truck.position = new Vector3(start.x, 0f, start.y);
            truck.rotation = Quaternion.Euler(0f, 270f, 0f);   // west
            var nav = NavigationService.Install(New("nav"), truck, null, rootA, A);
            Assert.IsTrue(nav.Ready);
            return nav;
        }

        [Test]
        public void TripDataJoinsLieOnTheSeamsAndGoalsInTheLastTile()
        {
            var g = Graph();
            var d = NavTripsData.LoadDefault();
            Assert.AreEqual(NavTripsData.ResourcePath, "Nav/nav_trips");
            foreach (var id in new[] { "tykocin", "monki", "s8" })
            {
                var t = d.Find(id);
                Assert.NotNull(t, id);
                Assert.AreEqual(t.tiles.Length - 1, t.joins.Length, id);
                for (int i = 0; i < t.joins.Length; i++)
                {
                    var j = t.joins[i];
                    int a = g.IndexOf(j.from), b = g.IndexOf(j.to);
                    Assert.GreaterOrEqual(a, 0, j.from); Assert.GreaterOrEqual(b, 0, j.to);
                    Assert.Less(g.DistanceTo(a, j.x, j.y), 1.0, $"{id}: join {j.from}->{j.to} on the seam (tile {j.from})");
                    Assert.Less(g.DistanceTo(b, j.x, j.y), 1.0, $"{id}: join {j.from}->{j.to} on the seam (tile {j.to})");
                    Assert.NotNull(Game.Core.Navigation.RouteGraph.Load(j.from), j.from);
                }
                int last = g.IndexOf(t.goalTile);
                Assert.AreEqual(t.tiles[t.tiles.Length - 1], t.goalTile);
                Assert.IsTrue(g.Contains(last, t.goalX, t.goalY, 1.0), $"{id}: goal inside {t.goalTile}");
            }
            Assert.AreEqual(28, d.Find("tykocin").tiles.Length);
        }

        [Test]
        public void ThreeTileTripIsOneContinuousRouteThroughTheSeams()
        {
            var g = Graph();
            var nav = Setup(g, out _, out _, out _, out Vector2 start);
            var data = ThreeTiles();
            var trip = new NavTrip(data, id => Anchor(g, id));
            Assert.IsFalse(trip.Failed, trip.FailReason);
            var ta = g.Tiles[g.IndexOf(A)];
            nav.StartTrip(trip, ta.anchorX, ta.anchorY, remember: false);
            int steps = nav.StepTripForTest();
            Assert.AreEqual(3, steps, "one leg per frame");
            Assert.IsTrue(trip.PlanDone);
            Assert.IsFalse(trip.Failed, trip.FailReason);
            Assert.AreEqual(3, trip.PlannedCount);
            var p = nav.Path;
            Assert.AreSame(trip.Combined, p);
            Assert.IsTrue(p.HasRoute);
            Debug.Log($"[TEST] 3-tile trip: {p.Length:F0} m, {p.Count} points, {p.ManCount} manoeuvres, planning {trip.TotalPlanMs:F1} ms, ETA {nav.Guidance.RemainingSeconds:F0} s");

            float maxGap = 0f;
            for (int i = 1; i < p.Count; i++) maxGap = Mathf.Max(maxGap, (p.Points[i] - p.Points[i - 1]).magnitude);
            Assert.Less(maxGap, 2f * NavTrip.SeamInsetM + 60f, "no jump in the polyline (seam join = straight inset bridge)");
            foreach (var j in data.joins)
            {
                float d = DistToPath(p, Local(g, A, j.x, j.y));
                Assert.Less(d, 2f * NavTrip.SeamInsetM, $"route crosses the seam {j.from}|{j.to} at the corridor join (got {d:F1} m)");
            }
            Assert.Less((p.Points[0] - start).magnitude, 30f, "starts at the truck");
            Assert.Less((p.Destination - Local(g, A, data.goalX, data.goalY)).magnitude, 10f, "ends at the goal (in A's frame)");
            Assert.Greater(p.Length, (Local(g, A, data.goalX, data.goalY) - start).magnitude, "longer than the straight line");

            var gd = nav.Guidance;
            Assert.IsTrue(gd.HasRoute && gd.OnRoute);
            Assert.AreEqual(p.Length, gd.RemainingM, 30f);
            // ETA from the speed limits: between 80 km/h (truck max) and 20 km/h average
            Assert.Greater(gd.RemainingSeconds, p.Length / (80f / 3.6f));
            Assert.Less(gd.RemainingSeconds, p.Length / (20f / 3.6f));
            Assert.AreEqual("Test", nav.NameOf(p.DestinationName));
            Assert.AreEqual(1, p.ManCount - Enumerable.Range(0, p.ManCount).Count(k => p.ManType[k] != Game.Core.Navigation.Maneuver.Arrive), "only one arrival (the goal), none on the seams");
        }

        [Test]
        public void SeamSwitchKeepsTheGoalAndRebaseMovesNothing()
        {
            var g = Graph();
            var nav = Setup(g, out var rootA, out var rootB, out var truck, out _);
            var trip = new NavTrip(ThreeTiles(), id => Anchor(g, id));
            var ta = g.Tiles[g.IndexOf(A)]; var tb = g.Tiles[g.IndexOf(B)];
            nav.StartTrip(trip, ta.anchorX, ta.anchorY, remember: false);
            nav.StepTripForTest();
            var p = nav.Path;
            // a route point 150 m past the A|B seam (A frame)
            var seam = Local(g, A, ThreeTiles().joins[0].x, ThreeTiles().joins[0].y);
            int k0 = 0; float best = float.MaxValue;
            for (int i = 0; i < p.Count; i++) { float d = (p.Points[i] - seam).sqrMagnitude; if (d < best) { best = d; k0 = i; } }
            int k = k0; while (k < p.Count - 1 && p.S[k] < p.S[k0] + 150f) k++;
            Vector2 q = p.Points[k], dir = (p.Points[k] - p.Points[k - 1]).normalized;
            truck.position = new Vector3(q.x, 0f, q.y);
            truck.rotation = Quaternion.LookRotation(new Vector3(dir.x, 0f, dir.y));
            nav.StepForTest(q, Mathf.Atan2(dir.x, dir.y) * Mathf.Rad2Deg, 14f, 0.1f);
            float remBefore = nav.Guidance.RemainingM;
            Vector2 goalB = trip.GoalIn(tb.anchorX, tb.anchorY);

            var oldToNew = new Vector2((float)(ta.anchorX - tb.anchorX), (float)(ta.anchorY - tb.anchorY));
            Assert.IsTrue(nav.SwitchRegion(B, rootB, oldToNew));
            Assert.AreSame(trip, nav.Trip, "trip kept across the seam");
            Assert.AreEqual(1, trip.Current);
            Assert.IsTrue(nav.HasPin);
            Assert.Less((nav.Pin - goalB).magnitude, 0.01f, "goal re-expressed in B's frame");
            Assert.AreEqual(tb.anchorX, nav.AnchorX, 0.01); Assert.AreEqual(tb.anchorY, nav.AnchorY, 0.01);
            nav.SampleForTest();
            var qb = q + oldToNew;
            Assert.Less((nav.Position - qb).magnitude, 0.01f);
            nav.StepForTest(nav.Position, Mathf.Atan2(dir.x, dir.y) * Mathf.Rad2Deg, 14f, 0.1f);
            Assert.IsTrue(nav.Guidance.OnRoute, "on the recomposed route in B's frame");
            Assert.AreEqual(remBefore, nav.Guidance.RemainingM, 2f, "remaining distance continuous across the switch");
            Assert.Less(nav.Path.Points[0].x - qb.x, 2100f, "the path starts in B's leg (A's leg dropped)");

            // origin rebase: roots and truck shift together
            var shift = new Vector3(-2048f, 0f, 1024f);
            foreach (var t in new[] { rootA, rootB, truck }) t.position += shift;
            nav.SampleForTest();
            Assert.Less((nav.Position - qb).magnitude, 0.01f, "no jump after a rebase");
            nav.StepForTest(nav.Position, Mathf.Atan2(dir.x, dir.y) * Mathf.Rad2Deg, 14f, 0.1f);
            Assert.AreEqual(remBefore, nav.Guidance.RemainingM, 2f);
        }

        [Test]
        public void RerouteReplansOnlyTheTrucksLegAndKeepsTheGoal()
        {
            var g = Graph();
            var nav = Setup(g, out _, out _, out _, out Vector2 start);
            var trip = new NavTrip(ThreeTiles(), id => Anchor(g, id));
            var ta = g.Tiles[g.IndexOf(A)];
            nav.StartTrip(trip, ta.anchorX, ta.anchorY, remember: false);
            nav.StepTripForTest();
            Vector2 dest = nav.Path.Destination;
            double planned1 = trip.Legs[1].PlanMs, planned2 = trip.Legs[2].PlanMs;
            int v = nav.Path.Version;
            // the truck is on a road 150 m along the route, then re-route from there (as after leaving the route)
            var p = nav.Path;
            int k = 0; while (k < p.Count - 1 && p.S[k] < 150f) k++;
            nav.StepForTest(p.Points[k], 270f, 10f, 0.1f);
            nav.ReplanTripLegForTest();
            Assert.AreSame(trip, nav.Trip);
            Assert.AreNotEqual(v, nav.Path.Version, "recomposed");
            Assert.Less((nav.Path.Destination - dest).magnitude, 0.5f, "same goal");
            Assert.AreEqual(planned1, trip.Legs[1].PlanMs, "leg 2 not re-planned");
            Assert.AreEqual(planned2, trip.Legs[2].PlanMs, "leg 3 not re-planned");
            Assert.AreEqual(1, nav.RerouteCount);
        }

        [Test]
        public void TrackingTheLongRouteAllocatesNothing()
        {
            var g = Graph();
            var nav = Setup(g, out _, out _, out _, out _);
            var trip = new NavTrip(NavTripsData.LoadDefault().Find("tykocin"), id => Anchor(g, id));
            var ta = g.Tiles[g.IndexOf(A)];
            nav.StartTrip(trip, ta.anchorX, ta.anchorY, remember: false);
            nav.StepTripForTest();
            Assert.IsFalse(trip.Failed, trip.FailReason);
            var p = nav.Path;
            // drive along the route 1 m per step (warm-up first: JIT, first ETA)
            for (int i = 0; i < 50; i++) nav.StepForTest(p.Points[Mathf.Min(i, p.Count - 1)], 270f, 14f, 0.02f);
            long a0 = System.GC.GetAllocatedBytesForCurrentThread();
            var sw = System.Diagnostics.Stopwatch.StartNew();
            int n = 0;
            for (int i = 50; i < Mathf.Min(p.Count, 3050); i++, n++)
            {
                Vector2 d = p.Points[i] - p.Points[i - 1];
                nav.StepForTest(p.Points[i], Mathf.Atan2(d.x, d.y) * Mathf.Rad2Deg, 14f, 0.02f);
            }
            sw.Stop();
            long a1 = System.GC.GetAllocatedBytesForCurrentThread();
            Debug.Log($"[TEST] tracking on the {p.Length:F0} m trip ({p.Count} points): {sw.Elapsed.TotalMilliseconds * 1000.0 / n:F1} us/step over {n} steps, {a1 - a0} B allocated");
            Assert.AreEqual(0, a1 - a0, "zero GC in the driving loop");
        }

        [Test]
        public void WholeTykocinTripFromKleeberga()
        {
            var g = Graph();
            var nav = Setup(g, out _, out _, out _, out Vector2 start);
            var data = NavTripsData.LoadDefault().Find("tykocin");
            var trip = new NavTrip(data, id => Anchor(g, id));
            var ta = g.Tiles[g.IndexOf(A)];
            nav.StartTrip(trip, ta.anchorX, ta.anchorY, remember: false);
            Assert.AreEqual(2, trip.Current, "kleeberga = 3rd tile of the corridor");
            int steps = nav.StepTripForTest();
            Assert.IsFalse(trip.Failed, trip.FailReason);
            Assert.AreEqual(data.tiles.Length - 2, steps);
            var p = nav.Path;
            float straight = (Local(g, A, data.goalX, data.goalY) - start).magnitude;
            Debug.Log($"[TEST] tykocin trip from {A}: {p.Length:F0} m (straight {straight:F0} m), {p.Count} points, {p.ManCount} manoeuvres, " +
                      $"planning {trip.TotalPlanMs:F1} ms over {steps} frames (max leg {trip.Legs.Max(l => l.PlanMs):F2} ms), ETA {nav.Guidance.RemainingSeconds / 60f:F1} min");
            Assert.Greater(p.Length, straight);
            Assert.Less(p.Length, 2f * straight);
            for (int i = 2; i < data.joins.Length; i++)
            {
                var j = data.joins[i];
                Assert.Less(DistToPath(p, Local(g, A, j.x, j.y)), 2f * NavTrip.SeamInsetM, $"join {j.from}|{j.to}");
            }
        }

        [Test]
        public void TripChoiceRouteToThenRememberedThenStreamer()
        {
            Assert.AreEqual("monki", NavStreamFollower.ChooseTrip(new[] { "Kamion.exe", "-route_to", "monki" }, "s8", "tykocin"));
            Assert.AreEqual("s8", NavStreamFollower.ChooseTrip(new[] { "Kamion.exe" }, "s8", "tykocin"));
            Assert.IsNull(NavStreamFollower.ChooseTrip(new[] { "Kamion.exe" }, "-", "tykocin"));
            Assert.AreEqual("tykocin", NavStreamFollower.ChooseTrip(new[] { "Kamion.exe" }, "", "tykocin"));
            Assert.AreEqual("tykocin", NavStreamFollower.ChooseTrip(System.Array.Empty<string>(), "", null));
        }

        [Test]
        public void MapPinEndsTheTripAndClearForgetsIt()
        {
            var g = Graph();
            var nav = Setup(g, out _, out _, out _, out Vector2 start);
            var ta = g.Tiles[g.IndexOf(A)];
            nav.StartTrip(new NavTrip(ThreeTiles(), id => Anchor(g, id)), ta.anchorX, ta.anchorY);
            Assert.AreEqual("test3", PlayerPrefs.GetString(NavigationService.TripPref));
            nav.SetPin(start + new Vector2(-200f, 0f));
            Assert.IsNull(nav.Trip, "a pin from the map replaces the trip");
            nav.StartTrip(new NavTrip(ThreeTiles(), id => Anchor(g, id)), ta.anchorX, ta.anchorY);
            nav.ClearRoute();
            Assert.IsNull(nav.Trip);
            Assert.IsFalse(nav.HasPin);
            Assert.AreEqual("-", PlayerPrefs.GetString(NavigationService.TripPref), "cleared = remembered as none");
        }
    }
}
