using System;

namespace Game.Telemetry
{
    /// <summary>
    /// ADR 0244: allocation-free text formatting for the per-frame diagnostics CSV (Boot <see cref="DiagnosticsSampler"/>,
    /// frametimes.csv v1). Pure C# (no UnityEngine): the same source is compiled by tools/loop-runner for .NET tests.
    /// The previous FlushCsv built every row with float.ToString / StringBuilder.Append(long), i.e. ~6 managed strings per
    /// frame in every build (ESTIMATED ~6 KB/s at 30 FPS). Rows are written into a reused char buffer instead.
    /// </summary>
    public static class FrameCsvFormat
    {
        /// <summary>Header of frametimes.csv v1 (tools/perf/src/perfgate/formats.py FRAMETIMES_V1_COLUMNS).</summary>
        public const string Header = "frame,t_s,frame_ms,cpu_main_ms,gpu_ms,render_scale,mirror_n,ab";

        /// <summary>Upper bound of the characters one row can take (8 columns, clamped magnitudes, separators, newline).</summary>
        public const int MaxRowChars = 8 * 24 + 8;

        /// <summary>
        /// Appends one frametimes.csv row: frame, t_s (F4), frame_ms (F3), cpu_main_ms (F3), gpu_ms (F3),
        /// render_scale (F2), mirror_n (integer), ab (integer, empty while the A/B toggler is off: <paramref name="ab"/> &lt; 0).
        /// Returns the new write position. <paramref name="buf"/> needs <see cref="MaxRowChars"/> free characters.
        /// </summary>
        public static int AppendRow(char[] buf, int pos, long frame, float tS, float frameMs, float cpuMs, float gpuMs,
            float renderScale, int mirrors, int ab)
        {
            pos = AppendInt(buf, pos, frame); buf[pos++] = ',';
            pos = AppendFixed(buf, pos, tS, 4); buf[pos++] = ',';
            pos = AppendFixed(buf, pos, frameMs, 3); buf[pos++] = ',';
            pos = AppendFixed(buf, pos, cpuMs, 3); buf[pos++] = ',';
            pos = AppendFixed(buf, pos, gpuMs, 3); buf[pos++] = ',';
            pos = AppendFixed(buf, pos, renderScale, 2); buf[pos++] = ',';
            pos = AppendInt(buf, pos, mirrors); buf[pos++] = ',';
            if (ab >= 0) pos = AppendInt(buf, pos, ab);
            buf[pos++] = '\n';
            return pos;
        }

        /// <summary>Decimal integer, invariant culture ("-" sign, no grouping). Allocation-free.</summary>
        public static int AppendInt(char[] buf, int pos, long v)
        {
            if (v == long.MinValue) { const string min = "-9223372036854775808"; min.CopyTo(0, buf, pos, min.Length); return pos + min.Length; }
            if (v < 0) { buf[pos++] = '-'; v = -v; }
            int start = pos;
            do { buf[pos++] = (char)('0' + (int)(v % 10)); v /= 10; } while (v > 0);
            Array.Reverse(buf, start, pos - start);
            return pos;
        }

        /// <summary>
        /// Same text as <c>v.ToString("F" + decimals, CultureInfo.InvariantCulture)</c> for finite values with
        /// |v| &lt; 9e15 / 10^decimals: fixed decimals with trailing zeros, rounding half away from zero, "-0.000" for
        /// small negative values that round to zero (as .NET Core 3.0+). Digits beyond the float's precision follow the
        /// exact binary value (the Mono runtime prints 7 significant digits first; differences are in the last digit
        /// only, see ADR 0244). NaN / infinity print as NaN / ±Infinity. Allocation-free.
        /// </summary>
        public static int AppendFixed(char[] buf, int pos, double v, int decimals)
        {
            if (double.IsNaN(v)) return Copy(buf, pos, "NaN");
            if (double.IsPositiveInfinity(v)) return Copy(buf, pos, "Infinity");
            if (double.IsNegativeInfinity(v)) return Copy(buf, pos, "-Infinity");
            if (decimals < 0) decimals = 0;
            if (decimals > 9) decimals = 9;
            if (v < 0 || BitConverter.DoubleToInt64Bits(v) < 0) { buf[pos++] = '-'; v = -v; }
            long scale = 1;
            for (int i = 0; i < decimals; i++) scale *= 10;
            double limit = 9.0e15 / scale;
            if (v > limit) v = limit;
            long n = (long)Math.Round(v * scale, MidpointRounding.AwayFromZero);
            pos = AppendInt(buf, pos, n / scale);
            if (decimals > 0)
            {
                buf[pos++] = '.';
                long fp = n % scale;
                for (int i = decimals - 1; i >= 0; i--) { buf[pos + i] = (char)('0' + (int)(fp % 10)); fp /= 10; }
                pos += decimals;
            }
            return pos;
        }

        static int Copy(char[] buf, int pos, string s)
        {
            s.CopyTo(0, buf, pos, s.Length);
            return pos + s.Length;
        }
    }
}
