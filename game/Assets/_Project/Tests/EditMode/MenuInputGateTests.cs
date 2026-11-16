using Game.Controls;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>
    /// Review #131 P1-1 (ADR 0265): while a settings panel / modal is open the pad, keyboard and PC wheel must not
    /// drive the truck - their buttons navigate the menu. The gate lives in <see cref="DriverInputMixer"/>
    /// (<see cref="DriverInputMixer.MenuOpen"/>, <see cref="IMenuGatedInput"/>); the scene sets the flag from
    /// <c>m_SettingsPanel != null || UiFocus.HasModal</c>. Pure logic with fake devices (no hardware, no Input System):
    /// empty intent while open, nothing leaks in the frame the panel closes (button edge, either update order), a
    /// button held across the close is not a new press, autopilot / touch sources are not gated, no allocation.
    /// </summary>
    public class MenuInputGateTests
    {
        const float Dt = 1f / 60f;
        static readonly VehicleFeedback Fb = new VehicleFeedback { ForwardSpeed = 14f, HandwheelLockDeg = 800f };

        /// <summary>
        /// A menu-capable device. <see cref="PressedThisFrame"/> behaves like <c>InputAction.WasPressedThisFrame</c>
        /// (pad B = N, pad A = parking brake); <see cref="ButtonDown"/> is a level read through a real
        /// <see cref="ButtonEdges"/> like the mapped buttons of <see cref="HidWheelDriverInput"/>; the ramp is a key ramp.
        /// </summary>
        sealed class FakeDevice : IDriverInput, IMenuGatedInput
        {
            public string Name => "fake-pad";
            public bool Enabled { get; set; } = true;
            public bool PressedThisFrame, ButtonDown, Steering;
            public float Throttle, Brake, Clutch, Steer;
            public float Ramp;
            public int Samples, Blocked;
            readonly ButtonEdges m_Edges = new ButtonEdges(1);

            public void Sample(float dt, in VehicleFeedback fb, ref DriverIntent intent)
            {
                Samples++;
                Ramp = Throttle;
                intent.Throttle = Ramp; intent.Brake = Brake; intent.Clutch = Clutch;
                intent.Steer = Steer; intent.SteerActive = Steering; intent.HandsOn = Steering; intent.DirectSteer = Steering;
                if (PressedThisFrame)
                {
                    intent.Selector = SelectorRequest.Neutral;
                    intent.ToggleParkingBrake = true;
                    intent.RetarderDelta += 1;
                    intent.ToggleManual = true;
                }
                if (m_Edges.Pressed(0, ButtonDown))
                {
                    intent.ShiftDelta += 1;
                    intent.TurnSignal = TurnSignalRequest.Left;
                    intent.ToggleCoupling = true;
                }
            }

            public void SampleBlocked(float dt, in VehicleFeedback fb)
            {
                Blocked++;
                Ramp = 0f;
                m_Edges.Pressed(0, ButtonDown);
            }
        }

        /// <summary>Not a menu device (autopilot, touch wheel, gyro): never gated.</summary>
        sealed class FakeAutopilot : IDriverInput
        {
            public string Name => "fake-autopilot";
            public bool Enabled { get; set; } = true;
            public int Samples;
            public void Sample(float dt, in VehicleFeedback fb, ref DriverIntent intent)
            {
                Samples++;
                intent.Steer = 0.25f; intent.SteerActive = true; intent.HandsOn = true;
                intent.Throttle = 0.4f;
            }
        }

        static void AssertEmpty(in DriverIntent i, string what)
        {
            Assert.IsFalse(i.SteerActive, what + ": steering");
            Assert.IsFalse(i.HandsOn, what + ": hands on");
            Assert.IsFalse(i.DirectSteer, what + ": direct steer");
            Assert.AreEqual(0f, i.Steer, what + ": steer");
            Assert.AreEqual(0f, i.Throttle, what + ": throttle");
            Assert.AreEqual(0f, i.Brake, what + ": brake");
            Assert.AreEqual(0f, i.Clutch, what + ": clutch");
            AssertNoCommands(i, what);
        }

        static void AssertNoCommands(in DriverIntent i, string what)
        {
            Assert.AreEqual(SelectorRequest.None, i.Selector, what + ": selector");
            Assert.AreEqual(0, i.ShiftDelta, what + ": shift");
            Assert.AreEqual(0, i.TargetGear, what + ": target gear");
            Assert.IsFalse(i.ToggleParkingBrake, what + ": parking brake");
            Assert.IsFalse(i.ToggleManual, what + ": manual");
            Assert.AreEqual(0, i.RetarderDelta, what + ": retarder");
            Assert.IsFalse(i.ToggleCoupling, what + ": coupling");
            Assert.IsFalse(i.ToggleLandingGear, what + ": landing gear");
            Assert.IsFalse(i.ToggleBrakeCruise, what + ": brake cruise");
            Assert.IsFalse(i.ToggleReverseCamera, what + ": reverse camera");
            Assert.AreEqual(TurnSignalRequest.None, i.TurnSignal, what + ": turn signal");
        }

        static FakeDevice Busy() => new FakeDevice
        {
            PressedThisFrame = true, ButtonDown = true, Steering = true, Steer = -0.7f, Throttle = 1f, Brake = 0.5f, Clutch = 0.3f,
        };

        [Test]
        public void Closed_DeviceDrives_AsBefore()
        {
            var mixer = new DriverInputMixer();
            var pad = Busy();
            mixer.Add(pad);
            var i = mixer.Sample(Dt, Fb);
            Assert.IsFalse(mixer.MenuGateActive);
            Assert.AreEqual(1f, i.Throttle);
            Assert.AreEqual(0.5f, i.Brake);
            Assert.AreEqual(0.3f, i.Clutch);
            Assert.IsTrue(i.SteerActive);
            Assert.AreEqual(-0.7f, i.Steer);
            Assert.AreEqual(SelectorRequest.Neutral, i.Selector);
            Assert.IsTrue(i.ToggleParkingBrake);
            Assert.AreEqual(1, i.ShiftDelta);
            Assert.AreEqual(0, pad.Blocked);
        }

        [Test]
        public void Open_MenuDevice_GivesEmptyIntent()
        {
            var mixer = new DriverInputMixer();
            var pad = Busy();
            mixer.Add(pad);
            mixer.MenuOpen = true;
            for (int f = 0; f < 5; f++)
            {
                pad.PressedThisFrame = f % 2 == 0;   // navigating: A / B / d-pad presses every other frame
                var i = mixer.Sample(Dt, Fb);
                Assert.IsTrue(mixer.MenuGateActive);
                AssertEmpty(i, "frame " + f);
            }
            Assert.AreEqual(0, pad.Samples, "the device is not sampled as a driving input while the menu is open");
            Assert.AreEqual(5, pad.Blocked);
            Assert.AreEqual("-", mixer.SteeringSource);
        }

        [Test]
        public void Open_AutopilotAndTouch_StillDrive()
        {
            var mixer = new DriverInputMixer();
            var auto = new FakeAutopilot();
            var pad = Busy();
            mixer.Add(auto);
            mixer.Add(pad);
            mixer.MenuOpen = true;
            var i = mixer.Sample(Dt, Fb);
            Assert.AreEqual(1, auto.Samples);
            Assert.IsTrue(i.SteerActive);
            Assert.AreEqual(0.25f, i.Steer);
            Assert.AreEqual(0.4f, i.Throttle, "the pad's full throttle is not mixed in");
            Assert.AreEqual(0f, i.Brake);
            Assert.AreEqual("fake-autopilot", mixer.SteeringSource);
            AssertNoCommands(i, "autopilot + gated pad");
        }

        /// <summary>The UI closed the panel BEFORE the mixer sample of the same frame: the flag is already false while
        /// the button that closed it is still "pressed this frame".</summary>
        [Test]
        public void CloseFrame_UiBeforeSample_ButtonEdgeDoesNotReachVehicle()
        {
            var mixer = new DriverInputMixer();
            var pad = new FakeDevice();
            mixer.Add(pad);
            mixer.MenuOpen = true;
            AssertEmpty(mixer.Sample(Dt, Fb), "open");

            // Frame N: pad B pressed, the UI handled it first and closed the panel.
            pad.PressedThisFrame = true;
            mixer.MenuOpen = false;
            var close = mixer.Sample(Dt, Fb);
            Assert.IsTrue(mixer.MenuGateActive, "the gate holds for the close frame");
            AssertEmpty(close, "close frame");

            // Frame N+1: the press is over; driving input is back.
            pad.PressedThisFrame = false;
            pad.Throttle = 0.6f;
            var after = mixer.Sample(Dt, Fb);
            Assert.IsFalse(mixer.MenuGateActive);
            Assert.AreEqual(0.6f, after.Throttle);
            AssertNoCommands(after, "first driving frame");

            // A new press after the close is a driving command again.
            pad.PressedThisFrame = true;
            var press = mixer.Sample(Dt, Fb);
            Assert.AreEqual(SelectorRequest.Neutral, press.Selector);
            Assert.IsTrue(press.ToggleParkingBrake);
        }

        /// <summary>The mixer sampled BEFORE the UI closed the panel (flag still true in the press frame).</summary>
        [Test]
        public void CloseFrame_SampleBeforeUi_ButtonEdgeDoesNotReachVehicle()
        {
            var mixer = new DriverInputMixer();
            var pad = new FakeDevice();
            mixer.Add(pad);
            mixer.MenuOpen = true;
            pad.PressedThisFrame = true;                 // frame N: press, panel still open at the sample
            AssertEmpty(mixer.Sample(Dt, Fb), "press frame");
            pad.PressedThisFrame = false;
            mixer.MenuOpen = false;                      // frame N+1: the panel is gone
            AssertEmpty(mixer.Sample(Dt, Fb), "hold frame");
            pad.Throttle = 1f;
            Assert.AreEqual(1f, mixer.Sample(Dt, Fb).Throttle, "frame N+2 drives");
        }

        /// <summary>Level-read buttons with their own edge state (PC wheel, <see cref="ButtonEdges"/>): a button pressed
        /// in the menu and still held after it closed must not become a press in the first driving frame.</summary>
        [Test]
        public void ButtonHeldAcrossClose_IsNotANewPress()
        {
            var mixer = new DriverInputMixer();
            var wheel = new FakeDevice();
            mixer.Add(wheel);
            Assert.AreEqual(0, mixer.Sample(Dt, Fb).ShiftDelta);

            mixer.MenuOpen = true;
            AssertEmpty(mixer.Sample(Dt, Fb), "open");
            wheel.ButtonDown = true;                     // pressed while the menu is open (closes it)
            AssertEmpty(mixer.Sample(Dt, Fb), "pressed in menu");
            mixer.MenuOpen = false;
            AssertEmpty(mixer.Sample(Dt, Fb), "close frame");
            for (int f = 0; f < 10; f++) AssertNoCommands(mixer.Sample(Dt, Fb), "held after close, frame " + f);

            wheel.ButtonDown = false;
            AssertNoCommands(mixer.Sample(Dt, Fb), "released");
            wheel.ButtonDown = true;
            var press = mixer.Sample(Dt, Fb);
            Assert.AreEqual(1, press.ShiftDelta, "a new press after the menu shifts");
            Assert.AreEqual(TurnSignalRequest.Left, press.TurnSignal);
        }

        [Test]
        public void Open_RampsAreDropped_NoThrottleLeftOverAfterClose()
        {
            var mixer = new DriverInputMixer();
            var keys = new FakeDevice { Throttle = 1f };
            mixer.Add(keys);
            Assert.AreEqual(1f, mixer.Sample(Dt, Fb).Throttle);
            Assert.AreEqual(1f, keys.Ramp);
            mixer.MenuOpen = true;
            mixer.Sample(Dt, Fb);
            Assert.AreEqual(0f, keys.Ramp, "the source resets its ramp while the menu is open");
        }

        [Test]
        public void Reopen_GatesAgain_AndDisabledSourceStaysDisabled()
        {
            var mixer = new DriverInputMixer();
            var pad = Busy();
            var old = Busy();
            old.Enabled = false;                         // e.g. the fixed-key keyboard replaced by the rebindable one
            mixer.Add(pad);
            mixer.Add(old);
            for (int cycle = 0; cycle < 3; cycle++)
            {
                mixer.MenuOpen = true;
                AssertEmpty(mixer.Sample(Dt, Fb), "open " + cycle);
                mixer.MenuOpen = false;
                AssertEmpty(mixer.Sample(Dt, Fb), "close " + cycle);
                pad.PressedThisFrame = false;
                Assert.AreEqual(1f, mixer.Sample(Dt, Fb).Throttle, "drive " + cycle);
                pad.PressedThisFrame = true;
            }
            Assert.AreEqual(0, old.Samples, "a disabled source is never sampled");
            Assert.AreEqual(0, old.Blocked, "a disabled source is not touched by the gate");
            Assert.IsFalse(old.Enabled, "the gate does not use (or restore) Enabled");
        }

        [Test]
        public void Gate_DoesNotAllocate()
        {
            var mixer = new DriverInputMixer();
            var pad = Busy();
            var auto = new FakeAutopilot();
            mixer.Add(auto);
            mixer.Add(pad);
            void Run()
            {
                for (int f = 0; f < 600; f++)
                {
                    mixer.MenuOpen = f % 120 >= 60;      // open / close several times
                    mixer.Sample(Dt, Fb);
                }
            }
            GcAllocCounter.AssertZero(Run, warmup: Run, message: "menu gate must not allocate in the driving loop");
        }
    }
}
