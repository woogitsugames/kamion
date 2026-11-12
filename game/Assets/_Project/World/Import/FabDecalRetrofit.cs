using System.IO;
using Game.Editor.Build;
using UnityEditor;
using UnityEngine;

namespace Game.World.Import
{
    /// <summary>ADR 0131: converts already imported Fab cover / drain materials (URP Lit) to the World PBR road-decal
    /// state that <see cref="FabMaterials"/> now creates at import, without a full region reimport. Idempotent.
    /// Batch: -executeMethod Game.World.Import.FabDecalRetrofit.RunBatch -region bialystok-industrial-c</summary>
    public static class FabDecalRetrofit
    {
        public static void RunBatch()
        {
            string region = EditorTools.Arg("-region", "bialystok-industrial-c");
            int n = Run(region);
            Debug.Log($"[FabDecalRetrofit] converted={n} region={region}");
            EditorApplication.Exit(n >= 0 ? 0 : 1);
        }

        public static int Run(string region)
        {
            string dir = $"Assets/_Generated/World/{region}/Materials";
            if (!AssetDatabase.IsValidFolder(dir)) { Debug.LogError("[FabDecalRetrofit] missing " + dir); return -1; }
            int n = 0;
            foreach (var guid in AssetDatabase.FindAssets("t:Material M_fab_", new[] { dir }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                string id = Path.GetFileNameWithoutExtension(path).Substring(2);   // M_fab_x -> fab_x
                if (!(id.Contains("cover") || id.Contains("drain"))) continue;
                var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
                var baseMap = mat.GetTexture("_BaseMap") as Texture2D;
                var mask = mat.HasProperty("_MetallicGlossMap") ? mat.GetTexture("_MetallicGlossMap") as Texture2D
                         : mat.GetTexture("_MaskMap") as Texture2D;
                if (baseMap == null) { Debug.LogWarning("[FabDecalRetrofit] no base map: " + path); continue; }
                FabMaterials.ApplyDecal(mat, baseMap, mask);
                Debug.Log($"[FabDecalRetrofit] {path} -> {mat.shader.name} mask={(mask != null ? mask.name : "none")}");
                n++;
            }
            AssetDatabase.SaveAssets();
            return n;
        }
    }
}
