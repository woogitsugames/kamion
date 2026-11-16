using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text.RegularExpressions;
using Game.Editor.Build;
using Game.Editor.Setup;
using Game.Vehicle.Physics;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using Json = Game.Editor.Setup.TruckAssetBuilder.Json;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0280 §9 (D79): the visual trailer wheels sit on the physics axles of curtainsider_tridem_13_6.trailer.json
    /// (kingpin -> axles 6.32 / 7.63 / 8.94 m) within 1 cm - in the Blender export manifest (every LOD), in the exported
    /// LOD0 FBX geometry, in the graybox prefab (git) and in the generated art prefab (Assets/_Generated, when built).
    /// The shader default of the curtain soiling axles follows the same data.
    /// </summary>
    public class TrailerAxleSyncTests
    {
        const float Tol = 0.01f;   // 1 cm (task contract, ADR 0280 §9)
        const string DataAsset = "Assets/_Project/Vehicle/Runtime/Resources/VehicleData_Tractor4x2.asset";
        const string Manifest = "art-source/truck/trailer/export/trailer_manifest.json";
        const string GrayboxPrefab = "Assets/_Project/Vehicle/Runtime/Prefabs/Trailer_Curtainsider_Graybox.prefab";
        const string Shader = "Assets/_Project/Rendering/Shaders/TruckExterior.shader";
        const string TmpDir = "Assets/_TestTmp_TrailerAxles";

        static TrailerDefinition Def()
        {
            var data = AssetDatabase.LoadAssetAtPath<VehicleDataAsset>(DataAsset);
            Assert.That(data, Is.Not.Null, DataAsset);
            var def = data.Trailer;
            Assert.That(def.axles.Length, Is.EqualTo(3), "tridem");
            return def;
        }

        /// <summary>Physics wheel centre (x, z) for a role like WHEEL_2L (L = -x, Unity vehicle frame).</summary>
        static Vector2 PhysicsXZ(TrailerDefinition def, string role)
        {
            int axle = role[6] - '1';
            float half = (float)def.axles[axle].trackWidth * 0.5f;
            return new Vector2(role[7] == 'L' ? -half : half, (float)def.axles[axle].positionZ);
        }

        static void AssertNear(string what, Vector2 got, Vector2 want, List<string> errors)
        {
            float d = (got - want).magnitude;
            if (d > Tol) errors.Add($"{what}: ({got.x:F4}, {got.y:F4}) vs physics ({want.x:F4}, {want.y:F4}), {d * 100f:F1} cm");
        }

        static Dictionary<string, object> LoadManifest() =>
            Json.Obj(Json.Parse(File.ReadAllText(Path.Combine(EditorTools.RepoRoot, Manifest))));

        [OneTimeTearDown]
        public void Cleanup()
        {
            if (AssetDatabase.IsValidFolder(TmpDir)) AssetDatabase.DeleteAsset(TmpDir);
        }

        [Test]
        public void PhysicsAxles_AreTheD79Tridem()
        {
            var def = Def();
            // dims.json trailer_axle_z_m (SOURCED, ADR 0280 §7/§10): kingpin -> centre axle 7.63 m, spacing 1.31 m.
            Assert.That(def.axles[1].positionZ, Is.EqualTo(-7.63).Within(1e-6));
            Assert.That(def.axles[1].positionZ - def.axles[2].positionZ, Is.EqualTo(1.31).Within(1e-6));
            Assert.That(def.axles[0].positionZ - def.axles[1].positionZ, Is.EqualTo(1.31).Within(1e-6));
        }

        [Test]
        public void ManifestWheelPivots_MatchTrailerJson_AllLods()
        {
            var def = Def();
            var errors = new List<string>();
            int n = 0;
            foreach (var lod in Json.Obj(LoadManifest()["lods"]))
                foreach (var kv in Json.Obj(Json.Obj(lod.Value)["objects"]))
                {
                    var o = Json.Obj(kv.Value);
                    string role = Json.Str(o["role"]);
                    if (!role.StartsWith("WHEEL_")) continue;
                    var p = Json.Arr(o["pivot_unity_vehicle"]);
                    AssertNear($"{lod.Key} {kv.Key}", new Vector2((float)Json.Num(p[0]), (float)Json.Num(p[2])), PhysicsXZ(def, role), errors);
                    n++;
                }
            Assert.That(n, Is.EqualTo(18), "6 wheels x 3 LODs");
            Assert.That(errors, Is.Empty, string.Join("\n", errors));
        }

        [Test]
        public void ManifestPhysicsCrosscheck_AllRowsMatch()
        {
            // = tools/blender/truck/trailer/check_export.py ALLOWED_MISMATCH (documented owner decisions, not the axles)
            string[] allowed = { "tyre radius: mesh free", "cargo front z", "cargo height", "combination length" };
            var bad = new List<string>();
            int axleRows = 0;
            foreach (var r in Json.Arr(Json.Obj(LoadManifest()["physics_crosscheck"])["rows"]))
            {
                var row = Json.Obj(r);
                string item = Json.Str(row["item"]);
                if (item.StartsWith("axle ")) axleRows++;
                if (row["match"] is bool ok && ok) continue;
                bool doc = false;
                foreach (var a in allowed) doc |= item.StartsWith(a);
                if (!doc) bad.Add(item);
            }
            Assert.That(axleRows, Is.EqualTo(3), "axle 1..3 rows in physics_crosscheck");
            Assert.That(bad, Is.Empty, "physics_crosscheck mismatches: " + string.Join("; ", bad));
        }

        [Test]
        public void Lod0Fbx_WheelGeometry_CentredOnPhysicsAxles()
        {
            var lod0 = Json.Obj(Json.Obj(LoadManifest()["lods"])["LOD0"]);
            string src = Path.Combine(EditorTools.RepoRoot, Json.Str(lod0["file"]));
            Assert.That(File.Exists(src) && new FileInfo(src).Length > 1024, "missing FBX (or LFS pointer): " + src);
            Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, TmpDir));
            string dst = $"{TmpDir}/{Path.GetFileName(src)}";
            File.Copy(src, Path.Combine(EditorTools.ProjectRoot, dst), true);
            AssetDatabase.ImportAsset(dst, ImportAssetOptions.ForceSynchronousImport);
            var mi = (ModelImporter)AssetImporter.GetAtPath(dst);
            TruckAssetBuilder.ApplyModelSettings(mi);
            mi.materialImportMode = ModelImporterMaterialImportMode.None;
            mi.SaveAndReimport();
            AssertFbxOnAxles(dst);
        }

        /// <summary>The LOD0 FBX the art prefab was built from (TrailerAssetBuilder copy in Assets/_Generated, outside git).</summary>
        [Test]
        public void GeneratedLod0Fbx_UsedByArtPrefab_OnPhysicsAxles()
        {
            string p = "Assets/_Generated/Trailer/Source/SM_Trailer_LOD0.fbx";
            if (AssetDatabase.LoadAssetAtPath<GameObject>(p) == null) Assert.Ignore(p + " not built: run TrailerAssetBuilder.BuildBatch");
            AssertFbxOnAxles(p);
        }

        static void AssertFbxOnAxles(string assetPath)
        {
            var def = Def();
            var root = AssetDatabase.LoadAssetAtPath<GameObject>(assetPath);
            Assert.That(root, Is.Not.Null, assetPath);
            var errors = new List<string>();
            // AXLE_n empties (axle centre line, from the same AXLES list as the axle beams, mudguards and side guards)
            int axles = 0;
            foreach (var t in root.GetComponentsInChildren<Transform>(true))
            {
                var a = Regex.Match(t.name, @"^AXLE_([123])(_LOD0)?$");
                if (!a.Success) continue;
                Vector3 p = root.transform.InverseTransformPoint(t.position);
                float want = (float)def.axles[a.Groups[1].Value[0] - '1'].positionZ;
                if (Mathf.Abs(p.z - want) > Tol || Mathf.Abs(p.x) > Tol) errors.Add($"{assetPath} {t.name} at ({p.x:F4}, {p.z:F4}) vs axle z {want:F4}");
                axles++;
            }
            if (axles != 3) errors.Add($"{assetPath}: {axles} AXLE_n empties (want 3)");
            int n = 0;
            foreach (var mf in root.GetComponentsInChildren<MeshFilter>(true))
            {
                var m = Regex.Match(mf.name, @"^WHEEL_([123][LR])_LOD0$");
                if (!m.Success || mf.sharedMesh == null) continue;
                string role = "WHEEL_" + m.Groups[1].Value;
                var toRoot = root.transform.worldToLocalMatrix * mf.transform.localToWorldMatrix;
                Vector3 pivot = toRoot.MultiplyPoint3x4(Vector3.zero);
                Vector3 centre = toRoot.MultiplyPoint3x4(mf.sharedMesh.bounds.center);
                var want = PhysicsXZ(def, role);
                AssertNear(role + " pivot", new Vector2(pivot.x, pivot.z), want, errors);
                // the tyre + rim mesh is symmetric about its spin axis only in z: the bounds centre z is the axle line
                if (Mathf.Abs(centre.z - want.y) > Tol) errors.Add($"{role} mesh centre z {centre.z:F4} vs axle {want.y:F4}");
                n++;
            }
            Assert.That(n, Is.EqualTo(6), "WHEEL_*_LOD0 meshes in the FBX");
            Assert.That(errors, Is.Empty, string.Join("\n", errors));
        }

        [Test]
        public void GrayboxPrefab_WheelSpinners_OnPhysicsAxles()
        {
            var def = Def();
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(GrayboxPrefab);
            Assert.That(prefab, Is.Not.Null, GrayboxPrefab);
            AssertSpinners(prefab, def, "graybox");
        }

        [Test]
        public void ArtPrefab_WheelSpinners_OnPhysicsAxles()
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(TrailerAssetBuilder.PrefabPath);
            if (prefab == null) Assert.Ignore(TrailerAssetBuilder.PrefabPath + " not built (outside git): run TrailerAssetBuilder.BuildBatch");
            var def = Def();
            AssertSpinners(prefab, def, "art");
            // the art wheel meshes hang under the physics spinners with zero offset: their bounds centre (z) is the axle line
            var vis = prefab.GetComponent<TrailerVisuals>();
            var errors = new List<string>();
            int n = 0;
            foreach (var spin in vis.wheelSpinners)
                foreach (var mf in spin.GetComponentsInChildren<MeshFilter>(true))
                {
                    if (mf.sharedMesh == null) continue;
                    var toRoot = prefab.transform.worldToLocalMatrix * mf.transform.localToWorldMatrix;
                    Vector3 c = toRoot.MultiplyPoint3x4(mf.sharedMesh.bounds.center);
                    Vector3 s = prefab.transform.InverseTransformPoint(spin.position);
                    if (Mathf.Abs(c.z - s.z) > Tol || Mathf.Abs(Mathf.Abs(c.x) - Mathf.Abs(s.x)) > 0.25f)
                        errors.Add($"{mf.name}: mesh centre ({c.x:F3}, {c.z:F3}) vs spinner ({s.x:F3}, {s.z:F3})");
                    n++;
                }
            Assert.That(n, Is.GreaterThanOrEqualTo(18), "6 wheels x 3 LODs under the spinners");
            Assert.That(errors, Is.Empty, string.Join("\n", errors));
        }

        static void AssertSpinners(GameObject prefab, TrailerDefinition def, string what)
        {
            var vis = prefab.GetComponent<TrailerVisuals>();
            Assert.That(vis, Is.Not.Null, what + ": TrailerVisuals");
            Assert.That(vis.wheelSpinners.Length, Is.EqualTo(6), what + ": spinners");
            var errors = new List<string>();
            var hit = new bool[3];
            foreach (var spin in vis.wheelSpinners)
            {
                Vector3 p = prefab.transform.InverseTransformPoint(spin.position);
                int best = 0;
                for (int a = 1; a < 3; a++)
                    if (Mathf.Abs(p.z - (float)def.axles[a].positionZ) < Mathf.Abs(p.z - (float)def.axles[best].positionZ)) best = a;
                hit[best] = true;
                string role = $"WHEEL_{best + 1}{(p.x < 0f ? 'L' : 'R')}";
                AssertNear($"{what} {spin.parent.name}", new Vector2(p.x, p.z), PhysicsXZ(def, role), errors);
            }
            Assert.That(hit, Is.All.True, what + ": every axle has wheels");
            Assert.That(errors, Is.Empty, string.Join("\n", errors));
        }

        [Test]
        public void TruckExteriorShader_CurtainAxlesDefault_MatchesTrailerJson()
        {
            var def = Def();
            string text = File.ReadAllText(Path.Combine(EditorTools.ProjectRoot, Shader));
            var m = Regex.Match(text, @"_CurtainAxles\s*\("".*?""\s*,\s*Vector\)\s*=\s*\(([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)");
            Assert.That(m.Success, "_CurtainAxles property not found in " + Shader);
            for (int i = 0; i < 3; i++)
                Assert.That(double.Parse(m.Groups[i + 1].Value, CultureInfo.InvariantCulture), Is.EqualTo(def.axles[i].positionZ).Within(1e-4), $"_CurtainAxles[{i}]");
        }
    }
}
