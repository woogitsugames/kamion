using System.Collections.Generic;
using Game.World;
using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// Runtime safety net of a route start (ADR 0262): the combination never starts outside or inside a region-edge
    /// closure and never inside a static collider. Two steps, both once per spawn (never in the driving loop):
    /// 1. <see cref="StartClearance"/>.SafeStartS on the scene's
    ///    <see cref="WorldBoundary"/> closures - also repairs scenes baked with the old fixed 12 m spawn;
    /// 2. a box around the combination (tractor + trailer, <see cref="StartClearance.MarginM"/> around) tested with
    ///    <c>Physics.OverlapBoxNonAlloc</c>; when it touches anything the start moves along the route in
    ///    <see cref="StepM"/> steps to the first free place.
    /// Every move is logged as a warning: it means the data (catalog startS, baked spawn) should be regenerated.
    /// </summary>
    public static class SpawnSafety
    {
        /// <summary>Step of the search along the route [m].</summary>
        public const float StepM = 2f;
        /// <summary>Longest search along the route [m]. WORKING_VALUE.</summary>
        public const float MaxSearchM = 200f;
        /// <summary>Underside of the test box above the road [m]: clears the road and terrain colliders, kerbs (0.12-0.15 m)
        /// and the crossfall under a 3.55 m wide box; concrete barriers (0.81 m) and bollards reach into it. WORKING_VALUE.</summary>
        public const float BoxBottomM = 0.5f;
        /// <summary>Top of the test box above the road [m]: the 4.0 m trailer.</summary>
        public const float BoxTopM = 4.0f;

        static readonly Collider[] s_Hits = new Collider[128];   // the vehicle's own colliders are in the box too
        static readonly List<StartClearance.Crossing> s_Crossings = new List<StartClearance.Crossing>(8);

        /// <summary>
        /// Start distance for a requested one. <paramref name="reason"/> = why the requested place was not used
        /// (closure on the route, name of the blocking collider); null = the requested distance is returned unchanged.
        /// </summary>
        public static float ResolveStartS(WorldRoute route, WorldBoundary boundary, float requestedS, IList<Transform> ignore, out string reason)
        {
            reason = null;
            if (route == null || route.points == null || route.points.Length < 2) return requestedS;
            float length = route.Length;
            float s = Mathf.Clamp(requestedS, 0f, length);
            // Last place a start may stand: BehindClosureM before a closure the route LEAVES the region through (review P2-1:
            // a start requested near / past the exit row must not end up outside it, facing the tile edge).
            float limit = length;
            if (boundary != null && boundary.closures != null && boundary.closures.Length > 0)
            {
                // Route and closures are both stored in the region-root frame (WorldSceneBuilder parents nothing between them).
                StartClearance.Crossings(route.points, route.distances, boundary.closures, s_Crossings);
                float safe = StartClearance.SafeStartS(s_Crossings, s, length);
                if (safe > s + 0.01f) { reason = "region-edge closure on the route"; s = safe; }
                float entry = StartClearance.SafeStartS(s_Crossings, 0f, length);   // the entry rule wins on a very short route
                for (int i = 0; i < s_Crossings.Count; i++)
                {
                    var c = s_Crossings[i];
                    if (!c.entry && c.s > entry) limit = Mathf.Min(limit, Mathf.Max(entry, c.s - StartClearance.BehindClosureM));
                }
                if (s > limit + 0.01f) { reason = (reason != null ? reason + " + " : "") + "region-edge closure ahead on the route"; s = limit; }
            }
            float from = s;
            for (float d = 0f; d <= MaxSearchM && from + d <= limit; d += StepM)
            {
                Collider hit = FirstOverlap(route, from + d, ignore);
                if (hit == null)
                {
                    if (d > 0f) s = from + d;
                    return s;
                }
                if (d == 0f) reason = (reason != null ? reason + " + " : "") + "collider '" + hit.name + "'";
            }
            Debug.LogError("[START] no free place for the combination within " + MaxSearchM.ToString("F0", System.Globalization.CultureInfo.InvariantCulture) +
                           " m of route_s=" + from.ToString("F1", System.Globalization.CultureInfo.InvariantCulture) + " (" + reason + ")");
            return from;
        }

        /// <summary>First non-trigger collider (not under <paramref name="ignore"/>) inside the combination box at route distance s; null = free.</summary>
        public static Collider FirstOverlap(WorldRoute route, float s, IList<Transform> ignore) =>
            FirstOverlap(route, s, ignore, StartClearance.RearM, StartClearance.MarginM);

        /// <summary>As above for a box reaching <paramref name="rearM"/> behind the route point with <paramref name="marginM"/> around
        /// (tests: the tractor alone swept along the route ahead of the start).</summary>
        public static Collider FirstOverlap(WorldRoute route, float s, IList<Transform> ignore, float rearM, float marginM)
        {
            Pose(route, s, rearM, marginM, out Vector3 centre, out Vector3 half, out Quaternion rot);
            int n = Physics.OverlapBoxNonAlloc(centre, half, s_Hits, rot, ~0, QueryTriggerInteraction.Ignore);
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
