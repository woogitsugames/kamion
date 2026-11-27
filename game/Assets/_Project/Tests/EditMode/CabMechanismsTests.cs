using Game.Controls;
using Game.Gameplay;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    public class CabMechanismsTests
    {
        [Test]
        public void Wipers_WaitInIntermittent_KeepStrokeSpeed_ParkWhenSwitchedOff()
        {
            var drive = new WiperDrive();
            drive.Step(3f);
            Assert.AreEqual(0, drive.Starts);
            drive.CycleMode();
            drive.Step(0.01f);
            Assert.AreEqual(WiperMode.Intermittent, drive.Mode);
            Assert.AreEqual(1, drive.Starts);

            drive.Step(WiperDrive.SlowSeconds / 2f);
            Assert.AreEqual(0.5f, drive.Phase, 1e-5f);
            var left = WiperDrive.Rotation(drive.Phase, WiperDrive.LeftSweepDegrees);
            var right = WiperDrive.Rotation(drive.Phase, WiperDrive.RightSweepDegrees);
            Assert.That(Quaternion.Angle(left, Quaternion.identity), Is.EqualTo(72f).Within(0.001f));
            Assert.That(Quaternion.Angle(right, Quaternion.identity),
                Is.EqualTo(95f).Within(0.001f));
            Assert.Greater((left * Vector3.forward).x, 0f);
            Assert.Greater((right * Vector3.forward).x, 0f);
            drive.Step(WiperDrive.SlowSeconds / 2f);
            Assert.AreEqual(1, drive.Parks);
            drive.Step(WiperDrive.IntermittentPause - 0.01f);
            Assert.AreEqual(1, drive.Starts);
            drive.Step(0.02f);
            Assert.AreEqual(2, drive.Starts);

            drive.CycleMode();
            Assert.AreEqual(WiperMode.Slow, drive.Mode);
            drive.Step(WiperDrive.SlowSeconds);
            Assert.AreEqual(3, drive.Starts);
            drive.CycleMode();
            Assert.AreEqual(WiperMode.Fast, drive.Mode);
            drive.Step(WiperDrive.FastSeconds);
            Assert.AreEqual(3, drive.Starts, "the active slow stroke still has time left");
            drive.Step(WiperDrive.SlowSeconds - WiperDrive.FastSeconds + 0.01f);
            Assert.AreEqual(4, drive.Starts);
            Assert.AreEqual(WiperDrive.FastSeconds, drive.CycleSeconds);
            drive.Step(WiperDrive.FastSeconds / 2f);
            drive.CycleMode();
            Assert.AreEqual(WiperMode.Off, drive.Mode);
            Assert.AreEqual(0.5f, drive.Phase, 1e-5f);
            drive.Step(WiperDrive.FastSeconds / 2f);
            drive.Step(5f);
            Assert.AreEqual(0f, drive.Phase);
            Assert.AreEqual(4, drive.Starts);
            Assert.AreEqual(4, drive.Parks);
        }

        [Test]
        public void Wipers_StableBindingIsExposedInBothMaps()
        {
            using var actions = new DrivingActions();
            const string action = DrivingActionCatalog.CycleWipers;
            Assert.AreEqual("<Keyboard>/u", actions.EffectivePath(DrivingActionCatalog.KeyboardMap, action, 0));
            actions.SetOverride(DrivingActionCatalog.GamepadMap, action, 0, "<Gamepad>/rightShoulder");
            string stored = actions.SaveOverrides();
            using var restored = new DrivingActions();
            Assert.IsTrue(restored.LoadOverrides(stored));
            Assert.AreEqual("<Gamepad>/rightShoulder", restored.EffectivePath(DrivingActionCatalog.GamepadMap, action, 0));
        }

        sealed class FixedRandom : System.Random
        {
            public double Roll;
            public int Calls;
            public override double NextDouble() { Calls++; return Roll; }
        }

        [TestCase(0f, 0.4f, 0.45f, false)]
        [TestCase(15f, 0.4f, 0.45f, false)]
        [TestCase(24f, 0.4f, 0.45f, false)]
        [TestCase(8f, 0.1f, 0.45f, false)]
        [TestCase(8f, 0.9f, 0.45f, false)]
        [TestCase(8f, 0.4f, 0f, false)]
        [TestCase(8f, 0.4f, 1f, false)]
        [TestCase(8f, 0.4f, 0.45f, true)]
        public void BrakeSqueal_InvalidConditionsDoNotDraw(float speed, float pressure, float demand, bool inhibited)
        {
            var gate = new BrakeSquealGate();
            var random = new FixedRandom();
            Assert.IsFalse(gate.Step(1f, speed, pressure, demand, inhibited, random));
            Assert.AreEqual(0, random.Calls);
        }

        [Test]
        public void BrakeSqueal_RequiresDwell_RollsOncePerApplication_AndHasCooldown()
        {
            var gate = new BrakeSquealGate();
            var random = new FixedRandom { Roll = 0.9 };
            Assert.IsFalse(gate.Step(0.05f, 8f, 0.4f, 0.45f, false, random));
            Assert.AreEqual(0, random.Calls);
            Assert.IsFalse(gate.Step(0.05f, 8f, 0.4f, 0.45f, false, random));
            random.Roll = 0.1;
            Assert.IsFalse(gate.Step(1f, 8f, 0.4f, 0.45f, false, random), "no reroll while the brake stays applied");
            Assert.AreEqual(1, random.Calls);
            gate.Step(0.1f, 8f, 0.4f, 0f, false, random);
            Assert.IsTrue(gate.Step(0.11f, -8f, 0.4f, 0.45f, false, random), "reverse also rolls");
            gate.Step(0.1f, 8f, 0.4f, 0f, false, random);
            Assert.IsFalse(gate.Step(0.11f, 8f, 0.4f, 0.45f, false, random));
            Assert.AreEqual(2, random.Calls, "cooldown consumed the attempt without a roll");
            gate.Step(3f, 8f, 0.4f, 0f, false, random);
            Assert.IsTrue(gate.Step(0.11f, 8f, 0.4f, 0.45f, false, random));
            Assert.AreEqual(3, random.Calls);
        }
    }
}
