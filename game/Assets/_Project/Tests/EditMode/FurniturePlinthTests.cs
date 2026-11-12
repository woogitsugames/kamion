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
    /// <summary>ADR0120: exercise the actual modifier on GPU and the importer's data-gated factory.</summary>
    public class FurniturePlinthTests
    {
        const string Keyword = "_FURNITURE_PLINTH";
        const string Dir = "Assets/_Generated/FurniturePlinthTests";
        static Shader s_Probe;
        static Type Importer => Type.GetType("Game.World.Import.WorldPbrMaterials, Game.World.Import.Editor", true);

        static Shader Probe()
        {
            if (s_Probe != null) return s_Probe;
            string text = File.ReadAllText(Path.Combine(Application.dataPath, "_Project/Rendering/Shaders/WorldSurface.shader"));
            StringAssert.Contains("return half4(color, 1.0);", text);
            text = text.Replace("Shader \"Kamion/World Surface\"", "Shader \"Hidden/Kamion/FurniturePlinthReadback\"")
                .Replace("\"KamionLampPools.hlsl\"", "\"Assets/_Project/Rendering/Shaders/KamionLampPools.hlsl\"")
                .Replace("\"VegetationGround.hlsl\"", "\"Assets/_Project/Rendering/Shaders/VegetationGround.hlsl\"")
                .Replace("return half4(color, 1.0);", "return half4(albedo, 1.0);");
            Directory.CreateDirectory(Path.Combine(Path.GetDirectoryName(Application.dataPath), Dir));
            string path = Dir + "/FurniturePlinthReadback.shader";
            File.WriteAllText(Path.Combine(Path.GetDirectoryName(Application.dataPath), path), text);
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);
            s_Probe = AssetDatabase.LoadAssetAtPath<Shader>(path);
            Assert.NotNull(s_Probe);
            Assert.IsFalse(ShaderUtil.ShaderHasError(s_Probe));
            return s_Probe;
        }

        static Color Read(bool enabled, Color32 marker, float grain, float dirt)
        {
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null) Assert.Ignore("GPU readback requires graphics");
            var mat = new Material(Probe());
            var baseMap = new Texture2D(1, 1, TextureFormat.RGBAFloat, false, true);
            var scan = new Texture2D(1, 1, TextureFormat.RGBAFloat, false, true);
            var mesh = new Mesh();
            var cb = new CommandBuffer { name = "Furniture plinth marker readback" };
            var rt = RenderTexture.GetTemporary(16, 16, 0, RenderTextureFormat.ARGBFloat, RenderTextureReadWrite.Linear);
            var pixels = new Texture2D(1, 1, TextureFormat.RGBAFloat, false, true);
            var previous = RenderTexture.active;
            try
            {
                baseMap.SetPixel(0, 0, new Color(.5f, .5f, .5f, 1)); baseMap.Apply();
                scan.SetPixel(0, 0, new Color(grain, grain, grain, 1)); scan.Apply();
                mat.SetTexture("_BaseMap", baseMap); mat.SetTexture("_MacroMap", baseMap);
                mat.SetTexture("_FurnitureMap", scan);
                mat.SetColor("_BaseColor", new Color(.3f, .3f, .28f, 1).gamma);
                mat.SetFloat("_MacroStrength", 0); mat.SetFloat("_GroundMasks", 0);
                mat.SetFloat("_Cull", (float)CullMode.Off);
                mat.SetVector("_FurnitureDetail", new Vector4(1, .25f, dirt, 0));
                if (enabled) mat.EnableKeyword(Keyword); else mat.DisableKeyword(Keyword);
                mesh.vertices = new[] { new Vector3(-1,-1,0), new Vector3(1,-1,0), new Vector3(1,1,0), new Vector3(-1,1,0) };
                mesh.normals = new[] { Vector3.back, Vector3.back, Vector3.back, Vector3.back };
                mesh.colors32 = new[] { marker, marker, marker, marker };
                mesh.triangles = new[] { 0, 1, 2, 0, 2, 3 };
                cb.SetRenderTarget(rt); cb.ClearRenderTarget(true, true, Color.magenta);
                cb.SetViewProjectionMatrices(Matrix4x4.identity, Matrix4x4.identity);
                cb.DrawMesh(mesh, Matrix4x4.identity, mat, 0, 0);
                Graphics.ExecuteCommandBuffer(cb);
                RenderTexture.active = rt;
                pixels.ReadPixels(new Rect(8,8,1,1), 0, 0); pixels.Apply();
                var result = pixels.GetPixel(0,0);
                Assert.Less(result.b, .8f, "Unrendered/magenta probe");
                return result;
            }
            finally
            {
                RenderTexture.active = previous; cb.Release(); RenderTexture.ReleaseTemporary(rt);
                UnityEngine.Object.DestroyImmediate(pixels); UnityEngine.Object.DestroyImmediate(mesh);
                UnityEngine.Object.DestroyImmediate(scan); UnityEngine.Object.DestroyImmediate(baseMap);
                UnityEngine.Object.DestroyImmediate(mat);
            }
        }

        [TestCase(0, 0)] [TestCase(255, 255)] [TestCase(100, 128)]
        public void UnmarkedConcreteIsIdenticalWithKeywordOffAndOn(int blue, int alpha)
        {
            var marker = new Color32(51, 64, (byte)blue, (byte)alpha);
            var old = Read(false, marker, .1f, .9f);
            var current = Read(true, marker, .1f, .9f);
            Assert.That(current.r, Is.EqualTo(old.r).Within(1e-6f));
            Assert.That(current.g, Is.EqualTo(old.g).Within(1e-6f));
            Assert.That(current.b, Is.EqualTo(old.b).Within(1e-6f));
        }

        [Test]
        public void MarkedBoardUsesTheScanInLinearSpace()
        {
            var marker = new Color32(51, 192, 64, 128);
            var old = Read(false, marker, .25f, 0);
            var current = Read(true, marker, .25f, 0);
            Assert.That(current.r / old.r, Is.EqualTo(.5f).Within(.003f));
        }

        [Test]
        public void MarkedBoardDirtFadesAboveTheGroundLine()
        {
            var foot = Read(true, new Color32(51,64,64,128), .5f, .55f);
            var top = Read(true, new Color32(51,192,64,128), .5f, .55f);
            Assert.Less(foot.r, top.r * .9f);
            Assert.Less(foot.g / foot.r, top.g / top.r);
        }

        static Dictionary<string, object> Definition() => new Dictionary<string, object>
        {
            ["color"] = new List<object> { .3d, .3d, .28d }, ["rough"] = .9d,
            ["furniture_plinth_detail"] = new Dictionary<string, object>
            { ["texture"] = "furniture_plinth", ["tile_m"] = 1d, ["dirt_h"] = .25d, ["dirt_strength"] = .55d }
        };

        [Test]
        public void ImportKeepsByteColorMarkersWithoutRequiringUvChannels()
        {
            var method = Importer.GetMethod("Channels", BindingFlags.Public | BindingFlags.Static);
            var def = Definition();
            object[] args = { def, "concrete_plinth", false, false, false };
            method.Invoke(null, args);
            Assert.IsFalse((bool)args[2]); Assert.IsFalse((bool)args[3]); Assert.IsTrue((bool)args[4]);
            def.Remove("furniture_plinth_detail");
            args = new object[] { def, "concrete_plinth", false, false, false };
            method.Invoke(null, args);
            Assert.IsFalse((bool)args[4]);
        }

        [Test]
        public void FactoryPersistsVariantAndClearsItWhenTheDataFlagIsRemoved()
        {
            Directory.CreateDirectory(Path.Combine(Path.GetDirectoryName(Application.dataPath), Dir + "/Textures"));
            AssetDatabase.Refresh();
            var resultType = Importer.Assembly.GetType("Game.World.Import.RegionImporter+Result", true);
            var result = Activator.CreateInstance(resultType);
            resultType.GetField("Dir").SetValue(result, Dir);
            var create = Importer.GetMethod("Create", BindingFlags.Public | BindingFlags.Static);
            var def = Definition();
            var mat = (Material)create.Invoke(null, new[] { result, (object)"concrete_plinth", def, Dir + "/M_plinth.mat" });
            Assert.AreEqual("Kamion/World Surface", mat.shader.name);
            Assert.IsTrue(mat.IsKeywordEnabled(Keyword)); Assert.AreEqual(0, mat.GetFloat("_GroundMasks"));
            Assert.That(mat.GetColor("_BaseColor").linear.r, Is.EqualTo(.3f).Within(1e-5f));
            AssetDatabase.SaveAssets();
            Assert.IsTrue(AssetDatabase.LoadAssetAtPath<Material>(Dir + "/M_plinth.mat").IsKeywordEnabled(Keyword));
            def.Remove("furniture_plinth_detail");
            Assert.IsNull(create.Invoke(null, new[] { result, (object)"concrete_plinth", def, Dir + "/M_plinth.mat" }));
            Assert.IsFalse(mat.IsKeywordEnabled(Keyword)); Assert.IsNull(mat.GetTexture("_FurnitureMap"));
        }
    }
}
