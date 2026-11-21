// Build #3 (s24) P2 GPS: "zawroc" 580/330/70 m on al. Tysiaclecia (DK8, tile bialystok-industrial-c) at t=180-240 s,
// three trip re-routes (the last one +1.5 km). Diagnosis (gps-dk8-s24): the route autopilot drives the C control route
// (route_start.json: depot -> DK8/DK19 northbound, ends ~330 m before the north seam) + the after_route link
// c-dk8-to-maczka, which turns round over the median crossover at (-821, 861) and comes back south to the Maczka seam.
// The GPS leg 1 of trip tykocin turns west at the DK8/DK19 junction (~(-540, 50)); once the truck passes that junction
// northbound, the destination is behind it and every re-plan correctly asks for a U-turn. These tests pin both halves:
// the GPS leg itself is stable and U-turn free, and the control path disagrees with it (data, not the planner).
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using Game.Core.Navigation;
using UnityEngine;
using Xunit;

namespace NavRunner.Tests
{
    public class NavTripDk8MaczkaTests
    {
        const string Region = "bialystok-industrial-c";
        /// <summary>Exit of trip tykocin leg 1 (nav_trips.json join C | Maczka, x 776970.83 y 596281.056, side W, inset
        /// NavTrip.SeamInsetM = 3 m) in C-local metres (origin 777995 / 596223).</summary>
        static readonly Vector2 k_Exit = new Vector2(-1021.17f, 58.056f);
        /// <summary>Truck spawn of build #3 ([START] route_s=12.0 en=729.5,-395.7), heading along the start route.</summary>
        static readonly Vector2 k_Start = new Vector2(729.5f, -395.7f);

        static string Root => Path.GetFullPath(Path.Combine(Application.dataPath, "..", ".."));

        static bool HasUTurn(RoutePath p)
        {
            for (int k = 0; k < p.ManCount; k++) if (p.ManType[k] == Maneuver.UTurn) return true;
            return false;
        }

        /// <summary>Truck heading at point i: chord to the first point >= 8 m ahead (a real truck has no heading of a 0.5 m
        /// polyline kink at a junction node).</summary>
        static float HeadingAlong(RoutePath p, int i)
        {
            int j = i + 1;
            while (j < p.Count - 1 && p.S[j] - p.S[i] < 8f) j++;
            Vector2 d = p.Points[j] - p.Points[i];
            return Mathf.Atan2(d.x, d.y) * Mathf.Rad2Deg;
        }

        /// <summary>Autopilot path of build #3 in C: route_start.json points + link c-dk8-to-maczka (route_links.json).</summary>
        static List<Vector2> ControlPath()
        {
            var pts = new List<Vector2>();
            using (var d = JsonDocument.Parse(File.ReadAllText(Path.Combine(Root, "Data", "Regions", Region, "route_start.json"))))
                foreach (var p in d.RootElement.GetProperty("points_en").EnumerateArray()) pts.Add(new Vector2(p[0].GetSingle(), p[1].GetSingle()));
            string links = Path.Combine(Root, "game", "Assets", "_Project", "World", "Runtime", "Streaming", "Resources", "WorldStreaming", "route_links.json");
            using (var d = JsonDocument.Parse(File.ReadAllText(links)))
                foreach (var l in d.RootElement.GetProperty("links").EnumerateArray())
                {
                    if (l.GetProperty("id").GetString() != "c-dk8-to-maczka") continue;
                    var e = l.GetProperty("e"); var n = l.GetProperty("n");
                    for (int i = 0; i < e.GetArrayLength(); i++) pts.Add(new Vector2(e[i].GetSingle(), n[i].GetSingle()));
                }
            return pts;
        }

        [Fact]
        public void Leg1_FollowingTheGpsRoute_NoUTurnNoRerouteAndNoDetour()
        {
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g) { AllowTileExit = true };   // as NavTrip.PlanLeg
            var leg = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(k_Start, -152f, k_Exit, leg));
            Assert.False(HasUTurn(leg), "leg 1 from the depot has no U-turn");
            Assert.True(leg.Length < 2300f, $"leg 1 {leg.Length:F0} m: west at the DK8/DK19 junction, no loop to the north seam");
            float maxN = float.MinValue;
            for (int i = 0; i < leg.Count; i++) maxN = Mathf.Max(maxN, leg.Points[i].y);
            Assert.True(maxN < 150f, $"leg 1 never drives north of the DK8/DK19 junction (max N {maxN:F0} m)");

            // A driver following the GPS: track every point, re-plan from it (as the trip re-route would) - same route,
            // never a U-turn, never a re-route request, remaining length only decreasing.
            var tracker = new RouteTracker();
            var gd = new NavGuidance();
            var q = RoutePath.For(g);
            float last = float.MaxValue;
            for (int i = 0; i < leg.Count - 2 && leg.Length - leg.S[i] > 10f; i += 2)   // last metres: AlreadyThere (NavTrip: Ok)
            {
                float hd = HeadingAlong(leg, i);
                tracker.Update(leg, leg.Points[i], hd, 13f, 0.5f, ref gd);
                Assert.False(gd.NeedsReroute, $"no re-route at point {i}");
                Assert.Equal(PlanStatus.Ok, planner.Plan(leg.Points[i], hd, k_Exit, q));
                Assert.False(HasUTurn(q), $"re-plan at point {i} {leg.Points[i]} has no U-turn");
                Assert.True(q.Length <= last + 5f, $"re-plan at point {i}: {q.Length:F0} m after {last:F0} m (no detour)");
                last = q.Length;
            }
        }

        [Fact]
        public void Reroute_AtJunctionNode_StartsOnTheEdgeAlongTheHeading()
        {
            // Junction node on leg 1 (Andersa westbound): every edge is 0 m away; the nearest-edge tie went to a one-way
            // slip road ~63 deg off the heading and the re-plan asked for a U-turn (fixed: RoutePlanner start snap).
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g) { AllowTileExit = true };
            var node = new Vector2(81.178f, -454.167f);
            float heading = -62f;
            var hv = new Vector2(Mathf.Sin(heading * Mathf.Deg2Rad), Mathf.Cos(heading * Mathf.Deg2Rad));
            int nearest = g.Snap(node, RoutePlanner.SnapStartM, out float along, out _, out _);
            Assert.True(Vector2.Dot(g.DirectionAt(nearest * 2, along, 8f), hv) < RoutePlanner.SnapHeadingMinCos,
                "distance alone picks the slip road at the node");
            var q = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(node, heading, k_Exit, q));
            Assert.True(Vector2.Dot(g.DirectionAt(q.Directed[0], 0f, 8f), hv) >= RoutePlanner.SnapHeadingMinCos,
                "the re-plan starts on the edge along the heading");
            Assert.False(HasUTurn(q), "no false U-turn");
            Assert.True(q.Length < 1300f, $"{q.Length:F0} m: straight on to the seam");
            GcAllocCounter.AssertZero(() => planner.Plan(node, heading, k_Exit, q), message: "re-plan allocates nothing");
        }

        [Fact]
        public void ControlPath_BeforeTheDk8Junction_AgreesWithTheGps()
        {
            // Up to the DK8/DK19 junction the autopilot path IS the GPS route: re-plans from it have no U-turn.
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g) { AllowTileExit = true };
            var q = RoutePath.For(g);
            var pts = ControlPath();
            Assert.True(pts.Count > 1500, "route_start + link loaded");
            for (int i = 0; i + 1 < pts.Count && pts[i].y < 30f; i += 5)
            {
                Vector2 d = pts[i + 1] - pts[i];
                if (d.sqrMagnitude < 1e-4f) continue;
                Assert.Equal(PlanStatus.Ok, planner.Plan(pts[i], Mathf.Atan2(d.x, d.y) * Mathf.Rad2Deg, k_Exit, q));
                Assert.False(HasUTurn(q), $"before the junction, point {i} {pts[i]}: no U-turn");
            }
        }

        [Fact(Skip = "Known data defect (build #3 P2, gps-dk8-s24): the C control route + after_route link c-dk8-to-maczka " +
                     "drive north past the DK8/DK19 junction and turn round over the median at (-821, 861), ~1.5 km more than " +
                     "the GPS leg. Needs a branching / replacing link from the C route start (route_links.yaml + WorldStreamer " +
                     "start-tile replace). Un-skip when fixed.")]
        public void ControlPath_ForTripTykocin_HasNoUTurnAndNoDetour()
        {
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g) { AllowTileExit = true };
            var q = RoutePath.For(g);
            var pts = ControlPath();
            float len = 0f;
            for (int i = 0; i + 1 < pts.Count; i++) len += Vector2.Distance(pts[i], pts[i + 1]);
            var leg = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(k_Start, -152f, k_Exit, leg));
            Assert.True(len < leg.Length + 300f, $"control path {len:F0} m vs GPS leg {leg.Length:F0} m");
            for (int i = 0; i + 1 < pts.Count - 20; i += 10)
            {
                Vector2 d = pts[i + 1] - pts[i];
                if (d.sqrMagnitude < 1e-4f) continue;
                Assert.Equal(PlanStatus.Ok, planner.Plan(pts[i], Mathf.Atan2(d.x, d.y) * Mathf.Rad2Deg, k_Exit, q));
                Assert.False(HasUTurn(q), $"point {i} {pts[i]}: no U-turn");
            }
        }
    }
}
