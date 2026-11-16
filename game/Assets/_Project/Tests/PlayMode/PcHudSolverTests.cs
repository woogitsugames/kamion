using Game.Controls;
using Game.UI.Driving;
using Game.UI.Navigation;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0265 - driving-HUD solver on a monitor (touch controls hidden, mirror windows sized by height): for 16:9,
    /// 21:9, 32:9, 1440p, 4K (all after <see cref="HudScaleModel"/>) and odd windows, in every HUD state, no zone overlaps
    /// another, everything is inside the content, the mirror windows keep the glass aspect and the GPS widget fits.
    /// Pure solver (lives in the PlayMode assembly only because it references Game.UI).
    /// </summary>
    public class PcHudSolverTests
    {
        static readonly Vector2Int[] k_Monitors =
        {
            new Vector2Int(1920, 1080), new Vector2Int(2560, 1080), new Vector2Int(3440, 1440), new Vector2Int(2560, 1440),
            new Vector2Int(3840, 2160), new Vector2Int(5120, 1440), new Vector2Int(1280, 720), new Vector2Int(1280, 1024),
            new Vector2Int(1680, 1050), new Vector2Int(1080, 1920),
        };
        static readonly float[] k_Dpi = { 0f, 96f, 120f, 144f, 192f };
        static readonly float[] k_User = { 0.8f, 1f, 1.4f };

        static string Check(in HudLayoutResult r, Vector2 size)
        {
            for (int i = 0; i < HudLayoutResult.ZoneCount; i++)
            {
                if (!r.Zone(i, out Rect a)) continue;
                if (a.width <= 1f || a.height <= 1f) return HudLayoutResult.ZoneName(i) + " empty " + a;
                if (a.xMin < -0.01f || a.yMin < -0.01f || a.xMax > size.x + 0.01f || a.yMax > size.y + 0.01f)
                    return HudLayoutResult.ZoneName(i) + " " + a + " outside " + size;
                for (int j = i + 1; j < HudLayoutResult.ZoneCount; j++)
                    if (r.Zone(j, out Rect b) && a.Overlaps(b)) return HudLayoutResult.ZoneName(i) + " " + a + " overlaps " + HudLayoutResult.ZoneName(j) + " " + b;
            }
            return null;
        }

        [Test]
        public void Monitor_NoOverlap_InsideContent_AllMonitorsAllStates()
        {
            int checkedCount = 0;
            foreach (var m in k_Monitors)
            foreach (float dpi in k_Dpi)
            foreach (float user in k_User)
            {
                HudScaleModel.Solve(new HudScaleInput { SafePx = new Rect(0f, 0f, m.x, m.y), Dpi = dpi, Desktop = true, UserScale = user }, out var sc);
                for (int bits = 0; bits < 1 << 7; bits++)
                {
                    var s = new HudLayoutInput
                    {
                        Width = sc.SizeUnits.x, Height = sc.SizeUnits.y, HideTouchControls = true, MirrorAspect = 0.55f,
                        Gyro = (bits & 1) != 0, DevPanelOpen = (bits & 2) != 0, Telemetry = (bits & 4) != 0, MirrorLeft = (bits & 8) != 0,
                        MirrorRight = (bits & 16) != 0, ReverseView = (bits & 32) != 0, DevText = (bits & 64) != 0,
                    };
                    HudLayout.Solve(s, out var r);
                    string err = Check(r, sc.SizeUnits);
                    if (err != null) Assert.Fail($"{m.x}x{m.y} dpi {dpi} user {user} state {bits}: {err}");
                    Assert.IsFalse(r.ShowTouchControls);
                    for (int z = 8; z <= 13; z++) Assert.IsFalse(r.Zone(z, out _), HudLayoutResult.ZoneName(z) + " hidden on a monitor");
                    if (NavHudLayout.Solve(r, sc.SizeUnits.x, sc.SizeUnits.y, s.Telemetry, out Rect nav))
                        for (int i = 0; i < HudLayoutResult.ZoneCount; i++)
                            if (r.Zone(i, out Rect a) && a.Overlaps(nav)) Assert.Fail($"{m.x}x{m.y} state {bits}: nav {nav} overlaps {HudLayoutResult.ZoneName(i)} {a}");
                    checkedCount++;
                }
            }
            Assert.Greater(checkedCount, 0);
        }

        [Test]
        public void Monitor_MirrorWindows_ShownWhileDriving_AspectKept_SameOn16by9And32by9()
        {
            Rect first = default;
            foreach (var m in new[] { new Vector2Int(1920, 1080), new Vector2Int(2560, 1080), new Vector2Int(3440, 1440), new Vector2Int(3840, 2160), new Vector2Int(5120, 1440) })
            {
                HudScaleModel.Solve(new HudScaleInput { SafePx = new Rect(0f, 0f, m.x, m.y), Dpi = 96f, Desktop = true, UserScale = 1f }, out var sc);
                var s = new HudLayoutInput { Width = sc.SizeUnits.x, Height = sc.SizeUnits.y, HideTouchControls = true, MirrorAspect = 0.55f, MirrorLeft = true, MirrorRight = true };
                HudLayout.Solve(s, out var r);
                Assert.IsTrue(r.ShowMirrorLeft && r.ShowMirrorRight, m + ": both mirror windows while driving");
                Assert.AreEqual(0.55f, r.MirrorLeft.width / r.MirrorLeft.height, 1e-3f, m + ": not stretched");
                if (first.width == 0f) first = r.MirrorLeft;
                Assert.AreEqual(first.width, r.MirrorLeft.width, 0.01f, m + ": same window in units on every monitor");
                Assert.AreEqual(first.height, r.MirrorLeft.height, 0.01f, m + ": same window in units on every monitor");
                Assert.IsTrue(NavHudLayout.Solve(r, sc.SizeUnits.x, sc.SizeUnits.y, false, out _), m + ": GPS widget shown while driving");
            }
        }

        [Test]
        public void Touch_LayoutUnchanged_ByDefault()
        {
            var s = new HudLayoutInput { Width = 2310f, Height = 1080f, MirrorLeft = true, MirrorRight = true };
            HudLayout.Solve(s, out var r);
            Assert.IsTrue(r.ShowTouchControls);
            Assert.AreEqual(HudLayout.MirrorSize.x, r.MirrorLeft.width, 1e-4f);
            Assert.AreEqual(HudLayout.MirrorSize.y, r.MirrorLeft.height, 1e-4f);
            for (int z = 8; z <= 13; z++) Assert.IsTrue(r.Zone(z, out _), HudLayoutResult.ZoneName(z));
        }
    }
}
