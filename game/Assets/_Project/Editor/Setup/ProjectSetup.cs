using System;
using Game.Editor.Build;
using UnityEditor;
using UnityEditor.Build;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Editor.Setup
{
    /// <summary>
    /// Idempotent project configuration as code (Stage 0). Re-run after editor upgrades:
    ///   Unity.exe -batchmode -quit -buildTarget Android -projectPath game
    ///     -executeMethod Game.Editor.Setup.ProjectSetup.ApplyAll
    /// Rationale for the values: docs/adr/0006-graphics-api-and-android-targets.md.
    /// Tier values are WORKING_VALUEs — rendering-perf owns the tuning.
    /// </summary>
    public static class ProjectSetup
    {
        public const string CompanyName = "woogitsugames";
        public const string ProductName = "Kamion";
        public const string ApplicationId = "com.woogitsugames.kamion";
        public const string Version = "0.1.0";
        public const int MinSdk = 29;      // Android 10: Vulkan 1.1 baseline, thermal API
        public const int TargetSdk = 36;   // Google Play requirement for new apps since 2025-08-31 → 2026-08-31 (API 36)

        public const string SettingsDir = "Assets/_Project/Rendering/Settings";
        const string BaseUrpAsset = SettingsDir + "/Mobile_RPAsset.asset";

        struct Tier
        {
            public string Name;
            public float RenderScale;
            public int Msaa;
            public bool Hdr;
            public float ShadowDistance;
            public int ShadowResolution;
            public int Cascades;
            public bool SoftShadows;
            public int AdditionalLightsPerObject;
            public float LodBias;
            public int Anisotropic; // 0 disable, 1 per-texture, 2 force
        }

        static readonly Tier[] k_Tiers =
        {
            new Tier { Name = "Low",    RenderScale = 0.75f, Msaa = 1, Hdr = false, ShadowDistance = 30f,  ShadowResolution = 512,  Cascades = 1, SoftShadows = false, AdditionalLightsPerObject = 2, LodBias = 0.6f, Anisotropic = 0 },
            new Tier { Name = "Medium", RenderScale = 0.85f, Msaa = 2, Hdr = false, ShadowDistance = 50f,  ShadowResolution = 1024, Cascades = 1, SoftShadows = false, AdditionalLightsPerObject = 4, LodBias = 1.0f, Anisotropic = 1 },
            new Tier { Name = "High",   RenderScale = 1.0f,  Msaa = 4, Hdr = true,  ShadowDistance = 80f,  ShadowResolution = 2048, Cascades = 2, SoftShadows = true,  AdditionalLightsPerObject = 4, LodBias = 1.5f, Anisotropic = 1 },
            new Tier { Name = "Ultra",  RenderScale = 1.0f,  Msaa = 4, Hdr = true,  ShadowDistance = 120f, ShadowResolution = 2048, Cascades = 4, SoftShadows = true,  AdditionalLightsPerObject = 8, LodBias = 2.0f, Anisotropic = 2 },
        };

        public static void ApplyAll()
        {
            int exit = 0;
            try
            {
                ApplyPlayerSettings();
                var assets = CreateUrpTierAssets();
                ApplyQualityLevels(assets);
                BootSceneBuilder.BuildAndRegister();
                AssetDatabase.SaveAssets();
                Debug.Log("SETUP_RESULT: OK");
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Debug.Log("SETUP_RESULT: FAILED");
                exit = 1;
            }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        [MenuItem("Kamion/Setup/Apply project settings")]
        static void MenuApply()
        {
            ApplyPlayerSettings();
            ApplyQualityLevels(CreateUrpTierAssets());
            AssetDatabase.SaveAssets();
        }

        public static void ApplyPlayerSettings()
        {
            var android = NamedBuildTarget.Android;
            PlayerSettings.companyName = CompanyName;
            PlayerSettings.productName = ProductName;
            PlayerSettings.bundleVersion = Version;
            PlayerSettings.SetApplicationIdentifier(android, ApplicationId);
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Standalone, ApplicationId);

            PlayerSettings.SetScriptingBackend(android, ScriptingImplementation.IL2CPP);
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
            PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.Android, false);
            PlayerSettings.SetGraphicsAPIs(BuildTarget.Android, new[] { GraphicsDeviceType.Vulkan, GraphicsDeviceType.OpenGLES3 });
            PlayerSettings.colorSpace = ColorSpace.Linear;
            PlayerSettings.Android.minSdkVersion = (AndroidSdkVersions)MinSdk;
            PlayerSettings.Android.targetSdkVersion = (AndroidSdkVersions)TargetSdk;

            PlayerSettings.defaultInterfaceOrientation = UIOrientation.AutoRotation;
            PlayerSettings.allowedAutorotateToPortrait = false;
            PlayerSettings.allowedAutorotateToPortraitUpsideDown = false;
            PlayerSettings.allowedAutorotateToLandscapeLeft = true;
            PlayerSettings.allowedAutorotateToLandscapeRight = true;
            PlayerSettings.Android.renderOutsideSafeArea = true; // UI keeps to Screen.safeArea itself
            PlayerSettings.Android.optimizedFramePacing = true;
            PlayerSettings.Android.startInFullscreen = true;
            PlayerSettings.Android.preferredInstallLocation = AndroidPreferredInstallLocation.Auto;
            PlayerSettings.SetManagedStrippingLevel(android, ManagedStrippingLevel.Low);
            PlayerSettings.SetIl2CppCompilerConfiguration(android, Il2CppCompilerConfiguration.Release);
            Debug.Log($"[SETUP] player settings: {ApplicationId} min={MinSdk} target={TargetSdk} IL2CPP ARM64 Vulkan+GLES3 linear landscape");
        }

        static UniversalRenderPipelineAsset[] CreateUrpTierAssets()
        {
            var result = new UniversalRenderPipelineAsset[k_Tiers.Length];
            for (int i = 0; i < k_Tiers.Length; i++)
            {
                var t = k_Tiers[i];
                string path = $"{SettingsDir}/URP_{t.Name}.asset";
                if (AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(path) == null &&
                    !AssetDatabase.CopyAsset(BaseUrpAsset, path))
                    throw new InvalidOperationException($"Cannot create {path} from {BaseUrpAsset}");

                var asset = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(path);
                var so = new SerializedObject(asset);
                Set(so, "m_RenderScale", t.RenderScale);
                Set(so, "m_MSAA", t.Msaa);
                Set(so, "m_SupportsHDR", t.Hdr);
                Set(so, "m_HDRColorBufferPrecision", 0);
                Set(so, "m_MainLightShadowsSupported", true);
                Set(so, "m_MainLightShadowmapResolution", t.ShadowResolution);
                Set(so, "m_ShadowDistance", t.ShadowDistance);
                Set(so, "m_ShadowCascadeCount", t.Cascades);
                Set(so, "m_SoftShadowsSupported", t.SoftShadows);
                Set(so, "m_AdditionalLightsPerObjectLimit", t.AdditionalLightsPerObject);
                Set(so, "m_AdditionalLightShadowsSupported", false);
                Set(so, "m_RequireDepthTexture", false);
                Set(so, "m_RequireOpaqueTexture", false);
                Set(so, "m_UseSRPBatcher", true);
                so.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(asset);
                result[i] = asset;
            }
            AssetDatabase.SaveAssets();
            return result;
        }

        static void Set(SerializedObject so, string prop, float v) { Find(so, prop).floatValue = v; }
        static void Set(SerializedObject so, string prop, int v) { Find(so, prop).intValue = v; }
        static void Set(SerializedObject so, string prop, bool v) { Find(so, prop).boolValue = v; }

        static SerializedProperty Find(SerializedObject so, string prop) =>
            so.FindProperty(prop) ?? throw new InvalidOperationException($"{so.targetObject.name}: no property {prop}");

        static void ApplyQualityLevels(UniversalRenderPipelineAsset[] assets)
        {
            var qs = AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/QualitySettings.asset")[0];
            var so = new SerializedObject(qs);
            var levels = so.FindProperty("m_QualitySettings");
            levels.arraySize = k_Tiers.Length;
            for (int i = 0; i < k_Tiers.Length; i++)
            {
                var t = k_Tiers[i];
                var e = levels.GetArrayElementAtIndex(i);
                e.FindPropertyRelative("name").stringValue = t.Name;
                e.FindPropertyRelative("customRenderPipeline").objectReferenceValue = assets[i];
                e.FindPropertyRelative("vSyncCount").intValue = 0;
                e.FindPropertyRelative("antiAliasing").intValue = 0; // URP asset owns MSAA
                e.FindPropertyRelative("shadowDistance").floatValue = t.ShadowDistance;
                e.FindPropertyRelative("lodBias").floatValue = t.LodBias;
                e.FindPropertyRelative("anisotropicTextures").intValue = t.Anisotropic;
                e.FindPropertyRelative("globalTextureMipmapLimit").intValue = 0;
                e.FindPropertyRelative("realtimeReflectionProbes").boolValue = false;
                e.FindPropertyRelative("softParticles").boolValue = false;
                e.FindPropertyRelative("skinWeights").intValue = i < 2 ? 2 : 4;
                e.FindPropertyRelative("excludedTargetPlatforms").arraySize = 0;
            }

            var perPlatform = so.FindProperty("m_PerPlatformDefaultQuality");
            for (int i = 0; i < perPlatform.arraySize; i++)
            {
                var pair = perPlatform.GetArrayElementAtIndex(i);
                string platform = pair.FindPropertyRelative("first").stringValue;
                int level = platform == "Standalone" ? 2 : 1; // desktop High, mobile & rest Medium
                pair.FindPropertyRelative("second").intValue = level;
            }
            so.FindProperty("m_CurrentQuality").intValue = 1;
            so.ApplyModifiedPropertiesWithoutUndo();

            GraphicsSettings.defaultRenderPipeline = assets[1];
            AssetDatabase.SaveAssets();
            Debug.Log("[SETUP] quality tiers: " + string.Join(", ", QualitySettings.names));
        }
    }
}
