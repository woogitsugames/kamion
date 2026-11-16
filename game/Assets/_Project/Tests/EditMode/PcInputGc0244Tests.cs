using System;
using System.Reflection;
using Game.Controls;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0244 (driving-loop GC audit), extension for the PC input paths that came after the audit (ADR 0263 / 0264 /
    /// 0265, review #131 P1-1 menu gate): the per-frame driver input of a PC session must not allocate.
    /// Covered, with REAL Input System devices (virtual gamepad, keyboard and joystick added for the test, so the device
    /// branches run, not the early "no device" return): <see cref="GamepadDriverInput"/> (stick filter, triggers, look,
    /// commands), <see cref="KeyboardBindingsDriverInput"/> (key ramp), <see cref="HidWheelDriverInput"/> through
    /// <see cref="PcWheel"/> (absolute steering, pedals, paddles, mapped buttons, H-shifter) and its force feedback step
    /// with an available sink, all inside one <see cref="DriverInputMixer"/> in the bootstrap's priority order with the menu
    /// gate opening and closing (<see cref="IMenuGatedInput.SampleBlocked"/>).
    /// <para>GC counted with <see cref="GcAllocCounter"/> (Recorder "GC.Alloc"; GC.GetAllocatedBytesForCurrentThread is 0
    /// under Mono in the editor). The test assembly does not reference Unity.InputSystem (asmdef owned by the lead), so the
    /// virtual devices are added and removed by reflection OUTSIDE the measured window; connect-time work (device match,
    /// control resolve, onDeviceChange subscription) is in the warm-up, as in the game (it may allocate once).</para>
    /// </summary>
    public class PcInputGc0244Tests
    {
        const float Dt = 1f / 60f;
        const string DevicePrefix = "KamionGc0244";

        static readonly Type s_InputSystem = Type.GetType("UnityEngine.InputSystem.InputSystem, Unity.InputSystem");
        static readonly Type s_InputDevice = Type.GetType("UnityEngine.InputSystem.InputDevice, Unity.InputSystem");

        object m_Pad, m_Kb, m_Joy;
        DrivingActions m_Actions;
        PcWheel m_Wheel;

        [TearDown]
        public void TearDown()
        {
            m_Wheel?.Dispose(); m_Wheel = null;
            m_Actions?.Dispose(); m_Actions = null;
            RemoveVirtual(ref m_Pad); RemoveVirtual(ref m_Kb); RemoveVirtual(ref m_Joy);
        }

        /// <summary>InputSystem.AddDevice(layout, name, variants) + MakeCurrent, by reflection (null when the API is missing).</summary>
        static object AddVirtual(string layout)
        {
            if (s_InputSystem == null || s_InputDevice == null) return null;
            var add = s_InputSystem.GetMethod("AddDevice", BindingFlags.Public | BindingFlags.Static, null,
                new[] { typeof(string), typeof(string), typeof(string) }, null);
            if (add == null) return null;
            object dev = add.Invoke(null, new object[] { layout, DevicePrefix + layout, null });
            dev?.GetType().GetMethod("MakeCurrent", BindingFlags.Public | BindingFlags.Instance, null, Type.EmptyTypes, null)?.Invoke(dev, null);
            return dev;
        }

        static void RemoveVirtual(ref object dev)
        {
            if (dev == null || s_InputSystem == null || s_InputDevice == null) { dev = null; return; }
            var rm = s_InputSystem.GetMethod("RemoveDevice", BindingFlags.Public | BindingFlags.Static, null, new[] { s_InputDevice }, null);
            try { rm?.Invoke(null, new[] { dev }); }
            catch (TargetInvocationException) { }   // already removed
            dev = null;
        }

        static object Current(string type) =>
            Type.GetType("UnityEngine.InputSystem." + type + ", Unity.InputSystem")?.GetProperty("current", BindingFlags.Public | BindingFlags.Static)?.GetValue(null);

        /// <summary>A wheel profile on the generic Joystick layout that exercises every per-frame branch of the HID wheel.</summary>
        static WheelProfileSet TestProfiles() => new WheelProfileSet
        {
            profiles = new[]
            {
                new WheelDeviceProfile
                {
                    id = "gc-test", deviceRangeDeg = 900f, defaultRangeDeg = 540f,
                    steer = new WheelAxisBinding { control = "stick/x" },
                    throttle = new WheelAxisBinding { control = "stick/up" },
                    brake = new WheelAxisBinding { control = "stick/down" },
                    clutch = new WheelAxisBinding { control = "stick/right" },
                    paddleUp = "trigger", paddleDown = "stick/left",
                    shifterGates = new[] { "stick/right", "trigger" }, shifterReverse = "stick/left",
                    buttons = new[]
                    {
                        new WheelButtonBinding { action = "ParkingBrake", control = "trigger" },
                        new WheelButtonBinding { action = "RangeToggle", control = "stick/up" },
                    },
                },
            },
        };

        [Test]
        public void PcSession_MixerPadKeysWheelForceFeedback_WithMenuGate_ZeroGcAlloc()
        {
            m_Pad = AddVirtual("Gamepad");
            m_Kb = AddVirtual("Keyboard");
            m_Joy = AddVirtual("Joystick");
            Assert.IsNotNull(Current("Gamepad"), "virtual gamepad present (the pad's device branch must run)");
            Assert.IsNotNull(Current("Keyboard"), "virtual keyboard present (the key ramp's device branch must run)");

            var feel = PadKeyboardFeel.Defaults();
            var tuning = PadUserTuning.From(feel);
            m_Actions = new DrivingActions();
            m_Actions.Enable();
            var pad = new GamepadDriverInput(m_Actions.Gamepad, feel, tuning);
            var keys = new KeyboardBindingsDriverInput(m_Actions.Keyboard, feel, tuning);
            var oldKeyboard = new KeyboardDriverInput { Enabled = false };   // PcInputBridge disables it (ADR 0264)
            m_Wheel = new PcWheel();
            m_Wheel.Input.Settings = new WheelSettings { profileOverride = "gc-test" };
            m_Wheel.Input.Profiles = TestProfiles();
            m_Wheel.ForceFeedback.Settings = m_Wheel.Input.Settings.forceFeedback;
            var sink = new RecordingForceFeedbackSink(256);
            m_Wheel.Sink = sink;
            m_Wheel.Input.Rebind();

            // Bootstrap order (DrivingLabBootstrap + PcInputBridge): pad, keys, old keyboard, PC wheel, touch wheel, gyro, touch.
            var mixer = new DriverInputMixer();
            mixer.Add(oldKeyboard);
            mixer.Add(m_Wheel.Input);
            mixer.Add(new TouchSteeringWheel());
            mixer.Add(new GyroSteering());
            mixer.Add(new TouchControls());
            mixer.InsertBefore(oldKeyboard, pad);
            mixer.InsertBefore(oldKeyboard, keys);

            var fb = new VehicleFeedback { HandwheelLockDeg = 800f };
            int frame = 0;
            float acc = 0f;
            void Frames()
            {
                for (int i = 0; i < 600; i++, frame++)
                {
                    mixer.MenuOpen = frame % 240 >= 200;            // settings panel opens and closes
                    fb.ForwardSpeed = (frame % 150) * 0.2f;
                    fb.RoadWheelAngleNormalized = Mathf.Sin(frame * 0.01f) * 0.3f;
                    var it = mixer.Sample(Dt, fb);
                    for (int s = 0; s < 2; s++)                     // ~2 fixed steps per rendered frame
                        acc += m_Wheel.StepForceFeedback(0.01f, !mixer.MenuGateActive, fb.ForwardSpeed, -600f * it.Steer, 20f, 30000f, 30000f + 800f * it.Steer);
                    acc += it.Throttle + pad.LastStick + keys.View.LookDegS.x;
                }
            }

            Frames();   // warm-up: device match / control resolve / onDeviceChange subscription (connect time)
            Assert.IsTrue(m_Wheel.Input.Connected, "virtual joystick bound to the test profile (the wheel's device branch must run)");
            Assert.Greater(sink.Count, 0, "force feedback reached the sink (active path)");
            GcAllocCounter.AssertZero(Frames, warmup: null, baselineSamples: 0,
                message: "PC driving input (pad + rebindable keys + HID wheel + FFB, menu gate) allocated in the driving loop");
            Assert.IsFalse(float.IsNaN(acc));
        }

        [Test]
        public void PcSession_NoVirtualDevices_IdleWheel_ZeroGcAlloc()
        {
            // No virtual devices: the wheel finds no matching device (idle branch, force feedback inactive -> Stop) - the
            // common case on a PC without a wheel; the pad / keys take the "no device" branch unless the test machine has a
            // real pad / keyboard (then their device branch runs - also allocation-free).
            var feel = PadKeyboardFeel.Defaults();
            var tuning = PadUserTuning.From(feel);
            m_Actions = new DrivingActions();
            m_Actions.Enable();
            var pad = new GamepadDriverInput(m_Actions.Gamepad, feel, tuning);
            var keys = new KeyboardBindingsDriverInput(m_Actions.Keyboard, feel, tuning);
            m_Wheel = new PcWheel();
            m_Wheel.Input.Profiles = TestProfiles();
            m_Wheel.Input.Settings = new WheelSettings { profileOverride = "no-such-profile" };
            m_Wheel.Input.Rebind();
            var mixer = new DriverInputMixer();
            mixer.Add(pad); mixer.Add(keys); mixer.Add(m_Wheel.Input); mixer.Add(new TouchSteeringWheel());
            var fb = new VehicleFeedback { HandwheelLockDeg = 800f, ForwardSpeed = 10f };
            float acc = 0f;
            void Frames()
            {
                for (int i = 0; i < 600; i++)
                {
                    mixer.MenuOpen = i % 100 >= 90;
                    var it = mixer.Sample(Dt, fb);
                    acc += it.Steer + m_Wheel.StepForceFeedback(0.01f, true, fb.ForwardSpeed, 100f, 20f, 30000f, 30000f);
                }
            }
            GcAllocCounter.AssertZero(Frames, warmup: Frames, message: "idle PC input paths allocated in the driving loop");
            Assert.IsFalse(m_Wheel.Input.Connected);
            Assert.IsFalse(float.IsNaN(acc));
        }
    }
}
