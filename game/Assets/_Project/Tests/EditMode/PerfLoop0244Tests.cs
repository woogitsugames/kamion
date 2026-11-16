using System.Globalization;
using System.Linq;
using Game.Rendering;
using Game.Telemetry;
using NUnit.Framework;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0244 (driving-loop GC audit): the safe fixes keep their behaviour and do not allocate.
    /// GC is counted with <see cref="GcAllocCounter"/> (Recorder "GC.Alloc"; GC.GetAllocatedBytesForCurrentThread is 0
    /// under Mono in the editor). The bulk parity of the CSV formatter runs on .NET in tools/loop-runner.
    /// </summary>
    public class PerfLoop0244Tests
    {
        static readonly CultureInfo Ci = CultureInfo.InvariantCulture;

        static string Row(long frame, float t, float ms, float cpu, float gpu, float scale, int mirrors, int ab)
        {
            var buf = new char[FrameCsvFormat.MaxRowChars];
            int n = FrameCsvFormat.AppendRow(buf, 0, frame, t, ms, cpu, gpu, scale, mirrors, ab);
            return new string(buf, 0, n);
        }

        /// <summary>Values with at most 7 significant digits and no binary tie: identical to the former ToString row on any runtime.</summary>
        [Test]
        public void FrameCsvRow_MatchesFormerToStringColumns_PlusMirrorAndAb()
        {
            float t = 12.3456f, ms = 33.333f, cpu = 21.5f, gpu = 18.125f, scale = 0.85f;
            string former = 1234.ToString(Ci) + "," + t.ToString("F4", Ci) + "," + ms.ToString("F3", Ci) + "," + cpu.ToString("F3", Ci)
                            + "," + gpu.ToString("F3", Ci) + "," + scale.ToString("F2", Ci);
            Assert.AreEqual(former + ",2,\n", Row(1234, t, ms, cpu, gpu, scale, 2, -1), "A/B off: empty ab column");
            Assert.AreEqual(former + ",0,1\n", Row(1234, t, ms, cpu, gpu, scale, 0, 1));
            Assert.AreEqual("frame,t_s,frame_ms,cpu_main_ms,gpu_ms,render_scale,mirror_n,ab", FrameCsvFormat.Header);
        }

        [Test]
        public void FrameCsvRow_ZeroGcAlloc()
        {
            var buf = new char[FrameCsvFormat.MaxRowChars * 128];
            void Fill()
            {
                int pos = 0;
                for (int i = 0; i < 128; i++)
                    pos = FrameCsvFormat.AppendRow(buf, pos, 5000 + i, 100.25f + i * 0.033f, 33.4f, 20.1f, 17.9f, 0.8f, 1, 0);
            }
            GcAllocCounter.AssertZero(Fill, Fill, 0, "frametimes.csv rows must not allocate (ADR 0244)");
        }

        [Test]
        public void CabRegistry_TracksEnableAndDisable()
        {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var go = new GameObject("cab 0244");
            try
            {
                var cab = go.AddComponent<CabInteriorLighting>();
                Assert.IsTrue(CabInteriorLighting.Enabled.Contains(cab), "OnEnable (ExecuteAlways) registers");
                cab.enabled = false;
                Assert.IsFalse(CabInteriorLighting.Enabled.Contains(cab), "OnDisable unregisters");
                cab.enabled = true;
                go.SetActive(false);
                Assert.IsFalse(CabInteriorLighting.Enabled.Contains(cab), "inactive GameObject unregisters");
                go.SetActive(true);
                Assert.AreEqual(1, CabInteriorLighting.Enabled.Count(c => c == cab), "registered once");
            }
            finally { Object.DestroyImmediate(go); }
            Assert.IsFalse(CabInteriorLighting.Enabled.Any(c => c == null), "destroyed cab removed");
        }

        /// <summary>Edit mode (visual QA calls Refresh per control camera) keeps searching on every call, as before ADR 0244.</summary>
        [Test]
        public void CabEnvironmentFallback_EditModeSearchesEveryCall()
        {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var go = new GameObject("cab 0244 env");
            try
            {
                var cab = go.AddComponent<CabInteriorLighting>();
                int before = cab.EnvironmentSearches;
                cab.Refresh(null);
                cab.Refresh(null);
                cab.Refresh(null);
                Assert.AreEqual(before + 3, cab.EnvironmentSearches);
            }
            finally { Object.DestroyImmediate(go); }
        }
    }
}
