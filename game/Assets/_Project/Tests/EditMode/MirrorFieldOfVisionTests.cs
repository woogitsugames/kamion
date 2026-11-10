using System.Collections.Generic;
using System.IO;
using Game.Editor.Build;
using Game.Editor.Setup;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using Json = Game.Editor.Setup.TruckAssetBuilder.Json;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// Review r6 C-N8: every mirror of the modern cab, as placed by TruckAssetBuilder (art glass + MirrorAim adjustment,
    /// MirrorOptics camera), covers its UN ECE R46 field of vision from the design eye point. Fields: UN Regulation No 46,
    /// para 15.2.4.2 (class II), 15.2.4.4 (IV), 15.2.4.5 (V), 15.2.4.6 (VI) (OJ EU L 237, 8.8.2014, consolidated text).
    /// Flat road y = 0, outermost vehicle side = trailer half width 1.275 m (2.55 m, WORKING_VALUE), front = TractorDimensions.
    /// Own-vehicle occlusion is not modelled here (the control frames cab-mirrors-* show it).
    /// </summary>
    public class MirrorFieldOfVisionTests
    {
        const float Side = 1.275f;

        static Vector3 V(object o) { var a = Json.Arr(o); return new Vector3((float)Json.Num(a[0]), (float)Json.Num(a[1]), (float)Json.Num(a[2])); }

        static Dictionary<string, MirrorOptics.View> Views(out Vector3 eye, out Dictionary<string, float> adjust)
        {
            var m = Json.Obj(Json.Parse(File.ReadAllText(Path.Combine(EditorTools.RepoRoot, "art-source/truck/exterior/export/truck_exterior_manifest.json"))));
            var lod0 = Json.Obj(Json.Obj(m["lods"])["LOD0"]);
            eye = V(Json.Obj(Json.Obj(lod0["empties"])["EYE_POINT"])["position_unity_vehicle"]);
            var views = new Dictionary<string, MirrorOptics.View>();
            adjust = new Dictionary<string, float>();
            foreach (var kv in Json.Obj(lod0["objects"]))
            {
                var o = Json.Obj(kv.Value);
                string role = Json.Str(o["role"]);
                if (!role.StartsWith("MIRROR_")) continue;
                Vector3 q = V(o["pivot_unity_vehicle"]), n = V(o["normal_unity_vehicle"]).normalized;
                Vector3 up = V(Json.Obj(o["axes_unity_vehicle"])["Y"]).normalized;
                var size = Json.Arr(o["size_m"]);
                var turn = TruckAssetBuilder.MirrorAdjustment(role, eye, q, n, Quaternion.identity, out float ang, out bool clamped);
                Assert.IsFalse(clamped, $"{role}: adjustment {ang:F1} deg is outside the adjuster range; re-aim the modelled glass");
                adjust[role] = ang;
                views[role] = MirrorOptics.Build(eye, q, turn * n, turn * up, (float)Json.Num(size[0]), (float)Json.Num(size[1]), TruckAssetBuilder.MirrorRadius(role));
            }
            Assert.AreEqual(6, views.Count, "six mirror glasses in the manifest");
            return views;
        }

        static void Covers(MirrorOptics.View v, string what, float x0, float x1, float z0, float z1)
        {
            float c = MirrorOptics.GroundCoverage(v, Mathf.Min(x0, x1), Mathf.Max(x0, x1), Mathf.Min(z0, z1), Mathf.Max(z0, z1));
            Assert.GreaterOrEqual(c, 0.999f, $"{what}: {c * 100f:F1} % of the R46 field in view");
        }

        [Test]
        public void ClassII_and_IV_BothSides_CoverR46()
        {
            var v = Views(out var eye, out _);
            float ez = eye.z;
            foreach (var (s, side) in new[] { (-1f, "L"), (1f, "R") })
            {
                // II: 5 m wide from 30 m behind the ocular points (to the horizon; checked to 60 m) + 1 m wide from 4 m behind.
                Covers(v["MIRROR_Main" + side], "II " + side + " 5 m @ 30-60 m", s * Side, s * (Side + 5f), ez - 30f, ez - 60f);
                Covers(v["MIRROR_Main" + side], "II " + side + " 1 m @ 4-30 m", s * Side, s * (Side + 1f), ez - 4f, ez - 30f);
                // IV: 15 m wide from 10 to 25 m behind + 4.5 m wide from 1.5 m behind.
                Covers(v["MIRROR_Wide" + side], "IV " + side + " 15 m @ 10-25 m", s * Side, s * (Side + 15f), ez - 10f, ez - 25f);
                Covers(v["MIRROR_Wide" + side], "IV " + side + " 4.5 m @ 1.5-10 m", s * Side, s * (Side + 4.5f), ez - 1.5f, ez - 10f);
            }
        }

        [Test]
        public void ClassV_SeesTheGroundBesideThePassengerDoor()
        {
            var v = Views(out var eye, out _);
            float front = new TractorDimensions().FrontFaceZ;
            // V: 2 m outside the passenger-side cab plane, from 1.75 m behind to 1 m ahead of the ocular points (bumper if nearer).
            Covers(v["MIRROR_Kerb"], "V", Side, Side + 2f, eye.z - 1.75f, Mathf.Min(eye.z + 1f, front));
            Assert.Less(Vector3.Dot(v["MIRROR_Kerb"].forward, Vector3.up), -0.5f, "kerb mirror looks down");
        }

        [Test]
        public void ClassVI_LooksAtTheRoadInFront_NotTheSky()
        {
            var v = Views(out _, out _);
            float front = new TractorDimensions().FrontFaceZ;
            var f = v["MIRROR_Front"];
            Assert.Less(Mathf.Asin(f.forward.y) * Mathf.Rad2Deg, -30f, "front mirror axis must point at the road");
            Assert.Less(Mathf.Asin(f.forward.y) * Mathf.Rad2Deg + f.HalfVDeg, 0f, "no sky in the front mirror (upper edge below the horizon)");
            // VI: from the front plane 2 m ahead, from the driver-side plane to 2 m outside the passenger side.
            Covers(f, "VI", -Side, Side + 2f, front, front + 2f);
        }
    }
}
