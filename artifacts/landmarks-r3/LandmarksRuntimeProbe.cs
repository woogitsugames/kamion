using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Game.World;

namespace Game.Editor.VisualQA
{
    // Temporary read-only diagnostic, copied into the Editor assembly only while
    // this method runs. It does not save scenes, meshes, profiles or settings.
    public static class LandmarksRuntimeProbe
    {
        [Serializable] public class Row
        {
            public string prototype;
            public int instanceIndex;
            public float[] worldMatrix;
            public Vector3 up;
            public Vector3 position;
            public float axisTiltDeg;
            public int[] lodSubmeshes;
            public float[] lodEnds;
        }
        [Serializable] public class Result
        {
            public string scope = "Runtime WorldInstances.SyncOrigin matrix readback, no geometry edit or image-based straightening";
            public string scene;
            public Row[] rows;
            public bool allVertical;
        }
        static string Arg(string name)
        {
            var args = Environment.GetCommandLineArgs();
            for(int i=0;i+1<args.Length;i++) if(args[i]==name) return args[i+1];
            throw new Exception("Missing argument "+name);
        }
        public static void Run()
        {
            string scene=Arg("-landmarksScene"), output=Arg("-landmarksOutput");
            EditorSceneManager.OpenScene(scene,OpenSceneMode.Single);
            var rows=new List<Row>();
            foreach(var world in UnityEngine.Object.FindObjectsByType<WorldInstances>(FindObjectsInactive.Include,FindObjectsSortMode.None))
            {
                if(world.set==null) continue;
                typeof(WorldInstances).GetMethod("SyncOrigin",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(world,null);
                var matrices=(Matrix4x4[])typeof(WorldInstances).GetField("m_World",BindingFlags.NonPublic|BindingFlags.Instance).GetValue(world);
                foreach(var run in world.set.runs)
                {
                    var proto=world.set.prototypes[run.prototype];
                    if(!proto.name.Contains("chimney")) continue;
                    for(int i=run.start;i<run.start+run.count;i++)
                    {
                        var m=matrices[i];
                        var up=m.MultiplyVector(Vector3.up).normalized;
                        var values=new float[16];
                        for(int k=0;k<16;k++) values[k]=m[k];
                        var subs=new int[proto.lods.Length];
                        for(int k=0;k<subs.Length;k++) subs[k]=proto.lods[k].subMeshCount;
                        rows.Add(new Row {prototype=proto.name,instanceIndex=i,worldMatrix=values,up=up,
                            position=m.MultiplyPoint3x4(Vector3.zero),axisTiltDeg=Vector3.Angle(up,Vector3.up),
                            lodSubmeshes=subs,lodEnds=proto.lodEndM});
                    }
                }
            }
            bool vertical=rows.Count==2;
            foreach(var row in rows) vertical &= row.axisTiltDeg<0.001f;
            Directory.CreateDirectory(Path.GetDirectoryName(output));
            File.WriteAllText(output,JsonUtility.ToJson(new Result{scene=scene,rows=rows.ToArray(),allVertical=vertical},true));
            if(!vertical) throw new Exception("Expected exactly two vertical EC instance matrices");
            Debug.Log("LANDMARKS_RUNTIME_PROBE: OK, two vertical chimney matrices");
        }
    }
}
