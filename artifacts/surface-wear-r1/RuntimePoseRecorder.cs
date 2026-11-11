using System;
using System.Collections.Generic;
using System.IO;
using Game.Rendering;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

namespace SurfaceWearQA
{
    // QA artifact only. Install in ignored Editor folder while Unity is stopped, after explicit ROOT release.
    [InitializeOnLoad]
    public static class RuntimePoseRecorder
    {
        [Serializable] public class Pose { public string name,parent;public Vector3 position,localPosition,scale;public Quaternion rotation,localRotation; }
        [Serializable] public class Row { public string id,scene;public Vector3 cameraPosition;public Quaternion cameraRotation;public float fov,near,far;public int width,height;public float[] view,projection;public Pose truck,trailer; }
        [Serializable] public class Packet { public string note="Actual beginCameraRendering world pose and matrices. Readonly QA, no transform/material mutation. Baseline serialized comparison is a separate proof, not retroactive runtime evidence.";public List<Row> cameras=new List<Row>(); }
        static readonly Dictionary<string,Row> rows=new Dictionary<string,Row>();
        static string output;
        static RuntimePoseRecorder()
        {
            var args=Environment.GetCommandLineArgs();int i=Array.IndexOf(args,"-qaOutput");
            if(i<0||i+1>=args.Length||!args[i+1].Replace('\\','/').Contains("artifacts/surface-wear-r1/"))return;
            output=Path.Combine(args[i+1],"runtime-pose.json");RenderPipelineManager.beginCameraRendering+=Capture;
        }
        static float[] Matrix(Matrix4x4 m){var a=new float[16];for(int r=0;r<4;r++)for(int c=0;c<4;c++)a[r*4+c]=m[r,c];return a;}
        static Pose Read(Transform t){return t==null?null:new Pose{name=t.name,parent=t.parent==null?"":t.parent.name,position=t.position,localPosition=t.localPosition,rotation=t.rotation,localRotation=t.localRotation,scale=t.lossyScale};}
        static void Capture(ScriptableRenderContext context,Camera camera)
        {
            var cc=camera.GetComponent<ControlCamera>();if(cc==null)return;
            var truck=UnityEngine.Object.FindAnyObjectByType<VehicleBody>();var trailer=UnityEngine.Object.FindAnyObjectByType<TrailerBody>();
            rows[cc.id]=new Row{id=cc.id,scene=SceneManager.GetActiveScene().name,cameraPosition=camera.transform.position,cameraRotation=camera.transform.rotation,
                fov=camera.fieldOfView,near=camera.nearClipPlane,far=camera.farClipPlane,width=camera.targetTexture==null?camera.pixelWidth:camera.targetTexture.width,
                height=camera.targetTexture==null?camera.pixelHeight:camera.targetTexture.height,view=Matrix(camera.worldToCameraMatrix),projection=Matrix(camera.projectionMatrix),
                truck=Read(truck==null?null:truck.transform),trailer=Read(trailer==null?null:trailer.transform)};
            var packet=new Packet();foreach(string key in new SortedSet<string>(rows.Keys,StringComparer.Ordinal))packet.cameras.Add(rows[key]);
            Directory.CreateDirectory(Path.GetDirectoryName(output));File.WriteAllText(output,JsonUtility.ToJson(packet,true));
        }
    }
}
