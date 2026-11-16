using UnityEngine;

namespace Game.Controls
{
    /// <summary>Where the diagnostics text panel goes (ADR 0276). Collapsed = not shown while the start menu is open
    /// (no room without covering the menu); it comes back when the menu closes.</summary>
    public enum OverlayPanelPlace : byte { TopLeft, BottomLeft, Collapsed }

    /// <summary>Where the three diagnostics buttons go (ADR 0276): a column or a row in a right-hand corner.</summary>
    public enum OverlayButtonsPlace : byte { ColumnTopRight, ColumnBottomRight, RowBottomRight, RowTopRight }

    /// <summary>Input of <see cref="MenuOverlayLayout.Solve"/>. All rects in canvas units of the content rect
    /// (<see cref="HudScaleModel"/>), origin at its centre, y up (the coordinates the start menu is placed in).</summary>
    public struct MenuOverlayInput
    {
        /// <summary>Content size in canvas units (<see cref="HudScaleResult.SizeUnits"/>).</summary>
        public Vector2 ContentUnits;
        /// <summary>The start menu is on screen; <see cref="MenuBlock"/> is its bounding box before any shift.</summary>
        public bool HasMenu;
        public Rect MenuBlock;
        /// <summary>The diagnostics overlay exists (buttons always, panel when <see cref="PanelShown"/>).</summary>
        public bool HasOverlay;
        /// <summary>The player / tester wants the text panel ("Ukryj" / "Diagnostyka" button).</summary>
        public bool PanelShown;
        /// <summary>Size reserved for the text panel (the largest measured so far, <see cref="MenuOverlayLayout.ReservePanel"/>).</summary>
        public Vector2 PanelSize;
        /// <summary>One button and the spacing between buttons.</summary>
        public Vector2 ButtonSize;
        public float ButtonSpacing;
    }

    public struct MenuOverlayResult
    {
        /// <summary>Vertical offset applied to the whole start-menu block (negative = down).</summary>
        public float MenuShiftY;
        public OverlayPanelPlace Panel;
        public OverlayButtonsPlace Buttons;
        /// <summary>Final rects (centre origin, y up). Empty when the item is not shown.</summary>
        public Rect MenuRect, PanelRect, ButtonsRect;
        /// <summary>False only when no candidate avoids every overlap (fallback layout, the overlay may cover the menu).</summary>
        public bool Fits;

        public bool SameAs(in MenuOverlayResult o) =>
            MenuShiftY == o.MenuShiftY && Panel == o.Panel && Buttons == o.Buttons && Fits == o.Fits
            && MenuRect == o.MenuRect && PanelRect == o.PanelRect && ButtonsRect == o.ButtonsRect;
    }

    /// <summary>
    /// ADR 0276 (integration s23 P2): the diagnostics overlay (text panel top-left, three buttons top-right) covered the
    /// title and the first button of the start menu. One pure layout for both: candidates for the panel (top-left,
    /// bottom-left, collapsed) and the buttons (column / row in a right corner) are tried in a fixed order of
    /// preference; for each the start menu may move vertically inside the content rect; the first candidate where the
    /// menu, the panel and the buttons are pairwise apart by <see cref="Gap"/> wins, with the smallest menu shift.
    /// Without a menu the overlay keeps its historic place (panel top-left, column top-right). Without an overlay the
    /// menu never moves. Pure maths, no Unity objects, no allocation (runs every frame in the overlay and the menu).
    /// Lives in Game.Controls next to <see cref="HudScaleModel"/> because the EditMode tests do not see Game.UI.
    /// </summary>
    public static class MenuOverlayLayout
    {
        /// <summary>Distance of the overlay from the content edge [units] (the overlay used 24 before ADR 0276).</summary>
        public const float Margin = 24f;
        /// <summary>Minimum clearance between the menu, the panel and the buttons [units]. WORKING_VALUE.</summary>
        public const float Gap = 16f;
        public const int ButtonCount = 3;
        /// <summary>Panel size reserved before the first measurement [units] (7 lines of 30 px text). WORKING_VALUE.</summary>
        public static readonly Vector2 DefaultPanelSize = new Vector2(1180f, 300f);
        /// <summary>The reserved panel size grows in steps of this many units, so FPS digits do not move the menu.</summary>
        public const float ReserveStep = 20f;

        // Order of preference (panel, buttons). Collapsed comes last: the panel is shown whenever it fits.
        static readonly OverlayPanelPlace[] k_Panels = { OverlayPanelPlace.TopLeft, OverlayPanelPlace.BottomLeft, OverlayPanelPlace.Collapsed };
        static readonly OverlayButtonsPlace[] k_Buttons =
            { OverlayButtonsPlace.ColumnTopRight, OverlayButtonsPlace.ColumnBottomRight, OverlayButtonsPlace.RowBottomRight, OverlayButtonsPlace.RowTopRight };

        /// <summary>Reserved panel size: never smaller than before (monotonic) and rounded up to <see cref="ReserveStep"/>.</summary>
        public static Vector2 ReservePanel(Vector2 reserved, Vector2 measured)
        {
            float w = Mathf.Max(reserved.x, Ceil(measured.x)), h = Mathf.Max(reserved.y, Ceil(measured.y));
            return new Vector2(w, h);
        }

        static float Ceil(float v) => v <= 0f ? 0f : (float)System.Math.Ceiling(v / ReserveStep) * ReserveStep;

        public static Vector2 ColumnSize(Vector2 button, float spacing) =>
            new Vector2(button.x, ButtonCount * button.y + (ButtonCount - 1) * spacing);

        public static Vector2 RowSize(Vector2 button, float spacing) =>
            new Vector2(ButtonCount * button.x + (ButtonCount - 1) * spacing, button.y);

        public static Rect PanelRectFor(OverlayPanelPlace place, Vector2 content, Vector2 size)
        {
            float hw = content.x * 0.5f, hh = content.y * 0.5f;
            switch (place)
            {
                case OverlayPanelPlace.TopLeft: return new Rect(-hw + Margin, hh - Margin - size.y, size.x, size.y);
                case OverlayPanelPlace.BottomLeft: return new Rect(-hw + Margin, -hh + Margin, size.x, size.y);
                default: return default;
            }
        }

        public static Rect ButtonsRectFor(OverlayButtonsPlace place, Vector2 content, Vector2 button, float spacing)
        {
            float hw = content.x * 0.5f, hh = content.y * 0.5f;
            bool column = place == OverlayButtonsPlace.ColumnTopRight || place == OverlayButtonsPlace.ColumnBottomRight;
            bool top = place == OverlayButtonsPlace.ColumnTopRight || place == OverlayButtonsPlace.RowTopRight;
            Vector2 s = column ? ColumnSize(button, spacing) : RowSize(button, spacing);
            float x = hw - Margin - s.x;
            float y = top ? hh - Margin - s.y : -hh + Margin;
            return new Rect(x, y, s.x, s.y);
        }

        /// <summary>Rect of button <paramref name="index"/> (0 = first: top of a column, left of a row) inside the group rect.</summary>
        public static Rect ButtonRect(OverlayButtonsPlace place, Rect group, Vector2 button, float spacing, int index)
        {
            bool column = place == OverlayButtonsPlace.ColumnTopRight || place == OverlayButtonsPlace.ColumnBottomRight;
            if (column) return new Rect(group.x, group.yMax - (index + 1) * button.y - index * spacing, button.x, button.y);
            return new Rect(group.x + index * (button.x + spacing), group.y, button.x, button.y);
        }

        /// <summary>True when the rects are closer than <paramref name="gap"/> (touching or overlapping). Empty rects never collide.</summary>
        public static bool Collide(Rect a, Rect b, float gap)
        {
            if (a.width <= 0f || a.height <= 0f || b.width <= 0f || b.height <= 0f) return false;
            return a.xMin < b.xMax + gap && b.xMin < a.xMax + gap && a.yMin < b.yMax + gap && b.yMin < a.yMax + gap;
        }

        static bool Inside(Rect r, Vector2 content)
        {
            if (r.width <= 0f || r.height <= 0f) return true;
            float hw = content.x * 0.5f + 0.01f, hh = content.y * 0.5f + 0.01f;
            return r.xMin >= -hw && r.xMax <= hw && r.yMin >= -hh && r.yMax <= hh;
        }

        /// <summary>Narrows [lo, hi] (menu shift) so that the shifted menu clears <paramref name="r"/>: a rect in the upper half
        /// pushes the menu below it, one in the lower half above it. A rect beside the menu (horizontal gap) adds nothing.</summary>
        static void Constrain(Rect menu, Rect r, ref float lo, ref float hi)
        {
            if (r.width <= 0f || r.height <= 0f) return;
            if (r.xMax + Gap <= menu.xMin || menu.xMax + Gap <= r.xMin) return;
            if (r.center.y >= 0f) hi = Mathf.Min(hi, r.yMin - Gap - menu.yMax);
            else lo = Mathf.Max(lo, r.yMax + Gap - menu.yMin);
        }

        public static void Solve(in MenuOverlayInput s, out MenuOverlayResult r)
        {
            r = default;
            Vector2 c = s.ContentUnits;
            if (!s.HasOverlay)
            {
                r.Panel = OverlayPanelPlace.Collapsed;
                r.MenuRect = s.HasMenu ? s.MenuBlock : default;
                r.Fits = true;
                return;
            }
            if (!s.HasMenu)
            {
                // Historic place (driving scenes, no menu): panel top-left, buttons in a column top-right.
                r.Panel = s.PanelShown ? OverlayPanelPlace.TopLeft : OverlayPanelPlace.Collapsed;
                r.Buttons = OverlayButtonsPlace.ColumnTopRight;
                r.PanelRect = PanelRectFor(r.Panel, c, s.PanelSize);
                r.ButtonsRect = ButtonsRectFor(r.Buttons, c, s.ButtonSize, s.ButtonSpacing);
                r.Fits = !Collide(r.PanelRect, r.ButtonsRect, Gap);
                return;
            }

            Rect m = s.MenuBlock;
            float hh = c.y * 0.5f;
            // The menu stays inside the content; a menu taller than the content (never by design) may stay where it is.
            float baseLo = Mathf.Min(0f, -hh - m.yMin), baseHi = Mathf.Max(0f, hh - m.yMax);
            for (int p = 0; p < k_Panels.Length; p++)
            {
                var panel = k_Panels[p];
                if (!s.PanelShown && panel != OverlayPanelPlace.Collapsed) continue;
                Rect pr = PanelRectFor(panel, c, s.PanelSize);
                if (!Inside(pr, c)) continue;
                for (int b = 0; b < k_Buttons.Length; b++)
                {
                    var buttons = k_Buttons[b];
                    Rect br = ButtonsRectFor(buttons, c, s.ButtonSize, s.ButtonSpacing);
                    if (!Inside(br, c) || Collide(pr, br, Gap)) continue;
                    float lo = baseLo, hi = baseHi;
                    Constrain(m, pr, ref lo, ref hi);
                    Constrain(m, br, ref lo, ref hi);
                    if (lo > hi + 1e-3f) continue;
                    float shift = Mathf.Clamp(0f, lo, hi);
                    r.MenuShiftY = shift;
                    r.Panel = panel;
                    r.Buttons = buttons;
                    r.PanelRect = pr;
                    r.ButtonsRect = br;
                    r.MenuRect = new Rect(m.x, m.y + shift, m.width, m.height);
                    r.Fits = true;
                    return;
                }
            }
            // Nothing fits (a window smaller than any supported screen): panel collapsed, buttons at the historic place.
            r.Panel = OverlayPanelPlace.Collapsed;
            r.Buttons = OverlayButtonsPlace.ColumnTopRight;
            r.ButtonsRect = ButtonsRectFor(r.Buttons, c, s.ButtonSize, s.ButtonSpacing);
            r.MenuRect = m;
            r.Fits = false;
        }
    }
}
