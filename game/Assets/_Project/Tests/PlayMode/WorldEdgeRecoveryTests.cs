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

            // The recording: north edge on al. Tysiąclecia, 105 km/h, heading out. The outbound (eastern) carriageway
            // runs (-844.3, 966.4) -> (-856.5, 1024.0) in roads.graph.json; start 25 m before the edge, along the road.
            Vector2 edgeEN = new Vector2(-856.5f, max.y), roadDir = (edgeEN - new Vector2(-844.3f, 966.4f)).normalized;
            Vector2 startEN = edgeEN - roadDir * 25f;
            Vector3 start = root.transform.TransformPoint(new Vector3(startEN.x, 0f, startEN.y));
            Vector3 fwd = root.transform.TransformDirection(new Vector3(roadDir.x, 0f, roadDir.y));
            Assert.IsTrue(Physics.Raycast(start + Vector3.up * 300f, Vector3.down, out var startHit, 600f, ~0, QueryTriggerInteraction.Ignore), "collision 25 m before the edge");
            Assert.AreEqual("col_asphalt", startHit.collider.name, "the start is on the carriageway");
            float gy = startHit.point.y;
            start.y = gy;
            // The whole combination (tractor + coupled trailer), rolling in gear; the lab re-applies the parking brake
            // after a spawn, which cannot stop 105 km/h within 25 m.
            boot.SpawnAt(boot.CurrentSpawn, start, Quaternion.LookRotation(fwd, Vector3.up));
            body.SetMoving(105f / 3.6f, 11);
            Physics.SyncTransforms();
            rig.AddLookDelta(new Vector2(400f, -300f));   // the driver's fingers on the look pad during the fall

            float lowestY = float.MaxValue, maxSpeed = 0f;
            float tEnd = Time.time + 4f;
            while (Time.time < tEnd && net.ResetCount == 0)
            {
                yield return new WaitForFixedUpdate();
                if (net.ResetCount == 0) lowestY = Mathf.Min(lowestY, body.transform.position.y);   // the pose after the reset is elsewhere
                maxSpeed = Mathf.Max(maxSpeed, body.Body.linearVelocity.magnitude * 3.6f);
                Row();
            }
            File.WriteAllText(EvidencePath("world-edge-reset.csv"), csv.ToString());
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
                Assert.That(inside, Is.GreaterThan(2f).And.LessThan(90f), "closure set back from the edge: " + c.road);
                // The closure is a physical obstacle: a ray along the road at bumper height hits it.
                Vector3 p = root.transform.TransformPoint(c.localPos) + Vector3.up * 0.6f;
                Vector3 dir = Quaternion.Euler(0f, c.headingDeg, 0f) * Vector3.forward;
                Assert.IsTrue(Physics.Raycast(p - dir * 6f, dir, out var hit, 8f, ~0, QueryTriggerInteraction.Ignore), "closure collider: " + c.road);
                Assert.That(hit.distance, Is.InRange(5.2f, 6.2f));
                if (Mathf.Abs(c.localPos.x + 860f) < 12f && c.localPos.z > 900f) tysiaclecia = true;
            }
            Assert.IsTrue(tysiaclecia, "al. Tysiąclecia Państwa Polskiego (the road of the recording) is closed before the north edge");
            // Evidence: surface profile of the outbound carriageway of al. Tysiąclecia before the north edge (the
            // recording's 90 -> 94 km/h). Line: artifacts/drive-fold-r10/tysiaclecia_outbound_line.json (the chain of
            // roads.graph.json edges, ~960 m) when present, else the last 170 m.
            var line = new[] { new Vector2(-820.5f, 858.0f), new Vector2(-827.3f, 885.6f), new Vector2(-831.9f, 906.3f), new Vector2(-842.2f, 955.2f), new Vector2(-844.3f, 966.4f), new Vector2(-856.5f, 1024.0f) };
            string lineFile = EvidencePath("tysiaclecia_outbound_line.json");
            if (File.Exists(lineFile))
            {
                var nums = System.Text.RegularExpressions.Regex.Matches(File.ReadAllText(lineFile), @"-?\d+(\.\d+)?");
                line = new Vector2[nums.Count / 2];
                for (int k = 0; k < line.Length; k++)
                    line[k] = new Vector2(float.Parse(nums[2 * k].Value, CultureInfo.InvariantCulture), float.Parse(nums[2 * k + 1].Value, CultureInfo.InvariantCulture));
            }
            var prof = new System.Text.StringBuilder("s_m,east_m,north_m,top_y_m,collider\n");
            float sAlong = 0f;
            for (int k = 0; k + 1 < line.Length; k++)
            {
                float segLen = Vector2.Distance(line[k], line[k + 1]);
                for (float d = 0f; d < segLen; d += 2f)
                {
                    Vector2 en = Vector2.Lerp(line[k], line[k + 1], d / segLen);
                    Vector3 w = root.transform.TransformPoint(new Vector3(en.x, 0f, en.y));
                    float top = float.NegativeInfinity; string who = "";
                    foreach (var h in Physics.RaycastAll(new Vector3(w.x, root.transform.position.y + 400f, w.z), Vector3.down, 800f, ~0, QueryTriggerInteraction.Ignore))
                        if (h.collider.GetComponentInParent<WorldBoundary>() != null && h.collider.GetComponent<BoxCollider>() == null && h.point.y > top) { top = h.point.y; who = h.collider.name; }
                    prof.AppendFormat(CultureInfo.InvariantCulture, "{0:F0},{1:F1},{2:F1},{3:F2},{4}\n", sAlong + d, en.x, en.y, top, who);
                }
                sAlong += segLen;
            }
            File.WriteAllText(EvidencePath("tysiaclecia-north-profile.csv"), prof.ToString());
            // Ground to the horizon: the apron renderer reaches far beyond the region.
            var apron = root.transform.Find("WorldEdge/Apron").GetComponent<MeshRenderer>();
            Assert.Greater(apron.bounds.size.x, 2048f + 2f * 1400f, "apron beyond the far clip plane on both sides");
        }
    }
}
