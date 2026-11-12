using UnityEngine;

namespace Game.Core.Navigation
{
    public enum PlanStatus : byte { Ok = 0, StartOffRoad, GoalOffRoad, NoPath, AlreadyThere }

    /// <summary>
    /// A* over directed edges of a <see cref="RouteGraph"/> (edge-based, so OSM turn restrictions and the no-U-turn rule
    /// of a 16.5 m combination are exact). Cost = travel time of a truck; all buffers are allocated once per graph, so a
    /// plan or a re-plan after leaving the route allocates nothing (EditMode test). Typical cost on this region: see ADR 0150.
    /// All speeds and penalties are WORKING_VALUES (no measured truck travel times in the project yet).
    /// </summary>
    public sealed class RoutePlanner
    {
        /// <summary>Upper bound of the truck speed used by the cost model and the heuristic [km/h] (PL: 80 km/h limit for trucks
        /// on expressways, 70 / 50 elsewhere).</summary>
        public const float MaxTruckKmh = 80f;
        /// <summary>Snap distance for the start and the destination [m].</summary>
        public const float SnapStartM = 60f, SnapGoalM = 80f;
        /// <summary>Penalties [s]. WORKING_VALUES.</summary>
        public const float RightTurnS = 6f, LeftTurnS = 10f, SharpTurnS = 20f, DeadEndUTurnS = 240f, AgainstHeadingS = 300f, RestrictedS = 600f;

        readonly RouteGraph m_G;
        readonly float[] m_Cost;
        readonly int[] m_Parent, m_Stamp;
        readonly bool[] m_Closed;
        readonly int[] m_HeapItem;
        readonly float[] m_HeapKey;
        int m_HeapCount, m_Gen;

        public RouteGraph Graph => m_G;
        /// <summary>States expanded by the last plan (diagnostics / tests).</summary>
        public int LastExpanded { get; private set; }

        public RoutePlanner(RouteGraph g)
        {
            m_G = g;
            int n = g.DirectedCount + 1;
            m_Cost = new float[n]; m_Parent = new int[n]; m_Stamp = new int[n]; m_Closed = new bool[n];
            int cap = n * 8 + 64;
            m_HeapItem = new int[cap]; m_HeapKey = new float[cap];
            m_EdgeFirstPoint = new int[2 * g.EdgeCount + 8];
            m_Scratch = RoutePath.For(g);
        }

        /// <summary>Effective truck speed on an edge [m/s] for the cost model.</summary>
        public static float SpeedMs(RouteGraph g, int e)
        {
            // Without an OSM limit: urban class speeds incl. junction delays (service 15, residential 30, secondary 40,
            // primary/trunk 55 km/h); with one: 80 % of the limit, capped at the truck limit. WORKING_VALUES.
            float kmh;
            if (g.EdgeMaxSpeedOsm[e] && g.EdgeMaxSpeed[e] > 0) kmh = Mathf.Min(g.EdgeMaxSpeed[e] * 0.8f, MaxTruckKmh);
            else kmh = g.EdgeClass[e] switch { 0 => 15f, 1 => 30f, 2 => 40f, _ => 55f };
            if ((g.EdgeFlags[e] & RouteGraph.FlagLink) != 0) kmh = Mathf.Min(kmh, 40f);
            return Mathf.Max(5f, kmh) / 3.6f;
        }

        static float SignedTurn(Vector2 inDir, Vector2 outDir) => Vector2.SignedAngle(outDir, inDir);   // + = right (x east, y north)

        float TurnCost(int inDirected, int outDirected)
        {
            var g = m_G;
            Vector2 a = g.DirectionAt(inDirected, g.GeomLength(inDirected >> 1) - 6f, 6f), b = g.DirectionAt(outDirected, 6f, 6f);
            float t = SignedTurn(a, b), at = Mathf.Abs(t);
            if (at < 30f) return 0f;
            if (at > 135f) return SharpTurnS;
            return t > 0f ? RightTurnS : LeftTurnS;
        }

        int Gen()
        {
            if (++m_Gen == int.MaxValue) { System.Array.Clear(m_Stamp, 0, m_Stamp.Length); m_Gen = 1; }
            return m_Gen;
        }

        float CostOf(int s) => m_Stamp[s] == m_Gen ? m_Cost[s] : float.MaxValue;

        void Push(int item, float key)
        {
            if (m_HeapCount >= m_HeapItem.Length) return;   // cannot happen with the capacity above; drop rather than allocate
            int i = m_HeapCount++;
            while (i > 0)
            {
                int p = (i - 1) >> 1;
                if (m_HeapKey[p] <= key) break;
                m_HeapItem[i] = m_HeapItem[p]; m_HeapKey[i] = m_HeapKey[p];
                i = p;
            }
            m_HeapItem[i] = item; m_HeapKey[i] = key;
        }

        int Pop()
        {
            int top = m_HeapItem[0];
            int last = --m_HeapCount;
            if (last > 0)
            {
                int item = m_HeapItem[last]; float key = m_HeapKey[last];
                int i = 0;
                while (true)
                {
                    int c = 2 * i + 1;
                    if (c >= last) break;
                    if (c + 1 < last && m_HeapKey[c + 1] < m_HeapKey[c]) c++;
                    if (m_HeapKey[c] >= key) break;
                    m_HeapItem[i] = m_HeapItem[c]; m_HeapKey[i] = m_HeapKey[c];
                    i = c;
                }
                m_HeapItem[i] = item; m_HeapKey[i] = key;
            }
            return top;
        }

        /// <summary>
        /// Plans from <paramref name="start"/> (truck position, heading in degrees clockwise from north; NaN = any
        /// direction) to <paramref name="goal"/> into <paramref name="path"/>. No allocation.
        /// </summary>
        public PlanStatus Plan(Vector2 start, float headingDeg, Vector2 goal, RoutePath path)
        {
            // Planned into a scratch path and copied on success: a failed re-plan keeps the current route.
            m_Scratch ??= RoutePath.For(m_G);
            var st = PlanInto(start, headingDeg, goal, m_Scratch);
            LastFailedDestination = m_Scratch.Destination;
            if (st == PlanStatus.Ok) path.CopyFrom(m_Scratch);
            return st;
        }

        RoutePath m_Scratch;
        /// <summary>Snapped destination of the last plan (also when it failed with AlreadyThere / NoPath).</summary>
        public Vector2 LastFailedDestination { get; private set; }

        PlanStatus PlanInto(Vector2 start, float headingDeg, Vector2 goal, RoutePath path)
        {
            var g = m_G;
            path.Clear();
            LastExpanded = 0;
            int se = g.Snap(start, SnapStartM, out float sAlong, out Vector2 sPt, out _);
            if (se < 0) return PlanStatus.StartOffRoad;
            int ge = g.Snap(goal, SnapGoalM, out float gAlong, out Vector2 gPt, out _, truckOnly: false);
            if (ge < 0) return PlanStatus.GoalOffRoad;

            int gen = Gen();
            int goalState = g.DirectedCount;
            m_HeapCount = 0;
            Vector2 heading = float.IsNaN(headingDeg) ? Vector2.zero
                : new Vector2(Mathf.Sin(headingDeg * Mathf.Deg2Rad), Mathf.Cos(headingDeg * Mathf.Deg2Rad));
            float hInv = 3.6f / MaxTruckKmh;
            int goalPrev = -1, goalVia = -1;   // goalVia = directed edge that reaches the goal point; goalPrev = its predecessor (-1: start)
            float goalCost = float.MaxValue;
            float seLen = g.GeomLength(se), geLen = g.GeomLength(ge);

            for (int dir = 0; dir < 2; dir++)
            {
                if (dir == 1 && g.IsOneway(se)) continue;
                int d = se * 2 + dir;
                float along = dir == 0 ? sAlong : seLen - sAlong;   // distance from the directed start to the truck
                float pen = 0f;
                if (heading != Vector2.zero && Vector2.Dot(g.DirectionAt(d, along, 8f), heading) < -0.2f) pen = AgainstHeadingS;
                float v = SpeedMs(g, se);
                // Goal on the start edge, ahead in this direction.
                if (ge == se)
                {
                    float goalAlong = dir == 0 ? gAlong : geLen - gAlong;
                    if (goalAlong >= along - 0.5f)
                    {
                        float c = pen + (goalAlong - along) / v;
                        if (c < goalCost) { goalCost = c; goalVia = d; goalPrev = -2; }   // -2: direct, no full edge
                    }
                }
                float cost = pen + (seLen - along) / v;
                m_Stamp[d] = gen; m_Cost[d] = cost; m_Parent[d] = -1; m_Closed[d] = false;
                Push(d, cost + Vector2.Distance(g.NodePos[g.EndNode(d)], gPt) * hInv);
            }
            if (goalVia >= 0) Push(goalState, goalCost);

            while (m_HeapCount > 0)
            {
                float key = m_HeapKey[0];
                int s = Pop();
                if (s == goalState) break;
                if (m_Stamp[s] != gen || m_Closed[s]) continue;
                m_Closed[s] = true;
                LastExpanded++;
                if (key > goalCost) break;
                float gs = m_Cost[s];
                int node = g.EndNode(s), inE = s >> 1;
                bool deadEnd = g.ChoicesAt(node, s) == 0;
                for (int k = g.OutStart[node]; k < g.OutStart[node + 1]; k++)
                {
                    int d = g.OutDirected[k], e = d >> 1;
                    float extra;
                    if (e == inE)
                    {
                        if (!deadEnd) continue;   // no U-turns with a 16.5 m combination, except at a dead end (turning area)
                        extra = DeadEndUTurnS;
                    }
                    else
                    {
                        if (!g.TurnAllowed(inE, node, e)) continue;
                        extra = TurnCost(s, d);
                    }
                    if ((g.EdgeFlags[e] & RouteGraph.FlagNoTruck) != 0 && e != ge) continue;
                    if ((g.EdgeFlags[e] & RouteGraph.FlagRestricted) != 0 && e != ge && e != se) extra += RestrictedS;
                    float v = SpeedMs(g, e), len = g.GeomLength(e);
                    if (e == ge)
                    {
                        float goalAlong = RouteGraph.Reversed(d) ? len - gAlong : gAlong;
                        float c = gs + extra + goalAlong / v;
                        if (c < goalCost) { goalCost = c; goalVia = d; goalPrev = s; Push(goalState, c); }
                    }
                    float nc = gs + extra + len / v;
                    if (nc < CostOf(d))
                    {
                        m_Stamp[d] = gen; m_Cost[d] = nc; m_Parent[d] = s; m_Closed[d] = false;
                        Push(d, nc + Vector2.Distance(g.NodePos[g.EndNode(d)], gPt) * hInv);
                    }
                }
            }
            if (goalVia < 0) return PlanStatus.NoPath;

            // Directed edge sequence: goalVia preceded by the parent chain of goalPrev.
            int n = 0;
            if (path.Directed.Length > m_EdgeFirstPoint.Length) return PlanStatus.NoPath;
            if (goalPrev >= 0)
                for (int s = goalPrev; s >= 0; s = m_Parent[s]) { if (n >= path.Directed.Length - 1) return PlanStatus.NoPath; n++; }
            if (n + 1 > path.Directed.Length) return PlanStatus.NoPath;
            path.DirectedCount = n + 1;
            path.Directed[n] = goalVia;
            int idx = n - 1;
            if (goalPrev >= 0) for (int s = goalPrev; s >= 0; s = m_Parent[s]) path.Directed[idx--] = s;

            path.Destination = gPt;
            path.DestinationName = g.EdgeName[ge];
            path.CostSeconds = goalCost;
            BuildGeometry(g, path, sAlong, gAlong, sPt, gPt);
            if (path.Count < 2 || path.Length < 5f)
            {
                path.Clear();
                path.Destination = gPt; path.DestinationName = g.EdgeName[ge];
                return PlanStatus.AlreadyThere;
            }
            BuildManeuvers(g, path);
            path.Version++;
            return PlanStatus.Ok;
        }

        // ------------------------------------------------------------------ geometry

        /// <summary>Appends the directed edge between directed distances a..b (a &lt;= b).</summary>
        static void AppendRange(RouteGraph g, RoutePath p, int d, float a, float b)
        {
            int e = d >> 1;
            bool rev = RouteGraph.Reversed(d);
            ushort name = g.EdgeName[e];
            byte lim = g.EdgeMaxSpeedOsm[e] ? g.EdgeMaxSpeed[e] : (byte)0;
            p.Add(g.PointAlong(d, a), name, lim);
            int k0 = g.EdgeStart[e], k1 = g.EdgeStart[e + 1] - 1;
            float len = g.PointS[k1];
            if (!rev)
            {
                for (int k = k0; k <= k1; k++) { float s = g.PointS[k]; if (s > a && s < b) p.Add(g.Points[k], name, lim); }
            }
            else
            {
                for (int k = k1; k >= k0; k--) { float s = len - g.PointS[k]; if (s > a && s < b) p.Add(g.Points[k], name, lim); }
            }
            p.Add(g.PointAlong(d, b), name, lim);
        }

        // Path index where each directed edge of the route begins (filled by BuildGeometry, read by BuildManeuvers).
        readonly int[] m_EdgeFirstPoint;

        void BuildGeometry(RouteGraph g, RoutePath p, float sAlong, float gAlong, Vector2 sPt, Vector2 gPt)
        {
            int m = p.DirectedCount;
            for (int i = 0; i < m; i++)
            {
                int d = p.Directed[i], e = d >> 1;
                float len = g.GeomLength(e);
                float a = 0f, b = len;
                if (i == 0) a = RouteGraph.Reversed(d) ? len - sAlong : sAlong;
                if (i == m - 1) b = RouteGraph.Reversed(d) ? len - gAlong : gAlong;
                m_EdgeFirstPoint[i] = Mathf.Max(0, p.Count - 1);
                if (b < a) b = a;
                AppendRange(g, p, d, a, b);
            }
            m_EdgeFirstPoint[0] = 0;
        }

        // ------------------------------------------------------------------ manoeuvres

        /// <summary>Two turns closer than this [m] in the same direction merge into one (dual carriageway crossings). WORKING_VALUE.</summary>
        public const float MergeTurnsM = 30f;

        void BuildManeuvers(RouteGraph g, RoutePath p)
        {
            int m = p.DirectedCount;
            for (int i = 1; i < m; i++)
            {
                int prev = p.Directed[i - 1], cur = p.Directed[i];
                int ep = prev >> 1, ec = cur >> 1;
                int node = g.StartNode(cur);
                Vector2 inDir = g.DirectionAt(prev, g.GeomLength(ep) - 8f, 8f);
                if (g.IsRoundabout(ec) && !g.IsRoundabout(ep))
                {
                    int j = i;
                    int exits = 0;
                    while (j < m && g.IsRoundabout(p.Directed[j] >> 1))
                    {
                        if (j > i && HasExit(g, g.StartNode(p.Directed[j]))) exits++;
                        j++;
                    }
                    float turn = 0f; ushort nm = g.EdgeName[ec];
                    if (j < m)
                    {
                        exits++;   // the exit taken
                        Vector2 outDir = g.DirectionAt(p.Directed[j], 8f, 8f);
                        turn = SignedTurn(inDir, outDir);
                        nm = NameFrom(g, p, j);
                    }
                    p.AddManeuver(m_EdgeFirstPoint[i], Maneuver.Roundabout, turn, exits, nm, prev);
                    p.SetLaneGuidance(g, p.ManCount - 1, prev, turn);
                    i = j;   // the exit transition belongs to this manoeuvre
                    continue;
                }
                if (g.IsRoundabout(ec)) continue;
                int choices = g.ChoicesAt(node, prev);
                if (choices <= 1) continue;
                Vector2 o = g.DirectionAt(cur, 8f, 8f);
                float t = SignedTurn(inDir, o), at = Mathf.Abs(t);
                float straightestOther = 180f;
                for (int k = g.OutStart[node]; k < g.OutStart[node + 1]; k++)
                {
                    int d = g.OutDirected[k], e = d >> 1;
                    if (e == ep || e == ec || !g.TurnAllowed(ep, node, e)) continue;
                    straightestOther = Mathf.Min(straightestOther, Mathf.Abs(SignedTurn(inDir, g.DirectionAt(d, 8f, 8f))));
                }
                Maneuver type;
                if (at < 25f)
                {
                    if (straightestOther > at + 20f) continue;   // the obvious way on
                    type = t >= 0f ? Maneuver.SlightRight : Maneuver.SlightLeft;   // fork: keep right / left
                }
                else type = RoutePath.Classify(t);
                ushort name = NameFrom(g, p, i);
                int pt = m_EdgeFirstPoint[i];
                int last = p.ManCount - 1;
                if (last >= 0 && p.ManType[last] != Maneuver.Roundabout && p.S[pt] - p.S[p.ManPoint[last]] < MergeTurnsM
                    && Mathf.Sign(p.ManTurn[last]) == Mathf.Sign(t))
                {
                    float sum = p.ManTurn[last] + t;
                    p.ManTurn[last] = sum; p.ManType[last] = RoutePath.Classify(sum); p.ManName[last] = name;
                    p.SetLaneGuidance(g, last, p.ManIn[last], sum);
                    continue;
                }
                p.AddManeuver(pt, type, t, 0, name, prev);
                p.SetLaneGuidance(g, p.ManCount - 1, prev, t);
            }
            p.AddManeuver(p.Count - 1, Maneuver.Arrive, 0f, 0, p.DestinationName);
        }

        /// <summary>A roundabout node with a road leaving the roundabout (any vehicle may count it as an exit).</summary>
        static bool HasExit(RouteGraph g, int node)
        {
            for (int k = g.OutStart[node]; k < g.OutStart[node + 1]; k++)
                if (!g.IsRoundabout(g.OutDirected[k] >> 1)) return true;
            return false;
        }

        /// <summary>First street name on the route from directed edge <paramref name="i"/> on (within the next 4 edges).</summary>
        static ushort NameFrom(RouteGraph g, RoutePath p, int i)
        {
            for (int k = i; k < Mathf.Min(p.DirectedCount, i + 4); k++)
            {
                ushort n = g.EdgeName[p.Directed[k] >> 1];
                if (n != 0) return n;
            }
            return 0;
        }
    }
}
