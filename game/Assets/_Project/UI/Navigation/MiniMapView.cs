using System.Diagnostics;
using Game.Core.Navigation;
using Game.UI.CabDisplays;
using Game.UI.Driving;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using P = Game.UI.CabDisplays.DisplayPalette;

namespace Game.UI.Navigation
{
    /// <summary>
    /// GPS widget of the driving HUD (ADR 0150): guidance banner (next manoeuvre pictogram, distance, street; "then"
    /// chip) over a heading-up minimap (region roads and buildings, route ahead, destination flag, truck chevron, OSM speed
    /// limit, current street, north marker). Zoom follows speed. One DisplayCanvas render texture shown by a RawImage in
    /// the zone of <see cref="NavHudLayout"/>; a tap opens the full map.
    /// Cost: one static underlay mesh draw + one dynamic batch per refresh (15 Hz on Low, 30 Hz otherwise), zero GC per
    /// refresh (PlayMode test), CPU ms in <see cref="LastCpuMs"/>.
    /// </summary>
    [DefaultExecutionOrder(110)]
    public sealed class MiniMapView : MonoBehaviour, IPointerClickHandler
    {
        public const float BannerH = 108f, StreetH = 36f;
        static readonly Color k_Frame = new Color(0.06f, 0.065f, 0.07f, 0.95f);

        NavigationService m_Nav;
        DrivingHud m_Hud;
        UnityEngine.Canvas m_HudCanvas;
        RectTransform m_Rt;
        RawImage m_Image;
        DisplayCanvas m_Canvas;
        Vector2 m_Size;
        float m_Ppu;
        float m_T, m_Zoom = 1.6f;
        bool m_NightBaked;
        Mesh m_Under;
        readonly TextBuffer m_B = new TextBuffer(48), m_Fit = new TextBuffer(96);
        int m_Refreshes;
        double m_CpuSum;

        public System.Action OnOpenMap;
        [Tooltip("-1 = from the quality tier (Low 15 Hz, else 30 Hz)")] public float hz = -1f;

        public DisplayCanvas Canvas => m_Canvas;
        public bool Visible => m_Rt != null && m_Rt.gameObject.activeSelf;
        public Rect Zone { get; private set; }
        public double LastCpuMs { get; private set; }
        public double AverageCpuMs => m_Refreshes > 0 ? m_CpuSum / m_Refreshes : 0;
        public int RefreshCount => m_Refreshes;
        /// <summary>Restarts the CPU statistics (after warm-up: glyph rasterisation and the static map bake are one-off).</summary>
        public void ResetStats() { m_Refreshes = 0; m_CpuSum = 0; }

        public static MiniMapView Create(DrivingHud hud, NavigationService nav)
        {
            var go = new GameObject("NavMiniMap", typeof(RectTransform)) { layer = 5 };
            var rt = (RectTransform)go.transform;
            rt.SetParent(hud.SafeAreaRect, false);
            rt.anchorMin = rt.anchorMax = Vector2.zero; rt.pivot = Vector2.zero;
            var frame = go.AddComponent<Image>();
            frame.color = k_Frame;
            var img = new GameObject("Map", typeof(RectTransform)) { layer = 5 };
            var irt = (RectTransform)img.transform;
            irt.SetParent(rt, false);
            irt.anchorMin = Vector2.zero; irt.anchorMax = Vector2.one;
            irt.offsetMin = new Vector2(3f, 3f); irt.offsetMax = new Vector2(-3f, -3f);
            var v = go.AddComponent<MiniMapView>();
            v.m_Image = img.AddComponent<RawImage>();
            v.m_Image.raycastTarget = false;   // the frame (parent) takes the tap
            v.m_Nav = nav; v.m_Hud = hud; v.m_Rt = rt; v.m_HudCanvas = hud.GetComponent<UnityEngine.Canvas>();
            v.Relayout(true);
            return v;
        }

        void OnDestroy() { m_Canvas?.Dispose(); m_Canvas = null; Font.textureRebuilt -= OnFontRebuilt; }

        void OnEnable() => Font.textureRebuilt += OnFontRebuilt;
        void OnDisable() => Font.textureRebuilt -= OnFontRebuilt;
        bool m_NeedGlyphs = true;
        void OnFontRebuilt(Font f) { if (m_Canvas != null && f == m_Canvas.Font) { m_NeedGlyphs = true; m_T = float.MaxValue; } }

        public void OnPointerClick(PointerEventData e) => OnOpenMap?.Invoke();

        float Hz => hz > 0f ? hz : QualitySettings.GetQualityLevel() <= 0 ? 15f : 30f;

        /// <summary>Places the widget in its zone; re-creates the render texture when the size or the scale changed.</summary>
        public void Relayout(bool force = false)
        {
            if (m_Hud == null) return;
            var size = m_Hud.SafeSizeUnits;
            bool show = m_Nav != null && m_Nav.Ready && NavHudLayout.Solve(m_Hud.Layout, size.x, size.y, m_Hud.TelemetryVisible, out Rect z);
            if (!show) { if (m_Rt.gameObject.activeSelf) m_Rt.gameObject.SetActive(false); return; }
            NavHudLayout.Solve(m_Hud.Layout, size.x, size.y, m_Hud.TelemetryVisible, out z);
            if (!m_Rt.gameObject.activeSelf) m_Rt.gameObject.SetActive(true);
            float ppu = m_HudCanvas != null ? m_HudCanvas.scaleFactor : 1f;   // UiViewport keeps canvas scale = pixels per unit
            if (!force && z == Zone && Mathf.Approximately(ppu, m_Ppu) && m_Canvas != null) return;
            Zone = z;
            m_Rt.anchoredPosition = z.position; m_Rt.sizeDelta = z.size;
            Vector2 inner = z.size - new Vector2(6f, 6f);
            if (m_Canvas == null || inner != m_Size || !Mathf.Approximately(ppu, m_Ppu))
            {
                m_Canvas?.Dispose();
                m_Size = inner; m_Ppu = ppu;
                m_Canvas = new DisplayCanvas("MiniMap", Mathf.RoundToInt(inner.x), Mathf.RoundToInt(inner.y), Mathf.Max(0.5f, ppu), 2500, UiFonts.Default, 1.0f);
                m_Image.texture = m_Canvas.Texture;
                m_Under = null;
                m_NeedGlyphs = true;
            }
            m_T = float.MaxValue;
        }

        void LateUpdate()
        {
            if (m_Hud == null || m_Nav == null) return;
            Relayout();
            if (!Visible || m_Canvas == null) return;
            float dt = Time.unscaledDeltaTime;
            m_T += dt;
            if (m_T < 1f / Hz) return;
            float step = m_T < 1f ? m_T : 0f;
            m_T = 0f;
            Draw(step);
        }

        void RequestGlyphs()
        {
            m_NeedGlyphs = false;
            foreach (float s in s_Sizes) m_Canvas.RequestGlyphs(NavText.Charset, s);
        }

        static readonly float[] s_Sizes = { 40f, 23f, 21f, 19f, 18f, 16f, 15f };

        /// <summary>One refresh (public for the zero-GC test and captures).</summary>
        public void Draw(float dt)
        {
            if (m_Canvas == null) return;
            long t0 = Stopwatch.GetTimestamp();
            if (m_NeedGlyphs) RequestGlyphs();
            bool night = m_Nav.Night;
            var pal = night ? P.NavNight : P.NavDay;
            if (m_Under == null || m_NightBaked != night)
            {
                m_Under = m_Nav.StaticMap(night);
                m_NightBaked = night;
                m_Canvas.SetUnderlay(m_Under);
            }
            var d = m_Canvas;
            float W = m_Canvas.DesignWidth, H = m_Canvas.DesignHeight;
            var g = m_Nav.Guidance;
            var path = m_Nav.Path;
            bool route = g.HasRoute;
            float top = route ? BannerH : 0f;
            float mapH = H - top - StreetH;

            float kmh = Mathf.Abs(m_Nav.SpeedMs) * 3.6f;
            // Zoom: 1.7 px/m standing (≈ 200 m across), 0.75 px/m at 70 km/h; smoothed (τ 1.2 s). WORKING_VALUES.
            float target = Mathf.Lerp(1.7f, 0.75f, Mathf.Clamp01(kmh / 70f));
            m_Zoom = dt <= 0f ? target : Mathf.Lerp(m_Zoom, target, 1f - Mathf.Exp(-dt / 1.2f));
            float ax = W * 0.5f, ay = top + mapH * 0.72f;
            var xf = MapXf.Make(m_Nav.Position, m_Nav.HeadingDeg, m_Zoom, ax, ay);

            d.Begin();
            if (m_Under != null) d.DrawUnderlay(xf.Matrix(), m_Zoom * d.Scale);
            if (route)
            {
                Vector2 from = g.Segment >= 1 ? Vector2.Lerp(path.Points[g.Segment - 1], path.Points[g.Segment],
                    SegT(path, g.Segment, g.RouteS)) : path.Points[0];
                NavDraw.Route(d, path, g.Segment, from, xf, 9f, pal.RouteCasing, g.OnRoute ? pal.Route : pal.RoutePassed, W, H);
                Vector2 fp = xf.ToScreen(path.Points[path.Count - 1]);
                NavDraw.Flag(d, fp.x, fp.y, 30f, pal.Arrow, P.TellRed);
            }
            else if (m_Nav.HasPin)
            {
                Vector2 pp = xf.ToScreen(m_Nav.PinOnRoad);
                NavDraw.Pin(d, pp.x, pp.y, 34f, P.TellRed, pal.LimitFace, pal.ArrowEdge);
            }
            NavDraw.TruckArrow(d, ax, ay, 0f, 20f, pal.Arrow, pal.ArrowEdge);
            NavDraw.North(d, W - 26f, top + 26f, 17f, m_Nav.HeadingDeg, pal.Bar, pal.BarSub, P.TellRed);

            // Speed limit (OSM-tagged only) above the street strip, lower left.
            if (route && g.OnRoute && g.CurrentLimit > 0) NavDraw.LimitSign(d, m_B, 32f, H - StreetH - 32f, 25f, g.CurrentLimit, pal);

            // Street strip.
            d.Rect(0f, H - StreetH, W, StreetH, pal.Bar);
            string street = m_Nav.NameOf(m_Nav.CurrentStreet);
            if (street.Length > 0) NavDraw.FitText(d, m_Fit, NavLayout.Abbreviate(street), W * 0.5f, H - 11f, 19f, W - 16f, pal.BarText, DisplayCanvas.Align.Center);

            if (route) Banner(d, g, path, W, pal);
            d.End(pal.Bg);

            LastCpuMs = (Stopwatch.GetTimestamp() - t0) * 1000.0 / Stopwatch.Frequency;
            m_CpuSum += LastCpuMs; m_Refreshes++;
        }

        static float SegT(RoutePath p, int seg, float s)
        {
            float a = p.S[seg - 1], b = p.S[seg];
            return b - a > 1e-4f ? Mathf.Clamp01((s - a) / (b - a)) : 0f;
        }

        void Banner(DisplayCanvas d, in NavGuidance g, RoutePath p, float W, in P.Nav pal)
        {
            d.Rect(0f, 0f, W, BannerH, pal.Box);
            if (g.Arrived)
            {
                NavDraw.ManeuverIcon(d, 54f, BannerH * 0.5f, 84f, Maneuver.Arrive, 0f, pal.BoxText, pal.Box);
                d.Text(NavText.Arrived, 104f, 62f, 23f, pal.BoxText);
                return;
            }
            if (!g.OnRoute || g.Next < 0)
            {
                d.Text(Time.unscaledTime - m_Nav.LastRerouteTime < 3f ? NavText.Rerouting : NavText.OffRoute, 20f, 64f, 23f, pal.BoxText);
                return;
            }
            int k = g.Next;
            var type = p.ManType[k];
            NavDraw.ManeuverIcon(d, 54f, BannerH * 0.5f, 84f, type, p.ManTurn[k], pal.BoxText, pal.Box);
            m_B.Clear();
            NavDraw.AppendDistance(m_B, g.NextM);
            d.Text(m_B, 104f, 52f, 40f, pal.BoxText);
            if (type == Maneuver.Roundabout && p.ManExit[k] > 0)
            {
                // Exit number in the ring of the pictogram.
                m_B.Clear().Append(p.ManExit[k]);
                d.Text(m_B, 54f, BannerH * 0.5f + 6f, 16f, pal.BoxText, DisplayCanvas.Align.Center);
            }
            string nm = m_Nav.NameOf(p.ManName[k]);
            float nameW = W - 104f - 10f;
            if (nm.Length > 0) NavDraw.FitText(d, m_Fit, NavLayout.Abbreviate(nm), 104f, 90f, 19f, nameW, pal.BoxSub);
            if (g.Then >= 0 && W >= 300f)
            {
                // "then" chip: small pictogram of the following manoeuvre, top right.
                float cx = W - 34f;
                d.Rect(cx - 28f, 8f, 56f, 56f, pal.RouteCasing);
                NavDraw.ManeuverIcon(d, cx, 36f, 40f, p.ManType[g.Then], p.ManTurn[g.Then], pal.BoxText, pal.RouteCasing);
            }
        }
    }
}
