using UnityEngine;
using P = Game.UI.CabDisplays.DisplayPalette;
using T = Game.UI.CabDisplays.CabDisplayText;

namespace Game.UI.CabDisplays
{
    /// <summary>
    /// The 12.3" instrument cluster (D20: screen only, no analogue dials), 1560 x 600 design px = the A6 texture layout
    /// (same quad UVs), now drawn live from <see cref="CabDisplayState"/>:
    /// - top: telltale row in the r3b order (park, brake, air, ABS, trailer ABS, retarder, MIL, preheat, battery, oil,
    ///   coolant, belt, beam) - only lit lamps are drawn, in full ISO 2575 colour (review r4 C-N2); turn-signal arrows at
    ///   the ends;
    /// - left: rev counter 0-2500 1/min with the green band at the engine's torque plateau and the red zone above the
    ///   governed speed; fuel and AdBlue bars below;
    /// - centre: digital road speed, brake cruise and endurance-brake stage, AMT gear box (A/M, gear or N/R, shift arrow);
    /// - right: clock, outside temperature, odometer, trip, trip average, range; both air-brake circuits with the
    ///   low-pressure mark.
    /// </summary>
    public sealed class ClusterLayout
    {
        public const int Width = 1560, Height = 600;
        public const float RevMax = 2500f;
        const float RevCx = 250f, RevCy = 300f, RevR = 205f, RevA0 = 210f, RevA1 = -30f;

        readonly TextBuffer m_B = new TextBuffer(40);
        float m_K = 1f;   // night dimming

        Color32 C(Color32 c) => m_K >= 0.999f ? c : P.Scale(c, m_K);

        public static void RequestGlyphs(DisplayCanvas d)
        {
            d.RequestGlyphs(T.Digits, 196f);
            d.RequestGlyphs(T.Charset, 70f);
            foreach (float s in s_TextSizes) d.RequestGlyphs(T.Charset, s);
        }

        static readonly float[] s_TextSizes = { 44f, 36f, 32f, 30f, 28f, 26f, 24f, 22f, 13f, 12f };

        static float RevAngle(float rpm) => RevA0 + (RevA1 - RevA0) * Mathf.Clamp(rpm, 0f, RevMax) / RevMax;

        public void Draw(DisplayCanvas d, in CabDisplayState s)
        {
            m_K = s.Night ? P.ClusterNight : 1f;
            d.Begin();
            Telltales(d, s);
            RevCounter(d, s);
            Speed(d, s);
            Gear(d, s);
            TripComputer(d, s);
            Levels(d, s);
            Air(d, s);
            d.End(P.ClusterBg);
        }

        // ------------------------------------------------------------------ rev counter

        void RevCounter(DisplayCanvas d, in CabDisplayState s)
        {
            // Green economy band (torque plateau) and dim red zone above the governed maximum.
            if (s.EcoHighRpm > s.EcoLowRpm)
                d.Arc(RevCx, RevCy, RevR - 13f, RevR - 3f, RevAngle(s.EcoLowRpm), RevAngle(s.EcoHighRpm), C(P.Band));
            if (s.MaxRpm > 0f && s.MaxRpm < RevMax)
                d.Arc(RevCx, RevCy, RevR - 13f, RevR - 3f, RevAngle(s.MaxRpm), RevAngle(RevMax), C(P.RedZone));
            // Ticks every 100 1/min, major every 500 with numerals x100.
            for (int i = 0; i <= 25; i++)
            {
                bool major = i % 5 == 0;
                float a = RevAngle(i * 100f) * Mathf.Deg2Rad;
                float ca = Mathf.Cos(a), sa = -Mathf.Sin(a);
                float l = major ? 24f : 12f;
                d.Line(RevCx + RevR * ca, RevCy + RevR * sa, RevCx + (RevR - l) * ca, RevCy + (RevR - l) * sa,
                    major ? 4f : 3f, C(major ? P.White : P.Grey), false);
                if (major)
                {
                    m_B.Clear().Append(i);
                    float tx = RevCx + (RevR - 56f) * ca, ty = RevCy + (RevR - 56f) * sa;
                    d.Text(m_B, tx, ty + 11f, 32f, C(P.White), DisplayCanvas.Align.Center);
                }
            }
            d.Text(T.RpmUnit, RevCx, RevCy + 78f, 24f, C(P.Grey), DisplayCanvas.Align.Center);
            // Needle (engine off: rests at 0).
            float na = RevAngle(s.EngineRpm) * Mathf.Deg2Rad;
            float nc = Mathf.Cos(na), ns = -Mathf.Sin(na);
            d.Line(RevCx - 26f * nc, RevCy - 26f * ns, RevCx + (RevR - 14f) * nc, RevCy + (RevR - 14f) * ns, 7f, C(P.Needle), false);
            d.Disc(RevCx, RevCy, 20f, C(P.Hub));
            d.Ring(RevCx, RevCy, 19f, 21f, C(P.Dim));
        }

        // ------------------------------------------------------------------ speed

        void Speed(DisplayCanvas d, in CabDisplayState s)
        {
            const float cx = Width * 0.5f;
            int v = Mathf.RoundToInt(Mathf.Abs(s.SpeedKmh));
            m_B.Clear().Append(v);
            d.Text(m_B, cx, 228f, 196f, C(P.White), DisplayCanvas.Align.Center);
            d.Text(T.KmH, cx, 297f, 36f, C(P.Grey), DisplayCanvas.Align.Center);

            // Brake cruise (downhill speed control) on the left, endurance brake stage on the right.
            if (s.BrakeCruiseKmh > 0f)
            {
                float x = d.Text(T.BrakeCruise, cx - 175f, 349f, 30f, C(P.TellGreen));
                m_B.Clear().Append(Mathf.RoundToInt(s.BrakeCruiseKmh));
                d.Text(m_B, cx - 175f + x + 10f, 349f, 30f, C(P.TellGreen));
            }
            if (s.RetarderLever > 0)
            {
                // "EB" for the engine brake, then one box per retarder stage, filled up to the stalk position.
                Color32 lab = C(s.RetarderFill > 0.05f || s.RetarderLever == 1 ? P.White : P.Grey);
                float x = cx + 40f;
                x += d.Text(s.RetarderLever == 1 ? T.EngineBrake : T.Retarder, x, 349f, 30f, lab) + 12f;
                for (int i = 0; i < s.RetarderStages; i++)
                {
                    bool on = i < s.RetarderLever - 1;
                    if (on) d.Rect(x, 327f, 18f, 22f, C(P.White));
                    else d.RectOutline(x, 327f, 18f, 22f, 2f, C(P.Dim));
                    x += 24f;
                }
            }
            else if (s.HillHold)
            {
                d.Text(T.HillHold, cx + 60f, 349f, 30f, C(P.TellGreen));
            }
        }

        // ------------------------------------------------------------------ AMT gear

        void Gear(DisplayCanvas d, in CabDisplayState s)
        {
            const float cx = Width * 0.5f, y = 400f, h = 100f, w = 300f, r = 12f;
            Color32 panel = C(P.Panel);
            d.Rect(cx - w * 0.5f + r, y, w - 2f * r, h, panel);
            d.Rect(cx - w * 0.5f, y + r, r, h - 2f * r, panel);
            d.Rect(cx + w * 0.5f - r, y + r, r, h - 2f * r, panel);
            d.Disc(cx - w * 0.5f + r, y + r, r, panel); d.Disc(cx + w * 0.5f - r, y + r, r, panel);
            d.Disc(cx - w * 0.5f + r, y + h - r, r, panel); d.Disc(cx + w * 0.5f - r, y + h - r, r, panel);

            const float baseline = 478f;
            d.Text(s.ManualMode ? T.Manual : T.Auto, cx - 128f, baseline, 70f, C(P.Grey));
            int shown = s.ShiftTarget != 0 ? s.ShiftTarget : s.Gear;
            Color32 gc = C(s.ShiftTarget != 0 ? P.Grey : P.White);
            if (s.Selector == 'N' || shown == 0) d.Text(T.Neutral, cx - 22f, baseline, 70f, gc);
            else if (shown < 0 || s.Selector == 'R')
            {
                m_B.Clear().Append(T.Reverse).Append(Mathf.Max(1, Mathf.Abs(shown)));
                d.Text(m_B, cx - 22f, baseline, 70f, gc);
            }
            else
            {
                m_B.Clear().Append(shown);
                d.Text(m_B, cx - 22f, baseline, 70f, gc);
            }
            // Shift in progress: arrow up / down next to the gear (the AMT works, the driver sees why the pull stopped).
            if (s.ShiftTarget != 0 && s.Gear != 0 && s.ShiftTarget != s.Gear)
            {
                bool up = Mathf.Abs(s.ShiftTarget) > Mathf.Abs(s.Gear);
                float ax = cx + 110f, ay = 450f;
                Color32 ac = C(P.TellGreen);
                if (up) d.Triangle(new Vector2(ax - 14f, ay + 10f), new Vector2(ax + 14f, ay + 10f), new Vector2(ax, ay - 14f), ac);
                else d.Triangle(new Vector2(ax - 14f, ay - 10f), new Vector2(ax, ay + 14f), new Vector2(ax + 14f, ay - 10f), ac);
            }
        }

        // ------------------------------------------------------------------ trip computer (right top)

        void TripComputer(DisplayCanvas d, in CabDisplayState s)
        {
            const float x0 = 1150f, x1 = 1350f;
            m_B.Clear().AppendClock(s.ClockMinutes);
            d.Text(m_B, x0, 99f, 30f, C(P.White));
            int t = Mathf.RoundToInt(s.OutsideTempC);
            m_B.Clear();
            if (t > 0) m_B.Append('+');
            m_B.Append(t).Append(T.DegC);
            d.Text(m_B, x1, 99f, 30f, C(P.White));

            m_B.Clear().Append((long)s.OdometerKm, 1, true).Append(' ').Append(T.Km);
            d.Text(m_B, x0, 159f, 30f, C(P.Grey));
            m_B.Clear().Append(T.TripPrefix).AppendFixed(s.TripKm, 1, true).Append(' ').Append(T.Km);
            d.Text(m_B, x1, 159f, 30f, C(P.Grey));

            d.Rect(x0, 204f, Width - 40f - x0, 2f, C(P.Dim));

            if (float.IsNaN(s.AvgConsumption)) d.Text(T.AvgNone, x0, 257f, 30f, C(P.Grey));
            else
            {
                m_B.Clear().Append(T.AvgPrefix).AppendFixed(s.AvgConsumption, 1).Append(T.AvgUnit);
                d.Text(m_B, x0, 257f, 30f, C(P.Grey));
            }
            d.Text(T.Range, x0, 309f, 30f, C(P.Grey));
            m_B.Clear().Append(Mathf.RoundToInt(s.RangeKm), 1, true).Append(' ').Append(T.Km);
            d.Text(m_B, Width - 40f, 309f, 30f, C(s.FuelLitres < 0.1f * s.FuelCapacityLitres ? P.TellAmber : P.White), DisplayCanvas.Align.Right);
        }

        // ------------------------------------------------------------------ fuel / AdBlue (left bottom)

        void Levels(DisplayCanvas d, in CabDisplayState s)
        {
            float fuel = s.FuelCapacityLitres > 0f ? Mathf.Clamp01(s.FuelLitres / s.FuelCapacityLitres) : 0f;
            Bar(d, 470f, T.Fuel, fuel, fuel < 0.1f ? P.TellAmber : P.White);
            float ad = Mathf.Clamp01(s.AdBlueFraction);
            Bar(d, 522f, T.AdBlue, ad, ad < 0.1f ? P.TellAmber : P.AdBlue);
        }

        void Bar(DisplayCanvas d, float y, string label, float frac, Color32 col)
        {
            d.Text(label, 40f, y + 17f, 26f, C(P.Grey));
            d.RectOutline(150f, y, 200f, 18f, 2f, C(P.Dim));
            if (frac > 0f) d.Rect(153f, y + 3f, 194f * frac, 12f, C(col));
            for (int k = 1; k < 4; k++) d.Rect(150f + 50f * k - 1f, y + 18f, 2f, 8f, C(P.Dim));
        }

        // ------------------------------------------------------------------ air circuits (right bottom)

        void Air(DisplayCanvas d, in CabDisplayState s)
        {
            const float full = 12.5f;
            d.Text(T.Bar, 1460f, 431f, 24f, C(P.Grey));
            for (int i = 0; i < 2; i++)
            {
                float v = i == 0 ? s.AirCircuit1Bar : s.AirCircuit2Bar, y = 470f + i * 52f;
                bool low = v < s.AirWarnBar;
                d.Text(i == 0 ? "I" : "II", 1200f, y + 17f, 26f, C(P.Grey));
                d.RectOutline(1240f, y, 180f, 18f, 2f, C(P.Dim));
                float f = Mathf.Clamp01(v / full);
                if (f > 0f) d.Rect(1243f, y + 3f, 174f * f, 12f, C(low ? P.TellRed : P.White));
                float mx = 1240f + 180f * s.AirWarnBar / full;
                d.Rect(mx - 1f, y - 4f, 2f, 26f, C(P.Grey));
                m_B.Clear().AppendFixed(v, 1);
                d.Text(m_B, 1432f, y + 18f, 28f, C(low ? P.TellRed : P.White));
            }
        }

        // ------------------------------------------------------------------ telltales

        const float TY = 12f, TS = 44f, TP = 72f, TW = 4f;
        enum Lamp { Park, Brake, Air, Abs, TrailerAbs, Retarder, Mil, Preheat, Battery, Oil, Coolant, Belt, Beam }

        void Telltales(DisplayCanvas d, in CabDisplayState s)
        {
            float x0 = (Width - TP * 12f - TS) * 0.5f;
            float X(Lamp l) => x0 + (int)l * TP;
            if (s.ParkingBrake) RingLamp(d, X(Lamp.Park), C(P.TellRed), "P", 24f);
            if (s.AirLowWarning) RingLamp(d, X(Lamp.Brake), C(P.TellRed), "!", 24f);
            if (s.AirLowWarning)
            {
                RingLamp(d, X(Lamp.Air), C(P.TellRed), "I II", 13f);
                d.Rect(X(Lamp.Air) + 10f, TY + TS, TS - 20f, 2f, C(P.TellRed));
            }
            if (s.AbsFault) RingLamp(d, X(Lamp.Abs), C(P.TellAmber), "ABS", 12f);
            if (s.TrailerAbsFault) TrailerLamp(d, X(Lamp.TrailerAbs), C(P.TellAmber));
            if (s.RetarderLever >= 2) RingLamp(d, X(Lamp.Retarder), C(P.TellGreen), "R", 24f);
            if (!s.EngineRunning)
            {
                BatteryLamp(d, X(Lamp.Battery), C(P.TellRed));
                OilLamp(d, X(Lamp.Oil), C(P.TellRed));
            }
            if (s.HighBeam) BeamLamp(d, X(Lamp.Beam), C(P.TellBlue), true);
            else if (s.LowBeam) BeamLamp(d, X(Lamp.Beam), C(P.TellGreen), false);
            // Turn signals: green arrows at both ends of the row, flashing with the relay.
            if (s.FlasherOn && (s.Indicators == -1 || s.Indicators == 2)) Arrow(d, 60f, true, C(P.TellGreen));
            if (s.FlasherOn && (s.Indicators == 1 || s.Indicators == 2)) Arrow(d, Width - 60f, false, C(P.TellGreen));
        }

        void RingLamp(DisplayCanvas d, float x, Color32 c, string text, float size)
        {
            float cx = x + TS * 0.5f, cy = TY + TS * 0.5f;
            d.Ring(cx, cy, 16f - TW * 0.5f, 16f + TW * 0.5f, c);
            // Brake-drum brackets left and right of the circle.
            d.Arc(x + 16f, cy, 20f - TW * 0.5f, 20f + TW * 0.5f, 125f, 235f, c);
            d.Arc(x + TS - 16f, cy, 20f - TW * 0.5f, 20f + TW * 0.5f, -55f, 55f, c);
            d.Text(text, cx, cy + size * 0.36f, size, c, DisplayCanvas.Align.Center);
        }

        void TrailerLamp(DisplayCanvas d, float x, Color32 c)
        {
            d.RectOutline(x + 2f, TY + 8f, TS - 8f, 20f, TW, c);
            d.Rect(x + TS - 6f, TY + 20f, 8f, TW, c);
            d.Ring(x + 10f, TY + 33f, 3.5f, 6.5f, c);
            d.Ring(x + 22f, TY + 33f, 3.5f, 6.5f, c);
            d.Text("ABS", x + 18f, TY + 23f, 11f, c, DisplayCanvas.Align.Center);
        }

        void BatteryLamp(DisplayCanvas d, float x, Color32 c)
        {
            d.RectOutline(x + 4f, TY + 12f, TS - 8f, 24f, TW, c);
            d.Rect(x + 10f, TY + 7f, 6f, 5f, c);
            d.Rect(x + TS - 16f, TY + 7f, 6f, 5f, c);
            d.Rect(x + 10f, TY + 22f, 8f, 3f, c);
            d.Rect(x + TS - 18f, TY + 22f, 8f, 3f, c);
            d.Rect(x + TS - 15.5f, TY + 19f, 3f, 9f, c);
        }

        void OilLamp(DisplayCanvas d, float x, Color32 c)
        {
            // Oil can: body, spout, drop.
            d.RectOutline(x + 6f, TY + 18f, 26f, 16f, TW, c);
            d.Line(x + 30f, TY + 20f, x + 42f, TY + 12f, TW, c);
            d.Line(x + 10f, TY + 18f, x + 16f, TY + 13f, TW, c);
            d.Disc(x + 42f, TY + 30f, 3.5f, c);
        }

        void BeamLamp(DisplayCanvas d, float x, Color32 c, bool high)
        {
            // Lamp body (half disc) and three beams: dipped beams slope down, main beams are horizontal.
            d.Arc(x + 22f, TY + 22f, 0f, 18f, 90f, 270f, c);
            d.Rect(x + 20f, TY + 4f, 4f, 36f, c);
            for (int k = 0; k < 3; k++)
            {
                float y = TY + 10f + 12f * k;
                d.Line(x + 30f, y, x + 52f, high ? y : y + 6f, TW, c);
            }
        }

        void Arrow(DisplayCanvas d, float cx, bool left, Color32 c)
        {
            float cy = TY + TS * 0.5f, s = left ? -1f : 1f;
            d.Triangle(new Vector2(cx + s * 22f, cy), new Vector2(cx, cy - 18f), new Vector2(cx, cy + 18f), c);
            d.Rect(left ? cx : cx - 18f, cy - 7f, 18f, 14f, c);
        }
    }
}
