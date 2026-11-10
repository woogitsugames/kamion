using System;
using System.Globalization;
using System.Text;
using UnityEngine;

namespace Game.Controls
{
    /// <summary>
    /// Writes what the driver did to logcat as <c>[CONTROLS]</c> lines so the owner's session can be replayed by reading
    /// <c>adb logcat -d -s Unity | grep CONTROLS</c>. One-shot commands (selector, shift, parking brake, ...) are logged the
    /// frame they happen; the continuous axes (steer, throttle, brake) are logged on change, at most
    /// <see cref="MinIntervalS"/> apart, plus one line when all three return to rest. Idle frames allocate nothing.
    /// Format: <c>[CONTROLS] in t=12.35 steer=+0.31 thr=0.80 brk=0.00 v=45.2</c> (t = seconds since the logger started,
    /// v = signed km/h) and <c>[CONTROLS] cmd t=13.10 selector=Reverse shift=+1 ...</c>.
    /// </summary>
    public sealed class ControlInputLogger
    {
        public const float MinIntervalS = 0.25f, ChangeThreshold = 0.05f;

        readonly Action<string> m_Sink;
        readonly StringBuilder m_Sb = new StringBuilder(160);
        float m_T0 = float.NaN, m_LastAxisT = float.NegativeInfinity;
        float m_Steer, m_Throttle, m_Brake;
        bool m_AtRest = true;

        /// <summary>The line count written so far (tests).</summary>
        public int Lines { get; private set; }

        public ControlInputLogger(Action<string> sink = null) { m_Sink = sink ?? (s => Debug.Log(s)); }

        public void Observe(float time, in DriverIntent intent, float speedKmh)
        {
            if (float.IsNaN(m_T0)) m_T0 = time;
            float steer = intent.SteerActive ? intent.Steer : 0f;
            bool rest = Mathf.Abs(steer) < 0.01f && intent.Throttle < 0.01f && intent.Brake < 0.01f;
            bool changed = Mathf.Abs(steer - m_Steer) >= ChangeThreshold || Mathf.Abs(intent.Throttle - m_Throttle) >= ChangeThreshold
                           || Mathf.Abs(intent.Brake - m_Brake) >= ChangeThreshold;
            if (time - m_LastAxisT >= MinIntervalS && ((!rest && changed) || (rest && !m_AtRest)))
            {
                var ci = CultureInfo.InvariantCulture;
                Begin("in", time);
                m_Sb.Append(" steer=").Append(steer.ToString("+0.00;-0.00;+0.00", ci))
                    .Append(" thr=").Append(intent.Throttle.ToString("F2", ci))
                    .Append(" brk=").Append(intent.Brake.ToString("F2", ci))
                    .Append(" v=").Append(speedKmh.ToString("F1", ci));
                Emit();
                m_Steer = steer; m_Throttle = intent.Throttle; m_Brake = intent.Brake;
                m_AtRest = rest; m_LastAxisT = time;
            }

            if (intent.Selector != SelectorRequest.None || intent.ShiftDelta != 0 || intent.ToggleParkingBrake || intent.ToggleManual
                || intent.RetarderDelta != 0 || intent.ToggleCoupling || intent.ToggleLandingGear || intent.ToggleBrakeCruise
                || intent.ToggleReverseCamera)
            {
                Begin("cmd", time);
                if (intent.Selector != SelectorRequest.None) m_Sb.Append(" selector=").Append(intent.Selector.ToString());
                if (intent.ShiftDelta != 0) m_Sb.Append(" shift=").Append(intent.ShiftDelta > 0 ? "+1" : "-1");
                if (intent.ToggleParkingBrake) m_Sb.Append(" parking=toggle");
                if (intent.ToggleManual) m_Sb.Append(" manual=toggle");
                if (intent.RetarderDelta != 0) m_Sb.Append(" retarder=").Append(intent.RetarderDelta > 0 ? "+1" : "-1");
                if (intent.ToggleCoupling) m_Sb.Append(" coupling=toggle");
                if (intent.ToggleLandingGear) m_Sb.Append(" landingGear=toggle");
                if (intent.ToggleBrakeCruise) m_Sb.Append(" brakeCruise=toggle");
                if (intent.ToggleReverseCamera) m_Sb.Append(" reverseCam=toggle");
                Emit();
            }
        }

        /// <summary>A named event (camera mode, menu, respawn): <c>[CONTROLS] event t=.. text</c>.</summary>
        public void Event(float time, string text)
        {
            if (float.IsNaN(m_T0)) m_T0 = time;
            Begin("event", time);
            m_Sb.Append(' ').Append(text);
            Emit();
        }

        void Begin(string kind, float time)
        {
            m_Sb.Length = 0;
            m_Sb.Append("[CONTROLS] ").Append(kind).Append(" t=").Append((time - m_T0).ToString("F2", CultureInfo.InvariantCulture));
        }

        void Emit() { Lines++; m_Sink(m_Sb.ToString()); }
    }
}
