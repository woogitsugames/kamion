using System.Collections.Generic;
using Game.Controls;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// PC wheel data (ADR 0263) through Unity's JsonUtility: the shipped profiles parse and are sane, player settings
    /// round-trip, migrate and clamp. Needs Unity (JsonUtility, Resources) — runs only in the EditMode runner.
    /// </summary>
    public class PcWheelDataTests
    {
        [Test]
        public void ShippedProfiles_ParseUniqueIdsGenericAndSteerAxis()
        {
            var text = Resources.Load<TextAsset>(WheelProfiles.ResourcePath);
            Assert.IsNotNull(text, "Resources/Controls/wheel_profiles.json");
            var set = WheelProfiles.FromJson(text.text);
            Assert.AreEqual(WheelProfileSet.CurrentSchema, set.schema);
            Assert.GreaterOrEqual(set.profiles.Length, 7);
            Assert.IsNotNull(set.ById("generic"));
            var ids = new HashSet<string>();
            foreach (var p in set.profiles)
            {
                Assert.IsTrue(ids.Add(p.id), "duplicate id " + p.id);
                Assert.IsTrue(p.steer.Present, p.id + ": steering axis");
                Assert.That(p.defaultRangeDeg, Is.InRange(WheelSteeringMap.RangeMinDeg, WheelSteeringMap.RangeMaxDeg), p.id);
                Assert.IsFalse(string.IsNullOrEmpty(p.status), p.id + ": status (UNVERIFIED/SOURCED/VERIFIED)");
                foreach (var b in p.buttons) Assert.AreNotEqual(WheelAction.None, b.Parse(), p.id + ": unknown action " + b.action);
            }
        }

        [Test]
        public void ShippedProfiles_MatchSourcedIds()
        {
            var set = WheelProfiles.LoadDefault();
            Assert.AreEqual("lg-g29", set.Find(0x046d, 0xc24f, "").id);    // hid-ids.h
            Assert.AreEqual("lg-g920", set.Find(0x046d, 0xc262, "").id);
            Assert.AreEqual("tm-t300", set.Find(0x044f, 0xb66e, "").id);   // hid-tmff2
            Assert.AreEqual("ft-csl", set.Find(0x0eb7, 0x0020, "").id);    // hid-fanatecff
            Assert.AreEqual("generic", set.Find(0x1234, 0x5678, "Unknown wheel").id);
        }

        [Test]
        public void CorruptProfiles_StillGiveGeneric()
        {
            Assert.IsNotNull(WheelProfiles.FromJson("{not json").ById("generic"));
            Assert.IsNotNull(WheelProfiles.FromJson("").ById("generic"));
        }

        [Test]
        public void Settings_RoundTripAndClamp()
        {
            var s = WheelSettings.Defaults();
            s.rangeDeg = 720f; s.mapping = WheelSteerMapping.OneToOne; s.forceFeedbackEnabled = false; s.forceFeedback.gain = 1.5f;
            s.SetCalibration(new WheelCalibrationRecord { profileId = "lg-g29", hasBrake = true, brake = AxisCalibration.Pedal(1f, -1f, 0.04f, 0.02f), deviceRangeDeg = 900f });
            var r = WheelSettings.FromJson(s.ToJson());
            Assert.AreEqual(720f, r.rangeDeg);
            Assert.AreEqual(WheelSteerMapping.OneToOne, r.mapping);
            Assert.IsFalse(r.forceFeedbackEnabled);
            Assert.AreEqual(1.5f, r.forceFeedback.gain, 1e-5f);
            var c = r.CalibrationFor("lg-g29");
            Assert.IsNotNull(c);
            Assert.IsTrue(c.hasBrake);
            Assert.AreEqual(1f, c.brake.rawMin);
            Assert.AreEqual(0.04f, c.brake.deadZoneLow, 1e-5f);

            var bad = WheelSettings.FromJson("{\"schema\":1,\"rangeDeg\":5000,\"mapping\":7}");
            Assert.AreEqual(900f, bad.rangeDeg);
            Assert.AreEqual(WheelSteerMapping.ScaledToLock, bad.mapping);
        }

        [Test]
        public void Settings_MigrateFromNoSchemaAndFromNewer()
        {
            var v0 = WheelSettings.FromJson("{\"rangeDeg\":540}");
            Assert.AreEqual(WheelSettings.CurrentSchema, v0.schema);
            Assert.AreEqual(540f, v0.rangeDeg);
            Assert.IsTrue(v0.forceFeedbackEnabled, "missing field keeps its default");
            var future = WheelSettings.FromJson("{\"schema\":99,\"rangeDeg\":450,\"unknownField\":3}");
            Assert.AreEqual(WheelSettings.CurrentSchema, future.schema);
            Assert.AreEqual(450f, future.rangeDeg);
            Assert.IsNotNull(WheelSettings.FromJson("garbage{"));
        }

        /// <summary>The per-step path (shifter, edges, axis maths, force feedback, mixer) must not allocate (CLAUDE.md).</summary>
        [Test]
        public void PerStepPath_DoesNotAllocate()
        {
            var ffb = new ForceFeedbackModel(ForceFeedbackSettings.Defaults());
            var sink = new RecordingForceFeedbackSink(64);
            var shifter = new HShifterMapper();
            var edges = new ButtonEdges(4);
            var gates = new bool[6];
            var cal = AxisCalibration.Steering(-1f, 0f, 1f, 0.02f);
            var pedal = AxisCalibration.Pedal(1f, -1f, 0.03f, 0.02f);
            var auto = AutoPedal.Create(1f);
            var mixer = new DriverInputMixer();
            var fb = new VehicleFeedback { HandwheelLockDeg = 800f };
            int frame = 0;
            void Frame()
            {
                frame++;
                float raw = (frame % 200) / 100f - 1f;
                var it = new DriverIntent();
                it.ClearCommands();
                gates[frame % 6] = (frame / 10) % 2 == 0;
                shifter.Update(0.01f, HShifterMapper.Slot(gates, 6, false), (frame / 50) % 2 == 0, ref it);
                edges.Pressed(frame % 4, frame % 3 == 0);
                float dev = WheelSteeringMap.DeviceDeg(WheelAxisMath.Steer(raw, cal), 900f);
                it.Steer = WheelSteeringMap.Command(dev, 540f, 800f, WheelSteerMapping.ScaledToLock);
                it.Throttle = WheelAxisMath.Pedal(raw, pedal) + auto.Value(raw, 0.03f, 0.02f) * 0f;
                var inp = new ForceFeedbackInputs
                {
                    Active = frame % 97 != 0, ForwardSpeed = 15f, AligningTorqueNm = -600f * it.Steer, SteeringRatio = 20f,
                    CabPerDeviceDeg = WheelSteeringMap.CabPerDeviceDeg(540f, 800f, WheelSteerMapping.ScaledToLock),
                    DeviceRateDegS = raw * 90f, PastSoftLockDeg = WheelSteeringMap.PastSoftLockDeg(dev, 540f, 800f, WheelSteerMapping.ScaledToLock),
                    SteeredLoadLeftN = 30000f, SteeredLoadRightN = 30000f + raw * 1000f,
                };
                ffb.Step(0.01f, inp, sink);
                mixer.Sample(0.01f, fb);
            }
            GcAllocCounter.AssertZero(() => { for (int i = 0; i < 300; i++) Frame(); }, warmup: () => { for (int i = 0; i < 10; i++) Frame(); },
                message: "PC wheel per-step path allocated");
        }

        [Test]
        public void Settings_SetCalibrationReplacesSameProfile()
        {
            var s = WheelSettings.Defaults();
            s.SetCalibration(new WheelCalibrationRecord { profileId = "a", hasSteer = true });
            s.SetCalibration(new WheelCalibrationRecord { profileId = "a", hasThrottle = true });
            s.SetCalibration(new WheelCalibrationRecord { profileId = "b" });
            Assert.AreEqual(2, s.calibrations.Length);
            Assert.IsTrue(s.CalibrationFor("a").hasThrottle);
            Assert.IsFalse(s.CalibrationFor("a").hasSteer);
        }
    }
}
