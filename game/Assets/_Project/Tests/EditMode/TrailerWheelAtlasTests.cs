using System.Collections.Generic;
using System.IO;
using Game.Editor.Build;
using Game.Editor.Setup;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using Json = Game.Editor.Setup.TruckAssetBuilder.Json;

namespace Game.Tests
{
    /// <summary>
    /// Review s23 (trailer, P1 "red rims"): the steel wheels of the curtainsider sampled red paint and text of other islands
    /// of the Metal atlas (docs/06 §2) - the kept lathe UV of the rim was never packed and lay under chassis islands.
    /// Every Metal face of the six LOD0 wheels (exported FBX, art-source) must read no red texel (R - G > 0.2, docs/06 §5)
    /// in the Metal albedo of every tier (High / Medium / Low). Same rule as tools/blender/truck/trailer/check_export.py.
    /// </summary>
    public class TrailerWheelAtlasTests
    {
        const string Manifest = "art-source/truck/trailer/export/trailer_manifest.json";
        const string TmpDir = "Assets/_TestTmp_TrailerWheelAtlas";
        const float RedDelta = 0.2f;

        [OneTimeTearDown]
        public void Cleanup()
        {
            if (AssetDatabase.IsValidFolder(TmpDir)) AssetDatabase.DeleteAsset(TmpDir);
        }

        static Texture2D LoadPng(string repoPath)
        {
            string p = Path.Combine(EditorTools.RepoRoot, repoPath);
            Assert.That(File.Exists(p) && new FileInfo(p).Length > 1024, "missing texture (or LFS pointer): " + p);
            var t = new Texture2D(2, 2, TextureFormat.RGBA32, false, false);
            Assert.That(t.LoadImage(File.ReadAllBytes(p)), "PNG decode: " + p);
            return t;
        }

        [Test]
        public void Lod0Wheels_MetalAlbedo_NoRedTexels_AllTiers()
        {
            var man = Json.Obj(Json.Parse(File.ReadAllText(Path.Combine(EditorTools.RepoRoot, Manifest))));
            var lod0 = Json.Obj(Json.Obj(man["lods"])["LOD0"]);
            string src = Path.Combine(EditorTools.RepoRoot, Json.Str(lod0["file"]));
            Assert.That(File.Exists(src) && new FileInfo(src).Length > 1024, "missing FBX (or LFS pointer): " + src);
            Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, TmpDir));
            string dst = $"{TmpDir}/{Path.GetFileName(src)}";
            File.Copy(src, Path.Combine(EditorTools.ProjectRoot, dst), true);
            AssetDatabase.ImportAsset(dst, ImportAssetOptions.ForceSynchronousImport);
            var mi = (ModelImporter)AssetImporter.GetAtPath(dst);
            TruckAssetBuilder.ApplyModelSettings(mi);   // materials embedded (InPrefab): renderer slot names = Blender slots
            mi.SaveAndReimport();
            var root = AssetDatabase.LoadAssetAtPath<GameObject>(dst);
            Assert.That(root, Is.Not.Null, dst);

            // UV sample points of the Metal faces of the wheels: triangle centroids + points 1/4 of the way to each corner
            var uvs = new List<Vector2>();
            int wheels = 0;
            foreach (var r in root.GetComponentsInChildren<MeshRenderer>(true))
            {
                if (!r.name.StartsWith("WHEEL_") || !r.name.EndsWith("_LOD0")) continue;
                var mesh = r.GetComponent<MeshFilter>().sharedMesh;
                var mats = r.sharedMaterials;
                Assert.That(mesh.subMeshCount, Is.EqualTo(mats.Length), r.name + " submeshes vs materials");
                var uv = mesh.uv;
                bool metal = false;
                for (int s = 0; s < mats.Length; s++)
                {
                    if (mats[s] == null || !mats[s].name.StartsWith("MI_Trl_Metal")) continue;
                    metal = true;
                    var tri = mesh.GetTriangles(s);
                    for (int i = 0; i < tri.Length; i += 3)
                    {
                        Vector2 a = uv[tri[i]], b = uv[tri[i + 1]], c = uv[tri[i + 2]], m = (a + b + c) / 3f;
                        uvs.Add(m);
                        uvs.Add(Vector2.Lerp(m, a, 0.5f));
                        uvs.Add(Vector2.Lerp(m, b, 0.5f));
                        uvs.Add(Vector2.Lerp(m, c, 0.5f));
                    }
                }
                Assert.That(metal, r.name + ": no MI_Trl_Metal submesh");
                wheels++;
            }
            Assert.That(wheels, Is.EqualTo(6), "WHEEL_*_LOD0 renderers");

            var report = new List<string>();
            var tex = Json.Obj(Json.Obj(Json.Obj(man["textures"])["Metal"])["C"]);
            Assert.That(tex.Count, Is.EqualTo(3), "Metal C tiers");
            foreach (var tier in tex)
            {
                var t = LoadPng(Json.Str(Json.Obj(tier.Value)["path"]));
                int red = 0;
                var hit = new HashSet<int>();
                foreach (var p in uvs)
                {
                    int x = Mathf.Clamp(Mathf.FloorToInt(p.x * t.width), 0, t.width - 1);
                    int y = Mathf.Clamp(Mathf.FloorToInt(p.y * t.height), 0, t.height - 1);   // PNG row 0 = top, GetPixel y 0 = bottom = v 0
                    if (!hit.Add(y * t.width + x)) continue;
                    var c = t.GetPixel(x, y);
                    if (c.r - c.g > RedDelta) red++;
                }
                Object.DestroyImmediate(t);
                report.Add($"{tier.Key}: {red} red of {hit.Count} wheel texels");
                if (red > 0) Assert.Fail("Metal albedo red on the wheels (docs/06 §2): " + string.Join("; ", report));
            }
            TestContext.WriteLine(string.Join("; ", report));
        }
    }
}
