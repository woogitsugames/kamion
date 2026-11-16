using System.Globalization;
using System.Text;
using Game.Controls;
using Game.Core;
using Game.Platform;
using Game.Rendering;
using Game.Telemetry;
using Game.UI.Layout;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.UI;

namespace Game.UI
{
    /// <summary>
    /// Diagnostics overlay (uGUI, built in code — no prefab to keep in sync). Canvas is
    /// Screen Space - Camera so the editor visual-QA runner can capture it with Camera.Render.
    /// Layout stays inside Screen.safeArea (camera cutout / rounded corners).
    /// ADR 0276: the panel and the buttons are placed by <see cref="MenuOverlayLayout"/> together with the start menu
    /// (<see cref="MenuOverlayBoard"/>) - nothing covers the menu title or its buttons; without a menu the historic
    /// place (panel top-left, buttons top-right) is kept.
    /// </summary>
    public sealed class DiagnosticsOverlay : MonoBehaviour
    {
        const float RefreshInterval = 0.5f;
        const int FontSize = 30;
        static readonly Color k_PanelColor = new Color(0f, 0f, 0f, 0.62f);
        static readonly Color k_TextColor = new Color(0.96f, 0.96f, 0.92f, 1f);
        static readonly Color k_ButtonColor = new Color(0.16f, 0.17f, 0.18f, 0.85f);

        IPlatformServices m_Platform;
        DiagnosticsSampler m_Sampler;
        Canvas m_Canvas;
        RectTransform m_SafeArea;
        GameObject m_Panel;
        RectTransform m_PanelRt;
        readonly RectTransform[] m_ButtonRts = new RectTransform[MenuOverlayLayout.ButtonCount];
        bool m_UserShowPanel = true;
        MenuOverlayResult m_AppliedLayout;
        bool m_LayoutApplied;
        Text m_Body;
        Text m_FpsButtonLabel;
        Text m_TierButtonLabel;
        Text m_HideButtonLabel;
        UiViewport m_View;
        float m_NextRefresh;
        string m_Header;
        readonly StringBuilder m_Sb = new StringBuilder(1024);
        int m_LastFpsTarget = int.MinValue;
        int m_LastTierLevel = int.MinValue;
        string m_LastBody;
        bool? m_LastHideLabel;

        public static DiagnosticsOverlay Create(Camera camera, IPlatformServices platform, DiagnosticsSampler sampler)
        {
            var go = new GameObject("DiagnosticsOverlay");
            var overlay = go.AddComponent<DiagnosticsOverlay>();
            overlay.m_Platform = platform;
            overlay.m_Sampler = sampler;
            overlay.Build(camera);
            overlay.RefreshNow();
            return overlay;
        }

        /// <summary>Editor capture only: lay out against a fake safe area (normalized 0..1).</summary>
        public void OverrideSafeAreaNormalized(Rect normalized)
        {
            m_View.OverrideSafeAreaNormalized(normalized);
            m_View.Refresh();
        }

        void Build(Camera camera)
        {
            m_Canvas = gameObject.AddComponent<Canvas>();
            m_Canvas.renderMode = RenderMode.ScreenSpaceCamera;
            m_Canvas.worldCamera = camera;
            m_Canvas.planeDistance = camera != null ? Mathf.Max(camera.nearClipPlane * 2f, 0.5f) : 1f;
            m_Canvas.sortingOrder = 1000;
            gameObject.AddComponent<GraphicRaycaster>();

            var font = UiFonts.Default;

            m_View = new UiViewport(m_Canvas);   // scale by the shorter side / DPI + safe area (ADR 0079)
            m_SafeArea = m_View.SafeArea;

            // Text panel: top-left of the safe area unless the start menu needs the room (ADR 0276, ApplyLayout).
            var panelRt = NewRect("Panel", m_SafeArea);
            m_Panel = panelRt.gameObject;
            m_PanelRt = panelRt;
            panelRt.anchorMin = panelRt.anchorMax = new Vector2(0.5f, 0.5f);
            panelRt.pivot = new Vector2(0f, 1f);
            var bg = m_Panel.AddComponent<Image>();
            bg.color = k_PanelColor;
            bg.raycastTarget = false;
            var layout = m_Panel.AddComponent<VerticalLayoutGroup>();
            layout.padding = new RectOffset(22, 22, 16, 16);
            layout.childControlWidth = layout.childControlHeight = true;
            layout.childForceExpandWidth = layout.childForceExpandHeight = false;
            var fitter = m_Panel.AddComponent<ContentSizeFitter>();
            fitter.horizontalFit = ContentSizeFitter.FitMode.PreferredSize;
            fitter.verticalFit = ContentSizeFitter.FitMode.PreferredSize;

            var bodyRt = NewRect("Body", panelRt);
            m_Body = bodyRt.gameObject.AddComponent<Text>();
            m_Body.font = font;
            m_Body.fontSize = FontSize;
            m_Body.lineSpacing = 1.1f;
            m_Body.color = k_TextColor;
            m_Body.alignment = TextAnchor.UpperLeft;
            m_Body.horizontalOverflow = HorizontalWrapMode.Overflow;
            m_Body.verticalOverflow = VerticalWrapMode.Overflow;
            m_Body.raycastTarget = false;

            // Buttons: a column top-right, or a column / row in another right-hand corner while the start menu is open
            // (ADR 0276). Each button is placed by ApplyLayout (no layout group: the arrangement changes).
            var buttons = NewRect("Buttons", m_SafeArea);
            buttons.anchorMin = Vector2.zero; buttons.anchorMax = Vector2.one;
            buttons.offsetMin = buttons.offsetMax = Vector2.zero;

            m_FpsButtonLabel = NewButton(buttons, font, "FpsButton", () => { QualityTiers.ToggleFrameRate(); RefreshNow(); });
            m_TierButtonLabel = NewButton(buttons, font, "TierButton", () => { QualityTiers.Next(); RefreshNow(); });
            m_HideButtonLabel = NewButton(buttons, font, "HideButton", () => { m_UserShowPanel = !m_UserShowPanel; ApplyLayout(); RefreshNow(); });
            for (int i = 0; i < m_ButtonRts.Length; i++) m_ButtonRts[i] = (RectTransform)buttons.GetChild(i);

            EnsureEventSystem();

            m_Header = BuildHeader();
            m_View.Refresh();
            ApplyLayout();
        }

        void OnEnable() { MenuOverlayBoard.OverlayActive = true; m_LayoutApplied = false; }

        void OnDisable() => MenuOverlayBoard.OverlayActive = false;

        /// <summary>ADR 0276: publish the panel state, solve the shared layout with the start menu and apply it when it
        /// changed. Allocation-free (structs, cached RectTransforms); runs every frame.</summary>
        void ApplyLayout()
        {
            if (m_PanelRt == null) return;
            MenuOverlayBoard.OverlayActive = isActiveAndEnabled;
            MenuOverlayBoard.PanelShown = m_UserShowPanel;
            if (m_Panel.activeSelf)
                MenuOverlayBoard.PanelSize = MenuOverlayLayout.ReservePanel(MenuOverlayBoard.PanelSize, m_PanelRt.rect.size);
            MenuOverlayBoard.Solve(m_View.SizeUnits, out var r);
            if (m_LayoutApplied && r.SameAs(m_AppliedLayout)) return;
            m_LayoutApplied = true;
            m_AppliedLayout = r;

            bool show = r.Panel != OverlayPanelPlace.Collapsed;
            if (m_Panel.activeSelf != show) m_Panel.SetActive(show);
            if (show)
            {
                bool top = r.Panel == OverlayPanelPlace.TopLeft;
                m_PanelRt.pivot = new Vector2(0f, top ? 1f : 0f);
                m_PanelRt.anchoredPosition = new Vector2(r.PanelRect.xMin, top ? r.PanelRect.yMax : r.PanelRect.yMin);
            }
            for (int i = 0; i < m_ButtonRts.Length; i++)
            {
                var b = MenuOverlayLayout.ButtonRect(r.Buttons, r.ButtonsRect, MenuOverlayBoard.ButtonSize, MenuOverlayBoard.ButtonSpacing, i);
                var rt = m_ButtonRts[i];
                rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0.5f);
                rt.pivot = Vector2.zero;
                rt.anchoredPosition = b.position;
                rt.sizeDelta = b.size;
            }
        }

        static RectTransform NewRect(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.layer = 5; // UI
            var rt = (RectTransform)go.transform;
            rt.SetParent(parent, false);
            return rt;
        }

        static Text NewButton(RectTransform parent, Font font, string name, UnityEngine.Events.UnityAction onClick)
        {
            var rt = NewRect(name, parent);
            var img = rt.gameObject.AddComponent<Image>();
            img.color = k_ButtonColor;
            rt.sizeDelta = MenuOverlayBoard.ButtonSize;   // placed by ApplyLayout (ADR 0276)
            var button = rt.gameObject.AddComponent<Button>();
            button.targetGraphic = img;
            button.onClick.AddListener(onClick);

            var labelRt = NewRect("Label", rt);
            labelRt.anchorMin = Vector2.zero;
            labelRt.anchorMax = Vector2.one;
            labelRt.offsetMin = labelRt.offsetMax = Vector2.zero;
            var label = labelRt.gameObject.AddComponent<Text>();
            label.font = font;
            label.fontSize = FontSize;
            label.color = k_TextColor;
            label.alignment = TextAnchor.MiddleCenter;
            label.raycastTarget = false;
            return label;
        }

        static void EnsureEventSystem()
        {
            if (Object.FindAnyObjectByType<EventSystem>() != null) return;
            var go = new GameObject("EventSystem", typeof(EventSystem));
            var module = go.AddComponent<InputSystemUIInputModule>();
            module.AssignDefaultActions();
        }

        static string BuildHeader()
        {
            var b = BuildInfo.Current;
            var sb = new StringBuilder(512);
            sb.Append("KAMION ").Append(b.IdentityLabel);   // ADR 0276: git sha + content hash of the player data
            if (b.development) sb.Append(" DEV");
            sb.Append("  ·  Unity ").Append(b.unityVersion).Append('\n');
            sb.Append("Device: ").Append(SystemInfo.deviceModel)
              .Append("  ·  RAM ").Append(SystemInfo.systemMemorySize).Append(" MB")
              .Append("  ·  CPU ").Append(SystemInfo.processorCount).Append(" cores\n");
            sb.Append("GPU: ").Append(SystemInfo.graphicsDeviceName)
              .Append("  ·  ").Append(SystemInfo.graphicsDeviceVersion)
              .Append("  ·  VRAM ").Append(SystemInfo.graphicsMemorySize).Append(" MB");
            return sb.ToString();
        }

        void Update()
        {
            m_View.Refresh();
            ApplyLayout();
            if (Time.unscaledTime >= m_NextRefresh) RefreshNow();
        }

        public void RefreshNow()
        {
            m_NextRefresh = Time.unscaledTime + RefreshInterval;
            if (m_Body == null) return;
            m_View.Refresh();
            var ci = CultureInfo.InvariantCulture;
            int targetFps = Application.targetFrameRate;
            // Button labels update only when the displayed value changes (they allocated a formatted string every 0.5 s before, even with the panel hidden).
            if (targetFps != m_LastFpsTarget)
            {
                m_LastFpsTarget = targetFps;
                m_FpsButtonLabel.text = targetFps > 0 ? "Cel: " + targetFps + " FPS" : "Cel: auto";
            }
            // QualityTiers.Current reads QualitySettings.names (a new array each call): gate on the level index instead.
            int tierLevel = QualitySettings.GetQualityLevel();
            if (m_LastTierLevel != tierLevel)
            {
                m_LastTierLevel = tierLevel;
                m_TierButtonLabel.text = "Jakość: " + QualityTiers.Current;
            }
            bool hidden = !m_UserShowPanel;
            if (m_LastHideLabel != hidden)
            {
                m_LastHideLabel = hidden;
                m_HideButtonLabel.text = hidden ? "Diagnostyka" : "Ukryj";
            }
            if (!m_Panel.activeSelf) return;

            var snap = m_Sampler != null ? m_Sampler.Snapshot : default;
            var f = snap.Frames;
            var sb = m_Sb;
            sb.Clear();
            sb.Append(m_Header).Append('\n');
            sb.Append("Screen: ").Append(Screen.width).Append('x').Append(Screen.height)
              .Append(" @ ").Append(Screen.currentResolution.refreshRateRatio.value.ToString("F0", ci)).Append(" Hz")
              .Append("  ·  safe ").Append(Screen.safeArea.width.ToString("F0", ci)).Append('x').Append(Screen.safeArea.height.ToString("F0", ci))
              .Append("  ·  quality ").Append(QualityTiers.Current)
              .Append("  ·  target ").Append(targetFps > 0 ? targetFps.ToString(ci) : "auto").Append(" fps\n");
            if (f.Samples > 0)
            {
                sb.Append("FPS ").Append(f.MeanFps.ToString("F1", ci))
                  .Append("   frame p50 ").Append(f.P50Ms.ToString("F1", ci))
                  .Append(" · p95 ").Append(f.P95Ms.ToString("F1", ci))
                  .Append(" · p99 ").Append(f.P99Ms.ToString("F1", ci))
                  .Append(" ms  (").Append(f.Samples).Append(" frames)\n");
            }
            else
            {
                sb.Append("FPS —   frame p50 — · p95 — · p99 — ms\n");
            }
            sb.Append("Battery ").Append(snap.BatteryTempC.HasValue ? snap.BatteryTempC.Value.ToString("F1", ci) + " °C" : "n/a")
              .Append("  ·  thermal ").Append(ThermalStatusNames.Get(snap.ThermalStatus))
              .Append("  ·  headroom ").Append(snap.ThermalHeadroom.HasValue ? snap.ThermalHeadroom.Value.ToString("F2", ci) : "n/a").Append('\n');
            sb.Append("Memory: PSS ").Append(snap.PssKb.HasValue ? (snap.PssKb.Value / 1024).ToString(ci) + " MB" : "n/a")
              .Append("  ·  Unity alloc ").Append((snap.UnityAllocatedBytes >> 20).ToString(ci))
              .Append(" / reserved ").Append((snap.UnityReservedBytes >> 20).ToString(ci)).Append(" MB")
              .Append("  ·  session ").Append(snap.SessionSeconds.ToString("F0", ci)).Append(" s");
            if (!SbEquals(sb, m_LastBody)) { m_LastBody = sb.ToString(); m_Body.text = m_LastBody; }
        }

        /// <summary>Char-by-char comparison of a StringBuilder with a string — no allocation; Text.text is set only when the displayed content changed.</summary>
        static bool SbEquals(StringBuilder sb, string s)
        {
            if (s == null || sb.Length != s.Length) return false;
            for (int i = 0; i < sb.Length; i++) if (sb[i] != s[i]) return false;
            return true;
        }
    }
}
