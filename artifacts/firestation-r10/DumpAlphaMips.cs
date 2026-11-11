// QA ONLY: copied temporarily into ignored Assets/_Generated/FireStationR7QA/Editor.
// No production material/import setting is changed. Outputs actual Editor imported mip pixels.
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

public static class FireStationR7AlphaMips
{
    public static void Run()
    {
        int exit=0;
        try
        {
            string repo=Path.GetFullPath(Path.Combine(Application.dataPath,"../.."));
            string task=Path.Combine(repo,"artifacts/firestation-r10");
            string actual="Assets/_Generated/World/bialystok-industrial-c/Textures/fire_station_alpha.png";
            var source=(TextureImporter)AssetImporter.GetAtPath(actual);
            if(source==null) throw new InvalidOperationException("Source alpha importer missing");
            var original=AssetDatabase.LoadAssetAtPath<Texture2D>(actual);
            string qa="Assets/_Generated/FireStationR7QA";
            Directory.CreateDirectory(Path.Combine(repo,"game",qa));
            foreach(string phase in new[]{"before","after"})
            {
                string input=phase=="before"?Path.Combine(task,"baseline-materials/fire_station_alpha.png"):
                    Path.Combine(repo,"art-source/world/textures/fire_station_alpha.png");
                string dst=qa+"/alpha_"+phase+".png";
                File.Copy(input,Path.Combine(repo,"game",dst),true);
                AssetDatabase.ImportAsset(dst,ImportAssetOptions.ForceSynchronousImport);
                var ti=(TextureImporter)AssetImporter.GetAtPath(dst);
                var settings=new TextureImporterSettings();source.ReadTextureSettings(settings);ti.SetTextureSettings(settings);
                ti.textureCompression=source.textureCompression;ti.compressionQuality=source.compressionQuality;
                ti.crunchedCompression=source.crunchedCompression;ti.maxTextureSize=source.maxTextureSize;
                ti.SetPlatformTextureSettings(source.GetDefaultPlatformTextureSettings());
                foreach(string platform in new[]{"Standalone","Android"})ti.SetPlatformTextureSettings(source.GetPlatformTextureSettings(platform));
                ti.isReadable=true;ti.SaveAndReimport();
                var texture=AssetDatabase.LoadAssetAtPath<Texture2D>(dst);
                if(texture.width!=original.width || texture.height!=original.height || texture.format!=original.format)
                    throw new InvalidOperationException("QA clone differs from actual source texture resolution/format");
                string output=Path.Combine(task,"actual-alpha-mips",phase);Directory.CreateDirectory(output);
                File.WriteAllText(Path.Combine(output,"import.txt"),
                    $"QA_CLONE_OF={actual}\nsize={texture.width}x{texture.height}\nformat={texture.format}\nmips={texture.mipmapCount}\n"+
                    $"preserveCoverage={ti.mipMapsPreserveCoverage}\ncutoff={ti.alphaTestReferenceValue}\nalphaTransparency={ti.alphaIsTransparency}\n"+
                    $"readableOverrideForQA=true\nandroidFormat={ti.GetPlatformTextureSettings("Android").format}\n"+
                    $"actualSourceFormat={original.format}\nactualSourceSize={original.width}x{original.height}\n"+
                    "Editor mip data; phone GPU/ASTC appearance remains unverified.\n");
                for(int mip=0;mip<texture.mipmapCount;mip++)
                {
                    int w=Math.Max(1,texture.width>>mip),h=Math.Max(1,texture.height>>mip);
                    var pixels=texture.GetPixels32(mip);
                    var readable=new Texture2D(w,h,TextureFormat.RGBA32,false);
                    readable.SetPixels32(pixels);readable.Apply(false,false);
                    File.WriteAllBytes(Path.Combine(output,$"mip{mip:D2}.png"),readable.EncodeToPNG());
                    UnityEngine.Object.DestroyImmediate(readable);
                }
            }
            Debug.Log("E_ALPHA_MIPS_RESULT: OK");
        }
        catch(Exception e){Debug.LogException(e);Debug.Log("E_ALPHA_MIPS_RESULT: FAILED");exit=1;}
        if(Application.isBatchMode)EditorApplication.Exit(exit);
    }
}
