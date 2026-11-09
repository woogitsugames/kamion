using UnityEngine;
using UnityEngine.Audio;

namespace TruckSim.Audio
{
    /// <summary>
    /// Plays an <see cref="EngineSoundBank"/> (rpm x load grid of loops) through a small fixed pool of
    /// AudioSources. Per frame: pick the (up to) 4 bracketing cells, crossfade them with a hybrid
    /// equal-gain/equal-power law, pitch every voice to rpm / clipRpm, slew voice gains.
    /// New voices start crank-phase-aligned to the loudest playing voice, so adjacent loops add
    /// coherently (their firing harmonics line up) instead of comb-filtering.
    ///
    /// Mirror of tools/audio/runtime_sim.py (LayerGrid). Keep both in sync; the Python mirror is
    /// what the demo renders and crossfade checks run on.
    ///
    /// Zero GC after construction: fixed arrays, no LINQ/closures/strings in <see cref="Tick"/>.
    /// </summary>
    public sealed class EngineLayerGrid
    {
        public const float MinWeight = 1e-4f;
        const float SilentGain = 1e-5f;

        sealed class Voice
        {
            public AudioSource Src;
            public int Cell = -1;
            public float Gain;
            public float Target;
        }

        readonly EngineSoundBank _bank;
        readonly Voice[] _voices;
        readonly float[] _spc;          // samples per engine cycle, per clip
        readonly int[] _reqCell = new int[4];
        readonly float[] _reqWeight = new float[4];
        readonly bool[] _reqTaken = new bool[4];
        int _reqCount;
        uint _rng;

        /// <summary>Gain slew time for voice fade-in/out and weight changes [s].</summary>
        public float FadeTime = 0.03f;

        /// <summary>1 = equal-gain crossfade (coherent signals), 0 = equal-power. Tuned value: 0.9.</summary>
        public float Coherence = 0.9f;

        public int ActiveVoices { get; private set; }

        public EngineLayerGrid(EngineSoundBank bank, Transform parent, int poolSize, AudioMixerGroup output,
                               uint seed, string label)
        {
            _bank = bank;
            _rng = seed == 0 ? 1u : seed;
            int n = bank.clips.Length;
            _spc = new float[n];
            for (int i = 0; i < n; i++)
                _spc[i] = bank.clips[i] != null ? (float)bank.clips[i].samples / bank.clipCycles[i] : 1f;

            _voices = new Voice[Mathf.Max(poolSize, 4)];
            for (int i = 0; i < _voices.Length; i++)
            {
                var go = new GameObject(label + "_voice" + i); // construction only, not per frame
                go.transform.SetParent(parent, false);
                var src = go.AddComponent<AudioSource>();
                src.playOnAwake = false;
                src.loop = true;
                src.volume = 0f;
                src.priority = 16; // engine must never be culled by voice limiting
                src.spatialBlend = bank.spatialBlend;
                src.dopplerLevel = 0f; // pitch is driven by rpm; doppler handled separately if wanted
                src.rolloffMode = AudioRolloffMode.Logarithmic;
                src.minDistance = 4f;
                src.maxDistance = 250f;
                src.outputAudioMixerGroup = output;
                _voices[i] = new Voice { Src = src };
            }
        }

        /// <summary>Hybrid crossfade law; returns gain of the lower point, outputs gain of the upper.</summary>
        float XFade(float t, out float upper)
        {
            float c = Coherence;
            float a = t * Mathf.PI * 0.5f;
            upper = c * t + (1f - c) * Mathf.Sin(a);
            return c * (1f - t) + (1f - c) * Mathf.Cos(a);
        }

        static void Bracket(float[] pts, float v, out int i0, out int i1, out float t)
        {
            int last = pts.Length - 1;
            if (v <= pts[0]) { i0 = i1 = 0; t = 0f; return; }
            if (v >= pts[last]) { i0 = i1 = last; t = 0f; return; }
            int i = 0;
            while (i < last - 1 && v >= pts[i + 1]) i++;
            i0 = i;
            i1 = i + 1;
            t = (v - pts[i]) / (pts[i + 1] - pts[i]);
        }

        void Request(int cell, float w)
        {
            for (int i = 0; i < _reqCount; i++)
                if (_reqCell[i] == cell) { _reqWeight[i] += w; return; }
            _reqCell[_reqCount] = cell;
            _reqWeight[_reqCount] = w;
            _reqTaken[_reqCount] = false;
            _reqCount++;
        }

        uint NextRandom()
        {
            _rng = 1664525u * _rng + 1013904223u; // same LCG as the Python mirror
            return _rng >> 8;
        }

        /// <summary>Advance one frame. bankGain scales the whole grid (perspective blend, engine-brake amount).</summary>
        public void Tick(float rpm, float load, float bankGain, float dt)
        {
            int nr = _bank.RpmCount;
            Bracket(_bank.rpmPoints, rpm, out int r0, out int r1, out float tr);
            int l0 = 0, l1 = 0;
            float tl = 0f;
            if (_bank.LoadCount > 1) Bracket(_bank.loadPoints, load, out l0, out l1, out tl);
            float gr0 = XFade(tr, out float gr1);
            float gl0 = XFade(tl, out float gl1);

            _reqCount = 0;
            if (bankGain > 0f)
            {
                Request(l0 * nr + r0, gl0 * gr0 * bankGain);
                Request(l0 * nr + r1, gl0 * gr1 * bankGain);
                Request(l1 * nr + r0, gl1 * gr0 * bankGain);
                Request(l1 * nr + r1, gl1 * gr1 * bankGain);
            }

            // reference voice for crank-phase alignment = loudest active voice
            Voice reference = null;
            for (int i = 0; i < _voices.Length; i++)
            {
                var v = _voices[i];
                if (v.Cell >= 0 && (reference == null || v.Gain > reference.Gain)) reference = v;
            }

            // existing voices keep / lose their cell
            for (int i = 0; i < _voices.Length; i++)
            {
                var v = _voices[i];
                if (v.Cell < 0) continue;
                v.Target = 0f;
                for (int r = 0; r < _reqCount; r++)
                {
                    if (!_reqTaken[r] && _reqCell[r] == v.Cell)
                    {
                        v.Target = _reqWeight[r] > MinWeight ? _reqWeight[r] : 0f;
                        _reqTaken[r] = true;
                        break;
                    }
                }
            }

            // new voices for cells that are not playing yet
            for (int r = 0; r < _reqCount; r++)
            {
                if (_reqTaken[r] || _reqWeight[r] <= MinWeight) continue;
                Voice v = null;
                for (int i = 0; i < _voices.Length && v == null; i++)
                    if (_voices[i].Cell < 0) v = _voices[i];
                if (v == null) // pool exhausted: steal the quietest voice
                {
                    for (int i = 0; i < _voices.Length; i++)
                        if (_voices[i] != reference && (v == null || _voices[i].Gain < v.Gain)) v = _voices[i];
                    v.Src.Stop();
                }
                StartVoice(v, _reqCell[r], _reqWeight[r], reference);
            }

            // slew gains, set pitch, retire silent voices
            float step = FadeTime > 0f ? dt / FadeTime : 1f;
            int active = 0;
            for (int i = 0; i < _voices.Length; i++)
            {
                var v = _voices[i];
                if (v.Cell < 0) continue;
                v.Gain = Mathf.MoveTowards(v.Gain, v.Target, step);
                if (v.Target <= 0f && v.Gain <= SilentGain)
                {
                    v.Src.Stop();
                    v.Src.volume = 0f;
                    v.Cell = -1;
                    v.Gain = 0f;
                    continue;
                }
                v.Src.volume = v.Gain;
                v.Src.pitch = Mathf.Clamp(rpm / _bank.clipRpmExact[v.Cell], 0.05f, 3f);
                active++;
            }
            ActiveVoices = active;
        }

        void StartVoice(Voice v, int cell, float weight, Voice reference)
        {
            var clip = _bank.clips[cell];
            v.Cell = cell;
            v.Gain = 0f;
            v.Target = weight;
            v.Src.clip = clip;
            v.Src.volume = 0f;
            v.Src.Play();
            float phase = 0f;
            if (reference != null && reference.Cell >= 0)
            {
                float refPos = reference.Src.timeSamples / _spc[reference.Cell];
                phase = refPos - Mathf.Floor(refPos);
            }
            int cycles = _bank.clipCycles[cell];
            int k = (int)(NextRandom() % (uint)cycles); // random whole cycle decorrelates noise/irregularity
            int pos = (int)((k + phase) * _spc[cell]);
            v.Src.timeSamples = pos % clip.samples; // set after Play(): Play() may reset the position
        }

        public void StopAll()
        {
            for (int i = 0; i < _voices.Length; i++)
            {
                var v = _voices[i];
                if (v.Src != null) { v.Src.Stop(); v.Src.volume = 0f; }
                v.Cell = -1;
                v.Gain = 0f;
                v.Target = 0f;
            }
            ActiveVoices = 0;
        }
    }
}
