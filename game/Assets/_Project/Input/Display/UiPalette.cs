using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// WCAG 2.x contrast maths (relative luminance, contrast ratio, alpha compositing). Pure, no allocation. Lives in
    /// Game.Controls so the EditMode tests can check every colour pair of <see cref="UiPalette"/> (ADR 0283).
    /// Translucent HUD panels are composited in LINEAR light (the project renders in linear colour space, uGUI blends
    /// there), against a worst-case background (white sky / snow), not against black.
    /// </summary>
    public static class UiContrast
    {
        /// <summary>WCAG 2.x AA: normal text.</summary>
        public const float AaText = 4.5f;
        /// <summary>WCAG 2.x AA: large text (&gt;= 24 px regular / 18.66 px bold) and non-text UI parts (1.4.11).</summary>
        public const float AaLargeOrGraphic = 3f;

        /// <summary>sRGB channel (0..1) to linear light (WCAG 2.x / IEC 61966-2-1).</summary>
        public static float ToLinear(float c) => c <= 0.04045f ? c / 12.92f : Mathf.Pow((c + 0.055f) / 1.055f, 2.4f);

        /// <summary>Relative luminance of an opaque sRGB colour (alpha ignored).</summary>
        public static float Luminance(Color c) => 0.2126f * ToLinear(c.r) + 0.7152f * ToLinear(c.g) + 0.0722f * ToLinear(c.b);

        /// <summary>Contrast ratio (1..21) of two relative luminances.</summary>
        public static float Ratio(float l1, float l2)
        {
            float hi = Mathf.Max(l1, l2), lo = Mathf.Min(l1, l2);
            return (hi + 0.05f) / (lo + 0.05f);
        }

        /// <summary>Contrast ratio of two opaque sRGB colours.</summary>
        public static float Ratio(Color a, Color b) => Ratio(Luminance(a), Luminance(b));

        /// <summary>Relative luminance of <paramref name="fg"/> (with its alpha) drawn over an opaque <paramref name="bg"/>,
        /// blended in linear light.</summary>
        public static float CompositeLuminance(Color fg, Color bg)
        {
            float a = Mathf.Clamp01(fg.a);
            float r = a * ToLinear(fg.r) + (1f - a) * ToLinear(bg.r);
            float g = a * ToLinear(fg.g) + (1f - a) * ToLinear(bg.g);
            float b = a * ToLinear(fg.b) + (1f - a) * ToLinear(bg.b);
            return 0.2126f * r + 0.7152f * g + 0.0722f * b;
        }

        /// <summary>Opaque text <paramref name="text"/> on a translucent <paramref name="panel"/> over <paramref name="scene"/>.</summary>
        public static float RatioOnTranslucent(Color text, Color panel, Color scene) =>
            Ratio(Luminance(text), CompositeLuminance(panel, scene));
    }

    /// <summary>
    /// The one colour table of the UI (ADR 0283, D84 "HUD i menu zbyt AI slop"): menus, settings, driving HUD and mirror
    /// frames share it. Own look, taken from what a truck display actually is - a near-black, matte screen with warm
    /// white type, one amber accent for selection, and telltale colours only where ISO 2575 gives them a meaning (red =
    /// stop / danger, amber = fault, green = function on, blue = main beam; the same family as the cab cluster,
    /// <c>Game.UI.CabDisplays.DisplayPalette</c>). No gradients, no glow, no glass, no neon.
    /// Every text / background pair the UI uses is listed in <see cref="Pairs"/> and checked against WCAG 2.x AA by
    /// <c>UiThemeContrastTests</c>; the table with the ratios is in ADR 0283.
    /// </summary>
    public static class UiPalette
    {
        static Color C(byte r, byte g, byte b, float a = 1f) => new Color(r / 255f, g / 255f, b / 255f, a);

        // ---- type
        /// <summary>Main text: warm white (not pure white - no halation on a dark screen).</summary>
        public static readonly Color Ink = C(236, 233, 225);
        /// <summary>Secondary text (units, hints, descriptions). AA on every surface.</summary>
        public static readonly Color InkMuted = C(184, 181, 172);
        /// <summary>Disabled control text (WCAG exempts it; kept >= 3:1 anyway).</summary>
        public static readonly Color InkDisabled = C(128, 126, 120);
        /// <summary>Dark text on the light "selected segment" fill.</summary>
        public static readonly Color InkOnLight = C(22, 24, 27);

        // ---- surfaces (menus: opaque)
        public static readonly Color Scrim = C(8, 9, 10, 0.80f);
        public static readonly Color Panel = C(22, 24, 27);
        public static readonly Color Row = C(30, 33, 37);
        public static readonly Color Button = C(43, 47, 52);
        public static readonly Color ButtonPressed = C(52, 57, 63);
        /// <summary>Switched-on toggle in the older panels that keep light text on it (control settings, bindings, about).</summary>
        public static readonly Color ButtonActive = C(64, 78, 70);
        /// <summary>Selected segment / active tab: inverted (light fill, dark text) - reads as "chosen" without colour.</summary>
        public static readonly Color SegmentOn = C(236, 233, 225);

        // ---- accent
        /// <summary>Selection frame (pad / keyboard focus), section marks. The only accent colour.</summary>
        public static readonly Color Accent = C(232, 163, 58);
        /// <summary>Mouse hover frame (muted).</summary>
        public static readonly Color Hover = C(184, 181, 172, 0.85f);

        // ---- HUD (over the 3D view)
        /// <summary>HUD strip / mirror bezel. 96 % opaque: the text keeps AA over a white sky (linear-light blend).</summary>
        public static readonly Color HudPanel = C(17, 19, 21, 0.96f);
        public static readonly Color MirrorBezel = C(11, 12, 13, 1f);
        public static readonly Color GaugeTrack = C(58, 61, 66);
        public static readonly Color GaugeFill = C(184, 181, 172);

        // ---- telltales (ISO 2575 meaning; same family as the cab cluster DisplayPalette)
        public static readonly Color TellRed = C(184, 50, 31);
        public static readonly Color TellAmber = C(226, 150, 28);
        public static readonly Color TellGreen = C(74, 168, 92);
        public static readonly Color TellBlue = C(96, 150, 240);
        /// <summary>Telltale position when the lamp is off (the slot stays, nothing jumps).</summary>
        public static readonly Color TellOff = C(58, 61, 66);

        /// <summary>Worst-case scene behind a translucent HUD panel (overexposed sky / snow).</summary>
        public static readonly Color WorstSceneWhite = Color.white;

        /// <summary>How a pair is used: text needs 4.5:1, a graphic part (icon, frame, bar) 3:1.</summary>
        public enum Use { Text, Graphic }

        public readonly struct Pair
        {
            public readonly string Name;
            public readonly Color Fg, Bg;
            public readonly Use Use;
            /// <summary>Bg is translucent over the 3D view: checked composited over <see cref="WorstSceneWhite"/>.</summary>
            public readonly bool OverScene;
            public Pair(string name, Color fg, Color bg, Use use, bool overScene = false) { Name = name; Fg = fg; Bg = bg; Use = use; OverScene = overScene; }
            public float Required => Use == Use.Text ? UiContrast.AaText : UiContrast.AaLargeOrGraphic;
            public float Ratio => OverScene ? UiContrast.RatioOnTranslucent(Fg, Bg, WorstSceneWhite) : UiContrast.Ratio(Fg, Bg);
        }

        /// <summary>Every colour pair drawn by the UI (ADR 0283 table). Tests: each meets <see cref="Pair.Required"/>.</summary>
        public static readonly Pair[] Pairs =
        {
            new Pair("tekst / panel", Ink, Panel, Use.Text),
            new Pair("tekst / wiersz", Ink, Row, Use.Text),
            new Pair("tekst / przycisk", Ink, Button, Use.Text),
            new Pair("tekst / przycisk wciśnięty", Ink, ButtonPressed, Use.Text),
            new Pair("tekst drugorzędny / panel", InkMuted, Panel, Use.Text),
            new Pair("tekst drugorzędny / wiersz", InkMuted, Row, Use.Text),
            new Pair("tekst drugorzędny / przycisk", InkMuted, Button, Use.Text),
            new Pair("tekst wybranego segmentu", InkOnLight, SegmentOn, Use.Text),
            new Pair("tekst / przycisk włączony", Ink, ButtonActive, Use.Text),
            new Pair("akcent (nagłówek, licznik) / panel", Accent, Panel, Use.Text),
            new Pair("akcent / wiersz", Accent, Row, Use.Text),
            new Pair("ramka fokusu / panel", Accent, Panel, Use.Graphic),
            new Pair("ramka fokusu / wiersz", Accent, Row, Use.Graphic),
            new Pair("ramka najechania / panel", new Color(Hover.r, Hover.g, Hover.b, 1f), Panel, Use.Graphic),
            new Pair("przycisk wyłączony / przycisk", InkDisabled, Button, Use.Graphic),
            new Pair("HUD tekst / pasek nad białym niebem", Ink, HudPanel, Use.Text, true),
            new Pair("HUD tekst drugorzędny / pasek nad białym niebem", InkMuted, HudPanel, Use.Text, true),
            new Pair("HUD akcent / pasek nad białym niebem", Accent, HudPanel, Use.Text, true),
            new Pair("HUD kierunkowskaz / pasek nad białym niebem", TellGreen, HudPanel, Use.Graphic, true),
            new Pair("HUD światła drogowe / pasek nad białym niebem", TellBlue, HudPanel, Use.Graphic, true),
            new Pair("HUD wskaźnik ciśnienia / tor", GaugeFill, GaugeTrack, Use.Graphic),
            new Pair("ostrzeżenie czerwone: tekst / pole", Ink, TellRed, Use.Text),
            new Pair("ostrzeżenie bursztynowe: tekst / pole", InkOnLight, TellAmber, Use.Text),
            new Pair("ramka lusterka / biały obraz", MirrorBezel, Color.white, Use.Graphic),
        };
    }
}
