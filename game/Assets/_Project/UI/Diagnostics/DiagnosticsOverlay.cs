using System.Globalization;
using System.Text;
using Game.Core;
using Game.Platform;
using Game.Rendering;
using Game.Telemetry;
using Game.UI.CabDisplays;
using Game.UI.Layout;
using TMPro;
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
        TextMeshProUGUI m_Body;
        Text m_FpsButtonLabel;
        Text m_TierButtonLabel;
        Text m_HideButtonLabel;
        UiViewport m_View;
        float m_NextRefresh;
        string m_Header;
        readonly TextBuffer m_Buf = new TextBuffer(1024);

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

            // Text panel, top-left of the safe area.
            var panelRt = NewRect("Panel", m_SafeArea);
            m_Panel = panelRt.gameObject;
            panelRt.anchorMin = panelRt.anchorMax = panelRt.pivot = new Vector2(0f, 1f);
            panelRt.anchoredPosition = new Vector2(24f, -24f);
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
            m_Body = bodyRt.gameObject.AddComponent<TextMeshProUGUI>();
            m_Body.font = UiFonts.DefaultTmp;
            m_Body.fontSize = FontSize;
            m_Body.lineSpacing = 1.1f;
            m_Body.color = k_TextColor;
            m_Body.alignment = TextAlignmentOptions.TopLeft;
            m_Body.overflowMode = TextOverflowModes.Overflow;
            m_Body.raycastTarget = false;

            // Buttons column, top-right of the safe area.
            var buttons = NewRect("Buttons", m_SafeArea);
            buttons.anchorMin = buttons.anchorMax = buttons.pivot = new Vector2(1f, 1f);
            buttons.anchoredPosition = new Vector2(-24f, -24f);
            buttons.sizeDelta = new Vector2(300f, 0f);
            var col = buttons.gameObject.AddComponent<VerticalLayoutGroup>();
            col.spacing = 14f;
            col.childControlWidth = col.childControlHeight = true;
            col.childForceExpandWidth = true;
            col.childForceExpandHeight = false;
            buttons.gameObject.AddComponent<ContentSizeFitter>().verticalFit = ContentSizeFitter.FitMode.PreferredSize;

            m_FpsButtonLabel = NewButton(buttons, font, "FpsButton", () => { QualityTiers.ToggleFrameRate(); RefreshNow(); });
            m_TierButtonLabel = NewButton(buttons, font, "TierButton", () => { QualityTiers.Next(); RefreshNow(); });
            m_HideButtonLabel = NewButton(buttons, font, "HideButton", () => { m_Panel.SetActive(!m_Panel.activeSelf); RefreshNow(); });

            EnsureEventSystem();

            m_Header = BuildHeader();
            m_View.Refresh();
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
            var le = rt.gameObject.AddComponent<LayoutElement>();
            le.minHeight = le.preferredHeight = 84f;
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
            sb.Append("KAMION ").Append(b.ShortLabel);
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
            if (Time.unscaledTime >= m_NextRefresh) RefreshNow();
        }

        public void RefreshNow()
        {
            m_NextRefresh = Time.unscaledTime + RefreshInterval;
            if (m_Body == null) return;
            m_View.Refresh();
            var ci = CultureInfo.InvariantCulture;
            int targetFps = Application.targetFrameRate;
            m_FpsButtonLabel.text = targetFps > 0 ? $"Cel: {targetFps} FPS" : "Cel: auto";
            m_TierButtonLabel.text = "Jakość: " + QualityTiers.Current;
            m_HideButtonLabel.text = m_Panel.activeSelf ? "Ukryj" : "Diagnostyka";
            if (!m_Panel.activeSelf) return;

            var snap = m_Sampler != null ? m_Sampler.Snapshot : default;
            var f = snap.Frames;
            var sb = m_Buf;
            sb.Clear();
            sb.Append(m_Header).Append('\n');
            sb.Append("Screen: ").Append(Screen.width).Append('x').Append(Screen.height)
              .Append(" @ ").AppendFixed(Screen.currentResolution.refreshRateRatio.value, 0, false, '.').Append(" Hz")
              .Append("  ·  safe ").AppendFixed(Screen.safeArea.width, 0, false, '.').Append('x').AppendFixed(Screen.safeArea.height, 0, false, '.')
              .Append("  ·  quality ").Append(QualityTiers.Current)
              .Append("  ·  target ");
            if (targetFps > 0) sb.Append(targetFps); else sb.Append("auto");
            sb.Append(" fps\n");
            if (f.Samples > 0)
            {
                sb.Append("FPS ").AppendFixed(f.MeanFps, 1, false, '.')
                  .Append("   frame p50 ").AppendFixed(f.P50Ms, 1, false, '.')
                  .Append(" · p95 ").AppendFixed(f.P95Ms, 1, false, '.')
                  .Append(" · p99 ").AppendFixed(f.P99Ms, 1, false, '.')
                  .Append(" ms  (").Append(f.Samples).Append(" frames)\n");
            }
            else
            {
                sb.Append("FPS —   frame p50 — · p95 — · p99 — ms\n");
            }
            sb.Append("Battery ");
            if (snap.BatteryTempC.HasValue) sb.AppendFixed(snap.BatteryTempC.Value, 1, false, '.').Append(" °C"); else sb.Append("n/a");
            sb.Append("  ·  thermal ").Append(ThermalStatusNames.Get(snap.ThermalStatus))
              .Append("  ·  headroom ");
            if (snap.ThermalHeadroom.HasValue) sb.AppendFixed(snap.ThermalHeadroom.Value, 2, false, '.'); else sb.Append("n/a");
            sb.Append('\n');
            sb.Append("Memory: PSS ");
            if (snap.PssKb.HasValue) sb.Append(snap.PssKb.Value / 1024).Append(" MB"); else sb.Append("n/a");
            sb.Append("  ·  Unity alloc ").Append(snap.UnityAllocatedBytes >> 20)
              .Append(" / reserved ").Append(snap.UnityReservedBytes >> 20).Append(" MB")
              .Append("  ·  session ").AppendFixed(snap.SessionSeconds, 0, false, '.').Append(" s");
            m_Body.SetCharArray(sb.Chars, 0, sb.Length);   // zero-alloc: reused char buffer
        }
    }
}
