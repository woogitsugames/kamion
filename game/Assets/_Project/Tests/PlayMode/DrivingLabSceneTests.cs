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
