// Roundabout exit numbers (M35 point 4): Maneuver.Roundabout carries the exit number (counted in the driving
// direction, vehicle-accessible exits only) and the guidance state exposes it (NavGuidance.NextExit) without GC
// allocation. Tested on the two region roundabouts: Rondo Putry and Rondo Pamięci Bieżeństwa.
using Game.Core.Navigation;
using UnityEngine;
using Xunit;

namespace NavRunner.Tests
{
    public class RoundaboutExitTests
    {
        const string Region = "bialystok-industrial-c";

        // Anchors (region metres): Andersa near Rondo Putry, Kombatantów, Andersa NW carriageway, Rondo Putry ring.
        static readonly Vector2 k_Andersa = new Vector2(-225.64f, -239.35f);
        static readonly Vector2 k_Kombatantow = new Vector2(-1.7f, -897.8f);
        static readonly Vector2 k_AndersaNW = new Vector2(-457.95f, -55.97f);
        static readonly Vector2 k_PutryRing = new Vector2(-555.60f, -10.18f);

        static int RoundaboutMan(RoutePath p)
        {
            for (int k = 0; k < p.ManCount; k++) if (p.ManType[k] == Maneuver.Roundabout) return k;
            return -1;
        }

        [Fact]
        public void Putry_Exit2ToTysiaclecia()
        {
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(k_Andersa, float.NaN, new Vector2(-205.02f, -854.88f), p));
            int k = RoundaboutMan(p);
            Assert.True(k >= 0, "route enters Rondo Putry");
            Assert.Equal(2, p.ManExit[k]);
            Assert.Equal("Aleja Tysiąclecia Państwa Polskiego", g.Names[p.ManName[k]]);
        }

        [Fact]
        public void Putry_ExitToRingGoal()
        {
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(k_Andersa, float.NaN, k_PutryRing, p));
            int k = RoundaboutMan(p);
            Assert.True(k >= 0);
            Assert.Equal(2, p.ManExit[k]);
            Assert.Equal("Rondo Krzysztofa Jakuba Putry Wicemarszałka Sejmu RP", g.Names[p.ManName[k]]);
        }

        [Fact]
        public void Biezenstwa_Exit4TurnsRoundToAndersaNW()
        {
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(k_Kombatantow, float.NaN, k_AndersaNW, p));
            int k = RoundaboutMan(p);
            Assert.True(k >= 0, "route enters Rondo Pamięci Bieżeństwa");
            Assert.Equal(4, p.ManExit[k]);
            Assert.True(Mathf.Abs(p.ManTurn[k]) > 150f, "turns round (almost U-turn) at the roundabout");
            Assert.Equal("Generała Władysława Andersa", g.Names[p.ManName[k]]);
        }

        [Fact]
        public void GuidanceState_ExposesNextExit_WithoutAllocation()
        {
            var g = RouteGraph.Load(Region);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, planner.Plan(k_Andersa, float.NaN, new Vector2(-205.02f, -854.88f), p));
            int k = RoundaboutMan(p);
            Assert.True(k >= 0);
            var tr = new RouteTracker();
            var gd = new NavGuidance();
            // warm-up (JIT)
            tr.Update(p, p.Points[0], 0f, 10f, 0.02f, ref gd);
            long before = System.GC.GetAllocatedBytesForCurrentThread();
            byte seen = 0;
            for (int i = 0; i < p.Count && seen == 0; i++)
            {
                tr.Update(p, p.Points[i], 0f, 10f, 0.02f, ref gd);
                if (gd.Next == k) seen = gd.NextExit;
            }
            long bytes = System.GC.GetAllocatedBytesForCurrentThread() - before;
            Assert.Equal(0, bytes);
            Assert.Equal(2, seen);
        }
    }
}
