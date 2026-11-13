using System.Collections.Generic;
using System.Globalization;
using System.IO;
using Game.Editor.Build;
using Game.Editor.Setup;
using Game.Editor.VisualQA;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using Json = Game.Editor.Setup.TruckAssetBuilder.Json;

namespace Game.Tests
{
    /// <summary>
    /// ADR 0181: lamp lenses carry a lens-local frame in uv1 (x = W_mm + u', y = style * 256 + H_mm + v') on every LOD of
    /// the tractor and the trailer, the number plates are PLATE (13) emitters with lens style PLATE, and the shader
    /// function that turns the frame into optics stays bounded (no lamp brighter than the ADR 0178 limit allows).
    /// </summary>
    public class TruckLampLensTests
    {
        const string ExtManifest = "art-source/truck/exterior/export/truck_exterior_manifest.json";
        const string TrlManifest = "art-source/truck/trailer/export/trailer_manifest.json";
        const string TmpDir = "Assets/_TestTmp_LampLens";
        const int IndL = 4, TailBrake = 6, Reverse = 7, Plate = 13, Reflex = 15;
        const int Pillow = 1, Fresnel = 3, ReflexStyle = 4, PlateStyle = 5;

        struct LensVert { public Vector3 p; public int group, style, w, h; public float emit, u, v; }

        static Dictionary<string, object> Load(string rel) =>
            Json.Obj(Json.Parse(File.ReadAllText(Path.Combine(EditorTools.RepoRoot, rel))));

        [OneTimeTearDown]
        public void Cleanup()
        {
            if (AssetDatabase.IsValidFolder(TmpDir)) AssetDatabase.DeleteAsset(TmpDir);
        }

        static List<LensVert> Verts(string manifest, string lod)
        {
            string src = Path.Combine(EditorTools.RepoRoot, Json.Str(Json.Obj(Json.Obj(Load(manifest)["lods"])[lod])["file"]));
            Assert.That(File.Exists(src) && new FileInfo(src).Length > 1024, "missing FBX (or LFS pointer): " + src);
            Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, TmpDir));
            string dst = $"{TmpDir}/{Path.GetFileName(src)}";
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
            var outv = new List<LensVert>();
            var data = new List<Vector2>();
            var lens = new List<Vector2>();
            foreach (var mf in root.GetComponentsInChildren<MeshFilter>(true))
            {
                var mesh = mf.sharedMesh;
                if (mesh == null || mf.name.StartsWith("COL_")) continue;
                mesh.GetUVs(2, data);
                mesh.GetUVs(1, lens);
                if (data.Count == 0 || lens.Count != data.Count) continue;
                var v = mesh.vertices;
                var toRoot = root.transform.worldToLocalMatrix * mf.transform.localToWorldMatrix;
                for (int i = 0; i < v.Length; i++)
                {
                    int w = Mathf.FloorToInt(lens[i].x);
                    if (w < 1) continue;
                    int yi = Mathf.FloorToInt(lens[i].y);
                    outv.Add(new LensVert
                    {
                        p = toRoot.MultiplyPoint3x4(v[i]), group = Mathf.RoundToInt(data[i].x), emit = data[i].y, w = w, style = yi / 256, h = yi % 256,
                        u = lens[i].x - w, v = lens[i].y - yi,
                    });
                }
            }
            return outv;
        }

        [TestCase(ExtManifest), TestCase(TrlManifest)]
        public void Manifest_DeclaresLensStyles(string manifest)
        {
            var styles = Json.Obj(Json.Obj(Load(manifest)["shader_contract"])["lens_styles"]);
            Assert.AreEqual("PILLOW", Json.Str(styles["1"]));
            Assert.AreEqual("FLUTE", Json.Str(styles["2"]));
            Assert.AreEqual("FRESNEL", Json.Str(styles["3"]));
            Assert.AreEqual("REFLEX", Json.Str(styles["4"]));
            Assert.AreEqual("PLATE", Json.Str(styles["5"]));
        }

        [TestCase(ExtManifest, "LOD0"), TestCase(ExtManifest, "LOD1"), TestCase(ExtManifest, "LOD2")]
        [TestCase(TrlManifest, "LOD0"), TestCase(TrlManifest, "LOD1"), TestCase(TrlManifest, "LOD2")]
        public void LensFrame_IsWellFormed_OnEveryLod(string manifest, string lod)
        {
            var verts = Verts(manifest, lod);
            Assert.That(verts.Count, Is.GreaterThan(40), "no lens frames in " + lod);
            foreach (var x in verts)
            {
                Assert.That(x.style, Is.InRange(1, 5), "lens style");
                Assert.That(x.w, Is.InRange(1, 1023));
                Assert.That(x.h, Is.InRange(1, 255));
                // u', v' = 0.02 + 0.96 * (0..1): the integer part must never be reached by interpolation or decimation.
                Assert.That(x.u, Is.InRange(0.015f, 0.985f), "u' out of the packed range");
                Assert.That(x.v, Is.InRange(0.015f, 0.985f), "v' out of the packed range");
                if (x.style == ReflexStyle) Assert.That(x.group == Reflex && x.emit < 0.01f, "REFLEX style only on non-emissive reflectors");
                else Assert.That(x.group != Reflex && x.emit > 0.01f, "lamp lens styles only on emitters");
            }
            // Stop / tail and indicator chambers on both sides are pillow lenses, reversing lamps Fresnel.
            Assert.That(verts.Exists(x => x.group == TailBrake && x.style == Pillow && x.p.x < -0.5f) &&
                        verts.Exists(x => x.group == TailBrake && x.style == Pillow && x.p.x > 0.5f), "tail / stop lens frame, both sides");
            Assert.That(verts.Exists(x => x.group == IndL && x.style == Pillow), "rear indicator lens frame");
            Assert.That(verts.Exists(x => x.group == Reverse && x.style == Fresnel), "reversing lamp lens frame");
        }

        [TestCase(ExtManifest, "LOD0"), TestCase(ExtManifest, "LOD2"), TestCase(TrlManifest, "LOD0"), TestCase(TrlManifest, "LOD2")]
        public void RearNumberPlate_IsLitByThePlateLamp(string manifest, string lod)
        {
            var verts = Verts(manifest, lod);
            var plate = verts.FindAll(x => x.style == PlateStyle);
            Assert.That(plate.Count, Is.GreaterThanOrEqualTo(4), "rear plate without the PLATE lens frame");
            foreach (var x in plate)
            {
                Assert.AreEqual(Plate, x.group, "plate face must be in light group PLATE (13)");
                Assert.That(x.emit, Is.GreaterThan(0.5f));
                Assert.That(x.w, Is.InRange(515, 525), "PL / EU plate width 520 mm");
                Assert.That(x.h, Is.InRange(110, 118), "PL / EU plate height 114 mm");
            }
            // The plate lamp itself: a PLATE emitter that is not the plate face, above the plate's lower edge.
            float yMin = float.MaxValue, yMax = float.MinValue;
            foreach (var x in plate) { yMin = Mathf.Min(yMin, x.p.y); yMax = Mathf.Max(yMax, x.p.y); }
            Assert.That(verts.Exists(x => x.group == Plate && x.style != PlateStyle && x.p.y > yMax - 0.005f && x.p.y < yMax + 0.08f),
                "no plate lamp lens just above the plate (UN R48 6.8)");
        }

        static string F(float v) => v.ToString("R", CultureInfo.InvariantCulture);
        static string Lens(float w, float h, int style, float u, float v) =>
            $"KamionLensEval(float2({F(w + 0.02f + 0.96f * u)}, {F(style * 256 + h + 0.02f + 0.96f * v)}))";
        static float Probe(string expr) => TruckPaintProbe.Read(TruckPaintProbe.BuildProbeShader("(" + expr + ").xxx"), 1f, false, true, out _);

        [Test]
        public void Shader_LensFade_IsZeroAtNyquist_AndFullFromFourPixelsPerPeriod()
        {
            // Review s20 P1-1: pattern contrast vs pixels per period (pitch / footprint).
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null) Assert.Ignore("GPU readback requires a graphics device");
            Assert.That(Probe("KamionLensFade(1.0, 2.0)"), Is.EqualTo(0f).Within(1e-3f), "2 px / period");
            Assert.That(Probe("KamionLensFade(1.0, 1.5)"), Is.EqualTo(0f).Within(1e-3f), "1.5 px / period");
            Assert.That(Probe("KamionLensFade(1.0, 3.0)"), Is.EqualTo(0.5f).Within(1e-2f), "3 px / period");
            Assert.That(Probe("KamionLensFade(1.0, 4.0)"), Is.EqualTo(1f).Within(1e-3f), "4 px / period");
        }

        [Test]
        public void Shader_NoLensFrame_LeavesTheLampUntouched()
        {
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null) Assert.Ignore("GPU readback requires a graphics device");
            const string none = "KamionLensEval(float2(0.002, 0.002))";
            Assert.That(Probe(none + ".hdr"), Is.EqualTo(1f).Within(1e-4f));
            Assert.That(Probe(none + ".disp"), Is.EqualTo(1f).Within(1e-4f));
            Assert.That(Probe(none + ".shade"), Is.EqualTo(1f).Within(1e-4f));
            Assert.That(Probe(none + ".style"), Is.EqualTo(0f).Within(1e-4f));
        }

        [TestCase(1, 120f, 126f), TestCase(2, 90f, 31f), TestCase(3, 110f, 90f)]
        public void Shader_LampLens_NeverAmplifies_AndGasketIsDarkerThanTheEmitter(int style, float w, float h)
        {
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null) Assert.Ignore("GPU readback requires a graphics device");
            float hdrMax = 0f, dispMax = 0f;
            foreach (float u in new[] { 0.004f, 0.1f, 0.31f, 0.5f, 0.77f, 0.996f })
                foreach (float v in new[] { 0.004f, 0.23f, 0.5f, 0.9f })
                {
                    float hdr = Probe(Lens(w, h, style, u, v) + ".hdr"), disp = Probe(Lens(w, h, style, u, v) + ".disp");
                    Assert.That(hdr, Is.InRange(0f, 1.0001f), "pre-limit scale must not amplify the lamp");
                    Assert.That(disp, Is.InRange(0f, 1.0001f), "post-limit scale must stay under the ADR 0178 ceiling");
                    hdrMax = Mathf.Max(hdrMax, hdr); dispMax = Mathf.Max(dispMax, disp);
                }
            Assert.That(dispMax, Is.GreaterThan(0.75f), "an emitter must reach (nearly) the full limited level");
            float edge = Probe(Lens(w, h, style, 0.002f, 0.5f) + ".disp");
            Assert.That(edge, Is.LessThan(0.6f * dispMax), "gasket at the lens edge");
        }

        [Test]
        public void Shader_Reflex_NeverEmits_AndPlateFallsOffFromTheLamp()
        {
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null) Assert.Ignore("GPU readback requires a graphics device");
            Assert.That(Probe(Lens(47f, 126f, ReflexStyle, 0.4f, 0.6f) + ".hdr"), Is.EqualTo(0f).Within(1e-5f));
            Assert.That(Probe(Lens(47f, 126f, ReflexStyle, 0.4f, 0.6f) + ".disp"), Is.EqualTo(0f).Within(1e-5f));
            float top = Probe(Lens(520f, 114f, PlateStyle, 0.5f, 1f) + ".plate");
            float bottom = Probe(Lens(520f, 114f, PlateStyle, 0.5f, 0f) + ".plate");
            float corner = Probe(Lens(520f, 114f, PlateStyle, 0f, 0f) + ".plate");
            Assert.That(top, Is.InRange(0.9f, 1f));
            Assert.That(bottom, Is.LessThan(top).And.GreaterThan(0.25f * top), "plate bottom is dimmer but lit");
            Assert.That(corner, Is.LessThan(bottom).And.GreaterThan(0.1f * top), "no black plate corner (UN R4 asks for a bounded gradient)");
        }
    }
}
