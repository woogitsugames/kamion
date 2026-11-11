using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Editor.VisualQA
{
    /// <summary>Opt-in editor-only evidence for asphalt ablations; no player/runtime behaviour.</summary>
    [InitializeOnLoad]
    public static class AsphaltQaStateProbe
    {
        static readonly HashSet<string> seen = new HashSet<string>();
        [Serializable] sealed class Snapshot
        {
            public string camera, maskFormat;
            public int width, height;
            public float fov, aspect;
            public Vector3 position;
            public float[] view, projection;
            public Vector4 roadWear, paintWear, freshPaintWear;
            public bool detailGlobal, paintUnderlay;
        }
        static AsphaltQaStateProbe()
        {
            if (Environment.GetEnvironmentVariable("KAMION_ASPHALT_QA_STATE") == "1")
                RenderPipelineManager.beginCameraRendering += Log;
        }

        static void Log(ScriptableRenderContext context, Camera camera)
        {
            if (camera.targetTexture == null || camera.targetTexture.width < 1000
                || !camera.name.StartsWith("QA_", StringComparison.Ordinal) || camera.name == "QA_UICamera"
                || !seen.Add(camera.name)) return;
            var material = AssetDatabase.LoadAssetAtPath<Material>(
                "Assets/_Generated/World/bialystok-industrial-c/Materials/M_road_asphalt.mat");
            if (material != null)
                Debug.Log($"[ASPHALT_STATE] camera={camera.name} frame={Time.frameCount} " +
                    $"detailGlobal={Shader.IsKeywordEnabled("_KAMION_WORLD_DETAIL")} " +
                    $"detailMaterial={material.IsKeywordEnabled("_KAMION_WORLD_DETAIL")} " +
                    $"wear={material.GetVector("_AsphaltWear").ToString("R")} shader={material.shader.name} " +
                    $"keywords={string.Join(",", material.shaderKeywords)}");
            string directory = Environment.GetEnvironmentVariable("KAMION_ASPHALT_QA_DIRECTORY");
            if (material == null || string.IsNullOrEmpty(directory)) return;
            var paint = AssetDatabase.LoadAssetAtPath<Material>(
                "Assets/_Generated/World/bialystok-industrial-c/Materials/M_marking_white.mat");
            var mask = material.GetTexture("_MaskMap") as Texture2D;
            var state = new Snapshot {
                camera = camera.name, width = camera.targetTexture.width, height = camera.targetTexture.height,
                fov = camera.fieldOfView, aspect = camera.aspect, position = camera.transform.position,
                view = RowMajor(camera.worldToCameraMatrix), projection = RowMajor(camera.projectionMatrix),
                roadWear = material.GetVector("_AsphaltWear"), detailGlobal = Shader.IsKeywordEnabled("_KAMION_WORLD_DETAIL"),
                paintWear = paint != null ? paint.GetVector("_PaintWear") : Vector4.zero,
                freshPaintWear = paint != null ? paint.GetVector("_PaintFreshWear") : Vector4.one,
                paintUnderlay = paint != null && paint.IsKeywordEnabled("_ROADWEAR"),
                maskFormat = mask != null ? mask.format.ToString() : "none"
            };
            string output = Path.Combine(directory, "runtime-cameras");
            Directory.CreateDirectory(output);
            string name = System.Text.RegularExpressions.Regex.Replace(camera.name, "[^A-Za-z0-9._-]", "_");
            File.WriteAllText(Path.Combine(output, name + ".json"), JsonUtility.ToJson(state, true));
        }

        static float[] RowMajor(Matrix4x4 matrix)
        {
            var values = new float[16];
            for (int r = 0; r < 4; r++) for (int c = 0; c < 4; c++) values[r * 4 + c] = matrix[r, c];
            return values;
        }
    }
}
