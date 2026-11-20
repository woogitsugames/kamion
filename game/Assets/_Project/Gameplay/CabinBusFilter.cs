using Game.Core;
using TruckSim.Audio;
using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// Listener bus gain (D92, ADR 0311): sits on the AudioListener object and multiplies the whole mix by
    /// <see cref="Target"/> (set by <see cref="TruckAudioController"/> from the cab gain and the interior blend), ramped
    /// per frame inside each DSP block. There is no AudioMixer in the project and AudioListener.volume cannot go above 1,
    /// so a gain over unity has to be applied here. Feeds the measurement capture (ADR 0286) after the gain, so the
    /// recorded level is the level the player hears. Audio thread: no allocation.
    /// </summary>
    public sealed class CabinBusFilter : MonoBehaviour
    {
        volatile float m_Target = 1f;
        float m_Current = 1f; // audio thread only

        /// <summary>Linear bus gain the next DSP blocks ramp to (main thread writes).</summary>
        public float Target
        {
            get => m_Target;
            set => m_Target = value;
        }

        void OnEnable() => AudioOutputCapture.SetBusTap(gameObject);

        void OnDisable() => AudioOutputCapture.ClearBusTap(gameObject);

        void OnAudioFilterRead(float[] data, int channels)
        {
            m_Current = CabinLoudness.Apply(data, channels, m_Current, m_Target);
            AudioOutputCapture.Push(data, channels);
        }
    }
}
