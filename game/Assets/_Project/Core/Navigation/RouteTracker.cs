using UnityEngine;

namespace Game.Core.Navigation
{
    /// <summary>Guidance state of one update (what the banner, the minimap and the cab navigation show).</summary>
    public struct NavGuidance
    {
        public bool HasRoute, OnRoute, Arrived, NeedsReroute;
        /// <summary>Distance along the route of the truck's projection [m] and its distance from the route line [m].</summary>
        public float RouteS, OffRouteM;
        public int Segment;
        public float RemainingM;
        /// <summary>Next manoeuvre (index into the path's manoeuvre arrays, -1 none) and the distance to it [m].</summary>
        public int Next;
        public float NextM;
        /// <summary>Exit number of the next manoeuvre when it is a roundabout (1-based, in the driving direction; 0 otherwise).</summary>
        public byte NextExit;
        /// <summary>The manoeuvre after the next when it follows closely ("then ..."), -1 otherwise.</summary>
        public int Then;
        public ushort CurrentName;
        public byte CurrentLimit;
        /// <summary>ETA of the remaining route [s] (OSM speed limits + the PL truck profile, NavEta); 0 when unknown.</summary>
        public float RemainingSeconds;
        /// <summary>Lane guidance for the next manoeuvre: lane count of the incoming edge, direction class and
        /// bitmasks of allowed / recommended lanes (bit i = lane i, OSM order, leftmost = bit 0); 0 / -1 = none.
        /// Precomputed by the planner, copied here - no allocation in the driving loop.</summary>
        public byte NextLaneCount;
        public byte NextLaneCls;
        public uint NextLanesAllowed, NextLanesRec;
        public int NextLaneSrc;
    }

    /// <summary>
    /// Follows the truck along a <see cref="RoutePath"/>: projection onto the route polyline (windowed search around the
    /// last segment, global after a jump), next manoeuvre and distances, off-route detection (distance or driving against
    /// the route) with a hold time before a re-plan is requested. Pure, no allocation (EditMode test).
    /// </summary>
    public sealed class RouteTracker
    {
        /// <summary>Off-route distance [m] (route = carriageway centreline; a truck on the outer lane is ~5 m off). WORKING_VALUE.</summary>
        public const float OffRouteM = 25f;
        /// <summary>Seconds off the route before a re-plan is requested. WORKING_VALUE.</summary>
        public const float RerouteHoldS = 2.5f;
        /// <summary>"Then" manoeuvre shown when it follows the next one within this distance [m]. WORKING_VALUE.</summary>
        public const float ThenWithinM = 120f;
        /// <summary>Arrival radius [m] along the route. WORKING_VALUE.</summary>
        public const float ArriveM = 20f;

        /// <summary>ETA refresh period [s] (ADR 0168): NavEta is O(route points), so it is recomputed at 1 Hz instead of
        /// every frame; immediately on a new / changed route and after a re-acquire jump. The HUD shows minutes. WORKING_VALUE.</summary>
        public const float EtaPeriodS = 1f;

        int m_Seg = -1, m_Version = -1;
        float m_OffT;
        RoutePath m_Path;
        float m_EtaT, m_Eta;
        bool m_EtaValid;

        /// <summary>Number of full ETA computations since construction (diagnostics / throttling test).</summary>
        public int EtaComputations { get; private set; }

        public void Reset() { m_Seg = -1; m_OffT = 0f; m_Version = -1; m_Path = null; m_EtaValid = false; m_EtaT = 0f; }

        /// <param name="headingDeg">Truck heading clockwise from north.</param>
        /// <param name="speedMs">Forward speed (driving against the route counts only when moving).</param>
        public void Update(RoutePath p, Vector2 pos, float headingDeg, float speedMs, float dt, ref NavGuidance g)
        {
            g.Next = -1; g.Then = -1; g.NeedsReroute = false; g.NextExit = 0; g.RemainingSeconds = 0f;
            g.NextLaneCount = 0; g.NextLaneCls = 0; g.NextLanesAllowed = 0; g.NextLanesRec = 0; g.NextLaneSrc = -1;
            g.HasRoute = p != null && p.HasRoute;
            if (!g.HasRoute) { g.OnRoute = false; g.Arrived = false; g.RemainingM = 0f; g.NextM = float.NaN; m_Seg = -1; m_EtaValid = false; return; }
            if (p.Version != m_Version || !ReferenceEquals(p, m_Path))
            { m_Version = p.Version; m_Path = p; m_Seg = -1; m_OffT = 0f; m_EtaValid = false; }

            int n = p.Count;
            int a = 1, b = n - 1;
            if (m_Seg >= 1) { a = Mathf.Max(1, m_Seg - 8); b = Mathf.Min(n - 1, m_Seg + 40); }
            float off = Project(p, pos, a, b, out int seg, out float s);
            if (m_Seg >= 1 && off > 40f) { off = Project(p, pos, 1, n - 1, out seg, out s); m_EtaValid = false; }   // re-acquire after a jump / reset
            m_Seg = seg;
            g.Segment = seg; g.RouteS = s; g.OffRouteM = off;
            g.RemainingM = Mathf.Max(0f, p.Length - s);
            m_EtaT += dt;
            if (!m_EtaValid || m_EtaT >= EtaPeriodS)
            {
                m_Eta = NavEta.RemainingSeconds(p, s);
                m_EtaT = 0f; m_EtaValid = true;
                EtaComputations++;
            }
            g.RemainingSeconds = m_Eta;
            g.CurrentName = p.Name[seg - 1]; g.CurrentLimit = p.Limit[seg - 1];

            Vector2 segDir = (p.Points[seg] - p.Points[seg - 1]);
            float sl = segDir.magnitude;
            Vector2 hd = new Vector2(Mathf.Sin(headingDeg * Mathf.Deg2Rad), Mathf.Cos(headingDeg * Mathf.Deg2Rad));
            bool against = sl > 1e-3f && speedMs > 3f && Vector2.Dot(segDir / sl, hd) < -0.3f;
            bool offNow = off > OffRouteM || against;
            m_OffT = offNow ? m_OffT + dt : 0f;
            g.OnRoute = !offNow || m_OffT < RerouteHoldS;
            g.Arrived = g.RemainingM <= ArriveM && off <= OffRouteM;
            g.NeedsReroute = !g.Arrived && m_OffT >= RerouteHoldS;

            for (int k = 0; k < p.ManCount; k++)
            {
                float ms = p.S[p.ManPoint[k]];
                if (ms > s + 1f || p.ManType[k] == Maneuver.Arrive)
                {
                    g.Next = k; g.NextM = Mathf.Max(0f, ms - s); g.NextExit = p.ManExit[k];
                    g.NextLaneCount = p.ManLaneCount[k]; g.NextLaneCls = p.ManLaneCls[k];
                    g.NextLanesAllowed = p.ManLanesAllowed[k]; g.NextLanesRec = p.ManLanesRec[k];
                    g.NextLaneSrc = p.ManIn[k];
                    if (k + 1 < p.ManCount && p.S[p.ManPoint[k + 1]] - ms <= ThenWithinM) g.Then = k + 1;
                    break;
                }
            }
        }

        /// <summary>Re-arms the off-route timer after a re-plan was issued (avoid planning every frame while still off).</summary>
        public void ClearOffRoute() => m_OffT = 0f;

        static float Project(RoutePath p, Vector2 pos, int a, int b, out int seg, out float s)
        {
            float best = float.MaxValue; seg = a; s = 0f;
            for (int i = a; i <= b; i++)
            {
                Vector2 p0 = p.Points[i - 1], ab = p.Points[i] - p0;
                float l2 = ab.sqrMagnitude;
                float t = l2 > 1e-8f ? Mathf.Clamp01(Vector2.Dot(pos - p0, ab) / l2) : 0f;
                float d2 = (pos - (p0 + ab * t)).sqrMagnitude;
                if (d2 < best) { best = d2; seg = i; s = p.S[i - 1] + t * (p.S[i] - p.S[i - 1]); }
            }
            return Mathf.Sqrt(best);
        }
    }
}
