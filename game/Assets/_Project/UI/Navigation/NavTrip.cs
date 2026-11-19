using System;
using System.Collections.Generic;
using Game.Core.Navigation;
using UnityEngine;

namespace Game.UI.Navigation
{
    /// <summary>JsonUtility shape of Resources/Nav/nav_trips.json (tools/ui/build_nav_trips.py, ADR 0302).</summary>
    [Serializable]
    public sealed class NavTripsData
    {
        public string schema;
        public NavTripData[] trips = Array.Empty<NavTripData>();

        public const string ResourcePath = "Nav/nav_trips";

        public static NavTripsData LoadDefault()
        {
            var ta = Resources.Load<TextAsset>(ResourcePath);
            return ta != null ? JsonUtility.FromJson<NavTripsData>(ta.text) : new NavTripsData();
        }

        public NavTripData Find(string id)
        {
            if (trips != null)
                foreach (var t in trips)
                    if (string.Equals(t.id, id, StringComparison.OrdinalIgnoreCase)) return t;
            return null;
        }
    }

    [Serializable]
    public sealed class NavTripData
    {
        public string id, label, goalTile;
        public string[] tiles = Array.Empty<string>();
        public NavTripJoin[] joins = Array.Empty<NavTripJoin>();
        /// <summary>Goal, EPSG:2180 (end of the last tile's control route).</summary>
        public double goalX, goalY;
    }

    /// <summary>Seam crossing between tiles[i] and tiles[i+1] (EPSG:2180); side = side of the seam seen from "from".</summary>
    [Serializable]
    public sealed class NavTripJoin { public string from, to, side; public double x, y; }

    /// <summary>
    /// ADR 0302: a GPS route over several streamed tiles. The routing graphs stay per tile (ADR 0150); the trip is a chain
    /// of legs, one per tile of the corridor (route_links.json, ADR 0285): leg i is planned in tile i's graph from the seam
    /// where the trip enters the tile (or from the truck in the current tile) to the seam where it leaves (or the goal).
    /// The legs are concatenated into ONE <see cref="RoutePath"/> in the frame of the current tile (each leg moved by its
    /// origin difference), so the tracker, the ETA, the minimap line and the cab screen work unchanged across seams.
    /// - Planning is incremental: <see cref="StepPlan"/> plans one leg per call (the service calls it once per frame).
    /// - Re-route after leaving the route: only the current leg (one A*, no allocation), then <see cref="Compose"/>.
    /// - Tile switch: <see cref="Compose"/> in the new frame - nothing re-planned, the goal is kept.
    /// - Street names: one table for the whole trip (strings de-duplicated), leg indices remapped at plan time.
    /// Compose allocates only when the combined path outgrows its capacity (tile / re-route event, never per frame).
    /// </summary>
    public sealed class NavTrip
    {
        /// <summary>Start / goal points of a leg are moved this far into the tile across the seam (both graphs end in the
        /// same boundary node there; inside the tile the snap is unambiguous). WORKING_VALUE.</summary>
        public const float SeamInsetM = 3f;

        public sealed class Leg
        {
            public string RegionId;
            public double AnchorX, AnchorY;
            /// <summary>Entry / exit point in tile-local metres; HasEntry false for the first tile of the trip.</summary>
            public Vector2 Entry, Exit;
            public float EntryHeadingDeg;
            public bool HasEntry;
            public RouteGraph Graph;
            public RoutePlanner Planner;
            public RoutePath Path;
            public ushort[] NameMap;
            public PlanStatus Status = PlanStatus.NoPath;
            public bool Planned;
            public double PlanMs;
        }

        public readonly string Id, Label;
        public readonly Leg[] Legs;
        readonly List<string> m_Names = new List<string> { "" };
        readonly Dictionary<string, ushort> m_NameIx = new Dictionary<string, ushort> { { "", 0 } };
        readonly ushort m_LabelName;
        int m_Next;            // next leg to plan (StepPlan)

        /// <summary>Leg of the tile the GPS measures in; -1 = the current tile is not on the trip.</summary>
        public int Current { get; private set; } = -1;
        public RoutePath Combined { get; private set; }
        public bool PlanDone => m_Next >= Legs.Length;
        public bool Failed { get; private set; }
        public string FailReason { get; private set; } = "";
        public double TotalPlanMs { get; private set; }
        public int ComposeCount { get; private set; }
        /// <summary>Calls of <see cref="StepPlan"/> that planned a leg (= frames of the incremental planning).</summary>
        public int StepCount { get; private set; }
        /// <summary>Trip street index of the trip label (destination name).</summary>
        public ushort LabelName => m_LabelName;
        public int PlannedCount { get { int n = 0; foreach (var l in Legs) if (l.Planned) n++; return n; } }

        /// <summary>Goal point in tile-local metres of the last leg.</summary>
        public Vector2 GoalLocal { get; }

        /// <summary>
        /// Builds the legs of <paramref name="data"/> (tile anchors from <paramref name="anchorOf"/>: tile id -> EPSG:2180
        /// origin; false = tile unknown → trip fails). Graphs load lazily in <see cref="StepPlan"/>.
        /// </summary>
        public NavTrip(NavTripData data, Func<string, (bool ok, double x, double y)> anchorOf)
        {
            Id = data.id; Label = string.IsNullOrEmpty(data.label) ? data.id : data.label;
            m_LabelName = Intern(Label);
            int n = data.tiles != null ? data.tiles.Length : 0;
            Legs = new Leg[n];
            for (int i = 0; i < n; i++)
            {
                var a = anchorOf(data.tiles[i]);
                var leg = new Leg { RegionId = data.tiles[i], AnchorX = a.x, AnchorY = a.y };
                if (!a.ok) { Failed = true; FailReason = "tile " + data.tiles[i] + " not in the tile graph"; }
                Legs[i] = leg;
            }
            for (int i = 0; i + 1 < n; i++)
            {
                var j = i < data.joins.Length ? data.joins[i] : null;
                if (j == null || j.from != data.tiles[i] || j.to != data.tiles[i + 1]) { Failed = true; FailReason = "join " + i + " does not match the tiles"; break; }
                Vector2 dir = SideDir(j.side);
                var a = Legs[i]; var b = Legs[i + 1];
                a.Exit = new Vector2((float)(j.x - a.AnchorX), (float)(j.y - a.AnchorY)) - dir * SeamInsetM;
                b.Entry = new Vector2((float)(j.x - b.AnchorX), (float)(j.y - b.AnchorY)) + dir * SeamInsetM;
                b.EntryHeadingDeg = Mathf.Atan2(dir.x, dir.y) * Mathf.Rad2Deg;
                b.HasEntry = true;
            }
            if (n > 0)
            {
                var last = Legs[n - 1];
                GoalLocal = new Vector2((float)(data.goalX - last.AnchorX), (float)(data.goalY - last.AnchorY));
                last.Exit = GoalLocal;
            }
            else { Failed = true; FailReason = "no tiles"; }
        }

        /// <summary>Unit vector (east, north) pointing across the seam from the "from" tile.</summary>
        public static Vector2 SideDir(string side)
        {
            switch (side)
            {
                case "N": return new Vector2(0f, 1f);
                case "S": return new Vector2(0f, -1f);
                case "E": return new Vector2(1f, 0f);
                default: return new Vector2(-1f, 0f);
            }
        }

        public int IndexOf(string regionId)
        {
            for (int i = 0; i < Legs.Length; i++) if (Legs[i].RegionId == regionId) return i;
            return -1;
        }

        /// <summary>Sets the current leg (tile the GPS measures in). Legs before it are not shown any more.</summary>
        public void SetCurrent(string regionId) => Current = IndexOf(regionId);

        /// <summary>
        /// Plans the next unplanned leg (one A* in one tile; loads the tile's graph the first time - allocates, a planning
        /// event). The current leg is planned from <paramref name="pos"/> / <paramref name="headingDeg"/> (truck, current
        /// frame); legs before the current one are skipped. True when every leg is planned (or the trip failed).
        /// </summary>
        public bool StepPlan(Vector2 pos, float headingDeg)
        {
            if (Failed) return true;
            while (m_Next < Legs.Length && Current >= 0 && m_Next < Current) { Legs[m_Next].Planned = false; m_Next++; }
            if (m_Next >= Legs.Length) return true;
            int i = m_Next++;
            StepCount++;
            if (!PlanLeg(i, pos, headingDeg)) { Failed = true; FailReason = Legs[i].RegionId + ": " + Legs[i].Status; }
            return PlanDone || Failed;
        }

        /// <summary>Re-plans leg <paramref name="i"/> (the current one after leaving the route) from the truck. No
        /// allocation once the leg's graph is loaded.</summary>
        public bool PlanLeg(int i, Vector2 pos, float headingDeg)
        {
            var leg = Legs[i];
            if (leg.Graph == null)
            {
                leg.Graph = RouteGraph.Load(leg.RegionId);
                if (leg.Graph == null) { leg.Status = PlanStatus.NoPath; return false; }
                leg.Planner = new RoutePlanner(leg.Graph) { AllowTileExit = true };   // legs end on the seam (ADR 0302)
                leg.Path = RoutePath.For(leg.Graph);
                leg.NameMap = new ushort[leg.Graph.Names.Length];
                for (int k = 0; k < leg.NameMap.Length; k++) leg.NameMap[k] = Intern(leg.Graph.Names[k]);
            }
            long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
            // the truck's leg starts at the truck; the others at their entry seam (the first tile of a trip started
            // elsewhere has no entry: from the truck too - the plan fails cleanly when the truck is not in that tile)
            bool fromTruck = i == Current || !leg.HasEntry;
            Vector2 start = fromTruck ? pos : leg.Entry;
            float hd = fromTruck ? headingDeg : leg.EntryHeadingDeg;
            leg.Status = leg.Planner.Plan(start, hd, leg.Exit, leg.Path);
            if (leg.Status == PlanStatus.AlreadyThere) { leg.Path.Clear(); leg.Status = PlanStatus.Ok; }   // truck already at the seam
            leg.PlanMs = (System.Diagnostics.Stopwatch.GetTimestamp() - t0) * 1000.0 / System.Diagnostics.Stopwatch.Frequency;
            TotalPlanMs += leg.PlanMs;
            leg.Planned = leg.Status == PlanStatus.Ok;
            return leg.Planned;
        }

        ushort Intern(string s)
        {
            s ??= "";
            if (m_NameIx.TryGetValue(s, out ushort v)) return v;
            if (m_Names.Count >= ushort.MaxValue) return 0;
            v = (ushort)m_Names.Count;
            m_Names.Add(s);
            m_NameIx[s] = v;
            return v;
        }

        public string NameOf(ushort i) => i < m_Names.Count ? m_Names[i] : "";
        public int NameCount => m_Names.Count;

        /// <summary>Trip street index of a street index of the current leg's graph (the street under the truck).</summary>
        public ushort MapCurrentName(ushort graphName)
        {
            if (Current < 0) return 0;
            var m = Legs[Current].NameMap;
            return m != null && graphName < m.Length ? m[graphName] : (ushort)0;
        }

        /// <summary>
        /// Concatenates the planned legs from the current one to the goal into <see cref="Combined"/>, in the frame of the
        /// tile with origin (<paramref name="frameX"/>, <paramref name="frameY"/>). Stops at the first unplanned leg.
        /// Allocates only when the combined path needs more capacity. Returns the number of legs composed.
        /// </summary>
        public int Compose(double frameX, double frameY)
        {
            int from = Mathf.Max(0, Current);
            int points = 16, edges = 4;
            for (int i = from; i < Legs.Length && Legs[i].Planned; i++) { points += Legs[i].Path.Count; edges += Legs[i].Path.ManCount; }
            var c = Combined;
            if (c == null || c.Points.Length < points || c.ManPoint.Length < edges + 4)
            {
                int ver = c != null ? c.Version : 0;
                c = Combined = new RoutePath(points + points / 2, edges + edges / 2 + 8);
                c.Version = ver + 1;
            }
            c.Clear();
            int legs = 0;
            float cost = 0f;
            for (int i = from; i < Legs.Length; i++)
            {
                var leg = Legs[i];
                if (!leg.Planned) break;
                var p = leg.Path;
                var off = new Vector2((float)(leg.AnchorX - frameX), (float)(leg.AnchorY - frameY));
                int b = c.Count;
                // seam: the previous leg ended SeamInsetM before the seam, this one starts SeamInsetM after - straight join
                for (int k = 0; k < p.Count; k++)
                {
                    ushort nm = p.Name[k] < leg.NameMap.Length ? leg.NameMap[p.Name[k]] : (ushort)0;
                    c.Add(p.Points[k] + off, nm, p.Limit[k], p.Class[k]);
                }
                bool last = i == Legs.Length - 1;
                for (int k = 0; k < p.ManCount; k++)
                {
                    if (p.ManType[k] == Maneuver.Arrive && !last) continue;   // the seam is not an arrival
                    int pt = Mathf.Clamp(b + p.ManPoint[k] - (b > 0 && p.Count > 0 && (p.Points[0] + off - c.Points[b - 1]).sqrMagnitude < 1e-4f ? 1 : 0), 0, c.Count - 1);
                    ushort mn = p.ManName[k] < leg.NameMap.Length ? leg.NameMap[p.ManName[k]] : (ushort)0;
                    c.AddManeuver(pt, p.ManType[k], p.ManTurn[k], p.ManExit[k], mn, -1);
                    int m = c.ManCount - 1;
                    c.ManLaneCount[m] = p.ManLaneCount[k]; c.ManLaneCls[m] = p.ManLaneCls[k];
                    c.ManLanesAllowed[m] = p.ManLanesAllowed[k]; c.ManLanesRec[m] = p.ManLanesRec[k];
                }
                cost += p.CostSeconds;
                if (last) c.Destination = p.Destination + off;
                legs++;
            }
            if (legs > 0 && from + legs < Legs.Length)   // partial (still planning): destination = end of what is known
                c.Destination = c.Count > 0 ? c.Points[c.Count - 1] : Vector2.zero;
            c.DestinationName = m_LabelName;
            c.CostSeconds = cost;
            c.Version++;
            ComposeCount++;
            return legs;
        }

        /// <summary>Goal in the frame of the tile with origin (frameX, frameY).</summary>
        public Vector2 GoalIn(double frameX, double frameY)
        {
            var last = Legs[Legs.Length - 1];
            return GoalLocal + new Vector2((float)(last.AnchorX - frameX), (float)(last.AnchorY - frameY));
        }

        /// <summary>Length [m] of the planned legs from the current one (diagnostics).</summary>
        public float PlannedLength()
        {
            float s = 0f;
            for (int i = Mathf.Max(0, Current); i < Legs.Length; i++) if (Legs[i].Planned) s += Legs[i].Path.Length;
            return s;
        }
    }
}
