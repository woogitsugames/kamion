using System;
using System.IO;
using System.Reflection;
using System.Collections.Generic;
using Game.Gameplay.Furniture;
using Game.Vehicle.Runtime;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Tests
{
    /// <summary>Actual Forward GPU comparison with the installed URP Lit, not a duplicate CPU formula.</summary>
    public class FurnitureSignTests
    {
        const string Keyword = "_FURNITURE_RETRO";
        string m_Pipeline;
        int m_MaxLod;
        static Shader s_CoefficientProbe;

        static Shader CoefficientProbe()
        {
            if (s_CoefficientProbe != null) return s_CoefficientProbe;
            const string dir = "Assets/_Generated/FurnitureSignProbe";
            string root = Path.GetDirectoryName(Application.dataPath);
            Directory.CreateDirectory(Path.Combine(root, dir));
            string shader = File.ReadAllText(Path.Combine(Application.dataPath, "_Project/Rendering/Shaders/FurnitureSign.shader"));
            string fragment = File.ReadAllText(Path.Combine(Application.dataPath, "_Project/Rendering/Shaders/FurnitureSignForward.hlsl"));
            StringAssert.Contains("outColor = color;", fragment);
            fragment = fragment.Replace("outColor = color;", "outColor = half4(_EmissionColor.rgb, 1);");
            shader = shader.Replace("Shader \"Kamion/Furniture Sign\"", "Shader \"Hidden/Kamion/FurnitureSignCoefficient\"")
                .Replace("\"FurnitureSignForward.hlsl\"", "\"FurnitureCoefficientForward.hlsl\"");
            File.WriteAllText(Path.Combine(root, dir, "FurnitureCoefficientForward.hlsl"), fragment);
            File.WriteAllText(Path.Combine(root, dir, "FurnitureCoefficient.shader"), shader);
            AssetDatabase.ImportAsset(dir + "/FurnitureCoefficientForward.hlsl", ImportAssetOptions.ForceSynchronousImport);
            AssetDatabase.ImportAsset(dir + "/FurnitureCoefficient.shader", ImportAssetOptions.ForceSynchronousImport);
            s_CoefficientProbe = AssetDatabase.LoadAssetAtPath<Shader>(dir + "/FurnitureCoefficient.shader");
            return s_CoefficientProbe;
        }

        [OneTimeSetUp] public void SetUpPipelineTag()
        {
            m_Pipeline = Shader.globalRenderPipeline;
            m_MaxLod = Shader.globalMaximumLOD;
            Debug.Log($"[FurnitureSignProbe] previous pipeline='{m_Pipeline}', maximumLOD={m_MaxLod}");
            // These command-buffer tests do not run a camera loop that normally selects the pipeline tag.
            Shader.globalRenderPipeline = "UniversalPipeline";
            Shader.globalMaximumLOD = int.MaxValue;
        }
        [OneTimeTearDown] public void RestorePipelineTag()
        {
            Shader.globalRenderPipeline = m_Pipeline;
            Shader.globalMaximumLOD = m_MaxLod;
        }

        static Color Draw(bool candidate, bool keyword, bool sourceOn, float distance = 50,
            float eyeOffset = 0, bool back = false, bool transparent = false,
            float gain = 800, bool coefficientOnly = false, float lampHalfWidth = 1, float exposureScale = 1,
            float sourceX=0,float sourceY=0)
        {
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null) Assert.Ignore("GPU required");
            var shader = coefficientOnly ? CoefficientProbe() : Shader.Find(candidate ? "Kamion/Furniture Sign" : "Universal Render Pipeline/Lit");
            Assert.NotNull(shader);
            Assert.IsFalse(ShaderUtil.ShaderHasError(shader));
            var mat = new Material(shader);
            var tex = new Texture2D(1, 1, TextureFormat.RGBAFloat, false, true);
            var mesh = new Mesh();
            var cb = new CommandBuffer { name = "Furniture sign Forward readback" };
            var rt = RenderTexture.GetTemporary(16, 16, 24, RenderTextureFormat.ARGBFloat, RenderTextureReadWrite.Linear);
            var pixel = new Texture2D(1, 1, TextureFormat.RGBAFloat, false, true);
            var previous = RenderTexture.active;
            float savedExposure = Shader.GetGlobalFloat("_KamionExposure");
            var globals = new[] { "_WorldSpaceCameraPos", "_MainLightPosition", "_MainLightColor", "_FurnitureRetroHead0",
                "_FurnitureRetroHead1", "_FurnitureRetroHead2", "_FurnitureRetroHead3", "_FurnitureRetroForward", "_FurnitureRetroUp", "_FurnitureRetroState" };
            var savedGlobals = new Vector4[globals.Length];
            for (int k = 0; k < globals.Length; k++) savedGlobals[k] = Shader.GetGlobalVector(globals[k]);
            try
            {
                tex.SetPixel(0, 0, new Color(.6f, .2f, .1f, transparent ? 0 : 1)); tex.Apply();
                mat.SetTexture("_BaseMap", tex);
                mat.SetColor("_BaseColor", Color.white);
                mat.SetColor("_EmissionColor", new Color(gain, gain, gain, 1));
                mat.DisableKeyword("_EMISSION");
                mat.EnableKeyword("_ALPHATEST_ON"); mat.SetFloat("_AlphaClip", 1); mat.SetFloat("_Cutoff", .5f);
                mat.SetFloat("_Surface", 0); mat.SetFloat("_Smoothness", .55f); mat.SetFloat("_Metallic", 0);
                mat.SetFloat("_SrcBlend", 1); mat.SetFloat("_DstBlend", 0);
                mat.SetFloat("_SrcBlendAlpha", 1); mat.SetFloat("_DstBlendAlpha", 0);
                mat.SetFloat("_ZWrite", 1); mat.SetFloat("_Cull", 0); mat.SetFloat("_AlphaToMask", 0);
                if (keyword) mat.EnableKeyword(Keyword); else mat.DisableKeyword(Keyword);
                var normal = back ? Vector3.forward : Vector3.back;
                mesh.vertices = new[] { new Vector3(-1,-1,0), new Vector3(1,-1,0), new Vector3(1,1,0), new Vector3(-1,1,0) };
                mesh.normals = new[] { normal, normal, normal, normal };
                mesh.uv = new[] { Vector2.zero, Vector2.right, Vector2.one, Vector2.up };
                mesh.triangles = new[] { 0,1,2,0,2,3 };
                cb.SetRenderTarget(rt); cb.ClearRenderTarget(true, true, Color.magenta);
                cb.SetViewProjectionMatrices(Matrix4x4.identity, Matrix4x4.identity);
                cb.SetGlobalVector("_WorldSpaceCameraPos", new Vector4(eyeOffset, 0, -distance, 1));
                cb.SetGlobalVector("_MainLightPosition", new Vector4(0, 0, -1, 0));
                cb.SetGlobalVector("_MainLightColor", new Vector4(.25f, .25f, .25f, 1));
                cb.SetGlobalVector("_FurnitureRetroHead0", new Vector4(sourceX-lampHalfWidth, sourceY, -distance, 1));
                cb.SetGlobalVector("_FurnitureRetroHead1", new Vector4(sourceX+lampHalfWidth, sourceY, -distance, 1));
                cb.SetGlobalVector("_FurnitureRetroHead2", Vector4.zero);
                cb.SetGlobalVector("_FurnitureRetroHead3", Vector4.zero);
                cb.SetGlobalVector("_FurnitureRetroForward", new Vector4(0, 0, 1, 0));
                cb.SetGlobalVector("_FurnitureRetroUp", new Vector4(0, 1, 0, 0));
                cb.SetGlobalVector("_FurnitureRetroState", new Vector4(sourceOn ? 1 : 0, 0, 0, 0));
                cb.SetGlobalFloat("_KamionExposure", exposureScale);
                int pass = mat.FindPass("ForwardLit"); Assert.GreaterOrEqual(pass, 0, shader.name + " has no ForwardLit pass");
                cb.DrawMesh(mesh, Matrix4x4.identity, mat, 0, pass);
                Graphics.ExecuteCommandBuffer(cb);
                RenderTexture.active = rt; pixel.ReadPixels(new Rect(8,8,1,1), 0, 0); pixel.Apply();
                var c = pixel.GetPixel(0,0);
                Assert.IsFalse(float.IsNaN(c.r) || float.IsInfinity(c.r));
                if (!transparent && !coefficientOnly) Assert.Less(c.b, .9f, "Probe did not render");
                return c;
            }
            finally
            {
                for (int k = 0; k < globals.Length; k++) Shader.SetGlobalVector(globals[k], savedGlobals[k]);
                Shader.SetGlobalFloat("_KamionExposure",savedExposure);
                RenderTexture.active = previous; cb.Release(); RenderTexture.ReleaseTemporary(rt);
                UnityEngine.Object.DestroyImmediate(pixel); UnityEngine.Object.DestroyImmediate(mesh);
                UnityEngine.Object.DestroyImmediate(tex); UnityEngine.Object.DestroyImmediate(mat);
            }
        }

        static void Same(Color a, Color b)
        {
            Assert.That(a.r, Is.EqualTo(b.r).Within(.0002f));
            Assert.That(a.g, Is.EqualTo(b.g).Within(.0002f));
            Assert.That(a.b, Is.EqualTo(b.b).Within(.0002f));
        }

        [Test] public void KeywordOffMatchesInstalledUrpLitOnGpu() => Same(Draw(false,false,false), Draw(true,false,false));
        [Test] public void EnabledKeywordWithNoSourceMatchesInstalledUrpLit() => Same(Draw(false,false,false), Draw(true,true,false));
        [Test] public void AlphaCutoutRemainsEmptyWithHeadlights() => Same(Color.magenta, Draw(true,true,true,transparent:true));
        [TestCase(1f)] [TestCase(800f)] public void HdrReturnCoefficientReachesGpuWithoutGammaEncoding(float gain)
        {
            var c = Draw(true,true,false,gain:gain,coefficientOnly:true);
            Assert.That(c.r, Is.EqualTo(gain).Within(gain * .002f));
            Assert.That(c.g, Is.EqualTo(gain).Within(gain * .002f));
            Assert.That(c.b, Is.EqualTo(gain).Within(gain * .002f));
        }
        [Test] public void ReturnDoesNotCreateAdditionalPasses()
        {
            var a = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            var b = new Material(Shader.Find("Kamion/Furniture Sign"));
            try
            {
                Assert.GreaterOrEqual(a.FindPass("ForwardLit"), 0);
                Assert.GreaterOrEqual(b.FindPass("ForwardLit"), 0);
                Debug.Log($"[FurnitureSignProbe] actual passes URP={a.passCount}, furniture={b.passCount}");
                Assert.AreEqual(a.passCount, b.passCount);
            }
            finally { UnityEngine.Object.DestroyImmediate(a); UnityEngine.Object.DestroyImmediate(b); }
        }
        [Test] public void SourceBrightensFaceButNotItsBack()
        {
            Assert.Greater(Draw(true,true,true).r - Draw(true,true,false).r, .005f);
            Same(Draw(true,true,false,back:true), Draw(true,true,true,back:true));
        }
        [Test] public void ObservationAngleSuppressesReturn()
        {
            float aligned = Draw(true,true,true).r - Draw(true,true,false).r;
            float side = Draw(true,true,true,eyeOffset:40).r - Draw(true,true,false,eyeOffset:40).r;
            Assert.Greater(aligned, .005f); Assert.Less(side, aligned * .01f);
        }
        [Test] public void ReturnTracksTheScenesExposedLightUnits()
        {
            float full = Draw(true,true,true).r - Draw(true,true,false).r;
            float half = Draw(true,true,true,exposureScale:.5f).r - Draw(true,true,false,exposureScale:.5f).r;
            Assert.Greater(full,.005f);
            Assert.That(half,Is.EqualTo(full * .5f).Within(.0003f));
            Same(Draw(true,true,false,exposureScale:0),Draw(true,true,true,exposureScale:0));
        }
        [Test] public void LowBeamUpsweepIlluminatesTheRightShoulderRatherThanOncomingSide()
        {
            float right=Draw(true,true,true,distance:25,eyeOffset:-3.5f,sourceX:-3.5f,sourceY:-1).r
                       -Draw(true,true,false,distance:25,eyeOffset:-3.5f,sourceX:-3.5f,sourceY:-1).r;
            float left=Draw(true,true,true,distance:25,eyeOffset:3.5f,sourceX:3.5f,sourceY:-1).r
                      -Draw(true,true,false,distance:25,eyeOffset:3.5f,sourceX:3.5f,sourceY:-1).r;
            Assert.Greater(right,.005f);
            Assert.Less(left,right*.01f);
        }
        [Test] public void ReturnFallsWithDistanceAndEndsBeyondRange()
        {
            // Keep the observation angle constant while testing distance, rather than letting
            // the closer fixed-width headlamps widen the observation angle and suppress return.
            float near = Draw(true,true,true,distance:25,lampHalfWidth:.5f).r - Draw(true,true,false,distance:25,lampHalfWidth:.5f).r;
            float far = Draw(true,true,true,distance:50).r - Draw(true,true,false,distance:50).r;
            Assert.Greater(near, far * 2); Assert.Greater(far, .005f);
            Same(Draw(true,true,false,distance:160), Draw(true,true,true,distance:160));
        }
        [Test] public void PublisherClearsSourceWhenMissingOffOrDisabled()
        {
            var go = new GameObject("Furniture source test");
            var left = new GameObject("left"); var right = new GameObject("right");
            var sun = RenderSettings.sun;
            var lampTexture = Shader.GetGlobalTexture("_TruckLightState");
            var lampScale = Shader.GetGlobalFloat("_TruckLightNitsScale");
            try
            {
                RenderSettings.sun = null;
                var lamps = go.AddComponent<TruckLights>(); lamps.forceLowBeam = true;
                FurnitureRetroSource.Publish(lamps,left.transform,right.transform);
                Assert.AreEqual(1, Shader.GetGlobalVector("_FurnitureRetroState").x);
                FurnitureRetroSource.Publish(lamps,null,right.transform);
                Assert.AreEqual(0, Shader.GetGlobalVector("_FurnitureRetroState").x);
                lamps.forceLowBeam = false;
                FurnitureRetroSource.Publish(lamps,left.transform,right.transform);
                Assert.AreEqual(0, Shader.GetGlobalVector("_FurnitureRetroState").x);
                lamps.forceLowBeam = true; lamps.enabled = false;
                FurnitureRetroSource.Publish(lamps,left.transform,right.transform);
                Assert.AreEqual(0, Shader.GetGlobalVector("_FurnitureRetroState").x);
            }
            finally
            {
                RenderSettings.sun = sun;
                FurnitureRetroSource.Publish(null,null,null);
                UnityEngine.Object.DestroyImmediate(go); UnityEngine.Object.DestroyImmediate(left); UnityEngine.Object.DestroyImmediate(right);
                Shader.SetGlobalTexture("_TruckLightState", lampTexture);
                Shader.SetGlobalFloat("_TruckLightNitsScale", lampScale);
            }
        }

        [Test] public void FactoryKeepsFaceUvAndRestoresOrdinaryLitWhenRetroIsRemoved()
        {
            var importer = Type.GetType("Game.World.Import.WorldPbrMaterials, Game.World.Import.Editor", true);
            var resultType = importer.Assembly.GetType("Game.World.Import.RegionImporter+Result", true);
            const string dir = "Assets/_Generated/FurnitureSignFactoryTests";
            Directory.CreateDirectory(Path.Combine(Path.GetDirectoryName(Application.dataPath), dir, "Textures"));
            AssetDatabase.Refresh();
            var result = Activator.CreateInstance(resultType);
            resultType.GetField("Dir").SetValue(result, dir);
            var def = new Dictionary<string, object> {
                {"color", new List<object>{1.0,1.0,1.0}}, {"rough",.45}, {"furniture_sign_face","B-33_70"},
                {"furniture_sign_retro",new Dictionary<string,object>{{"gain",800.0}}} };
            var create = importer.GetMethod("Create", BindingFlags.Public | BindingFlags.Static);
            var channels = importer.GetMethod("Channels", BindingFlags.Public | BindingFlags.Static);
            var mat = (Material)create.Invoke(null, new[] {result,(object)"sign_B-33_70",def,dir+"/M_sign.mat"});
            Assert.AreEqual("Kamion/Furniture Sign",mat.shader.name);
            Assert.IsTrue(mat.IsKeywordEnabled(Keyword)); Assert.IsFalse(mat.IsKeywordEnabled("_EMISSION"));
            Assert.That(mat.GetColor("_EmissionColor").r, Is.EqualTo(800).Within(.001f));
            var texture = mat.GetTexture("_BaseMap"); Assert.NotNull(texture);
            string materialGuid = AssetDatabase.AssetPathToGUID(dir+"/M_sign.mat");
            string textureGuid = AssetDatabase.AssetPathToGUID(AssetDatabase.GetAssetPath(texture));
            AssetDatabase.SaveAssets();
            Assert.IsTrue(AssetDatabase.LoadAssetAtPath<Material>(dir+"/M_sign.mat").IsKeywordEnabled(Keyword));
            def.Remove("furniture_sign_retro");
            var restored = (Material)create.Invoke(null, new[] {result,(object)"sign_B-33_70",def,dir+"/M_sign.mat"});
            Assert.AreEqual(materialGuid,AssetDatabase.AssetPathToGUID(AssetDatabase.GetAssetPath(restored)));
            Assert.AreEqual("Universal Render Pipeline/Lit",restored.shader.name);
            Assert.IsFalse(restored.IsKeywordEnabled(Keyword)); Assert.IsFalse(restored.IsKeywordEnabled("_EMISSION"));
            Assert.AreEqual(textureGuid,AssetDatabase.AssetPathToGUID(AssetDatabase.GetAssetPath(restored.GetTexture("_BaseMap"))));
            Assert.AreEqual(Color.black,restored.GetColor("_EmissionColor"));
            var args = new object[] {def,"sign_B-33_70",false,false,false};
            channels.Invoke(null,args);
            Assert.IsTrue((bool)args[2]); Assert.IsFalse((bool)args[3]); Assert.IsFalse((bool)args[4]);
        }

        [Test] public void PublisherUsesHighBeamSocketsWhenLowBeamIsOff()
        {
            var go = new GameObject("Furniture high beam source");
            var left = new GameObject("high-left"); var right = new GameObject("high-right");
            var sun = RenderSettings.sun;
            var lampTexture = Shader.GetGlobalTexture("_TruckLightState");
            var lampScale = Shader.GetGlobalFloat("_TruckLightNitsScale");
            try
            {
                RenderSettings.sun = null;
                var lamps = go.AddComponent<TruckLights>(); lamps.highBeam = true;
                left.transform.position = new Vector3(-1,1.4f,5); right.transform.position = new Vector3(1,1.4f,5);
                FurnitureRetroSource.Publish(lamps,null,null,left.transform,right.transform);
                Assert.AreEqual(1,Shader.GetGlobalVector("_FurnitureRetroState").x);
                Assert.AreEqual(0,Shader.GetGlobalVector("_FurnitureRetroHead0").w);
                var actual = Shader.GetGlobalVector("_FurnitureRetroHead2");
                Assert.That(new Vector3(actual.x,actual.y,actual.z),Is.EqualTo(left.transform.position));
                Assert.Greater(actual.w,0);
                FurnitureRetroSource.Publish(lamps,null,null,null,right.transform);
                Assert.AreEqual(0,Shader.GetGlobalVector("_FurnitureRetroState").x);
            }
            finally
            {
                RenderSettings.sun = sun;
                FurnitureRetroSource.Publish(null,null,null);
                UnityEngine.Object.DestroyImmediate(go); UnityEngine.Object.DestroyImmediate(left); UnityEngine.Object.DestroyImmediate(right);
                Shader.SetGlobalTexture("_TruckLightState",lampTexture); Shader.SetGlobalFloat("_TruckLightNitsScale",lampScale);
            }
        }

        [Test] public void AssemblyFlagCoversCurrentRoadFrontsWithoutOverridingAuthoredMaterials()
        {
            var importer = Type.GetType("Game.World.Import.WorldPbrMaterials, Game.World.Import.Editor", true);
            var resultType = importer.Assembly.GetType("Game.World.Import.RegionImporter+Result", true);
            const string dir = "Assets/_Generated/FurnitureSignFamilyTests";
            string root = Path.GetDirectoryName(Application.dataPath);
            Directory.CreateDirectory(Path.Combine(root,dir,"Textures"));
            Directory.CreateDirectory(Path.Combine(root,dir,"Materials"));
            AssetDatabase.Refresh();
            var result = Activator.CreateInstance(resultType);
            resultType.GetField("Dir").SetValue(result,dir);
            var defs = (Dictionary<string,Dictionary<string,object>>)resultType.GetField("MaterialDefs").GetValue(result);
            var materials = (Dictionary<string,Material>)resultType.GetField("Materials").GetValue(result);
            var authored = new Dictionary<string,object>{{"test_owner","retained"}};
            defs["sign_B-33_70"] = authored;
            var def = new Dictionary<string,object> {
                {"color",new List<object>{1.0,1.0,1.0}}, {"rough",.5},
                {"furniture_sign_fronts",new Dictionary<string,object>{{"gain",800.0}}} };
            var create = importer.GetMethod("Create",BindingFlags.Public|BindingFlags.Static);
            Assert.IsNull(create.Invoke(null,new[]{result,(object)"plate_back",def,dir+"/M_back.mat"}));
            string meta = File.ReadAllText(Path.GetFullPath(Path.Combine(root,"../art-source/world/props/props_meta.json")));
            var expected = new HashSet<string>();
            var json = importer.Assembly.GetType("Game.World.Import.MiniJson",true);
            var parsed = (Dictionary<string,object>)json.GetMethod("Parse").Invoke(null,new object[]{meta});
            var prototypes = (Dictionary<string,object>)parsed["prototypes"];
            foreach (var proto in prototypes.Values)
                foreach (string name in (List<object>)((Dictionary<string,object>)proto)["materials"])
                    if (name.StartsWith("sign_",StringComparison.Ordinal) && !name.StartsWith("sign_facade_",StringComparison.Ordinal)) expected.Add(name);
            Assert.Greater(expected.Count,10,"Fixture must include direction boards, not just a single plate");
            Assert.AreEqual(expected.Count,defs.Count);
            Assert.AreSame(authored,defs["sign_B-33_70"]);
            Assert.IsFalse(materials.ContainsKey("sign_B-33_70"));
            bool directionBoard = false;
            foreach (string name in expected)
            {
                if (name=="sign_B-33_70") continue;
                Assert.AreEqual(name.Substring(5),defs[name]["furniture_sign_face"]);
                Assert.IsTrue(materials[name].IsKeywordEnabled(Keyword),name);
                Assert.NotNull(materials[name].GetTexture("_BaseMap"),name);
                directionBoard |= name.StartsWith("sign_E-",StringComparison.Ordinal);
            }
            Assert.IsTrue(directionBoard);
            var disabledResult = Activator.CreateInstance(resultType);
            resultType.GetField("Dir").SetValue(disabledResult,dir);
            def.Remove("furniture_sign_fronts");
            Assert.IsNull(create.Invoke(null,new[]{disabledResult,(object)"plate_back",def,dir+"/M_back.mat"}));
            Assert.AreEqual(0,((Dictionary<string,Material>)resultType.GetField("Materials").GetValue(disabledResult)).Count);
            Debug.Log($"[FurnitureSignProbe] current road fronts={expected.Count}; facade labels excluded; authored definition retained");
        }

        [Test] public void AutomaticBridgeResolvesSocketsAddedAfterItsFirstLookup()
        {
            var go=new GameObject("Late furniture rig");
            var sun=RenderSettings.sun;
            var texture=Shader.GetGlobalTexture("_TruckLightState");
            var scale=Shader.GetGlobalFloat("_TruckLightNitsScale");
            var type=typeof(FurnitureRetroSource);
            var initialize=type.GetMethod("Initialize",BindingFlags.NonPublic|BindingFlags.Static);
            var begin=type.GetMethod("BeginCamera",BindingFlags.NonPublic|BindingFlags.Static);
            try
            {
                RenderSettings.sun=null;
                var lamps=go.AddComponent<TruckLights>();lamps.forceLowBeam=true;
                initialize.Invoke(null,null);
                begin.Invoke(null,new object[]{default(ScriptableRenderContext),null});
                Assert.AreEqual(0,Shader.GetGlobalVector("_FurnitureRetroState").x);
                type.GetField("s_FastRetryUntil",BindingFlags.NonPublic|BindingFlags.Static).SetValue(null,0f);
                type.GetField("s_NextFind",BindingFlags.NonPublic|BindingFlags.Static).SetValue(null,Time.realtimeSinceStartup+1000);
                foreach(string name in new[]{"LIGHT_LowBeam_L","LIGHT_LowBeam_R","LIGHT_HighBeam_L","LIGHT_HighBeam_R"})
                    new GameObject(name).transform.SetParent(go.transform,false);
                begin.Invoke(null,new object[]{default(ScriptableRenderContext),null});
                Assert.AreEqual(1,Shader.GetGlobalVector("_FurnitureRetroState").x,"Hierarchy completion must bypass idle retry delay");
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(go); RenderSettings.sun=sun;initialize.Invoke(null,null);
                Shader.SetGlobalTexture("_TruckLightState",texture);Shader.SetGlobalFloat("_TruckLightNitsScale",scale);
            }
        }
    }
}

