using System.Collections;
using Game.Gameplay;
using Game.UI.Driving;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Game.Tests
{
    public class DrivingLabSceneTests
    {
        [UnityTest]
        public IEnumerator DrivingLab_Loads_TruckParkedAndStable()
        {
            Physics.simulationMode = SimulationMode.FixedUpdate;
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            var body = Object.FindAnyObjectByType<VehicleBody>();
            Assert.IsNotNull(body, "VehicleBody missing");
            Assert.IsTrue(body.Initialized, "vehicle not initialised");
            Assert.IsNotNull(Object.FindAnyObjectByType<DrivingHud>(), "HUD missing");
            Assert.IsNotNull(Object.FindAnyObjectByType<DrivingLabBootstrap>(), "bootstrap missing");
            Assert.AreEqual(0.01f, Time.fixedDeltaTime, 1e-6f, "fixed step must be 100 Hz");
            Vector3 p0 = body.transform.position;
            float end = Time.realtimeSinceStartup + 3f;
            while (Time.realtimeSinceStartup < end) yield return null;
            float drift = (body.transform.position - p0).magnitude;
            Debug.Log($"[TEST] DrivingLab: {body.StepCount} steps, drift {drift * 1000f:F1} mm, step {body.AverageStepMicros:F0} µs");
            Assert.Greater(body.StepCount, 50, "physics must be stepping");
            Assert.Less(drift, 0.05f, "parked truck must stay at the spawn");
            foreach (var w in body.Model.Wheels) Assert.IsTrue(w.Contact, w.Name + " has no ground contact");
        }

        /// <summary>Stage 2: every lab spawn preset puts the combination at rest (coupled presets: kingpin in the jaw).</summary>
        [UnityTest]
        public IEnumerator DrivingLab_SpawnPresets_CombinationAtRest()
        {
            Physics.simulationMode = SimulationMode.FixedUpdate;
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            var boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            var body = Object.FindAnyObjectByType<VehicleBody>();
            var trailer = Object.FindAnyObjectByType<TrailerBody>();
            Assert.IsNotNull(trailer, "trailer missing in DrivingLab");
            foreach (var preset in new[] { DrivingLabBootstrap.LabSpawn.Gross40t, DrivingLabBootstrap.LabSpawn.Cargo24t, DrivingLabBootstrap.LabSpawn.Empty, DrivingLabBootstrap.LabSpawn.Solo })
            {
                boot.Spawn(preset);
                yield return new WaitForFixedUpdate();
                Vector3 a0 = body.transform.position, b0 = trailer.transform.position;
                float end = Time.realtimeSinceStartup + 2f;
                while (Time.realtimeSinceStartup < end) yield return null;
                float da = (body.transform.position - a0).magnitude, db = (trailer.transform.position - b0).magnitude;
                var fw = body.Combination.FifthWheel;
                Debug.Log($"[TEST] spawn {preset}: coupled {body.Coupled}, mass {body.Model.TotalMass / 1000:F1} t, drift tractor {da * 1000:F1} mm trailer {db * 1000:F1} mm, kingpin err {fw.PositionError * 1000:F2} mm, legs {trailer.Model.LandingGearLoad / 1000:F0} kN");
                Assert.AreEqual(preset != DrivingLabBootstrap.LabSpawn.Solo, body.Coupled, "coupling state");
                Assert.Less(da, 0.05f, "tractor at rest");
                Assert.Less(db, 0.05f, "trailer at rest");
                if (body.Coupled) Assert.Less(fw.PositionError, 0.005, "kingpin in the jaw");
                else Assert.Greater(trailer.Model.LandingGearLoad, 10000, "parked trailer stands on its legs");
            }
        }

        /// <summary>
        /// End-to-end: input bridge → autopilot → vehicle on the scene's R50 circle (the device-measurement path),
        /// plus telemetry CSV recording. 4× time scale, ~24 s of simulation.
        /// </summary>
        [UnityTest]
        public IEnumerator DrivingLab_Autopilot_FollowsR50Circle_AndRecordsCsv()
        {
            Physics.simulationMode = SimulationMode.FixedUpdate;
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            var boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            var body = Object.FindAnyObjectByType<VehicleBody>();
            boot.StartAutopilot("circle50", "40");
            var rec = body.GetComponent<VehicleTelemetryRecorder>();
            rec.StartRecording();
            string file = rec.CurrentFile;
            Time.timeScale = 4f;
            try
            {
                float maxRadiusErr = 0f, speed = 0f;
                float end = Time.realtimeSinceStartup + 7f;
                while (Time.realtimeSinceStartup < end)
                {
                    yield return null;
                    if (body.SimTime > 15)
                    {
                        Vector3 d = body.transform.position - DrivingLabLayout.CircleR50Center; d.y = 0;
                        maxRadiusErr = Mathf.Max(maxRadiusErr, Mathf.Abs(d.magnitude - DrivingLabLayout.CircleR50));
                        speed = body.SpeedKmh;
                    }
                }
                rec.StopRecording();
                var lines = System.IO.File.ReadAllLines(file);
                Debug.Log($"[TEST] autopilot R50: sim {body.SimTime:F1} s, speed {speed:F1} km/h, max radius error after 15 s {maxRadiusErr:F2} m, CSV rows {lines.Length - 1} → {file}");
                Assert.Greater(body.SimTime, 18.0, "not enough simulation time");
                Assert.AreEqual(40f, speed, 4f, "autopilot holds 40 km/h");
                Assert.Less(maxRadiusErr, 2.0f, "follows the painted R50 circle");
                Assert.Greater(lines.Length, 1000, "CSV rows at 100 Hz");
                StringAssert.StartsWith("t,x,y,z,speed_kmh", lines[0]);
            }
            finally { Time.timeScale = 1f; }
        }

        [UnityTearDown]
        public IEnumerator UnloadLab()
        {
            // Leave an empty scene so later fixtures do not raycast against the pad.
            var lab = SceneManager.GetSceneByName(DrivingLabLayout.SceneName);
            if (!lab.IsValid() || !lab.isLoaded) yield break;
            var empty = SceneManager.CreateScene("Empty_" + Time.frameCount);
            SceneManager.SetActiveScene(empty);
            yield return SceneManager.UnloadSceneAsync(lab);
        }
    }
}
