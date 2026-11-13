using Game.Core.Navigation;
using Game.UI.CabDisplays;
using Game.UI.Layout;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using P = Game.UI.CabDisplays.DisplayPalette;

namespace Game.UI.Navigation
{
    /// <summary>
    /// Full-screen map for choosing the destination (ADR 0150). North-up vector map of the region from our own data
    /// (OSM-derived roads with street names along them, BDOT10k/OSM buildings), the truck, the destination pin, the
    /// planned route. Drag = pan, pinch / wheel = zoom, tap = destination pin; "Wyznacz trasę" plans with the GPS planner,
    /// "Wyczyść trasę" removes it. The simulation is PAUSED while the map is open (Time.timeScale 0 + audio pause): the map
    /// covers the road, and truck navigations accept destination entry only at standstill. Android back closes it.
    /// </summary>
    public sealed class FullMapView : MonoBehaviour
    {
        const float Margin = 24f, BtnH = 88f, PanelH = 176f;
        static readonly Color k_Panel = new Color(0.07f, 0.075f, 0.08f, 0.96f);
        static readonly Color k_Button = new Color(0.17f, 0.18f, 0.19f, 1f);
        static readonly Color k_Primary = new Color(0.16f, 0.36f, 0.62f, 1f);   // route blue family (DisplayPalette.Nav.Route)
        static readonly Color k_Text = new Color(0.95f, 0.95f, 0.92f, 1f);
        static readonly Color k_Muted = new Color(0.68f, 0.69f, 0.68f, 1f);

        static FullMapView s_Open;
        public static bool IsOpen => s_Open != null && s_Open.m_Visible;

        /// <summary>Android back / Escape while the map is open: closes it and reports the key as consumed.</summary>
        public static bool HandleBack()
        {
            if (!IsOpen) return false;
            s_Open.Close();
            return true;
        }

        NavigationService m_Nav;
        Canvas m_UiCanvas;
        UiViewport m_View;
        RectTransform m_Root, m_SafeRt;
        RawImage m_Image;
        DisplayCanvas m_Canvas;
        Vector2 m_DesignSize;
        float m_Ppu;
        Vector2 m_Centre;
        float m_Zoom = 1f;
        bool m_Visible, m_Dirty = true;
        float m_RedrawT;
        float m_PrevTimeScale = 1f;
        bool m_Paused;
        int m_StateKey = int.MinValue;
        Mesh m_Under;
        bool m_UnderNight;

        GameObject m_Panel;
        Text m_Title, m_Sub, m_PauseNote;
        Button m_Primary, m_Secondary;
        Text m_PrimaryLabel, m_SecondaryLabel;
        System.Action m_PrimaryAction, m_SecondaryAction;

        readonly TextBuffer m_B = new TextBuffer(48);
        int[] m_RoadOrder;
        Vector4[] m_Placed = new Vector4[128];
        int m_PlacedCount;
        Vector2[] m_NameAt;
        byte[] m_NameN;

        public DisplayCanvas MapCanvas => m_Canvas;
        public Vector2 Centre => m_Centre;
        public float Zoom => m_Zoom;

        /// <param name="cam">null = Screen Space - Overlay (runtime); a camera for captures (Camera.Render).</param>
        public static FullMapView Create(NavigationService nav, Camera cam = null)
        {
            var go = new GameObject("NavFullMap") { layer = 5 };
            var v = go.AddComponent<FullMapView>();
            v.m_Nav = nav;
            v.Build(cam);
            v.SetVisible(false);
            return v;
        }

        public void OverrideScreen(Vector2 px, Rect safePx, float dpi)
        {
            m_View.OverrideScreen(px, safePx, dpi); m_View.Refresh(); EnsureCanvas();
            m_Zoom = DefaultZoom(); Recenter(); Relayout();
        }

        void Build(Camera cam)
        {
            m_UiCanvas = gameObject.AddComponent<Canvas>();
            m_UiCanvas.renderMode = cam != null ? RenderMode.ScreenSpaceCamera : RenderMode.ScreenSpaceOverlay;
            m_UiCanvas.worldCamera = cam;
            m_UiCanvas.planeDistance = cam != null ? Mathf.Max(cam.nearClipPlane * 2f, 0.11f) : 1f;
            m_UiCanvas.sortingOrder = 950;   // above the driving HUD (900)
            gameObject.AddComponent<GraphicRaycaster>();
            m_View = new UiViewport(m_UiCanvas);
            m_Root = (RectTransform)transform;
            m_SafeRt = m_View.SafeArea;

            var img = NewRect("Map", m_Root);
            img.SetAsFirstSibling();
            Stretch(img);
            m_Image = img.gameObject.AddComponent<RawImage>();
            m_Image.color = Color.white;
            var gest = img.gameObject.AddComponent<MapGestures>();
            gest.owner = this;

            // Top left: back. Top right: zoom + recentre. Bottom: destination panel.
            Btn(m_SafeRt, "Back", new Vector2(0f, 1f), new Vector2(Margin, -Margin - 80f), new Vector2(190f, 80f), NavText.Back, 28, k_Button, Close, out _);
            Btn(m_SafeRt, "ZoomIn", new Vector2(1f, 1f), new Vector2(-Margin - 88f, -Margin - 88f), new Vector2(88f, 88f), NavText.ZoomIn, 40, k_Button, () => ZoomBy(1.6f), out _);
            Btn(m_SafeRt, "ZoomOut", new Vector2(1f, 1f), new Vector2(-Margin - 88f, -Margin - 184f), new Vector2(88f, 88f), NavText.ZoomOut, 40, k_Button, () => ZoomBy(1f / 1.6f), out _);
            Btn(m_SafeRt, "Recenter", new Vector2(1f, 1f), new Vector2(-Margin - 132f, -Margin - 280f), new Vector2(132f, 80f), NavText.Recenter, 24, k_Button, Recenter, out _);
            var pn = NewRect("PauseNote", m_SafeRt);
            pn.anchorMin = pn.anchorMax = new Vector2(0.5f, 1f); pn.pivot = new Vector2(0.5f, 1f);
            pn.anchoredPosition = new Vector2(0f, -Margin); pn.sizeDelta = new Vector2(560f, 48f);
            var pni = pn.gameObject.AddComponent<Image>(); pni.color = k_Panel; pni.raycastTarget = false;
            m_PauseNote = Label(pn, "Text", NavText.Paused, 21, TextAnchor.MiddleCenter, k_Muted);
            Stretch((RectTransform)m_PauseNote.transform);

            var panel = NewRect("Panel", m_SafeRt);
            m_Panel = panel.gameObject;
            panel.anchorMin = panel.anchorMax = new Vector2(0.5f, 0f); panel.pivot = new Vector2(0.5f, 0f);
            var pimg = panel.gameObject.AddComponent<Image>(); pimg.color = k_Panel;
            m_Title = Label(panel, "Title", "", 30, TextAnchor.UpperLeft, k_Text);
            m_Sub = Label(panel, "Sub", "", 23, TextAnchor.UpperLeft, k_Muted);
            m_Primary = Btn(panel, "Primary", new Vector2(1f, 0f), Vector2.zero, new Vector2(280f, BtnH), "", 28, k_Primary, () => m_PrimaryAction?.Invoke(), out m_PrimaryLabel);
            m_Secondary = Btn(panel, "Secondary", new Vector2(1f, 0f), Vector2.zero, new Vector2(240f, BtnH), "", 26, k_Button, () => m_SecondaryAction?.Invoke(), out m_SecondaryLabel);
            EnsureEventSystem();
        }

        static void EnsureEventSystem()
        {
            if (EventSystem.current != null || Object.FindAnyObjectByType<EventSystem>() != null) return;
            var es = new GameObject("EventSystem");
            es.AddComponent<EventSystem>();
            es.AddComponent<UnityEngine.InputSystem.UI.InputSystemUIInputModule>();
        }

        // ------------------------------------------------------------------ open / close

        public void Open()
        {
            if (m_Nav == null || !m_Nav.Ready) return;
            s_Open = this;
            SetVisible(true);
            if (!m_Paused)
            {
                m_PrevTimeScale = Time.timeScale;
                Time.timeScale = 0f;
                AudioListener.pause = true;
                m_Paused = true;
            }
            m_View.Invalidate();
            m_View.Refresh();
            EnsureCanvas();
            Recenter();
            m_Zoom = DefaultZoom();
            m_StateKey = int.MinValue;
            Relayout();
            Debug.Log("[NAV] map open (simulation paused)");
        }

        public void Close()
        {
            SetVisible(false);
            if (m_Paused)
            {
                Time.timeScale = m_PrevTimeScale > 0f ? m_PrevTimeScale : 1f;
                AudioListener.pause = false;
                m_Paused = false;
            }
            m_Canvas?.Dispose(); m_Canvas = null;   // a full-screen render texture is not kept while driving
            m_Image.texture = null;
            if (s_Open == this) s_Open = null;
        }

        void OnEnable() => Font.textureRebuilt += OnFontRebuilt;
        void OnDisable() => Font.textureRebuilt -= OnFontRebuilt;

        void OnFontRebuilt(Font f)
        {
            if (m_Canvas == null || f != m_Canvas.Font) return;
            foreach (float s in s_Sizes) m_Canvas.RequestGlyphs(NavText.Charset, s);
            m_Dirty = true;
        }

        void OnDestroy()
        {
            if (m_Paused) { Time.timeScale = m_PrevTimeScale > 0f ? m_PrevTimeScale : 1f; AudioListener.pause = false; m_Paused = false; }
            m_Canvas?.Dispose(); m_Canvas = null;
            if (s_Open == this) s_Open = null;
        }

        void SetVisible(bool on)
        {
            m_Visible = on;
            if (m_UiCanvas != null) m_UiCanvas.enabled = on;
            var gr = GetComponent<GraphicRaycaster>();
            if (gr != null) gr.enabled = on;
        }

        float DefaultZoom() => Mathf.Min(m_DesignSize.x, m_DesignSize.y) / 900f;   // ~900 m across the short side. WORKING_VALUE.
        float MinZoom => Mathf.Min(m_DesignSize.x, m_DesignSize.y) / 3200f;
        float MaxZoom => Mathf.Min(m_DesignSize.x, m_DesignSize.y) / 110f;

        void EnsureCanvas()
        {
            Vector2 px = m_View.PixelSize;   // the viewport's pixel size (honours the capture / test override)
            float ppu = m_View.PixelsPerUnit;
            if (px.x < 1f || px.y < 1f) px = new Vector2(Screen.width, Screen.height);
            Vector2 units = new Vector2(Mathf.Round(px.x / ppu), Mathf.Round(px.y / ppu));
            if (m_Canvas != null && units == m_DesignSize && Mathf.Approximately(ppu, m_Ppu)) return;
            m_Canvas?.Dispose();
            m_DesignSize = units; m_Ppu = ppu;
            // Render scale: full resolution, 0.75 on Low (a paused, static picture - fill cost is paid once per redraw).
            float scale = ppu * (QualitySettings.GetQualityLevel() <= 0 ? 0.75f : 1f);
            m_Canvas = new DisplayCanvas("FullMap", (int)units.x, (int)units.y, scale, 14000, UiFonts.Default, 1.0f);
            m_Image.texture = m_Canvas.Texture;
            m_Under = null;
            foreach (float s in s_Sizes) m_Canvas.RequestGlyphs(NavText.Charset, s);
            m_Dirty = true;
        }

        static readonly float[] s_Sizes = { 22f, 19f, 17f, 16f, 15f };

        // ------------------------------------------------------------------ view

        public void Recenter() { if (m_Nav != null && m_Nav.HasPosition) m_Centre = m_Nav.Position; m_Dirty = true; }

        public void ZoomBy(float k) => ZoomAbout(m_DesignSize * 0.5f, k);

        /// <summary>Zoom by <paramref name="k"/> keeping the map point under <paramref name="design"/> (design px, y down) fixed.</summary>
        public void ZoomAbout(Vector2 design, float k)
        {
            var xf = Xf();
            Vector2 w = xf.ToWorld(design);
            m_Zoom = Mathf.Clamp(m_Zoom * k, MinZoom, MaxZoom);
            xf = Xf();
            Vector2 w2 = xf.ToWorld(design);
            m_Centre += w - w2;
            ClampCentre();
            m_Dirty = true;
        }

        /// <summary>Pan by a design-px delta (y down).</summary>
        public void Pan(Vector2 designDelta)
        {
            m_Centre += new Vector2(-designDelta.x, designDelta.y) / m_Zoom;
            ClampCentre();
            m_Dirty = true;
        }

        void ClampCentre()
        {
            var g = m_Nav.Graph;
            if (g == null) return;
            m_Centre = new Vector2(Mathf.Clamp(m_Centre.x, g.Min.x, g.Max.x), Mathf.Clamp(m_Centre.y, g.Min.y, g.Max.y));
        }

        MapXf Xf() => MapXf.Make(m_Centre, 0f, m_Zoom, m_DesignSize.x * 0.5f, m_DesignSize.y * 0.5f);

        /// <summary>Tap at design px: sets the destination pin on the nearest road.</summary>
        public void TapAt(Vector2 design)
        {
            Vector2 w = Xf().ToWorld(design);
            m_Nav.SetPin(w);   // failure shows the "too far from a road" message
            m_StateKey = int.MinValue;
            m_Dirty = true;
        }

        public void PlanRoute()
        {
            m_Nav.PlanToPin();
            m_StateKey = int.MinValue;
            m_Dirty = true;
        }

        public void ClearRoute()
        {
            m_Nav.ClearRoute();
            m_StateKey = int.MinValue;
            m_Dirty = true;
        }

        /// <summary>Screen pixel -> design px (y down) on the map image.</summary>
        public Vector2 ScreenToDesign(Vector2 screen, Camera eventCam)
        {
            var rt = (RectTransform)m_Image.transform;
            RectTransformUtility.ScreenPointToLocalPointInRectangle(rt, screen, eventCam, out Vector2 local);
            Rect r = rt.rect;
            return new Vector2((local.x - r.xMin) / Mathf.Max(1f, r.width) * m_DesignSize.x, (r.yMax - local.y) / Mathf.Max(1f, r.height) * m_DesignSize.y);
        }

        public float PixelsToDesign => m_UiCanvas.scaleFactor > 0f ? 1f / m_UiCanvas.scaleFactor : 1f;

        // ------------------------------------------------------------------ frame

        void LateUpdate()
        {
            if (!m_Visible) return;
            if (m_View.Refresh()) { EnsureCanvas(); Relayout(); }
            int key = StateKey();
            if (key != m_StateKey) { m_StateKey = key; Relayout(); }
            m_RedrawT += Time.unscaledDeltaTime;
            if (m_Dirty || m_RedrawT > 0.5f) DrawNow();
        }

        int StateKey()
        {
            int k = m_Nav.HasPin ? 1 : 0;
            k |= m_Nav.Path != null && m_Nav.Path.HasRoute ? 2 : 0;
            k |= (int)m_Nav.LastStatus << 2;
            return k ^ (m_Nav.Path != null ? m_Nav.Path.Version << 8 : 0) ^ (m_Nav.Pin.GetHashCode() << 3);
        }

        /// <summary>Bottom panel text and buttons for the current state; panel width fits the safe area.</summary>
        void Relayout()
        {
            Vector2 safe = m_View.SizeUnits;
            float pw = Mathf.Min(1240f, safe.x - 2f * Margin);
            var prt = (RectTransform)m_Panel.transform;
            prt.anchoredPosition = new Vector2(0f, Margin);
            prt.sizeDelta = new Vector2(pw, PanelH);
            bool route = m_Nav.Path != null && m_Nav.Path.HasRoute;
            string dest = m_Nav.HasPin ? m_Nav.NameOf(m_Nav.PinName) : "";
            if (dest.Length == 0) dest = NavText.Unnamed;
            string title, sub = "";
            m_PrimaryAction = null; m_SecondaryAction = null;
            string pl = null, sl = null;
            var st = m_Nav.LastStatus;
            if (st == PlanStatus.GoalOffRoad) { title = NavText.OffRoad; }
            else if (!m_Nav.HasPin) { title = NavText.TapHint; }
            else if (route)
            {
                title = NavText.Destination + ": " + NavLayout.Abbreviate(dest);
                m_B.Clear(); NavDraw.AppendDistance(m_B, m_Nav.Path.Length);
                int min = Mathf.Max(1, Mathf.RoundToInt(m_Nav.Path.CostSeconds / 60f));
                sub = m_B.ToString() + " · " + NavText.About + " " + min + " " + NavText.Minutes;
                pl = NavText.Drive; m_PrimaryAction = Close;
                sl = NavText.ClearRoute; m_SecondaryAction = ClearRoute;
            }
            else
            {
                title = NavText.Destination + ": " + NavLayout.Abbreviate(dest);
                m_B.Clear(); NavDraw.AppendDistance(m_B, Vector2.Distance(m_Nav.Position, m_Nav.PinOnRoad));
                sub = m_B.ToString() + " " + NavText.StraightLine;
                if (st == PlanStatus.GoalOffReach) sub = NavText.OffReach;
                else if (st == PlanStatus.NoPath) sub = NavText.NoPath;
                else if (st == PlanStatus.StartOffRoad) sub = NavText.StartOffRoad;
                else if (st == PlanStatus.AlreadyThere) sub = NavText.AlreadyThere;
                pl = NavText.PlanRoute; m_PrimaryAction = PlanRoute;
                sl = NavText.ClearPin; m_SecondaryAction = ClearRoute;
            }
            m_Title.text = title; m_Sub.text = sub;
            bool two = pw >= 900f;   // buttons beside the text, otherwise the text gets the top row
            SetBtn(m_Primary, m_PrimaryLabel, pl, new Vector2(-Margin - 280f, 22f));
            SetBtn(m_Secondary, m_SecondaryLabel, sl, new Vector2(-Margin - 280f - 16f - 240f, 22f));
            float textW = pl == null ? pw - 2f * Margin : two ? pw - 2f * Margin - 560f : pw - 2f * Margin;
            var trt = (RectTransform)m_Title.transform;
            trt.anchorMin = trt.anchorMax = new Vector2(0f, 1f); trt.pivot = new Vector2(0f, 1f);
            trt.anchoredPosition = new Vector2(Margin, -18f); trt.sizeDelta = new Vector2(textW, 44f);
            var srt = (RectTransform)m_Sub.transform;
            srt.anchorMin = srt.anchorMax = new Vector2(0f, 1f); srt.pivot = new Vector2(0f, 1f);
            srt.anchoredPosition = new Vector2(Margin, -64f); srt.sizeDelta = new Vector2(textW, 36f);
            m_Dirty = true;
        }

        static void SetBtn(Button b, Text label, string text, Vector2 pos)
        {
            bool on = text != null;
            if (b.gameObject.activeSelf != on) b.gameObject.SetActive(on);
            if (!on) return;
            label.text = text;
            var rt = (RectTransform)b.transform;
            rt.anchoredPosition = pos;
        }

        /// <summary>Redraws the map now (captures, tests).</summary>
        public void DrawNow()
        {
            if (m_Canvas == null) return;
            m_Dirty = false; m_RedrawT = 0f;
            bool night = m_Nav.Night;
            var pal = night ? P.NavNight : P.NavDay;
            if (m_Under == null || m_UnderNight != night) { m_Under = m_Nav.StaticMap(night); m_UnderNight = night; m_Canvas.SetUnderlay(m_Under); }
            var d = m_Canvas;
            float W = m_DesignSize.x, H = m_DesignSize.y;
            var xf = Xf();
            d.Begin();
            if (m_Under != null) d.DrawUnderlay(xf.Matrix(), m_Zoom * d.Scale);
            Labels(d, xf, night, pal, W, H);
            var path = m_Nav.Path;
            if (path != null && path.HasRoute)
            {
                float w = Mathf.Clamp(m_Zoom * 7f, 6f, 14f);
                NavDraw.Route(d, path, 0, path.Points[0], xf, w, pal.RouteCasing, pal.Route, W, H);
                Vector2 fp = xf.ToScreen(path.Points[path.Count - 1]);
                NavDraw.Flag(d, fp.x, fp.y, 40f, pal.Arrow, P.TellRed);
            }
            else if (m_Nav.HasPin)
            {
                Vector2 pp = xf.ToScreen(m_Nav.PinOnRoad);
                NavDraw.Pin(d, pp.x, pp.y, 46f, P.TellRed, pal.LimitFace, pal.ArrowEdge);
            }
            if (m_Nav.HasPosition)
            {
                Vector2 tp = xf.ToScreen(m_Nav.Position);
                NavDraw.TruckArrow(d, tp.x, tp.y, m_Nav.HeadingDeg, 24f, pal.Arrow, pal.ArrowEdge);
            }
            // Scale bar and attribution, bottom left above the panel (inside the safe area).
            Rect safe = SafeDesignRect();
            float by = safe.yMax - PanelH - Margin - 16f;
            ScaleBar(d, safe.xMin + Margin, by - 26f, pal);
            d.Text(NavText.Attribution, safe.xMin + Margin, by, 16f, night ? pal.BarSub : new Color32(70, 72, 76, 255));
            d.End(pal.Bg);
        }

        Rect SafeDesignRect()
        {
            var s = m_SafeRt;
            Vector2 a = s.anchorMin, b = s.anchorMax;
            // y down in design px.
            return Rect.MinMaxRect(a.x * m_DesignSize.x, (1f - b.y) * m_DesignSize.y, b.x * m_DesignSize.x, (1f - a.y) * m_DesignSize.y);
        }

        void ScaleBar(DisplayCanvas d, float x, float y, in P.Nav pal)
        {
            // Largest of 1-2-5 x 10^n metres that fits in 160 design px.
            float maxM = 160f / m_Zoom, m = 1f;
            float[] steps = s_Steps;
            for (int i = 0; i < steps.Length; i++) if (steps[i] <= maxM) m = steps[i];
            float len = m * m_Zoom;
            Color32 c = pal.Arrow;
            d.Rect(x, y, len, 4f, c);
            d.Rect(x, y - 8f, 3f, 12f, c);
            d.Rect(x + len - 3f, y - 8f, 3f, 12f, c);
            m_B.Clear();
            NavDraw.AppendDistance(m_B, m);
            d.Text(m_B, x + len + 10f, y + 6f, 15f, c);
        }

        static readonly float[] s_Steps = { 10f, 20f, 50f, 100f, 200f, 500f, 1000f, 2000f };

        // ------------------------------------------------------------------ street names

        void Labels(DisplayCanvas d, in MapXf xf, bool night, in P.Nav pal, float W, float H)
        {
            var map = m_Nav.Map;
            if (map == null || m_Zoom < 0.25f) return;
            if (m_RoadOrder == null)
            {
                BuildChains(map);
                m_NameAt = new Vector2[map.Names.Length];
                m_NameN = new byte[map.Names.Length];
            }
            System.Array.Clear(m_NameN, 0, m_NameN.Length);
            m_PlacedCount = 0;
            Color32 fg = night ? new Color32(200, 202, 206, 255) : new Color32(52, 54, 58, 255);
            Color32 halo = night ? pal.Bg : new Color32(250, 250, 246, 255);
            foreach (int i in m_RoadOrder)
            {
                int nm = m_ChainName[i];
                if (nm == 0 || m_NameN[nm] >= 3) continue;
                if (m_ChainClass[i] == 0 && m_Zoom < 0.9f) continue;   // minor names only when zoomed in
                // Longest nearly straight visible run of the street chain (direction within 15° of the run's first segment).
                float best = 0f; Vector2 ba = default, bb = default;
                int k0 = m_ChainStart[i], k1 = m_ChainStart[i + 1];
                Vector2 runA = default, runDir = default, prev = default;
                float runLen = 0f;
                for (int k = k0; k < k1; k++)
                {
                    Vector2 q = xf.ToScreen(m_ChainPts[k]);
                    bool inside = q.x > 30f && q.x < W - 30f && q.y > 30f && q.y < H - 30f;
                    if (k > k0)
                    {
                        Vector2 seg = q - prev;
                        float sl = seg.magnitude;
                        bool cont = inside && runLen > 0f && sl > 1e-3f && Vector2.Dot(seg / sl, runDir) > 0.966f;
                        if (cont) runLen += sl;
                        else if (inside && sl > 1e-3f && prev.x > 30f && prev.x < W - 30f && prev.y > 30f && prev.y < H - 30f)
                        { runA = prev; runDir = seg / sl; runLen = sl; }
                        else runLen = 0f;
                        if (runLen > 0f && runLen * runLen > best) { best = runLen * runLen; ba = runA; bb = q; }
                    }
                    prev = q;
                }
                if (best <= 0f) continue;
                string text = NavLayout.Abbreviate(map.Names[nm]);
                float size = m_ChainClass[i] >= 2 ? 19f : 17f;
                float tw = d.Measure(text, size);
                if (Mathf.Sqrt(best) < tw + 24f) continue;
                Vector2 c = (ba + bb) * 0.5f;
                if (m_NameN[nm] > 0 && (m_NameAt[nm] - c).sqrMagnitude < 420f * 420f) continue;
                float ang = Mathf.Atan2(bb.y - ba.y, bb.x - ba.x) * Mathf.Rad2Deg;
                if (ang > 90f) ang -= 180f; else if (ang < -90f) ang += 180f;
                // Axis-aligned box of the rotated label.
                float ca = Mathf.Abs(Mathf.Cos(ang * Mathf.Deg2Rad)), sa = Mathf.Abs(Mathf.Sin(ang * Mathf.Deg2Rad));
                float hw = (tw * ca + size * sa) * 0.5f + 4f, hh = (tw * sa + size * ca) * 0.5f + 4f;
                var box = new Vector4(c.x - hw, c.y - hh, c.x + hw, c.y + hh);
                if (Overlaps(box)) continue;
                if (m_PlacedCount < m_Placed.Length) m_Placed[m_PlacedCount++] = box;
                m_NameAt[nm] = c; m_NameN[nm]++;
                const float o = 1.6f;
                d.TextRotated(text, c.x - o, c.y, ang, size, halo); d.TextRotated(text, c.x + o, c.y, ang, size, halo);
                d.TextRotated(text, c.x, c.y - o, ang, size, halo); d.TextRotated(text, c.x, c.y + o, ang, size, halo);
                d.TextRotated(text, c.x, c.y, ang, size, fg);
            }
        }

        Vector2[] m_ChainPts;
        int[] m_ChainStart;
        ushort[] m_ChainName;
        byte[] m_ChainClass;

        /// <summary>
        /// Joins the map's road polylines (split at every junction) into street chains - consecutive pieces with the same
        /// name meeting end to end - so a label can use a long straight stretch of the street. Built once per map open.
        /// </summary>
        void BuildChains(NavMapData map)
        {
            int n = map.RoadCount;
            var used = new bool[n];
            var byEnd = new System.Collections.Generic.Dictionary<long, System.Collections.Generic.List<int>>();
            long Key(Vector2 p, int name) => ((long)Mathf.RoundToInt(p.x * 2f) * 73856093L) ^ ((long)Mathf.RoundToInt(p.y * 2f) * 19349663L) ^ ((long)name << 40);
            void Index(Vector2 p, int name, int road)
            {
                long k = Key(p, name);
                if (!byEnd.TryGetValue(k, out var l)) byEnd[k] = l = new System.Collections.Generic.List<int>(2);
                l.Add(road);
            }
            for (int i = 0; i < n; i++)
            {
                if (map.RoadName[i] == 0 || map.RoadStart[i + 1] - map.RoadStart[i] < 2) continue;
                Index(map.RoadPoints[map.RoadStart[i]], map.RoadName[i], i);
                Index(map.RoadPoints[map.RoadStart[i + 1] - 1], map.RoadName[i], i);
            }
            var pts = new System.Collections.Generic.List<Vector2>(map.RoadPoints.Length);
            var starts = new System.Collections.Generic.List<int>();
            var names = new System.Collections.Generic.List<ushort>();
            var classes = new System.Collections.Generic.List<byte>();
            var chain = new System.Collections.Generic.List<Vector2>(256);
            int Next(Vector2 end, int name)
            {
                if (!byEnd.TryGetValue(Key(end, name), out var l)) return -1;
                foreach (int r in l) if (!used[r]) return r;
                return -1;
            }
            void Append(int r, bool atEnd)
            {
                used[r] = true;
                int a = map.RoadStart[r], b = map.RoadStart[r + 1] - 1;
                Vector2 tail = atEnd ? chain[chain.Count - 1] : chain[0];
                bool fwd = (map.RoadPoints[a] - tail).sqrMagnitude <= (map.RoadPoints[b] - tail).sqrMagnitude;
                if (atEnd) { if (fwd) for (int k = a + 1; k <= b; k++) chain.Add(map.RoadPoints[k]); else for (int k = b - 1; k >= a; k--) chain.Add(map.RoadPoints[k]); }
                else { if (fwd) for (int k = a + 1; k <= b; k++) chain.Insert(0, map.RoadPoints[k]); else for (int k = b - 1; k >= a; k--) chain.Insert(0, map.RoadPoints[k]); }
            }
            for (int i = 0; i < n; i++)
            {
                if (used[i] || map.RoadName[i] == 0 || map.RoadStart[i + 1] - map.RoadStart[i] < 2) continue;
                int name = map.RoadName[i];
                byte cls = map.RoadClass[i];
                used[i] = true;
                chain.Clear();
                for (int k = map.RoadStart[i]; k < map.RoadStart[i + 1]; k++) chain.Add(map.RoadPoints[k]);
                for (int r; (r = Next(chain[chain.Count - 1], name)) >= 0;) { Append(r, true); cls = (byte)Mathf.Max(cls, map.RoadClass[r]); }
                for (int r; (r = Next(chain[0], name)) >= 0;) { Append(r, false); cls = (byte)Mathf.Max(cls, map.RoadClass[r]); }
                starts.Add(pts.Count); names.Add((ushort)name); classes.Add(cls);
                pts.AddRange(chain);
            }
            starts.Add(pts.Count);
            m_ChainPts = pts.ToArray(); m_ChainStart = starts.ToArray(); m_ChainName = names.ToArray(); m_ChainClass = classes.ToArray();
            m_RoadOrder = new int[m_ChainName.Length];
            for (int i = 0; i < m_RoadOrder.Length; i++) m_RoadOrder[i] = i;
            var cl = m_ChainClass;
            System.Array.Sort(m_RoadOrder, (a, b) => cl[b].CompareTo(cl[a]));
        }

        bool Overlaps(Vector4 b)
        {
            for (int i = 0; i < m_PlacedCount; i++)
            {
                var p = m_Placed[i];
                if (b.x < p.z && b.z > p.x && b.y < p.w && b.w > p.y) return true;
            }
            return false;
        }

        // ------------------------------------------------------------------ uGUI helpers

        static RectTransform NewRect(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform)) { layer = 5 };
            var rt = (RectTransform)go.transform;
            rt.SetParent(parent, false);
            return rt;
        }

        static void Stretch(RectTransform rt)
        {
            rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = rt.offsetMax = Vector2.zero;
        }

        static Text Label(Transform parent, string name, string text, int size, TextAnchor anchor, Color c)
        {
            var rt = NewRect(name, parent);
            var t = rt.gameObject.AddComponent<Text>();
            t.font = UiFonts.Default; t.fontSize = size; t.alignment = anchor; t.color = c; t.text = text;
            t.horizontalOverflow = HorizontalWrapMode.Wrap; t.verticalOverflow = VerticalWrapMode.Truncate;
            t.raycastTarget = false;
            return t;
        }

        /// <param name="corner">Anchor and pivot (0/1 per axis); <paramref name="pos"/> = offset of the button's lower-left
        /// corner from that anchor... expressed as anchoredPosition with pivot (0,0).</param>
        static Button Btn(Transform parent, string name, Vector2 corner, Vector2 pos, Vector2 size, string text, int fontSize, Color bg,
            UnityEngine.Events.UnityAction onClick, out Text label)
        {
            var rt = NewRect(name, parent);
            rt.anchorMin = rt.anchorMax = corner; rt.pivot = Vector2.zero;
            rt.anchoredPosition = pos; rt.sizeDelta = size;
            var img = rt.gameObject.AddComponent<Image>(); img.color = bg;
            var b = rt.gameObject.AddComponent<Button>();
            b.targetGraphic = img;
            var cb = b.colors; cb.highlightedColor = Color.white; cb.pressedColor = new Color(0.8f, 0.8f, 0.8f, 1f); cb.selectedColor = Color.white; b.colors = cb;
            b.onClick.AddListener(onClick);
            label = Label(rt, "Label", text, fontSize, TextAnchor.MiddleCenter, k_Text);
            Stretch((RectTransform)label.transform);
            return b;
        }
    }

    /// <summary>Map gestures: one finger pans, two fingers pinch-zoom (and pan), mouse wheel zooms, a short tap sets the pin.</summary>
    public sealed class MapGestures : MonoBehaviour, IPointerDownHandler, IPointerUpHandler, IDragHandler, IScrollHandler
    {
        public FullMapView owner;
        /// <summary>A press that moved less than this [screen px] and lasted less than <see cref="TapS"/> is a tap. WORKING_VALUES.</summary>
        public const float TapMovePx = 18f, TapS = 0.45f;

        readonly int[] m_Id = { int.MinValue, int.MinValue };
        readonly Vector2[] m_Pos = new Vector2[2];
        int m_Count;
        bool m_Multi;
        float m_DownT, m_Moved;

        public void OnPointerDown(PointerEventData e)
        {
            if (m_Count >= 2) return;
            int slot = m_Id[0] == int.MinValue ? 0 : 1;
            m_Id[slot] = e.pointerId; m_Pos[slot] = e.position;
            m_Count++;
            if (m_Count == 1) { m_Multi = false; m_Moved = 0f; m_DownT = Time.unscaledTime; }
            else m_Multi = true;
        }

        public void OnDrag(PointerEventData e)
        {
            int slot = e.pointerId == m_Id[0] ? 0 : e.pointerId == m_Id[1] ? 1 : -1;
            if (slot < 0 || owner == null) return;
            float k = owner.PixelsToDesign;
            if (m_Count == 2)
            {
                int other = 1 - slot;
                Vector2 a0 = m_Pos[slot], b = m_Pos[other], a1 = e.position;
                float d0 = Vector2.Distance(a0, b), d1 = Vector2.Distance(a1, b);
                Vector2 mid0 = (a0 + b) * 0.5f, mid1 = (a1 + b) * 0.5f;
                if (d0 > 4f) owner.ZoomAbout(owner.ScreenToDesign(mid1, e.pressEventCamera), d1 / d0);
                Vector2 dm = mid1 - mid0;
                owner.Pan(new Vector2(dm.x, -dm.y) * k);
            }
            else
            {
                owner.Pan(new Vector2(e.delta.x, -e.delta.y) * k);
            }
            m_Moved += e.delta.magnitude;
            m_Pos[slot] = e.position;
        }

        public void OnPointerUp(PointerEventData e)
        {
            int slot = e.pointerId == m_Id[0] ? 0 : e.pointerId == m_Id[1] ? 1 : -1;
            if (slot < 0) return;
            m_Id[slot] = int.MinValue;
            m_Count--;
            if (m_Count == 0)
            {
                if (!m_Multi && m_Moved < TapMovePx && Time.unscaledTime - m_DownT < TapS && owner != null)
                    owner.TapAt(owner.ScreenToDesign(e.position, e.pressEventCamera));
                m_Multi = false;
            }
        }

        public void OnScroll(PointerEventData e)
        {
            if (owner == null) return;
            owner.ZoomAbout(owner.ScreenToDesign(e.position, e.enterEventCamera), e.scrollDelta.y > 0f ? 1.25f : 0.8f);
        }

        void OnDisable() { m_Id[0] = m_Id[1] = int.MinValue; m_Count = 0; }
    }
}
