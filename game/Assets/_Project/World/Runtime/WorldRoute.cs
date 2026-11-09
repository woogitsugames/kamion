using UnityEngine;

namespace Game.World
{
    /// <summary>
    /// A drivable route as a polyline in the region's local frame (x = east, z = north; y = ground height when known,
    /// otherwise 0). Imported from <c>Data/Regions/&lt;id&gt;/route_start.json</c> (scripts/export-route.py, right-lane
    /// offset on two-way roads). Used by the route autopilot (device measurements, PlayMode route test) and to place the
    /// spawn at the depot gate.
    /// </summary>
    public sealed class WorldRoute : MonoBehaviour
    {
        public string routeId = "start";
        [Tooltip("Polyline in region-local metres relative to the region root (x east, y height above anchor, z north)")]
        public Vector3[] points = System.Array.Empty<Vector3>();
        [Tooltip("Cumulative distance along the polyline (m)")]
        public float[] distances = System.Array.Empty<float>();
        [Tooltip("Speed limit per point (km/h, 0 = unknown)")]
        public float[] speedLimitsKmh = System.Array.Empty<float>();

        public float Length => distances != null && distances.Length > 0 ? distances[distances.Length - 1] : 0f;

        /// <summary>World-space point at distance s along the route (clamped).</summary>
        public Vector3 PointAt(float s)
        {
            if (points.Length == 0) return transform.position;
            if (s <= 0f) return transform.TransformPoint(points[0]);
            for (int i = 1; i < points.Length; i++)
            {
                if (distances[i] < s) continue;
                float t = Mathf.InverseLerp(distances[i - 1], distances[i], s);
                return transform.TransformPoint(Vector3.Lerp(points[i - 1], points[i], t));
            }
            return transform.TransformPoint(points[points.Length - 1]);
        }

        /// <summary>World-space unit tangent (horizontal) at distance s.</summary>
        public Vector3 TangentAt(float s)
        {
            Vector3 a = PointAt(s - 2f), b = PointAt(s + 2f);
            Vector3 d = b - a; d.y = 0f;
            return d.sqrMagnitude > 1e-6f ? d.normalized : Vector3.forward;
        }

        /// <summary>World-space copy of the polyline (for the path-follower autopilot).</summary>
        public Vector3[] WorldPoints()
        {
            var r = new Vector3[points.Length];
            for (int i = 0; i < points.Length; i++) r[i] = transform.TransformPoint(points[i]);
            return r;
        }

        void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(0.1f, 0.4f, 1f);
            for (int i = 1; i < points.Length; i++)
                Gizmos.DrawLine(transform.TransformPoint(points[i - 1]) + Vector3.up, transform.TransformPoint(points[i]) + Vector3.up);
        }
    }
}
