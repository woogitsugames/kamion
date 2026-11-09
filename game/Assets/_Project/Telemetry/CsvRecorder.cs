using System;
using System.IO;
using System.Text;

namespace Game.Telemetry
{
    /// <summary>
    /// Column-oriented CSV recorder for high-rate numeric telemetry (e.g. one row per 100 Hz physics step).
    /// The caller fills <see cref="Row"/> and calls <see cref="CommitRow"/>; rows are buffered as doubles and
    /// formatted with an allocation-free fixed-point formatter into a reusable char buffer. A constant
    /// <c>trailer</c> (e.g. "config_id,commit") is appended to every row. Flushes to disk when the buffer is full,
    /// on <see cref="Flush"/> and on <see cref="Dispose"/>.
    /// </summary>
    public sealed class CsvRecorder : IDisposable
    {
        readonly StreamWriter m_Writer;
        readonly int m_Cols;
        readonly double[] m_Buffer;
        readonly int m_RowCapacity;
        readonly int[] m_Decimals;
        readonly string m_Trailer;
        char[] m_Chars;
        int m_Rows;

        public readonly double[] Row;
        public string FilePath { get; }
        public long RowsWritten { get; private set; }

        /// <param name="decimals">Fixed decimals per column (null = 4 for all).</param>
        public CsvRecorder(string path, string[] columns, string trailerHeader, string trailer, int[] decimals = null, int rowCapacity = 128)
        {
            FilePath = path;
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            m_Writer = new StreamWriter(path, false, new UTF8Encoding(false), 1 << 16);
            m_Cols = columns.Length;
            m_RowCapacity = Math.Max(1, rowCapacity);
            m_Buffer = new double[m_Cols * m_RowCapacity];
            Row = new double[m_Cols];
            m_Decimals = new int[m_Cols];
            for (int i = 0; i < m_Cols; i++) m_Decimals[i] = decimals != null && i < decimals.Length ? decimals[i] : 4;
            m_Trailer = trailer ?? "";
            m_Chars = new char[m_RowCapacity * (m_Cols * 24 + m_Trailer.Length + 4)];
            var header = new StringBuilder();
            header.Append(string.Join(",", columns));
            if (!string.IsNullOrEmpty(trailerHeader)) header.Append(',').Append(trailerHeader);
            m_Writer.WriteLine(header.ToString());
        }

        public void CommitRow()
        {
            Array.Copy(Row, 0, m_Buffer, m_Rows * m_Cols, m_Cols);
            m_Rows++;
            if (m_Rows >= m_RowCapacity) Flush();
        }

        public void Flush()
        {
            if (m_Rows == 0) { m_Writer.Flush(); return; }
            int pos = 0;
            for (int r = 0; r < m_Rows; r++)
            {
                int b = r * m_Cols;
                for (int c = 0; c < m_Cols; c++)
                {
                    if (c > 0) m_Chars[pos++] = ',';
                    pos = AppendFixed(m_Chars, pos, m_Buffer[b + c], m_Decimals[c]);
                }
                if (m_Trailer.Length > 0)
                {
                    m_Chars[pos++] = ',';
                    m_Trailer.CopyTo(0, m_Chars, pos, m_Trailer.Length);
                    pos += m_Trailer.Length;
                }
                m_Chars[pos++] = '\n';
            }
            m_Writer.Write(m_Chars, 0, pos);
            m_Writer.Flush();
            RowsWritten += m_Rows;
            m_Rows = 0;
        }

        /// <summary>Formats v with a fixed number of decimals (trailing zeros trimmed). Allocation-free.</summary>
        public static int AppendFixed(char[] buf, int pos, double v, int decimals)
        {
            if (double.IsNaN(v)) { buf[pos++] = 'N'; buf[pos++] = 'a'; buf[pos++] = 'N'; return pos; }
            if (double.IsInfinity(v)) v = v > 0 ? 9.99e15 : -9.99e15;
            if (v < 0) { buf[pos++] = '-'; v = -v; }
            if (decimals < 0) decimals = 0;
            if (decimals > 9) decimals = 9;
            long scale = 1;
            for (int i = 0; i < decimals; i++) scale *= 10;
            if (v > 9.0e15 / scale) v = 9.0e15 / scale;
            long n = (long)Math.Round(v * scale, MidpointRounding.AwayFromZero);
            long ip = n / scale, fp = n % scale;
            // integer part
            int start = pos;
            do { buf[pos++] = (char)('0' + ip % 10); ip /= 10; } while (ip > 0);
            Array.Reverse(buf, start, pos - start);
            if (decimals > 0 && fp > 0)
            {
                int digits = decimals;
                while (fp % 10 == 0) { fp /= 10; digits--; }
                buf[pos++] = '.';
                int fs = pos;
                for (int i = 0; i < digits; i++) { buf[pos++] = (char)('0' + fp % 10); fp /= 10; }
                Array.Reverse(buf, fs, digits);
            }
            if (pos - start == 1 && buf[start] == '0' && start > 0 && buf[start - 1] == '-') { buf[start - 1] = '0'; pos--; }
            return pos;
        }

        public void Dispose()
        {
            try { Flush(); }
            finally { m_Writer.Dispose(); }
        }
    }
}
