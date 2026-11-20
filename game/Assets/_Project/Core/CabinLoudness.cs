using System;
using System.Globalization;
using UnityEngine;

namespace Game.Core
{
    /// <summary>
    /// Cabin loudness calibration (owner decision D92, ADR 0311): the whole listener mix in the cab view gets one gain so a
    /// cab drive measures -18 LUFS integrated (BS.1770-4) at master 1.0, true peak &lt;= -1 dBTP. One gain for every
    /// source the listener hears - engine, tyres, wind, pneumatics, ambience, one-shots - so the balance of the layers
    /// (ADR 0142/0145/0148/0176 factors) is unchanged. The exterior view keeps gain 1 (D92: exterior unchanged); the
    /// cab/exterior crossfade of <c>TruckAudioController</c> (0.15 s) blends between the two.
    /// The gains are measured, not tuned by ear: <c>tools/audio/lufs_calibrate.py</c> reads the player captures
    /// (<c>-audio_capture</c>, ADR 0286) and prints the new value = old + (target - measured). Per sound set, because the
    /// ElevenLabs and procedural cab mixes differ in level. Launch argument <c>-audio_cab_gain_db X</c> overrides both
    /// (measurement / A-B; 0 = the pre-D92 mix). The bus also runs <see cref="BusLimiter"/> (-1.5 dBFS sample ceiling) so the
    /// loudest moments (full-throttle launch, horn) stay under the true-peak ceiling.
    /// </summary>
    public static class CabinLoudness
    {
        /// <summary>D92 target, integrated loudness of a cab drive [LUFS] (WORKING_VALUE tolerance +-1 LU).</summary>
        public const float TargetLufs = -18f;
        /// <summary>D92 / docs/08: true-peak ceiling [dBTP].</summary>
        public const float TruePeakCeilingDbtp = -1f;

        /// <summary>Cab bus gain with the ElevenLabs sound set [dB]: before -25.1 LUFS (straight050 + circle50, 40 t, build 83226d958) -> +7.1 (ADR 0311).</summary>
        public const float ElevenLabsCabGainDb = 7.1f;
        /// <summary>Cab bus gain with the procedural sound set [dB]: before -24.2 LUFS (same programme) -> +6.2 (ADR 0311).</summary>
        public const float ProceduralCabGainDb = 6.2f;
        /// <summary>Sanity range of a calibration gain [dB] (a larger correction means the mix itself is off).</summary>
        public const float MinGainDb = -12f, MaxGainDb = 12f;

        static bool s_ArgRead;
        static float s_OverrideDb = float.NaN;

        /// <summary>Calibrated cab gain [dB] for a sound set; the launch-argument override wins when given.</summary>
        public static float CabGainDb(bool elevenLabs)
        {
            float o = OverrideDb;
            if (!float.IsNaN(o)) return o;
            return elevenLabs ? ElevenLabsCabGainDb : ProceduralCabGainDb;
        }

        /// <summary>Linear cab gain for a sound set.</summary>
        public static float CabGainLinear(bool elevenLabs) => DbToLinear(CabGainDb(elevenLabs));

        public static float DbToLinear(float db) => Mathf.Pow(10f, Mathf.Clamp(db, MinGainDb, MaxGainDb) / 20f);

        /// <summary>Gain of the listener bus for an interior blend (0 = exterior: exactly 1, 1 = cab: the cab gain).</summary>
        public static float BusGain(float cabGainLinear, float interior) =>
            1f + (cabGainLinear - 1f) * Mathf.Clamp01(interior);

        /// <summary><c>-audio_cab_gain_db X</c> (NaN when absent). Reads the command line once.</summary>
        public static float OverrideDb
        {
            get
            {
                if (!s_ArgRead)
                {
                    s_ArgRead = true;
                    s_OverrideDb = ParseOverride(Environment.GetCommandLineArgs());
                }
                return s_OverrideDb;
            }
        }

        public static float ParseOverride(string[] args)
        {
            if (args == null) return float.NaN;
            for (int i = 0; i < args.Length - 1; i++)
                if (string.Equals(args[i], "-audio_cab_gain_db", StringComparison.OrdinalIgnoreCase)
                    && float.TryParse(args[i + 1], NumberStyles.Float, CultureInfo.InvariantCulture, out float v)
                    && v >= MinGainDb && v <= MaxGainDb)
                    return v;
            return float.NaN;
        }

        /// <summary>
        /// Audio thread: multiplies an interleaved block by a gain ramped linearly per frame from <paramref name="from"/> to
        /// <paramref name="to"/> (no zipper / click on a view change). Returns the gain reached (= <paramref name="to"/>).
        /// A unity gain leaves the block untouched (bit-exact pass-through). No allocation.
        /// </summary>
        public static float Apply(float[] data, int channels, float from, float to)
        {
            if (data == null || channels <= 0) return to;
            if (from == 1f && to == 1f) return to;
            int frames = data.Length / channels;
            if (frames <= 0) return to;
            if (from == to)
            {
                for (int i = 0; i < frames * channels; i++) data[i] *= to;
                return to;
            }
            float span = to - from, inv = 1f / frames;
            int k = 0;
            for (int f = 0; f < frames; f++)
            {
                float g = from + span * ((f + 1) * inv);   // no running sum: the block ends exactly on the target
                for (int c = 0; c < channels; c++) data[k++] *= g;
            }
            return to;
        }
    }
}
