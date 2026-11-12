// ETA from OSM speed limits + the PL truck profile (M35 extension a): 80/70/50 km/h
// (art. 20 ustawy Prawo o ruchu drogowym, Dz.U. 1997 nr 98 poz. 602 - quoted, UNVERIFIED in this session).
using Game.Core.Navigation;
using UnityEngine;
using Xunit;

namespace NavRunner.Tests
{
    public class NavEtaTests
    {
        [Fact]
        public void TruckSpeed_Profile80_70_50()
        {
            Assert.Equal(50f, NavEta.TruckSpeedKmh(0, 0));    // service: built-up
            Assert.Equal(50f, NavEta.TruckSpeedKmh(1, 0));    // residential/tertiary: built-up
            Assert.Equal(70f, NavEta.TruckSpeedKmh(2, 0));    // secondary: outside built-up
            Assert.Equal(80f, NavEta.TruckSpeedKmh(3, 0));    // primary/trunk: expressway
            Assert.Equal(30f, NavEta.TruckSpeedKmh(3, 30));   // OSM limit below the profile caps it
            Assert.Equal(80f, NavEta.TruckSpeedKmh(3, 90));   // OSM limit above the truck limit does not raise it
        }

        [Fact]
        public void RemainingSeconds_OnSyntheticPath()
        {
            var p = new RoutePath(8, 4);
            // Name/limit/class of a point describe the segment that STARTS at it (RoutePath), so the last point's are unused.
            p.Add(new Vector2(0, 0), 0, 0, 3);          // segment 0-100: class 3, no OSM limit -> 80 km/h
            p.Add(new Vector2(100, 0), 0, 50, 3);       // segment 100-200: OSM limit 50 caps class 3 -> 50 km/h
            p.Add(new Vector2(200, 0), 0, 0, 0);
            // full: 100 m @ 80 km/h + 100 m @ 50 km/h = 4.5 + 7.2 = 11.7 s
            Assert.Equal(11.7, NavEta.RemainingSeconds(p, 0f), 0.01);
            Assert.Equal(7.2, NavEta.RemainingSeconds(p, 100f), 0.01);
            Assert.Equal(0f, NavEta.RemainingSeconds(p, 200f), 0.01);
            Assert.Equal(0f, NavEta.RemainingSeconds(null, 0f));
        }

        [Fact]
        public void RemainingSeconds_OnRegionRoute_AndInGuidance()
        {
            var g = RouteGraph.Load("bialystok-industrial-c");
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(new Vector2(-1.7f, -897.8f), float.NaN, new Vector2(-172f, -298f), p));
            float eta0 = NavEta.RemainingSeconds(p, 0f);
            Assert.True(eta0 > 0f);
            Assert.True(eta0 < p.Length / 5f, "ETA cannot beat 5 m/s");
            float etaHalf = NavEta.RemainingSeconds(p, p.Length / 2f);
            Assert.True(etaHalf > 0f && etaHalf < eta0, "ETA shrinks along the route");

            var tr = new RouteTracker();
            var gd = new NavGuidance();
            tr.Update(p, p.Points[0], 0f, 10f, 0.02f, ref gd);
            Assert.Equal(eta0, gd.RemainingSeconds, 0.01);
        }
    }
}
