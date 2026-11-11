using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;
namespace SurfaceWearQA {
 public static class PaintWearAblation {
 static readonly Dictionary<Renderer,Material[]> originals=new Dictionary<Renderer,Material[]>();
 static readonly Dictionary<Material,Material> clones=new Dictionary<Material,Material>();
 static string Arg(string key,string fallback){var a=Environment.GetCommandLineArgs();int i=Array.IndexOf(a,key);return i>=0&&i+1<a.Length?a[i+1]:fallback;}
 static void Apply(Scene scene,OpenSceneMode mode){foreach(var r in UnityEngine.Object.FindObjectsByType<MeshRenderer>(FindObjectsInactive.Include,FindObjectsSortMode.None)) {var old=r.sharedMaterials;var next=(Material[])old.Clone();bool changed=false;for(int i=0;i<next.Length;i++){var m=next[i];if(m==null||!m.IsKeywordEnabled("_DECAL_PAINT"))continue;if(!clones.TryGetValue(m,out var copy)){copy=new Material(m){name=m.name+"_QA_PAINTCONTROL"};string shaderName=Arg("-qaPaintShader","");if(shaderName!=""){var shader=Shader.Find(shaderName);if(shader==null)throw new Exception("Missing diagnosticshader "+shaderName);copy.shader=shader;copy.shaderKeywords=m.shaderKeywords;}var v=m.GetVector("_PaintWear");copy.SetVector("_PaintWear",new Vector4(float.Parse(Arg("-qaPaintWheel","0"),System.Globalization.CultureInfo.InvariantCulture),Arg("-qaPaintWheel","0")=="0"?0:v.y,v.z,v.w));clones[m]=copy;Debug.Log("PAINT_ABLATION_ORIGINAL "+m.name+"="+v.ToString("R"));}next[i]=copy;changed=true;}if(changed){originals[r]=old;r.sharedMaterials=next;}}}
 public static void Run(){int exit=1;EditorSceneManager.sceneOpened+=Apply;try {int rendered=Game.Editor.VisualQA.VisualQaRunner.Render(Arg("-qaScene","WorldC_High"),2340,1080,Arg("-qaTier","High"),Arg("-qaOutput",""),Arg("-qaLighting","overcast"),Arg("-qaCameras","d_field_p8_turn"));if(rendered<1||clones.Count==0)throw new Exception("Missing actual ablation frame/material");foreach(var m in clones.Values){var v=m.GetVector("_PaintWear");if(v.x!=float.Parse(Arg("-qaPaintWheel","0"),System.Globalization.CultureInfo.InvariantCulture))throw new Exception("Wear override was reset");Debug.Log("PAINT_ABLATION_RENDERED "+m.name+"="+v.ToString("R"));}exit=0;}catch(Exception e){Debug.LogException(e);}finally{EditorSceneManager.sceneOpened-=Apply;foreach(var p in originals)if(p.Key!=null)p.Key.sharedMaterials=p.Value;foreach(var m in clones.Values)UnityEngine.Object.DestroyImmediate(m);Debug.Log("PAINT_ABLATION_RESTORED renderers="+originals.Count+" clonedMaterials="+clones.Count);originals.Clear();clones.Clear();}EditorApplication.Exit(exit);}
 }
}
