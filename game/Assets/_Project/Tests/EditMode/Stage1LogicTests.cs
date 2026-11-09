using Game.Controls;
using Game.Telemetry;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    public class Stage1LogicTests
    {
        [Test]
        public void Inertia_Diagonalize_Reconstructs()
        {
            var m = default(Mat3);
            m.m00 = 9000; m.m11 = 30000; m.m22 = 26000; m.m12 = m.m21 = 4200; m.m01 = m.m10 = -300; m.m02 = m.m20 = 150;
            InertiaUtil.Diagonalize(m, out Vector3 d, out Quaternion q);
            // R diag Rᵀ applied to basis vectors must reproduce M.
            for (int c = 0; c < 3; c++)
            {
                var e = Vector3.zero; e[c] = 1f;
                Vector3 local = Quaternion.Inverse(q) * e;
                Vector3 r = q * new Vector3(d.x * local.x, d.y * local.y, d.z * local.z);
                Vector3 expected = new Vector3((float)(c == 0 ? m.m00 : c == 1 ? m.m10 : m.m20), (float)(c == 0 ? m.m01 : c == 1 ? m.m11 : m.m21), (float)(c == 0 ? m.m02 : c == 1 ? m.m12 : m.m22));
                Assert.That((r - expected).magnitude, Is.LessThan(1f), $"column {c}: {r} vs {expected}");
            }
        }

        [Test]
        public void VehicleData_DefaultAsset_Parses()
        {
            var model = VehicleDataAsset.LoadDefault().CreateModel();
            Assert.AreEqual(4, model.Wheels.Length);
            Assert.Greater(model.MassProps.Mass, 5000);
        }

        [Test]
        public void TractorDimensions_InSyncWith_DimsJson()
        {
            Assert.DoesNotThrow(() => Game.Editor.Setup.DrivingLabSceneBuilder.ReadAndCheckDims());
            var d = new TractorDimensions();
            Assert.AreEqual(new Vector3(-0.55f, 2.50f, 4.15f), d.EyePointVehicle);
        }

        [Test]
        public void Steering_DeadZone_And_Curve()
        {
            Assert.AreEqual(0f, SteeringMath.DeadZone(0.005f, 0.01f));
            Assert.AreEqual(1f, SteeringMath.DeadZone(1f, 0.01f), 1e-5f);
            Assert.Less(SteeringMath.DeadZone(0.02f, 0.01f), 0.02f);
            Assert.AreEqual(-0.5f, SteeringMath.Curve(-0.5f, 0f), 1e-6f);
            Assert.AreEqual(90f, SteeringMath.ClockwiseAngleFromUp(new Vector2(1, 0)), 1e-3f);
        }

        [Test]
        public void TouchWheel_HandOverHand_AndSelfCentre()
        {
            var w = new TouchSteeringWheel { HalfRangeDeg = 900f };
            w.PointerDown(new Vector2(0, 100));
            // Two full clockwise turns in 30° increments.
            for (int i = 1; i <= 24; i++) { float a = i * 30f * Mathf.Deg2Rad; w.PointerDrag(new Vector2(Mathf.Sin(a), Mathf.Cos(a)) * 100f); }
            Assert.AreEqual(720f, w.WheelDeg, 0.5f);
            w.PointerUp();
            var it = new DriverIntent();
            w.Sample(0.1f, new VehicleFeedback { ForwardSpeed = 0f }, ref it);
            Assert.AreEqual(720f, w.WheelDeg, 0.01f, "no self-centre at standstill");
            for (int i = 0; i < 100; i++) w.Sample(0.05f, new VehicleFeedback { ForwardSpeed = 10f, AligningTorque = 500f }, ref it);
            Assert.AreEqual(0f, w.WheelDeg, 0.01f, "returns to centre when moving");
            Assert.Greater(TouchSteeringWheel.SelfCentreRate(10f, 800f, 540f, 8f, 800f), TouchSteeringWheel.SelfCentreRate(3f, 100f, 540f, 8f, 800f));
        }

        [Test]
        public void Gyro_SignAndCalibration_BothSensorConventions()
        {
            var tiltRight = new Vector3(Mathf.Sin(0.2f), -Mathf.Cos(0.2f), 0f);
            var level = new Vector3(0f, -1f, 0f);
            float rel = GyroMath.Relative(GyroMath.TiltAngleDeg(tiltRight), GyroMath.TiltAngleDeg(level));
            float relReaction = GyroMath.Relative(GyroMath.TiltAngleDeg(-tiltRight), GyroMath.TiltAngleDeg(-level));
            Assert.AreEqual(0.2f * Mathf.Rad2Deg, rel, 1e-3f);
            Assert.AreEqual(rel, relReaction, 1e-3f, "gravity vs reaction convention after calibration");
            Assert.AreEqual(1f, GyroMath.SteerFromTilt(60f, 35f, 1f));
            // DeviceToScreen: landscape-left device tilted right still gives a positive angle on screen.
            var dev = new Vector3(-Mathf.Cos(0.2f), -Mathf.Sin(0.2f), 0f); // portrait-frame vector equivalent
            var scr = GyroMath.DeviceToScreen(dev, ScreenOrientation.LandscapeLeft);
            Assert.AreEqual(new Vector3(Mathf.Sin(0.2f), -Mathf.Cos(0.2f), 0f).x, scr.x, 1e-5f);
        }

        [Test]
        public void OneEuro_SmoothsJitter_TracksSteps()
        {
            var f = new OneEuroFilter(1f, 0.02f, 1f);
            float maxDev = 0f;
            var rng = new System.Random(1);
            for (int i = 0; i < 200; i++) { float v = f.Filter(10f + (float)(rng.NextDouble() - 0.5), 0.016f); if (i > 100) maxDev = Mathf.Max(maxDev, Mathf.Abs(v - 10f)); }
            Assert.Less(maxDev, 0.25f, "jitter ±0.5 attenuated");
            for (int i = 0; i < 60; i++) f.Filter(40f, 0.016f);
            Assert.AreEqual(40f, f.Value, 1f, "follows a step within ~1 s");
        }

        [Test]
        public void Mixer_SteerPriority_PedalMax_CommandsMerged()
        {
            var mixer = new DriverInputMixer();
            var kb = new KeyboardDriverInput { Enabled = false };
            var wheel = new TouchSteeringWheel();
            var touch = new TouchControls { ThrottleRaw = 0.5f };
            mixer.Add(kb); mixer.Add(wheel); mixer.Add(touch);
            wheel.SetWheelDeg(135f);
            touch.RequestParkingToggle();
            var r = mixer.Sample(1f, default);
            Assert.Greater(r.Steer, 0.4f);
            Assert.AreEqual("koło", mixer.SteeringSource);
            Assert.AreEqual(TouchControls.Shape(0.5f, touch.ThrottleExponent), r.Throttle, 1e-6f);
            Assert.IsTrue(r.ToggleParkingBrake);
            Assert.IsFalse(mixer.Sample(1f, default).ToggleParkingBrake, "one-shot");
        }

        [Test]
        public void Csv_FixedFormatter()
        {
            var buf = new char[64];
            string F(double v, int d) => new string(buf, 0, CsvRecorder.AppendFixed(buf, 0, v, d));
            Assert.AreEqual("1.05", F(1.05, 4));
            Assert.AreEqual("-12.5", F(-12.5, 3));
            Assert.AreEqual("0", F(-0.00001, 3));
            Assert.AreEqual("30000", F(30000.0, 2));
            Assert.AreEqual("0.0001", F(0.0001, 4));
        }
    }
}
