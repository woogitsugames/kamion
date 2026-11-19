using UnityEngine;

namespace Game.Core.Navigation
{
    /// <summary>Which limits of a road the combination exceeds (ADR 0307).</summary>
    [System.Flags]
    public enum LimitKind : byte { None = 0, Height = 1, Weight = 2, AxleLoad = 4, Length = 8 }

    /// <summary>
    /// The combination the limits are compared with (ADR 0307), in the units of the routing graph (KRTG v2):
    /// weight / axle load in 0.01 t, height / length in cm. <see cref="Default"/> = the constants the planner routes with
    /// (<see cref="RoutePlanner.TruckMaxWeightCt"/> ...); the session replaces the weight with the mass of the vehicle
    /// model (tractor + trailer + cargo). Height and length have no runtime source yet: the constants stay.
    /// </summary>
    public struct TruckLimits
    {
        public int WeightCt, AxleLoadCt, HeightCm, LengthCm;

        public static TruckLimits Default => new TruckLimits
        {
            WeightCt = RoutePlanner.TruckMaxWeightCt, AxleLoadCt = RoutePlanner.TruckMaxAxleLoadCt,
            HeightCm = RoutePlanner.TruckMaxHeightCm, LengthCm = RoutePlanner.TruckMaxLengthCm,
        };

        /// <summary>Limits of edge <paramref name="e"/> below this combination (a limit equal to the value is allowed,
        /// as in <see cref="RoutePlanner.EdgeAllowed"/>).</summary>
        public LimitKind Exceeded(RouteGraph g, int e)
        {
            LimitKind k = LimitKind.None;
            if (g.EdgeMaxHeightCm[e] != 0 && g.EdgeMaxHeightCm[e] < HeightCm) k |= LimitKind.Height;
            if (g.EdgeMaxWeightC[e] != 0 && g.EdgeMaxWeightC[e] < WeightCt) k |= LimitKind.Weight;
            if (g.EdgeMaxAxleLoadC[e] != 0 && g.EdgeMaxAxleLoadC[e] < AxleLoadCt) k |= LimitKind.AxleLoad;
            if (g.EdgeMaxLengthCm[e] != 0 && g.EdgeMaxLengthCm[e] < LengthCm) k |= LimitKind.Length;
            return k;
        }
    }

    /// <summary>
    /// A stretch of road with a limit below the combination (ADR 0307): on a planned route (<see cref="S0"/>..<see cref="S1"/>
    /// = route chainage) or ahead on the road without a route (<see cref="RestrictionScout.OnRoad"/>). The limit values are
    /// the graph's (0 = not limited); <see cref="Exceeded"/> says which of them the combination breaks.
    /// </summary>
    public struct RouteRestriction
    {
        public float S0, S1;
        /// <summary>Where the limited stretch begins (frame of the path / graph).</summary>
        public Vector2 Pos;
        public ushort MaxHeightCm, MaxWeightC, MaxAxleLoadC, MaxLengthCm;
        public ushort Name;
        public LimitKind Exceeded;

        public bool SameLimits(in RouteRestriction o) =>
            MaxHeightCm == o.MaxHeightCm && MaxWeightC == o.MaxWeightC && MaxAxleLoadC == o.MaxAxleLoadC && MaxLengthCm == o.MaxLengthCm;

        public static RouteRestriction Of(RouteGraph g, int e, LimitKind exceeded) => new RouteRestriction
        {
            MaxHeightCm = g.EdgeMaxHeightCm[e], MaxWeightC = g.EdgeMaxWeightC[e], MaxAxleLoadC = g.EdgeMaxAxleLoadC[e],
            MaxLengthCm = g.EdgeMaxLengthCm[e], Name = g.EdgeName[e], Exceeded = exceeded,
        };
    }

    /// <summary>
    /// Finds the next limited stretch before the truck (ADR 0307, D91: the game warns, it does not block). No allocation.
    /// </summary>
    public static class RestrictionScout
    {
        /// <summary>Warning distance before the limited stretch [m] (D91: "about 500 m before the bridge").</summary>
        public const float WarnM = 500f;
        /// <summary>Snap radius of the truck to a road when there is no route [m].</summary>
        public const float SnapM = 30f;
        /// <summary>Without a route the scout follows the road while it continues within this angle [deg]; a sharper
        /// continuation is a turn the driver has to choose - the scout stops there. WORKING_VALUE.</summary>
        public const float FollowDeg = 40f;
        const int MaxSteps = 64;

        /// <summary>
        /// Next restriction of route <paramref name="p"/> from chainage <paramref name="routeS"/>: the first one that is
        /// not behind the truck and begins within <paramref name="lookM"/>. <paramref name="distM"/> = 0 on the stretch.
        /// </summary>
        public static bool OnRoute(RoutePath p, float routeS, float lookM, out RouteRestriction r, out float distM)
        {
            r = default; distM = 0f;
            if (p == null) return false;
            for (int i = 0; i < p.RestrCount; i++)
            {
                if (p.Restr[i].S1 <= routeS) continue;
                float d = p.Restr[i].S0 - routeS;
                if (d > lookM) return false;      // sorted by chainage
                r = p.Restr[i]; distM = d > 0f ? d : 0f;
                return true;
            }
            return false;
        }

        /// <summary>
        /// Without a route: the road under the truck (<paramref name="pos"/>, heading clockwise from north) followed
        /// forward up to <paramref name="lookM"/>, straight on at junctions (<see cref="FollowDeg"/>). True when a stretch
        /// with a limit below <paramref name="truck"/> lies ahead; <paramref name="distM"/> to its beginning (0 = on it).
        /// </summary>
        public static bool OnRoad(RouteGraph g, Vector2 pos, float headingDeg, in TruckLimits truck, float lookM,
            out RouteRestriction r, out float distM)
        {
            r = default; distM = 0f;
            if (g == null || g.EdgeCount == 0) return false;
            int e = g.Snap(pos, SnapM, out float along, out _, out _);
            if (e < 0) return false;
            Vector2 hd = new Vector2(Mathf.Sin(headingDeg * Mathf.Deg2Rad), Mathf.Cos(headingDeg * Mathf.Deg2Rad));
            float len = g.GeomLength(e);
            Vector2 fwd = g.DirectionAt(2 * e, Mathf.Clamp(along, 0f, len), 6f);
            bool rev = Vector2.Dot(fwd, hd) < 0f;
            int d = 2 * e + (rev ? 1 : 0);
            float done = -(rev ? len - along : along);      // chainage of the start of directed edge d, from the truck
            float cos = Mathf.Cos(FollowDeg * Mathf.Deg2Rad);
            for (int step = 0; step < MaxSteps; step++)
            {
                int ce = d >> 1;
                LimitKind k = truck.Exceeded(g, ce);
                if (k != LimitKind.None)
                {
                    r = RouteRestriction.Of(g, ce, k);
                    r.S0 = Mathf.Max(0f, done); r.S1 = done + g.GeomLength(ce);
                    r.Pos = done > 0f ? g.PointAlong(d, 0f) : pos;
                    distM = r.S0;
                    return true;
                }
                done += g.GeomLength(ce);
                if (done >= lookM) return false;
                int node = g.EndNode(d);
                float el = g.GeomLength(ce);
                Vector2 dirIn = g.DirectionAt(d, el, 6f);
                int best = -1; float bestDot = cos;
                for (int o = g.OutStart[node]; o < g.OutStart[node + 1]; o++)
                {
                    int nd = g.OutDirected[o];
                    if ((nd >> 1) == ce) continue;                                   // no U-turn
                    float dot = Vector2.Dot(dirIn, g.DirectionAt(nd, 0f, 6f));
                    if (dot > bestDot) { bestDot = dot; best = nd; }
                }
                if (best < 0) return false;
                d = best;
            }
            return false;
        }
    }
}
