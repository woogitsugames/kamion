using System;
using System.Globalization;
using System.IO;
using System.Text;
using Unity.Profiling;
using UnityEngine;
using UnityEngine.Profiling;
using UnityEngine.SceneManagement;

namespace Game.Telemetry
{
    /// <summary>
    /// PC (Windows player) measurement run, ADR 0266 — the desktop counterpart of the Boot diagnostics +
    /// scripts/device-metrics.ps1. Off unless the player is started with <c>-metrics &lt;dir&gt;</c> (see
    /// <see cref="PcMetricsOptions.Parse"/>); starts itself after the first scene load, so no scene or bootstrap change is needed.
    ///
    /// Per frame (allocation-free, preallocated arrays): unscaled frame time, CPU main / GPU time from FrameTimingManager,
    /// render counters (draw calls, batches, SetPass calls, triangles; -1 if the counter is not available in this player),
    /// GC collection count and the index of the scene. Every 0.5 s: Unity allocated / reserved memory, Mono used / heap,
    /// graphics-driver memory (development players only, else -1). Region load time: from the frame that started a
    /// single-mode scene load (or <see cref="MarkRegionLoadStart"/>) to the end of the first frame of the new scene.
    /// Everything is written once, at the end: frames.csv, memory.csv, run.json (format "kamion/pc-metrics/1"),
    /// parsed by tools/pcperf/pc_metrics.py. Process RAM / VRAM come from Windows counters in scripts/pc-metrics.ps1.
    /// </summary>
    public sealed class PcFrameMetricsRecorder : MonoBehaviour
    {
        public const string Format = "kamion/pc-metrics/1";
        public const string FramesHeader = "frame,t_s,frame_ms,cpu_main_ms,gpu_ms,draw_calls,batches,setpass,tris,gc_count,scene";
        public const string MemoryHeader = "t_s,allocated_mb,reserved_mb,mono_used_mb,mono_heap_mb,gfx_driver_mb,gc_count";
        const float MemoryInterval = 0.5f;
        const int MaxLoads = 32;

        static PcFrameMetricsRecorder s_Instance;
        static double s_MarkedLoadStart = -1;
        static double s_DrivingReady = -1;

        PcMetricsOptions m_Opt;
        bool m_Recording, m_Done;
        double m_RecStart;          // realtimeSinceStartupAsDouble at the start of the window
        double m_LastUpdate;        // time of the latest Update (start-of-frame approximation for an unmarked load)
        double m_NextMemory;
        int m_FocusLost;
        string m_EndReason = "running";
        int m_SceneIndex;
        int m_GcAtStart;

        // Frame buffer (preallocated).
        int m_Count, m_Dropped;
        long[] m_Frame;
        float[] m_T, m_Ms, m_Cpu, m_Gpu;
        int[] m_Draws, m_Batches, m_SetPass, m_Gc;
        long[] m_Tris;
        byte[] m_Scene;
        readonly FrameTiming[] m_Timing = new FrameTiming[1];
        ProfilerRecorder m_RecDraws, m_RecBatches, m_RecSetPass, m_RecTris;

        // Memory samples (preallocated).
        int m_MemCount;
        float[] m_MemT, m_MemAlloc, m_MemReserved, m_MemMono, m_MemMonoHeap, m_MemGfx;
        int[] m_MemGc;

        // Region loads.
        readonly LoadRecord[] m_Loads = new LoadRecord[MaxLoads];
        int m_LoadCount;
        int m_PendingLoad = -1;     // index of a load waiting for its first frame
        int m_PendingFrames;        // frames seen since the pending load

        [Serializable]
        public sealed class LoadRecord
        {
            public string scene;
            public double loadStart_s;
            public double firstFrameEnd_s;
            public double seconds;
            public string startSource;
        }

        /// <summary>Optional precise hook: call right before SceneManager.LoadScene of a region (e.g. in GameBootstrap / BootMenu).
        /// Without it the start of the frame that requested the load is used (error ≤ 1 frame).</summary>
        public static void MarkRegionLoadStart() => s_MarkedLoadStart = Time.realtimeSinceStartupAsDouble;

        /// <summary>Optional hook: the truck is spawned and drivable (e.g. DrivingLabBootstrap after spawn). Written to run.json.</summary>
        public static void MarkDrivingReady() { if (s_DrivingReady < 0) s_DrivingReady = Time.realtimeSinceStartupAsDouble; }

        public static bool Active => s_Instance != null;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void AutoStart()
        {
            if (s_Instance != null) return;
            var opt = PcMetricsOptions.Parse(Environment.GetCommandLineArgs());
            if (!opt.Enabled) return;
            var go = new GameObject("PcFrameMetricsRecorder");
            DontDestroyOnLoad(go);
            go.AddComponent<PcFrameMetricsRecorder>().Configure(opt);
        }

        void Configure(PcMetricsOptions opt)
        {
            s_Instance = this;
            m_Opt = opt;
            int cap = PcMetricsMath.FrameCapacity(opt.Seconds + 1f, opt.MaxFps);
            m_Frame = new long[cap];
            m_T = new float[cap]; m_Ms = new float[cap]; m_Cpu = new float[cap]; m_Gpu = new float[cap];
            m_Draws = new int[cap]; m_Batches = new int[cap]; m_SetPass = new int[cap]; m_Gc = new int[cap];
            m_Tris = new long[cap];
            m_Scene = new byte[cap];
            int memCap = (int)Math.Ceiling((opt.Seconds + 2f) / MemoryInterval) + 8;
            m_MemT = new float[memCap]; m_MemAlloc = new float[memCap]; m_MemReserved = new float[memCap];
            m_MemMono = new float[memCap]; m_MemMonoHeap = new float[memCap]; m_MemGfx = new float[memCap]; m_MemGc = new int[memCap];
            for (int i = 0; i < MaxLoads; i++) m_Loads[i] = new LoadRecord();

            // Release players expose these counters too (UNVERIFIED for Unity 6000.3 Windows release: -1 in the CSV means "not available").
            m_RecDraws = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Draw Calls Count");
            m_RecBatches = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Batches Count");
            m_RecSetPass = ProfilerRecorder.StartNew(ProfilerCategory.Render, "SetPass Calls Count");
            m_RecTris = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Triangles Count");

            SceneManager.sceneLoaded += OnSceneLoaded;
            ApplyVSync();
            m_LastUpdate = Time.realtimeSinceStartupAsDouble;
            Debug.Log($"[PCMET] on: dir={opt.OutputDirectory} seconds={opt.Seconds} warmup={opt.WarmupSeconds} start={opt.Start} vsync={opt.VSync} buffer={cap} frames");
            if (opt.Start == PcMetricsStart.Boot) BeginWindow();
        }

        void ApplyVSync()
        {
            if (m_Opt.VSync >= 0) QualitySettings.vSyncCount = m_Opt.VSync;
        }

        void BeginWindow()
        {
            m_Recording = true;
            m_RecStart = Time.realtimeSinceStartupAsDouble;
            m_NextMemory = m_RecStart;
            m_GcAtStart = GC.CollectionCount(0);
            Debug.Log($"[PCMET] window start t={m_RecStart:F2}s scene={SceneManager.GetActiveScene().name}");
        }

        void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            if (mode != LoadSceneMode.Single) return;
            if (m_SceneIndex < 255) m_SceneIndex++;
            ApplyVSync();   // a tier switch in the new scene may reset the quality level
            if (m_LoadCount >= MaxLoads) return;
            var r = m_Loads[m_LoadCount];
            bool marked = s_MarkedLoadStart >= 0;
            r.scene = scene.name;
            r.loadStart_s = marked ? s_MarkedLoadStart : m_LastUpdate;
            r.startSource = marked ? "marked" : "frame";
            r.firstFrameEnd_s = -1;
            r.seconds = -1;
            s_MarkedLoadStart = -1;
            m_PendingLoad = m_LoadCount;
            m_PendingFrames = 0;
            m_LoadCount++;
        }

        void Update()
        {
            double now = Time.realtimeSinceStartupAsDouble;
            m_LastUpdate = now;
            if (m_Done) return;

            // First Update of the new scene: its delta time carries the synchronous load hitch -> not part of the window
            // (the load is reported in run.json "loads"). Second Update: the first frame of the scene has been presented.
            if (m_PendingLoad >= 0)
            {
                if (++m_PendingFrames < 2) return;
                var r = m_Loads[m_PendingLoad];
                r.firstFrameEnd_s = now;
                r.seconds = now - r.loadStart_s;
                m_PendingLoad = -1;
                if (!m_Recording && m_Opt.Start == PcMetricsStart.Region) BeginWindow();
            }

            if (!m_Recording)
            {
                if (now > m_Opt.TimeoutSeconds) Finish("timeout_no_region", 3);
                return;
            }

            float t = (float)(now - m_RecStart);
            if (m_Count < m_Frame.Length)
            {
                int i = m_Count++;
                FrameTimingManager.CaptureFrameTimings();
                float cpu = 0f, gpu = 0f;
                if (FrameTimingManager.GetLatestTimings(1, m_Timing) > 0)
                {
                    cpu = (float)m_Timing[0].cpuMainThreadFrameTime;
                    gpu = (float)m_Timing[0].gpuFrameTime;
                }
                m_Frame[i] = Time.frameCount;
                m_T[i] = t;
                m_Ms[i] = Time.unscaledDeltaTime * 1000f;
                m_Cpu[i] = cpu;
                m_Gpu[i] = gpu;
                m_Draws[i] = m_RecDraws.Valid ? (int)m_RecDraws.LastValue : -1;
                m_Batches[i] = m_RecBatches.Valid ? (int)m_RecBatches.LastValue : -1;
                m_SetPass[i] = m_RecSetPass.Valid ? (int)m_RecSetPass.LastValue : -1;
                m_Tris[i] = m_RecTris.Valid ? m_RecTris.LastValue : -1;
                m_Gc[i] = GC.CollectionCount(0);
                m_Scene[i] = (byte)m_SceneIndex;
            }
            else m_Dropped++;

            if (now >= m_NextMemory && m_MemCount < m_MemT.Length)
            {
                m_NextMemory = now + MemoryInterval;
                int k = m_MemCount++;
                const float Mb = 1f / (1024f * 1024f);
                m_MemT[k] = t;
                m_MemAlloc[k] = Profiler.GetTotalAllocatedMemoryLong() * Mb;
                m_MemReserved[k] = Profiler.GetTotalReservedMemoryLong() * Mb;
                m_MemMono[k] = Profiler.GetMonoUsedSizeLong() * Mb;
                m_MemMonoHeap[k] = Profiler.GetMonoHeapSizeLong() * Mb;
                long gfx = Profiler.GetAllocatedMemoryForGraphicsDriver();   // 0 outside development players
                m_MemGfx[k] = gfx > 0 ? gfx * Mb : -1f;
                m_MemGc[k] = GC.CollectionCount(0);
            }

            if (t >= m_Opt.Seconds) Finish("duration", 0);
        }

        void OnApplicationFocus(bool focus)
        {
            if (!focus && m_Recording && !m_Done) m_FocusLost++;
        }

        void OnApplicationQuit()
        {
            if (!m_Done) Finish("quit", -1);
        }

        void OnDestroy()
        {
            SceneManager.sceneLoaded -= OnSceneLoaded;
            m_RecDraws.Dispose(); m_RecBatches.Dispose(); m_RecSetPass.Dispose(); m_RecTris.Dispose();
            if (s_Instance == this) s_Instance = null;
        }

        /// <summary>Writes the files (allocations allowed here — the window is over) and optionally quits with <paramref name="exitCode"/>.</summary>
        void Finish(string reason, int exitCode)
        {
            if (m_Done) return;
            m_Done = true;
            m_Recording = false;
            m_EndReason = reason;
            bool ok = WriteAll();
            Debug.Log($"[PCMET] done reason={reason} frames={m_Count} dropped={m_Dropped} focusLost={m_FocusLost} written={ok} dir={m_Opt.OutputDirectory}");
            if (exitCode >= 0 && m_Opt.QuitWhenDone && !Application.isEditor)
                Application.Quit(ok ? exitCode : 4);
        }

        bool WriteAll()
        {
            try
            {
                Directory.CreateDirectory(m_Opt.OutputDirectory);
                WriteFrames(Path.Combine(m_Opt.OutputDirectory, "frames.csv"));
                WriteMemory(Path.Combine(m_Opt.OutputDirectory, "memory.csv"));
                File.WriteAllText(Path.Combine(m_Opt.OutputDirectory, "run.json"), JsonUtility.ToJson(BuildRunJson(), true), new UTF8Encoding(false));
                return true;
            }
            catch (Exception e)
            {
                Debug.LogError($"[PCMET] write failed: {e.Message}");
                return false;
            }
        }

        void WriteFrames(string path)
        {
            var ci = CultureInfo.InvariantCulture;
            using var w = new StreamWriter(path, false, new UTF8Encoding(false));
            w.WriteLine(FramesHeader);
            var sb = new StringBuilder(128);
            for (int i = 0; i < m_Count; i++)
            {
                sb.Clear();
                sb.Append(m_Frame[i]).Append(',')
                  .Append(m_T[i].ToString("F4", ci)).Append(',')
                  .Append(m_Ms[i].ToString("F3", ci)).Append(',')
                  .Append(m_Cpu[i].ToString("F3", ci)).Append(',')
                  .Append(m_Gpu[i].ToString("F3", ci)).Append(',')
                  .Append(m_Draws[i]).Append(',')
                  .Append(m_Batches[i]).Append(',')
                  .Append(m_SetPass[i]).Append(',')
                  .Append(m_Tris[i]).Append(',')
                  .Append(m_Gc[i]).Append(',')
                  .Append(m_Scene[i]);
                w.WriteLine(sb.ToString());
            }
        }

        void WriteMemory(string path)
        {
            var ci = CultureInfo.InvariantCulture;
            using var w = new StreamWriter(path, false, new UTF8Encoding(false));
            w.WriteLine(MemoryHeader);
            for (int k = 0; k < m_MemCount; k++)
                w.WriteLine(string.Format(ci, "{0:F3},{1:F1},{2:F1},{3:F1},{4:F1},{5:F1},{6}",
                    m_MemT[k], m_MemAlloc[k], m_MemReserved[k], m_MemMono[k], m_MemMonoHeap[k], m_MemGfx[k], m_MemGc[k]));
        }

        RunJson BuildRunJson()
        {
            var j = new RunJson();
            j.format = Format;
            j.label = m_Opt.Label;
            j.endReason = m_EndReason;
            j.isEditor = Application.isEditor;
            j.platform = Application.platform.ToString();
            j.unityVersion = Application.unityVersion;
            j.appVersion = Application.version;
            j.development = Debug.isDebugBuild;
            j.buildLabel = TryBuildLabel();
            j.commandLine = Environment.CommandLine;

            j.system = new SystemJson
            {
                os = SystemInfo.operatingSystem,
                cpu = SystemInfo.processorType,
                cpuCores = SystemInfo.processorCount,
                cpuFrequencyMHz = SystemInfo.processorFrequency,
                systemMemoryMb = SystemInfo.systemMemorySize,
                gpu = SystemInfo.graphicsDeviceName,
                gpuVendor = SystemInfo.graphicsDeviceVendor,
                gpuMemoryMb = SystemInfo.graphicsMemorySize,
                graphicsApi = SystemInfo.graphicsDeviceVersion,
                deviceModel = SystemInfo.deviceModel,
            };
            int q = QualitySettings.GetQualityLevel();
            j.display = new DisplayJson
            {
                width = Screen.width,
                height = Screen.height,
                fullScreenMode = Screen.fullScreenMode.ToString(),
                refreshRateHz = (float)Screen.currentResolution.refreshRateRatio.value,
                vSyncCount = QualitySettings.vSyncCount,
                targetFrameRate = Application.targetFrameRate,
                qualityLevel = q,
                qualityName = q >= 0 && q < QualitySettings.names.Length ? QualitySettings.names[q] : q.ToString(),
            };
            j.options = new OptionsJson
            {
                seconds = m_Opt.Seconds,
                warmupSeconds = m_Opt.WarmupSeconds,
                start = m_Opt.Start.ToString().ToLowerInvariant(),
                vsyncOverride = m_Opt.VSync,
                maxFps = m_Opt.MaxFps,
            };
            j.recording = new RecordingJson
            {
                windowStartRealtime_s = m_RecStart,
                frames = m_Count,
                droppedFrames = m_Dropped,
                focusLost = m_FocusLost,
                gcAtStart = m_GcAtStart,
                gcAtEnd = GC.CollectionCount(0),
                memorySamples = m_MemCount,
                drivingReadyRealtime_s = s_DrivingReady,
                countersAvailable = m_RecDraws.Valid,
            };
            j.loads = new LoadRecord[m_LoadCount];
            for (int i = 0; i < m_LoadCount; i++) j.loads[i] = m_Loads[i];

            // In-game percentiles over the window after warm-up — cross-check for the Python parser (same nearest rank).
            var sorted = new float[m_Count];
            int n = 0;
            for (int i = 0; i < m_Count; i++) if (m_T[i] >= m_Opt.WarmupSeconds) sorted[n++] = m_Ms[i];
            Array.Sort(sorted, 0, n);
            double sum = 0; for (int i = 0; i < n; i++) sum += sorted[i];
            j.inGame = new InGameJson
            {
                samples = n,
                meanFps = n > 0 && sum > 0 ? (float)(1000.0 * n / sum) : 0f,
                p50Ms = PcMetricsMath.NearestRank(sorted, n, 0.50),
                p95Ms = PcMetricsMath.NearestRank(sorted, n, 0.95),
                p99Ms = PcMetricsMath.NearestRank(sorted, n, 0.99),
                maxMs = n > 0 ? sorted[n - 1] : 0f,
                over33Ms = PcMetricsMath.CountOver(sorted, n, 33.4f),
                over50Ms = PcMetricsMath.CountOver(sorted, n, 50f),
                over100Ms = PcMetricsMath.CountOver(sorted, n, 100f),
            };
            return j;
        }

        static string TryBuildLabel()
        {
            try { return Game.Core.BuildInfo.Current.ShortLabel; }
            catch (Exception) { return ""; }
        }

        [Serializable] public sealed class RunJson
        {
            public string format, label, endReason, platform, unityVersion, appVersion, buildLabel, commandLine;
            public bool isEditor, development;
            public SystemJson system;
            public DisplayJson display;
            public OptionsJson options;
            public RecordingJson recording;
            public LoadRecord[] loads;
            public InGameJson inGame;
        }
        [Serializable] public sealed class SystemJson
        {
            public string os, cpu, gpu, gpuVendor, graphicsApi, deviceModel;
            public int cpuCores, cpuFrequencyMHz, systemMemoryMb, gpuMemoryMb;
        }
        [Serializable] public sealed class DisplayJson
        {
            public int width, height, vSyncCount, targetFrameRate, qualityLevel;
            public float refreshRateHz;
            public string fullScreenMode, qualityName;
        }
        [Serializable] public sealed class OptionsJson
        {
            public float seconds, warmupSeconds;
            public string start;
            public int vsyncOverride, maxFps;
        }
        [Serializable] public sealed class RecordingJson
        {
            public double windowStartRealtime_s, drivingReadyRealtime_s;
            public int frames, droppedFrames, focusLost, gcAtStart, gcAtEnd, memorySamples;
            public bool countersAvailable;
        }
        [Serializable] public sealed class InGameJson
        {
            public int samples, over33Ms, over50Ms, over100Ms;
            public float meanFps, p50Ms, p95Ms, p99Ms, maxMs;
        }
    }
}
