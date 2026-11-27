using System.Collections;
using Game.Cameras;
using Game.Gameplay;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Game.Tests
{
    public class CabMechanismsPlayModeTests
    {
        [UnityTest]
        public IEnumerator DrivingLab_WiperEventsShareTheVisualClock_AndAllocateNothing()
        {
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            var audio = Object.FindAnyObjectByType<TruckAudioController>();
            Assert.IsNotNull(audio);
            Assert.IsTrue(audio.HasAudio);
            audio.enabled = false; // explicit update order below, without rendered-frame timing jitter
            var drive = audio.vehicle.Wipers;
            int wetness = Shader.PropertyToID("_KamionWet");
            Vector4 saved = Shader.GetGlobalVector(wetness);
            try
            {
                audio.rig.SetMode(CameraMode.Cab);
                Shader.SetGlobalVector(wetness, Vector4.zero);
                drive.CycleMode();
                drive.Step(0.01f);
                audio.AudioStep(0.2f);
                Assert.AreEqual("wiper_dry_cab", audio.LastWiperSweep?.name);
                string dryClip = audio.LastWiperSweep.name;
                Assert.AreEqual(1, audio.WiperSweepEvents);
                Assert.AreEqual(0, audio.WiperParkEvents);
                drive.Step(WiperDrive.SlowSeconds);
                audio.AudioStep(0.01f);
                Assert.AreEqual(0f, drive.Phase);
                Assert.AreEqual(1, audio.WiperParkEvents);

                Shader.SetGlobalVector(wetness, Vector4.one);
                audio.rig.SetMode(CameraMode.Chase);
                drive.CycleMode(); // slow
                drive.CycleMode(); // fast
                drive.Step(0.01f);
                audio.AudioStep(0.2f);
                Assert.AreEqual("wiper_wet", audio.LastWiperSweep?.name);
                Assert.AreEqual(1.5f, audio.WiperPlaybackPitch, 0.001f);

                long before = System.GC.GetAllocatedBytesForCurrentThread();
                for (int i = 0; i < 300; i++)
                {
                    drive.Step(0.01f);
                    audio.AudioStep(0.01f);
                }
                long bytes = System.GC.GetAllocatedBytesForCurrentThread() - before;
                Assert.AreEqual(0L, bytes);
                Assert.AreEqual(drive.Starts, audio.WiperSweepEvents);
                Assert.AreEqual(drive.Parks, audio.WiperParkEvents);
                Assert.AreEqual(0, audio.BrakeSquealEvents, "parked truck");
                Debug.Log($"[CAB_MECH] DrivingLab dry={dryClip} wet={audio.LastWiperSweep.name} fastPitch={audio.WiperPlaybackPitch:F2} starts={drive.Starts} parks={drive.Parks} GC={bytes} B/300 updates");
            }
            finally
            {
                Shader.SetGlobalVector(wetness, saved);
                while (drive.Mode != WiperMode.Off) drive.CycleMode();
                drive.Step(WiperDrive.SlowSeconds);
                audio.enabled = true;
            }
        }

        [UnityTest]
        public IEnumerator DrivingLab_ServiceBrakePlaysSporadicallyInBothPerspectives()
        {
            SceneManager.LoadScene(DrivingLabLayout.SceneName, LoadSceneMode.Single);
            yield return null;
            var boot = Object.FindAnyObjectByType<DrivingLabBootstrap>();
            var audio = Object.FindAnyObjectByType<TruckAudioController>();
            Assert.IsNotNull(audio);
            Assert.IsTrue(audio.HasAudio);
            boot.SpawnAt(DrivingLabBootstrap.LabSpawn.Solo, DrivingLabLayout.Spawn, Quaternion.identity);
            var body = audio.vehicle;
            var previousSimulation = Physics.simulationMode;
            Physics.simulationMode = SimulationMode.Script;
            try
            {
                body.SetMoving(10f / 3.6f, 0);
                const int applications = 64;
                foreach (var camera in new[] { CameraMode.Cab, CameraMode.Chase })
                {
                    audio.rig.SetMode(camera);
                    int before = audio.BrakeSquealEvents;
                    float minPressure = 1f, maxPressure = 0f;
                    long bytes = 0;
                    for (int i = 0; i < applications; i++)
                    {
                        var input = body.Input;
                        input.ParkingBrake = false;
                        input.Brake = 0f;
                        body.Input = input;
                        body.Tick(0.01f);
                        audio.AudioStep(3.1f); // independent application after the audio cooldown
                        input.Brake = 0.55f;
                        body.Input = input;
                        int start = audio.BrakeSquealEvents;
                        for (int j = 0; j < 65; j++)
                        {
                            // Controlled speed on the lab surface; chamber pressure and wheel contacts come from the solver.
                            body.Body.linearVelocity = body.transform.forward * (10f / 3.6f);
                            body.Tick(0.01f);
                            Physics.Simulate(0.01f);
                            int previous = audio.BrakeSquealEvents;
                            long gcBefore = System.GC.GetAllocatedBytesForCurrentThread();
                            audio.AudioStep(0.01f);
                            bytes += System.GC.GetAllocatedBytesForCurrentThread() - gcBefore;
                            if (previous == audio.BrakeSquealEvents) continue;
                            float pressure = 0f;
                            foreach (var wheel in body.Model.Wheels)
                                if (wheel.Contact) pressure = Mathf.Max(pressure, (float)wheel.BrakePressure);
                            minPressure = Mathf.Min(minPressure, pressure);
                            maxPressure = Mathf.Max(maxPressure, pressure);
                        }
                        Assert.LessOrEqual(audio.BrakeSquealEvents - start, 1);
                    }
                    int played = audio.BrakeSquealEvents - before;
                    Assert.That(played, Is.InRange(1, applications - 1));
                    Assert.AreEqual(0L, bytes);
                    string expected = camera == CameraMode.Cab ? "brake_service_squeal_cab" : "brake_service_squeal";
                    Assert.AreEqual(expected, audio.LastBrakeSqueal?.name);
                    Debug.Log($"[CAB_MECH] DrivingLab service brake speed=10 km/h pedal=0.55 view={camera} events={played}/{applications} pressure={minPressure:F3}–{maxPressure:F3} clip={audio.LastBrakeSqueal.name} GC={bytes} B/{applications * 65} updates");
                }
            }
            finally { Physics.simulationMode = previousSimulation; }
        }
    }
}
