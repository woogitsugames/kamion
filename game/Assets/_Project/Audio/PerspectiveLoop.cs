using UnityEngine;

namespace TruckSim.Audio
{
    /// <summary>
    /// One looping layer in two perspectives (exterior reference clip + prerendered cabin clip, tools/audio
    /// sfx_layers.cab_filter). Both AudioSources always exist; <see cref="Set"/> crossfades them equal-power by the
    /// interior blend. The exterior source is 3D at the truck, the cabin source is 2D. A zero-volume source is
    /// virtualised by Unity (no decode), so the idle perspective costs nothing. Without a cabin clip the exterior clip
    /// is used for both with the cabin gain scaled by <c>cabFallbackGain</c>.
    /// </summary>
    public sealed class PerspectiveLoop
    {
        readonly AudioSource m_Ext, m_Cab;
        readonly float m_CabFallbackGain;

        public bool Valid { get; }

        public PerspectiveLoop(Transform parent, string name, AudioClip ext, AudioClip cab, Vector3 localPos,
            int priority, float cabFallbackGain = 0.5f)
        {
            Valid = ext != null;
            m_CabFallbackGain = cab != null ? 1f : cabFallbackGain;
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            m_Ext = Make(go, "ext", ext, priority);
            m_Cab = Make(go, "cab", cab != null ? cab : ext, priority);
            m_Cab.spatialBlend = 0f;
        }

        static AudioSource Make(GameObject go, string tag, AudioClip clip, int priority)
        {
            var child = new GameObject(tag);
            child.transform.SetParent(go.transform, false);
            var s = child.AddComponent<AudioSource>();
            s.playOnAwake = false;
            s.loop = true;
            s.clip = clip;
            s.volume = 0f;
            s.priority = priority;
            s.dopplerLevel = 0f;
            s.spatialBlend = 1f;
            s.rolloffMode = AudioRolloffMode.Logarithmic;
            s.minDistance = 4f;
            s.maxDistance = 250f;
            if (clip != null)
            {
                s.Play();
                s.time = Random.value * clip.length * 0.99f; // de-phase layers that share a clip
            }
            return s;
        }

        /// <param name="gain">linear gain at the exterior (0 = silent).</param>
        /// <param name="pitch">playback pitch.</param>
        /// <param name="interior">0 = outside, 1 = cab.</param>
        public void Set(float gain, float pitch, float interior)
        {
            if (!Valid) return;
            float a = interior * 1.5707964f;
            m_Ext.volume = gain * Mathf.Cos(a);
            m_Cab.volume = gain * m_CabFallbackGain * Mathf.Sin(a);
            m_Ext.pitch = pitch;
            m_Cab.pitch = pitch;
        }

        /// <summary>Sources are 2D (spatialBlend 0) for roaming ambience: pans both perspectives in the stereo field.</summary>
        public void Make2D(float pan)
        {
            m_Ext.spatialBlend = 0f;
            m_Ext.panStereo = pan;
            m_Cab.panStereo = pan;
        }

        public void SetPan(float pan)
        {
            m_Ext.panStereo = pan;
            m_Cab.panStereo = pan;
        }
    }
}
