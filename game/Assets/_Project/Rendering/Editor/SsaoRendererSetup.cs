using System;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering.Editor
{
    /// <summary>
    /// ADR 0080: the Ultra tier's own renderer with URP screen-space ambient occlusion (after opaques, depth source,
    /// half resolution, interleaved-gradient noise, low sample count and blur). A separate renderer asset instead of a
    /// feature toggled at run time on the shared <c>Mobile_Renderer</c>: Low / Medium / High keep a renderer with no
    /// features (no depth prepass, no extra passes, no variants), and nothing is written to assets at run time.
    /// Reproducible: <c>-executeMethod Game.Rendering.Editor.SsaoRendererSetup.EnsureBatch</c> (or the menu item).
    /// The world shaders are custom (no _SCREEN_SPACE_OCCLUSION sampling), hence "after opaque": the AO is blended
    /// over the lit colour, which is right for an ambient-dominated overcast and a compromise under direct sun
    /// (kept weak: intensity 1, radius 0.6 m, falloff 80 m). WORKING_VALUE until measured on the Fold / S24+.
    /// </summary>
    public static class SsaoRendererSetup
    {
        public const string BaseRenderer = "Assets/_Project/Rendering/Settings/Mobile_Renderer.asset";
        public const string SsaoRenderer = "Assets/_Project/Rendering/Settings/Mobile_Renderer_SSAO.asset";
        public const string UltraAsset = "Assets/_Project/Rendering/Settings/URP_Ultra.asset";

        public static void EnsureBatch()
        {
            int exit = 0;
            try { Ensure(); Debug.Log("SSAO_SETUP_RESULT: OK"); }
            catch (Exception e) { Debug.LogException(e); Debug.Log("SSAO_SETUP_RESULT: FAILED"); exit = 1; }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        [MenuItem("Kamion/Rendering/Create Ultra SSAO renderer")]
        public static void Ensure()
        {
            if (AssetDatabase.LoadAssetAtPath<UniversalRendererData>(SsaoRenderer) == null && !AssetDatabase.CopyAsset(BaseRenderer, SsaoRenderer))
                throw new InvalidOperationException("cannot copy " + BaseRenderer);
            var data = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(SsaoRenderer);
            ScreenSpaceAmbientOcclusion ssao = null;
            foreach (var f in data.rendererFeatures) if (f is ScreenSpaceAmbientOcclusion s) ssao = s;
            if (ssao == null)
            {
                ssao = ScriptableObject.CreateInstance<ScreenSpaceAmbientOcclusion>();
                ssao.name = "ScreenSpaceAmbientOcclusion";
                AssetDatabase.AddObjectToAsset(ssao, data);
                data.rendererFeatures.Add(ssao);
            }
            var so = new SerializedObject(ssao);
            Set(so, "m_Settings.AOMethod", 1);              // InterleavedGradient (no blue-noise textures)
            so.FindProperty("m_Settings.Downsample").boolValue = true;
            so.FindProperty("m_Settings.AfterOpaque").boolValue = true;
            Set(so, "m_Settings.Source", 0);                // Depth (normals reconstructed; no DepthNormals pass in our shaders)
            Set(so, "m_Settings.NormalSamples", 1);         // Medium
            so.FindProperty("m_Settings.Intensity").floatValue = 1.0f;
            so.FindProperty("m_Settings.DirectLightingStrength").floatValue = 0.25f;
            so.FindProperty("m_Settings.Radius").floatValue = 0.6f;
            Set(so, "m_Settings.Samples", 2);               // Low
            Set(so, "m_Settings.BlurQuality", 2);           // Low (single kawase)
            so.FindProperty("m_Settings.Falloff").floatValue = 80f;
            so.ApplyModifiedPropertiesWithoutUndo();
            ssao.SetActive(true);
            EditorUtility.SetDirty(ssao);

            // feature map (local file ids), as the renderer-data inspector writes it
            AssetDatabase.SaveAssets();
            var dso = new SerializedObject(data);
            var map = dso.FindProperty("m_RendererFeatureMap");
            map.arraySize = data.rendererFeatures.Count;
            for (int i = 0; i < data.rendererFeatures.Count; i++)
                if (AssetDatabase.TryGetGUIDAndLocalFileIdentifier(data.rendererFeatures[i], out string _, out long id))
                    map.GetArrayElementAtIndex(i).longValue = id;
            dso.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(data);

            var urp = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(UltraAsset);
            if (urp == null) throw new InvalidOperationException("missing " + UltraAsset);
            var uso = new SerializedObject(urp);
            var list = uso.FindProperty("m_RendererDataList");
            if (list.arraySize < 2) list.arraySize = 2;
            list.GetArrayElementAtIndex(0).objectReferenceValue = data;
            // ADR 0152: index 1 = the plain renderer for the reflection capture (a render request through the SSAO renderer
            // failed every face on the Fold/Adreno 840: "RenderPass: Fake or uninitialized surface", "EndRenderPass: Not inside a Renderpass").
            list.GetArrayElementAtIndex(1).objectReferenceValue = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(BaseRenderer);
            uso.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(urp);
            AssetDatabase.SaveAssets();
        }

        static void Set(SerializedObject so, string prop, int v)
        {
            var p = so.FindProperty(prop);
            if (p == null) throw new InvalidOperationException("SSAO setting not found: " + prop);
            if (p.propertyType == SerializedPropertyType.Enum) p.enumValueIndex = v; else p.intValue = v;
        }
    }
}
