using System.Collections.Generic;
using System.IO;
using System.Text;
using Game.Editor.Build;
using Game.Editor.Setup;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEngine;
using Json = Game.Editor.Setup.TruckAssetBuilder.Json;

namespace Game.Tests.EditMode
{
    /// <summary>
    /// drive-feel-s24 (D93 pkt 3, ADR 0312): on a bend or a roundabout the driver must see the trailer's wheels on the inside
    /// of the turn in the class II (main) or class IV (wide-angle) mirror of that side. Geometry: the mirrors as placed by
    /// TruckAssetBuilder (art glass + MirrorAim + MirrorOptics, the same construction as MirrorFieldOfVisionTests), the
    /// fifth wheel of tractor_4x2_generic.vehicle.json (z 0.68 m, vehicle frame: ground under the rear axle) and the tridem
    /// of curtainsider_tridem_13_6.trailer.json (axles 6.32 / 7.63 / 8.94 m behind the kingpin, track 2.04 m; tyre 385/65 R22.5,
    /// radius 0.515 m, half width 0.19 m). Articulation = trailer yaw relative to the tractor (+ = trailer rear swung to the
    /// left = a left turn). Own-vehicle occlusion is not modelled (the cab-mirrors-* control frames show it). Writes the
    /// table to artifacts/drive-feel-s24/mirror_trailer_visibility.csv.
    /// </summary>
    public class MirrorTrailerVisibilityTests
    {
        const float KingpinZ = 0.68f, Track = 2.04f, TyreR = 0.515f, TyreHalfW = 0.19f;
        static readonly float[] AxleBehindKingpin = { 6.32f, 7.63f, 8.94f };

        static Vector3 V(object o) { var a = Json.Arr(o); return new Vector3((float)Json.Num(a[0]), (float)Json.Num(a[1]), (float)Json.Num(a[2])); }

        static Dictionary<string, MirrorOptics.View> Views()
        {
            var m = Json.Obj(Json.Parse(File.ReadAllText(Path.Combine(EditorTools.RepoRoot, "art-source/truck/exterior/export/truck_exterior_manifest.json"))));
            var lod0 = Json.Obj(Json.Obj(m["lods"])["LOD0"]);
            var eye = V(Json.Obj(Json.Obj(lod0["empties"])["EYE_POINT"])["position_unity_vehicle"]);
            var views = new Dictionary<string, MirrorOptics.View>();
            foreach (var kv in Json.Obj(lod0["objects"]))
            {
                var o = Json.Obj(kv.Value);
                string role = Json.Str(o["role"]);
                if (!role.StartsWith("MIRROR_")) continue;
                Vector3 q = V(o["pivot_unity_vehicle"]), n = V(o["normal_unity_vehicle"]).normalized;
                Vector3 up = V(Json.Obj(o["axes_unity_vehicle"])["Y"]).normalized;
                var size = Json.Arr(o["size_m"]);
                var turn = TruckAssetBuilder.MirrorAdjustment(role, eye, q, n, Quaternion.identity, out _, out _);
                views[role] = MirrorOptics.Build(eye, q, turn * n, turn * up, (float)Json.Num(size[0]), (float)Json.Num(size[1]), TruckAssetBuilder.MirrorRadius(role));
            }
            return views;
        }

        /// <summary>Outer face of the inside trailer wheel of an axle at wheel-centre height and at the ground, tractor frame.</summary>
        static void InsideWheel(float articulationDeg, float behindKingpin, out Vector3 centre, out Vector3 contact)
        {
            float side = articulationDeg >= 0f ? -1f : 1f;   // left turn: trailer rear swings left, inside = left (-X)
            var rot = Quaternion.Euler(0f, articulationDeg, 0f);   // Unity +Y rotation maps -Z to -X: +articulation swings the trailer rear left
            Vector3 local = new Vector3(side * (0.5f * Track + TyreHalfW), 0f, -behindKingpin);
            Vector3 k = new Vector3(0f, 0f, KingpinZ);
            Vector3 p = k + rot * local;
            centre = new Vector3(p.x, TyreR, p.z);
            contact = new Vector3(p.x, 0.05f, p.z);
        }

        static bool SeesWheel(MirrorOptics.View v, float art, float behind)
        {
            InsideWheel(art, behind, out var c, out var g);
            return MirrorOptics.Sees(v, c) || MirrorOptics.Sees(v, g);
        }

        /// <summary>The class II view turned outward by <paramref name="yawOutDeg"/> about its own up axis, as
        /// RenderTextureMirror.AdjustEuler does to the camera (left: +yaw local = towards vehicle -X).</summary>
        static MirrorOptics.View Panned(MirrorOptics.View v, bool left, float yawOutDeg)
        {
            var q = Quaternion.AngleAxis(left ? yawOutDeg : -yawOutDeg, v.up);
            v.forward = q * v.forward; v.right = q * v.right;
            return v;
        }

        /// <summary>Smallest outward pan [deg, 0.5 steps, -10..40] that puts the inside wheel of the last axle in class II; NaN = none.</summary>
        static float RequiredPan(MirrorOptics.View v, bool left, float art)
        {
            for (float y = -10f; y <= 40f; y += 0.5f)
                if (SeesWheel(Panned(v, left, Mathf.Abs(y) < 1e-4f ? 0f : y), left ? art : -art, AxleBehindKingpin[2])) return y;
            return float.NaN;
        }

        [Test]
        public void TrailerPan_KeepsLastAxleInClassII_UpTo45Deg_AndLeavesTheR46AimAtZero()
        {
            var v = Views();
            var csv = new StringBuilder("articulation_deg,side,required_pan_deg,shipped_pan_deg,class_II_with_pan\n");
            var fails = new List<string>();
            foreach (float art in new[] { 0f, 5f, 10f, 15f, 20f, 25f, 30f, 35f, 40f, 45f, 50f, 55f, 60f })
            foreach (bool left in new[] { true, false })
            {
                int phase = left ? 0 : 1;
                float artLeft = left ? art : -art;
                float pan = RenderTextureMirror.TrailerPanDeg(phase, artLeft, RenderTextureMirror.TrailerPanGain,
                    RenderTextureMirror.TrailerPanStartDeg, RenderTextureMirror.TrailerPanMaxDeg);
                var mv = v[left ? "MIRROR_MainL" : "MIRROR_MainR"];
                bool ok = SeesWheel(Panned(mv, left, pan), artLeft, AxleBehindKingpin[2]);
                csv.AppendLine(string.Format(System.Globalization.CultureInfo.InvariantCulture, "{0:F0},{1},{2:F1},{3:F1},{4}",
                    art, left ? "L" : "R", RequiredPan(mv, left, art), pan, ok ? 1 : 0));
                if (art >= 5f && art <= 45f && !ok) fails.Add($"{(left ? "L" : "R")} {art} deg (pan {pan:F1})");
                // The outside mirror never moves.
                Assert.AreEqual(0f, RenderTextureMirror.TrailerPanDeg(1 - phase, artLeft, RenderTextureMirror.TrailerPanGain,
                    RenderTextureMirror.TrailerPanStartDeg, RenderTextureMirror.TrailerPanMaxDeg), "outside mirror pans");
            }
            Assert.AreEqual(0f, RenderTextureMirror.TrailerPanDeg(0, 0f, 0.7f, 20f, 25f), "straight: R46 aim untouched");
            Assert.AreEqual(0f, RenderTextureMirror.TrailerPanDeg(0, float.NaN, 0.7f, 20f, 25f), "NaN: no pan");
            string dir = Path.Combine(EditorTools.RepoRoot, "artifacts", "drive-feel-s24");
            Directory.CreateDirectory(dir);
            File.WriteAllText(Path.Combine(dir, "mirror_trailer_pan.csv"), csv.ToString());
            Debug.Log("[MIRROR-TRAILER-PAN]\n" + csv);
            Assert.IsEmpty(fails, "last trailer axle not in class II with the shipped pan: " + string.Join(", ", fails));
        }

        [Test]
        public void InsideTrailerWheels_VisibleInClassIIorIV_OnBendsAndRoundabouts()
        {
            var v = Views();
            var csv = new StringBuilder("articulation_deg,side,axle_m_behind_kingpin,class_II,class_IV\n");
            var fails = new List<string>();
            foreach (float art in new[] { 0f, 5f, 10f, 15f, 20f, 25f, 30f, 35f, 40f, 45f, 50f, 55f, 60f })
            foreach (float sgn in new[] { 1f, -1f })
            {
                string side = sgn > 0 ? "L" : "R";
                bool anyRear = false;
                foreach (float behind in AxleBehindKingpin)
                {
                    bool ii = SeesWheel(v["MIRROR_Main" + side], sgn * art, behind);
                    bool iv = SeesWheel(v["MIRROR_Wide" + side], sgn * art, behind);
                    csv.AppendLine(string.Format(System.Globalization.CultureInfo.InvariantCulture, "{0:F0},{1},{2:F2},{3},{4}", art, side, behind, ii ? 1 : 0, iv ? 1 : 0));
                    if (behind == AxleBehindKingpin[2]) anyRear = ii || iv;
                }
                // Required (WORKING_VALUE): the last trailer axle's inside wheel in II or IV up to 45 deg (R = 12.5 m ring
                // steady state is ~35-40 deg for this trailer; 45 = tight roundabout / yard margin).
                if (art <= 45f && !anyRear) fails.Add($"{side} {art} deg");
            }
            string dir = Path.Combine(EditorTools.RepoRoot, "artifacts", "drive-feel-s24");
            Directory.CreateDirectory(dir);
            File.WriteAllText(Path.Combine(dir, "mirror_trailer_visibility.csv"), csv.ToString());
            Debug.Log("[MIRROR-TRAILER]\n" + csv);
            Assert.IsEmpty(fails, "inside wheel of the last trailer axle not in class II/IV: " + string.Join(", ", fails));
        }
    }
}
