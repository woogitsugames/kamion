using System;
using System.IO;
using Game.Editor.Build;
using UnityEditor;
using UnityEngine;

namespace Game.World.Import
{
    /// <summary>ADR0153 opt-in palette atlas. Reuses World PBR and its existing instanced pass.</summary>
    public static class VehicleLodAtlasMaterials
    {
        public static Material Create(RegionImporter.Result region, string path)
        {
            var shader = Shader.Find("Kamion/World PBR")
                ?? throw new InvalidOperationException("Kamion/World PBR missing");
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(shader); AssetDatabase.CreateAsset(mat, path); }
            mat.shader = shader;
            mat.shaderKeywords = Array.Empty<string>();
            mat.EnableKeyword("_UV_MESH0");
            mat.enableInstancing = true;
            var dir = Path.Combine(EditorTools.RepoRoot, "art-source", "world", "textures");
            var albedo = InstanceImporter.ImportTexture(region, Path.Combine(dir, "vehicle_lod_details_BaseColor.png"), true);
            var mask = InstanceImporter.ImportTexture(region, Path.Combine(dir, "vehicle_lod_details_MaskMap.png"), true, true);
            mat.SetTexture("_BaseMap", albedo);
            mat.SetTexture("_MaskMap", mask);
            WorldPbrMaterials.SetLinearTint(mat, Vector3.one);
            mat.SetVector("_Tile", new Vector4(1, 1, 16, 1));
            mat.SetFloat("_AlbedoScale", 1);
            mat.SetFloat("_NormalStrength", 0);
            mat.SetFloat("_SmoothnessScale", 1);
            mat.SetFloat("_MetallicScale", 1);
            mat.SetFloat("_MacroStrength", 0);
            mat.SetFloat("_MacroWear", 0);
            mat.SetFloat("_ElementJitter", 0);
            mat.SetFloat("_ReceiveShadows", 1);
            mat.SetFloat("_OffsetFactor", 0);
            mat.SetFloat("_OffsetUnits", 0);
            mat.SetVector("_SkyOcc", Vector4.zero);
            mat.renderQueue = -1;
            mat.SetOverrideTag("RenderType", "Opaque");
            EditorUtility.SetDirty(mat);
            return mat;
        }
    }
}
