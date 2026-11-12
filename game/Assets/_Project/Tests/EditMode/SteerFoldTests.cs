using System;
using System.Globalization;
using System.IO;
using System.Text;
using Game.Cameras;
using Game.Controls;
using Game.Gameplay;
using Game.Vehicle.Physics;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0135 (owner test on the Fold, APK 11db0552): touch-wheel drag gesture (direction, mm mapping at low speed and
    /// at speed, no jump on touch-down, no dead travel at the stop), cab-wheel marker, settings schema 4 migration,
    /// near-square orientation policy, portrait cab FOV, and the reach/lag evidence CSV
    /// (written when KAMION_STEER_EVIDENCE_DIR is set).
    /// </summary>
    public class SteerFoldTests
    {
        const float Dt = 0.01f;
        const float Lock = 800f;   // 40 deg x 20:1 (tractor_4x2_generic.vehicle.json)

        static Steering PhysicsSteering() => new Steering(new SteeringDefinition { maxRoadWheelAngleDeg = 40, maxSteerRateDegS = 30, steeringRatio = 20 });

        static TouchSteeringWheel DragWheel(float range = 270f) => new TouchSteeringWheel { Grab = WheelGrab.Drag, HalfRangeDeg = range, DeadZone = 0f };

        /// <summary>Slides the finger sideways by dxMm in 1 mm events starting at x0 (y fixed).</summary>
        static void Slide(TouchSteeringWheel w, float x0, float dxMm, float y = 15f)
        {
            int n = Mathf.Max(1, Mathf.CeilToInt(Mathf.Abs(dxMm)));
            for (int i = 1; i <= n; i++) w.PointerDrag(Vector2.zero, new Vector2(x0 + dxMm * i / n, y));
        }

        static float TargetDeg(TouchSteeringWheel w, float kmh)
        {
            var it = new DriverIntent();
            w.Sample(Dt, new VehicleFeedback { ForwardSpeed = kmh / 3.6f, HandwheelLockDeg = Lock }, ref it);
            return it.Steer * Lock;
        }

        // ---------------------------------------------------------------- drag gesture

        [Test]
        public void Drag_RightSlideTurnsRight_LeftSlideTurnsLeft_ThroughColumnAndPhysics_AllSpeeds()
        {
            foreach (float kmh in new[] { 0f, 5f, 30f, 80f })
            foreach (float range in new[] { 270f, 900f })
            foreach (float dir in new[] { 1f, -1f })
            {
                var w = DragWheel(range);
                w.PointerDown(Vector2.zero, new Vector2(30f, 15f));
                Slide(w, 30f, 6f * dir);
                var col = new SteeringColumn(null, Lock);
                var st = PhysicsSteering();
                var fb = new VehicleFeedback { ForwardSpeed = kmh / 3.6f, HandwheelLockDeg = Lock };
                for (int i = 0; i < 100; i++) { var it = new DriverIntent(); w.Sample(Dt, fb, ref it); col.Step(Dt, it.Steer * Lock, it.HandsOn, kmh, 0f); st.Update(col.Normalized, Dt); }
                string tag = $"drag {dir:+0;-0} range {range} at {kmh} km/h";
                Assert.AreEqual(dir, Mathf.Sign(w.WheelDeg), tag + ": on-screen wheel");
                Assert.AreEqual(dir, Mathf.Sign(col.AngleDeg), tag + ": cab wheel");
                Assert.AreEqual(dir, Math.Sign(st.Angle), tag + ": road wheel");
            }
        }

        [Test]
        public void Drag_FullLock_Within25mm_WhenManoeuvring()
        {
            var w = DragWheel();
            w.PointerDown(Vector2.zero, new Vector2(40f, 15f));
            Slide(w, 40f, -25f);
            Assert.AreEqual(-270f, w.WheelDeg, 0.01f, "comfort range in 25 mm");
            Assert.AreEqual(-Lock, TargetDeg(w, 5f), 0.5f, "full lock at 5 km/h");
            Assert.AreEqual(-Lock, TargetDeg(w, 20f), 0.5f, "full lock at 20 km/h");
        }

        [Test]
        public void Drag_AtSpeed_FiveCabDegreesPerMillimetre()
        {
            var f = SteeringFeel.Defaults();
            foreach (float range in new[] { 270f, 540f })
            {
                var w = DragWheel(range);
                w.PointerDown(Vector2.zero, new Vector2(10f, 15f));
                Slide(w, 10f, 4f);
                Assert.AreEqual(4f * f.dragHighSpeedHandwheelDegPerMm, TargetDeg(w, 80f), 0.05f, "4 mm at 80 km/h, range " + range);
            }
        }

        [Test]
        public void Drag_TouchDownAnywhere_NoJump_VerticalMotionIgnored()
        {
            var w = DragWheel();
            w.SetWheelDeg(40f);
            foreach (var p in new[] { new Vector2(1f, 1f), new Vector2(55f, 30f), new Vector2(-3f, 70f) })
            {
                w.PointerDown(new Vector2(500f, -500f), p);
                Assert.AreEqual(40f, w.WheelDeg, 1e-4f, "touch-down at " + p);
                w.PointerDrag(Vector2.zero, p + new Vector2(0f, 12f));
                Assert.AreEqual(40f, w.WheelDeg, 1e-4f, "vertical slide does not steer");
                w.PointerUp();
            }
            w.PointerDown(Vector2.zero, new Vector2(float.NaN, float.NaN));
            w.PointerDrag(Vector2.zero, new Vector2(float.NaN, float.NaN));
            Assert.AreEqual(40f, w.WheelDeg, 1e-4f, "no DPI / position: nothing moves");
        }

        [Test]
        public void Drag_PastTheStop_ReversesImmediately()
        {
            var f = SteeringFeel.Defaults();
            var w = DragWheel();
            w.PointerDown(Vector2.zero, new Vector2(0f, 15f));
            Slide(w, 0f, 60f);   // far past the stop
            Assert.AreEqual(270f, w.WheelDeg, 1e-3f);
            w.PointerDrag(Vector2.zero, new Vector2(59f, 15f));
            Assert.AreEqual(270f - f.dragScreenDegPerMm, w.WheelDeg, 1e-3f, "1 mm back = one step back, no dead travel");
        }

        [Test]
        public void ColumnMarker_ShowsCabWheel_WhileHeld_AndEqualsDrawingWhenSettled()
        {
            var w = DragWheel();
            w.PointerDown(Vector2.zero, new Vector2(0f, 15f));
            Slide(w, 0f, 20f);   // 216 deg on screen at 5 km/h
            var col = new SteeringColumn(null, Lock);
            var fb = new VehicleFeedback { ForwardSpeed = 5f / 3.6f, HandwheelLockDeg = Lock };
            var it = new DriverIntent();
            w.Sample(Dt, fb, ref it); col.Step(Dt, it.Steer * Lock, it.HandsOn, 5f, 0f); w.FollowColumn(col.Normalized);
            Assert.Less(w.ColumnScreenDeg, w.WheelDeg - 100f, "first step: the heavy wheel lags, the marker shows it");
            for (int i = 0; i < 300; i++) { w.Sample(Dt, fb, ref it); col.Step(Dt, it.Steer * Lock, it.HandsOn, 5f, 0f); w.FollowColumn(col.Normalized); }
            Assert.AreEqual(w.WheelDeg, w.ColumnScreenDeg, 0.5f, "settled: marker on the drawing");
            Assert.IsTrue(w.Held, "held the whole time");
        }

        [Test]
        public void PixelsToMm_UsesDpi_WithFallback()
        {
            Assert.AreEqual(25.4f, SteeringMath.PixelsToMm(new Vector2(400f, 0f), 400f).x, 1e-4f);
            Assert.AreEqual(25.4f, SteeringMath.PixelsToMm(new Vector2(SteeringMath.FallbackDpi, 0f), 0f).x, 1e-4f);
        }

        // ---------------------------------------------------------------- settings

        [Test]
        public void Settings_Schema4_MigratesV3ToDrag_KeepsExplicitRotate_AppliesGesture()
        {
            Assert.AreEqual(4, ControlSettings.CurrentSchema);
            var v3 = ControlSettings.FromJson("{\"schema\":3,\"wheelRangeDeg\":450,\"speedSensitiveSteering\":false}");
            Assert.AreEqual(4, v3.schema);
            Assert.IsTrue(v3.wheelDragGrab, "v3 save gets the drag gesture");
            Assert.AreEqual(450f, v3.wheelRangeDeg); Assert.IsFalse(v3.speedSensitiveSteering, "other choices kept");
            var v4 = ControlSettings.FromJson("{\"schema\":4,\"wheelDragGrab\":false}");
            Assert.IsFalse(v4.wheelDragGrab, "explicit v4 choice kept");
            Assert.AreEqual(v4.ToJson(), ControlSettings.FromJson(v4.ToJson()).ToJson());
            var w = new TouchSteeringWheel();
            v4.ApplyTo(w, null, null);
            Assert.AreEqual(WheelGrab.Rotate, w.Grab);
            ControlSettings.Defaults().ApplyTo(w, null, null);
            Assert.AreEqual(WheelGrab.Drag, w.Grab);
            StringAssert.Contains("grab=rotate", v4.LogLine("t"));
        }

        // ---------------------------------------------------------------- orientation + camera

        [Test]
        public void Orientation_NearSquareFollowsHolding_ElongatedLandscapeOnly()
        {
            // name, w, h, any orientation
            var cases = new (string, int, int, bool)[]
            {
                ("fold inner landscape", 2184, 1968, true), ("fold inner portrait", 1968, 2184, true),
                ("fold recording 1200x1080", 1200, 1080, true), ("square", 1500, 1500, true),
                ("S24+ landscape", 2340, 1080, false), ("S24+ portrait", 1080, 2340, false),
                ("fold cover", 2520, 1080, false), ("16:10 tablet", 2560, 1600, false), ("4:3 tablet", 2048, 1536, false),
                ("unknown", 0, 0, false),
            };
            foreach (var (name, w, h, any) in cases)
            {
                var a = ScreenOrientationPolicy.Decide(w, h);
                Assert.IsTrue(a.LandscapeLeft && a.LandscapeRight, name + ": landscape always allowed");
                Assert.AreEqual(any, a.Portrait, name);
                Assert.AreEqual(any, a.PortraitUpsideDown, name);
                Assert.IsTrue(a.Equals(ScreenOrientationPolicy.Decide(h, w)), name + ": same decision in both orientations (no flip-flop)");
            }
        }

        [Test]
        public void CabFov_PortraitKeepsHorizontalField_LandscapeUnchanged()
        {
            Assert.AreEqual(55f, CameraRig.CabVerticalFov(55f, 2.17f), 1e-4f);
            Assert.AreEqual(55f, CameraRig.CabVerticalFov(55f, 1.11f), 1e-4f);
            Assert.AreEqual(55f, CameraRig.CabVerticalFov(55f, 0f), 1e-4f, "unknown aspect");
            float v = CameraRig.CabVerticalFov(55f, 0.9f);
            float h = 2f * Mathf.Atan(Mathf.Tan(v * 0.5f * Mathf.Deg2Rad) * 0.9f) * Mathf.Rad2Deg;
            Assert.AreEqual(55f, h, 1e-3f, "portrait 0.9: horizontal FOV = setting");
            Assert.LessOrEqual(CameraRig.CabVerticalFov(75f, 0.3f), 90f);
        }

        [Test]
        public void Drag_SimRange_ScaledTravel_About46mm()
        {
            var w = DragWheel(900f);
            Assert.AreEqual(900f / w.DragDegPerMm, 25f * Mathf.Sqrt(900f / 270f), 1e-3f);
            Assert.That(900f / w.DragDegPerMm, Is.InRange(44f, 48f), "900 deg sim range: ~46 mm (was 83 mm)");
            Assert.AreEqual(SteeringFeel.Defaults().dragScreenDegPerMm, DragWheel(180f).DragDegPerMm, 1e-5f, "short ranges keep 10.8 deg/mm");
        }

        [Test]
        public void Dpi_Sanitised_PanelPreferredWhenPlausible()
        {
            Assert.AreEqual(SteeringMath.FallbackDpi, SteeringMath.SanitizeDpi(0f), 1e-4f);
            Assert.AreEqual(SteeringMath.FallbackDpi, SteeringMath.SanitizeDpi(float.NaN), 1e-4f);
            Assert.AreEqual(120f, SteeringMath.SanitizeDpi(40f), 1e-4f);
            Assert.AreEqual(900f, SteeringMath.SanitizeDpi(4000f), 1e-4f);
            Assert.AreEqual(374f, DeviceDisplay.Choose(420f, 374f), 1e-4f, "panel xdpi within 0.6-1.6x of the bucket");
            Assert.AreEqual(480f, DeviceDisplay.Choose(480f, 60f), 1e-4f, "implausible panel value: bucket");
            Assert.AreEqual(374f, DeviceDisplay.Choose(0f, 374f), 1e-4f, "no bucket: panel");
            Assert.AreEqual("portrait", DeviceDisplay.NaturalOrientation(2184, 1968, 1), "landscape window at rotation 90: natural portrait");
            Assert.AreEqual("landscape", DeviceDisplay.NaturalOrientation(2184, 1968, 0));
            Assert.AreEqual("portrait", DeviceDisplay.NaturalOrientation(1968, 2184, 0));
            Assert.AreEqual("unknown", DeviceDisplay.NaturalOrientation(1968, 2184, -1));
        }

        [Test]
        public void OrientationLock_NearSquare_KeepsLaunchOrientation_NeverRotates()
        {
            foreach (var start in new[] { ScreenOrientation.Portrait, ScreenOrientation.LandscapeLeft })
            {
                var l = new ScreenOrientationLock();
                int w = start == ScreenOrientation.Portrait ? 1968 : 2184, h = start == ScreenOrientation.Portrait ? 2184 : 1968;
                Assert.AreEqual(OrientationCommand.Lock, l.Step(0f, w, h, start, false), "first frame: lock, no AllowAuto");
                Assert.AreEqual(start, l.LockTo, "keeps the orientation the display already has");
                for (float t = 0.1f; t < 30f; t += 0.5f) Assert.AreEqual(OrientationCommand.None, l.Step(t, w, h, start, true), "never asks for a rotation");
            }
            var u = new ScreenOrientationLock();
            Assert.AreEqual(OrientationCommand.None, u.Step(0f, 1968, 2184, ScreenOrientation.AutoRotation, false), "not concrete yet: wait");
            Assert.AreEqual(OrientationCommand.Lock, u.Step(0.1f, 1968, 2184, ScreenOrientation.Portrait, false));
        }

        [Test]
        public void OrientationLock_FoldUnfold_PhoneLandscape_GyroLock()
        {
            var l = new ScreenOrientationLock();
            Assert.AreEqual(OrientationCommand.Lock, l.Step(0f, 1968, 2184, ScreenOrientation.Portrait, false));
            // Fold -> cover screen (elongated) held upright: forced to landscape (ADR 0147), then L/R auto-rotation.
            Assert.AreEqual(OrientationCommand.Lock, l.Step(10f, 1080, 2520, ScreenOrientation.Portrait, false));
            Assert.AreEqual(ScreenOrientation.LandscapeLeft, l.LockTo);
            Assert.IsFalse(l.Allowed.Portrait);
            Assert.AreEqual(OrientationCommand.AllowAuto, l.Step(10.5f, 2520, 1080, ScreenOrientation.LandscapeLeft, false));
            Assert.AreEqual(OrientationCommand.None, l.Step(11f, 2520, 1080, ScreenOrientation.LandscapeLeft, false));
            Assert.AreEqual(OrientationCommand.None, l.Step(13f, 2520, 1080, ScreenOrientation.LandscapeLeft, false));
            Assert.IsFalse(l.Locked, "phone without gyro: landscape L/R rotate as before");
            Assert.AreEqual(OrientationCommand.Lock, l.Step(14f, 2520, 1080, ScreenOrientation.LandscapeRight, true), "gyro on: lock");
            Assert.AreEqual(ScreenOrientation.LandscapeRight, l.LockTo);
            Assert.AreEqual(OrientationCommand.AllowAuto, l.Step(15f, 2520, 1080, ScreenOrientation.LandscapeRight, false), "gyro off: unlock");
            // Unfold: keep whatever the inner screen shows.
            Assert.AreEqual(OrientationCommand.Lock, l.Step(20f, 2184, 1968, ScreenOrientation.LandscapeRight, true));
            Assert.AreEqual(ScreenOrientation.LandscapeRight, l.LockTo);
        }

        [Test]
        public void OrientationLock_PhoneWithGyro_LocksAfterSettle()
        {
            var l = new ScreenOrientationLock();
            Assert.AreEqual(OrientationCommand.AllowAuto, l.Step(0f, 2340, 1080, ScreenOrientation.LandscapeLeft, true));
            Assert.AreEqual(OrientationCommand.None, l.Step(1f, 2340, 1080, ScreenOrientation.LandscapeLeft, true));
            Assert.AreEqual(OrientationCommand.Lock, l.Step(1.3f, 2340, 1080, ScreenOrientation.LandscapeLeft, true));
            Assert.AreEqual(OrientationCommand.None, l.Step(1.4f, 2340, 1080, ScreenOrientation.LandscapeLeft, true), "no repeat");
        }

        // ---------------------------------------------------------------- evidence

        /// <summary>
        /// Reach and lag, before (ADR 0058: rotate gesture, hand rate 540/480) and after (ADR 0135: drag, 720/600).
        /// Rotate reach: a thumb anchored in the lower-left screen corner sweeps the upper half of the rim at most;
        /// +-120 deg is the assumed comfortable sweep (WORKING_VALUE, from the owner's frames: the finger never passes
        /// the 3/9 o'clock line). Drag reach: the free width of the grab area plus the wheel (assumed 25 mm one way).
        /// </summary>
        [Test]
        public void Evidence_ReachAndLag_Csv()
        {
            var ci = CultureInfo.InvariantCulture;
            var after = SteeringFeel.Defaults();
            var before = SteeringFeel.Defaults();
            before.handRateDegS = new[] { 540f, 480f, 300f, 200f, 130f, 110f };
            const float rotateReachDeg = 120f, dragReachMm = 25f;
            var sb = new StringBuilder("kmh,before_reach_lock_frac,after_reach_lock_frac,before_t90_full_lock_s,after_t90_full_lock_s,before_cab_deg_per_mm_at_rim_s24,after_cab_deg_per_mm\n");
            foreach (float kmh in new[] { 5f, 10f, 20f, 40f, 60f, 80f })
            {
                float gainRot = before.WheelGain(kmh, 270f, Lock, before.highSpeedScreenToHandwheel);
                float reachBefore = Mathf.Min(1f, rotateReachDeg / 270f * gainRot);
                var dw = new TouchSteeringWheel { Grab = WheelGrab.Drag, DeadZone = 0f, Feel = after };
                float gainDrag = after.WheelGain(kmh, 270f, Lock, dw.HighSpeedScreenToHandwheel);
                float reachAfter = Mathf.Min(1f, dragReachMm * after.dragScreenDegPerMm / 270f * gainDrag);
                float t90b = T90(before, Lock, kmh), t90a = T90(after, Lock, kmh);   // same target: hand-rate change only
                // Rotate gesture at the rim of the 400-unit wheel on the S24+ (1 px/unit, ~516 dpi, r ~ 180 units): mm per on-screen degree.
                float mmPerDegRim = 180f * Mathf.Deg2Rad * 25.4f / 516f;
                float cabPerMmBefore = gainRot * Lock / 270f / mmPerDegRim;
                float cabPerMmAfter = after.dragScreenDegPerMm * gainDrag * Lock / 270f;
                sb.Append(kmh.ToString("F0", ci)).Append(',').Append(reachBefore.ToString("F2", ci)).Append(',').Append(reachAfter.ToString("F2", ci)).Append(',')
                  .Append(t90b.ToString("F2", ci)).Append(',').Append(t90a.ToString("F2", ci)).Append(',')
                  .Append(cabPerMmBefore.ToString("F1", ci)).Append(',').Append(cabPerMmAfter.ToString("F1", ci)).Append('\n');
                Assert.GreaterOrEqual(reachAfter, reachBefore - 1e-4f, "reach at " + kmh);
                if (kmh <= 20f) Assert.AreEqual(1f, reachAfter, 1e-4f, "full lock reachable when manoeuvring");
                Assert.LessOrEqual(t90a, t90b + 1e-4f, "never slower than ADR 0058 at " + kmh);
            }
            Debug.Log("[TEST] ADR 0135 reach/lag\n" + sb);
            string dir = Environment.GetEnvironmentVariable("KAMION_STEER_EVIDENCE_DIR");
            if (!string.IsNullOrEmpty(dir)) { Directory.CreateDirectory(dir); File.WriteAllText(Path.Combine(dir, "adr0135_reach_lag.csv"), sb.ToString()); }
        }

        /// <summary>Time for the cab wheel to reach 90 % of a step target (hands on, no aligning torque).</summary>
        static float T90(SteeringFeel feel, float targetDeg, float kmh)
        {
            var c = new SteeringColumn(feel, Lock);
            int n = 0;
            while (c.AngleDeg < 0.9f * targetDeg && n < 1000) { c.Step(Dt, targetDeg, true, kmh, 0f); n++; }
            return n * Dt;
        }
    }
}
