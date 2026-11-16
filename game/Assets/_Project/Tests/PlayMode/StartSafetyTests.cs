using System.Collections;
using System.Text.RegularExpressions;
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
    /// ADR 0277 (review 0262 P2-2, P2-5): the start safety net through the real bootstrap in the DrivingLab scene with a
    /// synthetic route, synthetic region-edge closures and barrier cubes - the old-scene path (baked spawn point, no menu,
    /// no route_s), the search back towards the entry closure, no free place (the combination is NOT placed, the start
    /// menu says why) and the first physics step on the final pose.
    /// </summary>
    public class StartSafetyTests
    {
        const float Behind = StartClearance.BehindClosureM;

        /// <summary>Records the rigidbody state at the first FixedUpdate after <see cref="Arm"/>, before every other script
        /// (VehicleBody applies its forces later in the same step) and before the physics step itself.</summary>
        [DefaultExecutionOrder(-32000)]
        sealed class FirstStepProbe : MonoBehaviour
        {
            public bool armed, seen;
            public Vector3 position, velocity, angular;
            Rigidbody m_Rb;
            public void Arm() { m_Rb = GetComponent<Rigidbody>(); armed = true; seen = false; }
            void FixedUpdate()
            {
                if (!armed || seen) return;
                seen = true;
                position = m_Rb.position; velocity = m_Rb.linearVelocity; angular = m_Rb.angularVelocity;
            }
        }

        static WorldRoute MakeRoute()
        {
            // Straight route heading 45 deg (north-east) at y = 0, 300 m long, 10 m points (as RouteSpawnTests).
            var go = new GameObject("TestRoute");
            var r = go.AddComponent<WorldRoute>();
            int n = 31;
            r.points = new Vector3[n]; r.distances = new float[n]; r.speedLimitsKmh = new float[n];
            Vector3 dir = new Vector3(1f, 0f, 1f).normalized;
            for (int i = 0; i < n; i++) { r.points[i] = new Vector3(-500f, 0f, -500f) + dir * (10f * i); r.distances[i] = 10f * i; }
            return r;
        }

        /// <summary>Region-edge closures on the test route: entry row at route_s <paramref name="entryS"/> (road towards the edge =
        /// 225 deg, against the route), optional exit row at <paramref name="exitS"/> (45 deg, along the route).</summary>
        static WorldBoundary MakeBoundary(WorldRoute route, float entryS, float exitS = -1f)
        {
            var b = new GameObject("TestBoundary").AddComponent<WorldBoundary>();
            var entry = new WorldBoundary.Closure { localPos = route.points[Mathf.RoundToInt(entryS / 10f)], headingDeg = 225f, widthM = 7f, road = "t" };
            b.closures = exitS < 0f ? new[] { entry }
                : new[] { entry, new WorldBoundary.Closure { localPos = route.points[Mathf.RoundToInt(exitS / 10f)], headingDeg = 45f, widthM = 7f, road = "t" } };
            return b;
        }

        static GameObject Barrier(WorldRoute route, float s)
        {
            var block = GameObject.CreatePrimitive(PrimitiveType.Cube);
            block.name = "TestBarrier";
            block.transform.SetPositionAndRotation(route.PointAt(s) + Vector3.up * 0.4f, Quaternion.LookRotation(route.TangentAt(s)));
            block.transform.localScale = new Vector3(6f, 0.81f, 0.6f);   // concrete barrier element across the lane
            Physics.SyncTransforms();
            return block;
        }

        static Transform SpawnPointAt(WorldRoute route, float s)
        {
            var t = new GameObject("Spawn_DepotGate").transform;   // as WorldSceneBuilder bakes it
            t.SetPositionAndRotation(route.PointAt(s), Quaternion.LookRotation(route.TangentAt(s), Vector3.up));
            return t;
        }

        static float Along(Transform body, WorldRoute route, float s) => Vector3.Dot(body.position - route.PointAt(s), route.TangentAt(s));

        static IEnumerator LoadLab(System.Action<DrivingLabBootstrap, VehicleBody, TrailerBody, WorldRoute> ready)
        {
            Physics.simulationMode = SimulationMode.FixedUpdate;
            StartRequest.Consume(out _, out _);          // no menu request: the scene's own start
            StartRequest.ConsumeStartFailure();
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            var boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            var body = Object.FindAnyObjectByType<VehicleBody>();
            var trailer = Object.FindAnyObjectByType<TrailerBody>();
            var route = MakeRoute();
            boot.route = route;
            boot.Spawn(DrivingLabBootstrap.LabSpawn.Gross40t);
            yield return new WaitForFixedUpdate();
            ready(boot, body, trailer, route);
        }

        /// <summary>P2-5: a scene baked before ADR 0262 (spawn point at the old 12 m, outside the entry closure), started
        /// without the menu and without route_s, is repaired by the same path Awake uses; a free baked spawn stays.</summary>
        [UnityTest]
        public IEnumerator OldScene_NoMenuNoRouteS_BakedSpawnIsRepaired_AndAFreeOneStays()
        {
            DrivingLabBootstrap boot = null; VehicleBody body = null; WorldRoute route = null;
            yield return LoadLab((b, v, t, r) => { boot = b; body = v; route = r; });
            var boundary = MakeBoundary(route, 60f);

            boot.spawnPoint = SpawnPointAt(route, StartClearance.DefaultStartS);
            LogAssert.Expect(LogType.Warning, new Regex(@"\[START\] start moved along the route: route_s 12\.0 -> 85\.0 \(region-edge closure on the route\)"));
            Assert.IsTrue(boot.RestartFromSceneStart());
            yield return new WaitForFixedUpdate();
            Vector3 d = body.transform.position - route.PointAt(60f + Behind); d.y = 0f;
            Assert.Less(d.magnitude, 1.5f, "old 12 m spawn outside the closure at 60 m: the tractor must stand 25 m behind the row");
            Assert.IsTrue(body.Coupled);

            Object.Destroy(boot.spawnPoint.gameObject);
            boot.spawnPoint = SpawnPointAt(route, 120f);
            Assert.IsTrue(boot.RestartFromSceneStart());
            Assert.AreEqual(StartOutcome.Unchanged, boot.LastStart.outcome);
            yield return new WaitForFixedUpdate();
            Vector3 e = body.transform.position - boot.spawnPoint.position; e.y = 0f;
            Assert.Less(e.magnitude, 1.5f, "a free baked spawn point is used as it is");
            LogAssert.NoUnexpectedReceived();
            Object.Destroy(boundary.gameObject);
        }

        /// <summary>The first physics step after a (re)start already runs on the final pose: rigidbody at the resolved
        /// route point, zero velocities (pose set through the rigidbody before the step, not moved during the simulation).</summary>
        [UnityTest]
        public IEnumerator FirstFixedUpdate_RunsOnTheFinalPose_AtRest()
        {
            DrivingLabBootstrap boot = null; VehicleBody body = null; TrailerBody trailer = null; WorldRoute route = null;
            yield return LoadLab((b, v, t, r) => { boot = b; body = v; trailer = t; route = r; });
            var boundary = MakeBoundary(route, 60f);
            boot.spawnPoint = SpawnPointAt(route, StartClearance.DefaultStartS);
            var probe = body.gameObject.AddComponent<FirstStepProbe>();
            var trailerProbe = trailer.gameObject.AddComponent<FirstStepProbe>();
            yield return new WaitForFixedUpdate();

            LogAssert.Expect(LogType.Warning, new Regex(@"\[START\] start moved along the route: route_s 12\.0 -> 85\.0"));
            Assert.IsTrue(boot.RestartFromSceneStart());
            var rb = body.GetComponent<Rigidbody>();
            Vector3 placed = rb.position;
            Vector3 trailerPlaced = trailer.GetComponent<Rigidbody>().position;
            probe.Arm(); trailerProbe.Arm();
            yield return new WaitForFixedUpdate();

            Assert.IsTrue(probe.seen && trailerProbe.seen, "probes saw the first step");
            Assert.Less((probe.position - placed).magnitude, 1e-3f, "first FixedUpdate on the pose set by the spawn (no later teleport)");
            Assert.Less((trailerProbe.position - trailerPlaced).magnitude, 1e-3f, "trailer: first FixedUpdate on its spawn pose");
            Vector3 flat = probe.position - route.PointAt(60f + Behind); flat.y = 0f;
            Assert.Less(flat.magnitude, 1.5f, "the pose is the resolved start (85 m), not the baked 12 m");
            Assert.Less(probe.velocity.magnitude, 1e-3f); Assert.Less(probe.angular.magnitude, 1e-3f);
            Assert.Less(trailerProbe.velocity.magnitude, 1e-3f); Assert.Less(trailerProbe.angular.magnitude, 1e-3f);
            Object.Destroy(boundary.gameObject);
        }

        /// <summary>P2-2: nothing free ahead up to the exit-side zone end -> the search goes back towards the entry closure.</summary>
        [UnityTest]
        public IEnumerator BlockedAhead_StartMovesBack()
        {
            DrivingLabBootstrap boot = null; VehicleBody body = null; WorldRoute route = null;
            yield return LoadLab((b, v, t, r) => { boot = b; body = v; route = r; });
            var boundary = MakeBoundary(route, 60f, 240f);        // zone 85 .. 215 m
            var block = Barrier(route, 205f);                     // blocks every start from ~199 m to the zone end
            LogAssert.Expect(LogType.Warning, new Regex(@"\[START\] start moved along the route: route_s 200\.0 -> 198\.0 \(collider 'TestBarrier', searched back\)"));
            Assert.IsTrue(boot.SetRouteSpawn(200f));
            yield return new WaitForFixedUpdate();
            float front = Along(body.transform, route, 205f) + StartClearance.FrontM;
            Assert.Less(front, -0.3f - StartClearance.MarginM + 0.01f, "tractor front clear of the barrier face with the margin");
            Assert.AreEqual(198f, boot.LastStart.s, 1e-3f);
            Object.Destroy(block); Object.Destroy(boundary.gameObject);
        }

        /// <summary>P2-2: no free place on a respawn - the combination stays where it is (no start inside the barrier) and the HUD says why.</summary>
        [UnityTest]
        public IEnumerator NoFreePlace_Respawn_KeepsTheCombination()
        {
            DrivingLabBootstrap boot = null; VehicleBody body = null; WorldRoute route = null;
            yield return LoadLab((b, v, t, r) => { boot = b; body = v; route = r; });
            Assert.IsTrue(boot.SetRouteSpawn(150f));
            yield return new WaitForFixedUpdate();
            Vector3 before = body.transform.position;

            var boundary = MakeBoundary(route, 60f, 120f);        // zone 85 .. 95 m
            var block = Barrier(route, 90f);                      // every place of the zone touches it
            LogAssert.Expect(LogType.Error, new Regex(@"\[START\] no free place for the combination: route_s 90\.0, zone 85\.0-95\.0 m"));
            Assert.IsFalse(boot.SetRouteSpawn(90f));
            Assert.AreEqual(StartOutcome.NoSpace, boot.LastStart.outcome);
            yield return new WaitForFixedUpdate();
            Assert.IsTrue(body.gameObject.activeSelf, "a respawn failure keeps the driving combination");
            Vector3 d = body.transform.position - before; d.y = 0f;
            Assert.Less(d.magnitude, 0.5f, "not moved into the barrier");
            Assert.AreEqual(StartSafetyTexts.NoSpaceRespawn, boot.StatusText);
            Object.Destroy(block); Object.Destroy(boundary.gameObject);
        }

        /// <summary>P2-2: no free place at the scene start (old scene, no menu) - vehicle and trailer are switched off before
        /// any physics step inside the barrier, the game returns to the start menu and the menu shows the Polish notice once.</summary>
        [UnityTest]
        public IEnumerator NoFreePlace_SceneStart_DoesNotPlaceTheCombination_AndTheMenuSaysWhy()
        {
            DrivingLabBootstrap boot = null; VehicleBody body = null; TrailerBody trailer = null; WorldRoute route = null;
            yield return LoadLab((b, v, t, r) => { boot = b; body = v; trailer = t; route = r; });
            var boundary = MakeBoundary(route, 60f, 120f);        // zone 85 .. 95 m
            var block = Barrier(route, 90f);
            boot.spawnPoint = SpawnPointAt(route, 90f);
            LogAssert.Expect(LogType.Error, new Regex(@"\[START\] no free place for the combination: route_s 90\.0"));
            Assert.IsFalse(boot.RestartFromSceneStart());
            Assert.IsTrue(boot.StartFailed);
            Assert.IsFalse(body.gameObject.activeSelf, "tractor switched off: no physics step inside the barrier");
            Assert.IsFalse(trailer.gameObject.activeSelf, "trailer switched off");
            Assert.IsFalse(boot.enabled);
            Assert.AreEqual(StartSafetyTexts.NoSpaceMessage, StartRequest.StartFailure);

            for (int i = 0; i < 30 && SceneManager.GetActiveScene().name != StartSafetyTexts.MenuScene; i++) yield return null;
            Assert.AreEqual(StartSafetyTexts.MenuScene, SceneManager.GetActiveScene().name, "back to the start menu");
            yield return null;
            var menu = Object.FindAnyObjectByType<GameBootstrap>().Menu;
            Assert.AreEqual(StartSafetyTexts.NoSpaceMessage, menu.NoticeText, "the menu says why");
            Assert.AreEqual("", StartRequest.StartFailure, "shown once");
            Assert.IsTrue(block == null && boundary == null, "the lab scene with its test objects is gone");
        }
    }
}
