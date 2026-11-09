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
