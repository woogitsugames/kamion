using Game.Core.Navigation;
using Game.UI.CabDisplays;
using UnityEngine;

namespace Game.UI.Navigation
{
    /// <summary>Map view transform: region metres -> design px (y down), rotated so that <see cref="UpDeg"/> points up.</summary>
    public struct MapXf
    {
        public float E, N, Zoom, Cx, Cy, Cos, Sin, UpDeg;

        /// <param name="upDeg">Direction (clockwise from north) shown upwards: the heading (heading-up) or 0 (north-up).</param>
        public static MapXf Make(Vector2 centre, float upDeg, float zoom, float cx, float cy)
        {
            float h = upDeg * Mathf.Deg2Rad;
            return new MapXf { E = centre.x, N = centre.y, Zoom = zoom, Cx = cx, Cy = cy, Cos = Mathf.Cos(h), Sin = Mathf.Sin(h), UpDeg = upDeg };
        }

        public Vector2 ToScreen(Vector2 p)
        {
            float x = p.x - E, y = p.y - N;
            float r = x * Cos - y * Sin, f = x * Sin + y * Cos;
            return new Vector2(Cx + r * Zoom, Cy - f * Zoom);
        }

        public Vector2 ToWorld(Vector2 s)
        {
            float r = (s.x - Cx) / Zoom, f = (Cy - s.y) / Zoom;
            // Inverse rotation: x = r cos + f sin, y = -r sin + f cos.
            return new Vector2(E + r * Cos + f * Sin, N - r * Sin + f * Cos);
        }

        /// <summary>Design px from region metres as a matrix (static underlay mesh).</summary>
        public Matrix4x4 Matrix()
        {
            var m = Matrix4x4.identity;
            m.m00 = Zoom * Cos; m.m01 = -Zoom * Sin; m.m03 = Cx - Zoom * (Cos * E - Sin * N);
            m.m10 = -Zoom * Sin; m.m11 = -Zoom * Cos; m.m13 = Cy + Zoom * (Sin * E + Cos * N);
            return m;
        }
    }

    /// <summary>
    /// Drawing shared by the full map, the HUD minimap and the guidance banner (DisplayCanvas primitives, no allocation).
    /// Look: truck-navigation / OEM style - flat colours of <see cref="DisplayPalette"/>, one route blue with a darker
    /// casing, white manoeuvre arrows on the blue banner, a generic round speed-limit sign; no brand, no logo.
    /// </summary>
    public static class NavDraw
    {
        /// <summary>Route ahead from (segment, distance) to the end: casing + fill, joints as discs, culled to the canvas.</summary>
        public static void Route(DisplayCanvas d, RoutePath p, int fromSeg, Vector2 fromPoint, in MapXf xf, float w, Color32 casing, Color32 fill,
            float viewW, float viewH)
        {
            if (p == null || !p.HasRoute) return;
            int a = Mathf.Clamp(fromSeg, 1, p.Count - 1);
            for (int pass = 0; pass < 2; pass++)
            {
                float lw = pass == 0 ? w + 4f : w;
                Color32 c = pass == 0 ? casing : fill;
                Vector2 prev = xf.ToScreen(fromSeg >= 1 ? fromPoint : p.Points[0]);
                d.Disc(prev.x, prev.y, lw * 0.5f, c);
                for (int i = a; i < p.Count; i++)
                {
                    Vector2 q = xf.ToScreen(p.Points[i]);
                    if (Visible(prev, q, lw, viewW, viewH))
                    {
                        d.Line(prev.x, prev.y, q.x, q.y, lw, c, false);
                        d.Disc(q.x, q.y, lw * 0.5f, c);
                    }
                    prev = q;
                }
            }
        }

        static bool Visible(Vector2 a, Vector2 b, float pad, float w, float h) =>
            Mathf.Max(a.x, b.x) >= -pad && Mathf.Min(a.x, b.x) <= w + pad && Mathf.Max(a.y, b.y) >= -pad && Mathf.Min(a.y, b.y) <= h + pad;

        /// <summary>Truck chevron at (x, y) pointing <paramref name="screenDeg"/> (0 = up, clockwise), outlined.</summary>
        public static void TruckArrow(DisplayCanvas d, float x, float y, float screenDeg, float size, Color32 fill, Color32 edge)
        {
            float a = screenDeg * Mathf.Deg2Rad, c = Mathf.Cos(a), s = Mathf.Sin(a);
            Vector2 R(float px, float py) => new Vector2(x + px * c - py * s, y + px * s + py * c);
            float k = size / 26f;
            Vector2 tipO = R(0f, -32f * k), lO = R(-24f * k, 23f * k), rO = R(24f * k, 23f * k), nO = R(0f, 12f * k);
            Vector2 tip = R(0f, -26f * k), l = R(-19f * k, 18f * k), r = R(19f * k, 18f * k), n = R(0f, 6f * k);
            d.Triangle(tipO, lO, nO, edge); d.Triangle(tipO, nO, rO, edge);
            d.Triangle(tip, l, n, fill); d.Triangle(tip, n, r, fill);
        }

        /// <summary>Destination flag standing on (x, y).</summary>
        public static void Flag(DisplayCanvas d, float x, float y, float h, Color32 pole, Color32 cloth)
        {
            d.Disc(x, y, h * 0.09f, pole);
            d.Rect(x - h * 0.035f, y - h, h * 0.07f, h, pole);
            d.Triangle(new Vector2(x, y - h), new Vector2(x + h * 0.55f, y - h * 0.8f), new Vector2(x, y - h * 0.58f), cloth);
        }

        /// <summary>Map pin (tap target before a route exists): disc on a stem.</summary>
        public static void Pin(DisplayCanvas d, float x, float y, float h, Color32 body, Color32 dot, Color32 edge)
        {
            d.Line(x, y, x, y - h * 0.55f, h * 0.12f, edge, false);
            d.Disc(x, y - h * 0.7f, h * 0.34f, edge);
            d.Disc(x, y - h * 0.7f, h * 0.28f, body);
            d.Disc(x, y - h * 0.7f, h * 0.1f, dot);
            d.Disc(x, y, h * 0.07f, edge);
        }

        /// <summary>
        /// Manoeuvre pictogram in a box of <paramref name="size"/> centred on (cx, cy): turn arrows (stem from below, bent
        /// branch with a head), U-turn, roundabout (ring, entry stem, exit arrow at the exit's direction) and the
        /// destination flag.
        /// </summary>
        public static void ManeuverIcon(DisplayCanvas d, float cx, float cy, float size, Maneuver type, float turnDeg, Color32 c, Color32 bg)
        {
            float k = size / 100f;
            float stroke = 12f * k;
            switch (type)
            {
                case Maneuver.Arrive:
                    Flag(d, cx - 10f * k, cy + 38f * k, 76f * k, c, c);
                    return;
                case Maneuver.UTurn:
                {
                    // Stem up, half circle, head down - turning back to the left (driving on the right).
                    float r = 18f * k, x0 = cx + r, x1 = cx - r, top = cy - 14f * k;
                    d.Line(x0, cy + 40f * k, x0, top, stroke, c, false);
                    d.Arc(cx, top, r - stroke * 0.5f, r + stroke * 0.5f, 0f, 180f, c);
                    d.Line(x1, top, x1, cy + 14f * k, stroke, c, false);
                    d.Triangle(new Vector2(x1, cy + 36f * k), new Vector2(x1 - 16f * k, cy + 12f * k), new Vector2(x1 + 16f * k, cy + 12f * k), c);
                    return;
                }
                case Maneuver.Roundabout:
                {
                    float r = 20f * k;
                    Vector2 o = new Vector2(cx, cy);
                    d.Ring(o.x, o.y, r - 5f * k, r + 5f * k, c);
                    d.Line(cx, cy + 44f * k, cx, cy + r, stroke, c, false);   // entry from below
                    float a = (Mathf.Clamp(turnDeg, -179f, 179f)) * Mathf.Deg2Rad;
                    Vector2 dir = new Vector2(Mathf.Sin(a), -Mathf.Cos(a));
                    Vector2 s0 = o + dir * r, s1 = o + dir * (r + 18f * k);
                    d.Line(s0.x, s0.y, s1.x, s1.y, stroke, c, false);
                    Vector2 n = new Vector2(-dir.y, dir.x);
                    d.Triangle(s1 + dir * 18f * k, s1 + n * 14f * k, s1 - n * 14f * k, c);
                    return;
                }
            }
            float turn = type == Maneuver.Continue ? 0f : turnDeg;
            float ang = Mathf.Clamp(turn, -150f, 150f);
            if (type == Maneuver.SlightLeft || type == Maneuver.SlightRight) ang = Mathf.Clamp(Mathf.Abs(ang), 30f, 45f) * Mathf.Sign(turn == 0f ? (type == Maneuver.SlightRight ? 1f : -1f) : turn);
            float ar = ang * Mathf.Deg2Rad;
            Vector2 baseP = new Vector2(cx, cy + 44f * k), joint = new Vector2(cx, cy + 2f * k);
            Vector2 dv = new Vector2(Mathf.Sin(ar), -Mathf.Cos(ar));
            Vector2 end = joint + dv * 26f * k;
            d.Line(baseP.x, baseP.y, joint.x, joint.y, stroke, c, false);
            d.Disc(joint.x, joint.y, stroke * 0.5f, c);
            d.Line(joint.x, joint.y, end.x, end.y, stroke, c, false);
            Vector2 nn = new Vector2(-dv.y, dv.x);
            d.Triangle(end + dv * 20f * k, end + nn * 17f * k, end - nn * 17f * k, c);
        }

        /// <summary>Generic round limit sign (white disc, red ring, black numerals).</summary>
        public static void LimitSign(DisplayCanvas d, TextBuffer b, float cx, float cy, float r, int kmh, in DisplayPalette.Nav pal)
        {
            d.Disc(cx, cy, r, pal.LimitFace);
            d.Ring(cx, cy, r * 0.76f, r, pal.Limit);
            b.Clear().Append(kmh);
            d.Text(b, cx, cy + r * 0.27f, r * (kmh >= 100 ? 0.62f : 0.72f), pal.LimitText, DisplayCanvas.Align.Center);
        }

        // ------------------------------------------------------------------ ADR 0307: road limits below the combination

        /// <summary>Value of limit <paramref name="k"/> of <paramref name="r"/> in the graph's units (0.01 t / cm).</summary>
        public static int LimitValue(in RouteRestriction r, LimitKind k) =>
            k == LimitKind.Height ? r.MaxHeightCm : k == LimitKind.Weight ? r.MaxWeightC : k == LimitKind.AxleLoad ? r.MaxAxleLoadC : r.MaxLengthCm;

        /// <summary>"3,7 m" / "12 t" (Polish decimal comma, one decimal, cut - never rounded up above the limit).</summary>
        public static void AppendLimit(TextBuffer b, LimitKind k, int centi, bool space)
        {
            b.Append(centi / 100);
            int tenths = centi % 100 / 10;
            if (tenths != 0) b.Append(',').Append(tenths);
            if (space) b.Append(' ');
            b.Append(k == LimitKind.Height || k == LimitKind.Length ? NavText.Metres : NavText.Tonnes);
        }

        /// <summary>Round prohibition sign with the limit value (schematic, like <see cref="LimitSign"/>): height with the two
        /// black triangles (B-16), weight plain (B-18); axle load / length the same disc with the value.</summary>
        public static void RestrictionSign(DisplayCanvas d, TextBuffer b, float cx, float cy, float r, float textSize, LimitKind k, int centi, bool unit,
            in DisplayPalette.Nav pal)
        {
            d.Disc(cx, cy, r, pal.LimitFace);
            d.Ring(cx, cy, r * 0.80f, r, pal.Limit);
            b.Clear();
            if (unit) AppendLimit(b, k, centi, false);
            else { b.Append(centi / 100); if (centi % 100 / 10 != 0) b.Append(',').Append(centi % 100 / 10); }
            d.Text(b, cx, cy + textSize * 0.36f, textSize, pal.LimitText, DisplayCanvas.Align.Center);
            if (k == LimitKind.Height)
            {
                float t = r * 0.17f, y0 = cy - r * 0.74f, y1 = cy + r * 0.74f;
                d.Triangle(new Vector2(cx - t, y0), new Vector2(cx + t, y0), new Vector2(cx, y0 + t * 1.2f), pal.LimitText);
                d.Triangle(new Vector2(cx - t, y1), new Vector2(cx + t, y1), new Vector2(cx, y1 - t * 1.2f), pal.LimitText);
            }
        }

        /// <summary>One sign per limit the combination exceeds, left to right from <paramref name="x"/> (centre of the first).
        /// Returns the x after the last sign.</summary>
        public static float RestrictionSigns(DisplayCanvas d, TextBuffer b, float x, float cy, float r, float textSize, float pitch,
            in RouteRestriction rs, in DisplayPalette.Nav pal)
        {
            for (int i = 0; i < 4; i++)
            {
                var k = (LimitKind)(1 << i);
                if ((rs.Exceeded & k) == 0) continue;
                RestrictionSign(d, b, x, cy, r, textSize, k, LimitValue(rs, k), true, pal);
                x += pitch;
            }
            return x - pitch + r;
        }

        /// <summary>Map marker of a limited stretch: the sign of its first exceeded limit at the screen point.</summary>
        public static void RestrictionMarker(DisplayCanvas d, TextBuffer b, Vector2 at, float r, float textSize, in RouteRestriction rs,
            in DisplayPalette.Nav pal)
        {
            for (int i = 0; i < 4; i++)
            {
                var k = (LimitKind)(1 << i);
                if ((rs.Exceeded & k) == 0) continue;
                d.Disc(at.x, at.y, r + 2f, pal.ArrowEdge);
                RestrictionSign(d, b, at.x, at.y, r, textSize, k, LimitValue(rs, k), false, pal);
                return;
            }
        }

        /// <summary>Markers of every limited stretch of the route, and of the scouted one without a route.</summary>
        public static void RestrictionMarkers(DisplayCanvas d, TextBuffer b, NavigationService nav, in MapXf xf, float r, float textSize,
            float w, float h, float top, in DisplayPalette.Nav pal)
        {
            var p = nav.Path;
            var cur = nav.Restriction;
            if (p != null && p.HasRoute)
                for (int i = 0; i < p.RestrCount; i++)
                {
                    Vector2 s = xf.ToScreen(p.Restr[i].Pos);
                    if (s.x < -r || s.x > w + r || s.y < top - r || s.y > h + r) continue;
                    RestrictionMarker(d, b, s, r, textSize, p.Restr[i], pal);
                }
            if (cur.Active && !cur.OnRoute)
            {
                Vector2 s = xf.ToScreen(cur.R.Pos);
                if (s.x >= -r && s.x <= w + r && s.y >= top - r && s.y <= h + r) RestrictionMarker(d, b, s, r, textSize, cur.R, pal);
            }
        }

        /// <summary>Warning strip: signs of the exceeded limits, "Ograniczenie" and "za 450 m" / "na tym odcinku".</summary>
        public static void RestrictionStrip(DisplayCanvas d, TextBuffer b, float x, float y, float w, float h, float labelSize, float distSize,
            float signText, in NavigationService.RestrictionWarning rw, in DisplayPalette.Nav pal)
        {
            d.Rect(x, y, w, h, pal.Bar);
            d.Rect(x, y, 5f, h, pal.Limit);
            float r = h * 0.41f;
            float tx = RestrictionSigns(d, b, x + 14f + r, y + h * 0.5f, r, signText, r * 2f + 6f, rw.R, pal) + 12f;
            d.Text(NavText.Restriction, tx, y + h * 0.40f, labelSize, pal.BarSub);
            b.Clear();
            if (rw.DistM > 0f) { b.Append(NavText.RestrictionIn).Append(' '); AppendDistance(b, rw.DistM); }
            else b.Append(NavText.RestrictionHere);
            d.Text(b, tx, y + h * 0.84f, distSize, pal.BarText);
        }

        /// <summary>North marker: small triangle + "N" at (cx, cy) for a map whose up direction is <paramref name="upDeg"/>.</summary>
        public static void North(DisplayCanvas d, float cx, float cy, float r, float upDeg, Color32 bg, Color32 fg, Color32 accent)
        {
            d.Disc(cx, cy, r, bg);
            float a = -upDeg * Mathf.Deg2Rad;   // north on screen
            Vector2 dir = new Vector2(Mathf.Sin(a), -Mathf.Cos(a)), n = new Vector2(-dir.y, dir.x);
            Vector2 o = new Vector2(cx, cy);
            d.Triangle(o + dir * r * 0.85f, o + n * r * 0.32f, o - n * r * 0.32f, accent);
            d.Triangle(o - dir * r * 0.85f, o + n * r * 0.32f, o - n * r * 0.32f, fg);
        }

        /// <summary>
        /// Lane bar under the manoeuvre banner: one cell per lane of the incoming edge (OSM order, leftmost first),
        /// an arrow per lane in its turn direction; recommended lanes in the bright banner text colour, other
        /// allowed lanes subdued, lanes that do not lead in the manoeuvre's direction dark. Flat OEM style.
        /// </summary>
        public static void LaneBar(DisplayCanvas d, RouteGraph g, int laneSrc, int count, byte cls, uint allowed, uint rec,
            float x, float y, float w, float h, in DisplayPalette.Nav pal)
        {
            if (count <= 0 || laneSrc < 0 || g == null) return;
            d.Rect(x, y, w, h, pal.Box);
            float cw = w / count;
            int e = laneSrc >> 1;
            bool rev = RouteGraph.Reversed(laneSrc);
            Color32 dim = DisplayPalette.Scale(pal.BoxText, 0.3f);
            for (int i = 0; i < count; i++)
            {
                float cx = x + cw * (i + 0.5f);
                if (i > 0) d.Line(x + cw * i, y + 3f, x + cw * i, y + h - 3f, 1.5f, DisplayPalette.Scale(pal.BoxText, 0.35f), false);
                bool isRec = (rec >> i & 1) != 0, isAllowed = (allowed >> i & 1) != 0;
                Color32 c = isRec ? pal.BoxText : isAllowed ? pal.BoxSub : dim;
                byte mask = g.LaneMask(e, rev, i);
                LaneArrow(d, cx, y + h * 0.5f, Mathf.Min(cw * 0.6f, h * 0.62f), LaneAngle(mask, cls), c);
            }
        }

        /// <summary>Screen angle of a lane arrow from its direction mask (prefers the manoeuvre's class, else the strongest turn).</summary>
        public static float LaneAngle(byte mask, byte cls)
        {
            byte m = (mask & cls) != 0 ? (byte)(mask & cls) : mask;
            if ((m & RouteGraph.LaneReverse) != 0) return 180f;
            if ((m & RouteGraph.LaneRight) != 0) return 90f;
            if ((m & (RouteGraph.LaneSlightRight | RouteGraph.LaneMergeToRight)) != 0) return 40f;
            if ((m & RouteGraph.LaneThrough) != 0) return 0f;
            if ((m & (RouteGraph.LaneSlightLeft | RouteGraph.LaneMergeToLeft)) != 0) return -40f;
            if ((m & RouteGraph.LaneLeft) != 0) return -90f;
            return 0f;
        }

        /// <summary>Small straight arrow centred on (cx, cy), pointing up rotated by <paramref name="angleDeg"/> (clockwise).</summary>
        public static void LaneArrow(DisplayCanvas d, float cx, float cy, float size, float angleDeg, Color32 c)
        {
            float a = angleDeg * Mathf.Deg2Rad, co = Mathf.Cos(a), si = Mathf.Sin(a);
            Vector2 R(float px, float py) => new Vector2(cx + px * co - py * si, cy + px * si + py * co);
            float k = size / 24f;
            Vector2 tail = R(0f, 11f * k), joint = R(0f, 0f), tip = R(0f, -11f * k);
            d.Line(tail.x, tail.y, joint.x, joint.y, 5f * k, c, false);
            Vector2 bl = R(-5.5f * k, 1f * k), br = R(5.5f * k, 1f * k);
            d.Triangle(tip, bl, br, c);
        }

        public static void AppendDistance(TextBuffer b, float m) => NavLayout.AppendDistance(b, m);

        /// <summary>
        /// Text that must fit <paramref name="maxWidth"/>: drawn at <paramref name="size"/>, else at most 15 % smaller,
        /// else cut with "..." (street names like "Rondo Krzysztofa Jakuba Putry ..."). No allocation (<paramref name="b"/>).
        /// </summary>
        public static void FitText(DisplayCanvas d, TextBuffer b, string s, float x, float baseline, float size, float maxWidth, Color32 c,
            DisplayCanvas.Align align = DisplayCanvas.Align.Left)
        {
            if (string.IsNullOrEmpty(s)) return;
            if (d.Measure(s, size) <= maxWidth) { d.Text(s, x, baseline, size, c, align); return; }
            float small = size * 0.85f;
            if (d.Measure(s, small) <= maxWidth) { d.Text(s, x, baseline, small, c, align); return; }
            float dots = d.Measure("...", small);
            b.Clear();
            for (int i = 0; i < s.Length; i++)
            {
                b.Append(s[i]);
                if (d.Measure(b, small) + dots > maxWidth) { b.Clear(); b.Append(s, i); break; }
            }
            b.Append("...");
            d.Text(b, x, baseline, small, c, align);
        }
    }
}
