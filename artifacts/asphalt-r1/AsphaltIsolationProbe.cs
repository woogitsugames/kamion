// Temporary editor-only diagnostic, copied under _Generated and removed after one capture.
using System;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

[InitializeOnLoad]
public static class AsphaltIsolationProbe
{
    static bool applied;
    static AsphaltIsolationProbe()
    {
        if (Environment.GetEnvironmentVariable("KAMION_ASPHALT_ISOLATE_ROAD") == "1")
            RenderPipelineManager.beginCameraRendering += Isolate;
    }
    static void Isolate(ScriptableRenderContext context, Camera camera)
    {
        if (applied || camera.name != "QA_d_wear_lane_old") return;
        applied = true;
        int kept = 0, shadowsOnly = 0;
        foreach (var renderer in UnityEngine.Object.FindObjectsByType<MeshRenderer>(FindObjectsSortMode.None))
        {
            bool road = false;
            foreach (var material in renderer.sharedMaterials)
                if (material != null && material.name.IndexOf("road_asphalt", StringComparison.OrdinalIgnoreCase) >= 0)
                    road = true;
            if (road) { kept++; continue; }
            // Keep shadow casting, suppress only the visible non-road surfaces.
            renderer.shadowCastingMode = ShadowCastingMode.ShadowsOnly;
            shadowsOnly++;
        }
        Debug.Log($"[ASPHALT_ISOLATION] roadRenderers={kept} nonRoadShadowsOnly={shadowsOnly}; " +
            "diagnostic only, custom indirect instances are not filtered");
    }
}
