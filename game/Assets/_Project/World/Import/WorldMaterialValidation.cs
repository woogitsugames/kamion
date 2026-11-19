using System.IO;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Game.World.Import
{
    /// <summary>Never serialize a missing material slot or a known broken shader into a world scene.</summary>
    public static class WorldMaterialValidation
    {
        public static Material Require(Material material, string context)
        {
            if (material == null) throw new InvalidDataException($"[WORLD_MATERIAL] {context}: missing material");
            var shader = material.shader;
            if (shader == null || shader.name == "Hidden/InternalErrorShader" || ShaderUtil.ShaderHasError(shader))
                throw new InvalidDataException($"[WORLD_MATERIAL] {context}: {material.name}, shader '{shader?.name}', keywords [{string.Join(",", material.shaderKeywords)}]: missing shader or compilation error");
            return material;
        }
    }

    /// <summary>Also check existing scenes: rebuilding a player does not rerun the world importer.</summary>
    public sealed class WorldMaterialBuildGuard : IProcessSceneWithReport
    {
        public int callbackOrder => 0;

        public void OnProcessScene(Scene scene, BuildReport report)
        {
            if (report == null) return; // player builds only
            foreach (var root in scene.GetRootGameObjects())
            {
                if (!root.TryGetComponent<WorldRegionRoot>(out var region)) continue;
                var edge = root.transform.Find("WorldEdge");
                if (edge != null)
                    foreach (Transform child in edge)
                        if (child.name.StartsWith("ClosureGroup_", System.StringComparison.Ordinal))
                            throw new BuildFailedException($"{scene.path}: legacy grouped closures; reimport region '{region.regionId}' (both tiers) before building");
                foreach (var renderer in root.GetComponentsInChildren<Renderer>(true))
                {
                    var mats = renderer.sharedMaterials;
                    for (int i = 0; i < mats.Length; i++)
                        WorldMaterialValidation.Require(mats[i], $"{scene.path}/{region.regionId}/{renderer.name}, slot {i}");
                }
                foreach (var instances in root.GetComponentsInChildren<WorldInstances>(true))
                    if (instances.set != null)
                        foreach (var material in instances.set.materials)
                            WorldMaterialValidation.Require(material, $"{scene.path}/{region.regionId}/{instances.set.name}");
            }
        }
    }
}
