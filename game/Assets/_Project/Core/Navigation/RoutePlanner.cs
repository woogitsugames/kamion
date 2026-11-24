using UnityEngine;

namespace Game.Core.Navigation
{
    /// <summary>GoalOffReach (M27): the tapped destination is in an off-reach part of the map (outside the main strongly
    /// connected component); the pin was snapped to the nearest main-component node instead of failing with NoPath.</summary>
    public enum PlanStatus : byte { Ok = 0, StartOffRoad, GoalOffRoad, NoPath, AlreadyThere, GoalOffReach }

    /// <summary>Which roads leaving a roundabout count for the exit number (ADR 0168). One-way entries never count.</summary>
    public enum ExitCountPolicy : byte
    {
        /// <summary>Every road a motor vehicle may legally drive out on (incl. exits closed to trucks: hgv=no, weight limits).</summary>
        AnyMotorVehicle = 0,
        /// <summary>Only exits the player's truck may use (no hgv=no / access=no, no weight / axle / height / length limit
        /// below the combination, no hgv=destination).</summary>
        ThisTruck = 1,
    }

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
        /// <summary>Maximum extra snap distance to resolve opposing carriageways at the start [m], WORKING_VALUE.</summary>
        public const float SnapHeadingExtraM = 15f;
        /// <summary>Start edge alignment below which a known heading re-snaps to an aligned edge: cos 60 deg, the same cone as
        /// <see cref="RouteGraph.Snap"/>'s heading filter (one-way: signed; two-way: either direction). WORKING_VALUE.</summary>
        public const float SnapHeadingMinCos = 0.5f;
        /// <summary>Penalties [s]. WORKING_VALUES.</summary>
        public const float RightTurnS = 6f, LeftTurnS = 10f, SharpTurnS = 20f, DeadEndUTurnS = 240f, AgainstHeadingS = 300f, RestrictedS = 600f;

        // Truck limits of the player's combination (tractor 4x2 + 13.6 m curtainsider, docs/VEHICLE_REFERENCE_DATA.md):
        // GCW 40.0 t (laden40 preset; legal max 40 t per Directive 96/53/EC - quoted, UNVERIFIED), height 4.00 m (trailer
        // roof top), combination length 16.47 m (kingpin 0.68 m ahead of the drive axle), max axle load 11.5 t (drive-axle
        // legal max, quoted UNVERIFIED; the laden40 drive axle actually carries 10.76 t).
        /// <summary>Max total weight of the combination [0.01 t] = 40.00 t.</summary>
        public const int TruckMaxWeightCt = 4000;
        /// <summary>Max axle load [0.01 t] = 11.50 t.</summary>
        public const int TruckMaxAxleLoadCt = 1150;
        /// <summary>Max height [cm] = 4.00 m.</summary>
        public const int TruckMaxHeightCm = 400;
        /// <summary>Max vehicle (combination) length [cm] = 16.47 m.</summary>
        public const int TruckMaxLengthCm = 1647;

        /// <summary>
        /// May the truck use edge <paramref name="e"/>? An OSM limit below the truck's parameters forbids the edge
        /// (a limit equal to the parameter is allowed); hgv=destination is allowed only as the goal edge
        /// (<paramref name="isGoal"/>), like the no-truck access edges.
        /// </summary>
        public static bool EdgeAllowed(RouteGraph g, int e, bool isGoal)
        {
            if ((g.EdgeFlags[e] & RouteGraph.FlagHgvDestination) != 0 && !isGoal) return false;
            if (g.EdgeMaxWeightC[e] != 0 && g.EdgeMaxWeightC[e] < TruckMaxWeightCt) return false;
            if (g.EdgeMaxAxleLoadC[e] != 0 && g.EdgeMaxAxleLoadC[e] < TruckMaxAxleLoadCt) return false;
            if (g.EdgeMaxHeightCm[e] != 0 && g.EdgeMaxHeightCm[e] < TruckMaxHeightCm) return false;
            if (g.EdgeMaxLengthCm[e] != 0 && g.EdgeMaxLengthCm[e] < TruckMaxLengthCm) return false;
            return true;
        }

        /// <summary>How roundabout exits are counted for the exit number (ADR 0168). Default: every exit a motor vehicle may
        /// legally drive out on, including exits closed to trucks (what the driver sees and counts).</summary>
        public const ExitCountPolicy DefaultExitCounting = ExitCountPolicy.AnyMotorVehicle;
        public ExitCountPolicy ExitCounting = DefaultExitCounting;
        /// <summary>ADR 0302: a leg of a multi-tile trip ends on the seam, i.e. on an outbound carriageway towards the tile
        /// edge - the no-return zone (ADR 0168) and the off-reach exits (M27) are the way OUT there, not traps. True: the
        /// goal snaps to any road and the search may enter the no-return zone (it can only end at the goal or a dead end).</summary>
        public bool AllowTileExit;
        /// <summary>ADR 0302: fallback of a trip leg that has no legal path inside its tile (e.g. DK65 tagged maxaxleload
        /// 10 t &lt; the truck's 11.5 t, while the detour lies outside the corridor tiles): edges over the truck's limits are
        /// allowed at their normal cost. The caller reports it (<see cref="LastUsedRelaxed"/>).</summary>
        public bool RelaxTruckLimits;
        bool m_UsedRelaxed;
        /// <summary>ADR 0307: the combination the route restrictions (<see cref="RoutePath.Restr"/>) are reported for.
        /// Routing legality keeps the constants (<see cref="EdgeAllowed"/>).</summary>
        public TruckLimits Truck = TruckLimits.Default;
        /// <summary>The last search expanded at least one edge over the truck's limits (with <see cref="RelaxTruckLimits"/>).</summary>
        public bool LastUsedRelaxed => m_UsedRelaxed;

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
            m_EdgeLastPoint = new int[2 * g.EdgeCount + 8];
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

        /// <summary>Alignment (cos) of edge <paramref name="e"/> at <paramref name="along"/> with the unit heading; signed for a
        /// one-way edge, absolute for a two-way one (it may be driven either way).</summary>
        static float StartAlignment(RouteGraph g, int e, float along, Vector2 heading)
        {
            float c = Vector2.Dot(g.DirectionAt(e * 2, along, 8f), heading);
            return g.IsOneway(e) ? c : Mathf.Abs(c);
        }

        RoutePath m_Scratch;
        /// <summary>Snapped destination of the last plan (also when it failed with AlreadyThere / NoPath).</summary>
        public Vector2 LastFailedDestination { get; private set; }

        PlanStatus PlanInto(Vector2 start, float headingDeg, Vector2 goal, RoutePath path)
        {
            var g = m_G;
            path.Clear();
            LastExpanded = 0;
            m_UsedRelaxed = false;
            Vector2 heading = float.IsNaN(headingDeg) ? Vector2.zero
                : new Vector2(Mathf.Sin(headingDeg * Mathf.Deg2Rad), Mathf.Cos(headingDeg * Mathf.Deg2Rad));
            int se = g.Snap(start, SnapStartM, out float sAlong, out Vector2 sPt, out float sDist);
            if (se < 0) return PlanStatus.StartOffRoad;
            // Distance alone can select the opposite one-way carriageway. The A* heading penalty is too late:
            // it can only start on that edge, so it would drive against the truck and plan a false U-turn.
            // Reconsider nearby aligned edges before se fixes the start topology; retain the nearest edge when
            // no plausible alternative exists (e.g. a truck actually facing the wrong way on a one-way road).
            // gps-dk8-s24 (build #3 re-routes on DK8): the same holds for an edge that is merely off the heading, not
            // against it - at a junction node every edge is 0 m away and a one-way slip road leaving it at ~60-90 deg
            // won the tie (re-plan from (81, -454) in C: start on the northbound slip, false "zawroc" ahead).
            if (heading != Vector2.zero && StartAlignment(g, se, sAlong, heading) < SnapHeadingMinCos)
            {
                int aligned = g.Snap(start, Mathf.Min(SnapStartM, sDist + SnapHeadingExtraM),
                    out float aAlong, out Vector2 aPt, out _, heading: heading);
                if (aligned >= 0) { se = aligned; sAlong = aAlong; sPt = aPt; }
            }
            // M27: prefer an edge drivable to from the main component; an off-reach goal falls back to the plain snap
            // and then fails with NoPath (the UI never sends such a goal - SetPin snaps the pin to the reachable part).
            // Off-reach edges are NOT skipped in the search (integration r5): A* never reaches them from the main part
            // anyway, and a truck starting on a one-way entry from the tile edge (off-reach) must still route out.
            int ge = g.Snap(goal, SnapGoalM, out float gAlong, out Vector2 gPt, out _, truckOnly: false, mainComponentOnly: !AllowTileExit);
            if (ge < 0) ge = g.Snap(goal, SnapGoalM, out gAlong, out gPt, out _, truckOnly: false);
            if (ge < 0) return PlanStatus.GoalOffRoad;
            // ADR 0168: edges of the no-return zone (outbound carriageways ending at the region-edge closure) are skipped,
            // so a goal snapped there by the fallback fails with NoPath; a truck already inside may still drive on in it.
            bool startInTrap = g.EdgeNoReturnMask[se] || g.NodeNoReturnMask[g.EdgeFrom[se]];

            int gen = Gen();
            int goalState = g.DirectedCount;
            m_HeapCount = 0;
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
                    if (!startInTrap && !AllowTileExit && g.EdgeNoReturnMask[e]) continue;   // ADR 0168: never route into the no-return zone
                    if (!EdgeAllowed(g, e, e == ge))   // OSM weight / height / length limits below the truck's, hgv=destination off-goal
                    {
                        if (!RelaxTruckLimits) continue;
                        // ADR 0302 fallback: allowed at its normal cost - every path of the leg crosses the limited road
                        // anyway (the strict search found none), a per-edge penalty would only push it onto side roads
                        m_UsedRelaxed = true;
                    }
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
            byte cls = g.EdgeClass[e];
            p.Add(g.PointAlong(d, a), name, lim, cls);
            int k0 = g.EdgeStart[e], k1 = g.EdgeStart[e + 1] - 1;
            float len = g.PointS[k1];
            if (!rev)
            {
                for (int k = k0; k <= k1; k++) { float s = g.PointS[k]; if (s > a && s < b) p.Add(g.Points[k], name, lim, cls); }
            }
            else
            {
                for (int k = k1; k >= k0; k--) { float s = len - g.PointS[k]; if (s > a && s < b) p.Add(g.Points[k], name, lim, cls); }
            }
            p.Add(g.PointAlong(d, b), name, lim, cls);
        }

        // Path index where each directed edge of the route begins / ends (filled by BuildGeometry, read by BuildManeuvers).
        readonly int[] m_EdgeFirstPoint, m_EdgeLastPoint;

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
                int before = p.Count;
                if (b < a) b = a;
                float s0 = before > 0 ? p.S[before - 1] : 0f;
                // First point of edge i: reuses before-1 only when AppendRange deduplicates it (< 1 cm); when shifted
                // carriageway axes leave a larger gap at a junction, edge i starts at `before` (ADR 0329 addendum).
                bool dedup = before > 0 && (g.PointAlong(d, a) - p.Points[before - 1]).sqrMagnitude < 1e-4f;
                AppendRange(g, p, d, a, b);
                m_EdgeFirstPoint[i] = before == 0 ? 0 : dedup ? before - 1 : Mathf.Min(before, p.Count - 1);
                m_EdgeLastPoint[i] = Mathf.Max(0, p.Count - 1);
                LimitKind over = Truck.Exceeded(g, e);
                if (over != LimitKind.None && p.Count > 0)   // ADR 0307: only a relaxed plan gets here
                {
                    var r = RouteRestriction.Of(g, e, over);
                    r.S0 = s0; r.S1 = p.S[p.Count - 1]; r.Pos = g.PointAlong(d, a);
                    p.AddRestriction(r);
                }
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
                        if (j > i && HasExit(g, g.StartNode(p.Directed[j]), ExitCounting)) exits++;
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
                    p.ManEndPoint[p.ManCount - 1] = m_EdgeLastPoint[j - 1];
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

        /// <summary>
        /// Is there an exit at roundabout node <paramref name="node"/> that counts for the exit number (ADR 0168)?
        /// Only roads that can legally be driven OUT of the ring count (<see cref="RouteGraph.OutDirected"/> holds only the
        /// allowed directions, so a one-way entry is never an exit). <see cref="ExitCountPolicy.AnyMotorVehicle"/> (default)
        /// also counts exits closed to this truck (hgv=no / access=no, maxweight / maxaxleload / height / length below the
        /// combination, hgv=destination) - the driver counts the exits he sees; <see cref="ExitCountPolicy.ThisTruck"/> skips them.
        /// </summary>
        public static bool HasExit(RouteGraph g, int node, ExitCountPolicy policy)
        {
            for (int k = g.OutStart[node]; k < g.OutStart[node + 1]; k++)
            {
                int e = g.OutDirected[k] >> 1;
                if (g.IsRoundabout(e)) continue;
                if (policy == ExitCountPolicy.ThisTruck && !TruckMayExit(g, e)) continue;
                return true;
            }
            return false;
        }

        /// <summary>The player's truck may leave the ring onto edge <paramref name="e"/> (not as the goal edge).</summary>
        public static bool TruckMayExit(RouteGraph g, int e) =>
            (g.EdgeFlags[e] & RouteGraph.FlagNoTruck) == 0 && EdgeAllowed(g, e, false);

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
