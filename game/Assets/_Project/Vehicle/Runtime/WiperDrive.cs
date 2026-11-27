using UnityEngine;

namespace Game.Vehicle.Runtime
{
    public enum WiperMode : byte { Off, Intermittent, Slow, Fast }

    /// <summary>One clock for the outbound and return stroke, the park contact and the intermittent dwell.</summary>
    public sealed class WiperDrive
    {
        // WORKING_VALUE, seconds per round trip and parked seconds between intermittent sweeps.
        public const float SlowSeconds = 1.2f, FastSeconds = 0.8f, IntermittentPause = 2.4f;
        public const float SweepDegrees = 95f; // Imported TRAKT pivots sweep up around their local +Y.

        public WiperMode Mode { get; private set; }
        public float CycleSeconds { get; private set; }
        public float Phase { get; private set; }
        public int Starts { get; private set; }
        public int Parks { get; private set; }

        WiperMode m_CycleMode;
        float m_Elapsed, m_Wait;
        bool m_Moving;

        public void CycleMode() => Mode = (WiperMode)(((int)Mode + 1) % 4);

        public static Quaternion Rotation(float phase) =>
            Quaternion.AngleAxis(SweepDegrees * (0.5f - 0.5f * Mathf.Cos(2f * Mathf.PI * phase)), Vector3.up);

        public void Step(float dt)
        {
            if (dt <= 0f) return;
            if (m_Moving)
            {
                m_Elapsed += dt;
                if (m_Elapsed < CycleSeconds)
                {
                    Phase = m_Elapsed / CycleSeconds;
                    return;
                }
                m_Moving = false;
                Phase = 0f;
                Parks++;
                if (Mode == WiperMode.Intermittent && m_CycleMode == Mode)
                {
                    m_Wait = IntermittentPause - (m_Elapsed - CycleSeconds);
                    return;
                }
            }
            else if (Mode == WiperMode.Intermittent && m_Wait > 0f)
            {
                m_Wait -= dt;
                if (m_Wait > 0f) return;
            }

            m_Wait = 0f;
            if (Mode == WiperMode.Off) return;
            m_CycleMode = Mode;
            CycleSeconds = Mode == WiperMode.Fast ? FastSeconds : SlowSeconds;
            m_Moving = true;
            m_Elapsed = 0f;
            Starts++;
        }
    }
}
