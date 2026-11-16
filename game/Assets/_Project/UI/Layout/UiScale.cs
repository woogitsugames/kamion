using Game.Controls;
using UnityEngine;

namespace Game.UI.Layout
{
    /// <summary>
    /// Canvas scale for every screen-space canvas of the game (ADR 0079 touch, ADR 0265 monitor). Facade over the pure
    /// <see cref="HudScaleModel"/> (Game.Controls, unit-tested in EditMode). Touch: layouts are authored in canvas units,
    /// one unit is one pixel on the reference phone (1080 px short side, about 2.8 in); the scale follows the SHORTER side
    /// of the safe area and the physical size (DPI), never a fixed pixel count. Monitor: see <see cref="HudScaleModel"/>.
    /// </summary>
    public static class UiScale
    {
        public const float ReferenceShortUnits = HudScaleModel.ReferenceShortUnits;
        public const float MaxShortUnits = HudScaleModel.MaxShortUnits;
        public const float ReferenceShortInches = HudScaleModel.ReferenceShortInches;
        public const float PhysicalExponent = HudScaleModel.PhysicalExponent;
        public const float MinWidthUnits = HudScaleModel.MinWidthUnits;

        /// <summary>Touch: canvas units along the shorter side for a physical short-side length; dpi &lt;= 0 = unknown.</summary>
        public static float ShortUnits(float shortPx, float dpi) => HudScaleModel.TouchShortUnits(shortPx, dpi);

        /// <summary>Touch: pixels per canvas unit for a safe area of the given pixel size.</summary>
        public static float PixelsPerUnit(float safeWidthPx, float safeHeightPx, float dpi) => HudScaleModel.TouchPixelsPerUnit(safeWidthPx, safeHeightPx, dpi);

        /// <summary>Touch: safe-area size in canvas units.</summary>
        public static Vector2 SizeUnits(float safeWidthPx, float safeHeightPx, float dpi)
        {
            float s = PixelsPerUnit(safeWidthPx, safeHeightPx, dpi);
            return new Vector2(safeWidthPx / s, safeHeightPx / s);
        }

        /// <summary>Content size in canvas units for either form factor (monitor: after the ultrawide clamp).</summary>
        public static Vector2 SizeUnits(float safeWidthPx, float safeHeightPx, float dpi, bool desktop, float userScale = 1f)
        {
            var input = new HudScaleInput { SafePx = new Rect(0f, 0f, safeWidthPx, safeHeightPx), Dpi = dpi, Desktop = desktop, UserScale = userScale };
            HudScaleModel.Solve(input, out var r);
            return r.SizeUnits;
        }
    }
}
