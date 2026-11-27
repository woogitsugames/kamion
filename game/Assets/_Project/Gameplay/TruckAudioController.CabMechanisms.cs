using Game.Vehicle.Physics;
using TruckSim.Audio;
using UnityEngine;

namespace Game.Gameplay
{
    public sealed partial class TruckAudioController
    {
        static readonly int k_Wetness = Shader.PropertyToID("_KamionWet");
        readonly System.Random m_BrakeRandom = new System.Random();
        readonly System.Random m_RattleRandom = new System.Random(3550);
        BrakeSquealGate m_BrakeSquealGate;
        TrailerRattleGate m_TrailerRattleGate;
        AudioSource m_WiperSweepSource, m_WiperParkSource, m_BrakeSquealSource, m_TrailerRattleSource;
        int m_LastWiperStart, m_LastWiperPark;

        [Header("Trailer / fifth-wheel rattle (ADR 0355 addendum, WORKING_VALUE)")]
        [Range(0f, 1f)] public float trailerRattleVolume = 0.55f, cabTrailerRattleFactor = 0.35f;

        public int WiperSweepEvents { get; private set; }
        public int WiperParkEvents { get; private set; }
        public int BrakeSquealEvents { get; private set; }
        public int TrailerRattleEvents { get; private set; }
        public AudioClip LastWiperSweep { get; private set; }
        public AudioClip LastBrakeSqueal { get; private set; }
        public AudioClip LastTrailerRattle { get; private set; }
        public TrailerRattleKind LastTrailerRattleKind { get; private set; }
        public float TrailerRattleEnergy => m_TrailerRattleGate.Energy;
        public float WiperPlaybackPitch => m_WiperSweepSource != null ? m_WiperSweepSource.pitch : 0f;

        void SetupCabMechanisms(float frontAxleZ)
        {
            if (m_Lib.wiperDry.IsValid || m_Lib.wiperWet.IsValid)
                m_WiperSweepSource = Source("WiperSweep", null, false, new Vector3(0f, 2.5f, frontAxleZ + 0.6f), 65);
            if (m_Lib.wiperPark.IsValid)
                m_WiperParkSource = Source("WiperPark", null, false, new Vector3(0f, 2.5f, frontAxleZ + 0.6f), 65);
            if (m_Lib.brakeServiceSqueal.IsValid)
                m_BrakeSquealSource = Source("ServiceBrakeSqueal", null, false, new Vector3(0f, 0.5f, frontAxleZ), 68);
            if (m_Lib.trailerRattleChainA.IsValid || m_Lib.trailerRattleChainB.IsValid ||
                m_Lib.trailerRattleTarpA.IsValid || m_Lib.trailerRattleKingpin.IsValid)
                m_TrailerRattleSource = Source("TrailerRattle", null, false, new Vector3(0f, 1.2f, -1.5f), 74);
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
            if (m_BrakeSquealSource != null)
            {
                m_BrakeSquealSource.spatialBlend = spatial;
                float pressure = 0f;
                var wheels = model.Wheels;
                for (int i = 0; i < wheels.Length; i++)
                    if (wheels[i].Contact) pressure = Mathf.Max(pressure, (float)wheels[i].BrakePressure);
                bool inhibited = vehicle.Input.ParkingBrake || model.HillHoldActive;
                if (m_BrakeSquealGate.Step(dt, speedKmh, pressure, (float)model.BrakeDemand, inhibited, m_BrakeRandom))
                {
                    var squeal = Perspective(m_Lib.brakeServiceSqueal);
                    m_BrakeSquealSource.volume = 0.22f;
                    m_BrakeSquealSource.pitch = Mathf.Lerp(0.90f, 1.10f, (float)m_BrakeRandom.NextDouble());
                    m_BrakeSquealSource.PlayOneShot(squeal);
                    LastBrakeSqueal = squeal;
                    BrakeSquealEvents++;
                }
            }
            UpdateTrailerRattle(dt, spatial);
        }

        void UpdateTrailerRattle(float dt, float spatial)
        {
            if (m_TrailerRattleSource == null) return;
            m_TrailerRattleSource.spatialBlend = spatial;
            bool coupled = vehicle.Trailer != null && vehicle.Coupled && vehicle.Trailer.Model != null;
            double simTime = 0;
            float tSpeedKmh = 0f, bodyVertAccel = 0f, maxComp = 0f, signedPeak = 0f, kingpinY = 0f, massKg = 0f, rough = 0f;
            double sinceCoupled = 100.0;
            if (coupled)
            {
                var tm = vehicle.Trailer.Model;
                var fw = vehicle.Combination.FifthWheel;
                simTime = tm.Time;
                tSpeedKmh = Mathf.Abs((float)tm.SpeedForward) * 3.6f;
                bodyVertAccel = Mathf.Abs((float)tm.LocalAcceleration.y);
                kingpinY = (float)fw.KingpinLoadLocal.y;
                massKg = (float)tm.Mass;
                sinceCoupled = fw.SinceCoupled;
                var tw = tm.Wheels;
                float totalFz = 0f, roughFz = 0f;
                for (int i = 0; i < tw.Length; i++)
                {
                    if (!tw[i].Contact) continue;
                    float cr = (float)tw[i].CompressionRate;
                    float acr = Mathf.Abs(cr);
                    if (acr > maxComp) { maxComp = acr; signedPeak = cr; }
                    float fz = (float)tw[i].Fz;
                    if (fz > 0f)
                    {
                        totalFz += fz;
                        int sid = tw[i].SurfaceId;
                        if (sid == 3 || sid == 4 || sid == 5) roughFz += fz;
                    }
                }
                rough = totalFz > 1f ? roughFz / totalFz : 0f;
            }
            if (!m_TrailerRattleGate.Step(dt, simTime, coupled, tSpeedKmh, bodyVertAccel, maxComp, signedPeak,
                    kingpinY, massKg, rough, sinceCoupled, m_RattleRandom, out var kind, out float gain, out float pitch))
                return;
            var pair = TrailerRattlePair(kind);
            var clip = Perspective(pair);
            if (clip == null) return;
            float vol = trailerRattleVolume * Mathf.Lerp(1f, cabTrailerRattleFactor, m_Interior) * gain;
            m_TrailerRattleSource.pitch = pitch;
            m_TrailerRattleSource.PlayOneShot(clip, vol);
            LastTrailerRattle = clip;
            LastTrailerRattleKind = kind;
            TrailerRattleEvents++;
        }

        VehicleAudioLibrary.PerspectivePair TrailerRattlePair(TrailerRattleKind kind)
        {
            switch (kind)
            {
                case TrailerRattleKind.ChainB: return m_Lib.trailerRattleChainB.IsValid ? m_Lib.trailerRattleChainB : m_Lib.trailerRattleChainA;
                case TrailerRattleKind.TarpA: return m_Lib.trailerRattleTarpA.IsValid ? m_Lib.trailerRattleTarpA : m_Lib.trailerRattleChainA;
                case TrailerRattleKind.Kingpin: return m_Lib.trailerRattleKingpin.IsValid ? m_Lib.trailerRattleKingpin : m_Lib.trailerRattleChainB;
                default: return m_Lib.trailerRattleChainA;
            }
        }

        AudioClip Perspective(in VehicleAudioLibrary.PerspectivePair pair) =>
            m_Interior > 0.5f && pair.cab != null ? pair.cab : pair.ext;
    }
}
