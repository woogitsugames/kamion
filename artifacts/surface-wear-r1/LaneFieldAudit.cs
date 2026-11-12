using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEditor;
using Game.World.Import;
namespace SurfaceWearQA {
public static class LaneFieldAudit {
 [Serializable] public class Row {public string file,material;public bool changed,unsupported;public int vertices,triangles;public float area;public Vector3 centerENU,boundsMinENU,boundsMaxENU;}
 [Serializable] public class Packet {public string note="Actualproductionhelper acceptance/sourcecomponentbounds; QA only, no sourceoutputs modified.";public List<Row> components=new List<Row>();}
 static int Find(int[] p,int i){while(p[i]!=i){p[i]=p[p[i]];i=p[i];}return i;}
 public static void Run(){string root=Path.GetFullPath(Path.Combine(Application.dataPath,"../.."));var packet=new Packet();
 foreach(string file in Directory.GetFiles(Path.Combine(root,"Data/raw/derived/bialystok-industrial-c/world"),"chunk_*.glb")) {
 var g=GlbReader.Load(file);var node=g.Find("markings");if(node==null)continue;var field=new RoadPaintLaneField(g.Find("road"));var result=field.Transfer(node,out var stats);
 for(int pi=0;pi<node.Primitives.Count;pi++) {var a=node.Primitives[pi];var b=result.Primitives[pi];if(a.Material!="marking_white"||a.Uv1==null)continue;
 var parent=new int[a.Positions.Length];for(int i=0;i<parent.Length;i++)parent[i]=i;var same=new Dictionary<(Vector3,float),int>();
 for(int i=0;i<parent.Length;i++){var key=(a.Positions[i],a.Uv1[i].y);if(same.TryGetValue(key,out int old))parent[Find(parent,i)]=Find(parent,old);else same[key]=i;}
 for(int j=0;j<a.Indices.Length;j+=3){int x=Find(parent,a.Indices[j]);parent[Find(parent,a.Indices[j+1])]=x;parent[Find(parent,a.Indices[j+2])]=x;}
 var groups=new Dictionary<int,List<int>>();for(int j=0;j<a.Indices.Length;j+=3){int id=Find(parent,a.Indices[j]);if(!groups.TryGetValue(id,out var list))groups[id]=list=new List<int>();list.Add(j);}
 foreach(var ts in groups.Values) {var verts=new HashSet<int>();bool constant=true,changed=false,unsupported=false;float area=0;Vector3 sum=Vector3.zero,min=Vector3.positiveInfinity,max=Vector3.negativeInfinity;
 foreach(int j in ts){var va=a.Positions[a.Indices[j]];var vb=a.Positions[a.Indices[j+1]];var vc=a.Positions[a.Indices[j+2]];float ar=Vector3.Cross(vb-va,vc-va).magnitude*.5f;area+=ar;sum+=(va+vb+vc)/3f*ar;for(int k=0;k<3;k++)verts.Add(a.Indices[j+k]);}
 foreach(int i in verts){constant&=Mathf.Abs(a.Uv1[i].x-.5f)<1e-5f;changed|=Mathf.Abs(a.Uv1[i].x-b.Uv1[i].x)>1e-6f;unsupported|=!field.TrySample(a.Positions[i],out _);min=Vector3.Min(min,a.Positions[i]);max=Vector3.Max(max,a.Positions[i]);}
 if(!constant||area<.5f||(!changed&&!unsupported))continue;Vector3 center=sum/area;Vector3 ENU(Vector3 v)=>new Vector3(v.x,v.z,v.y);
 packet.components.Add(new Row{file=Path.GetFileName(file),material=a.Material,changed=changed,unsupported=unsupported,vertices=verts.Count,triangles=ts.Count,area=area,centerENU=ENU(center),boundsMinENU=ENU(min),boundsMaxENU=ENU(max)});
 }
 }
 }
 string output=Path.Combine(root,"artifacts/surface-wear-r1/actual-lane-components.json");File.WriteAllText(output,JsonUtility.ToJson(packet,true));Debug.Log("LANE_COMPONENT_AUDIT: OK count="+packet.components.Count);EditorApplication.Exit(0);
 }
}
}
