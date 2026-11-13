using System.Collections.Generic;
using System.IO;
using Game.Editor.Build;
using Game.Editor.Setup;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using Json = Game.Editor.Setup.TruckAssetBuilder.Json;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0175 (appearance vs UN R48 / WT): the exported LOD0 meshes carry the lamp groups the rules ask for - two reversing
    /// lamps on the semi-trailer, rear fog lamps in their own light group (14, not the front fog group 11), a single rear fog
    /// lamp on the tractor's driver side - and TruckLights drives group 14. Positions and distances are checked on the
    /// generator output by tools/blender/truck/regs_check.py (tests/physics/test_truck_regs.py).
    /// </summary>
    public class TruckRegulationLampTests
    {
        const string ExtManifest = "art-source/truck/exterior/export/truck_exterior_manifest.json";
        const string TrlManifest = "art-source/truck/trailer/export/trailer_manifest.json";
        const string TmpDir = "Assets/_TestTmp_RegLamps";
        const int Reverse = 7, FogFront = 11, Plate = 13, FogRear = 14, Reflex = 15;

        static Dictionary<string, object> Load(string rel) =>
            Json.Obj(Json.Parse(File.ReadAllText(Path.Combine(EditorTools.RepoRoot, rel))));

        [OneTimeTearDown]
        public void Cleanup()
        {
            if (AssetDatabase.IsValidFolder(TmpDir)) AssetDatabase.DeleteAsset(TmpDir);
        }

        [TestCase(ExtManifest), TestCase(TrlManifest)]
        public void Manifest_LightGroupIds_AreSharedByTractorAndTrailer(string manifest)
        {
            var groups = Json.Obj(Json.Obj(Load(manifest)["shader_contract"])["light_groups"]);
            Assert.AreEqual("REVERSE", Json.Str(groups[Reverse.ToString()]));
            Assert.AreEqual("FOG", Json.Str(groups[FogFront.ToString()]));
            Assert.AreEqual("PLATE", Json.Str(groups[Plate.ToString()]));
            Assert.AreEqual("FOG_REAR", Json.Str(groups[FogRear.ToString()]));
            Assert.LessOrEqual(groups.Count, 16, "TruckLights state texture is 16 x 1");
        }

        /// <summary>Lamp-emitter vertices (uv2.y > 0) of one light group in the root frame, all meshes of the LOD0 FBX.</summary>
        static List<Vector3> Emitters(string manifest, string tmpName, int group) => GroupVerts(manifest, "LOD0", tmpName, group, true);

        /// <summary>Vertices of one light group (uv2.x) in the root frame; emitting = only uv2.y > 0, else only uv2.y == 0.</summary>
        static List<Vector3> GroupVerts(string manifest, string lod, string tmpName, int group, bool emitting)
        {
            string src = Path.Combine(EditorTools.RepoRoot, Json.Str(Json.Obj(Json.Obj(Load(manifest)["lods"])[lod])["file"]));
            Assert.That(File.Exists(src) && new FileInfo(src).Length > 1024, "missing FBX (or LFS pointer): " + src);
            Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, TmpDir));
            string dst = $"{TmpDir}/{tmpName}.fbx";
            if (AssetDatabase.LoadAssetAtPath<GameObject>(dst) == null)
            {
                File.Copy(src, Path.Combine(EditorTools.ProjectRoot, dst), true);
                AssetDatabase.ImportAsset(dst, ImportAssetOptions.ForceSynchronousImport);
                var mi = (ModelImporter)AssetImporter.GetAtPath(dst);
                TruckAssetBuilder.ApplyModelSettings(mi);
                mi.materialImportMode = ModelImporterMaterialImportMode.None;
                mi.SaveAndReimport();
            }
            var root = AssetDatabase.LoadAssetAtPath<GameObject>(dst);
            Assert.That(root, Is.Not.Null, dst);
            var pts = new List<Vector3>();
            var data = new List<Vector2>();
            foreach (var mf in root.GetComponentsInChildren<MeshFilter>(true))
            {
                var mesh = mf.sharedMesh;
                if (mesh == null || mf.name.StartsWith("COL_")) continue;
                mesh.GetUVs(2, data);
                if (data.Count == 0) continue;
                var v = mesh.vertices;
                var toRoot = root.transform.worldToLocalMatrix * mf.transform.localToWorldMatrix;
                for (int i = 0; i < v.Length; i++)
                    if ((data[i].y > 0.01f) == emitting && Mathf.Abs(data[i].x - group) < 0.25f) pts.Add(toRoot.MultiplyPoint3x4(v[i]));
            }
            return pts;
        }

        [Test]
        public void Trailer_HasTwoReversingLamps_AndRearFogInItsOwnGroup()
        {
            var rev = Emitters(TrlManifest, "Trailer_LOD0", Reverse);
            Assert.That(rev.Exists(p => p.x < -0.3f), "no reversing lamp on the left (UN R48 6.4.2.2: two on trailers longer than 6 m)");
            Assert.That(rev.Exists(p => p.x > 0.3f), "no reversing lamp on the right");
            foreach (var p in rev) Assert.That(p.y, Is.InRange(0.25f, 1.20f), "reversing lamp height (R48 6.4.4.2)");
            var fog = Emitters(TrlManifest, "Trailer_LOD0", FogRear);
            Assert.That(fog.Count, Is.GreaterThan(0), "no rear fog lamp in light group 14");
            Assert.That(fog.Exists(p => p.x < -0.3f), "a rear fog lamp must be on the driver's (left) side (R48 6.11.4.1)");
            foreach (var p in fog) Assert.That(p.y, Is.InRange(0.25f, 1.00f), "rear fog lamp height (R48 6.11.4.2)");
            Assert.That(Emitters(TrlManifest, "Trailer_LOD0", FogFront).Count, Is.EqualTo(0), "the trailer has no FRONT fog lamps (group 11)");
        }

        /// <summary>Review s17 P0: the Low tier renders LOD2 at every distance. The rear contour (R48 6.21 / R104), the class III
        /// triangles and the reflectors must exist there, tagged REFLEX (15) and never emissive.</summary>
        [Test]
        public void Trailer_LOD2_KeepsRearContourAndReflectors_AsNonEmissiveReflex()
        {
            var groups = Json.Obj(Json.Obj(Load(TrlManifest)["shader_contract"])["light_groups"]);
            Assert.AreEqual("REFLEX", Json.Str(groups[Reflex.ToString()]));
            Assert.AreEqual(0, GroupVerts(TrlManifest, "LOD2", "Trailer_LOD2", Reflex, true).Count, "a retro-reflector must not emit");
            var refl = GroupVerts(TrlManifest, "LOD2", "Trailer_LOD2", Reflex, false);
            float zMin = float.MaxValue;
            foreach (var p in refl) zMin = Mathf.Min(zMin, p.z);
            var rear = refl.FindAll(p => p.z < zMin + 0.3f);
            Assert.That(rear.Exists(p => p.x < -1.1f && p.y > 3.0f), "rear contour, left upper corner missing at LOD2");
            Assert.That(rear.Exists(p => p.x > 1.1f && p.y > 3.0f), "rear contour, right upper corner missing at LOD2");
            Assert.That(rear.Exists(p => p.y > 3.85f && p.x < -1.0f) && rear.Exists(p => p.y > 3.85f && p.x > 1.0f), "rear contour header missing at LOD2");
            Assert.That(refl.Exists(p => p.y < 0.8f && Mathf.Abs(p.x) > 0.5f), "rear triangle reflectors missing at LOD2");
            Assert.That(refl.Exists(p => Mathf.Abs(p.x) > 1.2f && p.y < 1.3f && p.z > zMin + 2f), "side reflectors missing at LOD2");
        }

        [Test]
        public void Tractor_HasOneRearFogLamp_OnTheDriverSide()
        {
            var fog = Emitters(ExtManifest, "TruckExterior_LOD0", FogRear);
            Assert.That(fog.Count, Is.GreaterThan(0), "no rear fog lamp on the tractor (UN R48 6.11: mandatory)");
            foreach (var p in fog)
            {
                Assert.That(p.x, Is.LessThan(-0.3f), "single rear fog lamp: driver's side (left)");
                Assert.That(p.z, Is.LessThan(-0.5f), "rear fog lamp sits at the frame end, behind the rear axle");
                Assert.That(p.y, Is.InRange(0.25f, 1.00f), "rear fog lamp height (R48 6.11.4.2)");
            }
        }

        [Test]
        public void TruckLights_RearFog_DrivesGroup14_OnlyWithTheDippedBeam()
        {
            var oldTex = Shader.GetGlobalTexture("_TruckLightState");
            float oldScale = Shader.GetGlobalFloat("_TruckLightNitsScale");
            var go = new GameObject("Rear fog test");
            try
            {
                var lights = go.AddComponent<TruckLights>();
                lights.forceLowBeam = true; lights.rearFog = false; lights.Refresh();
                Assert.AreEqual(0f, lights.StateTexture.GetPixel(FogRear, 0).r, 1e-6f);
                lights.rearFog = true; lights.Refresh();
                var c = lights.StateTexture.GetPixel(FogRear, 0);
                Assert.Greater(c.r * TruckLights.NitsPerEncodedUnit, 1000f, "rear fog lit");
                Assert.Less(c.g, c.r * 0.1f, "rear fog is red");
                Assert.AreEqual(0f, lights.StateTexture.GetPixel(FogFront, 0).r, 1e-6f, "front fog group untouched");
            }
            finally
            {
                Object.DestroyImmediate(go);
                Shader.SetGlobalTexture("_TruckLightState", oldTex);
                Shader.SetGlobalFloat("_TruckLightNitsScale", oldScale);
            }
        }
    }
}
