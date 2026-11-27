using UnityEngine;

namespace Game.Controls
{
    /// <summary>What the monitor HUD shows right now (ADR 0283). Content canvas units (<see cref="HudScaleModel"/>: always
    /// 1440 units high, 16:9 at most - ultrawide monitors get the same centred content).</summary>
    public struct DesktopHudInput
    {
        public float Width, Height;
        /// <summary>Speed / gear / air strip shown (false = telltale row only: cab view with live cab instruments).</summary>
        public bool Strip;
        /// <summary>Extended detail (rev counter, endurance brake, brake cruise, trailer) - a second row of the strip.</summary>
        public bool Extended;
        public bool MirrorLeft, MirrorRight;
        /// <summary>Glass aspect (width / height) of the mirror texture; &lt;= 0 = <see cref="DesktopHudLayout.DefaultMirrorAspect"/>.</summary>
        public float MirrorAspect;
        /// <summary>Player preferences (<see cref="HudPrefsData"/>): size (fraction of the height; &lt;= 0 = default),
        /// vertical drop 0..1, inset towards the centre 0..1.</summary>
        public float MirrorSize, MirrorDrop, MirrorInset;
        /// <summary>ADR 0340 addendum: the class IV (wide-angle) glass of the mirror head has a picture (both sides).</summary>
        public bool MirrorWide;
        public bool ReverseView;
        /// <summary>The "Panel" button (developer / lab page) is on screen (extended detail or developer diagnostics).</summary>
        public bool DevToggle;
        public bool DevPanelOpen, Telemetry, DevText;
        /// <summary>Cab view with live cab instruments and the extended detail on (<see cref="HudVisibility.Compact"/>): the
        /// strip carries only the extended row (the dash cluster shows speed / gear / air) and the whole block moves to the
        /// right, over the centre of the dash - off the steering wheel and the cluster (int-ui-s23 §7 p.4).</summary>
        public bool Compact;
        /// <summary>Full window width in the same units (&gt; <see cref="Width"/> on ultrawide monitors, where the content is
        /// narrowed to 16:9); 0 = same as <see cref="Width"/>. The mirror windows may use the side bands (§7 p.6).</summary>
        public float ScreenWidth;

        public bool SameAs(in DesktopHudInput o) =>
            Width == o.Width && Height == o.Height && Strip == o.Strip && Extended == o.Extended && MirrorLeft == o.MirrorLeft
            && MirrorRight == o.MirrorRight && MirrorAspect == o.MirrorAspect && MirrorSize == o.MirrorSize && MirrorDrop == o.MirrorDrop
            && MirrorInset == o.MirrorInset && ReverseView == o.ReverseView && DevToggle == o.DevToggle && DevPanelOpen == o.DevPanelOpen
            && Telemetry == o.Telemetry && DevText == o.DevText && Compact == o.Compact && ScreenWidth == o.ScreenWidth
            && MirrorWide == o.MirrorWide;
    }

    /// <summary>Monitor HUD zones, content canvas units, origin bottom-left, y up.</summary>
    public struct DesktopHudResult
    {
        public Rect Strip, Telltales, ReverseView, MirrorLeft, MirrorRight, DevToggle, DevPanel, Telemetry, DevText;
        /// <summary>GPS widget (guidance banner + minimap, ADR 0150): bottom-left column, under or beside the left mirror.</summary>
        public Rect Nav;
        /// <summary>Kept free of HUD furniture except the reversing view (which replaces the road view while reversing) and
        /// the developer overlays: the road ahead between the mirrors.</summary>
        public Rect ClearView;
        public bool ShowStrip, ShowMirrorLeft, ShowMirrorRight, ShowReverseView, ShowDevToggle, ShowDevPanel, ShowTelemetry, ShowDevText;
        /// <summary>The GPS widget fits (and the developer telemetry does not use that corner).</summary>
        public bool ShowNav;
        /// <summary>Compact cab block (extended row only, right of the wheel) is laid out.</summary>
        public bool Compact;
        /// <summary>How far the mirror windows may reach outside the content on each side (ultrawide side band; units).</summary>
        public float MirrorOutboard;
        /// <summary>ADR 0340 addendum: wide-angle (class IV) glass of each mirror head, directly under the main window, same
        /// width. Decoration of the window, not a zone of its own: shown only when both fit without touching another zone
        /// (<see cref="ShowMirrorWide"/>); the main windows never move or shrink for it.</summary>
        public Rect MirrorWideLeft, MirrorWideRight;
        public bool ShowMirrorWide;

        public const int ZoneCount = 10;
        static readonly string[] k_Names = { "Strip", "Telltales", "ReverseView", "MirrorLeft", "MirrorRight", "DevToggle", "DevPanel", "Telemetry", "DevText", "Nav" };
        public static string ZoneName(int i) => k_Names[i];

        /// <summary>Zone <paramref name="i"/>; returns whether it is on screen.</summary>
        public bool Zone(int i, out Rect r)
        {
            switch (i)
            {
                case 0: r = Strip; return ShowStrip;
                case 1: r = Telltales; return true;
                case 2: r = ReverseView; return ShowReverseView;
                case 3: r = MirrorLeft; return ShowMirrorLeft;
                case 4: r = MirrorRight; return ShowMirrorRight;
                case 5: r = DevToggle; return ShowDevToggle;
                case 6: r = DevPanel; return ShowDevPanel;
                case 7: r = Telemetry; return ShowTelemetry;
                case 8: r = DevText; return ShowDevText;
                default: r = Nav; return ShowNav;
            }
        }
    }

    /// <summary>
    /// Monitor driving HUD (ADR 0283, D84). Replaces the floating top cluster of ADR 0265 on a PC:
    /// bottom centre = one low strip like the display in a dashboard (telltale row with the turn-signal arrows and the
    /// active warnings, under it speed / gear / both air circuits; the extended detail adds one row); the mirror windows
    /// sit at the outer edges at the height of real class II mirrors in the field of view, larger than before and
    /// adjustable (size, height, inset); the road between them (<see cref="DesktopHudResult.ClearView"/>) stays free;
    /// reversing camera top centre (where the inside mirror would be); developer button bottom right, its panel above.
    /// alt-ui-polish-s23 (int-ui-s23 §7 p.4-6): the telltale row sits directly on the strip (one block, one panel, arrows
    /// inside it), the "Panel" button is attached to the block's right edge; in the cab with live instruments the extended
    /// detail is a compact block right of the wheel without the speed (no double speed over the dash cluster); on
    /// ultrawide monitors the mirror windows go out to the window edges (side bands, capped) instead of covering the right
    /// lane; the free road view is 45 % of the content width.
    /// Pure, no allocation, unit-tested on 16:9, 21:9 and 32:9 (EditMode). All sizes WORKING_VALUE (owner's monitor).
    /// </summary>
    public static class DesktopHudLayout
    {
        public const float Margin = 32f, Gap = 16f;
        public static readonly Vector2 StripSize = new Vector2(720f, 112f);
        /// <summary>Second row of the extended detail (rev counter, endurance brake, brake cruise, trailer).</summary>
        public const float ExtendedRowHeight = 84f;
        public static readonly Vector2 TelltaleSize = new Vector2(720f, 52f);
        public static readonly Vector2 ReverseSize = new Vector2(560f, 316f);
        public static readonly Vector2 DevToggleSize = new Vector2(150f, 56f);
        public static readonly Vector2 DevPanelSize = new Vector2(424f, 378f);
        public const float TelemetryMaxWidth = 760f, TelemetryWideEnough = 640f, TelemetryMaxHeight = 600f;
        public const float DevTextHeight = 112f, DevTextWidth = 760f;
        /// <summary>Width of the free road view between the mirror windows, as a fraction of the content width. WORKING_VALUE
        /// (0.40 in ADR 0283; 0.45 since §7 p.6 - an inset window covered the right lane; more would push the developer panel
        /// into it on a portrait window).</summary>
        public const float ClearViewFraction = 0.45f;
        /// <summary>Gap between the HUD block and the "Panel" button attached to it.</summary>
        public const float ToggleGap = 8f;
        /// <summary>Ultrawide: the mirror windows reach into the side band by at most this fraction of the content width. WORKING_VALUE.</summary>
        public const float MirrorOutboardMaxFraction = 0.25f;
        public const float DefaultMirrorAspect = 0.55f;
        /// <summary>Smallest useful mirror window height; below it the windows are hidden (never drawn squashed). WORKING_VALUE.</summary>
        public const float MirrorMinHeight = 200f;
        /// <summary>Inset of the mirror glass inside its window [units]. ADR 0340: 6 - the glass sits under the lip of a
        /// 7-unit housing ring with rounded corners (Game.UI.Driving.MirrorWindowArt); it was 3 (ADR 0283: "a thin
        /// housing edge", which read as a raw picture-in-picture rectangle on the build, critic s24 build #5 p. 5). The
        /// window rect itself is unchanged. WORKING_VALUE (owner to judge on the build).</summary>
        public const float MirrorBezel = 6f;
        /// <summary>ADR 0340 addendum (critic build #10 p.8): gap between the main window and the wide-angle glass under it
        /// (the head's cross web) [units]. WORKING_VALUE.</summary>
        public const float MirrorWideGap = 16f;
        /// <summary>Width / height of the wide-angle glass as drawn. The class IV texture is taller (about 0.9-1.0): the
        /// window shows its lower part (road, kerb, trailer wheels), cropped, never squashed. WORKING_VALUE.</summary>
        public const float MirrorWideAspect = 1.30f;
        /// <summary>Room the mirror head needs around its glasses (moulded edge + contact shadow, Game.UI.Driving.MirrorWindowArt)
        /// [units]: the wide-angle glass is shown only when this much stays free below it.</summary>
        public const float MirrorHeadClear = 18f;

        public static float StripHeight(bool extended) => StripSize.y + (extended ? ExtendedRowHeight : 0f);

        public static void Solve(in DesktopHudInput s, out DesktopHudResult r)
        {
            r = default;
            float w = s.Width, h = s.Height, cx = w * 0.5f, top = h - Margin;

            // ---- one block at the bottom: strip with the telltale row directly on it (or the row alone), "Panel" button
            // attached to the right. Centred; the compact cab block sits right of the wheel (never left of the centre).
            r.ShowStrip = s.Strip || s.Extended;
            r.Compact = s.Compact && r.ShowStrip;
            float stripH = r.ShowStrip ? (r.Compact ? ExtendedRowHeight : StripHeight(s.Extended)) : 0f;
            r.ShowDevToggle = s.DevToggle || s.DevPanelOpen;
            float toggleRoom = r.ShowDevToggle ? DevToggleSize.x + ToggleGap : 0f;
            float gx = cx - StripSize.x * 0.5f;
            if (r.Compact) gx = Mathf.Max(gx, w - Margin - toggleRoom - StripSize.x);
            r.Strip = new Rect(gx, Margin, StripSize.x, stripH);
            float ty = r.ShowStrip ? r.Strip.yMax : Margin;
            r.Telltales = new Rect(gx, ty, TelltaleSize.x, TelltaleSize.y);
            r.DevToggle = new Rect(gx + StripSize.x + ToggleGap, Margin, DevToggleSize.x, DevToggleSize.y);

            // ---- developer text above the telltales; developer panel at the right edge above the button (and above the
            // block when the compact block reaches under it)
            r.ShowDevText = s.DevText;
            r.DevText = new Rect(cx - DevTextWidth * 0.5f, r.Telltales.yMax + Gap, DevTextWidth, DevTextHeight);
            r.ShowDevPanel = s.DevPanelOpen;
            float dpx = w - Margin - DevPanelSize.x, dpy = r.DevToggle.yMax;
            if (r.Telltales.xMax > dpx) dpy = Mathf.Max(dpy, r.Telltales.yMax);
            r.DevPanel = new Rect(dpx, dpy + 8f, DevPanelSize.x, DevPanelSize.y);

            // ---- top centre: reversing view
            r.ShowReverseView = s.ReverseView;
            r.ReverseView = new Rect(cx - ReverseSize.x * 0.5f, top - ReverseSize.y, ReverseSize.x, ReverseSize.y);

            // ---- clear road view between the mirrors
            float clearW = Mathf.Max(Mathf.Max(ClearViewFraction * w, DevTextWidth), Mathf.Max(r.Telltales.width, r.ReverseView.width));
            float clearBottom = Mathf.Max(r.Telltales.yMax, r.ShowDevText ? r.DevText.yMax : 0f) + Gap;
            r.ClearView = new Rect(cx - clearW * 0.5f, clearBottom, clearW, Mathf.Max(0f, top - clearBottom));

            // ---- mirror windows: outer edges, size from the content height, glass aspect kept
            SolveMirrors(s, ref r);

            // ---- developer overlays win over a mirror window they would cover (developer features only)
            if (r.ShowDevPanel && r.ShowMirrorRight && r.DevPanel.Overlaps(r.MirrorRight)) r.ShowMirrorRight = false;
            r.ShowTelemetry = s.Telemetry;
            if (s.Telemetry)
            {
                float x0 = r.ShowMirrorLeft ? Mathf.Max(Margin, r.MirrorLeft.xMax + Gap) : Margin;
                float limit = cx - ReverseSize.x * 0.5f - Gap;
                if (r.ShowMirrorLeft && limit - x0 < TelemetryWideEnough)
                {
                    r.ShowMirrorLeft = false;
                    x0 = Margin;
                }
                float tw = Mathf.Max(0f, Mathf.Min(TelemetryMaxWidth, limit - x0));
                float tbottom = Margin;
                float th = Mathf.Min(TelemetryMaxHeight, top - tbottom);
                r.Telemetry = new Rect(x0, top - th, tw, th);
            }
            SolveNav(s, ref r);
            SolveMirrorWide(s, ref r);
        }

        /// <summary>ADR 0340 addendum: the wide-angle glasses under the main windows - only when both main windows are on
        /// screen and both wide glasses (with the head's edge) clear every other zone; otherwise the heads carry the main
        /// glass only. Developer telemetry on = off (it uses that column).</summary>
        static void SolveMirrorWide(in DesktopHudInput s, ref DesktopHudResult r)
        {
            r.ShowMirrorWide = false;
            float wh = r.MirrorLeft.width / MirrorWideAspect;
            r.MirrorWideLeft = new Rect(r.MirrorLeft.x, r.MirrorLeft.yMin - MirrorWideGap - wh, r.MirrorLeft.width, wh);
            r.MirrorWideRight = new Rect(r.MirrorRight.x, r.MirrorRight.yMin - MirrorWideGap - wh, r.MirrorRight.width, wh);
            if (!s.MirrorWide || !r.ShowMirrorLeft || !r.ShowMirrorRight || s.Telemetry || wh < 60f) return;
            Rect a = Grow(r.MirrorWideLeft, MirrorHeadClear), b = Grow(r.MirrorWideRight, MirrorHeadClear);
            if (a.yMin < Margin - MirrorHeadClear) return;
            for (int i = 0; i < DesktopHudResult.ZoneCount; i++)
            {
                if (i == 3 || i == 4 || !r.Zone(i, out Rect z)) continue;
                if (Intersects(a, z) || Intersects(b, z)) return;
            }
            r.ShowMirrorWide = true;
        }

        static Rect Grow(Rect r, float by) => new Rect(r.x - by, r.y - by, r.width + 2f * by, r.height + 2f * by);

        /// <summary>GPS widget size (ADR 0150 NavHudLayout: preferred 340 x 440, minimum 220 x 250 units).</summary>
        public static readonly Vector2 NavPreferred = new Vector2(340f, 440f), NavMinimum = new Vector2(220f, 250f);

        /// <summary>GPS widget: bottom-left, left of the strip and the clear view; under the left mirror window when the
        /// column below it is tall enough, otherwise beside it. Hidden while the developer telemetry is on.</summary>
        static void SolveNav(in DesktopHudInput s, ref DesktopHudResult r)
        {
            r.ShowNav = false;
            if (s.Telemetry) return;
            float top = s.Height - Margin;
            float x1 = Mathf.Min(r.ClearView.xMin, r.Telltales.xMin) - Gap;
            if (r.ShowStrip) x1 = Mathf.Min(x1, r.Strip.xMin - Gap);
            if (r.ShowDevToggle) x1 = Mathf.Min(x1, r.DevToggle.xMin - Gap);
            // under the mirror (full column)
            float yTop = r.ShowMirrorLeft ? r.MirrorLeft.yMin - Gap : top;
            float w = Mathf.Min(NavPreferred.x, x1 - Margin), h = Mathf.Min(NavPreferred.y, yTop - Margin);
            if (w >= NavMinimum.x && h >= NavMinimum.y) { r.Nav = new Rect(Margin, Margin, w, h); r.ShowNav = true; return; }
            if (!r.ShowMirrorLeft) return;
            // beside the mirror (between it and the clear view)
            float x0 = Mathf.Max(Margin, r.MirrorLeft.xMax + Gap);
            w = Mathf.Min(NavPreferred.x, x1 - x0); h = Mathf.Min(NavPreferred.y, top - Margin);
            if (w >= NavMinimum.x && h >= NavMinimum.y) { r.Nav = new Rect(x0, Margin, w, h); r.ShowNav = true; }
        }

        /// <summary>Mirror window size and place (both windows the same size, mirrored about the centre).</summary>
        static void SolveMirrors(in DesktopHudInput s, ref DesktopHudResult r)
        {
            float w = s.Width, h = s.Height, top = h - Margin;
            float aspect = s.MirrorAspect > 0.05f ? s.MirrorAspect : DefaultMirrorAspect;
            float size = s.MirrorSize > 0f ? Mathf.Clamp(s.MirrorSize, HudPreferences.MirrorSizeMin, HudPreferences.MirrorSizeMax) : HudPreferences.MirrorSizeDefault;
            float drop = Mathf.Clamp01(s.MirrorDrop), inset = Mathf.Clamp01(s.MirrorInset);

            // Ultrawide: the content is 16:9 in the middle; the windows may go out into the side band (capped), so they sit
            // at the window edges like real mirrors instead of over the right lane (§7 p.6).
            float band = s.ScreenWidth > w ? Mathf.Min((s.ScreenWidth - w) * 0.5f, MirrorOutboardMaxFraction * w) : 0f;
            r.MirrorOutboard = band;
            float outer = Margin - band;
            float room = r.ClearView.xMin - Gap - outer;   // outer edge .. clear view, per side

            // Bottom limit: the content edge, or above any part of the HUD block that reaches under a mirror column.
            float bottom = Margin;
            bottom = AboveIfUnderColumn(bottom, r.ShowStrip, r.Strip, outer, room, w);
            bottom = AboveIfUnderColumn(bottom, true, r.Telltales, outer, room, w);
            bottom = AboveIfUnderColumn(bottom, r.ShowDevToggle, r.DevToggle, outer, room, w);

            float mh = Mathf.Min(size * h, top - bottom);
            float mw = mh * aspect;
            if (mw > room) { mw = Mathf.Max(0f, room); mh = mw / aspect; }
            bool fits = mh >= MirrorMinHeight - 1e-3f;

            float xLeft = outer + inset * Mathf.Max(0f, room - mw);
            float yTop = top - drop * Mathf.Max(0f, top - bottom - mh);
            r.MirrorLeft = new Rect(xLeft, yTop - mh, mw, mh);
            r.MirrorRight = new Rect(w - xLeft - mw, yTop - mh, mw, mh);
            r.ShowMirrorLeft = s.MirrorLeft && fits;
            r.ShowMirrorRight = s.MirrorRight && fits;
        }

        /// <summary>Raises <paramref name="bottom"/> above <paramref name="z"/> when it lies under the left or the right mirror
        /// column (outer edge .. clear view).</summary>
        static float AboveIfUnderColumn(float bottom, bool shown, Rect z, float outer, float room, float w)
        {
            if (!shown) return bottom;
            float lx0 = outer, lx1 = outer + room, rx0 = w - outer - room, rx1 = w - outer;
            bool under = (z.xMin < lx1 && z.xMax > lx0) || (z.xMin < rx1 && z.xMax > rx0);
            return under ? Mathf.Max(bottom, z.yMax + Gap) : bottom;
        }

        /// <summary>True when <paramref name="inner"/> lies inside <paramref name="outer"/> (tolerance <paramref name="eps"/>).</summary>
        public static bool Inside(Rect inner, Rect outer, float eps = 0.5f) =>
            inner.xMin >= outer.xMin - eps && inner.yMin >= outer.yMin - eps && inner.xMax <= outer.xMax + eps && inner.yMax <= outer.yMax + eps;

        /// <summary>Two rects share area (touching edges do not count).</summary>
        public static bool Intersects(Rect a, Rect b, float eps = 0.01f) =>
            a.xMin < b.xMax - eps && b.xMin < a.xMax - eps && a.yMin < b.yMax - eps && b.yMin < a.yMax - eps;
    }
}
