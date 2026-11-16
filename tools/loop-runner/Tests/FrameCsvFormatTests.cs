using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using Game.Telemetry;
using Xunit;
using Xunit.Abstractions;

namespace LoopRunner.Tests
{
    /// <summary>ADR 0244: allocation-free frametimes.csv formatting keeps the text of the former ToString("F*") rows.</summary>
    public class FrameCsvFormatTests
    {
        static readonly CultureInfo Ci = CultureInfo.InvariantCulture;
        readonly ITestOutputHelper m_Out;
        public FrameCsvFormatTests(ITestOutputHelper output) { m_Out = output; }

        static string Fixed(double v, int decimals)
        {
            var buf = new char[64];
            int n = FrameCsvFormat.AppendFixed(buf, 0, v, decimals);
            return new string(buf, 0, n);
        }

        static string Int(long v)
        {
            var buf = new char[32];
            int n = FrameCsvFormat.AppendInt(buf, 0, v);
            return new string(buf, 0, n);
        }

        [Theory]
        [InlineData(0f, 3)]
        [InlineData(33.333332f, 3)]
        [InlineData(16.666666f, 3)]
        [InlineData(0.75f, 2)]
        [InlineData(1f, 2)]
        [InlineData(1799.9999f, 4)]
        [InlineData(1234.5677f, 4)]
        [InlineData(999.9995f, 3)]
        [InlineData(0.0005f, 3)]
        [InlineData(-1.5f, 3)]
        public void AppendFixed_MatchesInvariantToString(float v, int decimals)
        {
            Assert.Equal(v.ToString("F" + decimals, Ci), Fixed(v, decimals));
        }

        /// <summary>Exact binary ties round half away from zero (.NET 8 ToString prints 0.12 / 2 here).</summary>
        [Theory]
        [InlineData(0.125f, 2, "0.13")]
        [InlineData(0.375f, 2, "0.38")]
        [InlineData(2.5f, 0, "3")]
        [InlineData(41.5625f, 3, "41.563")]
        [InlineData(33210.78125f, 4, "33210.7813")]
        public void AppendFixed_ExactTiesRoundAwayFromZero(float v, int decimals, string expected)
        {
            Assert.Equal(expected, Fixed(v, decimals));
        }

        [Theory]
        [InlineData(0L)]
        [InlineData(7L)]
        [InlineData(-42L)]
        [InlineData(1234567890123L)]
        [InlineData(long.MaxValue)]
        [InlineData(long.MinValue)]
        public void AppendInt_MatchesInvariantToString(long v)
        {
            Assert.Equal(v.ToString(Ci), Int(v));
        }

        [Fact]
        public void AppendFixed_NonFinite()
        {
            Assert.Equal("NaN", Fixed(double.NaN, 3));
            Assert.Equal("Infinity", Fixed(double.PositiveInfinity, 3));
            Assert.Equal("-Infinity", Fixed(double.NegativeInfinity, 3));
        }

        /// <summary>
        /// The value ranges of the frame CSV (session time F4 up to 10 h, frame / CPU / GPU ms F3 up to 2 s, render
        /// scale F2): 200 000 random floats per column format print exactly like float.ToString("F*") on .NET 8, except
        /// exact binary ties at the last printed digit (e.g. 41.5625 at F3), which .NET 8 sometimes rounds down and
        /// AppendFixed always rounds away from zero. Those may differ by one unit of the last digit, nothing else.
        /// </summary>
        [Theory]
        [InlineData(4, 0.0, 36000.0)]
        [InlineData(3, 0.0, 2000.0)]
        [InlineData(3, 0.0, 50.0)]
        [InlineData(2, 0.3, 1.0)]
        public void AppendFixed_RandomFloatsInCsvRanges_MatchToStringExceptExactTies(int decimals, double lo, double hi)
        {
            var rng = new Random(244 + decimals);
            int ties = 0;
            const int n = 200_000;
            double unit = Math.Pow(10, -decimals);
            for (int i = 0; i < n; i++)
            {
                float v = (float)(lo + rng.NextDouble() * (hi - lo));
                string expected = v.ToString("F" + decimals, Ci), got = Fixed(v, decimals);
                if (expected == got) continue;
                // decimal holds the float's exact binary value here (< 2^24 * 2^-k, at most 28 digits)
                decimal scaled = (decimal)(double)v * (decimal)Math.Pow(10, decimals);
                bool exactTie = scaled - decimal.Truncate(scaled) == 0.5m;
                double diff = double.Parse(got, Ci) - double.Parse(expected, Ci);
                Assert.True(exactTie && Math.Abs(diff - unit) < unit * 1e-3,
                    $"{v:R} F{decimals}: expected {expected} got {got} (exact tie {exactTie})");
                ties++;
            }
            m_Out.WriteLine($"F{decimals} [{lo}, {hi}]: {ties} / {n} exact ties rounded away from zero (.NET 8 rounded them down)");
        }

        /// <summary>Reference text: invariant ToString("F*"), exact binary ties rounded away from zero (see above).</summary>
        static string Ref(float v, int decimals)
        {
            decimal exact = (decimal)(double)v;
            return Math.Round(exact, decimals, MidpointRounding.AwayFromZero).ToString("F" + decimals, Ci);
        }

        /// <summary>Row text = the former StringBuilder row (6 columns) + mirror_n + ab (empty while A/B is off).</summary>
        [Fact]
        public void AppendRow_MatchesFormerRowPlusMirrorAndAbColumns()
        {
            var rng = new Random(2440);
            var buf = new char[FrameCsvFormat.MaxRowChars * 4];
            for (int i = 0; i < 20_000; i++)
            {
                long frame = rng.Next(0, int.MaxValue);
                float t = (float)(rng.NextDouble() * 3600), ms = (float)(rng.NextDouble() * 120), cpu = (float)(rng.NextDouble() * 60),
                    gpu = (float)(rng.NextDouble() * 60), scale = (float)(0.5 + rng.NextDouble() * 0.5);
                int mirrors = rng.Next(0, 7), ab = rng.Next(-1, 2);
                string former = frame.ToString(Ci) + "," + Ref(t, 4) + "," + Ref(ms, 3) + "," + Ref(cpu, 3)
                                + "," + Ref(gpu, 3) + "," + Ref(scale, 2);
                string expected = former + "," + mirrors.ToString(Ci) + "," + (ab >= 0 ? ab.ToString(Ci) : "") + "\n";
                int len = FrameCsvFormat.AppendRow(buf, 0, frame, t, ms, cpu, gpu, scale, mirrors, ab);
                Assert.Equal(expected, new string(buf, 0, len));
                Assert.True(len <= FrameCsvFormat.MaxRowChars);
            }
        }

        [Fact]
        public void AppendRow_WorstCaseFitsMaxRowChars()
        {
            var buf = new char[FrameCsvFormat.MaxRowChars];
            int len = FrameCsvFormat.AppendRow(buf, 0, long.MinValue, -float.MaxValue, -float.MaxValue, -float.MaxValue, -float.MaxValue,
                -float.MaxValue, int.MinValue, int.MaxValue);
            Assert.True(len <= FrameCsvFormat.MaxRowChars, $"{len} chars");
        }

        [Fact]
        public void AppendRow_IsAllocationFree()
        {
            var buf = new char[FrameCsvFormat.MaxRowChars * 128];
            int Fill(int rows)
            {
                int pos = 0;
                for (int i = 0; i < rows; i++)
                    pos = FrameCsvFormat.AppendRow(buf, pos, 1000 + i, 12.3456f + i, 33.333f, 21.5f, 18.25f, 0.85f, 2, -1);
                return pos;
            }
            Fill(128);   // JIT warm-up
            long before = GC.GetAllocatedBytesForCurrentThread();
            int total = 0;
            for (int k = 0; k < 100; k++) total += Fill(128);
            long bytes = GC.GetAllocatedBytesForCurrentThread() - before;
            Assert.True(total > 0);
            Assert.Equal(0L, bytes);
        }

        /// <summary>The header is the frametimes.csv v1 contract of tools/perf (perfgate.formats.FRAMETIMES_V1_COLUMNS).</summary>
        [Fact]
        public void Header_MatchesPerfgateContract()
        {
            string formats = Path.Combine(RepoRoot(), "tools", "perf", "src", "perfgate", "formats.py");
            string py = File.ReadAllText(formats);
            var m = Regex.Match(py, @"FRAMETIMES_V1_COLUMNS\s*=\s*\(([^)]*)\)", RegexOptions.Singleline);
            Assert.True(m.Success, "FRAMETIMES_V1_COLUMNS not found in " + formats);
            var cols = Regex.Matches(m.Groups[1].Value, "\"([a-z_0-9]+)\"").Select(x => x.Groups[1].Value);
            string expected = string.Join(",", cols);
            Assert.True(expected == FrameCsvFormat.Header, $"header {FrameCsvFormat.Header} vs perfgate {expected}");
        }

        static string RepoRoot()
        {
            var d = new DirectoryInfo(AppContext.BaseDirectory);
            while (d != null && !File.Exists(Path.Combine(d.FullName, "CLAUDE.md"))) d = d.Parent;
            Assert.NotNull(d);
            return d.FullName;
        }
    }
}
