using System;
using System.Collections.Generic;
using System.IO;
using Game.Editor.Build;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Editor.VisualQA
{
    /// <summary>ADR0087 GPU readback of the actual Truck Exterior Color-property upload contract.
    /// The diagnostic retains source properties/CBUFFER, replaces the fragment return, uses CullOff for the numeric quad and rewrites local include paths.
    /// No light, exposure, texture sampling or render-target sRGB conversion participates.</summary>
    public static class TruckPaintProbe
    {
        const string ProbeShader = "Assets/_Generated/TruckPaintProbe/TruckPaintReadback.shader";
        [Serializable] public sealed class Sample
        {
            public string setter;
            public string encoding;
            public float input;
            public float stored;
            public float gpu;
        }
        [Serializable] sealed class Evidence
        {
            public string unityVersion;
            public string colorSpace;
            public string graphicsDevice;
            public string originalPaintPropertyType;
            public string originalShaderSha256;
            public Sample[] samples;
            public string lampTextureFormat, drlTextureR, highTextureR, drlGpuR, highGpuR, nightDrlGpuR, nightLowGpuR, highOffGpuR;
            public float nitsPerEncodedUnit, emissionProbeExposure;
            public string exposedDayDrl, exposedHigh, exposedNightLow, exposedNightDrl, exposedHighOff;
            public bool drlFinite, highFinite, daytimeLowBeamOff, automaticNightLowBeamOn;
        }

        public static Shader BuildProbeShader(string expression = "_PaintColor.rgb", string vertexOverride = null, bool lightLayers = false)
        {
            string original = Path.Combine(Application.dataPath, "_Project/Rendering/Shaders/TruckExterior.shader");
            string text = File.ReadAllText(original).Replace("Cull Back", "Cull Off");
            text = text.Replace("Shader \"Kamion/Truck Exterior\"", "Shader \"Hidden/Kamion/TruckPaintReadback\"")
                .Replace("../../Rendering/Shaders/KamionLampPools.hlsl", "Assets/_Project/Rendering/Shaders/KamionLampPools.hlsl");
            text = text.Replace("\"KamionVehicleEnv.hlsl\"", "\"Assets/_Project/Rendering/Shaders/KamionVehicleEnv.hlsl\"").Replace("\"KamionToeParity.hlsl\"", "\"Assets/_Project/Rendering/Shaders/KamionToeParity.hlsl\"");
            int declaration = text.IndexOf("half4 frag(", StringComparison.Ordinal);
            if (declaration < 0) throw new InvalidOperationException("Truck Exterior fragment declaration changed");
            int body = text.IndexOf('{', declaration);
            int depth = 1, end = body + 1;
            for (; end < text.Length && depth > 0; end++)
            {
                if (text[end] == '{') depth++;
                else if (text[end] == '}') depth--;
            }
            if (depth != 0) throw new InvalidOperationException("Truck Exterior fragment braces not balanced");
            text = text.Substring(0, body) + "{ return half4(" + expression + ", 1); }" + text.Substring(end);
            if(vertexOverride!=null) text=text.Replace("o.positionCS = pcs;","o.positionCS = "+vertexOverride+";");
            // Production has no LIGHT_LAYERS variant. This QA-only define verifies its unconditional per-draw accessor.
            if(lightLayers) text=text.Replace("#include \"Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl\"","#define _LIGHT_LAYERS 1\n#include \"Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl\"");
            string full = Path.Combine(EditorTools.ProjectRoot, ProbeShader);
            Directory.CreateDirectory(Path.GetDirectoryName(full));
            File.WriteAllText(full, text);
            AssetDatabase.ImportAsset(ProbeShader, ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);
            var shader = AssetDatabase.LoadAssetAtPath<Shader>(ProbeShader);
            if (shader == null || ShaderUtil.ShaderHasError(shader)) throw new InvalidOperationException("Tint readback shader failed to compile");
            return shader;
        }

        public static float Read(Shader shader, float value, bool gammaEncode, bool setColor, out float stored)
        {
            var mat = new Material(shader);
            var color = new Color(value, value, value, 1f);
            if (gammaEncode) color = color.gamma;
            if (setColor) mat.SetColor("_PaintColor", color);
            else mat.SetVector("_PaintColor", new Vector4(color.r, color.g, color.b, 1));
            stored = mat.GetVector("_PaintColor").x;
            var mesh = new Mesh();
            mesh.vertices = new[] { new Vector3(-1,-1,0), new Vector3(1,-1,0), new Vector3(1,1,0), new Vector3(-1,1,0) };
            mesh.normals = new[] { Vector3.back, Vector3.back, Vector3.back, Vector3.back };
            mesh.uv = new[] { Vector2.zero, Vector2.right, Vector2.one, Vector2.up };
            mesh.triangles = new[] { 0, 1, 2, 0, 2, 3 };
            var rt = RenderTexture.GetTemporary(16, 16, 0, RenderTextureFormat.ARGBFloat, RenderTextureReadWrite.Linear);
            var cb = new CommandBuffer { name = "Truck Exterior tint numeric readback" };
            cb.SetRenderTarget(rt);
            cb.ClearRenderTarget(true, true, Color.magenta);
            cb.SetViewProjectionMatrices(Matrix4x4.identity, Matrix4x4.identity);
            cb.DrawMesh(mesh, Matrix4x4.identity, mat, 0, 0);
            Graphics.ExecuteCommandBuffer(cb);
            var previous = RenderTexture.active;
            RenderTexture.active = rt;
            var pixels = new Texture2D(1, 1, TextureFormat.RGBAFloat, false, true);
            pixels.ReadPixels(new Rect(8, 8, 1, 1), 0, 0);
            pixels.Apply();
            float result = pixels.GetPixel(0, 0).r;
            RenderTexture.active = previous;
            cb.Release();
            RenderTexture.ReleaseTemporary(rt);
            UnityEngine.Object.DestroyImmediate(pixels);
            UnityEngine.Object.DestroyImmediate(mesh);
            UnityEngine.Object.DestroyImmediate(mat);
            return result;
        }

        [Serializable] sealed class DirectionSample { public string ray; public float gpuRed; }
        [Serializable] sealed class DirectionEvidence { public string graphicsDevice; public float captureActive; public DirectionSample[] samples; }
        public static void WriteEnvironmentDirections(string output)
        {
            var rows=new List<DirectionSample>();
            foreach(string ray in new[]{"0,1,0","0,-1,0","1,1,0","1,-1,0","0,1,1","0,-1,1","1,0.75,0","1,-0.75,0","-1,0.75,0","-1,-0.75,0","0,0.75,1","0,-0.75,1","0,0.75,-1","0,-0.75,-1"})
            {
                var shader=BuildProbeShader("SAMPLE_TEXTURECUBE_LOD(_KamionVehicleEnvCube, sampler_KamionVehicleEnvCube, normalize(float3("+ray+")),0).rgb");
                rows.Add(new DirectionSample{ray=ray,gpuRed=Read(shader,1f,false,true,out _)});
            }
            File.WriteAllText(output,JsonUtility.ToJson(new DirectionEvidence{graphicsDevice=SystemInfo.graphicsDeviceType.ToString(),captureActive=Shader.GetGlobalFloat("_KamionVehicleCapture"),samples=rows.ToArray()},true));
            Debug.Log("TRUCK_ENV_DIRECTION_PROBE: "+output);
        }

        public static void RunBatch()
        {
            var shader = BuildProbeShader();
            var samples = new List<Sample>();
            foreach (bool setColor in new[] { false, true })
                foreach (bool gamma in new[] { false, true })
                    foreach (float value in new[] { 0.04f, 0.08f, 0.15f, 0.18f, 0.5f, 0.78f, 0.785f, 1f, 1.5f, 2.5f })
                    {
                        float gpu = Read(shader, value, gamma, setColor, out float stored);
                        samples.Add(new Sample { setter = setColor ? "SetColor" : "SetVector", encoding = gamma ? "linear.gamma" : "raw linear", input = value, stored = stored, gpu = gpu });
                    }
            var original = Shader.Find("Kamion/Truck Exterior");
            string source = Path.Combine(Application.dataPath, "_Project/Rendering/Shaders/TruckExterior.shader");
            string sha;
            using (var hash = System.Security.Cryptography.SHA256.Create()) sha = BitConverter.ToString(hash.ComputeHash(File.ReadAllBytes(source))).Replace("-", "").ToLowerInvariant();
            var evidence = new Evidence { unityVersion = Application.unityVersion, colorSpace = QualitySettings.activeColorSpace.ToString(), graphicsDevice = SystemInfo.graphicsDeviceType.ToString(),
                originalPaintPropertyType = original.GetPropertyType(original.FindPropertyIndex("_PaintColor")).ToString(), originalShaderSha256 = sha, samples = samples.ToArray() };
            var previousSun=RenderSettings.sun;
            var previousState=Shader.GetGlobalTexture("_TruckLightState");
            float previousScale=Shader.GetGlobalFloat("_TruckLightNitsScale"), previousExposure=Shader.GetGlobalFloat("_KamionExposure");
            var sunGo=new GameObject("Truck lamp numeric probe sun");
            var lampGo=new GameObject("Truck lamp numeric probe state");
            try
            {
                var sun=sunGo.AddComponent<Light>(); sun.type=LightType.Directional;
                sun.transform.rotation=Quaternion.Euler(50f,0f,0f); RenderSettings.sun=sun;
                var lights=lampGo.AddComponent<TruckLights>(); lights.highBeam=true; lights.Refresh();
                float drl=lights.StateTexture.GetPixel(1,0).r, high=lights.StateTexture.GetPixel(3,0).r;
                evidence.lampTextureFormat=lights.StateTexture.format.ToString();
                evidence.drlTextureR=drl.ToString("R", System.Globalization.CultureInfo.InvariantCulture);
                evidence.highTextureR=high.ToString("R", System.Globalization.CultureInfo.InvariantCulture);
                evidence.drlFinite=!float.IsNaN(drl)&&!float.IsInfinity(drl);
                evidence.highFinite=!float.IsNaN(high)&&!float.IsInfinity(high);
                evidence.daytimeLowBeamOff=lights.StateTexture.GetPixel(2,0).r==0f;
                var lampShader=BuildProbeShader("SAMPLE_TEXTURE2D_LOD(_TruckLightState, sampler_point_clamp, float2((_PaintColor.r + 0.5)/16.0,0.5),0).rgb");
                float drlGpu=Read(lampShader,1f,true,true,out _), highGpu=Read(lampShader,3f,true,true,out _);
                evidence.drlGpuR=drlGpu.ToString("R",System.Globalization.CultureInfo.InvariantCulture);
                evidence.highGpuR=highGpu.ToString("R",System.Globalization.CultureInfo.InvariantCulture);
                sun.transform.rotation=Quaternion.Euler(-5f,0f,0f); lights.highBeam=false; lights.Refresh();
                evidence.automaticNightLowBeamOn=lights.LowBeamOn;
                evidence.nightDrlGpuR=Read(lampShader,1f,true,true,out _).ToString("R",System.Globalization.CultureInfo.InvariantCulture);
                evidence.nightLowGpuR=Read(lampShader,2f,true,true,out _).ToString("R",System.Globalization.CultureInfo.InvariantCulture);
                evidence.highOffGpuR=Read(lampShader,3f,true,true,out _).ToString("R",System.Globalization.CultureInfo.InvariantCulture);
                evidence.nitsPerEncodedUnit=TruckLights.NitsPerEncodedUnit;
                evidence.emissionProbeExposure=0.0001f; Shader.SetGlobalFloat("_KamionExposure",evidence.emissionProbeExposure);
                var decodeShader=BuildProbeShader("TruckLampRadiance(SAMPLE_TEXTURE2D_LOD(_TruckLightState, sampler_point_clamp, float2((_PaintColor.r + 0.5)/16.0,0.5),0).rgb)");
                sun.transform.rotation=Quaternion.Euler(40f,0f,0f); lights.highBeam=true; lights.Refresh();
                evidence.exposedDayDrl=Read(decodeShader,1f,true,true,out _).ToString("R",System.Globalization.CultureInfo.InvariantCulture);
                evidence.exposedHigh=Read(decodeShader,3f,true,true,out _).ToString("R",System.Globalization.CultureInfo.InvariantCulture);
                sun.transform.rotation=Quaternion.Euler(-5f,0f,0f); lights.highBeam=false; lights.Refresh();
                evidence.exposedNightLow=Read(decodeShader,2f,true,true,out _).ToString("R",System.Globalization.CultureInfo.InvariantCulture);
                evidence.exposedNightDrl=Read(decodeShader,1f,true,true,out _).ToString("R",System.Globalization.CultureInfo.InvariantCulture);
                evidence.exposedHighOff=Read(decodeShader,3f,true,true,out _).ToString("R",System.Globalization.CultureInfo.InvariantCulture);
            }
            finally
            {
                RenderSettings.sun=previousSun;
                UnityEngine.Object.DestroyImmediate(lampGo); UnityEngine.Object.DestroyImmediate(sunGo);
                Shader.SetGlobalTexture("_TruckLightState",previousState); Shader.SetGlobalFloat("_TruckLightNitsScale",previousScale);
                Shader.SetGlobalFloat("_KamionExposure",previousExposure);
            }
            string output = EditorTools.Arg("-tintProbeOutput", Path.Combine(EditorTools.RepoRoot, "artifacts/truck-paint-r1/paint-color-probe.json"));
            Directory.CreateDirectory(Path.GetDirectoryName(output));
            File.WriteAllText(output, JsonUtility.ToJson(evidence, true));
            Debug.Log("TINT_PROBE_RESULT: OK samples=" + samples.Count + " output=" + output);
        }
    }
}
