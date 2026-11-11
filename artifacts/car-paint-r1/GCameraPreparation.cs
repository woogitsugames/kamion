using System;
using System.IO;
using System.Linq;
using System.Reflection;
using Game.Editor.Build;
using Game.World;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Game.Editor.VisualQA
{
    // Ignored diagnostic adapter only. No source scene or vehicle placement is changed.
    public static class GCameraPreparation
    {
        [Serializable] public class Instance { public string p,src; public float e,n,z,yaw; }
        [Serializable] public class Entry { public string id,type="persp",kind="photo_match",note; public float fov_deg=40; public float[] pos,look_at; }
        [Serializable] public class Input { public Instance source_instance; public Entry[] cameras; }
        [Serializable] public class Output { public string schema="truck-sim-pl/gate3-cameras/1",region="bialystok-industrial-c",note; public Instance source_instance; public Entry[] cameras; public int testedDirections; public float[] rayLengthsM; }
        struct Proxy { public Matrix4x4 inverse; public Bounds bounds; }

        static Proxy[] VehicleProxies(Vector3 target)
        {
            var result=new System.Collections.Generic.List<Proxy>();
            foreach(var renderer in UnityEngine.Object.FindObjectsByType<WorldInstances>(FindObjectsInactive.Include,FindObjectsSortMode.None))
            {
                var set=renderer.set;
                if(set==null)continue;
                foreach(var run in set.runs)
                {
                    var prototype=set.prototypes[run.prototype];
                    if(!prototype.name.StartsWith("car_")&&!prototype.name.StartsWith("van_"))continue;
                    for(int j=0;j<run.count;j++)
                    {
                        var matrix=set.LocalMatrix(run.start+j);
                        Vector3 shift=renderer.transform.position;
                        matrix.m03+=shift.x;matrix.m13+=shift.y;matrix.m23+=shift.z;
                        if(Vector2.Distance(new Vector2(matrix.m03,matrix.m23),new Vector2(target.x,target.z))<.1f)continue;
                        var bounds=prototype.lods[0].bounds;bounds.Expand(.1f);
                        result.Add(new Proxy{inverse=matrix.inverse,bounds=bounds});
                    }
                }
            }
            return result.ToArray();
        }

        static bool CrossesVehicle(Proxy[] proxies,Vector3 from,Vector3 to)
        {
            foreach(var proxy in proxies)
            {
                var origin=proxy.inverse.MultiplyPoint3x4(from);
                var delta=proxy.inverse.MultiplyPoint3x4(to)-origin;
                if(proxy.bounds.IntersectRay(new Ray(origin,delta.normalized),out float hit)&&hit<=delta.magnitude+.2f)return true;
            }
            return false;
        }

        static float[] Local(WorldRegionRoot root,Vector3 world) => new[] {
            world.x+root.originShift.x,world.z+root.originShift.z,(float)root.anchorZ+world.y+root.originShift.y };

        public static void RunBatch()
        {
            string folder=Path.Combine(EditorTools.RepoRoot,"artifacts/car-paint-r1");
            var input=JsonUtility.FromJson<Input>(File.ReadAllText(Path.Combine(folder,"wheel-cameras.json")));
            var old=JsonUtility.FromJson<Input>(File.ReadAllText(Path.Combine(folder,"qa-cameras.json"))).cameras.First(c=>c.id=="r10b_black_05");
            // Reuse the already canonical prefabs; the production installer performs its normal generated-scene wiring.
            var installer=Type.GetType("Game.World.Import.WorldTruckInstaller, Game.World.Import.Editor",true);
            var install=installer.GetMethod("InstallInScene",BindingFlags.Public|BindingFlags.Static);
            foreach(string name in new[]{"WorldC","WorldC_High"})
                install.Invoke(null,new object[]{"Assets/_Generated/World/bialystok-industrial-c/"+name+".unity"});
            EditorSceneManager.OpenScene("Assets/_Generated/World/bialystok-industrial-c/WorldC_High.unity",OpenSceneMode.Single);
            foreach(var cooker in UnityEngine.Object.FindObjectsByType<WorldCollisionCooker>(FindObjectsInactive.Include,FindObjectsSortMode.None)) cooker.Cook();
            Physics.SyncTransforms();
            var root=UnityEngine.Object.FindAnyObjectByType<WorldRegionRoot>();
            if(root==null)throw new InvalidOperationException("Region root missing");
            var item=input.source_instance;
            Vector3 target=root.LocalToUnity(item.e,item.n,item.z+.8f);
            var vehicleProxies=VehicleProxies(target);
            Vector3 prior=root.LocalToUnity(old.pos[0],old.pos[1],old.pos[2]);
            float initial=Mathf.Atan2(prior.z-target.z,prior.x-target.x),chosen=0;
            bool found=false;int tested=0;
            float[] radii={5,20,45};
            for(int k=0;k<720;k++)
            {
                float delta=k==0?0:((k+1)/2)*.5f*(k%2==1?1:-1)*Mathf.Deg2Rad;
                float angle=initial+delta;bool clear=true;tested++;
                foreach(float radius in radii)
                {
                    Vector3 eye=target+new Vector3(Mathf.Cos(angle)*radius,1.5f,Mathf.Sin(angle)*radius);
                    Vector3 ray=eye-target;
                    // Starts inside the target vehicle: its own collider is ignored by PhysX. Reject all intervening colliders.
                    if(Physics.Raycast(target,ray.normalized,out _,ray.magnitude+.2f,~0,QueryTriggerInteraction.Ignore)
                        ||CrossesVehicle(vehicleProxies,target,eye)
                        ||Physics.CheckSphere(eye,.2f,~0,QueryTriggerInteraction.Ignore)){clear=false;break;}
                }
                if(clear){chosen=angle;found=true;break;}
            }
            if(!found)throw new InvalidOperationException("No common unobstructed 5/20/45m direction; do not fabricate LOD proof");
            var entries=new System.Collections.Generic.List<Entry>{old,input.cameras[0]};
            foreach(float radius in radii)
            {
                Vector3 eye=target+new Vector3(Mathf.Cos(chosen)*radius,1.5f,Mathf.Sin(chosen)*radius);
                entries.Add(new Entry{id="g_current_black_lod_"+radius.ToString("00",System.Globalization.CultureInfo.InvariantCulture),
                    pos=Local(root,eye),look_at=Local(root,target),note="WORKING_VALUE QA camera at "+radius+"m; actual source "+item.src+". Cooked scene full rays plus actual instanced vehicle OBBs tested; world placements unchanged."});
            }
            var output=new Output{source_instance=item,cameras=entries.ToArray(),testedDirections=tested,rayLengthsM=radii,
                note="Actual own generated scene full cooked-collision rays plus instanced vehicle OBBs (including omitted car colliders), all5/20/45m rays share a clear direction. QA cameras only; not surveyed positions. Target source and wheel camera preserved. Visual occlusion must still be inspected."};
            File.WriteAllText(Path.Combine(folder,"pearl-cameras.json"),JsonUtility.ToJson(output,true));
            Debug.Log("G_CAMERA_PREP_RESULT: OK tested="+tested);
        }
    }
}
