// QA-only full-shader clone. Production source, native assets and scene placements stay unchanged.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Game.Editor.Build;
using Game.Rendering;
using Game.World;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.Editor.VisualQA
{
    public static class R4RearControls
    {
        sealed class Binding { public WorldInstances renderer;public WorldInstanceSet original,copy;public List<Material> materials=new List<Material>(); }
        static readonly List<Binding> bindings=new List<Binding>();
        static Shader diagnostic;
        static string repo=>EditorTools.RepoRoot;
        static string Hash(string p){using(var h=System.Security.Cryptography.SHA256.Create())return BitConverter.ToString(h.ComputeHash(File.ReadAllBytes(p))).Replace("-","").ToLowerInvariant();}
        static Shader Build()
        {
            string source=Path.Combine(repo,"game/Assets/_Project/Environment/Shaders/WorldPBR.shader");
            string s=File.ReadAllText(source).Replace("Shader \"Kamion/World PBR\"","Shader \"Hidden/Kamion/R4RearSameFrameControl\"")
                .Replace("../../Rendering/Shaders/KamionLampPools.hlsl","Assets/_Project/Rendering/Shaders/KamionLampPools.hlsl")
                .Replace("../../Rendering/Shaders/VegetationGround.hlsl","Assets/_Project/Rendering/Shaders/VegetationGround.hlsl")
                .Replace("TEXTURE2D(_RunoffMap);","TEXTURE2D(_RunoffMap); float _R4ForceLevel; float _R4OpacityOff; float4 _R4TargetOrigin;");
            const string vertex="o.carFilm = CarInstanceFilm(float2(GetObjectToWorldMatrix()._m03, GetObjectToWorldMatrix()._m23));";
            const string mask="mask.a = lerp(mask.a, 0.25h, carFilmOpacity);";
            if(!s.Contains(vertex)||!s.Contains(mask))throw new InvalidOperationException("QA clone anchors changed");
            s=s.Replace(vertex,vertex+@"
                if (_R4ForceLevel >= 0 && all(abs(float2(GetObjectToWorldMatrix()._m03,GetObjectToWorldMatrix()._m23)-_R4TargetOrigin.xy)<0.02))
                    o.carFilm.x = _R4ForceLevel / 3.0;");
            s=s.Replace(mask,@"if (all(abs(float2(GetObjectToWorldMatrix()._m03,GetObjectToWorldMatrix()._m23)-_R4TargetOrigin.xy)<0.02))
                        carFilmOpacity *= 1.0h-saturate(_R4OpacityOff);
                    "+mask);
            const string asset="Assets/_Generated/R4RearControls/R4RearControls.shader";
            string full=Path.Combine(EditorTools.ProjectRoot,asset);Directory.CreateDirectory(Path.GetDirectoryName(full));File.WriteAllText(full,s);
            AssetDatabase.ImportAsset(asset,ImportAssetOptions.ForceSynchronousImport|ImportAssetOptions.ForceUpdate);
            var shader=AssetDatabase.LoadAssetAtPath<Shader>(asset);
            if(shader==null||ShaderUtil.ShaderHasError(shader))throw new InvalidOperationException("Rear-control shader clone compile failed");
            return shader;
        }
        static void Install(ScriptableRenderContext context,Camera camera)
        {
            if(camera.GetComponent<ControlCamera>()==null)return;
            foreach(var w in UnityEngine.Object.FindObjectsByType<WorldInstances>(FindObjectsInactive.Include,FindObjectsSortMode.None))
            {
                if(w.set==null||bindings.Any(b=>b.renderer==w))continue;
                var b=new Binding{renderer=w,original=w.set};
                b.copy=UnityEngine.Object.Instantiate(w.set);b.copy.hideFlags=HideFlags.DontSave;
                var mats=b.copy.materials.ToArray();
                for(int i=0;i<mats.Length;i++)
                {
                    var original=mats[i];if(original==null||!original.IsKeywordEnabled("_CARPAINT"))continue;
                    var clone=new Material(original){shader=diagnostic,hideFlags=HideFlags.DontSave,name=original.name+"_R4_QA"};
                    clone.shaderKeywords=original.shaderKeywords;clone.enableInstancing=true;mats[i]=clone;b.materials.Add(clone);
                }
                b.copy.materials=mats;w.set=b.copy;bindings.Add(b);
            }
        }
        static void Restore()
        {
            foreach(var b in bindings){if(b.renderer!=null)b.renderer.set=b.original;foreach(var m in b.materials)UnityEngine.Object.DestroyImmediate(m);if(b.copy!=null)UnityEngine.Object.DestroyImmediate(b.copy);}
            bindings.Clear();
        }
        public static void RunBatch()
        {
            string folder=Path.Combine(repo,"artifacts/car-paint-r1");
            // Existing, unchanged vertex-policy probe with additive per-instance logging.
            R4CarFilmGpuProbe.RunBatch();
            var gpu=JsonUtility.FromJson<R4CarFilmGpuProbe.Evidence>(File.ReadAllText(Path.Combine(folder,"r4-gpu/instanced-film-gpu-proof.json")));
            var target=gpu.perInstance.Where(s=>s.prototype=="car_hatch_black"&&Mathf.Abs(s.e-674.796f)<.01f&&Mathf.Abs(s.n+523.807f)<.01f).ToArray();
            if(target.Length!=1||target[0].gpuLevel!=3)throw new InvalidOperationException("Natural target GPU level3 not proven");
            diagnostic=Build();
            string cameraJson=Path.Combine(folder,"r4-rear-control-camera.json");
            string oldGate=Environment.GetEnvironmentVariable("KAMION_R4_UNUSED");
            float oldForce=Shader.GetGlobalFloat("_R4ForceLevel"),oldOff=Shader.GetGlobalFloat("_R4OpacityOff");var oldTarget=Shader.GetGlobalVector("_R4TargetOrigin");
            var previousArgs=Environment.GetCommandLineArgs();
            // VisualQaRunner reads -qaGate3 from the process arguments supplied by the wrapper.
            if(!previousArgs.Contains("-qaGate3"))throw new InvalidOperationException("Supplemental camera argument missing");
            string oldPose=Environment.GetEnvironmentVariable("KAMION_G_POSE_OUTPUT");
            string source=Path.Combine(repo,"game/Assets/_Project/Environment/Shaders/WorldPBR.shader");var originalHash=Hash(source);
            try
            {
                Shader.SetGlobalVector("_R4TargetOrigin",new Vector4(674.796f,-523.807f,0,0));
                foreach(string tier in new[]{"Low","High"})foreach(string light in new[]{"clear","overcast"})
                foreach(string mode in new[]{"off","level0","level1","level2","level3"})
                {
                    float level=mode=="off"?-1:float.Parse(mode.Substring(5));
                    Shader.SetGlobalFloat("_R4ForceLevel",level);Shader.SetGlobalFloat("_R4OpacityOff",mode=="off"?1:0);
                    string output=Path.Combine(folder,EditorTools.Arg("-r4ControlTag","r4-rear-controls"),tier+"-"+light,mode);
                    if(Directory.Exists(output))throw new InvalidOperationException("Refuse overwrite "+output);
                    Environment.SetEnvironmentVariable("KAMION_G_POSE_OUTPUT",Path.Combine(output,"poses"));
                    RenderPipelineManager.beginCameraRendering+=Install;
                    try
                    {
                        int count=VisualQaRunner.Render(tier=="High"?"WorldC_High":"WorldC",2340,1080,tier,output,light,"r4_rear_target_3");
                        if(count!=1)throw new InvalidOperationException("Expected exactly one rear control, got "+count);
                        File.WriteAllText(Path.Combine(output,"control-state.json"),"{\"mode\":\""+mode+"\",\"forceLevel\":"+level.ToString(System.Globalization.CultureInfo.InvariantCulture)+",\"opacityOff\":"+(mode=="off"?"true":"false")+",\"target\":[674.796,-523.807],\"naturalLevel\":3,\"shaderSourceSha256\":\""+originalHash+"\",\"note\":\"QA-only same-frame control, not historical R3 BEFORE; phase, upper-role and non-target cars unchanged\"}");
                    }
                    finally{RenderPipelineManager.beginCameraRendering-=Install;Restore();}
                }
                if(Hash(source)!=originalHash)throw new InvalidOperationException("Production source changed during QA control");
                Debug.Log("R4_REAR_CONTROLS_RESULT: OK frames=20 sourceUnchanged=True");
            }
            finally
            {
                Restore();Shader.SetGlobalFloat("_R4ForceLevel",oldForce);Shader.SetGlobalFloat("_R4OpacityOff",oldOff);Shader.SetGlobalVector("_R4TargetOrigin",oldTarget);
                Environment.SetEnvironmentVariable("KAMION_G_POSE_OUTPUT",oldPose);
            }
        }
    }
}
