using UnityEngine;

namespace Game.Core
{
    /// <summary>
    /// Player audio preferences shared by the settings panel (Game.UI) and the audio runtime (Game.Gameplay), ADR 0137.
    /// Engine sound source: the ElevenLabs recordings or the procedural synthesis (owner A/B comparison).
    /// Stored in PlayerPrefs; <see cref="Version"/> increments on every change so the runtime can poll without allocating.
    /// </summary>
    public static class AudioPreferences
    {
        public const string PrefEngineSource = "audio.engineSource";
        public const int EngineProcedural = 0, EngineElevenLabs = 1;

        static int s_Engine = -1;

        /// <summary>Incremented whenever a preference changes in this process.</summary>
        public static int Version { get; private set; }

        /// <summary>0 = procedural synthesis (ADR 0007), 1 = ElevenLabs layers (ADR 0137, default).</summary>
        public static int EngineSource
        {
            get
            {
                if (s_Engine < 0) s_Engine = Mathf.Clamp(PlayerPrefs.GetInt(PrefEngineSource, EngineElevenLabs), 0, 1);
                return s_Engine;
            }
            set
            {
                int v = Mathf.Clamp(value, 0, 1);
                if (v == EngineSource) return;
                s_Engine = v;
                PlayerPrefs.SetInt(PrefEngineSource, v);
                PlayerPrefs.Save();
                Version++;
                Debug.Log("[AUDIO] engine source=" + (v == EngineElevenLabs ? "elevenlabs" : "procedural"));
            }
        }

        public static bool ElevenLabsEngine
        {
            get => EngineSource == EngineElevenLabs;
            set => EngineSource = value ? EngineElevenLabs : EngineProcedural;
        }

        /// <summary>Launch argument / test override: "el" | "elevenlabs" | "synth" | "procedural". Unknown values are ignored.</summary>
        public static void ApplyArgument(string arg)
        {
            if (string.IsNullOrEmpty(arg)) return;
            arg = arg.ToLowerInvariant();
            if (arg == "el" || arg == "elevenlabs") EngineSource = EngineElevenLabs;
            else if (arg == "synth" || arg == "procedural") EngineSource = EngineProcedural;
        }
    }
}
