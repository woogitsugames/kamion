using UnityEngine;

namespace Game.Controls
{
    /// <summary>What the canvas scale is computed from (one screen, one canvas).</summary>
    public struct HudScaleInput
    {
        /// <summary>Safe area in pixels (the whole window on a PC monitor).</summary>
        public Rect SafePx;
        /// <summary>Reported DPI; 0 or less = unknown.</summary>
        public float Dpi;
        /// <summary>Monitor form factor (no touch controls on screen): height-proportional scale and the ultrawide
        /// content clamp. False = touch form factor (phone / tablet, ADR 0079 behaviour unchanged).</summary>
        public bool Desktop;
        /// <summary>Player HUD scale on a monitor (1 = default); ignored on touch screens.</summary>
        public float UserScale;
    }

    /// <summary>Result: pixels per canvas unit and the rect (pixels) every layout lives in.</summary>
    public struct HudScaleResult
    {
        public float PixelsPerUnit;
        /// <summary>Content rect in pixels: the safe area, on a monitor narrowed to <see cref="HudScaleModel.MaxContentAspect"/>.</summary>
        public Rect ContentPx;
        /// <summary>Content size in canvas units (the coordinate space of every layout).</summary>
        public Vector2 SizeUnits;
        /// <summary>True when the content was narrowed (ultrawide monitor).</summary>
        public bool Clamped;
    }

    /// <summary>
    /// Canvas scale and content rect for every screen-space canvas (ADR 0079 touch, ADR 0265 monitor). Pure maths, no
    /// Unity objects, no allocation; unit-tested in EditMode (lives in Game.Controls because the EditMode test assembly
    /// references it and not Game.UI - <c>Game.UI.Layout.UiScale</c> is the facade the UI uses).
    ///
    /// Touch (phone, tablet, foldable): one unit = one pixel on the reference phone; the scale follows the SHORTER side
    /// of the safe area and the physical size (DPI) - unchanged from ADR 0079.
    ///
    /// Monitor (ADR 0265): the HUD is not under the thumbs any more, so it follows the window HEIGHT: the content is
    /// always <see cref="DesktopShortUnits"/> units high, i.e. the same layout at 1080p, 1440p and 4K, just sharper.
    /// Ultrawide (21:9, 32:9): the content is narrowed to <see cref="MaxContentAspect"/> and centred, so the HUD and the
    /// menus stay in front of the driver instead of running into the far corners; the 3D view still uses the whole
    /// width (only the canvas content is narrowed). The OS display scaling (Windows 125 % / 150 %, reported as DPI)
    /// can make the HUD larger, never so large that fewer than <see cref="MinDesktopShortUnits"/> units remain.
    /// All sizes WORKING_VALUE until the owner looks at the build on his monitor.
    /// </summary>
    public static class HudScaleModel
    {
        // ---- touch (ADR 0079; moved here from UiScale unchanged)
        /// <summary>Canvas units along the shorter safe-area side on a phone (and whenever the DPI is unknown).</summary>
        public const float ReferenceShortUnits = 1080f;
        /// <summary>Largest unit count along the shorter side (big tablets).</summary>
        public const float MaxShortUnits = 1700f;
        /// <summary>Physical length of the shorter side on the reference phone [in]. WORKING_VALUE.</summary>
        public const float ReferenceShortInches = 2.8f;
        /// <summary>0 = controls scale with the screen, 1 = controls keep their physical size. WORKING_VALUE.</summary>
        public const float PhysicalExponent = 0.6f;
        /// <summary>Every layout is guaranteed at least this many units of width.</summary>
        public const float MinWidthUnits = 1680f;

        // ---- monitor (ADR 0265)
        /// <summary>Canvas units along the window height on a monitor: 1080p = 0.75 px/unit, 1440p = 1, 4K = 1.5. WORKING_VALUE.</summary>
        public const float DesktopShortUnits = 1440f;
        /// <summary>Fewest units along the height (the start menu block and the settings panel are designed for 1080). </summary>
        public const float MinDesktopShortUnits = 1080f;
        /// <summary>Pixels per unit at 96 DPI (Windows 100 %) below which the HUD is not shrunk (720p and smaller windows). WORKING_VALUE.</summary>
        public const float DesktopMinPpuAt96Dpi = 0.75f;
        /// <summary>Widest content aspect on a monitor (16:9). WORKING_VALUE.</summary>
        public const float MaxContentAspect = 16f / 9f;
        /// <summary>Player HUD scale range on a monitor.</summary>
        public const float UserScaleMin = 0.8f, UserScaleMax = 1.4f;

        /// <summary>Touch: canvas units along the shorter side for a physical short-side length; dpi &lt;= 1 = unknown.</summary>
        public static float TouchShortUnits(float shortPx, float dpi)
        {
            if (dpi <= 1f || shortPx <= 0f) return ReferenceShortUnits;
            float inches = shortPx / dpi;
            float u = ReferenceShortUnits * Mathf.Pow(inches / ReferenceShortInches, PhysicalExponent);
            return Mathf.Clamp(u, ReferenceShortUnits, MaxShortUnits);
        }

        /// <summary>Touch: pixels per canvas unit for a safe area of the given pixel size (ADR 0079).</summary>
        public static float TouchPixelsPerUnit(float safeWidthPx, float safeHeightPx, float dpi)
        {
            if (safeWidthPx <= 0f || safeHeightPx <= 0f) return 1f;
            float shortPx = Mathf.Min(safeWidthPx, safeHeightPx);
            float scale = shortPx / TouchShortUnits(shortPx, dpi);
            if (safeWidthPx / scale < MinWidthUnits) scale = safeWidthPx / MinWidthUnits;
            return scale;
        }

        /// <summary>Clamps a stored player scale (NaN / out of range = default 1).</summary>
        public static float SanitizeUserScale(float s) =>
            float.IsNaN(s) || float.IsInfinity(s) || s <= 0f ? 1f : Mathf.Clamp(s, UserScaleMin, UserScaleMax);

        /// <summary>Monitor: pixels per canvas unit for a content rect of the given pixel size.</summary>
        public static float DesktopPixelsPerUnit(float contentWidthPx, float contentHeightPx, float dpi, float userScale)
        {
            if (contentWidthPx <= 0f || contentHeightPx <= 0f) return 1f;
            float shortPx = Mathf.Min(contentWidthPx, contentHeightPx);
            float ppu = shortPx / DesktopShortUnits;
            if (dpi > 1f) ppu = Mathf.Max(ppu, DesktopMinPpuAt96Dpi * dpi / 96f);   // OS display scaling
            else ppu = Mathf.Max(ppu, DesktopMinPpuAt96Dpi);
            ppu *= SanitizeUserScale(userScale);
            ppu = Mathf.Min(ppu, shortPx / MinDesktopShortUnits);   // never fewer than 1080 units high
            if (contentWidthPx / ppu < MinWidthUnits) ppu = contentWidthPx / MinWidthUnits;   // portrait / square windows
            return ppu;
        }

        /// <summary>Content rect: the safe area, on a monitor narrowed to <see cref="MaxContentAspect"/> and centred.</summary>
        public static Rect ContentRect(Rect safePx, bool desktop, out bool clamped)
        {
            clamped = false;
            if (!desktop || safePx.height <= 0f) return safePx;
            float maxW = safePx.height * MaxContentAspect;
            if (safePx.width <= maxW + 0.5f) return safePx;
            clamped = true;
            float x = safePx.x + (safePx.width - maxW) * 0.5f;
            return new Rect(Mathf.Round(x), safePx.y, Mathf.Round(maxW), safePx.height);
        }

        public static void Solve(in HudScaleInput s, out HudScaleResult r)
        {
            r.ContentPx = ContentRect(s.SafePx, s.Desktop, out r.Clamped);
            float w = Mathf.Max(1f, r.ContentPx.width), h = Mathf.Max(1f, r.ContentPx.height);
            r.PixelsPerUnit = s.Desktop ? DesktopPixelsPerUnit(w, h, s.Dpi, s.UserScale) : TouchPixelsPerUnit(w, h, s.Dpi);
            r.SizeUnits = new Vector2(w / r.PixelsPerUnit, h / r.PixelsPerUnit);
        }
    }
}
