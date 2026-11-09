using System.Collections;
using Game.Gameplay;
using Game.Telemetry;
using Game.UI;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Game.Tests
{
    public class BootSceneTests
    {
        [UnityTest]
        public IEnumerator Boot_StartsDiagnostics_WithoutErrors()
        {
            SceneManager.LoadScene("Boot", LoadSceneMode.Single);
            yield return null;
            Assert.IsNotNull(Object.FindAnyObjectByType<GameBootstrap>(), "GameBootstrap missing");
            var sampler = Object.FindAnyObjectByType<DiagnosticsSampler>();
            Assert.IsNotNull(sampler, "DiagnosticsSampler missing");
            Assert.IsNotNull(Object.FindAnyObjectByType<DiagnosticsOverlay>(), "DiagnosticsOverlay missing");

            float end = Time.realtimeSinceStartup + 2f;
            while (Time.realtimeSinceStartup < end) yield return null;

            var snap = sampler.Snapshot;
            Assert.Greater(snap.Frames.Samples, 10, "frame samples");
            Assert.Greater(snap.Frames.P50Ms, 0f);
            // Error/exception logs during the run fail the test automatically (Unity Test Framework).
        }
    }
}
