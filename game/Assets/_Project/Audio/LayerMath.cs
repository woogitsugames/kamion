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

        // ---- ADR 0145: tyre scrub vs squeal ----
        // Measured (tools/physics-runner circles with the tridem semi-trailer, tools/audio/tyre_slip_scan.py): in a tight
        // slow turn the outer trailer axles are dragged sideways at 8-10 deg (R 12 m) to 18-22 deg (R 9 m) slip angle
        // while the tractor stays under 2 deg. The old squeal (onset 0.8 x AlphaRef = 4.6 deg) therefore whistled at
        // full level in every tight turn above 15 km/h. That geometric drag is scrub (low groan, creaks), not squeal.

        /// <summary>Share of a surface that scrubs audibly (rubber dragged sideways; loose ground mostly shifts).</summary>
        public static readonly float[] SurfaceScrubbable = { 1.0f, 0.7f, 1.0f, 0.8f, 0.5f, 0.3f };

        public const float ScrubAlphaOn = 1.0f * Mathf.Deg2Rad, ScrubAlphaFull = 5.0f * Mathf.Deg2Rad;
        public const float ScrubSpeedOn = 0.3f, ScrubSpeedFull = 1.2f, ScrubFadeStart = 6.0f, ScrubFadeEnd = 11.0f;
        public const float SquealOnset = 1.3f, SquealFull = 2.0f, SquealSpeedOn = 5.0f, SquealSpeedFull = 9.0f;

        static float Smooth01(float x)
        {
            x = Mathf.Clamp01(x);
            return x * x * (3f - 2f * x);
        }

        /// <summary>
        /// Scrub gain 0..1 from the largest lateral slip angle of the scrubbing axles (trailer axles when coupled, else the
        /// tractor's) [rad] and the road speed [m/s]: on from 1 deg, full at 5 deg; fades in over 0.3-1.2 m/s (none at a
        /// standstill) and out over 6-11 m/s (22-40 km/h), where a real slide becomes a squeal.
        /// </summary>
        public static float ScrubGain(float slipAngleRad, float speedMs)
        {
            float a = Smooth01((slipAngleRad - ScrubAlphaOn) / (ScrubAlphaFull - ScrubAlphaOn));
            float on = Smooth01((speedMs - ScrubSpeedOn) / (ScrubSpeedFull - ScrubSpeedOn));
            float off = 1f - Smooth01((speedMs - ScrubFadeStart) / (ScrubFadeEnd - ScrubFadeStart));
            return a * on * off;
        }

        /// <summary>Scrub pitch from the sliding speed of the tread across the road (v sin alpha): 0.85..1.15.</summary>
        public static float ScrubPitch(float slipAngleRad, float speedMs) =>
            0.85f + 0.3f * Mathf.Clamp01(speedMs * Mathf.Sin(Mathf.Abs(slipAngleRad)) / 1.0f);

        /// <summary>
        /// Squeal gain 0..1 (ADR 0145): combined slip (normalised, 1 = KappaRef / AlphaRef) on from 1.3, full at 2.0, and only
        /// at speed (on from 5 m/s = 18 km/h, full at 9 m/s = 32 km/h). Below that the slip is heard as scrub.
        /// </summary>
        public static float SquealGain(float combinedSlipNorm, float speedMs)
        {
            return Smooth01((combinedSlipNorm - SquealOnset) / (SquealFull - SquealOnset)) *
                   Smooth01((speedMs - SquealSpeedOn) / (SquealSpeedFull - SquealSpeedOn));
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

        // ---- ADR 0176: synthesised retarder (tone + flow) and engine-brake events; mirror tools/audio/synth0176_ab.py ----
        /// <summary>Propshaft speed of the 0176 retarder loops at pitch 1 (tools/audio/synth0176.REF_SHAFT_RPM).</summary>
        public const float RetarderRefShaftRpm = 1000f;
        /// <summary>Shaft speed at which the rotor tone reaches full level (tip-speed law below it).</summary>
        public const float RetarderToneFullRpm = 1600f;
        public const float RetarderToneMix = 0.35f, RetarderFlowMix = 0.65f;

        /// <summary>Propshaft speed [rpm] from road speed [m/s], driven-wheel radius [m] and final-drive ratio.</summary>
        public static float ShaftRpm(float speedMs, float wheelRadius, float finalDrive) =>
            Mathf.Abs(speedMs) / Mathf.Max(wheelRadius, 0.1f) * finalDrive * (60f / (2f * Mathf.PI));

        /// <summary>
        /// Rotor/stator blade-pass tone: grows with the fill and with the rotor tip speed (power 1.5 up to
        /// <see cref="RetarderToneFullRpm"/>), so a full retarder at walking pace is a faint whine, not a full one.
        /// </summary>
        public static float RetarderToneGain(float fill, float shaftRpm, float volume) =>
            volume * RetarderToneMix * Mathf.Pow(Mathf.Clamp01(fill), 0.8f) *
            Mathf.Pow(Mathf.Clamp01(Mathf.Abs(shaftRpm) / RetarderToneFullRpm), 1.5f);

        /// <summary>Oil churning / flow noise: amplitude ~ sqrt of the dissipated power (Retarder.Power / maxPower).</summary>
        public static float RetarderFlowGain(float powerW, float maxPowerW, float volume) =>
            volume * RetarderFlowMix * Mathf.Sqrt(Mathf.Clamp01(powerW / Mathf.Max(maxPowerW, 1f)));

        /// <summary>Both 0176 retarder loops follow the propshaft speed (blade-pass frequency ~ shaft rpm).</summary>
        public static float RetarderTonePitch(float shaftRpm) => Mathf.Clamp(Mathf.Abs(shaftRpm) / RetarderRefShaftRpm, 0.2f, 2.5f);

        /// <summary>Exhaust back-pressure dump when the flap opens: louder at high rpm (more exhaust flow), 0.4..1 x volume.</summary>
        public static float EngineBrakeReleaseLevel(float rpm, float volume) =>
            volume * (0.4f + 0.6f * Mathf.Clamp01((rpm - 900f) / 1100f));

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
