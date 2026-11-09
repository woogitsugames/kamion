using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace Game.Editor.Build
{
    /// <summary>
    /// Batchmode build entry points. Always exit the editor with 0 on success, non-zero on failure.
    ///   Unity.exe -batchmode -quit -buildTarget Android -projectPath game
    ///     -executeMethod Game.Editor.Build.BuildCommands.BuildAndroidApk
    ///     [-buildOutput path/to.apk] [-development]
    /// Prints "BUILD_RESULT: Succeeded|Failed ..." for scripts.
    /// </summary>
    public static class BuildCommands
    {
        public static void BuildAndroidApk()
        {
            int exit = 1;
            try
            {
                exit = BuildAndroid(
                    EditorTools.Arg("-buildOutput", Path.Combine(EditorTools.RepoRoot, "artifacts", "apk", "kamion.apk")),
                    EditorTools.HasArg("-development"));
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                Debug.Log("BUILD_RESULT: Failed (exception)");
            }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }

        [MenuItem("Kamion/Build/Android APK (release-like)")]
        static void MenuBuildRelease() => BuildAndroid(Path.Combine(EditorTools.RepoRoot, "artifacts", "apk", "kamion.apk"), false);

        public static int BuildAndroid(string outputPath, bool development)
        {
            if (EditorUserBuildSettings.activeBuildTarget != BuildTarget.Android &&
                !EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.Android, BuildTarget.Android))
            {
                Debug.LogError("BUILD_RESULT: Failed (cannot switch to Android; start Unity with -buildTarget Android)");
                return 2;
            }

            // Vehicle audio: generated WAVs are not in git; import them when present (build-android.ps1 renders them if missing).
            bool audio = Game.Editor.Audio.VehicleAudioImporter.ImportIfNeeded();
            Debug.Log(audio ? "[BUILD] vehicle audio library present" : "[BUILD] WARNING: no vehicle audio (art-source/audio/generated missing) - the APK will be silent");

            var scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToList();
            // Content tiers (ADR 0012): the High world scene ships only when asked for (-worldHigh); the default APK
            // carries the Low/Medium content only.
            const string worldHigh = "Assets/_Generated/World/bialystok-industrial-c/WorldC_High.unity";
            if (EditorTools.HasArg("-worldHigh"))
            {
                if (File.Exists(Path.Combine(EditorTools.ProjectRoot, worldHigh))) scenes.Add(worldHigh);
                else Debug.LogWarning("[BUILD] -worldHigh: " + worldHigh + " missing (scripts/import-region.ps1)");
            }
            if (scenes.Count == 0)
            {
                Debug.LogError("BUILD_RESULT: Failed (no scenes in build settings)");
                return 3;
            }

            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outputPath)));
            EditorUserBuildSettings.buildAppBundle = false;
            EditorUserBuildSettings.exportAsGoogleAndroidProject = false;

            var options = new BuildPlayerOptions
            {
                scenes = scenes.ToArray(),
                locationPathName = outputPath,
                target = BuildTarget.Android,
                targetGroup = BuildTargetGroup.Android,
                // LZ4HC: the world meshes compress ~2x better than with LZ4 and decompress just as fast at load (ADR 0012).
                options = development ? BuildOptions.Development : BuildOptions.CompressWithLz4HC,
            };

            Debug.Log($"[BUILD] Android APK → {outputPath} (development={development}) scenes=[{string.Join(", ", scenes)}]");
            // BuildInfoWriter sets versionCode from the git commit count for this build only;
            // restore it afterwards so building never dirties ProjectSettings.asset.
            int savedVersionCode = PlayerSettings.Android.bundleVersionCode;
            BuildReport report;
            try { report = BuildPipeline.BuildPlayer(options); }
            finally
            {
                PlayerSettings.Android.bundleVersionCode = savedVersionCode;
                AssetDatabase.SaveAssets();
            }
            var s = report.summary;
            WriteContentReport(report, outputPath);
            bool ok = s.result == BuildResult.Succeeded;
            Debug.Log($"BUILD_RESULT: {s.result} errors={s.totalErrors} warnings={s.totalWarnings} " +
                      $"size={s.totalSize} time={s.totalTime.TotalSeconds:F0}s output={s.outputPath}");
            if (!ok)
            {
                foreach (var step in report.steps)
                foreach (var m in step.messages)
                    if (m.type == LogType.Error || m.type == LogType.Exception)
                        Debug.Log($"BUILD_ERROR: {m.content}");
            }
            return ok ? 0 : 1;
        }

        /// <summary>Packed size per asset type and for the generated world (build report) → log + JSON next to the APK.</summary>
        static void WriteContentReport(BuildReport report, string outputPath)
        {
            try
            {
                var byType = new System.Collections.Generic.Dictionary<string, ulong>();
                ulong world = 0, worldMeshes = 0;
                foreach (var pa in report.packedAssets)
                foreach (var c in pa.contents)
                {
                    string t = c.type != null ? c.type.Name : "?";
                    byType.TryGetValue(t, out ulong v);
                    byType[t] = v + c.packedSize;
                    if (c.sourceAssetPath != null && c.sourceAssetPath.StartsWith("Assets/_Generated/World/"))
                    {
                        world += c.packedSize;
                        var parts = c.sourceAssetPath.Split('/');
                        string key = "world/" + (parts.Length > 5 ? parts[4] + (parts.Length > 6 ? "/" + parts[5] : "") : parts[parts.Length - 1]);
                        byType.TryGetValue(key, out ulong wv);
                        byType[key] = wv + c.packedSize;
                        if (t == "Mesh") worldMeshes += c.packedSize;
                    }
                }
                var top = byType.OrderByDescending(k => k.Value).Take(16).Select(k => $"{k.Key} {k.Value / 1048576.0:F1}");
                Debug.Log($"BUILD_CONTENT: world={world / 1048576.0:F1} MB (meshes {worldMeshes / 1048576.0:F1} MB, uncompressed) by type: {string.Join(", ", top)}");
                const string nl = "\n";
                var json = "{" + nl + "  \"world_bytes\": " + world + "," + nl + "  \"world_mesh_bytes\": " + worldMeshes + "," + nl +
                           "  \"by_type\": {" + nl +
                           string.Join("," + nl, byType.OrderByDescending(k => k.Value).Select(k => $"    \"{k.Key}\": {k.Value}")) + nl + "  }" + nl + "}" + nl;
                File.WriteAllText(Path.ChangeExtension(outputPath, ".content.json"), json);
            }
            catch (Exception e) { Debug.LogWarning("[BUILD] content report failed: " + e.Message); }
        }
    }
}
