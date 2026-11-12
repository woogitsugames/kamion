// Graph quality report (M35 extension c): unnamed edges, suspicious turn restrictions, roundabouts without oneway.
// Numbers verified against the Python reader (tools/worldgen/navgraph/build_route_graph.py parse) of the same file.
using Game.Core.Navigation;
using NavRunner.Sim;
using Xunit;

namespace NavRunner.Tests
{
    public class GraphQualityTests
    {
        const string Region = "bialystok-industrial-c";

        [Fact]
        public void Region_Report_MatchesPythonReader()
        {
            var g = RouteGraph.Load(Region);
            Assert.NotNull(g);
            var r = GraphReport.Scan(g);
            Assert.Equal(646, g.EdgeCount);
            Assert.Equal(412, r.UnnamedEdges);                 // 412 of 646 edges have no street name (service roads, arms)
            Assert.Equal(22, r.NoTruckEdges);                  // access=no / hgv=no / emergency_access
            Assert.Equal(72, r.RestrictedEdges);               // private/destination/driveway (600 s penalty)
            Assert.Equal(277, r.OnewayEdges);
            Assert.Equal(12, r.RoundaboutEdges);               // 2 rings: Putry (4) + Pamięci Bieżeństwa (8)
            Assert.Equal(0, r.RoundaboutWithoutOneway);        // every ring edge is oneway (OSM junction=roundabout implies it)
            Assert.Equal(7, r.RestrictionsNo + r.RestrictionsOnly);
            Assert.Equal(6, r.RestrictionsNo);
            Assert.Equal(1, r.RestrictionsOnly);
            Assert.Equal(0, r.RestrictionsOutOfRange);
            Assert.Empty(r.SuspiciousRestrictions);
            string text = r.ToText(g);
            Assert.Contains("unnamed edges: 412", text);
            Assert.Contains("roundabout without oneway: 0", text);
        }

        [Fact]
        public void Synthetic_SuspiciousRestrictionDetected()
        {
            var g = new RouteGraph();
            g.Names = new[] { "" };
            g.NodePos = new[] { new UnityEngine.Vector2(0, 0), new UnityEngine.Vector2(100, 0) };
            g.NodeFlags = new byte[2];
            g.EdgeFrom = new[] { 0 }; g.EdgeTo = new[] { 1 };
            g.EdgeLength = new[] { 100f }; g.EdgeClass = new byte[1]; g.EdgeFlags = new byte[1];
            g.EdgeName = new ushort[1]; g.EdgeMaxSpeed = new byte[1]; g.EdgeMaxSpeedOsm = new bool[1];
            g.EdgeStart = new[] { 0, 2 };
            g.Points = new[] { new UnityEngine.Vector2(0, 0), new UnityEngine.Vector2(100, 0) };
            g.BuildAdjacency();
            // via node 99 does not exist
            g.RestrFrom = new[] { 0 }; g.RestrVia = new[] { 99 }; g.RestrTo = new[] { 0 }; g.RestrKind = new byte[] { 0 };
            var r = GraphReport.Scan(g);
            Assert.Equal(1, r.RestrictionsOutOfRange);
            Assert.Single(r.SuspiciousRestrictions);
            Assert.Contains("out of range", r.SuspiciousRestrictions[0]);
        }
    }
}
