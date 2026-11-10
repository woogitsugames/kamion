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
    /// Owner report (map audit MA-003): the Kwadrat Park boom did not open and had no collision. This test runs on the
    /// imported world scene (WorldC), not on a synthetic rig:
    ///  * every imported boom is a closed, solid <see cref="DepotBarrier"/> (ray along the lane hits its collider);
    ///  * the 40 t combination driven along the start route by the path follower is let through by the boom on its
    ///    lane (opens before the tractor arrives, is never touched, never breaks) and the boom closes behind the trailer;
    ///  * the boom of the other lane stays closed.
    /// Skipped when WorldC is not in the build (generated, gitignored: scripts/import-region.ps1).
    /// </summary>
    public class WorldCBarrierTests
    {
        const float Dt = 0.01f;
        const int StepsPerFrame = 40;

        sealed class BoomContactProbe : MonoBehaviour
        {
            public int Contacts;
            public string First;
            void OnCollisionEnter(Collision c)
            {
                if (Contacts++ == 0) First = c.collider.name + " v " + c.relativeVelocity.magnitude.ToString("F2", CultureInfo.InvariantCulture);
            }
        }

        [UnityTest]
        public IEnumerator WorldC_GateBoom_IsSolid_Opens_ForCombination_AndCloses()
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
            var bars = Object.FindObjectsByType<DepotBarrier>(FindObjectsSortMode.None);
            Assert.GreaterOrEqual(bars.Length, 2, "Kwadrat Park gate kit: one automatic boom per lane");

            // ---- every boom: closed, visible, solid ----
            DepotBarrier onRoute = null;
            float routeS = 0f, bestD = float.MaxValue;
            var pts = route.WorldPoints();
            foreach (var b in bars)
            {
                Assert.AreEqual(DepotBarrier.BarrierState.Closed, b.State, b.name + " starts closed");
                var col = b.GetComponent<BoxCollider>();
                Assert.IsTrue(col != null && col.enabled && !col.isTrigger, b.name + " has a solid collider");
                Assert.IsNotNull(b.GetComponent<MeshFilter>().sharedMesh, b.name + " has a mesh");
                var t = b.transform;
                Vector3 mid = t.TransformPoint(new Vector3(b.boomLengthM * 0.5f, 0f, 0f));
                // a ray along the lane, 4 m before the boom, must be stopped by the boom itself (all layers: the boom is on Ignore Raycast)
                Vector3 dir = t.forward * b.travelSign;
                bool hitBoom = false;
                foreach (var h in Physics.RaycastAll(mid - dir * 4f, dir, 8f, ~0, QueryTriggerInteraction.Ignore))
                    if (h.collider == col) hitBoom = true;
                Assert.IsTrue(hitBoom, b.name + ": ray along the lane does not hit the boom collider");
                // boom height over the carriageway (0.8 .. 1.2 m)
                Assert.IsTrue(Physics.Raycast(mid, Vector3.down, out var ground, 3f), b.name + ": no ground under the boom");
                Assert.That(ground.distance, Is.InRange(0.7f, 1.3f), b.name + " boom height over the road");
                // which boom spans the start route?
                float acc = 0f;
                for (int i = 1; i < pts.Length; i++)
                {
                    Vector3 a = pts[i - 1], c = pts[i];
                    Vector3 ac = c - a;
                    float u = Mathf.Clamp01(Vector3.Dot(mid - a, ac) / Mathf.Max(1e-6f, ac.sqrMagnitude));
                    Vector3 q = a + ac * u;
                    float d = new Vector2(q.x - mid.x, q.z - mid.z).magnitude;
                    if (d < bestD) { bestD = d; onRoute = b; routeS = acc + ac.magnitude * u; }
                    acc += ac.magnitude;
                    if (acc > 600f) break;
                }
            }
            Assert.Less(bestD, 2.5f, "no boom across the start route lane (nearest " + bestD.ToString("F1", CultureInfo.InvariantCulture) + " m)");
            Vector3 travel = onRoute.transform.forward * onRoute.travelSign;
            Assert.Greater(Vector3.Dot(travel, route.TangentAt(routeS)), 0.7f, "boom travel direction against the route");
            var probe = onRoute.gameObject.AddComponent<BoomContactProbe>();

            // ---- drive the combination through ----
            boot.Spawn(DrivingLabBootstrap.LabSpawn.Gross40t);
            boot.enabled = false;
            Physics.simulationMode = SimulationMode.Script;
            try
            {
                var driver = new PathFollowerDriverInput { TargetSpeedKmh = 50f, MaxLateralAccel = 1.3f };
                driver.SetPath(pts, route.speedLimitsKmh);
                driver.Enabled = true;
                var rb = body.Body;
                Vector3 vPrev = rb.linearVelocity;
                Vector3 hinge = onRoute.transform.position;
                float maxDv = 0f, angleAt8m = -1f, vAtBoomKmh = 0f, openedAtS = -1f, closedAtS = -1f, tOpenStart = -1f, tOpen = -1f;
                bool broken = false, otherMoved = false, everOpen = false;
                int steps = 0, maxLoop = 0;
                float endS = routeS + 70f;
                while (driver.Progress < endS && steps * Dt < 240f)
                {
                    for (int k = 0; k < StepsPerFrame && driver.Progress < endS; k++)
                    {
                        var m = body.Model;
                        var fb = new VehicleFeedback { ForwardSpeed = (float)m.SpeedForward, Position = body.transform.position, Forward = body.transform.forward };
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
                        foreach (var b in bars) b.Tick(Dt);
                        Physics.Simulate(Dt);
                        maxLoop = Mathf.Max(maxLoop, onRoute.LoopColliders);
                        steps++;

                        Vector3 v = rb.linearVelocity;
                        maxDv = Mathf.Max(maxDv, (v - vPrev).magnitude);
                        vPrev = v;
                        float along = Vector3.Dot(body.transform.position - hinge, travel);     // tractor origin relative to the boom plane
                        if (angleAt8m < 0f && along > -8f) { angleAt8m = onRoute.AngleDeg; vAtBoomKmh = v.magnitude * 3.6f; }
                        var st = onRoute.State;
                        if (st == DepotBarrier.BarrierState.Opening && tOpenStart < 0f) { tOpenStart = steps * Dt; openedAtS = driver.Progress; }
                        if (st == DepotBarrier.BarrierState.Open && !everOpen) { everOpen = true; tOpen = steps * Dt; }
                        if (st == DepotBarrier.BarrierState.Closed && everOpen && closedAtS < 0f) closedAtS = driver.Progress;
                        if (st == DepotBarrier.BarrierState.Broken) broken = true;
                        foreach (var b in bars) if (b != onRoute && b.State != DepotBarrier.BarrierState.Closed) otherMoved = true;
                    }
                    yield return null;
                }

                var ci = CultureInfo.InvariantCulture;
                string summary = string.Format(ci,
                    "[TEST] WorldC gate boom: {0} booms, route boom {1} at s={2:F1} m (lane offset {3:F2} m), opening started at s={4:F1} m, " +
                    "open after {5:F2} s, angle {6:F1} deg with the tractor origin 8 m before the boom at {7:F1} km/h, closed again at s={8:F1} m, " +
                    "boom contacts {9}{10}, broken {11}, other boom moved {12}, max |dv|/step {13:F3} m/s, loop query max {14} colliders (buffer {15})",
                    bars.Length, onRoute.name, routeS, bestD, openedAtS, tOpen - tOpenStart, angleAt8m, vAtBoomKmh, closedAtS,
                    probe.Contacts, probe.Contacts > 0 ? " (" + probe.First + ")" : "", broken, otherMoved, maxDv, maxLoop, DepotBarrier.LoopBufferSize);
                Debug.Log(summary);
                try
                {
                    string dir = Path.Combine(Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..")), "artifacts", "tests");
                    Directory.CreateDirectory(dir);
                    File.AppendAllText(Path.Combine(dir, "worldc-barrier.txt"), System.DateTime.Now.ToString("s", ci) + " " + summary + System.Environment.NewLine);
                }
                catch (IOException) { }

                Assert.IsFalse(broken, "the boom was broken by the combination: " + summary);
                Assert.AreEqual(0, probe.Contacts, "the combination touched the boom: " + summary);
                Assert.IsTrue(everOpen, "the boom never opened: " + summary);
                Assert.Greater(closedAtS, routeS, "the boom did not close behind the trailer: " + summary);
                Assert.IsFalse(otherMoved, "the boom of the other lane moved: " + summary);
                Assert.Less(maxDv, 0.8f, "jolt at the gate: " + summary);
                Assert.Less(maxLoop, DepotBarrier.LoopBufferSize, "presence loop buffer full (vehicles can be missed): " + summary);
            }
            finally
            {
                Physics.simulationMode = prevMode;
            }
        }
    }
}
