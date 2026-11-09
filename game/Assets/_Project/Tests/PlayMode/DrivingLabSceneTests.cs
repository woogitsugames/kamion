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
            // Engine audio is wired to the physics when the generated library exists (gitignored WAVs).
            var audio = Object.FindAnyObjectByType<TruckAudioController>();
            Assert.IsNotNull(audio, "audio controller missing");
            if (TruckSim.Audio.VehicleAudioLibrary.LoadDefault() != null)
            {
                Assert.IsTrue(audio.HasAudio, "engine audio not started");
                Debug.Log($"[TEST] audio: {audio.Engine.ActiveEngineVoices} engine voices at {audio.Rpm:F0} rpm, interior blend {audio.InteriorBlend:F2}");
                Assert.Greater(audio.Engine.ActiveEngineVoices, 0, "idle loop voices playing");
            }
            else Debug.LogWarning("[TEST] VehicleAudioLibrary not generated - audio part skipped");
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
        /// Stage 2 end-to-end through the touch controls: Solo spawn → release P, R, arm the jaw, creep back under the
        /// parked trailer → coupled; raise the legs; drive off; stop, lower the legs, uncouple. 4× time scale.
        /// </summary>
        [UnityTest]
        public IEnumerator DrivingLab_CoupleAndUncouple_ThroughTouchControls()
        {
            Physics.simulationMode = SimulationMode.FixedUpdate;
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            var boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            var body = Object.FindAnyObjectByType<VehicleBody>();
            var trailer = Object.FindAnyObjectByType<TrailerBody>();
            var touch = boot.Touch;
            boot.Spawn(DrivingLabBootstrap.LabSpawn.Solo);
            yield return null;
            Time.timeScale = 4f;
            try
            {
                touch.RequestParkingToggle();
                touch.RequestSelector(Game.Controls.SelectorRequest.Reverse);
                touch.RequestCouplingToggle();
                yield return null;
                Assert.IsTrue(body.Combination.CouplingArmed, "jaw armed by the Siodło button");
                touch.ThrottleRaw = 0.16f; // shaped 0.16^1.6 ≈ 0.05: idle creep like the runner scenario
                double t0 = body.SimTime;
                while (!body.Coupled && body.SimTime - t0 < 20) yield return null;
                touch.ThrottleRaw = 0f; touch.BrakeRaw = 1f;
                Assert.IsTrue(body.Coupled, "coupled while reversing under the parked trailer");
                double tc = body.SimTime - t0;
                touch.RequestLandingGearToggle();
                t0 = body.SimTime;
                // Crank 10.4 s (0.52 m at 0.05 m/s), then the air suspension re-levels (τ 8 s): average 16..20 s like the runner.
                double kpSum = 0; int kpN = 0;
                while (body.SimTime - t0 < 20)
                {
                    yield return null;
                    if (body.SimTime - t0 > 16) { kpSum += body.Combination.FifthWheel.KingpinLoadLocal.y; kpN++; }
                }
                var tm = trailer.Model;
                Assert.IsFalse(tm.LandingGearDown, "legs commanded up");
                Assert.Less(tm.LandingGearLoad, 1.0, "legs off the ground");
                // Standstill on locked brakes is statically indeterminate (tire stick shares the nose load), so the
                // kingpin load is checked rolling, like the runner (couple_uncouple: 20-24 s while driving).
                double kpStand = kpSum / System.Math.Max(1, kpN) / body.Combination.StaticKingpinLoad;
                touch.BrakeRaw = 0f;
                touch.RequestSelector(Game.Controls.SelectorRequest.Drive);
                touch.ThrottleRaw = 0.55f;
                t0 = body.SimTime;
                kpSum = 0; kpN = 0;
                while (body.SimTime - t0 < 6)
                {
                    yield return null;
                    if (body.SimTime - t0 > 3) { kpSum += body.Combination.FifthWheel.KingpinLoadLocal.y; kpN++; }
                }
                double kp = kpSum / System.Math.Max(1, kpN) / body.Combination.StaticKingpinLoad;
                float v = body.SpeedKmh;
                touch.ThrottleRaw = 0f; touch.BrakeRaw = 1f;
                t0 = body.SimTime;
                while (body.SimTime - t0 < 4) yield return null;
                Assert.Greater(v, 3f, "combination drives off");
                bool refused = true;
                touch.RequestCouplingToggle(); // legs still up: must be refused
                yield return null;
                refused = body.Coupled;
                touch.RequestLandingGearToggle();
                t0 = body.SimTime;
                while (body.SimTime - t0 < 13) yield return null;
                touch.RequestCouplingToggle();
                yield return null;
                Debug.Log($"[TEST] touch coupling: coupled after {tc:F1} s of creep, kingpin load {kp:F2}× static rolling ({kpStand:F2}× at standstill on brakes), drive-off {v:F1} km/h, uncouple with legs up refused {refused}, legs load {tm.LandingGearLoad / 1000:F0} kN, uncoupled {!body.Coupled}");
                Assert.IsTrue(refused, "uncoupling refused with the legs up");
                Assert.IsFalse(body.Coupled, "uncoupled after lowering the legs");
                Assert.That(kp, Is.InRange(0.85, 1.15), "kingpin carries the static nose load");
            }
            finally { Time.timeScale = 1f; }
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
