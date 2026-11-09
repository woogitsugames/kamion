namespace TruckSim.Audio
{
    /// <summary>
    /// What the engine audio needs from the vehicle simulation. Implemented by the powertrain
    /// (or a debug driver). All values are read once per frame; implementations must not allocate.
    /// </summary>
    public interface IEngineAudioState
    {
        /// <summary>Crankshaft speed [rpm]. 0 = engine stopped.</summary>
        float Rpm { get; }

        /// <summary>Engine load / fuelling fraction 0..1 (0 = overrun, no injection; 1 = full load).</summary>
        float Load { get; }

        /// <summary>Driver throttle pedal 0..1 (used for turbo whistle level and lift-off detection).</summary>
        float Throttle { get; }

        /// <summary>Engine (compression-release / exhaust) brake activation 0..1.</summary>
        float EngineBrake { get; }

        /// <summary>Turbo boost as a fraction of maximum boost pressure 0..1 (from the turbo model, already lagged).</summary>
        float TurboBoost { get; }
    }

    /// <summary>Plain value snapshot of <see cref="IEngineAudioState"/> (push-style API, tests).</summary>
    public struct EngineAudioInput
    {
        public float Rpm;
        public float Load;
        public float Throttle;
        public float EngineBrake;
        public float TurboBoost;

        public static EngineAudioInput From(IEngineAudioState s)
        {
            EngineAudioInput i;
            i.Rpm = s.Rpm;
            i.Load = s.Load;
            i.Throttle = s.Throttle;
            i.EngineBrake = s.EngineBrake;
            i.TurboBoost = s.TurboBoost;
            return i;
        }
    }
}
