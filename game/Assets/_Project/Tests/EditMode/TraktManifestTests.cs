using System.Collections.Generic;
using System.IO;
using Game.Editor.Build;
using Game.Editor.Setup;
using Game.Rendering;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using Json = Game.Editor.Setup.TruckAssetBuilder.Json;

namespace Game.Tests
{
    /// <summary>
    /// Track A7: the art manifests agree with the physics (ADR 0014) and with what the prefab builder assumes, and the cab
    /// fill reacts to the sun direction relative to the cab.
    /// </summary>
    public class TraktManifestTests
    {
        static Dictionary<string, object> Load(string rel) =>
            Json.Obj(Json.Parse(File.ReadAllText(Path.Combine(EditorTools.RepoRoot, rel))));

        static Vector3 V(object o) { var a = Json.Arr(o); return new Vector3((float)Json.Num(a[0]), (float)Json.Num(a[1]), (float)Json.Num(a[2])); }

        [Test]
        public void ExteriorRig_ParentsResolve_AndMatchThePhysics()
        {
            var m = Load("art-source/truck/exterior/export/truck_exterior_manifest.json");
            var lod0 = Json.Obj(Json.Obj(m["lods"])["LOD0"]);
            var objs = Json.Obj(lod0["objects"]);
            foreach (var kv in objs)
            {
                string rp = Json.Str(Json.Obj(kv.Value)["rig_parent"]);
                Assert.That(rp == "TruckExterior_LOD0" || objs.ContainsKey(rp), $"{kv.Key}: rig_parent {rp} unresolved");
            }
            var data = VehicleDataAsset.LoadDefault();
            var model = data.CreateModel();
            // Wheel centres (art) vs physics hardpoints: within 1 cm laterally and longitudinally (ADR 0014 track 2.04 / 1.82).
            foreach (var w in model.Wheels)
            {
                var hp = w.HardpointLocal.ToUnity();
                string role = "WHEEL_" + (hp.z > 1.85f ? "F" : "R") + (hp.x < 0 ? "L" : "R") + "_LOD0";
                var art = V(Json.Obj(objs[role])["pivot_unity_vehicle"]);
                Assert.AreEqual(art.x, hp.x, 0.011f, role + " x");
                Assert.AreEqual(art.z, hp.z, 0.011f, role + " z");
            }
            var mount = data.Vehicle.cab.mountCenter;
            var cab = V(Json.Obj(m["cab_body"])["unity_vehicle"]);
            Assert.AreEqual((float)mount.y, cab.y, 0.011f, "cab mount height");
            Assert.AreEqual((float)mount.z, cab.z, 0.011f, "cab mount z");
            var eye = V(Json.Obj(Json.Obj(lod0["empties"])["EYE_POINT"])["position_unity_vehicle"]);
            Assert.That((eye - new TractorDimensions().EyePointVehicle).magnitude, Is.LessThan(0.005f), "EYE_POINT = dims.json driver eye");
        }

        [Test]
        public void MainMirrors_FaceTheDriverEye()
        {
            var m = Load("art-source/truck/exterior/export/truck_exterior_manifest.json");
            var lod0 = Json.Obj(Json.Obj(m["lods"])["LOD0"]);
            var objs = Json.Obj(lod0["objects"]);
            var eye = V(Json.Obj(Json.Obj(lod0["empties"])["EYE_POINT"])["position_unity_vehicle"]);
            foreach (var name in new[] { "MIRROR_MainL_LOD0", "MIRROR_MainR_LOD0", "MIRROR_WideL_LOD0", "MIRROR_WideR_LOD0" })
            {
                var o = Json.Obj(objs[name]);
                var n = V(o["normal_unity_vehicle"]).normalized;
                var toEye = (eye - V(o["pivot_unity_vehicle"])).normalized;
                Assert.That(Vector3.Dot(n, toEye), Is.GreaterThan(0.2f), name + " glass faces the cab side");
                // The reflected line of sight looks rearwards (the mirror camera is set up on it).
                var r = Vector3.Reflect(-toEye, n);
                Assert.That(r.z, Is.LessThan(-0.7f), name + " shows the road behind");
            }
        }

        [Test]
        public void CabFill_FollowsSunThroughTheGlass()
        {
            var envGo = new GameObject("env");
            var cabGo = new GameObject("cab");
            try
            {
                var env = envGo.AddComponent<EnvironmentLighting>();
                var low = LightingPreset.CreateLowSun();
                env.presets = new[] { low };
                env.Apply();
                var fill = cabGo.AddComponent<CabInteriorLighting>();
                fill.cab = cabGo.transform;
                Vector3 sun = env.Model.SunDirection; sun.y = 0f;
                cabGo.transform.rotation = Quaternion.LookRotation(sun.normalized, Vector3.up);      // driving into the sun
                fill.Refresh(null);
                float ahead = fill.LastFill.y;
                cabGo.transform.rotation = Quaternion.LookRotation(-sun.normalized, Vector3.up);     // sun behind the cab
                fill.Refresh(null);
                float behind = fill.LastFill.y;
                Assert.That(behind, Is.GreaterThan(0f), "sky light through the glass still bounces");
                Assert.That(ahead, Is.GreaterThan(behind * 2f), "sun through the windscreen fills the cab");
                Object.DestroyImmediate(low);
            }
            finally
            {
                Object.DestroyImmediate(cabGo);
                Object.DestroyImmediate(envGo);
            }
        }
    }
}
