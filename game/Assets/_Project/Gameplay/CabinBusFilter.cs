using Game.Core;
using TruckSim.Audio;
using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// Listener bus (D92, ADR 0311): sits on the AudioListener object and multiplies the whole mix by <see cref="Target"/>
    /// (set by <see cref="TruckAudioController"/> from the calibrated cab gain and the interior blend), ramped per frame
    /// inside each DSP block, then runs the look-ahead peak limiter (<see cref="BusLimiter"/>, ceiling -1.5 dBFS sample peak)
    /// so the loudest cab moments stay under -1 dBTP. There is no AudioMixer in the project and AudioListener.volume cannot
    /// go above 1, so a gain over unity has to be applied here. Feeds the measurement capture (ADR 0286) after gain and
    /// limiter, so the recorded level is the level the player hears. Audio thread: no allocation.
    /// </summary>
    public sealed class CabinBusFilter : MonoBehaviour
    {
        volatile float m_Target = 1f;
        float m_Current = 1f; // audio thread only
        readonly BusLimiter m_Limiter = new BusLimiter();
        int m_Rate = 48000;
        float m_NextLog;
        float m_LoggedMin = 1f;

        /// <summary>Linear bus gain the next DSP blocks ramp to (main thread writes).</summary>
        public float Target
        {
            get => m_Target;
            set => m_Target = value;
        }

        public BusLimiter Limiter => m_Limiter;

        void Awake() => m_Rate = AudioSettings.outputSampleRate;

        void OnEnable() => AudioOutputCapture.SetBusTap(gameObject);

        void OnDisable() => AudioOutputCapture.ClearBusTap(gameObject);

        void Update()
        {
            // diagnostics: one line when the limiter worked harder than before (at most every 5 s, allocation only then)
            if (Time.unscaledTime < m_NextLog) return;
            m_NextLog = Time.unscaledTime + 5f;
            float mn = m_Limiter.MinGain;
            if (mn < m_LoggedMin - 0.01f)
            {
                m_LoggedMin = mn;
                Debug.Log($"[AUDIO] cab bus limiter: min gain {20f * Mathf.Log10(Mathf.Max(mn, 1e-6f)):F1} dB, limited frames {m_Limiter.LimitedFrames}");
            }
        }

        void OnAudioFilterRead(float[] data, int channels)
        {
            m_Current = CabinLoudness.Apply(data, channels, m_Current, m_Target);
            m_Limiter.Process(data, channels, m_Rate);
            AudioOutputCapture.Push(data, channels);
        }
    }
}
