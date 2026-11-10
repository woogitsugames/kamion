using UnityEngine;

namespace Game.UI.Driving
{
    /// <summary>What is on screen right now (everything that changes where the HUD zones may go).</summary>
    public struct HudLayoutInput
    {
        /// <summary>Safe-area size in canvas units (<see cref="Game.UI.Layout.UiScale"/>).</summary>
        public float Width, Height;
        public bool Gyro;
        /// <summary>Developer panel expanded (button grid or the lab page).</summary>
        public bool DevPanelOpen;
        public bool Telemetry;
        /// <summary>A mirror texture is available and the insets are switched on.</summary>
        public bool MirrorLeft, MirrorRight;
        public bool ReverseView;
        /// <summary>Developer status / coupling lines.</summary>
        public bool DevText;

        public bool SameAs(in HudLayoutInput o) =>
            Width == o.Width && Height == o.Height && Gyro == o.Gyro && DevPanelOpen == o.DevPanelOpen && Telemetry == o.Telemetry &&
            MirrorLeft == o.MirrorLeft && MirrorRight == o.MirrorRight && ReverseView == o.ReverseView && DevText == o.DevText;
    }

    /// <summary>HUD zones, in safe-area canvas units, origin bottom-left, y up.</summary>
    public struct HudLayoutResult
    {
        public Rect Cluster, ParkWarn, ReverseView, MirrorLeft, MirrorRight, DevToggle, DevPanel, Telemetry;
        public Rect Steering, TurnSignals, Stalk, Brake, Throttle, Gears, DevText;
        /// <summary>False while a developer overlay (telemetry left, panel right) needs the inset's place.</summary>
        public bool ShowMirrorLeft, ShowMirrorRight;
        public bool ShowDevPanel, ShowTelemetry, ShowReverseView, ShowDevText;

        public const int ZoneCount = 15;
        static readonly string[] k_Names =
        {
            "Cluster", "ParkWarn", "ReverseView", "MirrorLeft", "MirrorRight", "DevToggle", "DevPanel", "Telemetry",
            "Steering", "TurnSignals", "Stalk", "Brake", "Throttle", "Gears", "DevText",
        };

        public static string ZoneName(int i) => k_Names[i];

        /// <summary>Zone <paramref name="i"/>; returns whether it is on screen in this state.</summary>
        public bool Zone(int i, out Rect r)
        {
            switch (i)
            {
                case 0: r = Cluster; return true;
                case 1: r = ParkWarn; return true;        // reserved even while faded out
                case 2: r = ReverseView; return ShowReverseView;
                case 3: r = MirrorLeft; return ShowMirrorLeft;
                case 4: r = MirrorRight; return ShowMirrorRight;
                case 5: r = DevToggle; return true;
                case 6: r = DevPanel; return ShowDevPanel;
                case 7: r = Telemetry; return ShowTelemetry;
                case 8: r = Steering; return true;
                case 9: r = TurnSignals; return true;
                case 10: r = Stalk; return true;
                case 11: r = Brake; return true;
                case 12: r = Throttle; return true;
                case 13: r = Gears; return true;
                default: r = DevText; return ShowDevText;
            }
        }
    }

    /// <summary>
    /// Adaptive driving-HUD layout (ADR 0079): pure maths from the safe-area size and the HUD state to
    /// non-overlapping zones, for aspect ratios from 1:1 (foldables) to 21:9 and beyond. No Unity objects,
    /// no allocation - it runs whenever the screen or the state changes and is unit-tested on its own.
    ///
    /// Zones: top centre = instrument cluster (speed, gear, rpm, warning lamps, air) with the mirror insets on
    /// both sides, parking-brake warning and reversing view below it; top right = one developer button, its panel
    /// drops down under it; top left = telemetry (developer); bottom left = steering wheel (or gyro panel), turn
    /// signals above it, retarder stalk beside it; bottom right = pedals with the gear selector beside them (not
    /// above: low zones cover the dashboard, not the road); bottom centre = developer text.
    /// All sizes are WORKING_VALUES in canvas units (one unit = one pixel on a 1080-px-high phone).
    /// </summary>
    public static class HudLayout
    {
        public const float Margin = 24f, Gap = 12f;
        public static readonly Vector2 ClusterSize = new Vector2(440f, 156f);
        public static readonly Vector2 ParkWarnSize = new Vector2(440f, 44f);
        public static readonly Vector2 ReverseSize = new Vector2(440f, 248f);
        public static readonly Vector2 MirrorSize = new Vector2(160f, 290f);
        public static readonly Vector2 DevToggleSize = new Vector2(150f, 60f);
        public static readonly Vector2 DevPanelSize = new Vector2(424f, 378f);
        public const float TelemetryMaxWidth = 760f, TelemetryWideEnough = 640f, TelemetryMaxHeight = 600f;
        public const float WheelSize = 400f;
        public static readonly Vector2 GyroSize = new Vector2(400f, 240f);
        public static readonly Vector2 TurnSignalsSize = new Vector2(400f, 64f);
        public static readonly Vector2 StalkSize = new Vector2(104f, 376f);
        public static readonly Vector2 BrakeSize = new Vector2(190f, 300f);
        public static readonly Vector2 ThrottleSize = new Vector2(170f, 360f);
        public static readonly Vector2 GearsSize = new Vector2(208f, 328f);
        public const float DevTextHeight = 112f;
        const float ControlsBottom = Margin + 8f, WheelLeft = Margin + 16f;

        public static void Solve(in HudLayoutInput s, out HudLayoutResult r)
        {
            r = default;
            float w = s.Width, h = s.Height, cx = w * 0.5f, top = h - Margin;

            // ---- centre column, top down
            r.Cluster = new Rect(cx - ClusterSize.x * 0.5f, top - ClusterSize.y, ClusterSize.x, ClusterSize.y);
            r.ParkWarn = new Rect(r.Cluster.x, r.Cluster.y - 8f - ParkWarnSize.y, ParkWarnSize.x, ParkWarnSize.y);
            r.ReverseView = new Rect(cx - ReverseSize.x * 0.5f, r.ParkWarn.y - 8f - ReverseSize.y, ReverseSize.x, ReverseSize.y);
            r.ShowReverseView = s.ReverseView;
            r.MirrorLeft = new Rect(r.Cluster.x - Gap - MirrorSize.x, top - MirrorSize.y, MirrorSize.x, MirrorSize.y);
            r.MirrorRight = new Rect(r.Cluster.xMax + Gap, top - MirrorSize.y, MirrorSize.x, MirrorSize.y);
            r.ShowMirrorLeft = s.MirrorLeft;
            r.ShowMirrorRight = s.MirrorRight;

            // ---- bottom left: steering, turn signals, retarder stalk
            float steerH = s.Gyro ? GyroSize.y : WheelSize;
            r.Steering = new Rect(WheelLeft, ControlsBottom, WheelSize, steerH);
            r.TurnSignals = new Rect(WheelLeft, ControlsBottom + WheelSize + 8f, TurnSignalsSize.x, TurnSignalsSize.y);
            r.Stalk = new Rect(r.Steering.xMax + 10f, ControlsBottom, StalkSize.x, StalkSize.y);
            float leftTop = Mathf.Max(r.TurnSignals.yMax, r.Stalk.yMax);

            // ---- bottom right: throttle at the edge, brake, gear selector
            r.Throttle = new Rect(w - Margin - ThrottleSize.x, ControlsBottom, ThrottleSize.x, ThrottleSize.y);
            r.Brake = new Rect(r.Throttle.x - 10f - BrakeSize.x, ControlsBottom, BrakeSize.x, BrakeSize.y);
            r.Gears = new Rect(r.Brake.x - Gap - GearsSize.x, ControlsBottom, GearsSize.x, GearsSize.y);

            // ---- top right: developer button, panel under it. Beside the right mirror inset when there is room,
            // otherwise the inset gives way while the panel is open.
            r.DevToggle = new Rect(w - Margin - DevToggleSize.x, top - DevToggleSize.y, DevToggleSize.x, DevToggleSize.y);
            r.DevPanel = new Rect(w - Margin - DevPanelSize.x, r.DevToggle.y - 8f - DevPanelSize.y, DevPanelSize.x, DevPanelSize.y);
            r.ShowDevPanel = s.DevPanelOpen;
            if (s.DevPanelOpen && r.ShowMirrorRight && r.DevPanel.x < r.MirrorRight.xMax + Gap)
            {
                // Narrow canvas: the panel moves under the inset when the screen is tall enough for that (near-square
                // foldables), otherwise the inset gives way.
                float below = r.MirrorRight.y - 8f - DevPanelSize.y;
                if (below >= r.Throttle.yMax + Gap) r.DevPanel.y = below;
                else r.ShowMirrorRight = false;
            }

            // ---- top left: telemetry (developer). Beside the left mirror inset when that leaves a usable width,
            // otherwise the inset gives way while telemetry is shown.
            r.ShowTelemetry = s.Telemetry;
            if (s.Telemetry)
            {
                float room = (r.ShowMirrorLeft ? r.MirrorLeft.x : r.Cluster.x) - Gap - Margin;
                if (r.ShowMirrorLeft && room < TelemetryWideEnough)
                {
                    r.ShowMirrorLeft = false;
                    room = r.Cluster.x - Gap - Margin;
                }
                float tw = Mathf.Min(TelemetryMaxWidth, room);
                float th = Mathf.Min(TelemetryMaxHeight, top - (leftTop + Gap));
                r.Telemetry = new Rect(Margin, top - th, tw, th);
            }

            // ---- bottom centre: developer text between the two control groups
            r.ShowDevText = s.DevText;
            float dx0 = r.Stalk.xMax + Gap, dx1 = r.Gears.x - Gap;
            r.DevText = new Rect(dx0, Margin, Mathf.Max(0f, dx1 - dx0), DevTextHeight);
        }
    }
}
