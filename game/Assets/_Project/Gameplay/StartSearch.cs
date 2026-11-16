using System.Collections.Generic;
using Game.World;
using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>What a probe found at one route distance (<see cref="IStartSpaceProbe"/>).</summary>
    public enum StartBlock
    {
        /// <summary>The combination fits here.</summary>
        Free = 0,
        /// <summary>A static collider in the combination box (barrier, bollard, sign, building).</summary>
        Collider = 1,
        /// <summary>The route bends under the straight combination more than <see cref="StartSearch.MaxCurveOffsetM"/>
        /// (roundabout, tight bend: the straight trailer would stand on the island / kerb; review 0262 P2-8).</summary>
        Curve = 2,
        /// <summary>The overlap buffer was full: not every collider was seen, so the place counts as taken (review 0262 P2-9).</summary>
        Overflow = 3,
    }

    /// <summary>Asks the world whether the combination fits at a route distance. Implemented on top of physics by
    /// <see cref="SpawnSafety"/>; by plain data in the tests (the search itself never touches physics).</summary>
    public interface IStartSpaceProbe
    {
        StartBlock Probe(float s);
    }

    /// <summary>Why a start moved (bit set; the log line names each).</summary>
    [System.Flags]
    public enum StartMoveReason
    {
        None = 0,
        /// <summary>Requested start outside / inside the closure the route enters the region through: moved forward behind it.</summary>
        EntryClosure = 1,
        /// <summary>Requested start at / past the closure the route leaves the region through: moved back in front of it.</summary>
        ExitClosure = 2,
        /// <summary>The place was taken (collider / curve / overflow): moved along the route to the nearest free place.</summary>
        Blocked = 4,
        /// <summary>The free place was found behind the requested one (searched back towards the entry closure).</summary>
        SearchedBack = 8,
    }

    public enum StartOutcome
    {
        /// <summary>The requested place is free and inside the region: start exactly there.</summary>
        Unchanged = 0,
        /// <summary>Start at <see cref="StartSearchResult.s"/> instead (see the reasons).</summary>
        Moved = 1,
        /// <summary>No free place between the closures within the search limits: the combination must NOT be placed.</summary>
        NoSpace = 2,
    }

    public struct StartSearchResult
    {
        public StartOutcome outcome;
        /// <summary>Start distance to use (Unchanged / Moved); the zone-snapped request for NoSpace (never to be spawned at).</summary>
        public float s;
        public float requestedS;
        public StartMoveReason reasons;
        /// <summary>What blocked the first probed place (Free when it was free or never probed).</summary>
        public StartBlock firstBlock;
        /// <summary>Drivable zone of the route the search stayed in [m] (lo &gt; hi = the route has none).</summary>
        public float zoneLo, zoneHi;
        /// <summary>Number of probes made (at most 1 + MaxForwardM/StepM + MaxBackM/StepM).</summary>
        public int probes;
    }

    /// <summary>
    /// Pure start-place search of ADR 0277 (successor of the forward-only search of ADR 0262): no physics, no allocation,
    /// unit-testable. Input: the crossings of the start route with the region-edge closure rows
    /// (<see cref="StartClearance.Crossings"/>), the route length, the requested distance and a probe.
    /// <list type="number">
    /// <item>Zones. The route is cut by the closure rows into stretches; a stretch is inside the region when it follows a
    /// row the route ENTERS through (or the route start, when the first row on the route is an exit row or there is none).
    /// The usable part of an inside stretch keeps <see cref="StartClearance.BehindClosureM"/> from the rows at both ends;
    /// a stretch too short for that keeps only the physical footprint (rear end + boards + margin behind, front + boards +
    /// margin ahead); a stretch too short for even that is not usable (review 0262 P2-4: short routes). A requested start
    /// outside every zone snaps to the nearest zone point (tie: forward). Only rows around the requested start count, so
    /// an entry row far ahead behind an exit row no longer pulls the start there (review 0262 P2-3).</item>
    /// <item>Place. The probe checks the snapped place; when it is taken the search goes FORWARD in <see cref="StepM"/>
    /// steps up to <see cref="MaxForwardM"/> (never past the zone end), then BACK up to <see cref="MaxBackM"/> (never
    /// before the zone start = behind the entry closure). Nothing free = <see cref="StartOutcome.NoSpace"/>: the caller
    /// must not place the combination (review 0262 P2-2: it used to start inside the collider).</item>
    /// </list>
    /// </summary>
    public static class StartSearch
    {
        /// <summary>Step of the search along the route [m]. WORKING_VALUE (ADR 0262 value kept).</summary>
        public const float StepM = 2f;
        /// <summary>Longest search ahead of the requested start [m]. WORKING_VALUE (ADR 0262 value kept).</summary>
        public const float MaxForwardM = 200f;
        /// <summary>Longest search back from the requested start [m] (and never before the entry closure). WORKING_VALUE.</summary>
        public const float MaxBackM = 200f;
        /// <summary>Largest lateral distance of the route from the straight combination footprint [m] (review 0262 P2-8).
        /// WORKING_VALUE: above the 0.88 m measured at the catalog start of dk65-06 (largest of the 21 regions, route
        /// data 2026-11-16), far below a roundabout (7.1 m measured on dk65-06 within 60 m of its start).</summary>
        public const float MaxCurveOffsetM = 1.0f;

        /// <summary>
        /// Drivable zone around <paramref name="requestedS"/> and the zone-snapped start (no probing). False = the route
        /// has no usable zone at all. <paramref name="crossings"/> must be ordered by s (as StartClearance.Crossings gives them).
        /// </summary>
        public static bool SnapToZone(List<StartClearance.Crossing> crossings, float routeLength, float requestedS,
                                      out float s, out float zoneLo, out float zoneHi, out StartMoveReason reason)
        {
            reason = StartMoveReason.None;
            float want = Mathf.Clamp(requestedS, 0f, Mathf.Max(0f, routeLength));
            s = want; zoneLo = 1f; zoneHi = 0f;
            int n = crossings != null ? crossings.Count : 0;
            bool found = false;
            float bestD = float.PositiveInfinity;
            // Stretch k lies between boundary k-1 and boundary k (boundary -1 = route start, boundary n = route end).
            for (int k = 0; k <= n; k++)
            {
                bool leftIsRow = k > 0;
                bool inside = leftIsRow ? crossings[k - 1].entry : (n == 0 || !crossings[0].entry);
                if (!inside) continue;
                float left = leftIsRow ? crossings[k - 1].s : 0f;
                bool rightIsRow = k < n;
                float right = rightIsRow ? crossings[k].s : routeLength;
                float lo = left + (leftIsRow ? StartClearance.BehindClosureM : 0f);
                float hi = right - (rightIsRow ? StartClearance.BehindClosureM : 0f);
                if (lo > hi)
                {
                    // Short stretch: only the physical footprint with its margin (boards on the inner side of each row).
                    lo = left + (leftIsRow ? StartClearance.RearM + StartClearance.BoardsM + StartClearance.MarginM : 0f);
                    hi = right - (rightIsRow ? StartClearance.FrontM + (crossings[k].entry ? 0f : StartClearance.BoardsM) + StartClearance.MarginM : 0f);
                    if (lo > hi) continue;
                }
                float snapped = want < lo ? lo : want > hi ? hi : want;
                float d = Mathf.Abs(snapped - want);
                // Nearest zone point; on a tie the later zone (forward) wins.
                if (!found || d < bestD || (d == bestD && snapped > s))
                {
                    found = true; bestD = d; s = snapped; zoneLo = lo; zoneHi = hi;
                }
            }
            if (!found) { s = want; return false; }
            if (s > want + 0.01f) reason = StartMoveReason.EntryClosure;
            else if (s < want - 0.01f) reason = StartMoveReason.ExitClosure;
            return true;
        }

        /// <summary>Full search (zones, then the probe forward and back). Generic probe: no boxing of a struct probe.</summary>
        public static StartSearchResult Resolve<TProbe>(List<StartClearance.Crossing> crossings, float routeLength, float requestedS, ref TProbe probe)
            where TProbe : IStartSpaceProbe
        {
            var r = new StartSearchResult { requestedS = requestedS, firstBlock = StartBlock.Free };
            if (!SnapToZone(crossings, routeLength, requestedS, out float s, out r.zoneLo, out r.zoneHi, out r.reasons))
            {
                r.s = s; r.outcome = StartOutcome.NoSpace;
                return r;
            }
            r.s = s;
            r.probes = 1;
            r.firstBlock = probe.Probe(s);
            if (r.firstBlock == StartBlock.Free)
            {
                r.outcome = r.reasons == StartMoveReason.None ? StartOutcome.Unchanged : StartOutcome.Moved;
                return r;
            }
            // Forward first (the start keeps the most route ahead and the ADR 0262 behaviour), then back to the entry closure.
            for (int i = 1; i * StepM <= MaxForwardM; i++)
            {
                float t = s + i * StepM;
                if (t > r.zoneHi + 1e-3f) break;
                r.probes++;
                if (probe.Probe(t) == StartBlock.Free) { r.s = t; r.reasons |= StartMoveReason.Blocked; r.outcome = StartOutcome.Moved; return r; }
            }
            for (int i = 1; i * StepM <= MaxBackM; i++)
            {
                float t = s - i * StepM;
                if (t < r.zoneLo - 1e-3f) break;
                r.probes++;
                if (probe.Probe(t) == StartBlock.Free)
                {
                    r.s = t; r.reasons |= StartMoveReason.Blocked | StartMoveReason.SearchedBack; r.outcome = StartOutcome.Moved;
                    return r;
                }
            }
            r.outcome = StartOutcome.NoSpace;
            return r;
        }

        /// <summary>
        /// Largest horizontal distance of the route from the straight combination standing at <paramref name="s"/>
        /// (tractor origin on the route point, heading = route tangent as WorldRoute.TangentAt: chord s-2 .. s+2), over the
        /// stretch from the trailer rear end to the tractor front [m]. Region-root frame; pure.
        /// </summary>
        public static float MaxLateralOffset(Vector3[] points, float[] distances, float s, float rearM, float frontM)
        {
            if (points == null || distances == null || points.Length < 2 || distances.Length != points.Length) return 0f;
            Vector3 p = PointAt(points, distances, s);
            Vector3 a = PointAt(points, distances, s - 2f), b = PointAt(points, distances, s + 2f);
            float tx = b.x - a.x, tz = b.z - a.z, len = Mathf.Sqrt(tx * tx + tz * tz);
            if (len < 1e-4f) return 0f;
            tx /= len; tz /= len;
            float from = s - rearM, to = s + frontM, worst = 0f;
            worst = Mathf.Max(worst, Lateral(PointAt(points, distances, from), p, tx, tz));
            worst = Mathf.Max(worst, Lateral(PointAt(points, distances, to), p, tx, tz));
            for (int i = 0; i < points.Length; i++)
                if (distances[i] > from && distances[i] < to) worst = Mathf.Max(worst, Lateral(points[i], p, tx, tz));
            return worst;
        }

        static float Lateral(Vector3 q, Vector3 p, float tx, float tz) => Mathf.Abs((q.x - p.x) * tz - (q.z - p.z) * tx);

        /// <summary>Point at distance s (clamped), as WorldRoute.PointAt in the route's own frame.</summary>
        public static Vector3 PointAt(Vector3[] points, float[] distances, float s)
        {
            if (s <= 0f) return points[0];
            for (int i = 1; i < points.Length; i++)
            {
                if (distances[i] < s) continue;
                float span = distances[i] - distances[i - 1];
                float t = span > 1e-6f ? (s - distances[i - 1]) / span : 1f;
                return new Vector3(points[i - 1].x + (points[i].x - points[i - 1].x) * t,
                                   points[i - 1].y + (points[i].y - points[i - 1].y) * t,
                                   points[i - 1].z + (points[i].z - points[i - 1].z) * t);
            }
            return points[points.Length - 1];
        }

        /// <summary>Reasons for the [START] log line (English, like the other log lines) - built only when a start moved or failed (once per start).</summary>
        public static string Describe(StartMoveReason r, StartBlock firstBlock, string blockerName)
        {
            var sb = new System.Text.StringBuilder(96);
            if ((r & StartMoveReason.EntryClosure) != 0) sb.Append("region-edge closure on the route");
            if ((r & StartMoveReason.ExitClosure) != 0) Join(sb, "region-edge closure ahead on the route");
            if ((r & StartMoveReason.Blocked) != 0 || firstBlock != StartBlock.Free)
            {
                Join(sb, firstBlock == StartBlock.Curve ? "route bends under the combination"
                       : firstBlock == StartBlock.Overflow ? "overlap buffer full"
                       : "collider '" + (blockerName ?? "?") + "'");
                if ((r & StartMoveReason.SearchedBack) != 0) sb.Append(", searched back");
            }
            return sb.ToString();
        }

        static void Join(System.Text.StringBuilder sb, string s) { if (sb.Length > 0) sb.Append(" + "); sb.Append(s); }
    }
}
