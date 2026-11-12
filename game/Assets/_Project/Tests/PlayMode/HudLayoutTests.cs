using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using Game.Cameras;
using Game.Controls;
using Game.Gameplay;
using Game.UI;
using Game.UI.Driving;
using Game.UI.Layout;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using UnityEngine.UI;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0079 - adaptive HUD layout. For every supported screen (21:9 phones, the near-square inner screen of a
    /// foldable in both orientations, a 16:10 tablet) and every HUD state: no two zones overlap and everything lies
    /// inside the safe area - first on the pure solver, then on the real uGUI objects (HUD, settings panel, start menu).
    /// </summary>
    public class HudLayoutTests
    {
        public struct Device
        {
            public string Name; public int W, H; public float Dpi;
            /// <summary>Safe-area insets in pixels (left, right, top, bottom).</summary>
            public float L, R, T, B;
            public Rect SafePx => new Rect(L, B, W - L - R, H - T - B);
            public override string ToString() => Name;
        }

        // DPI values are nominal (UNVERIFIED on the devices); the layout must hold for any DPI, including unknown (0).
        static readonly Device[] k_Devices =
        {
            new Device { Name = "phone-2400x1080", W = 2400, H = 1080, Dpi = 400f, L = 90f },
            new Device { Name = "phone-2340x1080-A16", W = 2340, H = 1080, Dpi = 385f, L = 94f },
            new Device { Name = "fold-inner-2176x1812", W = 2176, H = 1812, Dpi = 368f, T = 60f },
            new Device { Name = "fold-inner-rotated-1968x2184", W = 1968, H = 2184, Dpi = 368f, T = 60f },
            new Device { Name = "tablet-2560x1600", W = 2560, H = 1600, Dpi = 274f },
            // Portrait is not a supported orientation (landscape only); the solver must still not overlap anything.
            new Device { Name = "portrait-1080x2400-unsupported", W = 1080, H = 2400, Dpi = 400f, T = 90f },
        };

        static IEnumerable<Device> Devices => k_Devices;
        const int StateCount = 1 << 7;

        static HudLayoutInput State(Vector2 size, int bits) => new HudLayoutInput
        {
            Width = size.x, Height = size.y,
            Gyro = (bits & 1) != 0, DevPanelOpen = (bits & 2) != 0, Telemetry = (bits & 4) != 0, MirrorLeft = (bits & 8) != 0,
            MirrorRight = (bits & 16) != 0, ReverseView = (bits & 32) != 0, DevText = (bits & 64) != 0,
        };

        /// <summary>Null when the zones are fine, otherwise what is wrong (the message is only built on failure:
        /// the sweeps check millions of rectangle pairs).</summary>
        static string CheckZones(in HudLayoutResult r, Vector2 size)
        {
            const float eps = 0.01f;
            for (int i = 0; i < HudLayoutResult.ZoneCount; i++)
            {
                if (!r.Zone(i, out Rect a)) continue;
                if (a.width <= 1f || a.height <= 1f) return $"{HudLayoutResult.ZoneName(i)} {a} is empty";
                if (!(a.xMin >= -eps && a.yMin >= -eps && a.xMax <= size.x + eps && a.yMax <= size.y + eps))
                    return $"{HudLayoutResult.ZoneName(i)} {a} outside the safe area {size}";
                for (int j = i + 1; j < HudLayoutResult.ZoneCount; j++)
                {
                    if (!r.Zone(j, out Rect b)) continue;
                    if (a.xMin < b.xMax - eps && b.xMin < a.xMax - eps && a.yMin < b.yMax - eps && b.yMin < a.yMax - eps)
                        return $"{HudLayoutResult.ZoneName(i)} {a} overlaps {HudLayoutResult.ZoneName(j)} {b}";
                }
            }
            return null;
        }

        static void AssertZones(in HudLayoutResult r, Vector2 size, string what)
        {
            string err = CheckZones(r, size);
            if (err != null) Assert.Fail(what + ": " + err);
        }

        [Test]
        public void Scale_FollowsShorterSideAndDpi_NotFixedPixels()
        {
            // Reference phone: one unit = one pixel.
            Assert.AreEqual(1f, UiScale.PixelsPerUnit(2340f, 1080f, 385f), 0.02f);
            Assert.AreEqual(1f, UiScale.PixelsPerUnit(2340f, 1080f, 0f), 1e-4f);
            // Foldable inner screen: more units than the old height-matched 1297 x 1080, so the same controls take less of the view.
            Vector2 fold = UiScale.SizeUnits(2176f, 1812f, 368f);
            Assert.Greater(fold.y, 1400f); Assert.Greater(fold.x, 1700f);
            // Unknown DPI on a near-square screen: the minimum width still holds.
            Vector2 sq = UiScale.SizeUnits(1812f, 1812f, 0f);
            Assert.AreEqual(UiScale.MinWidthUnits, sq.x, 0.5f);
            // The same resolution at twice the pixel density is a smaller screen: fewer units (bigger controls relative to it).
            Assert.Less(UiScale.SizeUnits(2560f, 1600f, 548f).y, UiScale.SizeUnits(2560f, 1600f, 274f).y);
            foreach (var d in k_Devices)
                foreach (float dpi in new[] { 0f, d.Dpi, 160f, 640f })
                {
                    Vector2 u = UiScale.SizeUnits(d.SafePx.width, d.SafePx.height, dpi);
                    Assert.GreaterOrEqual(u.x, UiScale.MinWidthUnits - 0.5f, d.Name);
                    Assert.GreaterOrEqual(Mathf.Min(u.x, u.y), UiScale.ReferenceShortUnits - 0.5f, d.Name);
                }
        }

        [Test]
        public void Solver_NoOverlap_InsideSafeArea_AllDevicesAllStates([ValueSource(nameof(Devices))] Device d)
        {
            int checkedStates = 0;
            foreach (float dpi in new[] { 0f, d.Dpi, 160f, 640f })
                foreach (bool cutout in new[] { false, true })
                {
                    Rect safe = cutout ? d.SafePx : new Rect(0, 0, d.W, d.H);
                    Vector2 size = UiScale.SizeUnits(safe.width, safe.height, dpi);
                    for (int bits = 0; bits < StateCount; bits++)
                    {
                        HudLayout.Solve(State(size, bits), out var r);
                        string err = CheckZones(r, size);
                        if (err != null) Assert.Fail($"{d.Name} dpi {dpi} cutout {cutout} state {Convert.ToString(bits, 2)}: {err}");
                        checkedStates++;
                    }
                }
            Debug.Log($"[HUD-R10] solver {d.Name}: {checkedStates} layouts, no overlap, all inside the safe area");
        }

        [Test]
        public void Solver_NoOverlap_AspectSweep_1to1_to_21to9_AndBeyond()
        {
            int checkedStates = 0;
            for (float aspect = 0.45f; aspect <= 3.2f; aspect += 0.01f)
                foreach (float shortPx in new[] { 720f, 1080f, 1440f, 1812f, 2160f })
                    foreach (float dpi in new[] { 0f, 220f, 400f })
                    {
                        float w = aspect >= 1f ? shortPx * aspect : shortPx, h = aspect >= 1f ? shortPx : shortPx / aspect;
                        Vector2 size = UiScale.SizeUnits(w, h, dpi);
                        for (int bits = 0; bits < StateCount; bits++)
                        {
                            HudLayout.Solve(State(size, bits), out var r);
                            string err = CheckZones(r, size);
                            if (err != null) Assert.Fail($"aspect {aspect:F2} short {shortPx} dpi {dpi} state {Convert.ToString(bits, 2)}: {err}");
                            checkedStates++;
                        }
                    }
            Debug.Log($"[HUD-R10] solver aspect sweep 0.45..3.2: {checkedStates} layouts, no overlap, all inside the safe area");
        }

        [Test]
        public void Solver_MirrorInsetsStay_WhenNoDeveloperOverlayNeedsTheirPlace()
        {
            foreach (var d in k_Devices)
            {
                Vector2 size = UiScale.SizeUnits(d.SafePx.width, d.SafePx.height, d.Dpi);
                HudLayout.Solve(State(size, 8 | 16), out var r);
                Assert.IsTrue(r.ShowMirrorLeft && r.ShowMirrorRight, d.Name + ": both insets while driving");
                HudLayout.Solve(State(size, 8 | 16 | 32), out r);
                Assert.IsTrue(r.ShowMirrorLeft && r.ShowMirrorRight && r.ShowReverseView, d.Name + ": insets + reversing view");
            }
        }

        [Test]
        public void Solver_ControlsCoverLessOfTheView_ThanTheFixedLayout()
        {
            // Old layout on the Fold inner screen (height-matched 1297 x 1080 canvas): the right-hand group reached 616 of
            // 1080 units (57 % of the height), the left one 590 (55 %). Now, with the nominal DPI:
            Vector2 size = UiScale.SizeUnits(2176f, 1812f, 368f);
            HudLayout.Solve(State(size, 0), out var r);
            float right = Mathf.Max(r.Throttle.yMax, r.Gears.yMax) / size.y, left = Mathf.Max(r.TurnSignals.yMax, r.Stalk.yMax) / size.y;
            Debug.Log($"[HUD-R10] fold inner {size.x:F0}x{size.y:F0} units: left controls top {left:P0}, right controls top {right:P0} of the height, cluster bottom {(size.y - r.Cluster.yMin) / size.y:P0} from the top");
            Assert.Less(right, 0.30f);
            Assert.Less(left, 0.36f);
        }

        // ------------------------------------------------------------------ real uGUI objects

        Camera m_Cam;
        RenderTexture m_Rt;
        Texture2D m_Fake;

        void MakeCamera(Device d)
        {
            var go = new GameObject("HudLayoutCam");
            m_Cam = go.AddComponent<Camera>();
            m_Cam.clearFlags = CameraClearFlags.SolidColor;
            m_Cam.backgroundColor = new Color(0.30f, 0.34f, 0.38f);
            m_Cam.nearClipPlane = 0.05f; m_Cam.farClipPlane = 10f;
            m_Cam.cullingMask = 1 << 5;
            m_Rt = new RenderTexture(d.W, d.H, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            m_Cam.targetTexture = m_Rt;
            m_Fake = new Texture2D(4, 4);
        }

        [TearDown]
        public void TearDown()
        {
            if (m_Cam != null) { m_Cam.targetTexture = null; UnityEngine.Object.Destroy(m_Cam.gameObject); }
            if (m_Rt != null) { m_Rt.Release(); UnityEngine.Object.Destroy(m_Rt); }
            if (m_Fake != null) UnityEngine.Object.Destroy(m_Fake);
            foreach (var h in UnityEngine.Object.FindObjectsByType<DrivingHud>(FindObjectsSortMode.None)) UnityEngine.Object.Destroy(h.gameObject);
            foreach (var p in UnityEngine.Object.FindObjectsByType<ControlSettingsPanel>(FindObjectsSortMode.None)) UnityEngine.Object.Destroy(p.gameObject);
            foreach (var m in UnityEngine.Object.FindObjectsByType<BootMenu>(FindObjectsSortMode.None)) UnityEngine.Object.Destroy(m.gameObject);
            PlayerPrefs.DeleteKey(ControlSettings.PrefKey);
        }

        static readonly Vector3[] s_Corners = new Vector3[4];

        /// <summary>Rect of <paramref name="rt"/> in the local space of <paramref name="space"/>, origin at its bottom-left corner.</summary>
        static Rect RectIn(RectTransform rt, RectTransform space)
        {
            rt.GetWorldCorners(s_Corners);
            Vector2 min = new Vector2(float.MaxValue, float.MaxValue), max = new Vector2(float.MinValue, float.MinValue);
            for (int i = 0; i < 4; i++)
            {
                Vector2 p = space.InverseTransformPoint(s_Corners[i]);
                min = Vector2.Min(min, p); max = Vector2.Max(max, p);
            }
            min -= space.rect.min; max -= space.rect.min;
            return Rect.MinMaxRect(min.x, min.y, max.x, max.y);
        }

        static bool Contains(Rect outer, Rect inner, float eps) =>
            inner.xMin >= outer.xMin - eps && inner.yMin >= outer.yMin - eps && inner.xMax <= outer.xMax + eps && inner.yMax <= outer.yMax + eps;

        /// <summary>The solved zones match the real rect transforms, every graphic of a zone stays inside it, zones do not
        /// overlap and lie in the safe area, and the safe area has the size the scale promises.</summary>
        [UnityTest]
        public IEnumerator Hud_RealObjects_NoOverlap_InsideSafeArea([ValueSource(nameof(Devices))] Device d)
        {
            MakeCamera(d);
            bool gyro = false, mirrors = false, reverse = false;
            var ctx = new DrivingHudContext
            {
                IsGyroMode = () => gyro,
                LeftMirrorTexture = () => mirrors ? m_Fake : null,
                RightMirrorTexture = () => mirrors ? m_Fake : null,
                ReverseCameraTexture = () => reverse ? m_Fake : null,
                ReverseCameraLabel = () => "KAMERA COFANIA (naczepa)",
                StatusLine = () => "AUTOPILOT (pomiar)",
                CouplingStatus = () => "Naczepa odpięta (nogi opuszczone) · sworzeń 2.00 m za siodłem",
            };
            var hud = DrivingHud.Create(m_Cam, ctx);
            hud.OverrideScreen(new Vector2(d.W, d.H), d.SafePx, d.Dpi);
            yield return null;

            // driving / mirrors / mirrors + reverse / gyro + developer everything / developer panel only
            int[] states = { 0, 8 | 16, 8 | 16 | 32, 1 | 2 | 4 | 8 | 16 | 32 | 64, 2 | 8 | 16, 4 | 8 | 16 | 64 };
            foreach (int bits in states)
            {
                gyro = (bits & 1) != 0; mirrors = (bits & 8) != 0; reverse = (bits & 32) != 0;
                hud.SetDevPanelOpen((bits & 2) != 0);
                hud.SetTelemetryVisible((bits & 4) != 0);
                hud.SetDevDiagnostics((bits & 64) != 0);
                hud.RefreshNow();
                yield return null;
                Canvas.ForceUpdateCanvases();
                string what = $"{d.Name} state {Convert.ToString(bits, 2)}";

                var safe = hud.SafeAreaRect;
                Vector2 expect = UiScale.SizeUnits(d.SafePx.width, d.SafePx.height, d.Dpi);
                Assert.AreEqual(expect.x, hud.SafeSizeUnits.x, 0.5f, what);
                Assert.AreEqual(expect.x, safe.rect.width, 1.5f, what + ": safe-area rect width [units] (canvas scale applied)");
                Assert.AreEqual(expect.y, safe.rect.height, 1.5f, what + ": safe-area rect height [units]");
                var canvasRt = (RectTransform)hud.transform;
                Assert.IsTrue(Contains(new Rect(Vector2.zero, canvasRt.rect.size), RectIn(safe, canvasRt), 1f), what + ": safe area inside the canvas");

                var layout = hud.Layout;
                AssertZones(layout, hud.SafeSizeUnits, what);
                var bounds = new Rect(Vector2.zero, safe.rect.size);
                for (int i = 0; i < HudLayoutResult.ZoneCount; i++)
                {
                    bool on = layout.Zone(i, out Rect solved);
                    var zt = hud.ZoneTransform(i);
                    string zn = HudLayoutResult.ZoneName(i);
                    if (i != 1 && i != 14) Assert.AreEqual(on, zt.gameObject.activeInHierarchy, $"{what}: {zn} visibility");
                    if (!on) continue;
                    Rect real = RectIn(zt, safe);
                    Assert.IsTrue(Contains(solved, real, 0.6f) && Contains(real, solved, 0.6f), $"{what}: {zn} real {real} != solved {solved}");
                    Assert.IsTrue(Contains(bounds, real, 0.6f), $"{what}: {zn} {real} outside the safe area {bounds.size}");
                    foreach (var g in zt.GetComponentsInChildren<Graphic>(false))
                    {
                        if (g.transform.parent != null && g.transform.parent.name == "Rotating") continue;
                        if (g.name == "Rotating") continue;   // the wheel sprite turns inside its square
                        Rect gr = RectIn(g.rectTransform, safe);
                        if (g.name == "GrabArea")
                        {
                            // ADR 0135: invisible touch target of the wheel, extended over the empty margin to the
                            // safe-area edges left of and below the wheel; it must stay inside the safe area and must not
                            // reach any other zone (checked against every zone below).
                            Assert.AreEqual(0f, g.color.a, 1e-6f, $"{what}: GrabArea is invisible");
                            Assert.IsTrue(Contains(bounds, gr, 0.6f), $"{what}: GrabArea {gr} outside the safe area");
                            Assert.IsTrue(Contains(gr, real, 0.6f), $"{what}: GrabArea {gr} does not cover the whole wheel {real}");
                            Assert.IsTrue(gr.xMin <= Mathf.Max(0f, real.xMin - 59f) + 0.6f && gr.yMin <= Mathf.Max(0f, real.yMin - 59f) + 0.6f, $"{what}: GrabArea {gr} margin left/below the wheel {real}");
                            for (int j = 0; j < HudLayoutResult.ZoneCount; j++)
                                if (j != i && layout.Zone(j, out Rect other) && other.Overlaps(gr) && Rect.MinMaxRect(Mathf.Max(other.xMin, gr.xMin), Mathf.Max(other.yMin, gr.yMin), Mathf.Min(other.xMax, gr.xMax), Mathf.Min(other.yMax, gr.yMax)).width > 0.6f
                                    && Rect.MinMaxRect(Mathf.Max(other.xMin, gr.xMin), Mathf.Max(other.yMin, gr.yMin), Mathf.Min(other.xMax, gr.xMax), Mathf.Min(other.yMax, gr.yMax)).height > 0.6f)
                                    Assert.Fail($"{what}: GrabArea {gr} overlaps {HudLayoutResult.ZoneName(j)} {other}");
                            continue;
                        }
                        Assert.IsTrue(Contains(real, gr, 2.5f), $"{what}: {zn}/{g.name} {gr} sticks out of its zone {real}");
                    }
                }
            }
            UnityEngine.Object.Destroy(hud.gameObject);
        }

        /// <summary>ADR 0135 r2: the wheel touch target covers the drawing + margin (30 % radius or 8 mm), reaches the
        /// safe-area edges left/below, and never covers another zone (buttons, pedals).</summary>
        [Test]
        public void WheelGrabRect_CoversDrawingPlusMargin_NeverOverButtons()
        {
            foreach (var (name, w, h, ppu, dpi) in new (string, float, float, float, float)[]
                     { ("fold inner 2184x1968", 2184f, 1968f, 2184f / 1680f, 374f), ("fold inner 1200x1080", 1200f, 1080f, 1200f / 1680f, 374f),
                       ("cover 2340x1080", 2340f, 1080f, 1f, 420f), ("S24+ 2340x1080", 2340f, 1080f, 1f, 516f) })
            {
                var size = Game.UI.Layout.UiScale.SizeUnits(w, h, dpi);
                var input = new Game.UI.Driving.HudLayoutInput { Width = size.x, Height = size.y };
                Game.UI.Driving.HudLayout.Solve(input, out var r);
                float m = Game.UI.Driving.HudLayout.GrabMarginUnits(Game.UI.Layout.UiScale.PixelsPerUnit(w, h, dpi), dpi);
                Rect g = Game.UI.Driving.HudLayout.WheelGrabRect(r, size.x, size.y, m);
                Rect wheel = new Rect(r.Steering.x, r.Steering.y, Game.UI.Driving.HudLayout.WheelSize, Game.UI.Driving.HudLayout.WheelSize);
                Assert.IsTrue(g.xMin <= wheel.xMin && g.yMin <= wheel.yMin && g.xMax >= wheel.xMax && g.yMax >= wheel.yMax, name + ": covers the drawing");
                Assert.AreEqual(Mathf.Max(0f, wheel.xMin - m), g.xMin, 0.01f, name + ": left margin / safe edge");
                Assert.AreEqual(Mathf.Max(0f, wheel.yMin - m), g.yMin, 0.01f, name + ": bottom margin / safe edge");
                Assert.GreaterOrEqual(m, 60f - 1e-3f, name + ": >= 30 % of the radius");
                for (int i = 0; i < Game.UI.Driving.HudLayoutResult.ZoneCount; i++)
                {
                    if (i == 8 || !r.Zone(i, out Rect z)) continue;
                    bool overlap = z.xMin < g.xMax - 0.01f && z.xMax > g.xMin + 0.01f && z.yMin < g.yMax - 0.01f && z.yMax > g.yMin + 0.01f;
                    Assert.IsFalse(overlap, name + ": grab area over " + Game.UI.Driving.HudLayoutResult.ZoneName(i));
                }
                Debug.Log("[TEST] " + name + ": wheel " + wheel + " grab " + g + " margin " + m.ToString("F0") + " units");
            }
        }

        /// <summary>Folding / unfolding while driving: the same HUD object lays out again for the new screen.</summary>
        [UnityTest]
        public IEnumerator Hud_RelayoutsOnScreenChange()
        {
            var cover = k_Devices[0]; var inner = k_Devices[2];
            MakeCamera(cover);
            var hud = DrivingHud.Create(m_Cam, new DrivingHudContext());
            hud.OverrideScreen(new Vector2(cover.W, cover.H), cover.SafePx, cover.Dpi);
            yield return null;
            Rect throttleCover = hud.Layout.Throttle; Vector2 sizeCover = hud.SafeSizeUnits;
            hud.OverrideScreen(new Vector2(inner.W, inner.H), inner.SafePx, inner.Dpi);   // unfolded
            yield return null;
            Assert.AreNotEqual(sizeCover, hud.SafeSizeUnits);
            Assert.AreEqual(hud.SafeSizeUnits.x - HudLayout.Margin, hud.Layout.Throttle.xMax, 0.01f, "throttle follows the right edge");
            Assert.AreNotEqual(throttleCover.x, hud.Layout.Throttle.x);
            AssertZones(hud.Layout, hud.SafeSizeUnits, "after unfolding");
            hud.OverrideScreen(new Vector2(cover.W, cover.H), cover.SafePx, cover.Dpi);   // folded again
            yield return null;
            Assert.AreEqual(throttleCover, hud.Layout.Throttle);
        }

        /// <summary>D39: the developer buttons stay in the build, behind one button; collapsed they take no room.</summary>
        [UnityTest]
        public IEnumerator Hud_DeveloperPanel_CollapsedByDefault_OneButton()
        {
            MakeCamera(k_Devices[2]);
            var hud = DrivingHud.Create(m_Cam, new DrivingHudContext());
            yield return null;
            Assert.IsFalse(hud.DevPanelOpen);
            string[] dev = { "Camera", "SteerMode", "Menu", "Settings", "Telemetry", "Record", "Reset", "Lab", "Couple", "Legs" };
            var all = hud.GetComponentsInChildren<Button>(true);
            foreach (string n in dev)
            {
                var b = Array.Find(all, x => x.name == n);
                Assert.IsNotNull(b, "developer button missing: " + n);
                Assert.IsFalse(b.gameObject.activeInHierarchy, n + " visible while the panel is collapsed");
            }
            var toggle = Array.Find(all, x => x.name == "DevToggle");
            Assert.IsNotNull(toggle); Assert.IsTrue(toggle.gameObject.activeInHierarchy);
            toggle.onClick.Invoke();
            Assert.IsTrue(hud.DevPanelOpen);
            foreach (string n in dev) Assert.IsTrue(Array.Find(all, x => x.name == n).gameObject.activeInHierarchy, n + " hidden while the panel is open");
            Array.Find(all, x => x.name == "Lab").onClick.Invoke();
            Assert.IsTrue(Array.Find(all, x => x.name == "Spawn0").gameObject.activeInHierarchy, "lab page");
            Assert.IsFalse(Array.Find(all, x => x.name == "Camera").gameObject.activeInHierarchy, "lab page replaces the grid");
            toggle.onClick.Invoke();
            Assert.IsFalse(hud.DevPanelOpen);
            Assert.IsFalse(Array.Find(all, x => x.name == "Spawn0").gameObject.activeInHierarchy);
        }

        [UnityTest]
        public IEnumerator SettingsPanel_FitsSafeArea([ValueSource(nameof(Devices))] Device d)
        {
            MakeCamera(d);
            var p = ControlSettingsPanel.Create(m_Cam, ControlSettings.Defaults(), null, null);
            p.OverrideScreen(new Vector2(d.W, d.H), d.SafePx, d.Dpi);
            yield return null;
            Canvas.ForceUpdateCanvases();
            var safe = p.SafeAreaRect;
            var bounds = new Rect(Vector2.zero, safe.rect.size);
            Rect panel = RectIn(p.PanelRect, safe);
            Assert.IsTrue(Contains(bounds, panel, 0.6f), $"{d.Name}: settings panel {panel} outside the safe area {bounds.size}");
            Debug.Log($"[HUD-R10] settings {d.Name}: safe {bounds.size.x:F0}x{bounds.size.y:F0} units, panel {panel.width:F0}x{panel.height:F0}, twoColumns {p.TwoColumns}, scrolls {p.Scrolls}");
            int buttons = 0;
            foreach (var g in p.PanelRect.GetComponentsInChildren<Graphic>(false))
            {
                Rect gr = RectIn(g.rectTransform, safe);
                // Horizontally nothing may be cut (the owner's report); vertically the rows may scroll under the mask.
                Assert.IsTrue(gr.xMin >= panel.xMin - 1f && gr.xMax <= panel.xMax + 1f, $"{d.Name}: {g.transform.parent.name}/{g.name} {gr} cut by the panel {panel}");
                if (g.GetComponent<Button>() != null) buttons++;
                if (!p.Scrolls) Assert.IsTrue(Contains(panel, gr, 1f), $"{d.Name}: {g.transform.parent.name}/{g.name} {gr} outside the panel {panel}");
            }
            Assert.GreaterOrEqual(buttons, 28, "all setting buttons built");
            foreach (string fixedName in new[] { "Title", "Zamknij", "Przywróć domyślne" })
            {
                var t = p.PanelRect.Find(fixedName);
                Assert.IsNotNull(t, fixedName);
                Assert.IsTrue(Contains(panel, RectIn((RectTransform)t, safe), 1f), $"{d.Name}: {fixedName} cut");
            }
            if (d.W >= d.H) Assert.IsTrue(p.TwoColumns, d.Name + ": two columns on a landscape screen");
        }

        [UnityTest]
        public IEnumerator StartMenu_FitsSafeArea([ValueSource(nameof(Devices))] Device d)
        {
            MakeCamera(d);
            var starts = new List<(string, Action)>
            {
                ("DrivingLab — plac testowy", () => { }),
                ("Trasa G3-A — Kwadrat Park, brama, Bieżeństwa", () => { }),
                ("Trasa G3-B — Andersa, Rondo Putry", () => { }),
            };
            var menu = BootMenu.Create(m_Cam, StartMenuOptions.Load(), starts, null);
            menu.OverrideScreen(new Vector2(d.W, d.H), d.SafePx, d.Dpi);
            yield return null;
            Canvas.ForceUpdateCanvases();
            var safe = menu.SafeAreaRect;
            var bounds = new Rect(Vector2.zero, safe.rect.size);
            foreach (var g in safe.GetComponentsInChildren<Graphic>(false))
                Assert.IsTrue(Contains(bounds, RectIn(g.rectTransform, safe), 1f), $"{d.Name}: menu item {g.transform.parent.name}/{g.name} {RectIn(g.rectTransform, safe)} outside the safe area {bounds.size}");
        }

        // ------------------------------------------------------------------ captures (explicit)

        static string OutDir => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "artifacts", "hud-r10"));

        /// <summary>Renders <paramref name="cam"/> at the device resolution and saves it at most 960 px wide.</summary>
        static void Shot(Camera cam, Device d, string name)
        {
            var rt = new RenderTexture(d.W, d.H, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            var prev = cam.targetTexture;
            cam.targetTexture = rt;
            Canvas.ForceUpdateCanvases();
            cam.Render();
            cam.targetTexture = prev;
            float k = Mathf.Min(1f, 960f / Mathf.Max(d.W, d.H));
            int w = Mathf.RoundToInt(d.W * k), h = Mathf.RoundToInt(d.H * k);
            var small = RenderTexture.GetTemporary(w, h, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            Graphics.Blit(rt, small);
            var prevA = RenderTexture.active;
            RenderTexture.active = small;
            var tex = new Texture2D(w, h, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, w, h), 0, 0); tex.Apply();
            RenderTexture.active = prevA;
            RenderTexture.ReleaseTemporary(small);
            Directory.CreateDirectory(OutDir);
            File.WriteAllBytes(Path.Combine(OutDir, name + ".png"), tex.EncodeToPNG());
            UnityEngine.Object.Destroy(tex); rt.Release(); UnityEngine.Object.Destroy(rt);
            Debug.Log($"[HUD-R10] {name}.png {w}x{h}");
        }

        /// <summary>Explicit: HUD over the real cab view of the DrivingLab + settings + start menu for every device, to
        /// artifacts/hud-r10/*.png (at most 960 px). Needs a GPU. Run: -testFilter Game.Tests.HudLayoutTests.Capture_AllDevices</summary>
        [UnityTest, Explicit("visual capture, run on demand")]
        public IEnumerator Capture_AllDevices()
        {
            Physics.simulationMode = SimulationMode.Script;
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            var boot = UnityEngine.Object.FindAnyObjectByType<DrivingLabBootstrap>();
            var body = UnityEngine.Object.FindAnyObjectByType<VehicleBody>();
            var rig = UnityEngine.Object.FindAnyObjectByType<CameraRig>();
            boot.enabled = false;
            var old = UnityEngine.Object.FindAnyObjectByType<DrivingHud>();
            if (old != null) UnityEngine.Object.Destroy(old.gameObject);
            yield return null;
            Texture mirL = null, mirR = null;
            foreach (var mir in UnityEngine.Object.FindObjectsByType<RenderTextureMirror>(FindObjectsSortMode.None))
            {
                mir.RenderNow();
                if (!mir.main) continue;
                if (mir.phase == 0) mirL = mir.Texture; else mirR = mir.Texture;
            }
            bool mirrors = true, reverse = false;
            var ctx = new DrivingHudContext
            {
                Vehicle = body, Rig = rig,
                LeftMirrorTexture = () => mirrors ? mirL : null,
                RightMirrorTexture = () => mirrors ? mirR : null,
                ReverseCameraTexture = () => reverse ? mirL : null,
                ReverseCameraLabel = () => "KAMERA COFANIA (naczepa)",
                MirrorInsets = () => mirrors,
                StatusLine = () => "AUTOPILOT (pomiar)",
                CouplingStatus = () => "Naczepa odpięta (nogi opuszczone) · sworzeń 2.00 m za siodłem",
            };
            var cam = rig.cam;
            foreach (var d in k_Devices)
            {
                if (d.H > d.W * 1.5f) continue;   // portrait phone: not a supported orientation
                var hud = DrivingHud.Create(cam, ctx);
                hud.OverrideScreen(new Vector2(d.W, d.H), d.SafePx, d.Dpi);
                reverse = false; mirrors = true;
                yield return null; hud.RefreshNow();
                Shot(cam, d, d.Name + "-1-driving");
                hud.SetDevPanelOpen(true);
                yield return null; hud.RefreshNow();
                Shot(cam, d, d.Name + "-2-dev-panel");
                hud.SetTelemetryVisible(true); hud.SetDevDiagnostics(true); reverse = true;
                yield return null; hud.RefreshNow();
                Shot(cam, d, d.Name + "-3-dev-everything");
                UnityEngine.Object.Destroy(hud.gameObject);
                yield return null;

                var panel = ControlSettingsPanel.Create(cam, ControlSettings.Defaults(), null, null);
                panel.OverrideScreen(new Vector2(d.W, d.H), d.SafePx, d.Dpi);
                yield return null;
                Shot(cam, d, d.Name + "-4-settings");
                UnityEngine.Object.Destroy(panel.gameObject);
                yield return null;

                var starts = new List<(string, Action)>
                {
                    ("DrivingLab — plac testowy", () => { }),
                    ("Trasa G3-A — Kwadrat Park, brama, Bieżeństwa", () => { }),
                    ("Trasa G3-B — Andersa, Rondo Putry", () => { }),
                };
                var menu = BootMenu.Create(cam, StartMenuOptions.Load(), starts, null);
                menu.OverrideScreen(new Vector2(d.W, d.H), d.SafePx, d.Dpi);
                yield return null;
                Shot(cam, d, d.Name + "-5-menu");
                UnityEngine.Object.Destroy(menu.gameObject);
                yield return null;
            }
        }
    }
}
