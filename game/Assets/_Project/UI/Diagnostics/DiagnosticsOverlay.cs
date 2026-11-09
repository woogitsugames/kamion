using System.Globalization;
using System.Text;
using Game.Core;
using Game.Platform;
using Game.Rendering;
using Game.Telemetry;
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
        Text m_Body;
        Text m_FpsButtonLabel;
        Text m_TierButtonLabel;
        Text m_HideButtonLabel;
        Rect m_AppliedSafeArea;
        Vector2Int m_AppliedScreen;
        Rect? m_SafeAreaOverride;
        float m_NextRefresh;
        string m_Header;
        readonly StringBuilder m_Sb = new StringBuilder(1024);

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
            m_SafeAreaOverride = normalized;
            ApplySafeArea();
        }

        void Build(Camera camera)
        {
            m_Canvas = gameObject.AddComponent<Canvas>();
            m_Canvas.renderMode = RenderMode.ScreenSpaceCamera;
            m_Canvas.worldCamera = camera;
            m_Canvas.planeDistance = camera != null ? Mathf.Max(camera.nearClipPlane * 2f, 0.5f) : 1f;
            m_Canvas.sortingOrder = 1000;
            var scaler = gameObject.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 1f; // landscape: scale by height
            gameObject.AddComponent<GraphicRaycaster>();

            var font = UiFonts.Default;

            m_SafeArea = NewRect("SafeArea", transform);
            m_SafeArea.anchorMin = Vector2.zero;
            m_SafeArea.anchorMax = Vector2.one;
            m_SafeArea.offsetMin = m_SafeArea.offsetMax = Vector2.zero;

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
            m_Body = bodyRt.gameObject.AddComponent<Text>();
            m_Body.font = font;
            m_Body.fontSize = FontSize;
            m_Body.lineSpacing = 1.1f;
            m_Body.color = k_TextColor;
            m_Body.alignment = TextAnchor.UpperLeft;
            m_Body.horizontalOverflow = HorizontalWrapMode.Overflow;
            m_Body.verticalOverflow = VerticalWrapMode.Overflow;
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
            ApplySafeArea();
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
            ApplySafeArea();
            if (Time.unscaledTime >= m_NextRefresh) RefreshNow();
        }

        void ApplySafeArea()
        {
            if (m_SafeArea == null) return;
            Rect n;
            if (m_SafeAreaOverride.HasValue)
            {
                n = m_SafeAreaOverride.Value;
            }
            else
            {
                var screen = new Vector2Int(Screen.width, Screen.height);
                var safe = Screen.safeArea;
                if (safe == m_AppliedSafeArea && screen == m_AppliedScreen) return;
                m_AppliedSafeArea = safe;
                m_AppliedScreen = screen;
                if (screen.x <= 0 || screen.y <= 0) return;
                n = new Rect(safe.x / screen.x, safe.y / screen.y, safe.width / screen.x, safe.height / screen.y);
            }
            m_SafeArea.anchorMin = n.min;
            m_SafeArea.anchorMax = n.max;
            m_SafeArea.offsetMin = m_SafeArea.offsetMax = Vector2.zero;
        }

        public void RefreshNow()
        {
            m_NextRefresh = Time.unscaledTime + RefreshInterval;
            if (m_Body == null) return;
            var ci = CultureInfo.InvariantCulture;
            int targetFps = Application.targetFrameRate;
            m_FpsButtonLabel.text = targetFps > 0 ? $"Cel: {targetFps} FPS" : "Cel: auto";
            m_TierButtonLabel.text = "Jakość: " + QualityTiers.Current;
            m_HideButtonLabel.text = m_Panel.activeSelf ? "Ukryj" : "Diagnostyka";
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
            m_Body.text = sb.ToString();
        }
    }
}
