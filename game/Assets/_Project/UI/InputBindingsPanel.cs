using System;
using System.Collections.Generic;
using System.Globalization;
using Game.Controls;
using Game.UI.Layout;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Game.UI
{
    /// <summary>
    /// Keyboard and gamepad bindings screen (ADR 0264), same flat dark-panel language as <see cref="ControlSettingsPanel"/>
    /// (no icons, no maker button glyphs: pad controls are named by position, <see cref="DrivingActionCatalog.GamepadControlLabel"/>).
    /// Two pages (Klawiatura / Pad): feel steppers on top, then one row per action with its bindings; a binding button
    /// starts interactive rebinding (Backspace or the pad's middle-right button cancels, 10 s timeout). Every change is
    /// saved at once through the callbacks. Closes itself when its owner (the settings panel) is destroyed.
    /// Focus (ADR 0265, review #131 P2-1): while open it is the top <see cref="UiFocus"/> owner, so the settings panel
    /// below does not take the pad selection back; the screen itself is pointer-operated - its buttons never take the
    /// pad / keyboard selection, because a key or pad press here is a new binding, not navigation (Enter / pad A must
    /// not click the selected button again while it is being bound).
    /// Not in the driving loop: allocation is fine here.
    /// </summary>
    public sealed class InputBindingsPanel : MonoBehaviour
    {
        static readonly Color k_Dim = new Color(0.02f, 0.025f, 0.03f, 0.80f);
        static readonly Color k_Panel = new Color(0.06f, 0.065f, 0.07f, 0.98f);
        static readonly Color k_Row = new Color(1f, 1f, 1f, 0.045f);
        static readonly Color k_Button = new Color(0.16f, 0.17f, 0.18f, 0.95f);
        static readonly Color k_ButtonOn = new Color(0.30f, 0.36f, 0.30f, 0.95f);
        static readonly Color k_Text = new Color(0.95f, 0.95f, 0.91f, 1f);
        static readonly Color k_Muted = new Color(0.70f, 0.70f, 0.67f, 1f);
        static readonly Color k_Amber = new Color(0.95f, 0.66f, 0.18f, 1f);

        const float RowH = 62f, Pad = 36f, Edge = 20f, HeaderH = 150f, FooterH = 108f, MaxW = 1500f;

        DrivingActions m_Actions;
        InputBindingsStore m_Store;
        PadKeyboardFeel m_Feel;
        Action m_Save, m_TuningChanged;
        Transform m_Owner;
        Font m_Font;
        UiViewport m_View;
        RectTransform m_Safe;
        bool m_GamepadPage;
        string m_Status = "";
        InputActionRebindingExtensions.RebindingOperation m_Op;
        InputAction m_OpAction;
        int m_OpIndex = -1;
        bool m_Closing;
        readonly List<Action> m_Refresh = new List<Action>();

        public RectTransform PanelRect { get; private set; }

        /// <summary>
        /// Opens the screen. <paramref name="save"/> writes the overrides (after a rebind / reset);
        /// <paramref name="tuningChanged"/> applies and writes <see cref="InputBindingsStore.Tuning"/>.
        /// </summary>
        public static InputBindingsPanel Create(Transform owner, DrivingActions actions, InputBindingsStore store, PadKeyboardFeel feel, Action save, Action tuningChanged)
        {
            var go = new GameObject("InputBindingsPanel");
            var p = go.AddComponent<InputBindingsPanel>();
            p.m_Owner = owner; p.m_Actions = actions; p.m_Store = store; p.m_Feel = feel ?? PadKeyboardFeel.Defaults();
            p.m_Save = save; p.m_TuningChanged = tuningChanged;
            p.m_GamepadPage = Gamepad.current != null && Keyboard.current == null;
            p.Build();
            return p;
        }

        public void Close()
        {
            m_Closing = true;
            CancelRebind();
            Destroy(gameObject);
        }

        void OnDestroy() { m_Closing = true; CancelRebind(); UiFocus.Pop(this, true); }   // the selection returns to the settings panel

        /// <summary>Becomes the top focus owner with nothing selected (see the class summary).</summary>
        void TakeFocus()
        {
            UiFocus.Push(this, null, false);
            var es = EventSystem.current;
            if (es == null) return;
            es.firstSelectedGameObject = null;   // navigation with nothing selected must not pick an item of the panel below
            es.SetSelectedGameObject(null);
        }

        void CancelRebind()
        {
            if (m_Op == null) return;
            var op = m_Op; m_Op = null; m_OpAction = null; m_OpIndex = -1;
            op.Cancel();   // OnCancel re-enables the map and disposes
        }

        void Build()
        {
            var canvas = gameObject.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 1300;   // above the settings panel (1200)
            gameObject.AddComponent<GraphicRaycaster>();
            m_Font = UiFonts.Default;
            var dim = Rect("Dim", transform);
            dim.anchorMin = Vector2.zero; dim.anchorMax = Vector2.one; dim.offsetMin = dim.offsetMax = Vector2.zero;
            dim.gameObject.AddComponent<Image>().color = k_Dim;
            m_View = new UiViewport(canvas);
            m_Safe = m_View.SafeArea;
            m_View.Refresh();
            BuildContent();
            TakeFocus();
        }

        void Update()
        {
            if (m_Owner == null) { Close(); return; }   // settings panel closed (Escape / back)
            if (!UiFocus.IsTop(this)) TakeFocus();      // the settings panel below was laid out again (window resized) and pushed itself
            if (m_View != null && m_View.Refresh()) BuildContent();
        }

        void BuildContent()
        {
            for (int i = m_Safe.childCount - 1; i >= 0; i--)
            {
                var c = m_Safe.GetChild(i);
                c.SetParent(null, false);
                Destroy(c.gameObject);
            }
            m_Refresh.Clear();

            Vector2 avail = m_View.SizeUnits - new Vector2(2f * Edge, 2f * Edge);
            float panelW = Mathf.Min(MaxW, avail.x);
            float colW = panelW - 2f * Pad;
            var panel = Rect("Panel", m_Safe);
            PanelRect = panel;
            panel.anchorMin = panel.anchorMax = panel.pivot = new Vector2(0.5f, 0.5f);
            panel.gameObject.AddComponent<Image>().color = k_Panel;

            var viewport = Rect("Viewport", panel);
            viewport.anchorMin = Vector2.zero; viewport.anchorMax = Vector2.one;
            viewport.offsetMin = new Vector2(0f, FooterH); viewport.offsetMax = new Vector2(0f, -HeaderH);
            viewport.gameObject.AddComponent<Image>().color = new Color(0, 0, 0, 0);
            viewport.gameObject.AddComponent<RectMask2D>();
            var content = Rect("Content", viewport);
            content.anchorMin = new Vector2(0f, 1f); content.anchorMax = new Vector2(1f, 1f); content.pivot = new Vector2(0.5f, 1f);

            float y = 0f;
            var set = m_GamepadPage ? m_Actions.Gamepad : m_Actions.Keyboard;
            if (m_GamepadPage)
            {
                Header(content, "CZUŁOŚĆ PADA", colW, ref y);
                Stepper(content, colW, ref y, "Martwa strefa gałki", () => Pct(m_Store.Tuning.StickDeadZone),
                    d => m_Store.Tuning.StickDeadZone = ControlSettingsPanel.Step(m_Store.Tuning.StickDeadZone, d, 0.02f, PadUserTuning.DeadZoneMin, PadUserTuning.DeadZoneMax));
                Stepper(content, colW, ref y, "Krzywa gałki (1 = liniowa)", () => m_Store.Tuning.StickExponent.ToString("F1", CultureInfo.InvariantCulture),
                    d => m_Store.Tuning.StickExponent = ControlSettingsPanel.Step(m_Store.Tuning.StickExponent, d, 0.1f, PadUserTuning.ExponentMin, PadUserTuning.ExponentMax));
                Stepper(content, colW, ref y, "Skręt przy prędkości", () => Pct(m_Store.Tuning.SpeedLimitScale),
                    d => m_Store.Tuning.SpeedLimitScale = ControlSettingsPanel.Step(m_Store.Tuning.SpeedLimitScale, d, 0.1f, PadUserTuning.SpeedLimitMin, PadUserTuning.SpeedLimitMax));
            }
            else
            {
                Header(content, "CZUŁOŚĆ KLAWIATURY", colW, ref y);
                Stepper(content, colW, ref y, "Szybkość skrętu", () => Pct(m_Store.Tuning.KeySteerScale),
                    d => m_Store.Tuning.KeySteerScale = ControlSettingsPanel.Step(m_Store.Tuning.KeySteerScale, d, 0.1f, PadUserTuning.KeySpeedMin, PadUserTuning.KeySpeedMax));
                Stepper(content, colW, ref y, "Skręt przy prędkości", () => Pct(m_Store.Tuning.SpeedLimitScale),
                    d => m_Store.Tuning.SpeedLimitScale = ControlSettingsPanel.Step(m_Store.Tuning.SpeedLimitScale, d, 0.1f, PadUserTuning.SpeedLimitMin, PadUserTuning.SpeedLimitMax));
            }
            y += 14f;
            Header(content, "PRZYPISANIA", colW, ref y);
            foreach (var def in DrivingActionCatalog.All)
            {
                if (!def.Visible) continue;
                var action = set.Map.FindAction(def.Name, true);
                BindingRow(content, colW, ref y, def, action);
            }

            float contentH = y + 8f;
            float panelH = Mathf.Min(avail.y, HeaderH + contentH + FooterH);
            panel.sizeDelta = new Vector2(panelW, panelH);
            content.sizeDelta = new Vector2(0f, contentH);
            var scroll = viewport.gameObject.AddComponent<ScrollRect>();
            scroll.viewport = viewport; scroll.content = content;
            scroll.horizontal = false; scroll.vertical = contentH > panelH - HeaderH - FooterH + 0.5f;
            scroll.movementType = ScrollRect.MovementType.Clamped;
            scroll.scrollSensitivity = 40f;

            // ---- title + page switch + status
            var title = Label(panel, "Title", "KLAWIATURA I PAD", 38, TextAnchor.MiddleLeft, k_Text);
            TopBand(title.rectTransform, Pad, Pad + 460f, 14f, 60f);
            float segW = 210f;
            var bk = TextButton(panel, "Klawiatura", () => { m_GamepadPage = false; BuildContent(); });
            TopRight((RectTransform)bk.transform, Pad + segW + 12f, 18f, new Vector2(segW, 56f));
            var bp = TextButton(panel, "Pad", () => { m_GamepadPage = true; BuildContent(); });
            TopRight((RectTransform)bp.transform, Pad, 18f, new Vector2(segW, 56f));
            bk.GetComponent<Image>().color = m_GamepadPage ? k_Button : k_ButtonOn;
            bp.GetComponent<Image>().color = m_GamepadPage ? k_ButtonOn : k_Button;
            var status = Label(panel, "Status", "", 24, TextAnchor.MiddleLeft, k_Muted);
            TopBand(status.rectTransform, Pad, Pad, 84f, 52f);
            status.horizontalOverflow = HorizontalWrapMode.Wrap;
            m_Refresh.Add(() =>
            {
                status.text = m_Status.Length > 0 ? m_Status
                    : m_GamepadPage ? (Gamepad.current == null ? "Pad niepodłączony. Przypisania zapiszą się i zadziałają po podłączeniu." : "Kliknij przypisanie i naciśnij przycisk pada.")
                    : "Kliknij przypisanie i naciśnij klawisz. Escape jest zarezerwowany dla menu.";
                status.color = m_Status.StartsWith("Uwaga", StringComparison.Ordinal) ? k_Amber : k_Muted;
            });

            // ---- footer
            float inner = panelW - 2f * Pad;
            float closeW = Mathf.Min(320f, inner * 0.42f), resetW = Mathf.Min(460f, inner - closeW - 20f);
            var reset = TextButton(panel, "Przywróć domyślne", ResetToDefaults);
            Place((RectTransform)reset.transform, new Vector2(Pad, 20f), new Vector2(resetW, 72f));
            var close = TextButton(panel, "Zamknij", Close);
            Place((RectTransform)close.transform, new Vector2(panelW - Pad - closeW, 20f), new Vector2(closeW, 72f));
            close.GetComponent<Image>().color = k_ButtonOn;

            foreach (var r in m_Refresh) r();
        }

        /// <summary>Resets the bindings of the current page's device and the tuning to the shipped values.</summary>
        public void ResetToDefaults()
        {
            CancelRebind();
            (m_GamepadPage ? m_Actions.Gamepad : m_Actions.Keyboard).Map.RemoveAllBindingOverrides();
            var d = PadUserTuning.From(m_Feel);
            if (m_GamepadPage) { m_Store.Tuning.StickDeadZone = d.StickDeadZone; m_Store.Tuning.StickExponent = d.StickExponent; }
            else m_Store.Tuning.KeySteerScale = d.KeySteerScale;
            m_Store.Tuning.SpeedLimitScale = d.SpeedLimitScale;
            m_Status = m_GamepadPage ? "Przywrócono domyślne ustawienia pada." : "Przywrócono domyślne ustawienia klawiatury.";
            m_TuningChanged?.Invoke();   // also saves the overrides
            BuildContent();
        }

        void BindingRow(RectTransform parent, float colW, ref float y, DrivingActionDef def, InputAction action)
        {
            var row = Row(parent, def.LabelPl, colW, ref y, 420f);
            var bindings = action.bindings;
            // Buttons for the leaf bindings (composite parts are listed with their part: "w lewo" / "w prawo").
            int count = 0;
            for (int i = 0; i < bindings.Count; i++) if (!bindings[i].isComposite) count++;
            float x0 = 440f, w = Mathf.Max(120f, (colW - x0 - 12f - 8f * (count - 1)) / Mathf.Max(1, count));
            int n = 0;
            for (int i = 0; i < bindings.Count; i++)
            {
                if (bindings[i].isComposite) continue;
                int index = i;
                var b = TextButton(row, "", () => BeginRebind(action, index));
                Place((RectTransform)b.transform, new Vector2(x0 + n * (w + 8f), 6f), new Vector2(w, RowH - 20f));
                var label = b.GetComponentInChildren<Text>();
                label.fontSize = 24;
                m_Refresh.Add(() => label.text = BindingText(action, index));
                n++;
            }
        }

        string BindingText(InputAction action, int index)
        {
            var b = action.bindings[index];
            if (m_OpAction == action && m_OpIndex == index) return "…";
            string part = b.isPartOfComposite ? (b.name == "negative" || b.name == "Negative" ? "w lewo: " : "w prawo: ") : "";
            string path = b.effectivePath;
            if (string.IsNullOrEmpty(path)) return part + "—";
            if (m_GamepadPage) return part + DrivingActionCatalog.GamepadControlLabel(path);
            string s = action.GetBindingDisplayString(index, InputBinding.DisplayStringOptions.DontIncludeInteractions);
            return part + (string.IsNullOrEmpty(s) ? path : s);
        }

        void BeginRebind(InputAction action, int index)
        {
            CancelRebind();
            m_Status = m_GamepadPage ? "Naciśnij przycisk pada (środkowy prawy = anuluj)…" : "Naciśnij klawisz (Backspace = anuluj)…";
            m_OpAction = action; m_OpIndex = index;
            m_Op = m_Actions.StartRebind(action, index, m_GamepadPage, changed =>
            {
                m_Op = null; m_OpAction = null; m_OpIndex = -1;
                if (changed) m_Save?.Invoke();   // saved even when the screen is closing
                if (m_Closing) return;
                if (changed)
                {
                    string path = action.bindings[index].effectivePath;
                    string other = DrivingActions.FindConflict(action.actionMap, path, action, index);
                    var otherDef = other != null ? DrivingActionCatalog.Find(other) : null;
                    m_Status = otherDef != null ? "Uwaga: to samo przypisanie ma też „" + otherDef.LabelPl + "”." : "Zapisano.";
                }
                else m_Status = "Anulowano.";
                foreach (var r in m_Refresh) r();
            });
            foreach (var r in m_Refresh) r();
        }

        // ------------------------------------------------------------------ widgets (same look as ControlSettingsPanel)

        void Header(RectTransform parent, string text, float colW, ref float y)
        {
            var l = Label(parent, "Header", text, 24, TextAnchor.LowerLeft, k_Amber);
            PlaceTop(l.rectTransform, Pad, y, new Vector2(colW, 40f));
            y += 50f;
        }

        RectTransform Row(RectTransform parent, string label, float colW, ref float y, float labelW)
        {
            var row = Rect("Row " + label, parent);
            PlaceTop(row, Pad, y, new Vector2(colW, RowH - 8f));
            row.gameObject.AddComponent<Image>().color = k_Row;
            var l = Label(row, "Label", label, 28, TextAnchor.MiddleLeft, k_Text);
            Place(l.rectTransform, new Vector2(20f, 0f), new Vector2(labelW, RowH - 8f));
            y += RowH;
            return row;
        }

        void Stepper(RectTransform parent, float colW, ref float y, string label, Func<string> value, Action<int> step)
        {
            var row = Row(parent, label, colW, ref y, 520f);
            var v = Label(row, "Value", "", 28, TextAnchor.MiddleCenter, k_Text);
            Place(v.rectTransform, new Vector2(colW - 300f, 0f), new Vector2(120f, RowH - 8f));
            var minus = TextButton(row, "−", () => { step(-1); TuningEdited(); });
            Place((RectTransform)minus.transform, new Vector2(colW - 400f, 6f), new Vector2(80f, RowH - 20f));
            var plus = TextButton(row, "+", () => { step(+1); TuningEdited(); });
            Place((RectTransform)plus.transform, new Vector2(colW - 92f, 6f), new Vector2(80f, RowH - 20f));
            m_Refresh.Add(() => v.text = value());
        }

        void TuningEdited()
        {
            m_Store.Tuning.Clamp(PadUserTuning.From(m_Feel));
            m_TuningChanged?.Invoke();
            foreach (var r in m_Refresh) r();
        }

        static string Pct(float v) => Mathf.RoundToInt(v * 100f).ToString(CultureInfo.InvariantCulture) + "%";

        static RectTransform Rect(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform)) { layer = 5 };
            var rt = (RectTransform)go.transform;
            rt.SetParent(parent, false);
            return rt;
        }

        static void Place(RectTransform rt, Vector2 bottomLeft, Vector2 size)
        {
            rt.anchorMin = rt.anchorMax = rt.pivot = Vector2.zero; rt.anchoredPosition = bottomLeft; rt.sizeDelta = size;
        }

        static void PlaceTop(RectTransform rt, float x, float yFromTop, Vector2 size)
        {
            rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(0f, 1f);
            rt.anchoredPosition = new Vector2(x, -yFromTop);
            rt.sizeDelta = size;
        }

        static void TopRight(RectTransform rt, float rightInset, float topInset, Vector2 size)
        {
            rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(1f, 1f);
            rt.anchoredPosition = new Vector2(-rightInset, -topInset);
            rt.sizeDelta = size;
        }

        static void TopBand(RectTransform rt, float leftInset, float rightInset, float topInset, float height)
        {
            rt.anchorMin = new Vector2(0f, 1f); rt.anchorMax = new Vector2(1f, 1f); rt.pivot = new Vector2(0.5f, 1f);
            rt.offsetMin = new Vector2(leftInset, -topInset - height); rt.offsetMax = new Vector2(-rightInset, -topInset);
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

        GameObject TextButton(Transform parent, string text, UnityEngine.Events.UnityAction onClick)
        {
            var rt = Rect(string.IsNullOrEmpty(text) ? "Binding" : text, parent);
            var img = rt.gameObject.AddComponent<Image>();
            img.color = k_Button;
            var b = rt.gameObject.AddComponent<Button>();
            b.targetGraphic = img;
            b.onClick.AddListener(onClick);
            UiFocus.PointerOnly(b);   // hover frame, no pad / keyboard selection (also not by a click)
            var l = Label(rt, "Label", text, 28, TextAnchor.MiddleCenter, k_Text);
            l.rectTransform.anchorMin = Vector2.zero; l.rectTransform.anchorMax = Vector2.one;
            l.rectTransform.offsetMin = l.rectTransform.offsetMax = Vector2.zero;
            return rt.gameObject;
        }
    }
}
