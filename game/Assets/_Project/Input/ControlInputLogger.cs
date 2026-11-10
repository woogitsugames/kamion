using System;
using System.Globalization;
using System.Text;
using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// Records what the driver did and writes it to logcat as <c>[CONTROLS]</c> lines, so the owner's session can be
    /// replayed with <c>adb logcat -d -s Unity | grep CONTROLS</c>.
    /// Hot path (<see cref="Observe"/>, <see cref="Event"/>) only copies plain values into a preallocated ring of structs:
    /// zero allocation, no strings built. Lines are formatted and written by <see cref="Flush"/>, which the game calls on
    /// menu return, on pause / focus loss / destroy, and via <see cref="TryFlush"/> (idle moment, at most every
    /// <see cref="FlushIntervalS"/>, or when the ring is three quarters full).
    /// Axes are recorded on change (at most every <see cref="MinIntervalS"/>, plus once when all return to rest);
    /// one-shot commands the frame they happen. Format: <c>[CONTROLS] in t=12.35 steer=+0.31 thr=0.80 brk=0.00 v=45.2 hw=+120</c> (steer = target, hw = cab wheel [deg]),
    /// <c>[CONTROLS] cmd t=13.10 selector=Reverse shift=+1 ...</c>, <c>[CONTROLS] event t=.. text</c>.
    /// </summary>
    public sealed class ControlInputLogger
    {
        public const float MinIntervalS = 0.25f, ChangeThreshold = 0.05f, FlushIntervalS = 10f;
        public const int Capacity = 2048;

        enum Kind : byte { Axes, Command, Event }

        struct Entry
        {
            public Kind kind;
            public float t, steer, thr, brk, speed, hw;
            public byte selector; public sbyte shift, retarder;
            public ushort toggles;
            public string text;   // reference to a caller-owned (cached) string, never built here
        }

        const ushort TParking = 1, TManual = 2, TCoupling = 4, TLanding = 8, TCruise = 16, TRevCam = 32;

        readonly Action<string> m_Sink;
        readonly Entry[] m_Ring = new Entry[Capacity];
        readonly StringBuilder m_Sb = new StringBuilder(160);
        int m_Head, m_Count, m_Dropped;
        float m_T0 = float.NaN, m_LastAxisT = float.NegativeInfinity, m_LastFlushT = float.NaN;
        float m_Steer, m_Throttle, m_Brake;
        bool m_AtRest = true;

        /// <summary>Lines written by <see cref="Flush"/> so far (tests).</summary>
        public int Lines { get; private set; }
        /// <summary>Entries recorded and not yet written.</summary>
        public int Pending => m_Count;

        public ControlInputLogger(Action<string> sink = null) { m_Sink = sink ?? WriteNoStack; }

        /// <summary>
        /// Debug.Log without the managed stack trace: the Player's "Log" stack-trace type is ScriptOnly, which made every
        /// [CONTROLS] line in the owner's logcat (S24+, 2026-11-10) carry a second DebugLogHandler line.
        /// </summary>
        public static void WriteNoStack(string line) => Debug.LogFormat(LogType.Log, LogOption.NoStacktrace, null, "{0}", line);

        /// <param name="handwheelDeg">Simulated cab steering-wheel angle [deg] (ADR 0058), NaN = not logged.</param>
        public void Observe(float time, in DriverIntent intent, float speedKmh, float handwheelDeg = float.NaN)
        {
            if (float.IsNaN(m_T0)) m_T0 = time;
            float steer = intent.SteerActive ? intent.Steer : 0f;
            bool rest = Mathf.Abs(steer) < 0.01f && intent.Throttle < 0.01f && intent.Brake < 0.01f;
            bool changed = Mathf.Abs(steer - m_Steer) >= ChangeThreshold || Mathf.Abs(intent.Throttle - m_Throttle) >= ChangeThreshold
                           || Mathf.Abs(intent.Brake - m_Brake) >= ChangeThreshold;
            if (time - m_LastAxisT >= MinIntervalS && ((!rest && changed) || (rest && !m_AtRest)))
            {
                ref Entry e = ref Next();
                e.kind = Kind.Axes; e.t = time - m_T0; e.steer = steer; e.thr = intent.Throttle; e.brk = intent.Brake; e.speed = speedKmh; e.hw = handwheelDeg;
                m_Steer = steer; m_Throttle = intent.Throttle; m_Brake = intent.Brake;
                m_AtRest = rest; m_LastAxisT = time;
            }

            if (intent.Selector != SelectorRequest.None || intent.ShiftDelta != 0 || intent.ToggleParkingBrake || intent.ToggleManual
                || intent.RetarderDelta != 0 || intent.ToggleCoupling || intent.ToggleLandingGear || intent.ToggleBrakeCruise
                || intent.ToggleReverseCamera)
            {
                ref Entry e = ref Next();
                e.kind = Kind.Command; e.t = time - m_T0;
                e.selector = (byte)intent.Selector;
                e.shift = (sbyte)Mathf.Clamp(intent.ShiftDelta, -1, 1);
                e.retarder = (sbyte)Mathf.Clamp(intent.RetarderDelta, -1, 1);
                ushort tg = 0;
                if (intent.ToggleParkingBrake) tg |= TParking;
                if (intent.ToggleManual) tg |= TManual;
                if (intent.ToggleCoupling) tg |= TCoupling;
                if (intent.ToggleLandingGear) tg |= TLanding;
                if (intent.ToggleBrakeCruise) tg |= TCruise;
                if (intent.ToggleReverseCamera) tg |= TRevCam;
                e.toggles = tg;
            }
        }

        /// <summary>Records a named event. <paramref name="text"/> must be a cached/literal string (it is stored by reference).</summary>
        public void Event(float time, string text)
        {
            if (float.IsNaN(m_T0)) m_T0 = time;
            ref Entry e = ref Next();
            e.kind = Kind.Event; e.t = time - m_T0; e.text = text;
        }

        ref Entry Next()
        {
            if (m_Count == Capacity) { m_Head = (m_Head + 1) % Capacity; m_Count--; m_Dropped++; }   // overwrite the oldest
            int idx = (m_Head + m_Count) % Capacity;
            m_Count++;
            m_Ring[idx] = default;
            return ref m_Ring[idx];
        }

        /// <summary>Writes pending lines when it is a good moment: <paramref name="idle"/> (no input active) and
        /// <see cref="FlushIntervalS"/> elapsed, or the ring is nearly full. Returns true if it flushed.</summary>
        public bool TryFlush(float time, bool idle)
        {
            if (m_Count == 0) { return false; }
            if (float.IsNaN(m_LastFlushT)) m_LastFlushT = time;
            if (m_Count >= Capacity * 3 / 4 || (idle && time - m_LastFlushT >= FlushIntervalS)) { Flush(time); return true; }
            return false;
        }

        /// <summary>Formats and writes every pending entry (allocates; keep off the driving hot path).</summary>
        public void Flush(float time = 0f)
        {
            m_LastFlushT = time;
            var ci = CultureInfo.InvariantCulture;
            if (m_Dropped > 0) { Write("[CONTROLS] event dropped=" + m_Dropped.ToString(ci)); m_Dropped = 0; }
            for (int i = 0; i < m_Count; i++)
            {
                ref Entry e = ref m_Ring[(m_Head + i) % Capacity];
                m_Sb.Length = 0;
                m_Sb.Append("[CONTROLS] ").Append(e.kind == Kind.Axes ? "in" : e.kind == Kind.Command ? "cmd" : "event")
                    .Append(" t=").Append(e.t.ToString("F2", ci));
                switch (e.kind)
                {
                    case Kind.Axes:
                        m_Sb.Append(" steer=").Append(e.steer.ToString("+0.00;-0.00;+0.00", ci))
                            .Append(" thr=").Append(e.thr.ToString("F2", ci))
                            .Append(" brk=").Append(e.brk.ToString("F2", ci))
                            .Append(" v=").Append(e.speed.ToString("F1", ci));
                        if (!float.IsNaN(e.hw)) m_Sb.Append(" hw=").Append(e.hw.ToString("+0;-0;+0", ci));
                        break;
                    case Kind.Command:
                        if (e.selector != 0) m_Sb.Append(" selector=").Append(((SelectorRequest)e.selector).ToString());
                        if (e.shift != 0) m_Sb.Append(" shift=").Append(e.shift > 0 ? "+1" : "-1");
                        if ((e.toggles & TParking) != 0) m_Sb.Append(" parking=toggle");
                        if ((e.toggles & TManual) != 0) m_Sb.Append(" manual=toggle");
                        if (e.retarder != 0) m_Sb.Append(" retarder=").Append(e.retarder > 0 ? "+1" : "-1");
                        if ((e.toggles & TCoupling) != 0) m_Sb.Append(" coupling=toggle");
                        if ((e.toggles & TLanding) != 0) m_Sb.Append(" landingGear=toggle");
                        if ((e.toggles & TCruise) != 0) m_Sb.Append(" brakeCruise=toggle");
                        if ((e.toggles & TRevCam) != 0) m_Sb.Append(" reverseCam=toggle");
                        break;
                    default:
                        m_Sb.Append(' ').Append(e.text);
                        break;
                }
                Write(m_Sb.ToString());
            }
            m_Head = 0; m_Count = 0;
        }

        void Write(string line) { Lines++; m_Sink(line); }
    }
}
