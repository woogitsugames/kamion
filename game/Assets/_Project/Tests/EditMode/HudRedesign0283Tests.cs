using System.Collections.Generic;
using System.Text.RegularExpressions;
using Game.Controls;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0283 (D84: HUD / menu redesign, larger adjustable mirror windows). Pure logic only:
    /// WCAG AA contrast of every colour pair of <see cref="UiPalette"/>; the monitor HUD layout
    /// (<see cref="DesktopHudLayout"/>) on 16:9, 21:9, 32:9, 4K, 720p and a portrait monitor with every state and mirror
    /// preference (inside the content, no overlap, clear road view, same windows on every aspect); HUD visibility rules;
    /// warning order; the Polish text table; HUD / mirror preferences sanitising; the menu input map (keyboard / mouse /
    /// pad) and the driving gate behind it; the main-mirror adjustment; zero GC in the per-frame HUD maths.
    /// </summary>
    public class HudRedesign0283Tests
    {
        // ================================================================== contrast

        [Test]
        public void Contrast_KnownValues()
        {
            Assert.AreEqual(21f, UiContrast.Ratio(Color.white, Color.black), 0.01f);
            Assert.AreEqual(1f, UiContrast.Ratio(Color.grey, Color.grey), 1e-4f);
            // #767676 on white is the classic 4.54:1 AA boundary grey.
            var g = new Color(118 / 255f, 118 / 255f, 118 / 255f);
            Assert.AreEqual(4.54f, UiContrast.Ratio(g, Color.white), 0.01f);
            // Opaque panel over anything = the panel itself.
            Assert.AreEqual(UiContrast.Luminance(UiPalette.Panel), UiContrast.CompositeLuminance(UiPalette.Panel, Color.white), 1e-6f);
        }

        [Test]
        public void Contrast_EveryPalettePair_MeetsWcagAA()
        {
            var fails = new List<string>();
            foreach (var p in UiPalette.Pairs)
            {
                float r = p.Ratio;
                TestContext.WriteLine($"| {p.Name} | {r:F2} : 1 | {p.Required:F1} | {(r >= p.Required ? "TAK" : "NIE")} |");
                if (r < p.Required) fails.Add($"{p.Name}: {r:F2} < {p.Required:F1}");
            }
            Assert.IsEmpty(fails, string.Join("; ", fails));
            Assert.GreaterOrEqual(UiPalette.Pairs.Length, 20, "every pair the UI draws is listed");
        }

        [Test]
        public void Contrast_HudStrip_TranslucencyIsTheLimit()
        {
            // The HUD text keeps AA over a white sky only because the strip is 96 % opaque; at 85 % the muted text would fail.
            var thin = new Color(UiPalette.HudPanel.r, UiPalette.HudPanel.g, UiPalette.HudPanel.b, 0.85f);
            Assert.Less(UiContrast.RatioOnTranslucent(UiPalette.InkMuted, thin, Color.white), UiContrast.AaText);
            Assert.GreaterOrEqual(UiContrast.RatioOnTranslucent(UiPalette.InkMuted, UiPalette.HudPanel, Color.white), UiContrast.AaText);
        }

        // ================================================================== monitor HUD layout

        struct Monitor { public string Name; public float W, H; }

        static readonly Monitor[] k_Monitors =
        {
            new Monitor { Name = "16:9 1080p", W = 1920, H = 1080 },
            new Monitor { Name = "21:9 2560x1080", W = 2560, H = 1080 },
            new Monitor { Name = "21:9 3440x1440", W = 3440, H = 1440 },
            new Monitor { Name = "32:9 5120x1440", W = 5120, H = 1440 },
            new Monitor { Name = "32:9 3840x1080", W = 3840, H = 1080 },
            new Monitor { Name = "16:9 4K", W = 3840, H = 2160 },
            new Monitor { Name = "16:9 720p", W = 1280, H = 720 },
            new Monitor { Name = "16:10 1920x1200", W = 1920, H = 1200 },
            new Monitor { Name = "portrait 1080x1920", W = 1080, H = 1920 },
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

        [Test]
        public void Layout_EveryMonitorStateAndPreference_InsideContent_NoOverlap_ClearViewFree()
        {
            float[] sizes = { HudPreferences.MirrorSizeMin, HudPreferences.MirrorSizeDefault, HudPreferences.MirrorSizeMax };
            float[] drops = { 0f, 0.5f, 1f };
            float[] insets = { 0f, 1f };
            int cases = 0;
            foreach (var m in k_Monitors)
            {
                var size = ContentUnits(m.W, m.H);
                var content = new Rect(0f, 0f, size.x, size.y);
                foreach (float ms in sizes)
                foreach (float d in drops)
                foreach (float ins in insets)
                for (int flags = 0; flags < 128; flags++)
                {
                    DesktopHudLayout.Solve(Input(size, flags, ms, d, ins), out var r);
                    string what = $"{m.Name} size {ms} drop {d} inset {ins} flags {flags}";
                    for (int i = 0; i < DesktopHudResult.ZoneCount; i++)
                    {
                        if (!r.Zone(i, out Rect a)) continue;
                        Assert.IsTrue(DesktopHudLayout.Inside(a, content), $"{what}: {DesktopHudResult.ZoneName(i)} {a} outside {content}");
                        Assert.Greater(a.width, 0f, what + " " + DesktopHudResult.ZoneName(i));
                        for (int j = i + 1; j < DesktopHudResult.ZoneCount; j++)
                        {
                            if (!r.Zone(j, out Rect b)) continue;
                            Assert.IsFalse(DesktopHudLayout.Intersects(a, b),
                                $"{what}: {DesktopHudResult.ZoneName(i)} {a} overlaps {DesktopHudResult.ZoneName(j)} {b}");
                        }
                    }
                    // The road between the mirrors stays free of everything but the reversing view and the developer overlays.
                    for (int i = 0; i < DesktopHudResult.ZoneCount; i++)
                    {
                        if (i == 2 || i == 7 || !r.Zone(i, out Rect a)) continue;   // reverse view, telemetry (developer)
                        Assert.IsFalse(DesktopHudLayout.Intersects(a, r.ClearView), $"{what}: {DesktopHudResult.ZoneName(i)} {a} in the clear view {r.ClearView}");
                    }
                    if ((flags & (16 | 32)) == 0) Assert.IsTrue(r.ShowMirrorLeft && r.ShowMirrorRight, what + ": mirrors give way only to developer overlays");
                    if (r.ShowMirrorLeft && r.ShowMirrorRight)
                    {
                        Assert.AreEqual(0.55f, r.MirrorLeft.width / r.MirrorLeft.height, 1e-3f, what + ": glass aspect kept");
                        Assert.AreEqual(r.MirrorLeft.size, r.MirrorRight.size, what + ": same size");
                        Assert.AreEqual(size.x * 0.5f - r.MirrorLeft.center.x, r.MirrorRight.center.x - size.x * 0.5f, 0.01f, what + ": symmetric");
                        Assert.GreaterOrEqual(r.MirrorLeft.height, DesktopHudLayout.MirrorMinHeight - 0.01f, what);
                    }
                    Assert.AreEqual(size.x * 0.5f, r.Telltales.center.x, 0.01f, what + ": telltales centred");
                    cases++;
                }
            }
            Assert.AreEqual(k_Monitors.Length * 3 * 3 * 2 * 128, cases);
        }

        [Test]
        public void Layout_MirrorWindows_SameOn16by9_21by9_32by9()
        {
            var a = ContentUnits(1920, 1080);
            var b = ContentUnits(2560, 1080);
            var c = ContentUnits(5120, 1440);
            DesktopHudLayout.Solve(Input(a, 1, 0f, 0f, 0f), out var ra);
            DesktopHudLayout.Solve(Input(b, 1, 0f, 0f, 0f), out var rb);
            DesktopHudLayout.Solve(Input(c, 1, 0f, 0f, 0f), out var rc);
            Assert.AreEqual(ra.MirrorLeft, rb.MirrorLeft, "21:9 = 16:9 (content clamped to 16:9)");
            Assert.AreEqual(ra.MirrorLeft, rc.MirrorLeft, "32:9 = 16:9");
            Assert.AreEqual(ra.Strip, rc.Strip);
            Assert.IsTrue(ra.ShowMirrorLeft && ra.ShowMirrorRight);
            Assert.IsTrue(ra.ShowNav, "GPS widget fits bottom left (under the left mirror)");
            Assert.AreEqual(DesktopHudLayout.NavPreferred.x, ra.Nav.width, 0.01f);
        }

        [Test]
        public void Layout_DefaultMirrors_LargerThanAdr0265_AndGrowWithThePreference()
        {
            var u = ContentUnits(1920, 1080);
            DesktopHudLayout.Solve(Input(u, 1, 0f, 0f, 0f), out var def);
            Assert.AreEqual(HudPreferences.MirrorSizeDefault * u.y, def.MirrorLeft.height, 0.01f, "default = 42 % of the height");
            Assert.Greater(def.MirrorLeft.height, Game.Cameras.MirrorWindowLayout.HeightFraction * u.y * 1.3f, "at least 30 % larger than ADR 0265");
            float last = 0f;
            for (float s = HudPreferences.MirrorSizeMin; s <= HudPreferences.MirrorSizeMax + 1e-4f; s += HudPreferences.MirrorSizeStep)
            {
                DesktopHudLayout.Solve(Input(u, 1, s, 0f, 0f), out var r);
                Assert.GreaterOrEqual(r.MirrorLeft.height, last - 1e-3f, "size " + s);
                last = r.MirrorLeft.height;
            }
            // 1080p, largest: 60 % of 1440 units = 864 units = 648 px high.
            Assert.AreEqual(0.60f * u.y, last, 0.5f);
        }

        [Test]
        public void Layout_DropAndInset_MoveTheWindows_WithinLimits()
        {
            var u = ContentUnits(2560, 1440);
            DesktopHudLayout.Solve(Input(u, 1, 0.42f, 0f, 0f), out var top);
            DesktopHudLayout.Solve(Input(u, 1, 0.42f, 1f, 0f), out var low);
            DesktopHudLayout.Solve(Input(u, 1, 0.42f, 0f, 1f), out var inner);
            Assert.AreEqual(u.y - DesktopHudLayout.Margin, top.MirrorLeft.yMax, 0.01f, "drop 0 = top edge");
            Assert.AreEqual(DesktopHudLayout.Margin, low.MirrorLeft.yMin, 0.01f, "drop 1 = down to the bottom margin");
            Assert.AreEqual(DesktopHudLayout.Margin, top.MirrorLeft.xMin, 0.01f, "inset 0 = outer edge");
            Assert.AreEqual(inner.ClearView.xMin - DesktopHudLayout.Gap, inner.MirrorLeft.xMax, 0.01f, "inset 1 = next to the clear view");
        }

        [Test]
        public void Layout_StripAndExtendedRow_TelltalesAlwaysThere()
        {
            var u = ContentUnits(1920, 1080);
            DesktopHudLayout.Solve(Input(u, 0, 0f, 0f, 0f), out var cab);
            DesktopHudLayout.Solve(Input(u, 1, 0f, 0f, 0f), out var min);
            DesktopHudLayout.Solve(Input(u, 3, 0f, 0f, 0f), out var ext);
            Assert.IsFalse(cab.ShowStrip);
            Assert.AreEqual(DesktopHudLayout.Margin, cab.Telltales.yMin, 0.01f, "cab view: telltale row alone at the bottom");
            Assert.IsTrue(min.ShowStrip);
            Assert.AreEqual(DesktopHudLayout.StripSize.y, min.Strip.height, 0.01f);
            Assert.AreEqual(DesktopHudLayout.StripSize.y + DesktopHudLayout.ExtendedRowHeight, ext.Strip.height, 0.01f);
            Assert.Greater(ext.Telltales.yMin, min.Telltales.yMin, "telltales sit on top of the taller strip");
            // A strip of the dashboard, not a panel over the road: below 25 % of the height even when extended.
            Assert.Less(ext.Telltales.yMax / u.y, 0.25f);
        }

        // ================================================================== alt-ui-polish-s23 (int-ui-s23 §7 p.4-6)

        /// <summary>Window width in content units (the content is narrowed to 16:9 on ultrawide; the height scale is shared).</summary>
        static float ScreenUnits(float w, float h) => w * ContentUnits(w, h).y / h;

        [Test]
        public void Layout_CompactCabBlock_AndUltrawideMirrors_AllStates_NoOverlap_ClearViewFree()
        {
            float[] sizes = { HudPreferences.MirrorSizeMin, HudPreferences.MirrorSizeDefault, HudPreferences.MirrorSizeMax };
            float[] drops = { 0f, 0.5f, 1f };
            float[] insets = { 0f, 1f };
            int cases = 0;
            foreach (var m in k_Monitors)
            {
                var size = ContentUnits(m.W, m.H);
                float sw = ScreenUnits(m.W, m.H);
                var content = new Rect(0f, 0f, size.x, size.y);
                foreach (float ms in sizes)
                foreach (float d in drops)
                foreach (float ins in insets)
                for (int flags = 0; flags < 256; flags++)
                {
                    var input = Input(size, flags & 127, ms, d, ins);
                    input.Compact = (flags & 128) != 0;
                    input.ScreenWidth = sw;
                    DesktopHudLayout.Solve(input, out var r);
                    string what = $"{m.Name} size {ms} drop {d} inset {ins} flags {flags}";
                    var screen = new Rect(-r.MirrorOutboard, 0f, size.x + 2f * r.MirrorOutboard, size.y);
                    Assert.LessOrEqual(r.MirrorOutboard, (sw - size.x) * 0.5f + 0.01f, what + ": side band only");
                    for (int i = 0; i < DesktopHudResult.ZoneCount; i++)
                    {
                        if (!r.Zone(i, out Rect a)) continue;
                        bool mirror = i == 3 || i == 4;
                        Assert.IsTrue(DesktopHudLayout.Inside(a, mirror ? screen : content), $"{what}: {DesktopHudResult.ZoneName(i)} {a} outside");
                        for (int j = i + 1; j < DesktopHudResult.ZoneCount; j++)
                            if (r.Zone(j, out Rect b))
                                Assert.IsFalse(DesktopHudLayout.Intersects(a, b), $"{what}: {DesktopHudResult.ZoneName(i)} {a} overlaps {DesktopHudResult.ZoneName(j)} {b}");
                        if (i != 2 && i != 7)
                            Assert.IsFalse(DesktopHudLayout.Intersects(a, r.ClearView), $"{what}: {DesktopHudResult.ZoneName(i)} {a} in the clear view {r.ClearView}");
                    }
                    if ((flags & (16 | 32)) == 0) Assert.IsTrue(r.ShowMirrorLeft && r.ShowMirrorRight, what + ": mirrors give way only to developer overlays");
                    if (r.ShowMirrorLeft && r.ShowMirrorRight)
                        Assert.AreEqual(size.x * 0.5f - r.MirrorLeft.center.x, r.MirrorRight.center.x - size.x * 0.5f, 0.01f, what + ": symmetric");
                    // One block: the telltale row sits on the strip, the "Panel" button on its right edge.
                    if (r.ShowStrip) Assert.AreEqual(r.Strip.yMax, r.Telltales.yMin, 0.01f, what + ": telltales on the strip");
                    if (r.ShowDevToggle) Assert.AreEqual(r.Telltales.xMax + DesktopHudLayout.ToggleGap, r.DevToggle.xMin, 0.01f, what + ": Panel attached");
                    if (r.Compact) Assert.Less(r.Telltales.yMax / size.y, 0.25f, what + ": compact block on the dash");
                    cases++;
                }
            }
            Assert.AreEqual(k_Monitors.Length * 3 * 3 * 2 * 256, cases);
        }

        [Test]
        public void Layout_CompactCabBlock_ExtendedRowOnly_RightOfTheWheel()
        {
            var u = ContentUnits(1920, 1080);
            var input = Input(u, 1 | 2 | 8, 0f, 0f, 0f);
            DesktopHudLayout.Solve(input, out var full);
            input.Compact = true;
            DesktopHudLayout.Solve(input, out var cab);
            Assert.IsTrue(cab.Compact && cab.ShowStrip);
            Assert.AreEqual(DesktopHudLayout.ExtendedRowHeight, cab.Strip.height, 0.01f, "no speed / gear / air row over the live cluster");
            Assert.Less(cab.Telltales.yMax, full.Telltales.yMax, "lower than the full extended block");
            Assert.GreaterOrEqual(cab.Strip.xMin, u.x * 0.5f, "right of the centre (steering wheel and cluster)");
            Assert.AreEqual(u.x - DesktopHudLayout.Margin, cab.DevToggle.xMax, 0.01f, "block + Panel end at the right margin");
            Assert.AreEqual(u.x * 0.5f, full.Telltales.center.x, 0.01f, "outside the cab the block stays centred");

            var vis = HudVisibility.Resolve(HudDetail.Extended, CabHudMode.Auto, cabCamera: true, cabInstrumentsLive: true, devDiagnostics: false);
            Assert.IsTrue(vis.Compact && vis.Strip && vis.Extended);
            Assert.IsFalse(HudVisibility.Resolve(HudDetail.Extended, CabHudMode.Auto, false, true, false).Compact, "chase camera: full strip");
            Assert.IsFalse(HudVisibility.Resolve(HudDetail.Extended, CabHudMode.Auto, true, false, false).Compact, "graybox without a live cluster: full strip");
        }

        [Test]
        public void Layout_Ultrawide_MirrorsAtTheWindowEdges_SameSize_NeverInTheRoad()
        {
            var a = ContentUnits(1920, 1080);
            var b = ContentUnits(2560, 1080);
            var ia = Input(a, 1, 0f, 0f, 0f); ia.ScreenWidth = ScreenUnits(1920, 1080);
            var ib = Input(b, 1, 0f, 0f, 0f); ib.ScreenWidth = ScreenUnits(2560, 1080);
            DesktopHudLayout.Solve(ia, out var ra);
            DesktopHudLayout.Solve(ib, out var rb);
            Assert.AreEqual(0f, ra.MirrorOutboard, 0.01f, "16:9: no side band");
            Assert.Greater(rb.MirrorOutboard, 0f, "21:9: side band used");
            Assert.AreEqual(ra.MirrorLeft.size, rb.MirrorLeft.size, "same window size");
            Assert.Less(rb.MirrorLeft.xMin, ra.MirrorLeft.xMin, "21:9: further out than on 16:9");
            Assert.AreEqual(DesktopHudLayout.Margin - rb.MirrorOutboard, rb.MirrorLeft.xMin, 0.01f, "at the window edge");
            // Inset all the way: next to the free road view, never in it (the right lane, §7 p.6).
            for (float inset = 0f; inset <= 1.001f; inset += 0.1f)
            {
                ib.MirrorInset = inset;
                DesktopHudLayout.Solve(ib, out var r);
                Assert.IsFalse(DesktopHudLayout.Intersects(r.MirrorRight, r.ClearView), "inset " + inset);
                Assert.GreaterOrEqual(r.ClearView.width, DesktopHudLayout.ClearViewFraction * b.x - 0.01f);
            }
            Assert.AreEqual(3f, DesktopHudLayout.MirrorBezel, "thin housing edge, not a picture-in-picture frame");
        }

        // ================================================================== visibility / warnings / texts

        [Test]
        public void Visibility_CabInstrumentsReplaceTheStrip_OnlyInTheCab()
        {
            var cabLive = HudVisibility.Resolve(HudDetail.Minimal, CabHudMode.Auto, cabCamera: true, cabInstrumentsLive: true, devDiagnostics: false);
            Assert.IsFalse(cabLive.Strip, "auto + live cluster in the dash: warnings only");
            Assert.IsFalse(cabLive.DevToggle);
            Assert.IsTrue(HudVisibility.Resolve(HudDetail.Minimal, CabHudMode.Auto, true, false, false).Strip, "graybox (no live cluster): strip");
            Assert.IsTrue(HudVisibility.Resolve(HudDetail.Minimal, CabHudMode.Auto, false, true, false).Strip, "chase camera: strip");
            Assert.IsFalse(HudVisibility.Resolve(HudDetail.Minimal, CabHudMode.WarningsOnly, true, false, false).Strip);
            Assert.IsTrue(HudVisibility.Resolve(HudDetail.Minimal, CabHudMode.Strip, true, true, false).Strip);
            var ext = HudVisibility.Resolve(HudDetail.Extended, CabHudMode.WarningsOnly, true, true, false);
            Assert.IsTrue(ext.Strip && ext.Extended && ext.DevToggle, "the extended key always shows the detail and the panel button");
            Assert.IsTrue(HudVisibility.Resolve(HudDetail.Minimal, CabHudMode.Auto, false, false, true).DevToggle, "devhud=1");
        }

        [Test]
        public void Warnings_SeverityOrder_Capped_DriveAwayReplacesParking()
        {
            var buf = new HudWarning[4];
            var all = new HudWarningInput { ParkingBrake = true, ParkDriveAway = true, AirLow = true, TrailerEmergency = true, AbsFault = true, TrailerAbsFault = true, AbsActive = true };
            int n = HudWarnings.Collect(all, buf);
            Assert.AreEqual(HudWarnings.MaxShown, n);
            Assert.AreEqual(new[] { HudWarning.ParkDriveAway, HudWarning.AirLow, HudWarning.TrailerEmergency, HudWarning.None }, buf);
            n = HudWarnings.Collect(new HudWarningInput { ParkingBrake = true, AbsFault = true, AbsActive = true }, buf);
            Assert.AreEqual(2, n);
            Assert.AreEqual(HudWarning.ParkingBrake, buf[0]);
            Assert.AreEqual(HudWarning.AbsFault, buf[1], "a fault hides the 'ABS regulating' note");
            Assert.AreEqual(0, HudWarnings.Collect(default, buf));
            Assert.IsTrue(HudWarnings.IsRed(HudWarning.AirLow));
            Assert.IsFalse(HudWarnings.IsRed(HudWarning.AbsFault));
        }

        [Test]
        public void Texts_Polish_NoBrands_PrebuiltNumbers()
        {
            Assert.AreEqual("0", HudTexts.Speed(-3));
            Assert.AreEqual("87", HudTexts.Speed(87));
            Assert.AreEqual("199", HudTexts.Speed(500));
            Assert.AreEqual("8,1", HudTexts.Air(81), "Polish decimal comma");
            Assert.AreEqual("0,0", HudTexts.Air(-1));
            Assert.AreEqual("15,0", HudTexts.Air(999));
            Assert.AreEqual("1200", HudTexts.RpmHundreds(12));
            Assert.AreEqual(HudTexts.Off, HudTexts.Cruise(0));
            Assert.AreEqual("40 km/h", HudTexts.Cruise(40));
            Assert.AreSame(HudTexts.Speed(42), HudTexts.Speed(42), "looked up, not formatted per frame");

            var brand = new Regex(@"\b(scania|volvo|man|daf|iveco|renault|mercedes|actros|ets2?|euro truck|scs|kenworth|peterbilt|freightliner)\b", RegexOptions.IgnoreCase);
            var texts = new List<string> { HudTexts.KmH, HudTexts.Bar, HudTexts.Retarder, HudTexts.BrakeCruise, HudTexts.Trailer, HudTexts.ReverseCamera };
            for (int i = 1; i < HudTexts.WarningCount; i++) texts.Add(HudTexts.Warning((HudWarning)i));
            foreach (var d in DrivingActionCatalog.All) texts.Add(d.LabelPl);
            foreach (var t in texts)
            {
                Assert.IsFalse(brand.IsMatch(t), "brand name in UI text: " + t);
                Assert.LessOrEqual(t.Length, 24, "fits a tile / row: " + t);
            }
            for (int i = 1; i < HudTexts.WarningCount; i++)
            {
                string w = HudTexts.Warning((HudWarning)i);
                Assert.AreEqual(w.ToUpperInvariant(), w, "warning tiles in capitals: " + w);
            }
        }

        // ================================================================== preferences

        [Test]
        public void Prefs_Sanitize_BrokenValuesToDefaults()
        {
            var p = new HudPrefsData
            {
                Detail = (HudDetail)7, Cab = (CabHudMode)9, MirrorSize = float.NaN, MirrorDrop = 3f, MirrorInset = -1f,
                MirrorYawOut = 40f, MirrorPitchDown = float.PositiveInfinity,
            };
            p.Sanitize();
            Assert.IsTrue(p.SameAs(HudPrefsData.Defaults), HudPreferences.LogLine(p));
            var ok = new HudPrefsData { Detail = HudDetail.Extended, Cab = CabHudMode.Strip, MirrorSize = 0.5f, MirrorDrop = 0.25f, MirrorInset = 1f, MirrorYawOut = -2f, MirrorPitchDown = 1.5f };
            var copy = ok;
            copy.Sanitize();
            Assert.IsTrue(copy.SameAs(ok), "valid values kept");
            Assert.AreEqual(0.44f, HudPrefsData.Step(0.42f, +1, HudPreferences.MirrorSizeStep, HudPreferences.MirrorSizeMin, HudPreferences.MirrorSizeMax), 1e-5f);
            Assert.AreEqual(HudPreferences.MirrorSizeMax, HudPrefsData.Step(0.60f, +1, HudPreferences.MirrorSizeStep, HudPreferences.MirrorSizeMin, HudPreferences.MirrorSizeMax), 1e-5f);
        }

        [Test]
        public void Prefs_StoreAndReload_RoundTrip()
        {
            var keys = new[] { HudPreferences.PrefDetail, HudPreferences.PrefCab, HudPreferences.PrefMirrorSize, HudPreferences.PrefMirrorDrop,
                HudPreferences.PrefMirrorInset, HudPreferences.PrefMirrorYaw, HudPreferences.PrefMirrorPitch };
            try
            {
                foreach (var k in keys) PlayerPrefs.DeleteKey(k);
                HudPreferences.Reload();
                Assert.IsTrue(HudPreferences.Current.SameAs(HudPrefsData.Defaults), "no prefs = defaults");
                int v0 = HudPreferences.Version;
                var want = new HudPrefsData { Detail = HudDetail.Extended, Cab = CabHudMode.WarningsOnly, MirrorSize = 0.5f, MirrorDrop = 0.3f, MirrorInset = 0.6f, MirrorYawOut = 1.5f, MirrorPitchDown = -1f };
                HudPreferences.Set(want);
                Assert.Greater(HudPreferences.Version, v0, "HUD lays out again");
                HudPreferences.Reload();
                Assert.IsTrue(HudPreferences.Current.SameAs(want), HudPreferences.LogLine(HudPreferences.Current));
                HudPreferences.ToggleDetail();
                Assert.AreEqual(HudDetail.Minimal, HudPreferences.Current.Detail);
            }
            finally
            {
                foreach (var k in keys) PlayerPrefs.DeleteKey(k);
                HudPreferences.Reload();
            }
        }

        // ================================================================== menu input

        [Test]
        public void Menu_EveryCommand_OnKeyboardAndPad_NoControlTwice()
        {
            var seen = new HashSet<string>();
            var kb = new bool[MenuCommandMap.CommandCount];
            var pad = new bool[MenuCommandMap.CommandCount];
            foreach (var b in MenuCommandMap.All)
            {
                Assert.IsTrue(seen.Add(b.Path), "control bound twice in the menu: " + b.Path);
                if (b.IsKeyboard) kb[(int)b.Command] = true;
                if (b.IsGamepad) pad[(int)b.Command] = true;
            }
            for (int c = 0; c < MenuCommandMap.CommandCount; c++)
            {
                Assert.IsTrue(kb[c], (MenuCommand)c + " has a keyboard control");
                Assert.IsTrue(pad[c], (MenuCommand)c + " has a pad control");
            }
            Assert.IsTrue(MenuCommandMap.Has(MenuCommand.Back, "<Keyboard>/escape"));
            Assert.IsTrue(MenuCommandMap.Has(MenuCommand.Back, "<Gamepad>/buttonEast"));
            Assert.IsTrue(MenuCommandMap.Has(MenuCommand.Submit, "<Keyboard>/enter"));
            Assert.IsTrue(MenuCommandMap.Has(MenuCommand.Submit, "<Gamepad>/buttonSouth"));
            Assert.IsTrue(MenuCommandMap.Has(MenuCommand.Submit, "<Mouse>/leftButton"));
            Assert.AreEqual(0, MenuCommandMap.StepTab(4, 1, 5), "tabs wrap");
            Assert.AreEqual(4, MenuCommandMap.StepTab(0, -1, 5));
        }

        [Test]
        public void Menu_ControlsSharedWithDriving_AreBlockedByTheGate()
        {
            // The menu reuses driving controls (arrows = steering / pedals, d-pad = indicators, A = parking brake, B = N,
            // E / Q / bumpers = gears): review #131 P1-1 - they must not drive the truck while a menu is open.
            string[] shared = { "<Keyboard>/upArrow", "<Keyboard>/leftArrow", "<Keyboard>/e", "<Keyboard>/q", "<Gamepad>/rightShoulder",
                "<Gamepad>/leftShoulder", "<Gamepad>/dpad/left", "<Gamepad>/buttonSouth", "<Gamepad>/buttonEast", "<Gamepad>/leftStick/up" };
            foreach (var p in shared)
            {
                Assert.IsTrue(MenuCommandMap.SharedWithDriving(p), p + " is a driving default");
                bool inMenu = false;
                foreach (var b in MenuCommandMap.All) inMenu |= b.Path == p;
                Assert.IsTrue(inMenu, p + " is a menu control");
            }
            Assert.IsFalse(MenuCommandMap.SharedWithDriving("<Keyboard>/escape"), "Esc is menu-only");

            // The gate itself: a menu-capable source pressing "shift up" (E / RB) while the menu is open gives nothing.
            var mixer = new DriverInputMixer();
            var dev = new ShiftKeySource();
            mixer.Add(dev);
            mixer.MenuOpen = true;
            for (int f = 0; f < 4; f++)
            {
                dev.Pressed = true;
                var i = mixer.Sample(1f / 60f, default);
                Assert.AreEqual(0, i.ShiftDelta, "menu open: E / RB switch tabs, not gears");
                Assert.AreEqual(0f, i.Throttle, "menu open: up arrow navigates, no throttle");
            }
            mixer.MenuOpen = false;
            mixer.Sample(1f / 60f, default);   // closing frame: still held by the gate (ADR 0265 P1-1)
            dev.Pressed = true;
            Assert.AreEqual(1, mixer.Sample(1f / 60f, default).ShiftDelta, "closed: the key drives again");
        }

        sealed class ShiftKeySource : IDriverInput, IMenuGatedInput
        {
            public string Name => "fake-keyboard";
            public bool Enabled { get; set; } = true;
            public bool Pressed;
            public void Sample(float dt, in VehicleFeedback fb, ref DriverIntent intent)
            {
                intent.Throttle = Pressed ? 1f : 0f;
                if (Pressed) intent.ShiftDelta += 1;
                Pressed = false;
            }
            public void SampleBlocked(float dt, in VehicleFeedback fb) { Pressed = false; }
        }

        [Test]
        public void Catalog_HudDetailKey_DefaultI_NoConflict()
        {
            DrivingActionDef hud = null;
            foreach (var d in DrivingActionCatalog.All) if (d.Name == DrivingActionCatalog.HudDetail) hud = d;
            Assert.IsNotNull(hud, "rebindable action");
            CollectionAssert.AreEqual(new[] { "<Keyboard>/i" }, hud.Keyboard);
            foreach (var d in DrivingActionCatalog.All)
                if (d != hud) CollectionAssert.DoesNotContain(d.Keyboard, "<Keyboard>/i", d.Name + " also on I");
            Assert.IsFalse(MenuCommandMap.SharedWithDriving("<Keyboard>/i") && MenuCommandMap.Has(MenuCommand.Submit, "<Keyboard>/i"));
        }

        // ================================================================== mirror adjustment

        [Test]
        public void MirrorAdjust_OutwardIsAwayFromTheVehicle_OnBothSides()
        {
            // A camera looking back (-Z) along the side: turning by the adjustment must move its forward towards -X on the
            // left mirror (phase 0) and +X on the right one.
            var look = Quaternion.LookRotation(Vector3.back, Vector3.up);
            Vector3 fl = look * Quaternion.Euler(RenderTextureMirror.AdjustEuler(0, 3f, 0f)) * Vector3.forward;
            Vector3 fr = look * Quaternion.Euler(RenderTextureMirror.AdjustEuler(1, 3f, 0f)) * Vector3.forward;
            Assert.Less(fl.x, -0.04f, "left mirror turns to the left (outward)");
            Assert.Greater(fr.x, 0.04f, "right mirror turns to the right (outward)");
            Vector3 fd = look * Quaternion.Euler(RenderTextureMirror.AdjustEuler(1, 0f, 2f)) * Vector3.forward;
            Assert.Less(fd.y, -0.03f, "positive pitch looks down");
            Assert.AreEqual(Vector3.zero, RenderTextureMirror.AdjustEuler(0, 0f, 0f));
        }

        // ================================================================== GC

        [Test]
        public void PerFrameHudMaths_DoesNotAllocate()
        {
            var buf = new HudWarning[HudWarnings.MaxShown];
            var size = new Vector2(2560f, 1440f);
            float acc = 0f;
            void Run()
            {
                for (int i = 0; i < 2000; i++)
                {
                    var s = Input(size, i & 127, 0.30f + (i % 16) * 0.02f, (i % 5) * 0.25f, (i % 3) * 0.5f);
                    DesktopHudLayout.Solve(s, out var r);
                    var vis = HudVisibility.Resolve((HudDetail)(i & 1), (CabHudMode)(i % 3), (i & 2) != 0, (i & 4) != 0, (i & 8) != 0);
                    var w = new HudWarningInput { ParkingBrake = (i & 1) != 0, AirLow = (i & 2) != 0, AbsActive = (i & 4) != 0, ParkDriveAway = (i & 8) != 0 };
                    int n = HudWarnings.Collect(w, buf);
                    string sp = HudTexts.Speed(i % 220), air = HudTexts.Air(i % 160), rpm = HudTexts.RpmHundreds(i % 30), cr = HudTexts.Cruise(i % 130);
                    acc += r.MirrorLeft.height + n + (vis.Strip ? 1f : 0f) + sp.Length + air.Length + rpm.Length + cr.Length
                        + HudTexts.Warning(buf[0]).Length + (s.SameAs(s) ? 1f : 0f);
                }
            }
            GcAllocCounter.AssertZero(Run, warmup: Run, message: "monitor HUD per-frame maths (layout, visibility, warnings, text lookup) must not allocate");
            Assert.Greater(acc, 0f);
        }
    }
}
