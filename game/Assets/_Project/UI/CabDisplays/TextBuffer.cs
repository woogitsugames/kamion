namespace Game.UI.CabDisplays
{
    /// <summary>
    /// Fixed char buffer for display numbers without string allocations (zero GC in the refresh loop). Polish number
    /// style as on the reference cluster: decimal comma, thin-space thousands grouping ("184 327 km", "10,4").
    /// </summary>
    public sealed class TextBuffer
    {
        /// <summary>Thousands separator (narrow no-break space is not in every font atlas; a normal space reads the same).</summary>
        public const char Group = ' ';
        public readonly char[] Chars;
        public int Length { get; private set; }

        public TextBuffer(int capacity = 32) { Chars = new char[capacity]; }

        public TextBuffer Clear() { Length = 0; return this; }

        public TextBuffer Append(char c)
        {
            if (Length < Chars.Length) Chars[Length++] = c;
            return this;
        }

        public TextBuffer Append(string s)
        {
            if (s == null) return this;
            for (int i = 0; i < s.Length; i++) Append(s[i]);
            return this;
        }

        /// <summary>Integer, optionally zero-padded to <paramref name="minDigits"/>, optionally grouped by thousands.</summary>
        public TextBuffer Append(long v, int minDigits = 1, bool group = false)
        {
            if (v < 0) { Append('-'); v = -v; }
            // Digits right to left into the tail of the buffer, then move.
            int start = Length, digits = 0;
            do
            {
                if (group && digits > 0 && digits % 3 == 0) Append(Group);
                Append((char)('0' + (int)(v % 10)));
                v /= 10; digits++;
            } while (v > 0 || digits < minDigits);
            Reverse(start, Length - 1);
            return this;
        }

        /// <summary>Fixed-point number with <paramref name="decimals"/> digits after a decimal separator (rounded half away
        /// from zero). <paramref name="sep"/> ',' = Polish cluster style, '.' = invariant HUD style (float.ToString("F1", InvariantCulture)).</summary>
        public TextBuffer AppendFixed(double v, int decimals, bool group = false, char sep = ',')
        {
            long scale = 1;
            for (int i = 0; i < decimals; i++) scale *= 10;
            bool neg = v < 0;
            long n = (long)System.Math.Round(System.Math.Abs(v) * scale, System.MidpointRounding.AwayFromZero);
            if (neg && n != 0) Append('-');
            Append(n / scale, 1, group);
            if (decimals > 0)
            {
                Append(sep);
                Append(n % scale, decimals);
            }
            return this;
        }

        /// <summary>Signed fixed-point, .NET "+0.00;-0.00" style (positive section also for zero and -0.0), with an explicit separator.</summary>
        public TextBuffer AppendSigned(double v, int decimals, char sep = '.')
        {
            Append(v < 0 ? '-' : '+');
            return AppendFixed(System.Math.Abs(v), decimals, false, sep);
        }

        /// <summary>Fixed-point right-aligned in <paramref name="width"/> (PadLeft): spaces are inserted in place, no allocation.</summary>
        public TextBuffer AppendFixedPadded(double v, int decimals, char sep, int width)
        {
            int start = Length;
            AppendFixed(v, decimals, false, sep);
            PadLeftInPlace(start, width);
            return this;
        }

        /// <summary>Signed fixed-point right-aligned in <paramref name="width"/> (PadLeft).</summary>
        public TextBuffer AppendSignedPadded(double v, int decimals, char sep, int width)
        {
            int start = Length;
            AppendSigned(v, decimals, sep);
            PadLeftInPlace(start, width);
            return this;
        }

        /// <summary>String left-aligned in <paramref name="width"/> (PadRight): trailing spaces appended when shorter.</summary>
        public TextBuffer AppendRight(string s, int width)
        {
            if (s == null) return this;
            Append(s);
            for (int i = s.Length; i < width; i++) Append(' ');
            return this;
        }

        /// <summary>File name of a path (after the last '/' or '\\') without System.IO.Path.GetFileName allocating a string.</summary>
        public TextBuffer AppendFileName(string path)
        {
            if (path == null) return this;
            int slash = -1;
            for (int i = path.Length - 1; i >= 0; i--)
            {
                char c = path[i];
                if (c == '/' || c == '\\') { slash = i; break; }
            }
            for (int i = slash + 1; i < path.Length; i++) Append(path[i]);
            return this;
        }

        void PadLeftInPlace(int start, int width)
        {
            int pad = width - (Length - start);
            if (pad <= 0 || Length + pad > Chars.Length) return;
            for (int i = Length - 1; i >= start; i--) Chars[i + pad] = Chars[i];
            for (int i = 0; i < pad; i++) Chars[start + i] = ' ';
            Length += pad;
        }

        /// <summary>Clock "hh:mm" from minutes of the day.</summary>
        public TextBuffer AppendClock(int minutesOfDay)
        {
            minutesOfDay = ((minutesOfDay % 1440) + 1440) % 1440;
            Append(minutesOfDay / 60, 2);
            Append(':');
            Append(minutesOfDay % 60, 2);
            return this;
        }

        /// <summary>Duration "HHhMM" (tachograph style) from minutes.</summary>
        public TextBuffer AppendDurationHm(int minutes)
        {
            if (minutes < 0) minutes = 0;
            Append(minutes / 60, 2);
            Append('h');
            Append(minutes % 60, 2);
            return this;
        }

        void Reverse(int a, int b)
        {
            while (a < b) { char t = Chars[a]; Chars[a] = Chars[b]; Chars[b] = t; a++; b--; }
        }

        public override string ToString() => new string(Chars, 0, Length);   // tests / logs only
    }
}
