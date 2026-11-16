using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using Unity.Profiling;
using UnityEngine;
using UnityEngine.Profiling;

namespace TruckSim.Audio
{
    /// <summary>
    /// PC audio output (ADR 0284). The project AudioManager is shared with Android (DSP buffer 1024, 32 real voices);
    /// on a Windows/desktop player this resets the output once at boot, before any AudioSource exists:
    /// DSP buffer <see cref="PcDspBuffer"/>, <see cref="PcRealVoices"/> real voices (the truck keeps ~20 PerspectiveLoops
    /// x 2 sources plus four engine grids playing, so 32 voices virtualise low-priority layers such as the ambient bed).
    /// Launch arguments (all optional): <c>-audio_dsp N</c>, <c>-audio_voices N</c> (0 = keep the project value),
    /// <c>-audio_stats 1</c> (once-a-second [AUDIO-PC] voice/virtual counts), <c>-audio_capture out.wav</c> with
    /// <c>-audio_capture_t0 S</c> / <c>-audio_capture_s S</c> / <c>-audio_view cab|chase|split</c> (records the listener
    /// mix to a float WAV - the measured player output for LUFS/peak analysis, <c>tools/audio/pc_capture.py</c>).
    /// No allocation in the audio thread; the diagnostics allocate only when their arguments are given.
    /// </summary>
    public static class PcAudioRuntime
    {
        public const int PcDspBuffer = 512;
        public const int PcRealVoices = 64;

        /// <summary>Configuration the PC player asks for, from the current one and the two optional arguments
        /// (<paramref name="dspArg"/>/<paramref name="voicesArg"/>: null = PC default, "0" = keep current).</summary>
        public static AudioConfiguration PcConfiguration(AudioConfiguration current, string dspArg, string voicesArg)
        {
            int dsp = ParseInt(dspArg, PcDspBuffer);
            int voices = ParseInt(voicesArg, PcRealVoices);
            if (dsp > 0) current.dspBufferSize = Mathf.Clamp(Mathf.ClosestPowerOfTwo(dsp), 128, 4096);
            if (voices > 0) current.numRealVoices = Mathf.Clamp(voices, 8, 255);
            current.numVirtualVoices = Mathf.Max(current.numVirtualVoices, current.numRealVoices);
            return current;
        }

        static int ParseInt(string s, int fallback) =>
            int.TryParse(s, NumberStyles.Integer, CultureInfo.InvariantCulture, out int v) && v >= 0 ? v : fallback;

        internal static string Arg(string key)
        {
            var args = Environment.GetCommandLineArgs();
            string flag = "-" + key;
            for (int i = 0; i < args.Length - 1; i++)
                if (string.Equals(args[i], flag, StringComparison.OrdinalIgnoreCase)) return args[i + 1];
            return null;
        }

        internal static string Describe(AudioConfiguration c) =>
            $"rate={c.sampleRate} dsp={c.dspBufferSize} ({1000.0 * c.dspBufferSize / Math.Max(1, c.sampleRate):F1} ms) " +
            $"speakers={c.speakerMode} driver={AudioSettings.driverCapabilities} real={c.numRealVoices} virtual={c.numVirtualVoices} " +
            $"spatializer='{AudioSettings.GetSpatializerPluginName()}'";

#if UNITY_STANDALONE && !UNITY_EDITOR
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void ApplyOnBoot()
        {
            var before = AudioSettings.GetConfiguration();
            var want = PcConfiguration(before, Arg("audio_dsp"), Arg("audio_voices"));
            bool changed = want.dspBufferSize != before.dspBufferSize || want.numRealVoices != before.numRealVoices
                || want.numVirtualVoices != before.numVirtualVoices;
            bool ok = !changed || AudioSettings.Reset(want);
            Debug.Log($"[AUDIO-PC] output {(changed ? (ok ? "reset" : "RESET FAILED") : "unchanged")}: {Describe(AudioSettings.GetConfiguration())} (project: dsp={before.dspBufferSize} real={before.numRealVoices})");
            AudioOutputCapture.StartFromArguments();
        }
#elif UNITY_EDITOR || DEVELOPMENT_BUILD
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void DiagnosticsOnly() => AudioOutputCapture.StartFromArguments();
#endif
    }

    /// <summary>
    /// Records the AudioListener mix into a preallocated float buffer (OnAudioFilterRead on the listener object, so it
    /// follows the listener when cameras change) and writes a 32-bit float WAV on quit. Also logs voice statistics and
    /// the runtime memory of the loaded AudioClips. Diagnostics only: created by launch arguments.
    /// </summary>
    public sealed class AudioOutputCapture : MonoBehaviour
    {
        static float[] s_Buf;
        static int s_Write, s_Channels, s_Rate;
        static volatile bool s_Recording;

        string m_Path;
        float m_T0, m_T1, m_NextStats, m_NextListener;
        bool m_Stats, m_Started, m_Done;
        string m_View;
        int m_ViewStage;
        AudioListener m_Listener;
        AudioOutputTap m_Tap;
        readonly List<ProfilerRecorder> m_Rec = new List<ProfilerRecorder>();
        readonly List<string> m_RecNames = new List<string>();
        int m_PeakReal, m_PeakPlaying, m_PeakAudibleVirtual;
        readonly StringBuilder m_Sb = new StringBuilder(256);

        public static void StartFromArguments()
        {
            string path = PcAudioRuntime.Arg("audio_capture");
            bool stats = PcAudioRuntime.Arg("audio_stats") == "1";
            if (string.IsNullOrEmpty(path) && !stats) return;
            var go = new GameObject("AudioOutputCapture");
            DontDestroyOnLoad(go);
            var c = go.AddComponent<AudioOutputCapture>();
            c.m_Path = path;
            c.m_Stats = true;
            c.m_T0 = Seconds(PcAudioRuntime.Arg("audio_capture_t0"), 15f);
            float dur = Seconds(PcAudioRuntime.Arg("audio_capture_s"), 60f);
            c.m_T1 = c.m_T0 + dur;
            c.m_View = PcAudioRuntime.Arg("audio_view") ?? "";
            if (!string.IsNullOrEmpty(path))
            {
                var cfg = AudioSettings.GetConfiguration();
                s_Rate = cfg.sampleRate;
                s_Channels = cfg.speakerMode == AudioSpeakerMode.Mono ? 1 : cfg.speakerMode == AudioSpeakerMode.Stereo ? 2
                    : cfg.speakerMode == AudioSpeakerMode.Quad ? 4 : cfg.speakerMode == AudioSpeakerMode.Surround ? 5
                    : cfg.speakerMode == AudioSpeakerMode.Mode5point1 ? 6 : cfg.speakerMode == AudioSpeakerMode.Mode7point1 ? 8 : 2;
                s_Buf = new float[(int)(dur * s_Rate + s_Rate) * s_Channels];
                s_Write = 0;
            }
            Debug.Log($"[AUDIO-PC] capture='{path}' t0={c.m_T0:F1} t1={c.m_T1:F1} view='{c.m_View}' rate={s_Rate} ch={s_Channels}");
        }

        static float Seconds(string s, float fallback) =>
            float.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out float v) && v >= 0f ? v : fallback;

        /// <summary>Audio thread: append one mix block (interleaved). No allocation; drops a block whose channel count
        /// does not match the preallocated layout.</summary>
        internal static void Push(float[] data, int channels)
        {
            if (!s_Recording || s_Buf == null || channels != s_Channels) return;
            int n = Math.Min(data.Length, s_Buf.Length - s_Write);
            if (n <= 0) { s_Recording = false; return; }
            Array.Copy(data, 0, s_Buf, s_Write, n);
            s_Write += n;
        }

        void Start()
        {
            // audio-thread / main-thread markers (ns per frame); the full Audio category is ~70 markers, these are the totals
            foreach (var name in new[] { "Audio.Thread", "AudioManager.Update", "AudioManager.FixedUpdate", "Audibility computation" })
            {
                m_Rec.Add(ProfilerRecorder.StartNew(ProfilerCategory.Audio, name));
                m_RecNames.Add(name);
            }
        }

        void Update()
        {
            float t = Time.realtimeSinceStartup;
            if (t >= m_NextListener)
            {
                m_NextListener = t + 0.5f;
                FollowListener();
            }
            // cab / chase for the whole capture; split = cab first half, chase second half (switch 1.5 s before the middle,
            // the interior blend of TruckAudioController takes 0.15 s)
            if (m_ViewStage == 0 && !string.IsNullOrEmpty(m_View) && t >= m_T0 - 3f)
            {
                SetView(m_View == "split" ? "cab" : m_View);
                m_ViewStage = m_View == "split" ? 1 : 2;
            }
            if (m_ViewStage == 1 && t >= (m_T0 + m_T1) * 0.5f - 1.5f) { SetView("chase"); m_ViewStage = 2; }
            if (s_Buf != null && !m_Started && t >= m_T0) { m_Started = true; s_Recording = true; Debug.Log($"[AUDIO-PC] capture start t={t:F1}"); }
            if (s_Buf != null && m_Started && !m_Done && t >= m_T1) Finish("t1");
            if (m_Stats && t >= m_NextStats)
            {
                m_NextStats = t + 1f;
                LogStats(t);
            }
        }

        void FollowListener()
        {
            var l = FindAnyObjectByType<AudioListener>();
            if (l == m_Listener) return;
            if (m_Tap != null) Destroy(m_Tap);
            m_Listener = l;
            m_Tap = l != null ? l.gameObject.AddComponent<AudioOutputTap>() : null;
            Debug.Log($"[AUDIO-PC] listener -> {(l != null ? l.name : "none")}");
        }

        static void SetView(string view)
        {
            int mode = view == "chase" ? 1 : view == "orbit" ? 2 : 0;
            foreach (var mb in FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None))
            {
                if (mb.GetType().FullName != "Game.Cameras.CameraRig") continue;
                var m = mb.GetType().GetMethod("SetMode");
                var p = m?.GetParameters();
                if (p == null || p.Length != 1) continue;
                m.Invoke(mb, new[] { Enum.ToObject(p[0].ParameterType, mode) });
                Debug.Log($"[AUDIO-PC] camera view -> {view}");
            }
        }

        void LogStats(float t)
        {
            var src = FindObjectsByType<AudioSource>(FindObjectsSortMode.None);
            int playing = 0, virt = 0, audibleVirt = 0, audible = 0;
            m_Sb.Clear();
            foreach (var s in src)
            {
                if (!s.isPlaying) continue;
                playing++;
                bool aud = s.volume > 0.001f && !s.mute;
                if (aud) audible++;
                if (s.isVirtual) { virt++; if (aud) { audibleVirt++; if (audibleVirt <= 6) m_Sb.Append(s.transform.parent != null ? s.transform.parent.name + "/" : "").Append(s.name).Append(' '); } }
            }
            m_PeakPlaying = Math.Max(m_PeakPlaying, playing);
            m_PeakAudibleVirtual = Math.Max(m_PeakAudibleVirtual, audibleVirt);
            int real = playing - virt;
            m_PeakReal = Math.Max(m_PeakReal, real);
            var line = new StringBuilder(160);
            line.Append($"[AUDIO-PC] t={t:F1} sources={src.Length} playing={playing} audible={audible} real={real} virtual={virt} audibleVirtual={audibleVirt}");
            if (audibleVirt > 0) line.Append(" [").Append(m_Sb).Append(']');
            for (int i = 0; i < m_Rec.Count; i++) if (m_Rec[i].Valid) line.Append(' ').Append(m_RecNames[i].Replace(' ', '_')).Append('=').Append(m_Rec[i].LastValue);
            line.Append($" listenerVol={AudioListener.volume:F2}");
            Debug.Log(line.ToString());
        }

        void OnApplicationQuit()
        {
            if (s_Buf != null && !m_Done) Finish("quit");
            LogMemory();
            Debug.Log($"[AUDIO-PC] peaks: playing={m_PeakPlaying} real={m_PeakReal} audibleVirtual={m_PeakAudibleVirtual}");
            foreach (var r in m_Rec) r.Dispose();
        }

        void Finish(string why)
        {
            // memory and voice peaks also here: the player can stall in shutdown before OnApplicationQuit logs land
            LogMemory();
            Debug.Log($"[AUDIO-PC] peaks: playing={m_PeakPlaying} real={m_PeakReal} audibleVirtual={m_PeakAudibleVirtual}");
            m_Done = true;
            s_Recording = false;
            int n = s_Write;
            try
            {
                string full = Path.GetFullPath(m_Path);
                Directory.CreateDirectory(Path.GetDirectoryName(full));
                using (var w = new BinaryWriter(File.Create(full)))
                {
                    int bytes = n * 4;
                    w.Write(Encoding.ASCII.GetBytes("RIFF")); w.Write(36 + bytes); w.Write(Encoding.ASCII.GetBytes("WAVE"));
                    w.Write(Encoding.ASCII.GetBytes("fmt ")); w.Write(16); w.Write((short)3); w.Write((short)s_Channels);
                    w.Write(s_Rate); w.Write(s_Rate * s_Channels * 4); w.Write((short)(s_Channels * 4)); w.Write((short)32);
                    w.Write(Encoding.ASCII.GetBytes("data")); w.Write(bytes);
                    for (int i = 0; i < n; i++) w.Write(s_Buf[i]);
                }
                Debug.Log($"[AUDIO-PC] capture written ({why}): {full} frames={n / Math.Max(1, s_Channels)} ({(float)n / Math.Max(1, s_Channels) / s_Rate:F1} s) ch={s_Channels} rate={s_Rate}");
            }
            catch (Exception e) { Debug.LogWarning("[AUDIO-PC] capture write failed: " + e.Message); }
        }

        static void LogMemory()
        {
            long total = 0;
            int count = 0, loaded = 0;
            var byType = new Dictionary<string, long>();
            foreach (var c in Resources.FindObjectsOfTypeAll<AudioClip>())
            {
                count++;
                if (c.loadState == AudioDataLoadState.Loaded) loaded++;
                long m = Profiler.GetRuntimeMemorySizeLong(c);
                total += m;
                string k = c.loadType.ToString();
                byType[k] = (byType.TryGetValue(k, out long v) ? v : 0) + m;
            }
            var sb = new StringBuilder();
            foreach (var kv in byType) sb.Append(kv.Key).Append('=').Append((kv.Value / 1048576.0).ToString("F1", CultureInfo.InvariantCulture)).Append("MB ");
            Debug.Log($"[AUDIO-PC] clip memory: clips={count} loaded={loaded} total={(total / 1048576.0).ToString("F1", CultureInfo.InvariantCulture)} MB ({sb}) [Profiler.GetRuntimeMemorySizeLong]");
        }
    }

    /// <summary>Tap on the AudioListener object: hands every mix block to <see cref="AudioOutputCapture"/>.</summary>
    public sealed class AudioOutputTap : MonoBehaviour
    {
        void OnAudioFilterRead(float[] data, int channels) => AudioOutputCapture.Push(data, channels);
    }
}
