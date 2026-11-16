using Game.Controls;
using NUnit.Framework;

namespace Game.Tests
{
    /// <summary>
    /// PC wheel / pedals / H-shifter layer (ADR 0263), without hardware: calibration, rotation range and soft lock,
    /// inverted pedals, dead zones, steering direction in both mappings, shifter commands, mixer integration.
    /// Pure logic (no Unity API) — also compiled and run outside Unity (docs/status/wheel-0263-STATUS.md).
    /// </summary>
    public class PcWheelInputTests
    {
        const float Eps = 1e-4f;

        // ---------------- calibration ----------------

        [Test]
        public void Steer_OffCentreCalibration_GivesZeroAtCentreAndUnitAtStops()
        {
            var c = AxisCalibration.Steering(-0.9f, 0.1f, 1.0f);
            Assert.AreEqual(0f, WheelAxisMath.Steer(0.1f, c), Eps);
            Assert.AreEqual(-1f, WheelAxisMath.Steer(-0.9f, c), Eps);
            Assert.AreEqual(1f, WheelAxisMath.Steer(1.0f, c), Eps);
            Assert.AreEqual(0.5f, WheelAxisMath.Steer(0.55f, c), Eps, "right half scaled on its own span");
            Assert.AreEqual(-0.5f, WheelAxisMath.Steer(-0.4f, c), Eps, "left half scaled on its own span");
            Assert.AreEqual(1f, WheelAxisMath.Steer(5f, c), Eps, "clamped beyond the stop");
        }

        [Test]
        public void Steer_DescendingAxis_RightStillPositive()
        {
            // A device that reports full right as the lower raw value: calibrate left=+1, right=-1.
            var c = AxisCalibration.Steering(1f, 0f, -1f);
            Assert.AreEqual(1f, WheelAxisMath.Steer(-1f, c), Eps);
            Assert.AreEqual(-1f, WheelAxisMath.Steer(1f, c), Eps);
            Assert.AreEqual(0.25f, WheelAxisMath.Steer(-0.25f, c), Eps);
        }

        [Test]
        public void Steer_Invert_FlipsDirection()
        {
            var c = AxisCalibration.Steering(-1f, 0f, 1f);
            c.invert = true;
            Assert.AreEqual(-0.3f, WheelAxisMath.Steer(0.3f, c), Eps);
        }

        [Test]
        public void Steer_CentreDeadZone_RescaledWithoutStep()
        {
            var c = AxisCalibration.Steering(-1f, 0f, 1f, dead: 0.1f);
            Assert.AreEqual(0f, WheelAxisMath.Steer(0.05f, c), Eps);
            Assert.AreEqual(0f, WheelAxisMath.Steer(0.1f, c), Eps);
            Assert.Less(WheelAxisMath.Steer(0.11f, c), 0.02f, "continuous at the dead-zone edge");
            Assert.AreEqual(1f, WheelAxisMath.Steer(1f, c), Eps);
            Assert.AreEqual(0.5f, WheelAxisMath.Steer(0.55f, c), Eps);
        }

        [Test]
        public void Pedal_Inverted_ReleasedHighPressedLow()
        {
            var c = AxisCalibration.Pedal(rawReleased: 1f, rawPressed: -1f);
            Assert.AreEqual(0f, WheelAxisMath.Pedal(1f, c), Eps);
            Assert.AreEqual(1f, WheelAxisMath.Pedal(-1f, c), Eps);
            Assert.AreEqual(0.5f, WheelAxisMath.Pedal(0f, c), Eps);
            var same = AxisCalibration.Pedal(-1f, 1f); same.invert = true;
            Assert.AreEqual(WheelAxisMath.Pedal(0.3f, c), WheelAxisMath.Pedal(0.3f, same), Eps, "invert flag = swapped ends");
        }

        [Test]
        public void Pedal_DeadZones_RestAndSaturation()
        {
            var c = AxisCalibration.Pedal(0f, 1f, deadLow: 0.05f, deadHigh: 0.05f);
            Assert.AreEqual(0f, WheelAxisMath.Pedal(0.04f, c), Eps, "pot noise at rest = 0");
            Assert.AreEqual(1f, WheelAxisMath.Pedal(0.96f, c), Eps, "full before the mechanical stop");
            Assert.AreEqual(0.5f, WheelAxisMath.Pedal(0.5f, c), Eps);
            Assert.Less(WheelAxisMath.Pedal(0.051f, c), 0.01f, "no step at the rest edge");
        }

        [Test]
        public void Pedal_DegenerateCalibration_IsSafe()
        {
            var c = AxisCalibration.Pedal(0.5f, 0.5f);
            Assert.AreEqual(0f, WheelAxisMath.Pedal(0.7f, c), Eps);
            c.Sanitize();
            Assert.Greater(System.Math.Abs(c.rawMax - c.rawMin), 0.5f, "sanitize restores a span");
            var nan = new AxisCalibration { rawMin = float.NaN, rawMax = float.PositiveInfinity, deadZoneLow = 3f };
            nan.Sanitize();
            Assert.IsFalse(float.IsNaN(WheelAxisMath.Pedal(0.5f, nan)));
            Assert.LessOrEqual(nan.deadZoneLow, 0.5f);
        }

        [Test]
        public void CombinedPedals_SplitIntoThrottleAndBrake()
        {
            var c = AxisCalibration.Steering(-1f, 0f, 1f, dead: 0.02f);
            WheelAxisMath.SplitCombined(0.5f, c, out float t, out float b);
            Assert.Greater(t, 0.45f); Assert.AreEqual(0f, b, Eps);
            WheelAxisMath.SplitCombined(-1f, c, out t, out b);
            Assert.AreEqual(0f, t, Eps); Assert.AreEqual(1f, b, Eps);
            WheelAxisMath.SplitCombined(0.01f, c, out t, out b);
            Assert.AreEqual(0f, t, Eps); Assert.AreEqual(0f, b, Eps);
        }

        [Test]
        public void Calibrator_DetectsInvertedPedalFromReleasedReading()
        {
            var cal = new AxisCalibrator();
            foreach (var r in new[] { 0.98f, 0.5f, -0.97f, 0.1f, 0.99f }) cal.Observe(r);
            Assert.IsTrue(cal.Covers(2f, 0.9f));
            var p = cal.ToPedal(releasedRaw: 0.99f, deadLow: 0f, deadHigh: 0f);
            Assert.AreEqual(0f, WheelAxisMath.Pedal(0.99f, p), Eps);
            Assert.AreEqual(1f, WheelAxisMath.Pedal(-0.97f, p), Eps);
        }

        [Test]
        public void Calibrator_SteeringWithCentre()
        {
            var cal = new AxisCalibrator();
            cal.Observe(-0.95f); cal.Observe(0.97f); cal.MarkCentre(0.02f);
            var s = cal.ToSteering(0f);
            Assert.AreEqual(0f, WheelAxisMath.Steer(0.02f, s), Eps);
            Assert.AreEqual(1f, WheelAxisMath.Steer(0.97f, s), Eps);
            Assert.AreEqual(-1f, WheelAxisMath.Steer(-0.95f, s), Eps);
        }

        [Test]
        public void AutoPedal_UncalibratedInvertedAxis_RestIsZeroAndLightTouchIsNotFull()
        {
            var a = AutoPedal.Create(expectedSpan: 1f);
            Assert.AreEqual(0f, a.Value(1f, 0f, 0f), Eps, "first reading = released");
            Assert.AreEqual(0.1f, a.Value(0.9f, 0f, 0f), Eps, "light touch on an inverted axis");
            Assert.AreEqual(1f, a.Value(-1f, 0f, 0f), Eps, "full travel seen");
            Assert.AreEqual(0.5f, a.Value(0f, 0f, 0f), Eps, "span learned = 2");
        }

        [Test]
        public void AutoSteer_Uncalibrated_CentreFromFirstReadingAndLearnsSpan()
        {
            var a = AutoSteer.Create(expectedSpan: 1f);
            Assert.AreEqual(0f, a.Value(0.5f, false, 0f), Eps, "0..1 axis centred at 0.5");
            Assert.AreEqual(1f, a.Value(1f, false, 0f), Eps, "half the expected span per side");
            Assert.AreEqual(-0.5f, a.Value(0.25f, false, 0f), Eps);
            var b = AutoSteer.Create(1f);
            b.Value(0f, false, 0f);                       // -1..1 axis
            Assert.AreEqual(1f, b.Value(0.5f, false, 0f), Eps, "before full lock is seen");
            b.Value(1f, false, 0f);                       // full right seen
            Assert.AreEqual(0.5f, b.Value(0.5f, false, 0f), Eps, "span learned");
            Assert.AreEqual(-0.5f, b.Value(0.5f, true, 0f), Eps, "invert");
        }

        [Test]
        public void AutoDetect_FindsMovedAxis()
        {
            var b = new[] { 0f, 1f, -1f, 0.5f };
            var c = new[] { 0.01f, 1f, 0.2f, 0.5f };
            Assert.AreEqual(2, AxisAutoDetect.MostMoved(b, c, 4, 0.2f));
            Assert.AreEqual(-1, AxisAutoDetect.MostMoved(b, b, 4, 0.2f));
        }

        // ---------------- rotation range, soft lock, direction ----------------

        [Test]
        public void Range_ClampedTo270_900AndDevice()
        {
            Assert.AreEqual(270f, WheelSteeringMap.ClampRange(100f, 900f), Eps);
            Assert.AreEqual(900f, WheelSteeringMap.ClampRange(1080f, 1080f), Eps);
            Assert.AreEqual(540f, WheelSteeringMap.ClampRange(540f, 900f), Eps);
            Assert.AreEqual(900f, WheelSteeringMap.ClampRange(float.NaN, 900f), Eps);
            Assert.AreEqual(200f, WheelSteeringMap.ClampRange(540f, 200f), Eps, "a device that turns less than 270 limits the range");
        }

        [TestCase(270f)]
        [TestCase(540f)]
        [TestCase(900f)]
        public void ScaledToLock_RangeEndIsFullLock(float range)
        {
            const float lockDeg = 800f;   // 40 deg x 20:1 (tractor_4x2_generic)
            Assert.AreEqual(1f, WheelSteeringMap.Command(range / 2f, range, lockDeg, WheelSteerMapping.ScaledToLock), Eps);
            Assert.AreEqual(-0.5f, WheelSteeringMap.Command(-range / 4f, range, lockDeg, WheelSteerMapping.ScaledToLock), Eps);
            Assert.AreEqual(lockDeg / (range / 2f), WheelSteeringMap.CabPerDeviceDeg(range, lockDeg, WheelSteerMapping.ScaledToLock), Eps);
        }

        [Test]
        public void SoftLock_RangeSmallerThanDevice_ClampsAndReportsOvershoot()
        {
            // 900 deg device, 540 deg in-game range: past 270 deg the command stays at full lock.
            float dev = WheelSteeringMap.DeviceDeg(0.6667f, 900f);   // ~300 deg
            Assert.AreEqual(300f, dev, 0.1f);
            Assert.AreEqual(1f, WheelSteeringMap.Command(dev, 540f, 800f, WheelSteerMapping.ScaledToLock), Eps);
            Assert.AreEqual(30f, WheelSteeringMap.PastSoftLockDeg(dev, 540f, 800f, WheelSteerMapping.ScaledToLock), 0.1f);
            Assert.AreEqual(0f, WheelSteeringMap.PastSoftLockDeg(100f, 540f, 800f, WheelSteerMapping.ScaledToLock), Eps);
            Assert.AreEqual(-10f, WheelSteeringMap.PastSoftLockDeg(-280f, 540f, 800f, WheelSteerMapping.ScaledToLock), Eps);
        }

        [Test]
        public void OneToOne_DeviceDegreeIsCabDegree()
        {
            Assert.AreEqual(450f / 800f, WheelSteeringMap.Command(450f, 900f, 800f, WheelSteerMapping.OneToOne), Eps);
            Assert.AreEqual(90f, WheelSteeringMap.CabDeg(90f, 900f, 800f, WheelSteerMapping.OneToOne), Eps);
            Assert.AreEqual(1f, WheelSteeringMap.CabPerDeviceDeg(900f, 800f, WheelSteerMapping.OneToOne), Eps);
            // A car-like lock smaller than the range: the soft lock moves to the truck lock.
            Assert.AreEqual(200f, WheelSteeringMap.SoftLockDeg(900f, 200f, WheelSteerMapping.OneToOne), Eps);
            Assert.AreEqual(1f, WheelSteeringMap.Command(300f, 900f, 200f, WheelSteerMapping.OneToOne), Eps);
        }

        [Test]
        public void Direction_RightRimGivesPositiveSteerInEveryMapping()
        {
            var c = AxisCalibration.Steering(-1f, 0f, 1f);
            foreach (WheelSteerMapping m in new[] { WheelSteerMapping.ScaledToLock, WheelSteerMapping.OneToOne })
                foreach (float range in new[] { 270f, 540f, 900f })
                {
                    float dev = WheelSteeringMap.DeviceDeg(WheelAxisMath.Steer(0.3f, c), 900f);
                    Assert.Greater(WheelSteeringMap.Command(dev, range, 800f, m), 0f, m + " " + range);
                    float devL = WheelSteeringMap.DeviceDeg(WheelAxisMath.Steer(-0.3f, c), 900f);
                    Assert.Less(WheelSteeringMap.Command(devL, range, 800f, m), 0f, m + " " + range);
                }
        }

        // ---------------- H-shifter, paddles ----------------

        static DriverIntent Fresh() { var i = new DriverIntent(); i.ClearCommands(); return i; }

        [Test]
        public void HShifter_FromNeutralIntoFirst_RequestsDrive()
        {
            var h = new HShifterMapper();
            var it = Fresh();
            h.Update(0.01f, 1, false, ref it);
            Assert.AreEqual(SelectorRequest.Drive, it.Selector);
            Assert.AreEqual(1, it.TargetGear);
            Assert.AreEqual(0, it.ShiftDelta);
        }

        [Test]
        public void HShifter_QuickShiftThroughNeutral_GivesDeltaNotNeutral()
        {
            var h = new HShifterMapper();
            var it = Fresh(); h.Update(0.01f, 3, false, ref it);
            for (int i = 0; i < 20; i++) { it = Fresh(); h.Update(0.01f, 0, false, ref it); Assert.AreEqual(SelectorRequest.None, it.Selector); }
            it = Fresh(); h.Update(0.01f, 4, false, ref it);
            Assert.AreEqual(1, it.ShiftDelta);
            Assert.AreEqual(4, it.TargetGear);
            it = Fresh(); h.Update(0.01f, 2, false, ref it);
            Assert.AreEqual(-2, it.ShiftDelta, "skip shift 4 -> 2");
            it = Fresh(); h.Update(0.01f, 2, false, ref it);
            Assert.AreEqual(0, it.ShiftDelta, "holding a gate repeats nothing");
        }

        [Test]
        public void HShifter_RangeHigh_AddsGates()
        {
            var h = new HShifterMapper { GatesPerRange = 6 };
            var it = Fresh(); h.Update(0.01f, 6, false, ref it);
            it = Fresh(); h.Update(0.01f, 1, true, ref it);
            Assert.AreEqual(7, it.TargetGear);
            Assert.AreEqual(1, it.ShiftDelta, "6 low -> 1 high = 6 -> 7");
            Assert.AreEqual(12, h.Gear(6, true));
            h.UseRange = false;
            Assert.AreEqual(6, h.Gear(6, true));
        }

        [Test]
        public void HShifter_HeldNeutral_AndReverse()
        {
            var h = new HShifterMapper { NeutralHoldS = 0.5f };
            var it = Fresh(); h.Update(0.01f, 2, false, ref it);
            bool sawNeutral = false;
            for (int i = 0; i < 60; i++) { it = Fresh(); h.Update(0.01f, 0, false, ref it); sawNeutral |= it.Selector == SelectorRequest.Neutral; }
            Assert.IsTrue(sawNeutral);
            Assert.AreEqual(0, h.EngagedGear);
            it = Fresh(); h.Update(0.01f, -1, false, ref it);
            Assert.AreEqual(SelectorRequest.Reverse, it.Selector);
            it = Fresh(); h.Update(0.01f, 1, false, ref it);
            Assert.AreEqual(SelectorRequest.Drive, it.Selector, "R -> 1 goes through the selector, not a delta");
            Assert.AreEqual(0, it.ShiftDelta);
        }

        [Test]
        public void HShifter_SlotFromGates()
        {
            var g = new bool[6];
            Assert.AreEqual(0, HShifterMapper.Slot(g, 6, false));
            g[3] = true;
            Assert.AreEqual(4, HShifterMapper.Slot(g, 6, false));
            Assert.AreEqual(-1, HShifterMapper.Slot(g, 6, true));
            Assert.AreEqual(0, HShifterMapper.Slot(null, 6, false));
        }

        [Test]
        public void ButtonEdges_OnlyOnPress()
        {
            var e = new ButtonEdges(2);
            Assert.IsTrue(e.Pressed(0, true));
            Assert.IsFalse(e.Pressed(0, true));
            Assert.IsFalse(e.Pressed(0, false));
            Assert.IsTrue(e.Pressed(0, true));
            Assert.IsFalse(e.Pressed(5, true), "out of range is safe");
        }

        // ---------------- mixer integration ----------------

        sealed class FakeWheel : IDriverInput
        {
            public string Name => "fake-wheel";
            public bool Enabled { get; set; } = true;
            public float Steer, Clutch; public int Gear;
            public void Sample(float dt, in VehicleFeedback fb, ref DriverIntent intent)
            {
                intent.Steer = Steer; intent.SteerActive = true; intent.HandsOn = true; intent.DirectSteer = true;
                intent.Clutch = Clutch; intent.TargetGear = Gear;
            }
        }

        sealed class FakeKeys : IDriverInput
        {
            public string Name => "fake-keys";
            public bool Enabled { get; set; } = true;
            public bool Held; public float Throttle;
            public void Sample(float dt, in VehicleFeedback fb, ref DriverIntent intent)
            {
                intent.Steer = Held ? -1f : 0f; intent.SteerActive = Held; intent.HandsOn = Held; intent.Throttle = Throttle;
            }
        }

        [Test]
        public void Mixer_WheelSteersDirectly_KeysOverrideWhileHeld_PedalsMerge()
        {
            var mixer = new DriverInputMixer();
            var keys = new FakeKeys { Throttle = 0.2f };
            var wheel = new FakeWheel { Steer = 0.4f, Clutch = 0.7f, Gear = 3 };
            mixer.Add(keys); mixer.Add(wheel);
            var fb = new VehicleFeedback();
            var r = mixer.Sample(0.016f, fb);
            Assert.AreEqual(0.4f, r.Steer, Eps);
            Assert.IsTrue(r.DirectSteer);
            Assert.AreEqual(0.7f, r.Clutch, Eps);
            Assert.AreEqual(3, r.TargetGear);
            Assert.AreEqual(0.2f, r.Throttle, Eps);
            keys.Held = true;
            r = mixer.Sample(0.016f, fb);
            Assert.AreEqual(-1f, r.Steer, Eps);
            Assert.IsFalse(r.DirectSteer, "keyboard steering keeps the hand model");
            wheel.Enabled = false;
            r = mixer.Sample(0.016f, fb);
            Assert.AreEqual(0f, r.Clutch, Eps, "disabled source contributes no pedal");
        }

        // ---------------- profiles (pure matching) ----------------

        static WheelProfileSet Set() => new WheelProfileSet
        {
            profiles = new[]
            {
                new WheelDeviceProfile { id = "generic" },
                new WheelDeviceProfile { id = "a", vendorId = 0x1111, productIds = new[] { 0x22 }, productContains = "ALPHA" },
                new WheelDeviceProfile { id = "b", vendorId = 0x1111, productContains = "BETA" },
                new WheelDeviceProfile { id = "vendor", vendorId = 0x3333 },
            }
        };

        [Test]
        public void Profiles_MatchByIdsThenNameThenVendorThenGeneric()
        {
            var s = Set();
            Assert.AreEqual("a", s.Find(0x1111, 0x22, "x").id);
            Assert.AreEqual("b", s.Find(0x1111, 0x99, "Racing beta wheel").id);
            Assert.AreEqual("b", s.Find(0, 0, "BETA").id, "unknown ids: name only");
            Assert.AreEqual("vendor", s.Find(0x3333, 0x1, "?").id);
            Assert.AreEqual("generic", s.Find(0x9999, 0x1, "?").id);
            Assert.AreEqual("generic", s.Find(0x1111, 0x99, null).id, "vendor match without a vendor-only profile falls back");
        }

        [Test]
        public void Profiles_ActionNamesParse()
        {
            Assert.AreEqual(WheelAction.ParkingBrake, new WheelButtonBinding { action = "ParkingBrake" }.Parse());
            Assert.AreEqual(WheelAction.RangeToggle, new WheelButtonBinding { action = "rangetoggle" }.Parse());
            Assert.AreEqual(WheelAction.None, new WheelButtonBinding { action = "Turbo" }.Parse());
        }

        [Test]
        public void Profiles_SanitizeClampsRangesAndCalibrations()
        {
            var s = new WheelProfileSet { profiles = new[] { new WheelDeviceProfile { id = "x", deviceRangeDeg = float.NaN, defaultRangeDeg = 5000f, productIds = null } } };
            s.profiles[0].steer.calibration.deadZoneLow = 9f;
            s.Sanitize();
            Assert.AreEqual(900f, s.profiles[0].deviceRangeDeg, Eps);
            Assert.AreEqual(900f, s.profiles[0].defaultRangeDeg, Eps);
            Assert.LessOrEqual(s.profiles[0].steer.calibration.deadZoneLow, 0.5f);
            Assert.IsNotNull(s.profiles[0].productIds);
        }
    }
}
