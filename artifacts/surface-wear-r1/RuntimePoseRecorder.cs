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
        [Serializable] public class SignalState { public string material,path,shader,keywords,binding;public Color emission;public int rendererUses; }
        [Serializable] public class Row { public string id,scene;public Vector3 cameraPosition;public Quaternion cameraRotation;public float fov,near,far;public int width,height;public float[] view,projection;public Pose truck,trailer;public List<SignalState> signals; }
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
        static List<SignalState> Signals()
        {
            var found=new SortedDictionary<string,SignalState>(StringComparer.Ordinal);
            void Add(Material material,string binding)
            {
                if(material==null||(material.name!="M_signal_green_on"&&material.name!="M_signal_red_on"))return;
                if(!found.TryGetValue(material.name,out var state))
                {
                    state=new SignalState{material=material.name,path=AssetDatabase.GetAssetPath(material),shader=material.shader.name,
                        keywords=string.Join(",",material.shaderKeywords),emission=material.HasProperty("_EmissionColor")?material.GetColor("_EmissionColor"):Color.clear,binding=binding};
                    found.Add(material.name,state);
                }
                state.rendererUses++;
            }
            foreach(var renderer in UnityEngine.Object.FindObjectsByType<MeshRenderer>(FindObjectsInactive.Include,FindObjectsSortMode.None))
                foreach(var material in renderer.sharedMaterials)Add(material,"MeshRenderer.sharedMaterials");
            foreach(var instances in UnityEngine.Object.FindObjectsByType<Game.World.WorldInstances>(FindObjectsInactive.Include,FindObjectsSortMode.None))
            {
                var field=typeof(Game.World.WorldInstances).GetField("m_Mats",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);
                var materials=field==null?null:field.GetValue(instances)as Material[];
                if(materials!=null)foreach(var material in materials)Add(material,"WorldInstances.m_Mats (actual batch materials)");
                else if(instances.set!=null&&instances.set.materials!=null)foreach(var material in instances.set.materials)Add(material,"WorldInstances.set.materials (before batch allocation)");
            }
            return new List<SignalState>(found.Values);
        }
        static void Capture(ScriptableRenderContext context,Camera camera)
        {
            var cc=camera.GetComponent<ControlCamera>();if(cc==null)return;
            var truck=UnityEngine.Object.FindAnyObjectByType<VehicleBody>();var trailer=UnityEngine.Object.FindAnyObjectByType<TrailerBody>();
            rows[cc.id]=new Row{id=cc.id,scene=SceneManager.GetActiveScene().name,cameraPosition=camera.transform.position,cameraRotation=camera.transform.rotation,
                fov=camera.fieldOfView,near=camera.nearClipPlane,far=camera.farClipPlane,width=camera.targetTexture==null?camera.pixelWidth:camera.targetTexture.width,
                height=camera.targetTexture==null?camera.pixelHeight:camera.targetTexture.height,view=Matrix(camera.worldToCameraMatrix),projection=Matrix(camera.projectionMatrix),
                truck=Read(truck==null?null:truck.transform),trailer=Read(trailer==null?null:trailer.transform),signals=Signals()};
            var packet=new Packet();foreach(string key in new SortedSet<string>(rows.Keys,StringComparer.Ordinal))packet.cameras.Add(rows[key]);
            Directory.CreateDirectory(Path.GetDirectoryName(output));File.WriteAllText(output,JsonUtility.ToJson(packet,true));
        }
    }
}
