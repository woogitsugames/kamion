using Game.Controls;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0149 (owner's Fold video 2026-11-12, APK 387a492d24): the drag gesture's cab-wheel degrees per millimetre are
    /// capped between ~24 and 60 km/h so a millimetre of thumb never asks for more kinematic lateral acceleration than at
    /// 60 km/h. Unchanged at manoeuvring speed, from 60 km/h up, and for the rotate gesture. Closed-loop evidence (thumb
    /// model + physics core) lives in tools/physics-runner (TouchSteeringTests).
    /// </summary>
    public class SteerFoldR2Tests
    {
        const float Lock = 800f; // 40 deg x 20:1 (tractor_4x2_generic.vehicle.json)

        static float CabDegPerMm(WheelGrab grab, float kmh, SteeringFeel feel = null)
        {
            var w = new TouchSteeringWheel { Grab = grab, HalfRangeDeg = 270f, DeadZone = 0f, Feel = feel ?? SteeringFeel.Defaults() };
            w.PointerDown(new Vector2(0f, 150f), new Vector2(0f, 0f));
            if (grab == WheelGrab.Drag) w.PointerDrag(new Vector2(0f, 150f), new Vector2(1f, 0f));
            else w.SetWheelDeg(w.DragDegPerMm); // same on-screen angle as 1 mm of drag
            var it = new DriverIntent();
            w.Sample(0.01f, new VehicleFeedback { ForwardSpeed = kmh / 3.6f, HandwheelLockDeg = Lock }, ref it);
            return it.Steer * Lock;
        }

        [Test]
        public void Drag_CabDegPerMm_FollowsInverseSquareOfSpeedBelow60()
        {
            // 5 deg/mm at 60 km/h x (60 / v)^2, never above the ADR 0135 smoothstep curve.
            Assert.AreEqual(5f * (60f / 35f) * (60f / 35f), CabDegPerMm(WheelGrab.Drag, 35f), 0.05f);
            Assert.AreEqual(5f * (60f / 45f) * (60f / 45f), CabDegPerMm(WheelGrab.Drag, 45f), 0.05f);
            Assert.AreEqual(5f, CabDegPerMm(WheelGrab.Drag, 60f), 0.01f);
            for (float kmh = 21f; kmh < 60f; kmh += 1f)
            {
                float a = CabDegPerMm(WheelGrab.Drag, kmh), b = 5f * (60f / kmh) * (60f / kmh);
                Assert.LessOrEqual(a, b + 1e-3f, kmh + " km/h");
                Assert.LessOrEqual(a * kmh * kmh, 5f * 60f * 60f * 1.0001f, kmh + " km/h: lateral acceleration per mm above the 60 km/h value");
            }
        }

        [Test]
        public void Drag_UnchangedAtManoeuvringSpeedAndFrom60_RotateUnchanged()
        {
            var old = SteeringFeel.Defaults();
            old.dragLatAccelMatchKmh = 0f; // ADR 0135 curve
            foreach (float kmh in new[] { 0f, 5f, 15f, 20f, 60f, 80f, 100f })
                Assert.AreEqual(CabDegPerMm(WheelGrab.Drag, kmh, old), CabDegPerMm(WheelGrab.Drag, kmh), 1e-3f, kmh + " km/h");
            Assert.AreEqual(32f, CabDegPerMm(WheelGrab.Drag, 15f), 0.01f, "full lock (800 deg) in 25 mm when manoeuvring");
            foreach (float kmh in new[] { 30f, 35f, 45f })
            {
                Assert.Less(CabDegPerMm(WheelGrab.Drag, kmh), CabDegPerMm(WheelGrab.Drag, kmh, old), kmh + " km/h: drag is calmer");
                Assert.AreEqual(CabDegPerMm(WheelGrab.Rotate, kmh, old), CabDegPerMm(WheelGrab.Rotate, kmh), 1e-4f, kmh + " km/h: rotate gesture untouched");
            }
        }

        [Test]
        public void Drag_SpeedInsensitiveSetting_StillGivesFullGain()
        {
            var w = new TouchSteeringWheel { Grab = WheelGrab.Drag, HalfRangeDeg = 270f, DeadZone = 0f, SpeedSensitive = false };
            w.PointerDown(new Vector2(0f, 150f), new Vector2(0f, 0f));
            w.PointerDrag(new Vector2(0f, 150f), new Vector2(1f, 0f));
            var it = new DriverIntent();
            w.Sample(0.01f, new VehicleFeedback { ForwardSpeed = 35f / 3.6f, HandwheelLockDeg = Lock }, ref it);
            Assert.AreEqual(1f, w.LastGain, 1e-6f);
        }

        [Test]
        public void ShippedJson_CarriesTheMatchSpeed()
        {
            var json = Resources.Load<TextAsset>(SteeringFeel.ResourcePath);
            Assert.IsNotNull(json);
            Assert.AreEqual(60f, SteeringFeel.FromJson(json.text).dragLatAccelMatchKmh, 1e-4f);
            Assert.AreEqual(SteeringFeel.Defaults().dragLatAccelMatchKmh, SteeringFeel.FromJson(json.text).dragLatAccelMatchKmh, 1e-4f);
        }
    }
}
