using System;

namespace Game.Core.Recording
{
    public enum WavSampleFormat
    {
        /// <summary>32-bit IEEE float (WAVE_FORMAT_IEEE_FLOAT = 3): the mix exactly as Unity hands it over.</summary>
        Float32,
        /// <summary>16-bit PCM (WAVE_FORMAT_PCM = 1): half the size, clamped to [-1, 1].</summary>
        Pcm16,
    }

    /// <summary>
    /// RIFF/WAVE header and sample encoding for <see cref="WavStreamWriter"/> (ADR 0345). Float files carry the 18-byte
    /// fmt chunk (cbSize = 0) and a 'fact' chunk as the RIFF spec asks for non-PCM data; PCM16 is the classic 44-byte
    /// header. Sizes are little-endian uint32, so one file holds at most ~4 GiB of samples (float stereo 48 kHz: ~3.1 h).
    /// </summary>
    public static class WavFormat
    {
        public const int Pcm16HeaderSize = 44;
        public const int Float32HeaderSize = 58;

        public static int HeaderSize(WavSampleFormat f) => f == WavSampleFormat.Float32 ? Float32HeaderSize : Pcm16HeaderSize;

        public static int BytesPerSample(WavSampleFormat f) => f == WavSampleFormat.Float32 ? 4 : 2;

        /// <summary>Largest data chunk the uint32 RIFF size field can describe for this format.</summary>
        public static long MaxDataBytes(WavSampleFormat f) => uint.MaxValue - (HeaderSize(f) - 8);

        /// <summary>Writes the complete header for <paramref name="dataBytes"/> of samples into <paramref name="dst"/>
        /// (at least <see cref="HeaderSize"/> bytes). Called once at the start (size 0) and at every checkpoint.</summary>
        public static void WriteHeader(byte[] dst, WavSampleFormat f, int sampleRate, int channels, long dataBytes)
        {
            if (dst == null || dst.Length < HeaderSize(f)) throw new ArgumentException("header buffer too small");
            if (channels < 1 || sampleRate < 1) throw new ArgumentOutOfRangeException(nameof(channels));
            dataBytes = Math.Max(0, Math.Min(dataBytes, MaxDataBytes(f)));
            int bps = BytesPerSample(f);
            int blockAlign = channels * bps;
            int p = 0;
            Ascii(dst, ref p, "RIFF");
            U32(dst, ref p, (uint)(HeaderSize(f) - 8 + dataBytes));
            Ascii(dst, ref p, "WAVE");
            Ascii(dst, ref p, "fmt ");
            if (f == WavSampleFormat.Float32)
            {
                U32(dst, ref p, 18);
                U16(dst, ref p, 3);
            }
            else
            {
                U32(dst, ref p, 16);
                U16(dst, ref p, 1);
            }
            U16(dst, ref p, (ushort)channels);
            U32(dst, ref p, (uint)sampleRate);
            U32(dst, ref p, (uint)(sampleRate * blockAlign));
            U16(dst, ref p, (ushort)blockAlign);
            U16(dst, ref p, (ushort)(bps * 8));
            if (f == WavSampleFormat.Float32)
            {
                U16(dst, ref p, 0);                                    // cbSize
                Ascii(dst, ref p, "fact");
                U32(dst, ref p, 4);
                U32(dst, ref p, (uint)(dataBytes / blockAlign));        // sample frames
            }
            Ascii(dst, ref p, "data");
            U32(dst, ref p, (uint)dataBytes);
        }

        /// <summary>Encodes <paramref name="count"/> samples into <paramref name="dst"/> at <paramref name="dstOffset"/>;
        /// returns the byte count. No allocation.</summary>
        public static int Encode(float[] src, int offset, int count, byte[] dst, int dstOffset, WavSampleFormat f)
        {
            if (f == WavSampleFormat.Float32)
            {
                if (!BitConverter.IsLittleEndian) throw new PlatformNotSupportedException("big-endian float WAV");
                Buffer.BlockCopy(src, offset * 4, dst, dstOffset, count * 4);
                return count * 4;
            }
            int q = dstOffset;
            for (int i = 0; i < count; i++)
            {
                float s = src[offset + i];
                if (s > 1f) s = 1f; else if (s < -1f) s = -1f; else if (float.IsNaN(s)) s = 0f;
                int v = (int)Math.Round(s * 32767f);
                dst[q++] = (byte)v;
                dst[q++] = (byte)(v >> 8);
            }
            return count * 2;
        }

        static void Ascii(byte[] d, ref int p, string s)
        {
            for (int i = 0; i < 4; i++) d[p++] = (byte)s[i];
        }

        static void U32(byte[] d, ref int p, uint v)
        {
            d[p++] = (byte)v; d[p++] = (byte)(v >> 8); d[p++] = (byte)(v >> 16); d[p++] = (byte)(v >> 24);
        }

        static void U16(byte[] d, ref int p, ushort v)
        {
            d[p++] = (byte)v; d[p++] = (byte)(v >> 8);
        }
    }
}
