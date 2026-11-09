using UnityEngine;

namespace TruckSim.Audio
{
    /// <summary>
    /// Inspector-driven <see cref="IEngineAudioState"/> for listening tests without the powertrain.
    /// Optional auto-sweep runs rpm back and forth at the given load.
    /// </summary>
    public sealed class EngineAudioDebugState : MonoBehaviour, IEngineAudioState
    {
        [Range(0f, 2300f)] public float rpm = 600f;
        [Range(0f, 1f)] public float load = 0.12f;
        [Range(0f, 1f)] public float throttle;
        [Range(0f, 1f)] public float engineBrake;
        [Range(0f, 1f)] public float turboBoost;
        public bool autoSweep;
        [Range(50f, 1500f)] public float sweepRpmPerSecond = 150f;

        float _dir = 1f;

        public float Rpm => rpm;
        public float Load => load;
        public float Throttle => throttle;
        public float EngineBrake => engineBrake;
        public float TurboBoost => turboBoost;

        void Update()
        {
            if (!autoSweep) return;
            rpm += _dir * sweepRpmPerSecond * Time.deltaTime;
            if (rpm > 2100f) { rpm = 2100f; _dir = -1f; }
            if (rpm < 600f) { rpm = 600f; _dir = 1f; }
        }
    }
}
