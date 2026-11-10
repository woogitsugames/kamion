using System;
using System.Collections.Generic;
using Game.Core;
using Game.Rendering;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.UI;

namespace Game.UI
{
    /// <summary>
    /// Start menu (Polish), same flat dark language as the settings panel. Left column: one large button per start
    /// (DrivingLab, routes); right column: time of day, graphics tier, frame-rate cap and the control settings.
    /// Choosing a start logs one <c>[CONTROLS] menu-start ...</c> line with the whole choice.
    /// </summary>
    public sealed class BootMenu : MonoBehaviour
    {
        static readonly Color k_Panel = new Color(0.06f, 0.065f, 0.07f, 0.97f);
        static readonly Color k_Button = new Color(0.16f, 0.17f, 0.18f, 0.95f);
        static readonly Color k_ButtonOn = new Color(0.30f, 0.36f, 0.30f, 0.95f);
        static readonly Color k_Text = new Color(0.95f, 0.95f, 0.91f, 1f);
        static readonly Color k_Muted = new Color(0.70f, 0.70f, 0.67f, 1f);
        static readonly Color k_Amber = new Color(0.95f, 0.66f, 0.18f, 1f);

        const float ColW = 760f, BtnH = 104f, Gap = 16f;

        public StartMenuOptions Options { get; private set; }
        readonly List<Action> m_Refresh = new List<Action>();
        Font m_Font;
        RectTransform m_Safe;

        /// <summary>Builds the menu. <paramref name="cam"/> null = screen-space overlay; a camera = capture/test.</summary>
        public static BootMenu Create(Camera cam, StartMenuOptions options, IReadOnlyList<(string label, Action action)> starts, Action openSettings)
        {
            var go = new GameObject("BootMenu");
            var menu = go.AddComponent<BootMenu>();
            menu.Options = options;
            menu.Build(cam, starts, openSettings);
            return menu;
        }

        void Build(Camera cam, IReadOnlyList<(string label, Action action)> starts, Action openSettings)
        {
            var canvas = gameObject.AddComponent<Canvas>();
            canvas.renderMode = cam != null ? RenderMode.ScreenSpaceCamera : RenderMode.ScreenSpaceOverlay;
            canvas.worldCamera = cam;
            canvas.planeDistance = cam != null ? Mathf.Max(cam.nearClipPlane * 2f, 0.5f) : 1f;
            canvas.sortingOrder = 1100;
            var scaler = gameObject.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            scaler.matchWidthOrHeight = 1f;
            gameObject.AddComponent<GraphicRaycaster>();
            m_Font = UiFonts.Default;

            m_Safe = Rect("SafeArea", transform);
            m_Safe.anchorMin = Vector2.zero; m_Safe.anchorMax = Vector2.one; m_Safe.offsetMin = m_Safe.offsetMax = Vector2.zero;
            ApplySafeArea();

            // Centred block: left column starts, gap 80, right column options.
            float total = 2 * ColW + 80f, left = -total * 0.5f, right = left + ColW + 80f;
            float top = 400f;   // block top (centre-anchored, y up)

            Label(m_Safe, "Title", "TRUCK SIM PL — TEST WRAŻEŃ", 28, TextAnchor.LowerLeft, k_Amber, new Vector2(left, top + 52f), new Vector2(total, 44f));

            // ---- left: starts
            Label(m_Safe, "HeaderStart", "WYBIERZ START", 24, TextAnchor.LowerLeft, k_Muted, new Vector2(left, top - 8f), new Vector2(ColW, 36f));
            float y = top - 52f;
            for (int i = 0; i < starts.Count; i++)
            {
                var s = starts[i];
                string label = s.label;
                var action = s.action;
                var b = Button(m_Safe, label, new Vector2(left, y - BtnH), new Vector2(ColW, BtnH), 31, TextAnchor.MiddleLeft, () =>
                {
                    Debug.Log(Options.StartLine(label));
                    action();
                });
                b.GetComponentInChildren<Text>().rectTransform.offsetMin = new Vector2(32f, 0f);
                y -= BtnH + Gap;
            }

            // ---- right: options
            Label(m_Safe, "HeaderOptions", "OPCJE", 24, TextAnchor.LowerLeft, k_Muted, new Vector2(right, top - 8f), new Vector2(ColW, 36f));
            float oy = top - 52f;
            Segments("Pora dnia (trasy)", StartMenuOptions.LightingLabels, right, ref oy,
                () => Options.Lighting, i => Options.SetLighting(i));
            Segments("Jakość grafiki", QualityTiers.Names, right, ref oy,
                () => Array.IndexOf(QualityTiers.Names, Options.Tier), i => Options.SetTier(QualityTiers.Names[i]));
            string[] fpsNames = new string[QualityTiers.SupportedFrameRates.Length];
            for (int i = 0; i < fpsNames.Length; i++) fpsNames[i] = QualityTiers.SupportedFrameRates[i] + " FPS";
            Segments("Limit klatek", fpsNames, right, ref oy,
                () => Array.IndexOf(QualityTiers.SupportedFrameRates, Options.Fps),
                i => Options.SetFps(QualityTiers.SupportedFrameRates[i]));
            oy -= 8f;
            Button(m_Safe, "Ustawienia sterowania", new Vector2(right, oy - 80f), new Vector2(ColW, 80f), 32, TextAnchor.MiddleCenter, () => openSettings?.Invoke());
            Label(m_Safe, "Footer", "DrivingLab ma stałe światło. W jeździe: przycisk Menu wraca tutaj bez restartu aplikacji.\nWersja: " + BuildInfo.Current.ShortLabel,
                22, TextAnchor.UpperLeft, k_Muted, new Vector2(right, oy - 80f - 12f - 70f), new Vector2(ColW, 70f)).horizontalOverflow = HorizontalWrapMode.Wrap;

            if (FindAnyObjectByType<EventSystem>() == null)
                new GameObject("EventSystem", typeof(EventSystem)).AddComponent<InputSystemUIInputModule>().AssignDefaultActions();
            foreach (var r in m_Refresh) r();
        }

        /// <summary>Re-reads tier / fps / lighting (the options can also change from outside, e.g. a launch argument).</summary>
        public void RefreshNow() { foreach (var r in m_Refresh) r(); }

        void Segments(string title, string[] names, float x, ref float y, Func<int> current, Action<int> set)
        {
            Label(m_Safe, "Label " + title, title, 26, TextAnchor.LowerLeft, k_Text, new Vector2(x, y - 34f), new Vector2(ColW, 34f));
            y -= 40f;
            float gap = 8f, w = (ColW - gap * (names.Length - 1)) / names.Length, h = 66f;
            var images = new Image[names.Length];
            for (int i = 0; i < names.Length; i++)
            {
                int idx = i;
                var b = Button(m_Safe, names[i], new Vector2(x + i * (w + gap), y - h), new Vector2(w, h), 28, TextAnchor.MiddleCenter, () => { set(idx); RefreshNow(); });
                images[i] = b.GetComponent<Image>();
            }
            m_Refresh.Add(() => { int c = current(); for (int i = 0; i < images.Length; i++) images[i].color = i == c ? k_ButtonOn : k_Button; });
            y -= h + 22f;
        }

        void ApplySafeArea()
        {
            Rect sa = Screen.safeArea;
            if (Screen.width <= 0 || Screen.height <= 0) return;
            m_Safe.anchorMin = new Vector2(sa.xMin / Screen.width, sa.yMin / Screen.height);
            m_Safe.anchorMax = new Vector2(sa.xMax / Screen.width, sa.yMax / Screen.height);
        }

        static RectTransform Rect(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.layer = 5;
            var rt = (RectTransform)go.transform;
            rt.SetParent(parent, false);
            return rt;
        }

        // Centre-anchored, bottom-left pivot: positions are offsets from the screen centre of the safe area.
        static void Place(RectTransform rt, Vector2 bottomLeft, Vector2 size)
        {
            rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0.5f); rt.pivot = Vector2.zero; rt.anchoredPosition = bottomLeft; rt.sizeDelta = size;
        }

        Text Label(Transform parent, string name, string text, int size, TextAnchor align, Color color, Vector2 bottomLeft, Vector2 box)
        {
            var rt = Rect(name, parent);
            Place(rt, bottomLeft, box);
            var t = rt.gameObject.AddComponent<Text>();
            t.font = m_Font; t.fontSize = size; t.color = color; t.alignment = align; t.text = text;
            t.horizontalOverflow = HorizontalWrapMode.Overflow; t.verticalOverflow = VerticalWrapMode.Overflow;
            t.raycastTarget = false;
            return t;
        }

        GameObject Button(Transform parent, string text, Vector2 bottomLeft, Vector2 size, int fontSize, TextAnchor align, UnityEngine.Events.UnityAction onClick)
        {
            var rt = Rect(text, parent);
            Place(rt, bottomLeft, size);
            var img = rt.gameObject.AddComponent<Image>();
            img.color = k_Button;
            var b = rt.gameObject.AddComponent<Button>();
            b.targetGraphic = img;
            b.onClick.AddListener(onClick);
            var t = Label(rt, "Label", text, fontSize, align, k_Text, Vector2.zero, size);
            t.rectTransform.anchorMin = Vector2.zero; t.rectTransform.anchorMax = Vector2.one;
            t.rectTransform.offsetMin = t.rectTransform.offsetMax = Vector2.zero;
            return rt.gameObject;
        }
    }
}
