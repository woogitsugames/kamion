using System;
using Game.UI.CabDisplays;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools.Constraints;
using Is = UnityEngine.TestTools.Constraints.Is;
using Object = UnityEngine.Object;

namespace Game.Tests
{
    /// <summary>
    /// Live cab screens (review r4 C-N1): number formatting, the sun clock, the navigation data and manoeuvre logic, and
    /// the screens on a truck - content follows the solver (not a static picture), night mode with the dipped beam, and
    /// zero GC per refresh. (In the PlayMode assembly because the EditMode assembly does not reference Game.UI.)
    /// </summary>
    public class CabScreensTests
    {
        const float Dt = 0.01f;
        static readonly Vector3 O = new Vector3(0f, -800f, 0f);
        SimulationMode m_PrevMode;
        GameObject m_World;
        VehicleBody m_Body;

        [SetUp]
        public void SetUp()
        {
            m_PrevMode = Physics.simulationMode;
            Physics.simulationMode = SimulationMode.Script;
            m_World = new GameObject("CabScreensTestWorld");
        }

        [TearDown]
        public void TearDown()
        {
            if (m_Body != null) Object.DestroyImmediate(m_Body.gameObject);
            Object.DestroyImmediate(m_World);
            Physics.simulationMode = m_PrevMode;
        }

        // ------------------------------------------------------------------ pure logic

        [Test]
        public void TextBuffer_PolishNumberStyle()
        {
            var b = new TextBuffer();
            Assert.AreEqual("184 327", b.Clear().Append(184327, 1, true).ToString());
            Assert.AreEqual("1 000", b.Clear().Append(1000, 1, true).ToString());
            Assert.AreEqual("999", b.Clear().Append(999, 1, true).ToString());
            Assert.AreEqual("0", b.Clear().Append(0).ToString());
            Assert.AreEqual("-12", b.Clear().Append(-12).ToString());
            Assert.AreEqual("10,4", b.Clear().AppendFixed(10.36, 1).ToString());
            Assert.AreEqual("412,6", b.Clear().AppendFixed(412.55, 1).ToString());
            Assert.AreEqual("1 412,0", b.Clear().AppendFixed(1412.0, 1, true).ToString());
            Assert.AreEqual("0,0", b.Clear().AppendFixed(-0.01, 1).ToString());
            Assert.AreEqual("07:05", b.Clear().AppendClock(7 * 60 + 5).ToString());
            Assert.AreEqual("23:59", b.Clear().AppendClock(-1).ToString());
            Assert.AreEqual("00h47", b.Clear().AppendDurationHm(47).ToString());
            Assert.AreEqual("09h00", b.Clear().AppendDurationHm(540).ToString());
        }

        [Test]
        public void SolarClock_MatchesLightingPresets()
        {
            // LightingPreset values (Rendering/Runtime/Sky/LightingPreset.cs): overcast 30°/200°, low sun 9°/60° ("June
            // morning ~05:30"), dusk 1°/300° (summer evening). Expected from the spherical astronomy, EoT ignored.
            int overcast = SolarClock.LocalMinutes(30, 200), low = SolarClock.LocalMinutes(9, 60), dusk = SolarClock.LocalMinutes(1, 300);
            Debug.Log($"[TEST] sun clock: overcast {overcast / 60}:{overcast % 60:D2}, low sun {low / 60}:{low % 60:D2}, dusk {dusk / 60}:{dusk % 60:D2}");
            Assert.That(overcast, Is.InRange(12 * 60, 13 * 60 + 30), "overcast 30° SSW: early afternoon");
            Assert.That(low, Is.InRange(4 * 60 + 30, 6 * 60), "low sun 9° ENE: summer morning");
            Assert.That(dusk, Is.InRange(19 * 60 + 30, 21 * 60), "dusk 1° WNW: summer evening");
            // Mirror symmetry about the meridian: a winter sun at 10° SSE and SSW is symmetric about solar noon (CET).
            int am = SolarClock.LocalMinutes(10, 150), pm = SolarClock.LocalMinutes(10, 210);
            int noon = (int)Math.Round((12.0 - SolarClock.LongitudeDeg / 15.0 + 1.0) * 60.0);
            Assert.AreEqual(noon, (am + pm) / 2, 1);
            Assert.Less(am, noon); Assert.Greater(pm, noon);
        }

        [Test]
        public void NavMap_RegionDataLoads()
        {
            var m = NavMapData.Load("bialystok-industrial-c");
            Assert.NotNull(m, "Resources/CabDisplay/Nav/bialystok-industrial-c.bytes (tools/ui/build_nav_map.py)");
            Assert.Greater(m.RoadCount, 500);
            Assert.Greater(m.BuildingCount, 500);
            Assert.AreEqual(1202, m.Route.Length);
            Assert.AreEqual(2402.78f, m.RouteLength, 3f, "route_start.json length_m");
            Assert.That(Array.IndexOf(m.Names, "Generała Władysława Andersa"), Is.GreaterThan(0));
            int i = m.NearestRouteIndex(m.Route[600] + new Vector2(1.5f, 0f), -1, out float d);
            Assert.AreEqual(600, i, 1);
            Assert.Less(d, 2f);
            Assert.AreEqual("al. Tysiąclecia Państwa Polskiego", NavLayout.Abbreviate("Aleja Tysiąclecia Państwa Polskiego"));
        }

        [Test]
        public void NavManeuver_TurnDirection()
        {
            // L-shaped route: north 100 m, then east (right turn) 100 m; 2 m stations like route_start.json.
            var m = new NavMapData();
            int n = 101;
            m.Route = new Vector2[n]; m.RouteS = new float[n]; m.RouteName = new ushort[n]; m.RouteLimit = new ushort[n];
            for (int k = 0; k < n; k++)
            {
                m.Route[k] = k <= 50 ? new Vector2(0f, 2f * k) : new Vector2(2f * (k - 50), 100f);
                m.RouteS[k] = 2f * k;
            }
            int t = NavLayout.FindTurn(m, 0, out float turn);
            Assert.AreEqual(50, t, 2, "turn at the corner");
            Assert.Greater(turn, 60f, "right turn is positive");
            for (int k = 51; k < n; k++) m.Route[k] = new Vector2(-2f * (k - 50), 100f);
            NavLayout.FindTurn(m, 0, out turn);
            Assert.Less(turn, -60f, "left turn is negative");
            var b = new TextBuffer();
            NavLayout.AppendDistance(b, 432f); Assert.AreEqual("430 m", b.ToString());
            NavLayout.AppendDistance(b.Clear(), 1260f); Assert.AreEqual("1,3 km", b.ToString());
            NavLayout.AppendDistance(b.Clear(), 42f); Assert.AreEqual("40 m", b.ToString());
        }

        [Test]
        public void EcoBand_IsTorquePlateau()
        {
            var def = VehicleDataAsset.LoadDefault().CreateModel().Engine.Def;
            CabScreens.EcoBandOf(def, out float lo, out float hi);
            Debug.Log($"[TEST] green band {lo}-{hi} 1/min");
            Assert.That(lo, Is.InRange(900f, 1050f));
            Assert.That(hi, Is.InRange(1250f, 1450f));
        }

        // ------------------------------------------------------------------ screens on a truck

        CabScreens SpawnTruckWithScreens(bool moving)
        {
            var ground = GameObject.CreatePrimitive(PrimitiveType.Cube);
            ground.transform.SetParent(m_World.transform, false);
            ground.transform.SetPositionAndRotation(O + new Vector3(0f, -0.5f, 0f), Quaternion.identity);
            ground.transform.localScale = new Vector3(2000f, 1f, 2000f);
            ground.AddComponent<GroundSurface>().kind = SurfaceKind.DryAsphalt;
            Physics.SyncTransforms();
            m_Body = GrayboxTractorBuilder.Build(VehicleDataAsset.LoadDefault(), null, null);
            m_Body.ResetPose(O, Quaternion.identity);
            m_Body.gameObject.AddComponent<TruckLights>().body = m_Body;
            // Stand-ins for the art truck's display quads (the screens bind by renderer name).
            foreach (var name in new[] { "DISPLAY_Cluster_LOD0", "DISPLAY_Infotainment_LOD0", "DISPLAY_Tachograph_LOD0" })
            {
                var q = GameObject.CreatePrimitive(PrimitiveType.Quad);
                Object.DestroyImmediate(q.GetComponent<Collider>());
                q.name = name;
                q.transform.SetParent(m_Body.transform, false);
                q.transform.localPosition = new Vector3(0f, 2f, 1f);
            }
            if (moving)
            {
                m_Body.SetMoving(50f / 3.6f, 9);
                m_Body.Input = new DriverInput { Selector = GearSelector.Drive, Throttle = 0.3, RetarderLever = 0 };
            }
            else
            {
                m_Body.Model.InitParking(true);
                m_Body.Input = new DriverInput { Selector = GearSelector.Drive, ParkingBrake = true };
            }
            var s = CabScreens.Install(m_Body, null, "bialystok-industrial-c");
            Assert.NotNull(s, "screens install on a body with DISPLAY_Cluster_* renderers");
            return s;
        }

        void Step(int n)
        {
            for (int i = 0; i < n; i++) { m_Body.Tick(Dt); Physics.Simulate(Dt); }
        }

        static Color32[] Read(RenderTexture rt)
        {
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var t = new Texture2D(rt.width, rt.height, TextureFormat.RGBA32, false);
            t.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0, false);
            t.Apply();
            RenderTexture.active = prev;
            var px = t.GetPixels32();
            Object.DestroyImmediate(t);
            return px;
        }

        /// <summary>Mean sRGB luminance of a design-pixel box (y down) of a screen texture.</summary>
        static float Luma(Color32[] px, RenderTexture rt, float designW, float designH, float x0, float y0, float x1, float y1)
        {
            float sx = rt.width / designW, sy = rt.height / designH, sum = 0f;
            int n = 0;
            for (int y = Mathf.FloorToInt(y0 * sy); y < Mathf.CeilToInt(y1 * sy); y++)
            for (int x = Mathf.FloorToInt(x0 * sx); x < Mathf.CeilToInt(x1 * sx); x++)
            {
                var c = px[(rt.height - 1 - y) * rt.width + x];   // texture rows bottom-up
                sum += 0.2126f * c.r + 0.7152f * c.g + 0.0722f * c.b; n++;
            }
            return n > 0 ? sum / n / 255f : 0f;
        }

        [Test]
        public void Screens_FollowTheSolver_NotAStaticPicture()
        {
            var screens = SpawnTruckWithScreens(true);
            Step(50);
            screens.RenderNow();
            var st = screens.State;
            Assert.That(st.SpeedKmh, Is.InRange(35f, 65f), "speed from the solver");
            Assert.Greater(Mathf.Max(st.Gear, st.ShiftTarget), 0, $"a forward gear engaged or being shifted to (gear {st.Gear}, target {st.ShiftTarget})");
            Assert.Greater(st.EngineRpm, 600f);
            Assert.Greater(st.AirCircuit1Bar, 8f);
            Assert.IsFalse(st.ParkingBrake);
            Assert.AreEqual(0, screens.Cluster.Overflow, "cluster buffers large enough");
            var rt = screens.Cluster.Texture;
            var moving = Read(rt);
            // Speed digits region (centre, 1560 x 600 layout) is lit; telltale "P" slot dark while driving.
            float speedMoving = Luma(moving, rt, 1560, 600, 600, 40, 960, 240);
            Assert.Greater(speedMoving, 0.06f, "speed digits drawn");

            // Stop and apply the parking brake: digits change, the red P telltale appears.
            m_Body.Input = new DriverInput { Selector = GearSelector.Drive, Brake = 1.0, ParkingBrake = true };
            Step(1500);
            screens.RenderNow();
            Assert.Less(Mathf.Abs(screens.State.SpeedKmh), 1f);
            Assert.IsTrue(screens.State.ParkingBrake);
            var parked = Read(rt);
            int diff = 0;
            for (int i = 0; i < parked.Length; i++)
                if (Mathf.Abs(parked[i].r - moving[i].r) + Mathf.Abs(parked[i].g - moving[i].g) > 30) diff++;
            Assert.Greater(diff, parked.Length / 200, "the cluster image changes with the vehicle state");
            float parkSlotX = (1560f - 72f * 12f - 44f) * 0.5f;
            Color32 red = Avg(parked, rt, 1560, 600, parkSlotX, 12, parkSlotX + 44, 56);
            Assert.Greater(red.r, red.g + 20, "parking brake telltale is red");
            Debug.Log($"[TEST] cluster RT {rt.width}x{rt.height}, refresh {screens.LastCpuMs:F3} ms CPU, verts cluster {screens.Cluster.VertexCount} nav {screens.Nav.VertexCount}");
        }

        static Color32 Avg(Color32[] px, RenderTexture rt, float designW, float designH, float x0, float y0, float x1, float y1)
        {
            float sx = rt.width / designW, sy = rt.height / designH;
            long r = 0, g = 0, b = 0; int n = 0;
            for (int y = Mathf.FloorToInt(y0 * sy); y < Mathf.CeilToInt(y1 * sy); y++)
            for (int x = Mathf.FloorToInt(x0 * sx); x < Mathf.CeilToInt(x1 * sx); x++)
            {
                var c = px[(rt.height - 1 - y) * rt.width + x];
                r += c.r; g += c.g; b += c.b; n++;
            }
            return n == 0 ? new Color32() : new Color32((byte)(r / n), (byte)(g / n), (byte)(b / n), 255);
        }

        [Test]
        public void Screens_NightModeWithTheLightSensor()
        {
            var screens = SpawnTruckWithScreens(false);
            screens.lights = m_Body.GetComponent<TruckLights>();
            var prevSun = RenderSettings.sun;
            var sunGo = new GameObject("TestSun");
            sunGo.transform.SetParent(m_World.transform, false);
            var sun = sunGo.AddComponent<Light>();
            sun.type = LightType.Directional;
            RenderSettings.sun = sun;
            try
            {
                var nav = screens.Nav.Texture;
                // Overcast noon (30°, the overcast preset disables the sun light: the direction still counts).
                sunGo.transform.rotation = Quaternion.Euler(30f, 200f, 0f);
                sun.enabled = false;
                screens.RenderNow();
                Assert.IsFalse(screens.State.Night, "overcast day: day screens");
                float dayBg = Luma(Read(nav), nav, 1280, 768, 900, 300, 1000, 400);
                // Dusk (1° above the horizon): below the dipped-beam threshold (6°).
                sunGo.transform.rotation = Quaternion.Euler(1f, 300f, 0f);
                sun.enabled = true;
                screens.RenderNow();
                Assert.IsTrue(screens.State.Night, "dusk: night screens");
                Assert.IsTrue(screens.State.LowBeam, "dusk: dipped beam telltale");
                float nightBg = Luma(Read(nav), nav, 1280, 768, 900, 300, 1000, 400);
                Debug.Log($"[TEST] nav background day {dayBg:F2} night {nightBg:F2}, clock dusk {screens.State.ClockMinutes / 60}:{screens.State.ClockMinutes % 60:D2}");
                Assert.Greater(dayBg, 0.5f, "day map is light");
                Assert.Less(nightBg, 0.2f, "night map is dark");
            }
            finally { RenderSettings.sun = prevSun; }
        }

        [Test]
        public void Screens_Refresh_ZeroGcAllocation()
        {
            var screens = SpawnTruckWithScreens(true);
            Step(20);
            // The truck stands far from the region data here; put the map position on the route so the map path runs too.
            for (int i = 0; i < 5; i++) screens.Refresh(true, true, true, 0.033f, 0.1f);   // warm up (glyph atlas, JIT)

            object sink = null;
            Assert.That(() => { sink = new byte[64]; }, Is.AllocatingGCMemory(), "control: the constraint must see a 64 B allocation");
            GC.KeepAlive(sink);

            TestDelegate refresh = () =>
            {
                for (int i = 0; i < 60; i++)
                {
                    m_Body.Tick(Dt);
                    screens.Refresh(true, i % 3 == 0, i % 30 == 0, 0.033f, 0.1f);
                }
            };
            Assert.That(refresh, Is.Not.AllocatingGCMemory(), "60 cluster refreshes (+20 nav, 2 DIN) must not allocate");
            Debug.Log($"[TEST] GC: cab screen refresh allocated nothing; mean refresh {screens.AverageCpuMs:F3} ms CPU (editor), last {screens.LastCpuMs:F3} ms");
            Debug.Log($"[TEST] cost (editor CPU, sample + build + submit + mips): cluster {TimeRefresh(screens, true, false, false):F3} ms, DIN {TimeRefresh(screens, false, false, true):F3} ms");
        }

        static double TimeRefresh(CabScreens screens, bool c, bool n, bool d)
        {
            const int N = 200;
            var sw = System.Diagnostics.Stopwatch.StartNew();
            for (int i = 0; i < N; i++) screens.Refresh(c, n, d, 0.033f, 0.1f);
            GL.Flush();
            return sw.Elapsed.TotalMilliseconds / N;
        }

        [Test]
        public void Screens_NavMap_OnRoute_ZeroGcAndManeuver()
        {
            var screens = SpawnTruckWithScreens(false);
            var map = screens.NavLayout.Map;
            Assert.NotNull(map);
            // Region frame stand-in: a transform that maps the truck onto route station 300 (region-local metres).
            var frame = new GameObject("RegionFrame").transform;
            frame.SetParent(m_World.transform, false);
            Vector2 p = map.Route[300], dir = (map.Route[302] - map.Route[298]).normalized;
            // Truck at O facing +Z: frame so that InverseTransformPoint(O) = (p.x, ?, p.y) and forward follows the route.
            float yaw = Mathf.Atan2(dir.x, dir.y) * Mathf.Rad2Deg;
            frame.rotation = Quaternion.Euler(0f, -yaw, 0f);
            frame.position = O - frame.rotation * new Vector3(p.x, 0f, p.y);
            screens.regionFrame = frame;
            screens.RenderNow();
            Assert.AreEqual(300, screens.NavLayout.RouteIndex, 2, "truck located on the route");
            Assert.Less(screens.NavLayout.RouteDistance, 1f);
            Assert.AreEqual(0f, Mathf.DeltaAngle(screens.State.HeadingDeg, yaw), 1f, "heading in the region frame");
            Assert.IsFalse(float.IsNaN(screens.NavLayout.NextManeuverM), "a next manoeuvre or the destination is shown");
            Assert.AreEqual(0, screens.Nav.Overflow, "navigation buffers large enough");
            Debug.Log($"[TEST] nav on route: station {screens.NavLayout.RouteIndex}, next manoeuvre {screens.NavLayout.NextManeuverM:F0} m turn {screens.NavLayout.NextTurnDeg:F0}°, verts {screens.Nav.VertexCount}/{screens.Nav.MaxVertices}");

            for (int i = 0; i < 3; i++) screens.Refresh(false, true, false, 0f, 0.1f);
            TestDelegate nav = () => { for (int i = 0; i < 20; i++) screens.Refresh(false, true, false, 0f, 0.1f); };
            Assert.That(nav, Is.Not.AllocatingGCMemory(), "map refreshes on the route must not allocate");
            Debug.Log($"[TEST] cost (editor CPU): navigation on route {TimeRefresh(screens, false, true, false):F3} ms");
        }

        /// <summary>
        /// Review frames of the three screens at their native render-texture size (driving at ~50 km/h on the start route,
        /// retarder stage 2, brake cruise 60 km/h; day and night): artifacts/visual-qa/cab-screens/*.png.
        /// </summary>
        [Test]
        public void Screens_DumpReviewFrames()
        {
            var screens = SpawnTruckWithScreens(true);
            screens.resolutionScale = 1f;   // review at the High-tier size whatever the test runner's quality level
            screens.Init();
            var map = screens.NavLayout.Map;
            var frame = new GameObject("RegionFrame").transform;
            frame.SetParent(m_World.transform, false);
            int station = 560;
            Vector2 p = map.Route[station], dir = (map.Route[station + 2] - map.Route[station - 2]).normalized;
            float yaw = Mathf.Atan2(dir.x, dir.y) * Mathf.Rad2Deg;
            frame.rotation = Quaternion.Euler(0f, -yaw, 0f);
            frame.position = O - frame.rotation * new Vector3(p.x, 0f, p.y);
            screens.regionFrame = frame;
            m_Body.Input = new DriverInput { Selector = GearSelector.Drive, Throttle = 0.25, RetarderLever = 0, BrakeCruiseKmh = 60 };
            Step(60);
            var inp = m_Body.Input; inp.RetarderLever = 3; m_Body.Input = inp;
            Step(30);
            screens.Source.ClockOverride = () => 14 * 60 + 32;
            screens.Source.TripKm = 412.6; screens.Source.TripFuelLitres = 412.6 * 0.284;
            string dir0 = System.IO.Path.GetFullPath(System.IO.Path.Combine(Application.dataPath, "..", "..", "artifacts", "visual-qa", "cab-screens"));
            System.IO.Directory.CreateDirectory(dir0);
            var lights = m_Body.GetComponent<TruckLights>();
            var prevSun = RenderSettings.sun;
            RenderSettings.sun = null;   // no sun: night mode follows the (forced) dipped beam
            foreach (bool night in new[] { false, true })
            {
                lights.forceLowBeam = night;
                screens.RenderNow();
                Save(screens.Cluster.Texture, System.IO.Path.Combine(dir0, (night ? "night" : "day") + "-cluster.png"));
                Save(screens.Nav.Texture, System.IO.Path.Combine(dir0, (night ? "night" : "day") + "-nav.png"));
                Save(screens.Din.Texture, System.IO.Path.Combine(dir0, (night ? "night" : "day") + "-din.png"));
            }
            RenderSettings.sun = prevSun;
            Debug.Log($"[TEST] review frames in {dir0}: speed {screens.State.SpeedKmh:F0} km/h gear {screens.State.Gear} rpm {screens.State.EngineRpm:F0} lever {screens.State.RetarderLever} station {screens.NavLayout.RouteIndex} next {screens.NavLayout.NextManeuverM:F0} m {screens.NavLayout.NextTurnDeg:F0}°");
        }

        static void Save(RenderTexture rt, string path)
        {
            var px = Read(rt);
            var t = new Texture2D(rt.width, rt.height, TextureFormat.RGBA32, false);
            t.SetPixels32(px);
            t.Apply();
            System.IO.File.WriteAllBytes(path, t.EncodeToPNG());
            Object.DestroyImmediate(t);
        }
    }
}
