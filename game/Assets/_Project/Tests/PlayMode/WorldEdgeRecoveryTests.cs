using System.Collections;
using System.Globalization;
using System.IO;
using Game.Cameras;
using Game.Gameplay;
using Game.Vehicle.Runtime;
using Game.World;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0082 on the imported world (WorldC): the region edge has data and closures, and a combination that leaves
    /// the world (beyond the edge at speed, or under the collision) is put back on the last safe road pose, parked,
    /// with the cab camera at the driver's eye. Reproduces the owner's recording of 2026-11-10 (116 s: off the north
    /// edge on al. Tysiąclecia Państwa Polskiego at ~105 km/h). Evidence CSV: artifacts/drive-fold-r10/world-edge-reset.csv.
    /// Skipped when WorldC is not in the build (generated, gitignored: scripts/import-region.ps1).
    /// </summary>
    public class WorldEdgeRecoveryTests
    {
        static IEnumerator Load()
        {
            if (!Application.CanStreamedLevelBeLoaded(GameBootstrap.WorldCSceneName))
                Assert.Ignore("WorldC not in the build - run scripts/import-region.ps1 -Region bialystok-industrial-c");
            Physics.simulationMode = SimulationMode.FixedUpdate;
            SceneManager.LoadScene(GameBootstrap.WorldCSceneName, LoadSceneMode.Single);
            yield return null;
            yield return null;
        }

        static string EvidencePath(string file)
        {
            string dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "artifacts", "drive-fold-r10"));
            Directory.CreateDirectory(dir);
            return Path.Combine(dir, file);
        }

        [UnityTest]
        public IEnumerator LeavingTheRegion_AtSpeed_ResetsOntoTheLastSafeRoadPose()
        {
            yield return Load();
            var boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            var body = Object.FindAnyObjectByType<VehicleBody>();
            var root = Object.FindAnyObjectByType<WorldRegionRoot>();
            var rig = Object.FindAnyObjectByType<CameraRig>();
            Assert.IsNotNull(boot); Assert.IsNotNull(body); Assert.IsNotNull(root);
            var net = boot.SafetyNet;
            Assert.IsNotNull(net, "world scenes get the safety net");
            Assert.IsTrue(WorldBoundary.TryChunkBounds(root, out Vector2 min, out Vector2 max));
            Assert.AreEqual(2048f, max.x - min.x, 1f, "region width");

            // Stand at the spawn until safe poses exist (parked on the depot road, > 120 m inside).
            float t0 = Time.time;
            while (net.SafePoses.Count < 4 && Time.time - t0 < 12f) yield return new WaitForFixedUpdate();
            Assert.GreaterOrEqual(net.SafePoses.Count, 4, "safe poses recorded while standing on the road");
            Assert.IsTrue(net.SafePoses.TryGet(Time.time, net.safeMinAge, out var safe));
            Vector3 spawnPos = body.transform.position;

            var csv = new System.Text.StringBuilder("t_s,inside_m,x,y,z,speed_kmh,vy_ms,resets,reason\n");
            var ci = CultureInfo.InvariantCulture;
            void Row() => csv.AppendFormat(ci, "{0:F2},{1:F1},{2:F2},{3:F2},{4:F2},{5:F1},{6:F2},{7},{8}\n", Time.time - t0, net.LastInsideDistance,
                body.transform.position.x, body.transform.position.y, body.transform.position.z, body.Body.linearVelocity.magnitude * 3.6f,
                body.Body.linearVelocity.y, net.ResetCount, net.LastReason);

            // The recording: north edge on al. Tysiąclecia (E −857), 105 km/h, heading out. Start 25 m before the edge.
            Vector3 edgeLocal = new Vector3(-857f, 0f, max.y - 25f);
            Vector3 start = root.transform.TransformPoint(edgeLocal);
            Assert.IsTrue(Gate3Cameras.TryGroundY(start.x, start.z, root.transform.position.y + 400f, new[] { body.transform }, out float gy), "collision 25 m before the edge");
            start.y = gy + 0.3f;
            body.SetPose(start, Quaternion.LookRotation(Vector3.forward, Vector3.up));
            body.Body.linearVelocity = Vector3.forward * (105f / 3.6f);
            Physics.SyncTransforms();
            rig.AddLookDelta(new Vector2(400f, -300f));   // the driver's fingers on the look pad during the fall

            float lowestY = float.MaxValue, maxSpeed = 0f;
            float tEnd = Time.time + 4f;
            while (Time.time < tEnd && net.ResetCount == 0)
            {
                yield return new WaitForFixedUpdate();
                lowestY = Mathf.Min(lowestY, body.transform.position.y);
                maxSpeed = Mathf.Max(maxSpeed, body.Body.linearVelocity.magnitude * 3.6f);
                Row();
            }
            Assert.AreEqual(1, net.ResetCount, "reset when the vehicle left the region");
            Assert.AreEqual(WorldExitReason.OutOfBounds, net.LastReason);
            Assert.Greater(lowestY, gy - 2.5f, "caught before the fall (recording: fell for 10 s to 179 km/h)");
            Assert.Less(maxSpeed, 112f, "no free-fall speed build-up");
            for (int i = 0; i < 50; i++) { yield return new WaitForFixedUpdate(); Row(); }

            Assert.Less(Vector3.Distance(body.transform.position, spawnPos), 6f, "back on the last safe pose (the depot road)");
            Assert.Less(body.Body.linearVelocity.magnitude, 1.0f, "at rest after the reset");
            Assert.Greater(body.transform.up.y, 0.97f, "upright");
            Assert.IsTrue(body.Input.ParkingBrake, "parked");
            Assert.AreEqual(WorldSafetyNet.MsgOutOfBounds, boot.StatusText, "the driver is told why");
            Assert.Greater(net.LastInsideDistance, net.safeEdgeDistance - 1f);
            // Cab camera: at the driver's eye, look re-centred.
            var eye = body.GetComponent<VehicleVisuals>().cabPivot.Find("DriverEyePoint");
            yield return null;
            Assert.AreEqual(0f, rig.LookYaw, 1e-3f);
            Assert.Less(Vector3.Distance(rig.cam.transform.position, eye.position), 0.25f, "camera in the cab at the eye point");
            File.WriteAllText(EvidencePath("world-edge-reset.csv"), csv.ToString());
        }

        [UnityTest]
        public IEnumerator FallingUnderTheWorld_ResetsToo()
        {
            yield return Load();
            var boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            var body = Object.FindAnyObjectByType<VehicleBody>();
            var net = boot.SafetyNet;
            float t0 = Time.time;
            while (net.SafePoses.Count < 4 && Time.time - t0 < 12f) yield return new WaitForFixedUpdate();
            Vector3 spawnPos = body.transform.position;
            // Under the terrain at the spawn: nothing below within the probe depth (a hole in the collision).
            body.SetPose(spawnPos + Vector3.down * 25f, body.transform.rotation);
            Physics.SyncTransforms();
            float tEnd = Time.time + 3f;
            while (Time.time < tEnd && net.ResetCount == 0) yield return new WaitForFixedUpdate();
            Assert.AreEqual(1, net.ResetCount);
            Assert.AreNotEqual(WorldExitReason.OutOfBounds, net.LastReason);
            for (int i = 0; i < 50; i++) yield return new WaitForFixedUpdate();
            Assert.Less(Vector3.Distance(body.transform.position, spawnPos), 6f);
            Assert.AreEqual(WorldSafetyNet.MsgFell, boot.StatusText);
        }

        [UnityTest]
        public IEnumerator RegionEdge_HasClosuresBeforeTheEdge_AndGroundBeyondIt()
        {
            yield return Load();
            var root = Object.FindAnyObjectByType<WorldRegionRoot>();
            var boundary = root.GetComponent<WorldBoundary>();
            if (boundary == null) Assert.Ignore("scene imported before ADR 0082 - re-run scripts/import-region.ps1");
            Assert.Greater(boundary.closures.Length, 20, "roads leaving the region are closed (37 boundary nodes in roads.graph.json)");
            bool tysiaclecia = false;
            foreach (var c in boundary.closures)
            {
                float inside = WorldBoundary.InsideDistance(boundary.minEN, boundary.maxEN, c.localPos.x, c.localPos.z);
                Assert.That(inside, Is.GreaterThan(5f).And.LessThan(90f), "closure set back from the edge: " + c.road);
                // The closure is a physical obstacle: a ray along the road at bumper height hits it.
                Vector3 p = root.transform.TransformPoint(c.localPos) + Vector3.up * 0.6f;
                Vector3 dir = Quaternion.Euler(0f, c.headingDeg, 0f) * Vector3.forward;
                Assert.IsTrue(Physics.Raycast(p - dir * 6f, dir, out var hit, 8f, ~0, QueryTriggerInteraction.Ignore), "closure collider: " + c.road);
                Assert.That(hit.distance, Is.InRange(5.2f, 6.2f));
                if (Mathf.Abs(c.localPos.x + 860f) < 12f && c.localPos.z > 900f) tysiaclecia = true;
            }
            Assert.IsTrue(tysiaclecia, "al. Tysiąclecia Państwa Polskiego (the road of the recording) is closed before the north edge");
            // Evidence: road surface profile of the recording's last 320 m (the 90 -> 94 km/h rise before the edge).
            var prof = new System.Text.StringBuilder("north_m,road_y_m
");
            for (float n = 700f; n <= 1020f; n += 20f)
            {
                Vector3 w = root.transform.TransformPoint(new Vector3(-857f, 0f, n));
                if (Gate3Cameras.TryGroundY(w.x, w.z, root.transform.position.y + 400f, System.Array.Empty<Transform>(), out float ry))
                    prof.AppendFormat(CultureInfo.InvariantCulture, "{0:F0},{1:F2}
", n, ry);
            }
            File.WriteAllText(EvidencePath("tysiaclecia-north-profile.csv"), prof.ToString());
            // Ground to the horizon: the apron renderer reaches far beyond the region.
            var apron = root.transform.Find("WorldEdge/Apron").GetComponent<MeshRenderer>();
            Assert.Greater(apron.bounds.size.x, 2048f + 2f * 1400f, "apron beyond the far clip plane on both sides");
        }
    }
}
