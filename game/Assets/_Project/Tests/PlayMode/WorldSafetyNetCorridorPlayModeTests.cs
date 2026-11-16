using System.Collections;
using System.Globalization;
using Game.Gameplay;
using Game.Vehicle.Runtime;
using Game.World;
using Game.World.Streaming;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0273 §10 pkt 5 (D36, s23): with streaming on, the world safety net warns ("Koniec mapy") and stops the
    /// combination on the OUTER edge of the loaded corridor, and stays silent across a seam with a Ready neighbour.
    /// Start scene World_dk65-03 (tile 766731..768779 x 597247..599295, EPSG:2180; graph neighbours: dk65-02 east,
    /// dk65-04 north, dk65-01 south-east corner only). The south edge of dk65-03 is an outer edge that lies INSIDE the
    /// start rectangle widened by #157 (dk65-01 reaches further south), i.e. the case the widened rectangle missed.
    /// The vehicle is moved by script (physics simulation off, model speed set) so terrain and obstacles off the road
    /// cannot stop it: the test is about the safety net's edge, not about driving.
    /// Needs World_dk65-03 and World_dk65-04_Tile in the build (scripts/import-region.ps1 for both).
    /// </summary>
    public class WorldSafetyNetCorridorPlayModeTests
    {
        const string StartScene = "World_dk65-03";
        const double SeamY = 599295.0;
        const float HalfTile = 1024f;
        const float SlideSpeedMs = 20f;

        DrivingLabBootstrap m_Boot;
        VehicleBody m_Body;
        WorldStreamer m_Streamer;
        WorldRegionRoot m_Root;
        int m_Mask;

        [SetUp] public void EnableStreaming() => WorldStreamer.EnabledOverride = true;

        [TearDown]
        public void ResetStreaming()
        {
            WorldStreamer.EnabledOverride = null;
            Physics.simulationMode = SimulationMode.FixedUpdate;
        }

        IEnumerator Load()
        {
            string tileScene = RegionScenes.TileSceneNameFor("dk65-04");
            if (!Application.CanStreamedLevelBeLoaded(StartScene) || !Application.CanStreamedLevelBeLoaded(tileScene))
                Assert.Ignore($"{StartScene} / {tileScene} not in the build - run scripts/import-region.ps1 -Region dk65-03 and -Region dk65-04");
            Physics.simulationMode = SimulationMode.FixedUpdate;
            SceneManager.LoadScene(StartScene, LoadSceneMode.Single);
            yield return null;
            yield return null;
            m_Boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            m_Body = Object.FindAnyObjectByType<VehicleBody>();
            m_Root = Object.FindAnyObjectByType<WorldRegionRoot>();   // only the start scene is loaded yet
            m_Streamer = WorldStreamer.Active;
            Assert.IsNotNull(m_Boot); Assert.IsNotNull(m_Body); Assert.IsNotNull(m_Root);
            Assert.IsNotNull(m_Streamer, "streaming on: the hook installs the streamer");
            Assert.IsNotNull(m_Boot.SafetyNet, "world scenes get the safety net");
            int vl = UnityGroundQuery.ResolveVehicleLayer();
            m_Mask = Physics.DefaultRaycastLayers;
            if (vl >= 0) m_Mask &= ~(1 << vl);
            // Safe poses on the start road first (the reset needs one), with the solver running. The dk65-03 start route runs
            // E -> N within ~85 m of the east seam with dk65-02, which is not in the test build: with the outer-edge rule that
            // seam is an outer edge, so no pose would be "well inside" (safeEdgeDistance 120 m). The warm-up lowers the
            // threshold only to collect poses; the tests below run with the shipped value (int-ui-s23).
            var netWarm = m_Boot.SafetyNet;
            float safeEdge = netWarm.safeEdgeDistance;
            netWarm.safeEdgeDistance = 5f;
            m_Boot.SetRouteSpawn(12f);
            float t0 = Time.time;
            while (netWarm.SafePoses.Count < 3 && Time.time - t0 < 15f) yield return new WaitForFixedUpdate();
            netWarm.safeEdgeDistance = safeEdge;
            Assert.GreaterOrEqual(netWarm.SafePoses.Count, 3, "safe poses recorded on the route spawn");
            Physics.simulationMode = SimulationMode.Script;   // from here the test moves the vehicle
        }

        Vector3 Ground(Vector3 p)
        {
            Assert.IsTrue(Physics.Raycast(new Vector3(p.x, p.y + 300f, p.z), Vector3.down, out var hit, 800f, m_Mask, QueryTriggerInteraction.Ignore),
                "collision under " + p.ToString("F1"));
            return hit.point + Vector3.up * 0.5f;
        }

        /// <summary>Puts the tractor at a region-local point of dk65-03 (east, north), heading yawDeg, at rest.</summary>
        void Place(float east, float north, float yawDeg)
        {
            Vector3 p = Ground(m_Root.transform.TransformPoint(new Vector3(east, 0f, north)));
            m_Body.SetPose(p, Quaternion.Euler(0f, yawDeg, 0f));
            Physics.SyncTransforms();
        }

        /// <summary>One scripted fixed step along the heading at <see cref="SlideSpeedMs"/>, on the ground.</summary>
        void Step()
        {
            var tr = m_Body.transform;
            Vector3 p = Ground(tr.position + tr.forward * (SlideSpeedMs * Time.fixedDeltaTime));
            m_Body.SetPose(p, tr.rotation);   // zeroes the rigid body velocity (no fall)
            // Keep the solver at the slide speed: the "Koniec mapy" warning needs |SpeedKmh| > 15 and the model alone
            // brakes to 0 within the 400 m approach (first Win64 run: reset at the edge with speed 0, no warning; int-ui-s23).
            m_Body.SetMoving(SlideSpeedMs, 8);
            Physics.SyncTransforms();
        }

        [UnityTest, Timeout(240000)]
        public IEnumerator OuterEdgeOfTheCorridor_WarnsThenStops()
        {
            yield return Load();
            var net = m_Boot.SafetyNet;
            var b = m_Root.GetComponent<WorldBoundary>();
            // 400 m inside the outer south edge, 300 m west of the tile centre (away from the dk65-01 corner).
            const float east = -300f;
            float north = -HalfTile + 400f;
            if (b != null)
                Debug.Log(string.Format(CultureInfo.InvariantCulture,
                    "[SAFETY-TEST] widened start rectangle at the south test line: {0:F0} m inside (the corridor edge is 400 m)",
                    WorldBoundary.InsideDistance(b.minEN, b.maxEN, east, -HalfTile + 1f)));
            Place(east, north, 180f);
            for (int i = 0; i < 25; i++) yield return new WaitForFixedUpdate();
            int r0 = net.ResetCount;
            Assert.IsFalse(net.EdgeWarningShown, "no warning 400 m inside");
            Assert.That(net.LastInsideDistance, Is.InRange(395f, 405f), "streamer distance = the outer south edge of dk65-03");

            m_Body.SetMoving(SlideSpeedMs, 8);
            bool warned = false;
            float warnInside = float.NaN, lastInside = float.MaxValue;
            Vector3 last = m_Body.transform.position;
            float tEnd = Time.time + 40f;
            while (Time.time < tEnd && net.ResetCount == r0)
            {
                last = m_Body.transform.position;
                Step();
                yield return new WaitForFixedUpdate();
                if (net.ResetCount != r0) break;
                lastInside = net.LastInsideDistance;
                if (!warned && net.EdgeWarningShown) { warned = true; warnInside = net.LastInsideDistance; }
            }
            Debug.Log(string.Format(CultureInfo.InvariantCulture, "[SAFETY-TEST] outer edge: warned at {0:F1} m, last inside {1:F1} m, resets {2}, reason {3}",
                warnInside, lastInside, net.ResetCount - r0, net.LastReason));
            Assert.IsTrue(warned, "\"Koniec mapy\" warning before the outer edge of the corridor");
            Assert.That(warnInside, Is.InRange(200f, net.warnDistance), "warned on the approach, within the warning distance");
            Assert.AreEqual(r0 + 1, net.ResetCount, "stopped at the outer edge");
            Assert.AreEqual(WorldExitReason.OutOfBounds, net.LastReason, "out of the corridor, not a fall");
            for (int i = 0; i < 10; i++) yield return new WaitForFixedUpdate();
            Assert.Greater(Vector3.Distance(m_Body.transform.position, last), 300f, "put back on a safe road pose, away from the edge");
            Assert.IsTrue(m_Body.Input.ParkingBrake, "parked after the reset");
            Assert.AreEqual(WorldSafetyNet.MsgOutOfBounds, m_Boot.StatusText, "the driver is told why");
        }

        [UnityTest, Timeout(240000)]
        public IEnumerator SeamWithAReadyNeighbour_NoWarningNoReset()
        {
            yield return Load();
            var net = m_Boot.SafetyNet;
            // 300 m south of the seam with dk65-04 (inside the standstill load radius, ~400 m WORKING_VALUE), on the tile's
            // centre line (east/west outer edges 1024 m away).
            Place(0f, HalfTile - 300f, 0f);
            float t0 = Time.time;
            while (m_Streamer.StateOf("dk65-04") != TileState.Ready && Time.time - t0 < 90f) yield return null;
            Assert.AreEqual(TileState.Ready, m_Streamer.StateOf("dk65-04"), "dk65-04 Ready before the crossing");
            for (int i = 0; i < 25; i++) yield return new WaitForFixedUpdate();
            int r0 = net.ResetCount;
            Assert.IsFalse(net.EdgeWarningShown);

            m_Body.SetMoving(SlideSpeedMs, 8);
            bool warned = false, crossed = false;
            float minInside = float.MaxValue;
            float tEnd = Time.time + 60f;
            while (Time.time < tEnd)
            {
                Step();
                yield return new WaitForFixedUpdate();
                warned |= net.EdgeWarningShown;
                minInside = Mathf.Min(minInside, net.LastInsideDistance);
                double y = m_Streamer.AnchorY + m_Body.transform.position.z;
                if (y >= SeamY) crossed = true;
                if (y >= SeamY + 300.0 || net.ResetCount != r0) break;
            }
            Debug.Log(string.Format(CultureInfo.InvariantCulture, "[SAFETY-TEST] seam: crossed {0}, min inside {1:F1} m, warned {2}, resets {3}",
                crossed, minInside, warned, net.ResetCount - r0));
            Assert.IsTrue(crossed, "reached the seam with dk65-04");
            Assert.AreEqual(r0, net.ResetCount, "no safety-net reset on the seam");
            Assert.IsFalse(warned, "no \"Koniec mapy\" warning on the seam with a Ready neighbour");
            Assert.Greater(minInside, net.warnDistance, "the seam is not an edge (nearest outer edge stays beyond the warning distance)");
        }
    }
}
