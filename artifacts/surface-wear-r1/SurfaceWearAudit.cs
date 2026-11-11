using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using Unity.Collections;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
namespace SurfaceWearQA
{
 public static class SurfaceWearAudit
 {
  [Serializable] public sealed class MeshRow { public string scene,path,positions,normals,indices,uv0,uv1,uv1y,uv1ySource;public int vertices,submeshes;public bool hasUv1;public List<SubRow> parts=new List<SubRow>(); }
  [Serializable] public sealed class SubRow { public string material,keywords;public int triangles,constantHalfTriangles,shortApproachVertices;public double area,constantHalfArea;public float minimumTyreLength; }
  [Serializable] public sealed class MatRow { public string path,shader,keywords;public List<string> fields=new List<string>(); }
  [Serializable] public sealed class Packet { public string note;public List<MeshRow> meshes=new List<MeshRow>();public List<MatRow> materials=new List<MatRow>(); }
  static string Arg(string key,string fallback){var a=Environment.GetCommandLineArgs();int i=Array.IndexOf(a,key);return i>=0&&i+1<a.Length?a[i+1]:fallback;}
  static string Digest(MemoryStream s){using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(s.ToArray())).Replace("-","").ToLowerInvariant();}
  static string Vec3Hash(NativeArray<Vector3> a){using(var s=new MemoryStream())using(var w=new BinaryWriter(s)){foreach(var v in a){w.Write(v.x);w.Write(v.y);w.Write(v.z);}w.Flush();return Digest(s);}}
  static string Vec2Hash(NativeArray<Vector2> a){using(var s=new MemoryStream())using(var w=new BinaryWriter(s)){foreach(var v in a){w.Write(v.x);w.Write(v.y);}w.Flush();return Digest(s);}}
  static string YHash(NativeArray<Vector2> a){using(var s=new MemoryStream())using(var w=new BinaryWriter(s)){foreach(var v in a)w.Write(v.y);w.Flush();return Digest(s);}}
  static string SourceYHash(string repo,string name)
  {
   var bits=name.Split('_');string chunk=bits[0]+"_"+bits[1];string layer=string.Join("_",bits,2,bits.Length-2);
   var g=Game.World.Import.GlbReader.Load(Path.Combine(repo,"Data/raw/derived/bialystok-industrial-c/world/chunk_"+chunk+".glb"));
   using(var stream=new MemoryStream())using(var writer=new BinaryWriter(stream))
   {foreach(var p in g.Find(layer).Primitives)for(int i=0;i<p.Positions.Length;i++){float y=p.Uv1!=null?p.Uv1[i].y:(layer=="road"&&(p.Material=="road_asphalt"||p.Material=="road_asphalt_new")?5f:0f);writer.Write(Mathf.HalfToFloat(Mathf.FloatToHalf(y)));}writer.Flush();return Digest(stream);}
  }
  public static void Run()
  {
   string repo=Path.GetFullPath(Path.Combine(Application.dataPath,"../.."));string output=Arg("-surfaceAuditOut",Path.Combine(repo,"artifacts/surface-wear-r1/native-before.json"));
   var packet=new Packet{note="ActualuploadedUnityroad/markingmeshesviaEditorMeshUtility. Position/normal/index/UV0 hashesseparatefromUV1. Area islocalUnitym2, NOTpixelcoverage. ConstantUVx.5 isnotproofauthorship, butactualwheelmaskzero. Materialsserializedbindings, globaldetailtiergatesremainseparate."};var seenMats=new HashSet<string>();
   foreach(string scene in new[]{"WorldC","WorldC_High"})
   {
    EditorSceneManager.OpenScene("Assets/_Generated/World/bialystok-industrial-c/"+scene+".unity",OpenSceneMode.Single);var seen=new HashSet<string>();
    foreach(var renderer in UnityEngine.Object.FindObjectsByType<MeshRenderer>(FindObjectsInactive.Include,FindObjectsSortMode.None))
    {
     var filter=renderer.GetComponent<MeshFilter>();var mesh=filter==null?null:filter.sharedMesh;if(mesh==null)continue;string path=AssetDatabase.GetAssetPath(mesh);
     if(!path.Contains("_Generated/World/")||!(mesh.name.EndsWith("_road")||mesh.name.EndsWith("_markings"))||!seen.Add(path+"#"+mesh.name))continue;
     var row=new MeshRow{scene=scene,path=path+"#"+mesh.name,vertices=mesh.vertexCount,submeshes=mesh.subMeshCount,hasUv1=mesh.HasVertexAttribute(VertexAttribute.TexCoord1)};var mats=renderer.sharedMaterials;
     using(var data=MeshUtility.AcquireReadOnlyMeshData(mesh))using(var v=new NativeArray<Vector3>(mesh.vertexCount,Allocator.Temp))using(var n=new NativeArray<Vector3>(mesh.vertexCount,Allocator.Temp))using(var u0=new NativeArray<Vector2>(mesh.vertexCount,Allocator.Temp))using(var u1=new NativeArray<Vector2>(mesh.vertexCount,Allocator.Temp))using(var stream=new MemoryStream())using(var writer=new BinaryWriter(stream))
     {
      var d=data[0];d.GetVertices(v);d.GetNormals(n);if(mesh.HasVertexAttribute(VertexAttribute.TexCoord0))d.GetUVs(0,u0);if(row.hasUv1)d.GetUVs(1,u1);
      row.uv1y=row.hasUv1?YHash(u1):"ABSENT_SHADER_DEFAULT0";row.uv1ySource=row.hasUv1?SourceYHash(repo,mesh.name):"ABSENT_SHADER_DEFAULT0";row.positions=Vec3Hash(v);row.normals=Vec3Hash(n);row.uv0=Vec2Hash(u0);row.uv1=row.hasUv1?Vec2Hash(u1):"ABSENT_SHADER_DEFAULT0";
      for(int si=0;si<mesh.subMeshCount;si++)using(var index=new NativeArray<int>(d.GetSubMesh(si).indexCount,Allocator.Temp))
      {
       d.GetIndices(index,si);writer.Write(si);writer.Write(index.Length);foreach(int k in index)writer.Write(k);
       Material mat=si<mats.Length?mats[si]:null;var part=new SubRow{material=mat==null?"MISSING":mat.name,keywords=mat==null?"":string.Join(",",mat.shaderKeywords)};
       for(int j=0;j+2<index.Length;j+=3){int a=index[j],b=index[j+1],c=index[j+2];double ar=Vector3.Cross(v[b]-v[a],v[c]-v[a]).magnitude*.5;part.area+=ar;part.triangles++;if(row.hasUv1&&Mathf.Abs(u1[a].x-.5f)<.00001f&&Mathf.Abs(u1[b].x-.5f)<.00001f&&Mathf.Abs(u1[c].x-.5f)<.00001f){part.constantHalfTriangles++;part.constantHalfArea+=ar;}}
       if(row.hasUv1&&part.material=="M_decal_tyre")
       {
        var tyreVertices=new HashSet<int>();foreach(int k in index)tyreVertices.Add(k);
        part.minimumTyreLength=float.PositiveInfinity;
        foreach(int k in tyreVertices){part.minimumTyreLength=Mathf.Min(part.minimumTyreLength,u1[k].x);if(u1[k].x<0)part.shortApproachVertices++;}
       }
       row.parts.Add(part);
       if(mat!=null&&seenMats.Add(AssetDatabase.GetAssetPath(mat))){var mr=new MatRow{path=AssetDatabase.GetAssetPath(mat),shader=mat.shader.name,keywords=string.Join(",",mat.shaderKeywords)};foreach(string prop in new[]{"_WheelPolish","_GutterDirt","_DripBand","_CrackStrength","_DecalAlpha","_PaintWear","_Tint","_Tile","_Grime"})if(mat.HasProperty(prop))mr.fields.Add(prop+"="+(prop=="_PaintWear"||prop=="_Tint"||prop=="_Tile"||prop=="_Grime"?mat.GetVector(prop).ToString("R"):mat.GetFloat(prop).ToString("R",System.Globalization.CultureInfo.InvariantCulture)));foreach(string prop in new[]{"_BaseMap","_VarMap","_MacroMap","_CrackMap","_CrackNormal"})if(mat.HasProperty(prop))mr.fields.Add(prop+"="+AssetDatabase.GetAssetPath(mat.GetTexture(prop)));packet.materials.Add(mr);}
      }
      writer.Flush();row.indices=Digest(stream);
     }
     packet.meshes.Add(row);
    }
   }
   if(packet.meshes.Count==0)throw new Exception("Noactualroad/markingmeshesmatched; inspectactualassetpaths");Directory.CreateDirectory(Path.GetDirectoryName(output));File.WriteAllText(output,JsonUtility.ToJson(packet,true));Debug.Log("SURFACE_NATIVE_AUDIT: OK meshes="+packet.meshes.Count+" materials="+packet.materials.Count);EditorApplication.Exit(0);
  }
 }
}
