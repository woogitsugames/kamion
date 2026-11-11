using System;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Editor.VisualQA
{
    /// <summary>Opt-in editor-only evidence for asphalt ablations; no player/runtime behaviour.</summary>
    [InitializeOnLoad]
    public static class AsphaltQaStateProbe
    {
        static int frames;
        static AsphaltQaStateProbe()
        {
            if (Environment.GetEnvironmentVariable("KAMION_ASPHALT_QA_STATE") == "1")
                RenderPipelineManager.beginCameraRendering += Log;
        }

        static void Log(ScriptableRenderContext context, Camera camera)
        {
            if (camera.targetTexture == null || camera.targetTexture.width < 1000) return;
            var material = AssetDatabase.LoadAssetAtPath<Material>(
                "Assets/_Generated/World/bialystok-industrial-c/Materials/M_road_asphalt.mat");
            if (material != null)
                Debug.Log($"[ASPHALT_STATE] camera={camera.name} frame={Time.frameCount} " +
                    $"detailGlobal={Shader.IsKeywordEnabled("_KAMION_WORLD_DETAIL")} " +
                    $"detailMaterial={material.IsKeywordEnabled("_KAMION_WORLD_DETAIL")} " +
                    $"wear={material.GetVector("_AsphaltWear").ToString("R")} shader={material.shader.name} " +
                    $"keywords={string.Join(",", material.shaderKeywords)}");
            if (++frames >= 4) RenderPipelineManager.beginCameraRendering -= Log;
        }
    }
}
