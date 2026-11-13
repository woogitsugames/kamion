// Off-route detection and re-planning scenarios (M35 extension b), driven on the region graph with RouteTracker:
// driving along the route, a side deviation, driving against the route, and the re-plan from the off position.
using Game.Core.Navigation;
using UnityEngine;
using Xunit;

namespace NavRunner.Tests
{
    public class RerouteScenarioTests
    {
        const string Region = "bialystok-industrial-c";
        static readonly Vector2 k_A = new Vector2(-1.7f, -897.8f);
        static readonly Vector2 k_B = new Vector2(-172f, -298f);

        static float HeadingAlong(RoutePath p, int i)
        {
            Vector2 d = p.Points[System.Math.Min(i + 1, p.Count - 1)] - p.Points[i];
            return d.sqrMagnitude > 1e-6f ? Mathf.Atan2(d.x, d.y) * Mathf.Rad2Deg : 0f;
        }

        [Fact]
        public void Scenario_DriveAlongRoute_NoReroute()
        {
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(k_A, float.NaN, k_B, p));
            var tr = new RouteTracker();
            var gd = new NavGuidance();
            for (int i = 0; i < p.Count; i += 3)
            {
                tr.Update(p, p.Points[i], HeadingAlong(p, i), 10f, 0.1f, ref gd);
                Assert.True(gd.OnRoute, $"on route at point {i}");
                Assert.False(gd.NeedsReroute);
                Assert.True(gd.OffRouteM < 1f);
            }
            tr.Update(p, p.Points[p.Count - 1], HeadingAlong(p, p.Count - 1), 1f, 0.1f, ref gd);
            Assert.True(gd.Arrived);
        }

        [Fact]
        public void Scenario_SideDeviation_TriggersRerouteAndReplan()
        {
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(k_A, float.NaN, k_B, p));
            var tr = new RouteTracker();
            var gd = new NavGuidance();
            int i0 = p.Count / 3;
            Vector2 at = p.Points[i0];
            Vector2 dir = (p.Points[i0 + 1] - at).normalized;
            float heading = Mathf.Atan2(dir.x, dir.y) * Mathf.Rad2Deg;
            tr.Update(p, at, heading, 10f, 0.1f, ref gd);
            Assert.True(gd.OnRoute);

            Vector2 off = at + new Vector2(dir.y, -dir.x) * 40f;   // 40 m beside the route
            bool rerouteAsked = false;
            for (int i = 0; i < 60 && !rerouteAsked; i++)
            {
                tr.Update(p, off, heading, 10f, 0.1f, ref gd);
                rerouteAsked = gd.NeedsReroute;
            }
            Assert.True(rerouteAsked, "after 2.5 s off the route the tracker asks for a re-plan");

            var q = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(off, heading, p.Destination, q));
            Assert.True(Vector2.Distance(q.Points[0], off) < RoutePlanner.SnapStartM + 1f, "the new route starts at the truck");
            tr.ClearOffRoute();
            tr.Update(q, q.Points[0], heading, 10f, 0.1f, ref gd);
            Assert.False(gd.NeedsReroute, "after the re-plan the tracker is on the new route");
            Assert.True(gd.OnRoute);
        }

        [Fact]
        public void Scenario_DrivingAgainstRoute_TriggersReroute()
        {
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(k_A, float.NaN, k_B, p));
            var tr = new RouteTracker();
            var gd = new NavGuidance();
            int i0 = p.Count / 2;
            Vector2 at = p.Points[i0];
            float heading = HeadingAlong(p, i0);
            float back = (heading + 180f) % 360f;   // driving against the route
            bool rerouteAsked = false;
            for (int i = 0; i < 60 && !rerouteAsked; i++)
            {
                tr.Update(p, at, back, 10f, 0.1f, ref gd);
                rerouteAsked = gd.NeedsReroute;
            }
            Assert.True(rerouteAsked, "driving against the route for 2.5 s asks for a re-plan");
        }

        [Fact]
        public void Scenario_FailedReplan_KeepsCurrentRoute()
        {
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(k_A, float.NaN, k_B, p));
            int v = p.Version;
            // start 5 km away: no road within the snap distance
            var st = planner.Plan(new Vector2(5000f, 5000f), float.NaN, k_B, p);
            Assert.Equal(PlanStatus.StartOffRoad, st);
            Assert.True(p.HasRoute && p.Version == v, "a failed re-plan keeps the current route");
        }
    }
}
