using System;

namespace Game.Gameplay
{
    /// <summary>One attempt per service-brake application, after a short dwell at moderate chamber pressure.</summary>
    public struct BrakeSquealGate
    {
        // WORKING_VALUE: speed in km/h, pressure = fraction of maximum chamber pressure.
        public const float MinSpeedKmh = 1f, MaxSpeedKmh = 15f;
        public const float MinPressure = 0.22f, MaxPressure = 0.65f;
        public const float DwellSeconds = 0.10f, CooldownSeconds = 3f;
        public const double Probability = 0.28;

        float m_EligibleSeconds, m_Cooldown;
        bool m_Tried;

        public bool Step(float dt, float speedKmh, float pressure, float serviceDemand, bool inhibited, Random random)
        {
            m_Cooldown = Math.Max(0f, m_Cooldown - dt);
            if (serviceDemand < 0.08f) m_Tried = false;
            if (inhibited || serviceDemand < 0.12f || serviceDemand > 0.75f ||
                Math.Abs(speedKmh) < MinSpeedKmh || Math.Abs(speedKmh) >= MaxSpeedKmh ||
                pressure < MinPressure || pressure > MaxPressure)
            {
                m_EligibleSeconds = 0f;
                return false;
            }
            if (m_Tried) return false;
            m_EligibleSeconds += dt;
            if (m_EligibleSeconds < DwellSeconds) return false;
            m_Tried = true;
            if (m_Cooldown > 0f || random.NextDouble() >= Probability) return false;
            m_Cooldown = CooldownSeconds;
            return true;
        }
    }
}
