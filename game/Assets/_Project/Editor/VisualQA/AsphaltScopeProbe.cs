using System;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Editor.VisualQA
{
    /// <summary>Editor-only GPU check of the actual material-scope code, including object transforms.</summary>
    public static class AsphaltScopeProbe
    {
        public static Shader BuildShader()
        {
            string source = File.ReadAllText(Path.Combine(Application.dataPath, "_Project/Environment/Shaders/WorldPBR.shader"));
            int begin = source.IndexOf("// ADR0118: leave a separately owned site", StringComparison.Ordinal);
            int finish = source.IndexOf("// ---- ground grime", begin, StringComparison.Ordinal);
            if (begin < 0 || finish < 0) throw new InvalidOperationException("Ground scope block missing");
            string block = source.Substring(begin, finish - begin);
            int declaration = source.IndexOf("half4 frag(", StringComparison.Ordinal);
            int body = source.IndexOf('{', declaration);
            int depth = 1, end = body + 1;
            for (; end < source.Length && depth > 0; end++)
            {
                if (source[end] == '{') depth++;
                else if (source[end] == '}') depth--;
            }
            if (depth != 0) throw new InvalidOperationException("World fragment is not balanced");
            source = source.Substring(0, body) + "{ UNITY_SETUP_INSTANCE_ID(i); float3 pw = i.positionWS;\n" + block
                + "return half4(groundWear, groundWear, groundWear, 1); }" + source.Substring(end);
            source = source.Replace("Shader \"Kamion/World PBR\"", "Shader \"Hidden/Kamion/AsphaltScopeProbe\"")
                .Replace("\"../../Rendering/Shaders/", "\"Assets/_Project/Rendering/Shaders/");
            const string path = "Assets/_Generated/AsphaltScopeProbe/Scope.shader";
            string full = Path.Combine(Application.dataPath, "_Generated/AsphaltScopeProbe/Scope.shader");
            Directory.CreateDirectory(Path.GetDirectoryName(full));
            File.WriteAllText(full, source);
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);
            var shader = AssetDatabase.LoadAssetAtPath<Shader>(path);
            if (shader == null || ShaderUtil.ShaderHasError(shader)) throw new InvalidOperationException("Scope probe compilation failed");
            return shader;
        }

        public static float Read(Shader shader, Vector2 localEN, Vector3 objectShift, Vector4 bounds)
        {
            var material = new Material(shader);
            var mesh = new Mesh();
            var pixels = new Texture2D(1, 1, TextureFormat.RGBAFloat, false, true);
            var cb = new CommandBuffer { name = "Asphalt scope origin-shift check" };
            var rt = RenderTexture.GetTemporary(16, 16, 0, RenderTextureFormat.ARGBFloat, RenderTextureReadWrite.Linear);
            var previous = RenderTexture.active;
            try
            {
                material.SetVector("_GroundWearExclude", bounds);
                material.SetFloat("_Cull", (float)CullMode.Off);
                var centre = new Vector3(localEN.x, 0f, localEN.y);
                mesh.vertices = new[] { centre + new Vector3(-1,-1,0), centre + new Vector3(1,-1,0),
                    centre + new Vector3(1,1,0), centre + new Vector3(-1,1,0) };
                mesh.normals = new[] { Vector3.back, Vector3.back, Vector3.back, Vector3.back };
                mesh.uv = new[] { Vector2.zero, Vector2.right, Vector2.one, Vector2.up };
                mesh.triangles = new[] { 0, 1, 2, 0, 2, 3 };
                cb.SetRenderTarget(rt);
                cb.ClearRenderTarget(true, true, Color.magenta);
                cb.SetViewProjectionMatrices(Matrix4x4.Translate(-(centre + objectShift)), Matrix4x4.identity);
                cb.DrawMesh(mesh, Matrix4x4.Translate(objectShift), material, 0, 0);
                Graphics.ExecuteCommandBuffer(cb);
                RenderTexture.active = rt;
                pixels.ReadPixels(new Rect(8, 8, 1, 1), 0, 0);
                pixels.Apply();
                return pixels.GetPixel(0, 0).r;
            }
            finally
            {
                RenderTexture.active = previous;
                cb.Release();
                RenderTexture.ReleaseTemporary(rt);
                UnityEngine.Object.DestroyImmediate(pixels);
                UnityEngine.Object.DestroyImmediate(mesh);
                UnityEngine.Object.DestroyImmediate(material);
            }
        }
    }
}
