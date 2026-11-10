using System;
using System.Globalization;
using System.Text;
using Game.Cameras;
using Game.Controls;
using Game.Telemetry;
using Game.UI.Layout;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.UI;

namespace Game.UI.Driving
{
    /// <summary>Everything the driving HUD talks to. Any field may be null (visual-QA preview).</summary>
    public sealed class DrivingHudContext
    {
        public VehicleBody Vehicle;
        public TouchSteeringWheel Wheel;
        public TouchControls Touch;
        public GyroSteering Gyro;
        public CameraRig Rig;
        public VehicleTelemetryRecorder Recorder;
        public DiagnosticsSampler Sampler;
        public DriverInputMixer Mixer;
        public Func<bool> IsGyroMode;
        public Action ToggleSteeringMode, ToggleWheelRange, ResetVehicle, OpenMenu, OpenSettings;
        public Func<string> StatusLine;
        /// <summary>Developer diagnostics (status/autopilot/coupling lines) visible at start. Default off; launch argument devhud=1 or the four-finger hold toggles it.</summary>
        public bool DevDiagnostics;

        // ---- Stage 2 (lab actions; the stalk, coupling and landing-gear buttons go through TouchControls) ----
        /// <summary>Respawn: 0 solo (trailer parked in the coupling bay), 1 empty, 2 24 t cargo, 3 40 t gross.</summary>
        public Action<int> Spawn;
        public Func<int> CurrentSpawn;
        public Action ToggleAbsFault;
        public Func<bool> AbsFault;
        /// <summary>Endurance-brake stalk position (0 off, 1 engine brake, 2.. retarder stages) and its maximum.</summary>
        public Func<int> RetarderLever;
        public int RetarderLeverMax = 5;
        /// <summary>Brake-cruise set speed [km/h], 0 = off.</summary>
        public Func<float> BrakeCruiseKmh;
        /// <summary>One line about the trailer (coupled / parked, jaw-to-kingpin guide), empty without a trailer.</summary>
        public Func<string> CouplingStatus;
        /// <summary>Turn-signal lever (0 off, -1 left, +1 right, 2 hazard) and the flasher phase, for the lit buttons.</summary>
        public Func<int> TurnSignalLever;
        public Func<bool> TurnSignalLit;
        /// <summary>Texture of the active reversing camera, or null when the view is hidden.</summary>
        public Func<Texture> ReverseCameraTexture;
        public Func<string> ReverseCameraLabel;
        /// <summary>Main-mirror render textures shown as insets in the cab view (null = hidden).</summary>
        public Func<Texture> LeftMirrorTexture, RightMirrorTexture;
        public Action ToggleMirrorInsets;
        public Func<bool> MirrorInsets;
    }

    /// <summary>
    /// Driving HUD (uGUI built in code; Screen Space - Camera for visual-QA captures, Overlay at runtime).
    /// Adaptive layout (ADR 0079): every group is a zone placed by <see cref="HudLayout"/> from the safe-area size
    /// in canvas units (<see cref="UiViewport"/>: scale by the shorter side and DPI), solved again whenever the
    /// screen changes (rotation, folding a foldable) or the HUD state changes - zones never overlap, from 1:1 to 21:9.
    /// Left thumb = steering wheel (or gyro calibrate), turn signals above it, endurance-brake stalk (0 / engine
    /// brake / retarder R1–R4) + brake cruise beside it; right thumb = brake + throttle pedals with the gear
    /// selector (R N D, + − A/M, parking brake) beside them; top centre = one truck-style cluster (speed, gear, rpm,
    /// parking brake, ABS / STOP / engine brake / retarder lamps, both service-circuit pressures) flanked by the
    /// mirror insets, with the parking-brake warning and the reversing view below; top right = ONE developer
    /// button whose panel (camera, steering mode, menu, settings, telemetry, record, reset, lab, coupling, landing
    /// gear) drops down and collapses again; top left = telemetry panel (developer).
    /// Calm palette (dark translucent panels, off-white text, muted accent) — no neon, no glass effects.
    /// </summary>
    public sealed class DrivingHud : MonoBehaviour
    {
        const int Font = 30, SmallFont = 22;
        static readonly Color k_PedalPanel = new Color(0.06f, 0.065f, 0.07f, 0.97f);
        static readonly Color k_Panel = new Color(0.06f, 0.065f, 0.07f, 0.88f);
        static readonly Color k_Button = new Color(0.16f, 0.17f, 0.18f, 0.95f);
        static readonly Color k_TurnLit = new Color(0.30f, 0.52f, 0.28f, 0.95f);   // ISO 2575 green telltale family
        static readonly Color k_ButtonOn = new Color(0.30f, 0.36f, 0.30f, 0.92f);
        static readonly Color k_Text = new Color(0.95f, 0.95f, 0.91f, 1f);
        static readonly Color k_Muted = new Color(0.70f, 0.70f, 0.67f, 1f);
        static readonly Color k_Amber = new Color(0.95f, 0.66f, 0.18f, 1f);
        static readonly Color k_ParkOn = new Color(0.66f, 0.17f, 0.14f, 0.97f);
        static readonly Color k_Red = new Color(0.86f, 0.25f, 0.20f, 1f);
        static readonly Color k_ThrottleFill = new Color(0.45f, 0.62f, 0.45f, 0.85f);
        static readonly Color k_BrakeFill = new Color(0.72f, 0.30f, 0.26f, 0.85f);

        DrivingHudContext m_Ctx;
        Font m_Font;
        RectTransform m_SafeArea;
        UiViewport m_View;
        HudLayoutInput m_In;
        HudLayoutResult m_L;
        bool m_LayoutValid, m_DevOpen, m_LabOpen;
        RectTransform m_ClusterRt, m_ParkWarnRt, m_ReverseRt, m_DevToggleRt, m_DevPanelRt, m_LabRt, m_TelemetryRt, m_WheelRt, m_GyroRt,
            m_TurnRt, m_StalkRt, m_BrakeRt, m_ThrottleRt, m_GearsRt, m_DevTextRt;
        Text m_DevToggleLabel;
        Image m_DevToggleImage;

        GameObject m_WheelGo, m_GyroGo, m_TelemetryPanel, m_LabPanel, m_ReversePanel;
        Text m_Coupling, m_ReverseLabel, m_LampAbs, m_LampStop, m_LampEb, m_LampRet, m_Air1, m_Air2, m_CruiseLabel, m_AbsFaultLabel;
        Image m_Air1Bar, m_Air2Bar;
        RawImage m_ReverseImage, m_MirrorL, m_MirrorR;
        GameObject m_MirrorLGo, m_MirrorRGo;
        Text m_MirrorInsetLabel;
        readonly Image[] m_StalkCells = new Image[6];
        readonly Image[] m_SpawnBtns = new Image[4];
        Image m_CruiseBtn;
        Image m_TurnLeftBtn, m_TurnRightBtn, m_HazardBtn;
        int m_LastAir1 = int.MinValue, m_LastAir2 = int.MinValue;
        static readonly string[] k_AirStrings = BuildAirStrings();
        static readonly string[] k_CruiseStrings = BuildCruiseStrings();
        const string k_CruiseOff = "Zjazd\nwył.";
        Text m_ParkWarn;
        CanvasGroup m_ParkWarnGroup;
        ParkingBrakeWarningTracker m_ParkWarnTracker;
        float m_LastParkWarnAlpha = -1f;
        Text m_Speed, m_Gear, m_Rpm, m_Park, m_Status, m_Telemetry, m_GyroLabel;
        Text m_CamLabel, m_SteerLabel, m_TelLabel, m_RecLabel;
        Image m_RpmBar, m_RecImage, m_DriveBtn, m_NeutralBtn, m_ReverseBtn, m_ParkBtn, m_ManualBtn;
        int m_LastSpeed = int.MinValue, m_LastRpmBucket = int.MinValue;
        string m_LastGear;
        float m_NextTelemetry;
        readonly StringBuilder m_Sb = new StringBuilder(2048);
        static readonly string[] k_SpeedStrings = BuildNumbers(200);

        /// <summary>Developer diagnostic text (status line, coupling line). Off by default in every build; toggled by launch argument
        /// devhud=1 (context) or by holding four fingers on the screen for 0.8 s.</summary>
        public bool DevDiagnostics { get; private set; }
        float m_MultiTouchSince = -1f;
        bool m_MultiTouchLatched;

        public void SetDevDiagnostics(bool on)
        {
            DevDiagnostics = on;
            if (m_Status != null) m_Status.gameObject.SetActive(on);
            if (m_Coupling != null) m_Coupling.gameObject.SetActive(on && TelemetryVisible);
        }

        void PollDevGesture()
        {
            var ts = UnityEngine.InputSystem.Touchscreen.current;
            int n = 0;
            if (ts != null)
                foreach (var t in ts.touches) if (t.press.isPressed) n++;
            if (n >= 4)
            {
                if (m_MultiTouchSince < 0f) m_MultiTouchSince = Time.unscaledTime;
                else if (!m_MultiTouchLatched && Time.unscaledTime - m_MultiTouchSince >= 0.8f) { m_MultiTouchLatched = true; SetDevDiagnostics(!DevDiagnostics); }
            }
            else { m_MultiTouchSince = -1f; m_MultiTouchLatched = false; }
        }

        public bool TelemetryVisible => m_TelemetryPanel != null && m_TelemetryPanel.activeSelf;

        /// <param name="overlay">Screen Space - Overlay (runtime: always on top, no camera dependency); false = Screen
        /// Space - Camera, needed for visual-QA captures with Camera.Render.</param>
        public static DrivingHud Create(Camera cam, DrivingHudContext ctx, bool overlay = false)
        {
            var go = new GameObject("DrivingHud");
            var hud = go.AddComponent<DrivingHud>();
            hud.m_Ctx = ctx ?? new DrivingHudContext();
            hud.Build(overlay ? null : cam);
            return hud;
        }

        /// <summary>Editor capture only: lay out against a fake safe area (normalized).</summary>
        public void OverrideSafeAreaNormalized(Rect n) { m_View.OverrideSafeAreaNormalized(n); UpdateLayout(); }

        /// <summary>Tests / captures: lay out for a device screen (pixels, safe area in pixels, DPI; 0 = unknown). The
        /// canvas camera must render at the same pixel size.</summary>
        public void OverrideScreen(Vector2 pixelSize, Rect safeAreaPx, float dpi) { m_View.OverrideScreen(pixelSize, safeAreaPx, dpi); UpdateLayout(); }

        public void SetTelemetryVisible(bool on)
        {
            if (m_TelemetryPanel != null) m_TelemetryPanel.SetActive(on);
            // The coupling diagnostics line (kingpin offset, articulation, legs) is telemetry: hidden by default.
            if (m_Coupling != null) m_Coupling.gameObject.SetActive(on && DevDiagnostics);
            RefreshLabels();
            UpdateLayout();
        }

        // ------------------------------------------------------------------ build

        void Build(Camera cam)
        {
            var canvas = gameObject.AddComponent<Canvas>();
            canvas.renderMode = cam != null ? RenderMode.ScreenSpaceCamera : RenderMode.ScreenSpaceOverlay;
            canvas.worldCamera = cam;
            canvas.planeDistance = cam != null ? Mathf.Max(cam.nearClipPlane * 2f, 0.12f) : 1f;
            canvas.sortingOrder = 900;
            gameObject.AddComponent<GraphicRaycaster>();
            m_Font = UiFonts.Default;

            // Look pad first (behind everything) and full screen, not limited to the safe area.
            var look = Rect("LookPad", transform);
            Stretch(look);
            look.gameObject.AddComponent<Image>().color = new Color(0, 0, 0, 0);
            var lp = look.gameObject.AddComponent<LookPadWidget>();
            lp.onDrag = d => m_Ctx.Rig?.AddLookDelta(d);
            lp.onZoom = z => m_Ctx.Rig?.AddZoom(z);

            m_View = new UiViewport(canvas);   // scale by the shorter side / DPI + safe area (ADR 0079)
            m_SafeArea = m_View.SafeArea;

            BuildCluster();
            BuildCentreColumn();
            BuildTelemetryPanel();
            BuildWheel();
            BuildGyroPanel();
            BuildLeftControls();
            BuildPedalsAndGears();
            BuildDevPanel();
            BuildDevText();
            EnsureEventSystem();
            RefreshLabels();
            RefreshNow();
        }

        /// <summary>Zone root: a rect the layout solver positions (bottom-left anchored in the safe area).</summary>
        RectTransform Zone(string name, Vector2 size)
        {
            var rt = Rect(name, m_SafeArea);
            Place(rt, Vector2.zero, Vector2.zero, size);
            return rt;
        }

        RectTransform ZonePanel(string name, Vector2 size)
        {
            var rt = Zone(name, size);
            var img = rt.gameObject.AddComponent<Image>();
            img.color = k_Panel;
            img.raycastTarget = false;
            return rt;
        }

        /// <summary>Instrument cluster, one compact panel: speed / gear / parking brake / rpm on top, warning lamps and
        /// both service-circuit pressures in a strip below (a truck display, not two stacked game panels).</summary>
        void BuildCluster()
        {
            var p = ZonePanel("Readout", HudLayout.ClusterSize);
            m_ClusterRt = p;
            m_Speed = Label(p, "Speed", "0", 66, TextAnchor.MiddleRight, new Vector2(8f, 72f), new Vector2(150f, 80f));
            Label(p, "Unit", "km/h", 20, TextAnchor.LowerLeft, new Vector2(166f, 112f), new Vector2(70f, 28f)).color = k_Muted;
            m_Rpm = Label(p, "Rpm", "600 obr/min", 18, TextAnchor.LowerLeft, new Vector2(166f, 80f), new Vector2(130f, 26f));
            m_Rpm.color = k_Muted;
            m_Gear = Label(p, "Gear", "N", 50, TextAnchor.MiddleCenter, new Vector2(290f, 76f), new Vector2(92f, 72f));
            m_Park = Label(p, "Park", "(P)", 30, TextAnchor.MiddleCenter, new Vector2(380f, 80f), new Vector2(56f, 64f));
            m_Park.color = k_Red;
            var barBg = Rect("RpmBg", p);
            Place(barBg, Vector2.zero, new Vector2(12f, 60f), new Vector2(416f, 8f));
            var bbi = barBg.gameObject.AddComponent<Image>(); bbi.color = new Color(1f, 1f, 1f, 0.12f); bbi.raycastTarget = false;
            var bar = Rect("RpmBar", barBg);
            bar.anchorMin = Vector2.zero; bar.anchorMax = new Vector2(0f, 1f); bar.offsetMin = bar.offsetMax = Vector2.zero;
            m_RpmBar = bar.gameObject.AddComponent<Image>();
            m_RpmBar.color = k_Muted; m_RpmBar.raycastTarget = false;
            for (int r = 500; r < 2100; r += 500)
            {
                var tick = Rect("RpmTick" + r, barBg);
                float u = r / 2100f;
                tick.anchorMin = new Vector2(u, -0.4f); tick.anchorMax = new Vector2(u, 1.4f);
                tick.offsetMin = new Vector2(-1f, 0f); tick.offsetMax = new Vector2(1f, 0f);
                var ti = tick.gameObject.AddComponent<Image>(); ti.color = new Color(1f, 1f, 1f, 0.55f); ti.raycastTarget = false;
            }
            // ---- warning strip (bottom 52 units of the cluster)
            var sep = Rect("Separator", p);
            Place(sep, Vector2.zero, new Vector2(12f, 51f), new Vector2(416f, 1f));
            var si = sep.gameObject.AddComponent<Image>(); si.color = new Color(1f, 1f, 1f, 0.10f); si.raycastTarget = false;
            m_LampAbs = Lamp(p, "ABS", 8f);
            m_LampStop = Lamp(p, "STOP", 66f);
            m_LampEb = Lamp(p, "HS", 124f);
            m_LampRet = Lamp(p, "RET", 182f);
            m_Air1 = Label(p, "Air1", "— bar", 18, TextAnchor.MiddleLeft, new Vector2(252f, 16f), new Vector2(86f, 30f));
            m_Air2 = Label(p, "Air2", "— bar", 18, TextAnchor.MiddleLeft, new Vector2(346f, 16f), new Vector2(86f, 30f));
            m_Air1Bar = Bar(p, "Air1Bar", new Vector2(252f, 9f));
            m_Air2Bar = Bar(p, "Air2Bar", new Vector2(346f, 9f));
        }

        /// <summary>Under the cluster: parking-brake drive-away warning, reversing view; beside it: the mirror insets.</summary>
        void BuildCentreColumn()
        {
            // P applied, D/R + throttle: red text under the cluster, fades ~1 s after it clears.
            var pw = ZonePanel("ParkWarn", HudLayout.ParkWarnSize);
            m_ParkWarnRt = pw;
            pw.GetComponent<Image>().color = new Color(0.40f, 0.10f, 0.09f, 0.94f);
            m_ParkWarn = Label(pw, "Text", "Hamulec postojowy!", 26, TextAnchor.MiddleCenter, Vector2.zero, HudLayout.ParkWarnSize);
            m_ParkWarnGroup = pw.gameObject.AddComponent<CanvasGroup>();
            m_ParkWarnGroup.alpha = 0f; m_ParkWarnGroup.blocksRaycasts = false; m_ParkWarnGroup.interactable = false;

            m_MirrorL = MirrorInset("MirrorInsetL", out m_MirrorLGo);
            m_MirrorR = MirrorInset("MirrorInsetR", out m_MirrorRGo);

            var rev = ZonePanel("ReverseView", HudLayout.ReverseSize);
            m_ReverseRt = rev;
            var imgRt = Rect("Image", rev);
            imgRt.anchorMin = Vector2.zero; imgRt.anchorMax = Vector2.one; imgRt.offsetMin = new Vector2(5f, 5f); imgRt.offsetMax = new Vector2(-5f, -5f);
            m_ReverseImage = imgRt.gameObject.AddComponent<RawImage>();
            m_ReverseImage.raycastTarget = false;
            var labelBg = Rect("LabelBg", rev);
            Place(labelBg, Vector2.zero, new Vector2(5f, HudLayout.ReverseSize.y - 5f - 30f), new Vector2(300f, 30f));
            var lbi = labelBg.gameObject.AddComponent<Image>();
            lbi.color = k_Panel; lbi.raycastTarget = false;
            m_ReverseLabel = Label(rev, "Label", "KAMERA COFANIA", 17, TextAnchor.MiddleLeft, new Vector2(14f, HudLayout.ReverseSize.y - 5f - 30f), new Vector2(290f, 30f));
            m_ReversePanel = rev.gameObject;
            m_ReversePanel.SetActive(false);
        }

        void BuildTelemetryPanel()
        {
            var p = ZonePanel("Telemetry", new Vector2(HudLayout.TelemetryMaxWidth, 440f));
            m_TelemetryRt = p;
            m_TelemetryPanel = p.gameObject;
            m_Telemetry = Label(p, "Body", "", 20, TextAnchor.UpperLeft, Vector2.zero, Vector2.zero);
            var rt = m_Telemetry.rectTransform;
            rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = new Vector2(14f, 10f); rt.offsetMax = new Vector2(-14f, -10f);
            // The panel width follows the free column: long lines wrap, nothing spills over the cluster or the mirrors.
            m_Telemetry.horizontalOverflow = HorizontalWrapMode.Wrap;
            m_Telemetry.verticalOverflow = VerticalWrapMode.Truncate;
            m_TelemetryPanel.SetActive(false);
        }

        void BuildWheel()
        {
            var root = Zone("SteeringWheel", new Vector2(HudLayout.WheelSize, HudLayout.WheelSize));
            m_WheelRt = root;
            var hit = root.gameObject.AddComponent<Image>();
            hit.color = new Color(0, 0, 0, 0); // touch target = full square
            var rot = Rect("Rotating", root);
            Stretch(rot);
            var img = rot.gameObject.AddComponent<Image>();
            img.sprite = WheelSprite();
            img.color = new Color(0.55f, 0.58f, 0.60f, 0.34f);   // toned down (visual review r2): a guide, not a disc over the road
            img.raycastTarget = false;
            var w = root.gameObject.AddComponent<SteeringWheelWidget>();
            w.wheel = m_Ctx.Wheel;
            w.rotating = rot;
            m_WheelGo = root.gameObject;
        }

        void BuildGyroPanel()
        {
            var p = ZonePanel("Gyro", HudLayout.GyroSize);
            m_GyroRt = p;
            m_GyroLabel = Label(p, "Tilt", "Gyro", Font, TextAnchor.MiddleCenter, new Vector2(10f, 120f), new Vector2(380f, 100f));
            Button(p, "Calibrate", Vector2.zero, new Vector2(20f, 18f), new Vector2(360f, 88f), 26, () => m_Ctx.Gyro?.Calibrate(), out _).text = "Kalibruj (trzymaj prosto)";
            m_GyroGo = p.gameObject;
            m_GyroGo.SetActive(false);
        }

        static readonly string[] k_StalkLabels = { "0", "HS", "R1", "R2", "R3", "R4" };

        /// <summary>Turn signals above the wheel (lit with the flasher; self-cancel like a stalk) and the endurance-brake
        /// stalk + brake cruise beside it.</summary>
        void BuildLeftControls()
        {
            var turn = Zone("TurnSignals", HudLayout.TurnSignalsSize);
            m_TurnRt = turn;
            float th = HudLayout.TurnSignalsSize.y;
            Button(turn, "TurnLeft", Vector2.zero, new Vector2(0f, 0f), new Vector2(124f, th), 30, () => m_Ctx.Touch?.RequestTurnSignal(TurnSignalRequest.Left), out m_TurnLeftBtn).text = "←";
            Button(turn, "Hazard", Vector2.zero, new Vector2(132f, 0f), new Vector2(136f, th), 24, () => m_Ctx.Touch?.RequestTurnSignal(TurnSignalRequest.Hazard), out m_HazardBtn).text = "AWAR.";
            Button(turn, "TurnRight", Vector2.zero, new Vector2(276f, 0f), new Vector2(124f, th), 30, () => m_Ctx.Touch?.RequestTurnSignal(TurnSignalRequest.Right), out m_TurnRightBtn).text = "→";

            var stalk = Zone("Stalk", HudLayout.StalkSize);
            m_StalkRt = stalk;
            float sw = HudLayout.StalkSize.x;
            const float ch = 44f, pitch = 48f;
            for (int i = 0; i < k_StalkLabels.Length; i++)
            {
                int stage = i;
                float y = (k_StalkLabels.Length - 1 - i) * pitch;
                Button(stalk, "Stalk" + k_StalkLabels[i], Vector2.zero, new Vector2(0f, y), new Vector2(sw, ch), 24,
                    () => { if (m_Ctx.Touch != null && m_Ctx.RetarderLever != null) m_Ctx.Touch.RequestRetarderStep(stage - m_Ctx.RetarderLever()); }, out m_StalkCells[i]).text = k_StalkLabels[i];
            }
            float cy = k_StalkLabels.Length * pitch + 4f;
            m_CruiseLabel = Button(stalk, "Cruise", Vector2.zero, new Vector2(0f, cy), new Vector2(sw, 52f), 18,
                () => m_Ctx.Touch?.RequestBrakeCruiseToggle(), out m_CruiseBtn);
            var titleBg = Rect("TitleBg", stalk);
            Place(titleBg, Vector2.zero, new Vector2(0f, cy + 56f), new Vector2(sw, 28f));
            var tbi = titleBg.gameObject.AddComponent<Image>(); tbi.color = k_PedalPanel; tbi.raycastTarget = false;   // legible on any background
            Label(stalk, "Title", "Zwalniacz", 18, TextAnchor.MiddleCenter, new Vector2(0f, cy + 56f), new Vector2(sw, 28f)).color = k_Text;
        }

        /// <summary>Pedals at the right edge, gear selector beside them (R N D / + − A/M, parking brake below): the whole
        /// group stays as low as the throttle pedal instead of stacking two button rows over the road.</summary>
        void BuildPedalsAndGears()
        {
            m_BrakeRt = PedalRect("Brake", HudLayout.BrakeSize, k_BrakeFill, "HAMULEC", v => { if (m_Ctx.Touch != null) m_Ctx.Touch.BrakeRaw = v; });
            m_ThrottleRt = PedalRect("Throttle", HudLayout.ThrottleSize, k_ThrottleFill, "GAZ", v => { if (m_Ctx.Touch != null) m_Ctx.Touch.ThrottleRaw = v; });
            var g = Zone("Gears", HudLayout.GearsSize);
            m_GearsRt = g;
            const float bw = 100f, bh = 76f, pitch = 84f, x2 = 108f;
            float y0 = HudLayout.GearsSize.y - bh;
            Button(g, "R", Vector2.zero, new Vector2(0f, y0), new Vector2(bw, bh), 30, () => m_Ctx.Touch?.RequestSelector(SelectorRequest.Reverse), out m_ReverseBtn).text = "R";
            Button(g, "N", Vector2.zero, new Vector2(0f, y0 - pitch), new Vector2(bw, bh), 30, () => m_Ctx.Touch?.RequestSelector(SelectorRequest.Neutral), out m_NeutralBtn).text = "N";
            Button(g, "D", Vector2.zero, new Vector2(0f, y0 - 2 * pitch), new Vector2(bw, bh), 30, () => m_Ctx.Touch?.RequestSelector(SelectorRequest.Drive), out m_DriveBtn).text = "D";
            Button(g, "ShiftUp", Vector2.zero, new Vector2(x2, y0), new Vector2(bw, bh), 30, () => m_Ctx.Touch?.RequestShift(+1), out _).text = "+";
            Button(g, "ShiftDown", Vector2.zero, new Vector2(x2, y0 - pitch), new Vector2(bw, bh), 30, () => m_Ctx.Touch?.RequestShift(-1), out _).text = "−";
            Button(g, "Manual", Vector2.zero, new Vector2(x2, y0 - 2 * pitch), new Vector2(bw, bh), 30, () => m_Ctx.Touch?.RequestManualToggle(), out m_ManualBtn).text = "A/M";
            Button(g, "Park", Vector2.zero, Vector2.zero, new Vector2(HudLayout.GearsSize.x, bh), 26, () => m_Ctx.Touch?.RequestParkingToggle(), out m_ParkBtn).text = "(P)  <size=17>POSTOJOWY</size>";
        }

        /// <summary>Developer panel (D39: stays in the APK): ONE button top right; the camera / steering / menu / settings /
        /// telemetry / record / reset / lab / coupling / landing-gear buttons drop down under it and collapse again, so
        /// they never sit over the mirrors, the cluster or the road while driving. The lab page (spawn presets, ABS fault,
        /// reversing camera, mirror insets) replaces the grid in the same place.</summary>
        void BuildDevPanel()
        {
            m_DevToggleLabel = Button(m_SafeArea, "DevToggle", Vector2.zero, Vector2.zero, HudLayout.DevToggleSize, 24, () => SetDevPanelOpen(!m_DevOpen), out m_DevToggleImage);
            m_DevToggleRt = (RectTransform)m_DevToggleImage.transform;
            m_DevToggleLabel.text = "Panel";

            const float bw = 200f, bh = 66f, pad = 8f, pitchX = 208f, pitchY = 74f;
            var grid = ZonePanel("DevPanel", HudLayout.DevPanelSize);
            grid.GetComponent<Image>().raycastTarget = true;   // touches on the panel do not turn the camera
            m_DevPanelRt = grid;
            float y0 = HudLayout.DevPanelSize.y - pad - bh;
            Vector2 P(int col, int row) => new Vector2(pad + col * pitchX, y0 - row * pitchY);
            var sz = new Vector2(bw, bh);
            m_CamLabel = Button(grid, "Camera", Vector2.zero, P(0, 0), sz, 24, () => { m_Ctx.Rig?.NextMode(); RefreshLabels(); }, out _);
            m_SteerLabel = Button(grid, "SteerMode", Vector2.zero, P(1, 0), sz, 24, () => { m_Ctx.ToggleSteeringMode?.Invoke(); RefreshLabels(); }, out _);
            Button(grid, "Menu", Vector2.zero, P(0, 1), sz, 24, () => m_Ctx.OpenMenu?.Invoke(), out _).text = "Menu";
            Button(grid, "Settings", Vector2.zero, P(1, 1), sz, 24, () => { SetDevPanelOpen(false); m_Ctx.OpenSettings?.Invoke(); }, out _).text = "Ustawienia";
            m_TelLabel = Button(grid, "Telemetry", Vector2.zero, P(0, 2), sz, 24, () => SetTelemetryVisible(!TelemetryVisible), out _);
            m_RecLabel = Button(grid, "Record", Vector2.zero, P(1, 2), sz, 24, () => { m_Ctx.Recorder?.Toggle(); RefreshLabels(); }, out m_RecImage);
            Button(grid, "Reset", Vector2.zero, P(0, 3), sz, 24, () => m_Ctx.ResetVehicle?.Invoke(), out _).text = "Reset";
            Button(grid, "Lab", Vector2.zero, P(1, 3), sz, 24, () => SetLabOpen(true), out _).text = "Zestaw…";
            Button(grid, "Couple", Vector2.zero, P(0, 4), sz, 24, () => m_Ctx.Touch?.RequestCouplingToggle(), out _).text = "Siodło";
            Button(grid, "Legs", Vector2.zero, P(1, 4), sz, 24, () => m_Ctx.Touch?.RequestLandingGearToggle(), out _).text = "Nogi ↑↓";

            // ---- lab page (spawn presets, ABS fault, reversing camera, mirror insets)
            var lab = ZonePanel("LabPanel", HudLayout.DevPanelSize);
            lab.GetComponent<Image>().raycastTarget = true;
            m_LabRt = lab;
            float full = HudLayout.DevPanelSize.x - 2 * pad;
            Label(lab, "Title", "Start zestawu (reset pozycji)", 20, TextAnchor.MiddleLeft, new Vector2(pad + 4f, HudLayout.DevPanelSize.y - pad - 30f), new Vector2(full, 30f)).color = k_Muted;
            string[] names = { "Solo", "Pusta", "24 t", "40 t" };
            float sbw = (full - 3 * pad) / 4f, ly = HudLayout.DevPanelSize.y - pad - 30f - pad - bh;
            for (int i = 0; i < 4; i++)
            {
                int idx = i;
                Button(lab, "Spawn" + i, Vector2.zero, new Vector2(pad + i * (sbw + pad), ly), new Vector2(sbw, bh), 24, () => { m_Ctx.Spawn?.Invoke(idx); SetLabOpen(false); }, out m_SpawnBtns[i]).text = names[i];
            }
            m_AbsFaultLabel = Button(lab, "AbsFault", Vector2.zero, new Vector2(pad, ly - pitchY), sz, 22, () => m_Ctx.ToggleAbsFault?.Invoke(), out _);
            Button(lab, "RevCam", Vector2.zero, new Vector2(pad + pitchX, ly - pitchY), sz, 22, () => m_Ctx.Touch?.RequestReverseCameraToggle(), out _).text = "Kamera cofania";
            m_MirrorInsetLabel = Button(lab, "MirrorInsets", Vector2.zero, new Vector2(pad, ly - 2 * pitchY), new Vector2(full, bh), 22, () => m_Ctx.ToggleMirrorInsets?.Invoke(), out _);
            Button(lab, "LabBack", Vector2.zero, new Vector2(pad, pad), new Vector2(full, bh), 24, () => SetLabOpen(false), out _).text = "Wróć";
            m_LabPanel = lab.gameObject;
            m_DevPanelRt.gameObject.SetActive(false);
            m_LabPanel.SetActive(false);
        }

        /// <summary>Developer text (status / autopilot line, coupling line): bottom centre, between the control groups,
        /// over the dashboard - never over the horizon (review r2 #3).</summary>
        void BuildDevText()
        {
            m_DevTextRt = Zone("DevText", new Vector2(480f, HudLayout.DevTextHeight));
            m_Status = Label(m_DevTextRt, "Status", "", 20, TextAnchor.LowerCenter, Vector2.zero, Vector2.zero);
            HalfOf(m_Status.rectTransform, 0.5f, 1f);
            m_Status.color = k_Amber;
            m_Status.horizontalOverflow = HorizontalWrapMode.Wrap;
            m_Status.gameObject.SetActive(m_Ctx.DevDiagnostics);
            DevDiagnostics = m_Ctx.DevDiagnostics;
            m_Coupling = Label(m_DevTextRt, "Coupling", "", 20, TextAnchor.LowerCenter, Vector2.zero, Vector2.zero);
            HalfOf(m_Coupling.rectTransform, 0f, 0.5f);
            m_Coupling.color = k_Muted;
            m_Coupling.horizontalOverflow = HorizontalWrapMode.Wrap;
            m_Coupling.gameObject.SetActive(false);   // shown with the telemetry panel, developer mode only
        }

        /// <summary>Mirror inset (main mirror, portrait) beside the cluster; image flipped like a mirror.</summary>
        RawImage MirrorInset(string name, out GameObject go)
        {
            var rt = Zone(name, HudLayout.MirrorSize);
            var frame = rt.gameObject.AddComponent<Image>();
            frame.color = new Color(0.03f, 0.03f, 0.035f, 0.95f); frame.raycastTarget = false;
            var img = Rect("Image", rt);
            img.anchorMin = Vector2.zero; img.anchorMax = Vector2.one; img.offsetMin = new Vector2(5f, 5f); img.offsetMax = new Vector2(-5f, -5f);
            var ri = img.gameObject.AddComponent<RawImage>();
            ri.uvRect = new Rect(1f, 0f, -1f, 1f); // mirror image
            ri.raycastTarget = false;
            go = rt.gameObject;
            go.SetActive(false);
            return ri;
        }

        // ------------------------------------------------------------------ layout

        /// <summary>Developer panel expanded / collapsed (collapsing also leaves the lab page).</summary>
        public void SetDevPanelOpen(bool open)
        {
            m_DevOpen = open;
            if (!open) m_LabOpen = false;
            m_LayoutValid = false;
            UpdateLayout();
        }

        public bool DevPanelOpen => m_DevOpen;

        void SetLabOpen(bool open)
        {
            m_LabOpen = open && m_DevOpen;
            m_LayoutValid = false;
            UpdateLayout();
        }

        /// <summary>The zones as last solved (tests, captures).</summary>
        public HudLayoutResult Layout => m_L;
        /// <summary>Safe-area size in canvas units as last applied.</summary>
        public Vector2 SafeSizeUnits => m_View.SizeUnits;
        public RectTransform SafeAreaRect => m_SafeArea;

        /// <summary>The rect transform that shows layout zone <paramref name="i"/> (see <see cref="HudLayoutResult.Zone"/>).</summary>
        public RectTransform ZoneTransform(int i)
        {
            switch (i)
            {
                case 0: return m_ClusterRt;
                case 1: return m_ParkWarnRt;
                case 2: return m_ReverseRt;
                case 3: return (RectTransform)m_MirrorLGo.transform;
                case 4: return (RectTransform)m_MirrorRGo.transform;
                case 5: return m_DevToggleRt;
                case 6: return m_LabOpen ? m_LabRt : m_DevPanelRt;
                case 7: return m_TelemetryRt;
                case 8: return m_In.Gyro ? m_GyroRt : m_WheelRt;
                case 9: return m_TurnRt;
                case 10: return m_StalkRt;
                case 11: return m_BrakeRt;
                case 12: return m_ThrottleRt;
                case 13: return m_GearsRt;
                default: return m_DevTextRt;
            }
        }

        /// <summary>Screen rotation, folding / unfolding, split screen: Unity resizes the canvas, the next refresh lays out again.</summary>
        void OnRectTransformDimensionsChange() { m_View?.Invalidate(); }

        /// <summary>Solves and applies the zones when the screen or the HUD state changed. No allocation.</summary>
        void UpdateLayout()
        {
            bool changed = m_View.Refresh();
            HudLayoutInput s;
            s.Width = m_View.SizeUnits.x; s.Height = m_View.SizeUnits.y;
            s.Gyro = m_Ctx.IsGyroMode != null && m_Ctx.IsGyroMode();
            s.DevPanelOpen = m_DevOpen;
            s.Telemetry = TelemetryVisible;
            s.MirrorLeft = m_Ctx.LeftMirrorTexture != null && m_Ctx.LeftMirrorTexture() != null;
            s.MirrorRight = m_Ctx.RightMirrorTexture != null && m_Ctx.RightMirrorTexture() != null;
            s.ReverseView = m_Ctx.ReverseCameraTexture != null && m_Ctx.ReverseCameraTexture() != null;
            s.DevText = DevDiagnostics;
            if (!changed && m_LayoutValid && s.SameAs(m_In)) return;
            m_In = s; m_LayoutValid = true;
            HudLayout.Solve(s, out m_L);

            SetRect(m_ClusterRt, m_L.Cluster);
            SetRect(m_ParkWarnRt, m_L.ParkWarn);
            SetRect(m_ReverseRt, m_L.ReverseView);
            SetRect((RectTransform)m_MirrorLGo.transform, m_L.MirrorLeft);
            SetRect((RectTransform)m_MirrorRGo.transform, m_L.MirrorRight);
            SetRect(m_DevToggleRt, m_L.DevToggle);
            SetRect(m_DevPanelRt, m_L.DevPanel);
            SetRect(m_LabRt, m_L.DevPanel);
            if (s.Telemetry) SetRect(m_TelemetryRt, m_L.Telemetry);
            SetRect(m_WheelRt, new Rect(m_L.Steering.x, m_L.Steering.y, HudLayout.WheelSize, HudLayout.WheelSize));
            SetRect(m_GyroRt, new Rect(m_L.Steering.x, m_L.Steering.y, HudLayout.GyroSize.x, HudLayout.GyroSize.y));
            SetRect(m_TurnRt, m_L.TurnSignals);
            SetRect(m_StalkRt, m_L.Stalk);
            SetRect(m_BrakeRt, m_L.Brake);
            SetRect(m_ThrottleRt, m_L.Throttle);
            SetRect(m_GearsRt, m_L.Gears);
            SetRect(m_DevTextRt, m_L.DevText);

            bool grid = m_DevOpen && !m_LabOpen, lab = m_DevOpen && m_LabOpen;
            if (m_DevPanelRt.gameObject.activeSelf != grid) m_DevPanelRt.gameObject.SetActive(grid);
            if (m_LabPanel.activeSelf != lab) m_LabPanel.SetActive(lab);
            m_DevToggleImage.color = m_DevOpen ? k_ButtonOn : k_Button;
            string tl = m_DevOpen ? "Zamknij" : "Panel";
            if (!ReferenceEquals(m_DevToggleLabel.text, tl)) m_DevToggleLabel.text = tl;
        }

        static void HalfOf(RectTransform rt, float y0, float y1)
        {
            rt.anchorMin = new Vector2(0f, y0); rt.anchorMax = new Vector2(1f, y1);
            rt.offsetMin = rt.offsetMax = Vector2.zero;
        }

        static void SetRect(RectTransform rt, Rect r)
        {
            rt.anchoredPosition = r.position;
            rt.sizeDelta = r.size;
        }

        Text Lamp(RectTransform parent, string text, float x)
        {
            var t = Label(parent, "Lamp" + text, text, 20, TextAnchor.MiddleCenter, new Vector2(x, 6f), new Vector2(56f, 40f));
            t.color = k_LampOff;
            return t;
        }

        Image Bar(RectTransform parent, string name, Vector2 pos)
        {
            var bg = Rect(name + "Bg", parent);
            Place(bg, Vector2.zero, pos, new Vector2(84f, 5f));
            var bgi = bg.gameObject.AddComponent<Image>(); bgi.color = new Color(1f, 1f, 1f, 0.12f); bgi.raycastTarget = false;
            var bar = Rect(name, bg);
            bar.anchorMin = Vector2.zero; bar.anchorMax = new Vector2(0f, 1f); bar.offsetMin = bar.offsetMax = Vector2.zero;
            var img = bar.gameObject.AddComponent<Image>();
            img.color = k_Muted; img.raycastTarget = false;
            return img;
        }

        static string[] BuildCruiseStrings()
        {
            var a = new string[121];
            for (int i = 0; i < a.Length; i++) a[i] = "Zjazd\n" + i.ToString(CultureInfo.InvariantCulture) + " km/h";
            return a;
        }

        static string[] BuildAirStrings()
        {
            // 0.0 .. 15.0 bar in 0.1 steps, prefixed per circuit at use time (no per-frame formatting).
            var a = new string[151];
            for (int i = 0; i < a.Length; i++) a[i] = (i / 10f).ToString("F1", CultureInfo.InvariantCulture) + " bar";
            return a;
        }

        static readonly Color k_LampOff = new Color(1f, 1f, 1f, 0.16f);
        static readonly Color k_Green = new Color(0.55f, 0.80f, 0.50f, 1f);

        RectTransform PedalRect(string name, Vector2 size, Color fillColor, string label, Action<float> onValue)
        {
            var rt = Zone(name, size);
            rt.gameObject.AddComponent<Image>().color = k_PedalPanel;   // near-opaque: road markings must not show through
            var fill = Rect("Fill", rt);
            fill.anchorMin = Vector2.zero; fill.anchorMax = new Vector2(1f, 0f); fill.offsetMin = fill.offsetMax = Vector2.zero;
            var fi = fill.gameObject.AddComponent<Image>();
            fi.color = fillColor; fi.raycastTarget = false;
            for (int i = 1; i < 4; i++)
            {
                var tick = Rect("Tick", rt);
                tick.anchorMin = new Vector2(0f, i / 4f); tick.anchorMax = new Vector2(1f, i / 4f);
                tick.offsetMin = new Vector2(16f, -1f); tick.offsetMax = new Vector2(-16f, 1f);
                var ti = tick.gameObject.AddComponent<Image>(); ti.color = new Color(1, 1, 1, 0.18f); ti.raycastTarget = false;
            }
            var l = Label(rt, "Label", label, SmallFont, TextAnchor.LowerCenter, new Vector2(0f, 0f), new Vector2(size.x, 40f));
            Place((RectTransform)l.transform, new Vector2(0.5f, 0f), new Vector2(-size.x * 0.5f, 10f), new Vector2(size.x, 36f));
            var w = rt.gameObject.AddComponent<PedalWidget>();
            w.fill = fill;
            w.onValue = onValue;
            return rt;
        }

        // ------------------------------------------------------------------ update

        void Update()
        {
            PollDevGesture();
            RefreshNow();
        }

        public void RefreshNow()
        {
            UpdateLayout();
            var v = m_Ctx.Vehicle;
            bool gyro = m_Ctx.IsGyroMode != null && m_Ctx.IsGyroMode();
            if (m_WheelGo.activeSelf == gyro) m_WheelGo.SetActive(!gyro);
            if (m_GyroGo.activeSelf != gyro) m_GyroGo.SetActive(gyro);

            int speed = 0; string gear = "N"; float rpm = 600f; bool park = true; float rpmMax = 2100f;
            GearSelector sel = GearSelector.Neutral; bool manual = false;
            if (v != null && v.Initialized)
            {
                var m = v.Model;
                speed = Mathf.Clamp(Mathf.RoundToInt(Mathf.Abs(v.SpeedKmh)), 0, k_SpeedStrings.Length - 1);
                rpm = (float)m.Engine.Rpm;
                rpmMax = (float)m.Engine.Def.maxRpm;
                park = v.Input.ParkingBrake;
                sel = v.Input.Selector;
                manual = v.Input.ManualMode;
                gear = GearLabel(sel, manual, m.Amt.Gear);
            }
            if (speed != m_LastSpeed) { m_LastSpeed = speed; m_Speed.text = k_SpeedStrings[speed]; }
            if (!ReferenceEquals(gear, m_LastGear)) { m_LastGear = gear; m_Gear.text = gear; }
            int bucket = Mathf.RoundToInt(rpm / 50f);
            if (bucket != m_LastRpmBucket)
            {
                m_LastRpmBucket = bucket;
                m_Rpm.text = (bucket * 50).ToString(CultureInfo.InvariantCulture) + " obr/min";
                m_RpmBar.rectTransform.anchorMax = new Vector2(Mathf.Clamp01(rpm / rpmMax), 1f);
                m_RpmBar.color = rpm > 1900f ? k_Amber : k_Muted;
            }
            if (m_Park.enabled != park) m_Park.enabled = park;
            bool warn = v != null && v.Initialized && v.Model.ParkingBrakeWarning;
            int warnCount = v != null && v.Initialized ? v.Model.ParkingBrakeWarningCount : 0;
            m_ParkWarnTracker.Poll(warn, warnCount, Time.unscaledTime);
            float wa = m_ParkWarnTracker.Alpha;
            if (!Mathf.Approximately(wa, m_LastParkWarnAlpha)) { m_LastParkWarnAlpha = wa; m_ParkWarnGroup.alpha = wa; }
            m_DriveBtn.color = sel == GearSelector.Drive && !manual ? k_ButtonOn : k_Button;
            m_ManualBtn.color = sel == GearSelector.Drive && manual ? k_ButtonOn : k_Button;
            m_NeutralBtn.color = sel == GearSelector.Neutral ? k_ButtonOn : k_Button;
            m_ReverseBtn.color = sel == GearSelector.Reverse ? k_ButtonOn : k_Button;
            m_ParkBtn.color = park ? k_ParkOn : k_Button;
            if (DevDiagnostics && m_Ctx.StatusLine != null) { var s = m_Ctx.StatusLine(); if (!ReferenceEquals(s, m_Status.text)) m_Status.text = s ?? ""; }
            if (gyro && m_Ctx.Gyro != null && Time.unscaledTime >= m_NextTelemetry)
                m_GyroLabel.text = "Gyro: " + m_Ctx.Gyro.RelativeTiltDeg.ToString("F1", CultureInfo.InvariantCulture) + "°" + (m_Ctx.Gyro.HasSensor ? "" : "  (brak czujnika)");
            if (TelemetryVisible && Time.unscaledTime >= m_NextTelemetry)
            {
                m_NextTelemetry = Time.unscaledTime + 0.2f;
                m_Telemetry.text = BuildTelemetry();
            }
            if (m_RecImage != null) m_RecImage.color = m_Ctx.Recorder != null && m_Ctx.Recorder.IsRecording ? new Color(0.55f, 0.16f, 0.14f, 0.95f) : k_Button;
            RefreshStage2(v);
        }

        void RefreshStage2(VehicleBody v)
        {
            int lever = m_Ctx.RetarderLever != null ? m_Ctx.RetarderLever() : 0;
            for (int i = 0; i < m_StalkCells.Length; i++) m_StalkCells[i].color = i == lever ? (i == 0 ? k_ButtonOn : new Color(0.42f, 0.36f, 0.20f, 0.95f)) : k_Button;
            int sig = m_Ctx.TurnSignalLever != null ? m_Ctx.TurnSignalLever() : 0;
            bool lit = sig != 0 && m_Ctx.TurnSignalLit != null && m_Ctx.TurnSignalLit();
            m_TurnLeftBtn.color = lit && (sig == -1 || sig == 2) ? k_TurnLit : k_Button;
            m_TurnRightBtn.color = lit && (sig == 1 || sig == 2) ? k_TurnLit : k_Button;
            m_HazardBtn.color = lit && sig == 2 ? k_TurnLit : k_Button;
            float cruise = m_Ctx.BrakeCruiseKmh != null ? m_Ctx.BrakeCruiseKmh() : 0f;
            string cl = cruise > 0f ? k_CruiseStrings[Mathf.Clamp(Mathf.RoundToInt(cruise), 0, k_CruiseStrings.Length - 1)] : k_CruiseOff;
            if (!ReferenceEquals(m_CruiseLabel.text, cl)) m_CruiseLabel.text = cl;
            m_CruiseBtn.color = cruise > 0f ? k_ButtonOn : k_Button;
            int spawn = m_Ctx.CurrentSpawn != null ? m_Ctx.CurrentSpawn() : -1;
            for (int i = 0; i < m_SpawnBtns.Length; i++) m_SpawnBtns[i].color = i == spawn ? k_ButtonOn : k_Button;
            bool fault = m_Ctx.AbsFault != null && m_Ctx.AbsFault();
            string fl = fault ? "ABS: USTERKA" : "ABS: sprawny";
            if (!ReferenceEquals(m_AbsFaultLabel.text, fl)) m_AbsFaultLabel.text = fl;

            bool absActive = false, low = false, eb = false, ret = false;
            double p1 = 0, p2 = 0;
            if (v != null && v.Initialized)
            {
                var m = v.Model;
                absActive = m.Air.AbsAnyActive || (v.Trailer != null && v.Coupled && v.Trailer.Model.Brakes.AbsAnyActive);
                low = m.Air.LowPressureWarning;
                eb = m.Engine.EngineBrakeState > 0.05;
                ret = m.Retarder.Torque > 50;
                p1 = m.Air.Front; p2 = m.Air.Rear;
            }
            m_LampAbs.color = fault || absActive ? k_Amber : k_LampOff;
            m_LampStop.color = low ? k_Red : k_LampOff;
            m_LampEb.color = eb ? k_Green : k_LampOff;
            m_LampRet.color = ret ? k_Green : k_LampOff;
            int i1 = Mathf.Clamp(Mathf.RoundToInt((float)p1 * 10f), 0, 150), i2 = Mathf.Clamp(Mathf.RoundToInt((float)p2 * 10f), 0, 150);
            if (i1 != m_LastAir1) { m_LastAir1 = i1; m_Air1.text = k_AirStrings[i1]; m_Air1Bar.rectTransform.anchorMax = new Vector2(Mathf.Clamp01(i1 / 130f), 1f); m_Air1Bar.color = low ? k_Red : k_Muted; }
            if (i2 != m_LastAir2) { m_LastAir2 = i2; m_Air2.text = k_AirStrings[i2]; m_Air2Bar.rectTransform.anchorMax = new Vector2(Mathf.Clamp01(i2 / 130f), 1f); m_Air2Bar.color = low ? k_Red : k_Muted; }

            if (DevDiagnostics && TelemetryVisible && m_Ctx.CouplingStatus != null && Time.unscaledTime >= m_NextCoupling)
            {
                m_NextCoupling = Time.unscaledTime + 0.1f;
                m_Coupling.text = m_Ctx.CouplingStatus() ?? "";
            }
            SetInset(m_MirrorLGo, m_MirrorL, m_Ctx.LeftMirrorTexture, m_L.ShowMirrorLeft);
            SetInset(m_MirrorRGo, m_MirrorR, m_Ctx.RightMirrorTexture, m_L.ShowMirrorRight);
            if (m_MirrorInsetLabel != null)
            {
                string ml = m_Ctx.MirrorInsets != null && m_Ctx.MirrorInsets() ? "Lusterka w kabinie: okienka" : "Lusterka w kabinie: rozglądanie";
                if (!ReferenceEquals(m_MirrorInsetLabel.text, ml)) m_MirrorInsetLabel.text = ml;
            }
            var tex = m_Ctx.ReverseCameraTexture != null ? m_Ctx.ReverseCameraTexture() : null;
            bool show = tex != null;
            if (m_ReversePanel.activeSelf != show) m_ReversePanel.SetActive(show);
            if (show)
            {
                if (m_ReverseImage.texture != tex) m_ReverseImage.texture = tex;
                if (m_Ctx.ReverseCameraLabel != null) { var l = m_Ctx.ReverseCameraLabel(); if (!ReferenceEquals(l, m_ReverseLabel.text)) m_ReverseLabel.text = l; }
            }
        }

        float m_NextCoupling;

        static void SetInset(GameObject go, RawImage img, Func<Texture> src, bool room)
        {
            var t = src != null ? src() : null;
            bool on = t != null && room;   // room: false while a developer overlay uses the inset's place
            if (go.activeSelf != on) go.SetActive(on);
            if (on && img.texture != t) img.texture = t;
        }

        static readonly string[] k_DriveGears = BuildGearLabels("D"), k_ManualGears = BuildGearLabels("M");

        static string GearLabel(GearSelector sel, bool manual, int gear)
        {
            if (sel == GearSelector.Neutral) return "N";
            if (sel == GearSelector.Reverse) return "R";
            var arr = manual ? k_ManualGears : k_DriveGears;
            return arr[Mathf.Clamp(gear, 0, arr.Length - 1)];
        }

        string BuildTelemetry()
        {
            var ci = CultureInfo.InvariantCulture;
            var sb = m_Sb; sb.Clear();
            var v = m_Ctx.Vehicle;
            if (v == null || !v.Initialized)
            {
                sb.Append("TELEMETRIA (podgląd)\nprędkość —  obroty —  bieg —\nkoła: Fz [kN] · poślizg · kąt znosu · nawierzchnia\nkrok fizyki — µs");
                return sb.ToString();
            }
            var m = v.Model;
            var inp = v.Input;
            sb.Append("TELEMETRIA  t=").Append(m.Time.ToString("F1", ci)).Append(" s\n");
            sb.Append("v ").Append(v.SpeedKmh.ToString("F1", ci)).Append(" km/h   a_x ").Append(m.LocalAcceleration.z.ToString("F2", ci))
              .Append("  a_y ").Append(m.LocalAcceleration.x.ToString("F2", ci)).Append(" m/s²   yaw ").Append((m.YawRate * MathUtil.Rad2Deg).ToString("F1", ci)).Append(" °/s\n");
            sb.Append("silnik ").Append(m.Engine.Rpm.ToString("F0", ci)).Append(" obr/min  M ").Append(m.EngineTorque.ToString("F0", ci))
              .Append(" Nm  bieg ").Append(m.Amt.Gear).Append(' ').Append(m.Amt.State).Append("  sprzęgło ").Append(m.Amt.ClutchCommand.ToString("F2", ci)).Append('\n');
            sb.Append("gaz ").Append(inp.Throttle.ToString("F2", ci)).Append("→").Append(m.ThrottleDemand.ToString("F2", ci))
              .Append("  hamulec ").Append(inp.Brake.ToString("F2", ci)).Append("→").Append(m.BrakeDemand.ToString("F2", ci))
              .Append("  skręt ").Append(inp.Steer.ToString("+0.00;-0.00", ci)).Append(" (koło kier. ").Append(m.Steering.HandwheelDeg.ToString("F0", ci)).Append("°)\n");
            sb.Append("powietrze ").Append(m.Air.Front.ToString("F1", ci)).Append('/').Append(m.Air.Rear.ToString("F1", ci))
              .Append(" bar  postojowy ").Append(m.ParkingBrakeState.ToString("F2", ci)).Append(m.HillHoldActive ? "  HSA" : "")
              .Append("  dźwignia ").Append(inp.RetarderLever).Append("  HS ").Append(m.Engine.EngineBrakeTorque.ToString("F0", ci))
              .Append(" Nm  ret ").Append(m.Retarder.Torque.ToString("F0", ci)).Append(" Nm\n");
            if (v.Trailer != null)
            {
                var fw = v.Combination.FifthWheel;
                var tm = v.Trailer.Model;
                sb.Append("naczepa ").Append((tm.Mass / 1000).ToString("F1", ci)).Append(" t  ").Append(fw.Coupled ? "sprzężona" : "odpięta")
                  .Append("  przegub ").Append((fw.Articulation * MathUtil.Rad2Deg).ToString("+0.0;-0.0", ci)).Append("°  siodło Fz ")
                  .Append((fw.KingpinLoadLocal.y / 1000).ToString("F0", ci)).Append(" kN Fx ").Append((fw.KingpinLoadLocal.z / 1000).ToString("F0", ci))
                  .Append(" kN  błąd ").Append((fw.PositionError * 1000).ToString("F2", ci)).Append(" mm\n");
                double tl = 0; foreach (var tw in tm.Wheels) tl += tw.Fz;
                sb.Append("  osie naczepy ").Append((tl / 1000).ToString("F0", ci)).Append(" kN  nogi ").Append((tm.LandingGearLoad / 1000).ToString("F0", ci))
                  .Append(" kN  zbiornik ").Append(tm.Brakes.Reservoir.ToString("F1", ci)).Append(" bar").Append(tm.Brakes.Emergency ? "  HAM. AWARYJNE" : "")
                  .Append(tm.Brakes.AbsAnyActive ? "  ABS" : "").Append('\n');
            }
            sb.Append("koło    Fz kN   poślizg  znos°  ugięcie  nawierzchnia\n");
            var ws = m.Wheels;
            for (int i = 0; i < ws.Length; i++)
            {
                var w = ws[i];
                sb.Append(w.Name.PadRight(8)).Append((w.Fz / 1000).ToString("F1", ci).PadLeft(6))
                  .Append((w.SlipRatio).ToString("+0.000;-0.000", ci).PadLeft(9))
                  .Append((w.SlipAngle * MathUtil.Rad2Deg).ToString("+0.0;-0.0", ci).PadLeft(7))
                  .Append((w.Compression * 100).ToString("+0.0;-0.0", ci).PadLeft(7)).Append(" cm  ")
                  .Append(w.Contact ? SurfaceTable.DisplayNamePl(w.SurfaceId) : "brak styku").Append('\n');
            }
            sb.Append("krok fizyki ").Append(v.LastStepMicros.ToString("F0", ci)).Append(" µs (śr. ").Append(v.AverageStepMicros.ToString("F0", ci)).Append(")");
            var s = m_Ctx.Sampler;
            if (s != null && s.Snapshot.Frames.Samples > 0)
            {
                var f = s.Snapshot.Frames;
                sb.Append("   klatka p50 ").Append(f.P50Ms.ToString("F1", ci)).Append(" · p95 ").Append(f.P95Ms.ToString("F1", ci))
                  .Append(" · p99 ").Append(f.P99Ms.ToString("F1", ci)).Append(" ms");
            }
            sb.Append('\n');
            if (m_Ctx.Mixer != null) sb.Append("sterowanie: ").Append(m_Ctx.Mixer.SteeringSource);
            if (m_Ctx.Recorder != null && m_Ctx.Recorder.IsRecording) sb.Append("   REC ").Append(System.IO.Path.GetFileName(m_Ctx.Recorder.CurrentFile));
            return sb.ToString();
        }

        void RefreshLabels()
        {
            if (m_CamLabel == null) return;
            var mode = m_Ctx.Rig != null ? m_Ctx.Rig.mode : CameraMode.Cab;
            m_CamLabel.text = mode == CameraMode.Cab ? "Kamera: kabina" : mode == CameraMode.Chase ? "Kamera: za" : "Kamera: orbita";
            bool gyro = m_Ctx.IsGyroMode != null && m_Ctx.IsGyroMode();
            m_SteerLabel.text = gyro ? "Ster.: gyro" : "Ster.: koło " + (m_Ctx.Wheel != null ? m_Ctx.Wheel.HalfRangeDeg.ToString("F0", CultureInfo.InvariantCulture) + "°" : "");
            m_TelLabel.text = TelemetryVisible ? "Telemetria ✓" : "Telemetria";
            m_RecLabel.text = m_Ctx.Recorder != null && m_Ctx.Recorder.IsRecording ? "Stop REC" : "Nagraj CSV";
        }

        // ------------------------------------------------------------------ helpers

        static string[] BuildNumbers(int n)
        {
            var a = new string[n];
            for (int i = 0; i < n; i++) a[i] = i.ToString(CultureInfo.InvariantCulture);
            return a;
        }

        static string[] BuildGearLabels(string prefix)
        {
            var a = new string[17];
            a[0] = prefix;
            for (int i = 1; i < a.Length; i++) a[i] = prefix + i.ToString(CultureInfo.InvariantCulture);
            return a;
        }

        static RectTransform Rect(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.layer = 5;
            var rt = (RectTransform)go.transform;
            rt.SetParent(parent, false);
            return rt;
        }

        static void Stretch(RectTransform rt)
        {
            rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = rt.offsetMax = Vector2.zero;
        }

        /// <summary>Places a rect by its bottom-left corner relative to an anchor point of the parent.</summary>
        static void Place(RectTransform rt, Vector2 anchor, Vector2 bottomLeftFromAnchor, Vector2 size)
        {
            rt.anchorMin = rt.anchorMax = anchor;
            rt.pivot = Vector2.zero;
            rt.anchoredPosition = bottomLeftFromAnchor;
            rt.sizeDelta = size;
        }

        RectTransform Panel(string name, Transform parent, Vector2 anchor, Vector2 offsetFromAnchor, Vector2 size)
        {
            var rt = Rect(name, parent);
            // Top anchors place the panel below the anchor point.
            Vector2 bl = offsetFromAnchor;
            if (anchor.y >= 1f) bl.y -= size.y;
            if (Mathf.Approximately(anchor.x, 0.5f)) bl.x -= size.x * 0.5f;
            if (anchor.x >= 1f) bl.x -= size.x;
            Place(rt, anchor, bl, size);
            var img = rt.gameObject.AddComponent<Image>();
            img.color = k_Panel;
            img.raycastTarget = false;
            return rt;
        }

        Text Label(Transform parent, string name, string text, int size, TextAnchor align, Vector2 bottomLeft, Vector2 box)
        {
            var rt = Rect(name, parent);
            Place(rt, Vector2.zero, bottomLeft, box);
            var t = rt.gameObject.AddComponent<Text>();
            t.font = m_Font;
            t.fontSize = size;
            t.color = k_Text;
            t.alignment = align;
            t.text = text;
            t.horizontalOverflow = HorizontalWrapMode.Overflow;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            t.raycastTarget = false;
            return t;
        }

        Text Button(Transform parent, string name, Vector2 anchor, Vector2 bottomLeft, Vector2 size, int fontSize, UnityEngine.Events.UnityAction onClick, out Image image)
        {
            var rt = Rect(name, parent);
            Place(rt, anchor, bottomLeft, size);
            image = rt.gameObject.AddComponent<Image>();
            image.color = k_Button;
            var b = rt.gameObject.AddComponent<Button>();
            b.targetGraphic = image;
            b.onClick.AddListener(onClick);
            var label = Label(rt, "Label", name, fontSize, TextAnchor.MiddleCenter, Vector2.zero, size);
            return label;
        }

        static void EnsureEventSystem()
        {
            if (FindAnyObjectByType<EventSystem>() != null) return;
            var go = new GameObject("EventSystem", typeof(EventSystem));
            go.AddComponent<InputSystemUIInputModule>().AssignDefaultActions();
        }

        static Sprite s_WheelSprite;

        /// <summary>Procedural steering-wheel ring (rim, three spokes, top marker), 256 px.</summary>
        static Sprite WheelSprite()
        {
            if (s_WheelSprite != null) return s_WheelSprite;
            const int n = 256;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };
            var px = new Color32[n * n];
            float c = (n - 1) * 0.5f;
            for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                float dx = x - c, dy = y - c;
                float r = Mathf.Sqrt(dx * dx + dy * dy);
                float a = 0f;
                a = Mathf.Max(a, Band(r, 110f, 122f));                                   // rim
                a = Mathf.Max(a, Band(r, 0f, 18f));                                      // hub
                if (dy < 6f && Mathf.Abs(dy) < 6f && r < 112f) a = Mathf.Max(a, 1f);    // left/right spokes
                if (dy < 0f && Mathf.Abs(dx) < 6f && r < 112f) a = Mathf.Max(a, 1f);    // bottom spoke
                byte g = 235;
                if (dy > 0f && Mathf.Abs(dx) < 10f && r > 100f && r < 126f) { a = 1f; px[y * n + x] = new Color32(240, 168, 50, 255); continue; } // top marker
                px[y * n + x] = new Color32(g, g, g, (byte)(Mathf.Clamp01(a) * 255));
            }
            tex.SetPixels32(px);
            tex.Apply(false, true);
            s_WheelSprite = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), 100f);
            return s_WheelSprite;
        }

        static float Band(float r, float r0, float r1) => Mathf.Clamp01(Mathf.Min(r - r0 + 1f, r1 - r + 1f));
    }
}
