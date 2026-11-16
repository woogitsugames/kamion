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
    /// Mirror windows on a monitor (D70: the main mirrors as fixed windows on screen; ADR 0265). Pure, no allocation.
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
