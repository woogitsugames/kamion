using System.Collections.Generic;
using System.IO;
using UnityEditor;

namespace Game.Editor.Setup
{
    /// <summary>Single place that defines the scenes in the build (Boot first).</summary>
    public static class BuildScenes
    {
        public static readonly string[] Paths = { BootSceneBuilder.ScenePath, DrivingLabSceneBuilder.ScenePath };

        public static void Apply()
        {
            var list = new List<EditorBuildSettingsScene>();
            foreach (var p in Paths)
                if (File.Exists(Path.Combine(Build.EditorTools.ProjectRoot, p))) list.Add(new EditorBuildSettingsScene(p, true));
            EditorBuildSettings.scenes = list.ToArray();
        }
    }
}
