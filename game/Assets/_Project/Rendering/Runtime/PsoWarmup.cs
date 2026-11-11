using System;
using System.Collections.Generic;
using System.Globalization;
using Unity.Jobs;
using Unity.Profiling;
using Unity.Profiling.LowLevel.Unsafe;
using UnityEngine;
using UnityEngine.Experimental.Rendering;

namespace Game.Rendering
{
    /// <summary>
    /// ADR 0113: graphics pipeline (PSO) warm-up and frame-spike diagnostics for the phone.
    /// <para>Warm-up: every <see cref="GraphicsStateCollection"/> under Resources/Pso recorded on the same graphics API and
    /// quality level is warmed (Vulkan pipelines created on worker threads) while the Boot / WorldC scenes load, so the first
    /// frames of a drive do not stall on vkCreateGraphicsPipelines (A16 Low: 14 of 27 frames > 40 ms of G3-A were in the first
    /// 5 s after the 25 s load; ADR 0106). Launch argument <c>pso_warm 0</c> skips it (A/B in one APK).</para>
    /// <para>Trace: <c>pso_trace &lt;s&gt;</c> records every graphics state used during the first s seconds and saves it to
    /// persistentDataPath/pso_&lt;api&gt;_&lt;quality&gt;_&lt;tag&gt;.graphicsstate (<c>pso_tag</c>); pull it with adb into
    /// Assets/_Project/Rendering/Resources/Pso/ (scripts in artifacts/perf-low-r2).</para>
    /// <para>Spikes: <c>spike_probe 1</c> logs <c>[SPIKE]</c> for every frame &gt; 40 ms after 20 s: delta time, GC count and,
    /// in a development build, the slowest profiler markers of that frame (all available markers are recorded).</para>
    /// </summary>
    public static class PsoWarmup
    {
        static bool s_Started;

        /// <summary>Called once from RenderOverrides.Parse (GameBootstrap.Awake) with the launch-argument getter.</summary>
        public static void Init(Func<string, string> arg)
        {
            if (s_Started || !Application.isPlaying || Application.isEditor || arg == null) return;
            s_Started = true;
            var go = new GameObject("PsoWarmup") { hideFlags = HideFlags.HideAndDontSave };
            UnityEngine.Object.DontDestroyOnLoad(go);
            var r = go.AddComponent<Runner>();
            float.TryParse(arg("pso_trace"), NumberStyles.Float, CultureInfo.InvariantCulture, out r.traceS);
            r.traceTag = string.IsNullOrEmpty(arg("pso_tag")) ? "run" : arg("pso_tag");
            r.warm = arg("pso_warm") != "0" && r.traceS <= 0f;
            r.spikes = arg("spike_probe") == "1";
        }

        sealed class Runner : MonoBehaviour
        {
            public float traceS;
            public string traceTag;
            public bool warm, spikes;
            GraphicsStateCollection m_Trace;
            readonly List<(GraphicsStateCollection c, JobHandle h, float t0)> m_Warm = new List<(GraphicsStateCollection, JobHandle, float)>();
            // spike probe
            ProfilerRecorder[] m_Rec;
            string[] m_RecName;
            int m_Gc;
            float m_ProbeFrom = 20f;
            readonly List<(long ns, int i)> m_Top = new List<(long, int)>(64);

            void Start()
            {
                string q = QualitySettings.names[QualitySettings.GetQualityLevel()];
                if (traceS > 0f)
                {
                    m_Trace = new GraphicsStateCollection();
                    bool ok = m_Trace.BeginTrace();
                    Debug.Log($"[PSO] trace start ok={ok} dev={Debug.isDebugBuild} ({traceS:F0} s) api={SystemInfo.graphicsDeviceType} quality={q} tag={traceTag}");
                }
                if (warm)
                {
                    var all = Resources.LoadAll<GraphicsStateCollection>("Pso");
                    int n = 0;
                    foreach (var c in all)
                    {
                        if (c == null) continue;
                        bool match = c.graphicsDeviceType == SystemInfo.graphicsDeviceType &&
                                     (string.IsNullOrEmpty(c.qualityLevelName) || c.qualityLevelName == q);
                        Debug.Log($"[PSO] collection {c.name} api={c.graphicsDeviceType} quality={c.qualityLevelName} variants={c.variantCount} " +
                                  $"states={c.totalGraphicsStateCount} match={match}");
                        if (!match) continue;
                        m_Warm.Add((c, c.WarmUp(), Time.realtimeSinceStartup));
                        n++;
                    }
                    Debug.Log($"[PSO] warm-up started: {n} of {all.Length} collections (api={SystemInfo.graphicsDeviceType} quality={q})");
                }
                else Debug.Log("[PSO] warm-up off (pso_warm 0 or tracing)");
                m_Gc = GC.CollectionCount(0);
            }

            void Update()
            {
                float now = Time.realtimeSinceStartup;
                for (int k = m_Warm.Count - 1; k >= 0; k--)
                {
                    var w = m_Warm[k];
                    if (!w.h.IsCompleted) continue;
                    w.h.Complete();
                    Debug.Log($"[PSO] warm-up done {w.c.name}: {w.c.completedWarmupCount}/{w.c.totalGraphicsStateCount} states in {now - w.t0:F2} s (t={now:F1})");
                    m_Warm.RemoveAt(k);
                }
                if (m_Trace != null && now >= traceS)
                {
                    m_Trace.EndTrace();
                    string q = QualitySettings.names[QualitySettings.GetQualityLevel()];
                    string path = System.IO.Path.Combine(Application.persistentDataPath, $"pso_{SystemInfo.graphicsDeviceType}_{q}_{traceTag}.graphicsstate");
                    bool ok = m_Trace.SaveToFile(path);
                    Debug.Log($"[PSO] trace saved={ok} {path} variants={m_Trace.variantCount} states={m_Trace.totalGraphicsStateCount} t={now:F1}");
                    m_Trace = null;
                }
                if (spikes) Probe(now);
            }

            void Probe(float now)
            {
                if (now < m_ProbeFrom) return;
                if (m_Rec == null) { StartRecorders(); return; }
                float dt = Time.unscaledDeltaTime * 1000f;
                int gc = GC.CollectionCount(0);
                bool gcHit = gc != m_Gc;
                m_Gc = gc;
                if (dt < 40f && !gcHit) return;
                m_Top.Clear();
                for (int i = 0; i < m_Rec.Length; i++)
                {
                    if (!m_Rec[i].Valid) continue;
                    long v = m_Rec[i].LastValue;
                    if (v >= 1500000) m_Top.Add((v, i));
                }
                m_Top.Sort((a, b) => b.ns.CompareTo(a.ns));
                var sb = new System.Text.StringBuilder(512);
                for (int j = 0; j < m_Top.Count && j < 24; j++)
                    sb.Append(' ').Append(m_RecName[m_Top[j].i]).Append('=').Append((m_Top[j].ns * 1e-6).ToString("F1", CultureInfo.InvariantCulture));
                var cam = ViewCameraResolver.Resolve(null);
                Vector3 p = cam != null ? cam.transform.position : Vector3.zero;
                Debug.Log(string.Format(CultureInfo.InvariantCulture, "[SPIKE] t={0:F2} frame={1} dt={2:F1} gc={3} pos=({4:F0},{5:F0},{6:F0}) markers:{7}",
                    now, Time.frameCount, dt, gcHit ? 1 : 0, p.x, p.y, p.z, sb));
            }

            void StartRecorders()
            {
                var handles = new List<ProfilerRecorderHandle>();
                ProfilerRecorderHandle.GetAvailable(handles);
                var rec = new List<ProfilerRecorder>();
                var names = new List<string>();
                foreach (var h in handles)
                {
                    var d = ProfilerRecorderHandle.GetDescription(h);
                    if (d.UnitType != ProfilerMarkerDataUnit.TimeNanoseconds) continue;
                    string cat = d.Category.Name;
                    if (cat == "GPU" || cat == "Profiler") continue;
                    var r = new ProfilerRecorder(h, 1, ProfilerRecorderOptions.Default);
                    if (!r.Valid) { r.Dispose(); continue; }
                    if (!r.IsRunning) r.Start();
                    rec.Add(r);
                    names.Add(cat + ":" + d.Name.Replace(' ', '_'));
                }
                m_Rec = rec.ToArray();
                m_RecName = names.ToArray();
                Debug.Log($"[SPIKE] probe on: {m_Rec.Length} time markers of {handles.Count} (development build: markers; release: counters only)");
            }

            void OnDestroy()
            {
                if (m_Rec != null) foreach (var r in m_Rec) r.Dispose();
            }
        }
    }
}
