using System.Collections;
using Game.Controls;
using Game.Gameplay;
using Game.Vehicle.Runtime;
using Game.World;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>Gate 3 launch arguments route_s / route_end / qacam_set=gate3 (logic behind them, no scene import needed).</summary>
    public class RouteSpawnTests
    {
        static WorldRoute MakeRoute()
        {
            // Straight route heading 45 deg (north-east) at y = 0, 300 m long, 10 m points.
            var go = new GameObject("TestRoute");
            var r = go.AddComponent<WorldRoute>();
            int n = 31;
            r.points = new Vector3[n]; r.distances = new float[n]; r.speedLimitsKmh = new float[n];
            Vector3 dir = new Vector3(1f, 0f, 1f).normalized;
            for (int i = 0; i < n; i++) { r.points[i] = new Vector3(-500f, 0f, -500f) + dir * (10f * i); r.distances[i] = 10f * i; }
            return r;
        }

        [UnityTest]
        public IEnumerator RouteS_SpawnsCoupledCombinationOnRouteWithHeading()
        {
            Physics.simulationMode = SimulationMode.FixedUpdate;
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            var boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            var body = Object.FindAnyObjectByType<VehicleBody>();
            var trailer = Object.FindAnyObjectByType<TrailerBody>();
            var route = MakeRoute();
            boot.route = route;
            boot.Spawn(DrivingLabBootstrap.LabSpawn.Gross40t);
            yield return new WaitForFixedUpdate();
            Vector3 baseline = body.transform.InverseTransformPoint(trailer.transform.position);   // trailer pose in the tractor frame, lab spawn
            boot.SetRouteSpawn(120f);
            yield return new WaitForFixedUpdate();

            Vector3 expect = route.PointAt(120f);
            Vector3 flatDelta = body.transform.position - expect; flatDelta.y = 0f;
            // The tractor origin is the spawn point (ResetPose); the jaw/trailer follow behind.
            Assert.Less(flatDelta.magnitude, 1.5f, "tractor not at route s=120");
            Vector3 fwd = body.transform.forward; fwd.y = 0f;
            Assert.Less(Vector3.Angle(fwd, route.TangentAt(120f)), 2f, "heading must follow the route tangent");
            Assert.IsTrue(body.Coupled, "combination must be coupled at route_s");
            Vector3 local = body.transform.InverseTransformPoint(trailer.transform.position);
            Assert.Less((local - baseline).magnitude, 0.3f, "trailer must sit in the jaw exactly as in the lab spawn, not parked elsewhere");
        }

        /// <summary>ADR 0262: a route start outside a region-edge closure moves behind it; a start inside a static collider
        /// moves along the route to the first free place (owner report 2026-11-15: truck in the barrier row).</summary>
        [UnityTest]
        public IEnumerator RouteS_OutsideAClosureOrInsideACollider_MovesAlongTheRoute()
        {
            Physics.simulationMode = SimulationMode.FixedUpdate;
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            var boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            var body = Object.FindAnyObjectByType<VehicleBody>();
            var route = MakeRoute();
            boot.route = route;
            boot.Spawn(DrivingLabBootstrap.LabSpawn.Gross40t);
            yield return new WaitForFixedUpdate();

            // The route enters the region through a closure 60 m from its start (road heading towards the edge = 225 deg).
            var boundary = new GameObject("TestBoundary").AddComponent<WorldBoundary>();
            boundary.closures = new[] { new WorldBoundary.Closure { localPos = route.points[6], headingDeg = 225f, widthM = 7f, road = "t" } };
            LogAssert.Expect(LogType.Warning, new System.Text.RegularExpressions.Regex(@"\[START\] start moved along the route: route_s 12\.0 -> 85\.0 \(region-edge closure"));
            boot.SetRouteSpawn(12f);
            yield return new WaitForFixedUpdate();
            Vector3 d = body.transform.position - route.PointAt(60f + StartClearance.BehindClosureM); d.y = 0f;
            Assert.Less(d.magnitude, 1.5f, "start 12 m is outside the closure at 60 m: the tractor must stand 25 m behind the row");

            // A barrier element standing on the route at s = 200 m: a start requested there moves on until the trailer is clear of it.
            var block = GameObject.CreatePrimitive(PrimitiveType.Cube);
            block.name = "TestBarrier";
            block.transform.SetPositionAndRotation(route.PointAt(200f) + Vector3.up * 0.4f, Quaternion.LookRotation(route.TangentAt(200f)));
            block.transform.localScale = new Vector3(6f, 0.81f, 0.6f);
            Physics.SyncTransforms();
            Assert.AreEqual("TestBarrier", SpawnSafety.FirstOverlap(route, 200f, new[] { body.transform, Object.FindAnyObjectByType<TrailerBody>().transform }).name);
            LogAssert.Expect(LogType.Warning, new System.Text.RegularExpressions.Regex(@"\[START\] start moved along the route: route_s 200\.0 -> 21[24]\.0 \(collider 'TestBarrier'\)"));
            boot.SetRouteSpawn(200f);
            yield return new WaitForFixedUpdate();
            float along = Vector3.Dot(body.transform.position - route.PointAt(200f), route.TangentAt(200f));
            Assert.GreaterOrEqual(along, StartClearance.RearM + StartClearance.MarginM, "the rear end of the trailer must be clear of the barrier");
            Assert.LessOrEqual(along, StartClearance.RearM + StartClearance.MarginM + 0.3f + 2f * SpawnSafety.StepM, "first free place, not further");
            Assert.IsTrue(body.Coupled);
            Object.Destroy(block);
            Object.Destroy(boundary.gameObject);
        }

        /// <summary>ADR 0262 / review P2-1: a start requested close to or past the closure the route LEAVES the region through
        /// moves back in front of it (never outside the exit row, facing the tile edge).</summary>
        [UnityTest]
        public IEnumerator RouteS_AtOrPastTheExitClosure_MovesBackInFrontOfIt()
        {
            Physics.simulationMode = SimulationMode.FixedUpdate;
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            var boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            var body = Object.FindAnyObjectByType<VehicleBody>();
            var route = MakeRoute();
            boot.route = route;
            boot.Spawn(DrivingLabBootstrap.LabSpawn.Gross40t);
            yield return new WaitForFixedUpdate();

            // The route leaves the region through a closure at s = 240 m (road heading towards the edge = route heading 45 deg).
            var boundary = new GameObject("TestBoundary").AddComponent<WorldBoundary>();
            boundary.closures = new[] { new WorldBoundary.Closure { localPos = route.points[24], headingDeg = 45f, widthM = 7f, road = "t" } };
            float expectS = 240f - StartClearance.BehindClosureM;
            foreach (float requested in new[] { 230f, 290f })
            {
                LogAssert.Expect(LogType.Warning, new System.Text.RegularExpressions.Regex(@"\[START\] start moved along the route: route_s " + requested.ToString("F1", System.Globalization.CultureInfo.InvariantCulture).Replace(".", @"\.") + @" -> 215\.0 \(region-edge closure ahead"));
                boot.SetRouteSpawn(requested);
                yield return new WaitForFixedUpdate();
                Vector3 d = body.transform.position - route.PointAt(expectS); d.y = 0f;
                Assert.Less(d.magnitude, 1.5f, "start " + requested + " m must move back to 25 m in front of the exit row at 240 m");
                Vector3 fwd = body.transform.forward; fwd.y = 0f;
                Assert.Less(Vector3.Angle(fwd, route.TangentAt(expectS)), 2f, "heading stays along the route");
            }
            // A start well in front of the exit row is left alone.
            boot.SetRouteSpawn(120f);
            yield return new WaitForFixedUpdate();
            Vector3 e = body.transform.position - route.PointAt(120f); e.y = 0f;
            Assert.Less(e.magnitude, 1.5f);
            Object.Destroy(boundary.gameObject);
        }
        [Test]
        public void PathFollower_SeekToAndEndS()
        {
            var r = MakeRoute();
            var d = new PathFollowerDriverInput { Enabled = true, TargetSpeedKmh = 30f };
            d.SetPath(r.WorldPoints(), r.speedLimitsKmh);
            d.EndS = 200f;
            d.SeekTo(150f);
            Assert.AreEqual(150f, d.Progress, 0.01f);
            // Standing at s=150 heading along the route: stopping point is 200 m, driver still wants to move.
            var fb = new VehicleFeedback { Position = r.PointAt(150f), Forward = r.TangentAt(150f), ForwardSpeed = 0f };
            var intent = new DriverIntent();
            d.Sample(0.02f, fb, ref intent);
            Assert.Greater(intent.Throttle, 0f);
            Assert.IsFalse(d.Finished);
            // At s=199 it reports finished and brakes.
            fb.Position = r.PointAt(199f);
            d.Sample(0.02f, fb, ref intent);
            Assert.IsTrue(d.Finished, "must finish at route_end");
            Assert.Greater(intent.Brake, 0f);
        }

        [Test]
        public void Gate3Cameras_ParseAndNormalise()
        {
            var f = Gate3Cameras.Parse("{\"cameras\":[{\"id\":\"g3a_eye_s0012\",\"kind\":\"driver_eye\",\"pos\":[1,2,3],\"look_at\":[4,5,6],\"fov_deg\":60}]}");
            Assert.AreEqual(1, f.cameras.Length);
            Assert.AreEqual("g3a-eye-s0012", Gate3Cameras.Norm(f.cameras[0].id));
            Assert.AreEqual(2.5f, Gate3Cameras.HeightAboveRoad("driver_eye"));
        }
    }
}
