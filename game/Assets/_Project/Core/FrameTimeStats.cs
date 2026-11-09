using System;

namespace Game.Core
{
    /// <summary>
    /// Rolling window of frame times (milliseconds) with nearest-rank percentiles.
    /// Allocation-free after construction: safe to call every frame.
    /// </summary>
    public sealed class FrameTimeStats
    {
        readonly float[] m_Ring;
        readonly float[] m_Scratch;
        int m_Next;
        int m_Count;

        public FrameTimeStats(int capacity)
        {
            if (capacity < 1) throw new ArgumentOutOfRangeException(nameof(capacity));
            m_Ring = new float[capacity];
            m_Scratch = new float[capacity];
        }

        public int Capacity => m_Ring.Length;
        public int Count => m_Count;

        public void Add(float frameMs)
        {
            m_Ring[m_Next] = frameMs;
            m_Next = (m_Next + 1) % m_Ring.Length;
            if (m_Count < m_Ring.Length) m_Count++;
        }

        public void Clear()
        {
            m_Next = 0;
            m_Count = 0;
        }

        /// <summary>Computes p50/p95/p99 and the mean of the current window in one sort.</summary>
        public FrameTimeSummary Compute()
        {
            if (m_Count == 0) return default;
            Array.Copy(m_Ring, m_Scratch, m_Count);
            Array.Sort(m_Scratch, 0, m_Count);
            double sum = 0;
            for (int i = 0; i < m_Count; i++) sum += m_Scratch[i];
            float mean = (float)(sum / m_Count);
            return new FrameTimeSummary(
                m_Count,
                mean,
                Percentile(0.50),
                Percentile(0.95),
                Percentile(0.99),
                m_Scratch[m_Count - 1]);
        }

        // Nearest-rank percentile on the sorted scratch buffer.
        float Percentile(double p)
        {
            int rank = (int)Math.Ceiling(p * m_Count - 1e-9);
            if (rank < 1) rank = 1;
            if (rank > m_Count) rank = m_Count;
            return m_Scratch[rank - 1];
        }
    }

    public readonly struct FrameTimeSummary
    {
        public readonly int Samples;
        public readonly float MeanMs;
        public readonly float P50Ms;
        public readonly float P95Ms;
        public readonly float P99Ms;
        public readonly float MaxMs;

        public FrameTimeSummary(int samples, float meanMs, float p50, float p95, float p99, float max)
        {
            Samples = samples;
            MeanMs = meanMs;
            P50Ms = p50;
            P95Ms = p95;
            P99Ms = p99;
            MaxMs = max;
        }

        public float MeanFps => MeanMs > 0f ? 1000f / MeanMs : 0f;
    }
}
