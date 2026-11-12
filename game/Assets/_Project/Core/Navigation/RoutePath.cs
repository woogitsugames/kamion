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
        /// <summary>Road class of the segment starting at the point (0 service .. 3 trunk/primary; ETA profile, NavEta).</summary>
        public readonly byte[] Class;
        public int Count;

        public readonly int[] Directed;
        public int DirectedCount;

        public readonly int[] ManPoint;
        public readonly Maneuver[] ManType;
        public readonly float[] ManTurn;
        public readonly byte[] ManExit;
        public readonly ushort[] ManName;
        /// <summary>Ring name (street-name index of the roundabout edges) for Roundabout manoeuvres; 0 otherwise.</summary>
        public readonly ushort[] ManRing;
        /// <summary>Directed edge the truck arrives on for this manoeuvre (-1: none, e.g. Arrive).</summary>
        public readonly int[] ManIn;
        /// <summary>Lane guidance for the manoeuvre: lane count of the incoming edge, direction class and the
        /// bitmasks of allowed / recommended lanes (bit i = lane i, OSM order, leftmost = bit 0).</summary>
        public readonly byte[] ManLaneCount;
        public readonly byte[] ManLaneCls;
        public readonly uint[] ManLanesAllowed, ManLanesRec;
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
            Class = new byte[pointCapacity];
            Directed = new int[edgeCapacity];
            int m = edgeCapacity + 4;
            ManPoint = new int[m]; ManType = new Maneuver[m]; ManTurn = new float[m]; ManExit = new byte[m]; ManName = new ushort[m];
            ManRing = new ushort[m];
            ManIn = new int[m]; ManLaneCount = new byte[m]; ManLaneCls = new byte[m];
            ManLanesAllowed = new uint[m]; ManLanesRec = new uint[m];
        }

        /// <summary>Capacity that fits any simple route of <paramref name="g"/> (every point of every edge in both directions).</summary>
        public static RoutePath For(RouteGraph g) => new RoutePath(2 * (g.Points.Length + g.EdgeCount) + 16, 2 * g.EdgeCount + 4);

        public void Clear()
        {
            Count = 0; DirectedCount = 0; ManCount = 0; CostSeconds = 0f; DestinationName = 0;
            Version++;
        }

        /// <summary>Appends a point (skips duplicates closer than 1 cm); false when full.</summary>
        public bool Add(Vector2 p, ushort name, byte limit, byte cls = 0)
        {
            if (Count > 0 && (p - Points[Count - 1]).sqrMagnitude < 1e-4f) { Name[Count - 1] = name; Limit[Count - 1] = limit; Class[Count - 1] = cls; return true; }
            if (Count >= Points.Length) return false;
            Points[Count] = p;
            S[Count] = Count == 0 ? 0f : S[Count - 1] + Vector2.Distance(Points[Count - 1], p);
            Name[Count] = name; Limit[Count] = limit; Class[Count] = cls;
            Count++;
            return true;
        }

        public void AddManeuver(int point, Maneuver type, float turnDeg, int exit, ushort name, int inDirected = -1)
        {
            if (ManCount >= ManPoint.Length) return;
            ManPoint[ManCount] = point; ManType[ManCount] = type; ManTurn[ManCount] = turnDeg; ManExit[ManCount] = (byte)Mathf.Clamp(exit, 0, 255);
            ManName[ManCount] = name; ManRing[ManCount] = 0; ManIn[ManCount] = inDirected;
            ManLaneCount[ManCount] = 0; ManLaneCls[ManCount] = 0; ManLanesAllowed[ManCount] = 0; ManLanesRec[ManCount] = 0;
            ManCount++;
        }

        /// <summary>Lane guidance of manoeuvre <paramref name="k"/>: which lanes of the incoming edge lead in the turn direction.</summary>
        public void SetLaneGuidance(RouteGraph g, int k, int inDirected, float turnDeg)
        {
            ManIn[k] = inDirected;
            if (inDirected < 0) { ManLaneCount[k] = 0; ManLaneCls[k] = 0; ManLanesAllowed[k] = 0; ManLanesRec[k] = 0; return; }
            int e = inDirected >> 1;
            bool rev = RouteGraph.Reversed(inDirected);
            int n = Mathf.Min(g.LaneCount(e, rev), 32);
            byte cls = LaneGuidance.ClassBit(turnDeg);
            uint allowed = 0u, rec = 0u;
            for (int i = 0; i < n; i++)
            {
                byte m = g.LaneMask(e, rev, i);
                if ((m & cls) == 0) continue;
                allowed |= 1u << i;
                if ((m & ~(byte)cls & ~RouteGraph.LaneThrough) == 0) rec |= 1u << i;   // only the turn direction (and through) marked
            }
            ManLaneCount[k] = (byte)n; ManLaneCls[k] = cls; ManLanesAllowed[k] = allowed; ManLanesRec[k] = rec;
        }

        /// <summary>Copies another path (same capacities) - e.g. the start route kept while a new one is planned.</summary>
        public void CopyFrom(RoutePath o)
        {
            System.Array.Copy(o.Points, Points, o.Count); System.Array.Copy(o.S, S, o.Count);
            System.Array.Copy(o.Name, Name, o.Count); System.Array.Copy(o.Limit, Limit, o.Count);
            System.Array.Copy(o.Class, Class, o.Count); Count = o.Count;
            System.Array.Copy(o.Directed, Directed, o.DirectedCount); DirectedCount = o.DirectedCount;
            System.Array.Copy(o.ManPoint, ManPoint, o.ManCount); System.Array.Copy(o.ManType, ManType, o.ManCount);
            System.Array.Copy(o.ManTurn, ManTurn, o.ManCount); System.Array.Copy(o.ManExit, ManExit, o.ManCount);
            System.Array.Copy(o.ManName, ManName, o.ManCount); System.Array.Copy(o.ManRing, ManRing, o.ManCount);
            System.Array.Copy(o.ManIn, ManIn, o.ManCount);
            System.Array.Copy(o.ManLaneCount, ManLaneCount, o.ManCount); System.Array.Copy(o.ManLaneCls, ManLaneCls, o.ManCount);
            System.Array.Copy(o.ManLanesAllowed, ManLanesAllowed, o.ManCount); System.Array.Copy(o.ManLanesRec, ManLanesRec, o.ManCount);
            ManCount = o.ManCount;
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

    /// <summary>
    /// Matches a manoeuvre's turn angle to the OSM turn:lanes direction classes (wiki Key:turn) and to the lane
    /// masks of the incoming edge: which lanes lead in the chosen direction (allowed) and which are dedicated to
    /// it (recommended). OSM has no "sharp" / merge classes: sharp turns map to left / right, merges are not
    /// matched. Pure static, no allocation.
    /// </summary>
    public static class LaneGuidance
    {
        /// <summary>Lane direction bit (RouteGraph.Lane*) matching the signed turn angle (+ = right).</summary>
        public static byte ClassBit(float turnDeg)
        {
            float a = Mathf.Abs(turnDeg);
            if (a >= 150f) return RouteGraph.LaneReverse;
            if (a >= 60f) return turnDeg > 0f ? RouteGraph.LaneRight : RouteGraph.LaneLeft;
            if (a >= 25f) return turnDeg > 0f ? RouteGraph.LaneSlightRight : RouteGraph.LaneSlightLeft;
            return RouteGraph.LaneThrough;
        }
    }
}
