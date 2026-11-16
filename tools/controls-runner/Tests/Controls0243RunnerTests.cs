// .NET mirror of game/Assets/_Project/Tests/EditMode/Controls0243Tests.cs (ADR 0243) for sessions without Unity.
// VehicleCameraBudget (URP assembly) is not compiled here: its ADR 0243 members only delegate to MirrorInsetBudget, which
// is tested directly. The EditMode suite remains the reference (lead runs it in Unity).
using System;
using System.Globalization;
using Game.Cameras;
using Game.Controls;
using Game.Vehicle.Runtime;
using UnityEngine;
using Xunit;
using Xunit.Abstractions;

namespace ControlsRunner.Tests
{
    public class Controls0243RunnerTests
    {
        /// <summary>Touch layout of the one mirror-window layout (Game.Cameras.MirrorWindowLayout.SolveTouch).</summary>
        static bool Place(float w, Rect cl, float top, float gap, float margin, float bottom, out Rect l, out Rect r)
        {
            MirrorWindowLayout.SolveTouch(w, cl, top, gap, margin, bottom, out var m);
            l = m.Left; r = m.Right;
            return m.Fits;
        }

        readonly ITestOutputHelper m_Out;
        public Controls0243RunnerTests(ITestOutputHelper o) { m_Out = o; }

        // ---------------------------------------------------------------- settings

        [Fact]
        public void Defaults_Wheel270_WindowsOn_Schema5()
        {
            var d = ControlSettings.Defaults();
            Assert.Equal(5, ControlSettings.CurrentSchema);
            Assert.Equal(270f, d.wheelRangeDeg);
            Assert.Equal(900f, ControlSettings.TouchHalfRangeSimDeg);
            Assert.Equal(ControlSettings.RangeMax, ControlSettings.TouchHalfRangeSimDeg);
            Assert.False(d.TouchWheelSimRange);
            Assert.True(d.mirrorInsets);
            Assert.Contains("mirrors=insets", d.LogLine("t"));
        }

        [Fact]
        public void Preset_SaveLoad_RoundTrip()
        {
            const string key = "runner.controls";
            PlayerPrefs.DeleteKey(key);
            var s = ControlSettings.Defaults();
            s.SetTouchWheelPreset(true); s.mirrorInsets = false;
            s.Save(key);
            var l = ControlSettings.Load(key, null);
            Assert.Equal(900f, l.wheelRangeDeg);
            Assert.False(l.mirrorInsets);
            Assert.Equal(5, l.schema);
            Assert.Contains("mirrors=look", l.LogLine("t"));
            Assert.Equal(l.ToJson(), ControlSettings.FromJson(l.ToJson()).ToJson());
            PlayerPrefs.DeleteKey(key);
        }

        [Theory]
        [InlineData(270f)] [InlineData(450f)] [InlineData(900f)]
        public void Migration_V4_KeepsRange_WindowsOn(float range)
        {
            var v4 = ControlSettings.FromJson("{\"schema\":4,\"wheelRangeDeg\":" + range.ToString(CultureInfo.InvariantCulture) + ",\"wheelDragGrab\":false}");
            Assert.Equal(5, v4.schema);
            Assert.Equal(range, v4.wheelRangeDeg);
            Assert.True(v4.mirrorInsets);
            Assert.False(v4.wheelDragGrab);
        }

        [Fact]
        public void Migration_Older_Future_Legacy_Clamp()
        {
            Assert.True(ControlSettings.FromJson("{\"schema\":4,\"mirrorInsets\":false}").mirrorInsets);
            Assert.True(ControlSettings.FromJson("{\"wheelRangeDeg\":360}").mirrorInsets);
            Assert.False(ControlSettings.FromJson("{\"schema\":9,\"mirrorInsets\":false}").mirrorInsets);
            Assert.Equal(5, ControlSettings.FromJson("{\"schema\":9}").schema);
            Assert.Equal(900f, ControlSettings.FromLegacySteerMode(1).wheelRangeDeg);
            Assert.True(ControlSettings.FromLegacySteerMode(1).mirrorInsets);
            Assert.Equal(900f, ControlSettings.FromJson("{\"schema\":5,\"wheelRangeDeg\":5000}").wheelRangeDeg);
            Assert.Equal(180f, ControlSettings.FromJson("{\"schema\":5,\"wheelRangeDeg\":10}").wheelRangeDeg);
            Assert.Equal(270f, ControlSettings.FromJson("{bad").wheelRangeDeg);
            var r = ControlSettings.FromJson("{\"schema\":5,\"wheelRangeDeg\":900,\"mirrorInsets\":false}");
            r.ResetToDefaults();
            Assert.Equal(270f, r.wheelRangeDeg); Assert.True(r.mirrorInsets);
        }

        static float WheelSteer(ControlSettings s, float sign)
        {
            var wheel = new TouchSteeringWheel(); s.ApplyTo(wheel, null, null);
            float mmPer10 = 10f / wheel.DragDegPerMm;
            wheel.PointerDown(new Vector2(0, 100), new Vector2(20f, 10f));
            for (int i = 1; i <= 6; i++)
            {
                float a = sign * i * 10f * Mathf.Deg2Rad;
                wheel.PointerDrag(new Vector2(Mathf.Sin(a), Mathf.Cos(a)) * 100f, new Vector2(20f + sign * i * mmPer10, 10f));
            }
            var it = new DriverIntent();
            for (int i = 0; i < 20; i++) wheel.Sample(0.02f, new VehicleFeedback(), ref it);
            return it.Steer;
        }

        [Fact]
        public void Direction_BothPresets_BothGestures()
        {
            foreach (bool sim in new[] { false, true })
            foreach (bool drag in new[] { true, false })
            {
                var s = ControlSettings.Defaults(); s.SetTouchWheelPreset(sim); s.wheelDragGrab = drag;
                Assert.True(WheelSteer(s, 1f) > 0.02f, $"sim {sim} drag {drag} right");
                Assert.True(WheelSteer(s, -1f) < -0.02f, $"sim {sim} drag {drag} left");
            }
            var c = ControlSettings.Defaults(); c.wheelDragGrab = false; c.speedSensitiveSteering = false; c.wheelDeadZone = 0f;
            var m = c.Clone(); m.SetTouchWheelPreset(true);
            Assert.InRange(WheelSteer(m, 1f) / WheelSteer(c, 1f), 270f / 900f - 0.02f, 270f / 900f + 0.02f);
        }

        // ---------------------------------------------------------------- layout

        static float PixelsPerUnit(Rect safe)
        {
            float shortPx = Mathf.Min(safe.width, safe.height);
            float s = shortPx / 1080f;
            if (safe.width / s < 1680f) s = safe.width / 1680f;
            return s;
        }

        static readonly (string name, float w, float h, Rect safe)[] k_Screens =
        {
            ("FHD+ 19.5:9 (A16 class)", 2340f, 1080f, new Rect(0f, 0f, 2340f, 1080f)),
            ("FHD+ notch left", 2340f, 1080f, new Rect(80f, 0f, 2260f, 1080f)),
            ("notch both + bar", 2400f, 1080f, new Rect(110f, 48f, 2180f, 1032f)),
            ("16:9 720p", 1280f, 720f, new Rect(0f, 0f, 1280f, 720f)),
            ("21:9", 2520f, 1080f, new Rect(96f, 0f, 2328f, 1080f)),
            ("QHD+ 20:9", 3120f, 1440f, new Rect(120f, 0f, 2880f, 1440f)),
            ("Fold inner ~1:1", 2176f, 1812f, new Rect(0f, 0f, 2176f, 1740f)),
            ("tablet 16:10", 2560f, 1600f, new Rect(0f, 0f, 2560f, 1600f)),
            ("4:3", 2048f, 1536f, new Rect(0f, 0f, 2048f, 1536f)),
        };

        [Fact]
        public void Windows_InsideSafeArea_OnEveryScreen()
        {
            const float margin = 24f, gap = 12f;
            foreach (var sc in k_Screens)
            {
                float ppu = PixelsPerUnit(sc.safe);
                float w = sc.safe.width / ppu, h = sc.safe.height / ppu, top = h - margin;
                var cl = new Rect(w * 0.5f - 220f, top - 156f, 440f, 156f);
                Assert.True(Place(w, cl, top, gap, margin, margin, out Rect l, out Rect r), sc.name);
                var canvas = new Rect(0f, 0f, w, h);
                Assert.True(MirrorWindowLayout.Inside(l, canvas) && MirrorWindowLayout.Inside(r, canvas), sc.name);
                Assert.False(l.Overlaps(cl) || r.Overlaps(cl), sc.name);
                Assert.True(l.xMax <= cl.xMin + 1e-3f && r.xMin >= cl.xMax - 1e-3f, sc.name);
                Assert.InRange((w * 0.5f - l.center.x) - (r.center.x - w * 0.5f), -1e-3f, 1e-3f);
                var lp = MirrorWindowLayout.ToScreenPixels(l, sc.safe, ppu);
                var rp = MirrorWindowLayout.ToScreenPixels(r, sc.safe, ppu);
                Assert.True(MirrorWindowLayout.Inside(lp, sc.safe), sc.name + " left px " + lp);
                Assert.True(MirrorWindowLayout.Inside(rp, sc.safe), sc.name + " right px " + rp);
                var road = new Rect(w / 3f, 0f, w / 3f, h * 0.6f);
                Assert.False(l.Overlaps(road) || r.Overlaps(road), sc.name + " over the road");
                m_Out.WriteLine($"{sc.name}: ppu {ppu:F3}, canvas {w:F0}x{h:F0}, left px {lp}, right px {rp}, Low texel/px {MirrorWindowLayout.TexelsPerPixel(168, ppu):F2}");
            }
        }

        [Fact]
        public void Windows_DoNotFit_Reported()
        {
            Assert.False(Place(700f, new Rect(100f, 900f, 440f, 156f), 1056f, 12f, 24f, 24f, out _, out _));
            Assert.False(Place(1100f, new Rect(500f, 900f, 440f, 156f), 1056f, 12f, 24f, 24f, out _, out _));
            Assert.False(Place(1680f, new Rect(620f, 150f, 440f, 156f), 306f, 12f, 24f, 24f, out _, out _));
            Assert.Equal(0.6f, MirrorWindowLayout.TexelsPerPixel(168, 1f), 4);
        }

        [Fact]
        public void LayoutAndBudget_DoNotAllocate()
        {
            var cl = new Rect(620f, 900f, 440f, 156f);
            var safe = new Rect(80f, 0f, 2260f, 1080f);
            float acc = 0f;
            Place(1680f, cl, 1056f, 12f, 24f, 24f, out _, out _);
            MirrorInsetBudget.ExpectedRendersPerFrame(2, false);
            long before = GC.GetAllocatedBytesForCurrentThread();
            for (int i = 0; i < 1000; i++)
            {
                Place(1680f + i, cl, 1056f, 12f, 24f, 24f, out Rect l, out Rect r);
                acc += MirrorWindowLayout.ToScreenPixels(l, safe, 1.2f).x + (MirrorWindowLayout.Inside(r, safe) ? 1f : 0f)
                    + MirrorWindowLayout.TexelsPerPixel(168, 1f) + MirrorInsetBudget.Interval(4, i % 2 == 0)
                    + MirrorInsetBudget.ExpectedRendersPerFrame(i % 5, false);
            }
            long bytes = GC.GetAllocatedBytesForCurrentThread() - before;
            Assert.Equal(0L, bytes);
            Assert.True(acc > 0f);
        }

        // ---------------------------------------------------------------- Low schedule with windows

        [Fact]
        public void Policy_Table()
        {
            for (int lvl = 0; lvl < 4; lvl++)
            {
                Assert.Equal(lvl == 2, MirrorInsetBudget.DueFor(lvl, false));
                Assert.Equal(lvl == 2 || lvl == 0, MirrorInsetBudget.DueFor(lvl, true));
                Assert.True(MirrorInsetBudget.FillSpareFor(lvl, false, false));
                Assert.False(MirrorInsetBudget.FillSpareFor(lvl, false, true));
                Assert.Equal(lvl != 0, MirrorInsetBudget.FillSpareFor(lvl, true, false));
                Assert.Equal(lvl == 0, MirrorInsetBudget.Applies(lvl, true));
                Assert.False(MirrorInsetBudget.Applies(lvl, false));
            }
            Assert.Equal(3f, MirrorInsetBudget.Interval(2, false));
            Assert.Equal(3f, MirrorInsetBudget.Interval(2, true));
            foreach (int c in new[] { 4, 5, 6 }) { Assert.Equal(16f, MirrorInsetBudget.Interval(c, false)); Assert.Equal(32f, MirrorInsetBudget.Interval(c, true)); }
        }

        static readonly int[] k_Class = { 2, 2, 4, 4, 5, 6 };

        /// <summary>Low (cap 1). windows: due step with MirrorInsetBudget intervals, no fill; else the ADR 0042 round-robin.</summary>
        static (float perFrame, float[] mean, int[] maxGap, int maxN) Simulate(bool windows, bool[] candidate, bool standing, int frames = 960)
        {
            var e = new MirrorRefreshSchedule.Entry[6];
            for (int i = 0; i < 6; i++)
                e[i] = new MirrorRefreshSchedule.Entry
                {
                    phase = i, main = k_Class[i] == 2, weight = k_Class[i] == 2 ? 1f : 0.5f, candidate = candidate[i],
                    interval = MirrorInsetBudget.Interval(k_Class[i], standing), fill = k_Class[i] <= 4,
                };
            var last = new int[6]; var count = new int[6]; var sum = new long[6]; var maxGap = new int[6];
            for (int i = 0; i < 6; i++) last[i] = -1;
            int total = 0, maxN = 0, warm = 64;
            for (int f = 0; f < frames + warm; f++)
            {
                int n = windows
                    ? MirrorRefreshSchedule.StepDue(e, 6, 1, MirrorInsetBudget.FillSpareFor(0, true, standing))
                    : MirrorRefreshSchedule.Step(e, 6, 1, 0);
                if (f < warm) { for (int i = 0; i < 6; i++) if (e[i].selected) last[i] = f; continue; }
                total += n; if (n > maxN) maxN = n;
                for (int i = 0; i < 6; i++)
                {
                    if (!e[i].selected) continue;
                    if (last[i] >= 0) { int g = f - last[i]; sum[i] += g; count[i]++; if (g > maxGap[i]) maxGap[i] = g; }
                    last[i] = f;
                }
            }
            var mean = new float[6];
            for (int i = 0; i < 6; i++) mean[i] = count[i] > 0 ? (float)sum[i] / count[i] : float.PositiveInfinity;
            return (total / (float)frames, mean, maxGap, maxN);
        }

        void Report(string label, (float perFrame, float[] mean, int[] maxGap, int maxN) r) =>
            m_Out.WriteLine($"{label}: renders/frame {r.perFrame:F3}, max/frame {r.maxN}, mean interval [{string.Join(", ", Array.ConvertAll(r.mean, x => x.ToString("F2", CultureInfo.InvariantCulture)))}], max gap [{string.Join(", ", r.maxGap)}]");

        [Fact]
        public void LowWindows_AllSix()
        {
            var all = new[] { true, true, true, true, true, true };
            var r = Simulate(true, all, false); Report("windows all six driving", r);
            Assert.Equal(1, r.maxN);
            for (int i = 0; i < 2; i++) { Assert.InRange(r.mean[i], 2.95f, 3.05f); Assert.True(r.maxGap[i] <= 4, $"class II {i} gap {r.maxGap[i]}"); }
            for (int i = 2; i < 6; i++) Assert.InRange(r.mean[i], 15.5f, 16.5f);
            Assert.InRange(r.perFrame, MirrorInsetBudget.ExpectedRendersPerFrame(4, false) - 0.02f, MirrorInsetBudget.ExpectedRendersPerFrame(4, false) + 0.02f);
            var rr = Simulate(false, all, false); Report("round-robin all six", rr);
            Assert.InRange(rr.perFrame, 0.9999f, 1.0001f);
            var st = Simulate(true, all, true); Report("windows all six standing", st);
            Assert.InRange(st.perFrame, 2f / 3f + 4f / 32f - 0.02f, 2f / 3f + 4f / 32f + 0.02f);
        }

        [Fact]
        public void LowWindows_TypicalForward()
        {
            var view = new[] { true, true, true, false, false, true };
            var r = Simulate(true, view, false); Report("windows forward (II L/R + IV L + VI)", r);
            Assert.InRange(r.perFrame, 2f / 3f + 2f / 16f - 0.02f, 2f / 3f + 2f / 16f + 0.02f);
            Assert.InRange(r.mean[0], 2.95f, 3.05f); Assert.InRange(r.mean[1], 2.95f, 3.05f);
            Assert.True(r.maxGap[0] <= 4 && r.maxGap[1] <= 4, $"class II gaps {r.maxGap[0]} {r.maxGap[1]}");
            var rr = Simulate(false, view, false); Report("round-robin forward", rr);
            Assert.InRange(rr.perFrame, 0.9999f, 1.0001f);
            Assert.InRange(rr.mean[0], 2.8f, 3.2f);
            Assert.True(r.perFrame < 0.8f * rr.perFrame);
            var only = Simulate(true, new[] { true, true, false, false, false, false }, false); Report("windows only", only);
            Assert.InRange(only.perFrame, 2f / 3f - 0.02f, 2f / 3f + 0.02f);
        }
    }
}
