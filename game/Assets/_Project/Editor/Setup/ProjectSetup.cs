using System;
using Game.Editor.Build;
using Game.Rendering;
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

        public const string QualityProfilePath = "Assets/_Project/Rendering/Resources/QualityProfile.asset";

        /// <summary>Per-tier values come from the QualityProfile asset (single source of truth, ADR 0010).</summary>
        public static QualityProfile.Tier[] LoadTiers()
        {
            var qp = AssetDatabase.LoadAssetAtPath<QualityProfile>(QualityProfilePath);
            if (qp == null)
            {
                System.IO.Directory.CreateDirectory(System.IO.Path.Combine(EditorTools.ProjectRoot, System.IO.Path.GetDirectoryName(QualityProfilePath)));
                qp = ScriptableObject.CreateInstance<QualityProfile>();
                qp.tiers = QualityProfile.Defaults();
                AssetDatabase.CreateAsset(qp, QualityProfilePath);
                AssetDatabase.SaveAssets();
            }
            // Migration: fields added after the asset was created deserialize as zero - take them from the code defaults.
            bool dirty = false;
            var defs = QualityProfile.Defaults();
            for (int i = 0; i < qp.tiers.Length; i++)
            {
                foreach (var d in defs)
                {
                    if (!string.Equals(d.name, qp.tiers[i].name, StringComparison.OrdinalIgnoreCase)) continue;
                    if (qp.tiers[i].treeCullM <= 0f)
                    {
                        qp.tiers[i].treeCardLodScale = d.treeCardLodScale; qp.tiers[i].treeThinStartM = d.treeThinStartM;
                        qp.tiers[i].treeCullM = d.treeCullM; qp.tiers[i].treeShadowLodMask = d.treeShadowLodMask;
                        qp.tiers[i].leafAlphaToCoverage = d.leafAlphaToCoverage;
                        dirty = true;
                    }
                    if (qp.tiers[i].forestHlodM <= 0f)   // ADR 0015
                    {
                        qp.tiers[i].forestHlodM = d.forestHlodM; qp.tiers[i].forestHlodCullM = d.forestHlodCullM;
                        dirty = true;
                    }
                }
            }
            if (qp.revision < 62)
            {
                // ADR 0062 (owner D36): High render-scale floor 0.80 -> 0.70, FSR 1.0 upscaling, frame-pacing fallback,
                // analytic lamp pools. A floor that someone tuned away from the old default is kept.
                for (int i = 0; i < qp.tiers.Length; i++)
                    foreach (var d in defs)
                    {
                        if (!string.Equals(d.name, qp.tiers[i].name, StringComparison.OrdinalIgnoreCase)) continue;
                        if (Mathf.Abs(qp.tiers[i].adaptiveScaleMin - 0.80f) < 1e-4f) qp.tiers[i].adaptiveScaleMin = d.adaptiveScaleMin;
                        qp.tiers[i].pacingFallbackFps = d.pacingFallbackFps;
                        qp.tiers[i].upscalingFilter = d.upscalingFilter;
                        qp.tiers[i].fsrSharpness = d.fsrSharpness;
                        qp.tiers[i].lampPools = d.lampPools;
                    }
                qp.revision = 62;
                dirty = true;
            }
            if (qp.revision < 80)
            {
                // ADR 0080: cloud deck quality and SSAO per tier (new fields deserialize as 0 / false).
                for (int i = 0; i < qp.tiers.Length; i++)
                    foreach (var d in defs)
                    {
                        if (!string.Equals(d.name, qp.tiers[i].name, StringComparison.OrdinalIgnoreCase)) continue;
                        qp.tiers[i].cloudQuality = d.cloudQuality;
                        qp.tiers[i].ssao = d.ssao;
                    }
                qp.revision = 80;
                dirty = true;
            }
            if (qp.revision < 106)
            {
                // ADR 0106: Truck Glass fast path per tier (Low on).
                for (int i = 0; i < qp.tiers.Length; i++)
                    foreach (var d in defs)
                        if (string.Equals(d.name, qp.tiers[i].name, StringComparison.OrdinalIgnoreCase)) qp.tiers[i].glassFast = d.glassFast;
                qp.revision = QualityProfile.CurrentRevision;
                dirty = true;
            }
            if (qp.deviceRules == null || qp.deviceRules.Length == 0) { qp.deviceRules = QualityProfile.DefaultDeviceRules(); dirty = true; }
            // Always re-serialize: new non-array fields (device rules) exist only as code initialisers until written once.
            EditorUtility.SetDirty(qp); AssetDatabase.SaveAssets();
            _ = dirty;
            return qp.tiers;
        }

        public static void ApplyAll()
        {
            int exit = 0;
            try
            {
                ApplyPlayerSettings();
                ApplyTimeAndLayers();
                var assets = CreateUrpTierAssets();
                ApplyQualityLevels(assets);
                BootSceneBuilder.BuildAndRegister();
                DrivingLabSceneBuilder.Build();
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

        /// <summary>Batchmode: player settings + URP tier assets + quality levels from the QualityProfile only (no scene rebuild).</summary>
        public static void ApplyRenderingBatch()
        {
            int exit = 0;
            try
            {
                ApplyPlayerSettings();
                ApplyQualityLevels(CreateUrpTierAssets());
                AssetDatabase.SaveAssets();
                Debug.Log("SETUP_RESULT: OK");
            }
            catch (Exception e) { Debug.LogException(e); Debug.Log("SETUP_RESULT: FAILED"); exit = 1; }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        [MenuItem("Kamion/Setup/Apply project settings")]
        static void MenuApply()
        {
            ApplyPlayerSettings();
            ApplyTimeAndLayers();
            ApplyQualityLevels(CreateUrpTierAssets());
            AssetDatabase.SaveAssets();
        }

        /// <summary>
        /// Physics step 100 Hz (docs/04 §1), at most 10 fixed steps per rendered frame, and the "Vehicle" layer
        /// (layer 8) that the wheel raycasts exclude.
        /// </summary>
        public static void ApplyTimeAndLayers()
        {
            var tm = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/TimeManager.asset")[0]);
            Find(tm, "Fixed Timestep").floatValue = 0.01f;
            Find(tm, "Maximum Allowed Timestep").floatValue = 0.1f;
            tm.ApplyModifiedPropertiesWithoutUndo();
            var tags = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/TagManager.asset")[0]);
            var layers = Find(tags, "layers");
            layers.GetArrayElementAtIndex(8).stringValue = "Vehicle";
            // World kerbs: hit by the wheel raycasts, never by vehicle body colliders (WorldCollisionCooker).
            layers.GetArrayElementAtIndex(9).stringValue = "WorldKerb";
            tags.ApplyModifiedPropertiesWithoutUndo();
            Physics.IgnoreLayerCollision(8, 9, true);   // also stored in the collision matrix (DynamicsManager)
            Debug.Log("[SETUP] fixedDeltaTime 0.01 s, max 0.1 s/frame, layer 8 = Vehicle, layer 9 = WorldKerb (ignores Vehicle)");
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
            // Debug.Log without a stack trace: every [CONTROLS]/telemetry line otherwise carries a captured trace (cost +
            // an extra logcat line). Warnings, errors, asserts and exceptions keep ScriptOnly traces (ADR 0058 note).
            PlayerSettings.SetStackTraceLogType(LogType.Log, StackTraceLogType.None);
            // World MeshColliders are cooked at load (WorldCollisionCooker, parallel Physics.BakeMesh), not prebaked: the
            // prebaked PhysX data was ~17 MB of the APK (ADR 0012, lead decision 2026-11-09). Collision meshes stay readable.
            PlayerSettings.bakeCollisionMeshes = false;
            // GPU / CPU frame times in the diagnostics CSV (FrameTimingManager) for on-device profiling.
            PlayerSettings.enableFrameTimingStats = true;
            Debug.Log($"[SETUP] player settings: {ApplicationId} min={MinSdk} target={TargetSdk} IL2CPP ARM64 Vulkan+GLES3 linear landscape");
        }

        static UniversalRenderPipelineAsset[] CreateUrpTierAssets()
        {
            var tiers = LoadTiers();
            var result = new UniversalRenderPipelineAsset[tiers.Length];
            for (int i = 0; i < tiers.Length; i++)
            {
                var t = tiers[i];
                string path = $"{SettingsDir}/URP_{t.name}.asset";
                if (AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(path) == null &&
                    !AssetDatabase.CopyAsset(BaseUrpAsset, path))
                    throw new InvalidOperationException($"Cannot create {path} from {BaseUrpAsset}");

                var asset = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(path);
                var so = new SerializedObject(asset);
                Set(so, "m_RenderScale", t.renderScale);
                // ADR 0062: upscaler used whenever the (adaptive) render scale is below 1.
                Set(so, "m_UpscalingFilter", (int)t.upscalingFilter);
                Set(so, "m_FsrOverrideSharpness", t.fsrSharpness > 0f);
                if (t.fsrSharpness > 0f) Set(so, "m_FsrSharpness", t.fsrSharpness);
                Set(so, "m_MSAA", t.msaa);
                Set(so, "m_SupportsHDR", t.hdr);
                Set(so, "m_HDRColorBufferPrecision", 0);            // R11G11B10: same 32 bpp as RGBA8 on the tile
                Set(so, "m_MainLightShadowsSupported", true);
                Set(so, "m_MainLightShadowmapResolution", t.shadowResolution);
                Set(so, "m_ShadowDistance", t.shadowDistance);
                Set(so, "m_ShadowCascadeCount", t.shadowCascades);
                Set(so, "m_Cascade2Split", t.cascade2Split);
                Find(so, "m_Cascade4Split").vector3Value = t.cascade4Split;
                Set(so, "m_Cascade3Split", new Vector2(t.cascade4Split.x, t.cascade4Split.y));
                Set(so, "m_ShadowDepthBias", t.shadowDepthBias);
                Set(so, "m_ShadowNormalBias", t.shadowNormalBias);
                Set(so, "m_SoftShadowsSupported", t.softShadows);
                Set(so, "m_SoftShadowQuality", (int)t.softShadowQuality);
                Set(so, "m_AdditionalLightsPerObjectLimit", t.additionalLightsPerObject);
                Set(so, "m_ColorGradingMode", t.hdr ? 1 : 0);        // HDR grading when the buffer is HDR
                Set(so, "m_ColorGradingLutSize", 32);
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
        static void Set(SerializedObject so, string prop, Vector2 v) { Find(so, prop).vector2Value = v; }

        static SerializedProperty Find(SerializedObject so, string prop) =>
            so.FindProperty(prop) ?? throw new InvalidOperationException($"{so.targetObject.name}: no property {prop}");

        static void ApplyQualityLevels(UniversalRenderPipelineAsset[] assets)
        {
            var qs = AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/QualitySettings.asset")[0];
            var so = new SerializedObject(qs);
            var levels = so.FindProperty("m_QualitySettings");
            var tiers = LoadTiers();
            levels.arraySize = tiers.Length;
            for (int i = 0; i < tiers.Length; i++)
            {
                var t = tiers[i];
                var e = levels.GetArrayElementAtIndex(i);
                e.FindPropertyRelative("name").stringValue = t.name;
                e.FindPropertyRelative("customRenderPipeline").objectReferenceValue = assets[i];
                e.FindPropertyRelative("vSyncCount").intValue = 0;
                // URP owns MSAA (URP_<tier>.m_MSAA) and mirrors it into QualitySettings.antiAliasing whenever the level becomes
                // active; write the same value so the editor does not leave a dirty ProjectSettings diff behind.
                e.FindPropertyRelative("antiAliasing").intValue = t.msaa > 1 ? t.msaa : 0;
                e.FindPropertyRelative("shadowDistance").floatValue = t.shadowDistance;
                e.FindPropertyRelative("lodBias").floatValue = t.lodBias;
                e.FindPropertyRelative("anisotropicTextures").intValue = t.anisotropic;
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
