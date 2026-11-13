using System;
using System.Collections.Generic;
using System.IO;
using Game.Editor.Build;
using UnityEditor;
using UnityEngine;
using static Game.World.Import.MiniJson;

namespace Game.World.Import
{
    /// <summary>ADR0153 opt-in palette atlas. Reuses World PBR and its existing instanced pass.</summary>
    public static class VehicleLodAtlasMaterials
    {
        public static float[] LodEnds(Dictionary<string, object> extras, int count)
        {
            var values = Arr(extras.Get("vehicle_lod_ends_m"));
            if (values == null || values.Count != count) throw new InvalidOperationException("Vehicle LOD distance count mismatch");
            var result = new float[count];
            for (int i = 0; i < count; i++)
            {
                result[i] = (float)Num(values[i]);
                if (float.IsNaN(result[i]) || float.IsInfinity(result[i]) || result[i] <= (i == 0 ? 0 : result[i - 1]))
                    throw new InvalidOperationException("Vehicle LOD distances must be positive, finite and increasing");
            }
            if (!Mathf.Approximately(result[count - 1], WorldInstances.VehicleCullM))
                throw new InvalidOperationException("Vehicle atlas must preserve cull distance");
            return result;
        }

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
            var albedo = InstanceImporter.ImportTexture(region, WorldLibrary.Resolve(region.Region, "textures", "vehicle_lod_details_BaseColor.png"), true);
            var mask = InstanceImporter.ImportTexture(region, WorldLibrary.Resolve(region.Region, "textures", "vehicle_lod_details_MaskMap.png"), true, true);
            mat.SetTexture("_BaseMap", albedo);
            mat.SetTexture("_MaskMap", mask);
            if (!WorldPbrMaterials.Imported.Contains(albedo)) WorldPbrMaterials.Imported.Add(albedo);
            if (!WorldPbrMaterials.Imported.Contains(mask)) WorldPbrMaterials.Imported.Add(mask);
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
            mat.SetOverrideTag("KamionVehicleLodAtlas", "1"); // explicit native migration marker, ADR0153
            EditorUtility.SetDirty(mat);
            return mat;
        }
    }
}
