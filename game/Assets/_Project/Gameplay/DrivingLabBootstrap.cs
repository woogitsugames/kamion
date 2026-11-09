using System.Globalization;
using Game.Cameras;
using Game.Controls;
using Game.Platform;
using Game.Rendering;
using Game.Telemetry;
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
    /// state (selector, manual mode, parking brake), the camera rig, HUD, telemetry recorder and diagnostics.
    /// Launch arguments: <c>autopilot</c> (circle50 | circle25) and <c>speed</c> (km/h) for scripted device runs.
    /// </summary>
    [DefaultExecutionOrder(-200)]
    public sealed class DrivingLabBootstrap : MonoBehaviour
    {
        public enum SteerMode { Wheel270 = 0, Wheel900 = 1, Gyro = 2 }
        const string PrefSteerMode = "controls.steerMode";

        public VehicleBody vehicle;
        public Camera mainCamera;

        readonly DriverInputMixer m_Mixer = new DriverInputMixer();
        public readonly AutopilotDriverInput Autopilot = new AutopilotDriverInput();
        public readonly KeyboardDriverInput Keyboard = new KeyboardDriverInput();
        public readonly TouchSteeringWheel Wheel = new TouchSteeringWheel();
        public readonly GyroSteering Gyro = new GyroSteering();
        public readonly TouchControls Touch = new TouchControls();

        CameraRig m_Rig;
        DrivingHud m_Hud;
        VehicleTelemetryRecorder m_Recorder;
        DiagnosticsSampler m_Sampler;
        SteerMode m_SteerMode;
        Vector3 m_SpawnPos;
        Quaternion m_SpawnRot;
        GearSelector m_Selector = GearSelector.Drive;
        bool m_Manual, m_Parking = true;
        string m_Status = "";
        float m_StatusUntil;

        public SteerMode CurrentSteerMode => m_SteerMode;
        public DriverInputMixer Mixer => m_Mixer;

        void Awake()
        {
            Time.fixedDeltaTime = 0.01f;     // 100 Hz (also in ProjectSettings/TimeManager.asset)
            Time.maximumDeltaTime = 0.1f;    // at most 10 physics steps per rendered frame
            if (Application.targetFrameRate <= 0) QualityTiers.SetTargetFrameRate(QualityTiers.SavedFrameRate > 0 ? QualityTiers.SavedFrameRate : 30);
            Screen.sleepTimeout = SleepTimeout.NeverSleep;

            if (vehicle == null) vehicle = FindAnyObjectByType<VehicleBody>();
            if (mainCamera == null) mainCamera = Camera.main;
            m_SpawnPos = vehicle.transform.position;
            m_SpawnRot = vehicle.transform.rotation;

            var platform = PlatformServices.Create();
            m_Sampler = FindAnyObjectByType<DiagnosticsSampler>();
            if (m_Sampler == null)
            {
                m_Sampler = gameObject.AddComponent<DiagnosticsSampler>();
                m_Sampler.Initialize(platform);
            }

            m_Mixer.Add(Autopilot);
            m_Mixer.Add(Keyboard);
            m_Mixer.Add(Wheel);
            m_Mixer.Add(Gyro);
            m_Mixer.Add(Touch);
            GyroSteering.EnableSensors();
            SetSteerMode((SteerMode)PlayerPrefs.GetInt(PrefSteerMode, 0));

            if (!vehicle.TryGetComponent(out m_Recorder)) m_Recorder = vehicle.gameObject.AddComponent<VehicleTelemetryRecorder>();
            m_Recorder.body = vehicle;

            if (!mainCamera.TryGetComponent(out m_Rig)) m_Rig = mainCamera.gameObject.AddComponent<CameraRig>();
            m_Rig.cam = mainCamera;
            m_Rig.target = vehicle.transform;
            m_Rig.targetBody = vehicle.GetComponent<Rigidbody>();
            var visuals = vehicle.GetComponent<VehicleVisuals>();
            m_Rig.eyeAnchor = visuals != null && visuals.cabPivot != null ? visuals.cabPivot.Find("DriverEyePoint") : null;

            m_Hud = DrivingHud.Create(mainCamera, new DrivingHudContext
            {
                Vehicle = vehicle, Wheel = Wheel, Touch = Touch, Gyro = Gyro, Rig = m_Rig, Recorder = m_Recorder,
                Sampler = m_Sampler, Mixer = m_Mixer,
                IsGyroMode = () => m_SteerMode == SteerMode.Gyro,
                ToggleSteeringMode = () => SetSteerMode((SteerMode)(((int)m_SteerMode + 1) % 3)),
                ResetVehicle = ResetVehicle,
                OpenMenu = () => SceneManager.LoadScene("Boot"),
                StatusLine = () => Time.unscaledTime < m_StatusUntil ? m_Status : (Autopilot.Enabled ? "AUTOPILOT (pomiar)" : ""),
            }, overlay: true);
            m_Hud.transform.SetParent(transform, false);

            string ap = platform.GetLaunchArgument("autopilot");
            if (!string.IsNullOrEmpty(ap)) StartAutopilot(ap, platform.GetLaunchArgument("speed"));
            Debug.Log($"[LAB] DrivingLab ready: vehicle={vehicle.name} steer={m_SteerMode} autopilot={(Autopilot.Enabled ? ap : "off")} fixedDt={Time.fixedDeltaTime}");
        }

        public void SetSteerMode(SteerMode mode)
        {
            m_SteerMode = mode;
            Wheel.HalfRangeDeg = mode == SteerMode.Wheel900 ? 900f : 270f;
            Wheel.Enabled = mode != SteerMode.Gyro;
            Gyro.Enabled = mode == SteerMode.Gyro;
            if (Gyro.Enabled) Gyro.Calibrate();
            PlayerPrefs.SetInt(PrefSteerMode, (int)mode);
        }

        public void StartAutopilot(string mode, string speedArg)
        {
            bool r25 = mode == "circle25";
            Autopilot.CircleCenter = r25 ? DrivingLabLayout.CircleR25Center : DrivingLabLayout.CircleR50Center;
            Autopilot.Radius = r25 ? DrivingLabLayout.CircleR25 : DrivingLabLayout.CircleR50;
            Autopilot.Clockwise = false;
            Autopilot.TargetSpeedKmh = float.TryParse(speedArg, NumberStyles.Float, CultureInfo.InvariantCulture, out float s) && s > 0 ? s : (r25 ? 25f : 40f);
            Autopilot.Enabled = true;
            m_SpawnPos = Autopilot.CircleCenter + new Vector3(Autopilot.Radius, 0f, 0f);
            m_SpawnRot = Quaternion.identity;
            ResetVehicle();
            m_Parking = false;
            m_Selector = GearSelector.Drive;
            m_Manual = false;
        }

        void ResetVehicle()
        {
            vehicle.ResetPose(m_SpawnPos, m_SpawnRot);
            m_Parking = !Autopilot.Enabled;
            Wheel.SetWheelDeg(0f);
            Flash("Reset pozycji");
        }

        void Flash(string s) { m_Status = s; m_StatusUntil = Time.unscaledTime + 2.5f; }

        void Update()
        {
            if (!vehicle.Initialized) return;
            var m = vehicle.Model;
            var fb = new VehicleFeedback
            {
                ForwardSpeed = (float)m.SpeedForward,
                AligningTorque = (float)m.AligningTorqueTotal,
                RoadWheelAngleNormalized = (float)(m.Steering.Angle / m.Steering.MaxAngle),
                Position = vehicle.transform.position,
                Forward = vehicle.transform.forward,
            };
            var intent = m_Mixer.Sample(Time.deltaTime, fb);
            ApplyCommands(intent);

            var input = vehicle.Input;
            input.Throttle = intent.Throttle;
            input.Brake = intent.Brake;
            if (intent.SteerActive) input.Steer = Mathf.Clamp(intent.Steer, -1f, 1f);
            input.Selector = m_Selector;
            input.ParkingBrake = m_Parking;
            input.ManualMode = m_Manual;
            if (intent.ShiftDelta > 0) input.ShiftUp = true;
            if (intent.ShiftDelta < 0) input.ShiftDown = true;
            vehicle.Input = input;
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
        }

        void OnApplicationPause(bool paused)
        {
            if (!paused) return;
            Gyro.Suspend();
            Touch.ThrottleRaw = 0f;
            Touch.BrakeRaw = 0f;
            Wheel.PointerUp();
        }

        void OnApplicationFocus(bool focus) { if (!focus) OnApplicationPause(true); }
    }
}
