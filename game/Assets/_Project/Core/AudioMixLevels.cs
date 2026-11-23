using UnityEngine;

namespace Game.Core
{
    /// <summary>
    /// Player volume per channel (ADR 0270), shared by the settings (Game.UI) and the audio runtime (Game.Gameplay ->
    /// Game.Audio). There is no AudioMixer in the project: master goes to <c>AudioListener.volume</c> (settings applier),
    /// the others are gains the audio code multiplies in - engine = <c>EngineAudio.ChannelGain</c>, ambient =
    /// <c>AmbientAudio.ChannelGain</c>, cab signals = <c>ClusterChime</c>. <see cref="Version"/> increments on every change
    /// so the runtime polls one int per frame (no allocation in the driving loop).
    /// </summary>
    public static class AudioMixLevels
    {
        public static float Master { get; private set; } = 1f;
        public static float Engine { get; private set; } = 1f;
        public static float Ambient { get; private set; } = 1f;
        public static float Ui { get; private set; } = 1f;

        public static int Version { get; private set; }

        /// <summary>GPS voice on / off (settings, ADR 0329). Read by <c>NavVoicePlayer</c> every step; no version needed.</summary>
        public static bool GpsVoice { get; private set; } = true;
        public static void SetGpsVoice(bool on) { GpsVoice = on; }

        /// <summary>0..1 while the GPS voice speaks (published by <c>NavVoicePlayer</c>, smoothed ~150 ms attack / 400 ms release);
        /// the truck audio multiplies engine / ambient / cab signals by <see cref="DuckGain"/> (ADR 0329).</summary>
        public static float VoiceDuck01 { get; private set; }
        public static void SetVoiceDuck(float v01) { VoiceDuck01 = Mathf.Clamp01(v01); }

        /// <summary>Engine / ambient level at full duck: -6 dB (0.5) - WORKING_VALUE, to be confirmed by ear (owner).</summary>
        public const float DuckDepth = 0.5f;
        /// <summary>Gain multiplier for the loops under the GPS voice: 1 (silent GPS) .. 1 - <see cref="DuckDepth"/>.</summary>
        public static float DuckGain => 1f - DuckDepth * VoiceDuck01;

        public static void Set(float master, float engine, float ambient, float ui)
        {
            master = Mathf.Clamp01(master); engine = Mathf.Clamp01(engine); ambient = Mathf.Clamp01(ambient); ui = Mathf.Clamp01(ui);
            if (master == Master && engine == Engine && ambient == Ambient && ui == Ui) return;
            Master = master; Engine = engine; Ambient = ambient; Ui = ui;
            Version++;
        }
    }
}
