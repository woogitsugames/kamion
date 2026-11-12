using System.Collections;
using System.IO;
using Game.Cameras;
using Game.Core.Navigation;
using Game.Gameplay;
using Game.UI.Driving;
using Game.UI.Layout;
using Game.UI.Navigation;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>
    /// GPS in the HUD (ADR 0150): the minimap zone never overlaps a HUD zone on phones (20:9, 21:9), the Fold's inner
    /// screen (~1:1, both orientations) and tablets; the minimap refresh and the guidance allocate nothing; the full map
    /// pauses the simulation and sets / plans / clears a route; captures for the visual loop (explicit).
    /// </summary>
    public class NavHudTests
    {
        const string Region = "bialystok-industrial-c";
        static readonly Vector2 k_Kombatantow = new Vector2(-1.7f, -897.8f);
        static readonly Vector2 k_AndersaSE = new Vector2(-172f, -298f);

        struct Dev { public string Name; public int W, H; public float Dpi, L, R, T, B; public Rect Safe => new Rect(L, B, W - L - R, H - T - B); }

        // DPI nominal (UNVERIFIED on the devices). fold-rec-1080x1200 = the owner's screen recording of the inner screen.
        static readonly Dev[] k_Devices =
        {
            new Dev { Name = "phone-2340x1080", W = 2340, H = 1080, Dpi = 385f, L = 94f },
            new Dev { Name = "phone-2400x1080", W = 2400, H = 1080, Dpi = 400f, L = 90f },
            new Dev { Name = "fold-rec-1080x1200", W = 1080, H = 1200, Dpi = 0f },
            new Dev { Name = "fold-inner-2176x1812", W = 2176, H = 1812, Dpi = 368f, T = 60f },
            new Dev { Name = "fold-inner-rotated-1968x2184", W = 1968, H = 2184, Dpi = 368f, T = 60f },
            new Dev { Name = "tablet-2560x1600", W = 2560, H = 1600, Dpi = 274f },
        };

        [Test]
        public void NavZone_NeverOverlapsHud_AllDevicesAllStates()
        {
            int shown = 0, total = 0;
            foreach (var d in k_Devices)
                foreach (float dpi in new[] { 0f, d.Dpi, 160f, 640f })
                    foreach (bool cutout in new[] { false, true })
                    {
                        Rect safe = cutout ? d.Safe : new Rect(0, 0, d.W, d.H);
                        Vector2 size = UiScale.SizeUnits(safe.width, safe.height, dpi);
                        for (int bits = 0; bits < 128; bits++)
                        {
                            var s = new HudLayoutInput
                            {
                                Width = size.x, Height = size.y, Gyro = (bits & 1) != 0, DevPanelOpen = (bits & 2) != 0, Telemetry = (bits & 4) != 0,
                                MirrorLeft = (bits & 8) != 0, MirrorRight = (bits & 16) != 0, ReverseView = (bits & 32) != 0, DevText = (bits & 64) != 0,
                            };
                            HudLayout.Solve(s, out var r);
                            total++;
                            if (!NavHudLayout.Solve(r, size.x, size.y, s.Telemetry, out Rect z)) continue;
                            shown++;
                            Assert.IsTrue(z.xMin >= -0.01f && z.yMin >= -0.01f && z.xMax <= size.x + 0.01f && z.yMax <= size.y + 0.01f, $"{d.Name}: {z} outside {size}");
                            for (int i = 0; i < HudLayoutResult.ZoneCount; i++)
                            {
                                if (!r.Zone(i, out Rect a)) continue;
                                bool overlap = a.xMin < z.xMax - 0.01f && z.xMin < a.xMax - 0.01f && a.yMin < z.yMax - 0.01f && z.yMin < a.yMax - 0.01f;
                                Assert.IsFalse(overlap, $"{d.Name} dpi {dpi} state {bits}: nav {z} overlaps {HudLayoutResult.ZoneName(i)} {a}");
                            }
                            // Also clear of the wheel's grab area (ADR 0135): a tap on the map must never steer.
                            Rect grab = HudLayout.WheelGrabRect(r, size.x, size.y, HudLayout.GrabMarginUnits(1f, dpi));
                            Assert.IsFalse(grab.Overlaps(z), $"{d.Name} dpi {dpi} state {bits}: nav {z} overlaps the wheel grab area {grab}");
                        }
                    }
            Debug.Log($"[NAV] nav zone shown in {shown}/{total} layouts");
            // Driving state (both mirror insets, no developer overlays) on the owner's devices: always shown.
            foreach (var d in k_Devices)
            {
                Vector2 size = UiScale.SizeUnits(d.Safe.width, d.Safe.height, d.Dpi);
                HudLayout.Solve(new HudLayoutInput { Width = size.x, Height = size.y, MirrorLeft = true, MirrorRight = true }, out var r);
                Assert.IsTrue(NavHudLayout.Solve(r, size.x, size.y, false, out Rect z), d.Name + ": minimap shown while driving");
                Debug.Log($"[NAV] {d.Name}: canvas {size.x:F0}x{size.y:F0} units, nav zone {z}");
            }
        }

        static NavigationService MakeService(out GameObject go)
        {
            go = new GameObject("NavTest");
            var nav = go.AddComponent<NavigationService>();
            nav.regionId = Region;
            nav.Init();
            Assert.IsTrue(nav.Ready, "routing graph + map data of " + Region);
            return nav;
        }

        [UnityTest]
        public IEnumerator MiniMap_RefreshAndGuidance_ZeroGc()
        {
            Physics.simulationMode = SimulationMode.Script;
            var camGo = new GameObject("Cam");
            var cam = camGo.AddComponent<Camera>();
            var hud = DrivingHud.Create(cam, new DrivingHudContext(), overlay: true);
            var nav = MakeService(out var navGo);
            nav.SetPoseForTest(k_Kombatantow, 270f, 0f);
            Assert.IsTrue(nav.SetPin(k_AndersaSE));
            Assert.AreEqual(PlanStatus.Ok, nav.PlanToPin());
            var mini = MiniMapView.Create(hud, nav);
            yield return null;
            hud.RefreshNow();
            mini.Relayout(true);
            Assert.IsTrue(mini.Visible, "minimap shown");
            var path = nav.Path;
            for (int i = 0; i < 30; i++) { nav.StepForTest(path.Points[i % path.Count], 270f, 8f, 0.033f); mini.Draw(0.033f); }
            mini.ResetStats();
            long before = System.GC.GetAllocatedBytesForCurrentThread();
            for (int i = 0; i < 300; i++)
            {
                int k = (i / 4) % (path.Count - 1);
                Vector2 dir = path.Points[k + 1] - path.Points[k];
                nav.StepForTest(path.Points[k], Mathf.Atan2(dir.x, dir.y) * Mathf.Rad2Deg, 10f, 0.033f);
                mini.Draw(0.033f);
            }
            long bytes = System.GC.GetAllocatedBytesForCurrentThread() - before;
            Debug.Log($"[NAV] minimap refresh: avg {mini.AverageCpuMs:F3} ms CPU over {mini.RefreshCount} refreshes, last {mini.LastCpuMs:F3} ms; " +
                      $"canvas {mini.Canvas.DesignWidth}x{mini.Canvas.DesignHeight} design px, {mini.Canvas.VertexCount} verts, overflow {mini.Canvas.Overflow}");
            Assert.AreEqual(0, bytes, "minimap refresh + guidance allocate nothing");
            Assert.AreEqual(0, mini.Canvas.Overflow);
            Object.Destroy(mini.gameObject); Object.Destroy(hud.gameObject); Object.Destroy(navGo); Object.Destroy(camGo);
            yield return null;
        }

        [UnityTest]
        public IEnumerator FullMap_PausesAndSetsRoute()
        {
            var nav = MakeService(out var navGo);
            nav.SetPoseForTest(k_Kombatantow, 270f, 0f);
            var full = FullMapView.Create(nav);
            float ts = Time.timeScale;
            full.Open();
            yield return null;
            Assert.IsTrue(FullMapView.IsOpen);
            Assert.AreEqual(0f, Time.timeScale, "simulation paused while the map is open");
            Assert.IsTrue(AudioListener.pause);
            // Tap on Andersa (design px of the current view), plan, clear.
            Vector2 design = MapXf.Make(full.Centre, 0f, full.Zoom, full.MapCanvas.DesignWidth * 0.5f, full.MapCanvas.DesignHeight * 0.5f).ToScreen(k_AndersaSE);
            full.TapAt(design);
            Assert.IsTrue(nav.HasPin);
            Assert.AreEqual("Generała Władysława Andersa", nav.NameOf(nav.PinName));
            full.PlanRoute();
            Assert.AreEqual(PlanStatus.Ok, nav.LastStatus);
            Assert.IsTrue(nav.Path.HasRoute);
            yield return null;
            full.ClearRoute();
            Assert.IsFalse(nav.Path.HasRoute);
            Assert.IsFalse(nav.HasPin);
            Assert.IsTrue(FullMapView.HandleBack(), "back closes the map");
            Assert.IsFalse(FullMapView.IsOpen);
            Assert.AreEqual(ts, Time.timeScale);
            Assert.IsFalse(AudioListener.pause);
            Object.Destroy(full.gameObject); Object.Destroy(navGo);
            yield return null;
        }

        // ------------------------------------------------------------------ captures

        static string OutDir => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "artifacts", "gps-map"));

        static void Shot(Camera cam, int W, int H, string name, int maxSide = 960)
        {
            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            var prev = cam.targetTexture;
            cam.targetTexture = rt;
            Canvas.ForceUpdateCanvases();
            cam.Render();
            cam.targetTexture = prev;
            Save(rt, name, maxSide);
            rt.Release(); Object.Destroy(rt);
        }

        static void Save(RenderTexture rt, string name, int maxSide)
        {
            float k = Mathf.Min(1f, (float)maxSide / Mathf.Max(rt.width, rt.height));
            int w = Mathf.RoundToInt(rt.width * k), h = Mathf.RoundToInt(rt.height * k);
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
            Object.Destroy(tex);
            Debug.Log($"[NAV] capture {name}.png {w}x{h}");
        }

        /// <summary>Explicit: HUD with the GPS widget over the DrivingLab cab view, the full map (pin, route) and the cab
        /// navigation texture for the Fold (recording size and native) and a 20:9 phone -> artifacts/gps-map/*.png.
        /// The 3D view is the lab (no world scene in a test); the map is the Białystok region at a pose on the route.
        /// Run: -testFilter Game.Tests.NavHudTests.Capture_Devices</summary>
        [UnityTest, Explicit("visual capture, run on demand")]
        public IEnumerator Capture_Devices()
        {
            Physics.simulationMode = SimulationMode.Script;
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            var boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            var body = Object.FindAnyObjectByType<VehicleBody>();
            var rig = Object.FindAnyObjectByType<CameraRig>();
            boot.enabled = false;
            var old = Object.FindAnyObjectByType<DrivingHud>();
            if (old != null) Object.Destroy(old.gameObject);
            yield return null;
            Texture mirL = null, mirR = null;
            foreach (var mir in Object.FindObjectsByType<RenderTextureMirror>(FindObjectsSortMode.None))
            {
                mir.RenderNow();
                if (!mir.main) continue;
                if (mir.phase == 0) mirL = mir.Texture; else mirR = mir.Texture;
            }
            var ctx = new DrivingHudContext { Vehicle = body, Rig = rig, LeftMirrorTexture = () => mirL, RightMirrorTexture = () => mirR, MirrorInsets = () => true };
            var cam = rig.cam;
            var nav = MakeService(out var navGo);
            nav.SetPoseForTest(k_Kombatantow, 270f, 0f);
            nav.SetPin(k_AndersaSE);
            Assert.AreEqual(PlanStatus.Ok, nav.PlanToPin());
            var path = nav.Path;
            // Pose ~120 m before the right turn onto al. Tysiąclecia, driving at 40 km/h.
            int idx = 0;
            for (int i = 0; i < path.Count; i++) if (path.S[i] <= 190f) idx = i;
            Vector2 at = path.Points[idx], dir = (path.Points[Mathf.Min(path.Count - 1, idx + 1)] - at).normalized;
            float heading = Mathf.Atan2(dir.x, dir.y) * Mathf.Rad2Deg;
            // Cab navigation screen (1280 x 768 design) with the live GPS route.
            {
                for (int i = 0; i < 40; i++) nav.StepForTest(at, heading, 11f, 0.05f);
                var layout = new Game.UI.CabDisplays.NavLayout { Map = nav.Map, Live = nav };
                var dc = new Game.UI.CabDisplays.DisplayCanvas("NavCapture", Game.UI.CabDisplays.NavLayout.Width, Game.UI.CabDisplays.NavLayout.Height, 1f, 6000, Game.UI.UiFonts.Default, 1f);
                Game.UI.CabDisplays.NavLayout.RequestGlyphs(dc);
                var st = new Game.UI.CabDisplays.CabDisplayState { HasPosition = true, PosE = at.x, PosN = at.y, HeadingDeg = heading, SpeedKmh = 40f, ClockMinutes = 14 * 60 + 5 };
                layout.Draw(dc, st, 0f);
                Save(dc.Texture, "cab-nav-live-route", 1280);
                layout.ReleaseStatic(); dc.Dispose();
            }
            foreach (var d in new[] { k_Devices[2], k_Devices[0], k_Devices[3] })
            {
                var hud = DrivingHud.Create(cam, ctx);
                hud.OverrideScreen(new Vector2(d.W, d.H), d.Safe, d.Dpi);
                var mini = MiniMapView.Create(hud, nav);
                for (int i = 0; i < 40; i++) { nav.StepForTest(at, heading, 11f, 0.05f); }
                yield return null;
                hud.RefreshNow(); mini.Relayout(true);
                for (int i = 0; i < 40; i++) mini.Draw(0.05f);
                Shot(cam, d.W, d.H, d.Name + "-1-hud");
                Save(mini.Canvas.Texture, d.Name + "-1b-minimap-native", 2048);

                // Arrival / roundabout states for the same widget are covered on the full map; here the off-route banner.
                var full = FullMapView.Create(nav, cam);
                full.Open();
                full.OverrideScreen(new Vector2(d.W, d.H), d.Safe, d.Dpi);
                yield return null;
                full.DrawNow();
                Shot(cam, d.W, d.H, d.Name + "-2-map-route");
                full.ClearRoute();
                full.TapAt(MapXf.Make(full.Centre, 0f, full.Zoom, full.MapCanvas.DesignWidth * 0.5f, full.MapCanvas.DesignHeight * 0.5f).ToScreen(k_AndersaSE));
                yield return null;
                full.DrawNow();
                Shot(cam, d.W, d.H, d.Name + "-3-map-pin");
                full.PlanRoute();
                full.Close();
                Object.Destroy(full.gameObject);
                Object.Destroy(mini.gameObject);
                Object.Destroy(hud.gameObject);
                yield return null;
            }
            Object.Destroy(navGo);
        }
    }
}
