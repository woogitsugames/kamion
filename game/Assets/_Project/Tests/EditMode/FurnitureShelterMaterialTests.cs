using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Tests
{
    public sealed class FurnitureShelterMaterialTests
    {
        const string Keyword = "_FURNITURE_SHELTER_PALETTE";
        const string Dir = "Assets/_Generated/FurnitureShelterMaterialTests";
        static readonly Color[] Sources = {
            new Color(.12f,.13f,.13f,.5f), new Color(.15f,.16f,.16f,.5f),
            new Color(.18f,.11f,.06f,.2f), new Color(.22f,.022f,.016f,.5f)
        };
        static readonly string[] Names = {"steel_painted", "shelter_roof", "bench_wood", "shelter_red_frame_0120"};
        static Shader s_Probe;
        static Shader s_SkyProbe;
        static readonly Vector4 SkyDown = new Vector4(.5f, .5f, .5f, 0f);
        static Type Importer => Type.GetType("Game.World.Import.WorldPbrMaterials, Game.World.Import.Editor", true);

        static Shader Probe(bool sky = false)
        {
            if (sky && s_SkyProbe != null) return s_SkyProbe;
            if (!sky && s_Probe != null) return s_Probe;
            string text = File.ReadAllText(Path.Combine(Application.dataPath, "_Project/Rendering/Shaders/WorldSurface.shader"));
            StringAssert.Contains("return half4(color, 1.0);", text);
            string name = sky ? "FurnitureShelterSkyReadback" : "FurnitureShelterReadback";
            text = text.Replace("Shader \"Kamion/World Surface\"", "Shader \"Hidden/Kamion/" + name + "\"")
                .Replace("\"KamionLampPools.hlsl\"", "\"Assets/_Project/Rendering/Shaders/KamionLampPools.hlsl\"")
                .Replace("\"VegetationGround.hlsl\"", "\"Assets/_Project/Rendering/Shaders/VegetationGround.hlsl\"")
                .Replace("return half4(color, 1.0);", sky ? "return half4(skyDown, 0, 0, 1);" : "return half4(albedo, smooth);");
            Directory.CreateDirectory(Path.Combine(Path.GetDirectoryName(Application.dataPath), Dir));
            string path = Dir + "/" + name + ".shader";
            File.WriteAllText(Path.Combine(Path.GetDirectoryName(Application.dataPath), path), text);
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);
            var probe = AssetDatabase.LoadAssetAtPath<Shader>(path);
            Assert.NotNull(probe);
            Assert.IsFalse(ShaderUtil.ShaderHasError(probe));
            if (sky) s_SkyProbe = probe; else s_Probe = probe;
            return probe;
        }

        static Color Read(bool palette, int source, bool detail, int uvSlot = -1, bool sky = false)
        {
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null) Assert.Ignore("GPU readback requires graphics");
            var mat = new Material(Probe(sky));
            var tex = new Texture2D(1, 1, TextureFormat.RGBAFloat, false, true);
            var mesh = new Mesh();
            var cb = new CommandBuffer {name = "Shelter palette albedo/smoothness readback"};
            var rt = RenderTexture.GetTemporary(16, 16, 0, RenderTextureFormat.ARGBFloat, RenderTextureReadWrite.Linear);
            var pixels = new Texture2D(1, 1, TextureFormat.RGBAFloat, false, true);
            var previous = RenderTexture.active;
            try
            {
                tex.SetPixel(0, 0, new Color(.6f,.6f,.6f,1)); tex.Apply();
                mat.SetTexture("_BaseMap", tex); mat.SetTexture("_MacroMap", tex);
                mat.SetColor("_BaseColor", new Color(Sources[source].r, Sources[source].g, Sources[source].b, 1).gamma);
                mat.SetFloat("_Smoothness", Sources[source].a);
                mat.SetFloat("_SmoothnessVar", .17f); mat.SetFloat("_MacroStrength", .12f);
                mat.SetColor("_MacroTint", Color.white); mat.SetFloat("_GroundMasks", 0);
                mat.SetFloat("_Cull", (float)CullMode.Off);
                for (int i = 0; i < Sources.Length; i++) mat.SetColor("_FurnitureShelter" + i, Sources[i].gamma);
                mat.SetVector("_FurnitureShelterSkyDown", SkyDown);
                mat.SetVector("_SkyOcc", palette ? Vector4.zero : new Vector4(SkyDown[source],0,0,0));
                if (palette) mat.EnableKeyword(Keyword);
                if (detail) mat.EnableKeyword("_KAMION_WORLD_DETAIL");
                mesh.vertices = new[] {new Vector3(-1,-1,0), new Vector3(1,-1,0), new Vector3(1,1,0), new Vector3(-1,1,0)};
                mesh.normals = new[] {Vector3.back, Vector3.back, Vector3.back, Vector3.back};
                var uv = new Vector2(uvSlot < 0 ? source : uvSlot, .5f);
                mesh.uv = new[] {uv, uv, uv, uv};
                mesh.colors = new[] {Color.white, Color.white, Color.white, Color.white};
                mesh.triangles = new[] {0,1,2,0,2,3};
                cb.SetRenderTarget(rt); cb.ClearRenderTarget(true, true, Color.magenta);
                cb.SetViewProjectionMatrices(Matrix4x4.identity, Matrix4x4.identity);
                cb.DrawMesh(mesh, Matrix4x4.identity, mat, 0, 0);
                Graphics.ExecuteCommandBuffer(cb);
                RenderTexture.active = rt;
                pixels.ReadPixels(new Rect(8,8,1,1), 0, 0); pixels.Apply();
                var value = pixels.GetPixel(0, 0);
                Assert.Less(value.b, .8f, "Unrendered/magenta probe");
                return value;
            }
            finally
            {
                RenderTexture.active = previous; cb.Release(); RenderTexture.ReleaseTemporary(rt);
                UnityEngine.Object.DestroyImmediate(pixels); UnityEngine.Object.DestroyImmediate(mesh);
                UnityEngine.Object.DestroyImmediate(tex); UnityEngine.Object.DestroyImmediate(mat);
            }
        }

        [TestCase(0,false)] [TestCase(1,false)] [TestCase(2,false)] [TestCase(3,false)]
        [TestCase(0,true)] [TestCase(1,true)] [TestCase(2,true)] [TestCase(3,true)]
        public void PaletteMatchesOriginalSurfaceInputsOnActualGpu(int source, bool detail)
        {
            var original = Read(false, source, detail);
            var merged = Read(true, source, detail);
            for (int channel = 0; channel < 4; channel++)
                Assert.That(merged[channel], Is.EqualTo(original[channel]).Within(1e-5f), "RGB and smoothness must retain the source recipe");
        }

        [Test]
        public void DisabledKeywordIgnoresThePaletteUv()
        {
            var a = Read(false, 0, false, 0);
            var b = Read(false, 0, false, 3);
            for (int channel = 0; channel < 4; channel++) Assert.That(a[channel], Is.EqualTo(b[channel]).Within(1e-6f));
        }

        [TestCase(0)] [TestCase(1)] [TestCase(2)] [TestCase(3)]
        public void PaletteRetainsEachSourcesDownwardSkyOcclusionOnGpu(int source)
        {
            var original = Read(false, source, false, sky: true);
            var merged = Read(true, source, false, sky: true);
            Assert.That(original.r, Is.EqualTo(SkyDown[source]).Within(1e-6f));
            Assert.That(merged.r, Is.EqualTo(original.r).Within(1e-6f));
        }

        [Test]
        public void PaletteAddsNoShaderPass()
        {
            Assert.That(Shader.Find("Kamion/World Surface").passCount, Is.EqualTo(3));
            Assert.That(Probe().passCount, Is.EqualTo(3));
        }

        static Dictionary<string, object> Definition() => new Dictionary<string, object>
        {
            ["color"] = new List<object>{1d,1d,1d}, ["rough"] = .5d,
            ["furniture_shelter_palette"] = new List<object>{Names[0],Names[1],Names[2],Names[3]}
        };

        static object Result(out Dictionary<string, Dictionary<string, object>> definitions)
        {
            var type = Importer.Assembly.GetType("Game.World.Import.RegionImporter+Result", true);
            var result = Activator.CreateInstance(type);
            type.GetField("Dir").SetValue(result, Dir);
            definitions = (Dictionary<string, Dictionary<string, object>>)type.GetField("MaterialDefs").GetValue(result);
            for (int i = 0; i < Names.Length; i++) definitions[Names[i]] = new Dictionary<string, object>
            {
                ["color"] = new List<object>{(double)Sources[i].r,(double)Sources[i].g,(double)Sources[i].b},
                ["rough"] = (double)(1f - Sources[i].a), ["metal"] = i == 0 ? .5d : 0d
            };
            for (int i = 0; i < Names.Length; i++) if (i != 3)
                definitions[Names[i]]["sky_occ"] = new List<object>{.5d, 0d};
            return result;
        }

        [Test]
        public void FactoryKeepsUvAndLinearRecipesAndDisablesRemovedFlag()
        {
            Directory.CreateDirectory(Path.Combine(Path.GetDirectoryName(Application.dataPath), Dir)); AssetDatabase.Refresh();
            var result = Result(out _); var def = Definition();
            var create = Importer.GetMethod("Create", BindingFlags.Public | BindingFlags.Static);
            var mat = (Material)create.Invoke(null, new[] {result, (object)"shelter_opaque_0120", def, Dir + "/M_palette.mat"});
            Assert.That(mat.shader.name, Is.EqualTo("Kamion/World Surface"));
            Assert.IsTrue(mat.IsKeywordEnabled(Keyword)); Assert.IsTrue(mat.enableInstancing);
            Assert.That(mat.GetVector("_FurnitureShelterSkyDown"), Is.EqualTo(SkyDown));
            for (int i = 0; i < Sources.Length; i++)
            {
                var value = mat.GetColor("_FurnitureShelter" + i).linear;
                for (int c = 0; c < 4; c++) Assert.That(value[c], Is.EqualTo(Sources[i][c]).Within(1e-5f));
            }
            object[] channels = {def, "shelter_opaque_0120", false, false, false};
            Importer.GetMethod("Channels").Invoke(null, channels);
            Assert.IsTrue((bool)channels[2]); Assert.IsFalse((bool)channels[3]); Assert.IsFalse((bool)channels[4]);
            def.Remove("furniture_shelter_palette");
            Assert.IsNull(create.Invoke(null, new[] {result, (object)"shelter_opaque_0120", def, Dir + "/M_palette.mat"}));
            Assert.IsFalse(mat.IsKeywordEnabled(Keyword));
        }

        [TestCase("texture")] [TestCase("emissive")] [TestCase("metal")]
        public void FactoryRejectsRecipesWithDifferentRenderingContracts(string field)
        {
            var result = Result(out var definitions);
            definitions[Names[0]][field] = field == "metal" ? (object).8d : "unsupported";
            var error = Assert.Throws<TargetInvocationException>(() => Importer.GetMethod("Create").Invoke(null,
                new[] {result, (object)"shelter_opaque_0120", Definition(), Dir + "/M_rejected.mat"}));
            Assert.That(error.InnerException, Is.TypeOf<InvalidOperationException>());
        }
    }
}
