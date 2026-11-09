using System;
using System.Collections.Generic;
using System.Globalization;
using Game.Controls;
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

        const float RowH = 76f, ColW = 700f;

        public ControlSettings Settings { get; private set; }
        Action m_OnChanged, m_OnClose, m_OnCalibrate;
        Font m_Font;
        RectTransform m_Safe;
        readonly List<Action> m_Refresh = new List<Action>();

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

        // ------------------------------------------------------------------ build

        void Build(Camera cam)
        {
            var canvas = gameObject.AddComponent<Canvas>();
            canvas.renderMode = cam != null ? RenderMode.ScreenSpaceCamera : RenderMode.ScreenSpaceOverlay;
            canvas.worldCamera = cam;
            canvas.planeDistance = cam != null ? Mathf.Max(cam.nearClipPlane * 2f, 0.12f) : 1f;
            canvas.sortingOrder = 1200;
            var scaler = gameObject.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 1f;
            gameObject.AddComponent<GraphicRaycaster>();
            m_Font = UiFonts.Default;

            var dim = Rect("Dim", transform);
            Stretch(dim);
            dim.gameObject.AddComponent<Image>().color = k_Dim;   // also swallows touches behind the panel

            m_Safe = Rect("SafeArea", transform);
            Stretch(m_Safe);
            ApplySafeArea();

            var panel = Rect("Panel", m_Safe);
            panel.anchorMin = panel.anchorMax = panel.pivot = new Vector2(0.5f, 0.5f);
            panel.sizeDelta = new Vector2(2 * ColW + 120f, 900f);
            panel.anchoredPosition = Vector2.zero;
            panel.gameObject.AddComponent<Image>().color = k_Panel;

            Label(panel, "Title", "USTAWIENIA STEROWANIA", 38, TextAnchor.MiddleLeft, k_Text, new Vector2(40f, 818f), new Vector2(900f, 60f));
            Label(panel, "Hint", "Zmiany działają od razu i zapisują się same.", 24, TextAnchor.MiddleRight, k_Muted, new Vector2(1000f, 818f), new Vector2(360f, 60f));

            float left = 40f, right = 40f + ColW + 40f, top = 800f;

            // Left column: wheel + pedals
            float y = top;
            Header(panel, "KIEROWNICA DOTYKOWA", left, ref y);
            Stepper(panel, left, ref y, "Zakres kierownicy", () => F0(Settings.wheelRangeDeg) + "°", d => Settings.wheelRangeDeg = Step(Settings.wheelRangeDeg, d, 90f, ControlSettings.RangeMin, ControlSettings.RangeMax));
            Stepper(panel, left, ref y, "Czułość", () => Pct(Settings.wheelSensitivity), d => Settings.wheelSensitivity = Step(Settings.wheelSensitivity, d, 0.1f, ControlSettings.GainMin, ControlSettings.GainMax));
            Stepper(panel, left, ref y, "Samocentrowanie", () => Settings.centreStrength <= 0.001f ? "wyłączone" : Pct(Settings.centreStrength), d => Settings.centreStrength = Step(Settings.centreStrength, d, 0.1f, ControlSettings.CentreMin, ControlSettings.CentreMax));
            Stepper(panel, left, ref y, "Martwa strefa", () => Pct(Settings.wheelDeadZone), d => Settings.wheelDeadZone = Step(Settings.wheelDeadZone, d, 0.01f, ControlSettings.DeadMin, ControlSettings.DeadMax));
            y -= 18f;
            Header(panel, "PEDAŁY", left, ref y);
            Segment(panel, left, ref y, "Krzywa gazu", "liniowa", "progresywna", () => Settings.throttleProgressive, v => Settings.throttleProgressive = v);
            Segment(panel, left, ref y, "Krzywa hamulca", "liniowa", "progresywna", () => Settings.brakeProgressive, v => Settings.brakeProgressive = v);

            // Right column: gyro
            y = top;
            Header(panel, "GYRO (PRZECHYŁ TELEFONU)", right, ref y);
            Segment(panel, right, ref y, "Sterowanie", "kierownica", "gyro", () => Settings.gyroEnabled, v => Settings.gyroEnabled = v);
            Segment(panel, right, ref y, "Kierunek", "normalny", "odwrócony", () => Settings.gyroInvert, v => Settings.gyroInvert = v);
            Stepper(panel, right, ref y, "Czułość gyro", () => Pct(Settings.gyroSensitivity), d => Settings.gyroSensitivity = Step(Settings.gyroSensitivity, d, 0.1f, ControlSettings.GainMin, ControlSettings.GainMax));
            Stepper(panel, right, ref y, "Pełny skręt przy przechyle", () => F0(Settings.GyroMaxTiltDeg) + "°", null);
            var calib = TextButton(panel, "Kalibruj", new Vector2(right, y - RowH), new Vector2(ColW, 64f), () => m_OnCalibrate?.Invoke());
            calib.GetComponent<Image>().color = k_Button;
            Label(panel, "CalibHint", "Trzymaj telefon tak, jak chcesz jechać prosto, i dotknij Kalibruj.", 22, TextAnchor.UpperLeft, k_Muted, new Vector2(right, y - RowH - 90f), new Vector2(ColW, 70f)).horizontalOverflow = HorizontalWrapMode.Wrap;

            // Footer
            TextButton(panel, "Przywróć domyślne", new Vector2(40f, 28f), new Vector2(420f, 72f), ResetToDefaults);
            var close = TextButton(panel, "Zamknij", new Vector2(2 * ColW + 120f - 40f - 320f, 28f), new Vector2(320f, 72f), Close);
            close.GetComponent<Image>().color = k_ButtonOn;

            if (UnityEngine.Object.FindAnyObjectByType<EventSystem>() == null)
                new GameObject("EventSystem", typeof(EventSystem)).AddComponent<InputSystemUIInputModule>().AssignDefaultActions();
            foreach (var r in m_Refresh) r();
        }

        void ApplySafeArea()
        {
            Rect sa = Screen.safeArea;
            if (Screen.width <= 0 || Screen.height <= 0) return;
            m_Safe.anchorMin = new Vector2(sa.xMin / Screen.width, sa.yMin / Screen.height);
            m_Safe.anchorMax = new Vector2(sa.xMax / Screen.width, sa.yMax / Screen.height);
            m_Safe.offsetMin = m_Safe.offsetMax = Vector2.zero;
        }

        void Header(RectTransform parent, string text, float x, ref float y)
        {
            Label(parent, "Header", text, 24, TextAnchor.LowerLeft, k_Amber, new Vector2(x, y - 40f), new Vector2(ColW, 40f));
            y -= 52f;
        }

        void Stepper(RectTransform parent, float x, ref float y, string label, Func<string> value, Action<int> step)
        {
            y -= RowH;
            var row = Rect("Row " + label, parent);
            Place(row, Vector2.zero, new Vector2(x, y), new Vector2(ColW, RowH - 8f));
            row.gameObject.AddComponent<Image>().color = k_Row;
            Label(row, "Label", label, 30, TextAnchor.MiddleLeft, k_Text, new Vector2(20f, 0f), new Vector2(330f, RowH - 8f));
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
            y -= RowH;
            var row = Rect("Row " + label, parent);
            Place(row, Vector2.zero, new Vector2(x, y), new Vector2(ColW, RowH - 8f));
            row.gameObject.AddComponent<Image>().color = k_Row;
            Label(row, "Label", label, 30, TextAnchor.MiddleLeft, k_Text, new Vector2(20f, 0f), new Vector2(250f, RowH - 8f));
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
