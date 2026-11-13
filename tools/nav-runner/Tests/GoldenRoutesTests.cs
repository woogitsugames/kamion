// Golden routes (M35): >= 30 start->goal pairs of the region with the expected manoeuvre sequence and length,
// recorded in Golden/golden_routes.json (each pair justified there; source of truth = the region KRTG graph / OSM,
// NOT Google). The test plans the pair with the real RoutePlanner and compares.
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using Game.Core.Navigation;
using UnityEngine;
using Xunit;

namespace NavRunner.Tests
{
    public class GoldenRoutesTests
    {
        const string Region = "bialystok-industrial-c";

        public sealed class GoldenDoc
        {
            public string region { get; set; }
            public double lengthTolM { get; set; }
            public double turnTolDeg { get; set; }
            public List<GoldenRoute> routes { get; set; }
        }
        public sealed class GoldenRoute
        {
            public string id { get; set; }
            public string label { get; set; }
            public double[] from { get; set; }
            public double[] to { get; set; }
            public string because { get; set; }
            public double lengthM { get; set; }
            public double costS { get; set; }
            public List<GoldenMan> maneuvers { get; set; }
        }
        public sealed class GoldenMan
        {
            public string type { get; set; }
            public double turnDeg { get; set; }
            public int exit { get; set; }
            public string street { get; set; }
        }

        static GoldenDoc Load()
        {
            string file = Path.Combine(System.AppContext.BaseDirectory, "golden_routes.json");
            Assert.True(File.Exists(file), "golden_routes.json next to the test assembly");
            var doc = JsonSerializer.Deserialize<GoldenDoc>(File.ReadAllText(file));
            Assert.Equal(Region, doc.region);
            return doc;
        }

        [Fact]
        public void Golden_AtLeast30Pairs()
        {
            var doc = Load();
            Assert.True(doc.routes.Count >= 30, $"at least 30 golden pairs (have {doc.routes.Count})");
            foreach (var r in doc.routes) Assert.False(string.IsNullOrWhiteSpace(r.because), r.id + " has a justification");
        }

        [Theory]
        [MemberData(nameof(GoldenCases))]
        public void Golden_MatchesPlanner(GoldenRoute r)
        {
            var doc = Load();
            var g = RouteGraph.Load(doc.region);
            Assert.NotNull(g);
            var planner = new RoutePlanner(g);
            var p = RoutePath.For(g);
            var st = planner.Plan(new Vector2((float)r.from[0], (float)r.from[1]), float.NaN, new Vector2((float)r.to[0], (float)r.to[1]), p);
            Assert.True(st == PlanStatus.Ok, $"{r.id} {r.label}: planned ({st})");
            Assert.Equal(r.lengthM, p.Length, doc.lengthTolM);
            Assert.Equal(r.maneuvers.Count, p.ManCount);
            for (int k = 0; k < p.ManCount; k++)
            {
                var m = r.maneuvers[k];
                Assert.True(p.ManType[k].ToString() == m.type, $"{r.id} man {k}: type {p.ManType[k]} != {m.type}");
                Assert.Equal(m.exit, p.ManExit[k]);
                Assert.Equal(m.street, g.Names[p.ManName[k]]);
                Assert.Equal(m.turnDeg, p.ManTurn[k], doc.turnTolDeg);
            }
            // route validity: connectivity, oneway, turn restrictions
            for (int i = 0; i < p.DirectedCount; i++)
            {
                int d = p.Directed[i], e = d >> 1;
                if (RouteGraph.Reversed(d)) Assert.False(g.IsOneway(e));
                if (i == 0) continue;
                Assert.Equal(g.EndNode(p.Directed[i - 1]), g.StartNode(d));
                Assert.True(g.TurnAllowed(p.Directed[i - 1] >> 1, g.StartNode(d), e));
            }
        }

        /// <summary>Counterfactual (integration r6): the G02 detour over Rondo Pamięci Bieżeństwa exists only because the
        /// median crossing of Andersa is flagged no-truck - without the flag the planner takes it (much shorter; ADR 0168 moved the goal before the point of no return).</summary>
        [Fact]
        public void NoTruckMedian_ForcesRoundaboutDetour()
        {
            var g = RouteGraph.Load(Region);
            var a = new Vector2(-1.7f, -897.8f); var b = new Vector2(-320f, -162f);
            var p = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, new RoutePlanner(g).Plan(a, float.NaN, b, p));
            float withBan = p.Length;
            bool ring = false;
            for (int i = 0; i < p.DirectedCount; i++) if (g.IsRoundabout(p.Directed[i] >> 1)) ring = true;
            Assert.True(ring, "G02 turns round on a roundabout");
            for (int e = 0; e < g.EdgeCount; e++) g.EdgeFlags[e] = (byte)(g.EdgeFlags[e] & ~RouteGraph.FlagNoTruck);
            var q = RoutePath.For(g);
            Assert.Equal(PlanStatus.Ok, new RoutePlanner(g).Plan(a, float.NaN, b, q));
            Assert.True(q.Length < withBan - 1000f, $"without no-truck flags the route is much shorter ({q.Length:F0} vs {withBan:F0} m)");
        }

        public static IEnumerable<object[]> GoldenCases()
        {
            foreach (var r in Load().routes) yield return new object[] { r };
        }
    }
}
