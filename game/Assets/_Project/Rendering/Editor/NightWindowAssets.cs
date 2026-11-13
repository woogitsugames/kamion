using UnityEditor;
using UnityEngine;

namespace Game.Rendering.Editor
{
    /// <summary>
    /// ADR 0192: import settings of the night data (Resources/Night, written by night_facade.py) and the material flags of
    /// the facades that carry windows.
    /// - *Id textures: point sampled, no mips, uncompressed, linear (the shader LOADs one texel: cell centre + class must be
    ///   exact - any filtering or block compression would split a window into two decisions).
    /// - *T textures: linear, bilinear, mips (no shimmer at distance), default compression (ASTC on Android).
    /// - Materials: facade_atlas (mode 1) and the LOD1 row materials "*__far_*" (mode 2) get _NIGHTWIN; RegionImporter calls
    ///   <see cref="ApplyMaterial"/> for every new import, <see cref="ApplyRegionMaterials"/> patches an imported region.
    /// </summary>
    public sealed class NightWindowAssets : AssetPostprocessor
    {
        public const string Folder = "Assets/_Project/Rendering/Resources/Night/";

        void OnPreprocessTexture()
        {
            if (!assetPath.StartsWith(Folder)) return;
            var ti = (TextureImporter)assetImporter;
            ti.sRGBTexture = false;
            ti.wrapMode = TextureWrapMode.Repeat;
            ti.textureType = TextureImporterType.Default;
            ti.alphaSource = TextureImporterAlphaSource.FromInput;
            ti.npotScale = TextureImporterNPOTScale.None;
            if (assetPath.EndsWith("Id.png"))
            {
                ti.filterMode = FilterMode.Point;
                ti.mipmapEnabled = false;
                ti.textureCompression = TextureImporterCompression.Uncompressed;
                foreach (var platform in new[] { "Android", "iPhone", "Standalone" })
                {
                    var s = ti.GetPlatformTextureSettings(platform);
                    s.overridden = true;
                    s.format = TextureImporterFormat.RGBA32;
                    s.textureCompression = TextureImporterCompression.Uncompressed;
                    ti.SetPlatformTextureSettings(s);
                }
            }
            else
            {
                ti.filterMode = FilterMode.Bilinear;
                ti.mipmapEnabled = true;
                ti.alphaSource = TextureImporterAlphaSource.None;
                ti.textureCompression = TextureImporterCompression.Compressed;
            }
        }

        /// <summary>Night-window mode of a world material id: 1 facade atlas, 2 LOD1 storey rows, 0 none.</summary>
        public static int ModeFor(string materialId)
        {
            if (string.IsNullOrEmpty(materialId)) return 0;
            string id = materialId.StartsWith("M_") ? materialId.Substring(2) : materialId;
            if (id == "facade_atlas") return 1;
            if (id.Contains("__far_")) return 2;
            return 0;
        }

        public static bool ApplyMaterial(Material m, string materialId)
        {
            int mode = ModeFor(materialId);
            if (m == null || !m.HasProperty("_NightWindows")) return false;
            bool changed = false;
            if (mode > 0)
            {
                if (!m.IsKeywordEnabled("_NIGHTWIN")) { m.EnableKeyword("_NIGHTWIN"); changed = true; }
                if (m.GetFloat("_NightWindows") != mode) { m.SetFloat("_NightWindows", mode); changed = true; }
            }
            else if (m.IsKeywordEnabled("_NIGHTWIN")) { m.DisableKeyword("_NIGHTWIN"); m.SetFloat("_NightWindows", 0f); changed = true; }
            if (changed) EditorUtility.SetDirty(m);
            return changed;
        }

        /// <summary>Batch: -executeMethod Game.Rendering.Editor.NightWindowAssets.ApplyRegionMaterials (all imported regions).</summary>
        public static void ApplyRegionMaterials()
        {
            int n = 0, seen = 0;
            foreach (var guid in AssetDatabase.FindAssets("t:Material", new[] { "Assets/_Generated/World" }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var m = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (m == null) continue;
                seen++;
                if (ApplyMaterial(m, m.name)) n++;
            }
            AssetDatabase.SaveAssets();
            Debug.Log($"[NightWindows] region materials: {seen} seen, {n} changed");
        }
    }
}
