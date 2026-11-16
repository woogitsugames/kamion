using System.Collections.Generic;
using UnityEngine;

namespace Game.World
{
    /// <summary>
    /// Where a start on a region's start route may stand relative to the region-edge closures (ADR 0262).
    /// A start route of a corridor tile begins ON the tile edge, and the importer closes every road that leaves the tile
    /// with a barrier row set back from the edge (WorldEdgeBuilder, ADR 0169: 60 m, less on short edges). A start at a
    /// fixed 12 m therefore stood outside the closure, facing it (owner report 2026-11-15), or inside the row (dk65-05,
    /// closure 14 m from the edge). The rule here: the start lies behind every closure the route ENTERS the region
    /// through. Pure geometry in the region-root frame (x = east, z = north); used by the importer (baked spawn), the
    /// runtime spawn (scenes baked before this ADR) and the EditMode test on the committed data. Never in the driving loop.
    /// </summary>
    public static class StartClearance
    {
        /// <summary>Start distance along the start route when no closure lies on it [m] (the depot gate of region C).</summary>
        public const float DefaultStartS = 12f;
        /// <summary>Spawn point (tractor origin, ground below the rear axle) to the front face of the tractor [m]:
        /// TractorDimensions wheelbase 3.70 + frontOverhang 1.45 (StartClearanceTests keeps it in step).</summary>
        public const float FrontM = 5.15f;
        /// <summary>Spawn point to the rear end of the coupled 13.6 m trailer [m]: 13.6 - (cargoBay.frontZ 1.572 + front wall 0.05)
        /// - fifth wheel lead 0.68 = 11.298 (StartClearanceTests keeps it in step).</summary>
        public const float RearM = 11.30f;
        /// <summary>Half of the legal vehicle width 2.55 m (96/53/EC).</summary>
        public const float HalfWidthM = 1.275f;
        /// <summary>Free space required around the combination at the start [m] (task: at least 0.5 m).</summary>
        public const float MarginM = 0.5f;
        /// <summary>Start this far along the route behind a closure the route enters through [m]. WORKING_VALUE: the rear end of
        /// the trailer is then 13.7 m inside the barrier row, so the row and its boards are in the mirrors, not under the trailer.</summary>
        public const float BehindClosureM = 25f;
        /// <summary>Route that has to be free of closures ahead of the start [m] (task: at least 300 m, or the rest of a shorter route).</summary>
        public const float AheadFreeM = 300f;
        /// <summary>Boards of a closure stand this far in front of the barrier row, on the inner side (WorldEdgeBuilder boardZ).</summary>
        public const float BoardsM = 0.75f;

        /// <summary>The route crosses the barrier row of a closure at route distance <see cref="s"/>.</summary>
        public struct Crossing
        {
            public float s;
            /// <summary>True: the route runs from the region edge inwards through the row (start must be behind it).
            /// False: the route leaves the region through the row (end of the drivable route).</summary>
            public bool entry;
            public int closure;
        }

        /// <summary>Length of the barrier row [m]: the resolved span (ADR 0169) or road width + 5 m, as WorldEdgeBuilder.ClosureSpan.</summary>
        public static float RowSpan(WorldBoundary.Closure c) => c.spanM > 0f ? c.spanM : c.widthM + 5f;

        /// <summary>
        /// Crossings of the route polyline with the closure rows, each row widened by <see cref="HalfWidthM"/> +
        /// <see cref="MarginM"/> at both ends (the vehicle is not a point). Ordered by route distance.
        /// </summary>
        public static void Crossings(Vector3[] points, float[] distances, IList<WorldBoundary.Closure> closures, List<Crossing> result)
        {
            result.Clear();
            if (points == null || distances == null || closures == null || points.Length < 2 || distances.Length != points.Length) return;
            for (int k = 0; k < closures.Count; k++)
            {
                var c = closures[k];
                float h = c.headingDeg * Mathf.Deg2Rad;
                var outward = new Vector2(Mathf.Sin(h), Mathf.Cos(h));      // road direction towards the region edge
                var right = new Vector2(outward.y, -outward.x);
                var centre = new Vector2(c.localPos.x, c.localPos.z);
                float half = RowSpan(c) * 0.5f + HalfWidthM + MarginM;
                for (int i = 1; i < points.Length; i++)
                {
                    var a = new Vector2(points[i - 1].x, points[i - 1].z) - centre;
                    var b = new Vector2(points[i].x, points[i].z) - centre;
                    float da = Vector2.Dot(a, outward), db = Vector2.Dot(b, outward);
                    // Crossing counted on the segment where the route leaves side a: da on the line itself belongs to the previous segment.
                    if (da == 0f || da * db > 0f) continue;
                    float t = da / (da - db);
                    float across = Vector2.Dot(Vector2.Lerp(a, b, t), right);
                    if (Mathf.Abs(across) > half) continue;
                    result.Add(new Crossing { s = Mathf.Lerp(distances[i - 1], distances[i], t), entry = db < da, closure = k });
                }
            }
            // Insertion sort by s (a handful of rows): no comparer allocation, once per start (ADR 0277: zero GC).
            for (int i = 1; i < result.Count; i++)
            {
                var c = result[i];
                int j = i - 1;
                while (j >= 0 && result[j].s > c.s) { result[j + 1] = result[j]; j--; }
                result[j + 1] = c;
            }
        }

        /// <summary>
        /// Start distance for a requested one: at least <see cref="BehindClosureM"/> behind the last closure the route
        /// enters the region through; unchanged when the requested start is already there or the route enters through none.
        /// </summary>
        public static float SafeStartS(Vector3[] points, float[] distances, IList<WorldBoundary.Closure> closures, float requestedS)
        {
            var list = new List<Crossing>();
            Crossings(points, distances, closures, list);
            return SafeStartS(list, requestedS, distances != null && distances.Length > 0 ? distances[distances.Length - 1] : 0f);
        }

        public static float SafeStartS(List<Crossing> crossings, float requestedS, float routeLength)
        {
            float s = Mathf.Max(0f, requestedS);
            for (int i = 0; i < crossings.Count; i++)
                if (crossings[i].entry) s = Mathf.Max(s, crossings[i].s + BehindClosureM);
            return routeLength > 0f ? Mathf.Min(s, routeLength) : s;
        }

        /// <summary>
        /// Free distance from the rear end of the combination standing at <paramref name="s"/> to the nearest closure row
        /// behind it and from its front face to the nearest row ahead [m] (float.PositiveInfinity = none; negative = the
        /// combination stands in the row). The boards on the inner side of a row count as part of it.
        /// </summary>
        public static void FreeAround(List<Crossing> crossings, float s, out float behindM, out float aheadM)
        {
            behindM = float.PositiveInfinity; aheadM = float.PositiveInfinity;
            for (int i = 0; i < crossings.Count; i++)
            {
                var c = crossings[i];
                // The inner side of a row (where the boards stand) is after an entry row and before an exit row.
                if (c.s <= s) behindM = Mathf.Min(behindM, (s - RearM) - (c.s + (c.entry ? BoardsM : 0f)));
                else aheadM = Mathf.Min(aheadM, (c.s - (c.entry ? 0f : BoardsM)) - (s + FrontM));
            }
        }
    }
}
