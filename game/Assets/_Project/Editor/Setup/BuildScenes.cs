using System.Collections.Generic;
using System.IO;
using UnityEditor;

namespace Game.Editor.Setup
{
    /// <summary>
    /// Single place that defines the scenes in the build (Boot first). Generated world scenes (gitignored, created by
    /// scripts/import-region.ps1) are included only when they exist.
    /// </summary>
    public static class BuildScenes
    {
        public const string WorldCScenePath = "Assets/_Generated/World/bialystok-industrial-c/WorldC.unity";
        public static readonly string[] Paths = { BootSceneBuilder.ScenePath, DrivingLabSceneBuilder.ScenePath, WorldCScenePath };

        public static void Apply()
        {
            var list = new List<EditorBuildSettingsScene>();
            foreach (var p in Paths)
                if (File.Exists(Path.Combine(Build.EditorTools.ProjectRoot, p))) list.Add(new EditorBuildSettingsScene(p, true));
            EditorBuildSettings.scenes = list.ToArray();
        }
    }
}
