// Artifact-only diagnostic: actual native paint meshes and actual WorldPBR fragment prefix.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Game.Editor.Build;
using Game.Rendering;
using Game.World;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Editor.VisualQA
{
    public static class R4CarOpacityProbe
    {
        const int Width=512,Height=256;
        [Serializable] public class Result
        {
            public string prototype;
            public int lod, pixels;
            public float maxHeightError,maxAxleError,maxOpacityError;
            public string yOrientation;
        }
        [Serializable] public class Evidence
        {
            public string method, shaderSha256, graphics;
            public int instances;
            public Result[] cases;
            public string note="Numeric diagnostic viewport and fragment-return adapter; actual meshes/material bindings and source fragment calculations. Not lighting, performance, full-image or device proof.";
        }
        static string Hash(string p){using(var h=System.Security.Cryptography.SHA256.Create())return BitConverter.ToString(h.ComputeHash(File.ReadAllBytes(p))).Replace("-","").ToLowerInvariant();}
        static Shader BuildShader(string source)
        {
            string s=File.ReadAllText(source).Replace("Shader \"Kamion/World PBR\"","Shader \"Hidden/Kamion/R4OpacityReadback\"")
                .Replace("../../Rendering/Shaders/KamionLampPools.hlsl","Assets/_Project/Rendering/Shaders/KamionLampPools.hlsl")
                .Replace("../../Rendering/Shaders/VegetationGround.hlsl","Assets/_Project/Rendering/Shaders/VegetationGround.hlsl")
                .Replace("TEXTURE2D(_RunoffMap);","TEXTURE2D(_RunoffMap); float4 _GProbeBounds;");
            s=s.Replace("o.positionCS = p.positionCS;",@"uint tile=0;
                #if defined(UNITY_INSTANCING_ENABLED)
                tile=unity_InstanceID & 3u;
                #endif
                float2 local=(v.positionOS.zy-_GProbeBounds.xy)/max(_GProbeBounds.zw,0.01);
                o.positionCS=float4(local*float2(0.24,0.80)+float2(-0.75+0.5*tile,0),0.1,1);");
            s=s.Replace("half carFilmOpacity = 0.0h;","half carFilmOpacity = 0.0h; half probeKeepUpper=0;")
                .Replace("half upperFilm = saturate(mask.r);","probeKeepUpper=keepUpper; half upperFilm = saturate(mask.r);");
            const string anchor="half3 albedo = base.rgb * _Tint.rgb * _AlbedoScale;";
            if(!s.Contains(anchor))throw new InvalidOperationException("Actual fragment anchor changed");
            s=s.Replace(anchor,@"#if defined(_CARPAINT)
                return half4(carFilmOpacity,i.uv.z,i.uv.w,probeKeepUpper);
                #endif
                "+anchor);
            const string asset="Assets/_Generated/R4CarOpacityProbe/OpacityReadback.shader";
            string full=Path.Combine(EditorTools.ProjectRoot,asset);Directory.CreateDirectory(Path.GetDirectoryName(full));File.WriteAllText(full,s);
            AssetDatabase.ImportAsset(asset,ImportAssetOptions.ForceSynchronousImport|ImportAssetOptions.ForceUpdate);
            var shader=AssetDatabase.LoadAssetAtPath<Shader>(asset);
            if(shader==null||ShaderUtil.ShaderHasError(shader))throw new InvalidOperationException("Opacity diagnostic shader compile failed");
            return shader;
        }
        static int Level(Matrix4x4 m,Vector4 rect)
        {
            uint x=unchecked((uint)Mathf.FloorToInt((m.m03-rect.x)*4f+.37f)),z=unchecked((uint)Mathf.FloorToInt((m.m23-rect.y)*4f+.37f));
            uint h=unchecked(x*1664525u+z*1013904223u);h^=h>>16;h=unchecked(h*2246822519u);h^=h>>13;
            return h<429496730u?0:(h<1932735283u?1:(h<3435973837u?2:3));
        }
        static Vector4 Dimensions(string name)
        {
            // x sill, y rear axle, z wheelbase; source-contract table is separately pinned/tested.
            if(name.StartsWith("van_"))return new Vector4(.27f,-1.48f,3,0);
            if(name.StartsWith("car_hatch_"))return new Vector4(.19f,-1.37f,2.62f,0);
            if(name.StartsWith("car_sedan_"))return new Vector4(.19f,-1.28f,2.70f,0);
            if(name.StartsWith("car_estate_"))return new Vector4(.19f,-1.27f,2.70f,0);
            if(name.StartsWith("car_suv_"))return new Vector4(.25f,-1.35f,2.66f,0);
            throw new InvalidOperationException("Unknown car class "+name);
        }
        static float ExpectedOpacity(float h,float u,float upper,int level)
        {
            float amount=.08f+.92f*(level/3f),falloff=.16f+.06f*(level/3f);
            float weight=Mathf.Max(Mathf.Max(Mathf.Clamp01(1-Mathf.Abs(u-.87f)/.28f),Mathf.Clamp01(1-Mathf.Abs(u+.13f)/.28f)),Mathf.Clamp01((-u-.20f)*8));
            return .5f*amount*Mathf.Pow(2,-Mathf.Max(h,0)/falloff*1.442695f)*(.72f+.28f*weight)*(1-upper);
        }
        public static void RunBatch()
        {
            EditorSceneManager.OpenScene("Assets/_Generated/World/bialystok-industrial-c/WorldC_High.unity",OpenSceneMode.Single);
            var wi=UnityEngine.Object.FindAnyObjectByType<WorldInstances>();var sky=UnityEngine.Object.FindAnyObjectByType<WorldSkyVisibility>();
            if(wi==null||wi.set==null||sky==null)throw new InvalidOperationException("Canonical candidate world missing");
            var set=wi.set;Vector3 origin=wi.transform.position;
            var corner=sky.transform.TransformPoint(new Vector3(sky.originLocal.x,sky.heightBase,sky.originLocal.y));
            var rect=new Vector4(corner.x,corner.z,1f/(sky.map.width*sky.texelM),1f/(sky.map.height*sky.texelM));
            var batch=new Matrix4x4[4];var found=new bool[4];int actual=0;
            foreach(var run in set.runs)
            {
                var p=set.prototypes[run.prototype];if(!p.name.StartsWith("car_")&&!p.name.StartsWith("van_"))continue;
                for(int j=0;j<run.count;j++){var m=set.LocalMatrix(run.start+j);m.m03+=origin.x;m.m13+=origin.y;m.m23+=origin.z;int l=Level(m,rect);if(!found[l]){batch[l]=m;found[l]=true;}actual++;}
            }
            if(found.Any(x=>!x))throw new InvalidOperationException("Four actual instance levels missing");
            var protos=set.prototypes.Where(p=>p.name.StartsWith("car_")||p.name.StartsWith("van_")).ToArray();
            var materials=set.materials;var source=Path.Combine(Application.dataPath,"_Project/Environment/Shaders/WorldPBR.shader");
            var shader=BuildShader(source);
            // Keep native assets strongly referenced while clearing unrelated scene renderers.
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
            var go=new GameObject("R4 actual UV opacity probe");var camera=go.AddComponent<Camera>();camera.enabled=false;camera.orthographic=true;
            camera.transform.position=new Vector3(0,0,-5000);camera.orthographicSize=5000;camera.nearClipPlane=.01f;camera.farClipPlane=20000;
            camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=new Color(9,9,9,9);camera.allowHDR=true;camera.allowMSAA=false;
            var extra=camera.GetUniversalAdditionalCameraData();extra.renderPostProcessing=false;extra.antialiasing=AntialiasingMode.None;extra.volumeLayerMask=0;
            var rt=new RenderTexture(Width,Height,24,RenderTextureFormat.ARGBFloat,RenderTextureReadWrite.Linear){filterMode=FilterMode.Point};rt.Create();camera.targetTexture=rt;
            var pixels=new Texture2D(Width,Height,TextureFormat.RGBAFloat,false,true);
            var pipeline=GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;float oldScale=pipeline==null?1:pipeline.renderScale;
            if(pipeline!=null)pipeline.renderScale=1; // Fixed numeric pixel-coordinate diagnostic, not an upscaler quality test.
            var rows=new List<Result>();
            try
            {
                foreach(var p in protos)for(int lod=0;lod<p.lods.Length;lod++)
                {
                    var mesh=p.lods[lod];var dims=Dimensions(p.name);var bounds=mesh.bounds;
                    if(!mesh.HasVertexAttribute(VertexAttribute.TexCoord1))throw new InvalidOperationException("Native UV1 absent "+mesh.name);
                    var slots=Enumerable.Range(0,mesh.subMeshCount).Where(s=>materials[p.materialStart[lod]+s].IsKeywordEnabled("_CARPAINT")).ToArray();
                    if(slots.Length!=1)throw new InvalidOperationException("Expected one paint material group "+p.name);
                    var material=new Material(materials[p.materialStart[lod]+slots[0]]){shader=shader,enableInstancing=true};material.SetFloat("_Cull",0);
                    Shader.SetGlobalVector("_GProbeBounds",new Vector4(bounds.center.z,bounds.center.y,bounds.extents.z,bounds.extents.y));
                    Action<ScriptableRenderContext,Camera> draw=(context,c)=>{if(c!=camera)return;Shader.SetGlobalVector("_KamionGIRect",rect);
                        var rp=new RenderParams(material){camera=c,worldBounds=new Bounds(Vector3.zero,Vector3.one*20000),shadowCastingMode=ShadowCastingMode.Off,receiveShadows=false,lightProbeUsage=LightProbeUsage.Off,reflectionProbeUsage=ReflectionProbeUsage.Off};
                        Graphics.RenderMeshInstanced(rp,mesh,slots[0],batch,4);};
                    RenderPipelineManager.beginCameraRendering+=draw;try{camera.Render();}finally{RenderPipelineManager.beginCameraRendering-=draw;}
                    var previous=RenderTexture.active;RenderTexture.active=rt;pixels.ReadPixels(new Rect(0,0,Width,Height),0,0);pixels.Apply();RenderTexture.active=previous;
                    var colors=pixels.GetPixels();var record=new Result{prototype=p.name,lod=lod};
                    double errPlus=0,errMinus=0;int count=0;
                    for(int y=2;y<Height-2;y++)for(int x=2;x<Width-2;x++)
                    {var color=colors[y*Width+x];if(color.r>.55f||color.g<-.1f||color.g>3||color.b<-1||color.b>2)continue;
                        float baseY=((2*(y+.5f)/Height-1)/.8f)*bounds.extents.y;
                        errPlus+=Math.Abs(color.g-(bounds.center.y+baseY-dims.x));errMinus+=Math.Abs(color.g-(bounds.center.y-baseY-dims.x));count++;}
                    bool flip=errMinus<errPlus;record.yOrientation=flip?"RTreadbackY inverted":"RTreadbackY direct";
                    for(int y=2;y<Height-2;y++)for(int x=2;x<Width-2;x++)
                    {
                        var color=colors[y*Width+x];if(color.r>.55f||color.g<-.1f||color.g>3||color.b<-1||color.b>2)continue;
                        int tile=Math.Min(3,x/(Width/4));float centre=-.75f+.5f*tile;
                        float z=((2*(x+.5f)/Width-1-centre)/.24f)*bounds.extents.z+bounds.center.z;
                        float h=((2*(y+.5f)/Height-1)/.8f)*bounds.extents.y*(flip?-1:1)+bounds.center.y-dims.x;
                        float u=(z-dims.y)/dims.z;
                        record.maxHeightError=Mathf.Max(record.maxHeightError,Mathf.Abs(color.g-h));record.maxAxleError=Mathf.Max(record.maxAxleError,Mathf.Abs(color.b-u));
                        record.maxOpacityError=Mathf.Max(record.maxOpacityError,Mathf.Abs(color.r-ExpectedOpacity(color.g,color.b,color.a,tile)));record.pixels++;
                    }
                    UnityEngine.Object.DestroyImmediate(material);
                    if(record.pixels<100||record.maxHeightError>.003f||record.maxAxleError>.003f||record.maxOpacityError>.003f)
                        throw new InvalidOperationException("UV/opacity readback mismatch "+JsonUtility.ToJson(record));
                    rows.Add(record);
                }
                var evidence=new Evidence{method="RenderMeshInstanced actual native paint meshes, four actual instance matrices, actual fragment opacity/UV1/keepUpper into linear float RT; CPU physical-coordinate and opacity comparison",shaderSha256=Hash(source),graphics=SystemInfo.graphicsDeviceType.ToString(),instances=actual,cases=rows.ToArray()};
                string folder=Path.Combine(EditorTools.RepoRoot,"artifacts/car-paint-r1/r4-gpu");Directory.CreateDirectory(folder);
                File.WriteAllText(Path.Combine(folder,"opacity-uv-proof.json"),JsonUtility.ToJson(evidence,true));
                Debug.Log("R4_OPACITY_GPU_RESULT: OK nativeLODs="+rows.Count+" actualInstances="+actual);
            }
            finally {if(pipeline!=null)pipeline.renderScale=oldScale;camera.targetTexture=null;rt.Release();UnityEngine.Object.DestroyImmediate(rt);UnityEngine.Object.DestroyImmediate(pixels);UnityEngine.Object.DestroyImmediate(go);GC.KeepAlive(set);}
        }
    }
}
