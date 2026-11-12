using System.Collections.Generic;
using System.Globalization;
using Game.Cameras;
using Game.Controls;
using Game.Platform;
using Game.Rendering;
using Game.Telemetry;
using Game.UI;
using Game.UI.Driving;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Game.Gameplay
{
    /// <summary>
    /// Composition root of the DrivingLab scene: wires input sources (autopilot, keyboard, touch wheel or gyro,
    /// touch pedals) through <see cref="DriverInputMixer"/> into <see cref="VehicleBody.Input"/>, owns the driver
    /// state (selector, manual mode, parking brake, endurance-brake stalk, brake cruise), the trailer and its
    /// coupling, the camera rig, mirrors, reversing camera, HUD, audio, telemetry recorder and diagnostics.
    /// Launch arguments: <c>autopilot</c> (circle50 | circle25), <c>speed</c> (km/h) and <c>trailer</c>
    /// (solo | empty | 24 | 40) for scripted device runs. An autopilot run without <c>trailer</c> is solo (Stage 1 measurement).
    /// </summary>
    [DefaultExecutionOrder(-200)]
    public sealed class DrivingLabBootstrap : MonoBehaviour
    {
        public enum SteerMode { Wheel270 = 0, Wheel900 = 1, Gyro = 2 }
        /// <summary>Spawn presets of the lab menu. Solo = tractor in the coupling bay, trailer parked behind it.</summary>
        public enum LabSpawn { Solo = 0, Empty = 1, Cargo24t = 2, Gross40t = 3 }
        const string PrefSpawn = "lab.spawn";
        /// <summary>
        /// Load at the first start / for players who never picked one (owner decision, ADR 0134, 2026-11-12): 24 t payload,
        /// ~40 t combination. "lab.spawn" is written only by an explicit choice in the spawn menu, so a stored value is kept.
        /// </summary>
        public const LabSpawn DefaultSpawn = LabSpawn.Cargo24t;

        /// <summary>Stored spawn choice (explicit menu pick) or <see cref="DefaultSpawn"/> when none is stored.</summary>
        public static LabSpawn StoredOrDefaultSpawn(bool hasStored, int stored) =>
            hasStored ? (LabSpawn)Mathf.Clamp(stored, 0, 3) : DefaultSpawn;

        public VehicleBody vehicle;
        public TrailerBody trailer;
        public Camera mainCamera;
        [Tooltip("World scenes (WorldC): spawn here instead of the lab layout; forward = heading")]
        public Transform spawnPoint;
        [Tooltip("World scenes: route for the route autopilot (launch argument autopilot=route)")]
        public Game.World.WorldRoute route;

        readonly DriverInputMixer m_Mixer = new DriverInputMixer();
        public readonly AutopilotDriverInput Autopilot = new AutopilotDriverInput();
        public readonly KeyboardDriverInput Keyboard = new KeyboardDriverInput();
        public readonly TouchSteeringWheel Wheel = new TouchSteeringWheel();
        public readonly GyroSteering Gyro = new GyroSteering();
        /// <summary>The simulated cab steering wheel (ADR 0058): driver target → hand-rate-limited wheel → Steering command, in the fixed step.</summary>
        public readonly SteeringColumn Column = new SteeringColumn();   // tuning loaded in Awake (Resources)
        float m_SteerTarget;
        bool m_SteerHandsOn, m_SteerBypass, m_SteerHasTarget;
        public readonly TouchControls Touch = new TouchControls();
        /// <summary>Turn-signal stalk + flasher (self-cancelling, 1.5 Hz); drives the lamps, the cluster arrows and the relay click.</summary>
        public readonly TurnSignal Signals = new TurnSignal();
        TruckLights m_Lights;
        public readonly PathFollowerDriverInput RouteDriver = new PathFollowerDriverInput();

        CameraRig m_Rig;
        DrivingHud m_Hud;
        VehicleTelemetryRecorder m_Recorder;
        DiagnosticsSampler m_Sampler;
        TruckAudioController m_Audio;
        SteerMode m_SteerMode;
        LabSpawn m_Spawn = DefaultSpawn;
        GearSelector m_Selector = GearSelector.Drive;
        bool m_Manual, m_Parking = true, m_AbsFault, m_ReverseCamForced;
        int m_Lever, m_LeverMax = 5, m_CouplingEvents;
        float m_CruiseKmh;
        string m_Status = "";
        float m_StatusUntil;
        ReversingCamera m_TractorCam, m_TrailerCam, m_ActiveRevCam;
        RenderTextureMirror m_MirrorL, m_MirrorR;
        bool m_MirrorInsets;
        const string PrefMirrorInsets = "lab.mirrorInsets";
        bool m_AutopilotStart;
        float m_RouteS = -1f, m_RouteEndS = -1f;
        bool m_RouteDoneLogged;
        float m_StartTime;
        Transform[] m_IgnoreRoots;

        /// <summary>Player control settings (settings menu); loaded from PlayerPrefs at start, saved on every change.</summary>
        public ControlSettings Controls { get; private set; }
        ControlSettingsPanel m_SettingsPanel;
        ControlInputLogger m_InputLog;
        CameraMode m_LoggedCamMode;
        static readonly string[] k_CamModeEvents = { "camera mode=Cab", "camera mode=Chase", "camera mode=Orbit" };   // cached: no string building at runtime
        public SteerMode CurrentSteerMode => m_SteerMode;
        public LabSpawn CurrentSpawn => m_Spawn;
        public DriverInputMixer Mixer => m_Mixer;
        public int RetarderLever => m_Lever;
        public bool AbsFault => m_AbsFault;

        void Awake()
        {
            Time.fixedDeltaTime = 0.01f;     // 100 Hz (also in ProjectSettings/TimeManager.asset)
            Time.maximumDeltaTime = 0.1f;    // at most 10 physics steps per rendered frame
            if (Application.targetFrameRate <= 0) QualityTiers.SetTargetFrameRate(QualityTiers.SavedFrameRate > 0 ? QualityTiers.SavedFrameRate : 30);
            Screen.sleepTimeout = SleepTimeout.NeverSleep;

            if (vehicle == null) vehicle = FindAnyObjectByType<VehicleBody>();
            if (trailer == null) trailer = FindAnyObjectByType<TrailerBody>();
            if (mainCamera == null) mainCamera = Camera.main;
            if (!vehicle.Initialized) vehicle.Initialize(vehicle.Data);
            m_LeverMax = 1 + Mathf.Max(0, vehicle.Model.Retarder.Def.present ? vehicle.Model.Retarder.Def.stages : 0);

            var platform = PlatformServices.Create();
            m_Sampler = FindAnyObjectByType<DiagnosticsSampler>();
            if (m_Sampler == null)
            {
                m_Sampler = gameObject.AddComponent<DiagnosticsSampler>();
                m_Sampler.Initialize(platform);
            }

            m_Mixer.Add(Autopilot);
            m_Mixer.Add(RouteDriver);
            m_Mixer.Add(Keyboard);
            m_Mixer.Add(Wheel);
            m_Mixer.Add(Gyro);
            m_Mixer.Add(Touch);
            Column.Feel = SteeringFeel.LoadDefault();
            Wheel.Feel = Column.Feel;
            Gyro.Feel = Column.Feel;
            Column.LockDeg = HandwheelLockDeg();
            GyroSteering.EnableSensors();
            Controls = ControlSettings.Load();
            ApplyControls();
            Controls.Log("loaded");
            m_InputLog = new ControlInputLogger();

            if (!vehicle.TryGetComponent(out m_Recorder)) m_Recorder = vehicle.gameObject.AddComponent<VehicleTelemetryRecorder>();
            m_Recorder.body = vehicle;

            if (!mainCamera.TryGetComponent(out m_Rig)) m_Rig = mainCamera.gameObject.AddComponent<CameraRig>();
            m_Rig.cam = mainCamera;
            m_Rig.target = vehicle.transform;
            m_Rig.targetBody = vehicle.GetComponent<Rigidbody>();
            var visuals = vehicle.GetComponent<VehicleVisuals>();
            m_Rig.eyeAnchor = visuals != null && visuals.cabPivot != null ? visuals.cabPivot.Find("DriverEyePoint") : null;
            ApplyControls();   // the rig exists now: camera settings (look gain, FOV, head motion)
            m_LoggedCamMode = m_Rig.mode;
            m_TractorCam = vehicle.GetComponentInChildren<ReversingCamera>(true);
            m_TrailerCam = trailer != null ? trailer.GetComponentInChildren<ReversingCamera>(true) : null;
            foreach (var mir in vehicle.GetComponentsInChildren<RenderTextureMirror>(true))
                if (!mir.main) continue;
                else if (mir.phase == 0) m_MirrorL = mir; else m_MirrorR = mir;
            m_MirrorInsets = PlayerPrefs.GetInt(PrefMirrorInsets, 1) != 0;

            m_Audio = gameObject.AddComponent<TruckAudioController>();
            m_Audio.vehicle = vehicle;
            m_Audio.rig = m_Rig;
            gameObject.AddComponent<ClusterChime>().vehicle = vehicle;
            // Live 12.3" cluster, navigation and DIN screens from the solver (art truck only; review r4 C-N1).
            CabScreensInstaller.Install(vehicle);

            m_Hud = DrivingHud.Create(mainCamera, new DrivingHudContext
            {
                Vehicle = vehicle, Wheel = Wheel, Touch = Touch, Gyro = Gyro, Rig = m_Rig, Recorder = m_Recorder,
                Sampler = m_Sampler, Mixer = m_Mixer,
                DevDiagnostics = platform.GetLaunchArgument("devhud") == "1",
                IsGyroMode = () => m_SteerMode == SteerMode.Gyro,
                ToggleSteeringMode = () => SetSteerMode((SteerMode)(((int)m_SteerMode + 1) % 3)),
                OpenSettings = OpenControlSettings,
                ResetVehicle = () => Spawn(m_Spawn),
                OpenMenu = ReturnToMenu,
                StatusLine = () => Time.unscaledTime < m_StatusUntil ? m_Status : (Autopilot.Enabled || RouteDriver.Enabled ? "AUTOPILOT (pomiar)" : ""),
                Spawn = i => Spawn((LabSpawn)i, persist: true),
                CurrentSpawn = () => (int)m_Spawn,
                ToggleAbsFault = () => SetAbsFault(!m_AbsFault),
                AbsFault = () => m_AbsFault,
                RetarderLever = () => m_Lever,
                RetarderLeverMax = m_LeverMax,
                BrakeCruiseKmh = () => m_CruiseKmh,
                CouplingStatus = CouplingStatus,
                TurnSignalLever = () => Signals.Lever,
                TurnSignalLit = () => Signals.Lit,
                ReverseCameraTexture = () => m_ActiveRevCam != null ? m_ActiveRevCam.Texture : null,
                ReverseCameraLabel = () => m_ActiveRevCam == m_TrailerCam ? "KAMERA COFANIA (naczepa)" : "KAMERA SIODŁA (za kabiną)",
                // Mirror strategy (visual review #14): in the cab view the main mirrors are shown as insets by default
                // (usable at any head angle); look-around still shows the real glass. Toggle in the lab menu.
                LeftMirrorTexture = () => MirrorInsetsOn && m_MirrorL != null ? m_MirrorL.Texture : null,
                RightMirrorTexture = () => MirrorInsetsOn && m_MirrorR != null ? m_MirrorR.Texture : null,
                MirrorInsets = () => m_MirrorInsets,
                ToggleMirrorInsets = () => { m_MirrorInsets = !m_MirrorInsets; PlayerPrefs.SetInt(PrefMirrorInsets, m_MirrorInsets ? 1 : 0); },
            }, overlay: true);
            m_Hud.transform.SetParent(transform, false);

            string ap = platform.GetLaunchArgument("autopilot");
            string tr = platform.GetLaunchArgument("trailer");
            // World route runs default to the 40 t combination (a solo run would leave the trailer parked at the spawn);
            // trailer=solo still gives a solo tractor. Lab circle runs stay solo (Stage 1 measurement).
            var apDefault = ap == "route" ? LabSpawn.Gross40t : LabSpawn.Solo;
            m_Spawn = ParseSpawn(tr, !string.IsNullOrEmpty(ap) ? apDefault : StoredOrDefaultSpawn(PlayerPrefs.HasKey(PrefSpawn), PlayerPrefs.GetInt(PrefSpawn, (int)DefaultSpawn)));
            // World scenes (spawn point): a Solo preference saved in the lab would leave the trailer parked behind the tractor
            // (device run 2026-11-09), so without an explicit trailer= argument the world start is always a coupled combination.
            if (spawnPoint != null && string.IsNullOrEmpty(tr) && m_Spawn == LabSpawn.Solo) m_Spawn = LabSpawn.Empty;
            if (trailer == null) m_Spawn = LabSpawn.Solo;
            m_IgnoreRoots = new[] { vehicle.transform, trailer != null ? trailer.transform : null };
            ReadRouteArguments(platform);
            m_StartTime = Time.time;
            if (ap == "route") { if (!StartRouteDriver(platform.GetLaunchArgument("speed"))) ap = null; }
            else if (!string.IsNullOrEmpty(ap)) { ConfigureAutopilot(ap, platform.GetLaunchArgument("speed")); m_AutopilotStart = true; }
            Spawn(m_Spawn);
            // World scenes: edge-of-region warning and recovery when the vehicle leaves the world (ADR 0082).
            var regionRoot = FindAnyObjectByType<Game.World.WorldRegionRoot>();
            if (regionRoot != null)
            {
                SafetyNet = gameObject.AddComponent<WorldSafetyNet>();
                SafetyNet.bootstrap = this;
                SafetyNet.vehicle = vehicle;
                SafetyNet.region = regionRoot;
            }
            // lighting=<preset> (clear | overcast | lowsun | dusk): device frames of the control set under the same light (A7).
            string menuLighting = StartRequest.ConsumeLighting();   // start menu choice; a launch argument wins
            string lighting = platform.GetLaunchArgument("lighting");
            if (string.IsNullOrEmpty(lighting)) lighting = menuLighting;
            if (!string.IsNullOrEmpty(lighting))
            {
                Debug.Log($"[CONTROLS] session lighting={lighting} tier={QualityTiers.Current} fps={Application.targetFrameRate}");
                var env = FindAnyObjectByType<EnvironmentLighting>();
                if (env == null || !env.SetPreset(lighting)) Debug.LogWarning($"[LAB] lighting={lighting}: no such preset");
            }
            ActivateControlCamera(platform.GetLaunchArgument("qacam"), platform.GetLaunchArgument("qacam_set"));
            // telemetry=1: record the vehicle CSV from the first physics step (device runs, e.g. the route jolt check).
            m_AutoRecord = platform.GetLaunchArgument("telemetry") == "1";
            m_Recorder.RouteProgress = () => RouteDriver.Enabled ? RouteDriver.Progress : 0f;
            Debug.Log($"[LAB] DrivingLab ready: vehicle={vehicle.name} trailer={(trailer != null ? trailer.name : "none")} spawn={m_Spawn} steer={m_SteerMode} autopilot={(Autopilot.Enabled || RouteDriver.Enabled ? ap : "off")} fixedDt={Time.fixedDeltaTime}");
        }

        /// <summary>
        /// Device visual QA (launch argument qacam=&lt;control camera id&gt;): renders the scene from that ControlCamera
        /// with the tier's camera settings, HUD hidden - native-resolution phone frames of the editor control set
        /// (scripts/device-metrics.ps1 -QaCamera).
        /// </summary>
        void ActivateControlCamera(string id, string set = null)
        {
            if (string.IsNullOrEmpty(id)) return;
            // qacam_set=gate3: cameras of Data/Regions/<region>/gate3_cameras.json, re-seated on the road collision.
            if (set == "gate3") Gate3Cameras.CreateAll(FindAnyObjectByType<Game.World.WorldRegionRoot>(), m_IgnoreRoots);
            string want = Gate3Cameras.Norm(id);
            foreach (var qa in FindObjectsByType<Game.Rendering.ControlCamera>(FindObjectsInactive.Include, FindObjectsSortMode.None))
            {
                if (qa.id != id && Gate3Cameras.Norm(qa.id) != want) continue;
                var cam = qa.GetComponent<Camera>();
                qa.gameObject.SetActive(true);
                cam.enabled = true;
                cam.depth = (mainCamera != null ? mainCamera.depth : 0f) + 10f;
                var applier = FindAnyObjectByType<Game.Rendering.QualityProfileApplier>();
                if (applier != null) { applier.targetCamera = cam; applier.ApplyNow(); }
                if (mainCamera != null) mainCamera.enabled = false;
                if (m_Hud != null) m_Hud.gameObject.SetActive(false);
                var qp = qa.transform.position;
                Debug.Log($"[LAB] control camera {id} active ({cam.pixelWidth}x{cam.pixelHeight}) pos=({qp.x:F1},{qp.y:F1},{qp.z:F1}) fwd=({qa.transform.forward.x:F2},{qa.transform.forward.y:F2},{qa.transform.forward.z:F2})");
                return;
            }
            Debug.LogWarning($"[LAB] qacam={id}: no such ControlCamera in the scene");
        }

        static LabSpawn ParseSpawn(string arg, LabSpawn fallback)
        {
            switch ((arg ?? "").Trim().ToLowerInvariant())
            {
                case "solo": return LabSpawn.Solo;
                case "empty": case "pusta": return LabSpawn.Empty;
                case "24": case "24t": return LabSpawn.Cargo24t;
                case "40": case "40t": return LabSpawn.Gross40t;
                default: return fallback;
            }
        }

        /// <summary>HUD "Ster." button: cycles wheel 270 / wheel 900 / gyro and keeps the other tuning of the settings menu.</summary>
        public void SetSteerMode(SteerMode mode)
        {
            Controls.gyroEnabled = mode == SteerMode.Gyro;
            if (mode != SteerMode.Gyro) Controls.wheelRangeDeg = mode == SteerMode.Wheel900 ? 900f : 270f;
            Controls.Save();
            Controls.Log("steer-mode");
            ApplyControls();
        }

        /// <summary>Pushes <see cref="Controls"/> into the input sources (live, also from the settings menu).</summary>
        public void ApplyControls()
        {
            bool wasGyro = Gyro.Enabled;
            Controls.ApplyTo(Wheel, Gyro, Touch, Column);
            m_SteerMode = Controls.gyroEnabled ? SteerMode.Gyro : (Controls.wheelRangeDeg >= 600f ? SteerMode.Wheel900 : SteerMode.Wheel270);
            if (Gyro.Enabled && !wasGyro) Gyro.Calibrate();
            if (!Controls.gyroEnabled) Gyro.Suspend();
            if (m_Rig != null)
            {
                m_Rig.lookDegPerPixel = ControlSettings.BaseLookDegPerPixel * Controls.lookSensitivity;
                m_Rig.cabFov = Controls.cabFov;
                m_Rig.headGain = Controls.headMotion ? ControlSettings.BaseHeadGain : 0f;
            }
            m_Hud?.RefreshNow();
        }

        /// <summary>HUD "Menu" and the Android back key: back to the start menu (Boot scene) without restarting the app.</summary>
        public void ReturnToMenu()
        {
            m_InputLog.Event(Time.unscaledTime, "menu-return");
            m_InputLog.Flush(Time.unscaledTime);
            SceneManager.LoadScene("Boot");
        }

        void OpenControlSettings()
        {
            if (m_SettingsPanel != null) return;
            m_SettingsPanel = ControlSettingsPanel.Create(null, Controls, ApplyControls, null, Gyro.Calibrate);
            m_SettingsPanel.transform.SetParent(transform, false);
        }

        /// <summary>Scripted circle drive (device measurements, tests): solo tractor on the circle, trailer parked in its bay.</summary>
        public void StartAutopilot(string mode, string speedArg)
        {
            ConfigureAutopilot(mode, speedArg);
            m_AutopilotStart = true;
            Spawn(LabSpawn.Solo);
        }

        /// <summary>World scenes: drive the scene's <see cref="route"/> with the path follower (measurements, route test).</summary>
        public bool StartRouteDriver(string speedArg)
        {
            if (route == null || route.points.Length < 2) { Debug.LogWarning("[LAB] autopilot=route but the scene has no route"); return false; }
            RouteDriver.SetPath(route.WorldPoints(), route.speedLimitsKmh);
            RouteDriver.TargetSpeedKmh = float.TryParse(speedArg, NumberStyles.Float, CultureInfo.InvariantCulture, out float s) && s > 0 ? s : 50f;
            if (m_RouteEndS > 0f) RouteDriver.EndS = m_RouteEndS;
            if (m_RouteS > 0f) RouteDriver.SeekTo(m_RouteS);
            RouteDriver.Enabled = true;
            m_Parking = false;
            return true;
        }

        /// <summary>
        /// Launch arguments route_s / route_end (gate 3): spawn the combination at route distance s (heading = route tangent,
        /// trailer coupled by the normal spawn path) and let the route autopilot stop smoothly at route_end.
        /// </summary>
        void ReadRouteArguments(IPlatformServices platform)
        {
            bool menuStart = StartRequest.Consume(out float menuS, out float menuEnd);   // Boot menu choice, once
            if (route == null || route.points.Length < 2) return;
            if (menuStart && menuS >= 0f) m_RouteS = Mathf.Min(menuS, route.Length);
            if (menuStart && menuEnd > 0f) m_RouteEndS = Mathf.Min(menuEnd, route.Length);
            var ci = CultureInfo.InvariantCulture;
            if (float.TryParse(platform.GetLaunchArgument("route_s"), NumberStyles.Float, ci, out float s) && s >= 0f) m_RouteS = Mathf.Min(s, route.Length);
            if (float.TryParse(platform.GetLaunchArgument("route_end"), NumberStyles.Float, ci, out float e) && e > 0f) m_RouteEndS = Mathf.Min(e, route.Length);
        }

        /// <summary>Respawns the current preset at route distance s (same as launch argument route_s; also used by tests).</summary>
        public void SetRouteSpawn(float s)
        {
            if (route == null || route.points.Length < 2) return;
            m_RouteS = Mathf.Clamp(s, 0f, route.Length);
            Spawn(m_Spawn);
        }

        /// <summary>Spawn pose at route distance s: ground height from the road collision when present (else the route's own y).</summary>
        public static void RouteSpawnPose(Game.World.WorldRoute route, float s, IList<Transform> ignore, out Vector3 pos, out Quaternion rot)
        {
            pos = route.PointAt(s);
            if (Gate3Cameras.TryGroundY(pos.x, pos.z, pos.y + 3f, ignore, out float gy)) pos.y = gy;
            rot = Quaternion.LookRotation(route.TangentAt(s), Vector3.up);
        }

        void ConfigureAutopilot(string mode, string speedArg)
        {
            bool r25 = mode == "circle25";
            Autopilot.CircleCenter = r25 ? DrivingLabLayout.CircleR25Center : DrivingLabLayout.CircleR50Center;
            Autopilot.Radius = r25 ? DrivingLabLayout.CircleR25 : DrivingLabLayout.CircleR50;
            Autopilot.Clockwise = false;
            Autopilot.TargetSpeedKmh = float.TryParse(speedArg, NumberStyles.Float, CultureInfo.InvariantCulture, out float s) && s > 0 ? s : (r25 ? 25f : 40f);
            Autopilot.Enabled = true;
        }

        /// <summary>
        /// (Re)spawns the tractor and the trailer for a preset. Coupled presets stand at the lane start with the
        /// trailer in the jaw at static equilibrium; Solo puts the tractor in the coupling bay, aligned 2 m ahead of
        /// the parked (empty) trailer's kingpin, ready to reverse under it. Everything starts parked.
        /// </summary>
        public void Spawn(LabSpawn spawn, bool persist = false)
        {
            m_Spawn = spawn;
            if (persist) PlayerPrefs.SetInt(PrefSpawn, (int)spawn);
            bool coupled = spawn != LabSpawn.Solo && trailer != null;
            if (route != null && m_RouteS >= 0f && !m_AutopilotStart)
            {
                RouteSpawnPose(route, m_RouteS, m_IgnoreRoots, out Vector3 rp, out Quaternion rr);
                SpawnAt(spawn, rp, rr);
                return;
            }
            if (spawnPoint != null && !m_AutopilotStart)
            {
                SpawnAt(spawn, spawnPoint.position, Quaternion.LookRotation(Vector3.ProjectOnPlane(spawnPoint.forward, Vector3.up), Vector3.up));
                return;
            }
            Vector3 pos;
            if (m_AutopilotStart) pos = Autopilot.CircleCenter + new Vector3(Autopilot.Radius, 0f, 0f);
            else if (coupled) pos = DrivingLabLayout.Spawn;
            else
            {
                float jaw = (float)vehicle.Model.Def.fifthWheel.position.z;
                pos = DrivingLabLayout.CouplingKingpin + new Vector3(0f, 0f, DrivingLabLayout.CouplingGap - jaw);
            }
            // Autopilot (device runs): solo on the circle, the trailer stays parked in its bay, off the circle.
            SpawnAt(spawn, pos, Quaternion.identity, m_AutopilotStart ? DrivingLabLayout.CouplingKingpin : (Vector3?)null);
        }

        /// <summary>
        /// Spawns a preset at a ground point and heading (flat ground). Coupled presets: trailer in the jaw behind the
        /// tractor. Solo: the trailer is parked on its legs with the kingpin <see cref="DrivingLabLayout.CouplingGap"/>
        /// behind the jaw, aligned (ready to reverse under).
        /// </summary>
        public void SpawnAt(LabSpawn spawn, Vector3 pos, Quaternion north, Vector3? parkedKingpin = null)
        {
            m_Spawn = spawn;
            bool coupled = spawn != LabSpawn.Solo && trailer != null;
            vehicle.ResetPose(pos, north);
            if (trailer != null)
            {
                var preset = spawn == LabSpawn.Cargo24t ? CargoPreset.Cargo24t : spawn == LabSpawn.Gross40t ? CargoPreset.Gross40t : CargoPreset.Empty;
                // A respawn is a full reset of the trailer state (legs, brakes, wheels); a pure load change while the
                // trailer stays connected uses TrailerBody.SetCargo (R7, in place).
                trailer.Initialize(vehicle.Data, preset, vehicle.Model.MassProps.Mass);
                vehicle.ConnectTrailer(trailer, coupled);
                CombinationPlacement.Tractor(vehicle.Model, pos, north, out Vector3 vp, out Quaternion vq);
                vehicle.SetPose(vp, vq);
                Vector3 tp; Quaternion tq;
                if (coupled) CombinationPlacement.Coupled(vehicle.Model, vp, vq, trailer.Model, 0f, out tp, out tq);
                else
                {
                    Vector3 kp = parkedKingpin ?? pos + north * new Vector3(0f, 0f, (float)vehicle.Model.Def.fifthWheel.position.z - DrivingLabLayout.CouplingGap);
                    CombinationPlacement.Parked(trailer.Model, kp, north, out tp, out tq);
                }
                trailer.SetPose(tp, tq);
            }
            Physics.SyncTransforms();
            m_CouplingEvents = 0;
            m_Lever = 0; m_CruiseKmh = 0f;
            Signals.Cancel();
            m_Parking = !Autopilot.Enabled && !RouteDriver.Enabled;
            m_Selector = GearSelector.Drive;
            m_Manual = false;
            Wheel.SetWheelDeg(0f);
            Column.SnapTo(0f);
            m_SteerTarget = 0f;
            SetAbsFault(m_AbsFault, silent: true);
            m_Rig.SetCombination(coupled);
            if (m_Audio != null) m_Audio.ResetEvents();
            Flash(!coupled ? "Solo: cofnij pod naczepę (R), Siodło = uzbrój szczęki" :
                "Zestaw: " + CargoPresets.DisplayNamePl(trailer.Preset) + ", " + (vehicle.Model.TotalMass / 1000).ToString("F1", CultureInfo.InvariantCulture) + " t");
        }

        /// <summary>EBS/ABS fault simulation for the jackknife demo: no ABS and no load sensing on tractor and trailer.</summary>
        public void SetAbsFault(bool fault, bool silent = false)
        {
            m_AbsFault = fault;
            var m = vehicle.Model;
            m.Air.AbsEnabled = !fault && m.Def.brakes.absEnabled;
            m.Air.LoadSensingEnabled = !fault;
            if (vehicle.Trailer != null)
            {
                var b = vehicle.Trailer.Model.Brakes;
                b.AbsEnabled = !fault && vehicle.Trailer.Model.Def.brakes.absEnabled;
                b.LoadSensingEnabled = !fault;
            }
            if (!silent) Flash(fault ? "USTERKA EBS: ABS i korektor siły hamowania wyłączone" : "ABS / EBS sprawne");
        }

        void Flash(string s) { m_Status = s; m_StatusUntil = Time.unscaledTime + 3f; }

        /// <summary>World-edge safety net of world scenes (null in the lab).</summary>
        public WorldSafetyNet SafetyNet { get; private set; }

        /// <summary>HUD status line for <paramref name="seconds"/> (safety net, other systems).</summary>
        public void ShowStatus(string s, float seconds = 3f) { m_Status = s; m_StatusUntil = Time.unscaledTime + seconds; }
        public string StatusText => Time.unscaledTime < m_StatusUntil ? m_Status : "";

        /// <summary>
        /// Recovery after the vehicle left the world (ADR 0082): the current preset, parked, on a ground point and heading.
        /// The cab camera look and head state are re-centred; autopilots keep running from the new pose.
        /// </summary>
        public void RecoverTo(Vector3 groundPos, Quaternion heading, string message)
        {
            SpawnAt(m_Spawn, groundPos, heading);
            m_Rig.ResetView();
            Touch.ThrottleRaw = 0f;
            Touch.BrakeRaw = 0f;
            ShowStatus(message, 6f);
            m_InputLog.Event(Time.unscaledTime, "safety-reset");
        }

        /// <summary>Recovery when no safe pose is known yet: the scene spawn (route start or spawn point).</summary>
        public void RecoverToSpawn(string message)
        {
            Spawn(m_Spawn);
            m_Rig.ResetView();
            ShowStatus(message, 6f);
            m_InputLog.Event(Time.unscaledTime, "safety-reset");
        }

        bool m_AutoRecord;

        /// <summary>Half lock-to-lock of the cab wheel [deg] = road-wheel lock x overall ratio (vehicle data).</summary>
        float HandwheelLockDeg()
        {
            var st = vehicle.Model.Steering;
            return (float)(st.MaxAngle * MathUtil.Rad2Deg * st.Def.steeringRatio);
        }

        /// <summary>
        /// Fixed step, before <see cref="VehicleBody"/> (execution order -200): steps the cab wheel toward the driver's
        /// target and writes its angle / lock as the steering command. Autopilots bypass the hand model (their own
        /// controllers are tuned on the raw command) and the column is kept at their angle for a seamless hand-over.
        /// </summary>
        void FixedUpdate()
        {
            if (!vehicle.Initialized || UnityEngine.Physics.simulationMode != SimulationMode.FixedUpdate) return;   // scripted stepping (tests) drives Input itself
            var m = vehicle.Model;
            Column.LockDeg = HandwheelLockDeg();
            if (m_SteerBypass) { if (m_SteerHasTarget) Column.SnapTo(m_SteerTarget * Column.LockDeg); }
            else Column.Step(Time.fixedDeltaTime, m_SteerTarget * Column.LockDeg, m_SteerHandsOn, (float)m.SpeedForward * 3.6f, (float)m.AligningTorqueTotal);
            var input = vehicle.Input;
            input.Steer = Column.Normalized;
            vehicle.Input = input;
            Wheel.FollowColumn(Column.Normalized);
        }

        void Update()
        {
            if (!vehicle.Initialized) return;
            if (m_AutoRecord) { m_AutoRecord = false; m_Recorder.StartRecording(); }
            if (!m_RouteDoneLogged && RouteDriver.Enabled && RouteDriver.Finished)
            {
                m_RouteDoneLogged = true;
                Debug.Log($"[GATE3] segment done t={(Time.time - m_StartTime).ToString("F1", CultureInfo.InvariantCulture)} s s={RouteDriver.Progress.ToString("F1", CultureInfo.InvariantCulture)}");
            }
            var m = vehicle.Model;
            var fb = new VehicleFeedback
            {
                ForwardSpeed = (float)m.SpeedForward,
                AligningTorque = (float)m.AligningTorqueTotal,
                RoadWheelAngleNormalized = (float)(m.Steering.Angle / m.Steering.MaxAngle),
                HandwheelLockDeg = Column.LockDeg,
                Position = vehicle.transform.position,
                Forward = vehicle.transform.forward,
            };
            var intent = m_Mixer.Sample(Time.deltaTime, fb);
            m_SteerBypass = Autopilot.Enabled || RouteDriver.Enabled;
            m_SteerHasTarget = intent.SteerActive;
            m_SteerTarget = intent.SteerActive ? Mathf.Clamp(intent.Steer, -1f, 1f) : 0f;
            m_SteerHandsOn = intent.SteerActive && intent.HandsOn;
            if (!m_SteerBypass) m_InputLog.Observe(Time.unscaledTime, intent, vehicle.SpeedKmh, Column.AngleDeg);
            if (m_Rig.mode != m_LoggedCamMode) { m_LoggedCamMode = m_Rig.mode; m_InputLog.Event(Time.unscaledTime, k_CamModeEvents[(int)m_LoggedCamMode]); }
            m_InputLog.TryFlush(Time.unscaledTime, intent.Throttle < 0.01f && intent.Brake < 0.01f && !intent.SteerActive);   // batched; allocates only on that frame
            var kb = UnityEngine.InputSystem.Keyboard.current;   // Android back key arrives as Escape
            if (kb != null && kb.escapeKey.wasPressedThisFrame)
            {
                if (m_SettingsPanel != null) m_SettingsPanel.Close(); else ReturnToMenu();
            }
            ApplyCommands(intent);
            UpdateTurnSignals(intent, fb.RoadWheelAngleNormalized);

            var input = vehicle.Input;
            input.Throttle = intent.Throttle;
            input.Brake = intent.Brake;
            // input.Steer is written by the steering column in FixedUpdate (ADR 0058).
            input.Selector = m_Selector;
            input.ParkingBrake = m_Parking;
            input.ManualMode = m_Manual;
            input.RetarderLever = m_Lever;
            input.BrakeCruiseKmh = m_CruiseKmh;
            if (intent.ShiftDelta > 0) input.ShiftUp = true;
            if (intent.ShiftDelta < 0) input.ShiftDown = true;
            vehicle.Input = input;

            // Coupling happened inside the solver (jaw locked while armed).
            var fw = vehicle.Combination.FifthWheel;
            if (fw.CouplingEvents != m_CouplingEvents)
            {
                if (fw.CouplingEvents > m_CouplingEvents) { Flash("Sprzężono. Podnieś nogi (Nogi ↑↓), zwolnij P"); m_Rig.SetCombination(true); }
                m_CouplingEvents = fw.CouplingEvents;
            }

            // Extra cameras: mirrors only in the cab view; reversing view while in R (or forced on).
            RenderTextureMirror.GlobalEnabled = m_Rig.mode == CameraMode.Cab;
            RenderTextureMirror.ForceRender = MirrorInsetsOn;
            bool rev = m_Selector == GearSelector.Reverse || m_ReverseCamForced;
            var want = !rev ? null : (vehicle.Coupled && m_TrailerCam != null ? m_TrailerCam : m_TractorCam);
            if (m_ActiveRevCam != want)
            {
                if (m_ActiveRevCam != null) m_ActiveRevCam.Active = false;
                m_ActiveRevCam = want;
                if (want != null) want.Active = true;
            }
        }

        void UpdateTurnSignals(in DriverIntent intent, float roadWheelNorm)
        {
            if (intent.TurnSignal != TurnSignalRequest.None)
            {
                Signals.Request(intent.TurnSignal);
                Flash(Signals.Lever == 0 ? "Kierunkowskaz: wył." : Signals.Lever == 2 ? "Światła awaryjne" : Signals.Lever < 0 ? "Kierunkowskaz: lewy" : "Kierunkowskaz: prawy");
            }
            int edge = Signals.Step(Time.deltaTime, roadWheelNorm);
            if (m_Audio != null) m_Audio.OnFlasherEdge(edge);
            if (m_Lights == null) m_Lights = vehicle.GetComponent<TruckLights>();
            if (m_Lights != null) { m_Lights.indicatorLever = Signals.Lever; m_Lights.flasherLit = Signals.Lit; }
        }

        void ApplyCommands(in DriverIntent intent)
        {
            switch (intent.Selector)
            {
                case SelectorRequest.Drive: m_Selector = GearSelector.Drive; break;
                case SelectorRequest.Neutral: m_Selector = GearSelector.Neutral; break;
                case SelectorRequest.Reverse: m_Selector = GearSelector.Reverse; break;
            }
            if (intent.ToggleParkingBrake) { m_Parking = !m_Parking; Flash(m_Parking ? "Hamulec postojowy: ZACIĄGNIĘTY" : "Hamulec postojowy: zwolniony"); }
            if (intent.ToggleManual && m_Selector == GearSelector.Drive) { m_Manual = !m_Manual; Flash(m_Manual ? "Skrzynia: tryb ręczny (−/+)" : "Skrzynia: automat"); }
            if (intent.ShiftDelta != 0 && m_Selector == GearSelector.Drive && !m_Manual) { m_Manual = true; Flash("Skrzynia: tryb ręczny (−/+)"); }
            if (intent.Selector == SelectorRequest.Drive && intent.ShiftDelta == 0 && !intent.ToggleManual) m_Manual = false;

            if (intent.RetarderDelta != 0)
            {
                m_Lever = Mathf.Clamp(m_Lever + intent.RetarderDelta, 0, m_LeverMax);
                Flash(m_Lever == 0 ? "Hamulce zwalniające: wył." : m_Lever == 1 ? "Hamulec silnikowy" : "Retarder stopień " + (m_Lever - 1).ToString(CultureInfo.InvariantCulture) + " + hamulec silnikowy");
            }
            if (intent.ToggleBrakeCruise)
            {
                float v = Mathf.Abs(vehicle.SpeedKmh);
                if (m_CruiseKmh > 0f) { m_CruiseKmh = 0f; Flash("Stała prędkość zjazdu: wył."); }
                else if (v >= 10f) { m_CruiseKmh = Mathf.Round(v); Flash("Stała prędkość zjazdu: " + m_CruiseKmh.ToString("F0", CultureInfo.InvariantCulture) + " km/h (retarder + hamulec silnikowy)"); }
                else Flash("Stała prędkość zjazdu: jedź co najmniej 10 km/h");
            }
            if (intent.ToggleReverseCamera) { m_ReverseCamForced = !m_ReverseCamForced; Flash(m_ReverseCamForced ? "Kamera cofania: zawsze" : "Kamera cofania: przy biegu R"); }
            if (intent.ToggleCoupling) ToggleCoupling();
            if (intent.ToggleLandingGear) ToggleLandingGear();
        }

        void ToggleCoupling()
        {
            var c = vehicle.Combination;
            if (vehicle.Trailer == null) { Flash("Brak naczepy (Zestaw…)"); return; }
            if (c.Coupled)
            {
                if (c.Uncouple()) { Flash("Siodło otwarte, naczepa odpięta (hamulec naczepy zaciągnięty)"); m_Rig.SetCombination(false); }
                else Flash("Najpierw opuść nogi podporowe do ziemi (Nogi ↑↓)");
                return;
            }
            c.CouplingArmed = !c.CouplingArmed;
            Flash(c.CouplingArmed ? "Szczęki siodła gotowe: cofaj powoli pod naczepę" : "Szczęki siodła: nieaktywne");
        }

        void ToggleLandingGear()
        {
            if (vehicle.Trailer == null) return;
            var t = vehicle.Trailer.Model;
            t.LandingGearDown = !t.LandingGearDown;
            Flash(t.LandingGearDown ? "Nogi podporowe: opuszczanie" : "Nogi podporowe: podnoszenie");
        }

        bool MirrorInsetsOn => m_MirrorInsets && m_Rig != null && m_Rig.mode == CameraMode.Cab;

        string CouplingStatus()
        {
            if (vehicle.Trailer == null || !vehicle.Initialized) return "";
            var ci = CultureInfo.InvariantCulture;
            var t = vehicle.Trailer.Model;
            var lg = t.Def.landingGear;
            float legs = Mathf.Clamp01((float)((t.LandingGearFootY - lg.raisedFootY) / (lg.loweredFootY - lg.raisedFootY)));
            string legsTxt = legs >= 0.99f ? "opuszczone" : legs <= 0.01f ? "podniesione" : (legs * 100f).ToString("F0", ci) + " %";
            var c = vehicle.Combination;
            if (c.Coupled)
                return "Naczepa sprzężona · przegub " + (c.FifthWheel.Articulation * MathUtil.Rad2Deg).ToString("+0;-0", ci) + "° · nogi " + legsTxt;
            // Kingpin relative to the jaw in the tractor frame (x right, z forward).
            Vector3 jaw = vehicle.transform.TransformPoint(vehicle.Model.Def.fifthWheel.position.ToUnity());
            Vector3 kp = vehicle.Trailer.transform.TransformPoint(t.KingpinLocal.ToUnity());
            Vector3 d = vehicle.transform.InverseTransformDirection(kp - jaw);
            // While the jaw is armed the core reports the kingpin offset it actually guides on (R5 throat).
            var oj = c.FifthWheel.OpenJawOffset;
            if (c.CouplingArmed && (oj.x != 0 || oj.y != 0 || oj.z != 0)) d = oj.ToUnity();
            string side = Mathf.Abs(d.x) < 0.005f ? "na osi" : (Mathf.Abs(d.x) * 100f).ToString("F0", ci) + " cm " + (d.x > 0 ? "w prawo" : "w lewo");
            string dist = d.z < 0 ? (-d.z).ToString("F2", ci) + " m za siodłem" : d.z.ToString("F2", ci) + " m przed siodłem";
            return "Naczepa odpięta (nogi " + legsTxt + ") · sworzeń " + dist + ", " + side + ", wys. " + (d.y * 100f).ToString("+0;-0", ci) + " cm · szczęki " + (c.CouplingArmed ? "GOTOWE" : "nieaktywne");
        }

        void OnApplicationPause(bool paused)
        {
            if (!paused) return;
            m_InputLog?.Flush(Time.unscaledTime);
            Gyro.Suspend();
            Touch.ThrottleRaw = 0f;
            Touch.BrakeRaw = 0f;
            Wheel.PointerUp();
        }

        void OnDestroy() { m_InputLog?.Flush(Time.unscaledTime); }

        void OnApplicationFocus(bool focus) { if (!focus) OnApplicationPause(true); }
    }
}
