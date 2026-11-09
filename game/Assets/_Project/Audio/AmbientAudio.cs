using UnityEngine;

namespace TruckSim.Audio
{
    public enum AmbientZone { None = 0, IndustrialYard = 1 }

    /// <summary>
    /// World ambience that follows the listener (not the world): industrial-yard bed (far traffic, mains hum, wind,
    /// distant clanks), a roaming forklift (traction motor, hydraulic pump, reversing beeper) and sparse birds.
    /// Interior/exterior comes from <see cref="Interior"/> (prerendered cabin variants, closed glass kills most birds).
    /// Level scales with <see cref="ZoneLevel"/> and falls with vehicle speed (the truck masks the yard).
    /// No allocations after Configure. All levels WORKING_VALUE.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class AmbientAudio : MonoBehaviour
    {
        [Header("Zone")]
        public AmbientZone zone = AmbientZone.IndustrialYard;
        [Range(0f, 1f)] public float zoneLevel = 1f;

        [Header("Mix (WORKING_VALUE)")]
        [Range(0f, 1f)] public float bedVolume = 0.30f;
        [Range(0f, 1f)] public float forkliftVolume = 0.16f;
        [Range(0f, 1f)] public float birdVolume = 0.35f;
        [Range(0f, 1f)] public float cabBedFactor = 0.5f, cabForkliftFactor = 0.7f, cabBirdFactor = 0.4f;
        [Tooltip("Birds are heard only below this speed [m/s] (engine and wind mask them).")]
        public float birdMaxSpeed = 10f;
        public Vector2 birdInterval = new Vector2(3.5f, 11f);

        /// <summary>Set every frame by the vehicle controller: 0 outside, 1 in the cab.</summary>
        public float Interior { get; set; } = 1f;
        public float SpeedMs { get; set; }

        PerspectiveLoop m_Bed, m_Forklift;
        AudioSource m_Bird;
        VehicleAudioLibrary m_Lib;
        float m_Level;       // smoothed zone level
        float m_NextBird;
        float m_PanPhase;

        public bool Ready => m_Bed != null && m_Bed.Valid;

        public void Configure(VehicleAudioLibrary lib)
        {
            m_Lib = lib;
            m_Bed = new PerspectiveLoop(transform, "AmbientBed", lib.ambientBed.ext, lib.ambientBed.cab, Vector3.zero, 160);
            m_Bed.Make2D(0f);
            m_Forklift = new PerspectiveLoop(transform, "Forklift", lib.forklift.ext, lib.forklift.cab, Vector3.zero, 170);
            m_Forklift.Make2D(0.5f);
            var go = new GameObject("Birds");
            go.transform.SetParent(transform, false);
            m_Bird = go.AddComponent<AudioSource>();
            m_Bird.playOnAwake = false;
            m_Bird.spatialBlend = 0f;
            m_Bird.priority = 200;
            m_NextBird = Time.time + Random.Range(birdInterval.x, birdInterval.y);
            m_PanPhase = Random.value * 6.28f;
        }

        void Update()
        {
            if (!Ready) return;
            float dt = Time.deltaTime;
            float target = zone == AmbientZone.IndustrialYard ? zoneLevel : 0f;
            m_Level = LayerMath.ExponentialStep(m_Level, target, dt, 2f, 2f); // zone borders fade over seconds
            float masked = 1f - 0.55f * Mathf.Clamp01(SpeedMs / 20f);
            float cab = Mathf.Lerp(1f, cabBedFactor, Interior);
            m_Bed.Set(bedVolume * m_Level * masked * cab, 1f, Interior);

            // forklift wanders: slow pan and distance swell (a different period from the loop, so it never repeats exactly)
            m_PanPhase += dt * 0.11f;
            float swell = 0.55f + 0.45f * Mathf.Sin(m_PanPhase * 0.7f + 1.3f);
            m_Forklift.SetPan(0.75f * Mathf.Sin(m_PanPhase));
            m_Forklift.Set(forkliftVolume * m_Level * swell * masked * Mathf.Lerp(1f, cabForkliftFactor, Interior), 1f, Interior);

            if (Time.time >= m_NextBird)
            {
                m_NextBird = Time.time + Random.Range(birdInterval.x, birdInterval.y);
                float speedFade = 1f - Mathf.Clamp01(SpeedMs / birdMaxSpeed);
                float v = birdVolume * m_Level * speedFade;
                if (v > 0.02f) PlayBird(v);
            }
        }

        void PlayBird(float volume)
        {
            bool cab = Interior > 0.5f;
            AudioClip clip;
            float r = Random.value;
            if (cab) clip = m_Lib.crowCaw.cab; // sparrow / tit are inaudible through closed glass: not rendered for the cab
            else clip = r < 0.45f ? m_Lib.birdSparrow : r < 0.8f ? m_Lib.birdTit : m_Lib.crowCaw.ext;
            if (clip == null) return;
            m_Bird.panStereo = Random.Range(-0.85f, 0.85f);
            m_Bird.pitch = Random.Range(0.93f, 1.08f);
            m_Bird.PlayOneShot(clip, volume * (cab ? cabBirdFactor : 1f));
        }
    }
}
