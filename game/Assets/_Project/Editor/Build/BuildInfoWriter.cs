using System;
using System.IO;
using Game.Core;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace Game.Editor.Build
{
    /// <summary>
    /// Bakes version + git SHA into Assets/_Project/Core/Resources/build_info.json before every
    /// player build (file is git-ignored). Also sets the Android versionCode from the commit count.
    /// </summary>
    public sealed class BuildInfoWriter : IPreprocessBuildWithReport
    {
        public const string AssetPath = "Assets/_Project/Core/Resources/" + BuildInfo.ResourceName + ".json";

        public int callbackOrder => -100;

        public void OnPreprocessBuild(BuildReport report)
        {
            bool dev = (report.summary.options & BuildOptions.Development) != 0;
            var info = Write(dev);
            Debug.Log($"[BUILD] build_info: {JsonUtility.ToJson(info)}");
        }

        public static BuildInfo Write(bool development)
        {
            string sha = EditorTools.Git("rev-parse --short=10 HEAD") ?? "unknown";
            string status = EditorTools.Git("status --porcelain --untracked-files=no");
            int.TryParse(EditorTools.Git("rev-list --count HEAD"), out int count);

            var info = new BuildInfo
            {
                version = PlayerSettings.bundleVersion,
                gitSha = sha,
                gitDirty = !string.IsNullOrEmpty(status),
                versionCode = Math.Max(1, count),
                buildTimeUtc = DateTime.UtcNow.ToString("yyyy-MM-dd'T'HH:mm:ss'Z'"),
                unityVersion = Application.unityVersion,
                development = development,
            };
            PlayerSettings.Android.bundleVersionCode = info.versionCode;

            string full = Path.Combine(EditorTools.ProjectRoot, AssetPath);
            Directory.CreateDirectory(Path.GetDirectoryName(full));
            File.WriteAllText(full, JsonUtility.ToJson(info, true));
            AssetDatabase.ImportAsset(AssetPath, ImportAssetOptions.ForceSynchronousImport);
            return info;
        }
    }
}
