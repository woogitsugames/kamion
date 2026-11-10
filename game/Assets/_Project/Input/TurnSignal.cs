using UnityEngine;

namespace Game.Controls
{
    /// <summary>One-shot turn-signal command (stalk / touch button / key).</summary>
    public enum TurnSignalRequest : byte { None = 0, Left = 1, Right = 2, Hazard = 3 }

    /// <summary>
    /// Turn-signal stalk + flasher unit. Lever: 0 off, -1 left, +1 right, 2 hazard (same coding as the cab screens).
    /// - A left / right request toggles that side (the opposite side switches over, like moving the stalk through the
    ///   detent); hazard is a separate switch that overrides the stalk and never self-cancels.
    /// - Self-cancel like a real stalk: the lever is armed once the road wheels have turned past <see cref="ArmAngle"/> in
    ///   the signalled direction and drops out when they return below <see cref="ReleaseAngle"/> (steering wheel back
    ///   towards centre). Lane changes below the arm angle stay on until the driver cancels them.
    /// - Flasher: <see cref="NominalHz"/> = 1.5 Hz (90 flashes/min), 50 % lit. UN ECE R48 prescribes 90 +/- 30 flashes per
    ///   minute (1.5 Hz +/- 0.5 Hz) for direction indicators; the exact paragraph number is UNVERIFIED. The first flash
    ///   starts lit immediately when the lever is operated.
    /// Pure logic, allocation free; <see cref="Step"/> returns the relay edge for the click sound.
    /// </summary>
    public sealed class TurnSignal
    {
        /// <summary>Flash rate [Hz] and the R48 band 1.0 .. 2.0 it is clamped to.</summary>
        public const float NominalHz = 1.5f, MinHz = 1.0f, MaxHz = 2.0f;
        /// <summary>Road-wheel angle (0..1 of full lock) that arms the self-cancel, and the angle below which it cancels. WORKING_VALUE (feel tuning pending).</summary>
        public const float ArmAngle = 0.20f, ReleaseAngle = 0.06f;

        float m_Hz = NominalHz;
        float m_Phase;       // 0..1 of the flash period
        bool m_Armed;
        int m_Lever;
        bool m_Lit;

        public float FlashHz { get => m_Hz; set => m_Hz = Mathf.Clamp(value, MinHz, MaxHz); }
        /// <summary>0 off, -1 left, +1 right, 2 hazard.</summary>
        public int Lever => m_Lever;
        public bool Active => m_Lever != 0;
        /// <summary>Relay contact closed (lamps lit).</summary>
        public bool Lit => m_Lit;
        public bool LeftLit => m_Lit && (m_Lever == -1 || m_Lever == 2);
        public bool RightLit => m_Lit && (m_Lever == 1 || m_Lever == 2);
        public bool Armed => m_Armed;

        public void Request(TurnSignalRequest r)
        {
            switch (r)
            {
                case TurnSignalRequest.Left: SetStalk(-1); break;
                case TurnSignalRequest.Right: SetStalk(+1); break;
                case TurnSignalRequest.Hazard:
                    m_Lever = m_Lever == 2 ? 0 : 2;
                    m_Armed = false;
                    break;
            }
        }

        void SetStalk(int dir)
        {
            if (m_Lever == 2) return;                      // hazard overrides the stalk
            m_Lever = m_Lever == dir ? 0 : dir;
            m_Armed = false;
        }

        /// <summary>Switches everything off (respawn).</summary>
        public void Cancel() { m_Lever = 0; m_Armed = false; m_Phase = 0f; m_Lit = false; }

        /// <summary>Advances the stalk and the flasher. <paramref name="roadWheelNorm"/>: road-wheel angle / full lock, + = right.
        /// Returns +1 on the relay closing (lamp on), -1 on opening, 0 otherwise.</summary>
        public int Step(float dt, float roadWheelNorm)
        {
            if (m_Lever == -1 || m_Lever == 1)
            {
                float turned = roadWheelNorm * m_Lever;     // > 0 = steering into the signalled direction
                if (turned > ArmAngle) m_Armed = true;
                else if (m_Armed && turned < ReleaseAngle) { m_Lever = 0; m_Armed = false; }
            }
            bool was = m_Lit;
            if (m_Lever == 0)
            {
                m_Phase = 0f; m_Lit = false;
            }
            else if (!was && m_Phase == 0f)
            {
                m_Lit = true;                               // first flash: lit at once
            }
            else
            {
                m_Phase += dt * m_Hz;
                if (m_Phase >= 1f) m_Phase -= Mathf.Floor(m_Phase);
                m_Lit = m_Phase < 0.5f;
                if (m_Phase == 0f) m_Phase = 1e-6f;         // keep "phase 0" reserved for the idle state
            }
            return m_Lit == was ? 0 : (m_Lit ? 1 : -1);
        }
    }
}
