using Game.Core.Navigation;
using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// Start point of a region start from the menu (ADR 0229): a distance along the region's start route (the scene's
    /// <c>WorldRoute</c>, imported from Data/Regions/&lt;id&gt;/route_start.json) and the road it lies on in the region's
    /// routing graph (<c>Resources/CabDisplay/Nav/&lt;id&gt;_route.bytes</c>, <see cref="RouteGraph"/>) - region id +
    /// region-local position + road id, the same triple a save will hold. Pure functions; used once per start, never in
    /// the driving loop.
    /// </summary>
    public static class RegionStart
    {
        /// <summary>Spawn distance the importer uses for every region scene (WorldSceneBuilder spawnS).</summary>
        public const float DefaultStartS = 12f;
        /// <summary>Route left ahead of the spawn at least: the tile-end closure stands 60 m before the edge (ADR 0169). WORKING_VALUE.</summary>
        public const float MinAheadM = 100f;
        /// <summary>Largest distance between the start point (right-lane centre) and the road axis of the graph [m].
        /// WORKING_VALUE: two-lane carriageways put the lane centre 2-6 m off the axis; dual carriageways up to ~15 m.</summary>
        public const float SnapMaxM = 30f;

        /// <summary>Spawn distance for a requested one: &lt; 0 = <see cref="DefaultStartS"/>; kept inside
        /// [0, length - <see cref="MinAheadM"/>] (0 on a route shorter than that). Unknown length (&lt;= 0): unclamped above.</summary>
        public static float ClampStartS(float requestedS, float routeLength)
        {
            float s = requestedS < 0f ? DefaultStartS : requestedS;
            if (routeLength <= 0f) return Mathf.Max(0f, s);
            return Mathf.Clamp(s, 0f, Mathf.Max(0f, routeLength - MinAheadM));
        }

        /// <summary>Region-local point (x = east, y = north) at distance s along a route polyline in region-root space
        /// (x east, z north; <paramref name="distances"/> cumulative). Clamped to the ends; zero for an empty route.</summary>
        public static Vector2 LocalPointAt(Vector3[] points, float[] distances, float s)
        {
            if (points == null || points.Length == 0) return Vector2.zero;
            if (s <= 0f || points.Length == 1 || distances == null || distances.Length != points.Length) return new Vector2(points[0].x, points[0].z);
            for (int i = 1; i < points.Length; i++)
            {
                if (distances[i] < s) continue;
                float t = Mathf.InverseLerp(distances[i - 1], distances[i], s);
                Vector3 p = Vector3.Lerp(points[i - 1], points[i], t);
                return new Vector2(p.x, p.z);
            }
            var last = points[points.Length - 1];
            return new Vector2(last.x, last.z);
        }

        /// <summary>Road of the start point: the nearest graph edge within <see cref="SnapMaxM"/>.</summary>
        public struct Road
        {
            /// <summary>Edge index in the region graph; -1 when no graph or nothing within <see cref="SnapMaxM"/>.</summary>
            public int Edge;
            /// <summary>Street name ("" = unnamed road or no edge).</summary>
            public string Name;
            /// <summary>Distance from the start point to the edge axis [m] (float.MaxValue when none).</summary>
            public float Distance;
            /// <summary>Distance along the edge from its start node [m].</summary>
            public float Along;
        }

        public static Road FindRoad(RouteGraph graph, Vector2 localEN, float maxDist = SnapMaxM)
        {
            var r = new Road { Edge = -1, Name = "", Distance = float.MaxValue };
            if (graph == null || graph.EdgeCount == 0) return r;
            int e = graph.Snap(localEN, maxDist, out float along, out _, out float dist);
            if (e < 0) return r;
            r.Edge = e; r.Distance = dist; r.Along = along;
            int n = graph.EdgeName[e];
            r.Name = n < graph.Names.Length ? graph.Names[n] : "";
            return r;
        }

        /// <summary>One log line for the start (region, route distance, local point, road): device logs show where a menu start put the truck.</summary>
        public static string Describe(string region, float s, Vector2 localEN, Road road) =>
            "[START] region=" + region + " route_s=" + s.ToString("F1", System.Globalization.CultureInfo.InvariantCulture) +
            " en=" + localEN.x.ToString("F1", System.Globalization.CultureInfo.InvariantCulture) + "," + localEN.y.ToString("F1", System.Globalization.CultureInfo.InvariantCulture) +
            " road_edge=" + road.Edge + " road='" + road.Name + "' road_dist=" +
            (road.Edge >= 0 ? road.Distance.ToString("F1", System.Globalization.CultureInfo.InvariantCulture) : "-");
    }
}
