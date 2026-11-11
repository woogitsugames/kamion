using System;
using System.IO;
using Game.Editor.Build;
using UnityEditor;
using UnityEngine;
namespace Game.Editor.VisualQA {
 public static class R4PlateReplay {
  [Serializable] public class Record {public string tier,shader,renderType,texture;public bool motionMixed,motionUpper,keyword,instancing;public int queue;public float version,smoothness;public Vector2 scale,offset;}
  public static void RunBatch(){
   string root=Path.Combine(EditorTools.RepoRoot,"artifacts/car-paint-r1/r4-plate-pass-replay");
   foreach(string tier in new[]{"Low","High"}){
    string folder=Path.Combine(root,tier+"-overcast");if(Directory.Exists(folder))throw new InvalidOperationException("Refuse overwrite "+folder);
    Environment.SetEnvironmentVariable("KAMION_G_POSE_OUTPUT",Path.Combine(folder,"poses"));
    int count=VisualQaRunner.Render(tier=="High"?"WorldC_High":"WorldC",2340,1080,tier,folder,"overcast","g_dirt_level_0");
    if(count!=1)throw new InvalidOperationException("Replay count "+count);
    var p=AssetDatabase.LoadAssetAtPath<Material>("Assets/_Generated/World/bialystok-industrial-c/Materials/M_car_plate.mat");
    var r=new Record{tier=tier,shader=p.shader.name,renderType=p.GetTag("RenderType",false,"missing"),texture=AssetDatabase.GetAssetPath(p.GetTexture("_BaseMap")),
      motionMixed=p.GetShaderPassEnabled("MotionVectors"),motionUpper=p.GetShaderPassEnabled("MOTIONVECTORS"),keyword=p.IsKeywordEnabled("_PLATE_LOCAL_CORNERS"),instancing=p.enableInstancing,
      queue=p.renderQueue,version=p.GetFloat("_PlatePayloadVersion"),smoothness=p.GetFloat("_Smoothness"),scale=p.GetTextureScale("_BaseMap"),offset=p.GetTextureOffset("_BaseMap")};
    File.WriteAllText(Path.Combine(folder,"actual-loaded-plate.json"),JsonUtility.ToJson(r,true));
    if(r.motionMixed||!r.keyword||r.version!=1||r.renderType!="Opaque"||r.queue!=2000)throw new InvalidOperationException("Loaded/replayed plate state invalid "+JsonUtility.ToJson(r));
   }
   Debug.Log("R4_PLATE_REPLAY_RESULT: OK frames=2");
  }
 }
}
