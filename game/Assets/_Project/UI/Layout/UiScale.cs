using UnityEngine;

namespace Game.UI.Layout
{
    /// <summary>
    /// Canvas scale for every screen-space canvas of the game (ADR 0079). Pure maths, no Unity objects.
    /// Layouts are authored in canvas units; one unit is one pixel on the reference phone (1080 px short side,
    /// about 2.8 in). The scale follows the SHORTER side of the safe area and the physical size (DPI), never a fixed
    /// pixel count, so a foldable's near-square inner screen or a tablet gets more units (more free view) instead
    /// of controls blown up with the screen height.
    /// </summary>
    public static class UiScale
    {
        /// <summary>Canvas units along the shorter safe-area side on a phone (and whenever the DPI is unknown).</summary>
        public const float ReferenceShortUnits = 1080f;
        /// <summary>Largest unit count along the shorter side (big tablets): controls stop shrinking relative to the screen here.</summary>
        public const float MaxShortUnits = 1700f;
        /// <summary>Physical length of the shorter side on the reference phone [in] (1080 px at ~385 dpi). WORKING_VALUE.</summary>
        public const float ReferenceShortInches = 2.8f;
        /// <summary>How fast units grow with physical size: 0 = controls scale with the screen (old behaviour),
        /// 1 = controls keep their physical size. WORKING_VALUE, to be tuned with the owner on the Fold.</summary>
        public const float PhysicalExponent = 0.6f;
        /// <summary>Every layout is guaranteed at least this many units of width (HUD zones, two-column menus).</summary>
        public const float MinWidthUnits = 1680f;

        /// <summary>Canvas units along the shorter side for a physical short-side length; dpi &lt;= 0 = unknown.</summary>
        public static float ShortUnits(float shortPx, float dpi)
        {
            if (dpi <= 1f || shortPx <= 0f) return ReferenceShortUnits;
            float inches = shortPx / dpi;
            float u = ReferenceShortUnits * Mathf.Pow(inches / ReferenceShortInches, PhysicalExponent);
            return Mathf.Clamp(u, ReferenceShortUnits, MaxShortUnits);
        }

        /// <summary>Pixels per canvas unit for a safe area of the given pixel size.</summary>
        public static float PixelsPerUnit(float safeWidthPx, float safeHeightPx, float dpi)
        {
            if (safeWidthPx <= 0f || safeHeightPx <= 0f) return 1f;
            float shortPx = Mathf.Min(safeWidthPx, safeHeightPx);
            float scale = shortPx / ShortUnits(shortPx, dpi);
            // Near-square and portrait-ish screens: never fewer than MinWidthUnits across.
            if (safeWidthPx / scale < MinWidthUnits) scale = safeWidthPx / MinWidthUnits;
            return scale;
        }

        /// <summary>Safe-area size in canvas units.</summary>
        public static Vector2 SizeUnits(float safeWidthPx, float safeHeightPx, float dpi)
        {
            float s = PixelsPerUnit(safeWidthPx, safeHeightPx, dpi);
            return new Vector2(safeWidthPx / s, safeHeightPx / s);
        }
    }
}
