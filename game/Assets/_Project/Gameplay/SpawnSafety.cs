using System.Collections.Generic;
using System.Globalization;
using Game.World;
using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// Runtime safety net of a route start (ADR 0262, ADR 0277): the combination never starts outside or inside a
    /// region-edge closure, never inside a static collider and never straight across a bend. Once per spawn (never in
    /// the driving loop), no allocation on the free path:
    /// 1. the scene's <see cref="WorldBoundary"/> closures cut the route into zones (<see cref="StartSearch.SnapToZone"/>)
    ///    - also repairs scenes baked with the old fixed 12 m spawn;
    /// 2. a box around the combination (tractor + trailer, <see cref="StartClearance.MarginM"/> around) tested with
    ///    <c>Physics.OverlapBoxNonAlloc</c> plus the bend check; when the place is taken the search goes forward, then
    ///    back to the entry closure (<see cref="StartSearch.Resolve{TProbe}"/>);
    /// 3. nothing free = <see cref="StartOutcome.NoSpace"/>: the caller does NOT place the combination (ADR 0277).
    /// Every move is logged as a warning: it means the data (catalog startS, baked spawn) should be regenerated.
    /// </summary>
    public static class SpawnSafety
    {
        /// <summary>Step of the search along the route [m] (<see cref="StartSearch.StepM"/>).</summary>
        public const float StepM = StartSearch.StepM;
        /// <summary>Longest search ahead [m] (<see cref="StartSearch.MaxForwardM"/>). WORKING_VALUE.</summary>
        public const float MaxSearchM = StartSearch.MaxForwardM;
        /// <summary>Underside of the test box above the road [m]: clears the road and terrain colliders, kerbs (0.12-0.15 m)
        /// and the crossfall under a 3.55 m wide box; concrete barriers (0.81 m) and bollards reach into it. WORKING_VALUE.</summary>
        public const float BoxBottomM = 0.5f;
        /// <summary>Top of the test box above the road [m]: the 4.0 m trailer.</summary>
        public const float BoxTopM = 4.0f;
        /// <summary>Overlap buffer [colliders]. The vehicle's own colliders are in the box too; a full buffer counts as taken
        /// (<see cref="StartBlock.Overflow"/>, review 0262 P2-9).</summary>
        public const int HitBuffer = 128;

        static readonly Collider[] s_Hits = new Collider[HitBuffer];
        static readonly List<StartClearance.Crossing> s_Crossings = new List<StartClearance.Crossing>(8);
        static readonly PhysicsProbe s_Probe = new PhysicsProbe();

        /// <summary>Physics probe of one search: the combination box + the bend check. One instance, fields set per search.</summary>
        sealed class PhysicsProbe : IStartSpaceProbe
        {
            public WorldRoute route;
            public IList<Transform> ignore;
            public Collider firstHit;
            public bool any;

            public StartBlock Probe(float s)
            {
                StartBlock b = Check(route, s, ignore, out Collider hit);
                if (!any) { any = true; firstHit = hit; }
                return b;
            }
        }

        /// <summary>What stands at route distance s: the bend check first (pure), then the combination box.</summary>
        public static StartBlock Check(WorldRoute route, float s, IList<Transform> ignore, out Collider hit)
        {
            hit = null;
            if (StartSearch.MaxLateralOffset(route.points, route.distances, s, StartClearance.RearM, StartClearance.FrontM) > StartSearch.MaxCurveOffsetM)
                return StartBlock.Curve;
            hit = FirstOverlap(route, s, ignore, StartClearance.RearM, StartClearance.MarginM, out bool overflow);
            if (hit != null) return StartBlock.Collider;
            return overflow ? StartBlock.Overflow : StartBlock.Free;
        }

        /// <summary>
        /// Start for a requested route distance (zones of the scene's closures, then the physics probe). The result's
        /// outcome NoSpace means: do not place the combination. <paramref name="blocker"/> = name of the first collider
        /// found (log only; null when none).
        /// </summary>
        public static StartSearchResult Resolve(WorldRoute route, WorldBoundary boundary, float requestedS, IList<Transform> ignore, out string blocker)
        {
            blocker = null;
            if (route == null || route.points == null || route.points.Length < 2)
                return new StartSearchResult { outcome = StartOutcome.Unchanged, s = requestedS, requestedS = requestedS };
            // Route and closures are both stored in the region-root frame (WorldSceneBuilder parents nothing between them).
            if (boundary != null && boundary.closures != null && boundary.closures.Length > 0)
                StartClearance.Crossings(route.points, route.distances, boundary.closures, s_Crossings);
            else s_Crossings.Clear();
            s_Probe.route = route; s_Probe.ignore = ignore; s_Probe.firstHit = null; s_Probe.any = false;
            var probe = s_Probe;
            var r = StartSearch.Resolve(s_Crossings, route.Length, requestedS, ref probe);
            if (s_Probe.firstHit != null) blocker = s_Probe.firstHit.name;
            s_Probe.route = null; s_Probe.ignore = null; s_Probe.firstHit = null;
            return r;
        }

        /// <summary>
        /// ADR 0262 signature kept for callers and tests: the start distance and the reason (null = unchanged). On
        /// NoSpace it logs an error and returns the requested distance - callers that place a vehicle must use
        /// <see cref="Resolve"/> and honour <see cref="StartOutcome.NoSpace"/> instead.
        /// </summary>
        public static float ResolveStartS(WorldRoute route, WorldBoundary boundary, float requestedS, IList<Transform> ignore, out string reason)
        {
            var r = Resolve(route, boundary, requestedS, ignore, out string blocker);
            reason = r.outcome == StartOutcome.Unchanged ? null : StartSearch.Describe(r.reasons, r.firstBlock, blocker);
            if (r.outcome == StartOutcome.NoSpace)
            {
                Debug.LogError(NoSpaceLog(r, reason));
                return requestedS;
            }
            return r.s;
        }

        /// <summary>Log line of a failed start (once per start).</summary>
        public static string NoSpaceLog(StartSearchResult r, string reason)
        {
            var ci = CultureInfo.InvariantCulture;
            return "[START] no free place for the combination: route_s " + r.requestedS.ToString("F1", ci) +
                   (r.zoneLo <= r.zoneHi
                       ? ", zone " + r.zoneLo.ToString("F1", ci) + "-" + r.zoneHi.ToString("F1", ci) + " m, searched " +
                         StartSearch.MaxForwardM.ToString("F0", ci) + " m ahead and " + StartSearch.MaxBackM.ToString("F0", ci) +
                         " m back (" + r.probes + " places)"
                       : ", the route has no drivable stretch between the region-edge closures") +
                   (string.IsNullOrEmpty(reason) ? "" : " (" + reason + ")") + "; the combination is not placed (ADR 0277)";
        }

        /// <summary>First non-trigger collider (not under <paramref name="ignore"/>) inside the combination box at route distance s; null = free.</summary>
        public static Collider FirstOverlap(WorldRoute route, float s, IList<Transform> ignore) =>
            FirstOverlap(route, s, ignore, StartClearance.RearM, StartClearance.MarginM, out _);

        /// <summary>As above for a box reaching <paramref name="rearM"/> behind the route point with <paramref name="marginM"/> around
        /// (tests: the tractor alone swept along the route ahead of the start).</summary>
        public static Collider FirstOverlap(WorldRoute route, float s, IList<Transform> ignore, float rearM, float marginM) =>
            FirstOverlap(route, s, ignore, rearM, marginM, out _);

        /// <summary>As above; <paramref name="overflow"/> = the buffer was full (some colliders may not have been seen).</summary>
        public static Collider FirstOverlap(WorldRoute route, float s, IList<Transform> ignore, float rearM, float marginM, out bool overflow)
        {
            Pose(route, s, rearM, marginM, out Vector3 centre, out Vector3 half, out Quaternion rot);
            int n = Physics.OverlapBoxNonAlloc(centre, half, s_Hits, rot, ~0, QueryTriggerInteraction.Ignore);
            overflow = n >= s_Hits.Length;
            Collider found = null;
            for (int i = 0; i < n; i++)
            {
                var c = s_Hits[i];
                s_Hits[i] = null;
                if (found != null || c == null || IsUnder(c.transform, ignore)) continue;
                found = c;
            }
            return found;
        }

        /// <summary>
        /// Box of the combination standing at route distance s as the spawn places it: tractor origin on the route point,
        /// heading = route tangent, trailer straight behind (CombinationPlacement.Coupled, articulation 0); pitched along
        /// the road between the route heights at the rear end and the front face.
        /// </summary>
        public static void Pose(WorldRoute route, float s, float rearM, float marginM, out Vector3 centre, out Vector3 halfExtents, out Quaternion rotation)
        {
            Vector3 p = route.PointAt(s);
            Vector3 fwd = route.TangentAt(s);
            float yRear = route.PointAt(s - rearM).y, yFront = route.PointAt(s + StartClearance.FrontM).y;
            float len = StartClearance.FrontM + rearM;
            Vector3 dir = (fwd * len + Vector3.up * (yFront - yRear)).normalized;
            rotation = Quaternion.LookRotation(dir, Vector3.up);
            float mid = (StartClearance.FrontM - rearM) * 0.5f;
            float yMid = Mathf.Lerp(yRear, yFront, 0.5f);
            centre = new Vector3(p.x, yMid, p.z) + fwd * mid + rotation * Vector3.up * ((BoxBottomM + BoxTopM) * 0.5f);
            halfExtents = new Vector3(StartClearance.HalfWidthM + marginM, (BoxTopM - BoxBottomM) * 0.5f, len * 0.5f + marginM);
        }

        static bool IsUnder(Transform t, IList<Transform> roots)
        {
            if (roots == null) return false;
            for (int i = 0; i < roots.Count; i++) if (roots[i] != null && t.IsChildOf(roots[i])) return true;
            return false;
        }
    }
}
