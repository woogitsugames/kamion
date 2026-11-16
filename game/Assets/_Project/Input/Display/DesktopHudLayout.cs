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
        public bool ReverseView;
        /// <summary>The "Panel" button (developer / lab page) is on screen (extended detail or developer diagnostics).</summary>
        public bool DevToggle;
        public bool DevPanelOpen, Telemetry, DevText;

        public bool SameAs(in DesktopHudInput o) =>
            Width == o.Width && Height == o.Height && Strip == o.Strip && Extended == o.Extended && MirrorLeft == o.MirrorLeft
            && MirrorRight == o.MirrorRight && MirrorAspect == o.MirrorAspect && MirrorSize == o.MirrorSize && MirrorDrop == o.MirrorDrop
            && MirrorInset == o.MirrorInset && ReverseView == o.ReverseView && DevToggle == o.DevToggle && DevPanelOpen == o.DevPanelOpen
            && Telemetry == o.Telemetry && DevText == o.DevText;
    }

    /// <summary>Monitor HUD zones, content canvas units, origin bottom-left, y up.</summary>
    public struct DesktopHudResult
    {
        public Rect Strip, Telltales, ReverseView, MirrorLeft, MirrorRight, DevToggle, DevPanel, Telemetry, DevText;
        /// <summary>Kept free of HUD furniture except the reversing view (which replaces the road view while reversing) and
        /// the developer overlays: the road ahead between the mirrors.</summary>
        public Rect ClearView;
        public bool ShowStrip, ShowMirrorLeft, ShowMirrorRight, ShowReverseView, ShowDevToggle, ShowDevPanel, ShowTelemetry, ShowDevText;

        public const int ZoneCount = 9;
        static readonly string[] k_Names = { "Strip", "Telltales", "ReverseView", "MirrorLeft", "MirrorRight", "DevToggle", "DevPanel", "Telemetry", "DevText" };
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
                default: r = DevText; return ShowDevText;
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
        /// <summary>Width of the free road view between the mirror windows, as a fraction of the content width. WORKING_VALUE.</summary>
        public const float ClearViewFraction = 0.40f;
        public const float DefaultMirrorAspect = 0.55f;
        /// <summary>Smallest useful mirror window height; below it the windows are hidden (never drawn squashed). WORKING_VALUE.</summary>
        public const float MirrorMinHeight = 200f;
        /// <summary>Frame around the mirror image [units] (the image is inset by this much).</summary>
        public const float MirrorBezel = 6f;

        public static float StripHeight(bool extended) => StripSize.y + (extended ? ExtendedRowHeight : 0f);

        public static void Solve(in DesktopHudInput s, out DesktopHudResult r)
        {
            r = default;
            float w = s.Width, h = s.Height, cx = w * 0.5f, top = h - Margin;

            // ---- bottom centre: strip, telltale row on top of it (or alone at the bottom)
            r.ShowStrip = s.Strip || s.Extended;
            float stripH = r.ShowStrip ? StripHeight(s.Extended) : 0f;
            r.Strip = new Rect(cx - StripSize.x * 0.5f, Margin, StripSize.x, stripH);
            float ty = r.ShowStrip ? r.Strip.yMax + 8f : Margin;
            r.Telltales = new Rect(cx - TelltaleSize.x * 0.5f, ty, TelltaleSize.x, TelltaleSize.y);

            // ---- developer text above the telltales, developer button bottom right
            r.ShowDevText = s.DevText;
            r.DevText = new Rect(cx - DevTextWidth * 0.5f, r.Telltales.yMax + Gap, DevTextWidth, DevTextHeight);
            r.ShowDevToggle = s.DevToggle || s.DevPanelOpen;
            r.DevToggle = new Rect(w - Margin - DevToggleSize.x, Margin, DevToggleSize.x, DevToggleSize.y);
            r.ShowDevPanel = s.DevPanelOpen;
            r.DevPanel = new Rect(w - Margin - DevPanelSize.x, r.DevToggle.yMax + 8f, DevPanelSize.x, DevPanelSize.y);

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
                float x0 = r.ShowMirrorLeft ? r.MirrorLeft.xMax + Gap : Margin;
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
        }

        /// <summary>Mirror window size and place (both windows the same size, mirrored about the centre).</summary>
        static void SolveMirrors(in DesktopHudInput s, ref DesktopHudResult r)
        {
            float w = s.Width, h = s.Height, top = h - Margin;
            float aspect = s.MirrorAspect > 0.05f ? s.MirrorAspect : DefaultMirrorAspect;
            float size = s.MirrorSize > 0f ? Mathf.Clamp(s.MirrorSize, HudPreferences.MirrorSizeMin, HudPreferences.MirrorSizeMax) : HudPreferences.MirrorSizeDefault;
            float drop = Mathf.Clamp01(s.MirrorDrop), inset = Mathf.Clamp01(s.MirrorInset);

            // Bottom limit: the content edge, or above the developer button when it is on screen under the right window.
            float bottom = Margin;
            if (r.ShowDevToggle) bottom = Mathf.Max(bottom, r.DevToggle.yMax + Gap);

            float mh = Mathf.Min(size * h, top - bottom);
            float mw = mh * aspect;
            float room = r.ClearView.xMin - Gap - Margin;   // outer edge .. clear view, per side
            if (mw > room) { mw = Mathf.Max(0f, room); mh = mw / aspect; }
            bool fits = mh >= MirrorMinHeight - 1e-3f;

            float xLeft = Margin + inset * Mathf.Max(0f, room - mw);
            float yTop = top - drop * Mathf.Max(0f, top - bottom - mh);
            r.MirrorLeft = new Rect(xLeft, yTop - mh, mw, mh);
            r.MirrorRight = new Rect(w - xLeft - mw, yTop - mh, mw, mh);
            r.ShowMirrorLeft = s.MirrorLeft && fits;
            r.ShowMirrorRight = s.MirrorRight && fits;
        }

        /// <summary>True when <paramref name="inner"/> lies inside <paramref name="outer"/> (tolerance <paramref name="eps"/>).</summary>
        public static bool Inside(Rect inner, Rect outer, float eps = 0.5f) =>
            inner.xMin >= outer.xMin - eps && inner.yMin >= outer.yMin - eps && inner.xMax <= outer.xMax + eps && inner.yMax <= outer.yMax + eps;

        /// <summary>Two rects share area (touching edges do not count).</summary>
        public static bool Intersects(Rect a, Rect b, float eps = 0.01f) =>
            a.xMin < b.xMax - eps && b.xMin < a.xMax - eps && a.yMin < b.yMax - eps && b.yMin < a.yMax - eps;
    }
}
