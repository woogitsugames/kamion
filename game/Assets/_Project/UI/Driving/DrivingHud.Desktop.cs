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
    /// alt-ui-polish-s23 (int-ui-s23 §7 p.4-6): the telltale row is the top row of the same panel (arrows inside it, a
    /// hairline between the rows), the "Panel" button hangs on the block's right edge in the same matte colour; in the
    /// cab with live instruments the extended detail shows only its own row, right of the wheel (no second speed);
    /// mirror windows are convex glass in a housing ring (ADR 0340: <see cref="MirrorWindowArt"/>, <see cref="UiPalette.MirrorBezel"/>).
    /// </summary>
    public sealed partial class DrivingHud
    {
        RectTransform m_DStrip, m_DTell, m_DExtRow, m_DMain;
        Image m_DTellBg, m_DSlotBgL, m_DSlotBgR;
        GameObject m_DTellRule;
        bool m_DBlockKnown, m_DBlockStrip, m_DBlockCompact;
        Text m_DSpeed, m_DGear, m_DAir1, m_DAir2, m_DRpm, m_DRet, m_DCruise;
        Image m_DAir1Bar, m_DAir2Bar, m_DRpmBar, m_DTurnL, m_DTurnR;
        GameObject m_DSlotL, m_DSlotR;
        readonly RectTransform[] m_DTile = new RectTransform[HudWarnings.MaxShown];
        readonly Image[] m_DTileBg = new Image[HudWarnings.MaxShown];
        readonly Text[] m_DTileText = new Text[HudWarnings.MaxShown];
        readonly HudWarning[] m_DWarn = new HudWarning[HudWarnings.MaxShown];
        readonly HudWarning[] m_DWarnShown = new HudWarning[HudWarnings.MaxShown];
        int m_DLimitH, m_DLimitW;
        /// <summary>ADR 0307: the GPS whose road-limit scout feeds the limit tiles (set by the navigation installer).</summary>
        [System.NonSerialized] public Game.UI.Navigation.NavigationService Nav;
        int m_DWarnCount = -1;
        DesktopHudInput m_DIn;
        DesktopHudResult m_D;
        Vector2 m_DScreenUnits, m_DContentOrigin, m_DMirrorOuterLimits;
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

        const float StripW = 720f, RowH = 112f, TileW = 184f, TilePitch = 192f;
        /// <summary>Visual QA only (editor control cameras have no live vehicle): shows the parking-brake tile.</summary>
        public static bool QaParkingBrakeTile;

        void BuildDesktop()
        {
            var strong = UiFonts.Strong;

            // ---- strip (bottom-left anchored zone; height follows the extended row)
            m_DStrip = Zone("DesktopStrip", new Vector2(StripW, RowH));
            var bg = m_DStrip.gameObject.AddComponent<Image>();
            bg.color = P.HudPanel; bg.raycastTarget = false;

            // Main row in its own container: the compact cab block hides it (the dash cluster shows speed / gear / air).
            m_DMain = Rect("MainRow", m_DStrip);
            Place(m_DMain, Vector2.zero, Vector2.zero, new Vector2(StripW, RowH));
            m_DSpeed = DLabel(m_DMain, "Speed", "0", strong, 68, TextAnchor.MiddleRight, P.Ink, new Vector2(12f, 12f), new Vector2(184f, 88f));
            DLabel(m_DMain, "SpeedUnit", HudTexts.KmH, m_Font, 22, TextAnchor.LowerLeft, P.InkMuted, new Vector2(202f, 26f), new Vector2(66f, 30f));
            DRule(m_DMain, "Rule1", new Vector2(276f, 16f), new Vector2(1f, 80f));
            m_DGear = DLabel(m_DMain, "Gear", "N", strong, 52, TextAnchor.MiddleCenter, P.Ink, new Vector2(278f, 14f), new Vector2(114f, 84f));
            DRule(m_DMain, "Rule2", new Vector2(394f, 16f), new Vector2(1f, 80f));
            m_DAir1 = AirRow(1, 62f, out m_DAir1Bar);
            m_DAir2 = AirRow(2, 20f, out m_DAir2Bar);

            // ---- extended row (above the main row inside the strip)
            m_DExtRow = Rect("ExtendedRow", m_DStrip);
            Place(m_DExtRow, Vector2.zero, new Vector2(0f, RowH), new Vector2(StripW, DesktopHudLayout.ExtendedRowHeight));
            DRule(m_DExtRow, "RuleTop", new Vector2(12f, 0f), new Vector2(StripW - 24f, 1f));
            m_DRpm = DLabel(m_DExtRow, "Rpm", "0", strong, 28, TextAnchor.MiddleRight, P.Ink, new Vector2(12f, 30f), new Vector2(100f, 36f));
            DLabel(m_DExtRow, "RpmUnit", HudTexts.Rpm, m_Font, 20, TextAnchor.MiddleLeft, P.InkMuted, new Vector2(118f, 30f), new Vector2(120f, 36f));
            m_DRpmBar = DBar(m_DExtRow, "RpmBar", new Vector2(16f, 16f), new Vector2(240f, 6f));
            DLabel(m_DExtRow, "RetCaption", HudTexts.Retarder, m_Font, 20, TextAnchor.MiddleLeft, P.InkMuted, new Vector2(290f, 50f), new Vector2(150f, 28f));
            m_DRet = DLabel(m_DExtRow, "Ret", "0", strong, 28, TextAnchor.MiddleLeft, P.Ink, new Vector2(290f, 12f), new Vector2(150f, 38f));
            DLabel(m_DExtRow, "CruiseCaption", HudTexts.BrakeCruise, m_Font, 20, TextAnchor.MiddleLeft, P.InkMuted, new Vector2(460f, 50f), new Vector2(248f, 28f));
            m_DCruise = DLabel(m_DExtRow, "Cruise", HudTexts.Off, strong, 28, TextAnchor.MiddleLeft, P.Ink, new Vector2(460f, 12f), new Vector2(248f, 38f));
            m_DExtRow.gameObject.SetActive(false);

            // ---- telltale row: arrow slots at the ends, warning tiles between. On the strip it is the top row of the same
            // panel (background on, hairline under it); alone (cab view) it has no background and the arrows keep a small one.
            m_DTell = Zone("DesktopTelltales", DesktopHudLayout.TelltaleSize);
            m_DTellBg = m_DTell.gameObject.AddComponent<Image>();
            m_DTellBg.color = P.HudPanel; m_DTellBg.raycastTarget = false; m_DTellBg.enabled = false;
            var rule = Rect("RowRule", m_DTell);
            Place(rule, Vector2.zero, new Vector2(12f, 0f), new Vector2(DesktopHudLayout.TelltaleSize.x - 24f, 1f));
            var ri = rule.gameObject.AddComponent<Image>(); ri.color = P.GaugeTrack; ri.raycastTarget = false;
            m_DTellRule = rule.gameObject;
            m_DTellRule.SetActive(false);
            m_DTurnL = ArrowSlot("TurnLeft", 0f, false);
            m_DTurnR = ArrowSlot("TurnRight", DesktopHudLayout.TelltaleSize.x - 64f, true);
            m_DSlotL = m_DTurnL.transform.parent.gameObject;
            m_DSlotR = m_DTurnR.transform.parent.gameObject;
            m_DSlotBgL = m_DSlotL.GetComponent<Image>();
            m_DSlotBgR = m_DSlotR.GetComponent<Image>();
            for (int i = 0; i < m_DTile.Length; i++)
            {
                var t = Rect("Warning" + i, m_DTell);
                Place(t, Vector2.zero, new Vector2(76f + i * TilePitch, 0f), new Vector2(TileW, DesktopHudLayout.TelltaleSize.y));
                m_DTileBg[i] = t.gameObject.AddComponent<Image>();
                m_DTileBg[i].color = P.TellRed; m_DTileBg[i].raycastTarget = false;
                // ADR 0344 addendum (critic build #10 "plakietka POSTOJOWY plaska jak naklejka UI"): the tile is a lit legend
                // lamp - a backlit lens recessed in a dark bezel (TelltaleLens), the tile colour multiplies it.
                m_DTileBg[i].sprite = TelltaleLens(); m_DTileBg[i].type = Image.Type.Sliced;
                m_DTileText[i] = DLabel(t, "Text", "", strong, 20, TextAnchor.MiddleCenter, P.Ink, new Vector2(10f, 0f), new Vector2(TileW - 20f, DesktopHudLayout.TelltaleSize.y));
                m_DTileText[i].horizontalOverflow = HorizontalWrapMode.Wrap;
                m_DTileText[i].resizeTextForBestFit = true; m_DTileText[i].resizeTextMinSize = 16; m_DTileText[i].resizeTextMaxSize = 20;
                m_DTile[i] = t;
                t.gameObject.SetActive(false);
            }
            m_DStrip.gameObject.SetActive(false);
            m_DTell.gameObject.SetActive(false);
        }

        Text AirRow(int circuit, float y, out Image bar)
        {
            DLabel(m_DMain, "AirLabel" + circuit, circuit == 1 ? "1" : "2", m_Font, 20, TextAnchor.MiddleCenter, P.InkMuted, new Vector2(408f, y), new Vector2(26f, 30f));
            bar = DBar(m_DMain, "AirBar" + circuit, new Vector2(438f, y + 12f), new Vector2(140f, 6f));
            var v = DLabel(m_DMain, "Air" + circuit, "0,0", UiFonts.Strong, 28, TextAnchor.MiddleRight, P.Ink, new Vector2(584f, y), new Vector2(68f, 32f));
            DLabel(m_DMain, "AirUnit" + circuit, HudTexts.Bar, m_Font, 20, TextAnchor.MiddleLeft, P.InkMuted, new Vector2(656f, y), new Vector2(56f, 32f));
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
            bool cab = m_Ctx.IsCabView;   // D90 / ADR 0294
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
            d.MirrorWide = m_Ctx.LeftWideMirrorTexture != null && m_Ctx.RightWideMirrorTexture != null
                && m_Ctx.LeftWideMirrorTexture() != null && m_Ctx.RightWideMirrorTexture() != null;
            d.ReverseView = m_Ctx.ReverseCameraTexture != null && m_Ctx.ReverseCameraTexture() != null;
            d.DevToggle = m_Vis.DevToggle;
            d.DevPanelOpen = m_DevOpen;
            d.Telemetry = TelemetryVisible;
            d.DevText = DevDiagnostics;
            d.Compact = m_Vis.Compact;
            if (screenChanged || !m_DesktopApplied)
            {
                m_DScreenUnits = m_View.PixelSize / m_View.PixelsPerUnit;
                m_DContentOrigin = Vector2.Scale(m_SafeArea.anchorMin, m_DScreenUnits);
                float reserve = MirrorWindowArt.HeadOut + MirrorWindowLayout.MountEdgeGap;
                m_DMirrorOuterLimits = new Vector2(reserve - m_DContentOrigin.x,
                    reserve - (1f - m_SafeArea.anchorMax.x) * m_DScreenUnits.x);
            }
            d.ScreenWidth = m_DScreenUnits.x;
            d.MirrorOuterLimits = cab && (m_Ctx.LeftMirrorMountViewport != null || m_Ctx.RightMirrorMountViewport != null)
                ? m_DMirrorOuterLimits : (Vector2?)null;
            if (!screenChanged && m_DValid && m_DesktopApplied && d.SameAs(m_DIn) && m_DPrefsVersion == HudPreferences.Version) return;
            m_DIn = d; m_DValid = true; m_DPrefsVersion = HudPreferences.Version;
            DesktopHudLayout.Solve(d, out m_D);
            // ADR 0342: the class II texture follows the window (PC High / Ultra: rows per window pixel row); 0 = no window shown.
            {
                Rect mw = m_D.ShowMirrorLeft ? m_D.MirrorLeft : m_D.ShowMirrorRight ? m_D.MirrorRight : default;
                Game.Core.MirrorOverrides.WindowPixelHeight = mw.height > 0f
                    ? Mathf.Max(0f, mw.height - 2f * DesktopHudLayout.MirrorBezel) * m_View.PixelsPerUnit : 0f;
            }

            if (!m_DesktopApplied) ApplyFormFactor(true);
            SetRect(m_DStrip, m_D.Strip);
            SetRect(m_DTell, m_D.Telltales);
            if (m_DStrip.gameObject.activeSelf != m_D.ShowStrip) m_DStrip.gameObject.SetActive(m_D.ShowStrip);
            if (m_DExtRow.gameObject.activeSelf != m_Vis.Extended) m_DExtRow.gameObject.SetActive(m_Vis.Extended);
            ApplyBlockStyle(m_D.ShowStrip, m_D.Compact);
            SetRect((RectTransform)m_MirrorLGo.transform, m_D.MirrorLeft);
            SetRect((RectTransform)m_MirrorRGo.transform, m_D.MirrorRight);
            LayoutMirrorHead(m_HeadL, m_D.MirrorLeft, m_D.MirrorWideLeft, m_D.ShowMirrorWide, d.MirrorOuterLimits.HasValue);
            LayoutMirrorHead(m_HeadR, m_D.MirrorRight, m_D.MirrorWideRight, m_D.ShowMirrorWide, d.MirrorOuterLimits.HasValue);
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
            m_L.Desktop = true; m_L.Nav = m_D.Nav; m_L.ShowNav = m_D.ShowNav;

            bool grid = m_DevOpen && !m_LabOpen, lab = m_DevOpen && m_LabOpen;
            if (m_DevPanelRt.gameObject.activeSelf != grid) m_DevPanelRt.gameObject.SetActive(grid);
            if (m_LabPanel.activeSelf != lab) m_LabPanel.SetActive(lab);
            m_DevToggleImage.color = m_DevOpen ? P.ButtonPressed : P.HudPanel;   // same matte block as the strip
            string tl = m_DevOpen ? HudTexts.DevToggleOpen : HudTexts.DevToggle;
            if (!ReferenceEquals(m_DevToggleLabel.text, tl)) m_DevToggleLabel.text = tl;
            m_LayoutValid = false;   // the touch branch lays out again when the form factor flips back
        }

        /// <summary>Strip + telltale row as one panel, or the row alone; compact cab block = extended row only (on change only).</summary>
        void ApplyBlockStyle(bool strip, bool compact)
        {
            if (m_DBlockKnown && m_DBlockStrip == strip && m_DBlockCompact == compact) return;
            m_DBlockKnown = true; m_DBlockStrip = strip; m_DBlockCompact = compact;
            m_DTellBg.enabled = strip;
            m_DTellRule.SetActive(strip);
            m_DSlotBgL.enabled = !strip;   // inside the panel the arrows need no box of their own
            m_DSlotBgR.enabled = !strip;
            m_DMain.gameObject.SetActive(!compact);
            m_DExtRow.anchoredPosition = new Vector2(0f, compact ? 0f : RowH);
            m_DLastTurn = int.MinValue;   // slot visibility depends on the block
        }

        /// <summary>Shows the monitor or the touch furniture (once per form-factor change).</summary>
        void ApplyFormFactor(bool desktop)
        {
            if (m_DesktopKnown && m_DesktopApplied == desktop) return;
            m_DesktopKnown = true;
            m_DesktopApplied = desktop;
            m_ClusterRt.gameObject.SetActive(!desktop);
            m_ParkWarnRt.gameObject.SetActive(!desktop);
            if (desktop)
            {
                // Touch controls are never on a monitor (the touch branch re-enables them from its own layout).
                m_TurnRt.gameObject.SetActive(false); m_StalkRt.gameObject.SetActive(false); m_BrakeRt.gameObject.SetActive(false);
                m_ThrottleRt.gameObject.SetActive(false); m_GearsRt.gameObject.SetActive(false);
            }
            if (m_DStrip != null) m_DStrip.gameObject.SetActive(desktop && m_D.ShowStrip);
            if (m_DTell != null) m_DTell.gameObject.SetActive(desktop);
            if (!desktop && !m_DevToggleRt.gameObject.activeSelf) m_DevToggleRt.gameObject.SetActive(true);
            MirrorHousingStyle(m_HeadL, desktop);
            MirrorHousingStyle(m_HeadR, desktop);
            m_DValid = false;
            m_LayoutValid = false;
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
            int turnKey = (lit ? sig + 10 : 0) + (m_D.ShowStrip ? 100 : 0);
            if (turnKey != m_DLastTurn)
            {
                m_DLastTurn = turnKey;
                bool l = lit && (sig == -1 || sig == 2), r = lit && (sig == 1 || sig == 2);
                m_DTurnL.color = l ? P.TellGreen : P.TellOff;
                m_DTurnR.color = r ? P.TellGreen : P.TellOff;
                // Cab view with live cab screens: the cluster in the dash has the arrows; here they appear only while lit.
                bool always = m_D.ShowStrip;
                if (m_DSlotL.activeSelf != (always || l)) m_DSlotL.SetActive(always || l);
                if (m_DSlotR.activeSelf != (always || r)) m_DSlotR.SetActive(always || r);
            }

            // warnings
            HudWarningInput w;
            w.ParkingBrake = park && live || QaParkingBrakeTile;
            w.ParkDriveAway = m_ParkWarnTracker.Alpha > 0.01f;
            w.AirLow = low;
            w.TrailerEmergency = trailerEmergency;
            w.AbsFault = m_Ctx.AbsFault != null && m_Ctx.AbsFault();
            w.TrailerAbsFault = false;   // no trailer ABS fault model yet (cab cluster shows the same)
            w.AbsActive = absActive;
            // ADR 0307 (D91): limit of the road ahead below the combination (GPS scout, 500 m before); warning only
            w.RoadLimitHeightCm = 0; w.RoadLimitWeightC = 0; w.RoadLimitOther = false;
            if (Nav != null)
            {
                var rw = Nav.Restriction;
                if (rw.Active)
                {
                    var ex = rw.R.Exceeded;
                    if ((ex & Game.Core.Navigation.LimitKind.Height) != 0) w.RoadLimitHeightCm = rw.R.MaxHeightCm;
                    if ((ex & Game.Core.Navigation.LimitKind.Weight) != 0) w.RoadLimitWeightC = rw.R.MaxWeightC;
                    w.RoadLimitOther = (ex & (Game.Core.Navigation.LimitKind.AxleLoad | Game.Core.Navigation.LimitKind.Length)) != 0;
                }
            }
            int n = HudWarnings.Collect(w, m_DWarn);
            bool same = n == m_DWarnCount && w.RoadLimitHeightCm == m_DLimitH && w.RoadLimitWeightC == m_DLimitW;
            m_DLimitH = w.RoadLimitHeightCm; m_DLimitW = w.RoadLimitWeightC;
            for (int i = 0; same && i < m_DWarn.Length; i++) same = m_DWarn[i] == m_DWarnShown[i];
            if (!same)
            {
                m_DWarnCount = n;
                float x0 = DesktopHudLayout.TelltaleSize.x * 0.5f - (n * TileW + Mathf.Max(0, n - 1) * (TilePitch - TileW)) * 0.5f;
                for (int i = 0; i < m_DWarn.Length; i++)
                {
                    m_DWarnShown[i] = m_DWarn[i];
                    bool on = i < n;
                    if (m_DTile[i].gameObject.activeSelf != on) m_DTile[i].gameObject.SetActive(on);
                    if (!on) continue;
                    bool red = HudWarnings.IsRed(m_DWarn[i]);
                    m_DTileBg[i].color = red ? P.TellRed : P.TellAmber;
                    m_DTileText[i].color = red ? P.Ink : P.InkOnLight;
                    m_DTileText[i].text = HudTexts.Warning(m_DWarn[i], w);
                    m_DTile[i].anchoredPosition = new Vector2(x0 + i * TilePitch, 0f);
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

        static Sprite s_ArrowSprite, s_LensSprite;

        /// <summary>Margin of the lens sprite outside the bezel (contact shadow) and the bezel width [canvas units].</summary>
        public const float LensShadow = 2.5f, LensBezel = 2.5f;

        /// <summary>
        /// Warning tile as a physical legend lamp (ADR 0344 addendum), nine-sliced, white so the tile colour tints it:
        /// a near-black bezel with rounded corners (top edge catches light), the lens recessed inside it (the bezel's
        /// shadow along the top inner edge, a thin light catch along the bottom), the backlight brighter in the middle
        /// than at the rim (a diffuser in front of a lamp is never even), and a soft shadow on the panel around it.
        /// 64 x 64 px, built once; no brand marks.
        /// </summary>
        public static Sprite TelltaleLens()
        {
            if (s_LensSprite != null) return s_LensSprite;
            const int n = 64;
            const float ppu = 2f;
            float m = LensShadow * ppu, ro = 7f * ppu, bz = LensBezel * ppu;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear, name = "TelltaleLens" };
            tex.hideFlags = HideFlags.HideAndDontSave;
            var px = new Color32[n * n];
            for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                float fx = x + 0.5f, fy = y + 0.5f;
                float d = LensRoundRect(fx, fy, n, m, ro);                 // < 0 inside the bezel outline
                float up = (fy / n - 0.5f) * 2f;                           // -1 bottom .. +1 top
                float inside = Mathf.Clamp01(0.5f - d);
                float lens = Mathf.Clamp01(-d - bz + 0.5f);                // 1 on the lens
                float depth = Mathf.Max(0f, -d - bz);                      // px into the lens from the bezel
                // lens: backlit diffuser - hot middle, dimmer rim, recess shadow under the top bezel, light catch at the bottom
                float rimT = Mathf.Clamp01(depth / 9f);
                float l = 0.66f + 0.34f * rimT * rimT * (3f - 2f * rimT);
                l *= 1f - 0.38f * Mathf.Max(0f, up) * Mathf.Clamp01(1f - depth / 4f);
                l += 0.10f * Mathf.Max(0f, -up) * Mathf.Clamp01(1f - depth / 2.5f);
                // bezel: dark moulding, lit on its upper outer edge
                float bzl = 0.055f + 0.16f * Mathf.Max(0f, up) * Mathf.Clamp01(1f - (-d) / bz);
                float c = Mathf.Lerp(bzl, l, lens);
                // shadow on the panel below / around the bezel
                float ds = LensRoundRect(fx, fy + 1.5f, n, m, ro);
                float sh = Mathf.Clamp01(1f - ds / m) * 0.38f;
                float a = inside + (1f - inside) * sh;
                float k = a > 1e-4f ? inside / a : 0f;
                byte v = (byte)(Mathf.Clamp01(c * k) * 255f);
                px[y * n + x] = new Color32(v, v, v, (byte)(Mathf.Clamp01(a) * 255f));
            }
            tex.SetPixels32(px);
            tex.Apply(false, true);
            float b = Mathf.Ceil(m + ro + 9f);
            s_LensSprite = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), 100f * ppu, 0, SpriteMeshType.FullRect, new Vector4(b, b, b, b));
            s_LensSprite.hideFlags = HideFlags.HideAndDontSave;
            return s_LensSprite;
        }

        static float LensRoundRect(float x, float y, float n, float inset, float radius)
        {
            float h = n * 0.5f - inset;
            float qx = Mathf.Abs(x - n * 0.5f) - (h - radius), qy = Mathf.Abs(y - n * 0.5f) - (h - radius);
            float ox = Mathf.Max(qx, 0f), oy = Mathf.Max(qy, 0f);
            return Mathf.Sqrt(ox * ox + oy * oy) + Mathf.Min(Mathf.Max(qx, qy), 0f) - radius;
        }

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
