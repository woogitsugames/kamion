using System;
using System.Collections.Generic;
using System.Globalization;
using Game.Controls;
using Game.Core.Settings;
using Game.UI.Layout;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.UI;
using P = Game.Controls.UiPalette;
using T = Game.UI.Settings.PcSettingsTexts;

namespace Game.UI.Settings
{
    /// <summary>
    /// PC settings screen (ADR 0270; tabs and new groups ADR 0283, D84 "menu niewygodne"): one screen, five tabs -
    /// Grafika (display + quality), Sterowanie (links to the wheel / pedal / camera panel and the bindings), Dźwięk,
    /// Rozgrywka (HUD scale, HUD detail, HUD in the cab, touch controls, units), Lusterka (windows on / off, size, height,
    /// inset, adjustment, live layout preview). Edits pending copies (<see cref="PcSettingsData"/>, <see cref="HudPrefsData"/>,
    /// touch-control mode, mirror windows); "Zastosuj" saves + applies (a display change opens the 15 s keep / revert
    /// countdown), "Anuluj" / Esc / pad B / right mouse discards, "Przywróć domyślne" loads the defaults of the open tab.
    /// Keyboard, mouse and pad (<see cref="MenuCommandMap"/>): tabs with Q / E or LB / RB (or a click), rows with the
    /// arrows / d-pad / stick, Enter / A to press; the focused item has the amber frame (<see cref="UiFocus"/>) and scrolls
    /// into view. While open it owns the focus (<see cref="UiFocus.Push"/>), so the driving scene gates every PC driving
    /// source (review #131 P1-1). Flat matte panels from <see cref="UiPalette"/> (WCAG AA), Inter Regular / SemiBold,
    /// no icons, gradients or glow (docs/06 section 7). Menu only, never in the driving loop.
    /// </summary>
    public sealed class PcSettingsPanel : MonoBehaviour
    {
        const float Pad = 40f, Edge = 20f, HeaderH = 96f, TabsH = 64f, HelpH = 40f, FooterH = 108f, RowH = 68f, LabelW = 420f;
        const float MaxPanelW = 1240f, MaxPanelH = 1240f;

        /// <summary>Opens the wheel / pedal / camera panel (set by the start menu before it opens this screen; null = not available).</summary>
        public static Action OpenControlSettings;

        /// <summary>Tab opened last (the screen reopens there in this session).</summary>
        static int s_LastTab;

        /// <summary>Settings shown in the controls (not applied yet).</summary>
        public PcSettingsData Pending { get; private set; }
        /// <summary>Settings in force (= saved file).</summary>
        public PcSettingsData Applied { get; private set; }
        public HudPrefsData HudPending => m_HudPending;
        public DisplayConfirmTimer Confirm { get; } = new DisplayConfirmTimer();
        public RectTransform PanelRect { get; private set; }
        /// <summary>Open tab (<see cref="PcSettingsTexts.Tabs"/>).</summary>
        public int Tab { get; private set; }
        public bool Dirty => !Pending.SameAs(Applied) || !m_HudPending.SameAs(m_HudApplied) || m_TouchPending != m_TouchApplied || m_MirrorsPending != m_MirrorsApplied;
        /// <summary>First selected item (tests).</summary>
        public GameObject FirstItem { get; private set; }
        /// <summary>Kept for the ADR 0270 tests / captures: the tabbed screen is always one column.</summary>
        public bool TwoColumns => false;

        Action m_OnClose;
        Font m_Font, m_Strong;
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
        HudPrefsData m_HudPending, m_HudApplied;
        TouchControlsMode m_TouchPending, m_TouchApplied;
        bool m_MirrorsPending, m_MirrorsApplied;
        float m_ColW;

        public static PcSettingsPanel Create(Camera cam, Action onClose = null)
        {
            var go = new GameObject("PcSettingsPanel");
            var p = go.AddComponent<PcSettingsPanel>();
            p.m_OnClose = onClose;
            p.Applied = PcSettingsRuntime.Current.Clone();
            p.Pending = p.Applied.Clone();
            p.m_HudApplied = p.m_HudPending = HudPreferences.Current;
            p.m_TouchApplied = p.m_TouchPending = UiPreferences.TouchControls;
            p.m_MirrorsApplied = p.m_MirrorsPending = ControlSettings.Load().mirrorInsets;
            p.m_Modes = PcSettingsRuntime.AvailableModes();
            p.Tab = Mathf.Clamp(s_LastTab, 0, T.Tabs.Length - 1);
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

        /// <summary>Defaults of the open tab into the pending copies (the other tabs keep their edits).</summary>
        public void ResetToDefaults()
        {
            var d = PcSettingsData.Defaults();
            var h = HudPrefsData.Defaults;
            switch (Tab)
            {
                case T.TabGraphics:
                    Pending.display = d.display; Pending.vsync = d.vsync; Pending.fpsCap = d.fpsCap; Pending.graphicsTier = d.graphicsTier;
                    break;
                case T.TabAudio:
                    Pending.volumes = d.volumes;
                    break;
                case T.TabGameplay:
                    Pending.hudScale = d.hudScale; m_HudPending.Detail = h.Detail; m_HudPending.Cab = h.Cab; m_TouchPending = TouchControlsMode.Auto;
                    break;
                case T.TabMirrors:
                    m_MirrorsPending = ControlSettings.Defaults().mirrorInsets;
                    m_HudPending.MirrorSize = h.MirrorSize; m_HudPending.MirrorDrop = h.MirrorDrop; m_HudPending.MirrorInset = h.MirrorInset;
                    m_HudPending.MirrorYawOut = h.MirrorYawOut; m_HudPending.MirrorPitchDown = h.MirrorPitchDown;
                    break;
            }
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
            HudPreferences.Set(m_HudPending);
            m_HudApplied = m_HudPending = HudPreferences.Current;
            UiPreferences.TouchControls = m_TouchPending;
            m_TouchApplied = m_TouchPending = UiPreferences.TouchControls;
            if (m_MirrorsPending != m_MirrorsApplied)
            {
                var c = ControlSettings.Load();
                c.mirrorInsets = m_MirrorsPending;
                c.Save();
                m_MirrorsApplied = m_MirrorsPending;
            }
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

        /// <summary>Opens tab <paramref name="index"/> (pending edits of every tab are kept).</summary>
        public void ShowTab(int index)
        {
            index = Mathf.Clamp(index, 0, T.Tabs.Length - 1);
            if (index == Tab && m_Content != null) return;
            Tab = index;
            s_LastTab = index;
            BuildContent();
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
            if (m_Dialog == null)
            {
                int tab = TabStep();
                if (tab != 0) { ShowTab(MenuCommandMap.StepTab(Tab, tab, T.Tabs.Length)); return; }
            }
            UiFocus.RestoreIfLost(this, m_Dialog != null ? m_Dialog.GetComponentInChildren<Selectable>().gameObject : FirstItem);
        }

        /// <summary>Esc / pad B / right mouse button (MenuCommand.Back).</summary>
        static bool BackPressed() =>
            (Keyboard.current != null && Keyboard.current.escapeKey.wasPressedThisFrame) ||
            (Gamepad.current != null && Gamepad.current.buttonEast.wasPressedThisFrame) ||
            (Mouse.current != null && Mouse.current.rightButton.wasPressedThisFrame);

        /// <summary>Q / E, LB / RB (MenuCommand.PrevTab / NextTab): -1, +1 or 0.</summary>
        static int TabStep()
        {
            var k = Keyboard.current;
            var g = Gamepad.current;
            if ((k != null && k.eKey.wasPressedThisFrame) || (g != null && g.rightShoulder.wasPressedThisFrame)) return 1;
            if ((k != null && k.qKey.wasPressedThisFrame) || (g != null && g.leftShoulder.wasPressedThisFrame)) return -1;
            return 0;
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
            m_Strong = UiFonts.Strong;

            var dim = Rect("Dim", transform);
            Stretch(dim);
            dim.gameObject.AddComponent<Image>().color = P.Scrim;   // swallows clicks behind the panel

            m_View = new UiViewport(canvas);
            m_Safe = m_View.SafeArea;
            UiFocus.EnsureEventSystem();
            m_View.Refresh();
            BuildContent();
            Debug.Log("[SETTINGS] pc open modes=" + m_Modes.Count + " tab=" + T.Tabs[Tab]);
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

            Vector2 avail = m_View.SizeUnits - new Vector2(2f * Edge, 2f * Edge);
            float panelW = Mathf.Min(MaxPanelW, avail.x);
            float panelH = Mathf.Min(MaxPanelH, avail.y);
            m_ColW = panelW - 2f * Pad;

            var panel = Rect("Panel", m_Safe);
            PanelRect = panel;
            panel.anchorMin = panel.anchorMax = panel.pivot = new Vector2(0.5f, 0.5f);
            panel.anchoredPosition = Vector2.zero;
            panel.sizeDelta = new Vector2(panelW, panelH);
            panel.gameObject.AddComponent<Image>().color = P.Panel;

            // ---- title + hint
            var title = Label(panel, "Title", T.Title, 40, TextAnchor.MiddleLeft, P.Ink, Vector2.zero, Vector2.zero, m_Strong);
            TopBand(title.rectTransform, Pad, Pad + 520f, 18f, 60f);
            m_Hint = Label(panel, "Hint", "", 24, TextAnchor.MiddleRight, P.InkMuted, Vector2.zero, Vector2.zero);
            TopBand(m_Hint.rectTransform, panelW - Pad - 500f, Pad, 18f, 60f);

            // ---- tabs (inverted fill = open tab)
            var tabRow = new Selectable[T.Tabs.Length];
            float gap = 8f, tw = (m_ColW - gap * (T.Tabs.Length - 1)) / T.Tabs.Length;
            for (int i = 0; i < T.Tabs.Length; i++)
            {
                int idx = i;
                var b = TextButton(panel, T.Tabs[i], new Vector2(Pad + i * (tw + gap), panelH - HeaderH - TabsH), new Vector2(tw, TabsH), () => ShowTab(idx), 26);
                bool open = i == Tab;
                b.GetComponent<Image>().color = open ? P.SegmentOn : P.Button;
                var t = b.GetComponentInChildren<Text>();
                t.color = open ? P.InkOnLight : P.Ink;
                t.font = open ? m_Strong : m_Font;
                tabRow[i] = b.GetComponent<Selectable>();
            }
            var keys = Label(panel, "Keys", T.HintKeys, 20, TextAnchor.MiddleLeft, P.InkMuted, new Vector2(Pad, panelH - HeaderH - TabsH - HelpH), new Vector2(m_ColW, HelpH));
            keys.horizontalOverflow = HorizontalWrapMode.Wrap; keys.resizeTextForBestFit = true; keys.resizeTextMinSize = 14; keys.resizeTextMaxSize = 20;
            m_Rows.Add(tabRow);

            // ---- content viewport
            m_Viewport = Rect("Viewport", panel);
            m_Viewport.anchorMin = Vector2.zero; m_Viewport.anchorMax = Vector2.one;
            m_Viewport.offsetMin = new Vector2(0f, FooterH); m_Viewport.offsetMax = new Vector2(0f, -(HeaderH + TabsH + HelpH + 8f));
            m_Viewport.gameObject.AddComponent<Image>().color = new Color(0, 0, 0, 0);
            m_Viewport.gameObject.AddComponent<RectMask2D>();
            m_Content = Rect("Content", m_Viewport);
            m_Content.anchorMin = new Vector2(0f, 1f); m_Content.anchorMax = new Vector2(1f, 1f); m_Content.pivot = new Vector2(0.5f, 1f);

            float y = 8f;
            switch (Tab)
            {
                case T.TabGraphics: BuildGraphics(ref y); break;
                case T.TabControls: BuildControls(ref y); break;
                case T.TabAudio: BuildAudio(ref y); break;
                case T.TabGameplay: BuildGameplay(ref y); break;
                default: BuildMirrors(ref y); break;
            }
            float contentH = y + 8f;
            float viewH = panelH - FooterH - (HeaderH + TabsH + HelpH + 8f);
            m_Content.sizeDelta = new Vector2(0f, contentH);
            m_Content.anchoredPosition = Vector2.zero;
            m_Scroll = m_Viewport.gameObject.AddComponent<ScrollRect>();
            m_Scroll.viewport = m_Viewport; m_Scroll.content = m_Content;
            m_Scroll.horizontal = false; m_Scroll.vertical = contentH > viewH + 0.5f;
            m_Scroll.movementType = ScrollRect.MovementType.Clamped;
            m_Scroll.scrollSensitivity = 40f;

            // ---- footer: defaults | cancel | apply
            float bw = Mathf.Min(300f, (m_ColW - 2f * 20f) / 3f), resetW = Mathf.Min(420f, m_ColW - 2f * bw - 2f * 20f);
            var reset = TextButton(panel, T.Defaults, new Vector2(Pad, 20f), new Vector2(resetW, 72f), ResetToDefaults);
            var cancel = TextButton(panel, T.Cancel, new Vector2(panelW - Pad - 2f * bw - 20f, 20f), new Vector2(bw, 72f), Cancel);
            var apply = TextButton(panel, T.Apply, new Vector2(panelW - Pad - bw, 20f), new Vector2(bw, 72f), Apply);
            m_ApplyButton = apply.GetComponent<Button>();
            m_Rows.Add(new[] { reset.GetComponent<Selectable>(), cancel.GetComponent<Selectable>(), m_ApplyButton });
            m_Refresh.Add(() =>
            {
                bool dirty = Dirty;
                m_ApplyButton.interactable = dirty;
                var img = m_ApplyButton.GetComponent<Image>();
                var lbl = m_ApplyButton.GetComponentInChildren<Text>();
                img.color = dirty ? P.SegmentOn : P.Button;
                lbl.color = dirty ? P.InkOnLight : P.InkDisabled;
                if (m_Hint != null) { m_Hint.text = dirty ? T.HintDirty : T.HintClean; m_Hint.color = dirty ? P.Accent : P.InkMuted; }
            });

            WireNavigation(m_Rows);
            if (FirstItem == null) FirstItem = tabRow[Tab].gameObject;
            // The first item of the tab content (or the open tab) gets the selection: the pad / keyboard user lands where the
            // settings are. This screen owns the focus while open (start menu below does not take it back, review #136 P2-2).
            UiFocus.Push(this, FirstItem, false);
            RefreshAll();
            if (Confirm.Pending) OpenConfirm();   // rebuilt while the countdown runs (window resized by the new mode)
            else if (EventSystem.current != null) EventSystem.current.SetSelectedGameObject(FirstItem);
        }

        void BuildGraphics(ref float y)
        {
            var c = m_Content;
            Header(c, T.SectionDisplay, ref y);
            Stepper(c, ref y, T.Resolution, ResolutionLabel, StepResolution, null);
            Segments(c, ref y, T.WindowMode, T.WindowModeLabels,
                () => Array.IndexOf(WindowModes.All, Pending.display.mode), i => Pending.display.mode = WindowModes.All[i]);
            Segments(c, ref y, T.Vsync, T.OffOn, () => Pending.vsync ? 1 : 0, i => Pending.vsync = i == 1);
            Stepper(c, ref y, T.FpsCap, FpsLabel,
                d => Pending.fpsCap = PcSettingsData.FpsCaps[PcSettingsData.StepIndex(Math.Max(0, Array.IndexOf(PcSettingsData.FpsCaps, Pending.fpsCap)), d, PcSettingsData.FpsCaps.Length)],
                () => !Pending.vsync);
            y += 18f;
            Header(c, T.SectionGraphics, ref y);
            Stepper(c, ref y, T.Tier, TierLabel,
                d => Pending.graphicsTier = TierChoices.All[PcSettingsData.StepIndex(Math.Max(0, Array.IndexOf(TierChoices.All, Pending.graphicsTier)), d, TierChoices.All.Length)], null);
        }

        void BuildControls(ref float y)
        {
            var c = m_Content;
            Header(c, T.SectionControls, ref y);
            Note(c, ref y, T.ControlsNote);
            if (OpenControlSettings != null)
            {
                var b = TextButton(c, T.ControlsWheel, Vector2.zero, new Vector2(m_ColW, RowH - 8f), OpenControls);
                PlaceTop((RectTransform)b.transform, Pad, y, new Vector2(m_ColW, RowH - 8f));
                y += RowH;
                AddRow(b.GetComponent<Selectable>());
            }
            else Note(c, ref y, T.ControlsUnavailable);
            if (ControlSettingsPanel.OpenInputBindings != null)
            {
                var b = TextButton(c, T.ControlsBindings, Vector2.zero, new Vector2(m_ColW, RowH - 8f), () => ControlSettingsPanel.OpenInputBindings?.Invoke(transform));
                PlaceTop((RectTransform)b.transform, Pad, y, new Vector2(m_ColW, RowH - 8f));
                y += RowH;
                AddRow(b.GetComponent<Selectable>());
            }
        }

        /// <summary>Leaves for the wheel / pedal / camera panel: pending edits are applied first (never lost silently); a
        /// display change waits for its keep / revert answer.</summary>
        void OpenControls()
        {
            var open = OpenControlSettings;
            if (Dirty) Apply();
            if (Confirm.Pending) return;
            m_OnClose?.Invoke();
            Destroy(gameObject);
            open?.Invoke();
        }

        void BuildAudio(ref float y)
        {
            var c = m_Content;
            Header(c, T.SectionAudio, ref y);
            VolumeRow(c, ref y, T.VolumeMaster, () => Pending.volumes.master, v => Pending.volumes.master = v);
            VolumeRow(c, ref y, T.VolumeEngine, () => Pending.volumes.engine, v => Pending.volumes.engine = v);
            VolumeRow(c, ref y, T.VolumeAmbient, () => Pending.volumes.ambient, v => Pending.volumes.ambient = v);
            VolumeRow(c, ref y, T.VolumeUi, () => Pending.volumes.ui, v => Pending.volumes.ui = v);
        }

        void BuildGameplay(ref float y)
        {
            var c = m_Content;
            Header(c, T.SectionHud, ref y);
            Stepper(c, ref y, T.HudScale, () => Pct(Pending.hudScale),
                d => Pending.hudScale = PcSettingsData.Step(Pending.hudScale, d, PcSettingsData.HudScaleStep, PcSettingsData.HudScaleMin, PcSettingsData.HudScaleMax), null);
            Segments(c, ref y, T.HudDetail, T.HudDetailLabels, () => (int)m_HudPending.Detail, i => m_HudPending.Detail = (HudDetail)i);
            Note(c, ref y, T.HudDetailNote);
            Segments(c, ref y, T.CabHud, T.CabHudLabels, () => (int)m_HudPending.Cab, i => m_HudPending.Cab = (CabHudMode)i);
            Note(c, ref y, T.CabHudNote);
            y += 18f;
            Header(c, T.SectionInterface, ref y);
            Segments(c, ref y, T.TouchControls, T.TouchControlsLabels, () => (int)m_TouchPending, i => m_TouchPending = UiPreferences.ParseTouchControls(i));
            // Units: the HUD and the cab displays render km/h only (ADR 0270 section Jednostki) - shown, not editable.
            Stepper(c, ref y, T.Units, () => T.UnitsMetric, null, null);
        }

        void BuildMirrors(ref float y)
        {
            var c = m_Content;
            Header(c, T.SectionMirrorWindows, ref y);
            Segments(c, ref y, T.MirrorWindows, T.OffOn, () => m_MirrorsPending ? 1 : 0, i => m_MirrorsPending = i == 1);
            Func<bool> on = () => m_MirrorsPending;
            Stepper(c, ref y, T.MirrorSize, () => Pct(m_HudPending.MirrorSize),
                d => m_HudPending.MirrorSize = HudPrefsData.Step(m_HudPending.MirrorSize, d, HudPreferences.MirrorSizeStep, HudPreferences.MirrorSizeMin, HudPreferences.MirrorSizeMax), on);
            Stepper(c, ref y, T.MirrorDrop, () => Pct(m_HudPending.MirrorDrop),
                d => m_HudPending.MirrorDrop = HudPrefsData.Step(m_HudPending.MirrorDrop, d, 0.1f, 0f, 1f), on);
            Stepper(c, ref y, T.MirrorInset, () => Pct(m_HudPending.MirrorInset),
                d => m_HudPending.MirrorInset = HudPrefsData.Step(m_HudPending.MirrorInset, d, 0.1f, 0f, 1f), on);
            Preview(c, ref y);
            y += 18f;
            Header(c, T.SectionMirrorAdjust, ref y);
            Stepper(c, ref y, T.MirrorYaw, () => Deg(m_HudPending.MirrorYawOut),
                d => m_HudPending.MirrorYawOut = HudPrefsData.Step(m_HudPending.MirrorYawOut, d, HudPreferences.MirrorAngleStep, -HudPreferences.MirrorYawMax, HudPreferences.MirrorYawMax), null);
            Stepper(c, ref y, T.MirrorPitch, () => Deg(m_HudPending.MirrorPitchDown),
                d => m_HudPending.MirrorPitchDown = HudPrefsData.Step(m_HudPending.MirrorPitchDown, d, HudPreferences.MirrorAngleStep, -HudPreferences.MirrorPitchMax, HudPreferences.MirrorPitchMax), null);
            Note(c, ref y, T.MirrorNote);
        }

        /// <summary>Schematic 16:9 monitor with the strip and the two mirror windows where <see cref="DesktopHudLayout"/>
        /// puts them for the pending values (outline only, no picture).</summary>
        void Preview(RectTransform parent, ref float y)
        {
            const float pw = 480f, ph = 270f;
            var cap = Label(parent, "PreviewCaption", T.Preview, 20, TextAnchor.LowerLeft, P.InkMuted, Vector2.zero, new Vector2(m_ColW, 28f));
            PlaceTop(cap.rectTransform, Pad, y, new Vector2(m_ColW, 28f));
            y += 34f;
            var box = Rect("Preview", parent);
            PlaceTop(box, Pad + LabelW, y, new Vector2(pw, ph));
            box.gameObject.AddComponent<Image>().color = P.Row;
            var strip = PreviewRect(box, "Strip", P.GaugeTrack);
            var tell = PreviewRect(box, "Telltales", P.GaugeTrack);
            var ml = PreviewRect(box, "MirrorL", P.InkMuted);
            var mr = PreviewRect(box, "MirrorR", P.InkMuted);
            y += ph + 12f;
            m_Refresh.Add(() =>
            {
                var s = new DesktopHudInput
                {
                    Width = 2560f, Height = 1440f, Strip = true, Extended = m_HudPending.Detail == HudDetail.Extended,
                    MirrorLeft = m_MirrorsPending, MirrorRight = m_MirrorsPending, MirrorAspect = DesktopHudLayout.DefaultMirrorAspect,
                    MirrorSize = m_HudPending.MirrorSize, MirrorDrop = m_HudPending.MirrorDrop, MirrorInset = m_HudPending.MirrorInset,
                };
                DesktopHudLayout.Solve(s, out var r);
                float k = pw / 2560f;
                SetPreview(strip, r.Strip, k, r.ShowStrip);
                SetPreview(tell, r.Telltales, k, true);
                SetPreview(ml, r.MirrorLeft, k, r.ShowMirrorLeft);
                SetPreview(mr, r.MirrorRight, k, r.ShowMirrorRight);
            });
        }

        static RectTransform PreviewRect(RectTransform parent, string name, Color c)
        {
            var rt = Rect(name, parent);
            rt.anchorMin = rt.anchorMax = rt.pivot = Vector2.zero;
            var img = rt.gameObject.AddComponent<Image>();
            img.color = c; img.raycastTarget = false;
            return rt;
        }

        static void SetPreview(RectTransform rt, UnityEngine.Rect r, float k, bool on)
        {
            rt.anchoredPosition = new Vector2(r.x * k, r.y * k);
            rt.sizeDelta = new Vector2(r.width * k, r.height * k);
            if (rt.gameObject.activeSelf != on) rt.gameObject.SetActive(on);
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

        /// <summary>Signed degrees with the Polish decimal comma ("+1,5°").</summary>
        static string Deg(float v) => (v > 0.001f ? "+" : "") + v.ToString("0.0", CultureInfo.InvariantCulture).Replace('.', ',') + "°";

        void VolumeRow(RectTransform parent, ref float y, string label, Func<float> get, Action<float> set) =>
            Stepper(parent, ref y, label, () => Pct(get()), d => set(PcSettingsData.Step(get(), d, PcSettingsData.VolumeStep, 0f, 1f)), null);

        // ------------------------------------------------------------------ rows

        /// <summary>Section head: SemiBold, warm white, with a short amber mark - readable, not a pale caption.</summary>
        void Header(RectTransform parent, string text, ref float y)
        {
            var mark = Rect("Mark " + text, parent);
            PlaceTop(mark, Pad, y + 10f, new Vector2(6f, 26f));
            var mi = mark.gameObject.AddComponent<Image>(); mi.color = P.Accent; mi.raycastTarget = false;
            var l = Label(parent, "Header " + text, text, 24, TextAnchor.MiddleLeft, P.Ink, Vector2.zero, new Vector2(m_ColW - 18f, 44f), m_Strong);
            PlaceTop(l.rectTransform, Pad + 18f, y, new Vector2(m_ColW - 18f, 44f));
            y += 54f;
        }

        void Note(RectTransform parent, ref float y, string text)
        {
            var l = Label(parent, "Note", text, 21, TextAnchor.UpperLeft, P.InkMuted, Vector2.zero, new Vector2(m_ColW, 56f));
            l.horizontalOverflow = HorizontalWrapMode.Wrap;
            PlaceTop(l.rectTransform, Pad, y, new Vector2(m_ColW, 56f));
            y += 60f;
        }

        RectTransform Row(RectTransform parent, string label, ref float y)
        {
            var row = Rect("Row " + label, parent);
            PlaceTop(row, Pad, y, new Vector2(m_ColW, RowH - 8f));
            row.gameObject.AddComponent<Image>().color = P.Row;
            var l = Label(row, "Label", label, 26, TextAnchor.MiddleLeft, P.Ink, new Vector2(20f, 0f), new Vector2(LabelW - 20f, RowH - 8f));
            l.horizontalOverflow = HorizontalWrapMode.Wrap; l.resizeTextForBestFit = true; l.resizeTextMinSize = 18; l.resizeTextMaxSize = 26;
            y += RowH;
            return row;
        }

        void AddRow(params Selectable[] items)
        {
            m_Rows.Add(items);
            if (FirstItem == null && items.Length > 0) FirstItem = items[0].gameObject;
        }

        /// <summary>"Label   [−]  value  [+]"; <paramref name="step"/> null = read-only value; <paramref name="enabled"/> null = always.</summary>
        void Stepper(RectTransform parent, ref float y, string label, Func<string> value, Action<int> step, Func<bool> enabled)
        {
            var row = Row(parent, label, ref y);
            float bx = LabelW + 20f, bw = 76f, vw = m_ColW - bx - 2f * bw - 20f;
            var v = Label(row, "Value", "", 26, TextAnchor.MiddleCenter, P.Ink, new Vector2(bx + bw, 0f), new Vector2(vw, RowH - 8f), m_Strong);
            v.horizontalOverflow = HorizontalWrapMode.Wrap; v.resizeTextForBestFit = true; v.resizeTextMinSize = 18; v.resizeTextMaxSize = 26;
            if (step == null)
            {
                v.color = P.InkMuted; v.alignment = TextAnchor.MiddleRight; v.font = m_Font;
                Place(v.rectTransform, Vector2.zero, new Vector2(bx, 0f), new Vector2(m_ColW - bx - 20f, RowH - 8f));
                m_Refresh.Add(() => v.text = value());
                return;
            }
            var minus = TextButton(row, "−", new Vector2(bx, 6f), new Vector2(bw, RowH - 20f), () => { step(-1); RefreshAll(); }).GetComponent<Button>();
            var plus = TextButton(row, "+", new Vector2(m_ColW - bw - 12f, 6f), new Vector2(bw, RowH - 20f), () => { step(+1); RefreshAll(); }).GetComponent<Button>();
            AddRow(minus, plus);
            m_Refresh.Add(() =>
            {
                bool on = enabled == null || enabled();
                minus.interactable = plus.interactable = on;
                v.text = value(); v.color = on ? P.Ink : P.InkDisabled;
            });
        }

        void Segments(RectTransform parent, ref float y, string label, string[] names, Func<int> current, Action<int> set)
        {
            var row = Row(parent, label, ref y);
            float gap = 6f, x0 = LabelW + 20f, w = (m_ColW - x0 - 12f - gap * (names.Length - 1)) / names.Length;
            var imgs = new Image[names.Length];
            var texts = new Text[names.Length];
            var sel = new Selectable[names.Length];
            for (int i = 0; i < names.Length; i++)
            {
                int idx = i;
                var b = TextButton(row, names[i], new Vector2(x0 + i * (w + gap), 6f), new Vector2(w, RowH - 20f), () => { set(idx); RefreshAll(); }, 23);
                imgs[i] = b.GetComponent<Image>();
                texts[i] = b.GetComponentInChildren<Text>();
                sel[i] = b.GetComponent<Button>();
            }
            AddRow(sel);
            m_Refresh.Add(() =>
            {
                int c = current();
                for (int i = 0; i < imgs.Length; i++)
                {
                    bool on = i == c;
                    imgs[i].color = on ? P.SegmentOn : P.Button;
                    texts[i].color = on ? P.InkOnLight : P.Ink;
                    texts[i].font = on ? m_Strong : m_Font;
                }
            });
        }

        // ------------------------------------------------------------------ navigation + focus

        /// <summary>Explicit navigation: up / down to the nearest item of the previous / next row (by position in the row),
        /// left / right inside the row (tabs row first, footer last). No wrap.</summary>
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

        // ------------------------------------------------------------------ confirm dialog

        void OpenConfirm()
        {
            if (!Confirm.Pending) Confirm.Start();
            if (m_Dialog != null) Destroy(m_Dialog);
            var root = Rect("ConfirmDisplay", m_Safe);
            Stretch(root);
            root.gameObject.AddComponent<Image>().color = P.Scrim;
            m_Dialog = root.gameObject;
            var box = Rect("Box", root);
            box.anchorMin = box.anchorMax = box.pivot = new Vector2(0.5f, 0.5f);
            box.sizeDelta = new Vector2(820f, 300f);
            box.gameObject.AddComponent<Image>().color = P.Panel;
            var t = Label(box, "Title", T.ConfirmTitle, 34, TextAnchor.MiddleLeft, P.Ink, new Vector2(Pad, 200f), new Vector2(820f - 2f * Pad, 70f), m_Strong);
            t.horizontalOverflow = HorizontalWrapMode.Wrap;
            m_DialogCountdown = Label(box, "Countdown", "", 26, TextAnchor.MiddleLeft, P.Accent, new Vector2(Pad, 140f), new Vector2(820f - 2f * Pad, 50f));
            m_DialogCountdown.text = string.Format(CultureInfo.InvariantCulture, T.ConfirmCountdown, Confirm.SecondsLeft);
            float bw = 300f;
            var revert = TextButton(box, T.ConfirmRevert, new Vector2(820f - Pad - 2f * bw - 20f, 30f), new Vector2(bw, 72f), RevertDisplay).GetComponent<Button>();
            var keep = TextButton(box, T.ConfirmKeep, new Vector2(820f - Pad - bw, 30f), new Vector2(bw, 72f), KeepDisplay).GetComponent<Button>();
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

        // ------------------------------------------------------------------ helpers

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

        Text Label(Transform parent, string name, string text, int size, TextAnchor align, Color color, Vector2 bottomLeft, Vector2 box, Font font = null)
        {
            var rt = Rect(name, parent);
            Place(rt, Vector2.zero, bottomLeft, box);
            var t = rt.gameObject.AddComponent<Text>();
            t.font = font != null ? font : m_Font; t.fontSize = size; t.color = color; t.alignment = align; t.text = text;
            t.horizontalOverflow = HorizontalWrapMode.Overflow; t.verticalOverflow = VerticalWrapMode.Overflow;
            t.raycastTarget = false;
            return t;
        }

        GameObject TextButton(Transform parent, string text, Vector2 bottomLeft, Vector2 size, UnityEngine.Events.UnityAction onClick, int fontSize = 26)
        {
            var rt = Rect(text, parent);
            Place(rt, Vector2.zero, bottomLeft, size);
            var img = rt.gameObject.AddComponent<Image>();
            img.color = P.Button;
            var b = rt.gameObject.AddComponent<Button>();
            b.targetGraphic = img;
            b.onClick.AddListener(onClick);
            UiFocus.Decorate(b);   // amber frame = pad / keyboard focus, muted frame = mouse hover (ADR 0265)
            var l = Label(rt, "Label", text, fontSize, TextAnchor.MiddleCenter, P.Ink, Vector2.zero, size);
            l.horizontalOverflow = HorizontalWrapMode.Wrap; l.resizeTextForBestFit = true; l.resizeTextMinSize = 16; l.resizeTextMaxSize = fontSize;
            return rt.gameObject;
        }
    }
}
