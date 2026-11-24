using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Text;
using System.Threading;
using Game.Core.Recording;
using UnityEngine;
using Debug = UnityEngine.Debug;

namespace Game.Gameplay
{
    /// <summary>
    /// Records the game's own audio output to a WAV for video capture (ADR 0345; the dev PC has no WASAPI loopback /
    /// "Stereo Mix"). Off by default; launch argument <c>-record_audio &lt;file.wav&gt;</c> [<c>-record_audio_format float|pcm16</c>].
    /// The mix is taken where the player hears it: from <see cref="CabinBusFilter"/> after the cab gain and limiter
    /// (<see cref="PushFromBus"/>), or, when the listener has no cab bus (menu, lab), from an own tap on the AudioListener
    /// object (<see cref="GameAudioRecorderTap"/>; ignored while the bus delivers, so a block is never recorded twice).
    /// Audio thread: one copy into a preallocated <see cref="AudioRingBuffer"/> (~21 s), no allocation, no lock.
    /// A <see cref="WavStreamWriter"/> thread writes the file and every 2 s rewrites the header + flushes, so a crash keeps
    /// the recording; <c>&lt;file&gt;.sync.json</c> next to it holds the clock mapping (UTC of the first block, frames vs
    /// UTC for drift) and is rewritten at each checkpoint. Log lines start with <c>[RECORD]</c>.
    /// Disabled: one argument scan at boot, one volatile bool check per DSP block in the bus filter.
    /// </summary>
    public sealed class GameAudioRecorder : MonoBehaviour
    {
        public const string Arg = "-record_audio";
        public const string FormatArg = "-record_audio_format";
        /// <summary>Ring capacity in seconds of audio (power of two samples above this).</summary>
        public const float RingSeconds = 20f;
        /// <summary>A pause longer than this between blocks is filled with silence (WORKING_VALUE; one DSP block is ~10.7 ms).</summary>
        public const float GapSeconds = 0.25f;

        static volatile bool s_On;
        static AudioRingBuffer s_Ring;
        static int s_Channels, s_Rate;
        static float[] s_Zero;
        static long s_GapFrames, s_Gaps;
        static long s_Ts0, s_FirstTicks, s_LastTicks, s_LastFramesStart, s_FramesPushed, s_BusTicks, s_ChannelMismatch;
        static DateTime s_Utc0;
        static double s_Rt0;

        string m_Path;
        WavSampleFormat m_Format;
        WavStreamWriter m_Writer;
        AudioListener m_Listener;
        GameAudioRecorderTap m_Tap;
        float m_NextFollow, m_NextStatus;
        bool m_FirstLogged, m_Closed;
        int m_Rate;

        public static bool Active => s_On;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Boot() => StartFromArguments(Environment.GetCommandLineArgs());

        /// <summary>Creates the recorder when <c>-record_audio &lt;path&gt;</c> is in <paramref name="args"/>; null otherwise.</summary>
        public static GameAudioRecorder StartFromArguments(string[] args)
        {
            string path = ArgValue(args, Arg);
            if (string.IsNullOrEmpty(path)) return null;
            var go = new GameObject("GameAudioRecorder");
            DontDestroyOnLoad(go);
            var r = go.AddComponent<GameAudioRecorder>();
            r.m_Path = Path.GetFullPath(path);
            r.m_Format = ParseFormat(ArgValue(args, FormatArg));
            return r;
        }

        public static string ArgValue(string[] args, string flag)
        {
            if (args == null) return null;
            for (int i = 0; i + 1 < args.Length; i++)
                if (string.Equals(args[i], flag, StringComparison.OrdinalIgnoreCase)) return args[i + 1];
            return null;
        }

        public static WavSampleFormat ParseFormat(string s) =>
            string.Equals(s, "pcm16", StringComparison.OrdinalIgnoreCase) || s == "16" ? WavSampleFormat.Pcm16 : WavSampleFormat.Float32;

        public static int ChannelsOf(AudioSpeakerMode m) => m switch
        {
            AudioSpeakerMode.Mono => 1,
            AudioSpeakerMode.Stereo => 2,
            AudioSpeakerMode.Quad => 4,
            AudioSpeakerMode.Surround => 5,
            AudioSpeakerMode.Mode5point1 => 6,
            AudioSpeakerMode.Mode7point1 => 8,
            AudioSpeakerMode.Prologic => 2,
            _ => 2,
        };

        void Start()
        {
            // configuration read here, not at boot: PcAudioRuntime may reset the output in BeforeSceneLoad too
            var cfg = AudioSettings.GetConfiguration();
            m_Rate = AudioSettings.outputSampleRate;
            int ch = ChannelsOf(cfg.speakerMode);
            try
            {
                Begin(m_Path, m_Rate, ch, m_Format, Time.realtimeSinceStartupAsDouble);
                m_Writer = new WavStreamWriter(m_Path, m_Rate, ch, m_Format, s_Ring) { OnCheckpoint = w => WriteSync(w, false) };
                m_Writer.StartThread();
                Debug.Log(string.Format(CultureInfo.InvariantCulture,
                    "[RECORD] audio -> '{0}' rate={1} ch={2} format={3} dsp={4} ring={5:F1}s utc0={6:o} realtime0={7:F4}",
                    m_Path, m_Rate, ch, m_Format, cfg.dspBufferSize, (double)s_Ring.Capacity / (m_Rate * ch), s_Utc0, s_Rt0));
                AudioSettings.OnAudioConfigurationChanged += OnConfigChanged;
            }
            catch (Exception e)
            {
                s_On = false;
                Debug.LogWarning("[RECORD] audio recorder failed to start: " + e.Message);
                enabled = false;
            }
        }

        /// <summary>Arms the static capture state (public for tests: no MonoBehaviour, no writer thread needed).</summary>
        public static void Begin(string path, int rate, int channels, WavSampleFormat format, double realtimeNow)
        {
            s_On = false;
            s_Channels = Math.Max(1, channels);
            s_Ring = new AudioRingBuffer((int)(RingSeconds * rate * s_Channels));
            s_Rate = Math.Max(1, rate);
            s_Zero = new float[4096 * s_Channels];
            s_FirstTicks = s_LastTicks = s_LastFramesStart = s_FramesPushed = s_BusTicks = s_ChannelMismatch = s_GapFrames = s_Gaps = 0;
            s_Ts0 = Stopwatch.GetTimestamp();
            s_Utc0 = DateTime.UtcNow;
            s_Rt0 = realtimeNow;
            s_On = true;
        }

        /// <summary>Disarms the capture (public for tests).</summary>
        public static void End() => s_On = false;

        public static AudioRingBuffer Ring => s_Ring;
        public static long FramesPushed => Interlocked.Read(ref s_FramesPushed);
        public static long ChannelMismatchBlocks => Interlocked.Read(ref s_ChannelMismatch);
        public static long GapFrames => Interlocked.Read(ref s_GapFrames);
        public static long Gaps => Interlocked.Read(ref s_Gaps);

        /// <summary>Tests: a bus push at an explicit Stopwatch timestamp.</summary>
        public static void PushFromBusAt(float[] data, int channels, long stopwatchTicks)
        {
            if (!s_On) return;
            Volatile.Write(ref s_BusTicks, stopwatchTicks);
            Accept(data, channels, stopwatchTicks);
        }

        /// <summary>Audio thread, from <see cref="CabinBusFilter"/> after gain + limiter.</summary>
        public static void PushFromBus(float[] data, int channels)
        {
            if (!s_On) return;
            long now = Stopwatch.GetTimestamp();
            Volatile.Write(ref s_BusTicks, now);
            Accept(data, channels, now);
        }

        /// <summary>Audio thread, from the own listener tap; skipped while the bus delivered within the last 200 ms.</summary>
        public static void PushFromTap(float[] data, int channels)
        {
            if (!s_On) return;
            long now = Stopwatch.GetTimestamp();
            long bus = Volatile.Read(ref s_BusTicks);
            if (bus != 0 && now - bus < Stopwatch.Frequency / 5) return;
            Accept(data, channels, now);
        }

        static void Accept(float[] data, int channels, long now)
        {
            if (data == null || channels != s_Channels)
            {
                Interlocked.Increment(ref s_ChannelMismatch);
                return;
            }
            long first = Interlocked.CompareExchange(ref s_FirstTicks, now, 0);
            long f = s_FramesPushed;
            if (first != 0)
            {
                // Gap: no block for > GapSeconds (scene change before the tap moved to the new listener, audio thread stall).
                // Silence for the missing wall time keeps sample index = time since the first block (sync with the video);
                // smaller differences are clock drift, corrected in the mux (scripts/record-drive.ps1).
                long expected = (long)((now - first) * (double)s_Rate / Stopwatch.Frequency);
                long behind = expected - f;
                if (behind > (long)(GapSeconds * s_Rate))
                {
                    long samples = behind * channels;
                    while (samples > 0)
                    {
                        int n = (int)Math.Min(samples, s_Zero.Length);
                        s_Ring.Write(s_Zero, 0, n);
                        samples -= n;
                    }
                    f += behind;
                    Interlocked.Add(ref s_GapFrames, behind);
                    Interlocked.Increment(ref s_Gaps);
                }
            }
            s_Ring.Write(data, 0, data.Length);
            Volatile.Write(ref s_LastFramesStart, f);
            Volatile.Write(ref s_LastTicks, now);
            Volatile.Write(ref s_FramesPushed, f + data.Length / channels);
        }

        static DateTime UtcOf(long ticks) => s_Utc0.AddTicks((long)((ticks - s_Ts0) * (double)TimeSpan.TicksPerSecond / Stopwatch.Frequency));
        static double RealtimeOf(long ticks) => s_Rt0 + (ticks - s_Ts0) / (double)Stopwatch.Frequency;

        void Update()
        {
            if (!s_On) return;
            float t = Time.realtimeSinceStartup;
            // no listener (it died with its scene): look every frame, so the gap (filled with silence) stays short
            if (t >= m_NextFollow || m_Listener == null)
            {
                m_NextFollow = t + 0.5f;
                FollowListener();
            }
            long first = Interlocked.Read(ref s_FirstTicks);
            if (!m_FirstLogged && first != 0)
            {
                m_FirstLogged = true;
                Debug.Log(string.Format(CultureInfo.InvariantCulture, "[RECORD] first block utc={0:o} realtime={1:F4} (sync point = sample 0 of the WAV)",
                    UtcOf(first), RealtimeOf(first)));
            }
            if (t >= m_NextStatus && m_Writer != null)
            {
                m_NextStatus = t + 60f;
                Debug.Log(string.Format(CultureInfo.InvariantCulture, "[RECORD] t={0:F0}s written={1:F1}s dropped={2} zeroFilled={3} mismatch={4} gaps={6} ({7:F2} s){5}",
                    t, m_Writer.SecondsWritten, s_Ring.DroppedSamples, m_Writer.ZeroFilledSamples, ChannelMismatchBlocks,
                    m_Writer.LastError != null ? " error=" + m_Writer.LastError : "", Gaps, (double)GapFrames / m_Rate));
            }
        }

        void FollowListener()
        {
            var l = FindAnyObjectByType<AudioListener>();
            bool bus = l != null && l.TryGetComponent(out CabinBusFilter f) && f.isActiveAndEnabled;
            if (l == m_Listener && (m_Tap != null) == (l != null && !bus)) return;
            if (m_Tap != null) Destroy(m_Tap);
            m_Listener = l;
            m_Tap = l != null && !bus ? l.gameObject.AddComponent<GameAudioRecorderTap>() : null;
            Debug.Log($"[RECORD] listener -> {(l != null ? l.name : "none")} source={(bus ? "cab bus (after gain + limiter)" : m_Tap != null ? "own tap" : "none")}");
        }

        void OnConfigChanged(bool deviceWasChanged)
        {
            var cfg = AudioSettings.GetConfiguration();
            Debug.LogWarning($"[RECORD] audio configuration changed (device={deviceWasChanged}) rate={AudioSettings.outputSampleRate} speakers={cfg.speakerMode}: blocks with another channel count are skipped");
        }

        void WriteSync(WavStreamWriter w, bool closed)
        {
            // writer thread (checkpoints) or main thread (close): small JSON, temp file + move so a crash never leaves half a file
            long first = Interlocked.Read(ref s_FirstTicks), last = Volatile.Read(ref s_LastTicks);
            var sb = new StringBuilder(640);
            var ci = CultureInfo.InvariantCulture;
            sb.Append("{\n");
            sb.Append("  \"version\": 1,\n");
            sb.Append("  \"wav\": \"").Append(w.Path.Replace("\\", "\\\\")).Append("\",\n");
            sb.Append("  \"sampleRate\": ").Append(w.SampleRate.ToString(ci)).Append(",\n");
            sb.Append("  \"channels\": ").Append(w.Channels.ToString(ci)).Append(",\n");
            sb.Append("  \"format\": \"").Append(w.Format == WavSampleFormat.Float32 ? "float32" : "pcm16").Append("\",\n");
            sb.Append("  \"utc0\": \"").Append(s_Utc0.ToString("o", ci)).Append("\",\n");
            sb.Append("  \"realtime0\": ").Append(s_Rt0.ToString("F4", ci)).Append(",\n");
            sb.Append("  \"firstBlockUtc\": ").Append(first != 0 ? "\"" + UtcOf(first).ToString("o", ci) + "\"" : "null").Append(",\n");
            sb.Append("  \"firstBlockRealtime\": ").Append(first != 0 ? RealtimeOf(first).ToString("F4", ci) : "null").Append(",\n");
            sb.Append("  \"lastPushUtc\": ").Append(last != 0 ? "\"" + UtcOf(last).ToString("o", ci) + "\"" : "null").Append(",\n");
            sb.Append("  \"lastPushFramesStart\": ").Append(Volatile.Read(ref s_LastFramesStart).ToString(ci)).Append(",\n");
            sb.Append("  \"framesPushed\": ").Append(FramesPushed.ToString(ci)).Append(",\n");
            sb.Append("  \"framesWritten\": ").Append(w.FramesWritten.ToString(ci)).Append(",\n");
            sb.Append("  \"droppedSamples\": ").Append(s_Ring.DroppedSamples.ToString(ci)).Append(",\n");
            sb.Append("  \"zeroFilledSamples\": ").Append(w.ZeroFilledSamples.ToString(ci)).Append(",\n");
            sb.Append("  \"channelMismatchBlocks\": ").Append(ChannelMismatchBlocks.ToString(ci)).Append(",\n");
            sb.Append("  \"gaps\": ").Append(Gaps.ToString(ci)).Append(",\n");
            sb.Append("  \"gapFrames\": ").Append(GapFrames.ToString(ci)).Append(",\n");
            sb.Append("  \"full\": ").Append(w.Full ? "true" : "false").Append(",\n");
            sb.Append("  \"checkpointUtc\": \"").Append(DateTime.UtcNow.ToString("o", ci)).Append("\",\n");
            sb.Append("  \"closed\": ").Append(closed ? "true" : "false").Append('\n');
            sb.Append("}\n");
            string target = w.Path + ".sync.json", tmp = target + ".tmp";
            File.WriteAllText(tmp, sb.ToString());
            if (File.Exists(target)) File.Delete(target);
            File.Move(tmp, target);
        }

        void Close(string why)
        {
            if (m_Closed) return;
            m_Closed = true;
            s_On = false;
            AudioSettings.OnAudioConfigurationChanged -= OnConfigChanged;
            if (m_Writer == null) return;
            try
            {
                m_Writer.OnCheckpoint = null;
                m_Writer.Stop();
                WriteSync(m_Writer, true);
                Debug.Log(string.Format(CultureInfo.InvariantCulture,
                    "[RECORD] closed ({0}): '{1}' {2:F1} s, frames={3} dropped={4} zeroFilled={5} mismatch={6} full={7} gaps={9} ({10:F2} s){8}",
                    why, m_Path, m_Writer.SecondsWritten, m_Writer.FramesWritten, s_Ring.DroppedSamples, m_Writer.ZeroFilledSamples,
                    ChannelMismatchBlocks, m_Writer.Full, m_Writer.LastError != null ? " error=" + m_Writer.LastError : "", Gaps, (double)GapFrames / m_Rate));
            }
            catch (Exception e) { Debug.LogWarning("[RECORD] close failed: " + e.Message); }
        }

        void OnApplicationQuit() => Close("quit");

        void OnDestroy() => Close("destroy");
    }

    /// <summary>Own tap on the AudioListener object when it has no <see cref="CabinBusFilter"/> (ADR 0345).</summary>
    public sealed class GameAudioRecorderTap : MonoBehaviour
    {
        void OnAudioFilterRead(float[] data, int channels) => GameAudioRecorder.PushFromTap(data, channels);
    }
}
