using UnityEngine;
using UnityEngine.UI;

namespace Game.UI.Layout
{
    /// <summary>
    /// One per canvas: keeps the canvas scale (<see cref="UiScale"/>) and the safe-area rect in step with the
    /// screen. <see cref="Refresh"/> is cheap and allocation-free; call it every frame - it returns true only when
    /// the pixel size, the safe area or the DPI changed (rotation, folding/unfolding, split screen), which is the
    /// moment to lay the canvas out again.
    /// </summary>
    public sealed class UiViewport
    {
        readonly Canvas m_Canvas;
        readonly CanvasScaler m_Scaler;
        readonly RectTransform m_Safe;

        Rect? m_SafeOverride;
        Vector2? m_PixelOverride;
        float? m_DpiOverride;

        bool m_Applied;
        Vector2 m_AppliedPx;
        Rect m_AppliedSafe;
        float m_AppliedDpi;

        /// <summary>Safe-area size in canvas units (the coordinate space of every layout).</summary>
        public Vector2 SizeUnits { get; private set; } = new Vector2(1920f, 1080f);
        /// <summary>Pixels per canvas unit currently applied.</summary>
        public float PixelsPerUnit { get; private set; } = 1f;
        public RectTransform SafeArea => m_Safe;

        /// <summary>Adds the scaler to the canvas object and creates the stretched "SafeArea" child.</summary>
        public UiViewport(Canvas canvas)
        {
            m_Canvas = canvas;
            m_Scaler = canvas.gameObject.AddComponent<CanvasScaler>();
            m_Scaler.uiScaleMode = CanvasScaler.ScaleMode.ConstantPixelSize;
            var go = new GameObject("SafeArea", typeof(RectTransform)) { layer = 5 };
            m_Safe = (RectTransform)go.transform;
            m_Safe.SetParent(canvas.transform, false);
            m_Safe.anchorMin = Vector2.zero; m_Safe.anchorMax = Vector2.one;
            m_Safe.offsetMin = m_Safe.offsetMax = Vector2.zero;
        }

        /// <summary>Editor capture / tests: fake safe area (normalised). Also pins the DPI to "unknown" unless
        /// <see cref="OverrideScreen"/> set one, so captures do not depend on the monitor of the build machine.</summary>
        public void OverrideSafeAreaNormalized(Rect normalized)
        {
            m_SafeOverride = normalized;
            if (!m_DpiOverride.HasValue) m_DpiOverride = 0f;
            m_Applied = false;
        }

        /// <summary>Tests / captures: lay out for a device screen (pixel size, safe area in pixels, DPI; 0 = unknown).
        /// The canvas must render at the same pixel size (camera target texture) for the picture to match.</summary>
        public void OverrideScreen(Vector2 pixelSize, Rect safeAreaPx, float dpi)
        {
            m_PixelOverride = pixelSize;
            m_SafeOverride = new Rect(safeAreaPx.x / pixelSize.x, safeAreaPx.y / pixelSize.y, safeAreaPx.width / pixelSize.x, safeAreaPx.height / pixelSize.y);
            m_DpiOverride = dpi;
            m_Applied = false;
        }

        /// <summary>Forces the next <see cref="Refresh"/> to report a change.</summary>
        public void Invalidate() => m_Applied = false;

        public bool Refresh()
        {
            Vector2 px;
            if (m_PixelOverride.HasValue) px = m_PixelOverride.Value;
            else
            {
                px = m_Canvas != null ? m_Canvas.pixelRect.size : Vector2.zero;
                if (px.x < 1f || px.y < 1f) px = new Vector2(Screen.width, Screen.height);
            }
            if (px.x < 1f || px.y < 1f) return false;

            Rect n;
            if (m_SafeOverride.HasValue) n = m_SafeOverride.Value;
            else if (Mathf.Abs(px.x - Screen.width) < 1f && Mathf.Abs(px.y - Screen.height) < 1f)
            {
                Rect s = Screen.safeArea;
                n = new Rect(s.x / px.x, s.y / px.y, s.width / px.x, s.height / px.y);
            }
            else n = new Rect(0f, 0f, 1f, 1f);   // rendering to a texture: no device cutouts
            float dpi = m_DpiOverride ?? Screen.dpi;

            if (m_Applied && px == m_AppliedPx && n == m_AppliedSafe && Mathf.Approximately(dpi, m_AppliedDpi)) return false;
            m_Applied = true; m_AppliedPx = px; m_AppliedSafe = n; m_AppliedDpi = dpi;

            float safeW = Mathf.Max(1f, n.width * px.x), safeH = Mathf.Max(1f, n.height * px.y);
            PixelsPerUnit = UiScale.PixelsPerUnit(safeW, safeH, dpi);
            SizeUnits = new Vector2(safeW / PixelsPerUnit, safeH / PixelsPerUnit);
            m_Scaler.scaleFactor = PixelsPerUnit;
            m_Canvas.scaleFactor = PixelsPerUnit;   // at once; the scaler would only apply it on its next Update
            m_Safe.anchorMin = n.min;
            m_Safe.anchorMax = n.max;
            m_Safe.offsetMin = m_Safe.offsetMax = Vector2.zero;
            return true;
        }
    }
}
