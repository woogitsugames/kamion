using System.Collections.Generic;
using System.Linq;
using UnityEditor.Build;
using UnityEditor.Rendering;
using UnityEngine;

namespace Game.Editor.Build
{
    /// <summary>
    /// Counts shader variants handed to the build (callbackOrder 100000 = after URP's own stripping) so the APK audit
    /// can report variant totals per shader. Read-only: it never strips anything.
    /// </summary>
    class ShaderVariantCounter : IPreprocessShaders
    {
        static readonly Dictionary<string, int> Counts = new Dictionary<string, int>();
        public int callbackOrder => 100000;

        public void OnProcessShader(Shader shader, ShaderSnippetData snippet, IList<ShaderCompilerData> data)
        {
            Counts.TryGetValue(shader.name, out int n);
            Counts[shader.name] = n + data.Count;
        }

        public static string Summary()
        {
            int total = Counts.Values.Sum();
            var top = Counts.OrderByDescending(k => k.Value).Take(12).Select(k => $"{k.Key}={k.Value}");
            return $"total={total} shaders={Counts.Count} top: {string.Join(", ", top)}";
        }
    }
}
