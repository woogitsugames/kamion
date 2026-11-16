using System;
using System.Collections.Generic;
using Game.Core;
using Game.Rendering;
using Game.UI.Layout;
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
    /// Scale and safe area: <see cref="UiViewport"/> (ADR 0079) - the 1600-unit block always fits, also on a
    /// near-square foldable screen, and follows rotation / folding.
    /// ADR 0265 (monitor): scale by the window height, 16:9 content on ultrawide (<see cref="UiViewport"/>); mouse and
    /// pad / keyboard navigation with an explicit order (left column top-down, right column top-down, left / right
    /// between the columns), the first start selected and a visible focus frame (<see cref="UiFocus"/>). Only the
    /// look and the navigation changed - the start actions are the same delegates as before.
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
        // ADR 0276: every menu item lives in this block (stretched over the safe area); the block moves vertically so the
        // diagnostics overlay never covers the title or a button (MenuOverlayLayout, shared with DiagnosticsOverlay).
        RectTransform m_Block;
        Rect m_BlockBounds;
        float m_AppliedShift = float.NaN;
        UiViewport m_View;
        // ADR 0265: navigation rows per column (left = starts + region picker, right = options).
        readonly List<List<Selectable[]>> m_Nav = new List<List<Selectable[]>> { new List<Selectable[]>(), new List<Selectable[]>() };
        GameObject m_FirstItem;

        /// <summary>The item selected first (pad / keyboard); tests.</summary>
        public GameObject FirstItem => m_FirstItem;
        /// <summary>Monitor form factor in the last layout (ADR 0265).</summary>
        public bool Desktop => m_View != null && m_View.Desktop;

        /// <summary>The safe-area rect all menu items live in (tests).</summary>
        public RectTransform SafeAreaRect => m_Safe;

        /// <summary>Tests / captures: lay out for a device screen (pixels, safe area in pixels, DPI; 0 = unknown).</summary>
        public void OverrideScreen(Vector2 pixelSize, Rect safeAreaPx, float dpi) { m_View.OverrideScreen(pixelSize, safeAreaPx, dpi); m_View.Refresh(); }

        /// <summary>Tests / captures: lay out for a screen of the given form factor (ADR 0265: monitors 16:9 .. 32:9).</summary>
        public void OverrideScreen(Vector2 pixelSize, Rect safeAreaPx, float dpi, bool desktop) { m_View.OverrideScreen(pixelSize, safeAreaPx, dpi, desktop); m_View.Refresh(); }

        /// <summary>Vertical shift of the menu block applied to make room for the diagnostics overlay (ADR 0276; tests).</summary>
        public float BlockShift => float.IsNaN(m_AppliedShift) ? 0f : m_AppliedShift;
        /// <summary>Bounding box of the menu items before the shift (centre origin, y up, canvas units; tests).</summary>
        public Rect BlockBounds => m_BlockBounds;

        void OnEnable() { if (m_Block != null) PublishBlock(); }

        void OnDisable() => MenuOverlayBoard.MenuActive = false;

        void PublishBlock()
        {
            MenuOverlayBoard.MenuActive = true;
            MenuOverlayBoard.MenuBlock = m_BlockBounds;
        }

        /// <summary>ADR 0276: shift the block as the shared layout says (allocation-free, every frame).</summary>
        void ApplyOverlayLayout()
        {
            if (m_Block == null || m_View == null) return;
            MenuOverlayBoard.Solve(m_View.SizeUnits, out var r);
            if (r.MenuShiftY == m_AppliedShift) return;
            m_AppliedShift = r.MenuShiftY;
            m_Block.anchoredPosition = new Vector2(0f, r.MenuShiftY);
        }

        void Update()
        {
            m_View?.Refresh();   // rotation, fold / unfold: scale + safe area follow, the block stays centred
            ApplyOverlayLayout();
            UiFocus.RestoreIfLost(this, m_FirstItem);   // ADR 0265: the pad never gets stuck without a selection
        }

        void OnRectTransformDimensionsChange() { m_View?.Invalidate(); }

        /// <summary>Opens the PC settings screen (ADR 0270); null = button hidden (phones).</summary>
        Action m_OpenPcSettings;
        public const string PcSettingsName = "PcSettings";

        /// <summary>Label of the button that opens the attributions / licences screen (<see cref="AboutPanel"/>).</summary>
        public const string AboutLabel = "Informacje";

        /// <summary>Builds the menu. <paramref name="cam"/> null = screen-space overlay; a camera = capture/test.
        /// <paramref name="openAbout"/> null = the menu opens its own <see cref="AboutPanel"/> (screen-space overlay).</summary>
        public static BootMenu Create(Camera cam, StartMenuOptions options, IReadOnlyList<(string label, Action action)> starts, Action openSettings,
                                      Action openAbout = null, IReadOnlyList<BootRegionChoice> regions = null, Action openPcSettings = null)
        {
            var go = new GameObject("BootMenu");
            var menu = go.AddComponent<BootMenu>();
            menu.Options = options;
            menu.m_OpenPcSettings = openPcSettings;
            menu.Build(cam, starts, openSettings, openAbout ?? (() => AboutPanel.Create(null, null)), regions);
            return menu;
        }

        // ---- region picker (ADR 0229): one row "< region >" + start button; regions missing from the APK are greyed out
        /// <summary>PlayerPrefs key of the last picked region id.</summary>
        public const string PrefRegion = "menu.region";
        public const string RegionPrevName = "RegionPrev", RegionNextName = "RegionNext", RegionStartName = "RegionStart";
        public const string RegionStartLabel = "Jedź w wybranym regionie", RegionMissingLabel = "Region niedostępny w tym APK";
        IReadOnlyList<BootRegionChoice> m_Regions;
        int m_RegionIndex = -1;
        Text m_RegionLabel, m_RegionDetail, m_RegionStartText;
        Button m_RegionStart;

        /// <summary>Index of the region shown in the picker (-1 = no picker).</summary>
        public int RegionIndex => m_RegionIndex;
        public BootRegionChoice CurrentRegion => m_RegionIndex >= 0 ? m_Regions[m_RegionIndex] : default;

        /// <summary>First index to show: the stored pick when it is in this APK, else the first region in this APK.</summary>
        public static int InitialRegionIndex(IReadOnlyList<BootRegionChoice> regions, string storedId)
        {
            if (regions == null || regions.Count == 0) return -1;
            int first = -1;
            for (int i = 0; i < regions.Count; i++)
            {
                if (!regions[i].Available) continue;
                if (regions[i].Id == storedId) return i;
                if (first < 0) first = i;
            }
            return first;
        }

        /// <summary>Shows the previous / next region (wraps; greyed regions included so the owner sees what is missing).</summary>
        public void StepRegion(int delta)
        {
            if (m_Regions == null || m_Regions.Count == 0) return;
            int n = m_Regions.Count;
            m_RegionIndex = ((m_RegionIndex + delta) % n + n) % n;
            RefreshRegion();
        }

        void StartRegion()
        {
            if (m_RegionIndex < 0) return;
            var r = m_Regions[m_RegionIndex];
            if (!r.Available || r.Start == null) return;
            PlayerPrefs.SetString(PrefRegion, r.Id);
            PlayerPrefs.Save();
            Debug.Log(Options.StartLine("region " + r.Id));
            r.Start();
        }

        void RefreshRegion()
        {
            if (m_RegionIndex < 0 || m_RegionLabel == null) return;
            var r = m_Regions[m_RegionIndex];
            m_RegionLabel.text = r.Label;
            m_RegionLabel.color = r.Available ? k_Text : k_Muted;
            m_RegionDetail.text = (m_RegionIndex + 1) + "/" + m_Regions.Count + " · " + r.Detail;
            m_RegionStart.interactable = r.Available;
            m_RegionStartText.text = r.Available ? RegionStartLabel : RegionMissingLabel;
            m_RegionStartText.color = r.Available ? k_Text : k_Muted;
        }

        float BuildRegionPicker(IReadOnlyList<BootRegionChoice> regions, float left, float y)
        {
            m_Regions = regions;
            m_RegionIndex = InitialRegionIndex(regions, PlayerPrefs.GetString(PrefRegion, ""));
            if (m_RegionIndex < 0) return y;   // no region of the catalog in this APK: no picker
            const float arrowW = 96f, rowH = 88f;
            y -= 8f;
            Label(m_Block, "HeaderRegion", "REGION — START NA POCZĄTKU TRASY", 24, TextAnchor.LowerLeft, k_Muted, new Vector2(left, y - 36f), new Vector2(ColW, 36f));
            y -= 44f;
            var prev = Button(m_Block, "<", new Vector2(left, y - rowH), new Vector2(arrowW, rowH), 40, TextAnchor.MiddleCenter, () => StepRegion(-1));
            prev.name = RegionPrevName;
            var next = Button(m_Block, ">", new Vector2(left + ColW - arrowW, y - rowH), new Vector2(arrowW, rowH), 40, TextAnchor.MiddleCenter, () => StepRegion(1));
            next.name = RegionNextName;
            m_Nav[0].Add(new[] { prev.GetComponent<Selectable>(), next.GetComponent<Selectable>() });
            float bw = ColW - 2f * (arrowW + Gap);
            var box = Rect("RegionBox", m_Block);
            Place(box, new Vector2(left + arrowW + Gap, y - rowH), new Vector2(bw, rowH));
            var bg = box.gameObject.AddComponent<Image>();
            bg.color = k_Panel; bg.raycastTarget = false;
            m_RegionLabel = Label(box, "RegionLabel", "", 28, TextAnchor.MiddleLeft, k_Text, new Vector2(-bw * 0.5f + 16f, 0f), new Vector2(bw - 32f, rowH * 0.5f));
            m_RegionDetail = Label(box, "RegionDetail", "", 21, TextAnchor.MiddleLeft, k_Muted, new Vector2(-bw * 0.5f + 16f, -rowH * 0.5f + 4f), new Vector2(bw - 32f, rowH * 0.5f - 4f));
            foreach (var t in new[] { m_RegionLabel, m_RegionDetail })
            {
                // Long street names shrink instead of running under the arrows.
                t.horizontalOverflow = HorizontalWrapMode.Wrap; t.verticalOverflow = VerticalWrapMode.Truncate;
                t.resizeTextForBestFit = true; t.resizeTextMinSize = 16; t.resizeTextMaxSize = t.fontSize;
            }
            y -= rowH + Gap;
            var go = Button(m_Block, RegionStartLabel, new Vector2(left, y - BtnH), new Vector2(ColW, BtnH), 31, TextAnchor.MiddleLeft, StartRegion);
            go.name = RegionStartName;
            m_RegionStart = go.GetComponent<Button>();
            m_Nav[0].Add(new Selectable[] { m_RegionStart });
            m_RegionStartText = go.GetComponentInChildren<Text>();
            m_RegionStartText.rectTransform.offsetMin = new Vector2(32f, 0f);
            y -= BtnH + Gap;
            m_Refresh.Add(RefreshRegion);
            return y;
        }

        void Build(Camera cam, IReadOnlyList<(string label, Action action)> starts, Action openSettings, Action openAbout,
                   IReadOnlyList<BootRegionChoice> regions)
        {
            var canvas = gameObject.AddComponent<Canvas>();
            canvas.renderMode = cam != null ? RenderMode.ScreenSpaceCamera : RenderMode.ScreenSpaceOverlay;
            canvas.worldCamera = cam;
            canvas.planeDistance = cam != null ? Mathf.Max(cam.nearClipPlane * 2f, 0.5f) : 1f;
            canvas.sortingOrder = 1100;
            gameObject.AddComponent<GraphicRaycaster>();
            m_Font = UiFonts.Default;

            m_View = new UiViewport(canvas);
            m_Safe = m_View.SafeArea;
            m_View.Refresh();
            m_Block = Rect("Block", m_Safe);
            m_Block.anchorMin = Vector2.zero; m_Block.anchorMax = Vector2.one;
            m_Block.offsetMin = m_Block.offsetMax = Vector2.zero;

            // Centred block: left column starts, gap 80, right column options.
            float total = 2 * ColW + 80f, left = -total * 0.5f, right = left + ColW + 80f;
            float top = 400f;   // block top (centre-anchored, y up)

            Label(m_Block, "Title", "TRUCK SIM PL — TEST WRAŻEŃ", 28, TextAnchor.LowerLeft, k_Amber, new Vector2(left, top + 52f), new Vector2(total, 44f));

            // ---- left: starts
            Label(m_Block, "HeaderStart", "WYBIERZ START", 24, TextAnchor.LowerLeft, k_Muted, new Vector2(left, top - 8f), new Vector2(ColW, 36f));
            float y = top - 52f;
            for (int i = 0; i < starts.Count; i++)
            {
                var s = starts[i];
                string label = s.label;
                var action = s.action;
                var b = Button(m_Block, label, new Vector2(left, y - BtnH), new Vector2(ColW, BtnH), 31, TextAnchor.MiddleLeft, () =>
                {
                    Debug.Log(Options.StartLine(label));
                    action();
                });
                b.GetComponentInChildren<Text>().rectTransform.offsetMin = new Vector2(32f, 0f);
                m_Nav[0].Add(new[] { b.GetComponent<Selectable>() });
                if (m_FirstItem == null) m_FirstItem = b;
                y -= BtnH + Gap;
            }
            if (regions != null && regions.Count > 0) y = BuildRegionPicker(regions, left, y);

            // ---- right: options
            Label(m_Block, "HeaderOptions", "OPCJE", 24, TextAnchor.LowerLeft, k_Muted, new Vector2(right, top - 8f), new Vector2(ColW, 36f));
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
            // Settings and "Informacje" (attributions + licences, LICENSES-AUDIT-S20 R-P0-1) share one row: the block height is unchanged.
            const float aboutW = 250f;
            var settingsBtn = Button(m_Block, "Ustawienia sterowania", new Vector2(right, oy - 80f), new Vector2(ColW - aboutW - Gap, 80f), 32, TextAnchor.MiddleCenter, () => openSettings?.Invoke());
            var aboutBtn = Button(m_Block, AboutLabel, new Vector2(right + ColW - aboutW, oy - 80f), new Vector2(aboutW, 80f), 32, TextAnchor.MiddleCenter, () => openAbout?.Invoke());
            m_Nav[1].Add(new[] { settingsBtn.GetComponent<Selectable>(), aboutBtn.GetComponent<Selectable>() });
            if (m_OpenPcSettings != null)
            {
                // ADR 0270: display / graphics / audio screen, one full-width row under the settings row; part of the
                // pad / keyboard grid of ADR 0265 (review #136 P2-2).
                oy -= 80f + Gap;
                var pcBtn = Button(m_Block, Game.UI.Settings.PcSettingsTexts.MenuButton, new Vector2(right, oy - 80f), new Vector2(ColW, 80f), 32, TextAnchor.MiddleCenter,
                    () => m_OpenPcSettings?.Invoke());
                pcBtn.name = PcSettingsName;
                m_Nav[1].Add(new[] { pcBtn.GetComponent<Selectable>() });
            }
            Label(m_Block, "Footer", "DrivingLab ma stałe światło. W jeździe: przycisk Menu wraca tutaj bez restartu aplikacji.\nWersja: " + BuildInfo.Current.IdentityLabel,
                22, TextAnchor.UpperLeft, k_Muted, new Vector2(right, oy - 80f - 12f - 70f), new Vector2(ColW, 70f)).horizontalOverflow = HorizontalWrapMode.Wrap;

            m_BlockBounds = MeasureBlock(m_Block);
            PublishBlock();
            ApplyOverlayLayout();

            UiFocus.EnsureEventSystem();
            UiFocus.ApplyGrid(m_Nav);
            if (m_FirstItem == null && m_RegionStart != null) m_FirstItem = m_RegionStart.gameObject;
            UiFocus.Push(this, m_FirstItem, m_View.Desktop);   // monitor: Enter / pad A starts at once; touch: no frame until a pad moves
            foreach (var r in m_Refresh) r();
        }

        void OnDestroy()
        {
            UiFocus.Pop(this, false);
            MenuOverlayBoard.MenuActive = false;
        }

        /// <summary>Bounding box of the direct children (all centre-anchored with a bottom-left pivot, see <see cref="Place"/>).</summary>
        static Rect MeasureBlock(RectTransform block)
        {
            float xMin = float.MaxValue, yMin = float.MaxValue, xMax = float.MinValue, yMax = float.MinValue;
            for (int i = 0; i < block.childCount; i++)
            {
                var c = (RectTransform)block.GetChild(i);
                Vector2 p = c.anchoredPosition, s = c.sizeDelta;
                xMin = Mathf.Min(xMin, p.x); yMin = Mathf.Min(yMin, p.y);
                xMax = Mathf.Max(xMax, p.x + s.x); yMax = Mathf.Max(yMax, p.y + s.y);
            }
            return xMin > xMax ? default(UnityEngine.Rect) : UnityEngine.Rect.MinMaxRect(xMin, yMin, xMax, yMax);
        }

        /// <summary>Re-reads tier / fps / lighting (the options can also change from outside, e.g. a launch argument).</summary>
        public void RefreshNow() { foreach (var r in m_Refresh) r(); }

        void Segments(string title, string[] names, float x, ref float y, Func<int> current, Action<int> set)
        {
            Label(m_Block, "Label " + title, title, 26, TextAnchor.LowerLeft, k_Text, new Vector2(x, y - 34f), new Vector2(ColW, 34f));
            y -= 40f;
            float gap = 8f, w = (ColW - gap * (names.Length - 1)) / names.Length, h = 66f;
            var images = new Image[names.Length];
            var row = new Selectable[names.Length];
            for (int i = 0; i < names.Length; i++)
            {
                int idx = i;
                var b = Button(m_Block, names[i], new Vector2(x + i * (w + gap), y - h), new Vector2(w, h), 28, TextAnchor.MiddleCenter, () => { set(idx); RefreshNow(); });
                images[i] = b.GetComponent<Image>();
                row[i] = b.GetComponent<Selectable>();
            }
            m_Nav[1].Add(row);
            m_Refresh.Add(() => { int c = current(); for (int i = 0; i < images.Length; i++) images[i].color = i == c ? k_ButtonOn : k_Button; });
            y -= h + 22f;
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
            UiFocus.Decorate(b);
            var t = Label(rt, "Label", text, fontSize, align, k_Text, Vector2.zero, size);
            t.rectTransform.anchorMin = Vector2.zero; t.rectTransform.anchorMax = Vector2.one;
            t.rectTransform.offsetMin = t.rectTransform.offsetMax = Vector2.zero;
            return rt.gameObject;
        }
    }

    /// <summary>One region of the start menu's region picker (ADR 0229). <see cref="Available"/> = its scene is in this APK.</summary>
    public readonly struct BootRegionChoice
    {
        public readonly string Id, Label, Detail;
        public readonly bool Available;
        public readonly Action Start;

        public BootRegionChoice(string id, string label, string detail, bool available, Action start)
        {
            Id = id ?? ""; Label = label ?? Id; Detail = detail ?? ""; Available = available; Start = start;
        }
    }
}
