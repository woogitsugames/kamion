using UnityEngine;

namespace TruckSim.Audio
{
    /// <summary>
    /// Pure mapping functions from physics state to layer parameters (no scene objects, unit-tested in EditMode).
    /// All constants are WORKING_VALUE until the owner's listening test.
    /// </summary>
    public static class LayerMath
    {
        // SurfaceKind ids: 0 dry asphalt, 1 wet asphalt, 2 concrete, 3 cobbles, 4 gravel, 5 grass.
        public const int SurfaceCount = 6;
        /// <summary>Relative loudness of each tyre loop (loops are rendered at equal RMS).</summary>
        public static readonly float[] SurfaceLevel = { 1.00f, 1.15f, 1.00f, 1.35f, 1.20f, 0.80f };
        /// <summary>Speed exponent of the level curve: rough surfaces rattle already at crawling speed.</summary>
        public static readonly float[] SurfaceSpeedExp = { 1.6f, 1.5f, 1.6f, 1.1f, 1.2f, 1.2f };
        /// <summary>Share of a surface that can squeal (loose ground cannot).</summary>
        public static readonly float[] SurfaceSquealable = { 1.0f, 0.8f, 1.0f, 0.5f, 0f, 0f };

        public const float KappaRef = 0.12f;   // slip ratio at which a loaded truck tyre starts to protest
        public const float AlphaRef = 0.10f;   // slip angle [rad] (~5.7 deg)

        /// <summary>Combined slip normalised to the squeal threshold (1 = onset).</summary>
        public static float CombinedSlip(float slipRatio, float slipAngleRad)
        {
            float k = slipRatio / KappaRef, a = slipAngleRad / AlphaRef;
            return Mathf.Sqrt(k * k + a * a);
        }

        /// <summary>Squeal gain 0..1: silent below 0.8 of the onset, full at 1.4; none when (almost) stationary.</summary>
        public static float SquealGain(float combinedSlipNorm, float speedMs)
        {
            if (speedMs < 1.5f) return 0f;
            float g = Mathf.Clamp01((combinedSlipNorm - 0.8f) / 0.6f);
            g = g * g * (3f - 2f * g);
            return g * Mathf.Clamp01((speedMs - 1.5f) / 2.5f);
        }

        public static float TyreGain(float speedMs, int surface, float volume)
        {
            float vn = Mathf.Clamp01(speedMs / 25f);
            return volume * SurfaceLevel[surface] * Mathf.Pow(vn, SurfaceSpeedExp[surface]);
        }

        public static float TyrePitch(float speedMs) => 0.75f + 0.6f * Mathf.Clamp01(speedMs / 25f);

        /// <summary>Retarder whine follows the gearbox output shaft speed (proportional to road speed).</summary>
        public static float RetarderPitch(float speedMs) => 0.5f + 1.0f * Mathf.Clamp01(speedMs / 22f);

        public static float RetarderGain(float fill, float volume) => volume * Mathf.Pow(Mathf.Clamp01(fill), 0.9f);

        /// <summary>Compressor stroke rate follows engine rpm (loop rendered at 14 strokes/s = pitch 1 at 1000 rpm).</summary>
        public static float CompressorPitch(float rpm) => Mathf.Clamp(rpm / 1000f, 0.5f, 1.8f);

        public static float ExponentialStep(float current, float target, float dt, float tauUp, float tauDown)
        {
            float tau = target > current ? tauUp : tauDown;
            return current + (target - current) * (1f - Mathf.Exp(-dt / Mathf.Max(tau, 1e-4f)));
        }
    }

    /// <summary>Flasher relay clock: 90 flashes/min (ECE R6 allows 60..120); tick on contact close, tock half a period later.</summary>
    public struct IndicatorClock
    {
        public const float Period = 0.667f;
        float m_Phase;
        int m_Last;

        /// <summary>0 = nothing, 1 = tick, 2 = tock. Call every frame; <paramref name="active"/> = a lever/hazard is on.</summary>
        public int Advance(float dt, bool active)
        {
            if (!active) { m_Phase = 0f; m_Last = 0; return 0; }
            if (m_Last == 0) { m_Last = 1; m_Phase = 0f; return 1; } // first contact closes immediately
            m_Phase += dt;
            if (m_Phase >= Period) m_Phase -= Period;
            int want = m_Phase < Period * 0.5f ? 1 : 2;
            if (want == m_Last) return 0;
            m_Last = want;
            return want;
        }
    }
}
