using Game.Cameras;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using TruckSim.Audio;
using UnityEngine;

namespace Game.Gameplay
{
    /// <summary>
    /// Connects the physics state of the player tractor to the audio runtime (docs/AUDIO_DESIGN.md §5, ADR 0007):
    /// - <see cref="EngineAudio"/> (rpm × load loop grids, engine brake, turbo) on the engine bay, fed through
    ///   <see cref="IEngineAudioState"/> from <see cref="VehicleModel"/>;
    /// - cab vs exterior bank blend from the camera mode (cab view = 1), smoothed over 0.15 s;
    /// - pneumatic one-shots from model events: service-brake release hiss, spring parking brake set / release,
    ///   air-dryer purge at governor cut-out, AMT shift cylinder;
    /// - road-roll and wind loops by speed (levels per AUDIO_DESIGN §4).
    /// Clips come from <see cref="VehicleAudioLibrary.LoadDefault"/>; without the generated library the truck is silent
    /// and a single warning is logged. No allocations after Start.
    /// </summary>
    [DefaultExecutionOrder(250)]
    public sealed class TruckAudioController : MonoBehaviour, IEngineAudioState
    {
        public VehicleBody vehicle;
        public CameraRig rig;

        [Header("Mix (WORKING_VALUE, owner listening test pending)")]
        [Range(0f, 1f)] public float pneumaticsVolume = 0.55f;
        [Range(0f, 1f)] public float roadVolume = 0.45f, windVolume = 0.30f;
        [Range(0f, 1f)] public float cabRoadFactor = 0.55f, cabWindFactor = 0.35f, cabPneumaticsFactor = 0.6f;

        VehicleAudioLibrary m_Lib;
        EngineAudio m_Engine;
        AudioSource m_OneShot, m_Road, m_Wind;
        float m_Interior = 1f;
        float m_BrakePeak, m_BrakeHeld;
        bool m_PrevPark, m_PrevCompressor, m_HasPrev;
        AmtState m_PrevAmt;

        public bool HasAudio => m_Engine != null;
        public float InteriorBlend => m_Interior;
        public EngineAudio Engine => m_Engine;

        // ---- IEngineAudioState ----
        public float Rpm => vehicle != null && vehicle.Initialized ? (float)vehicle.Model.Engine.Rpm : 0f;
        public float Load => vehicle != null && vehicle.Initialized ? Mathf.Clamp01((float)vehicle.Model.Engine.LastLoad) : 0f;
        public float Throttle => vehicle != null && vehicle.Initialized ? Mathf.Clamp01((float)vehicle.Model.ThrottleDemand) : 0f;
        public float EngineBrake => vehicle != null && vehicle.Initialized ? Mathf.Clamp01((float)vehicle.Model.Engine.EngineBrakeState) : 0f;
        public float TurboBoost => vehicle != null && vehicle.Initialized ? Mathf.Clamp01((float)vehicle.Model.Engine.Boost) : 0f;

        void Start()
        {
            m_Lib = VehicleAudioLibrary.LoadDefault();
            if (m_Lib == null || m_Lib.exteriorEngine == null)
            {
                Debug.LogWarning("[AUDIO] VehicleAudioLibrary missing (run tools/audio/render_all.py + Kamion/Audio/Import vehicle audio) — truck is silent");
                enabled = false;
                return;
            }
            var t = vehicle.transform;
            float wb = (float)vehicle.Model.Def.axles[0].positionZ;
            var go = new GameObject("EngineAudio");
            go.SetActive(false);
            go.transform.SetParent(t, false);
            go.transform.localPosition = new Vector3(0f, 1.0f, wb + 0.4f); // engine bay under the cab
            m_Engine = go.AddComponent<EngineAudio>();
            m_Engine.Configure(m_Lib, this);
            go.SetActive(true);

            m_OneShot = Source("Pneumatics", null, false, new Vector3(0f, 0.9f, wb * 0.5f), 64);
            m_Road = Source("RoadRoll", m_Lib.roadRollLoop, true, new Vector3(0f, 0.5f, wb * 0.5f), 64);
            m_Wind = Source("Wind", m_Lib.windLoop, true, new Vector3(0f, 3.0f, wb + 1.0f), 96);
            Debug.Log($"[AUDIO] vehicle audio ready ({m_Lib.sourceInfo})");
        }

        AudioSource Source(string name, AudioClip clip, bool loop, Vector3 local, int priority)
        {
            var go = new GameObject(name);
            go.transform.SetParent(vehicle.transform, false);
            go.transform.localPosition = local;
            var s = go.AddComponent<AudioSource>();
            s.playOnAwake = false;
            s.loop = loop;
            s.clip = clip;
            s.volume = 0f;
            s.priority = priority;
            s.dopplerLevel = 0f;
            s.rolloffMode = AudioRolloffMode.Logarithmic;
            s.minDistance = 4f;
            s.maxDistance = 250f;
            if (loop && clip != null) s.Play();
            return s;
        }

        void Update()
        {
            if (m_Engine == null || vehicle == null || !vehicle.Initialized) return;
            float dt = Time.deltaTime;
            float target = rig == null || rig.mode == CameraMode.Cab ? 1f : 0f;
            m_Interior = Mathf.MoveTowards(m_Interior, target, dt / 0.15f);
            m_Engine.InteriorBlend = m_Interior;
            float spatial = 1f - m_Interior; // cab: 2D, outside: 3D at the source

            var m = vehicle.Model;
            float v = Mathf.Abs((float)m.SpeedForward);
            float vn = Mathf.Clamp01(v / 25f);
            float roadGain = Mathf.Lerp(1f, cabRoadFactor, m_Interior), windGain = Mathf.Lerp(1f, cabWindFactor, m_Interior);
            if (m_Road.clip != null)
            {
                m_Road.volume = roadVolume * roadGain * Mathf.Pow(vn, 1.6f);
                m_Road.pitch = 0.75f + 0.6f * vn;
                m_Road.spatialBlend = spatial;
            }
            if (m_Wind.clip != null)
            {
                m_Wind.volume = windVolume * windGain * Mathf.Pow(vn, 2.2f);
                m_Wind.spatialBlend = spatial;
            }
            m_OneShot.spatialBlend = spatial;

            // ---- pneumatic events ----
            float pv = pneumaticsVolume * Mathf.Lerp(1f, cabPneumaticsFactor, m_Interior);
            float brake = (float)m.BrakeDemand;
            if (brake > 0.08f) { m_BrakePeak = Mathf.Max(m_BrakePeak, brake); m_BrakeHeld += dt; }
            else if (m_BrakePeak > 0f)
            {
                // Release after a held application: exhaust from the relay valves, louder after harder braking.
                if (m_BrakeHeld > 0.25f && m_Lib.airBrakeRelease != null) m_OneShot.PlayOneShot(m_Lib.airBrakeRelease, pv * Mathf.Lerp(0.35f, 1f, m_BrakePeak));
                m_BrakePeak = 0f; m_BrakeHeld = 0f;
            }
            bool park = vehicle.Input.ParkingBrake;
            bool comp = m.Air.CompressorLoaded;
            var amt = m.Amt.State;
            if (m_HasPrev)
            {
                if (park && !m_PrevPark && m_Lib.parkingBrakeSet != null) m_OneShot.PlayOneShot(m_Lib.parkingBrakeSet, pv);
                if (!park && m_PrevPark && m_Lib.airBrakeRelease != null) m_OneShot.PlayOneShot(m_Lib.airBrakeRelease, pv * 0.5f);
                if (m_PrevCompressor && !comp && m_Lib.airDryerPurge != null) m_OneShot.PlayOneShot(m_Lib.airDryerPurge, pv * 0.8f);
                bool shiftStart = (amt == AmtState.ShiftTorqueRamp || amt == AmtState.ShiftNeutral) &&
                                  m_PrevAmt != AmtState.ShiftTorqueRamp && m_PrevAmt != AmtState.ShiftNeutral;
                if (shiftStart && m_Lib.gearshiftAir != null) m_OneShot.PlayOneShot(m_Lib.gearshiftAir, pv * 0.6f);
            }
            m_PrevPark = park; m_PrevCompressor = comp; m_PrevAmt = amt; m_HasPrev = true;
        }

        /// <summary>Called after a respawn: avoids one-shots for the state jump.</summary>
        public void ResetEvents() { m_HasPrev = false; m_BrakePeak = 0f; m_BrakeHeld = 0f; }
    }
}
