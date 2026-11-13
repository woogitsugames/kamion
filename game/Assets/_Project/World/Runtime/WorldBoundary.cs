using System;
using UnityEngine;

namespace Game.World
{
    /// <summary>
    /// Edge of an imported region (ADR 0082). The region is a square of generated data (roads, terrain, collision);
    /// outside it there is nothing to drive on. This component stores the drivable rectangle in region-local metres
    /// (x = east, z = north) and the road closures built by the importer where a road leaves the region
    /// (WorldEdgeBuilder: concrete barriers + U-20 boards + a collider, set back from the edge).
    /// Pure data + geometry helpers; the reaction (warning, safe reset) is in Game.Gameplay.WorldSafetyNet.
    /// </summary>
    public sealed class WorldBoundary : MonoBehaviour
    {
        [Tooltip("South-west corner of the drivable rectangle, region-local metres (east, north)")]
        public Vector2 minEN;
        [Tooltip("North-east corner of the drivable rectangle, region-local metres (east, north)")]
        public Vector2 maxEN;
        public Closure[] closures = Array.Empty<Closure>();

        [Serializable]
        public struct Closure
        {
            [Tooltip("Centre of the barrier line on the road surface, region-local (x east, y height above the anchor, z north)")]
            public Vector3 localPos;
            [Tooltip("Heading of the road towards the region edge (degrees clockwise from north)")]
            public float headingDeg;
            [Tooltip("Width of the closed road [m]")]
            public float widthM;
            public string road;
            [Tooltip("Length of the barrier row across the road [m]; 0 = road width + 5 m (ADR 0169: merged / cut rows)")]
            public float spanM;
        }

        /// <summary>Union of the chunk rectangles (scenes imported before ADR 0082 have no WorldBoundary component).</summary>
        public static bool TryChunkBounds(WorldRegionRoot root, out Vector2 min, out Vector2 max)
        {
            min = new Vector2(float.MaxValue, float.MaxValue);
            max = new Vector2(float.MinValue, float.MinValue);
            if (root == null || root.chunks == null || root.chunks.Length == 0) return false;
            for (int i = 0; i < root.chunks.Length; i++)
            {
                min = Vector2.Min(min, root.chunks[i].minEN);
                max = Vector2.Max(max, root.chunks[i].maxEN);
            }
            return max.x > min.x && max.y > min.y;
        }

        /// <summary>
        /// Distance from a region-local point to the nearest edge of the rectangle [m]: positive inside, negative outside.
        /// </summary>
        public static float InsideDistance(Vector2 min, Vector2 max, float east, float north)
        {
            float dx = Mathf.Min(east - min.x, max.x - east);
            float dz = Mathf.Min(north - min.y, max.y - north);
            if (dx >= 0f && dz >= 0f) return Mathf.Min(dx, dz);
            // Outside: Euclidean distance to the rectangle, negative.
            float ox = Mathf.Max(0f, -dx), oz = Mathf.Max(0f, -dz);
            return -Mathf.Sqrt(ox * ox + oz * oz);
        }

        public float InsideDistance(Vector3 worldPos)
        {
            Vector3 l = transform.InverseTransformPoint(worldPos);
            return InsideDistance(minEN, maxEN, l.x, l.z);
        }
    }
}
