using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Game.Editor.Build;
using Game.Rendering;
using Game.World;
using Game.World.Import;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Editor.VisualQA
{
    public static class R4PlateGpuProbe
    {
        const string PathShader="Assets/_Generated/R4PlateProbe/Readback.shader";
        static WorldInstanceSet s_KeepSet;
        sealed class Input { public int index; public string prototype; public Matrix4x4 matrix; }
        [Serializable] sealed class Row { public string prototype,control;public int lod,index,cpuCell,gpuCell;public Vector3 shift;public Vector2 actual,expected; }
        [Serializable] sealed class Evidence { public string graphics,forwardMode,shader,texture,sourceSha256,instancesSha256;
            public int nativePlatePrimitives,nativeMeshes,instanceSamples,skippedLod2,ownedSrpCode,litSrpCode;public float maxUvError;
            public bool originalUnchanged,keywordEnabled,factoryIdempotent;public Row[] cases;public string note; }
        static uint Hash(Matrix4x4 m,Vector4 rect)
        {
            uint x=unchecked((uint)(int)Mathf.Floor((m.m03-rect.x)*4+.37f)),z=unchecked((uint)(int)Mathf.Floor((m.m23-rect.y)*4+.37f));
            uint h=unchecked(x*1664525u+z*1013904223u);h^=h>>16;h=unchecked(h*2246822519u);h^=h>>13;return h;
        }
        static Vector2 Expected(int cell)
        {
            return new Vector2(cell%4*.25f+4f/1024+(8.5f/16)*248f/1024,
                (7-cell/4)*.125f+5f/512+(4.5f/8)*54f/512);
        }
        static string Sha(string path)=>BitConverter.ToString(System.Security.Cryptography.SHA256.Create().ComputeHash(File.ReadAllBytes(path))).Replace("-","").ToLowerInvariant();
        static int Srp(Shader shader)
        {
            var method=typeof(ShaderUtil).GetMethod("GetSRPBatcherCompatibilityCode",BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic);
            return method==null?-999:Convert.ToInt32(method.Invoke(null,new object[]{shader,0}));
        }
        static Shader Build(string path)
        {
            string text=File.ReadAllText(path).Replace("Shader \"Kamion/World Car Plate\"","Shader \"Hidden/Kamion/R4PlateReadback\"")
                .Replace("#pragma fragment LitPassFragment","#pragma fragment PlateReadbackFragment")
                .Replace("return OriginalLitPassVertex(input);",@"Varyings output = OriginalLitPassVertex(input);
                    uint tile=0;
                    #if defined(UNITY_INSTANCING_ENABLED)
                    tile=unity_InstanceID & 3u;
                    #endif
                    output.positionCS=float4((input.staticLightmapUV.x+tile)*.5-1,input.staticLightmapUV.y*2-1,.1,1);
                    return output;");
            int anchor=text.IndexOf("ENDHLSL",StringComparison.Ordinal);
            text=text.Insert(anchor,"float4 PlateReadbackFragment(Varyings input):SV_Target { return float4(input.uv,0,1); }\n");
            string full=System.IO.Path.Combine(EditorTools.ProjectRoot,PathShader);Directory.CreateDirectory(System.IO.Path.GetDirectoryName(full));File.WriteAllText(full,text);
            AssetDatabase.ImportAsset(PathShader,ImportAssetOptions.ForceSynchronousImport|ImportAssetOptions.ForceUpdate);
            var shader=AssetDatabase.LoadAssetAtPath<Shader>(PathShader);
            if(shader==null||ShaderUtil.ShaderHasError(shader))throw new InvalidOperationException("Plate diagnostic shader import failed");return shader;
        }
        public static void RunBatch()
        {
            string folder=System.IO.Path.Combine(EditorTools.RepoRoot,"artifacts/car-paint-r1/r4-plate-gpu");Directory.CreateDirectory(folder);
            EditorSceneManager.OpenScene("Assets/_Generated/World/bialystok-industrial-c/WorldC_High.unity",OpenSceneMode.Single);
            var renderer=UnityEngine.Object.FindAnyObjectByType<WorldInstances>();var gi=UnityEngine.Object.FindAnyObjectByType<WorldSkyVisibility>();
            var set=renderer.set;s_KeepSet=set;Vector3 origin=renderer.transform.position;
            var plate=set.materials.First(m=>m.name=="M_car_plate");
            if(plate.shader.name!=WorldCarPlateMaterials.ShaderName||!plate.IsKeywordEnabled(WorldCarPlateMaterials.Keyword)||!WorldCarPlateMaterials.ValidNativeLibrary(set,plate))throw new InvalidOperationException("Native plate eligibility/binding missing");
            string source=System.IO.Path.Combine(Application.dataPath,"_Project/Environment/Shaders/WorldCarPlate.shader"),before=Sha(source);
            var evidence=new Evidence{graphics=SystemInfo.graphicsDeviceType.ToString(),shader=plate.shader.name,texture=AssetDatabase.GetAssetPath(plate.GetTexture("_BaseMap")),sourceSha256=before,
                instancesSha256=Sha(System.IO.Path.Combine(EditorTools.ProjectRoot,AssetDatabase.GetAssetPath(set))),nativePlatePrimitives=54,nativeMeshes=81,skippedLod2=27,
                ownedSrpCode=Srp(plate.shader),litSrpCode=Srp(Shader.Find("Universal Render Pipeline/Lit")),keywordEnabled=true,
                note="Actual plate-only source forward vertex function, native plate submeshes and RenderMeshInstanced matrices. Float RT UV readback, diagnostic clip/fragment only. Not phone, timing, uniqueness or far-readability proof."};
            // Exercise repeat success -> rejection -> success on PRIVATE clones only.
            var copy=UnityEngine.Object.Instantiate(set);var clonedPlate=new Material(plate);
            try
            {
                copy.materials=set.materials.Select(m=>m==plate?clonedPlate:m).ToArray();
                var region=new RegionImporter.Result{Instances=copy};region.Materials["car_plate"]=clonedPlate;
                string initial=EditorJsonUtility.ToJson(clonedPlate);
                WorldCarPlateMaterials.Configure(region);WorldCarPlateMaterials.Configure(region);
                if(EditorJsonUtility.ToJson(clonedPlate)!=initial)throw new InvalidOperationException("Repeat plate factory changed material state");
                var prototypesBefore=copy.prototypes;copy.prototypes=Array.Empty<WorldInstanceSet.Prototype>();WorldCarPlateMaterials.Configure(region);
                if(clonedPlate.shader.name!="Universal Render Pipeline/Lit"||clonedPlate.IsKeywordEnabled(WorldCarPlateMaterials.Keyword))throw new InvalidOperationException("Rejected migration retained enabled wrapper");
                copy.prototypes=prototypesBefore;WorldCarPlateMaterials.Configure(region);
                evidence.factoryIdempotent=EditorJsonUtility.ToJson(clonedPlate)==initial;
                if(!evidence.factoryIdempotent)throw new InvalidOperationException("Restored plate factory state differs");
            }
            finally{UnityEngine.Object.DestroyImmediate(clonedPlate);UnityEngine.Object.DestroyImmediate(copy);}
            var inputs=new List<Input>();
            foreach(var run in set.runs){var p=set.prototypes[run.prototype];if(!p.name.StartsWith("car_")&&!p.name.StartsWith("van_"))continue;
                for(int i=0;i<run.count;i++){int index=run.start+i;var matrix=set.LocalMatrix(index);matrix.m03+=origin.x;matrix.m13+=origin.y;matrix.m23+=origin.z;inputs.Add(new Input{index=index,prototype=p.name,matrix=matrix});}}
            var chosen=new[]{13465,14842,8908,731}.Select(index=>inputs.Single(i=>i.index==index)).ToArray();
            Vector3 corner=gi.transform.TransformPoint(new Vector3(gi.originLocal.x,gi.heightBase,gi.originLocal.y));
            float texelM=gi.texelM;
            var rect=new Vector4(corner.x,corner.z,1f/(gi.map.width*texelM),1f/(gi.map.height*texelM));
            var oldRect=Shader.GetGlobalVector("_KamionGIRect");var oldHeight=Shader.GetGlobalVector("_KamionGIHeight");
            var originalMaterialJson=EditorJsonUtility.ToJson(plate);
            var prototypes=set.prototypes.Where(p=>p.name.StartsWith("car_")||p.name.StartsWith("van_")).ToArray();
            renderer.set=null;EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
            var probeShader=Build(source); // Import/unload BEFORE constructing transient draw objects.
            var material=new Material(plate){shader=probeShader,enableInstancing=true,hideFlags=HideFlags.HideAndDontSave};
            material.EnableKeyword(WorldCarPlateMaterials.Keyword);material.SetFloat("_Cull",0);
            var go=new GameObject("Plate numeric probe");var camera=go.AddComponent<Camera>();camera.enabled=false;camera.transform.position=new Vector3(0,0,-5000);camera.orthographic=true;camera.orthographicSize=5000;
            camera.nearClipPlane=.01f;camera.farClipPlane=20000;camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=Color.magenta;camera.allowMSAA=false;camera.allowHDR=true;
            var extra=camera.GetUniversalAdditionalCameraData();extra.renderPostProcessing=false;extra.antialiasing=AntialiasingMode.None;extra.volumeLayerMask=0;
            var rt=new RenderTexture(64,8,24,RenderTextureFormat.ARGBFloat,RenderTextureReadWrite.Linear);rt.Create();camera.targetTexture=rt;
            var pixels=new Texture2D(64,8,TextureFormat.RGBAFloat,false,true);var rows=new List<Row>();
            try
            {
                void Draw(WorldInstanceSet.Prototype proto,int lod,Input[] batchInputs,Vector3 shift,string control)
                {
                    var mesh=proto.lods[lod];int sub=Enumerable.Range(0,mesh.subMeshCount).Single(s=>set.materials[proto.materialStart[lod]+s]==plate);
                    var matrices=batchInputs.Select(i=>{var m=i.matrix;m.m03+=shift.x;m.m23+=shift.z;return m;}).ToArray();
                    var movedRect=rect;movedRect.x+=shift.x;movedRect.y+=shift.z;
                    Action<ScriptableRenderContext,Camera> issue=(context,c)=>{if(c!=camera)return;Shader.SetGlobalVector("_KamionGIRect",movedRect);Shader.SetGlobalVector("_KamionGIHeight",new Vector4(0,.3f,texelM,control=="GI-off"?0:1));
                        var rp=new RenderParams(material){camera=c,worldBounds=new Bounds(Vector3.zero,Vector3.one*20000),shadowCastingMode=ShadowCastingMode.Off,receiveShadows=false,lightProbeUsage=LightProbeUsage.Off,reflectionProbeUsage=ReflectionProbeUsage.Off};
                        Graphics.RenderMeshInstanced(rp,mesh,sub,matrices,4);};
                    RenderPipelineManager.beginCameraRendering+=issue;try{camera.Render();}finally{RenderPipelineManager.beginCameraRendering-=issue;}
                    var active=RenderTexture.active;RenderTexture.active=rt;pixels.ReadPixels(new Rect(0,0,64,8),0,0);pixels.Apply();RenderTexture.active=active;
                    for(int j=0;j<4;j++){int cpu=(int)(Hash(batchInputs[j].matrix,rect)%27);var expected=Expected(cpu);Color pixel=pixels.GetPixel(8+16*j,4);var actual=new Vector2(pixel.r,pixel.g);
                        float error=(actual-expected).magnitude;evidence.maxUvError=Mathf.Max(error,evidence.maxUvError);
                        if(error>.0001f||pixel.b>.001f)throw new InvalidOperationException($"Plate UV mismatch {proto.name} lod{lod} {control} cpu{cpu} actual{actual} expected{expected}");
                        int gpu=Mathf.FloorToInt(actual.x*4)+4*(7-Mathf.FloorToInt(actual.y*8));
                        rows.Add(new Row{prototype=proto.name,lod=lod,index=batchInputs[j].index,cpuCell=cpu,gpuCell=gpu,control=control,shift=shift,actual=actual,expected=expected});}
                }
                foreach(var proto in prototypes)for(int lod=0;lod<2;lod++)Draw(proto,lod,chosen,Vector3.zero,"native54");
                foreach(var shift in new[]{new Vector3(1024,0,0),new Vector3(-1024,0,1024),new Vector3(4096,0,-4096),new Vector3(-4096,0,4096),new Vector3(512.25f,0,-2048.75f)})
                    for(int lod=0;lod<2;lod++)Draw(prototypes.First(p=>p.name=="car_hatch_black"),lod,chosen,shift,"rebase");
                Draw(prototypes.First(p=>p.name=="car_hatch_black"),0,chosen,Vector3.zero,"GI-off");
                var mode=extra.scriptableRenderer.GetType().GetProperty("renderingModeActual",BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public);
                evidence.forwardMode=mode?.GetValue(extra.scriptableRenderer)?.ToString()??"UNVERIFIED";
                if(evidence.forwardMode!="Forward")throw new InvalidOperationException("Current renderer is not proven Forward: "+evidence.forwardMode);
                evidence.cases=rows.ToArray();evidence.instanceSamples=rows.Count;evidence.originalUnchanged=Sha(source)==before&&EditorJsonUtility.ToJson(plate)==originalMaterialJson;
                if(!evidence.originalUnchanged)throw new InvalidOperationException("Plate source/material changed during diagnostic");
                File.WriteAllText(System.IO.Path.Combine(folder,"plate-vertex-gpu-proof.json"),JsonUtility.ToJson(evidence,true));Debug.Log("R4_PLATE_GPU_RESULT: OK samples="+rows.Count);
            }
            finally{Shader.SetGlobalVector("_KamionGIRect",oldRect);Shader.SetGlobalVector("_KamionGIHeight",oldHeight);UnityEngine.Object.DestroyImmediate(material);UnityEngine.Object.DestroyImmediate(pixels);rt.Release();UnityEngine.Object.DestroyImmediate(rt);UnityEngine.Object.DestroyImmediate(go);s_KeepSet=null;}
        }
    }
}
