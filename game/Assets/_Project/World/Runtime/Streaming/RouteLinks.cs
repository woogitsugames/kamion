using System;
using UnityEngine;

namespace Game.World.Streaming
{
    /// <summary>JsonUtility shape of route_links.json (tools/worldgen/streaming/route_links.py, stream-gaps-s23).</summary>
    [Serializable]
    public sealed class RouteLinksData
    {
        public string schema;
        public RouteLinkData[] links = Array.Empty<RouteLinkData>();
        public RouteCorridorData[] corridors = Array.Empty<RouteCorridorData>();
    }

    /// <summary>
    /// A driving path inside one tile that continues the route autopilot where the tile's own control route does not end
    /// on the seam towards the next corridor tile (Knyszyn Rynek, C DK8/DK19). Points: tile-local metres (E = x - anchorX,
    /// N = y - anchorY), centre of the rightmost lane every 2 m, the same lane rules as route_start.json (export-route.py).
    /// </summary>
    [Serializable]
    public sealed class RouteLinkData
    {
        public string id, tile, destination, afterRoute, replacesRoute, note;
        public float lengthM;
        public float[] e = Array.Empty<float>(), n = Array.Empty<float>(), maxspeedKmh = Array.Empty<float>();
        /// <summary>First / last point, EPSG:2180.</summary>
        public double startX, startY, endX, endY;
    }

    [Serializable]
    public sealed class RouteCorridorData
    {
        public string id, destination;
        public string[] tiles = Array.Empty<string>(), missing = Array.Empty<string>();
        public RouteJoinData[] joins = Array.Empty<RouteJoinData>();
    }

    [Serializable]
    public sealed class RouteJoinData { public string from, to, side, exit, entry; public double x, y; public float gapM, seamM; }

    /// <summary>
    /// Route links bound to a <see cref="TileGraph"/> (tile index per link). Pure C#; lookups allocate nothing.
    /// Destination filter: a link with destination "any" always applies; otherwise it applies when it equals the chosen
    /// destination (launch argument <c>-route_to</c>, default <see cref="DefaultDestination"/>).
    /// </summary>
    public sealed class RouteLinks
    {
        public const string ResourcePath = "WorldStreaming/route_links";
        public const string Schema = "truck-sim-pl/route-links/1";
        /// <summary>Owner's corridor (s23): Bialystok -> Knyszyn -> Tykocin.</summary>
        public const string DefaultDestination = "tykocin";

        public readonly RouteLinkData[] Links;
        public readonly RouteCorridorData[] Corridors;
        /// <summary>Tile index (in the bound graph) of each link; -1 = tile not in the graph.</summary>
        public readonly int[] TileOf;
        /// <summary>Tile index whose start route the link replaces; -1 = none.</summary>
        public readonly int[] ReplacesTile;

        public int Count => Links.Length;

        public RouteLinks(RouteLinksData data, TileGraph graph)
        {
            if (data == null) throw new ArgumentNullException(nameof(data));
            if (graph == null) throw new ArgumentNullException(nameof(graph));
            Links = data.links ?? Array.Empty<RouteLinkData>();
            Corridors = data.corridors ?? Array.Empty<RouteCorridorData>();
            TileOf = new int[Links.Length];
            ReplacesTile = new int[Links.Length];
            for (int i = 0; i < Links.Length; i++)
            {
                TileOf[i] = graph.IndexOf(Links[i].tile);
                ReplacesTile[i] = graph.IndexOf(Links[i].replacesRoute);
            }
        }

        public static RouteLinks FromJson(string json, TileGraph graph) => new RouteLinks(JsonUtility.FromJson<RouteLinksData>(json), graph);

        /// <summary>The links shipped in Resources (empty when missing: no link, behaviour as before).</summary>
        public static RouteLinks LoadDefault(TileGraph graph)
        {
            var ta = Resources.Load<TextAsset>(ResourcePath);
            return ta != null ? FromJson(ta.text, graph) : new RouteLinks(new RouteLinksData(), graph);
        }

        /// <summary>Link for every destination ("any" or empty): loses to a link naming the chosen destination
        /// (route-start-s24, WorldStreamer.FindLink).</summary>
        public static bool IsAnyDestination(string linkDestination) =>
            string.IsNullOrEmpty(linkDestination) || linkDestination == "any";

        public static bool Applies(string linkDestination, string chosen) =>
            IsAnyDestination(linkDestination) || string.Equals(linkDestination, chosen, StringComparison.OrdinalIgnoreCase);

        public bool Applies(int i, string chosen) => Applies(Links[i].destination, chosen);

        /// <summary>A link applying to <paramref name="chosen"/> replaces the start route of tile <paramref name="tile"/>.</summary>
        public bool IsRouteReplaced(int tile, string chosen)
        {
            for (int i = 0; i < Links.Length; i++) if (ReplacesTile[i] == tile && tile >= 0 && Applies(i, chosen)) return true;
            return false;
        }

        /// <summary>Unity world position of point k of link i for the world anchor (wx, wy) (floating origin, ADR 0235 §6);
        /// y = 0 (the route autopilot follows x / z only).</summary>
        public Vector3 WorldPoint(int i, int k, TileGraph graph, double wx, double wy)
        {
            var t = graph.Tiles[TileOf[i]];
            var l = Links[i];
            return new Vector3((float)(t.anchorX + l.e[k] - wx), 0f, (float)(t.anchorY + l.n[k] - wy));
        }

        /// <summary>Whole link in Unity world space (a tile event: allocates).</summary>
        public Vector3[] WorldPoints(int i, TileGraph graph, double wx, double wy)
        {
            var r = new Vector3[Links[i].e.Length];
            for (int k = 0; k < r.Length; k++) r[k] = WorldPoint(i, k, graph, wx, wy);
            return r;
        }

        /// <summary>Destination from the command line (<c>-route_to &lt;name&gt;</c> or <c>route_to=&lt;name&gt;</c>);
        /// <see cref="DefaultDestination"/> when absent.</summary>
        public static string DestinationFromArgs(string[] args)
        {
            if (args != null)
                for (int i = 0; i < args.Length; i++)
                {
                    string a = args[i];
                    if ((a == "-route_to" || a == "--route_to") && i + 1 < args.Length && !string.IsNullOrEmpty(args[i + 1])) return args[i + 1];
                    if (a.StartsWith("route_to=", StringComparison.Ordinal) && a.Length > 9) return a.Substring(9);
                }
            return DefaultDestination;
        }
    }
}
