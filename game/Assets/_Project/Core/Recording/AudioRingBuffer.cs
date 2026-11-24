using System;
using System.Threading;

namespace Game.Core.Recording
{
    /// <summary>
    /// Single-producer / single-consumer ring of interleaved float samples (ADR 0345). The producer is the audio thread
    /// (<c>OnAudioFilterRead</c>), the consumer the WAV writer thread. Preallocated, lock-free, no allocation in
    /// <see cref="Write"/> or <see cref="Read"/>. A block that does not fit whole is dropped whole (never split, so the
    /// channel interleave can never shift) and counted in <see cref="DroppedSamples"/>; the writer replaces dropped
    /// samples with silence so the file keeps the audio clock (sync with the video).
    /// </summary>
    public sealed class AudioRingBuffer
    {
        readonly float[] m_Buf;
        readonly int m_Mask;
        long m_Write;   // total samples ever written (producer owns, consumer reads)
        long m_Read;    // total samples ever read (consumer owns, producer reads)
        long m_Dropped;

        /// <param name="minCapacity">Minimum capacity in samples (rounded up to a power of two, at least 1024).</param>
        public AudioRingBuffer(int minCapacity)
        {
            int cap = 1024;
            while (cap < minCapacity && cap < (1 << 30)) cap <<= 1;
            m_Buf = new float[cap];
            m_Mask = cap - 1;
        }

        public int Capacity => m_Buf.Length;

        /// <summary>Samples waiting for the consumer.</summary>
        public int Available => (int)(Volatile.Read(ref m_Write) - Volatile.Read(ref m_Read));

        /// <summary>Samples accepted so far (producer counter).</summary>
        public long TotalWritten => Volatile.Read(ref m_Write);

        /// <summary>Samples of blocks that were dropped because the ring was full.</summary>
        public long DroppedSamples => Interlocked.Read(ref m_Dropped);

        /// <summary>Producer: appends <paramref name="count"/> samples from <paramref name="src"/> or drops the whole block.
        /// Returns true when written.</summary>
        public bool Write(float[] src, int offset, int count)
        {
            if (src == null || count <= 0) return true;
            long w = m_Write;
            long r = Volatile.Read(ref m_Read);
            if (count > m_Buf.Length - (int)(w - r))
            {
                Interlocked.Add(ref m_Dropped, count);
                return false;
            }
            int start = (int)(w & m_Mask);
            int first = Math.Min(count, m_Buf.Length - start);
            Array.Copy(src, offset, m_Buf, start, first);
            if (first < count) Array.Copy(src, offset + first, m_Buf, 0, count - first);
            Volatile.Write(ref m_Write, w + count);
            return true;
        }

        /// <summary>Consumer: copies up to <paramref name="max"/> samples into <paramref name="dst"/>; returns the count.</summary>
        public int Read(float[] dst, int offset, int max)
        {
            long r = m_Read;
            long w = Volatile.Read(ref m_Write);
            int n = (int)Math.Min(max, w - r);
            if (n <= 0) return 0;
            int start = (int)(r & m_Mask);
            int first = Math.Min(n, m_Buf.Length - start);
            Array.Copy(m_Buf, start, dst, offset, first);
            if (first < n) Array.Copy(m_Buf, 0, dst, offset + first, n - first);
            Volatile.Write(ref m_Read, r + n);
            return n;
        }
    }
}
