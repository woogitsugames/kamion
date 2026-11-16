using System;
using System.Collections.Generic;
using Game.Core;
using Game.Core.About;
using Game.UI.Layout;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.UI;

namespace Game.UI
{
    /// <summary>
    /// "Informacje" screen: attributions and full licence texts required by the data and software in the build
    /// (OSM ODbL, GUGiK, G3 sign base, Inter OFL, glTFast Apache 2.0; docs/reports/LICENSES-AUDIT-S20.md R-P0-1).
    /// Text: Resources/About/attributions.txt parsed by <see cref="AttributionDocument"/>; no network (addresses as plain
    /// text, ODbL 4.3a). Same flat dark-panel language as <see cref="ControlSettingsPanel"/>: fixed title and footer,
    /// the body scrolls; laid out again when the safe area changes (ADR 0079). Not in the driving loop.
    /// </summary>
    public sealed class AboutPanel : MonoBehaviour
    {
        static readonly Color k_Dim = new Color(0.02f, 0.025f, 0.03f, 0.72f);
        static readonly Color k_Panel = new Color(0.06f, 0.065f, 0.07f, 0.97f);
        static readonly Color k_Button = new Color(0.16f, 0.17f, 0.18f, 0.95f);
        static readonly Color k_ButtonOn = new Color(0.30f, 0.36f, 0.30f, 0.95f);
        static readonly Color k_Text = new Color(0.95f, 0.95f, 0.91f, 1f);
        static readonly Color k_Muted = new Color(0.70f, 0.70f, 0.67f, 1f);
        static readonly Color k_Amber = new Color(0.95f, 0.66f, 0.18f, 1f);

        const float MaxW = 1500f, Pad = 40f, Edge = 20f, HeaderH = 86f, FooterH = 108f;

        public const string Title = "INFORMACJE I LICENCJE";
        public const string CloseLabel = "Zamknij";

        Action m_OnClose;
        Font m_Font;
        RectTransform m_Safe;
        UiViewport m_View;
        ScrollRect m_Scroll;
        GameObject m_Close;
        /// <summary>Pad / arrow-key scroll speed [canvas units per second]. WORKING_VALUE.</summary>
        const float PadScrollSpeed = 1400f;

        /// <summary>The panel rect (tests: must lie inside the safe area).</summary>
        public RectTransform PanelRect { get; private set; }
        public RectTransform SafeAreaRect => m_Safe;
        /// <summary>The scrolling content (one Text per heading / paragraph / licence chunk).</summary>
        public RectTransform ContentRect { get; private set; }
        /// <summary>The parsed document shown (tests).</summary>
        public AttributionDocument Document { get; private set; }
        /// <summary>Problems found while loading (missing file or include, unresolved marker); empty = OK.</summary>
        public List<string> Problems { get; private set; } = new List<string>();

        /// <summary>Builds the panel. <paramref name="cam"/> null = screen-space overlay (runtime); a camera = capture/test.</summary>
        public static AboutPanel Create(Camera cam, Action onClose)
        {
            var go = new GameObject("AboutPanel");
            var p = go.AddComponent<AboutPanel>();
            p.m_OnClose = onClose;
            p.Load();
            p.Build(cam);
            return p;
        }

        public void Close()
        {
            m_OnClose?.Invoke();
            Destroy(gameObject);
        }

        /// <summary>Tests / captures: lay out for a device screen (pixels, safe area in pixels, DPI; 0 = unknown).</summary>
        public void OverrideScreen(Vector2 pixelSize, Rect safeAreaPx, float dpi)
        {
            m_View.OverrideScreen(pixelSize, safeAreaPx, dpi);
            m_View.Refresh();
            BuildContent();
        }

        /// <summary>Text of a Resources text asset (path without extension), null when missing.</summary>
        public static string LoadText(string resourcePath)
        {
            var ta = Resources.Load<TextAsset>(resourcePath);
            return ta != null ? ta.text : null;
        }

        void Load()
        {
            string text = LoadText(AttributionDocument.ResourcePath);
            Document = AttributionDocument.Parse(text);
            Problems = text == null ? new List<string> { "missing Resources/" + AttributionDocument.ResourcePath } : Document.Problems(LoadText);
            foreach (var p in Problems) Debug.LogError("[ABOUT] " + p);
            Debug.Log($"[ABOUT] opened blocks={Document.Blocks.Count} problems={Problems.Count}");
        }

        // ------------------------------------------------------------------ build

        void Build(Camera cam)
        {
            var canvas = gameObject.AddComponent<Canvas>();
            canvas.renderMode = cam != null ? RenderMode.ScreenSpaceCamera : RenderMode.ScreenSpaceOverlay;
            canvas.worldCamera = cam;
            canvas.planeDistance = cam != null ? Mathf.Max(cam.nearClipPlane * 2f, 0.12f) : 1f;
            canvas.sortingOrder = 1210;   // above the start menu (1100) and the settings panel (1200)
            gameObject.AddComponent<GraphicRaycaster>();
            m_Font = UiFonts.Default;

            var dim = Rect("Dim", transform);
            dim.anchorMin = Vector2.zero; dim.anchorMax = Vector2.one; dim.offsetMin = dim.offsetMax = Vector2.zero;
            dim.gameObject.AddComponent<Image>().color = k_Dim;   // also swallows touches behind the panel

            m_View = new UiViewport(canvas);
            m_Safe = m_View.SafeArea;
            m_View.Refresh();
            BuildContent();

            UiFocus.EnsureEventSystem();
            UiFocus.Push(this, m_Close, m_View.Desktop);   // ADR 0265: Enter / pad A / Esc / pad B close
        }

        void Update()
        {
            if (m_View != null && m_View.Refresh()) { BuildContent(); UiFocus.Push(this, m_Close, m_View.Desktop); }   // rotation, fold / unfold, split screen
            UiFocus.RestoreIfLost(this, m_Close);
            PadScroll();
        }

        void OnDestroy() => UiFocus.Pop(this, true);

        /// <summary>ADR 0265: the licence text scrolls with the pad (right stick / d-pad up-down) and the arrow / page keys.
        /// No allocation.</summary>
        void PadScroll()
        {
            if (m_Scroll == null || m_Scroll.content == null || !UiFocus.IsTop(this)) return;
            float v = 0f;
            var g = UnityEngine.InputSystem.Gamepad.current;
            if (g != null) v += g.rightStick.ReadValue().y + (g.dpad.up.isPressed ? 1f : 0f) - (g.dpad.down.isPressed ? 1f : 0f);
            var k = UnityEngine.InputSystem.Keyboard.current;
            if (k != null)
            {
                v += (k.upArrowKey.isPressed ? 1f : 0f) - (k.downArrowKey.isPressed ? 1f : 0f);
                v += (k.pageUpKey.isPressed ? 3f : 0f) - (k.pageDownKey.isPressed ? 3f : 0f);
            }
            if (Mathf.Abs(v) < 0.2f) return;
            var content = m_Scroll.content;
            float maxY = Mathf.Max(0f, content.rect.height - m_Scroll.viewport.rect.height);
            var p = content.anchoredPosition;
            p.y = Mathf.Clamp(p.y - v * PadScrollSpeed * Time.unscaledDeltaTime, 0f, maxY);
            content.anchoredPosition = p;
            m_Scroll.velocity = Vector2.zero;
        }

        void OnRectTransformDimensionsChange() { m_View?.Invalidate(); }

        void BuildContent()
        {
            for (int i = m_Safe.childCount - 1; i >= 0; i--)
            {
                var c = m_Safe.GetChild(i);
                c.SetParent(null, false);
                if (Application.isPlaying) Destroy(c.gameObject); else DestroyImmediate(c.gameObject);
            }

            Vector2 avail = m_View.SizeUnits - new Vector2(2f * Edge, 2f * Edge);
            float panelW = Mathf.Min(MaxW, avail.x), panelH = avail.y;

            var panel = Rect("Panel", m_Safe);
            PanelRect = panel;
            panel.anchorMin = panel.anchorMax = panel.pivot = new Vector2(0.5f, 0.5f);
            panel.anchoredPosition = Vector2.zero;
            panel.sizeDelta = new Vector2(panelW, panelH);
            panel.gameObject.AddComponent<Image>().color = k_Panel;

            // ---- scrolling body between the title and the footer
            var viewport = Rect("Viewport", panel);
            viewport.anchorMin = Vector2.zero; viewport.anchorMax = Vector2.one;
            viewport.offsetMin = new Vector2(Pad, FooterH); viewport.offsetMax = new Vector2(-Pad, -HeaderH);
            viewport.gameObject.AddComponent<Image>().color = new Color(0, 0, 0, 0);   // drag target
            viewport.gameObject.AddComponent<RectMask2D>();
            var content = Rect("Content", viewport);
            ContentRect = content;
            content.anchorMin = new Vector2(0f, 1f); content.anchorMax = new Vector2(1f, 1f); content.pivot = new Vector2(0.5f, 1f);
            content.anchoredPosition = Vector2.zero; content.sizeDelta = Vector2.zero;
            var vl = content.gameObject.AddComponent<VerticalLayoutGroup>();
            vl.childControlWidth = true; vl.childControlHeight = true;
            vl.childForceExpandWidth = true; vl.childForceExpandHeight = false;
            vl.spacing = 10f; vl.padding = new RectOffset(0, 24, 8, 24);   // right: room for the scroll bar
            content.gameObject.AddComponent<ContentSizeFitter>().verticalFit = ContentSizeFitter.FitMode.PreferredSize;

            int n = 0;
            foreach (var b in Document.Blocks)
            {
                switch (b.Kind)
                {
                    case AttributionBlockKind.Section: Block(content, "Section", b.Text.ToUpperInvariant(), 26, k_Amber, 18f); break;
                    case AttributionBlockKind.Entry: Block(content, "Entry", b.Text, 28, k_Text, 6f); break;
                    case AttributionBlockKind.Paragraph: Block(content, "Paragraph", b.Text, 24, k_Text, 0f); break;
                    case AttributionBlockKind.Include:
                        string t = LoadText(b.Text) ?? ("[brak pliku: " + b.Text + "]");
                        foreach (var chunk in AttributionDocument.Chunk(t, AttributionDocument.UiChunkChars))
                            Block(content, "License", chunk, 20, k_Muted, 0f);
                        break;
                }
                n++;
            }
            if (n == 0) Block(content, "Paragraph", "Brak tekstu informacji (plik About/attributions).", 24, k_Text, 0f);

            var scroll = viewport.gameObject.AddComponent<ScrollRect>();
            scroll.viewport = viewport; scroll.content = content;
            scroll.horizontal = false; scroll.vertical = true;
            scroll.movementType = ScrollRect.MovementType.Clamped;
            scroll.scrollSensitivity = 40f;
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

            // ---- fixed title
            var title = Label(panel, "Title", Title, 38, TextAnchor.MiddleLeft, k_Text);
            var tr = title.rectTransform;
            tr.anchorMin = new Vector2(0f, 1f); tr.anchorMax = new Vector2(1f, 1f); tr.pivot = new Vector2(0.5f, 1f);
            tr.offsetMin = new Vector2(Pad, -14f - 60f); tr.offsetMax = new Vector2(-Pad, -14f);
            title.horizontalOverflow = HorizontalWrapMode.Wrap;
            title.resizeTextForBestFit = true; title.resizeTextMinSize = 24; title.resizeTextMaxSize = 38;   // never cut on a narrow panel

            // ---- fixed footer: version on the left, close on the right
            float closeW = Mathf.Min(320f, (panelW - 2f * Pad) * 0.42f);
            var ver = Label(panel, "Version", "Wersja: " + BuildInfo.Current.IdentityLabel, 22, TextAnchor.MiddleLeft, k_Muted);
            var vr = ver.rectTransform;
            vr.anchorMin = vr.anchorMax = vr.pivot = Vector2.zero;
            vr.anchoredPosition = new Vector2(Pad, 20f); vr.sizeDelta = new Vector2(panelW - 3f * Pad - closeW, 72f);
            ver.horizontalOverflow = HorizontalWrapMode.Wrap;
            var close = TextButton(panel, CloseLabel, new Vector2(panelW - Pad - closeW, 20f), new Vector2(closeW, 72f), Close);
            close.GetComponent<Image>().color = k_ButtonOn;
            m_Close = close;
            m_Scroll = scroll;

            Canvas.ForceUpdateCanvases();
            LayoutRebuilder.ForceRebuildLayoutImmediate(content);
            scroll.verticalNormalizedPosition = 1f;   // start at the top
        }

        void Block(RectTransform parent, string name, string text, int size, Color color, float spaceAbove)
        {
            if (spaceAbove > 0f)
            {
                var gap = Rect("Gap", parent);
                gap.gameObject.AddComponent<LayoutElement>().minHeight = spaceAbove;
            }
            var t = Label(parent, name, text, size, TextAnchor.UpperLeft, color);
            t.horizontalOverflow = HorizontalWrapMode.Wrap;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            t.lineSpacing = 1.1f;
        }

        // ------------------------------------------------------------------ helpers

        static RectTransform Rect(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.layer = 5;
            var rt = (RectTransform)go.transform;
            rt.SetParent(parent, false);
            return rt;
        }

        Text Label(Transform parent, string name, string text, int size, TextAnchor align, Color color)
        {
            var rt = Rect(name, parent);
            var t = rt.gameObject.AddComponent<Text>();
            t.font = m_Font; t.fontSize = size; t.color = color; t.alignment = align; t.text = text;
            t.horizontalOverflow = HorizontalWrapMode.Overflow; t.verticalOverflow = VerticalWrapMode.Overflow;
            t.raycastTarget = false;
            return t;
        }

        GameObject TextButton(Transform parent, string text, Vector2 bottomLeft, Vector2 size, UnityEngine.Events.UnityAction onClick)
        {
            var rt = Rect(text, parent);
            rt.anchorMin = rt.anchorMax = rt.pivot = Vector2.zero;
            rt.anchoredPosition = bottomLeft; rt.sizeDelta = size;
            var img = rt.gameObject.AddComponent<Image>();
            img.color = k_Button;
            var b = rt.gameObject.AddComponent<Button>();
            b.targetGraphic = img;
            b.onClick.AddListener(onClick);
            UiFocus.Decorate(b, Close);   // ADR 0265: focus frame; Esc / pad B closes
            var l = Label(rt, "Label", text, 30, TextAnchor.MiddleCenter, k_Text);
            var lr = l.rectTransform;
            lr.anchorMin = Vector2.zero; lr.anchorMax = Vector2.one; lr.offsetMin = lr.offsetMax = Vector2.zero;
            return rt.gameObject;
        }
    }
}
