using System;
using System.IO;
using System.Threading;

namespace Game.Core.Recording
{
    /// <summary>
    /// Streams an <see cref="AudioRingBuffer"/> into a WAV file on its own background thread (ADR 0345). The header is
    /// rewritten with the current sizes and the file flushed to disk every <see cref="CheckpointSeconds"/>, so a crash or
    /// a killed process leaves a valid file up to the last checkpoint; <see cref="Stop"/> drains the ring, writes the
    /// final header and closes. Samples of blocks the ring dropped are written as silence (file length = audio clock).
    /// <see cref="Pump"/> and <see cref="Checkpoint"/> are public so tests can drive the writer synchronously
    /// (<see cref="Open"/> without <see cref="StartThread"/>).
    /// </summary>
    public sealed class WavStreamWriter : IDisposable
    {
        public readonly string Path;
        public readonly int SampleRate;
        public readonly int Channels;
        public readonly WavSampleFormat Format;
        public float CheckpointSeconds = 2f;
        /// <summary>Called on the writer thread after every checkpoint (sidecar sync file); exceptions are swallowed.</summary>
        public Action<WavStreamWriter> OnCheckpoint;

        readonly AudioRingBuffer m_Ring;
        readonly float[] m_Chunk;
        readonly byte[] m_Bytes;
        readonly byte[] m_Header;
        FileStream m_File;
        Thread m_Thread;
        volatile bool m_Stop;
        long m_DataBytes, m_ZeroFilled, m_DropHandled;
        int m_Checkpoints;
        bool m_Full;

        public WavStreamWriter(string path, int sampleRate, int channels, WavSampleFormat format, AudioRingBuffer ring)
        {
            Path = path;
            SampleRate = sampleRate;
            Channels = Math.Max(1, channels);
            Format = format;
            m_Ring = ring ?? throw new ArgumentNullException(nameof(ring));
            // 8192 frames per pass (~170 ms at 48 kHz), multiple of the channel count
            m_Chunk = new float[8192 * Channels];
            m_Bytes = new byte[m_Chunk.Length * 4];
            m_Header = new byte[WavFormat.Float32HeaderSize];
        }

        public long DataBytes => Interlocked.Read(ref m_DataBytes);
        public long FramesWritten => DataBytes / (Channels * WavFormat.BytesPerSample(Format));
        public double SecondsWritten => (double)FramesWritten / SampleRate;
        public long ZeroFilledSamples => Interlocked.Read(ref m_ZeroFilled);
        public int Checkpoints => m_Checkpoints;
        /// <summary>True once the 4 GiB WAV limit was reached (further samples are discarded).</summary>
        public bool Full => m_Full;
        public bool IsOpen => m_File != null;
        public string LastError { get; private set; }

        /// <summary>Creates the file and writes an empty header.</summary>
        public void Open()
        {
            string dir = System.IO.Path.GetDirectoryName(System.IO.Path.GetFullPath(Path));
            if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
            m_File = new FileStream(Path, FileMode.Create, FileAccess.Write, FileShare.Read, 1 << 16);
            WavFormat.WriteHeader(m_Header, Format, SampleRate, Channels, 0);
            m_File.Write(m_Header, 0, WavFormat.HeaderSize(Format));
            m_File.Flush(true);
        }

        public void StartThread()
        {
            if (m_File == null) Open();
            m_Stop = false;
            m_Thread = new Thread(Run) { Name = "WavStreamWriter", IsBackground = true, Priority = ThreadPriority.BelowNormal };
            m_Thread.Start();
        }

        void Run()
        {
            var sw = System.Diagnostics.Stopwatch.StartNew();
            double next = CheckpointSeconds;
            try
            {
                while (!m_Stop)
                {
                    Pump();
                    if (sw.Elapsed.TotalSeconds >= next)
                    {
                        next = sw.Elapsed.TotalSeconds + CheckpointSeconds;
                        Checkpoint();
                    }
                    Thread.Sleep(20);
                }
            }
            catch (Exception e) { LastError = e.Message; }
        }

        /// <summary>Moves everything the ring holds into the file (plus silence for dropped blocks). Returns samples moved.</summary>
        public int Pump()
        {
            if (m_File == null) return 0;
            int total = 0, n;
            while ((n = m_Ring.Read(m_Chunk, 0, m_Chunk.Length)) > 0)
            {
                WriteSamples(m_Chunk, n);
                total += n;
            }
            long dropped = m_Ring.DroppedSamples;
            long gap = dropped - m_DropHandled;
            if (gap > 0)
            {
                m_DropHandled = dropped;
                Array.Clear(m_Chunk, 0, m_Chunk.Length);
                while (gap > 0)
                {
                    int z = (int)Math.Min(gap, m_Chunk.Length);
                    WriteSamples(m_Chunk, z);
                    Interlocked.Add(ref m_ZeroFilled, z);
                    gap -= z;
                }
            }
            return total;
        }

        void WriteSamples(float[] src, int count)
        {
            if (m_Full) return;
            int bytes = count * WavFormat.BytesPerSample(Format);
            if (m_DataBytes + bytes > WavFormat.MaxDataBytes(Format)) { m_Full = true; return; }
            WavFormat.Encode(src, 0, count, m_Bytes, 0, Format);
            m_File.Write(m_Bytes, 0, bytes);
            Interlocked.Add(ref m_DataBytes, bytes);
        }

        /// <summary>Rewrites the header with the current sizes and flushes the file to disk.</summary>
        public void Checkpoint()
        {
            if (m_File == null) return;
            long pos = m_File.Position;
            WavFormat.WriteHeader(m_Header, Format, SampleRate, Channels, m_DataBytes);
            m_File.Seek(0, SeekOrigin.Begin);
            m_File.Write(m_Header, 0, WavFormat.HeaderSize(Format));
            m_File.Seek(pos, SeekOrigin.Begin);
            m_File.Flush(true);
            m_Checkpoints++;
            try { OnCheckpoint?.Invoke(this); } catch (Exception e) { LastError = e.Message; }
        }

        /// <summary>Stops the thread, drains the ring, writes the final header and closes the file. Idempotent.</summary>
        public void Stop()
        {
            m_Stop = true;
            if (m_Thread != null && m_Thread.IsAlive && Thread.CurrentThread != m_Thread) m_Thread.Join(5000);
            m_Thread = null;
            if (m_File == null) return;
            try
            {
                Pump();
                Checkpoint();
            }
            finally
            {
                m_File.Dispose();
                m_File = null;
            }
        }

        public void Dispose() => Stop();
    }
}
