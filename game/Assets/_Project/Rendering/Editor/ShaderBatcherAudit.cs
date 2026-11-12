using System;
using System.IO;
using System.Reflection;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace Game.Rendering.Editor
{
    /// <summary>ADR 0131: SRP Batcher compatibility and editor variant totals of chosen shaders, read through the
    /// internal ShaderUtil API the Shader inspector uses (reflection; reports "n/a" if an API is missing).
    /// Batch: -executeMethod Game.Rendering.Editor.ShaderBatcherAudit.RunBatch -auditShaders "Kamion/Furniture Sign;Kamion/World PBR" -auditOut path.txt</summary>
    public static class ShaderBatcherAudit
    {
        static string Arg(string name, string fallback)
        {
            var a = Environment.GetCommandLineArgs();
            for (int i = 0; i < a.Length - 1; i++) if (a[i] == name) return a[i + 1];
            return fallback;
        }

        public static void RunBatch()
        {
            string list = Arg("-auditShaders", "Kamion/Furniture Sign;Kamion/World PBR;Universal Render Pipeline/Lit");
            string output = Arg("-auditOut", null);
            var sb = new StringBuilder();
            // The compatibility code reads "Not initialized" until the SRP has rendered once in this process.
            var go = new GameObject("audit cam") { hideFlags = HideFlags.HideAndDontSave };
            var cam = go.AddComponent<Camera>();
            var rt = new RenderTexture(64, 64, 24);
            cam.targetTexture = rt;
            foreach (var n in list.Split(';'))
            {
                var sh = Shader.Find(n.Trim());
                if (sh == null) continue;
                var q = GameObject.CreatePrimitive(PrimitiveType.Quad);
                q.hideFlags = HideFlags.HideAndDontSave;
                q.transform.position = go.transform.forward * 2f;
                q.GetComponent<Renderer>().sharedMaterial = new Material(sh);
            }
            cam.Render();
            cam.targetTexture = null; rt.Release();
            const BindingFlags F = BindingFlags.NonPublic | BindingFlags.Public | BindingFlags.Static;
            var compat = typeof(ShaderUtil).GetMethod("GetSRPBatcherCompatibilityCode", F);
            var reason = typeof(ShaderUtil).GetMethod("GetSRPBatcherCompatibilityIssueReason", F);
            var variants = typeof(ShaderUtil).GetMethod("GetVariantCount", F, null, new[] { typeof(Shader), typeof(bool) }, null);
            foreach (var name in list.Split(';'))
            {
                var shader = Shader.Find(name.Trim());
                if (shader == null) { sb.AppendLine($"{name}: NOT FOUND"); continue; }
                string c = "n/a", r = "";
                if (compat != null)
                {
                    int code = Convert.ToInt32(compat.Invoke(null, new object[] { shader, 0 }));
                    c = code == 0 ? "compatible" : "NOT compatible (code " + code + ")";
                    if (code != 0 && reason != null) r = " reason=" + reason.Invoke(null, new object[] { shader, 0, code });
                }
                string v = variants != null ? Convert.ToString(variants.Invoke(null, new object[] { shader, false })) : "n/a";
                sb.AppendLine($"{name}: srpBatcher={c}{r} editorVariantTotal={v} passes={shader.passCount}");
            }
            Debug.Log("SHADER_BATCHER_AUDIT\n" + sb);
            if (!string.IsNullOrEmpty(output)) File.WriteAllText(output, sb.ToString());
            EditorApplication.Exit(0);
        }
    }
}
