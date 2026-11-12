using System;
using System.Globalization;
using System.IO;
using System.Text;
using Game.Controls;
using Game.Vehicle.Physics;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0058: the cab steering wheel as a heavy wheel turned by hands. Rate / acceleration limits, speed-dependent
    /// mapping, self-centring times, gyro dead zone, direction through the whole chain, visual = simulated angle, and
    /// the before/after evidence CSV (written when KAMION_STEER_EVIDENCE_DIR is set).
    /// </summary>
    public class SteeringFeelTests
    {
        const float Dt = 0.01f;   // project fixed step
        const float Lock = 800f;  // 40 deg x 20:1 (tractor_4x2_generic.vehicle.json)

        static Steering PhysicsSteering() => new Steering(new SteeringDefinition { maxRoadWheelAngleDeg = 40, maxSteerRateDegS = 30, steeringRatio = 20 });

        static Vector2 Finger(float clockwiseDeg, float r = 150f)
        {
            float a = clockwiseDeg * Mathf.Deg2Rad;
            return new Vector2(Mathf.Sin(a), Mathf.Cos(a)) * r;
        }

        /// <summary>Turns the on-screen wheel to an absolute angle in 10-degree finger moves (hand-over-hand).</summary>
        static void TurnTo(TouchSteeringWheel w, float deg)
        {
            float cur = w.WheelDeg;
            int n = Mathf.Max(1, Mathf.CeilToInt(Mathf.Abs(deg - cur) / 10f));
            for (int i = 1; i <= n; i++) w.PointerDrag(Finger(cur + (deg - cur) * i / n));
        }

        // ---------------------------------------------------------------- column dynamics

        [Test]
        public void StepInput_WheelRateAndAccelerationLimited_NoOvershoot()
        {
            var feel = SteeringFeel.Defaults();
            var c = new SteeringColumn(feel, Lock);
            float maxRate = 0f, maxAcc = 0f, prevRate = 0f, maxAngle = 0f;
            for (int i = 0; i < 400; i++)
            {
                c.Step(Dt, Lock, true, 0f, 0f);
                maxRate = Mathf.Max(maxRate, Mathf.Abs(c.RateDegS));
                maxAcc = Mathf.Max(maxAcc, Mathf.Abs(c.RateDegS - prevRate) / Dt);
                maxAngle = Mathf.Max(maxAngle, c.AngleDeg);
                prevRate = c.RateDegS;
            }
            Debug.Log($"[TEST] step to lock at 0 km/h: max rate {maxRate:F0} deg/s, max accel {maxAcc:F0} deg/s2");
            Assert.LessOrEqual(maxRate, feel.HandRate(0f) + 1e-3f, "hand rate limit (720 deg/s when manoeuvring, ADR 0135)");
            Assert.Greater(maxRate, 0.95f * feel.HandRate(0f), "uses the quick hand speed for a full swipe");
            Assert.LessOrEqual(maxAcc, 2f * feel.HandRate(0f) / feel.rateRiseTimeS + 1f, "no instant snap (acceleration limited)");
            Assert.AreEqual(Lock, c.AngleDeg, 0.01f, "reaches the target");
            Assert.LessOrEqual(maxAngle, Lock + 1e-3f, "no overshoot");

            // Full lock-to-lock takes a realistic time (~4.4 turns at 2 rev/s palm-spinning, ADR 0135; was 2.9-3.6 s at 540 deg/s).
            int steps = 0;
            c.SnapTo(-Lock);
            while (c.AngleDeg < Lock - 0.5f && steps < 1000) { c.Step(Dt, Lock, true, 0f, 0f); steps++; }
            Assert.That(steps * Dt, Is.InRange(2.1f, 2.7f), "lock to lock at standstill");
        }

        [Test]
        public void SmallFingerMotion_TrackingLag_Below80ms()
        {
            var c = new SteeringColumn(null, Lock);
            int steps = 0;
            while (c.AngleDeg < 10f * 0.632f && steps < 100) { c.Step(Dt, 10f, true, 50f, 0f); steps++; }
            Debug.Log($"[TEST] 10 deg step at 50 km/h: 63 % after {steps * Dt * 1000f:F0} ms");
            Assert.LessOrEqual(steps * Dt, 0.08f + 1e-4f);
        }

        [Test]
        public void HandRate_FallsWithSpeed()
        {
            var f = SteeringFeel.Defaults();
            Assert.AreEqual(720f, f.HandRate(0f), 1e-3f);
            Assert.AreEqual(130f, f.HandRate(80f), 1e-3f);
            Assert.AreEqual(110f, f.HandRate(150f), 1e-3f);
            for (float v = 0f; v < 120f; v += 5f) Assert.GreaterOrEqual(f.HandRate(v), f.HandRate(v + 5f), "monotonic at " + v);
        }

        [Test]
        public void At80kmh_FullFingerSwipe_RoadWheelRate_AtMost7DegPerS()
        {
            var wheel = new TouchSteeringWheel();   // defaults: comfort 270, speed-sensitive
            var col = new SteeringColumn(null, Lock);
            var st = PhysicsSteering();
            var fb = new VehicleFeedback { ForwardSpeed = 80f / 3.6f, HandwheelLockDeg = Lock };
            wheel.PointerDown(Finger(0f));
            float maxRoadRate = 0f, prevRoad = 0f, t = 0f;
            for (int i = 0; i < 300; i++, t += Dt)
            {
                if (t < 0.1f) TurnTo(wheel, 270f * (t + Dt) / 0.1f);   // whole on-screen range in 0.1 s
                var it = new DriverIntent();
                wheel.Sample(Dt, fb, ref it);
                col.Step(Dt, it.Steer * Lock, it.HandsOn, 80f, 0f);
                st.Update(col.Normalized, Dt);
                float road = (float)(st.Angle * MathUtil.Rad2Deg);
                maxRoadRate = Mathf.Max(maxRoadRate, Mathf.Abs(road - prevRoad) / Dt);
                prevRoad = road;
            }
            Debug.Log($"[TEST] 80 km/h full swipe: max road-wheel rate {maxRoadRate:F1} deg/s, road wheel after 3 s {prevRoad:F1} deg, cab wheel {col.AngleDeg:F0} deg");
            Assert.AreEqual(270f, wheel.WheelDeg, 0.5f, "on-screen wheel follows the finger 1:1");
            Assert.LessOrEqual(maxRoadRate, 7f, "road-wheel rate at 80 km/h (v2 pipeline: 30 deg/s)");
            Assert.AreEqual(270f, col.AngleDeg, 1f, "at speed one on-screen degree = one cab-wheel degree");
            Assert.AreEqual(270f / 20f, prevRoad, 0.2f, "road wheel = cab wheel / ratio");
        }

        [Test]
        public void SpeedSensitiveGain_ComfortFadesToOneToOne_SimStaysOne()
        {
            var f = SteeringFeel.Defaults();
            Assert.AreEqual(1f, f.WheelGain(0f, 270f, Lock), 1e-5f);
            Assert.AreEqual(1f, f.WheelGain(20f, 270f, Lock), 1e-5f);
            Assert.AreEqual(270f / Lock, f.WheelGain(60f, 270f, Lock), 1e-5f);
            Assert.AreEqual(270f / Lock, f.WheelGain(100f, 270f, Lock), 1e-5f);
            Assert.AreEqual(1f, f.WheelGain(80f, 900f, Lock), 1e-5f, "simulator range is already ~1:1");
            Assert.AreEqual(0.3f, f.GyroGain(80f), 1e-5f);
            Assert.AreEqual(1f, f.GyroGain(5f), 1e-5f);
        }

        [Test]
        public void FollowColumn_InvertsTarget_NoJumpOnRegrab()
        {
            var w = new TouchSteeringWheel { DeadZone = 0.05f, Sensitivity = 1.3f };
            var fb = new VehicleFeedback { ForwardSpeed = 40f / 3.6f, HandwheelLockDeg = Lock };
            w.SetWheelDeg(123f);
            var it = new DriverIntent();
            w.Sample(Dt, fb, ref it);
            float target = it.Steer;
            w.FollowColumn(target);
            Assert.AreEqual(123f, w.WheelDeg, 0.05f);
            w.Sample(Dt, fb, ref it);
            Assert.AreEqual(target, it.Steer, 1e-4f);
            w.PointerDown(Finger(0f));
            w.FollowColumn(0f);
            Assert.AreEqual(123f, w.WheelDeg, 0.05f, "held: the finger owns the on-screen wheel");
        }

        // ---------------------------------------------------------------- self-centring

        static float ReturnTime(float fromDeg, float kmh, float mz, float toDeg = 5f, float strength = 1f)
        {
            var c = new SteeringColumn(null, Lock) { CentreStrength = strength };
            c.SnapTo(fromDeg);
            int steps = 0;
            while (Mathf.Abs(c.AngleDeg) > toDeg && steps < 2000) { c.Step(Dt, 0f, false, kmh, mz); steps++; }
            return steps * Dt;
        }

        [Test]
        public void SelfCentre_RealisticTimes_NoneAtStandstill()
        {
            float city = ReturnTime(270f, 30f, 800f);
            float slow = ReturnTime(270f, 10f, 200f);
            float motorway = ReturnTime(60f, 80f, 800f, 2f);
            Debug.Log($"[TEST] self-centre: 270 deg at 30 km/h {city:F2} s, at 10 km/h {slow:F2} s; 60 deg at 80 km/h {motorway:F2} s");
            Assert.That(city, Is.InRange(0.9f, 2.0f), "after a city corner the wheel runs back in ~1-2 s");
            Assert.Greater(slow, city, "slower return at walking pace");
            Assert.Less(slow, 4f);
            Assert.That(motorway, Is.InRange(0.5f, 1.5f));
            Assert.AreEqual(20f, ReturnTime(270f, 0f, 0f) , 1e-3f, "no return at standstill (timeout)");
            Assert.AreEqual(20f, ReturnTime(270f, 30f, 800f, 5f, 0f), 1e-3f, "centring strength 0 = stays");
        }

        [Test]
        public void SelfCentre_NoOvershootPastCentre()
        {
            var c = new SteeringColumn(null, Lock);
            c.SnapTo(-400f);
            float max = -1e9f;
            for (int i = 0; i < 500; i++) { c.Step(Dt, 0f, false, 60f, 1500f); max = Mathf.Max(max, c.AngleDeg); }
            Assert.LessOrEqual(max, 1e-4f);
            Assert.AreEqual(0f, c.AngleDeg, 1e-3f);
        }

        // ---------------------------------------------------------------- gyro

        [Test]
        public void Gyro_DeadZone_Smoothed_AndRateLimitedThroughColumn()
        {
            Assert.AreEqual(0f, GyroMath.SteerFromTilt(0.8f, 35f, 1f), 1e-6f, "inside the 1 deg dead zone");
            Assert.AreEqual(0f, GyroMath.SteerFromTilt(-1f, 35f, 1f), 1e-6f);
            float justOut = GyroMath.SteerFromTilt(1.5f, 35f, 1f);
            Assert.That(justOut, Is.InRange(1e-4f, 0.02f), "no jump at the dead-zone edge");

            // A sudden 20 deg tilt at 80 km/h: target = 20/35 of lock x 0.3 at speed; the wheel ramps at the hand rate.
            var f = SteeringFeel.Defaults();
            float target = GyroMath.SteerFromTilt(20f, 35f, 1f) * f.GyroGain(80f) * Lock;
            var c = new SteeringColumn(f, Lock);
            float maxRate = 0f;
            for (int i = 0; i < 300; i++) { c.Step(Dt, target, true, 80f, 0f); maxRate = Mathf.Max(maxRate, Mathf.Abs(c.RateDegS)); }
            Assert.LessOrEqual(maxRate, f.HandRate(80f) + 1e-3f);
            Assert.AreEqual(target, c.AngleDeg, 0.01f);
            Assert.Less(target, 150f, "20 deg tilt at 80 km/h asks for < 150 deg of wheel");

            // 1-euro filter: tilt jitter of ±0.5 deg does not reach the output.
            var filter = new OneEuroFilter(1f, 0.02f, 1f);
            var rng = new System.Random(3);
            float maxOut = 0f;
            for (int i = 0; i < 200; i++)
            {
                float tilt = filter.Filter((float)(rng.NextDouble() - 0.5), 0.016f);
                maxOut = Mathf.Max(maxOut, Mathf.Abs(GyroMath.SteerFromTilt(tilt, 35f, 1f)));
            }
            Assert.AreEqual(0f, maxOut, 1e-6f, "jitter filtered and inside the dead zone");
        }

        // ---------------------------------------------------------------- direction + visual

        [Test]
        public void Direction_RightInput_PositiveCabWheel_PositiveRoadWheel_AllModes()
        {
            foreach (float kmh in new[] { 0f, 30f, 80f })
            {
                foreach (float range in new[] { 270f, 900f })
                {
                    var w = new TouchSteeringWheel { HalfRangeDeg = range };
                    w.PointerDown(Finger(0f));
                    TurnTo(w, 60f);
                    var col = new SteeringColumn(null, Lock);
                    var st = PhysicsSteering();
                    var fb = new VehicleFeedback { ForwardSpeed = kmh / 3.6f, HandwheelLockDeg = Lock };
                    for (int i = 0; i < 100; i++) { var it = new DriverIntent(); w.Sample(Dt, fb, ref it); col.Step(Dt, it.Steer * Lock, it.HandsOn, kmh, 0f); st.Update(col.Normalized, Dt); }
                    Assert.Greater(col.AngleDeg, 1f, $"wheel {range} at {kmh} km/h: cab wheel");
                    Assert.Greater(st.Angle, 0.0, $"wheel {range} at {kmh} km/h: road wheel");
                }
                // Gyro: right edge down.
                float g = GyroMath.SteerFromTilt(GyroMath.Relative(GyroMath.TiltAngleDeg(new Vector3(Mathf.Sin(0.3f), -Mathf.Cos(0.3f), 0)), GyroMath.TiltAngleDeg(new Vector3(0, -1, 0))), 35f, 1f)
                          * SteeringFeel.Defaults().GyroGain(kmh);
                var gc = new SteeringColumn(null, Lock);
                for (int i = 0; i < 100; i++) gc.Step(Dt, g * Lock, true, kmh, 0f);
                Assert.Greater(gc.AngleDeg, 1f, $"gyro at {kmh} km/h");
                // Keyboard (editor).
                float kb = KeyboardDriverInput.StepSteer(0f, +1, 0.3f, 1.2f, 2.0f);
                var kc = new SteeringColumn(null, Lock);
                for (int i = 0; i < 100; i++) kc.Step(Dt, kb * Lock, true, kmh, 0f);
                Assert.Greater(kc.AngleDeg, 1f, $"keyboard at {kmh} km/h");
            }
        }

        [Test]
        public void InCabWheel_EqualsSimulatedWheel()
        {
            // The visual uses Steering.HandwheelDeg (road-wheel angle x ratio); its rate limit (30 deg/s x 20 = 600 deg/s)
            // is above the hand limit, so it equals the column angle every fixed step.
            var col = new SteeringColumn(null, Lock);
            var st = PhysicsSteering();
            float maxErr = 0f;
            for (int i = 0; i < 600; i++)
            {
                float target = i < 200 ? Lock : i < 400 ? -300f : 0f;
                col.Step(Dt, target, i < 400, 15f, 600f);
                st.Update(col.Normalized, Dt);
                maxErr = Mathf.Max(maxErr, Mathf.Abs((float)st.HandwheelDeg - col.AngleDeg));
            }
            Assert.Less(maxErr, 0.01f, "in-cab wheel angle = simulated steering-wheel angle");
        }

        // ---------------------------------------------------------------- data + settings migration

        [Test]
        public void ShippedJson_EqualsCodeDefaults()
        {
            var json = Resources.Load<TextAsset>(SteeringFeel.ResourcePath);
            Assert.IsNotNull(json, "Resources/Controls/steering_feel.json");
            Assert.AreEqual(JsonUtility.ToJson(SteeringFeel.Defaults()), JsonUtility.ToJson(SteeringFeel.FromJson(json.text)));
            var broken = SteeringFeel.FromJson("{\"handRateSpeedsKmh\":[0,10],\"handRateDegS\":[1]}");
            Assert.AreEqual(720f, broken.HandRate(0f), 1e-3f, "mismatched table falls back to the defaults");
        }

        [Test]
        public void Migration_V2Save_GetsSpeedSensitiveSteering_KeepsOwnerChoices()
        {
            var v2 = ControlSettings.FromJson("{\"schema\":2,\"wheelRangeDeg\":450,\"centreStrength\":0.7,\"gyroEnabled\":true,\"cabFov\":60}");
            Assert.AreEqual(ControlSettings.CurrentSchema, v2.schema);
            Assert.IsTrue(v2.speedSensitiveSteering);
            Assert.AreEqual(450f, v2.wheelRangeDeg); Assert.AreEqual(0.7f, v2.centreStrength, 1e-6f); Assert.IsTrue(v2.gyroEnabled); Assert.AreEqual(60f, v2.cabFov);
            var v3 = ControlSettings.FromJson("{\"schema\":3,\"speedSensitiveSteering\":false}");
            Assert.IsFalse(v3.speedSensitiveSteering, "an explicit v3 choice is kept");
            Assert.AreEqual(v3.ToJson(), ControlSettings.FromJson(v3.ToJson()).ToJson());
        }

        // ---------------------------------------------------------------- evidence (before / after)

        /// <summary>The v2 pipeline (f6abb8b): normalised on-screen angle, 20 ms smoothing, self-centre on the on-screen
        /// wheel (540 deg/s max, 8 m/s, 800 N m), then only the physics road-wheel limit of 30 deg/s.</summary>
        sealed class LegacyPipeline
        {
            public float Wheel, Output;
            public readonly Steering St = PhysicsSteering();
            public void Step(float finger, bool held, float speedMs, float mz)
            {
                if (held) Wheel = finger;
                else
                {
                    float k = 0.6f * Mathf.Clamp01(Mathf.Abs(speedMs) / 8f) + 0.4f * Mathf.Clamp01(Mathf.Abs(mz) / 800f);
                    Wheel = Mathf.MoveTowards(Wheel, 0f, 540f * Mathf.Clamp01(k) * Dt);
                }
                float target = Mathf.Clamp(SteeringMath.DeadZone(Wheel / 270f, 0.01f), -1f, 1f);
                Output = Mathf.Lerp(Output, target, SteeringMath.SmoothingAlpha(Dt, 0.02f));
                St.Update(Output, Dt);
            }
        }

        struct Scenario { public string Id; public float Kmh; public float[] T, Finger; public float ReleaseAt, Duration; }

        static readonly Scenario[] k_Scenarios =
        {
            // Manoeuvring: quick 3/4 turn of the on-screen wheel to full comfort range, hold, release.
            new Scenario { Id = "parking_5kmh_full_swipe", Kmh = 5f, T = new[] { 0f, 0.5f, 0.9f, 3f }, Finger = new[] { 0f, 0f, 270f, 270f }, ReleaseAt = 2.4f, Duration = 5f },
            // Owner, S24+ 2026-11-10, t=180.9-182.5 at ~41 km/h ([CONTROLS] steer x 270 deg).
            new Scenario { Id = "owner_41kmh_replay", Kmh = 41f, T = new[] { 0f, 0.27f, 0.54f, 0.81f, 1.08f, 1.35f, 1.62f }, Finger = new[] { -0.07f * 270f, -0.51f * 270f, -0.66f * 270f, -0.77f * 270f, -0.44f * 270f, -0.14f * 270f, 0f }, ReleaseAt = 1.62f, Duration = 4f },
            // Owner, t=174.6-175.1 at ~90 km/h: 0 to full lock within 0.5 s. Here at 80 km/h.
            new Scenario { Id = "motorway_80kmh_full_swipe", Kmh = 80f, T = new[] { 0f, 0.5f, 0.9f, 3f }, Finger = new[] { 0f, 0f, -270f, -270f }, ReleaseAt = 2.4f, Duration = 5f },
            // A calm lane change at 80 km/h: +-25 deg of on-screen wheel.
            new Scenario { Id = "lanechange_80kmh_25deg", Kmh = 80f, T = new[] { 0f, 0.5f, 1.3f, 2.1f, 2.9f, 4f }, Finger = new[] { 0f, 0f, 25f, -25f, 0f, 0f }, ReleaseAt = 3.5f, Duration = 5f },
        };

        static float Interp(float[] x, float[] y, float t)
        {
            if (t <= x[0]) return y[0];
            for (int i = 1; i < x.Length; i++) if (t <= x[i]) return Mathf.Lerp(y[i - 1], y[i], (t - x[i - 1]) / (x[i] - x[i - 1]));
            return y[y.Length - 1];
        }

        [Test]
        public void Evidence_BeforeAfter_Csv()
        {
            string dir = Environment.GetEnvironmentVariable("KAMION_STEER_EVIDENCE_DIR");
            var ci = CultureInfo.InvariantCulture;
            foreach (var sc in k_Scenarios)
            {
                var sb = new StringBuilder("t,finger_deg,held,before_handwheel_deg,before_road_deg,after_target_deg,after_handwheel_deg,after_road_deg\n");
                var legacy = new LegacyPipeline();
                var wheel = new TouchSteeringWheel();
                var col = new SteeringColumn(null, Lock);
                var st = PhysicsSteering();
                var fb = new VehicleFeedback { ForwardSpeed = sc.Kmh / 3.6f, HandwheelLockDeg = Lock };
                float mz = 0f;   // conservative: speed (caster) term only
                bool down = false;
                float maxBeforeRate = 0f, maxAfterRate = 0f, prevB = 0f, prevA = 0f;
                for (float t = 0f; t < sc.Duration; t += Dt)
                {
                    bool held = t < sc.ReleaseAt;
                    float finger = Interp(sc.T, sc.Finger, t);
                    if (held && !down) { wheel.SetWheelDeg(finger); wheel.PointerDown(Finger(wheel.WheelDeg)); down = true; }
                    if (held) TurnTo(wheel, finger);
                    if (!held && down) { wheel.PointerUp(); down = false; }
                    legacy.Step(finger, held, fb.ForwardSpeed, mz);
                    var it = new DriverIntent();
                    wheel.Sample(Dt, fb, ref it);
                    col.Step(Dt, it.Steer * Lock, it.HandsOn, sc.Kmh, mz);
                    st.Update(col.Normalized, Dt);
                    wheel.FollowColumn(col.Normalized);
                    float bRoad = (float)(legacy.St.Angle * MathUtil.Rad2Deg), aRoad = (float)(st.Angle * MathUtil.Rad2Deg);
                    if (t > 0f) { maxBeforeRate = Mathf.Max(maxBeforeRate, Mathf.Abs(bRoad - prevB) / Dt); maxAfterRate = Mathf.Max(maxAfterRate, Mathf.Abs(aRoad - prevA) / Dt); }
                    prevB = bRoad; prevA = aRoad;
                    sb.Append(t.ToString("F2", ci)).Append(',').Append((held ? finger : wheel.WheelDeg).ToString("F2", ci)).Append(',').Append(held ? 1 : 0).Append(',')
                      .Append(((float)legacy.St.HandwheelDeg).ToString("F2", ci)).Append(',').Append(bRoad.ToString("F3", ci)).Append(',')
                      .Append((it.Steer * Lock).ToString("F2", ci)).Append(',').Append(col.AngleDeg.ToString("F2", ci)).Append(',').Append(aRoad.ToString("F3", ci)).Append('\n');
                }
                Debug.Log($"[TEST] evidence {sc.Id}: max road-wheel rate before {maxBeforeRate:F1} deg/s, after {maxAfterRate:F1} deg/s");
                Assert.LessOrEqual(maxAfterRate, maxBeforeRate + 1e-3f, sc.Id);
                if (!string.IsNullOrEmpty(dir))
                {
                    Directory.CreateDirectory(dir);
                    File.WriteAllText(Path.Combine(dir, sc.Id + ".csv"), sb.ToString());
                }
            }
        }
    }
}
