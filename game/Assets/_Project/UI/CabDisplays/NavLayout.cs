using UnityEngine;
using P = Game.UI.CabDisplays.DisplayPalette;
using T = Game.UI.CabDisplays.CabDisplayText;

namespace Game.UI.CabDisplays
{
    /// <summary>
    /// Navigation screen of the centre console (1280 x 768 design px = the A6 infotainment texture), heading-up map of the
    /// region (roads by class, building footprints) with the start route (G3), the truck arrow, the next manoeuvre
    /// (turn direction, distance, street after the turn), the speed limit of the current route section and a bottom bar
    /// (clock, remaining distance, arrival time, destination). No map brand, no logos. Night palette with the dipped beam.
    /// Zoom follows speed (wider ahead when faster), smoothed by the caller's refresh rate.
    /// </summary>
    public sealed class NavLayout
    {
        public const int Width = 1280, Height = 768;
        const float BarH = 110f, MapH = Height - BarH;
        const float ArrowX = Width * 0.5f, ArrowY = MapH - 130f;
        /// <summary>Off-route distance [m] after which the route is shown as lost.</summary>
        public const float OffRouteM = 25f;

        readonly TextBuffer m_B = new TextBuffer(64);
        NavMapData m_Map;
        int m_RouteHint = -1;
        float m_Zoom = 2.6f;   // design px per metre
        float m_Cos, m_Sin, m_E, m_N;

        Mesh m_Static;            // roads + buildings of the whole region in metres, baked once per palette
        bool m_StaticNight;
        DisplayCanvas m_StaticFor;

        public NavMapData Map { get => m_Map; set { m_Map = value; m_RouteHint = -1; ReleaseStatic(); } }
        public Mesh StaticMap => m_Static;

        public void ReleaseStatic()
        {
            if (m_StaticFor != null) m_StaticFor.SetUnderlay(null);
            m_StaticFor = null;
            if (m_Static == null) return;
            if (Application.isPlaying) Object.Destroy(m_Static); else Object.DestroyImmediate(m_Static);
            m_Static = null;
        }
        /// <summary>Route station of the last refresh (-1: off map / no route).</summary>
        public int RouteIndex { get; private set; } = -1;
        public float RouteDistance { get; private set; } = float.MaxValue;
        /// <summary>Distance to the next manoeuvre [m] and its turn (deg, + = right) of the last refresh (NaN: none).</summary>
        public float NextManeuverM { get; private set; } = float.NaN;
        public float NextTurnDeg { get; private set; }

        public static void RequestGlyphs(DisplayCanvas d)
        {
            foreach (float s in s_Sizes) d.RequestGlyphs(T.Charset, s);
        }

        static readonly float[] s_Sizes = { 46f, 44f, 32f, 30f, 26f };

        /// <param name="dt">Seconds since the last refresh (zoom smoothing).</param>
        public void Draw(DisplayCanvas d, in CabDisplayState s, float dt)
        {
            var pal = s.Night ? P.NavNight : P.NavDay;
            d.Begin();
            if (m_Map == null || !s.HasPosition)
            {
                d.Text(T.NoMap, Width * 0.5f, MapH * 0.5f, 32f, pal.BarSub, DisplayCanvas.Align.Center);
                Bar(d, s, pal, float.NaN, -1);
                d.End(pal.Bg);
                return;
            }

            // Zoom: 2.6 px/m (≈ 490 m across) standing, 1.3 px/m at 70 km/h and above.
            float target = Mathf.Lerp(2.6f, 1.3f, Mathf.Clamp01(Mathf.Abs(s.SpeedKmh) / 70f));
            m_Zoom = dt <= 0f ? target : Mathf.Lerp(m_Zoom, target, 1f - Mathf.Exp(-dt / 1.5f));
            float h = s.HeadingDeg * Mathf.Deg2Rad;
            m_Cos = Mathf.Cos(h); m_Sin = Mathf.Sin(h); m_E = s.PosE; m_N = s.PosN;

            var pos = new Vector2(s.PosE, s.PosN);
            RouteIndex = m_Map.NearestRouteIndex(pos, m_RouteHint, out float off);
            if (RouteIndex >= 0 && off > 60f) RouteIndex = m_Map.NearestRouteIndex(pos, -1, out off);   // re-acquire after a jump
            RouteDistance = off;
            m_RouteHint = RouteIndex;
            bool onRoute = RouteIndex >= 0 && off <= OffRouteM;

            // Roads and buildings: one static mesh in metres (baked on the first refresh and on a day/night switch), placed
            // by a matrix - the per-refresh CPU work is the route, the arrow and the text only.
            EnsureStatic(d, s.Night, pal);
            d.DrawUnderlay(MapMatrix(), m_Zoom * d.Scale);
            Route(d, pal, onRoute);
            TruckArrow(d, pal);
            Maneuver(d, pal, onRoute);
            SpeedLimit(d, pal, onRoute);
            Bar(d, s, pal, onRoute ? m_Map.RouteLength - m_Map.RouteS[RouteIndex] : float.NaN, onRoute ? RouteIndex : -1);
            d.End(pal.Bg);
        }

        Vector2 ToScreen(Vector2 p)
        {
            float x = p.x - m_E, y = p.y - m_N;
            // Right = (cos h, -sin h), forward = (sin h, cos h) for a heading h clockwise from north.
            float r = x * m_Cos - y * m_Sin, f = x * m_Sin + y * m_Cos;
            return new Vector2(ArrowX + r * m_Zoom, ArrowY - f * m_Zoom);
        }


        /// <summary>Design px from region metres for the current position, heading and zoom (y down).</summary>
        Matrix4x4 MapMatrix()
        {
            float z = m_Zoom, c = m_Cos, sn = m_Sin;
            var m = Matrix4x4.identity;
            m.m00 = z * c; m.m01 = -z * sn; m.m03 = ArrowX - z * (c * m_E - sn * m_N);
            m.m10 = -z * sn; m.m11 = -z * c; m.m13 = ArrowY + z * (sn * m_E + c * m_N);
            return m;
        }

        /// <summary>Minimum drawn road width per class [m] (≈ 5 / 9 / 12 / 15 px at 2 px/m, so minor roads stay visible).</summary>
        static float RoadMinM(byte cls) => cls switch { 0 => 2.5f, 1 => 4.5f, 2 => 6f, _ => 7.5f };

        void EnsureStatic(DisplayCanvas d, bool night, in P.Nav pal)
        {
            if (m_Static != null && m_StaticNight == night && m_StaticFor == d) return;
            ReleaseStatic();
            m_Static = BuildStatic(m_Map, pal, 1.6f);
            m_StaticNight = night;
            m_StaticFor = d;
            d.SetUnderlay(m_Static);
        }

        /// <summary>Bakes buildings, road casings and road fills of the whole map into one mesh (region metres).</summary>
        public static Mesh BuildStatic(NavMapData m, in P.Nav pal, float padMetres)
        {
            int quads = m.BuildingTris.Length / 3 + 64;
            for (int i = 0; i < m.RoadCount; i++) quads += 2 * (2 * (m.RoadStart[i + 1] - m.RoadStart[i]));
            var b = new DisplayCanvas("NavStatic", quads, padMetres);
            try
            {
                b.Begin();
                for (int i = 0; i < m.BuildingTriStart.Length - 1; i++)
                    for (int t = m.BuildingTriStart[i]; t < m.BuildingTriStart[i + 1]; t += 3)
                        b.Triangle(m.BuildingPoints[m.BuildingTris[t]], m.BuildingPoints[m.BuildingTris[t + 1]], m.BuildingPoints[m.BuildingTris[t + 2]], pal.Building);
                for (int pass = 0; pass < 2; pass++)
                    for (int i = 0; i < m.RoadCount; i++)
                    {
                        bool major = m.RoadClass[i] >= 2, casing = pass == 0;
                        float w = Mathf.Max(RoadMinM(m.RoadClass[i]), m.RoadWidth[i]) + (casing ? 2f : 0f);
                        Color32 c = casing ? (major ? pal.MajorCasing : pal.Casing) : (major ? pal.Major : pal.Road);
                        StaticPolyline(b, m.RoadPoints, m.RoadStart[i], m.RoadStart[i + 1], w, c);
                    }
                return b.BakeStatic("NavStaticMap");
            }
            finally { b.Dispose(); }
        }

        static void StaticPolyline(DisplayCanvas b, Vector2[] pts, int a, int e, float w, Color32 c)
        {
            if (e - a < 2) return;
            b.Disc(pts[a].x, pts[a].y, w * 0.5f, c);
            for (int k = a + 1; k < e; k++)
            {
                b.Line(pts[k - 1].x, pts[k - 1].y, pts[k].x, pts[k].y, w, c, false);
                b.Disc(pts[k].x, pts[k].y, w * 0.5f, c);
            }
        }

        void Route(DisplayCanvas d, in P.Nav pal, bool onRoute)
        {
            var m = m_Map;
            int n = m.Route.Length;
            if (n < 2) return;
            int from = onRoute ? RouteIndex : 0;
            // Passed part thin and grey, the part ahead in route blue with a darker casing; every 2nd station (4 m) is enough.
            if (onRoute && from > 1) StridePolyline(d, m.Route, 0, from + 1, 7f, pal.RoutePassed);
            StridePolyline(d, m.Route, from, n, 15f, onRoute ? pal.RouteCasing : pal.RoutePassed);
            if (onRoute) StridePolyline(d, m.Route, from, n, 11f, pal.Route);
        }

        void StridePolyline(DisplayCanvas d, Vector2[] pts, int a, int b, float w, Color32 c)
        {
            Vector2 prev = ToScreen(pts[a]);
            bool prevIn = InMap(prev);
            for (int k = a + 2; k < b + 1; k += 2)
            {
                int i = Mathf.Min(k, b - 1);
                Vector2 p = ToScreen(pts[i]);
                bool pin = InMap(p);
                if (pin || prevIn)
                {
                    d.Line(prev.x, prev.y, p.x, p.y, w, c, false);
                    d.Disc(p.x, p.y, w * 0.5f, c);
                }
                prev = p; prevIn = pin;
                if (i == b - 1) break;
            }
        }

        static bool InMap(Vector2 p) => p.x > -200f && p.x < Width + 200f && p.y > -200f && p.y < MapH + 200f;

        void TruckArrow(DisplayCanvas d, in P.Nav pal)
        {
            // Chevron pointing up (heading-up map), outlined for contrast on the route.
            Vector2 tip = new Vector2(ArrowX, ArrowY - 26f), l = new Vector2(ArrowX - 19f, ArrowY + 18f),
                r = new Vector2(ArrowX + 19f, ArrowY + 18f), notch = new Vector2(ArrowX, ArrowY + 6f);
            Vector2 tipO = new Vector2(ArrowX, ArrowY - 32f), lO = new Vector2(ArrowX - 24f, ArrowY + 23f),
                rO = new Vector2(ArrowX + 24f, ArrowY + 23f), notchO = new Vector2(ArrowX, ArrowY + 12f);
            d.Triangle(tipO, lO, notchO, pal.ArrowEdge); d.Triangle(tipO, notchO, rO, pal.ArrowEdge);
            d.Triangle(tip, l, notch, pal.Arrow); d.Triangle(tip, notch, r, pal.Arrow);
        }

        // ------------------------------------------------------------------ manoeuvre

        void Maneuver(DisplayCanvas d, in P.Nav pal, bool onRoute)
        {
            const float bh = 130f;
            if (!onRoute)
            {
                NextManeuverM = float.NaN;
                d.Rect(0f, 0f, 420f, bh, pal.Box);
                d.Text(T.OffRoute, 30f, 80f, 44f, pal.BoxText);
                return;
            }
            var m = m_Map;
            int k = FindTurn(m, RouteIndex, out float turn);
            float dist;
            ushort nameIdx;
            if (k < 0)
            {
                dist = m.RouteLength - m.RouteS[RouteIndex];
                nameIdx = LastName(m);
                turn = 0f;
                NextManeuverM = dist; NextTurnDeg = 0f;
            }
            else
            {
                dist = m.RouteS[k] - m.RouteS[RouteIndex];
                nameIdx = NameAfter(m, k);
                NextManeuverM = dist; NextTurnDeg = turn;
            }
            string nm = nameIdx < m.Names.Length ? m.Names[nameIdx] : "";
            string sub = nm.Length > 0 ? Abbreviate(nm) : (k < 0 ? T.Arrive : T.Straight);
            // Box grows with the street name (up to 60 % of the screen width), as on truck navigations.
            float bw = Mathf.Clamp(150f + d.Measure(sub, 26f) + 36f, 420f, Width * 0.6f);
            d.Rect(0f, 0f, bw, bh, pal.Box);
            ManeuverIcon(d, 75f, 65f, k < 0 ? 0f : turn, pal.BoxText, k < 0);
            m_B.Clear();
            AppendDistance(m_B, dist);
            d.Text(m_B, 150f, 72f, 46f, pal.BoxText);
            d.Text(sub, 150f, 112f, 26f, pal.BoxSub);
        }

        /// <summary>Next station ahead (≥ 15 m) where the route turns by more than 35° over ±12 m; -1 if none.</summary>
        public static int FindTurn(NavMapData m, int from, out float turnDeg)
        {
            turnDeg = 0f;
            int n = m.Route.Length;
            const int w = 6;   // stations (2 m each)
            for (int k = from + 1; k < n - w; k++)
            {
                if (k - w < 0) continue;
                if (m.RouteS[k] - m.RouteS[from] < 15f) continue;
                Vector2 a = m.Route[k] - m.Route[k - w], b = m.Route[k + w] - m.Route[k];
                float ang = Vector2.SignedAngle(b, a);   // positive = clockwise = right turn (x east, y north)
                if (Mathf.Abs(ang) > 35f)
                {
                    // Walk to the sharpest point of this bend.
                    int best = k; float bestAng = ang;
                    for (int j = k + 1; j < Mathf.Min(n - w, k + 3 * w); j++)
                    {
                        float aj = Vector2.SignedAngle(m.Route[j + w] - m.Route[j], m.Route[j] - m.Route[j - w]);
                        if (Mathf.Abs(aj) > Mathf.Abs(bestAng)) { bestAng = aj; best = j; }
                    }
                    // Total turn of the manoeuvre over ±20 m.
                    int a0 = Mathf.Max(0, best - 10), a1 = Mathf.Min(n - 1, best + 10);
                    turnDeg = Vector2.SignedAngle(m.Route[Mathf.Min(n - 1, a1 + 2)] - m.Route[a1], m.Route[a0] - m.Route[Mathf.Max(0, a0 - 2)]);
                    // A local kink of the lane offset (two-way -> one-way carriageway) is not a manoeuvre.
                    if (Mathf.Abs(turnDeg) >= 30f) return best;
                    k = best + w;
                    turnDeg = 0f;
                }
            }
            return -1;
        }

        static ushort NameAfter(NavMapData m, int k)
        {
            for (int i = k; i < Mathf.Min(m.Route.Length, k + 150); i++) if (m.RouteName[i] != 0) return m.RouteName[i];
            return 0;
        }

        static ushort LastName(NavMapData m)
        {
            for (int i = m.Route.Length - 1; i >= 0; i--) if (m.RouteName[i] != 0) return m.RouteName[i];
            return 0;
        }

        /// <summary>Polish street-name abbreviations as on signs and in navigations (al., gen., rondo names kept).</summary>
        public static string Abbreviate(string name)
        {
            // Allocates only when an abbreviation applies; names repeat, so cache the result.
            if (s_AbbrevCache.TryGetValue(name, out var r)) return r;
            r = name.Replace("Aleja ", "al. ").Replace("Generała ", "gen. ").Replace("Rondo Pamięci ", "Rondo ");
            s_AbbrevCache[name] = r;
            return r;
        }

        static readonly System.Collections.Generic.Dictionary<string, string> s_AbbrevCache = new System.Collections.Generic.Dictionary<string, string>();

        public static void AppendDistance(TextBuffer b, float m)
        {
            if (m >= 1000f) b.AppendFixed(m / 1000f, m >= 10000f ? 0 : 1).Append(' ').Append(T.Km);
            else if (m >= 100f) b.Append(Mathf.RoundToInt(m / 10f) * 10).Append(' ').Append(T.M);
            else b.Append(Mathf.Max(0, Mathf.RoundToInt(m / 5f) * 5)).Append(' ').Append(T.M);
        }

        void ManeuverIcon(DisplayCanvas d, float cx, float cy, float turn, Color32 c, bool arrive)
        {
            if (arrive)
            {
                // Destination flag: pole and pennant.
                d.Rect(cx - 16f, cy - 34f, 6f, 68f, c);
                d.Triangle(new Vector2(cx - 10f, cy - 34f), new Vector2(cx + 30f, cy - 20f), new Vector2(cx - 10f, cy - 6f), c);
                return;
            }
            // Stem from below, then the turned branch with a head; |turn| < 20: straight on.
            float a = Mathf.Clamp(turn, -135f, 135f) * Mathf.Deg2Rad;
            if (Mathf.Abs(turn) < 20f) a = 0f;
            Vector2 baseP = new Vector2(cx, cy + 40f), joint = new Vector2(cx, cy + 4f);
            Vector2 dir = new Vector2(Mathf.Sin(a), -Mathf.Cos(a));
            Vector2 end = joint + dir * 30f;
            d.Line(baseP.x, baseP.y, joint.x, joint.y, 11f, c, false);
            d.Disc(joint.x, joint.y, 5.5f, c);
            d.Line(joint.x, joint.y, end.x, end.y, 11f, c, false);
            Vector2 n = new Vector2(-dir.y, dir.x);
            d.Triangle(end + dir * 20f, end + n * 16f, end - n * 16f, c);
        }

        // ------------------------------------------------------------------ speed limit + bottom bar

        void SpeedLimit(DisplayCanvas d, in P.Nav pal, bool onRoute)
        {
            if (!onRoute) return;
            int lim = m_Map.RouteLimit[RouteIndex];
            if (lim <= 0) return;
            // Generic round limit sign (white disc, red ring, black numerals) at the lower left of the map.
            const float cx = 70f, cy = MapH - 70f;
            d.Disc(cx, cy, 44f, pal.LimitFace);
            d.Ring(cx, cy, 33f, 44f, pal.Limit);
            m_B.Clear().Append(lim);
            d.Text(m_B, cx, cy + 11f, 30f, pal.LimitText, DisplayCanvas.Align.Center);
        }

        void Bar(DisplayCanvas d, in CabDisplayState s, in P.Nav pal, float remainingM, int routeIndex)
        {
            d.Rect(0f, MapH, Width, BarH, pal.Bar);
            const float by = Height - 38f;
            m_B.Clear().AppendClock(s.ClockMinutes);
            d.Text(m_B, 40f, by, 44f, pal.BarText);
            if (float.IsNaN(remainingM)) return;
            m_B.Clear();
            AppendDistance(m_B, remainingM);
            d.Text(m_B, 220f, by, 44f, pal.BarText);
            // Arrival: remaining distance at the route's speed limits would need a speed profile; urban average 30 km/h. WORKING_VALUE.
            int eta = s.ClockMinutes + Mathf.CeilToInt(remainingM / 1000f / 30f * 60f);
            m_B.Clear().Append(T.Arrive).Append(' ').AppendClock(eta);
            d.Text(m_B, 470f, by - 2f, 32f, pal.BarSub);
            ushort last = LastName(m_Map);
            string dest = last < m_Map.Names.Length ? m_Map.Names[last] : "";
            if (dest.Length > 0) d.Text(Abbreviate(dest), Width - 30f, by - 2f, 30f, pal.BarSub, DisplayCanvas.Align.Right);
        }
    }
}
