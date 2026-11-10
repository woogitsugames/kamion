using System.IO;
using Game.Cameras;
using Game.Editor.Build;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using Json = Game.Editor.Setup.TruckAssetBuilder.Json;

namespace Game.Tests
{
    /// <summary>ADR 0052: the cab camera sits at the driver eye point = seat H-point + 0.635 m (UNECE R46), on the sprung cab.</summary>
    public class DriverSeatCameraTests
    {
        static Vector3 V(object o) { var a = Json.Arr(o); return new Vector3((float)Json.Num(a[0]), (float)Json.Num(a[1]), (float)Json.Num(a[2])); }

        GameObject m_Root;
        [TearDown] public void TearDown() { if (m_Root != null) Object.DestroyImmediate(m_Root); }

        [Test]
        public void Dims_EyeIsHPointPlus635mm_Vertical()
        {
            var d = new TractorDimensions();
            Vector3 off = d.EyePointVehicle - d.HPointVehicle;
            Assert.AreEqual(0f, off.x, 1e-4f); Assert.AreEqual(0f, off.z, 1e-4f);
            Assert.AreEqual(0.635f, off.y, 1e-4f, "UNECE R46 ocular point above the R-point");
            Assert.AreEqual(d.driverEyeAboveHPoint, off.y, 1e-4f);
        }

        [Test]
        public void InteriorManifest_HPoint_And_EyePoint_MatchDims()
        {
            var m = Json.Obj(Json.Parse(File.ReadAllText(Path.Combine(EditorTools.RepoRoot, "art-source/truck/interior/export/cab_interior_manifest.json"))));
            var lod0 = Json.Obj(Json.Obj(m["lods"])["LOD0"]);
            var emp = Json.Obj(lod0["empties_unity_local"]);
            Vector3 eye = V(emp["EYE_POINT"]), h = V(emp["H_POINT"]);
            Assert.That((eye - h - new Vector3(0f, 0.635f, 0f)).magnitude, Is.LessThan(0.002f), "interior EYE_POINT - H_POINT");
            // Cab-local -> vehicle frame: + cab mount (dims: cab_mount_height 1.15, cab_mount_z 3.925).
            var mount = new Vector3(0f, 1.15f, 3.925f);
            var d = new TractorDimensions();
            Assert.That((h + mount - d.HPointVehicle).magnitude, Is.LessThan(0.005f), "interior H_POINT = dims H-point");
            Assert.That((eye + mount - d.EyePointVehicle).magnitude, Is.LessThan(0.005f), "interior EYE_POINT = dims eye");
        }

        (CameraRig rig, Transform cab, Transform eye) BuildRig()
        {
            m_Root = new GameObject("rig_test");
            var truck = new GameObject("truck").transform; truck.SetParent(m_Root.transform, false);
            var cab = new GameObject("cabPivot").transform; cab.SetParent(truck, false);
            cab.localPosition = new Vector3(0f, 1.15f, 3.925f);
            var eye = new GameObject("DriverEyePoint").transform; eye.SetParent(cab, false);
            eye.localPosition = new TractorDimensions().EyePointVehicle - cab.localPosition;
            var camGo = new GameObject("cam", typeof(Camera)); camGo.transform.SetParent(m_Root.transform, false);
            var rig = camGo.AddComponent<CameraRig>();
            rig.cam = camGo.GetComponent<Camera>(); rig.target = truck; rig.eyeAnchor = eye; rig.mode = CameraMode.Cab;
            rig.headGain = 0f;
            return (rig, cab, eye);
        }

        [Test]
        public void CabCamera_AtEyePoint_AtRest_AndFollowsTheSprungCab()
        {
            var (rig, cab, eye) = BuildRig();
            rig.UpdateCab(0.016f);
            Assert.That((rig.cam.transform.position - eye.position).magnitude, Is.LessThan(1e-4f), "camera at the eye anchor");
            Assert.AreEqual(DriverHead.RestPitchDownDeg, rig.cam.transform.eulerAngles.x, 1e-3f, "rest gaze");
            // Cab pitched 2 deg and rolled 1.5 deg on its mounts: the camera moves with the cab, not the chassis.
            cab.localRotation = Quaternion.Euler(2f, 0f, 1.5f);
            cab.localPosition += new Vector3(0f, 0.02f, 0f);
            rig.UpdateCab(0.016f);
            Assert.That((rig.cam.transform.position - eye.position).magnitude, Is.LessThan(1e-4f));
            Assert.That(Quaternion.Angle(cab.rotation * Quaternion.Euler(DriverHead.RestPitchDownDeg, 0f, 0f), rig.cam.transform.rotation), Is.LessThan(0.01f));
            // Seat H-point is 0.635 m under the camera along the cab's up axis.
            Vector3 hWorld = eye.position - cab.up * 0.635f;
            Assert.AreEqual(0.635f, Vector3.Distance(hWorld, rig.cam.transform.position), 1e-4f);
        }

        [Test]
        public void LookAround_IsClampedToNeckLimits_AndTurnsAboutTheNeck()
        {
            var (rig, _, eye) = BuildRig();
            rig.AddLookDelta(new Vector2(100000f, 100000f));   // drag up = look up
            Assert.AreEqual(DriverHead.YawLimitDeg, rig.LookYaw, 1e-4f);
            Assert.AreEqual(-DriverHead.PitchUpLimitDeg, rig.LookPitch, 1e-4f);
            rig.AddLookDelta(new Vector2(-1000000f, -1000000f));
            Assert.AreEqual(-DriverHead.YawLimitDeg, rig.LookYaw, 1e-4f);
            Assert.AreEqual(DriverHead.PitchDownLimitDeg, rig.LookPitch, 1e-4f);
            Assert.LessOrEqual(DriverHead.YawLimitDeg, 100f, "no more than a neck plus a little torso twist");
            rig.UpdateCab(0.016f);
            // Eye parallax from the neck pivot: a few cm, never more than the head's own size.
            float moved = (rig.cam.transform.position - eye.position).magnitude;
            Assert.That(moved, Is.GreaterThan(0.01f).And.LessThan(0.25f));
            // Sway stays small (limited head motion, no motion sickness).
            Assert.LessOrEqual(rig.headMaxOffset, 0.05f);
        }

        [Test]
        public void LookAround_Returns_ToTheEyePoint()
        {
            var (rig, _, eye) = BuildRig();
            rig.AddLookDelta(new Vector2(300f, 0f));
            for (int i = 0; i < 400; i++) rig.UpdateCab(0.016f);
            Assert.AreEqual(0f, rig.LookYaw, 1e-3f);
            Assert.That((rig.cam.transform.position - eye.position).magnitude, Is.LessThan(1e-4f));
        }
    }
}
