using UnityEngine;

namespace Game.Core.Navigation
{
    /// <summary>Manoeuvre at a junction of the planned route (icon + text of the guidance).</summary>
    public enum Maneuver : byte
    {
        Continue = 0, SlightRight, Right, SharpRight, SlightLeft, Left, SharpLeft, UTurn, Roundabout, Arrive,
    }

    /// <summary>
    /// A planned route as flat, pre-allocated arrays (capacity fixed per graph, so planning and re-planning never
    /// allocate): polyline in region metres with cumulative distance, street name and OSM speed limit per point,
    /// the directed edges and the manoeuvres at junctions. Written by <see cref="RoutePlanner"/>, read by the map,
    /// the minimap, the guidance banner and the cab navigation screen.
    /// </summary>
    public sealed class RoutePath
    {
        public readonly Vector2[] Points;
        public readonly float[] S;
        public readonly ushort[] Name;
        /// <summary>Speed limit of the segment starting at the point [km/h]; 0 = not tagged in OSM (not shown).</summary>
        public readonly byte[] Limit;
        public int Count;

        public readonly int[] Directed;
        public int DirectedCount;

        public readonly int[] ManPoint;
        public readonly Maneuver[] ManType;
        public readonly float[] ManTurn;
        public readonly byte[] ManExit;
        public readonly ushort[] ManName;
        public int ManCount;

        public Vector2 Destination;
        public ushort DestinationName;
        /// <summary>Planner cost [s] (travel-time model, WORKING_VALUES in <see cref="RoutePlanner"/>).</summary>
        public float CostSeconds;
        /// <summary>Incremented on every write (consumers redraw / reset their tracking when it changes).</summary>
        public int Version;

        public bool HasRoute => Count >= 2;
        public float Length => Count > 0 ? S[Count - 1] : 0f;

        public RoutePath(int pointCapacity, int edgeCapacity)
        {
            Points = new Vector2[pointCapacity]; S = new float[pointCapacity]; Name = new ushort[pointCapacity]; Limit = new byte[pointCapacity];
            Directed = new int[edgeCapacity];
            int m = edgeCapacity + 4;
            ManPoint = new int[m]; ManType = new Maneuver[m]; ManTurn = new float[m]; ManExit = new byte[m]; ManName = new ushort[m];
        }

        /// <summary>Capacity that fits any simple route of <paramref name="g"/> (every point of every edge in both directions).</summary>
        public static RoutePath For(RouteGraph g) => new RoutePath(2 * (g.Points.Length + g.EdgeCount) + 16, 2 * g.EdgeCount + 4);

        public void Clear()
        {
            Count = 0; DirectedCount = 0; ManCount = 0; CostSeconds = 0f; DestinationName = 0;
            Version++;
        }

        /// <summary>Appends a point (skips duplicates closer than 1 cm); false when full.</summary>
        public bool Add(Vector2 p, ushort name, byte limit)
        {
            if (Count > 0 && (p - Points[Count - 1]).sqrMagnitude < 1e-4f) { Name[Count - 1] = name; Limit[Count - 1] = limit; return true; }
            if (Count >= Points.Length) return false;
            Points[Count] = p;
            S[Count] = Count == 0 ? 0f : S[Count - 1] + Vector2.Distance(Points[Count - 1], p);
            Name[Count] = name; Limit[Count] = limit;
            Count++;
            return true;
        }

        public void AddManeuver(int point, Maneuver type, float turnDeg, int exit, ushort name)
        {
            if (ManCount >= ManPoint.Length) return;
            ManPoint[ManCount] = point; ManType[ManCount] = type; ManTurn[ManCount] = turnDeg; ManExit[ManCount] = (byte)Mathf.Clamp(exit, 0, 255);
            ManName[ManCount] = name;
            ManCount++;
        }

        /// <summary>Copies another path (same capacities) - e.g. the start route kept while a new one is planned.</summary>
        public void CopyFrom(RoutePath o)
        {
            System.Array.Copy(o.Points, Points, o.Count); System.Array.Copy(o.S, S, o.Count);
            System.Array.Copy(o.Name, Name, o.Count); System.Array.Copy(o.Limit, Limit, o.Count); Count = o.Count;
            System.Array.Copy(o.Directed, Directed, o.DirectedCount); DirectedCount = o.DirectedCount;
            System.Array.Copy(o.ManPoint, ManPoint, o.ManCount); System.Array.Copy(o.ManType, ManType, o.ManCount);
            System.Array.Copy(o.ManTurn, ManTurn, o.ManCount); System.Array.Copy(o.ManExit, ManExit, o.ManCount);
            System.Array.Copy(o.ManName, ManName, o.ManCount); ManCount = o.ManCount;
            Destination = o.Destination; DestinationName = o.DestinationName; CostSeconds = o.CostSeconds;
            Version = System.Math.Max(Version, o.Version) + 1;
        }

        public static Maneuver Classify(float turnDeg)
        {
            float a = Mathf.Abs(turnDeg);
            if (a >= 165f) return Maneuver.UTurn;
            bool right = turnDeg > 0f;
            if (a < 45f) return right ? Maneuver.SlightRight : Maneuver.SlightLeft;
            if (a < 135f) return right ? Maneuver.Right : Maneuver.Left;
            return right ? Maneuver.SharpRight : Maneuver.SharpLeft;
        }
    }
}
