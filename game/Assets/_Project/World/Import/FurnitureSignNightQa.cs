// Owned, reversible editor fixture. It saves ONLY under Assets/_Generated/FurnitureSignQa.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Game.Editor.Build;
using Game.Editor.Setup;
using Game.Editor.VisualQA;
using Game.Rendering;
using Game.Vehicle.Runtime;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Object = UnityEngine.Object;

namespace Game.World.Import
{
    public static class FurnitureSignNightQa
    {
        const string Dir = "Assets/_Generated/FurnitureSignQa";
        const string Prototype = "plate_B-33_70";
        const string Keyword = "_FURNITURE_RETRO";
        static readonly string[] Modes = { "retro-disabled", "low", "high", "source-disabled" };
        static readonly float[] Distances = { 25, 50, 100 };

        [Serializable] sealed class Sample
        {
            public string tier, mode, camera, ground;
            public float requestedHorizontalM, cameraFov, exposure, trueSunElevation;
            public Vector3 sign, normal, eye, vehicle;
            public Vector4 state, lowLeft, lowRight, highLeft, highRight;
            public bool actualLightEnabled, actualLightActive, actualLowOn, actualHighOn;
            public int actualLightId;
            public float diagnosticManualEv100=5;
        }
        [Serializable] sealed class Evidence
        {
            public string sourcePrototype = Prototype;
            public string caveat = "Controlled pose, not photo calibration or driving physics. Sky model limit -8 degrees; no deeper-night claim. Analytic return has no light-path occlusion.";
            public float lateralOffsetWorkingM = 3.5f;
            public Sample[] samples;
        }
        [Serializable] sealed class MaterialRow
        {
            public string material,shader,texture,asset;
            public bool retro;
            public float coefficient;
        }
        [Serializable] sealed class Coverage { public MaterialRow[] fronts; }
        sealed class Target
        {
            public Vector3 point, normal;
            public readonly List<(float distance, Vector3 position, Quaternion rotation, string ground)> poses = new();
        }

        public static void Run()
        {
            int exit = 1;
            try
            {
                string tier = EditorTools.Arg("-furnitureQaTier", "Low");
                if (tier != "Low" && tier != "High") throw new ArgumentException("Use Low or High");
                string output = EditorTools.Arg("-furnitureQaOutput");
                if (string.IsNullOrEmpty(output)) throw new ArgumentException("Output directory required");
                Directory.CreateDirectory(output);
                Directory.CreateDirectory(Path.Combine(EditorTools.ProjectRoot, Dir));
                AssetDatabase.Refresh();
                string source = ScenePath(tier == "High" ? "WorldC_High" : "WorldC");
                EditorSceneManager.OpenScene(source, OpenSceneMode.Single);
                var assigned=Object.FindObjectsByType<WorldInstances>(FindObjectsSortMode.None)
                    .Where(w=>w.set!=null).SelectMany(w=>w.set.materials).Where(m=>m!=null)
                    .Where(m=>m.name.StartsWith("M_sign_",StringComparison.Ordinal) && !m.name.StartsWith("M_sign_facade_",StringComparison.Ordinal))
                    .GroupBy(AssetDatabase.GetAssetPath).Select(g=>g.First()).OrderBy(m=>m.name)
                    .Select(m=>new MaterialRow {material=m.name,asset=AssetDatabase.GetAssetPath(m),shader=m.shader.name,
                        texture=AssetDatabase.GetAssetPath(m.GetTexture("_BaseMap")),retro=m.IsKeywordEnabled(Keyword),
                        coefficient=m.HasProperty("_EmissionColor")?m.GetColor("_EmissionColor").r:0}).ToArray();
                File.WriteAllText(Path.Combine(output,"assigned-front-materials.json"),JsonUtility.ToJson(new Coverage{fronts=assigned},true));
                Cook();
                var lights = Object.FindAnyObjectByType<TruckLights>() ?? throw new InvalidOperationException("Real TruckLights missing");
                var body = lights.body ?? throw new InvalidOperationException("Real vehicle body missing");
                foreach (var rig in Object.FindObjectsByType<TruckVisualRig>(FindObjectsSortMode.None)) rig.Apply();
                var left = Socket(body.transform,"LIGHT_LowBeam_L");
                var right = Socket(body.transform,"LIGHT_LowBeam_R");
                Socket(body.transform,"LIGHT_HighBeam_L"); Socket(body.transform,"LIGHT_HighBeam_R");
                Vector3 headLocal = body.transform.InverseTransformPoint((left.position + right.position) * .5f);
                var target = SelectTarget(body,headLocal);
                string targetFile = Path.Combine(output,"target.json");
                File.WriteAllText(targetFile,JsonUtility.ToJson(new Sample { tier=tier, sign=target.point,normal=target.normal },true));
                foreach (var pose in target.poses)
                    foreach (string mode in Modes)
                        Capture(source,tier,mode,pose.distance,pose.position,pose.rotation,pose.ground,target,output);
                exit = 0;
                Debug.Log("FURNITURE_NIGHT_QA: OK; actual source state logged, no synthetic camera light");
            }
            catch (Exception e) { Debug.LogException(e); Debug.Log("FURNITURE_NIGHT_QA: FAILED"); }
            finally
            {
                EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                if (Application.isBatchMode) EditorApplication.Exit(exit);
            }
        }

        static string ScenePath(string name) => AssetDatabase.FindAssets("t:Scene " + name)
            .Select(AssetDatabase.GUIDToAssetPath).FirstOrDefault(p=>Path.GetFileNameWithoutExtension(p)==name)
            ?? throw new FileNotFoundException(name);

        static Transform Socket(Transform root,string name) => root.GetComponentsInChildren<Transform>(true)
            .FirstOrDefault(t=>t.name==name) ?? throw new InvalidOperationException("Real rig socket missing: " + name);

        static void Cook()
        {
            foreach (var cooker in Object.FindObjectsByType<WorldCollisionCooker>(FindObjectsInactive.Include,FindObjectsSortMode.None)) cooker.Cook();
            Physics.SyncTransforms();
        }

        static Target SelectTarget(VehicleBody body,Vector3 headLocal)
        {
            var library = GlbReader.Load(Path.Combine(EditorTools.RepoRoot,"art-source/world/props/street_props.glb"));
            var protoNode = library.Find(Prototype) ?? throw new InvalidOperationException("Source sign prototype missing");
            var front = protoNode.Primitives.First(p=>p.Material=="sign_B-33_70");
            if (front.Normals == null || front.Normals.Length==0) throw new InvalidOperationException("Front normals missing");
            var bounds = new Bounds(front.Positions[0],Vector3.zero);
            foreach (var p in front.Positions) bounds.Encapsulate(p);
            var candidates = new List<Target>();
            foreach (var draw in Object.FindObjectsByType<WorldInstances>(FindObjectsSortMode.None))
            {
                var set = draw.set;
                if (set==null) continue;
                foreach (var run in set.runs)
                {
                    if (set.prototypes[run.prototype].name!=Prototype) continue;
                    var proto = set.prototypes[run.prototype];
                    int frontIndex = protoNode.Primitives.FindIndex(p=>p.Material=="sign_B-33_70");
                    var material = set.materials[proto.materialStart[0]+frontIndex];
                    if (material.shader.name!="Kamion/Furniture Sign" || !material.IsKeywordEnabled(Keyword))
                        throw new InvalidOperationException("Import candidate before the night fixture: selected front is not opted in");
                    for (int i=run.start;i<run.start+run.count;i++)
                    {
                        var matrix = Matrix4x4.Translate(draw.transform.position) * set.LocalMatrix(i);
                        var target = new Target { point=matrix.MultiplyPoint3x4(bounds.center),normal=matrix.MultiplyVector(front.Normals[0]).normalized };
                        if (Mathf.Abs(target.normal.y)>.05f) continue;
                        target.normal=Vector3.ProjectOnPlane(target.normal,Vector3.up).normalized;
                        bool good=true;
                        foreach (float distance in Distances)
                        {
                            var rotation=Quaternion.LookRotation(-target.normal,Vector3.up);
                            var truckRight=rotation*Vector3.right;
                            var desiredHead=target.point+target.normal*distance-truckRight*3.5f; // explicit working lateral placement
                            var position=desiredHead-rotation*headLocal;
                            var hits=Physics.RaycastAll(new Vector3(position.x,target.point.y+2,position.z),Vector3.down,40,~0,QueryTriggerInteraction.Ignore)
                                .Where(h=>h.collider.GetComponent<GroundSurface>() is GroundSurface g && g.kind==SurfaceKind.DryAsphalt && h.normal.y>.8f)
                                .OrderBy(h=>h.distance).ToArray();
                            if (hits.Length==0) {good=false;break;}
                            position.y=hits[0].point.y;
                            var actualHead=position+rotation*headLocal;
                            var direction=target.point-actualHead;
                            bool blocked=Physics.RaycastAll(actualHead,direction.normalized,direction.magnitude-.2f,~0,QueryTriggerInteraction.Ignore)
                                .Any(h=>h.distance>.2f && h.collider.GetComponentInParent<VehicleBody>()==null && h.collider.GetComponentInParent<TrailerBody>()==null);
                            if (blocked) {good=false;break;}
                            target.poses.Add((distance,position,rotation,hits[0].collider.name));
                        }
                        if (good) candidates.Add(target);
                    }
                }
            }
            return candidates.OrderBy(t=>(t.point-body.transform.position).sqrMagnitude).FirstOrDefault()
                ?? throw new InvalidOperationException("No sign has asphalt and clear head-to-front line for all requested poses; inspect rather than inventing a source");
        }

        static T SaveOwned<T>(T value,string path) where T:Object
        {
            if (!path.StartsWith(Dir+"/",StringComparison.Ordinal)) throw new InvalidOperationException("Fixture asset path escaped owner directory");
            var old=AssetDatabase.LoadAssetAtPath<T>(path);
            if (old==null) {AssetDatabase.CreateAsset(value,path);return value;}
            EditorUtility.CopySerialized(value,old); Object.DestroyImmediate(value); EditorUtility.SetDirty(old);return old;
        }

        static void Capture(string source,string tier,string mode,float distance,Vector3 position,Quaternion rotation,string ground,Target target,string output)
        {
            var scene=EditorSceneManager.OpenScene(source,OpenSceneMode.Single);
            var lights=Object.FindAnyObjectByType<TruckLights>() ?? throw new InvalidOperationException("Rig missing");
            var body=lights.body ?? throw new InvalidOperationException("Body missing");
            var oldMatrix=body.transform.localToWorldMatrix;
            var delta=Matrix4x4.TRS(position,rotation,Vector3.one)*oldMatrix.inverse;
            foreach (var trailer in Object.FindObjectsByType<TrailerBody>(FindObjectsSortMode.None))
                trailer.transform.SetPositionAndRotation(delta.MultiplyPoint3x4(trailer.transform.position),delta.rotation*trailer.transform.rotation);
            body.transform.SetPositionAndRotation(position,rotation);
            lights.forceLowBeam=true; lights.highBeam=mode=="high"; lights.enabled=mode!="source-disabled";
            foreach (var rig in Object.FindObjectsByType<TruckVisualRig>(FindObjectsSortMode.None)) rig.Apply();
            var eyeTransform=body.transform.GetComponentsInChildren<Transform>(true).FirstOrDefault(t=>t.name=="EYE_POINT");
            var eye=eyeTransform!=null ? eyeTransform.position : body.transform.TransformPoint(DrivingLabSceneBuilder.ReadAndCheckDims().EyePointVehicle);
            string label=$"{tier}_{mode.Replace('-','_')}_{distance:0}";
            var env=Object.FindAnyObjectByType<EnvironmentLighting>() ?? throw new InvalidOperationException("Lighting missing");
            var dusk=AssetDatabase.LoadAssetAtPath<LightingPreset>("Assets/_Project/Rendering/Settings/Lighting/LP_Dusk.asset");
            var preset=Object.Instantiate(dusk); preset.name="LP_FurnitureNight";
            // Existing model stops at -8°. Do not silently claim -12° or astronomical night.
            preset.sunElevationDeg=SkyModel.MinTwilightElevationDeg;
            // A controlled manual camera exposure, not a change to the game's light presets.
            preset.autoExposure=false; preset.ev100=5; preset.exposureCompensation=0;
            preset=SaveOwned(preset,$"{Dir}/Night_{tier}.asset");
            env.presets=new[]{preset};env.activeIndex=0;
            env.skyMaterial=SaveOwned(new Material(env.skyMaterial),$"{Dir}/Sky_{label}.mat");
            if (mode=="retro-disabled")
                foreach (var draw in Object.FindObjectsByType<WorldInstances>(FindObjectsSortMode.None))
                {
                    var set=Object.Instantiate(draw.set);
                    for (int j=0;j<set.materials.Length;j++) if(set.materials[j]!=null && set.materials[j].IsKeywordEnabled(Keyword))
                    {
                        var mat=new Material(set.materials[j]);mat.DisableKeyword(Keyword);
                        set.materials[j]=SaveOwned(mat,$"{Dir}/Off_{label}_{j}.mat");
                    }
                    draw.set=SaveOwned(set,$"{Dir}/OffSet_{label}.asset");
                }
            foreach (var c in Object.FindObjectsByType<ControlCamera>(FindObjectsInactive.Include,FindObjectsSortMode.None)) Object.DestroyImmediate(c);
            foreach (var pair in new[]{("furniture-night-driver",55f),("furniture-night-detail",15f)})
            {
                var go=new GameObject(pair.Item1);
                go.transform.position=eye;go.transform.LookAt(target.point,Vector3.up);
                var camera=go.AddComponent<Camera>();camera.enabled=false;camera.fieldOfView=pair.Item2;camera.nearClipPlane=.05f;camera.farClipPlane=3500;
                go.AddComponent<UniversalAdditionalCameraData>();
                var control=go.AddComponent<ControlCamera>();control.id=pair.Item1;
                control.note="Real rig sockets and ocular point; controlled asphalt pose; 15 degree view is diagnostic zoom, not driver FOV.";
            }
            string sceneName="FurnitureSignNight_"+label;
            string scenePath=$"{Dir}/{sceneName}.unity";
            EditorSceneManager.SaveScene(scene,scenePath);
            AssetDatabase.SaveAssets();
            var samples=new List<Sample>();
            void Observe(ScriptableRenderContext context,Camera camera)
            {
                var control=camera.GetComponent<ControlCamera>();
                if(control==null || !control.id.StartsWith("furniture-night-",StringComparison.Ordinal)) return;
                var actual=Object.FindAnyObjectByType<TruckLights>();
                samples.Add(new Sample {tier=tier,mode=mode,camera=control.id,ground=ground,requestedHorizontalM=distance,
                    cameraFov=camera.fieldOfView,sign=target.point,normal=target.normal,eye=camera.transform.position,vehicle=position,
                    state=Shader.GetGlobalVector("_FurnitureRetroState"),lowLeft=Shader.GetGlobalVector("_FurnitureRetroHead0"),
                    lowRight=Shader.GetGlobalVector("_FurnitureRetroHead1"),highLeft=Shader.GetGlobalVector("_FurnitureRetroHead2"),
                    highRight=Shader.GetGlobalVector("_FurnitureRetroHead3"),exposure=Shader.GetGlobalFloat("_KamionExposure"),
                    actualLightEnabled=actual!=null && actual.enabled,actualLightActive=actual!=null && actual.gameObject.activeInHierarchy,
                    actualLowOn=actual!=null && actual.LowBeamOn,actualHighOn=actual!=null && actual.highBeam,
                    actualLightId=actual!=null?actual.GetInstanceID():0,
                    trueSunElevation=EnvironmentLighting.Instance?.Model?.TrueSunElevationDeg ?? 999});
            }
            RenderPipelineManager.beginCameraRendering+=Observe;
            FurnitureSignQaRigMode.Bind(mode);
            string folder=Path.Combine(output,mode,distance.ToString("0"));
            try
            {
                // Allow the runtime's 1 Hz missing-source retry deadline to expire before loading the next scene.
                // This does NOT replace the automatic bridge with a synthetic/published camera light.
                System.Threading.Thread.Sleep(1100);
                int count=VisualQaRunner.Render(sceneName,2340,1080,tier,folder,null,"furniture-night-driver,furniture-night-detail");
                if(count!=2 || samples.Count==0) throw new InvalidOperationException("Missing controlled frame/source evidence");
                bool on=mode!="source-disabled";
                if(samples.Any(s=>(s.state.x>.5f)!=on)) throw new InvalidOperationException("Automatic source state did not match controlled rig mode");
                if(on && samples.Any(s=>s.lowLeft.w<=0 || s.lowRight.w<=0)) throw new InvalidOperationException("Low socket pair not published");
                if(mode=="high" && samples.Any(s=>s.highLeft.w<=0 || s.highRight.w<=0)) throw new InvalidOperationException("High socket pair not published");
                Debug.Log($"[FurnitureNight] {label}: {samples.Count} actual camera-source samples; model sun=-8, eye={eye}, sign={target.point}");
            }
            finally
            {
                RenderPipelineManager.beginCameraRendering-=Observe;
                FurnitureSignQaRigMode.Unbind();
                Directory.CreateDirectory(folder);
                File.WriteAllText(Path.Combine(folder,"source-evidence.json"),JsonUtility.ToJson(new Evidence{samples=samples.ToArray()},true));
            }
        }
    }
}
