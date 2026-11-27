using System;
using TruckSim.Audio;
using UnityEngine;

namespace Game.Gameplay
{
    public enum TrailerRattleKind : byte
    {
        ChainA = 0,
        ChainB = 1,
        TarpA = 2,
        Kingpin = 3,
    }

    /// <summary>
    /// Physics-driven stochastic rattle of the coupled semi-trailer and fifth wheel (chains, tarpaulin buckles,
    /// kingpin slack) excited by trailer vertical acceleration, axle suspension motion, fifth-wheel load jolts,
    /// speed, and rough surfaces. Pure value type, zero GC allocations.
    /// </summary>
    public struct TrailerRattleGate
    {
        // WORKING_VALUE: thresholds & timing tuned for 40 t combination over curbs, ruts, cobbles and gravel.
        public const float MinSpeedKmh = 1.5f;
        public const float VerticalAccelThresholdMs2 = 1.6f;
        public const float SuspensionRateThresholdMs = 0.28f;
        public const float MinHitInterval = 0.06f;
        public const float MaxHitInterval = 0.30f;
        public const float ExcitationDecayTau = 0.28f;

        double m_LastSimTime;
        float m_SmoothedKingpinLoadN, m_LastVerticalExcitation;
        float m_Energy, m_Cooldown;
        bool m_HasSim, m_KingpinDominant;

        public float Energy => m_Energy;
        public float LastVerticalExcitation => m_LastVerticalExcitation;

        public bool Step(
            float dt,
            double simTime,
            bool coupled,
            float speedKmh,
            float bodyVertAccelMs2,
            float maxWheelCompRateMs,
            float signedPeakCompRateMs,
            float kingpinLoadN,
            float trailerMassKg,
            float roughSurfaceWeight,
            double sinceCoupled,
            System.Random random,
            out TrailerRattleKind kind,
            out float gain,
            out float pitch)
        {
            kind = TrailerRattleKind.ChainA;
            gain = 0f;
            pitch = 1f;
            if (!coupled || dt <= 0f || random == null)
            {
                m_Energy = 0f;
                m_Cooldown = 0f;
                m_HasSim = false;
                m_LastVerticalExcitation = 0f;
                return false;
            }

            if (simTime < m_LastSimTime)
            {
                m_HasSim = false;
                m_LastVerticalExcitation = 0f;
            }
            if (simTime > m_LastSimTime)
            {
                float simDt = Mathf.Max((float)(simTime - m_LastSimTime), 1e-4f);
                if (m_HasSim)
                {
                    m_SmoothedKingpinLoadN = LayerMath.ExponentialStep(m_SmoothedKingpinLoadN, kingpinLoadN, simDt, 0.14f, 0.14f);
                    float kingpinImpulse = Math.Abs(kingpinLoadN - m_SmoothedKingpinLoadN) / Mathf.Max(trailerMassKg, 5000f) * 3.8f;
                    float bodyAy = Math.Abs(bodyVertAccelMs2);
                    m_LastVerticalExcitation = Mathf.Max(bodyAy, kingpinImpulse);
                    m_KingpinDominant = kingpinImpulse > bodyAy && kingpinImpulse > VerticalAccelThresholdMs2;
                }
                else
                {
                    m_SmoothedKingpinLoadN = kingpinLoadN;
                    m_LastVerticalExcitation = Math.Abs(bodyVertAccelMs2);
                    m_KingpinDominant = false;
                }
                m_HasSim = true;
                m_LastSimTime = simTime;
            }

            float absSpeed = Math.Abs(speedKmh);
            float speedFactor = Mathf.Clamp01((absSpeed - MinSpeedKmh) / 35f);
            float bump = Mathf.Clamp01((m_LastVerticalExcitation - VerticalAccelThresholdMs2) / 5.5f);
            float susp = Mathf.Clamp01((Math.Abs(maxWheelCompRateMs) - SuspensionRateThresholdMs) / 0.9f);
            float rough = Mathf.Clamp01(roughSurfaceWeight) * Mathf.Clamp01((absSpeed - 2f) / 28f) * 0.55f;
            float couple = sinceCoupled >= 0.0 && sinceCoupled < 0.25 ? 0.85f : 0f;
            float stimulus = Mathf.Clamp01(Mathf.Max(Mathf.Max(bump, susp) * (0.25f + 0.75f * speedFactor), Mathf.Max(rough, couple)));

            m_Energy = LayerMath.ExponentialStep(m_Energy, stimulus, dt, 0.03f, ExcitationDecayTau);
            m_Cooldown = Math.Max(0f, m_Cooldown - dt);
            if (m_Energy < 0.08f || m_Cooldown > 0f) return false;

            float rate = 2.0f + 11.0f * m_Energy;
            float prob = 1f - Mathf.Exp(-rate * dt);
            if (random.NextDouble() >= prob) return false;

            m_Cooldown = MinHitInterval + (float)random.NextDouble() * Mathf.Lerp(MaxHitInterval - MinHitInterval, 0.06f, m_Energy);
            if ((m_KingpinDominant && random.NextDouble() < 0.65) || (sinceCoupled >= 0.0 && sinceCoupled < 0.30))
                kind = TrailerRattleKind.Kingpin;
            else
                kind = (TrailerRattleKind)random.Next(0, 3);

            gain = Mathf.Clamp01(0.28f + 0.72f * m_Energy) * (0.65f + 0.35f * (float)random.NextDouble());
            pitch = 0.88f + 0.26f * (float)random.NextDouble();
            return true;
        }
    }
}
