using System;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering.Editor
{
    /// <summary>
    /// ADR 0269: writes the PC URP assets (Resources/PcTiers/URP_PC_*.asset) and their renderers from
    /// <see cref="PcTierTable"/> - the generator behind the committed YAML (CLAUDE.md rule 7). Mobile assets
    /// (Settings/URP_*.asset), QualitySettings and GraphicsSettings are never touched.
    /// Renderers: PC_Renderer = copy of Mobile_Renderer, PC_Renderer_SSAO = copy of Mobile_Renderer_SSAO with the SAME SSAO
    /// settings (the SSAO keyword variants are kept in the build only for settings some quality-level asset uses; ADR 0269).
    /// Batch: -executeMethod Game.Rendering.Editor.PcTierAssetsSetup.EnsureBatch
    /// </summary>
    public static class PcTierAssetsSetup
    {
        public const string Dir = "Assets/_Project/Rendering/Resources/PcTiers";
        public const string BaseAsset = "Assets/_Project/Rendering/Settings/URP_Ultra.asset";
        public const string PcRenderer = Dir + "/PC_Renderer.asset";
        public const string PcRendererSsao = Dir + "/PC_Renderer_SSAO.asset";

        public static string AssetPath(PcTier t) => $"{Dir}/URP_PC_{PcTierTable.NameOf(t)}.asset";

        public static void EnsureBatch()
        {
            int exit = 0;
            try { Ensure(); Debug.Log("PC_TIERS_SETUP_RESULT: OK"); }
            catch (Exception e) { Debug.LogException(e); Debug.Log("PC_TIERS_SETUP_RESULT: FAILED"); exit = 1; }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        [MenuItem("Kamion/Rendering/Write PC tier URP assets (ADR 0269)")]
        public static void Ensure()
        {
            var errors = PcTierTable.Validate(PcTierTable.Defaults());
            if (errors.Count > 0) throw new InvalidOperationException("PcTierTable invalid: " + string.Join("; ", errors));
            if (!AssetDatabase.IsValidFolder(Dir)) AssetDatabase.CreateFolder("Assets/_Project/Rendering/Resources", "PcTiers");
            Copy(SsaoRendererSetup.BaseRenderer, PcRenderer);
            Copy(SsaoRendererSetup.SsaoRenderer, PcRendererSsao);
            var plain = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(PcRenderer);
            var ssao = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(PcRendererSsao);
            foreach (PcTier t in Enum.GetValues(typeof(PcTier)))
            {
                string path = AssetPath(t);
                Copy(BaseAsset, path);
                var asset = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(path);
                Write(asset, PcTierTable.Get(t), plain, ssao);
            }
            AssetDatabase.SaveAssets();
        }

        static void Copy(string from, string to)
        {
            if (AssetDatabase.LoadMainAssetAtPath(to) == null && !AssetDatabase.CopyAsset(from, to))
                throw new InvalidOperationException($"cannot copy {from} -> {to}");
        }

        static void Write(UniversalRenderPipelineAsset asset, PcTierSettings s, UniversalRendererData plain, UniversalRendererData ssao)
        {
            var so = new SerializedObject(asset);
            var list = so.FindProperty("m_RendererDataList");
            // SSAO tiers: [SSAO, plain] like URP_Ultra (VehicleReflectionCapture renders the cube with index 1, ADR 0152).
            var renderers = s.ssao ? new ScriptableRendererData[] { ssao, plain } : new ScriptableRendererData[] { plain };
            list.arraySize = renderers.Length;
            for (int i = 0; i < renderers.Length; i++) list.GetArrayElementAtIndex(i).objectReferenceValue = renderers[i];
            so.FindProperty("m_DefaultRendererIndex").intValue = 0;
            Set(so, "m_RenderScale", s.renderScale);
            Set(so, "m_UpscalingFilter", 0);
            Set(so, "m_FsrOverrideSharpness", false);
            Set(so, "m_MSAA", s.msaa);
            Set(so, "m_SupportsHDR", s.hdr);
            Set(so, "m_HDRColorBufferPrecision", 0);
            Set(so, "m_MainLightShadowsSupported", true);
            Set(so, "m_MainLightShadowmapResolution", s.shadowResolution);
            Set(so, "m_ShadowDistance", s.shadowDistance);
            Set(so, "m_ShadowCascadeCount", s.shadowCascades);
            Set(so, "m_Cascade2Split", s.cascade2Split);
            so.FindProperty("m_Cascade3Split").vector2Value = new Vector2(s.cascade3SplitX, s.cascade3SplitY);
            so.FindProperty("m_Cascade4Split").vector3Value = new Vector3(s.cascade4SplitX, s.cascade4SplitY, s.cascade4SplitZ);
            Set(so, "m_ShadowDepthBias", s.shadowDepthBias);
            Set(so, "m_ShadowNormalBias", s.shadowNormalBias);
            Set(so, "m_SoftShadowsSupported", s.softShadows);
            Set(so, "m_SoftShadowQuality", s.softShadowQuality);
            Set(so, "m_AdditionalLightsPerObjectLimit", s.additionalLightsPerObject);
            Set(so, "m_AdditionalLightShadowsSupported", false);
            Set(so, "m_ColorGradingMode", s.hdr ? 1 : 0);
            Set(so, "m_ColorGradingLutSize", 32);
            Set(so, "m_RequireDepthTexture", false);
            Set(so, "m_RequireOpaqueTexture", false);
            Set(so, "m_UseSRPBatcher", true);
            // ADR 0299: URP's dither round-trips through GetLinearToSRGB / GetSRGBToLinear; the fast approximations crush the
            // darks (linear 0.0037 -> 0.0021, sRGB 12 -> 7: the night sky / road of every dithered tier).
            Set(so, "m_UseFastSRGBLinearConversion", false);
            so.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(asset);
        }

        /// <summary>Differences between a PC URP asset and the table (empty = equal). Used by the EditMode test.</summary>
        public static List<string> Diff(UniversalRenderPipelineAsset a, PcTierSettings s)
        {
            var d = new List<string>();
            if (a == null) { d.Add("asset missing"); return d; }
            void Eq(object got, object want, string what) { if (!Equals(got, want)) d.Add($"{what}: asset {got} table {want}"); }
            void Near(float got, float want, string what) { if (Mathf.Abs(got - want) > 1e-4f) d.Add($"{what}: asset {got} table {want}"); }
            Near(a.renderScale, s.renderScale, "renderScale");
            Eq(a.msaaSampleCount, s.msaa, "msaa");
            Eq(a.supportsHDR, s.hdr, "hdr");
            Near(a.shadowDistance, s.shadowDistance, "shadowDistance");
            Eq(a.mainLightShadowmapResolution, s.shadowResolution, "shadowResolution");
            Eq(a.shadowCascadeCount, s.shadowCascades, "shadowCascades");
            Near(a.cascade2Split, s.cascade2Split, "cascade2Split");
            Near(a.cascade3Split.x, s.cascade3SplitX, "cascade3Split.x");
            Near(a.cascade3Split.y, s.cascade3SplitY, "cascade3Split.y");
            Near(a.cascade4Split.x, s.cascade4SplitX, "cascade4Split.x");
            Near(a.cascade4Split.y, s.cascade4SplitY, "cascade4Split.y");
            Near(a.cascade4Split.z, s.cascade4SplitZ, "cascade4Split.z");
            Near(a.shadowDepthBias, s.shadowDepthBias, "shadowDepthBias");
            Near(a.shadowNormalBias, s.shadowNormalBias, "shadowNormalBias");
            Eq(a.supportsSoftShadows, s.softShadows, "softShadows");
            Eq(a.maxAdditionalLightsCount, s.additionalLightsPerObject, "additionalLightsPerObject");
            var so = new SerializedObject(a);
            Eq(so.FindProperty("m_SoftShadowQuality").intValue, s.softShadowQuality, "softShadowQuality");
            Eq(so.FindProperty("m_UpscalingFilter").intValue, 0, "upscalingFilter");
            Eq(so.FindProperty("m_UseFastSRGBLinearConversion").boolValue, false, "useFastSRGBLinearConversion (ADR 0299)");
            bool hasSsao = false;
            var r0 = a.rendererDataList.Length > 0 ? a.rendererDataList[0] : null;
            if (r0 != null)
                foreach (var f in r0.rendererFeatures) if (f is ScreenSpaceAmbientOcclusion && f.isActive) hasSsao = true;
            Eq(hasSsao, s.ssao, "ssao (default renderer)");
            return d;
        }

        static void Set(SerializedObject so, string prop, float v) => Find(so, prop).floatValue = v;
        static void Set(SerializedObject so, string prop, int v) => Find(so, prop).intValue = v;
        static void Set(SerializedObject so, string prop, bool v) => Find(so, prop).boolValue = v;
        static SerializedProperty Find(SerializedObject so, string prop) =>
            so.FindProperty(prop) ?? throw new InvalidOperationException($"{so.targetObject.name}: no property {prop}");
    }
}
