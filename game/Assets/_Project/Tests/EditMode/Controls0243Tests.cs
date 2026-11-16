using Game.Cameras;
using Game.Controls;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// ADR 0243 (D70): touch-wheel range presets (270 default, 900 in the settings) with the save migration, fixed mirror
    /// windows inside the safe area, and the Low mirror refresh policy while the windows are on. Pure logic only.
    /// Order of the mirrors as built by TruckAssetBuilder: MainL, MainR (class II), WideL, WideR (IV), Kerb (V), Front (VI).
    /// </summary>
    public class Controls0243Tests
    {
        /// <summary>Touch layout of the one mirror-window layout (Game.Cameras.MirrorWindowLayout.SolveTouch).</summary>
        static bool Place(float w, Rect cl, float top, float gap, float margin, float bottom, out Rect l, out Rect r)
        {
            MirrorWindowLayout.SolveTouch(w, cl, top, gap, margin, bottom, out var m);
            l = m.Left; r = m.Right;
            return m.Fits;
        }

        const string TestKey = "test.controls0243.settings";

        [SetUp] public void SetUp() => PlayerPrefs.DeleteKey(TestKey);
        [TearDown] public void TearDown() => PlayerPrefs.DeleteKey(TestKey);

        // ---------------------------------------------------------------- settings: range presets + schema 5

        [Test]
        public void Defaults_Wheel270_MirrorWindowsOn_Schema5()
        {
            var d = ControlSettings.Defaults();
            Assert.AreEqual(5, ControlSettings.CurrentSchema);
            Assert.AreEqual(ControlSettings.TouchHalfRangeComfortDeg, d.wheelRangeDeg);
            Assert.AreEqual(270f, ControlSettings.TouchHalfRangeComfortDeg);
            Assert.AreEqual(900f, ControlSettings.TouchHalfRangeSimDeg);
            Assert.AreEqual(ControlSettings.RangeMax, ControlSettings.TouchHalfRangeSimDeg, "900 is reachable in the settings");
            Assert.IsFalse(d.TouchWheelSimRange);
            Assert.IsTrue(d.mirrorInsets);
            StringAssert.Contains("mirrors=insets", d.LogLine("t"));
            StringAssert.Contains("wheelRange=270", d.LogLine("t"));
        }

        [Test]
        public void Preset_SetsExactValues_AndSurvivesSaveLoad()
        {
            var s = ControlSettings.Defaults();
            s.SetTouchWheelPreset(true);
            Assert.AreEqual(900f, s.wheelRangeDeg);
            Assert.IsTrue(s.TouchWheelSimRange);
            s.mirrorInsets = false;
            s.Save(TestKey);
            var l = ControlSettings.Load(TestKey, null);
            Assert.AreEqual(900f, l.wheelRangeDeg);
            Assert.IsFalse(l.mirrorInsets, "explicit v5 choice kept");
            Assert.AreEqual(5, l.schema);
            StringAssert.Contains("mirrors=look", l.LogLine("t"));
            l.SetTouchWheelPreset(false);
            Assert.AreEqual(270f, l.wheelRangeDeg);
            Assert.IsFalse(l.TouchWheelSimRange);
        }

        [Test]
        public void Migration_V4_KeepsRange_SwitchesWindowsOn()
        {
            foreach (float range in new[] { 270f, 450f, 900f })
            {
                var v4 = ControlSettings.FromJson("{\"schema\":4,\"wheelRangeDeg\":" + range.ToString(System.Globalization.CultureInfo.InvariantCulture) + ",\"wheelDragGrab\":false}");
                Assert.AreEqual(5, v4.schema);
                Assert.AreEqual(range, v4.wheelRangeDeg, "the player's own range is kept");
                Assert.IsTrue(v4.mirrorInsets, "D70: windows on for an old save");
                Assert.IsFalse(v4.wheelDragGrab, "other v4 choices kept");
            }
            // Even a hand-written v4 with the (unknown in v4) field off gets the owner's default.
            Assert.IsTrue(ControlSettings.FromJson("{\"schema\":4,\"mirrorInsets\":false}").mirrorInsets);
            // Schema-less (Stage 1/2 JSON) and the legacy int key also end with the defaults of v5.
            Assert.IsTrue(ControlSettings.FromJson("{\"wheelRangeDeg\":360}").mirrorInsets);
            var legacy = ControlSettings.FromLegacySteerMode(1);
            Assert.AreEqual(900f, legacy.wheelRangeDeg);
            Assert.IsTrue(legacy.mirrorInsets);
            Assert.AreEqual(270f, ControlSettings.FromLegacySteerMode(0).wheelRangeDeg);
        }

        [Test]
        public void Migration_V5_RoundTrip_Clamp_Reset()
        {
            var v5 = ControlSettings.FromJson("{\"schema\":5,\"wheelRangeDeg\":5000,\"mirrorInsets\":false}");
            Assert.AreEqual(900f, v5.wheelRangeDeg, "clamped to the simulator range");
            Assert.IsFalse(v5.mirrorInsets);
            Assert.AreEqual(v5.ToJson(), ControlSettings.FromJson(v5.ToJson()).ToJson());
            Assert.AreEqual(180f, ControlSettings.FromJson("{\"schema\":5,\"wheelRangeDeg\":10}").wheelRangeDeg);
            v5.ResetToDefaults();
            Assert.AreEqual(270f, v5.wheelRangeDeg);
            Assert.IsTrue(v5.mirrorInsets);
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

        [Test]
        public void Direction_BothPresets_BothGestures_RightPositiveLeftNegative()
        {
            foreach (bool sim in new[] { false, true })
            foreach (bool drag in new[] { true, false })
            {
                var s = ControlSettings.Defaults(); s.SetTouchWheelPreset(sim); s.wheelDragGrab = drag;
                Assert.Greater(WheelSteer(s, 1f), 0.02f, $"sim {sim} drag {drag} right");
                Assert.Less(WheelSteer(s, -1f), -0.02f, $"sim {sim} drag {drag} left");
            }
            // Same finger travel: the simulator range turns less than the comfort range (rotate gesture is 1:1 on screen).
            var c = ControlSettings.Defaults(); c.wheelDragGrab = false; c.speedSensitiveSteering = false; c.wheelDeadZone = 0f;
            var m = c.Clone(); m.SetTouchWheelPreset(true);
            Assert.AreEqual(270f / 900f, WheelSteer(m, 1f) / WheelSteer(c, 1f), 0.02f);
        }

        // ---------------------------------------------------------------- mirror windows: layout in the safe area

        /// <summary>Reference-phone canvas scale (UiScale, DPI unknown): 1080 units on the short side, at least 1680 across.</summary>
        static float PixelsPerUnit(Rect safe)
        {
            float shortPx = Mathf.Min(safe.width, safe.height);
            float s = shortPx / 1080f;
            if (safe.width / s < 1680f) s = safe.width / 1680f;
            return s;
        }

        // name, screen width, height (landscape px), safe area x, y, w, h (notch / gesture bar / punch hole).
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

        [Test]
        public void Windows_InsideSafeArea_BesideCluster_Symmetric_OnEveryScreen()
        {
            Vector2 cluster = new Vector2(440f, 156f);   // HudLayout.ClusterSize (Game.UI; not referenced by this assembly)
            const float margin = 24f, gap = 12f;
            foreach (var sc in k_Screens)
            {
                float ppu = PixelsPerUnit(sc.safe);
                float w = sc.safe.width / ppu, h = sc.safe.height / ppu, top = h - margin;
                var cl = new Rect(w * 0.5f - cluster.x * 0.5f, top - cluster.y, cluster.x, cluster.y);
                bool fits = Place(w, cl, top, gap, margin, margin, out Rect l, out Rect r);
                Assert.IsTrue(fits, sc.name + ": windows fit");
                var canvas = new Rect(0f, 0f, w, h);
                Assert.IsTrue(MirrorWindowLayout.Inside(l, canvas), sc.name + " left in canvas " + l);
                Assert.IsTrue(MirrorWindowLayout.Inside(r, canvas), sc.name + " right in canvas " + r);
                Assert.IsFalse(l.Overlaps(cl), sc.name + ": left over cluster");
                Assert.IsFalse(r.Overlaps(cl), sc.name + ": right over cluster");
                Assert.Less(l.xMax, cl.xMin + 1e-3f, sc.name + ": left window is left of the cluster");
                Assert.Greater(r.xMin, cl.xMax - 1e-3f, sc.name + ": right window is right of the cluster");
                Assert.AreEqual(w * 0.5f - l.center.x, r.center.x - w * 0.5f, 1e-3f, sc.name + ": symmetric");
                Assert.AreEqual(l.yMax, r.yMax, 1e-3f);
                Assert.AreEqual(top, l.yMax, 1e-3f, sc.name + ": hangs from the top margin");
                // In screen pixels: inside Screen.safeArea (notch, punch hole, gesture bar never covered).
                var lp = MirrorWindowLayout.ToScreenPixels(l, sc.safe, ppu);
                var rp = MirrorWindowLayout.ToScreenPixels(r, sc.safe, ppu);
                Assert.IsTrue(MirrorWindowLayout.Inside(lp, sc.safe), sc.name + " left px " + lp + " safe " + sc.safe);
                Assert.IsTrue(MirrorWindowLayout.Inside(rp, sc.safe), sc.name + " right px " + rp);
                Assert.IsTrue(MirrorWindowLayout.Inside(lp, new Rect(0f, 0f, sc.w, sc.h)), sc.name + " on screen");
                // The road ahead (centre third of the width, lower 60 %) is not covered by a window.
                var road = new Rect(w / 3f, 0f, w / 3f, h * 0.6f);
                Assert.IsFalse(l.Overlaps(road) || r.Overlaps(road), sc.name + ": windows over the road ahead");
            }
        }

        [Test]
        public void Windows_DoNotFit_ReportedNotForced()
        {
            var cl = new Rect(100f, 900f, 440f, 156f);
            Assert.IsFalse(Place(700f, cl, 1056f, 12f, 24f, 24f, out _, out _), "left window off the canvas");
            var mid = new Rect(500f, 900f, 440f, 156f);
            Assert.IsFalse(Place(1100f, mid, 1056f, 12f, 24f, 24f, out _, out _), "right window off the canvas");
            Assert.IsFalse(Place(1680f, new Rect(620f, 150f, 440f, 156f), 306f, 12f, 24f, 24f, out _, out _), "below the bottom limit");
        }

        [Test]
        public void Windows_TexelRatio_A16Low()
        {
            // A16 Low: class II texture 224 x mirrorResolutionScale 0.75 = 168 rows (ADR 0136 r2); image 280 units at
            // 1 px/unit on a 1080-px-high screen -> 0.6 texel per pixel (magnified 1.67x).
            Assert.AreEqual(new Vector2(150f, 280f), MirrorWindowLayout.TouchImageSize);
            Assert.AreEqual(0.6f, MirrorWindowLayout.TexelsPerPixel(168, 1f), 1e-4f);
            Assert.AreEqual(1f, MirrorWindowLayout.TexelsPerPixel(280, 1f), 1e-4f);
            Assert.AreEqual(0f, MirrorWindowLayout.TexelsPerPixel(168, 0f));
            Assert.AreEqual(168, Mathf.RoundToInt(VehicleCameraBudget.MirrorHeightFor(0) * 0.75f));
        }

        /// <summary>
        /// H12: counted with <see cref="GcAllocCounter"/> (Recorder "GC.Alloc"). GC.GetAllocatedBytesForCurrentThread is 0 under
        /// Mono in the editor, so the former check could not fail in Unity (the .NET runner keeps it - valid on CoreCLR).
        /// Both form factors of the one layout (touch + monitor) and the Low window budget.
        /// </summary>
        [Test]
        public void Windows_Layout_DoesNotAllocate()
        {
            var cl = new Rect(620f, 900f, 440f, 156f);
            var safe = new Rect(80f, 0f, 2260f, 1080f);
            float acc = 0f;
            void Run()
            {
                for (int i = 0; i < 1000; i++)
                {
                    Place(1680f + i, cl, 1056f, 12f, 24f, 24f, out Rect l, out Rect r);
                    MirrorWindowLayout.Solve(new MirrorWindowInput { Width = 2560f + i, Height = 1440f, Centre = cl, Aspect = 0.55f, SideReserve = 162f }, out var m);
                    acc += MirrorWindowLayout.ToScreenPixels(l, safe, 1.2f).x + (MirrorWindowLayout.Inside(r, safe) ? 1f : 0f) + m.Left.width
                        + MirrorWindowLayout.TexelsPerPixel(168, 1f) + MirrorInsetBudget.Interval(4, i % 2 == 0)
                        + MirrorInsetBudget.ExpectedRendersPerFrame(i % 5, false);
                }
            }
            GcAllocCounter.AssertZero(Run, warmup: Run, message: "mirror window layout / budget maths must not allocate");
            Assert.Greater(acc, 0f);
        }

        // ---------------------------------------------------------------- Low refresh policy with the windows

        [Test]
        public void Policy_OnlyLowWithWindows_ChangesTheSchedule()
        {
            for (int lvl = 0; lvl < 4; lvl++)
            {
                // Windows off: every tier exactly as before (ADR 0042 / 0046 / 0068).
                Assert.AreEqual(VehicleCameraBudget.DueScheduleFor(lvl), MirrorInsetBudget.DueFor(lvl, false), $"level {lvl}");
                foreach (bool standing in new[] { false, true })
                {
                    Assert.AreEqual(!standing, VehicleCameraBudget.FillSpare(lvl, false, standing), $"level {lvl} fill");
                    foreach (int cls in new[] { 2, 4, 5, 6 })
                        Assert.AreEqual(VehicleCameraBudget.MirrorIntervalFor(lvl, cls, standing), VehicleCameraBudget.MirrorIntervalFor(lvl, cls, standing, false), $"level {lvl} class {cls}");
                }
                if (lvl == 0) continue;
                // Windows on, Medium / High / Ultra: unchanged.
                Assert.AreEqual(VehicleCameraBudget.DueScheduleFor(lvl), MirrorInsetBudget.DueFor(lvl, true), $"level {lvl} windows");
                Assert.AreEqual(true, VehicleCameraBudget.FillSpare(lvl, true, false));
                foreach (int cls in new[] { 2, 4, 5, 6 })
                    Assert.AreEqual(VehicleCameraBudget.MirrorIntervalFor(lvl, cls, false), VehicleCameraBudget.MirrorIntervalFor(lvl, cls, false, true));
            }
            Assert.IsTrue(MirrorInsetBudget.DueFor(0, true));
            Assert.IsFalse(VehicleCameraBudget.FillSpare(0, true, false), "no spare fill on Low with windows");
            Assert.AreEqual(3f, VehicleCameraBudget.MirrorIntervalFor(0, 2, false, true));
            Assert.AreEqual(3f, VehicleCameraBudget.MirrorIntervalFor(0, 2, true, true), "class II keeps its rate standing");
            foreach (int cls in new[] { 4, 5, 6 })
            {
                Assert.AreEqual(16f, VehicleCameraBudget.MirrorIntervalFor(0, cls, false, true));
                Assert.AreEqual(32f, VehicleCameraBudget.MirrorIntervalFor(0, cls, true, true));
            }
            Assert.AreEqual(1, VehicleCameraBudget.MirrorsPerFrameFor(0), "Low cap unchanged");
        }

        static readonly int[] k_Class = { 2, 2, 4, 4, 5, 6 };

        /// <summary>Runs the Low schedule; returns mean renders/frame, mean and max interval per mirror (frames).</summary>
        static (float perFrame, float[] mean, int[] maxGap, int maxN) Simulate(bool windows, bool[] candidate, bool standing, int frames = 960)
        {
            var e = new MirrorRefreshSchedule.Entry[6];
            for (int i = 0; i < 6; i++)
                e[i] = new MirrorRefreshSchedule.Entry
                {
                    phase = i, main = k_Class[i] == 2, weight = k_Class[i] == 2 ? 1f : 0.5f, candidate = candidate[i],
                    interval = VehicleCameraBudget.MirrorIntervalFor(0, k_Class[i], standing, windows), fill = k_Class[i] <= 4,
                };
            var last = new int[6]; var count = new int[6]; var sum = new long[6]; var maxGap = new int[6];
            for (int i = 0; i < 6; i++) last[i] = -1;
            int total = 0, maxN = 0, warm = 64;
            for (int f = 0; f < frames + warm; f++)
            {
                int n = MirrorInsetBudget.DueFor(0, windows)
                    ? MirrorRefreshSchedule.StepDue(e, 6, 1, VehicleCameraBudget.FillSpare(0, windows, standing))
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

        [Test]
        public void LowWindows_AllSix_ClassIIEvery3rd_Convex16th_UnderCap()
        {
            var all = new[] { true, true, true, true, true, true };
            var (pf, mean, gap, maxN) = Simulate(true, all, false);
            Assert.AreEqual(1, maxN, "never more than the Low cap of 1 per frame");
            for (int i = 0; i < 2; i++) { Assert.AreEqual(3f, mean[i], 0.05f, $"class II {i} mean"); Assert.LessOrEqual(gap[i], 4, $"class II {i} max gap"); }
            for (int i = 2; i < 6; i++) Assert.AreEqual(16f, mean[i], 0.5f, $"convex {i} mean");
            Assert.AreEqual(MirrorInsetBudget.ExpectedRendersPerFrame(4, false), pf, 0.02f);
            Assert.AreEqual(2f / 3f + 4f / 16f, pf, 0.02f);
            // The ADR 0042 round-robin (the A/B "rq_mirror_rate 0") renders one mirror every frame.
            var (rr, _, _, _) = Simulate(false, all, false);
            Assert.AreEqual(1f, rr, 1e-4f);
        }

        [Test]
        public void LowWindows_TypicalForwardView_RendersLessThanRoundRobin_SameClassIIRate()
        {
            // Cab view ahead: both windows (forced) + left wide-angle + front mirror glass on screen.
            var view = new[] { true, true, true, false, false, true };
            var (pf, mean, gap, _) = Simulate(true, view, false);
            Assert.AreEqual(2f / 3f + 2f / 16f, pf, 0.02f);
            Assert.AreEqual(MirrorInsetBudget.ExpectedRendersPerFrame(2, false), pf, 0.02f);
            Assert.AreEqual(3f, mean[0], 0.05f); Assert.AreEqual(3f, mean[1], 0.05f);
            Assert.LessOrEqual(gap[0], 4, "jitter of one frame at most"); Assert.LessOrEqual(gap[1], 4);
            var (rr, rrMean, _, _) = Simulate(false, view, false);
            Assert.AreEqual(1f, rr, 1e-4f);
            Assert.AreEqual(3f, rrMean[0], 0.2f, "the round-robin already refreshed class II every 3rd frame here");
            Assert.Less(pf, 0.8f * rr, "at least 20 % fewer mirror renders");
            // Windows only (no glass on screen) and standing.
            var only = new[] { true, true, false, false, false, false };
            Assert.AreEqual(2f / 3f, Simulate(true, only, false).perFrame, 0.02f);
            Assert.AreEqual(2f / 3f + 4f / 32f, Simulate(true, new[] { true, true, true, true, true, true }, true).perFrame, 0.02f);
        }
    }
}
