using System;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.Controls;

namespace Game.Controls
{
    /// <summary>
    /// PC steering wheel + pedals + H-shifter + paddles as a driver input (ADR 0263), read through the Unity Input
    /// System's generic HID support (devices reporting GenericDesktop/Joystick appear as <see cref="Joystick"/>; no
    /// vendor SDK). The device is matched to a data profile (<see cref="WheelProfileSet"/>) by vendor/product id or
    /// product name at connect time; controls are resolved once; per-frame reading is allocation-free.
    /// Steering is absolute (<see cref="DriverIntent.DirectSteer"/>): the calibrated device angle maps to the cab wheel
    /// through <see cref="WheelSteeringMap"/> (270-900 deg range, soft lock). Exposes the device angle/rate for the
    /// force-feedback model.
    /// </summary>
    public sealed class HidWheelDriverInput : IDriverInput, IDisposable
    {
        public string Name => "kierownica";
        public bool Enabled { get; set; } = true;

        public WheelSettings Settings;
        public WheelProfileSet Profiles;

        /// <summary>The matched device (null = none connected).</summary>
        public InputDevice Device { get; private set; }
        public WheelDeviceProfile Profile { get; private set; }
        public bool Connected => Device != null && Device.added;

        /// <summary>Physical wheel angle [deg], positive = clockwise; rate [deg/s] (for force feedback).</summary>
        public float DeviceDeg { get; private set; }
        public float DeviceRateDegS { get; private set; }
        /// <summary>In-game rotation range [deg] in use (lock-to-lock).</summary>
        public float RangeDeg { get; private set; }
        public float DeviceRangeDeg { get; private set; }
        public float CabLockDeg { get; private set; }
        /// <summary>Raw readings (calibration wizard, diagnostics).</summary>
        public float RawSteer { get; private set; }
        public float RawThrottle { get; private set; }
        public float RawBrake { get; private set; }
        public float RawClutch { get; private set; }

        public readonly HShifterMapper Shifter = new HShifterMapper();

        AxisControl m_Steer, m_Throttle, m_Brake, m_Clutch, m_Combined;
        AxisCalibration m_SteerCal, m_ThrottleCal, m_BrakeCal, m_ClutchCal, m_CombinedCal;
        bool m_SteerCalibrated, m_ThrottleCalibrated, m_BrakeCalibrated, m_ClutchCalibrated;
        AutoPedal m_AutoThrottle, m_AutoBrake, m_AutoClutch;
        AutoSteer m_AutoSteer;
        ButtonControl[] m_Gates = new ButtonControl[0];
        bool[] m_GateDown = new bool[0];
        ButtonControl m_Reverse, m_RangeHeld, m_PaddleUp, m_PaddleDown;
        ButtonControl[] m_ActionButtons = new ButtonControl[0];
        WheelAction[] m_Actions = new WheelAction[0];
        ButtonEdges m_Edges = new ButtonEdges(0);
        bool m_RangeHigh, m_HasPrevDeg, m_DevicesDirty = true, m_Subscribed;
        float m_PrevDeg;

        public HidWheelDriverInput(WheelSettings settings = null, WheelProfileSet profiles = null)
        {
            Settings = settings ?? WheelSettings.Defaults();
            Profiles = profiles;
        }

        public void Dispose()
        {
            if (m_Subscribed) InputSystem.onDeviceChange -= OnDeviceChange;
            m_Subscribed = false;
            Release();
        }

        void OnDeviceChange(InputDevice device, InputDeviceChange change) => m_DevicesDirty = true;

        /// <summary>Forget the device (settings changed → re-resolve on the next sample).</summary>
        public void Rebind() { Release(); m_DevicesDirty = true; }

        void Release()
        {
            Device = null; Profile = null;
            m_Steer = m_Throttle = m_Brake = m_Clutch = m_Combined = null;
            m_Reverse = m_RangeHeld = m_PaddleUp = m_PaddleDown = null;
            m_HasPrevDeg = false;
            DeviceRateDegS = 0f;
        }

        public void Sample(float dt, in VehicleFeedback fb, ref DriverIntent intent)
        {
            if (!m_Subscribed) { InputSystem.onDeviceChange += OnDeviceChange; m_Subscribed = true; }   // not in the ctor (MonoBehaviour field init)
            if (!Settings.enabled) { if (Device != null) Release(); Idle(ref intent); return; }
            if (m_DevicesDirty || (Device != null && !Device.added)) { m_DevicesDirty = false; FindDevice(); }
            if (Device == null || m_Steer == null) { Idle(ref intent); return; }

            CabLockDeg = fb.HandwheelLockDeg > 0f ? fb.HandwheelLockDeg : 800f;   // 800 = SteeringFeel.fallbackLockDeg

            // Steering (absolute).
            RawSteer = m_Steer.ReadValue();
            float norm;
            if (m_SteerCalibrated) norm = WheelAxisMath.Steer(RawSteer, m_SteerCal);
            else norm = m_AutoSteer.Value(RawSteer, m_SteerCal.invert, m_SteerCal.deadZoneLow);   // first reading = centre
            DeviceDeg = WheelSteeringMap.DeviceDeg(norm, DeviceRangeDeg);
            if (m_HasPrevDeg && dt > 1e-5f) DeviceRateDegS = (DeviceDeg - m_PrevDeg) / dt;
            m_PrevDeg = DeviceDeg; m_HasPrevDeg = true;
            intent.Steer = WheelSteeringMap.Command(DeviceDeg, RangeDeg, CabLockDeg, Settings.mapping);
            intent.SteerActive = true;
            intent.HandsOn = true;
            intent.DirectSteer = true;

            // Pedals.
            if (Profile.combinedPedals && m_Combined != null)
            {
                WheelAxisMath.SplitCombined(m_Combined.ReadValue(), m_CombinedCal, out float t, out float b);
                intent.Throttle = t; intent.Brake = b;
            }
            else
            {
                intent.Throttle = Pedal(m_Throttle, m_ThrottleCal, m_ThrottleCalibrated, ref m_AutoThrottle, out float rt); RawThrottle = rt;
                intent.Brake = Pedal(m_Brake, m_BrakeCal, m_BrakeCalibrated, ref m_AutoBrake, out float rb); RawBrake = rb;
            }
            intent.Clutch = Pedal(m_Clutch, m_ClutchCal, m_ClutchCalibrated, ref m_AutoClutch, out float rc); RawClutch = rc;

            // Paddles (edge 0, 1), mapped buttons (2..).
            if (m_Edges.Pressed(0, IsDown(m_PaddleUp))) intent.ShiftDelta += 1;
            if (m_Edges.Pressed(1, IsDown(m_PaddleDown))) intent.ShiftDelta -= 1;
            for (int i = 0; i < m_ActionButtons.Length; i++)
                if (m_Edges.Pressed(2 + i, IsDown(m_ActionButtons[i]))) Apply(m_Actions[i], ref intent);

            // H-shifter.
            if (m_Gates.Length > 0 || m_Reverse != null)
            {
                for (int i = 0; i < m_Gates.Length; i++) m_GateDown[i] = IsDown(m_Gates[i]);
                bool high = m_RangeHeld != null ? m_RangeHeld.isPressed : m_RangeHigh;
                Shifter.Update(dt, HShifterMapper.Slot(m_GateDown, m_GateDown.Length, IsDown(m_Reverse)), high, ref intent);
            }
        }

        /// <summary>Soft-lock overshoot of the current device angle [deg] (force feedback wall).</summary>
        public float PastSoftLockDeg => WheelSteeringMap.PastSoftLockDeg(DeviceDeg, RangeDeg, CabLockDeg, Settings.mapping);
        public float CabPerDeviceDeg => WheelSteeringMap.CabPerDeviceDeg(RangeDeg, CabLockDeg, Settings.mapping);

        static bool IsDown(ButtonControl b) => b != null && b.isPressed;

        static float Pedal(AxisControl ctl, AxisCalibration cal, bool calibrated, ref AutoPedal auto, out float raw)
        {
            raw = 0f;
            if (ctl == null) return 0f;
            raw = ctl.ReadValue();
            return calibrated ? WheelAxisMath.Pedal(raw, cal) : auto.Value(raw, cal.deadZoneLow, cal.deadZoneHigh);
        }

        void Idle(ref DriverIntent intent)
        {
            intent.SteerActive = false; intent.DirectSteer = false;
            intent.Throttle = 0f; intent.Brake = 0f; intent.Clutch = 0f;
            DeviceRateDegS = 0f;
        }

        void Apply(WheelAction a, ref DriverIntent intent)
        {
            switch (a)
            {
                case WheelAction.ParkingBrake: intent.ToggleParkingBrake = true; break;
                case WheelAction.RetarderMore: intent.RetarderDelta += 1; break;
                case WheelAction.RetarderLess: intent.RetarderDelta -= 1; break;
                case WheelAction.SignalLeft: intent.TurnSignal = TurnSignalRequest.Left; break;
                case WheelAction.SignalRight: intent.TurnSignal = TurnSignalRequest.Right; break;
                case WheelAction.Hazard: intent.TurnSignal = TurnSignalRequest.Hazard; break;
                case WheelAction.Drive: intent.Selector = SelectorRequest.Drive; break;
                case WheelAction.Neutral: intent.Selector = SelectorRequest.Neutral; break;
                case WheelAction.Reverse: intent.Selector = SelectorRequest.Reverse; break;
                case WheelAction.ToggleManual: intent.ToggleManual = true; break;
                case WheelAction.BrakeCruise: intent.ToggleBrakeCruise = true; break;
                case WheelAction.ReverseCamera: intent.ToggleReverseCamera = true; break;
                case WheelAction.Coupling: intent.ToggleCoupling = true; break;
                case WheelAction.LandingGear: intent.ToggleLandingGear = true; break;
                case WheelAction.ShiftUp: intent.ShiftDelta += 1; break;
                case WheelAction.ShiftDown: intent.ShiftDelta -= 1; break;
                case WheelAction.RangeToggle: m_RangeHigh = !m_RangeHigh; break;
            }
        }

        // ---------- connect time (may allocate) ----------

        void FindDevice()
        {
            Release();
            if (Profiles == null) Profiles = WheelProfiles.LoadDefault();
            var devices = InputSystem.devices;
            for (int i = 0; i < devices.Count; i++)
            {
                var d = devices[i];
                if (!(d is Joystick) || !d.added) continue;
                ReadIds(d, out int vid, out int pid);
                WheelDeviceProfile p = !string.IsNullOrEmpty(Settings.profileOverride) ? Profiles.ById(Settings.profileOverride) : null;
                if (p == null) p = Profiles.Find(vid, pid, d.description.product);
                if (p == null) continue;
                if (Bind(d, p)) return;
            }
        }

        /// <summary>USB vendor/product id from the HID descriptor JSON (0 when not a HID device or unreadable).</summary>
        static void ReadIds(InputDevice d, out int vid, out int pid)
        {
            vid = pid = 0;
            var caps = d.description.capabilities;
            if (string.IsNullOrEmpty(caps)) return;
            try
            {
                var desc = UnityEngine.InputSystem.HID.HID.HIDDeviceDescriptor.FromJson(caps);
                vid = desc.vendorId; pid = desc.productId;
            }
            catch (Exception) { }
        }

        bool Bind(InputDevice d, WheelDeviceProfile p)
        {
            var steer = Axis(d, p.steer);
            if (steer == null) return false;
            Device = d; Profile = p; m_Steer = steer;
            var rec = Settings.CalibrationFor(p.id);
            DeviceRangeDeg = rec != null && rec.deviceRangeDeg > 0f ? rec.deviceRangeDeg : p.deviceRangeDeg;
            RangeDeg = WheelSteeringMap.ClampRange(Settings.rangeDeg > 0f ? Settings.rangeDeg : p.defaultRangeDeg, DeviceRangeDeg);

            m_SteerCal = Pick(p.steer, rec != null && rec.hasSteer ? rec.steer : null, out m_SteerCalibrated);
            m_Throttle = Axis(d, p.throttle); m_ThrottleCal = Pick(p.throttle, rec != null && rec.hasThrottle ? rec.throttle : null, out m_ThrottleCalibrated);
            m_Brake = Axis(d, p.brake); m_BrakeCal = Pick(p.brake, rec != null && rec.hasBrake ? rec.brake : null, out m_BrakeCalibrated);
            m_Clutch = Axis(d, p.clutch); m_ClutchCal = Pick(p.clutch, rec != null && rec.hasClutch ? rec.clutch : null, out m_ClutchCalibrated);
            m_Combined = p.combinedPedals ? Axis(d, p.combined) : null; m_CombinedCal = p.combined?.calibration ?? new AxisCalibration();
            m_AutoSteer = AutoSteer.Create(p.steer.expectedSpan);
            m_AutoThrottle = AutoPedal.Create(p.throttle?.expectedSpan ?? 1f);
            m_AutoBrake = AutoPedal.Create(p.brake?.expectedSpan ?? 1f);
            m_AutoClutch = AutoPedal.Create(p.clutch?.expectedSpan ?? 1f);

            int g = p.shifterGates?.Length ?? 0;
            m_Gates = new ButtonControl[g]; m_GateDown = new bool[g];
            for (int i = 0; i < g; i++) m_Gates[i] = Button(d, p.shifterGates[i]);
            m_Reverse = Button(d, p.shifterReverse);
            m_RangeHeld = Button(d, p.shifterRange);
            Shifter.GatesPerRange = Math.Max(1, g);
            Shifter.Reset();
            m_PaddleUp = Button(d, p.paddleUp);
            m_PaddleDown = Button(d, p.paddleDown);
            int nb = p.buttons?.Length ?? 0;
            m_ActionButtons = new ButtonControl[nb]; m_Actions = new WheelAction[nb];
            for (int i = 0; i < nb; i++) { m_ActionButtons[i] = Button(d, p.buttons[i]?.control); m_Actions[i] = p.buttons[i]?.Parse() ?? WheelAction.None; }
            m_Edges = new ButtonEdges(2 + nb);
            return true;
        }

        static AxisCalibration Pick(WheelAxisBinding b, AxisCalibration stored, out bool calibrated)
        {
            if (stored != null) { calibrated = true; return stored; }
            calibrated = b != null && b.calibrated;
            return b?.calibration ?? new AxisCalibration();
        }

        static AxisControl Axis(InputDevice d, WheelAxisBinding b)
            => b == null || string.IsNullOrEmpty(b.control) ? null : d.TryGetChildControl<AxisControl>(b.control);

        static ButtonControl Button(InputDevice d, string path)
            => string.IsNullOrEmpty(path) ? null : d.TryGetChildControl<ButtonControl>(path);
    }
}
