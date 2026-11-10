using Game.UI.Driving;
using Game.Vehicle.Runtime;
using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// Cluster warning chime: one short, soft "ding" per parking-brake warning event (<c>VehicleModel.ParkingBrakeWarningCount</c>).
    /// The sound is synthesised in code (a 1.0 kHz bell tone with a quiet 2.4x partial and an exponential decay, 0.45 s): no recording,
    /// no third-party asset, no licence row needed (docs/LICENSES.md, row <c>cluster-chime-procedural</c>). 2D source (it comes from the
    /// dash), played whatever the camera. Polling via <see cref="ParkingBrakeWarningTracker"/>; no allocations after Awake.
    /// </summary>
    public sealed class ClusterChime : MonoBehaviour
    {
        public const int SampleRate = 24000;
        public const float DurationSeconds = 0.45f;

        public VehicleBody vehicle;
        [Range(0f, 1f)] public float volume = 0.6f;

        AudioSource m_Source;
        AudioClip m_Clip;
        ParkingBrakeWarningTracker m_Tracker;

        /// <summary>Number of chimes started (tests, diagnostics).</summary>
        public int ChimesPlayed { get; private set; }

        /// <summary>The chime waveform (mono, <see cref="SampleRate"/>); a new array.</summary>
        public static float[] Synthesize()
        {
            int n = Mathf.RoundToInt(SampleRate * DurationSeconds);
            var d = new float[n];
            const float f0 = 1000f;
            for (int i = 0; i < n; i++)
            {
                float t = i / (float)SampleRate;
                float attack = Mathf.Clamp01(t / 0.004f);
                float env = attack * Mathf.Exp(-t * 9f);
                float s = Mathf.Sin(2f * Mathf.PI * f0 * t) + 0.25f * Mathf.Sin(2f * Mathf.PI * f0 * 2.4f * t) * Mathf.Exp(-t * 9f);
                d[i] = 0.5f * env * s;
            }
            d[n - 1] = 0f;
            return d;
        }

        void Awake()
        {
            m_Clip = AudioClip.Create("ClusterChime", Mathf.RoundToInt(SampleRate * DurationSeconds), 1, SampleRate, false);
            m_Clip.SetData(Synthesize(), 0);
            m_Source = gameObject.AddComponent<AudioSource>();
            m_Source.playOnAwake = false;
            m_Source.spatialBlend = 0f;
            m_Source.clip = m_Clip;
            m_Source.priority = 20;
        }

        void Update() => Tick(Time.unscaledTime);

        /// <summary>One poll of the model (Update calls it every frame; tests call it with their own clock).</summary>
        public void Tick(float now)
        {
            if (vehicle == null || !vehicle.Initialized) { m_Tracker.Reset(); return; }
            var m = vehicle.Model;
            if (m_Tracker.Poll(m.ParkingBrakeWarning, m.ParkingBrakeWarningCount, now)) Chime();
        }

        void Chime()
        {
            ChimesPlayed++;
            m_Source.PlayOneShot(m_Clip, volume);
        }
    }
}
