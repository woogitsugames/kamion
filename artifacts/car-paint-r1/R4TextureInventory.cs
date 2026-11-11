using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using Game.Editor.Build;
using UnityEditor;
using UnityEngine;
using UnityEngine.Experimental.Rendering;
using UnityEngine.Profiling;
namespace Game.Editor.VisualQA {
 public static class R4TextureInventory {
  [Serializable] public class TextureRow {public string path,guid,format,graphicsFormat,androidFormat;public int width,height,mips,androidMax,sourceWidth,sourceHeight;public long nativeMipPayloadBytes,profilerRuntimeBytes,androidAstcMipBytes;public bool androidOverride;}
  [Serializable] public class SceneRow {public string scene;public string[] currentTextures,r3CounterfactualTextures;public int currentObjects,r3Objects;public long currentNativeMipPayload,r3NativeMipPayload,currentAndroidProjection,r3AndroidProjection;}
  [Serializable] public class Report {public string unity,graphics,method,note;public TextureRow[] textures;public SceneRow[] scenes;public int generatedLegacyObjects,generatedCleanObjects;}
  static long Astc(int width,int height,int block,int mips){long sum=0;for(int m=0;m<mips;m++){sum+=(long)((width+block-1)/block)*((height+block-1)/block)*16;width=Math.Max(1,width/2);height=Math.Max(1,height/2);}return sum;}
  public static void RunBatch(){
   string dir="Assets/_Generated/World/bialystok-industrial-c";
   var paths=AssetDatabase.FindAssets("t:Texture2D",new[]{dir+"/Textures/PBR"}).Select(AssetDatabase.GUIDToAssetPath).Where(p=>p.Contains("/car_grime/")||p.Contains("/car_grime_clean/")).Distinct().OrderBy(p=>p).ToArray();
   var rows=new List<TextureRow>();
   foreach(string path in paths){var texture=AssetDatabase.LoadAssetAtPath<Texture2D>(path);var importer=(TextureImporter)AssetImporter.GetAtPath(path);var android=importer.GetPlatformTextureSettings("Android");importer.GetSourceTextureWidthAndHeight(out int sw,out int sh);
    long bytes=0;int w=texture.width,h=texture.height;for(int m=0;m<texture.mipmapCount;m++){bytes+=(long)GraphicsFormatUtility.ComputeMipmapSize(w,h,texture.graphicsFormat);w=Math.Max(1,w/2);h=Math.Max(1,h/2);}
    var match=Regex.Match(android.format.ToString(),@"ASTC_(\d+)x(\d+)");float scale=Math.Min(1f,(float)android.maxTextureSize/Math.Max(sw,sh));int aw=Math.Max(1,Mathf.RoundToInt(sw*scale)),ah=Math.Max(1,Mathf.RoundToInt(sh*scale));int mipCount=importer.mipmapEnabled?1+(int)Math.Floor(Math.Log(Math.Max(aw,ah),2)):1;
    rows.Add(new TextureRow{path=path,guid=AssetDatabase.AssetPathToGUID(path),format=texture.format.ToString(),graphicsFormat=texture.graphicsFormat.ToString(),androidFormat=android.format.ToString(),width=texture.width,height=texture.height,mips=texture.mipmapCount,androidMax=android.maxTextureSize,sourceWidth=sw,sourceHeight=sh,nativeMipPayloadBytes=bytes,profilerRuntimeBytes=Profiler.GetRuntimeMemorySizeLong(texture),androidAstcMipBytes=android.overridden&&match.Success?Astc(aw,ah,int.Parse(match.Groups[1].Value),mipCount):-1,androidOverride=android.overridden});
   }
   var scenes=new List<SceneRow>();
   foreach(string name in new[]{"WorldC","WorldC_High"}){string path=dir+"/"+name+".unity";var current=AssetDatabase.GetDependencies(path,true).Where(p=>paths.Contains(p)).Distinct().OrderBy(p=>p).ToArray();
    var old=current.Select(p=>p.Replace("/car_grime_clean/","/car_grime/").Replace("car_grime_clean_","car_grime_")).Distinct().OrderBy(p=>p).ToArray();
    long Sum(string[] selected,Func<TextureRow,long> selector)=>selected.Sum(p=>selector(rows.Single(r=>r.path==p)));
    scenes.Add(new SceneRow{scene=name,currentTextures=current,r3CounterfactualTextures=old,currentObjects=current.Length,r3Objects=old.Length,currentNativeMipPayload=Sum(current,r=>r.nativeMipPayloadBytes),r3NativeMipPayload=Sum(old,r=>r.nativeMipPayloadBytes),currentAndroidProjection=Sum(current,r=>r.androidAstcMipBytes),r3AndroidProjection=Sum(old,r=>r.androidAstcMipBytes)});
   }
   var report=new Report{unity=Application.unityVersion,graphics=SystemInfo.graphicsDeviceType.ToString(),method="Actual generated Texture2D objects/formats/mips and scene dependency GUIDs. R3 counterfactual replaces only seven clean paint bindings by their pinned legacy maps; geometry/dependencies otherwise unchanged.",note="Native mip payload estimate excludes driver alignment/streaming and CPU copies. Profiler includes engine overhead and is not GPU-only. Android ASTC is exact-block complete-mip projection from actual override/source dimensions, UNVERIFIED on A16; no phone memory claim. Generated asset objects are distinct from scene-resident dependency estimates.",textures=rows.ToArray(),scenes=scenes.ToArray(),generatedLegacyObjects=paths.Count(p=>p.Contains("/car_grime/")),generatedCleanObjects=paths.Count(p=>p.Contains("/car_grime_clean/"))};
   File.WriteAllText(Path.Combine(EditorTools.RepoRoot,"artifacts/car-paint-r1/r4-clean-texture-residency.json"),JsonUtility.ToJson(report,true));Debug.Log("R4_TEXTURE_INVENTORY_RESULT: OK textures="+rows.Count);
  }
 }
}
