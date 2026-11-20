using System;

namespace Game.Core
{
    /// <summary>
    /// Look-ahead peak limiter of the listener bus (ADR 0313). The D92 cab gain (+6-7 dB) puts the loudest moments of the
    /// cab mix (full-throttle launch to 80 km/h, horn) near full scale; this keeps the bus under <see cref="CeilingDb"/>
    /// sample peak (0.5 dB under the -1 dBTP ceiling, margin for inter-sample peaks) without touching anything quieter -
    /// so it changes neither the integrated loudness of a normal drive nor the balance of the layers.
    /// Gain computer: requested gain per frame r = min(1, ceiling / peak); a sliding minimum over the look-ahead window,
    /// a release towards 1 (one-pole, <see cref="ReleaseSeconds"/>) and a box average of the same length as the window.
    /// The box average of window minima is &lt;= r at the frame it is applied to (the frame is delayed by window - 1), so no
    /// sample leaves above the ceiling and the gain curve has no step (no click). Latency = window - 1 frames
    /// (<see cref="LookaheadFrames"/> = 64: 1.3 ms at 48 kHz). Buffers are allocated in the constructor, <see cref="Process"/>
    /// does not allocate (audio thread).
    /// </summary>
    public sealed class BusLimiter
    {
        public const int LookaheadFrames = 64;
        public const int MaxChannels = 8;
        public const float CeilingDb = -1.5f;
        public const float ReleaseSeconds = 0.08f;

        readonly float[] m_Delay = new float[LookaheadFrames * MaxChannels];
        readonly float[] m_Req = new float[LookaheadFrames];   // requested gains, last L frames
        readonly float[] m_Rel = new float[LookaheadFrames];   // released minima, last L frames (box average input)
        readonly float m_Ceiling;
        int m_Pos, m_Channels;
        float m_Released = 1f;
        float m_ReleaseCoef;
        int m_Rate;

        /// <summary>Lowest gain applied since the last <see cref="ResetStats"/> (diagnostics, written by the audio thread).</summary>
        public float MinGain { get; private set; } = 1f;
        /// <summary>Frames processed with gain &lt; 1 since the last <see cref="ResetStats"/>.</summary>
        public long LimitedFrames { get; private set; }

        public BusLimiter() : this(CeilingDb) { }

        public BusLimiter(float ceilingDb)
        {
            m_Ceiling = (float)Math.Pow(10.0, ceilingDb / 20.0);
            Clear(0);
        }

        public void ResetStats()
        {
            MinGain = 1f;
            LimitedFrames = 0;
        }

        void Clear(int channels)
        {
            Array.Clear(m_Delay, 0, m_Delay.Length);
            for (int i = 0; i < LookaheadFrames; i++) { m_Req[i] = 1f; m_Rel[i] = 1f; }
            m_Released = 1f;
            m_Pos = 0;
            m_Channels = channels;
        }

        /// <summary>Limits an interleaved block in place (output delayed by <see cref="LookaheadFrames"/> - 1 frames).
        /// A change of the channel count resets the state (no history mixing between layouts).</summary>
        public void Process(float[] data, int channels, int sampleRate)
        {
            if (data == null || channels <= 0 || channels > MaxChannels) return;
            if (channels != m_Channels) Clear(channels);
            if (sampleRate != m_Rate && sampleRate > 0)
            {
                m_Rate = sampleRate;
                m_ReleaseCoef = 1f - (float)Math.Exp(-1.0 / (ReleaseSeconds * sampleRate));
            }
            const int L = LookaheadFrames;
            int frames = data.Length / channels;
            float minGain = MinGain;
            long limited = LimitedFrames;
            for (int f = 0, k = 0; f < frames; f++, k += channels)
            {
                float peak = 0f;
                for (int c = 0; c < channels; c++)
                {
                    float a = Math.Abs(data[k + c]);
                    if (a > peak) peak = a;
                }
                m_Req[m_Pos] = peak > m_Ceiling ? m_Ceiling / peak : 1f;
                float mn = 1f;
                for (int i = 0; i < L; i++) if (m_Req[i] < mn) mn = m_Req[i];
                m_Released = mn < m_Released ? mn : m_Released + (1f - m_Released) * m_ReleaseCoef;
                if (m_Released > mn) m_Released = mn;   // the release never lifts the gain over the window minimum
                m_Rel[m_Pos] = m_Released;
                float sum = 0f;
                for (int i = 0; i < L; i++) sum += m_Rel[i];
                float g = sum * (1f / L);
                if (g > 1f) g = 1f;
                // the oldest frame in the ring (written L - 1 frames ago) leaves now; the new frame takes its slot
                int slot = (m_Pos + 1) % L;
                int d = slot * MaxChannels, w = m_Pos * MaxChannels;
                for (int c = 0; c < channels; c++)
                {
                    float x = data[k + c];
                    m_Delay[w + c] = x;
                    data[k + c] = m_Delay[d + c] * g;
                }
                if (g < 1f) { limited++; if (g < minGain) minGain = g; }
                m_Pos = slot;
            }
            MinGain = minGain;
            LimitedFrames = limited;
        }
    }
}
