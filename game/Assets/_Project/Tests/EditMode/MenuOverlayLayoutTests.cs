using System.Collections.Generic;
using Game.Controls;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0276 (integration s23 P2): the diagnostics overlay (text panel + three buttons) must not cover the start menu
    /// (title, first button) on any supported screen. Pure logic: <see cref="MenuOverlayLayout"/> on the canvas size
    /// <see cref="HudScaleModel"/> gives for monitors (16:9, 21:9, 32:9, 1440p, 4K, OS scaling 150 %, HUD scale 1.4) and
    /// phones / tablet / foldable. The menu block is the geometry <c>BootMenu</c> builds (checked against the real
    /// object by the PlayMode test <c>MenuOverlayUiTests</c>).
    /// </summary>
    public class MenuOverlayLayoutTests
    {
        /// <summary>BootMenu block: 1600 wide (2 x 760 + 80), title top at +496; bottom -302 with 3 starts + region picker
        /// + the PC settings row (footer of the right column is the lowest item).</summary>
        public static readonly Rect MenuBlock3Starts = Rect.MinMaxRect(-800f, -302f, 800f, 496f);
        /// <summary>Phone (no PC settings row): the region start button of the left column is the lowest item (-288).</summary>
        public static readonly Rect MenuBlockPhone = Rect.MinMaxRect(-800f, -288f, 800f, 496f);

        static readonly Vector2 k_Button = new Vector2(300f, 84f);
        const float Spacing = 14f;

        public struct ScreenCase
        {
            public string Name; public float W, H, Dpi, User; public bool Desktop;
            public override string ToString() => Name;
        }

        static readonly ScreenCase[] k_Screens =
        {
            new ScreenCase { Name = "monitor-1920x1080", W = 1920, H = 1080, Dpi = 96, User = 1, Desktop = true },
            new ScreenCase { Name = "monitor-2560x1440", W = 2560, H = 1440, Dpi = 96, User = 1, Desktop = true },
            new ScreenCase { Name = "monitor-21x9-2560x1080", W = 2560, H = 1080, Dpi = 96, User = 1, Desktop = true },
            new ScreenCase { Name = "monitor-21x9-3440x1440", W = 3440, H = 1440, Dpi = 96, User = 1, Desktop = true },
            new ScreenCase { Name = "monitor-32x9-5120x1440", W = 5120, H = 1440, Dpi = 96, User = 1, Desktop = true },
            new ScreenCase { Name = "monitor-4k-3840x2160", W = 3840, H = 2160, Dpi = 96, User = 1, Desktop = true },
            new ScreenCase { Name = "monitor-4k-150pct", W = 3840, H = 2160, Dpi = 144, User = 1, Desktop = true },
            new ScreenCase { Name = "monitor-1080p-hud1.4", W = 1920, H = 1080, Dpi = 96, User = 1.4f, Desktop = true },
            new ScreenCase { Name = "window-1600x900", W = 1600, H = 900, Dpi = 96, User = 1, Desktop = true },
            new ScreenCase { Name = "phone-2400x1080", W = 2400, H = 1080, Dpi = 400, User = 1, Desktop = false },
            new ScreenCase { Name = "phone-2340x1080-A16", W = 2340, H = 1080, Dpi = 385, User = 1, Desktop = false },
            new ScreenCase { Name = "phone-1920x1080-dpi-unknown", W = 1920, H = 1080, Dpi = 0, User = 1, Desktop = false },
            new ScreenCase { Name = "tablet-2560x1600", W = 2560, H = 1600, Dpi = 274, User = 1, Desktop = false },
            new ScreenCase { Name = "fold-inner-2176x1812", W = 2176, H = 1812, Dpi = 368, User = 1, Desktop = false },
        };

        public static IEnumerable<ScreenCase> Screens => k_Screens;

        static Vector2 Units(ScreenCase s)
        {
            HudScaleModel.Solve(new HudScaleInput { SafePx = new Rect(0f, 0f, s.W, s.H), Dpi = s.Dpi, Desktop = s.Desktop, UserScale = s.User }, out var r);
            return r.SizeUnits;
        }

        static MenuOverlayInput Input(Vector2 units, Rect menu, bool panelShown = true, bool hasMenu = true, bool hasOverlay = true,
            Vector2? panel = null) => new MenuOverlayInput
        {
            ContentUnits = units, HasMenu = hasMenu, MenuBlock = menu, HasOverlay = hasOverlay, PanelShown = panelShown,
            PanelSize = panel ?? MenuOverlayLayout.DefaultPanelSize, ButtonSize = k_Button, ButtonSpacing = Spacing,
        };

        static void AssertNoCollision(in MenuOverlayResult r, Vector2 units, string what)
        {
            Assert.IsTrue(r.Fits, what + ": no layout without overlap");
            float hw = units.x * 0.5f + 0.01f, hh = units.y * 0.5f + 0.01f;
            foreach (var (name, rect) in new[] { ("menu", r.MenuRect), ("panel", r.PanelRect), ("buttons", r.ButtonsRect) })
            {
                if (rect.width <= 0f) continue;
                Assert.IsTrue(rect.xMin >= -hw && rect.xMax <= hw && rect.yMin >= -hh && rect.yMax <= hh,
                    $"{what}: {name} {rect} outside the content {units}");
            }
            Assert.IsFalse(MenuOverlayLayout.Collide(r.MenuRect, r.PanelRect, MenuOverlayLayout.Gap - 0.01f), $"{what}: panel {r.PanelRect} covers the menu {r.MenuRect}");
            Assert.IsFalse(MenuOverlayLayout.Collide(r.MenuRect, r.ButtonsRect, MenuOverlayLayout.Gap - 0.01f), $"{what}: buttons {r.ButtonsRect} cover the menu {r.MenuRect}");
            Assert.IsFalse(MenuOverlayLayout.Collide(r.PanelRect, r.ButtonsRect, MenuOverlayLayout.Gap - 0.01f), $"{what}: panel {r.PanelRect} covers the buttons {r.ButtonsRect}");
            // Every single button lies in the group rect (the overlay places them one by one).
            for (int i = 0; i < MenuOverlayLayout.ButtonCount; i++)
            {
                Rect b = MenuOverlayLayout.ButtonRect(r.Buttons, r.ButtonsRect, k_Button, Spacing, i);
                Assert.IsTrue(b.xMin >= r.ButtonsRect.xMin - 0.01f && b.xMax <= r.ButtonsRect.xMax + 0.01f
                              && b.yMin >= r.ButtonsRect.yMin - 0.01f && b.yMax <= r.ButtonsRect.yMax + 0.01f, $"{what}: button {i} {b} outside {r.ButtonsRect}");
                for (int j = i + 1; j < MenuOverlayLayout.ButtonCount; j++)
                    Assert.IsFalse(b.Overlaps(MenuOverlayLayout.ButtonRect(r.Buttons, r.ButtonsRect, k_Button, Spacing, j)), $"{what}: buttons {i} and {j} overlap");
            }
        }

        [Test]
        public void Menu_NeverCovered_AnyScreen_AnyPanelState([ValueSource(nameof(Screens))] ScreenCase s)
        {
            Vector2 units = Units(s);
            foreach (var menu in new[] { MenuBlock3Starts, MenuBlockPhone })
                foreach (bool shown in new[] { true, false })
                    foreach (var panel in new[] { MenuOverlayLayout.DefaultPanelSize, new Vector2(1400f, 360f), new Vector2(600f, 120f) })
                    {
                        if (menu.height > units.y) continue;   // a menu taller than the screen is a menu bug, not an overlay one
                        MenuOverlayLayout.Solve(Input(units, menu, shown, panel: panel), out var r);
                        string what = $"{s.Name} units {units} menu {menu.height:F0} panel {(shown ? panel.ToString() : "hidden")}";
                        AssertNoCollision(r, units, what);
                        Assert.IsTrue(r.MenuRect.height == menu.height && r.MenuRect.x == menu.x, what + ": the menu only moves vertically");
                    }
        }

        /// <summary>The bug of the integration screenshot (1080p monitor): the panel stays visible, the menu moves down instead.</summary>
        [TestCase(1920f, 1080f)]
        [TestCase(2560f, 1440f)]
        [TestCase(3840f, 2160f)]
        [TestCase(3440f, 1440f)]
        public void Monitor_PanelStaysVisible_MenuMovesDown(float w, float h)
        {
            Vector2 units = Units(new ScreenCase { W = w, H = h, Dpi = 96, User = 1, Desktop = true });
            MenuOverlayLayout.Solve(Input(units, MenuBlock3Starts), out var r);
            AssertNoCollision(r, units, $"{w}x{h}");
            Assert.AreEqual(OverlayPanelPlace.TopLeft, r.Panel);
            Assert.AreEqual(OverlayButtonsPlace.ColumnTopRight, r.Buttons, "16:9 content: the column fits beside the menu");
            Assert.Less(r.MenuShiftY, 0f, "the menu moves down to clear the panel");
            // Smallest shift: the menu top sits exactly one gap below the panel.
            Assert.AreEqual(r.PanelRect.yMin - MenuOverlayLayout.Gap, r.MenuRect.yMax, 0.01f);
        }

        [Test]
        public void Phone_NoRoomForPanel_PanelCollapses_ButtonsBeside()
        {
            Vector2 units = Units(k_Screens[9]);   // phone-2400x1080 (1080 units high: no free band above the menu)
            MenuOverlayLayout.Solve(Input(units, MenuBlock3Starts), out var r);
            AssertNoCollision(r, units, "phone");
            Assert.AreEqual(OverlayPanelPlace.Collapsed, r.Panel);
            Assert.AreEqual(0f, r.MenuShiftY, "the menu keeps its place when nothing has to move");
        }

        [Test]
        public void NoMenu_HistoricPlace_NoOverlay_NoShift()
        {
            Vector2 units = new Vector2(2560f, 1440f);
            MenuOverlayLayout.Solve(Input(units, default, hasMenu: false), out var a);
            Assert.AreEqual(OverlayPanelPlace.TopLeft, a.Panel);
            Assert.AreEqual(OverlayButtonsPlace.ColumnTopRight, a.Buttons);
            Assert.AreEqual(new Rect(-1280f + 24f, 720f - 24f - 300f, 1180f, 300f), a.PanelRect, "24 units from the corner as before ADR 0276");
            Assert.AreEqual(1280f - 24f, a.ButtonsRect.xMax, 0.01f);
            Assert.AreEqual(720f - 24f, a.ButtonsRect.yMax, 0.01f);
            Assert.IsTrue(a.Fits);

            MenuOverlayLayout.Solve(Input(units, MenuBlock3Starts, hasOverlay: false), out var b);
            Assert.AreEqual(0f, b.MenuShiftY);
            Assert.AreEqual(MenuBlock3Starts, b.MenuRect);
            Assert.AreEqual(OverlayPanelPlace.Collapsed, b.Panel);
        }

        [Test]
        public void HiddenPanel_MenuDoesNotMove_OnMonitor()
        {
            Vector2 units = Units(k_Screens[0]);
            MenuOverlayLayout.Solve(Input(units, MenuBlock3Starts, panelShown: false), out var r);
            AssertNoCollision(r, units, "hidden panel");
            Assert.AreEqual(OverlayPanelPlace.Collapsed, r.Panel);
            Assert.AreEqual(0f, r.MenuShiftY, "the buttons fit beside the 16:9 menu");
        }

        [Test]
        public void ReservePanel_Monotonic_Stepped_NoJitter()
        {
            var a = MenuOverlayLayout.ReservePanel(Vector2.zero, new Vector2(1101.3f, 281f));
            Assert.AreEqual(new Vector2(1120f, 300f), a);
            Assert.AreEqual(a, MenuOverlayLayout.ReservePanel(a, new Vector2(1090f, 270f)), "never shrinks");
            Assert.AreEqual(new Vector2(1140f, 300f), MenuOverlayLayout.ReservePanel(a, new Vector2(1121f, 299f)));
            // FPS digits change the measured width by a few units: the same reserve, the same menu shift.
            Vector2 units = Units(k_Screens[0]);
            MenuOverlayLayout.Solve(Input(units, MenuBlock3Starts, panel: MenuOverlayLayout.ReservePanel(a, new Vector2(1105f, 283f))), out var r1);
            MenuOverlayLayout.Solve(Input(units, MenuBlock3Starts, panel: MenuOverlayLayout.ReservePanel(a, new Vector2(1112f, 290f))), out var r2);
            Assert.IsTrue(r1.SameAs(r2));
        }

        [Test]
        public void Collide_UsesGap_EmptyNeverCollides()
        {
            var a = new Rect(0f, 0f, 10f, 10f);
            Assert.IsTrue(MenuOverlayLayout.Collide(a, new Rect(15f, 0f, 10f, 10f), 16f));
            Assert.IsFalse(MenuOverlayLayout.Collide(a, new Rect(26f, 0f, 10f, 10f), 16f));
            Assert.IsFalse(MenuOverlayLayout.Collide(a, default, 16f));
        }

        [Test]
        public void Solve_DoesNotAllocate()
        {
            Vector2 units = Units(k_Screens[0]);
            var input = Input(units, MenuBlock3Starts);
            float sink = 0f;
            void Run()
            {
                for (int i = 0; i < 1000; i++)
                {
                    input.PanelShown = (i & 1) == 0;
                    MenuOverlayLayout.Solve(input, out var r);
                    sink += r.MenuShiftY;
                }
            }
            GcAllocCounter.AssertZero(Run, warmup: Run, message: "the overlay / menu layout runs every frame");
            Assert.IsFalse(float.IsNaN(sink));
        }
    }
}
