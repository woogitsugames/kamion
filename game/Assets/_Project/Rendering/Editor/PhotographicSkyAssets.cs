using System;
using UnityEditor;
using UnityEngine;

namespace Game.Rendering.Editor
{
    /// <summary>Own sky-map import contract (ADR 0108). Does not change world materials or renderer assets.</summary>
    public static class PhotographicSkyAssets
    {
        public static void PrepareBatch()
        {
            int exit = 1;
            try
            {
                string[] ids = { "T_ClearClouds", "T_ClearClouds_02", "T_ClearClouds_03" };
                for (int i = 0; i < ids.Length; i++)
                {
                    string path = $"Assets/_Project/Rendering/Resources/Sky/{ids[i]}.png";
                    var importer = AssetImporter.GetAtPath(path) as TextureImporter;
                    if (importer == null) throw new InvalidOperationException("Missing derived CC0 cloud map: " + path);
                    importer.textureType = TextureImporterType.Default;
                    importer.sRGBTexture = false;
                    importer.mipmapEnabled = true;
                    importer.isReadable = false;
                    importer.alphaSource = TextureImporterAlphaSource.None;
                    importer.wrapModeU = TextureWrapMode.Repeat;
                    importer.wrapModeV = TextureWrapMode.Clamp;
                    importer.filterMode = FilterMode.Trilinear;
                    importer.anisoLevel = 1;
                    importer.maxTextureSize = 4096;
                    importer.textureCompression = TextureImporterCompression.CompressedHQ;
                    importer.SetPlatformTextureSettings(new TextureImporterPlatformSettings {
                        name = "Android", overridden = true, maxTextureSize = 4096,
                        format = TextureImporterFormat.ASTC_6x6, textureCompression = TextureImporterCompression.CompressedHQ
                    });
                    importer.SaveAndReimport();
                }
                PhotographicClouds.ResetCache();
                if (PhotographicClouds.VariantCount != ids.Length)
                    throw new InvalidOperationException($"Expected {ids.Length} cloud variants, got {PhotographicClouds.VariantCount}");
                for (int i = 0; i < ids.Length; i++)
                {
                    if (!PhotographicClouds.TryGet(i, out var texture, out var sun) || texture.width != 4096 || texture.height != 2048)
                        throw new InvalidOperationException($"Cloud texture variant {i} ({ids[i]}) or source axis failed import validation");
                    Debug.Log($"SKY_ASSETS_VARIANT[{i}]: id={ids[i]} width={texture.width} height={texture.height} sourceSun={sun}");
                }
                Debug.Log($"SKY_ASSETS_RESULT: OK variants={ids.Length}");
                exit = 0;
            }
            catch (Exception e) { Debug.LogException(e); Debug.Log("SKY_ASSETS_RESULT: FAILED"); }
            if (Application.isBatchMode) EditorApplication.Exit(exit);
        }
    }
}
