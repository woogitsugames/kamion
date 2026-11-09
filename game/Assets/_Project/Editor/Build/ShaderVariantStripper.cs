using System.Collections.Generic;
using UnityEditor.Build;
using UnityEditor.Rendering;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Editor.Build
{
    /// <summary>
    /// Strips shader variants this project can never select (APK audit 2026-11-09): Forward renderer only, no terrain
    /// details, no lightmaps / shadowmask / debug views. Runs before <see cref="ShaderVariantCounter"/>.
    /// Anything the project starts using (baked lighting, deferred) must be removed from this list.
    /// </summary>
    class ShaderVariantStripper : IPreprocessShaders
    {
        /// <summary>Off with -noShaderStrip (before/after measurement).</summary>
        public static bool Enabled = true;
        public int callbackOrder => 90000;

        static readonly string[] kStripShaderPrefixes =
        {
            "Hidden/Internal-DeferredShading", "Hidden/Internal-DeferredReflections", "Hidden/TerrainEngine/",
            "Hidden/Universal Render Pipeline/StencilDeferred", "Hidden/Universal Render Pipeline/ClusterDeferred",
        };

        static readonly string[] kStripKeywords =
        {
            "LIGHTMAP_ON", "DYNAMICLIGHTMAP_ON", "DIRLIGHTMAP_COMBINED", "LIGHTMAP_SHADOW_MIXING", "SHADOWS_SHADOWMASK",
            "DEBUG_DISPLAY", "_GBUFFER_NORMALS_OCT",
        };

        public void OnProcessShader(Shader shader, ShaderSnippetData snippet, IList<ShaderCompilerData> data)
        {
            if (!Enabled) return;
            foreach (var p in kStripShaderPrefixes)
                if (shader.name.StartsWith(p, System.StringComparison.Ordinal)) { data.Clear(); return; }

            var kws = new List<ShaderKeyword>(kStripKeywords.Length);
            foreach (var k in kStripKeywords)
            {
                var kw = new ShaderKeyword(shader, k);
                if (kw.index >= 0 || kw.name == k) kws.Add(kw);
            }
            if (kws.Count == 0) return;
            for (int i = data.Count - 1; i >= 0; i--)
            {
                var set = data[i].shaderKeywordSet;
                foreach (var kw in kws)
                    if (set.IsEnabled(kw)) { data.RemoveAt(i); break; }
            }
        }
    }
}
