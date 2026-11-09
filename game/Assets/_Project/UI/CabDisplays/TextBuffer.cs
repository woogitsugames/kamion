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

        /// <summary>Fixed-point number with <paramref name="decimals"/> digits after a decimal comma (rounded half away from zero).</summary>
        public TextBuffer AppendFixed(double v, int decimals, bool group = false)
        {
            long scale = 1;
            for (int i = 0; i < decimals; i++) scale *= 10;
            bool neg = v < 0;
            long n = (long)System.Math.Round(System.Math.Abs(v) * scale, System.MidpointRounding.AwayFromZero);
            if (neg && n != 0) Append('-');
            Append(n / scale, 1, group);
            if (decimals > 0)
            {
                Append(',');
                Append(n % scale, decimals);
            }
            return this;
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
