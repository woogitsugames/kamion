// .NET port of the pure parts of game/Assets/_Project/Tests/EditMode/HudRedesign0283Tests.cs (ADR 0283). Same cases and
// assertions; the Unity suite stays the reference (it also covers the driving gate, the mirror adjustment and GC).
using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using Game.Controls;
using UnityEngine;
using Xunit;
using Xunit.Abstractions;

namespace HudRunner.Tests
{
    public class HudRunnerTests
    {
        readonly ITestOutputHelper m_Out;
        public HudRunnerTests(ITestOutputHelper o) { m_Out = o; }

        [Fact]
        public void Contrast_KnownValues()
        {
            Assert.InRange(UiContrast.Ratio(Color.white, Color.black), 20.99f, 21.01f);
            var g = new Color(118 / 255f, 118 / 255f, 118 / 255f);
            Assert.InRange(UiContrast.Ratio(g, Color.white), 4.53f, 4.55f);
        }

        [Fact]
        public void Contrast_EveryPalettePair_MeetsWcagAA()
        {
            var fails = new List<string>();
            foreach (var p in UiPalette.Pairs)
            {
                float r = p.Ratio;
                m_Out.WriteLine($"| {p.Name} | {r:F2} : 1 | {p.Required:F1} | {(r >= p.Required ? "TAK" : "NIE")} |");
                if (r < p.Required) fails.Add($"{p.Name}: {r:F2} < {p.Required:F1}");
            }
            Assert.Empty(fails);
            Assert.True(UiPalette.Pairs.Length >= 20);
            var thin = new Color(UiPalette.HudPanel.r, UiPalette.HudPanel.g, UiPalette.HudPanel.b, 0.85f);
            Assert.True(UiContrast.RatioOnTranslucent(UiPalette.InkMuted, thin, Color.white) < UiContrast.AaText);
        }

        static readonly (string name, float w, float h)[] k_Monitors =
        {
            ("16:9 1080p", 1920, 1080), ("21:9 2560x1080", 2560, 1080), ("21:9 3440x1440", 3440, 1440), ("32:9 5120x1440", 5120, 1440),
            ("32:9 3840x1080", 3840, 1080), ("16:9 4K", 3840, 2160), ("16:9 720p", 1280, 720), ("16:10", 1920, 1200), ("portrait", 1080, 1920),
        };

        static Vector2 ContentUnits(float w, float h)
        {
            HudScaleModel.Solve(new HudScaleInput { SafePx = new Rect(0f, 0f, w, h), Dpi = 96f, Desktop = true, UserScale = 1f }, out var r);
            return r.SizeUnits;
        }

        static DesktopHudInput Input(Vector2 size, int flags, float mSize, float drop, float inset) => new DesktopHudInput
        {
            Width = size.x, Height = size.y,
            Strip = (flags & 1) != 0, Extended = (flags & 2) != 0, ReverseView = (flags & 4) != 0, DevToggle = (flags & 8) != 0,
            DevPanelOpen = (flags & 16) != 0, Telemetry = (flags & 32) != 0, DevText = (flags & 64) != 0,
            MirrorLeft = true, MirrorRight = true, MirrorAspect = 0.55f, MirrorSize = mSize, MirrorDrop = drop, MirrorInset = inset,
        };

        [Fact]
        public void Layout_EveryMonitorStateAndPreference()
        {
            float[] sizes = { HudPreferences.MirrorSizeMin, HudPreferences.MirrorSizeDefault, HudPreferences.MirrorSizeMax };
            float[] drops = { 0f, 0.5f, 1f };
            float[] insets = { 0f, 1f };
            int cases = 0, mirrorsShown = 0;
            foreach (var m in k_Monitors)
            {
                var size = ContentUnits(m.w, m.h);
                m_Out.WriteLine($"{m.name}: content {size}");
                var content = new Rect(0f, 0f, size.x, size.y);
                foreach (float ms in sizes)
                foreach (float d in drops)
                foreach (float ins in insets)
                for (int flags = 0; flags < 128; flags++)
                {
                    DesktopHudLayout.Solve(Input(size, flags, ms, d, ins), out var r);
                    string what = $"{m.name} size {ms} drop {d} inset {ins} flags {flags}";
                    for (int i = 0; i < DesktopHudResult.ZoneCount; i++)
                    {
                        if (!r.Zone(i, out Rect a)) continue;
                        Assert.True(DesktopHudLayout.Inside(a, content), $"{what}: {DesktopHudResult.ZoneName(i)} {a} outside {content}");
                        Assert.True(a.width > 0f, what + " " + DesktopHudResult.ZoneName(i));
                        for (int j = i + 1; j < DesktopHudResult.ZoneCount; j++)
                        {
                            if (!r.Zone(j, out Rect b)) continue;
                            Assert.False(DesktopHudLayout.Intersects(a, b), $"{what}: {DesktopHudResult.ZoneName(i)} {a} overlaps {DesktopHudResult.ZoneName(j)} {b}");
                        }
                    }
                    for (int i = 0; i < DesktopHudResult.ZoneCount; i++)
                    {
                        if (i == 2 || i == 7 || !r.Zone(i, out Rect a)) continue;
                        Assert.False(DesktopHudLayout.Intersects(a, r.ClearView), $"{what}: {DesktopHudResult.ZoneName(i)} {a} in clear view {r.ClearView}");
                    }
                    if ((flags & (16 | 32)) == 0) Assert.True(r.ShowMirrorLeft && r.ShowMirrorRight, what + ": mirrors give way only to developer overlays");
                    if (r.ShowMirrorLeft && r.ShowMirrorRight)
                    {
                        mirrorsShown++;
                        Assert.InRange(r.MirrorLeft.width / r.MirrorLeft.height, 0.549f, 0.551f);
                        Assert.Equal(r.MirrorLeft.size, r.MirrorRight.size);
                        Assert.InRange(size.x * 0.5f - r.MirrorLeft.center.x - (r.MirrorRight.center.x - size.x * 0.5f), -0.01f, 0.01f);
                        Assert.True(r.MirrorLeft.height >= DesktopHudLayout.MirrorMinHeight - 0.01f, what);
                    }
                    Assert.InRange(r.Telltales.center.x - size.x * 0.5f, -0.01f, 0.01f);
                    cases++;
                }
            }
            Assert.Equal(k_Monitors.Length * 3 * 3 * 2 * 128, cases);
            m_Out.WriteLine($"cases {cases}, both mirrors shown {mirrorsShown}");
        }

        [Fact]
        public void Layout_MirrorWindows_SameOn16by9_21by9_32by9()
        {
            DesktopHudLayout.Solve(Input(ContentUnits(1920, 1080), 1, 0f, 0f, 0f), out var ra);
            DesktopHudLayout.Solve(Input(ContentUnits(2560, 1080), 1, 0f, 0f, 0f), out var rb);
            DesktopHudLayout.Solve(Input(ContentUnits(5120, 1440), 1, 0f, 0f, 0f), out var rc);
            Assert.Equal(ra.MirrorLeft.ToString(), rb.MirrorLeft.ToString());
            Assert.Equal(ra.MirrorLeft.ToString(), rc.MirrorLeft.ToString());
            Assert.True(ra.ShowMirrorLeft && ra.ShowMirrorRight);
            m_Out.WriteLine($"1080p: mirror {ra.MirrorLeft} (units), x0.75 = {ra.MirrorLeft.width * 0.75f:F0} x {ra.MirrorLeft.height * 0.75f:F0} px; strip {ra.Strip}; telltales {ra.Telltales}; clear {ra.ClearView}");
        }

        [Fact]
        public void Layout_DefaultMirrors_Larger_AndGrow()
        {
            var u = ContentUnits(1920, 1080);
            DesktopHudLayout.Solve(Input(u, 1, 0f, 0f, 0f), out var def);
            Assert.InRange(def.MirrorLeft.height, HudPreferences.MirrorSizeDefault * u.y - 0.01f, HudPreferences.MirrorSizeDefault * u.y + 0.01f);
            Assert.True(def.MirrorLeft.height > 0.30f * u.y * 1.3f);
            float last = 0f;
            for (float s = HudPreferences.MirrorSizeMin; s <= HudPreferences.MirrorSizeMax + 1e-4f; s += HudPreferences.MirrorSizeStep)
            {
                DesktopHudLayout.Solve(Input(u, 1, s, 0f, 0f), out var r);
                Assert.True(r.MirrorLeft.height >= last - 1e-3f);
                last = r.MirrorLeft.height;
            }
            Assert.InRange(last, 0.60f * u.y - 0.5f, 0.60f * u.y + 0.5f);
        }

        [Fact]
        public void Layout_DropAndInset()
        {
            var u = ContentUnits(2560, 1440);
            DesktopHudLayout.Solve(Input(u, 1, 0.42f, 0f, 0f), out var top);
            DesktopHudLayout.Solve(Input(u, 1, 0.42f, 1f, 0f), out var low);
            DesktopHudLayout.Solve(Input(u, 1, 0.42f, 0f, 1f), out var inner);
            Assert.InRange(top.MirrorLeft.yMax - (u.y - DesktopHudLayout.Margin), -0.01f, 0.01f);
            Assert.InRange(low.MirrorLeft.yMin - DesktopHudLayout.Margin, -0.01f, 0.01f);
            Assert.InRange(top.MirrorLeft.xMin - DesktopHudLayout.Margin, -0.01f, 0.01f);
            Assert.InRange(inner.MirrorLeft.xMax - (inner.ClearView.xMin - DesktopHudLayout.Gap), -0.01f, 0.01f);
        }

        [Fact]
        public void Layout_StripRows()
        {
            var u = ContentUnits(1920, 1080);
            DesktopHudLayout.Solve(Input(u, 0, 0f, 0f, 0f), out var cab);
            DesktopHudLayout.Solve(Input(u, 1, 0f, 0f, 0f), out var min);
            DesktopHudLayout.Solve(Input(u, 3, 0f, 0f, 0f), out var ext);
            Assert.False(cab.ShowStrip);
            Assert.Equal(DesktopHudLayout.Margin, cab.Telltales.yMin);
            Assert.Equal(DesktopHudLayout.StripSize.y + DesktopHudLayout.ExtendedRowHeight, ext.Strip.height);
            Assert.True(ext.Telltales.yMin > min.Telltales.yMin);
            Assert.True(ext.Telltales.yMax / u.y < 0.25f);
        }

        [Fact]
        public void Visibility_And_Warnings()
        {
            Assert.False(HudVisibility.Resolve(HudDetail.Minimal, CabHudMode.Auto, true, true, false).Strip);
            Assert.True(HudVisibility.Resolve(HudDetail.Minimal, CabHudMode.Auto, true, false, false).Strip);
            Assert.True(HudVisibility.Resolve(HudDetail.Minimal, CabHudMode.Auto, false, true, false).Strip);
            Assert.False(HudVisibility.Resolve(HudDetail.Minimal, CabHudMode.WarningsOnly, true, false, false).Strip);
            var ext = HudVisibility.Resolve(HudDetail.Extended, CabHudMode.WarningsOnly, true, true, false);
            Assert.True(ext.Strip && ext.Extended && ext.DevToggle);

            var buf = new HudWarning[4];
            var all = new HudWarningInput { ParkingBrake = true, ParkDriveAway = true, AirLow = true, TrailerEmergency = true, AbsFault = true, TrailerAbsFault = true, AbsActive = true };
            Assert.Equal(3, HudWarnings.Collect(all, buf));
            Assert.Equal(new[] { HudWarning.ParkDriveAway, HudWarning.AirLow, HudWarning.TrailerEmergency, HudWarning.None }, buf);
            Assert.Equal(2, HudWarnings.Collect(new HudWarningInput { ParkingBrake = true, AbsFault = true, AbsActive = true }, buf));
            Assert.Equal(HudWarning.ParkingBrake, buf[0]);
            Assert.Equal(HudWarning.AbsFault, buf[1]);
        }

        [Fact]
        public void Texts()
        {
            Assert.Equal("0", HudTexts.Speed(-3));
            Assert.Equal("199", HudTexts.Speed(500));
            Assert.Equal("8,1", HudTexts.Air(81));
            Assert.Equal("15,0", HudTexts.Air(999));
            Assert.Equal("1200", HudTexts.RpmHundreds(12));
            Assert.Equal("40 km/h", HudTexts.Cruise(40));
            Assert.Same(HudTexts.Speed(42), HudTexts.Speed(42));
            var brand = new Regex(@"\b(scania|volvo|man|daf|iveco|renault|mercedes|actros|ets2?|euro truck|scs|kenworth|peterbilt|freightliner)\b", RegexOptions.IgnoreCase);
            var texts = new List<string> { HudTexts.KmH, HudTexts.Bar, HudTexts.Retarder, HudTexts.BrakeCruise, HudTexts.Trailer, HudTexts.ReverseCamera };
            for (int i = 1; i < HudTexts.WarningCount; i++) texts.Add(HudTexts.Warning((HudWarning)i));
            foreach (var d in DrivingActionCatalog.All) texts.Add(d.LabelPl);
            foreach (var t in texts) { Assert.False(brand.IsMatch(t), t); Assert.True(t.Length <= 24, t); }
        }

        [Fact]
        public void Prefs()
        {
            var p = new HudPrefsData { Detail = (HudDetail)7, Cab = (CabHudMode)9, MirrorSize = float.NaN, MirrorDrop = 3f, MirrorInset = -1f, MirrorYawOut = 40f, MirrorPitchDown = float.PositiveInfinity };
            p.Sanitize();
            Assert.True(p.SameAs(HudPrefsData.Defaults), HudPreferences.LogLine(p));
            var ok = new HudPrefsData { Detail = HudDetail.Extended, Cab = CabHudMode.Strip, MirrorSize = 0.5f, MirrorDrop = 0.25f, MirrorInset = 1f, MirrorYawOut = -2f, MirrorPitchDown = 1.5f };
            var copy = ok; copy.Sanitize();
            Assert.True(copy.SameAs(ok));
            Assert.InRange(HudPrefsData.Step(0.42f, +1, 0.02f, 0.30f, 0.60f), 0.4399f, 0.4401f);
            HudPreferences.Reload();
            Assert.True(HudPreferences.Current.SameAs(HudPrefsData.Defaults));
            var want = new HudPrefsData { Detail = HudDetail.Extended, Cab = CabHudMode.WarningsOnly, MirrorSize = 0.5f, MirrorDrop = 0.3f, MirrorInset = 0.6f, MirrorYawOut = 1.5f, MirrorPitchDown = -1f };
            HudPreferences.Set(want);
            HudPreferences.Reload();
            Assert.True(HudPreferences.Current.SameAs(want));
            HudPreferences.ToggleDetail();
            Assert.Equal(HudDetail.Minimal, HudPreferences.Current.Detail);
        }

        [Fact]
        public void Menu()
        {
            var seen = new HashSet<string>();
            var kb = new bool[MenuCommandMap.CommandCount];
            var pad = new bool[MenuCommandMap.CommandCount];
            foreach (var b in MenuCommandMap.All)
            {
                Assert.True(seen.Add(b.Path), b.Path);
                if (b.IsKeyboard) kb[(int)b.Command] = true;
                if (b.IsGamepad) pad[(int)b.Command] = true;
            }
            for (int c = 0; c < MenuCommandMap.CommandCount; c++) { Assert.True(kb[c], ((MenuCommand)c).ToString()); Assert.True(pad[c], ((MenuCommand)c).ToString()); }
            string[] shared = { "<Keyboard>/upArrow", "<Keyboard>/leftArrow", "<Keyboard>/e", "<Keyboard>/q", "<Gamepad>/rightShoulder",
                "<Gamepad>/leftShoulder", "<Gamepad>/dpad/left", "<Gamepad>/buttonSouth", "<Gamepad>/buttonEast", "<Gamepad>/leftStick/up" };
            foreach (var p in shared) Assert.True(MenuCommandMap.SharedWithDriving(p), p);
            Assert.False(MenuCommandMap.SharedWithDriving("<Keyboard>/escape"));
            Assert.Equal(0, MenuCommandMap.StepTab(4, 1, 5));
            Assert.Equal(4, MenuCommandMap.StepTab(0, -1, 5));
            DrivingActionDef hud = null;
            foreach (var d in DrivingActionCatalog.All) if (d.Name == DrivingActionCatalog.HudDetail) hud = d;
            Assert.NotNull(hud);
            Assert.Equal(new[] { "<Keyboard>/i" }, hud.Keyboard);
            foreach (var d in DrivingActionCatalog.All) if (d != hud) Assert.DoesNotContain("<Keyboard>/i", d.Keyboard);
        }
    }
}
