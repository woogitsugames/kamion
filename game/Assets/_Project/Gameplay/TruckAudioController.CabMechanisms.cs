using Game.Vehicle.Physics;
using TruckSim.Audio;
using UnityEngine;

namespace Game.Gameplay
{
    public sealed partial class TruckAudioController
    {
        static readonly int k_Wetness = Shader.PropertyToID("_KamionWet");
        readonly System.Random m_BrakeRandom = new System.Random();
        BrakeSquealGate m_BrakeSquealGate;
        AudioSource m_WiperSweepSource, m_WiperParkSource, m_BrakeSquealSource;
        int m_LastWiperStart, m_LastWiperPark;

        public int WiperSweepEvents { get; private set; }
        public int WiperParkEvents { get; private set; }
        public int BrakeSquealEvents { get; private set; }
        public AudioClip LastWiperSweep { get; private set; }
        public AudioClip LastBrakeSqueal { get; private set; }
        public float WiperPlaybackPitch => m_WiperSweepSource != null ? m_WiperSweepSource.pitch : 0f;

        void SetupCabMechanisms(float frontAxleZ)
        {
            if (m_Lib.wiperDry.IsValid || m_Lib.wiperWet.IsValid)
                m_WiperSweepSource = Source("WiperSweep", null, false, new Vector3(0f, 2.5f, frontAxleZ + 0.6f), 65);
            if (m_Lib.wiperPark.IsValid)
                m_WiperParkSource = Source("WiperPark", null, false, new Vector3(0f, 2.5f, frontAxleZ + 0.6f), 65);
            if (m_Lib.brakeServiceSqueal.IsValid)
                m_BrakeSquealSource = Source("ServiceBrakeSqueal", null, false, new Vector3(0f, 0.5f, frontAxleZ), 68);
        }

        void UpdateCabMechanisms(VehicleModel model, float speedKmh, float dt, float spatial)
        {
            var wipers = vehicle.Wipers;
            if (m_WiperSweepSource != null)
            {
                m_WiperSweepSource.spatialBlend = spatial;
                if (m_LastWiperStart != wipers.Starts)
                {
                    m_LastWiperStart = wipers.Starts;
                    // The current weather preset exposes surface wetness. Until rain is simulated,
                    // use it as the glass wetness proxy and keep the chosen material for both strokes.
                    bool wet = Shader.GetGlobalVector(k_Wetness).x >= 0.25f;
                    var pair = wet && m_Lib.wiperWet.IsValid ? m_Lib.wiperWet : m_Lib.wiperDry;
                    var clip = Perspective(pair);
                    if (clip != null)
                    {
                        m_WiperSweepSource.Stop();
                        m_WiperSweepSource.clip = clip;
                        m_WiperSweepSource.volume = 0.46f;
                        m_WiperSweepSource.pitch = clip.length / wipers.CycleSeconds;
                        m_WiperSweepSource.Play();
                        LastWiperSweep = clip;
                        WiperSweepEvents++;
                    }
                }
            }
            if (m_WiperParkSource != null)
            {
                m_WiperParkSource.spatialBlend = spatial;
                if (m_LastWiperPark != wipers.Parks)
                {
                    m_LastWiperPark = wipers.Parks;
                    m_WiperParkSource.volume = 0.26f;
                    m_WiperParkSource.PlayOneShot(Perspective(m_Lib.wiperPark));
                    WiperParkEvents++;
                }
            }
            if (m_BrakeSquealSource == null) return;
            m_BrakeSquealSource.spatialBlend = spatial;
            float pressure = 0f;
            var wheels = model.Wheels;
            for (int i = 0; i < wheels.Length; i++)
                if (wheels[i].Contact) pressure = Mathf.Max(pressure, (float)wheels[i].BrakePressure);
            bool inhibited = vehicle.Input.ParkingBrake || model.HillHoldActive;
            if (!m_BrakeSquealGate.Step(dt, speedKmh, pressure, (float)model.BrakeDemand, inhibited, m_BrakeRandom)) return;
            var squeal = Perspective(m_Lib.brakeServiceSqueal);
            m_BrakeSquealSource.volume = 0.22f;
            m_BrakeSquealSource.pitch = Mathf.Lerp(0.90f, 1.10f, (float)m_BrakeRandom.NextDouble());
            m_BrakeSquealSource.PlayOneShot(squeal);
            LastBrakeSqueal = squeal;
            BrakeSquealEvents++;
        }

        AudioClip Perspective(in VehicleAudioLibrary.PerspectivePair pair) =>
            m_Interior > 0.5f && pair.cab != null ? pair.cab : pair.ext;
    }
}
