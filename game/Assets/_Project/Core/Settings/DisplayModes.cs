using System;
using System.Collections.Generic;
using System.Globalization;

namespace Game.Core.Settings
{
    /// <summary>One display mode: size in pixels and refresh rate as a ratio (Unity <c>Resolution.refreshRateRatio</c>).</summary>
    public readonly struct DisplayMode : IEquatable<DisplayMode>
    {
        public readonly int Width, Height;
        public readonly uint RefreshNumerator, RefreshDenominator;

        public DisplayMode(int width, int height, uint refreshNumerator, uint refreshDenominator)
        {
            Width = width; Height = height; RefreshNumerator = refreshNumerator; RefreshDenominator = refreshDenominator;
        }

        public double RefreshHz => RefreshDenominator > 0 ? (double)RefreshNumerator / RefreshDenominator : 0.0;
        /// <summary>Refresh rounded to 0.01 Hz: the de-duplication key (drivers list 60000/1000 and 6000/100 as two modes).</summary>
        public int RefreshCentiHz => (int)Math.Round(RefreshHz * 100.0);
        public long Pixels => (long)Width * Height;

        public bool Equals(DisplayMode o) => Width == o.Width && Height == o.Height && RefreshCentiHz == o.RefreshCentiHz;
        public override bool Equals(object obj) => obj is DisplayMode o && Equals(o);
        public override int GetHashCode() => (Width * 397) ^ (Height * 31) ^ RefreshCentiHz;

        /// <summary>"1920 × 1080 · 59,94 Hz" (Polish decimal comma); without a known refresh just the size.</summary>
        public string Label()
        {
            var ci = CultureInfo.InvariantCulture;
            string size = Width.ToString(ci) + " × " + Height.ToString(ci);
            if (RefreshDenominator == 0 || RefreshNumerator == 0) return size;
            int c = RefreshCentiHz;
            string hz = c % 100 == 0 ? (c / 100).ToString(ci) : (c / 100.0).ToString("0.##", ci).Replace('.', ',');
            return size + " · " + hz + " Hz";
        }
    }

    /// <summary>
    /// The resolution list of the settings menu (ADR 0270): <c>Screen.resolutions</c> without duplicates (same size and the
    /// same refresh to 0.01 Hz), without nonsense entries, sorted by size then refresh, ascending. Pure (tests feed lists).
    /// </summary>
    public static class ResolutionList
    {
        public static List<DisplayMode> Build(IEnumerable<DisplayMode> raw)
        {
            var list = new List<DisplayMode>();
            if (raw == null) return list;
            var seen = new HashSet<DisplayMode>();
            foreach (var m in raw)
            {
                if (m.Width <= 0 || m.Height <= 0) continue;
                if (seen.Add(m)) list.Add(m);
            }
            list.Sort((a, b) =>
            {
                int c = a.Width.CompareTo(b.Width);
                if (c != 0) return c;
                c = a.Height.CompareTo(b.Height);
                return c != 0 ? c : a.RefreshCentiHz.CompareTo(b.RefreshCentiHz);
            });
            return list;
        }

        /// <summary>
        /// Index of the entry matching a stored choice: same size with the closest refresh; otherwise the entry with the
        /// closest pixel count (a monitor swap removes the stored mode). -1 for an empty list.
        /// <paramref name="refreshHz"/> 0 = unknown: the highest refresh of that size.
        /// </summary>
        public static int IndexOf(IReadOnlyList<DisplayMode> list, int width, int height, double refreshHz)
        {
            if (list == null || list.Count == 0) return -1;
            int best = -1;
            double bestErr = double.MaxValue;
            for (int i = 0; i < list.Count; i++)
            {
                var m = list[i];
                if (m.Width != width || m.Height != height) continue;
                double err = refreshHz > 0 ? Math.Abs(m.RefreshHz - refreshHz) : -m.RefreshHz;
                if (err < bestErr) { bestErr = err; best = i; }
            }
            if (best >= 0) return best;
            long px = (long)width * height;
            long bestPx = long.MaxValue;
            for (int i = 0; i < list.Count; i++)
            {
                long d = Math.Abs(list[i].Pixels - px);
                // ties: the larger refresh (list is sorted ascending, so the later one)
                if (d <= bestPx) { bestPx = d; best = i; }
            }
            return best;
        }
    }

    /// <summary>
    /// "Keep this display mode?" countdown (ADR 0270): after a resolution / window-mode change the old mode comes back by
    /// itself unless the player confirms within <see cref="Seconds"/> (a mode the monitor cannot show must not strand him).
    /// Pure state machine; the panel ticks it with unscaled time.
    /// </summary>
    public sealed class DisplayConfirmTimer
    {
        public enum State { Idle, Pending, Kept, Reverted }

        /// <summary>WORKING_VALUE: the common value in PC games' display menus.</summary>
        public const float DefaultSeconds = 15f;

        public float Seconds { get; private set; } = DefaultSeconds;
        public float Remaining { get; private set; }
        public State Current { get; private set; } = State.Idle;
        public bool Pending => Current == State.Pending;
        /// <summary>Whole seconds shown in the dialog (15, 14, ... 1).</summary>
        public int SecondsLeft => (int)Math.Ceiling(Math.Max(0f, Remaining));

        public void Start(float seconds = DefaultSeconds)
        {
            Seconds = seconds > 0f ? seconds : DefaultSeconds;
            Remaining = Seconds;
            Current = State.Pending;
        }

        /// <summary>Advances the countdown; true exactly once, when it runs out (the caller restores the old mode).</summary>
        public bool Tick(float dt)
        {
            if (Current != State.Pending) return false;
            if (dt > 0f) Remaining -= dt;
            if (Remaining > 0f) return false;
            Remaining = 0f;
            Current = State.Reverted;
            return true;
        }

        public void Keep() { if (Current == State.Pending) Current = State.Kept; }
        public void Revert() { if (Current == State.Pending) { Current = State.Reverted; Remaining = 0f; } }
    }

    /// <summary>
    /// Whether the saved display part is applied at startup (ADR 0270). Only a choice the player made (a settings file)
    /// is applied, and never against Unity's own window arguments (<c>-screen-width</c>, <c>-screen-height</c>,
    /// <c>-screen-fullscreen</c>, <c>-window-mode</c>, <c>-popupwindow</c>): scripts/build-windows.ps1 runs the evidence pass
    /// in a 1600x900 window through them (ADR 0261), and the first launch keeps the ProjectSettings default.
    /// </summary>
    public static class StartupDisplayPolicy
    {
        public static bool ShouldApply(bool fromSettingsFile, IReadOnlyList<string> commandLine)
        {
            if (!fromSettingsFile) return false;
            if (commandLine == null) return true;
            for (int i = 0; i < commandLine.Count; i++)
            {
                string a = commandLine[i];
                if (string.IsNullOrEmpty(a)) continue;
                a = a.ToLowerInvariant();
                if (a.StartsWith("-screen-", StringComparison.Ordinal) || a == "-window-mode" || a == "-popupwindow") return false;
            }
            return true;
        }
    }
}
