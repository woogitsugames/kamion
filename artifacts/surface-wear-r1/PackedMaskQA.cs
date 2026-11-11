using System;
using System.IO;
using System.Collections.Generic;
using System.Security.Cryptography;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;
using UnityEngine.Rendering;
namespace SurfaceWearQA
{
 public static class PackedMaskQA
 {
  const string PackedPath="Assets/_Generated/SurfaceWearQA/Textures/T_road_asphalt_packed16_MaskMap.png";
  const string OriginalPath="Assets/_Generated/World/bialystok-industrial-c/Textures/PBR/asphalt_worn/T_asphalt_worn_MaskMap.png";
  static string Arg(string key,string fallback){var a=Environment.GetCommandLineArgs();int i=Array.IndexOf(a,key);return i>=0&&i+1<a.Length?a[i+1]:fallback;}
  static string Repo=>Path.GetFullPath(Path.Combine(Application.dataPath,"../.."));
  static string Out=>Path.Combine(Repo,"artifacts/surface-wear-r1");
  static string Hash(byte[] bytes){using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(bytes)).Replace("-","").ToLowerInvariant();}
  [Serializable] public class ErrorRow {public int mip,size,pixels;public double[] meanAbsGBA;public float[] maxAbsGBA;public double[] fractionOver1GBA,fractionOver3GBA;}
  [Serializable] public class ImportProof {public string note,device,api,oldFormat,newFormat,oldGraphicsFormat,newGraphicsFormat,privatePngSha256;public int oldSize,newSize,mips;public bool linear,alpha,androidASTC8;public long runtimeTextureMemory;public List<ErrorRow> errors=new List<ErrorRow>();}
  static Color[] Sample(Texture texture,int size,float repeat,int mip,Material sampler)
  {
   var rt=RenderTexture.GetTemporary(size,size,0,RenderTextureFormat.ARGBFloat,RenderTextureReadWrite.Linear);
   var prior=RenderTexture.active;Texture2D read=null;
   try{sampler.SetFloat("_QARepeat",repeat);sampler.SetFloat("_QALod",mip);Graphics.Blit(texture,rt,sampler);RenderTexture.active=rt;
    read=new Texture2D(size,size,TextureFormat.RGBAFloat,false,true);read.ReadPixels(new Rect(0,0,size,size),0,0);read.Apply(false,false);return read.GetPixels();}
   finally{RenderTexture.active=prior;if(read!=null)UnityEngine.Object.DestroyImmediate(read);RenderTexture.ReleaseTemporary(rt);}
  }
  public static void ImportProbe()
  {
   int exit=1;Material sampler=null;
   try{
    string input=Path.Combine(Out,"packed-mask16-private/T_road_asphalt_packed16_MaskMap.png");
    Directory.CreateDirectory(Path.GetDirectoryName(Path.Combine(Repo,"game",PackedPath)));
    File.Copy(input,Path.Combine(Repo,"game",PackedPath),true);AssetDatabase.ImportAsset(PackedPath,ImportAssetOptions.ForceSynchronousImport);
    var ti=(TextureImporter)AssetImporter.GetAtPath(PackedPath);ti.textureType=TextureImporterType.Default;ti.sRGBTexture=false;ti.alphaSource=TextureImporterAlphaSource.FromInput;ti.alphaIsTransparency=false;
    ti.mipmapEnabled=true;ti.mipmapFilter=TextureImporterMipFilter.BoxFilter;ti.wrapMode=TextureWrapMode.Repeat;ti.filterMode=FilterMode.Trilinear;ti.anisoLevel=4;ti.maxTextureSize=4096;
    ti.textureCompression=TextureImporterCompression.CompressedHQ;
    ti.SetPlatformTextureSettings(new TextureImporterPlatformSettings{name="Android",overridden=true,maxTextureSize=2048,format=TextureImporterFormat.ASTC_8x8,compressionQuality=50});ti.SaveAndReimport();
    var old=AssetDatabase.LoadAssetAtPath<Texture2D>(OriginalPath);var packed=AssetDatabase.LoadAssetAtPath<Texture2D>(PackedPath);
    if(old==null||packed==null||old.width!=512||packed.width!=2048||packed.mipmapCount!=12)throw new Exception("Unexpected actual imported texture dimensions/mips");
    var settings=ti.GetPlatformTextureSettings("Android");
    var proof=new ImportProof{note="Actual GPU floating-point sampling, original512 repeated4x versus packed2048; linear masks. Android importer is ASTC8, actual device/graphics formats recorded separately. This is not an A16 timing or High image PASS.",
     device=SystemInfo.graphicsDeviceName,api=SystemInfo.graphicsDeviceType.ToString(),oldFormat=old.format.ToString(),newFormat=packed.format.ToString(),oldGraphicsFormat=old.graphicsFormat.ToString(),newGraphicsFormat=packed.graphicsFormat.ToString(),
     privatePngSha256=Hash(File.ReadAllBytes(input)),oldSize=old.width,newSize=packed.width,mips=packed.mipmapCount,linear=!ti.sRGBTexture,alpha=ti.alphaSource==TextureImporterAlphaSource.FromInput,
     androidASTC8=settings.overridden&&settings.format==TextureImporterFormat.ASTC_8x8&&settings.maxTextureSize==2048,runtimeTextureMemory=UnityEngine.Profiling.Profiler.GetRuntimeMemorySizeLong(packed)};
    var shader=Shader.Find("Hidden/SurfaceWearQA/MaskSampler");if(shader==null||ShaderUtil.ShaderHasError(shader))throw new Exception("Missing/error mask sampler shader");sampler=new Material(shader);
    for(int mip=0;mip<12;mip++){
     int size=Math.Max(1,2048>>mip);var a=Sample(old,size,4,mip,sampler);var b=Sample(packed,size,1,mip,sampler);
     var row=new ErrorRow{mip=mip,size=size,pixels=a.Length,meanAbsGBA=new double[3],maxAbsGBA=new float[3],fractionOver1GBA=new double[3],fractionOver3GBA=new double[3]};
     for(int i=0;i<a.Length;i++)for(int c=0;c<3;c++){float error=Mathf.Abs(a[i][c+1]-b[i][c+1])*255f;row.meanAbsGBA[c]+=error;row.maxAbsGBA[c]=Mathf.Max(row.maxAbsGBA[c],error);if(error>1.0001f)row.fractionOver1GBA[c]++;if(error>3.0001f)row.fractionOver3GBA[c]++;}
     for(int c=0;c<3;c++){row.meanAbsGBA[c]/=a.Length;row.fractionOver1GBA[c]/=a.Length;row.fractionOver3GBA[c]/=a.Length;}proof.errors.Add(row);
    }
    if(!proof.linear||!proof.alpha||!proof.androidASTC8)throw new Exception("Mask import contract failed");
    File.WriteAllText(Path.Combine(Out,"packed-mask16-gpu-proof.json"),JsonUtility.ToJson(proof,true));Debug.Log("PACKED_MASK_IMPORT_PROBE: OK");exit=0;
   }catch(Exception e){Debug.LogException(e);}finally{if(sampler!=null)UnityEngine.Object.DestroyImmediate(sampler);}EditorApplication.Exit(exit);
  }
  static readonly Dictionary<Renderer,Material[]> originals=new Dictionary<Renderer,Material[]>();
  static readonly Dictionary<Material,Material> clones=new Dictionary<Material,Material>();
  static void Apply(Scene scene,OpenSceneMode mode)
  {
   var packed=AssetDatabase.LoadAssetAtPath<Texture2D>(PackedPath);var shader=Shader.Find("Hidden/SurfaceWearQA/PackedRoadMask");
   if(packed==null||shader==null||ShaderUtil.ShaderHasError(shader))throw new Exception("Packed road diagnostic input/shader missing or invalid");
   foreach(var r in UnityEngine.Object.FindObjectsByType<MeshRenderer>(FindObjectsInactive.Include,FindObjectsSortMode.None)){
    var old=r.sharedMaterials;var next=(Material[])old.Clone();bool changed=false;
    for(int i=0;i<old.Length;i++){
     var material=old[i];if(material==null||material.name!="M_road_asphalt")continue;
     if(!clones.TryGetValue(material,out var copy)){
      copy=new Material(material){name="M_road_asphalt_QA_PACKED",shader=shader};copy.CopyPropertiesFromMaterial(material);copy.shaderKeywords=material.shaderKeywords;copy.renderQueue=material.renderQueue;copy.enableInstancing=material.enableInstancing;copy.SetTexture("_MaskMap",packed);
      foreach(string property in material.GetTexturePropertyNames())if(property!="_MaskMap"&&(copy.GetTexture(property)!=material.GetTexture(property)||copy.GetTextureScale(property)!=material.GetTextureScale(property)||copy.GetTextureOffset(property)!=material.GetTextureOffset(property)))throw new Exception("Unexpected diagnostic texture change "+property);
      foreach(string property in new[]{"_Tile","_Tint","_PaintWear","_Grime"})if(copy.GetVector(property)!=material.GetVector(property))throw new Exception("Unexpected diagnostic uniform change "+property);
      if(copy.GetFloat("_MetallicScale")!=0)throw new Exception("Packed R must not become metallic");clones.Add(material,copy);
     }next[i]=copy;changed=true;
    }if(changed){originals.Add(r,old);r.sharedMaterials=next;}
   }
  }
  public static void Render()
  {
   int exit=1;EditorSceneManager.sceneOpened+=Apply;bool async=ShaderUtil.allowAsyncCompilation;
   var keywordNames=new HashSet<string>();foreach(var k in Shader.enabledGlobalKeywords)keywordNames.Add(k.name);
   string[] vectors={"_KamionTone","_KamionWet","_KamionHazeColor","_KamionGroundEnv","_KamionHorizonEnv","_KamionVehicleEnvParams"};var saved=new Dictionary<string,Vector4>();foreach(string k in vectors)saved[k]=Shader.GetGlobalVector(k);
   string[] floats={"_KamionExposure","_KamionClearCoatOff","_KamionGrimeDetailOff","_KamionVehicleCapture","_KamionSkyCapOff"};var scalar=new Dictionary<string,float>();foreach(string k in floats)scalar[k]=Shader.GetGlobalFloat(k);
   try{int count=Game.Editor.VisualQA.VisualQaRunner.Render(Arg("-qaScene","WorldC"),2340,1080,Arg("-qaTier","Low"),Arg("-qaOutput",""),Arg("-qaLighting","overcast"),Arg("-qaCameras",""));
    if(count!=4||clones.Count!=1)throw new Exception("Expected4frames/one original old-road material");foreach(var copy in clones.Values)if(copy.shader.name!="Hidden/SurfaceWearQA/PackedRoadMask"||AssetDatabase.GetAssetPath(copy.GetTexture("_MaskMap"))!=PackedPath)throw new Exception("Diagnostic override was reset during rendering");
    Debug.Log("PACKED_MASK_RENDERED: OK frames="+count+" clonedMaterials="+clones.Count);exit=0;
   }catch(Exception e){Debug.LogException(e);}finally{
    EditorSceneManager.sceneOpened-=Apply;foreach(var p in originals)if(p.Key!=null)p.Key.sharedMaterials=p.Value;foreach(var m in clones.Values)UnityEngine.Object.DestroyImmediate(m);
    foreach(var p in saved)Shader.SetGlobalVector(p.Key,p.Value);foreach(var p in scalar)Shader.SetGlobalFloat(p.Key,p.Value);
    foreach(var k in Shader.enabledGlobalKeywords)if(!keywordNames.Contains(k.name))Shader.DisableKeyword(k.name);foreach(string k in keywordNames)Shader.EnableKeyword(k);
    ShaderUtil.allowAsyncCompilation=async;Debug.Log("PACKED_MASK_RESTORED: renderers="+originals.Count+" clones="+clones.Count+" globals/keywords restored");originals.Clear();clones.Clear();
   }EditorApplication.Exit(exit);
  }
 }
}
