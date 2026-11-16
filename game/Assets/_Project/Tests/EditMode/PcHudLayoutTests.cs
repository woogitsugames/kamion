using Game.Cameras;
using Game.Controls;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0265 - HUD and menus on a monitor: canvas scale and content rect (<see cref="HudScaleModel"/>) for 16:9, 21:9,
    /// 32:9, 1440p and 4K next to the phone; touch-control visibility (<see cref="TouchControlsPolicy"/>); mirror windows
    /// sized by height and never stretched (<see cref="MirrorWindowLayout"/>); explicit menu navigation order
    /// (<see cref="MenuNavGrid"/>). Pure logic only.
    /// </summary>
    public class PcHudLayoutTests
    {
        static HudScaleResult Desktop(float w, float h, float dpi = 96f, float user = 1f)
        {
            HudScaleModel.Solve(new HudScaleInput { SafePx = new Rect(0f, 0f, w, h), Dpi = dpi, Desktop = true, UserScale = user }, out var r);
            return r;
        }

        // ------------------------------------------------------------------ scale

        [TestCase(1920, 1080, 0.75f, 1920f, 0f)]
        [TestCase(2560, 1080, 0.75f, 1920f, 320f)]     // 21:9 (2.37)
        [TestCase(3440, 1440, 1.00f, 2560f, 440f)]     // 21:9 1440p
        [TestCase(2560, 1440, 1.00f, 2560f, 0f)]       // 1440p
        [TestCase(3840, 2160, 1.50f, 3840f, 0f)]       // 4K
        [TestCase(5120, 1440, 1.00f, 2560f, 1280f)]    // 32:9
        public void Monitor_ScaleFollowsHeight_ContentClampedTo16by9(int w, int h, float ppu, float contentW, float contentX)
        {
            var r = Desktop(w, h);
            Assert.AreEqual(ppu, r.PixelsPerUnit, 1e-4f, "px per unit");
            Assert.AreEqual(contentW, r.ContentPx.width, 0.5f, "content width [px]");
            Assert.AreEqual(contentX, r.ContentPx.x, 0.5f, "content centred");
            Assert.AreEqual(h, r.ContentPx.height, 0.5f, "full height");
            Assert.AreEqual(contentX > 0f, r.Clamped);
            // Every monitor gets the same layout space: 2560 x 1440 units (only sharper on 1440p / 4K).
            Assert.AreEqual(2560f, r.SizeUnits.x, 0.5f);
            Assert.AreEqual(1440f, r.SizeUnits.y, 0.5f);
        }

        [Test]
        public void Monitor_UltrawideHudNotStretched_SameUnitsAs16by9()
        {
            var a = Desktop(2560, 1440);
            var b = Desktop(3440, 1440);
            var c = Desktop(5120, 1440);
            Assert.AreEqual(a.PixelsPerUnit, b.PixelsPerUnit, 1e-5f);
            Assert.AreEqual(a.PixelsPerUnit, c.PixelsPerUnit, 1e-5f);
            Assert.AreEqual(a.SizeUnits, b.SizeUnits);
            Assert.AreEqual(a.SizeUnits, c.SizeUnits);
        }

        [Test]
        public void Monitor_OsScaling_EnlargesButKeepsAtLeast1080UnitsHigh()
        {
            // 1080p at Windows 125 % (120 dpi): floor 0.75 * 1.25 = 0.9375 px/unit.
            Assert.AreEqual(0.9375f, Desktop(1920, 1080, 120f).PixelsPerUnit, 1e-4f);
            // 1080p at 150 % (144 dpi): floor 1.125 would leave 960 units - capped at 1080 units high.
            var r = Desktop(1920, 1080, 144f);
            Assert.AreEqual(1f, r.PixelsPerUnit, 1e-4f);
            Assert.GreaterOrEqual(r.SizeUnits.y, HudScaleModel.MinDesktopShortUnits - 0.5f);
            // 4K at 150 % (144 dpi): height rule (1.5) already larger.
            Assert.AreEqual(1.5f, Desktop(3840, 2160, 144f).PixelsPerUnit, 1e-4f);
            // Unknown DPI behaves like 96.
            Assert.AreEqual(Desktop(1920, 1080, 96f).PixelsPerUnit, Desktop(1920, 1080, 0f).PixelsPerUnit, 1e-5f);
        }

        [Test]
        public void Monitor_SmallWindow_NotShrunkBelowFloor_WidthGuaranteed()
        {
            var r = Desktop(1280, 720);   // windowed 720p: the 0.75 floor would leave 960 units high - capped at 1080 units
            Assert.AreEqual(720f / 1080f, r.PixelsPerUnit, 1e-4f);
            Assert.AreEqual(1080f, r.SizeUnits.y, 0.5f);
            Assert.GreaterOrEqual(r.SizeUnits.x, HudScaleModel.MinWidthUnits - 0.5f);
            var p = Desktop(1080, 1920);   // portrait monitor: never fewer than 1680 units across
            Assert.AreEqual(HudScaleModel.MinWidthUnits, p.SizeUnits.x, 0.5f);
            Assert.IsFalse(p.Clamped);
        }

        [Test]
        public void Monitor_UserScale_ClampedAndApplied()
        {
            Assert.AreEqual(1.2f * 1f, Desktop(2560, 1440, 96f, 1.2f).PixelsPerUnit, 1e-4f);
            Assert.AreEqual(2.0f, Desktop(3840, 2160, 96f, 9f).PixelsPerUnit, 1e-4f, "9 -> 1.4 x 1.5 = 2.1, capped at 1080 units high");
            Assert.AreEqual(HudScaleModel.UserScaleMax, HudScaleModel.SanitizeUserScale(9f));
            Assert.AreEqual(1f, HudScaleModel.SanitizeUserScale(float.NaN));
            Assert.AreEqual(1f, HudScaleModel.SanitizeUserScale(0f));
            Assert.AreEqual(HudScaleModel.UserScaleMin, HudScaleModel.SanitizeUserScale(0.1f));
        }

        [Test]
        public void Phone_TouchScale_Unchanged_NoContentClamp()
        {
            // 20:9 phone 2400x1080 @ 400 dpi, cutout 90 px left (HudLayoutTests device): ADR 0079 numbers - 1080 units
            // on the short side, the 2.22 aspect is NOT narrowed (the pedals stay under the thumbs), user scale ignored.
            var safe = new Rect(90f, 0f, 2400f - 90f, 1080f);
            HudScaleModel.Solve(new HudScaleInput { SafePx = safe, Dpi = 400f, Desktop = false, UserScale = 1.4f }, out var r);
            Assert.AreEqual(1f, r.PixelsPerUnit, 1e-4f);
            Assert.AreEqual(safe, r.ContentPx);
            Assert.IsFalse(r.Clamped);
            Assert.AreEqual(2310f, r.SizeUnits.x, 0.5f);
            Assert.AreEqual(1080f, r.SizeUnits.y, 0.5f);
            Assert.AreEqual(HudScaleModel.TouchPixelsPerUnit(safe.width, safe.height, 400f), r.PixelsPerUnit, 1e-6f);
            // Tablet 2560x1600 @ 274 dpi: more units than the phone, controls do not blow up with the screen.
            Assert.Less(HudScaleModel.TouchPixelsPerUnit(2560f, 1600f, 274f), 1600f / 1080f);
        }

        // ------------------------------------------------------------------ touch controls

        [Test]
        public void TouchControls_AutoShowsOnPhone_HidesOnPcWithoutTouch()
        {
            // Phone / tablet build: always shown in Auto (also before the first touch).
            Assert.IsTrue(TouchControlsPolicy.Resolve(TouchControlsMode.Auto, true, true, false));
            Assert.IsTrue(TouchControlsPolicy.Resolve(TouchControlsMode.Auto, true, false, false));
            // PC without a touch screen: hidden.
            Assert.IsFalse(TouchControlsPolicy.Resolve(TouchControlsMode.Auto, false, false, false));
            // Touch laptop: hidden until the screen is touched, then shown.
            Assert.IsFalse(TouchControlsPolicy.Resolve(TouchControlsMode.Auto, false, true, false));
            Assert.IsTrue(TouchControlsPolicy.Resolve(TouchControlsMode.Auto, false, true, true));
        }

        [Test]
        public void TouchControls_AlwaysAndNeverOverrideEverything()
        {
            for (int i = 0; i < 8; i++)
            {
                bool a = (i & 1) != 0, b = (i & 2) != 0, c = (i & 4) != 0;
                Assert.IsTrue(TouchControlsPolicy.Resolve(TouchControlsMode.Always, a, b, c));
                Assert.IsFalse(TouchControlsPolicy.Resolve(TouchControlsMode.Never, a, b, c));
            }
        }

        [Test]
        public void TouchControls_StoredValueParsedSafely()
        {
            Assert.AreEqual(TouchControlsMode.Auto, UiPreferences.ParseTouchControls(0));
            Assert.AreEqual(TouchControlsMode.Always, UiPreferences.ParseTouchControls(1));
            Assert.AreEqual(TouchControlsMode.Never, UiPreferences.ParseTouchControls(2));
            Assert.AreEqual(TouchControlsMode.Auto, UiPreferences.ParseTouchControls(7));
            Assert.AreEqual(TouchControlsMode.Auto, UiPreferences.ParseTouchControls(-1));
            Assert.AreEqual("auto", TouchControlsPolicy.Label(TouchControlsMode.Auto));
            Assert.AreEqual("zawsze", TouchControlsPolicy.Label(TouchControlsMode.Always));
            Assert.AreEqual("nigdy", TouchControlsPolicy.Label(TouchControlsMode.Never));
        }

        [Test]
        public void UiPreferences_SaveAndReload()
        {
            bool hadTouch = PlayerPrefs.HasKey(UiPreferences.PrefTouchControls), hadScale = PlayerPrefs.HasKey(UiPreferences.PrefHudScale);
            int oldTouch = PlayerPrefs.GetInt(UiPreferences.PrefTouchControls, 0);
            float oldScale = PlayerPrefs.GetFloat(UiPreferences.PrefHudScale, 1f);
            try
            {
                UiPreferences.Reload();
                UiPreferences.TouchControls = TouchControlsMode.Never;
                UiPreferences.HudScale = 1.2f;
                UiPreferences.Reload();
                Assert.AreEqual(TouchControlsMode.Never, UiPreferences.TouchControls);
                Assert.AreEqual(1.2f, UiPreferences.HudScale, 1e-5f);
                PlayerPrefs.SetFloat(UiPreferences.PrefHudScale, 50f);   // corrupt / hand-edited
                PlayerPrefs.SetInt(UiPreferences.PrefTouchControls, 42);
                UiPreferences.Reload();
                Assert.AreEqual(HudScaleModel.UserScaleMax, UiPreferences.HudScale, 1e-5f);
                Assert.AreEqual(TouchControlsMode.Auto, UiPreferences.TouchControls);
            }
            finally
            {
                if (hadTouch) PlayerPrefs.SetInt(UiPreferences.PrefTouchControls, oldTouch); else PlayerPrefs.DeleteKey(UiPreferences.PrefTouchControls);
                if (hadScale) PlayerPrefs.SetFloat(UiPreferences.PrefHudScale, oldScale); else PlayerPrefs.DeleteKey(UiPreferences.PrefHudScale);
                UiPreferences.Reload();
            }
        }

        // ------------------------------------------------------------------ mirror windows (D70)

        static MirrorWindowResult Mirrors(float w, float h, float aspect = 0.55f)
        {
            var cluster = new Rect(w * 0.5f - 220f, h - 24f - 156f, 440f, 156f);
            MirrorWindowLayout.Solve(new MirrorWindowInput { Width = w, Height = h, Centre = cluster, Aspect = aspect, SideReserve = 162f }, out var r);
            return r;
        }

        [TestCase(2560f, 1440f)]   // 16:9 (all monitors after the content clamp)
        [TestCase(3440f, 1440f)]   // 21:9 if the content were not clamped
        [TestCase(5120f, 1440f)]   // 32:9 if the content were not clamped
        public void Mirrors_SizedByHeight_NotStretchedByWidth(float w, float h)
        {
            var r = Mirrors(w, h);
            Assert.IsTrue(r.Fits);
            Assert.AreEqual(MirrorWindowLayout.HeightFraction * h, r.Left.height, 0.01f, "height from the content height");
            Assert.AreEqual(0.55f, r.Left.width / r.Left.height, 1e-4f, "glass aspect kept");
            Assert.AreEqual(r.Left.size, r.Right.size, "both windows the same size");
            var ref16 = Mirrors(2560f, 1440f);
            Assert.AreEqual(ref16.Left.size, r.Left.size, "wider monitor = same window, more free view");
        }

        [Test]
        public void Mirrors_FlankCluster_InsideContent_NoOverlap()
        {
            foreach (var size in new[] { new Vector2(2560f, 1440f), new Vector2(1920f, 1080f), new Vector2(1707f, 1080f), new Vector2(1680f, 2987f) })
            {
                float w = size.x, h = size.y;
                var cluster = new Rect(w * 0.5f - 220f, h - 24f - 156f, 440f, 156f);
                var r = Mirrors(w, h);
                string what = size.ToString();
                Assert.IsFalse(r.Left.Overlaps(cluster), what);
                Assert.IsFalse(r.Right.Overlaps(cluster), what);
                Assert.IsFalse(r.Left.Overlaps(r.Right), what);
                Assert.GreaterOrEqual(r.Left.xMin, MirrorWindowLayout.Margin + 162f - 0.01f, what + " left edge kept free");
                Assert.LessOrEqual(r.Right.xMax, w - MirrorWindowLayout.Margin - 162f + 0.01f, what + " right edge kept free (developer button)");
                Assert.LessOrEqual(r.Left.yMax, h - MirrorWindowLayout.Margin + 0.01f, what);
                Assert.AreEqual(r.Left.yMax, cluster.yMax, 0.01f, what + " top-aligned with the cluster");
                Assert.AreEqual(0.55f, r.Left.width / r.Left.height, 1e-3f, what + " aspect kept when shrunk");
            }
        }

        [Test]
        public void Mirrors_TooNarrow_HiddenNotSquashed_AndTextureAspectUsed()
        {
            var narrow = Mirrors(900f, 1080f);
            Assert.IsFalse(narrow.Fits);
            var wide = Mirrors(2560f, 1440f, 0.8f);
            Assert.AreEqual(0.8f, wide.Left.width / wide.Left.height, 1e-4f);
            var def = Mirrors(2560f, 1440f, 0f);   // unknown texture: default glass aspect
            Assert.AreEqual(MirrorWindowLayout.DefaultAspect, def.Left.width / def.Left.height, 1e-4f);
        }

        // ------------------------------------------------------------------ menu navigation

        // Start menu shape: left = 3 starts, region < >, region start; right = 3 segments (3, 4, 2 items), settings + about.
        static readonly int[][] k_Menu = { new[] { 1, 1, 1, 2, 1 }, new[] { 3, 4, 2, 2 } };

        static (int c, int r, int i) Go(int c, int r, int i, NavDir d)
        {
            Assert.IsTrue(MenuNavGrid.Neighbour(k_Menu, c, r, i, d, out int nc, out int nr, out int ni), $"{c},{r},{i} {d}");
            return (nc, nr, ni);
        }

        [Test]
        public void Nav_UpDownWithinColumn_NoWrap()
        {
            Assert.AreEqual((0, 1, 0), Go(0, 0, 0, NavDir.Down));
            Assert.AreEqual((0, 3, 0), Go(0, 2, 0, NavDir.Down));
            Assert.AreEqual((0, 4, 0), Go(0, 3, 1, NavDir.Down));
            Assert.IsFalse(MenuNavGrid.Neighbour(k_Menu, 0, 0, 0, NavDir.Up, out _, out _, out _), "no wrap at the top");
            Assert.IsFalse(MenuNavGrid.Neighbour(k_Menu, 0, 4, 0, NavDir.Down, out _, out _, out _), "no wrap at the bottom");
            // Same relative position between rows of different length: last of 3 -> last of 4.
            Assert.AreEqual((1, 1, 3), Go(1, 0, 2, NavDir.Down));
            Assert.AreEqual((1, 2, 1), Go(1, 1, 3, NavDir.Down));
            Assert.AreEqual((1, 3, 0), Go(1, 2, 0, NavDir.Down));
        }

        [Test]
        public void Nav_LeftRight_WithinRow_ThenAcrossColumns()
        {
            Assert.AreEqual((0, 3, 1), Go(0, 3, 0, NavDir.Right));
            // Past the end of a left row into the right column, near end, same relative height.
            Assert.AreEqual((1, 0, 0), Go(0, 0, 0, NavDir.Right));
            Assert.AreEqual((1, 3, 0), Go(0, 4, 0, NavDir.Right));
            // From the right column back to the left: enters at the last item of the row.
            Assert.AreEqual((0, 3, 1), Go(1, 2, 0, NavDir.Left));
            Assert.IsFalse(MenuNavGrid.Neighbour(k_Menu, 0, 0, 0, NavDir.Left, out _, out _, out _), "nothing left of the left column");
            Assert.IsFalse(MenuNavGrid.Neighbour(k_Menu, 1, 3, 1, NavDir.Right, out _, out _, out _), "nothing right of the right column");
        }

        [Test]
        public void Nav_EveryItemReachable_AndMovesAreReversibleVertically()
        {
            int total = 0;
            for (int c = 0; c < k_Menu.Length; c++) for (int r = 0; r < k_Menu[c].Length; r++) total += k_Menu[c][r];
            // Flood fill from the first start button.
            var seen = new System.Collections.Generic.HashSet<(int, int, int)>();
            var queue = new System.Collections.Generic.Queue<(int, int, int)>();
            queue.Enqueue((0, 0, 0)); seen.Add((0, 0, 0));
            while (queue.Count > 0)
            {
                var (c, r, i) = queue.Dequeue();
                foreach (NavDir d in System.Enum.GetValues(typeof(NavDir)))
                    if (MenuNavGrid.Neighbour(k_Menu, c, r, i, d, out int nc, out int nr, out int ni) && seen.Add((nc, nr, ni)))
                        queue.Enqueue((nc, nr, ni));
            }
            Assert.AreEqual(total, seen.Count, "every menu item reachable with the pad");
            // One-item rows: down then up returns to the same item.
            for (int r = 0; r < 2; r++)
            {
                var d = Go(0, r, 0, NavDir.Down);
                Assert.AreEqual((0, r, 0), Go(d.c, d.r, d.i, NavDir.Up));
            }
        }

        [Test]
        public void Nav_EmptyRowsSkipped_InvalidInputSafe()
        {
            int[][] g = { new[] { 1, 0, 2 } };
            Assert.IsTrue(MenuNavGrid.Neighbour(g, 0, 0, 0, NavDir.Down, out _, out int nr, out _));
            Assert.AreEqual(2, nr);
            Assert.IsFalse(MenuNavGrid.Neighbour(null, 0, 0, 0, NavDir.Down, out _, out _, out _));
            Assert.IsFalse(MenuNavGrid.Neighbour(g, 3, 0, 0, NavDir.Down, out _, out _, out _));
            Assert.AreEqual(0, MenuNavGrid.MapIndex(5, 1, 4));
            Assert.AreEqual(3, MenuNavGrid.MapIndex(2, 3, 4));
        }
    }
}
