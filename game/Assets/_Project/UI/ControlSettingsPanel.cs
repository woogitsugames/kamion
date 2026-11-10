using System;
using System.Collections.Generic;
using System.Globalization;
using Game.Controls;
using Game.UI.Layout;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.UI;

namespace Game.UI
{
    /// <summary>
    /// Control settings screen (Polish), same flat dark-panel language as the driving HUD: steppers and two-way
    /// segments, no icons. Edits a <see cref="ControlSettings"/> in place; every change is clamped, saved and logged
    /// by <see cref="Commit"/> and reported through <c>onChanged</c> so the running game can apply it at once.
    /// Adaptive (ADR 0079): the panel always fits the safe area - two columns when the width allows, otherwise one;
    /// the rows scroll between a fixed title and a fixed footer when they are taller than the screen; it is laid
    /// out again when the screen changes (rotation, folding a foldable).
    /// </summary>
    public sealed class ControlSettingsPanel : MonoBehaviour
    {
        static readonly Color k_Dim = new Color(0.02f, 0.025f, 0.03f, 0.72f);
        static readonly Color k_Panel = new Color(0.06f, 0.065f, 0.07f, 0.97f);
        static readonly Color k_Row = new Color(1f, 1f, 1f, 0.045f);
        static readonly Color k_Button = new Color(0.16f, 0.17f, 0.18f, 0.95f);
        static readonly Color k_ButtonOn = new Color(0.30f, 0.36f, 0.30f, 0.95f);
        static readonly Color k_Text = new Color(0.95f, 0.95f, 0.91f, 1f);
        static readonly Color k_Muted = new Color(0.70f, 0.70f, 0.67f, 1f);
        static readonly Color k_Amber = new Color(0.95f, 0.66f, 0.18f, 1f);

        const float RowH = 66f, ColW = 700f, Pad = 40f, Edge = 20f, HeaderH = 86f, FooterH = 108f;

        public ControlSettings Settings { get; private set; }
        Action m_OnChanged, m_OnClose, m_OnCalibrate;
        Font m_Font;
        RectTransform m_Safe;
        UiViewport m_View;
        readonly List<Action> m_Refresh = new List<Action>();

        /// <summary>The panel rect (tests: must lie inside the safe area).</summary>
        public RectTransform PanelRect { get; private set; }
        public RectTransform SafeAreaRect => m_Safe;
        /// <summary>True when the rows are laid out in two columns.</summary>
        public bool TwoColumns { get; private set; }
        /// <summary>True when the rows are taller than the panel and scroll.</summary>
        public bool Scrolls { get; private set; }

        /// <summary>Builds the panel. <paramref name="cam"/> null = screen-space overlay (runtime); a camera = capture/test.</summary>
        public static ControlSettingsPanel Create(Camera cam, ControlSettings settings, Action onChanged, Action onClose, Action onCalibrate = null)
        {
            var go = new GameObject("ControlSettingsPanel");
            var p = go.AddComponent<ControlSettingsPanel>();
            p.Settings = settings;
            p.m_OnChanged = onChanged; p.m_OnClose = onClose; p.m_OnCalibrate = onCalibrate;
            p.Build(cam);
            return p;
        }

        public void Close()
        {
            m_OnClose?.Invoke();
            Destroy(gameObject);
        }

        /// <summary>Clamp, save, log and notify (called after every edit).</summary>
        public void Commit(string reason = "changed")
        {
            Settings.Clamp();
            Settings.Save();
            Settings.Log(reason);
            m_OnChanged?.Invoke();
            foreach (var r in m_Refresh) r();
        }

        public void ResetToDefaults()
        {
            Settings.ResetToDefaults();
            Commit("reset");
        }

        /// <summary>Tests / captures: lay out for a device screen (pixels, safe area in pixels, DPI; 0 = unknown).</summary>
        public void OverrideScreen(Vector2 pixelSize, Rect safeAreaPx, float dpi)
        {
            m_View.OverrideScreen(pixelSize, safeAreaPx, dpi);
            m_View.Refresh();
            BuildContent();
        }

        // ------------------------------------------------------------------ build

        void Build(Camera cam)
        {
            var canvas = gameObject.AddComponent<Canvas>();
            canvas.renderMode = cam != null ? RenderMode.ScreenSpaceCamera : RenderMode.ScreenSpaceOverlay;
            canvas.worldCamera = cam;
            canvas.planeDistance = cam != null ? Mathf.Max(cam.nearClipPlane * 2f, 0.12f) : 1f;
            canvas.sortingOrder = 1200;
            gameObject.AddComponent<GraphicRaycaster>();
            m_Font = UiFonts.Default;

            var dim = Rect("Dim", transform);
            Stretch(dim);
            dim.gameObject.AddComponent<Image>().color = k_Dim;   // also swallows touches behind the panel

            m_View = new UiViewport(canvas);
            m_Safe = m_View.SafeArea;
            m_View.Refresh();
            BuildContent();

            if (UnityEngine.Object.FindAnyObjectByType<EventSystem>() == null)
                new GameObject("EventSystem", typeof(EventSystem)).AddComponent<InputSystemUIInputModule>().AssignDefaultActions();
        }

        void Update()
        {
            if (m_View != null && m_View.Refresh()) BuildContent();   // rotation, fold / unfold, split screen
        }

        void OnRectTransformDimensionsChange() { m_View?.Invalidate(); }

        /// <summary>(Re)builds the panel for the current safe-area size. Not in the driving loop: allocation is fine here.</summary>
        void BuildContent()
        {
            for (int i = m_Safe.childCount - 1; i >= 0; i--)
            {
                var c = m_Safe.GetChild(i);
                c.SetParent(null, false);
                if (Application.isPlaying) Destroy(c.gameObject); else DestroyImmediate(c.gameObject);
            }
            m_Refresh.Clear();

            Vector2 avail = m_View.SizeUnits - new Vector2(2f * Edge, 2f * Edge);
            float twoW = 2f * ColW + 3f * Pad;
            TwoColumns = avail.x >= twoW;
            float panelW = TwoColumns ? twoW : Mathf.Min(ColW + 2f * Pad, avail.x);

            var panel = Rect("Panel", m_Safe);
            PanelRect = panel;
            panel.anchorMin = panel.anchorMax = panel.pivot = new Vector2(0.5f, 0.5f);
            panel.anchoredPosition = Vector2.zero;
            panel.gameObject.AddComponent<Image>().color = k_Panel;

            // ---- scrolling body between the title and the footer
            var viewport = Rect("Viewport", panel);
            viewport.anchorMin = Vector2.zero; viewport.anchorMax = Vector2.one;
            viewport.offsetMin = new Vector2(0f, FooterH); viewport.offsetMax = new Vector2(0f, -HeaderH);
            viewport.gameObject.AddComponent<Image>().color = new Color(0, 0, 0, 0);   // drag target
            viewport.gameObject.AddComponent<RectMask2D>();
            var content = Rect("Content", viewport);
            content.anchorMin = new Vector2(0f, 1f); content.anchorMax = new Vector2(1f, 1f); content.pivot = new Vector2(0.5f, 1f);

            float left = Pad, right = TwoColumns ? Pad + ColW + Pad : Pad;

            // Left column: wheel + pedals
            float y = 0f;
            Header(content, "KIEROWNICA DOTYKOWA", left, ref y);
            Stepper(content, left, ref y, "Zakres kierownicy", () => F0(Settings.wheelRangeDeg) + "°", d => Settings.wheelRangeDeg = Step(Settings.wheelRangeDeg, d, 90f, ControlSettings.RangeMin, ControlSettings.RangeMax));
            Stepper(content, left, ref y, "Czułość", () => Pct(Settings.wheelSensitivity), d => Settings.wheelSensitivity = Step(Settings.wheelSensitivity, d, 0.1f, ControlSettings.GainMin, ControlSettings.GainMax));
            Stepper(content, left, ref y, "Samocentrowanie", () => Settings.centreStrength <= 0.001f ? "wyłączone" : Pct(Settings.centreStrength), d => Settings.centreStrength = Step(Settings.centreStrength, d, 0.1f, ControlSettings.CentreMin, ControlSettings.CentreMax));
            Stepper(content, left, ref y, "Martwa strefa", () => Pct(Settings.wheelDeadZone), d => Settings.wheelDeadZone = Step(Settings.wheelDeadZone, d, 0.01f, ControlSettings.DeadMin, ControlSettings.DeadMax));
            Segment(content, left, ref y, "Przełożenie", "stałe", "od prędkości", () => Settings.speedSensitiveSteering, v => Settings.speedSensitiveSteering = v);
            y += 18f;
            Header(content, "PEDAŁY", left, ref y);
            Segment(content, left, ref y, "Krzywa gazu", "liniowa", "progresywna", () => Settings.throttleProgressive, v => Settings.throttleProgressive = v);
            Segment(content, left, ref y, "Krzywa hamulca", "liniowa", "progresywna", () => Settings.brakeProgressive, v => Settings.brakeProgressive = v);
            float leftEnd = y;

            // Right column (or continued below in one column): gyro + camera
            y = TwoColumns ? 0f : leftEnd + 18f;
            Header(content, "GYRO (PRZECHYŁ TELEFONU)", right, ref y);
            Segment(content, right, ref y, "Sterowanie", "kierownica", "gyro", () => Settings.gyroEnabled, v => Settings.gyroEnabled = v);
            Segment(content, right, ref y, "Kierunek", "normalny", "odwrócony", () => Settings.gyroInvert, v => Settings.gyroInvert = v);
            Stepper(content, right, ref y, "Czułość gyro", () => Pct(Settings.gyroSensitivity), d => Settings.gyroSensitivity = Step(Settings.gyroSensitivity, d, 0.1f, ControlSettings.GainMin, ControlSettings.GainMax));
            Stepper(content, right, ref y, "Pełny skręt przy przechyle", () => F0(Settings.GyroMaxTiltDeg) + "°", null);
            var calib = TextButton(content, "Kalibruj", Vector2.zero, new Vector2(ColW, 64f), () => m_OnCalibrate?.Invoke());
            PlaceTop((RectTransform)calib.transform, right, y, new Vector2(ColW, 64f));
            y += 64f + 8f;
            var hint = Label(content, "CalibHint", "Trzymaj telefon tak, jak chcesz jechać prosto, i dotknij Kalibruj.", 22, TextAnchor.UpperLeft, k_Muted, Vector2.zero, new Vector2(ColW, 62f));
            PlaceTop(hint.rectTransform, right, y, new Vector2(ColW, 62f));
            hint.horizontalOverflow = HorizontalWrapMode.Wrap;
            y += 62f + 18f;
            Header(content, "KAMERA (WIDOK Z KABINY)", right, ref y);
            Stepper(content, right, ref y, "Czułość rozglądania", () => Pct(Settings.lookSensitivity), d => Settings.lookSensitivity = Step(Settings.lookSensitivity, d, 0.1f, ControlSettings.LookMin, ControlSettings.LookMax));
            Stepper(content, right, ref y, "Pole widzenia", () => F0(Settings.cabFov) + "°", d => Settings.cabFov = Step(Settings.cabFov, d, 5f, ControlSettings.FovMin, ControlSettings.FovMax));
            Segment(content, right, ref y, "Ruch głowy", "włączony", "wyłączony", () => !Settings.headMotion, v => Settings.headMotion = !v);

            float contentH = Mathf.Max(leftEnd, y) + 8f;
            float panelH = Mathf.Min(avail.y, HeaderH + contentH + FooterH);
            panel.sizeDelta = new Vector2(panelW, panelH);
            content.sizeDelta = new Vector2(0f, contentH);
            content.anchoredPosition = Vector2.zero;
            float viewH = panelH - HeaderH - FooterH;
            Scrolls = contentH > viewH + 0.5f;
            var scroll = viewport.gameObject.AddComponent<ScrollRect>();
            scroll.viewport = viewport; scroll.content = content;
            scroll.horizontal = false; scroll.vertical = Scrolls;
            scroll.movementType = ScrollRect.MovementType.Clamped;
            scroll.scrollSensitivity = 40f;
            if (Scrolls)
            {
                // Slim position bar at the right edge (shows there is more below; also draggable).
                var track = Rect("Scrollbar", panel);
                track.anchorMin = new Vector2(1f, 0f); track.anchorMax = new Vector2(1f, 1f); track.pivot = new Vector2(1f, 0.5f);
                track.offsetMin = new Vector2(-18f, FooterH); track.offsetMax = new Vector2(-8f, -HeaderH);
                track.gameObject.AddComponent<Image>().color = new Color(1f, 1f, 1f, 0.06f);
                var handle = Rect("Handle", track);
                handle.offsetMin = handle.offsetMax = Vector2.zero;
                var hi = handle.gameObject.AddComponent<Image>(); hi.color = k_Muted;
                var sb = track.gameObject.AddComponent<Scrollbar>();
                sb.handleRect = handle; sb.targetGraphic = hi; sb.direction = Scrollbar.Direction.BottomToTop;
                scroll.verticalScrollbar = sb;
                scroll.verticalScrollbarVisibility = ScrollRect.ScrollbarVisibility.Permanent;
            }

            // ---- fixed title
            float inner = panelW - 2f * Pad;
            var title = Label(panel, "Title", "USTAWIENIA: STEROWANIE I KAMERA", 38, TextAnchor.MiddleLeft, k_Text, Vector2.zero, Vector2.zero);
            TopBand(title.rectTransform, Pad, TwoColumns ? Pad + 420f : Pad, 14f, 60f);
            title.horizontalOverflow = HorizontalWrapMode.Wrap; title.resizeTextForBestFit = true; title.resizeTextMinSize = 24; title.resizeTextMaxSize = 38;   // never cut on a narrow panel
            if (TwoColumns)
            {
                var h = Label(panel, "Hint", "Zmiany działają od razu i zapisują się same.", 24, TextAnchor.MiddleRight, k_Muted, Vector2.zero, Vector2.zero);
                TopBand(h.rectTransform, panelW - Pad - 520f, Pad, 14f, 60f);
            }

            // ---- fixed footer
            float closeW = Mathf.Min(320f, inner * 0.42f), resetW = Mathf.Min(420f, inner - closeW - 20f);
            TextButton(panel, "Przywróć domyślne", new Vector2(Pad, 20f), new Vector2(resetW, 72f), ResetToDefaults);
            var close = TextButton(panel, "Zamknij", new Vector2(panelW - Pad - closeW, 20f), new Vector2(closeW, 72f), Close);
            close.GetComponent<Image>().color = k_ButtonOn;

            foreach (var r in m_Refresh) r();
        }

        void Header(RectTransform parent, string text, float x, ref float y)
        {
            var l = Label(parent, "Header", text, 24, TextAnchor.LowerLeft, k_Amber, Vector2.zero, new Vector2(ColW, 40f));
            PlaceTop(l.rectTransform, x, y, new Vector2(ColW, 40f));
            y += 52f;
        }

        RectTransform Row(RectTransform parent, string label, float x, ref float y, float labelW)
        {
            var row = Rect("Row " + label, parent);
            PlaceTop(row, x, y, new Vector2(ColW, RowH - 8f));
            row.gameObject.AddComponent<Image>().color = k_Row;
            Label(row, "Label", label, 30, TextAnchor.MiddleLeft, k_Text, new Vector2(20f, 0f), new Vector2(labelW, RowH - 8f));
            y += RowH;
            return row;
        }

        void Stepper(RectTransform parent, float x, ref float y, string label, Func<string> value, Action<int> step)
        {
            var row = Row(parent, label, x, ref y, 330f);
            var v = Label(row, "Value", "", 30, TextAnchor.MiddleCenter, k_Text, new Vector2(470f, 0f), new Vector2(110f, RowH - 8f));
            if (step != null)
            {
                TextButton(row, "−", new Vector2(ColW - 330f + 20f, 6f), new Vector2(80f, RowH - 20f), () => { step(-1); Commit(); });
                TextButton(row, "+", new Vector2(ColW - 92f, 6f), new Vector2(80f, RowH - 20f), () => { step(+1); Commit(); });
            }
            else { v.color = k_Muted; Place(v.rectTransform, Vector2.zero, new Vector2(ColW - 330f, 0f), new Vector2(310f, RowH - 8f)); v.alignment = TextAnchor.MiddleRight; }
            m_Refresh.Add(() => v.text = value());
        }

        void Segment(RectTransform parent, float x, ref float y, string label, string a, string b, Func<bool> isB, Action<bool> set)
        {
            var row = Row(parent, label, x, ref y, 250f);
            float w = 200f;
            var ba = TextButton(row, a, new Vector2(ColW - 2 * w - 18f, 6f), new Vector2(w, RowH - 20f), () => { set(false); Commit(); });
            var bb = TextButton(row, b, new Vector2(ColW - w - 12f, 6f), new Vector2(w, RowH - 20f), () => { set(true); Commit(); });
            var ia = ba.GetComponent<Image>(); var ib = bb.GetComponent<Image>();
            m_Refresh.Add(() => { bool on = isB(); ia.color = on ? k_Button : k_ButtonOn; ib.color = on ? k_ButtonOn : k_Button; });
        }

        // ------------------------------------------------------------------ helpers

        /// <summary>One step of a value on a grid anchored at 0 (no float drift), clamped.</summary>
        public static float Step(float v, int dir, float step, float lo, float hi)
        {
            float n = Mathf.Round(v / step) + dir;
            return Mathf.Clamp(Mathf.Round(n * step * 1000f) / 1000f, lo, hi);
        }

        static string F0(float v) => v.ToString("F0", CultureInfo.InvariantCulture);
        static string Pct(float v) => Mathf.RoundToInt(v * 100f).ToString(CultureInfo.InvariantCulture) + "%";

        static RectTransform Rect(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.layer = 5;
            var rt = (RectTransform)go.transform;
            rt.SetParent(parent, false);
            return rt;
        }

        static void Stretch(RectTransform rt) { rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = rt.offsetMax = Vector2.zero; }

        static void Place(RectTransform rt, Vector2 anchor, Vector2 bottomLeft, Vector2 size)
        {
            rt.anchorMin = rt.anchorMax = anchor; rt.pivot = Vector2.zero; rt.anchoredPosition = bottomLeft; rt.sizeDelta = size;
        }

        /// <summary>Places a rect by its top-left corner, y measured down from the parent's top (scroll content).</summary>
        static void PlaceTop(RectTransform rt, float x, float yFromTop, Vector2 size)
        {
            rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(0f, 1f);
            rt.anchoredPosition = new Vector2(x, -yFromTop);
            rt.sizeDelta = size;
        }

        /// <summary>Stretches a rect across the parent's top edge with left / right insets.</summary>
        static void TopBand(RectTransform rt, float leftInset, float rightInset, float topInset, float height)
        {
            rt.anchorMin = new Vector2(0f, 1f); rt.anchorMax = new Vector2(1f, 1f); rt.pivot = new Vector2(0.5f, 1f);
            rt.offsetMin = new Vector2(leftInset, -topInset - height); rt.offsetMax = new Vector2(-rightInset, -topInset);
        }

        Text Label(Transform parent, string name, string text, int size, TextAnchor align, Color color, Vector2 bottomLeft, Vector2 box)
        {
            var rt = Rect(name, parent);
            Place(rt, Vector2.zero, bottomLeft, box);
            var t = rt.gameObject.AddComponent<Text>();
            t.font = m_Font; t.fontSize = size; t.color = color; t.alignment = align; t.text = text;
            t.horizontalOverflow = HorizontalWrapMode.Overflow; t.verticalOverflow = VerticalWrapMode.Overflow;
            t.raycastTarget = false;
            return t;
        }

        GameObject TextButton(Transform parent, string text, Vector2 bottomLeft, Vector2 size, UnityEngine.Events.UnityAction onClick)
        {
            var rt = Rect(text, parent);
            Place(rt, Vector2.zero, bottomLeft, size);
            var img = rt.gameObject.AddComponent<Image>();
            img.color = k_Button;
            var b = rt.gameObject.AddComponent<Button>();
            b.targetGraphic = img;
            b.onClick.AddListener(onClick);
            Label(rt, "Label", text, 30, TextAnchor.MiddleCenter, k_Text, Vector2.zero, size);
            return rt.gameObject;
        }
    }
}
