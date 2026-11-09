using UnityEngine;
using T = Game.UI.CabDisplays.CabDisplayText;

namespace Game.UI.CabDisplays
{
    /// <summary>
    /// Overhead DIN units (512 x 256 design px = the A6 DIN texture shared by the tachograph, radio and bunk panel faces):
    /// the tachograph line now shows driver 1 driving time since the session start and the remaining daily driving time
    /// (EU 561/2006 art. 6: 9 h), the clock and the road speed; the radio / CB lines stay fixed (no radio feature).
    /// Negative LCD, green-yellow segments; refreshed once a second.
    /// </summary>
    public sealed class DinLayout
    {
        public const int Width = 512, Height = 256;
        /// <summary>Daily driving limit [min] (Regulation (EC) No 561/2006, art. 6(1)).</summary>
        public const int DailyDrivingMinutes = 9 * 60;
        static readonly Color32 Bg = new Color32(10, 12, 10, 255), Lcd = new Color32(150, 200, 120, 255), Radio = new Color32(220, 150, 60, 255);

        readonly TextBuffer m_B = new TextBuffer(32);

        public static void RequestGlyphs(DisplayCanvas d)
        {
            d.RequestGlyphs(T.Charset, 34f);
            d.RequestGlyphs(T.Charset, 44f);
        }

        public void Draw(DisplayCanvas d, in CabDisplayState s)
        {
            float k = s.Night ? DisplayPalette.ClusterNight : 1f;
            Color32 lcd = DisplayPalette.Scale(Lcd, k), radio = DisplayPalette.Scale(Radio, k);
            d.Begin();
            // Line 1: "1 ▶ 00h47  ‖ 08h13" (driver slot 1, activity driving, time driven, remaining).
            float x = 14f, y1 = 44f;
            x += d.Text("1", x, y1, 34f, lcd) + 12f;
            d.Triangle(new Vector2(x, y1 - 24f), new Vector2(x + 22f, y1 - 12f), new Vector2(x, y1), lcd);
            x += 34f;
            m_B.Clear().AppendDurationHm(s.DrivingMinutes);
            x += d.Text(m_B, x, y1, 34f, lcd) + 22f;
            d.Rect(x, y1 - 26f, 3f, 30f, lcd); d.Rect(x + 8f, y1 - 26f, 3f, 30f, lcd);
            x += 24f;
            m_B.Clear().AppendDurationHm(DailyDrivingMinutes - s.DrivingMinutes);
            d.Text(m_B, x, y1, 34f, lcd);

            // Line 2: "2 ●  14:32   82km/h" (driver slot 2 empty/rest, clock, speed).
            float y2 = 94f;
            x = 14f;
            x += d.Text("2", x, y2, 34f, lcd) + 16f;
            d.Disc(x + 10f, y2 - 12f, 11f, lcd);
            x += 42f;
            m_B.Clear().AppendClock(s.ClockMinutes);
            x += d.Text(m_B, x, y2, 34f, lcd) + 30f;
            m_B.Clear().Append(Mathf.RoundToInt(Mathf.Abs(s.SpeedKmh))).Append(T.KmH);
            d.Text(m_B, x, y2, 34f, lcd);

            d.Rect(0f, 126f, Width, 4f, new Color32(0, 0, 0, 255));
            float rx = 14f;
            rx += d.Text(T.RadioBand, rx, 182f, 44f, radio) + 26f;
            d.Text(T.RadioFreq, rx, 182f, 44f, radio);
            rx = 14f;
            rx += d.Text(T.CbChannel, rx, 230f, 34f, radio) + 30f;
            d.Text(T.CbMode, rx, 230f, 34f, radio);
            d.End(Bg);
        }
    }
}
