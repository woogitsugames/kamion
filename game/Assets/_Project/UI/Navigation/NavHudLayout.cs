using Game.UI.Driving;
using UnityEngine;

namespace Game.UI.Navigation
{
    /// <summary>
    /// Zone of the GPS widget (guidance banner + heading-up minimap) in the driving HUD (ADR 0150, extends ADR 0079 without
    /// changing its solver): the top-left column between the safe-area edge and the left mirror inset (or the cluster),
    /// above the steering group. Never overlaps a HUD zone (tests over phones 20:9 / 21:9, Fold ~1:1, tablets). Hidden
    /// while the developer telemetry uses that corner, or when the screen leaves less than the minimum size.
    /// Sizes in canvas units (1 unit = 1 px on a 1080-px-high phone), WORKING_VALUES.
    /// </summary>
    public static class NavHudLayout
    {
        public static readonly Vector2 Preferred = new Vector2(340f, 440f);
        public static readonly Vector2 Minimum = new Vector2(220f, 250f);

        public static bool Solve(in HudLayoutResult r, float width, float height, bool telemetry, out Rect zone)
        {
            zone = default;
            if (telemetry) return false;
            // ADR 0283: the monitor HUD solves the GPS zone itself (bottom left, under / beside the left mirror window).
            if (r.Desktop) { zone = r.Nav; return r.ShowNav; }
            float top = height - HudLayout.Margin, x0 = HudLayout.Margin;
            float x1 = (r.ShowMirrorLeft ? r.MirrorLeft.x : r.Cluster.x) - HudLayout.Gap;
            if (r.ShowReverseView) x1 = Mathf.Min(x1, r.ReverseView.x - HudLayout.Gap);
            // ADR 0265: on a monitor the steering group is not on screen - only the developer text row is below.
            float bottom = r.ShowTouchControls ? Mathf.Max(r.TurnSignals.yMax, r.Stalk.yMax, r.Steering.yMax) + HudLayout.Gap
                                               : HudLayout.Margin + HudLayout.DevTextHeight + HudLayout.Gap;
            float w = Mathf.Min(Preferred.x, x1 - x0), h = Mathf.Min(Preferred.y, top - bottom);
            if (w < Minimum.x || h < Minimum.y) return false;
            zone = new Rect(x0, top - h, w, h);
            return true;
        }
    }
}
