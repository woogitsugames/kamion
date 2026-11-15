using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// Fixed on-screen mirror windows (D70, ADR 0243): where the left / right class II mirror windows go and how sharp their
    /// texture is. Pure maths on plain rects, no Unity objects, no allocation; used by Game.UI.Driving.HudLayout (which owns
    /// the other HUD zones) and unit-tested in EditMode (the test assembly does not reference Game.UI).
    /// <para>
    /// Canvas units, origin bottom-left, y up, relative to the safe area (Screen.safeArea; one unit = one pixel on the 1080-px
    /// reference phone, ADR 0079). The windows hang from the top margin on both sides of the instrument cluster, the left
    /// window shows the left mirror; outside the cluster column they cover sky and the A-pillar zone, not the road ahead.
    /// </para>
    /// </summary>
    public static class MirrorInsetLayout
    {
        /// <summary>Window size incl. the frame (portrait, the class II glass is about 0.55 wide / high). WORKING_VALUE (ADR 0079).</summary>
        public static readonly Vector2 Size = new Vector2(160f, 290f);
        /// <summary>Frame width around the image [units] (DrivingHud draws the texture inset by this much).</summary>
        public const float Frame = 5f;

        /// <summary>Image area of one window [units] (inside the frame).</summary>
        public static Vector2 ImageSize => new Vector2(Size.x - 2f * Frame, Size.y - 2f * Frame);

        /// <summary>
        /// Left and right window beside <paramref name="cluster"/>, <paramref name="gap"/> away from it, top at
        /// <paramref name="top"/>. Returns false when a window would leave the safe area of width <paramref name="width"/>
        /// (with <paramref name="margin"/>) or reach below <paramref name="bottomLimit"/> (the windows must then be hidden).
        /// </summary>
        public static bool Place(float width, Rect cluster, float top, float gap, float margin, float bottomLimit, out Rect left, out Rect right)
        {
            left = new Rect(cluster.x - gap - Size.x, top - Size.y, Size.x, Size.y);
            right = new Rect(cluster.xMax + gap, top - Size.y, Size.x, Size.y);
            return left.xMin >= margin - 1e-3f && right.xMax <= width - margin + 1e-3f && left.yMin >= bottomLimit - 1e-3f;
        }

        /// <summary>A safe-area canvas rect in screen pixels (Screen.safeArea origin, <paramref name="pixelsPerUnit"/> scale).</summary>
        public static Rect ToScreenPixels(Rect units, Rect safeAreaPx, float pixelsPerUnit) =>
            new Rect(safeAreaPx.x + units.x * pixelsPerUnit, safeAreaPx.y + units.y * pixelsPerUnit, units.width * pixelsPerUnit, units.height * pixelsPerUnit);

        /// <summary>True when <paramref name="inner"/> lies inside <paramref name="outer"/> (tolerance <paramref name="eps"/>).</summary>
        public static bool Inside(Rect inner, Rect outer, float eps = 0.5f) =>
            inner.xMin >= outer.xMin - eps && inner.yMin >= outer.yMin - eps && inner.xMax <= outer.xMax + eps && inner.yMax <= outer.yMax + eps;

        /// <summary>
        /// Texture rows per screen pixel row of the window image: render-texture height / image height in pixels.
        /// 1 = 1:1; below 1 the texture is magnified (softer, cheaper). The texture cost is what ADR 0243 budgets.
        /// </summary>
        public static float TexelsPerPixel(int textureHeight, float pixelsPerUnit) =>
            pixelsPerUnit > 1e-4f ? textureHeight / (ImageSize.y * pixelsPerUnit) : 0f;
    }
}
