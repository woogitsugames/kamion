using Game.Controls;
using UnityEngine;
using UnityEngine.UI;

namespace Game.UI.Layout
{
    /// <summary>
    /// One per canvas: keeps the canvas scale (<see cref="UiScale"/>) and the safe-area rect in step with the
    /// screen. <see cref="Refresh"/> is cheap and allocation-free; call it every frame - it returns true only when
    /// the pixel size, the safe area or the DPI changed (rotation, folding/unfolding, split screen), which is the
    /// moment to lay the canvas out again.
    /// ADR 0265: two form factors (<see cref="HudScaleModel"/>). Touch = ADR 0079 unchanged. Monitor (no touch controls,
    /// <see cref="TouchControlsPolicy"/>) = scale by the window height, the "SafeArea" rect narrowed to 16:9 and centred
    /// on ultrawide monitors (every layout lives in it, so the HUD and the menus never reach the far corners).
    /// </summary>
    public sealed class UiViewport
    {
        readonly Canvas m_Canvas;
        readonly CanvasScaler m_Scaler;
        readonly RectTransform m_Safe;

        Rect? m_SafeOverride;
        Vector2? m_PixelOverride;
        float? m_DpiOverride;
        bool? m_DesktopOverride;

        bool m_Applied;
        Vector2 m_AppliedPx;
        Rect m_AppliedSafe;
        float m_AppliedDpi;
        bool m_AppliedDesktop;
        float m_AppliedUserScale;

        /// <summary>Safe-area size in canvas units (the coordinate space of every layout).</summary>
        public Vector2 SizeUnits { get; private set; } = new Vector2(1920f, 1080f);
        /// <summary>Pixels per canvas unit currently applied.</summary>
        public float PixelsPerUnit { get; private set; } = 1f;
        public RectTransform SafeArea => m_Safe;
        /// <summary>Canvas size in pixels as last applied (the override in tests / captures).</summary>
        public Vector2 PixelSize => m_AppliedPx;
        /// <summary>Monitor form factor applied (no touch controls; ADR 0265).</summary>
        public bool Desktop => m_AppliedDesktop;
        /// <summary>True when the content was narrowed on an ultrawide monitor.</summary>
        public bool Clamped { get; private set; }

        /// <summary>Forces the form factor (tests, captures); null = from <see cref="TouchControlsPolicy.Current"/>.</summary>
        public void OverrideDesktop(bool? desktop) { m_DesktopOverride = desktop; m_Applied = false; }

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
        /// The canvas must render at the same pixel size (camera target texture) for the picture to match.
        /// A device screen is a touch device (ADR 0079 tests); use the overload with <c>desktop</c> for a monitor.</summary>
        public void OverrideScreen(Vector2 pixelSize, Rect safeAreaPx, float dpi) => OverrideScreen(pixelSize, safeAreaPx, dpi, false);

        /// <summary>Tests / captures: lay out for a screen of the given form factor (ADR 0265: monitors 16:9 .. 32:9).</summary>
        public void OverrideScreen(Vector2 pixelSize, Rect safeAreaPx, float dpi, bool desktop)
        {
            m_DesktopOverride = desktop;
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
            bool desktop = m_DesktopOverride ?? !TouchControlsPolicy.Current;
            float user = desktop ? UiPreferences.HudScale : 1f;

            if (m_Applied && px == m_AppliedPx && n == m_AppliedSafe && Mathf.Approximately(dpi, m_AppliedDpi)
                && desktop == m_AppliedDesktop && Mathf.Approximately(user, m_AppliedUserScale)) return false;
            m_Applied = true; m_AppliedPx = px; m_AppliedSafe = n; m_AppliedDpi = dpi; m_AppliedDesktop = desktop; m_AppliedUserScale = user;

            var input = new HudScaleInput
            {
                SafePx = new Rect(n.x * px.x, n.y * px.y, Mathf.Max(1f, n.width * px.x), Mathf.Max(1f, n.height * px.y)),
                Dpi = dpi, Desktop = desktop, UserScale = user,
            };
            HudScaleModel.Solve(input, out var r);
            PixelsPerUnit = r.PixelsPerUnit;
            SizeUnits = r.SizeUnits;
            Clamped = r.Clamped;
            m_Scaler.scaleFactor = PixelsPerUnit;
            m_Canvas.scaleFactor = PixelsPerUnit;   // at once; the scaler would only apply it on its next Update
            m_Safe.anchorMin = new Vector2(r.ContentPx.xMin / px.x, r.ContentPx.yMin / px.y);
            m_Safe.anchorMax = new Vector2(r.ContentPx.xMax / px.x, r.ContentPx.yMax / px.y);
            m_Safe.offsetMin = m_Safe.offsetMax = Vector2.zero;
            return true;
        }
    }
}
