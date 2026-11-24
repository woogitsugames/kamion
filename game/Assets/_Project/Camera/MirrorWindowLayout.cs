using UnityEngine;

namespace Game.Cameras
{
    /// <summary>Where the two mirror windows may go (canvas units of the content rect, origin bottom-left, y up).</summary>
    public struct MirrorWindowInput
    {
        /// <summary>Content size [units].</summary>
        public float Width, Height;
        /// <summary>Panel the windows flank (the instrument cluster, top centre).</summary>
        public Rect Centre;
        /// <summary>Glass aspect (width / height) of the mirror render texture; &lt;= 0 = <see cref="MirrorWindowLayout.DefaultAspect"/>.</summary>
        public float Aspect;
        /// <summary>Width kept free at both outer edges for corner buttons (the developer button top right) [units].</summary>
        public float SideReserve;
    }

    public struct MirrorWindowResult
    {
        public Rect Left, Right;
        /// <summary>False when not even <see cref="MirrorWindowLayout.MinHeight"/> fits beside the centre panel.</summary>
        public bool Fits;
    }

    /// <summary>
    /// The one layout of the fixed mirror windows (D70: the class II mirrors as fixed windows on screen). Two form factors,
    /// one place: <see cref="Solve"/> = monitor (ADR 0265), <see cref="SolveTouch"/> = touch / phone (ADR 0243, the
    /// fixed 160 x 290 unit windows of ADR 0079 kept inside the safe area). Pure, no allocation.
    /// <para>Monitor (D70: the main mirrors as fixed windows on screen; ADR 0265).</para>
    /// The windows are sized by the content HEIGHT (<see cref="HeightFraction"/>) and keep the glass aspect of the render
    /// texture - never stretched by a wide monitor: 16:9, 21:9 and 32:9 give the same window, only the free view beside it
    /// grows. They flank the cluster at the top like the touch layout the owner accepted (ADR 0079), top-aligned with
    /// the content edge; when the side room is too narrow the window shrinks as a whole (aspect kept).
    /// </summary>
    public static class MirrorWindowLayout
    {
        /// <summary>Window height as a fraction of the content height. WORKING_VALUE (owner to judge on the build).</summary>
        public const float HeightFraction = 0.30f;
        /// <summary>Smallest useful window height [units]; below it the windows are not shown. WORKING_VALUE.</summary>
        public const float MinHeight = 200f;
        /// <summary>Main-mirror glass aspect (RenderTextureMirror.aspect default 0.55).</summary>
        public const float DefaultAspect = 0.55f;
        public const float Margin = 24f, Gap = 12f;

        /// <summary>Touch window size incl. the frame [phone units, ADR 0079] (portrait, class II glass ~0.55). WORKING_VALUE.</summary>
        public static readonly Vector2 TouchSize = new Vector2(160f, 290f);
        /// <summary>Frame width around the image of a touch window [units] (the HUD draws the texture inset by this much).</summary>
        public const float TouchFrame = 5f;
        /// <summary>Image area of one touch window [units] (inside the frame).</summary>
        public static Vector2 TouchImageSize => new Vector2(TouchSize.x - 2f * TouchFrame, TouchSize.y - 2f * TouchFrame);

        /// <summary>
        /// Touch layout (ADR 0243, phone canvas units relative to the safe area): left and right window of
        /// <see cref="TouchSize"/> beside <paramref name="centre"/>, <paramref name="gap"/> away, top at <paramref name="top"/>.
        /// <see cref="MirrorWindowResult.Fits"/> = false when a window would leave the safe area of width
        /// <paramref name="width"/> (with <paramref name="margin"/>) or reach below <paramref name="bottomLimit"/>
        /// (the windows must then be hidden, never drawn off screen).
        /// </summary>
        public static void SolveTouch(float width, Rect centre, float top, float gap, float margin, float bottomLimit, out MirrorWindowResult r)
        {
            r = default;
            r.Left = new Rect(centre.x - gap - TouchSize.x, top - TouchSize.y, TouchSize.x, TouchSize.y);
            r.Right = new Rect(centre.xMax + gap, top - TouchSize.y, TouchSize.x, TouchSize.y);
            r.Fits = r.Left.xMin >= margin - 1e-3f && r.Right.xMax <= width - margin + 1e-3f && r.Left.yMin >= bottomLimit - 1e-3f;
        }

        /// <summary>A safe-area canvas rect in screen pixels (Screen.safeArea origin, <paramref name="pixelsPerUnit"/> scale).</summary>
        public static Rect ToScreenPixels(Rect units, Rect safeAreaPx, float pixelsPerUnit) =>
            new Rect(safeAreaPx.x + units.x * pixelsPerUnit, safeAreaPx.y + units.y * pixelsPerUnit, units.width * pixelsPerUnit, units.height * pixelsPerUnit);

        /// <summary>True when <paramref name="inner"/> lies inside <paramref name="outer"/> (tolerance <paramref name="eps"/>).</summary>
        public static bool Inside(Rect inner, Rect outer, float eps = 0.5f) =>
            inner.xMin >= outer.xMin - eps && inner.yMin >= outer.yMin - eps && inner.xMax <= outer.xMax + eps && inner.yMax <= outer.yMax + eps;

        /// <summary>
        /// Texture rows per screen pixel row of a touch window image: render-texture height / image height in pixels.
        /// 1 = 1:1; below 1 the texture is magnified (softer, cheaper). The texture cost is what ADR 0243 budgets.
        /// </summary>
        public static float TexelsPerPixel(int textureHeight, float pixelsPerUnit) =>
            pixelsPerUnit > 1e-4f ? textureHeight / (TouchImageSize.y * pixelsPerUnit) : 0f;

        // ------------------------------------------------------------------ glass look (ADR 0340)

        /// <summary>Barrel strength k of the window glass. WORKING_VALUE: a class II main mirror is only slightly convex
        /// (UN R46 minimum radius of curvature for class II: UNVERIFIED here), so straight edges (kerb line, trailer side)
        /// bend just visibly near the rim - not a fisheye. Centre magnification = 1 + k (1 + aspect^2) ~ 1.09 at 0.55.</summary>
        public const float GlassCurvature = 0.07f;
        /// <summary>Darkening at the glass corners (0 = none). WORKING_VALUE.</summary>
        public const float GlassVignette = 0.26f;

        /// <summary>
        /// Barrel map of a glass point: <paramref name="s"/>, <paramref name="t"/> in 0..1 across / along the glass,
        /// <paramref name="aspect"/> = glass width / height. Returns the 0..1 texture coordinate. Scale about the centre
        /// = (1 + k r^2) / (1 + k r_corner^2) with r in half-heights: the corners map to the texture corners for every
        /// k >= 0 (nothing outside the texture is sampled, nothing is cropped), the centre is magnified; k = 0 = identity.
        /// </summary>
        public static Vector2 Barrel(float s, float t, float aspect, float k)
        {
            float cx = (s - 0.5f) * 2f, cy = (t - 0.5f) * 2f;
            float ax = cx * aspect;
            float r2 = ax * ax + cy * cy, rc2 = aspect * aspect + 1f;
            float f = (1f + k * r2) / (1f + k * rc2);
            return new Vector2(0.5f + 0.5f * cx * f, 0.5f + 0.5f * cy * f);
        }

        /// <summary>Brightness factor of the glass at a point: 1 over the middle (out to 45 % of the corner distance),
        /// falling smoothly to 1 - <paramref name="strength"/> in the corners (a recessed glass under a housing lip).</summary>
        public static float GlassShade(float s, float t, float strength)
        {
            float cx = (s - 0.5f) * 2f, cy = (t - 0.5f) * 2f;
            float d = Mathf.Sqrt(0.5f * (cx * cx + cy * cy));
            float e = Mathf.Clamp01((d - 0.45f) / 0.55f);
            e = e * e * (3f - 2f * e);
            return 1f - Mathf.Clamp01(strength) * e;
        }

        public static void Solve(in MirrorWindowInput s, out MirrorWindowResult r)
        {
            r = default;
            float aspect = s.Aspect > 0.05f ? s.Aspect : DefaultAspect;
            float h = Mathf.Min(HeightFraction * s.Height, s.Height - 2f * Margin);
            float w = h * aspect;
            float edge = Margin + Mathf.Max(0f, s.SideReserve);
            float roomL = s.Centre.xMin - Gap - edge, roomR = s.Width - edge - (s.Centre.xMax + Gap);
            float room = Mathf.Min(roomL, roomR);
            if (w > room) { w = Mathf.Max(0f, room); h = w / aspect; }
            r.Fits = h >= MinHeight;
            float top = s.Height - Margin;
            r.Left = new Rect(s.Centre.xMin - Gap - w, top - h, w, h);
            r.Right = new Rect(s.Centre.xMax + Gap, top - h, w, h);
        }
    }
}
