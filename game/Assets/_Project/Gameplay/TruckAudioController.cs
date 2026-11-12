using Game.Cameras;
using Game.Core;
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
    /// - tyre rolling per surface (six loops cross-faded by the contact load on each SurfaceKind, tractor + trailer wheels),
    ///   tyre scrub from the trailer axles' slip angle at low speed and tyre squeal from combined slip at speed (ADR 0145),
    ///   wind by speed; every loop in an exterior and a prerendered cabin perspective;
    /// - retarder whine (Retarder.Fill), air compressor (Air.CompressorLoaded, pitch by rpm), parking-brake release,
    ///   flasher relay tick/tock (<see cref="OnFlasherEdge"/>, driven by the turn-signal stalk's flasher so the click and the lamps share one phase), industrial-yard ambience
    ///   (<see cref="AmbientAudio"/>).
    /// Clips come from <see cref="VehicleAudioLibrary.LoadDefault"/>; without the generated library the truck is silent
    /// and a single warning is logged. No allocations after Start (a change of the engine source in the settings
    /// rebuilds the engine voice pool once).
    /// Engine source (ADR 0137): <see cref="AudioPreferences.EngineSource"/> picks the ElevenLabs layers (default when
    /// imported) or the procedural synthesis; the retarder loop follows the same choice.
    /// Sound set (ADR 0142): with the ElevenLabs choice the effects follow too (pneumatics, AMT up/down shift, relay,
    /// compressor, tyres wet/concrete/gravel + dry and wind in the cab, ambience bed, turbo v2) and the set adds event
    /// sounds the synthesis never had: fifth-wheel coupling, suspension bumps (wheel compression rate), cab switches
    /// (selector/mode/stalk changes), reversing beeper (selector R), gear whine; plus a cabin mix where the engine sits
    /// ~3 dB lower and tyres/wind are audible at cruise. The procedural choice keeps the pre-0142 behaviour unchanged.
    /// Horn (<see cref="AudioCues.HornHeld"/>, <see cref="HornTap"/>) and cab doors (<see cref="OnDoor"/>) use the
    /// recordings in both sets (no procedural version exists).
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
        [Tooltip("ADR 0145: full-scale squeal / scrub loops (clips at -16 / -18 LUFS ext): squeal ~ -24 LUFS, ~10 dB over the dry " +
                 "road roll at 50 km/h; scrub ~ -30 LUFS, about the loaded engine at 600 rpm (WORKING_VALUE, owner listening test).")]
        [Range(0f, 1f)] public float scrubVolume = 0.25f, cabScrubFactor = 1.0f;
        [Range(0f, 1f)] public float squealVolume = 0.40f, retarderVolume = 0.50f, compressorVolume = 0.35f, relayVolume = 0.55f;
        [Range(0f, 1f)] public float cabSquealFactor = 1.0f, cabRetarderFactor = 0.85f, cabCompressorFactor = 0.75f, extRelayFactor = 0.25f;
        [Header("ElevenLabs set (ADR 0142). Cabin balance: ADR 0142 table (levels at idle / 50 / 80 km/h)")]
        [Range(0f, 2f)] public float elCabRoadFactor = 1.35f, elCabWindFactor = 1.45f, elCabBedFactor = 0.35f;
        [Range(0f, 1f)] public float elCabEngineScale = 0.7f;
        [Range(0f, 1f)] public float hornVolume = 0.9f, doorVolume = 0.8f, switchVolume = 0.45f, coupleVolume = 0.9f;
        [Range(0f, 1f)] public float bumpVolume = 0.8f, beeperVolume = 0.45f, gearWhineVolume = 0.10f, cabHornFactor = 0.7f;
        [Tooltip("Suspension compression rate [m/s] above which a bump thump plays (WORKING_VALUE, 0.3 s cooldown).")]
        public float bumpRateThreshold = 0.45f;
        [Tooltip("Industrial yard ambience level (0 = off). A future zone system sets AmbientAudio.zone / zoneLevel instead.")]
        [Range(0f, 1f)] public float ambientZoneLevel = 1f;

        VehicleAudioLibrary m_Lib;
        EngineAudio m_Engine;
        AudioSource m_OneShot;
        PerspectiveLoop m_Wind, m_Squeal, m_Scrub, m_Retarder, m_Compressor, m_RetarderSynth, m_RetarderEl;
        int m_PrefVersion = -1;
        readonly PerspectiveLoop[] m_Tyre = new PerspectiveLoop[LayerMath.SurfaceCount];
        readonly float[] m_SurfaceTarget = new float[LayerMath.SurfaceCount];
        readonly float[] m_SurfaceWeight = new float[LayerMath.SurfaceCount];
        AmbientAudio m_Ambient;
        int m_RelayEdge;
        bool m_PurgeAlt, m_SurfaceInit;
        float m_SquealGain, m_ScrubGain, m_RetarderGain, m_CompressorGain;
        float m_Interior = 1f;
        float m_BrakePeak, m_BrakeHeld;
        bool m_PrevPark, m_PrevCompressor, m_HasPrev;
        AmtState m_PrevAmt;
        // ADR 0142
        bool m_El;
        PerspectiveLoop m_Horn, m_Beeper, m_GearWhine;
        float m_HornGain, m_HornTap, m_BumpCooldown, m_SynthCabBed = 0.5f;
        int m_PrevCouple = -1, m_PrevLever;
        bool m_PrevManual, m_PrevCruise;
        GearSelector m_PrevSelector;

        public bool HasAudio => m_Engine != null;
        public float InteriorBlend => m_Interior;
        public EngineAudio Engine => m_Engine;
        /// <summary>Engine sound set in use (falls back to procedural when the ElevenLabs set is not imported).</summary>
        public EngineSoundSource EngineSource => m_Engine != null ? m_Engine.Source : EngineSoundSource.Procedural;
        /// <summary>Smoothed share of the tyre contact load on a SurfaceKind (sums to 1); for tests and diagnostics.</summary>
        public float SurfaceWeight(int surface) => m_SurfaceWeight[surface];
        public float SquealLevel => m_SquealGain;
        /// <summary>Smoothed tyre-scrub gain 0..1 (ADR 0145).</summary>
        public float ScrubLevel => m_ScrubGain;
        /// <summary>Last raw inputs of the tyre slip layers: largest scrub slip angle [rad] and worst combined slip (norm.).</summary>
        public float ScrubSlipAngle { get; private set; }
        public float WorstCombinedSlip { get; private set; }
        public PerspectiveLoop ScrubLoop => m_Scrub;
        public PerspectiveLoop SquealLoop => m_Squeal;
        public bool AmbientReady => m_Ambient != null && m_Ambient.Ready;
        /// <summary>The ElevenLabs effect set is active (ADR 0142).</summary>
        public bool ElevenLabsFx => m_El;
        /// <summary>Event counters and the last one-shot clip (tests, diagnostics; no allocation).</summary>
        public int ShiftUpEvents { get; private set; }
        public int ShiftDownEvents { get; private set; }
        public int SwitchEvents { get; private set; }
        public int BumpEvents { get; private set; }
        public int CoupleEvents { get; private set; }
        public AudioClip LastOneShot { get; private set; }
        public float HornLevel => m_HornGain;
        public PerspectiveLoop TyreLoop(int surface) => m_Tyre[surface];
        public PerspectiveLoop WindLoop => m_Wind;
        public PerspectiveLoop CompressorLoop => m_Compressor;
        public PerspectiveLoop BeeperLoop => m_Beeper;
        public AmbientAudio Ambient => m_Ambient;

        // ---- IEngineAudioState ----
        public float Rpm => vehicle != null && vehicle.Initialized ? (float)vehicle.Model.Engine.Rpm : 0f;
        public float Load => vehicle != null && vehicle.Initialized ? Mathf.Clamp01((float)vehicle.Model.Engine.LastLoad) : 0f;
        public float Throttle => vehicle != null && vehicle.Initialized ? Mathf.Clamp01((float)vehicle.Model.ThrottleDemand) : 0f;
        /// <summary>
        /// Engine-brake activation for the sound. Muted while the AMT is mid-shift: the upshift synchronisation brake
        /// (ADR 0134) and the decaying actuator state must not play the exhaust-brake roar for a few frames at every
        /// upshift. TODO(lider, after truck-feel merge): gate on <c>Amt.SyncBrakeRequest</c> instead of the shift states.
        /// </summary>
        public float EngineBrake
        {
            get
            {
                if (vehicle == null || !vehicle.Initialized) return 0f;
                var st = vehicle.Model.Amt.State;
                if (st == AmtState.ShiftTorqueRamp || st == AmtState.ShiftNeutral || st == AmtState.ShiftSync || st == AmtState.ShiftEngage) return 0f;
                return Mathf.Clamp01((float)vehicle.Model.Engine.EngineBrakeState);
            }
        }
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
            m_PrefVersion = AudioPreferences.Version;
            m_Engine.Configure(m_Lib, this, WantedSource());
            go.SetActive(true);

            m_OneShot = Source("Pneumatics", null, false, new Vector3(0f, 0.9f, wb * 0.5f), 64);
            var road = new Vector3(0f, 0.5f, wb * 0.5f);
            for (int i = 0; i < LayerMath.SurfaceCount; i++)
            {
                // surface 0 (dry asphalt) is the original road-roll loop; older libraries lack the others -> fall back to it
                var pair = m_Lib.tyreSurface != null && i < m_Lib.tyreSurface.Length && m_Lib.tyreSurface[i].IsValid
                    ? m_Lib.tyreSurface[i]
                    : new VehicleAudioLibrary.PerspectivePair { ext = m_Lib.roadRollLoop, cab = m_Lib.roadRollLoopCab };
                m_Tyre[i] = new PerspectiveLoop(t, "Tyre" + i, pair.ext, pair.cab, road, 64, 1f);
            }
            m_Wind = new PerspectiveLoop(t, "Wind", m_Lib.windLoop, m_Lib.windLoopCab, new Vector3(0f, 3.0f, wb + 1.0f), 96, 1f);
            m_Squeal = new PerspectiveLoop(t, "TyreSqueal", m_Lib.tyreSqueal.ext, m_Lib.tyreSqueal.cab, road, 60, 1f);
            // scrub sits at the trailer axles when coupled (they do the dragging), clips set in ApplySoundSet
            m_Scrub = new PerspectiveLoop(t, "TyreScrub", m_Lib.tyreScrub.ext, m_Lib.tyreScrub.cab, new Vector3(0f, 0.5f, -6.0f), 62, 1f);
            m_RetarderSynth = new PerspectiveLoop(t, "Retarder", m_Lib.retarder.ext, m_Lib.retarder.cab, new Vector3(0f, 0.7f, wb * 0.6f), 70, 1f);
            m_RetarderEl = m_Lib.elRetarder.IsValid
                ? new PerspectiveLoop(t, "RetarderEL", m_Lib.elRetarder.ext, m_Lib.elRetarder.cab, new Vector3(0f, 0.7f, wb * 0.6f), 70, 1f)
                : null;
            m_Compressor = new PerspectiveLoop(t, "Compressor", m_Lib.compressor.ext, m_Lib.compressor.cab, new Vector3(0.5f, 0.8f, wb + 0.5f), 80, 1f);
            if (m_Lib.ambientBed.IsValid)
            {
                var ag = new GameObject("Ambient");
                ag.transform.SetParent(t, false);
                m_Ambient = ag.AddComponent<AmbientAudio>();
                m_Ambient.zoneLevel = ambientZoneLevel;
                m_Ambient.Configure(m_Lib);
                m_SynthCabBed = m_Ambient.cabBedFactor;
            }
            if (m_Lib.elHorn.IsValid) m_Horn = new PerspectiveLoop(t, "Horn", m_Lib.elHorn.ext, m_Lib.elHorn.cab, new Vector3(0f, 3.6f, wb + 0.8f), 50, 1f);
            if (m_Lib.elReverseBeeper.IsValid)
                m_Beeper = new PerspectiveLoop(t, "ReverseBeeper", m_Lib.elReverseBeeper.ext, m_Lib.elReverseBeeper.cab, new Vector3(0f, 0.8f, -1.0f), 90, 1f);
            if (m_Lib.elGearWhineCab != null)
                m_GearWhine = new PerspectiveLoop(t, "GearWhine", m_Lib.elGearWhineCab, m_Lib.elGearWhineCab, new Vector3(0f, 1.0f, wb + 0.4f), 120, 1f);
            SelectRetarder();
            Debug.Log($"[AUDIO] vehicle audio ready ({m_Lib.sourceInfo}) engine={m_Engine.Source} elevenlabs={(m_Lib.HasElevenLabs ? "imported" : "missing")} fx={(m_Lib.HasElevenLabsFx ? "imported" : "missing")}");
        }

        EngineSoundSource WantedSource() =>
            AudioPreferences.ElevenLabsEngine && m_Lib.HasElevenLabs ? EngineSoundSource.ElevenLabs : EngineSoundSource.Procedural;

        void SelectRetarder()
        {
            var want = m_Engine.Source == EngineSoundSource.ElevenLabs && m_RetarderEl != null ? m_RetarderEl : m_RetarderSynth;
            if (m_Retarder != null && m_Retarder != want) m_Retarder.Set(0f, 1f, m_Interior);
            m_Retarder = want;
            ApplySoundSet();
        }

        /// <summary>
        /// Effect clips of the active set (ADR 0142). Called at start and on a settings change only: swaps clips on the
        /// existing sources (PerspectiveLoop.SetClips), no new objects.
        /// </summary>
        void ApplySoundSet()
        {
            m_El = m_Engine.Source == EngineSoundSource.ElevenLabs && m_Lib.HasElevenLabsFx;
            for (int i = 0; i < LayerMath.SurfaceCount; i++)
            {
                var syn = m_Lib.tyreSurface != null && i < m_Lib.tyreSurface.Length && m_Lib.tyreSurface[i].IsValid
                    ? m_Lib.tyreSurface[i]
                    : new VehicleAudioLibrary.PerspectivePair { ext = m_Lib.roadRollLoop, cab = m_Lib.roadRollLoopCab };
                var el = m_El && m_Lib.elTyreSurface != null && i < m_Lib.elTyreSurface.Length ? m_Lib.elTyreSurface[i] : default;
                if (el.IsValid) m_Tyre[i].SetClips(el.ext, el.cab, 1f);
                else if (m_El && i == 0 && m_Lib.elTyreDryCab != null) m_Tyre[i].SetClips(syn.ext, m_Lib.elTyreDryCab, 1f);
                else m_Tyre[i].SetClips(syn.ext, syn.cab, 1f);
            }
            // ADR 0145: the REGEN-03 recordings replace the procedural scrub / squeal in both sets (the procedural squeal was
            // the owner's complaint; its v2 and the scrub synthesis are placeholders for a library without REGEN-03)
            var scrub = m_Lib.elTyreScrub.IsValid ? m_Lib.elTyreScrub : m_Lib.tyreScrub;
            var squeal = m_Lib.elTyreSqueal.IsValid ? m_Lib.elTyreSqueal : m_Lib.tyreSqueal;
            m_Scrub.SetClips(scrub.ext, scrub.cab, 1f);
            m_Squeal.SetClips(squeal.ext, squeal.cab, 1f);
            m_Wind.SetClips(m_Lib.windLoop, m_El && m_Lib.elWindCab != null ? m_Lib.elWindCab : m_Lib.windLoopCab, 1f);
            if (m_El && m_Lib.elCompressor.IsValid) m_Compressor.SetClips(m_Lib.elCompressor.ext, m_Lib.elCompressor.cab, 1f);
            else m_Compressor.SetClips(m_Lib.compressor.ext, m_Lib.compressor.cab, 1f);
            if (m_Ambient != null)
            {
                m_Ambient.SetBed(m_El && m_Lib.elAmbientBed.IsValid ? m_Lib.elAmbientBed : m_Lib.ambientBed);
                m_Ambient.cabBedFactor = m_El ? elCabBedFactor : m_SynthCabBed;
            }
            m_Engine.CabEngineScale = m_El ? elCabEngineScale : 1f;
            if (!m_El)
            {
                m_Beeper?.Set(0f, 1f, m_Interior);
                m_GearWhine?.Set(0f, 1f, m_Interior);
            }
        }

        /// <summary>Applies a changed <see cref="AudioPreferences.EngineSource"/> (settings panel) once.</summary>
        void ApplyEngineSourceIfChanged()
        {
            if (m_PrefVersion == AudioPreferences.Version) return;
            m_PrefVersion = AudioPreferences.Version;
            var want = WantedSource();
            if (want == m_Engine.Source) return;
            m_Engine.Configure(m_Lib, this, want);
            SelectRetarder();
            Debug.Log($"[AUDIO] engine source switched to {m_Engine.Source}");
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

        void Update() => AudioStep(Time.deltaTime);

        /// <summary>One audio update with an explicit time step (Update uses the frame time; tests drive it with the physics
        /// step in script simulation mode). No allocation.</summary>
        public void AudioStep(float dt)
        {
            if (m_Engine == null || vehicle == null || !vehicle.Initialized) return;
            ApplyEngineSourceIfChanged();
            float target = rig == null || rig.mode == CameraMode.Cab ? 1f : 0f;
            m_Interior = Mathf.MoveTowards(m_Interior, target, dt / 0.15f);
            m_Engine.InteriorBlend = m_Interior;
            float spatial = 1f - m_Interior; // cab: 2D, outside: 3D at the source

            var m = vehicle.Model;
            float v = Mathf.Abs((float)m.SpeedForward);
            float vn = Mathf.Clamp01(v / 25f);
            UpdateTyres(m, v, dt);
            if (m_Wind.Valid) m_Wind.Set(windVolume * Mathf.Lerp(1f, m_El ? elCabWindFactor : cabWindFactor, m_Interior) * Mathf.Pow(vn, 2.2f), 1f, m_Interior);
            UpdateMechanical(m, v, dt);
            UpdateCues(m, v, dt);
            if (m_Ambient != null)
            {
                m_Ambient.Interior = m_Interior;
                m_Ambient.SpeedMs = v;
                m_Ambient.zoneLevel = ambientZoneLevel;
            }
            m_OneShot.spatialBlend = spatial;

            // ---- pneumatic events ----
            bool cabView = m_Interior > 0.5f; // one-shots pick a perspective when they start
            float pv = pneumaticsVolume * Mathf.Lerp(1f, cabPneumaticsFactor, m_Interior);
            float brake = (float)m.BrakeDemand;
            if (brake > 0.08f) { m_BrakePeak = Mathf.Max(m_BrakePeak, brake); m_BrakeHeld += dt; }
            else if (m_BrakePeak > 0f)
            {
                // Release after a held application: exhaust from the relay valves, louder after harder braking.
                if (m_BrakeHeld > 0.25f) PlaySet(m_Lib.elAirBrakeRelease, m_Lib.airBrakeRelease, m_Lib.airBrakeReleaseCab, cabView, pv * Mathf.Lerp(0.35f, 1f, m_BrakePeak));
                m_BrakePeak = 0f; m_BrakeHeld = 0f;
            }
            bool park = vehicle.Input.ParkingBrake;
            bool comp = m.Air.CompressorLoaded;
            var amt = m.Amt.State;
            if (m_HasPrev)
            {
                if (park && !m_PrevPark) PlaySet(m_Lib.elParkingBrakeSet, m_Lib.parkingBrakeSet, m_Lib.parkingBrakeSetCab, cabView, pv);
                if (!park && m_PrevPark)
                {
                    if (m_El && m_Lib.elParkingBrakeRelease.IsValid) Play(m_Lib.elParkingBrakeRelease.ext, m_Lib.elParkingBrakeRelease.cab, cabView, pv * 0.8f);
                    else if (m_Lib.parkingBrakeRelease != null) Play(m_Lib.parkingBrakeRelease, m_Lib.parkingBrakeReleaseCab, cabView, pv * 0.8f);
                    else Play(m_Lib.airBrakeRelease, m_Lib.airBrakeReleaseCab, cabView, pv * 0.5f);
                }
                if (m_PrevCompressor && !comp)
                {
                    // governor cut-out: alternate the loud purge and the softer 'psst' so it never repeats identically
                    m_PurgeAlt = !m_PurgeAlt;
                    if (m_PurgeAlt && m_Lib.airDryerPurgeB != null) PlaySet(m_Lib.elAirDryerPurgeB, m_Lib.airDryerPurgeB, m_Lib.airDryerPurgeBCab, cabView, pv * 0.9f);
                    else PlaySet(m_Lib.elAirDryerPurge, m_Lib.airDryerPurge, m_Lib.airDryerPurgeCab, cabView, pv * 0.8f);
                }
                bool shiftStart = (amt == AmtState.ShiftTorqueRamp || amt == AmtState.ShiftNeutral) &&
                                  m_PrevAmt != AmtState.ShiftTorqueRamp && m_PrevAmt != AmtState.ShiftNeutral;
                if (shiftStart)
                {
                    // AMT shift cylinder; the ElevenLabs set distinguishes up (click + clunk) and down (clunk + longer exhaust)
                    bool up = m.Amt.TargetGear > m.Amt.Gear;
                    if (up) ShiftUpEvents++; else ShiftDownEvents++;
                    PlaySet(up ? m_Lib.elGearshiftUp : m_Lib.elGearshiftDown, m_Lib.gearshiftAir, m_Lib.gearshiftAirCab, cabView, pv * 0.6f);
                }
            }
            m_PrevPark = park; m_PrevCompressor = comp; m_PrevAmt = amt; m_HasPrev = true;

            // ---- flasher relay (edges queued by OnFlasherEdge from the stalk's flasher) ----
            int ev = m_RelayEdge;
            m_RelayEdge = 0;
            if (ev != 0)
            {
                var pair = ev > 0 ? m_Lib.indicatorTick : m_Lib.indicatorTock;
                var elp = ev > 0 ? m_Lib.elIndicatorTick : m_Lib.elIndicatorTock;
                PlaySet(elp, pair.ext, pair.cab, cabView, relayVolume * (cabView ? 1f : extRelayFactor));
            }
        }

        /// <summary>Flasher relay edge for the click: +1 contact closes (tick), -1 opens (tock). Called by the gameplay layer
        /// with the return value of <c>TurnSignal.Step</c>; played in the next audio update.</summary>
        public void OnFlasherEdge(int edge) { if (edge != 0) m_RelayEdge = edge; }

        void Play(AudioClip ext, AudioClip cab, bool cabView, float volume)
        {
            var clip = cabView && cab != null ? cab : ext;
            if (clip == null) return;
            m_OneShot.PlayOneShot(clip, volume);
            LastOneShot = clip;
        }

        /// <summary>ElevenLabs clip of the event when that set is active, else the procedural pair (ADR 0142).</summary>
        void PlaySet(in VehicleAudioLibrary.PerspectivePair el, AudioClip ext, AudioClip cab, bool cabView, float volume)
        {
            if (m_El && el.IsValid) Play(el.ext, el.cab, cabView, volume);
            else Play(ext, cab, cabView, volume);
        }

        /// <summary>Short horn blast (UI button / settings preview): seconds of hold.</summary>
        public void HornTap(float seconds = 0.6f) => m_HornTap = Mathf.Max(m_HornTap, seconds);

        /// <summary>Cab door opened / closed (future cab interaction; settings preview). Recordings in both sets.</summary>
        public void OnDoor(bool open)
        {
            if (m_Lib == null) return;
            var p = open ? m_Lib.elDoorOpen : m_Lib.elDoorClose;
            if (p.IsValid) Play(p.ext, p.cab, m_Interior > 0.5f, doorVolume);
        }

        /// <summary>
        /// ADR 0142 cues: horn (hold flag / tap / settings preview), door preview, and in the ElevenLabs set: fifth-wheel
        /// coupling (FifthWheel.CouplingEvents), suspension bumps (max wheel compression rate), cab switch clicks (changes
        /// of selector, A/M mode, endurance-brake stalk, brake cruise), reversing beeper (selector R, engine running),
        /// gear whine.
        /// </summary>
        void UpdateCues(VehicleModel m, float v, float dt)
        {
            bool cabView = m_Interior > 0.5f;
            if (AudioCues.TryTake(out var cue))
            {
                if (cue == AudioCue.HornTap) HornTap();
                else if (cue == AudioCue.DoorOpen) OnDoor(true);
                else if (cue == AudioCue.DoorClose) OnDoor(false);
            }
            m_HornTap = Mathf.Max(0f, m_HornTap - dt);
            float hornTarget = AudioCues.HornHeld || m_HornTap > 0f ? hornVolume : 0f;
            m_HornGain = LayerMath.ExponentialStep(m_HornGain, hornTarget, dt, 0.012f, 0.06f);
            m_Horn?.Set(m_HornGain * Mathf.Lerp(1f, cabHornFactor, m_Interior), 1f, m_Interior);

            var input = vehicle.Input;
            int couple = vehicle.Combination != null ? vehicle.Combination.FifthWheel.CouplingEvents : 0;
            bool cruise = input.BrakeCruiseKmh > 0f;
            if (m_El && m_PrevCouple >= 0)
            {
                if (couple > m_PrevCouple && m_Lib.elTrailerCouple.IsValid)
                {
                    Play(m_Lib.elTrailerCouple.ext, m_Lib.elTrailerCouple.cab, cabView, coupleVolume);
                    CoupleEvents++;
                }
                if (m_Lib.elCabSwitch.IsValid && (input.Selector != m_PrevSelector || input.ManualMode != m_PrevManual ||
                                                  input.RetarderLever != m_PrevLever || cruise != m_PrevCruise))
                {
                    Play(m_Lib.elCabSwitch.ext, m_Lib.elCabSwitch.cab, cabView, switchVolume * (cabView ? 1f : 0.2f));
                    SwitchEvents++;
                }
            }
            m_PrevCouple = couple; m_PrevSelector = input.Selector; m_PrevManual = input.ManualMode;
            m_PrevLever = input.RetarderLever; m_PrevCruise = cruise;

            // suspension bump: fastest compression among the tractor wheels in contact
            m_BumpCooldown = Mathf.Max(0f, m_BumpCooldown - dt);
            if (m_El && m_BumpCooldown <= 0f && m_Lib.elSuspBump.IsValid)
            {
                float rate = 0f;
                var w = m.Wheels;
                for (int i = 0; i < w.Length; i++)
                    if (w[i].Contact && (float)w[i].CompressionRate > rate) rate = (float)w[i].CompressionRate;
                if (rate > bumpRateThreshold)
                {
                    float g = Mathf.Clamp01((rate - bumpRateThreshold) / bumpRateThreshold);
                    Play(m_Lib.elSuspBump.ext, m_Lib.elSuspBump.cab, cabView, bumpVolume * (0.35f + 0.65f * g));
                    m_BumpCooldown = 0.3f;
                    BumpEvents++;
                }
            }

            bool running = !m.Engine.Stalled && m.Engine.Rpm > 300.0;
            if (m_Beeper != null)
                m_Beeper.Set(m_El && running && input.Selector == GearSelector.Reverse ? beeperVolume : 0f, 1f, m_Interior);
            if (m_GearWhine != null)
            {
                // meshing gears under load at speed, heard in the cab; pitch with the input shaft (engine rpm)
                float gw = m_El ? gearWhineVolume * Mathf.Clamp01(v / 20f) * (0.3f + 0.7f * Load) * m_Interior : 0f;
                m_GearWhine.Set(gw, Mathf.Clamp((float)m.Engine.Rpm / 1300f, 0.5f, 1.8f), 1f);
            }
        }

        void UpdateTyres(VehicleModel m, float v, float dt)
        {
            // contact load per surface under the tractor and (when coupled) the trailer, and the worst slip
            for (int i = 0; i < m_SurfaceTarget.Length; i++) m_SurfaceTarget[i] = 0f;
            float total = 0f, slip = 0f, alphaTractor = 0f, alphaTrailer = 0f;
            Accumulate(m.Wheels, ref total, ref slip, ref alphaTractor);
            bool coupled = vehicle.Trailer != null && vehicle.Coupled && vehicle.Trailer.Model != null;
            if (coupled) Accumulate(vehicle.Trailer.Model.Wheels, ref total, ref slip, ref alphaTrailer);
            // scrub: the trailer axles are dragged sideways in a tight turn; solo, the tractor's own axles
            float alpha = coupled ? alphaTrailer : alphaTractor;
            ScrubSlipAngle = alpha;
            WorstCombinedSlip = slip;
            float squealable = 0f, scrubbable = 0f;
            float k = 1f - Mathf.Exp(-dt / 0.15f);
            float pitch = LayerMath.TyrePitch(v);
            for (int i = 0; i < m_SurfaceTarget.Length; i++)
            {
                float target = total > 1f ? m_SurfaceTarget[i] / total : (i == 0 ? 1f : 0f);
                m_SurfaceWeight[i] = m_SurfaceInit ? m_SurfaceWeight[i] + (target - m_SurfaceWeight[i]) * k : target; // first frame snaps (no fade-in from silence)
                squealable += m_SurfaceWeight[i] * LayerMath.SurfaceSquealable[i];
                scrubbable += m_SurfaceWeight[i] * LayerMath.SurfaceScrubbable[i];
                if (m_Tyre[i].Valid)
                    m_Tyre[i].Set(LayerMath.TyreGain(v, i, roadVolume) * m_SurfaceWeight[i] * Mathf.Lerp(1f, m_El ? elCabRoadFactor : cabRoadFactor, m_Interior), pitch, m_Interior);
            }
            m_SurfaceInit = true;
            float sg = LayerMath.SquealGain(slip, v) * squealable;
            m_SquealGain = LayerMath.ExponentialStep(m_SquealGain, sg, dt, 0.05f, 0.15f);
            if (m_Squeal.Valid)
                m_Squeal.Set(squealVolume * m_SquealGain * Mathf.Lerp(1f, cabSquealFactor, m_Interior),
                    0.9f + 0.25f * Mathf.Clamp01(slip - LayerMath.SquealOnset), m_Interior);
            float cg = LayerMath.ScrubGain(alpha, v) * scrubbable;
            // a new scrub after silence starts at a random point of the loop (6 s recording: no identical opening each turn)
            if (m_ScrubGain < 0.002f && cg > 0.002f) m_Scrub.Rephase();
            m_ScrubGain = LayerMath.ExponentialStep(m_ScrubGain, cg, dt, 0.12f, 0.25f);
            if (m_Scrub.Valid)
                m_Scrub.Set(scrubVolume * m_ScrubGain * Mathf.Lerp(1f, cabScrubFactor, m_Interior), LayerMath.ScrubPitch(alpha, v), m_Interior);
        }

        void Accumulate(Game.Vehicle.Physics.WheelState[] wheels, ref float total, ref float slip, ref float alpha)
        {
            for (int i = 0; i < wheels.Length; i++)
            {
                var w = wheels[i];
                if (!w.Contact || w.Fz <= 0.0) continue;
                float fz = (float)w.Fz;
                int sid = w.SurfaceId;
                if (sid < 0 || sid >= m_SurfaceTarget.Length) sid = 0;
                m_SurfaceTarget[sid] += fz;
                total += fz;
                float a = Mathf.Abs((float)w.SlipAngle);
                float s = LayerMath.CombinedSlip(Mathf.Abs((float)w.SlipRatio), a);
                if (s > slip) slip = s;
                if (a > alpha) alpha = a;
            }
        }

        void UpdateMechanical(VehicleModel m, float v, float dt)
        {
            float rpm = (float)m.Engine.Rpm;
            bool running = !m.Engine.Stalled && rpm > 300f;
            float rg = LayerMath.RetarderGain((float)m.Retarder.Fill, retarderVolume);
            m_RetarderGain = LayerMath.ExponentialStep(m_RetarderGain, rg, dt, 0.08f, 0.25f);
            if (m_Retarder.Valid) m_Retarder.Set(m_RetarderGain * Mathf.Lerp(1f, cabRetarderFactor, m_Interior), LayerMath.RetarderPitch(v), m_Interior);
            float cg = running && m.Air.CompressorLoaded ? compressorVolume : 0f;
            m_CompressorGain = LayerMath.ExponentialStep(m_CompressorGain, cg, dt, 0.15f, 0.12f);
            if (m_Compressor.Valid) m_Compressor.Set(m_CompressorGain * Mathf.Lerp(1f, cabCompressorFactor, m_Interior), LayerMath.CompressorPitch(rpm), m_Interior);
        }

        /// <summary>Called after a respawn: avoids one-shots for the state jump.</summary>
        public void ResetEvents() { m_HasPrev = false; m_BrakePeak = 0f; m_BrakeHeld = 0f; m_PrevCouple = -1; m_BumpCooldown = 0.5f; }
    }
}
