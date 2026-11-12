// Graph quality report for a KRTG region graph (M35 extension c): unnamed edges, suspicious turn restrictions,
// roundabouts without oneway, truck-forbidden / restricted edges. Used by the Runner (prints the report) and by tests.
using System.Collections.Generic;
using System.Text;
using Game.Core.Navigation;

namespace NavRunner.Sim
{
    public sealed class GraphReport
    {
        public int UnnamedEdges, NoTruckEdges, RestrictedEdges, HgvDestinationEdges, OnewayEdges, RoundaboutEdges;
        public int RoundaboutWithoutOneway, RestrictionsOutOfRange, RestrictionsNo, RestrictionsOnly;
        public readonly List<int> UnnamedEdgeIds = new List<int>();
        public readonly List<int> RoundaboutWithoutOnewayIds = new List<int>();
        public readonly List<string> SuspiciousRestrictions = new List<string>();

        public static GraphReport Scan(RouteGraph g)
        {
            var r = new GraphReport();
            for (int e = 0; e < g.EdgeCount; e++)
            {
                if (g.EdgeName[e] == 0) { r.UnnamedEdges++; r.UnnamedEdgeIds.Add(e); }
                if ((g.EdgeFlags[e] & RouteGraph.FlagNoTruck) != 0) r.NoTruckEdges++;
                if ((g.EdgeFlags[e] & RouteGraph.FlagRestricted) != 0) r.RestrictedEdges++;
                if ((g.EdgeFlags[e] & RouteGraph.FlagHgvDestination) != 0) r.HgvDestinationEdges++;
                if (g.IsOneway(e)) r.OnewayEdges++;
                if (g.IsRoundabout(e))
                {
                    r.RoundaboutEdges++;
                    if (!g.IsOneway(e)) { r.RoundaboutWithoutOneway++; r.RoundaboutWithoutOnewayIds.Add(e); }
                }
            }
            for (int i = 0; i < g.RestrFrom.Length; i++)
            {
                int f = g.RestrFrom[i], v = g.RestrVia[i], t = g.RestrTo[i];
                if (g.RestrKind[i] == 0) r.RestrictionsNo++; else r.RestrictionsOnly++;
                if (f < 0 || f >= g.EdgeCount || t < 0 || t >= g.EdgeCount || v < 0 || v >= g.NodeCount)
                {
                    r.RestrictionsOutOfRange++;
                    r.SuspiciousRestrictions.Add($"restriction {i}: from {f} via {v} to {t} out of range");
                }
                else if (g.StartNode(t) != v && g.EndNode(t) != v)
                {
                    r.SuspiciousRestrictions.Add($"restriction {i}: via node {v} is not an endpoint of to-edge {t}");
                }
                else if (g.EndNode(f) != v && g.StartNode(f) != v)
                {
                    r.SuspiciousRestrictions.Add($"restriction {i}: via node {v} is not an endpoint of from-edge {f}");
                }
            }
            return r;
        }

        public string ToText(RouteGraph g)
        {
            var sb = new StringBuilder();
            sb.AppendLine($"edges {g.EdgeCount}, nodes {g.NodeCount}, version {g.Version}");
            sb.AppendLine($"unnamed edges: {UnnamedEdges}");
            sb.AppendLine($"no-truck edges: {NoTruckEdges}, restricted-access edges: {RestrictedEdges}, hgv=destination: {HgvDestinationEdges}");
            sb.AppendLine($"one-way: {OnewayEdges}, roundabout: {RoundaboutEdges}, roundabout without oneway: {RoundaboutWithoutOneway}");
            sb.AppendLine($"turn restrictions: {RestrictionsNo + RestrictionsOnly} (no_* {RestrictionsNo}, only_* {RestrictionsOnly}), out of range: {RestrictionsOutOfRange}");
            foreach (var s in SuspiciousRestrictions) sb.AppendLine("suspicious: " + s);
            return sb.ToString();
        }
    }
}
