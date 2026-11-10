using Game.Controls;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>Control settings: defaults, save/load, clamping, schema migration, steering direction in every mode.</summary>
    public class ControlSettingsTests
    {
        const string TestKey = "test.controls.settings";
        const string TestLegacyKey = "test.controls.steerMode";

        [SetUp] public void SetUp() { PlayerPrefs.DeleteKey(TestKey); PlayerPrefs.DeleteKey(TestLegacyKey); }
        [TearDown] public void TearDown() { PlayerPrefs.DeleteKey(TestKey); PlayerPrefs.DeleteKey(TestLegacyKey); }

        static ControlSettings Custom() => new ControlSettings
        {
            wheelRangeDeg = 540f, wheelSensitivity = 1.4f, centreStrength = 0.6f, wheelDeadZone = 0.04f,
            gyroEnabled = true, gyroInvert = true, gyroSensitivity = 1.5f, throttleProgressive = false, brakeProgressive = true,
        };

        [Test]
        public void Defaults_MatchStage2Behaviour()
        {
            var d = ControlSettings.Defaults();
            Assert.AreEqual(270f, d.wheelRangeDeg);
            Assert.AreEqual(1f, d.wheelSensitivity);
            Assert.AreEqual(1f, d.centreStrength);
            Assert.IsFalse(d.gyroEnabled);
            Assert.IsFalse(d.gyroInvert);
            Assert.AreEqual(1.6f, d.ThrottleExponent, 1e-6f);
            Assert.AreEqual(1.4f, d.BrakeExponent, 1e-6f);
            Assert.AreEqual(35f, d.GyroMaxTiltDeg, 1e-4f);
        }

        [Test]
        public void SaveThenLoad_RoundTripsEveryField()
        {
            var s = Custom();
            s.Save(TestKey);
            var l = ControlSettings.Load(TestKey, TestLegacyKey);
            Assert.AreEqual(s.ToJson(), l.ToJson());
            Assert.AreEqual(540f, l.wheelRangeDeg);
            Assert.AreEqual(1.4f, l.wheelSensitivity, 1e-5f);
            Assert.AreEqual(0.6f, l.centreStrength, 1e-5f);
            Assert.AreEqual(0.04f, l.wheelDeadZone, 1e-5f);
            Assert.IsTrue(l.gyroEnabled); Assert.IsTrue(l.gyroInvert);
            Assert.AreEqual(1.5f, l.gyroSensitivity, 1e-5f);
            Assert.IsFalse(l.throttleProgressive); Assert.IsTrue(l.brakeProgressive);
        }

        [Test]
        public void Load_NothingSaved_GivesDefaults()
        {
            Assert.AreEqual(ControlSettings.Defaults().ToJson(), ControlSettings.Load(TestKey, TestLegacyKey).ToJson());
        }

        [Test]
        public void ResetToDefaults_RestoresEverything()
        {
            var s = Custom();
            s.ResetToDefaults();
            Assert.AreEqual(ControlSettings.Defaults().ToJson(), s.ToJson());
        }

        [Test]
        public void Load_ClampsOutOfRangeAndNaN()
        {
            var s = ControlSettings.FromJson("{\"schema\":1,\"wheelRangeDeg\":5000,\"wheelSensitivity\":-3,\"centreStrength\":99,\"wheelDeadZone\":0.9,\"gyroSensitivity\":0}");
            Assert.AreEqual(ControlSettings.RangeMax, s.wheelRangeDeg);
            Assert.AreEqual(ControlSettings.GainMin, s.wheelSensitivity);
            Assert.AreEqual(ControlSettings.CentreMax, s.centreStrength);
            Assert.AreEqual(ControlSettings.DeadMax, s.wheelDeadZone);
            Assert.AreEqual(ControlSettings.GainMin, s.gyroSensitivity);
            var n = new ControlSettings { wheelSensitivity = float.NaN, wheelRangeDeg = float.PositiveInfinity };
            n.Clamp();
            Assert.AreEqual(1f, n.wheelSensitivity);
            Assert.AreEqual(270f, n.wheelRangeDeg);
        }

        [Test]
        public void Load_CorruptJson_GivesDefaults()
        {
            PlayerPrefs.SetString(TestKey, "{not json");
            Assert.AreEqual(ControlSettings.Defaults().ToJson(), ControlSettings.Load(TestKey, TestLegacyKey).ToJson());
        }

        [Test]
        public void Migration_LegacySteerModeKey_Wheel900AndGyro()
        {
            PlayerPrefs.SetInt(TestLegacyKey, 1);
            var a = ControlSettings.Load(TestKey, TestLegacyKey);
            Assert.AreEqual(900f, a.wheelRangeDeg); Assert.IsFalse(a.gyroEnabled);
            PlayerPrefs.SetInt(TestLegacyKey, 2);
            var b = ControlSettings.Load(TestKey, TestLegacyKey);
            Assert.IsTrue(b.gyroEnabled); Assert.AreEqual(270f, b.wheelRangeDeg);
            PlayerPrefs.SetInt(TestLegacyKey, 0);
            Assert.AreEqual(270f, ControlSettings.Load(TestKey, TestLegacyKey).wheelRangeDeg);
        }

        [Test]
        public void Migration_NewSaveWinsOverLegacyKey()
        {
            PlayerPrefs.SetInt(TestLegacyKey, 2);
            new ControlSettings { wheelRangeDeg = 450f }.Save(TestKey);
            var l = ControlSettings.Load(TestKey, TestLegacyKey);
            Assert.AreEqual(450f, l.wheelRangeDeg); Assert.IsFalse(l.gyroEnabled);
        }

        [Test]
        public void Migration_SchemaLessAndFutureJson_KeepKnownFields()
        {
            var old = ControlSettings.FromJson("{\"wheelRangeDeg\":360,\"gyroInvert\":true}");   // no schema field
            Assert.AreEqual(ControlSettings.CurrentSchema, old.schema);
            Assert.AreEqual(360f, old.wheelRangeDeg); Assert.IsTrue(old.gyroInvert);
            Assert.AreEqual(1f, old.wheelSensitivity, "missing field keeps its default");
            var future = ControlSettings.FromJson("{\"schema\":7,\"wheelRangeDeg\":630,\"somethingNew\":1}");
            Assert.AreEqual(ControlSettings.CurrentSchema, future.schema);
            Assert.AreEqual(630f, future.wheelRangeDeg);
        }

        [Test]
        public void Migration_V1Json_GainsCameraDefaultsAndKeepsOwnerChoices()
        {
            // A save written by a Stage 3 build (schema 1, no camera fields).
            var v1 = ControlSettings.FromJson("{\"schema\":1,\"wheelRangeDeg\":540,\"gyroEnabled\":true,\"throttleProgressive\":false}");
            Assert.AreEqual(2, v1.schema);
            Assert.AreEqual(540f, v1.wheelRangeDeg); Assert.IsTrue(v1.gyroEnabled); Assert.IsFalse(v1.throttleProgressive);
            Assert.AreEqual(1f, v1.lookSensitivity); Assert.AreEqual(55f, v1.cabFov); Assert.IsTrue(v1.headMotion);
        }

        [Test]
        public void CameraSettings_AreClampedAndRoundTrip()
        {
            var s = ControlSettings.FromJson("{\"schema\":2,\"lookSensitivity\":9,\"cabFov\":5,\"headMotion\":false}");
            Assert.AreEqual(ControlSettings.LookMax, s.lookSensitivity); Assert.AreEqual(ControlSettings.FovMin, s.cabFov); Assert.IsFalse(s.headMotion);
            var back = ControlSettings.FromJson(s.ToJson());
            Assert.AreEqual(s.ToJson(), back.ToJson());
        }

        [Test]
        public void LogLine_ContainsAllChoices()
        {
            string l = Custom().LogLine("saved");
            StringAssert.StartsWith("[CONTROLS] saved v2", l);
            foreach (string part in new[] { "steer=gyro", "wheelRange=540", "wheelSens=1.40", "centre=0.60", "deadZone=0.040", "gyroInvert=on", "gyroSens=1.50", "throttle=linear", "brake=progressive", "lookSens=1.00", "cabFov=55", "headMotion=on" })
                StringAssert.Contains(part, l);
        }

        [Test]
        public void ApplyTo_PushesValuesIntoInputSources()
        {
            var wheel = new TouchSteeringWheel(); var gyro = new GyroSteering(); var touch = new TouchControls();
            wheel.SetWheelDeg(200f);
            var s = Custom(); s.wheelRangeDeg = 180f; s.ApplyTo(wheel, gyro, touch);
            Assert.AreEqual(180f, wheel.HalfRangeDeg); Assert.AreEqual(180f, wheel.WheelDeg, 1e-4f, "re-clamped to the shorter range");
            Assert.AreEqual(1.4f, wheel.Sensitivity, 1e-5f); Assert.AreEqual(0.6f, wheel.CentreStrength, 1e-5f); Assert.AreEqual(0.04f, wheel.DeadZone, 1e-5f);
            Assert.IsFalse(wheel.Enabled); Assert.IsTrue(gyro.Enabled); Assert.IsTrue(gyro.Invert);
            Assert.AreEqual(35f / 1.5f, gyro.MaxTiltDeg, 1e-4f);
            Assert.AreEqual(1f, touch.ThrottleExponent); Assert.AreEqual(1.4f, touch.BrakeExponent, 1e-6f);
        }

        // ---------------------------------------------------------------- steering direction in all modes

        static float WheelRight(ControlSettings s)
        {
            var wheel = new TouchSteeringWheel(); s.ApplyTo(wheel, null, null);
            wheel.PointerDown(new Vector2(0, 100));
            for (int i = 1; i <= 6; i++) { float a = i * 10f * Mathf.Deg2Rad; wheel.PointerDrag(new Vector2(Mathf.Sin(a), Mathf.Cos(a)) * 100f); }   // clockwise 60 deg
            var it = new DriverIntent();
            for (int i = 0; i < 20; i++) wheel.Sample(0.02f, new VehicleFeedback(), ref it);
            return it.Steer;
        }

        [Test]
        public void Direction_ClockwiseWheel_IsPositive_InWheel270And900()
        {
            foreach (float range in new[] { 270f, 900f })
                Assert.Greater(WheelRight(new ControlSettings { wheelRangeDeg = range, wheelSensitivity = 1.2f }), 0.02f, "range " + range);
        }

        [Test]
        public void Direction_WheelSensitivityAndRange_ScaleOutput()
        {
            float basic = WheelRight(new ControlSettings { wheelRangeDeg = 270f });
            Assert.AreEqual(60f / 270f, basic, 0.01f);
            Assert.Greater(WheelRight(new ControlSettings { wheelRangeDeg = 270f, wheelSensitivity = 2f }), basic * 1.9f);
            Assert.Less(WheelRight(new ControlSettings { wheelRangeDeg = 900f }), basic * 0.4f);
        }

        [Test]
        public void Direction_Gyro_RightTiltIsPositive_InvertFlips()
        {
            var s = new ControlSettings { gyroEnabled = true };
            Assert.Greater(GyroMath.SteerFromTilt(15f, s.GyroMaxTiltDeg, 1f, s.gyroInvert), 0.2f);
            s.gyroInvert = true;
            Assert.Less(GyroMath.SteerFromTilt(15f, s.GyroMaxTiltDeg, 1f, s.gyroInvert), -0.2f);
            Assert.Greater(GyroMath.SteerFromTilt(-15f, s.GyroMaxTiltDeg, 1f, s.gyroInvert), 0.2f);
            // Sensitivity 2 = half the tilt for the same output.
            var hi = new ControlSettings { gyroSensitivity = 2f };
            Assert.Greater(GyroMath.SteerFromTilt(15f, hi.GyroMaxTiltDeg, 1f, false), GyroMath.SteerFromTilt(15f, 35f, 1f, false) * 1.9f);
        }

        [Test]
        public void CentreStrength_ZeroKeepsWheel_TwoCentresFaster()
        {
            float Deg(float centre)
            {
                var w = new TouchSteeringWheel { CentreStrength = centre };
                w.SetWheelDeg(200f);
                var it = new DriverIntent();
                for (int i = 0; i < 10; i++) w.Sample(0.02f, new VehicleFeedback { ForwardSpeed = 10f, AligningTorque = 400f }, ref it);
                return w.WheelDeg;
            }
            Assert.AreEqual(200f, Deg(0f), 1e-3f);
            Assert.Less(Deg(2f), Deg(1f));
            Assert.Less(Deg(1f), 200f);
        }

        [Test]
        public void PedalCurves_LinearVsProgressive()
        {
            var s = new ControlSettings { throttleProgressive = false, brakeProgressive = true };
            var touch = new TouchControls { ThrottleRaw = 0.5f, BrakeRaw = 0.5f };
            s.ApplyTo(null, null, touch);
            var it = new DriverIntent();
            touch.Sample(0.02f, new VehicleFeedback(), ref it);
            Assert.AreEqual(0.5f, it.Throttle, 1e-6f, "linear");
            Assert.Less(it.Brake, 0.4f, "progressive: gentle at half travel");
            Assert.AreEqual(1f, TouchControls.Shape(1f, s.BrakeExponent), 1e-6f);
        }

        [Test]
        public void DeadZone_SettingSuppressesSmallInput()
        {
            var w = new TouchSteeringWheel(); new ControlSettings { wheelDeadZone = 0.1f }.ApplyTo(w, null, null);
            w.SetWheelDeg(20f);   // 0.074 of 270
            var it = new DriverIntent();
            for (int i = 0; i < 30; i++) w.Sample(0.02f, new VehicleFeedback(), ref it);
            Assert.AreEqual(0f, it.Steer, 1e-4f);
        }
    }
}
