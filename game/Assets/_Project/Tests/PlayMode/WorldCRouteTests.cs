using System.Collections;
using System.Globalization;
using System.IO;
using Game.Controls;
using Game.Gameplay;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using Game.World;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>
    /// Drives the full start route of the imported world (WorldC: Kwadrat Park gate → Rondo Bieżeństwa → Andersa →
    /// Rondo Putry → DK8/DK19, ~2.4 km) on the imported collision with the route path follower, physics stepped in
    /// script mode at exactly 0.01 s (many steps per frame, independent of rendering speed).
    /// Checks: no fall-through (chassis never below the route ground by more than 1.5 m, wheels in contact),
    /// route completed, and reports the maximum |Δv| per step (impulses from collision seams / kerbs).
    /// Skipped when WorldC is not in the build (generated, gitignored: scripts/import-region.ps1).
    /// </summary>
    public class WorldCRouteTests
    {
        const float Dt = 0.01f;
        const int StepsPerFrame = 40;

        [UnityTest]
        public IEnumerator WorldC_Route_Solo_NoFallThrough() => DriveRoute(DrivingLabBootstrap.LabSpawn.Solo, 50f);

        [UnityTest]
        public IEnumerator WorldC_Route_Combination40t_NoFallThrough() => DriveRoute(DrivingLabBootstrap.LabSpawn.Gross40t, 50f);

        /// <summary>Static colliders overlapping a box around the tractor (diagnosis of impacts on the world collision).</summary>
        static string DescribeObstacles(VehicleBody body)
        {
            var t = body.transform;
            var hits = Physics.OverlapBox(t.position + t.up * 1.8f + t.forward * 1f, new Vector3(1.6f, 1.9f, 4.5f), t.rotation);
            var sb = new System.Text.StringBuilder();
            foreach (var h in hits)
            {
                if (h.attachedRigidbody != null) continue;
                var p = h.transform.parent;
                sb.Append(p != null && p.parent != null ? p.parent.name + "/" : "").Append(h.name).Append(' ')
                  .Append(h.bounds.center.ToString("F1")).Append("; ");
            }
            return sb.Length > 0 ? sb.ToString() : "(no static collider in the box)";
        }

        static IEnumerator DriveRoute(DrivingLabBootstrap.LabSpawn preset, float targetKmh)
        {
            if (!Application.CanStreamedLevelBeLoaded(GameBootstrap.WorldCSceneName))
                Assert.Ignore("WorldC not in the build - run scripts/import-region.ps1 -Region bialystok-industrial-c");

            var prevMode = Physics.simulationMode;
            Physics.simulationMode = SimulationMode.FixedUpdate;
            SceneManager.LoadScene(GameBootstrap.WorldCSceneName, LoadSceneMode.Single);
            yield return null;
            yield return null;
            var boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            var body = Object.FindAnyObjectByType<VehicleBody>();
            var route = Object.FindAnyObjectByType<WorldRoute>();
            Assert.IsNotNull(boot, "bootstrap missing");
            Assert.IsNotNull(route, "route missing");
            Assert.Greater(route.Length, 2000f, "start route ~2.4 km");

            boot.Spawn(preset);
            boot.enabled = false;                    // the test owns the inputs
            Physics.simulationMode = SimulationMode.Script;
            try
            {
                var driver = new PathFollowerDriverInput { TargetSpeedKmh = targetKmh, MaxLateralAccel = preset == DrivingLabBootstrap.LabSpawn.Solo ? 2.0f : 1.3f };
                driver.SetPath(route.WorldPoints(), route.speedLimitsKmh);
                driver.Enabled = true;
                var rb = body.Body;
                Vector3 vPrev = rb.linearVelocity;
                float maxDv = 0f, maxDvAt = 0f, maxCte = 0f, maxBelow = -99f, maxBelowAt = 0f, vMaxKmh = 0f;
                int noContactRun = 0, maxNoContactRun = 0, steps = 0;
                float simLimit = route.Length / 3.0f + 120f;   // generous: average ≥ 3 m/s
                float lastProgress = 0f, lastProgressT = 0f;
                bool fell = false, stuck = false;
                var trailerRb = body.Trailer != null ? body.Trailer.Body : null;
                Vector3 tvPrev = trailerRb != null ? trailerRb.linearVelocity : Vector3.zero;
                float maxDvTrailer = 0f;
                string hitInfo = null;

                while (!driver.Finished && steps * Dt < simLimit)
                {
                    for (int k = 0; k < StepsPerFrame && !driver.Finished; k++)
                    {
                        var m = body.Model;
                        var fb = new VehicleFeedback
                        {
                            ForwardSpeed = (float)m.SpeedForward,
                            Position = body.transform.position,
                            Forward = body.transform.forward,
                        };
                        var intent = new DriverIntent();
                        driver.Sample(Dt, fb, ref intent);
                        var input = body.Input;
                        input.Throttle = intent.Throttle;
                        input.Brake = intent.Brake;
                        input.Steer = intent.Steer;
                        input.Selector = GearSelector.Drive;
                        input.ParkingBrake = false;
                        input.ManualMode = false;
                        body.Input = input;

                        body.Tick(Dt);
                        Physics.Simulate(Dt);
                        steps++;

                        Vector3 v = rb.linearVelocity;
                        float dv = (v - vPrev).magnitude;
                        if (dv > maxDv) { maxDv = dv; maxDvAt = driver.Progress; }
                        if (dv > 3f && hitInfo == null) hitInfo = DescribeObstacles(body);
                        vPrev = v;
                        if (trailerRb != null)
                        {
                            float dvt = (trailerRb.linearVelocity - tvPrev).magnitude;
                            maxDvTrailer = Mathf.Max(maxDvTrailer, dvt);
                            tvPrev = trailerRb.linearVelocity;
                        }
                        vMaxKmh = Mathf.Max(vMaxKmh, v.magnitude * 3.6f);
                        maxCte = Mathf.Max(maxCte, driver.CrossTrackError);

                        // Fall-through: chassis origin below the route ground at the current progress.
                        float groundY = route.PointAt(driver.Progress).y;
                        float below = groundY - body.transform.position.y;
                        if (below > maxBelow) { maxBelow = below; maxBelowAt = driver.Progress; }
                        if (below > 1.5f) fell = true;

                        int contacts = 0;
                        foreach (var w in m.Wheels) if (w.Contact) contacts++;
                        noContactRun = contacts == 0 ? noContactRun + 1 : 0;
                        maxNoContactRun = Mathf.Max(maxNoContactRun, noContactRun);
                        if (noContactRun > 100) fell = true;   // 1 s fully airborne

                        if (driver.Progress > lastProgress + 1f) { lastProgress = driver.Progress; lastProgressT = steps * Dt; }
                        if (steps * Dt - lastProgressT > 30f) stuck = true;
                        if (fell || stuck) break;
                    }
                    if (fell || stuck) break;
                    yield return null;
                }

                var ci = CultureInfo.InvariantCulture;
                string summary = string.Format(ci,
                    "[TEST] WorldC route {0}: {1} steps ({2:F0} s sim), progress {3:F0}/{4:F0} m, finished {5}, max |dv|/step {6:F3} m/s at s={7:F0} m{8}, " +
                    "max chassis below route ground {9:F2} m at s={10:F0} m, longest no-contact run {11} steps, max cross-track {12:F2} m, v max {13:F0} km/h, fell {14}, stuck {15}",
                    preset, steps, steps * Dt, driver.Progress, route.Length, driver.Finished, maxDv, maxDvAt,
                    trailerRb != null ? string.Format(ci, " (trailer {0:F3})", maxDvTrailer) : "",
                    maxBelow, maxBelowAt, maxNoContactRun, maxCte, vMaxKmh, fell, stuck) + (hitInfo != null ? " | impact near: " + hitInfo : "");
                Debug.Log(summary);
                try
                {
                    string dir = Path.Combine(Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..")), "artifacts", "tests");
                    Directory.CreateDirectory(dir);
                    File.AppendAllText(Path.Combine(dir, "worldc-route.txt"), System.DateTime.Now.ToString("s", ci) + " " + summary + System.Environment.NewLine);
                }
                catch (IOException) { }

                Assert.IsFalse(fell, "vehicle fell through / left the ground: " + summary);
                Assert.IsFalse(stuck, "vehicle stuck: " + summary);
                Assert.IsTrue(driver.Finished, "route not completed in time: " + summary);
                Assert.Less(maxCte, 4.0f, "path follower left the lane by > 4 m");
            }
            finally
            {
                Physics.simulationMode = prevMode;
            }
        }
    }
}
