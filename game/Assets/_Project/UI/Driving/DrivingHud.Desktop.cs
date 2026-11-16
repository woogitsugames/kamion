using Game.Cameras;
using Game.Controls;
using Game.UI.CabDisplays;
using Game.Vehicle.Runtime;
using UnityEngine;
using UnityEngine.UI;
using P = Game.Controls.UiPalette;

namespace Game.UI.Driving
{
    /// <summary>
    /// Monitor HUD (ADR 0283, D84 "HUD zbyt AI slop"): on a PC without touch controls the floating top cluster of ADR 0265
    /// is replaced by one low strip at the bottom centre, drawn like the display in a dashboard - telltale row (turn-signal
    /// arrows at the ends, active warnings as tiles between them), under it speed, gear and both air-brake circuits;
    /// the extended detail (key I, rebindable) adds rev counter, endurance brake and brake cruise as one more row. In the
    /// cab view with live cab screens only the telltale row stays (the cluster in the dash is the speedometer,
    /// <see cref="HudVisibility"/>). Mirror windows at the outer edges, larger and adjustable (<see cref="DesktopHudLayout"/>,
    /// <see cref="HudPreferences"/>). Colours from <see cref="UiPalette"/> (WCAG AA, ADR table), type Inter Regular / SemiBold.
    /// Per frame: compares and looks up prebuilt strings only - no allocation (PcHudGc0244Tests, HudRedesign0283Tests).
    /// The touch HUD (phones, ADR 0079) is unchanged.
    /// </summary>
    public sealed partial class DrivingHud
    {
        RectTransform m_DStrip, m_DTell, m_DExtRow;
        Text m_DSpeed, m_DGear, m_DAir1, m_DAir2, m_DRpm, m_DRet, m_DCruise;
        Image m_DAir1Bar, m_DAir2Bar, m_DRpmBar, m_DTurnL, m_DTurnR;
        readonly RectTransform[] m_DTile = new RectTransform[HudWarnings.MaxShown];
        readonly Image[] m_DTileBg = new Image[HudWarnings.MaxShown];
        readonly Text[] m_DTileText = new Text[HudWarnings.MaxShown];
        readonly HudWarning[] m_DWarn = new HudWarning[HudWarnings.MaxShown];
        readonly HudWarning[] m_DWarnShown = new HudWarning[HudWarnings.MaxShown];
        int m_DWarnCount = -1;
        DesktopHudInput m_DIn;
        DesktopHudResult m_D;
        HudVisibility m_Vis;
        bool m_DValid, m_DesktopApplied, m_DesktopKnown;
        int m_DPrefsVersion = int.MinValue, m_MirrorAdjustVersion = int.MinValue;
        int m_DLastSpeed = int.MinValue, m_DLastAir1 = int.MinValue, m_DLastAir2 = int.MinValue, m_DLastRpm = int.MinValue,
            m_DLastRet = int.MinValue, m_DLastCruise = int.MinValue, m_DLastTurn = int.MinValue;
        bool m_DLastLow;
        string m_DLastGear;

        /// <summary>Monitor HUD zones as last solved (tests, captures).</summary>
        public DesktopHudResult DesktopLayout => m_D;
        /// <summary>Monitor HUD visibility as last resolved (tests, captures).</summary>
        public HudVisibility DesktopVisibility => m_Vis;

        const float StripW = 640f, RowH = 112f;

        void BuildDesktop()
        {
            var strong = UiFonts.Strong;

            // ---- strip (bottom-left anchored zone; height follows the extended row)
            m_DStrip = Zone("DesktopStrip", new Vector2(StripW, RowH));
            var bg = m_DStrip.gameObject.AddComponent<Image>();
            bg.color = P.HudPanel; bg.raycastTarget = false;

            m_DSpeed = DLabel(m_DStrip, "Speed", "0", strong, 64, TextAnchor.MiddleRight, P.Ink, new Vector2(12f, 14f), new Vector2(172f, 84f));
            DLabel(m_DStrip, "SpeedUnit", HudTexts.KmH, m_Font, 22, TextAnchor.LowerLeft, P.InkMuted, new Vector2(190f, 26f), new Vector2(60f, 30f));
            DRule(m_DStrip, "Rule1", new Vector2(256f, 16f), new Vector2(1f, 80f));
            m_DGear = DLabel(m_DStrip, "Gear", "N", strong, 50, TextAnchor.MiddleCenter, P.Ink, new Vector2(258f, 14f), new Vector2(110f, 84f));
            DRule(m_DStrip, "Rule2", new Vector2(370f, 16f), new Vector2(1f, 80f));
            m_DAir1 = AirRow(1, 62f, out m_DAir1Bar);
            m_DAir2 = AirRow(2, 20f, out m_DAir2Bar);

            // ---- extended row (above the main row inside the strip)
            m_DExtRow = Rect("ExtendedRow", m_DStrip);
            Place(m_DExtRow, Vector2.zero, new Vector2(0f, RowH), new Vector2(StripW, DesktopHudLayout.ExtendedRowHeight));
            DRule(m_DExtRow, "RuleTop", new Vector2(12f, 0f), new Vector2(StripW - 24f, 1f));
            m_DRpm = DLabel(m_DExtRow, "Rpm", "0", strong, 26, TextAnchor.MiddleRight, P.Ink, new Vector2(12f, 30f), new Vector2(96f, 34f));
            DLabel(m_DExtRow, "RpmUnit", HudTexts.Rpm, m_Font, 18, TextAnchor.MiddleLeft, P.InkMuted, new Vector2(114f, 30f), new Vector2(110f, 34f));
            m_DRpmBar = DBar(m_DExtRow, "RpmBar", new Vector2(16f, 16f), new Vector2(224f, 6f));
            DLabel(m_DExtRow, "RetCaption", HudTexts.Retarder, m_Font, 18, TextAnchor.MiddleLeft, P.InkMuted, new Vector2(262f, 50f), new Vector2(140f, 26f));
            m_DRet = DLabel(m_DExtRow, "Ret", "0", strong, 26, TextAnchor.MiddleLeft, P.Ink, new Vector2(262f, 12f), new Vector2(140f, 36f));
            DLabel(m_DExtRow, "CruiseCaption", HudTexts.BrakeCruise, m_Font, 18, TextAnchor.MiddleLeft, P.InkMuted, new Vector2(410f, 50f), new Vector2(218f, 26f));
            m_DCruise = DLabel(m_DExtRow, "Cruise", HudTexts.Off, strong, 26, TextAnchor.MiddleLeft, P.Ink, new Vector2(410f, 12f), new Vector2(218f, 36f));
            m_DExtRow.gameObject.SetActive(false);

            // ---- telltale row: arrow slots at the ends, warning tiles between (no background of its own)
            m_DTell = Zone("DesktopTelltales", DesktopHudLayout.TelltaleSize);
            m_DTurnL = ArrowSlot("TurnLeft", 0f, false);
            m_DTurnR = ArrowSlot("TurnRight", DesktopHudLayout.TelltaleSize.x - 64f, true);
            for (int i = 0; i < m_DTile.Length; i++)
            {
                var t = Rect("Warning" + i, m_DTell);
                Place(t, Vector2.zero, new Vector2(72f + i * 168f, 0f), new Vector2(160f, DesktopHudLayout.TelltaleSize.y));
                m_DTileBg[i] = t.gameObject.AddComponent<Image>();
                m_DTileBg[i].color = P.TellRed; m_DTileBg[i].raycastTarget = false;
                m_DTileText[i] = DLabel(t, "Text", "", strong, 17, TextAnchor.MiddleCenter, P.Ink, Vector2.zero, new Vector2(160f, DesktopHudLayout.TelltaleSize.y));
                m_DTileText[i].horizontalOverflow = HorizontalWrapMode.Wrap;
                m_DTileText[i].resizeTextForBestFit = true; m_DTileText[i].resizeTextMinSize = 12; m_DTileText[i].resizeTextMaxSize = 17;
                m_DTile[i] = t;
                t.gameObject.SetActive(false);
            }
            m_DStrip.gameObject.SetActive(false);
            m_DTell.gameObject.SetActive(false);
        }

        Text AirRow(int circuit, float y, out Image bar)
        {
            DLabel(m_DStrip, "AirLabel" + circuit, circuit == 1 ? "1" : "2", m_Font, 20, TextAnchor.MiddleCenter, P.InkMuted, new Vector2(382f, y), new Vector2(24f, 30f));
            bar = DBar(m_DStrip, "AirBar" + circuit, new Vector2(410f, y + 12f), new Vector2(118f, 6f));
            var v = DLabel(m_DStrip, "Air" + circuit, "0,0", UiFonts.Strong, 26, TextAnchor.MiddleRight, P.Ink, new Vector2(530f, y), new Vector2(60f, 30f));
            DLabel(m_DStrip, "AirUnit" + circuit, HudTexts.Bar, m_Font, 18, TextAnchor.MiddleLeft, P.InkMuted, new Vector2(594f, y), new Vector2(40f, 30f));
            return v;
        }

        Image ArrowSlot(string name, float x, bool right)
        {
            var slot = Rect(name, m_DTell);
            Place(slot, Vector2.zero, new Vector2(x, 0f), new Vector2(64f, DesktopHudLayout.TelltaleSize.y));
            var sbg = slot.gameObject.AddComponent<Image>();
            sbg.color = P.HudPanel; sbg.raycastTarget = false;
            var a = Rect("Arrow", slot);
            a.anchorMin = a.anchorMax = a.pivot = new Vector2(0.5f, 0.5f);
            a.sizeDelta = new Vector2(36f, 30f);
            a.anchoredPosition = Vector2.zero;
            if (right) a.localScale = new Vector3(-1f, 1f, 1f);
            var img = a.gameObject.AddComponent<Image>();
            img.sprite = ArrowSprite();
            img.color = P.TellOff; img.raycastTarget = false;
            return img;
        }

        Text DLabel(Transform parent, string name, string text, Font font, int size, TextAnchor align, Color color, Vector2 bottomLeft, Vector2 box)
        {
            var t = Label(parent, name, text, size, align, bottomLeft, box);
            t.font = font;
            t.color = color;
            return t;
        }

        static void DRule(Transform parent, string name, Vector2 pos, Vector2 size)
        {
            var r = Rect(name, parent);
            Place(r, Vector2.zero, pos, size);
            var i = r.gameObject.AddComponent<Image>();
            i.color = P.GaugeTrack; i.raycastTarget = false;
        }

        static Image DBar(Transform parent, string name, Vector2 pos, Vector2 size)
        {
            var bg = Rect(name + "Track", parent);
            Place(bg, Vector2.zero, pos, size);
            var bgi = bg.gameObject.AddComponent<Image>();
            bgi.color = P.GaugeTrack; bgi.raycastTarget = false;
            var fill = Rect(name, bg);
            fill.anchorMin = Vector2.zero; fill.anchorMax = new Vector2(0f, 1f); fill.offsetMin = fill.offsetMax = Vector2.zero;
            var img = fill.gameObject.AddComponent<Image>();
            img.color = P.GaugeFill; img.raycastTarget = false;
            return img;
        }

        // ------------------------------------------------------------------ layout

        /// <summary>Monitor branch of <see cref="UpdateLayout"/>: visibility, preferences, <see cref="DesktopHudLayout"/>. No allocation.</summary>
        void UpdateDesktopLayout(bool screenChanged)
        {
            var prefs = HudPreferences.Current;
            bool cab = m_Ctx.Rig != null && m_Ctx.Rig.mode == CameraMode.Cab;
            m_Vis = HudVisibility.Resolve(prefs.Detail, prefs.Cab, cab, CabScreens.LiveClusters > 0, DevDiagnostics);
            if (!m_Vis.DevToggle && m_DevOpen) { m_DevOpen = false; m_LabOpen = false; }

            DesktopHudInput d;
            d.Width = m_View.SizeUnits.x; d.Height = m_View.SizeUnits.y;
            d.Strip = m_Vis.Strip; d.Extended = m_Vis.Extended;
            Texture texL = m_Ctx.LeftMirrorTexture != null ? m_Ctx.LeftMirrorTexture() : null;
            Texture texR = m_Ctx.RightMirrorTexture != null ? m_Ctx.RightMirrorTexture() : null;
            d.MirrorLeft = texL != null; d.MirrorRight = texR != null;
            Texture texA = texL != null ? texL : texR;
            d.MirrorAspect = texA != null && texA.height > 0 ? texA.width / (float)texA.height : 0f;
            d.MirrorSize = prefs.MirrorSize; d.MirrorDrop = prefs.MirrorDrop; d.MirrorInset = prefs.MirrorInset;
            d.ReverseView = m_Ctx.ReverseCameraTexture != null && m_Ctx.ReverseCameraTexture() != null;
            d.DevToggle = m_Vis.DevToggle;
            d.DevPanelOpen = m_DevOpen;
            d.Telemetry = TelemetryVisible;
            d.DevText = DevDiagnostics;
            if (!screenChanged && m_DValid && m_DesktopApplied && d.SameAs(m_DIn) && m_DPrefsVersion == HudPreferences.Version) return;
            m_DIn = d; m_DValid = true; m_DPrefsVersion = HudPreferences.Version;
            DesktopHudLayout.Solve(d, out m_D);

            if (!m_DesktopApplied) ApplyFormFactor(true);
            SetRect(m_DStrip, m_D.Strip);
            SetRect(m_DTell, m_D.Telltales);
            if (m_DStrip.gameObject.activeSelf != m_D.ShowStrip) m_DStrip.gameObject.SetActive(m_D.ShowStrip);
            if (m_DExtRow.gameObject.activeSelf != m_Vis.Extended) m_DExtRow.gameObject.SetActive(m_Vis.Extended);
            SetRect((RectTransform)m_MirrorLGo.transform, m_D.MirrorLeft);
            SetRect((RectTransform)m_MirrorRGo.transform, m_D.MirrorRight);
            SetRect(m_ReverseRt, m_D.ReverseView);
            SetRect(m_DevToggleRt, m_D.DevToggle);
            SetRect(m_DevPanelRt, m_D.DevPanel);
            SetRect(m_LabRt, m_D.DevPanel);
            if (d.Telemetry) SetRect(m_TelemetryRt, m_D.Telemetry);
            SetRect(m_DevTextRt, m_D.DevText);
            if (m_DevToggleRt.gameObject.activeSelf != m_D.ShowDevToggle) m_DevToggleRt.gameObject.SetActive(m_D.ShowDevToggle);

            // Keep the shared result meaningful for tests / captures written against HudLayoutResult.
            m_L = default;
            m_L.Cluster = m_D.ShowStrip ? m_D.Strip : m_D.Telltales;
            m_L.ParkWarn = m_D.Telltales;
            m_L.ReverseView = m_D.ReverseView; m_L.ShowReverseView = m_D.ShowReverseView;
            m_L.MirrorLeft = m_D.MirrorLeft; m_L.MirrorRight = m_D.MirrorRight;
            m_L.ShowMirrorLeft = m_D.ShowMirrorLeft; m_L.ShowMirrorRight = m_D.ShowMirrorRight;
            m_L.DevToggle = m_D.DevToggle; m_L.DevPanel = m_D.DevPanel; m_L.ShowDevPanel = m_D.ShowDevPanel;
            m_L.Telemetry = m_D.Telemetry; m_L.ShowTelemetry = m_D.ShowTelemetry;
            m_L.DevText = m_D.DevText; m_L.ShowDevText = m_D.ShowDevText;
            m_L.ShowTouchControls = false;

            bool grid = m_DevOpen && !m_LabOpen, lab = m_DevOpen && m_LabOpen;
            if (m_DevPanelRt.gameObject.activeSelf != grid) m_DevPanelRt.gameObject.SetActive(grid);
            if (m_LabPanel.activeSelf != lab) m_LabPanel.SetActive(lab);
            m_DevToggleImage.color = m_DevOpen ? k_ButtonOn : k_Button;
            string tl = m_DevOpen ? HudTexts.DevToggleOpen : HudTexts.DevToggle;
            if (!ReferenceEquals(m_DevToggleLabel.text, tl)) m_DevToggleLabel.text = tl;
            m_LayoutValid = false;   // the touch branch lays out again when the form factor flips back
        }

        /// <summary>Shows the monitor or the touch furniture (once per form-factor change).</summary>
        void ApplyFormFactor(bool desktop)
        {
            if (m_DesktopKnown && m_DesktopApplied == desktop) return;
            m_DesktopKnown = true;
            m_DesktopApplied = desktop;
            m_ClusterRt.gameObject.SetActive(!desktop);
            m_ParkWarnRt.gameObject.SetActive(!desktop);
            if (m_DStrip != null) m_DStrip.gameObject.SetActive(desktop && m_D.ShowStrip);
            if (m_DTell != null) m_DTell.gameObject.SetActive(desktop);
            if (!desktop && !m_DevToggleRt.gameObject.activeSelf) m_DevToggleRt.gameObject.SetActive(true);
            float bezel = desktop ? DesktopHudLayout.MirrorBezel : 5f;
            MirrorBezelStyle(m_MirrorLGo, bezel, desktop);
            MirrorBezelStyle(m_MirrorRGo, bezel, desktop);
            m_DValid = false;
            m_LayoutValid = false;
        }

        static void MirrorBezelStyle(GameObject go, float bezel, bool desktop)
        {
            var frame = go.GetComponent<Image>();
            if (frame != null) frame.color = desktop ? P.MirrorBezel : new Color(0.03f, 0.03f, 0.035f, 0.95f);
            var img = go.transform.childCount > 0 ? go.transform.GetChild(0) as RectTransform : null;
            if (img != null) { img.offsetMin = new Vector2(bezel, bezel); img.offsetMax = new Vector2(-bezel, -bezel); }
        }

        // ------------------------------------------------------------------ values

        /// <summary>Main-mirror adjustment from the preferences (both form factors; on change only).</summary>
        void ApplyMirrorAdjust()
        {
            int v = HudPreferences.Version;
            if (v == m_MirrorAdjustVersion) return;
            m_MirrorAdjustVersion = v;
            var p = HudPreferences.Current;
            RenderTextureMirror.AdjustYawOutDeg = p.MirrorYawOut;
            RenderTextureMirror.AdjustPitchDownDeg = p.MirrorPitchDown;
        }

        /// <summary>Monitor strip values. Prebuilt strings, change detection, no allocation.</summary>
        void RefreshDesktop(VehicleBody v, int speed, string gear, float rpm, float rpmMax, bool park)
        {
            if (speed != m_DLastSpeed) { m_DLastSpeed = speed; m_DSpeed.text = HudTexts.Speed(speed); }
            if (!ReferenceEquals(gear, m_DLastGear)) { m_DLastGear = gear; m_DGear.text = gear; }

            bool live = v != null && v.Initialized;
            double p1 = 0, p2 = 0;
            bool low = false, absActive = false, trailerEmergency = false;
            if (live)
            {
                var m = v.Model;
                p1 = m.Air.Front; p2 = m.Air.Rear;
                low = m.Air.LowPressureWarning;
                absActive = m.Air.AbsAnyActive || (v.Trailer != null && v.Coupled && v.Trailer.Model.Brakes.AbsAnyActive);
                trailerEmergency = v.Trailer != null && v.Coupled && v.Trailer.Model.Brakes.Emergency;
            }
            int i1 = Mathf.Clamp(Mathf.RoundToInt((float)p1 * 10f), 0, 150), i2 = Mathf.Clamp(Mathf.RoundToInt((float)p2 * 10f), 0, 150);
            bool lowChanged = low != m_DLastLow;
            m_DLastLow = low;
            if (i1 != m_DLastAir1 || lowChanged) { m_DLastAir1 = i1; m_DAir1.text = HudTexts.Air(i1); SetBar(m_DAir1Bar, i1 / 130f, low); }
            if (i2 != m_DLastAir2 || lowChanged) { m_DLastAir2 = i2; m_DAir2.text = HudTexts.Air(i2); SetBar(m_DAir2Bar, i2 / 130f, low); }

            // turn signals (lit with the flasher)
            int sig = m_Ctx.TurnSignalLever != null ? m_Ctx.TurnSignalLever() : 0;
            bool lit = sig != 0 && m_Ctx.TurnSignalLit != null && m_Ctx.TurnSignalLit();
            int turnKey = lit ? sig + 10 : 0;
            if (turnKey != m_DLastTurn)
            {
                m_DLastTurn = turnKey;
                m_DTurnL.color = lit && (sig == -1 || sig == 2) ? P.TellGreen : P.TellOff;
                m_DTurnR.color = lit && (sig == 1 || sig == 2) ? P.TellGreen : P.TellOff;
            }

            // warnings
            HudWarningInput w;
            w.ParkingBrake = park && live;
            w.ParkDriveAway = m_ParkWarnTracker.Alpha > 0.01f;
            w.AirLow = low;
            w.TrailerEmergency = trailerEmergency;
            w.AbsFault = m_Ctx.AbsFault != null && m_Ctx.AbsFault();
            w.TrailerAbsFault = false;   // no trailer ABS fault model yet (cab cluster shows the same)
            w.AbsActive = absActive;
            int n = HudWarnings.Collect(w, m_DWarn);
            bool same = n == m_DWarnCount;
            for (int i = 0; same && i < m_DWarn.Length; i++) same = m_DWarn[i] == m_DWarnShown[i];
            if (!same)
            {
                m_DWarnCount = n;
                float x0 = DesktopHudLayout.TelltaleSize.x * 0.5f - (n * 160f + Mathf.Max(0, n - 1) * 8f) * 0.5f;
                for (int i = 0; i < m_DWarn.Length; i++)
                {
                    m_DWarnShown[i] = m_DWarn[i];
                    bool on = i < n;
                    if (m_DTile[i].gameObject.activeSelf != on) m_DTile[i].gameObject.SetActive(on);
                    if (!on) continue;
                    bool red = HudWarnings.IsRed(m_DWarn[i]);
                    m_DTileBg[i].color = red ? P.TellRed : P.TellAmber;
                    m_DTileText[i].color = red ? P.Ink : P.InkOnLight;
                    m_DTileText[i].text = HudTexts.Warning(m_DWarn[i]);
                    m_DTile[i].anchoredPosition = new Vector2(x0 + i * 168f, 0f);
                }
            }

            if (!m_Vis.Extended) return;
            int hundreds = Mathf.Clamp(Mathf.RoundToInt(rpm / 100f), 0, 25);
            if (hundreds != m_DLastRpm)
            {
                m_DLastRpm = hundreds;
                m_DRpm.text = HudTexts.RpmHundreds(hundreds);
                SetBar(m_DRpmBar, rpmMax > 1f ? rpm / rpmMax : 0f, false);
                m_DRpmBar.color = rpm > 1900f ? P.Accent : P.GaugeFill;
            }
            int lever = m_Ctx.RetarderLever != null ? Mathf.Clamp(m_Ctx.RetarderLever(), 0, HudTexts.RetarderStages.Length - 1) : 0;
            if (lever != m_DLastRet) { m_DLastRet = lever; m_DRet.text = HudTexts.RetarderStages[lever]; m_DRet.color = lever > 0 ? P.Accent : P.Ink; }
            int cruise = m_Ctx.BrakeCruiseKmh != null ? Mathf.RoundToInt(m_Ctx.BrakeCruiseKmh()) : 0;
            if (cruise != m_DLastCruise) { m_DLastCruise = cruise; m_DCruise.text = HudTexts.Cruise(cruise); }
        }

        static void SetBar(Image bar, float fraction, bool red)
        {
            bar.rectTransform.anchorMax = new Vector2(Mathf.Clamp01(fraction), 1f);
            bar.color = red ? P.TellRed : P.GaugeFill;
        }

        // ------------------------------------------------------------------ icon

        static Sprite s_ArrowSprite;

        /// <summary>Own turn-signal arrow (pointing left; the right one is mirrored): filled head + shaft, 96 x 80 px, built once.</summary>
        static Sprite ArrowSprite()
        {
            if (s_ArrowSprite != null) return s_ArrowSprite;
            const int w = 96, h = 80;
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };
            var px = new Color32[w * h];
            float cy = (h - 1) * 0.5f;
            for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                float dy = Mathf.Abs(y - cy);
                // head: triangle from the tip (x = 2) to x = 46, half height grows to 38; shaft: x 44..93, half height 13.
                float head = x >= 2f && x <= 46f ? Mathf.Clamp01((x - 2f) / 44f * 38f - dy + 0.5f) : 0f;
                float shaft = x >= 44f && x <= 93f ? Mathf.Clamp01(13.5f - dy) * Mathf.Clamp01(93.5f - x) : 0f;
                float a = Mathf.Max(head, shaft);
                px[y * w + x] = new Color32(255, 255, 255, (byte)(Mathf.Clamp01(a) * 255f));
            }
            tex.SetPixels32(px);
            tex.Apply(false, true);
            s_ArrowSprite = Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(0.5f, 0.5f), 100f);
            return s_ArrowSprite;
        }
    }
}
