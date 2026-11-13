using System;
using System.Globalization;
using System.IO;
using System.Text;
using System.Threading;
using Game.Core;
using Game.Platform;
using UnityEngine;
using UnityEngine.Profiling;

namespace Game.Telemetry
{
    /// <summary>Latest diagnostics values, refreshed by <see cref="DiagnosticsSampler"/>.</summary>
    public struct DiagnosticsSnapshot
    {
        public FrameTimeSummary Frames;
        public float? BatteryTempC;
        public int? ThermalStatus;
        public float? ThermalHeadroom;
        public long? PssKb;
        public long UnityAllocatedBytes;
        public long UnityReservedBytes;
        public float SessionSeconds;
        public long FrameIndex;
    }

    /// <summary>JSON shape of diag/summary.json (read by scripts/device-metrics.ps1).</summary>
    [Serializable]
    public sealed class DiagnosticsSummaryJson
    {
        public string build;
        public string device;
        public string gpu;
        public string graphicsApi;
        public string qualityTier;
        public int targetFps;
        public string resolution;
        public float sessionSeconds;
        public long frames;
        public int windowSamples;
        public float meanFps;
        public float p50Ms;
        public float p95Ms;
        public float p99Ms;
        public float maxMs;
        public float batteryTempC = -1f;
        public int thermalStatus = -1;
        public float thermalHeadroom = -1f;
        public long pssKb = -1;
        public long unityAllocatedBytes;
        public long unityReservedBytes;
        public int systemMemoryMb;
        public float renderScale;
        public string capFallback;
    }

    /// <summary>
    /// Records every frame time into a rolling window (allocation-free per frame), polls slow
    /// platform sensors at low frequency, and periodically writes
    /// persistentDataPath/diag/frametimes.csv (all frames of the session) and diag/summary.json.
    /// Also logs a one-line "[DIAG]" summary to the player log / logcat.
    /// </summary>
    public sealed class DiagnosticsSampler : MonoBehaviour
    {
        public const int WindowFrames = 600;
        const float StatsInterval = 0.5f;
        const float SensorInterval = 2f;
        const float FlushInterval = 2f;
        const float SummaryInterval = 5f;
        /// <summary>ADR 0177: PSS period in the default (background) poll mode [s]. WORKING_VALUE.</summary>
        public const float PssIntervalBg = 10f;

        /// <summary>
        /// ADR 0177: how the slow platform sensors are polled (launch argument <c>diag_poll</c>).
        /// <c>bg</c> (default): battery / thermal status / headroom one per frame on consecutive frames, PSS on a background
        /// thread every <see cref="PssIntervalBg"/> s. <c>main</c>: pre-0177 behaviour (all four, PSS included, on the main
        /// thread in one frame every 2 s; A16: the frame after it was 5-16 of the 17-30 frames &gt; 40 ms of a gate-3 drive).
        /// <c>off</c>: no sensor polling (A/B only).
        /// </summary>
        public enum PollMode { Background, Main, Off }
        public PollMode Poll { get; private set; } = PollMode.Background;
        int m_SensorStep;
        float m_NextPss;
        Thread m_PssThread;
        AutoResetEvent m_PssWake;
        volatile bool m_PssQuit;
        long m_PssKbBg = -1;

        IPlatformServices m_Platform;
        FrameTimeStats m_Stats;
        DiagnosticsSnapshot m_Snapshot;

        // Pending CSV rows (frame index, session time, frame ms) — preallocated.
        float[] m_PendingTime;
        float[] m_PendingMs;
        float[] m_PendingCpu;
        float[] m_PendingGpu;
        float[] m_PendingScale;
        int[] m_PendingMirrors;
        int[] m_PendingAb;
        // FrameTimingManager (PlayerSettings "Frame Timing Stats"): GPU time of the frame on Vulkan/GLES devices that report
        // it (Mali, Xclipse); 0 when unsupported. Reported for the frame that finished a few frames earlier.
        readonly FrameTiming[] m_Timing = new FrameTiming[1];
        long[] m_PendingFrame;
        int m_PendingCount;

        float m_SessionStart;
        float m_NextStats, m_NextSensors, m_NextFlush, m_NextSummary;
        long m_Frame;
        bool m_SkipFirstFrame = true;

        StreamWriter m_Csv;
        readonly StringBuilder m_Sb = new StringBuilder(64 * 1024);
        string m_SummaryPath;
        readonly DiagnosticsSummaryJson m_Json = new DiagnosticsSummaryJson();

        public DiagnosticsSnapshot Snapshot => m_Snapshot;
        public string OutputDirectory { get; private set; }

        public void Initialize(IPlatformServices platform)
        {
            m_Platform = platform ?? new DefaultPlatformServices();
            string mode = null;
            try { mode = m_Platform.GetLaunchArgument("diag_poll"); } catch (Exception) { }
            Poll = mode == "main" ? PollMode.Main : mode == "off" ? PollMode.Off : PollMode.Background;
            if (Poll == PollMode.Background) StartPssThread();
            Debug.Log($"[DIAG] sensor poll mode={Poll} (diag_poll main|bg|off, ADR 0177)");
        }

        void StartPssThread()
        {
            if (m_PssThread != null) return;
            m_PssWake = new AutoResetEvent(false);
            m_PssThread = new Thread(PssLoop) { IsBackground = true, Name = "KamionDiagPss", Priority = System.Threading.ThreadPriority.BelowNormal };
            m_PssThread.Start();
        }

        // ADR 0177: android.os.Debug.getPss() walks the process smaps (tens of ms with ~1 GB mapped); off the main thread.
        void PssLoop()
        {
#if UNITY_ANDROID && !UNITY_EDITOR
            AndroidJNI.AttachCurrentThread();
#endif
            try
            {
                while (!m_PssQuit)
                {
                    m_PssWake.WaitOne();
                    if (m_PssQuit) break;
                    long? v = null;
                    try { v = m_Platform.GetProcessPssKb(); } catch (Exception) { }
                    Interlocked.Exchange(ref m_PssKbBg, v ?? -1);
                }
            }
            finally
            {
#if UNITY_ANDROID && !UNITY_EDITOR
                AndroidJNI.DetachCurrentThread();
#endif
            }
        }

        void Awake()
        {
            m_Stats = new FrameTimeStats(WindowFrames);
            int pendingCap = 1024;
            m_PendingTime = new float[pendingCap];
            m_PendingMs = new float[pendingCap];
            m_PendingFrame = new long[pendingCap];
            m_PendingCpu = new float[pendingCap];
            m_PendingGpu = new float[pendingCap];
            m_PendingScale = new float[pendingCap];
            m_PendingMirrors = new int[pendingCap];
            m_PendingAb = new int[pendingCap];
            m_SessionStart = Time.realtimeSinceStartup;
            OpenFiles();
        }

        void OpenFiles()
        {
            try
            {
                OutputDirectory = Path.Combine(Application.persistentDataPath, "diag");
                Directory.CreateDirectory(OutputDirectory);
                m_Csv = new StreamWriter(Path.Combine(OutputDirectory, "frametimes.csv"), false, new UTF8Encoding(false));
                m_Csv.WriteLine("frame,t_s,frame_ms,cpu_main_ms,gpu_ms,render_scale,mirror_n,ab");   // ADR 0068: mirror renders, A/B state
                m_SummaryPath = Path.Combine(OutputDirectory, "summary.json");
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[DIAG] cannot write diagnostics files: {e.Message}");
                m_Csv = null;
            }
        }

        void Update()
        {
            float now = Time.realtimeSinceStartup;
            float dtMs = Time.unscaledDeltaTime * 1000f;
            if (m_SkipFirstFrame) { m_SkipFirstFrame = false; return; }

            m_Frame++;
            m_Stats.Add(dtMs);
            FrameTimingManager.CaptureFrameTimings();
            float cpuMs = 0f, gpuMs = 0f;
            if (FrameTimingManager.GetLatestTimings(1, m_Timing) > 0)
            {
                cpuMs = (float)m_Timing[0].cpuMainThreadFrameTime;
                gpuMs = (float)m_Timing[0].gpuFrameTime;
            }
            if (m_PendingCount < m_PendingFrame.Length)
            {
                m_PendingCpu[m_PendingCount] = cpuMs;
                m_PendingGpu[m_PendingCount] = gpuMs;
                m_PendingScale[m_PendingCount] = Game.Core.RenderState.RenderScale;   // ADR 0062: A/B of the scale floor
                m_PendingMirrors[m_PendingCount] = Game.Core.ExtraViewStats.LastFrameMirrorRenders;   // ADR 0068
                m_PendingAb[m_PendingCount] = Game.Core.ExtraViewStats.AbIndex;
                m_PendingFrame[m_PendingCount] = m_Frame;
                m_PendingTime[m_PendingCount] = now - m_SessionStart;
                m_PendingMs[m_PendingCount] = dtMs;
                m_PendingCount++;
            }

            if (now >= m_NextStats)
            {
                m_NextStats = now + StatsInterval;
                m_Snapshot.Frames = m_Stats.Compute();
                m_Snapshot.UnityAllocatedBytes = Profiler.GetTotalAllocatedMemoryLong();
                m_Snapshot.UnityReservedBytes = Profiler.GetTotalReservedMemoryLong();
                m_Snapshot.SessionSeconds = now - m_SessionStart;
                m_Snapshot.FrameIndex = m_Frame;
            }

            if (m_Platform != null && Poll == PollMode.Main && now >= m_NextSensors)
            {
                m_NextSensors = now + SensorInterval;
                m_Snapshot.BatteryTempC = m_Platform.GetBatteryTemperatureC();
                m_Snapshot.ThermalStatus = m_Platform.GetThermalStatus();
                m_Snapshot.ThermalHeadroom = m_Platform.GetThermalHeadroom();
                m_Snapshot.PssKb = m_Platform.GetProcessPssKb();
            }
            else if (m_Platform != null && Poll == PollMode.Background)
            {
                // One JNI query per frame (battery, thermal status, headroom), started one frame after the CSV flush.
                if (m_SensorStep == 0 && now >= m_NextSensors) { m_NextSensors = now + SensorInterval; m_SensorStep = 1; }
                else if (m_SensorStep == 1) { m_Snapshot.BatteryTempC = m_Platform.GetBatteryTemperatureC(); m_SensorStep = 2; }
                else if (m_SensorStep == 2) { m_Snapshot.ThermalStatus = m_Platform.GetThermalStatus(); m_SensorStep = 3; }
                else if (m_SensorStep == 3) { m_Snapshot.ThermalHeadroom = m_Platform.GetThermalHeadroom(); m_SensorStep = 0; }
                if (now >= m_NextPss) { m_NextPss = now + PssIntervalBg; m_PssWake?.Set(); }
                long pss = Interlocked.Read(ref m_PssKbBg);
                m_Snapshot.PssKb = pss >= 0 ? pss : (long?)null;
            }

            if (now >= m_NextFlush || m_PendingCount == m_PendingFrame.Length)
            {
                m_NextFlush = now + FlushInterval;
                FlushCsv();
            }

            if (now >= m_NextSummary)
            {
                m_NextSummary = now + SummaryInterval;
                WriteSummary();
            }
        }

        void FlushCsv()
        {
            if (m_Csv == null || m_PendingCount == 0) { m_PendingCount = 0; return; }
            var ci = CultureInfo.InvariantCulture;
            m_Sb.Clear();
            for (int i = 0; i < m_PendingCount; i++)
            {
                m_Sb.Append(m_PendingFrame[i]).Append(',')
                    .Append(m_PendingTime[i].ToString("F4", ci)).Append(',')
                    .Append(m_PendingMs[i].ToString("F3", ci)).Append(',')
                    .Append(m_PendingCpu[i].ToString("F3", ci)).Append(',')
                    .Append(m_PendingGpu[i].ToString("F3", ci)).Append(',')
                    .Append(m_PendingScale[i].ToString("F2", ci)).Append('\n');
            }
            m_PendingCount = 0;
            m_Csv.Write(m_Sb);
            m_Csv.Flush();
        }

        void WriteSummary()
        {
            var s = m_Snapshot;
            var j = m_Json;
            var build = BuildInfo.Current;
            j.build = build.ShortLabel;
            j.device = SystemInfo.deviceModel;
            j.gpu = SystemInfo.graphicsDeviceName;
            j.graphicsApi = SystemInfo.graphicsDeviceVersion;
            int q = QualitySettings.GetQualityLevel();
            j.qualityTier = q >= 0 && q < QualitySettings.names.Length ? QualitySettings.names[q] : q.ToString();
            j.targetFps = Application.targetFrameRate;
            j.resolution = Screen.width + "x" + Screen.height;
            j.sessionSeconds = s.SessionSeconds;
            j.frames = s.FrameIndex;
            j.windowSamples = s.Frames.Samples;
            j.meanFps = s.Frames.MeanFps;
            j.p50Ms = s.Frames.P50Ms;
            j.p95Ms = s.Frames.P95Ms;
            j.p99Ms = s.Frames.P99Ms;
            j.maxMs = s.Frames.MaxMs;
            j.batteryTempC = s.BatteryTempC ?? -1f;
            j.thermalStatus = s.ThermalStatus ?? -1;
            j.thermalHeadroom = s.ThermalHeadroom ?? -1f;
            j.pssKb = s.PssKb ?? -1;
            j.unityAllocatedBytes = s.UnityAllocatedBytes;
            j.unityReservedBytes = s.UnityReservedBytes;
            j.systemMemoryMb = SystemInfo.systemMemorySize;
            j.renderScale = Game.Core.RenderState.RenderScale;
            j.capFallback = Game.Core.RenderState.ThermalFallback ? "thermal" : Game.Core.RenderState.PacingFallback ? "pacing" : "none";

            var ci = CultureInfo.InvariantCulture;
            Debug.Log(string.Format(ci,
                "[DIAG] t={0:F0}s tier={1} target={2} fps={3:F1} p50={4:F2} p95={5:F2} p99={6:F2} max={7:F2}ms temp={8:F1}C thermal={9} headroom={10:F2} pss={11}MB scale={12:F2} fallback={13}" +
                " mir={14:F2}/f cpu={15:F2} gpu={16} cap={17:F2}/f cpu={18:F2} gpu={19} shd_gpu={20} main_cpu={21:F2}{22}",
                j.sessionSeconds, j.qualityTier, j.targetFps, j.meanFps, j.p50Ms, j.p95Ms, j.p99Ms, j.maxMs,
                j.batteryTempC, j.thermalStatus, j.thermalHeadroom, j.pssKb >= 0 ? j.pssKb / 1024 : -1, j.renderScale, j.capFallback,
                // ADR 0068: fixed passes - mirror renders / capture faces per frame, main-thread ms per frame, GPU ms (development players only, else "-")
                Game.Core.ExtraViewStats.MirrorRendersPerFrame, Game.Core.ExtraViewStats.MirrorCpuMs, Gpu(Game.Core.ExtraViewStats.MirrorGpuMs),
                Game.Core.ExtraViewStats.CaptureFacesPerFrame, Game.Core.ExtraViewStats.CaptureCpuMs, Gpu(Game.Core.ExtraViewStats.CaptureGpuMs),
                Gpu(Game.Core.ExtraViewStats.ShadowGpuMs), Game.Core.ExtraViewStats.MainCpuMs,
                Game.Core.ExtraViewStats.AbState != null ? " ab=" + Game.Core.ExtraViewStats.AbState : ""));

            if (m_SummaryPath == null) return;
            try { File.WriteAllText(m_SummaryPath, JsonUtility.ToJson(j, true)); }
            catch (Exception e) { Debug.LogWarning($"[DIAG] summary write failed: {e.Message}"); }
        }

        static string Gpu(float ms) => ms >= 0f ? ms.ToString("F2", CultureInfo.InvariantCulture) : "-";

        void OnApplicationPause(bool paused)
        {
            if (paused) { FlushCsv(); WriteSummary(); }
        }

        void OnDestroy()
        {
            m_PssQuit = true;
            m_PssWake?.Set();
            FlushCsv();
            m_Csv?.Dispose();
            m_Csv = null;
        }
    }
}
