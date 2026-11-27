using System;
using System.IO;
using System.Linq;
using System.Text;
using Game.Editor.Build;
using UnityEditor;
using UnityEngine;
using UnityEngine.Profiling;

namespace Game.World.Import
{
    /// <summary>impostor-rebake-s24 (ADR 0023 dopisek): imported size, format, mips and runtime memory of every tree
    /// impostor atlas (impostor_tree_*.png + _n.png) under Assets/_Generated/World/*/Textures. Measurement only.
    /// Batch: -executeMethod Game.World.Import.ImpostorAtlasAudit.Run -auditOut path.tsv [-auditReimport 1]
    /// -auditReimport 1 re-applies the importer settings of InstanceImporter.ImportTexture (so a rebake copied over
    /// the generated textures is measured with the importer the region import would use).</summary>
    public static class ImpostorAtlasAudit
    {
        public static void Run()
        {
            int exit = 1;
            try
            {
                string outPath = EditorTools.Arg("-auditOut", Path.Combine(EditorTools.RepoRoot, "artifacts/impostor-rebake-s24/atlas-audit.tsv"));
                bool reimport = EditorTools.Arg("-auditReimport", "0") == "1";
                var guids = AssetDatabase.FindAssets("impostor_tree_ t:Texture2D", new[] { "Assets/_Generated/World" });
                var paths = guids.Select(AssetDatabase.GUIDToAssetPath).Where(p => p.Contains("/Textures/impostor_tree_")).OrderBy(p => p).ToList();
                var sb = new StringBuilder("path\tsrc_w\tsrc_h\tw\th\tformat\tmips\tnpot\tmax\tbytes\n");
                long total = 0, totalA = 0, totalN = 0;
                foreach (var p in paths)
                {
                    var ti = (TextureImporter)AssetImporter.GetAtPath(p);
                    if (reimport)
                    {
                        // the PC settings of InstanceImporter.ImportTexture (kept in sync by hand; measurement only)
                        ti.npotScale = InstanceImporter.ImpostorNpotScale;
                        ti.maxTextureSize = p.EndsWith("_n.png") ? InstanceImporter.ImpostorNormalMaxSize : InstanceImporter.ImpostorMaxSize;
                        ti.SaveAndReimport();
                    }
                    ti.GetSourceTextureWidthAndHeight(out int sw, out int sh);
                    var t = AssetDatabase.LoadAssetAtPath<Texture2D>(p);
                    long b = Profiler.GetRuntimeMemorySizeLong(t);
                    total += b;
                    if (p.EndsWith("_n.png")) totalN += b; else totalA += b;
                    sb.Append($"{p}\t{sw}\t{sh}\t{t.width}\t{t.height}\t{t.format}\t{t.mipmapCount}\t{ti.npotScale}\t{ti.maxTextureSize}\t{b}\n");
                }
                sb.Append($"#TOTAL\t{paths.Count} textures\t\t\t\t\t\t\t\t{total}\n");
                Directory.CreateDirectory(Path.GetDirectoryName(outPath));
                File.WriteAllText(outPath, sb.ToString());
                Debug.Log($"IMPOSTOR_AUDIT: n={paths.Count} total_mb={total / 1048576.0:F2} albedo_mb={totalA / 1048576.0:F2} normal_mb={totalN / 1048576.0:F2} -> {outPath}");
                exit = 0;
            }
            catch (Exception e) { Debug.LogException(e); }
            EditorApplication.Exit(exit);
        }
    }
}
