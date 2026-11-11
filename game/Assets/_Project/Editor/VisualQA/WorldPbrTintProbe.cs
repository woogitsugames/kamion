using System;
using System.Collections.Generic;
using System.IO;
using Game.Editor.Build;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Editor.VisualQA
{
    /// <summary>ADR0086 GPU readback of the actual World PBR Color-property upload contract.
    /// The ignored diagnostic shader is an exact source copy with only its fragment return replaced.
    /// No light, exposure, texture sampling or render-target sRGB conversion participates.</summary>
    public static class WorldPbrTintProbe
    {
        const string ProbeShader = "Assets/_Generated/TintGammaProbe/WorldPbrTintReadback.shader";
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
            public string originalTintPropertyType;
            public string originalShaderSha256;
            public Sample[] samples;
        }

        public static Shader BuildProbeShader()
        {
            string original = Path.Combine(Application.dataPath, "_Project/Environment/Shaders/WorldPBR.shader");
            string text = File.ReadAllText(original);
            text = text.Replace("Shader \"Kamion/World PBR\"", "Shader \"Hidden/Kamion/WorldPbrTintReadback\"")
                // every include relative to Environment/Shaders (KamionLampPools, VegetationGround, ...) must resolve from the probe's folder
                .Replace("\"../../Rendering/Shaders/", "\"Assets/_Project/Rendering/Shaders/");
            int declaration = text.IndexOf("half4 frag(", StringComparison.Ordinal);
            if (declaration < 0) throw new InvalidOperationException("World PBR fragment declaration changed");
            int body = text.IndexOf('{', declaration);
            int depth = 1, end = body + 1;
            for (; end < text.Length && depth > 0; end++)
            {
                if (text[end] == '{') depth++;
                else if (text[end] == '}') depth--;
            }
            if (depth != 0) throw new InvalidOperationException("World PBR fragment braces not balanced");
            text = text.Substring(0, body) + "{ return half4(_Tint.rgb, 1); }" + text.Substring(end);
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
            if (setColor) mat.SetColor("_Tint", color);
            else mat.SetVector("_Tint", new Vector4(color.r, color.g, color.b, 1));
            mat.SetFloat("_Cull", (float)CullMode.Off);
            stored = mat.GetVector("_Tint").x;
            var mesh = new Mesh();
            mesh.vertices = new[] { new Vector3(-1,-1,0), new Vector3(1,-1,0), new Vector3(1,1,0), new Vector3(-1,1,0) };
            mesh.normals = new[] { Vector3.back, Vector3.back, Vector3.back, Vector3.back };
            mesh.uv = new[] { Vector2.zero, Vector2.right, Vector2.one, Vector2.up };
            mesh.triangles = new[] { 0, 1, 2, 0, 2, 3 };
            var rt = RenderTexture.GetTemporary(16, 16, 0, RenderTextureFormat.ARGBFloat, RenderTextureReadWrite.Linear);
            var cb = new CommandBuffer { name = "World PBR tint numeric readback" };
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

        public static void RunBatch()
        {
            var shader = BuildProbeShader();
            var samples = new List<Sample>();
            foreach (bool setColor in new[] { false, true })
                foreach (bool gamma in new[] { false, true })
                    foreach (float value in new[] { 0.04f, 0.08f, 0.18f, 0.5f, 1f, 1.5f, 2.5f })
                    {
                        float gpu = Read(shader, value, gamma, setColor, out float stored);
                        samples.Add(new Sample { setter = setColor ? "SetColor" : "SetVector", encoding = gamma ? "linear.gamma" : "raw linear", input = value, stored = stored, gpu = gpu });
                    }
            var original = Shader.Find("Kamion/World PBR");
            string source = Path.Combine(Application.dataPath, "_Project/Environment/Shaders/WorldPBR.shader");
            string sha;
            using (var hash = System.Security.Cryptography.SHA256.Create()) sha = BitConverter.ToString(hash.ComputeHash(File.ReadAllBytes(source))).Replace("-", "").ToLowerInvariant();
            var evidence = new Evidence { unityVersion = Application.unityVersion, colorSpace = QualitySettings.activeColorSpace.ToString(), graphicsDevice = SystemInfo.graphicsDeviceType.ToString(),
                originalTintPropertyType = original.GetPropertyType(original.FindPropertyIndex("_Tint")).ToString(), originalShaderSha256 = sha, samples = samples.ToArray() };
            string output = EditorTools.Arg("-tintProbeOutput", Path.Combine(EditorTools.RepoRoot, "artifacts/tint-gamma-r1/tint-probe.json"));
            Directory.CreateDirectory(Path.GetDirectoryName(output));
            File.WriteAllText(output, JsonUtility.ToJson(evidence, true));
            Debug.Log("TINT_PROBE_RESULT: OK samples=" + samples.Count + " output=" + output);
        }
    }
}
