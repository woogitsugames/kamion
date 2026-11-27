using Game.Cameras;
using Game.Controls;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0340 addendum (critic build #10 p.8): the monitor mirror windows as a mirror head - the wide-angle (class IV)
    /// glass under the main window is a decoration that never moves, shrinks or hides the main windows and never touches
    /// another HUD zone; its picture is cropped, never squashed.
    /// </summary>
    public class MirrorHead0340Tests
    {
        static Vector2 ContentUnits(float w, float h)
        {
            HudScaleModel.Solve(new HudScaleInput { SafePx = new Rect(0f, 0f, w, h), Dpi = 96f, Desktop = true, UserScale = 1f }, out var r);
            return r.SizeUnits;
        }

        static DesktopHudInput Input(Vector2 size, int flags, float mSize, float drop, float inset, bool wide) => new DesktopHudInput
        {
            Width = size.x, Height = size.y,
            Strip = (flags & 1) != 0, Extended = (flags & 2) != 0, ReverseView = (flags & 4) != 0, DevToggle = (flags & 8) != 0,
            DevPanelOpen = (flags & 16) != 0, Telemetry = (flags & 32) != 0, DevText = (flags & 64) != 0,
            MirrorLeft = true, MirrorRight = true, MirrorAspect = 0.55f, MirrorSize = mSize, MirrorDrop = drop, MirrorInset = inset,
            MirrorWide = wide,
        };

        [Test]
        public void WideGlass_DefaultCabView_1080p_IsShownUnderBothWindows()
        {
            var size = ContentUnits(1920, 1080);
            DesktopHudLayout.Solve(Input(size, 0, HudPreferences.MirrorSizeDefault, 0f, 0f, true), out var r);
            Assert.IsTrue(r.ShowMirrorLeft && r.ShowMirrorRight);
            Assert.IsTrue(r.ShowMirrorWide, "default window size, cab view: the head carries both glasses");
            Assert.AreEqual(r.MirrorLeft.x, r.MirrorWideLeft.x, 1e-3f);
            Assert.AreEqual(r.MirrorLeft.width, r.MirrorWideLeft.width, 1e-3f);
            Assert.AreEqual(r.MirrorLeft.yMin - DesktopHudLayout.MirrorWideGap, r.MirrorWideLeft.yMax, 1e-3f);
            Assert.AreEqual(DesktopHudLayout.MirrorWideAspect, r.MirrorWideLeft.width / r.MirrorWideLeft.height, 1e-3f);
            Assert.AreEqual(size.x - r.MirrorWideLeft.xMax, r.MirrorWideRight.x, 1e-2f, "mirrored about the centre");
            Assert.IsTrue(r.ShowNav, "the GPS widget keeps its place");
            Assert.IsFalse(DesktopHudLayout.Intersects(r.MirrorWideLeft, r.Nav));
        }

        [Test]
        public void WideGlass_NeverChangesTheMainWindows_AndNeverTouchesAZone()
        {
            float[] sizes = { HudPreferences.MirrorSizeMin, HudPreferences.MirrorSizeDefault, HudPreferences.MirrorSizeMax };
            float[] drops = { 0f, 0.5f, 1f };
            int shown = 0, cases = 0;
            foreach (var px in new[] { new Vector2(1920, 1080), new Vector2(2560, 1080), new Vector2(3840, 2160), new Vector2(1280, 720), new Vector2(1920, 1200), new Vector2(1080, 1920) })
            {
                var size = ContentUnits(px.x, px.y);
                foreach (float ms in sizes)
                foreach (float d in drops)
                foreach (float inset in new[] { 0f, 1f })
                for (int flags = 0; flags < 128; flags++)
                {
                    DesktopHudLayout.Solve(Input(size, flags, ms, d, inset, false), out var a);
                    DesktopHudLayout.Solve(Input(size, flags, ms, d, inset, true), out var b);
                    cases++;
                    Assert.AreEqual(a.MirrorLeft, b.MirrorLeft); Assert.AreEqual(a.MirrorRight, b.MirrorRight);
                    Assert.AreEqual(a.ShowMirrorLeft, b.ShowMirrorLeft); Assert.AreEqual(a.ShowMirrorRight, b.ShowMirrorRight);
                    Assert.AreEqual(a.Nav, b.Nav); Assert.AreEqual(a.ShowNav, b.ShowNav);
                    Assert.IsFalse(a.ShowMirrorWide, "no class IV picture = no wide glass");
                    if (!b.ShowMirrorWide) continue;
                    shown++;
                    Assert.IsTrue(b.ShowMirrorLeft && b.ShowMirrorRight, "a wide glass only under a main window");
                    Assert.IsFalse((flags & 32) != 0, "the developer telemetry uses that column");
                    Assert.GreaterOrEqual(b.MirrorWideLeft.yMin, DesktopHudLayout.Margin - 1e-3f, "inside the content");
                    for (int i = 0; i < DesktopHudResult.ZoneCount; i++)
                    {
                        if (i == 3 || i == 4 || !b.Zone(i, out Rect z)) continue;
                        string where = $"{px} size {ms} drop {d} inset {inset} flags {flags}: {DesktopHudResult.ZoneName(i)}";
                        Assert.IsFalse(DesktopHudLayout.Intersects(b.MirrorWideLeft, z), where);
                        Assert.IsFalse(DesktopHudLayout.Intersects(b.MirrorWideRight, z), where);
                    }
                }
            }
            Assert.Greater(shown, cases / 20, "the wide glass is the normal case somewhere, not a dead feature");
        }

        [Test]
        public void WideCrop_KeepsTheAspect_CutsSkyFirst_StaysInsideTheTexture_Mirrored()
        {
            float pane = DesktopHudLayout.MirrorWideAspect;
            // taller texture (class IV glass ~0.95): full width, part of the height, more cut off the top than the bottom
            Rect uv = MirrorWindowLayout.WideCrop(0.95f, pane);
            Assert.AreEqual(1f, uv.x, 1e-6f); Assert.AreEqual(-1f, uv.width, 1e-6f, "mirrored left-right like the main glass");
            Assert.AreEqual(0.95f / pane, uv.height, 1e-5f);
            Assert.That(uv.y, Is.InRange(0f, 1f - uv.height));
            Assert.Less(uv.y, 1f - uv.height - uv.y, "sky goes first");
            Assert.AreEqual(pane, 0.95f * Mathf.Abs(uv.width) / uv.height, 1e-4f, "shown part has the pane's aspect");
            // wider texture: full height, sides cropped evenly
            uv = MirrorWindowLayout.WideCrop(2f, pane);
            Assert.AreEqual(1f, uv.height, 1e-6f); Assert.AreEqual(0f, uv.y, 1e-6f);
            Assert.AreEqual(pane, 2f * Mathf.Abs(uv.width) / uv.height, 1e-4f);
            Assert.AreEqual(1f - uv.x, uv.x + uv.width, 1e-5f, "centred");
            // degenerate input = whole texture
            Assert.AreEqual(new Rect(1f, 0f, -1f, 1f), MirrorWindowLayout.WideCrop(0f, pane));
        }

        [Test]
        public void WideGlassBarrel_IsMonotonic_AndStaysInsideTheTexture()
        {
            float k = MirrorWindowLayout.WideGlassCurvature, aspect = DesktopHudLayout.MirrorWideAspect;
            Assert.Greater(k, MirrorWindowLayout.GlassCurvature, "the wide-angle glass is the more convex one");
            for (int j = 0; j <= 20; j++)
            {
                float prev = -1f;
                for (int i = 0; i <= 20; i++)
                {
                    Vector2 uv = MirrorWindowLayout.Barrel(i / 20f, j / 20f, aspect, k);
                    Assert.That(uv.x, Is.InRange(-1e-5f, 1f + 1e-5f)); Assert.That(uv.y, Is.InRange(-1e-5f, 1f + 1e-5f));
                    Assert.Greater(uv.x, prev, "no fold-over across the glass");
                    prev = uv.x;
                }
            }
            Assert.That(MirrorWindowLayout.GlassTint.maxColorComponent, Is.InRange(0.85f, 0.98f), "a mirror returns a little less than it gets");
        }
    }
}
