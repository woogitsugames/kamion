using Game.Cameras;
using Game.Vehicle.Physics;
using Game.World;
using NUnit.Framework;
using UnityEngine;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0082 (owner recording 2026-11-10): region-edge geometry, the out-of-world monitor, the safe-pose buffer,
    /// the cab camera limits while driving / under extreme accelerations and the cab-suspension hard stops.
    /// </summary>
    public class WorldEdgeLogicTests
    {
        GameObject m_Root;

        [TearDown]
        public void TearDown() { if (m_Root != null) Object.DestroyImmediate(m_Root); }

        [Test]
        public void InsideDistance_IsPositiveInside_NegativeOutside()
        {
            Vector2 min = new Vector2(-1024f, -1024f), max = new Vector2(1024f, 1024f);
            Assert.AreEqual(1024f, WorldBoundary.InsideDistance(min, max, 0f, 0f), 1e-3f);
            Assert.AreEqual(24f, WorldBoundary.InsideDistance(min, max, -857f, 1000f), 1e-3f, "al. Tysiąclecia 24 m before the north edge");
            Assert.AreEqual(-6f, WorldBoundary.InsideDistance(min, max, -857f, 1030f), 1e-3f, "6 m beyond the north edge");
            Assert.AreEqual(-5f, WorldBoundary.InsideDistance(min, max, 1027f, 1028f), 1e-3f, "outside a corner: Euclidean");
        }

        [Test]
        public void ExitMonitor_OutOfBounds_IsImmediate_And_HasAMargin()
        {
            var m = new WorldExitMonitor();
            Assert.AreEqual(WorldExitReason.None, m.Step(0.1f, 200f, true, 0f));
            Assert.AreEqual(WorldExitReason.None, m.Step(0.1f, m.edgeMarginM + 0.5f, true, 0f));
            Assert.AreEqual(WorldExitReason.OutOfBounds, m.Step(0.1f, m.edgeMarginM - 0.5f, true, 0f), "before the terrain ends");
            Assert.AreEqual(WorldExitReason.OutOfBounds, m.Step(0.1f, -30f, false, -40f));
        }

        [Test]
        public void ExitMonitor_NoGround_And_Fall_AreDebounced()
        {
            var m = new WorldExitMonitor();
            // A crest / kerb jump: ground momentarily out of the probe, sink rate of a suspension drop - never a reset.
            for (int i = 0; i < 2; i++) Assert.AreEqual(WorldExitReason.None, m.Step(0.1f, 500f, false, -3f));
            Assert.AreEqual(WorldExitReason.None, m.Step(0.1f, 500f, true, -3f));
            for (int i = 0; i < 3; i++) Assert.AreEqual(WorldExitReason.None, m.Step(0.1f, 500f, false, -3f), "counter restarted by ground contact");
            Assert.AreEqual(WorldExitReason.NoGround, m.Step(0.1f, 500f, false, -3f));
            m.Reset();
            // Free fall with collision still far below (hole in a bridge deck): sink rate beyond anything a road gives.
            Assert.AreEqual(WorldExitReason.None, m.Step(0.1f, 500f, true, -25f));
            Assert.AreEqual(WorldExitReason.None, m.Step(0.1f, 500f, true, -25f));
            Assert.AreEqual(WorldExitReason.Falling, m.Step(0.1f, 500f, true, -26f));
            m.Reset();
            // 12 % downhill at 90 km/h sinks at 3 m/s: far below the threshold.
            for (int i = 0; i < 100; i++) Assert.AreEqual(WorldExitReason.None, m.Step(0.1f, 500f, true, -3f));
        }

        [Test]
        public void SafePoseBuffer_ReturnsNewestPoseOlderThanMinAge()
        {
            var b = new SafePoseBuffer(4);
            Assert.IsFalse(b.TryGet(10f, 2f, out _));
            for (int i = 0; i < 7; i++) b.Record(i, new Vector3(i, 0f, 0f), i * 10f);   // wraps: keeps t = 3..6
            Assert.AreEqual(4, b.Count);
            Assert.IsTrue(b.TryGet(6.5f, 2.5f, out var p));
            Assert.AreEqual(4f, p.time, 1e-4f, "t = 5 and 6 are too fresh");
            Assert.AreEqual(4f, p.position.x, 1e-4f);
            Assert.AreEqual(40f, p.yawDeg, 1e-4f);
            Assert.IsFalse(b.TryGet(4f, 2.5f, out _), "nothing old enough");
            b.Clear();
            Assert.AreEqual(0, b.Count);
        }

        (CameraRig rig, Transform cab, Transform eye) BuildRig()
        {
            m_Root = new GameObject("rig_test");
            var truck = new GameObject("truck").transform; truck.SetParent(m_Root.transform, false);
            var cab = new GameObject("cabPivot").transform; cab.SetParent(truck, false);
            cab.localPosition = new Vector3(0f, 1.15f, 3.925f);
            var eye = new GameObject("DriverEyePoint").transform; eye.SetParent(cab, false);
            eye.localPosition = new Vector3(-0.55f, 1.45f, 0.3f);
            var camGo = new GameObject("cam", typeof(Camera)); camGo.transform.SetParent(m_Root.transform, false);
            var rig = camGo.AddComponent<CameraRig>();
            rig.cam = camGo.GetComponent<Camera>(); rig.target = truck; rig.eyeAnchor = eye; rig.mode = CameraMode.Cab;
            return (rig, cab, eye);
        }

        [Test]
        public void CabLook_WhileDriving_KeepsTheRoadInView()
        {
            var (rig, _, _) = BuildRig();
            rig.speedKmh = 90f;
            rig.AddLookDelta(new Vector2(0f, 100000f));   // the stray drag of the recording: up
            Assert.AreEqual(-rig.drivingPitchUpDeg, rig.LookPitch, 1e-4f, "look-up limited while driving");
            Assert.Less(rig.drivingPitchUpDeg, rig.cabFov * 0.5f - DriverHead.RestPitchDownDeg, "the horizon stays inside the vertical field of view");
            rig.AddLookDelta(new Vector2(0f, -100000f));
            Assert.AreEqual(rig.drivingPitchDownDeg, rig.LookPitch, 1e-4f);
            rig.AddLookDelta(new Vector2(100000f, 0f));
            Assert.AreEqual(DriverHead.YawLimitDeg, rig.LookYaw, 1e-4f, "yaw (mirrors, junctions) is not limited");
            // Returns to the road sooner than at standstill.
            float t = 0f;
            while (t < rig.drivingLookReturnDelay + 2.5f) { rig.UpdateCab(0.02f); t += 0.02f; }
            Assert.AreEqual(0f, rig.LookPitch, 1e-3f);
            Assert.AreEqual(0f, rig.LookYaw, 1e-3f);
            Assert.Less(rig.drivingLookReturnDelay, rig.lookReturnDelay);
        }

        [Test]
        public void CabLook_AtStandstill_HasTheFullNeckRange_ThenEasesInWhenDrivingOff()
        {
            var (rig, _, _) = BuildRig();
            rig.speedKmh = 0f;
            rig.AddLookDelta(new Vector2(0f, 100000f));
            Assert.AreEqual(-DriverHead.PitchUpLimitDeg, rig.LookPitch, 1e-4f);
            rig.speedKmh = 40f;
            rig.UpdateCab(0.02f);
            Assert.Less(rig.LookPitch, -rig.drivingPitchUpDeg, "no snap on the first frame");
            for (int i = 0; i < 60; i++) rig.UpdateCab(0.02f);
            Assert.GreaterOrEqual(rig.LookPitch, -rig.drivingPitchUpDeg - 1e-3f);
        }

        [Test]
        public void CabCamera_StaysInTheEyeBox_WhateverTheInputs()
        {
            var (rig, cab, eye) = BuildRig();
            rig.headGain = 10f;           // absurd gain
            rig.headMaxOffset = 5f;       // and no sway limit
            var prop = typeof(CameraRig).GetField("m_AccFiltered", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            var rnd = new System.Random(7);
            for (int i = 0; i < 400; i++)
            {
                // Tumbling cab + crash-level accelerations + frantic look input (the fall in the recording).
                cab.localRotation = Quaternion.Euler(rnd.Next(-180, 180), rnd.Next(-180, 180), rnd.Next(-180, 180));
                prop.SetValue(rig, new Vector3(rnd.Next(-400, 400), rnd.Next(-400, 400), rnd.Next(-400, 400)));
                rig.AddLookDelta(new Vector2(rnd.Next(-900, 900), rnd.Next(-900, 900)));
                rig.UpdateCab(0.033f);
                Vector3 local = eye.InverseTransformPoint(rig.cam.transform.position);
                Assert.LessOrEqual(Mathf.Abs(local.x), rig.eyeBoxHalfExtents.x + 1e-3f, "x step " + i);
                Assert.LessOrEqual(Mathf.Abs(local.y), rig.eyeBoxHalfExtents.y + 1e-3f, "y step " + i);
                Assert.LessOrEqual(Mathf.Abs(local.z), rig.eyeBoxHalfExtents.z + 1e-3f, "z step " + i);
            }
            // A NaN from a broken body never reaches the camera transform.
            prop.SetValue(rig, new Vector3(float.NaN, 0f, 0f));
            rig.UpdateCab(0.033f);
            Vector3 p = rig.cam.transform.position;
            Assert.IsFalse(float.IsNaN(p.x) || float.IsNaN(p.y) || float.IsNaN(p.z));
            rig.ResetView();
            cab.localRotation = Quaternion.identity;
            rig.headGain = 0f;
            rig.UpdateCab(0.033f);
            Assert.That((rig.cam.transform.position - eye.position).magnitude, Is.LessThan(1e-4f), "ResetView re-centres the head");
        }

        [Test]
        public void CabSuspension_HardStops_HoldTheCabOnTheFrame()
        {
            var def = new CabSuspensionDefinition();
            var cab = new CabSuspension(def);
            double maxPitch = 0, maxRoll = 0;
            // 10 s of a tumbling fall: +-8 g specific force in the chassis frame, sign flipping at 3 Hz.
            for (int i = 0; i < 1000; i++)
            {
                double s = (i / 17) % 2 == 0 ? 1 : -1;
                cab.Update(new Vec3(80 * s, 0, -80 * s), 0.01);
                maxPitch = System.Math.Max(maxPitch, System.Math.Abs(cab.Pitch));
                maxRoll = System.Math.Max(maxRoll, System.Math.Abs(cab.Roll));
            }
            double lim = CabSuspension.HardStopFactor * MathUtil.Deg2Rad;
            Assert.LessOrEqual(maxPitch, def.maxPitchDeg * lim + 1e-9);
            Assert.LessOrEqual(maxRoll, def.maxRollDeg * lim + 1e-9);
            Assert.Greater(maxPitch, def.maxPitchDeg * MathUtil.Deg2Rad, "the excitation did reach the stops");
            // Normal driving stays on the springs: 0.6 g braking never touches the hard stop.
            var cab2 = new CabSuspension(def);
            for (int i = 0; i < 500; i++) cab2.Update(new Vec3(0, 0, -6), 0.01);
            Assert.Less(System.Math.Abs(cab2.Pitch), def.maxPitchDeg * lim * 0.999);
            Assert.Greater(cab2.Pitch, 0, "nose down under braking");
        }
    }
}
