using UnityEngine;

namespace Game.World
{
    /// <summary>
    /// Road surface height under a route point from the vertical-ray hits of the ground colliders (pure rules, shared by
    /// the importer's route heights and the runtime start check, ADR 0350).
    ///
    /// The ground collision of a tile has two stacked layers on a road: the carriageway mesh (col_asphalt, ...) and the
    /// terrain mesh under it - on an embankment 0.4-0.8 m lower (dk65-07: asphalt 14.95 m, terrain 14.19 m at the start).
    /// The old importer rule "hit closest to the previous point" was seeded with y = 0 when the first route points lay
    /// outside the tile (no hit), so it took the LOWEST layer and followed the terrain under the road for the whole
    /// route; the start box 0.5 m above the route then always overlapped col_asphalt (build #9: no start on dk65-07).
    /// Rules: a missing hit is "unknown" (never 0); with a known neighbour height the highest surface within
    /// <see cref="WindowM"/> of it wins (the road on top of the terrain; a viaduct deck 4.5 m+ above or a road under a
    /// bridge stays outside the window); without a reference the highest surface wins; unknown points take the height
    /// of the nearest known ones.
    /// </summary>
    public static class RouteGround
    {
        /// <summary>Vertical window around the reference height [m]: wider than the asphalt-over-terrain step (measured
        /// 0.4-0.8 m on dk65-07) plus a 5 % grade over a route step, far below a viaduct clearance (4.5 m+). WORKING_VALUE.</summary>
        public const float WindowM = 1.5f;

        /// <summary>
        /// Picks the surface height from <paramref name="count"/> hit heights (any order). <paramref name="refY"/> = height of
        /// the previous route point (NaN = none). Returns NaN when there is no hit.
        /// </summary>
        public static float Pick(float[] hitY, int count, float refY, float windowM = WindowM)
        {
            float best = float.NaN;
            if (count <= 0) return best;
            if (float.IsNaN(refY))
            {
                for (int i = 0; i < count; i++) if (float.IsNaN(best) || hitY[i] > best) best = hitY[i];
                return best;
            }
            // Highest surface inside the window (road over terrain).
            for (int i = 0; i < count; i++)
            {
                float y = hitY[i];
                if (Mathf.Abs(y - refY) <= windowM && (float.IsNaN(best) || y > best)) best = y;
            }
            if (!float.IsNaN(best)) return best;
            // Nothing near the reference: the closest surface (a step in the data; keeps viaduct levels apart).
            float bestD = float.MaxValue;
            for (int i = 0; i < count; i++)
            {
                float d = Mathf.Abs(hitY[i] - refY);
                if (d < bestD) { bestD = d; best = hitY[i]; }
            }
            return best;
        }

        /// <summary>
        /// Fills unknown heights (NaN y) of a polyline: between two known points linear in the point index, before the
        /// first / after the last known point the nearest known height. All unknown = 0 (no ground anywhere).
        /// Returns the number of filled points.
        /// </summary>
        public static int FillMissing(Vector3[] pts)
        {
            if (pts == null) return 0;
            int filled = 0, prev = -1;
            for (int i = 0; i < pts.Length; i++)
            {
                if (float.IsNaN(pts[i].y)) continue;
                if (prev < 0)
                    for (int k = 0; k < i; k++) { pts[k].y = pts[i].y; filled++; }
                else
                    for (int k = prev + 1; k < i; k++) { pts[k].y = Mathf.Lerp(pts[prev].y, pts[i].y, (k - prev) / (float)(i - prev)); filled++; }
                prev = i;
            }
            if (prev < 0)
            {
                for (int k = 0; k < pts.Length; k++) pts[k].y = 0f;
                return pts.Length;
            }
            for (int k = prev + 1; k < pts.Length; k++) { pts[k].y = pts[prev].y; filled++; }
            return filled;
        }
    }
}
