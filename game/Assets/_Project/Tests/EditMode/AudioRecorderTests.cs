using System;
using System.IO;
using System.Text;
using System.Threading;
using Game.Core.Recording;
using Game.Gameplay;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>ADR 0345: in-game audio recording for video capture (-record_audio): WAV header layout, ring buffer without
    /// lost samples, streaming writer with checkpoints, the bus/tap de-duplication of <see cref="GameAudioRecorder"/>.</summary>
    public class AudioRecorderTests
    {
        string m_Dir;

        [SetUp]
        public void SetUp()
        {
            m_Dir = Path.Combine(Path.GetTempPath(), "kamion-rec-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(m_Dir);
        }

        [TearDown]
        public void TearDown()
        {
            GameAudioRecorder.End();
            try { Directory.Delete(m_Dir, true); } catch (IOException) { }
        }

        static string Ascii(byte[] b, int at) => Encoding.ASCII.GetString(b, at, 4);
        static uint U32(byte[] b, int at) => BitConverter.ToUInt32(b, at);
        static ushort U16(byte[] b, int at) => BitConverter.ToUInt16(b, at);

        [Test]
        public void WavHeader_Pcm16_IsCanonical44Bytes()
        {
            var h = new byte[WavFormat.Pcm16HeaderSize];
            WavFormat.WriteHeader(h, WavSampleFormat.Pcm16, 48000, 2, 192000);
            Assert.AreEqual("RIFF", Ascii(h, 0));
            Assert.AreEqual(36u + 192000u, U32(h, 4));
            Assert.AreEqual("WAVE", Ascii(h, 8));
            Assert.AreEqual("fmt ", Ascii(h, 12));
            Assert.AreEqual(16u, U32(h, 16));
            Assert.AreEqual(1, U16(h, 20));          // PCM
            Assert.AreEqual(2, U16(h, 22));
            Assert.AreEqual(48000u, U32(h, 24));
            Assert.AreEqual(48000u * 4, U32(h, 28)); // byte rate
            Assert.AreEqual(4, U16(h, 32));          // block align
            Assert.AreEqual(16, U16(h, 34));
            Assert.AreEqual("data", Ascii(h, 36));
            Assert.AreEqual(192000u, U32(h, 40));
        }

        [Test]
        public void WavHeader_Float32_HasExtendedFmtAndFact()
        {
            var h = new byte[WavFormat.Float32HeaderSize];
            WavFormat.WriteHeader(h, WavSampleFormat.Float32, 44100, 6, 6 * 4 * 1000);
            Assert.AreEqual("RIFF", Ascii(h, 0));
            Assert.AreEqual(50u + 24000u, U32(h, 4));
            Assert.AreEqual("fmt ", Ascii(h, 12));
            Assert.AreEqual(18u, U32(h, 16));
            Assert.AreEqual(3, U16(h, 20));          // IEEE float
            Assert.AreEqual(6, U16(h, 22));
            Assert.AreEqual(44100u, U32(h, 24));
            Assert.AreEqual(44100u * 24, U32(h, 28));
            Assert.AreEqual(24, U16(h, 32));
            Assert.AreEqual(32, U16(h, 34));
            Assert.AreEqual(0, U16(h, 36));          // cbSize
            Assert.AreEqual("fact", Ascii(h, 38));
            Assert.AreEqual(4u, U32(h, 42));
            Assert.AreEqual(1000u, U32(h, 46));      // sample frames
            Assert.AreEqual("data", Ascii(h, 50));
            Assert.AreEqual(24000u, U32(h, 54));
        }

        [Test]
        public void Ring_WrapsAroundExactly_AndDropsWholeBlocksOnly()
        {
            var ring = new AudioRingBuffer(1000);
            Assert.AreEqual(1024, ring.Capacity);
            var block = new float[300];
            var got = new float[1024];
            float next = 0f, expect = 0f;
            for (int round = 0; round < 20; round++)
            {
                for (int i = 0; i < block.Length; i++) block[i] = next++;
                Assert.IsTrue(ring.Write(block, 0, block.Length));
                int n = ring.Read(got, 0, got.Length);
                Assert.AreEqual(300, n);
                for (int i = 0; i < n; i++) Assert.AreEqual(expect++, got[i]);
            }
            // fill: 3 blocks fit (900), the 4th does not and is dropped whole
            for (int b = 0; b < 4; b++) ring.Write(block, 0, block.Length);
            Assert.AreEqual(900, ring.Available);
            Assert.AreEqual(300, ring.DroppedSamples);
        }

        [Test]
        public void Ring_ConcurrentProducerConsumer_LosesNothing()
        {
            const int blocks = 4000, size = 1024;           // like 4000 DSP blocks of 512 stereo frames
            var ring = new AudioRingBuffer(1 << 18);
            long received = 0;
            bool ordered = true;
            var done = new ManualResetEventSlim(false);
            var consumer = new Thread(() =>
            {
                var buf = new float[4096];
                float expect = 0f;
                while (!done.IsSet || ring.Available > 0)
                {
                    int n = ring.Read(buf, 0, buf.Length);
                    for (int i = 0; i < n; i++)
                    {
                        if (buf[i] != expect) ordered = false;
                        expect = (expect + 1f) % 1000000f;
                    }
                    received += n;
                    if (n == 0) Thread.Sleep(1);
                }
            });
            consumer.Start();
            var block = new float[size];
            float v = 0f;
            for (int b = 0; b < blocks; b++)
            {
                for (int i = 0; i < size; i++) { block[i] = v; v = (v + 1f) % 1000000f; }
                Assert.IsTrue(ring.Write(block, 0, size), "ring overflow at block " + b);
                if ((b & 63) == 0) Thread.Sleep(1);
            }
            done.Set();
            Assert.IsTrue(consumer.Join(10000));
            Assert.AreEqual(0, ring.DroppedSamples);
            Assert.AreEqual((long)blocks * size, received);
            Assert.IsTrue(ordered, "samples out of order");
        }

        static (byte[] header, byte[] all) ReadShared(string path)
        {
            using var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
            var all = new byte[fs.Length];
            int off = 0, n;
            while (off < all.Length && (n = fs.Read(all, off, all.Length - off)) > 0) off += n;
            var h = new byte[Math.Min(all.Length, WavFormat.Float32HeaderSize)];
            Array.Copy(all, h, h.Length);
            return (h, all);
        }

        [Test]
        public void Writer_Float32_StreamsCheckpointsAndRoundTripsExactly()
        {
            string path = Path.Combine(m_Dir, "a.wav");
            var ring = new AudioRingBuffer(1 << 16);
            var w = new WavStreamWriter(path, 48000, 2, WavSampleFormat.Float32, ring);
            w.Open();
            var block = new float[1024];
            int frame = 0;
            void PushBlocks(int count)
            {
                for (int b = 0; b < count; b++)
                {
                    for (int i = 0; i < 512; i++, frame++)
                    {
                        float s = (float)Math.Sin(2 * Math.PI * 440 * frame / 48000.0) * 0.5f;
                        block[2 * i] = s; block[2 * i + 1] = -s;
                    }
                    ring.Write(block, 0, block.Length);
                    w.Pump();
                }
            }
            PushBlocks(100);
            w.Checkpoint();
            // mid-recording the file on disk is already a valid WAV up to the checkpoint (crash safety)
            var (h1, all1) = ReadShared(path);
            Assert.AreEqual((uint)(all1.Length - 8), U32(h1, 4));
            Assert.AreEqual((uint)(all1.Length - WavFormat.Float32HeaderSize), U32(h1, 54));
            Assert.AreEqual(51200u, U32(h1, 46));
            PushBlocks(181);
            w.Stop();
            var (h, all) = ReadShared(path);
            int frames = 281 * 512;
            Assert.AreEqual(frames, w.FramesWritten);
            Assert.AreEqual((uint)(frames * 8), U32(h, 54));
            Assert.AreEqual(WavFormat.Float32HeaderSize + frames * 8, all.Length);
            for (int f = 0; f < frames; f += 997)
            {
                float s = (float)Math.Sin(2 * Math.PI * 440 * f / 48000.0) * 0.5f;
                Assert.AreEqual(s, BitConverter.ToSingle(all, WavFormat.Float32HeaderSize + f * 8));
                Assert.AreEqual(-s, BitConverter.ToSingle(all, WavFormat.Float32HeaderSize + f * 8 + 4));
            }
        }

        [Test]
        public void Writer_Pcm16_ThreadedDrainAndClamp()
        {
            string path = Path.Combine(m_Dir, "b.wav");
            var ring = new AudioRingBuffer(1 << 16);
            var w = new WavStreamWriter(path, 48000, 1, WavSampleFormat.Pcm16, ring) { CheckpointSeconds = 0.05f };
            int checkpoints = 0;
            w.OnCheckpoint = _ => Interlocked.Increment(ref checkpoints);
            w.StartThread();
            var block = new float[512];
            for (int b = 0; b < 200; b++)
            {
                for (int i = 0; i < block.Length; i++) block[i] = (i % 4) switch { 0 => 0.25f, 1 => 1.5f, 2 => -2f, _ => 0f };
                Assert.IsTrue(ring.Write(block, 0, block.Length));
                if ((b & 15) == 0) Thread.Sleep(10);
            }
            w.Stop();
            Assert.Greater(checkpoints, 1);
            var (h, all) = ReadShared(path);
            Assert.AreEqual(1, U16(h, 20));
            Assert.AreEqual(200u * 512 * 2, U32(h, 40));
            Assert.AreEqual(44 + 200 * 512 * 2, all.Length);
            Assert.AreEqual((short)Math.Round(0.25 * 32767), BitConverter.ToInt16(all, 44));
            Assert.AreEqual((short)32767, BitConverter.ToInt16(all, 46));
            Assert.AreEqual((short)-32767, BitConverter.ToInt16(all, 48));
        }

        [Test]
        public void Writer_ReplacesDroppedBlocksWithSilence_KeepingTheClock()
        {
            string path = Path.Combine(m_Dir, "c.wav");
            var ring = new AudioRingBuffer(1024);
            var w = new WavStreamWriter(path, 48000, 2, WavSampleFormat.Float32, ring);
            w.Open();
            var block = new float[512];
            for (int i = 0; i < block.Length; i++) block[i] = 0.1f;
            for (int b = 0; b < 5; b++) ring.Write(block, 0, block.Length);   // 2 fit, 3 dropped (writer stalled)
            Assert.AreEqual(1536, ring.DroppedSamples);
            w.Pump();
            w.Stop();
            Assert.AreEqual(5 * 512 / 2, w.FramesWritten);
            Assert.AreEqual(1536, w.ZeroFilledSamples);
        }

        [Test]
        public void Recorder_BusWinsOverTap_AndChannelMismatchIsCounted()
        {
            GameAudioRecorder.Begin(Path.Combine(m_Dir, "d.wav"), 48000, 2, WavSampleFormat.Float32, 0.0);
            var block = new float[1024];
            GameAudioRecorder.PushFromTap(block, 2);          // no bus yet: tap records
            Assert.AreEqual(512, GameAudioRecorder.FramesPushed);
            GameAudioRecorder.PushFromBus(block, 2);
            GameAudioRecorder.PushFromTap(block, 2);          // bus just delivered: the tap block is the same mix, skipped
            Assert.AreEqual(1024, GameAudioRecorder.FramesPushed);
            Assert.AreEqual(2048, GameAudioRecorder.Ring.Available);
            GameAudioRecorder.PushFromBus(new float[3072], 6); // device switched to 5.1: not mixed into a stereo file
            Assert.AreEqual(1, GameAudioRecorder.ChannelMismatchBlocks);
            GameAudioRecorder.End();
            GameAudioRecorder.PushFromBus(block, 2);
            Assert.AreEqual(1024, GameAudioRecorder.FramesPushed);
        }

        [Test]
        public void Recorder_FillsPausesLongerThanGapSeconds_WithSilence()
        {
            GameAudioRecorder.Begin(Path.Combine(m_Dir, "e.wav"), 48000, 2, WavSampleFormat.Float32, 0.0);
            long f = System.Diagnostics.Stopwatch.Frequency, t0 = 1_000_000;
            var block = new float[1024];                                   // 512 frames = 10.67 ms
            GameAudioRecorder.PushFromBusAt(block, 2, t0);
            GameAudioRecorder.PushFromBusAt(block, 2, t0 + f * 512 / 48000);
            GameAudioRecorder.PushFromBusAt(block, 2, t0 + f * 1024 / 48000 + f / 10);   // 100 ms late: jitter/drift, no fill
            Assert.AreEqual(0, GameAudioRecorder.Gaps);
            Assert.AreEqual(1536, GameAudioRecorder.FramesPushed);
            long late = t0 + f * 2;                                         // next block 2 s after the first: scene change
            GameAudioRecorder.PushFromBusAt(block, 2, late);
            Assert.AreEqual(1, GameAudioRecorder.Gaps);
            Assert.AreEqual(96000 - 1536, GameAudioRecorder.GapFrames, 1);
            Assert.AreEqual(96000 + 512, GameAudioRecorder.FramesPushed, 1);   // sample index = time since the first block
            Assert.AreEqual(GameAudioRecorder.FramesPushed * 2, GameAudioRecorder.Ring.Available);
        }

        [Test]
        public void Recorder_Arguments()
        {
            var args = new[] { "Kamion.exe", "-scene", "x", "-record_audio", "C:/rec/a.wav", "-record_audio_format", "pcm16" };
            Assert.AreEqual("C:/rec/a.wav", GameAudioRecorder.ArgValue(args, GameAudioRecorder.Arg));
            Assert.AreEqual(WavSampleFormat.Pcm16, GameAudioRecorder.ParseFormat(GameAudioRecorder.ArgValue(args, GameAudioRecorder.FormatArg)));
            Assert.AreEqual(WavSampleFormat.Float32, GameAudioRecorder.ParseFormat(null));
            Assert.IsNull(GameAudioRecorder.ArgValue(new[] { "Kamion.exe", "-record_audio" }, GameAudioRecorder.Arg));
            Assert.IsNull(GameAudioRecorder.StartFromArguments(new[] { "Kamion.exe" }));
        }
    }
}
