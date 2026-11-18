using System.Collections;
using Game.Rendering;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0244: without an enabled EnvironmentLighting (DrivingLab has no sky rig) CabInteriorLighting.LateUpdate ran a
    /// FindAnyObjectByType scene search every frame. In play mode it is throttled to one search per
    /// <see cref="CabInteriorLighting.EnvironmentSearchIntervalS"/>, and a found environment is used at once.
    /// </summary>
    public class CabEnvironmentThrottleTests
    {
        GameObject m_Cab, m_Env;

        [TearDown]
        public void TearDown()
        {
            if (m_Cab != null) Object.Destroy(m_Cab);
            if (m_Env != null) Object.Destroy(m_Env);
        }

        [UnityTest]
        public IEnumerator NoEnvironment_SearchesAtMostOncePerInterval()
        {
            if (EnvironmentLighting.Instance != null) Assert.Ignore("an EnvironmentLighting is enabled in the test scene");
            m_Cab = new GameObject("cab 0244 throttle");
            var cab = m_Cab.AddComponent<CabInteriorLighting>();
            float t0 = Time.unscaledTime;
            int frames = 0;
            while (frames < 30 || Time.unscaledTime - t0 < 0.5f) { frames++; yield return null; }
            float elapsed = Time.unscaledTime - t0;
            int allowed = Mathf.FloorToInt(elapsed / CabInteriorLighting.EnvironmentSearchIntervalS) + 1;
            Assert.LessOrEqual(cab.EnvironmentSearches, allowed, $"{cab.EnvironmentSearches} searches in {frames} frames / {elapsed:F2} s");
            Assert.GreaterOrEqual(cab.EnvironmentSearches, 1, "the first frame still searches");
        }

        [UnityTest]
        public IEnumerator DisabledEnvironmentFoundOnce_IsKeptWithoutFurtherSearches()
        {
            if (EnvironmentLighting.Instance != null) Assert.Ignore("an EnvironmentLighting is enabled in the test scene");
            m_Env = new GameObject("env 0244 (disabled component)");
            var env = m_Env.AddComponent<EnvironmentLighting>();
            env.enabled = false;   // Instance stays null; FindAnyObjectByType still returns it (pre-0244 fallback)
            m_Cab = new GameObject("cab 0244 keep");
            var cab = m_Cab.AddComponent<CabInteriorLighting>();
            for (int i = 0; i < 10; i++) yield return null;
            Assert.IsNull(EnvironmentLighting.Instance);
            Assert.AreEqual(1, cab.EnvironmentSearches, "found once, then kept while alive");
        }
    }
}
