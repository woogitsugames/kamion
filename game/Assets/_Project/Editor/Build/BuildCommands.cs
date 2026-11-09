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

            var scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray();
            if (scenes.Length == 0)
            {
                Debug.LogError("BUILD_RESULT: Failed (no scenes in build settings)");
                return 3;
            }

            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outputPath)));
            EditorUserBuildSettings.buildAppBundle = false;
            EditorUserBuildSettings.exportAsGoogleAndroidProject = false;

            var options = new BuildPlayerOptions
            {
                scenes = scenes,
                locationPathName = outputPath,
                target = BuildTarget.Android,
                targetGroup = BuildTargetGroup.Android,
                options = development ? BuildOptions.Development : BuildOptions.None,
            };

            Debug.Log($"[BUILD] Android APK → {outputPath} (development={development}) scenes=[{string.Join(", ", scenes)}]");
            BuildReport report = BuildPipeline.BuildPlayer(options);
            var s = report.summary;
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
    }
}
