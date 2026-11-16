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

        public static void Set(float master, float engine, float ambient, float ui)
        {
            master = Mathf.Clamp01(master); engine = Mathf.Clamp01(engine); ambient = Mathf.Clamp01(ambient); ui = Mathf.Clamp01(ui);
            if (master == Master && engine == Engine && ambient == Ambient && ui == Ui) return;
            Master = master; Engine = engine; Ambient = ambient; Ui = ui;
            Version++;
        }
    }
}
