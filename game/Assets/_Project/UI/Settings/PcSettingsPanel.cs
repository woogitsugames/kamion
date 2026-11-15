using System;
using System.Collections.Generic;
using System.Globalization;
using Game.Core.Settings;
using Game.UI.Layout;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.UI;
using UnityEngine.UI;
using T = Game.UI.Settings.PcSettingsTexts;

namespace Game.UI.Settings
{
    /// <summary>
    /// PC settings screen (ADR 0270): resolution, window mode, vsync, frame cap, graphics tier, HUD scale, units, volumes.
    /// Same flat dark-panel language as <see cref="ControlSettingsPanel"/> (steppers and segments, no icons, no glow).
    /// Edits a pending copy; "Zastosuj" saves + applies (a display change opens a 15 s keep / revert countdown),
    /// "Anuluj" / Esc / pad B discards, "Przywróć domyślne" loads the defaults into the pending copy.
    /// Mouse, keyboard and pad: every control is a <see cref="Selectable"/> with explicit up / down / left / right
    /// navigation (rows in reading order, left / right inside a row); the selected item gets a frame and scrolls into view.
    /// After #131 (ADR 0265) is merged: replace <see cref="Decorate"/> with <c>UiFocus.Decorate(b, Cancel)</c> and
    /// <see cref="WireNavigation"/> with <c>UiFocus.ApplyGrid</c> (same row lists). Menu only, never in the driving loop.
    /// </summary>
    public sealed class PcSettingsPanel : MonoBehaviour
    {
        static readonly Color k_Dim = new Color(0.02f, 0.025f, 0.03f, 0.72f);
        static readonly Color k_Panel = new Color(0.06f, 0.065f, 0.07f, 0.97f);
        static readonly Color k_Row = new Color(1f, 1f, 1f, 0.045f);
        static readonly Color k_Button = new Color(0.16f, 0.17f, 0.18f, 0.95f);
        static readonly Color k_ButtonOn = new Color(0.30f, 0.36f, 0.30f, 0.95f);
        static readonly Color k_Text = new Color(0.95f, 0.95f, 0.91f, 1f);
        static readonly Color k_Muted = new Color(0.70f, 0.70f, 0.67f, 1f);
        static readonly Color k_Amber = new Color(0.95f, 0.66f, 0.18f, 1f);

        const float RowH = 66f, ColW = 700f, Pad = 40f, Edge = 20f, HeaderH = 86f, FooterH = 108f, LabelW = 300f;

        /// <summary>Settings shown in the controls (not applied yet).</summary>
        public PcSettingsData Pending { get; private set; }
        /// <summary>Settings in force (= saved file).</summary>
        public PcSettingsData Applied { get; private set; }
        public DisplayConfirmTimer Confirm { get; } = new DisplayConfirmTimer();
        public RectTransform PanelRect { get; private set; }
        public bool TwoColumns { get; private set; }
        public bool Dirty => !Pending.SameAs(Applied);
        /// <summary>First selected item (tests).</summary>
        public GameObject FirstItem { get; private set; }

        Action m_OnClose;
        Font m_Font;
        RectTransform m_Safe, m_Content, m_Viewport;
        ScrollRect m_Scroll;
        UiViewport m_View;
        List<DisplayMode> m_Modes;
        readonly List<Action> m_Refresh = new List<Action>();
        readonly List<Selectable[]> m_Rows = new List<Selectable[]>();
        Button m_ApplyButton;
        Text m_Hint;
        GameObject m_Dialog;
        Text m_DialogCountdown;
        PcDisplaySettings m_RevertWindow;     // window as it was before "Zastosuj" (runtime state)
        PcDisplaySettings m_RevertSettings;   // display part of the file before "Zastosuj"
        GameObject m_LastSelected;

        public static PcSettingsPanel Create(Camera cam, Action onClose = null)
        {
            var go = new GameObject("PcSettingsPanel");
            var p = go.AddComponent<PcSettingsPanel>();
            p.m_OnClose = onClose;
            p.Applied = PcSettingsRuntime.Current.Clone();
            p.Pending = p.Applied.Clone();
            p.m_Modes = PcSettingsRuntime.AvailableModes();
            p.Build(cam);
            return p;
        }

        // ------------------------------------------------------------------ actions

        public void Cancel()
        {
            if (Confirm.Pending) { RevertDisplay(); return; }
            Debug.Log("[SETTINGS] pc cancel dirty=" + Dirty);
            m_OnClose?.Invoke();
            Destroy(gameObject);
        }

        public void ResetToDefaults()
        {
            Pending = PcSettingsData.Defaults();
            RefreshAll();
        }

        public void Apply()
        {
            Pending.Sanitize();
            bool displayChanged = !Pending.display.SameAs(Applied.display);
            m_RevertWindow = PcSettingsRuntime.ReadCurrentDisplay();
            m_RevertSettings = Applied.display.Clone();
            PcSettingsRuntime.Commit(Pending, applyDisplay: displayChanged);
            Applied = PcSettingsRuntime.Current.Clone();
            Pending = Applied.Clone();
            if (displayChanged && PcSettingsRuntime.IsDesktopPlayer) OpenConfirm();
            RefreshAll();
        }

        public void KeepDisplay()
        {
            Confirm.Keep();
            Debug.Log("[SETTINGS] display kept");
            CloseConfirm();
        }

        /// <summary>Countdown ran out or "Przywróć": the window goes back and the file gets the old display part again.</summary>
        public void RevertDisplay()
        {
            Confirm.Revert();
            var s = Applied.Clone();
            s.display = m_RevertSettings ?? s.display;
            PcSettingsRuntime.Commit(s, applyDisplay: false);
            if (m_RevertWindow != null && PcSettingsRuntime.IsDesktopPlayer) PcSettingsRuntime.ApplyDisplay(m_RevertWindow);
            Applied = PcSettingsRuntime.Current.Clone();
            Pending = Applied.Clone();
            Debug.Log("[SETTINGS] display reverted");
            CloseConfirm();
            RefreshAll();
        }

        // ------------------------------------------------------------------ frame

        void Update()
        {
            if (m_View != null && m_View.Refresh()) BuildContent();
            if (Confirm.Pending)
            {
                if (Confirm.Tick(Time.unscaledDeltaTime)) { RevertDisplay(); return; }
                if (m_DialogCountdown != null) m_DialogCountdown.text = string.Format(CultureInfo.InvariantCulture, T.ConfirmCountdown, Confirm.SecondsLeft);
            }
            if (BackPressed()) { Cancel(); return; }
            var es = EventSystem.current;
            if (es == null) return;
            var sel = es.currentSelectedGameObject;
            if (sel == null || !sel.activeInHierarchy)
            {
                // Pad / keyboard must never be left without a selection (mouse clicks on empty space clear it).
                if (Keyboard.current != null && Keyboard.current.anyKey.wasPressedThisFrame || Gamepad.current != null && Gamepad.current.wasUpdatedThisFrame)
                    es.SetSelectedGameObject(m_Dialog != null ? m_Dialog.GetComponentInChildren<Selectable>().gameObject : FirstItem);
            }
            else if (sel != m_LastSelected)
            {
                m_LastSelected = sel;
                ScrollIntoView(sel.transform as RectTransform);
            }
        }

        static bool BackPressed() =>
            (Keyboard.current != null && Keyboard.current.escapeKey.wasPressedThisFrame) ||
            (Gamepad.current != null && Gamepad.current.buttonEast.wasPressedThisFrame);

        void ScrollIntoView(RectTransform item)
        {
            if (item == null || m_Scroll == null || !m_Scroll.vertical || !item.IsChildOf(m_Content)) return;
            var corners = new Vector3[4];
            item.GetWorldCorners(corners);
            Vector2 lo = m_Viewport.InverseTransformPoint(corners[0]), hi = m_Viewport.InverseTransformPoint(corners[2]);
            var r = m_Viewport.rect;
            float dy = 0f;
            if (hi.y > r.yMax) dy = hi.y - r.yMax + 12f;
            else if (lo.y < r.yMin) dy = lo.y - r.yMin - 12f;
            if (Mathf.Abs(dy) < 0.5f) return;
            var p = m_Content.anchoredPosition;
            float maxY = Mathf.Max(0f, m_Content.rect.height - r.height);
            p.y = Mathf.Clamp(p.y - dy, 0f, maxY);
            m_Content.anchoredPosition = p;
        }

        void OnRectTransformDimensionsChange() { m_View?.Invalidate(); }

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
            dim.gameObject.AddComponent<Image>().color = k_Dim;   // swallows clicks behind the panel

            m_View = new UiViewport(canvas);
            m_Safe = m_View.SafeArea;
            if (FindAnyObjectByType<EventSystem>() == null)
                new GameObject("EventSystem", typeof(EventSystem)).AddComponent<InputSystemUIInputModule>().AssignDefaultActions();
            m_View.Refresh();
            BuildContent();
            Debug.Log("[SETTINGS] pc open modes=" + m_Modes.Count);
        }

        void BuildContent()
        {
            for (int i = m_Safe.childCount - 1; i >= 0; i--)
            {
                var c = m_Safe.GetChild(i);
                c.SetParent(null, false);
                if (Application.isPlaying) Destroy(c.gameObject); else DestroyImmediate(c.gameObject);
            }
            m_Refresh.Clear();
            m_Rows.Clear();
            FirstItem = null;
            m_Dialog = null;
            m_Hint = null;
            m_LastSelected = null;

            Vector2 avail = m_View.SizeUnits - new Vector2(2f * Edge, 2f * Edge);
            float twoW = 2f * ColW + 3f * Pad;
            TwoColumns = avail.x >= twoW;
            float panelW = TwoColumns ? twoW : Mathf.Min(ColW + 2f * Pad, avail.x);

            var panel = Rect("Panel", m_Safe);
            PanelRect = panel;
            panel.anchorMin = panel.anchorMax = panel.pivot = new Vector2(0.5f, 0.5f);
            panel.anchoredPosition = Vector2.zero;
            panel.gameObject.AddComponent<Image>().color = k_Panel;

            m_Viewport = Rect("Viewport", panel);
            m_Viewport.anchorMin = Vector2.zero; m_Viewport.anchorMax = Vector2.one;
            m_Viewport.offsetMin = new Vector2(0f, FooterH); m_Viewport.offsetMax = new Vector2(0f, -HeaderH);
            m_Viewport.gameObject.AddComponent<Image>().color = new Color(0, 0, 0, 0);
            m_Viewport.gameObject.AddComponent<RectMask2D>();
            m_Content = Rect("Content", m_Viewport);
            m_Content.anchorMin = new Vector2(0f, 1f); m_Content.anchorMax = new Vector2(1f, 1f); m_Content.pivot = new Vector2(0.5f, 1f);

            float left = Pad, right = TwoColumns ? Pad + ColW + Pad : Pad;
            var content = m_Content;

            // ---- left: display + graphics
            float y = 0f;
            Header(content, T.SectionDisplay, left, ref y);
            Stepper(content, left, ref y, T.Resolution, ResolutionLabel, StepResolution, null);
            Segments(content, left, ref y, T.WindowMode, T.WindowModeLabels,
                () => Array.IndexOf(WindowModes.All, Pending.display.mode), i => Pending.display.mode = WindowModes.All[i]);
            Segments(content, left, ref y, T.Vsync, T.OffOn, () => Pending.vsync ? 1 : 0, i => Pending.vsync = i == 1);
            Stepper(content, left, ref y, T.FpsCap, FpsLabel,
                d => Pending.fpsCap = PcSettingsData.FpsCaps[PcSettingsData.StepIndex(Math.Max(0, Array.IndexOf(PcSettingsData.FpsCaps, Pending.fpsCap)), d, PcSettingsData.FpsCaps.Length)],
                () => !Pending.vsync);
            y += 18f;
            Header(content, T.SectionGraphics, left, ref y);
            Stepper(content, left, ref y, T.Tier, TierLabel,
                d => Pending.graphicsTier = TierChoices.All[PcSettingsData.StepIndex(Math.Max(0, Array.IndexOf(TierChoices.All, Pending.graphicsTier)), d, TierChoices.All.Length)], null);
            float leftEnd = y;

            // ---- right (or below): interface + audio
            y = TwoColumns ? 0f : leftEnd + 18f;
            Header(content, T.SectionInterface, right, ref y);
            Stepper(content, right, ref y, T.HudScale, () => Pct(Pending.hudScale),
                d => Pending.hudScale = PcSettingsData.Step(Pending.hudScale, d, PcSettingsData.HudScaleStep, PcSettingsData.HudScaleMin, PcSettingsData.HudScaleMax), null);
            // Units: the HUD and the cab displays render km/h only (ADR 0270 §Jednostki) - shown, not editable.
            Stepper(content, right, ref y, T.Units, () => T.UnitsMetric, null, null);
            y += 18f;
            Header(content, T.SectionAudio, right, ref y);
            VolumeRow(content, right, ref y, T.VolumeMaster, () => Pending.volumes.master, v => Pending.volumes.master = v);
            VolumeRow(content, right, ref y, T.VolumeEngine, () => Pending.volumes.engine, v => Pending.volumes.engine = v);
            VolumeRow(content, right, ref y, T.VolumeAmbient, () => Pending.volumes.ambient, v => Pending.volumes.ambient = v);
            VolumeRow(content, right, ref y, T.VolumeUi, () => Pending.volumes.ui, v => Pending.volumes.ui = v);

            float contentH = Mathf.Max(leftEnd, y) + 8f;
            float panelH = Mathf.Min(avail.y, HeaderH + contentH + FooterH);
            panel.sizeDelta = new Vector2(panelW, panelH);
            m_Content.sizeDelta = new Vector2(0f, contentH);
            m_Content.anchoredPosition = Vector2.zero;
            bool scrolls = contentH > panelH - HeaderH - FooterH + 0.5f;
            m_Scroll = m_Viewport.gameObject.AddComponent<ScrollRect>();
            m_Scroll.viewport = m_Viewport; m_Scroll.content = m_Content;
            m_Scroll.horizontal = false; m_Scroll.vertical = scrolls;
            m_Scroll.movementType = ScrollRect.MovementType.Clamped;
            m_Scroll.scrollSensitivity = 40f;

            // ---- title + hint
            var title = Label(panel, "Title", T.Title, 38, TextAnchor.MiddleLeft, k_Text, Vector2.zero, Vector2.zero);
            TopBand(title.rectTransform, Pad, TwoColumns ? Pad + 460f : Pad, 14f, 60f);
            title.horizontalOverflow = HorizontalWrapMode.Wrap; title.resizeTextForBestFit = true; title.resizeTextMinSize = 24; title.resizeTextMaxSize = 38;
            if (TwoColumns)
            {
                m_Hint = Label(panel, "Hint", "", 24, TextAnchor.MiddleRight, k_Muted, Vector2.zero, Vector2.zero);
                TopBand(m_Hint.rectTransform, panelW - Pad - 440f, Pad, 14f, 60f);
            }

            // ---- footer: defaults | cancel | apply
            float inner = panelW - 2f * Pad;
            float bw = Mathf.Min(300f, (inner - 2f * 20f) / 3f), resetW = Mathf.Min(420f, inner - 2f * bw - 2f * 20f);
            var reset = TextButton(panel, T.Defaults, new Vector2(Pad, 20f), new Vector2(resetW, 72f), ResetToDefaults);
            var cancel = TextButton(panel, T.Cancel, new Vector2(panelW - Pad - 2f * bw - 20f, 20f), new Vector2(bw, 72f), Cancel);
            var apply = TextButton(panel, T.Apply, new Vector2(panelW - Pad - bw, 20f), new Vector2(bw, 72f), Apply);
            m_ApplyButton = apply.GetComponent<Button>();
            m_Rows.Add(new[] { reset.GetComponent<Selectable>(), cancel.GetComponent<Selectable>(), m_ApplyButton });
            m_Refresh.Add(() =>
            {
                bool dirty = Dirty;
                m_ApplyButton.interactable = dirty;
                m_ApplyButton.GetComponent<Image>().color = dirty ? k_ButtonOn : k_Button;
                if (m_Hint != null) { m_Hint.text = dirty ? T.HintDirty : T.HintClean; m_Hint.color = dirty ? k_Amber : k_Muted; }
            });

            WireNavigation(m_Rows);
            if (FirstItem == null) FirstItem = cancel;
            // ADR 0265 (review #136 P2-2): this screen is the top focus owner while open, so the start menu below does not
            // take the pad / keyboard selection back (UiFocus.RestoreIfLost) and start a scene behind it. The selection
            // itself is still handled here (dialog, scroll into view).
            UiFocus.Push(this, FirstItem, false);
            RefreshAll();
            if (Confirm.Pending) OpenConfirm();   // rebuilt while the countdown runs (window resized by the new mode)
            else if (EventSystem.current != null) EventSystem.current.SetSelectedGameObject(FirstItem);
        }

        void OnDestroy() => UiFocus.Pop(this, true);   // the pad selection goes back to the start menu below

        void RefreshAll() { foreach (var r in m_Refresh) r(); }

        // ------------------------------------------------------------------ values

        /// <summary>Index into "native + modes" (0 = native).</summary>
        int ResolutionIndex()
        {
            var d = Pending.display;
            if (d.UsesNativeResolution) return 0;
            return 1 + Math.Max(0, ResolutionList.IndexOf(m_Modes, d.width, d.height, d.RefreshHz));
        }

        string ResolutionLabel()
        {
            int i = ResolutionIndex();
            if (i == 0)
            {
                var c = Screen.currentResolution;
                return T.Native + " (" + c.width.ToString(CultureInfo.InvariantCulture) + " × " + c.height.ToString(CultureInfo.InvariantCulture) + ")";
            }
            return m_Modes[i - 1].Label();
        }

        void StepResolution(int dir)
        {
            int i = PcSettingsData.StepIndex(ResolutionIndex(), dir, m_Modes.Count + 1);
            var d = Pending.display;
            if (i == 0) { d.width = d.height = d.refreshNumerator = d.refreshDenominator = 0; return; }
            var m = m_Modes[i - 1];
            d.width = m.Width; d.height = m.Height;
            d.refreshNumerator = (int)m.RefreshNumerator; d.refreshDenominator = (int)m.RefreshDenominator;
        }

        string FpsLabel()
        {
            if (Pending.vsync) return T.FpsByVsync;
            return Pending.fpsCap > 0 ? Pending.fpsCap.ToString(CultureInfo.InvariantCulture) + " FPS" : T.FpsNoCap;
        }

        string TierLabel()
        {
            int i = Math.Max(0, Array.IndexOf(TierChoices.All, Pending.graphicsTier));
            if (i != 0) return T.TierLabels[i];
            string auto = PcSettingsRuntime.AutoTier?.Invoke();
            int a = Array.IndexOf(TierChoices.QualityLevelNames, auto);
            return a > 0 ? T.TierLabels[0] + " (" + T.TierLabels[a] + ")" : T.TierLabels[0];
        }

        static string Pct(float v) => Mathf.RoundToInt(v * 100f).ToString(CultureInfo.InvariantCulture) + " %";

        void VolumeRow(RectTransform parent, float x, ref float y, string label, Func<float> get, Action<float> set) =>
            Stepper(parent, x, ref y, label, () => Pct(get()), d => set(PcSettingsData.Step(get(), d, PcSettingsData.VolumeStep, 0f, 1f)), null);

        // ------------------------------------------------------------------ rows

        void Header(RectTransform parent, string text, float x, ref float y)
        {
            var l = Label(parent, "Header", text, 24, TextAnchor.LowerLeft, k_Amber, Vector2.zero, new Vector2(ColW, 40f));
            PlaceTop(l.rectTransform, x, y, new Vector2(ColW, 40f));
            y += 52f;
        }

        RectTransform Row(RectTransform parent, string label, float x, ref float y)
        {
            var row = Rect("Row " + label, parent);
            PlaceTop(row, x, y, new Vector2(ColW, RowH - 8f));
            row.gameObject.AddComponent<Image>().color = k_Row;
            var l = Label(row, "Label", label, 28, TextAnchor.MiddleLeft, k_Text, new Vector2(20f, 0f), new Vector2(LabelW - 20f, RowH - 8f));
            l.horizontalOverflow = HorizontalWrapMode.Wrap; l.resizeTextForBestFit = true; l.resizeTextMinSize = 20; l.resizeTextMaxSize = 28;
            y += RowH;
            return row;
        }

        /// <summary>"Label   [−]  value  [+]"; <paramref name="step"/> null = read-only value; <paramref name="enabled"/> null = always.</summary>
        void Stepper(RectTransform parent, float x, ref float y, string label, Func<string> value, Action<int> step, Func<bool> enabled)
        {
            var row = Row(parent, label, x, ref y);
            float bx = LabelW + 20f, bw = 72f, vw = ColW - bx - 2f * bw - 20f;
            var v = Label(row, "Value", "", 27, TextAnchor.MiddleCenter, k_Text, new Vector2(bx + bw, 0f), new Vector2(vw, RowH - 8f));
            v.horizontalOverflow = HorizontalWrapMode.Wrap; v.resizeTextForBestFit = true; v.resizeTextMinSize = 18; v.resizeTextMaxSize = 27;
            if (step == null)
            {
                v.color = k_Muted; v.alignment = TextAnchor.MiddleRight;
                Place(v.rectTransform, Vector2.zero, new Vector2(bx, 0f), new Vector2(ColW - bx - 20f, RowH - 8f));
                m_Refresh.Add(() => v.text = value());
                return;
            }
            var minus = TextButton(row, "−", new Vector2(bx, 6f), new Vector2(bw, RowH - 20f), () => { step(-1); RefreshAll(); }).GetComponent<Button>();
            var plus = TextButton(row, "+", new Vector2(ColW - bw - 12f, 6f), new Vector2(bw, RowH - 20f), () => { step(+1); RefreshAll(); }).GetComponent<Button>();
            m_Rows.Add(new Selectable[] { minus, plus });
            if (FirstItem == null) FirstItem = minus.gameObject;
            m_Refresh.Add(() =>
            {
                bool on = enabled == null || enabled();
                minus.interactable = plus.interactable = on;
                v.text = value(); v.color = on ? k_Text : k_Muted;
            });
        }

        void Segments(RectTransform parent, float x, ref float y, string label, string[] names, Func<int> current, Action<int> set)
        {
            var row = Row(parent, label, x, ref y);
            float gap = 6f, x0 = LabelW + 20f, w = (ColW - x0 - 12f - gap * (names.Length - 1)) / names.Length;
            var imgs = new Image[names.Length];
            var sel = new Selectable[names.Length];
            for (int i = 0; i < names.Length; i++)
            {
                int idx = i;
                var b = TextButton(row, names[i], new Vector2(x0 + i * (w + gap), 6f), new Vector2(w, RowH - 20f), () => { set(idx); RefreshAll(); }, 24);
                imgs[i] = b.GetComponent<Image>();
                sel[i] = b.GetComponent<Button>();
            }
            m_Rows.Add(sel);
            if (FirstItem == null) FirstItem = sel[0].gameObject;
            m_Refresh.Add(() => { int c = current(); for (int i = 0; i < imgs.Length; i++) imgs[i].color = i == c ? k_ButtonOn : k_Button; });
        }

        // ------------------------------------------------------------------ navigation + focus

        /// <summary>Explicit navigation: up / down to the nearest item of the previous / next row (by position in the row),
        /// left / right inside the row. Same row lists as <c>UiFocus.ApplyGrid</c> of ADR 0265 (#131).</summary>
        public static void WireNavigation(IReadOnlyList<Selectable[]> rows)
        {
            for (int r = 0; r < rows.Count; r++)
            {
                var row = rows[r];
                for (int i = 0; i < row.Length; i++)
                {
                    // UnityEngine.UI.Navigation spelled out: inside Game.UI.* the simple name is the namespace Game.UI.Navigation (CS0118).
                    var nav = new UnityEngine.UI.Navigation { mode = UnityEngine.UI.Navigation.Mode.Explicit };
                    nav.selectOnLeft = i > 0 ? row[i - 1] : null;
                    nav.selectOnRight = i < row.Length - 1 ? row[i + 1] : null;
                    nav.selectOnUp = r > 0 ? Pick(rows[r - 1], i, row.Length) : null;
                    nav.selectOnDown = r < rows.Count - 1 ? Pick(rows[r + 1], i, row.Length) : null;
                    row[i].navigation = nav;
                }
            }
        }

        static Selectable Pick(Selectable[] row, int i, int fromCount)
        {
            if (row.Length == 0) return null;
            int j = fromCount <= 1 ? 0 : Mathf.RoundToInt(i * (row.Length - 1) / (float)(fromCount - 1));
            return row[Mathf.Clamp(j, 0, row.Length - 1)];
        }

        static void Decorate(Button b)
        {
            var cb = b.colors;
            cb.normalColor = Color.white; cb.highlightedColor = new Color(0.88f, 0.88f, 0.86f, 1f); cb.selectedColor = Color.white;
            cb.pressedColor = new Color(0.75f, 0.75f, 0.72f, 1f); cb.disabledColor = new Color(0.6f, 0.6f, 0.6f, 0.5f);
            b.colors = cb;
            b.gameObject.AddComponent<PcFocusOutline>().Init(k_Amber);
        }

        // ------------------------------------------------------------------ confirm dialog

        void OpenConfirm()
        {
            if (!Confirm.Pending) Confirm.Start();
            if (m_Dialog != null) Destroy(m_Dialog);
            var root = Rect("ConfirmDisplay", m_Safe);
            Stretch(root);
            root.gameObject.AddComponent<Image>().color = k_Dim;
            m_Dialog = root.gameObject;
            var box = Rect("Box", root);
            box.anchorMin = box.anchorMax = box.pivot = new Vector2(0.5f, 0.5f);
            box.sizeDelta = new Vector2(820f, 300f);
            box.gameObject.AddComponent<Image>().color = k_Panel;
            var t = Label(box, "Title", T.ConfirmTitle, 34, TextAnchor.MiddleLeft, k_Text, new Vector2(Pad, 200f), new Vector2(820f - 2f * Pad, 70f));
            t.horizontalOverflow = HorizontalWrapMode.Wrap;
            m_DialogCountdown = Label(box, "Countdown", "", 26, TextAnchor.MiddleLeft, k_Amber, new Vector2(Pad, 140f), new Vector2(820f - 2f * Pad, 50f));
            m_DialogCountdown.text = string.Format(CultureInfo.InvariantCulture, T.ConfirmCountdown, Confirm.SecondsLeft);
            float bw = 300f;
            var revert = TextButton(box, T.ConfirmRevert, new Vector2(820f - Pad - 2f * bw - 20f, 30f), new Vector2(bw, 72f), RevertDisplay).GetComponent<Button>();
            var keep = TextButton(box, T.ConfirmKeep, new Vector2(820f - Pad - bw, 30f), new Vector2(bw, 72f), KeepDisplay).GetComponent<Button>();
            keep.GetComponent<Image>().color = k_ButtonOn;
            WireNavigation(new[] { new Selectable[] { revert, keep } });
            // Default = revert: Enter / pad A pressed out of habit must not keep a mode the monitor may not show.
            if (EventSystem.current != null) EventSystem.current.SetSelectedGameObject(revert.gameObject);
        }

        void CloseConfirm()
        {
            if (m_Dialog != null) Destroy(m_Dialog);
            m_Dialog = null;
            m_DialogCountdown = null;
            if (EventSystem.current != null && m_ApplyButton != null) EventSystem.current.SetSelectedGameObject(FirstItem);
        }

        // ------------------------------------------------------------------ helpers (same as ControlSettingsPanel)

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

        static void PlaceTop(RectTransform rt, float x, float yFromTop, Vector2 size)
        {
            rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(0f, 1f);
            rt.anchoredPosition = new Vector2(x, -yFromTop);
            rt.sizeDelta = size;
        }

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

        GameObject TextButton(Transform parent, string text, Vector2 bottomLeft, Vector2 size, UnityEngine.Events.UnityAction onClick, int fontSize = 28)
        {
            var rt = Rect(text, parent);
            Place(rt, Vector2.zero, bottomLeft, size);
            var img = rt.gameObject.AddComponent<Image>();
            img.color = k_Button;
            var b = rt.gameObject.AddComponent<Button>();
            b.targetGraphic = img;
            b.onClick.AddListener(onClick);
            Decorate(b);
            var l = Label(rt, "Label", text, fontSize, TextAnchor.MiddleCenter, k_Text, Vector2.zero, size);
            l.horizontalOverflow = HorizontalWrapMode.Wrap; l.resizeTextForBestFit = true; l.resizeTextMinSize = 16; l.resizeTextMaxSize = fontSize;
            return rt.gameObject;
        }
    }
}
