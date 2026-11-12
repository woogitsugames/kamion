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
    // Artifact-only numeric adapter: actual WorldPBR instance vertex path and actual imported matrices.
    // Vertex clip coordinates are packed into four readback tiles; material lighting is replaced by flat film data.
    public static class Life3DCarFilmGpuProbe
    {
        const string ProbePath="Assets/_Generated/Life3DCarFilmGpuProbe/CarFilmReadback.shader";
        static WorldInstanceSet s_KeepSet;
        sealed class Input { public string prototype;public Matrix4x4 matrix;public WorldInstanceSet.Prototype mesh;public Vector3 regionPosition;public int index; }
        [Serializable] public class Example { public string prototype;public int level,index;public float e,n,z;public Vector3 worldOrigin; }
        [Serializable] public class Case { public string label;public Vector3 shift;public int[] expected,actual;public float[] phase;public bool pass; }
        [Serializable] public class InputSample { public string prototype;public int nativeIndex,cpuLevel,gpuLevel;public float e,n,z; }
        [Serializable] public class Evidence { public string unity,graphics,shaderSha256,instancesSha256,method,note;public int instanceCount;public int[] cpuCounts,gpuCounts;public float maximumLevelError;public Case[] cases;public Example[] examples;public InputSample[] perInstance; }

        static string Hash(string path)
        {
            using(var sha=System.Security.Cryptography.SHA256.Create())return BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes(path))).Replace("-","").ToLowerInvariant();
        }
        static float[] Expected(Matrix4x4 m,Vector4 rect)
        {
            uint x=unchecked((uint)Mathf.FloorToInt((m.m03-rect.x)*4f+.37f));
            uint z=unchecked((uint)Mathf.FloorToInt((m.m23-rect.y)*4f+.37f));
            uint h=unchecked(x*1664525u+z*1013904223u);h^=h>>16;h=unchecked(h*2246822519u);h^=h>>13;
            uint level=h<429496730u?0u:(h<1932735283u?1u:(h<3435973837u?2u:3u));
            return new[]{level/3f,(h&1023u)/1024f};
        }

        static Shader BuildShader(string source)
        {
            string text=File.ReadAllText(source);
            if(!text.Contains("float2 CarInstanceFilm"))throw new InvalidOperationException("Actual film policy missing");
            text=text.Replace("Shader \"Kamion/World PBR\"","Shader \"Hidden/Kamion/Life3DCarFilmReadback\"")
                .Replace("../../Rendering/Shaders/KamionLampPools.hlsl","Assets/_Project/Rendering/Shaders/KamionLampPools.hlsl")
                .Replace("../../Rendering/Shaders/VegetationGround.hlsl","Assets/_Project/Rendering/Shaders/VegetationGround.hlsl")
                .Replace("TEXTURE2D(_RunoffMap);","TEXTURE2D(_RunoffMap); float4 _GProbeBounds;");
            const string clip="o.positionCS = p.positionCS;";
            if(!text.Contains(clip))throw new InvalidOperationException("Vertex adapter anchor changed");
            text=text.Replace(clip,@"uint probeTile = 0;
                #if defined(UNITY_INSTANCING_ENABLED)
                probeTile = unity_InstanceID & 3u;
                #endif
                float2 probeLocal = (v.positionOS.xy - _GProbeBounds.xy) / max(_GProbeBounds.zw, 0.01);
                o.positionCS = float4(probeLocal * float2(0.24, 0.80) + float2(-0.75 + 0.5 * probeTile, 0), 0.1, 1);");
            int declaration=text.IndexOf("half4 frag(",StringComparison.Ordinal),body=text.IndexOf('{',declaration),depth=1,end=body+1;
            for(;end<text.Length&&depth>0;end++){if(text[end]=='{')depth++;else if(text[end]=='}')depth--;}
            if(declaration<0||body<0||depth!=0)throw new InvalidOperationException("Fragment adapter anchor changed");
            text=text.Substring(0,body)+@"{
                UNITY_SETUP_INSTANCE_ID(i);
                #if defined(_CARPAINT)
                return half4(i.carFilm.x, i.carFilm.y, 0, 1);
                #else
                return half4(1,0,1,1);
                #endif
            }"+text.Substring(end);
            string full=Path.Combine(Directory.GetParent(Application.dataPath).FullName,ProbePath);
            Directory.CreateDirectory(Path.GetDirectoryName(full));File.WriteAllText(full,text);
            AssetDatabase.ImportAsset(ProbePath,ImportAssetOptions.ForceSynchronousImport|ImportAssetOptions.ForceUpdate);
            var shader=AssetDatabase.LoadAssetAtPath<Shader>(ProbePath);
            if(shader==null||ShaderUtil.ShaderHasError(shader))throw new InvalidOperationException("Actual WorldPBR film readback shader failed");
            return shader;
        }

        static Color[] Read(Camera camera,RenderTexture rt,Texture2D pixels,Material material,Mesh mesh,Matrix4x4[] batch,Vector4 rect)
        {
            Bounds bounds=mesh.bounds;
            Shader.SetGlobalVector("_GProbeBounds",new Vector4(bounds.center.x,bounds.center.y,bounds.extents.x,bounds.extents.y));
            Action<ScriptableRenderContext,Camera> issue=(context,c)=>
            {
                if(c!=camera)return;
                Shader.SetGlobalVector("_KamionGIRect",rect);
                var rp=new RenderParams(material){camera=c,worldBounds=new Bounds(Vector3.zero,Vector3.one*10000),
                    shadowCastingMode=ShadowCastingMode.Off,receiveShadows=false,layer=0,lightProbeUsage=LightProbeUsage.Off,
                    reflectionProbeUsage=ReflectionProbeUsage.Off,motionVectorMode=MotionVectorGenerationMode.Camera};
                for(int sub=0;sub<mesh.subMeshCount;sub++)Graphics.RenderMeshInstanced(rp,mesh,sub,batch,4);
            };
            RenderPipelineManager.beginCameraRendering+=issue;
            try{camera.Render();}finally{RenderPipelineManager.beginCameraRendering-=issue;}
            var previous=RenderTexture.active;RenderTexture.active=rt;
            pixels.ReadPixels(new Rect(0,0,64,16),0,0);pixels.Apply();RenderTexture.active=previous;
            return Enumerable.Range(0,4).Select(i=>pixels.GetPixel(8+i*16,8)).ToArray();
        }

        public static void RunBatch()
        {
            string folder=Path.Combine(EditorTools.RepoRoot,"artifacts/life-r3/gpu-d");Directory.CreateDirectory(folder);
            string source=Path.Combine(Application.dataPath,"_Project/Environment/Shaders/WorldPBR.shader");
            EditorSceneManager.OpenScene("Assets/_Generated/World/bialystok-industrial-c/WorldC_High.unity",OpenSceneMode.Single);
            var renderer=UnityEngine.Object.FindAnyObjectByType<WorldInstances>();
            var gi=UnityEngine.Object.FindAnyObjectByType<WorldSkyVisibility>();
            if(renderer==null||renderer.set==null||gi==null||gi.map==null)throw new InvalidOperationException("Canonical real instance/GI assets missing");
            var set=renderer.set;s_KeepSet=set;
            string instancesPath=Path.Combine(Directory.GetParent(Application.dataPath).FullName,AssetDatabase.GetAssetPath(set));
            Vector3 corner=gi.transform.TransformPoint(new Vector3(gi.originLocal.x,gi.heightBase,gi.originLocal.y));
            var rect=new Vector4(corner.x,corner.z,1f/(gi.map.width*gi.texelM),1f/(gi.map.height*gi.texelM));
            var inputs=new List<Input>();Vector3 origin=renderer.transform.position;
            foreach(var run in set.runs)
            {
                var prototype=set.prototypes[run.prototype];
                if(!prototype.name.StartsWith("car_")&&!prototype.name.StartsWith("van_"))continue;
                for(int j=0;j<run.count;j++)
                {
                    var matrix=set.LocalMatrix(run.start+j);matrix.m03+=origin.x;matrix.m13+=origin.y;matrix.m23+=origin.z;
                    inputs.Add(new Input{prototype=prototype.name,matrix=matrix,mesh=prototype,regionPosition=set.LocalPosition(run.start+j),index=run.start+j});
                }
            }
            if(inputs.Count<4)throw new InvalidOperationException("No actual parked vehicle inputs");
            var examples=new Input[4];
            foreach(var input in inputs.Where(i=>i.prototype=="car_hatch_black"))
            {
                int level=Mathf.RoundToInt(Expected(input.matrix,rect)[0]*3);if(examples[level]==null)examples[level]=input;
            }
            if(examples.Any(i=>i==null))throw new InvalidOperationException("Actual same-prototype four-level coverage missing");
            var evidence=new Evidence{unity=Application.unityVersion,graphics=SystemInfo.graphicsDeviceType.ToString(),
                shaderSha256=Hash(source),instancesSha256=Hash(instancesPath),instanceCount=inputs.Count,cpuCounts=new int[4],gpuCounts=new int[4],
                method="Graphics.RenderMeshInstanced, same RenderParams/instance matrix path as WorldInstances.Flush; actual imported matrices, actual source vertex film function",
                note="Numeric diagnostic viewport/fragment adapter only, linear float RT without lighting/post. Full actual vehicle input coverage plus same-prototype LOD0/1/2 meshes and rebased inputs. Not performance or device proof."};
            evidence.examples=Enumerable.Range(0,4).Select(j=>new Example{prototype=examples[j].prototype,level=j,index=examples[j].index,
                e=examples[j].regionPosition.x,n=examples[j].regionPosition.z,z=examples[j].regionPosition.y,
                worldOrigin=examples[j].matrix.GetColumn(3)}).ToArray();
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
            var shader=BuildShader(source);var material=new Material(shader){enableInstancing=true};
            material.EnableKeyword("_CARPAINT");material.SetFloat("_Cull",(float)CullMode.Off);material.SetVector("_CarFlake",new Vector4(400,1,.08f,1));
            var quad=new Mesh();quad.vertices=new[]{new Vector3(-1,-1,0),new Vector3(1,-1,0),new Vector3(1,1,0),new Vector3(-1,1,0)};
            quad.normals=new[]{Vector3.back,Vector3.back,Vector3.back,Vector3.back};quad.uv=new[]{Vector2.zero,Vector2.right,Vector2.one,Vector2.up};quad.triangles=new[]{0,1,2,0,2,3};quad.RecalculateBounds();
            var go=new GameObject("G film numeric probe");var camera=go.AddComponent<Camera>();camera.enabled=false;camera.orthographic=true;
            camera.transform.position=new Vector3(0,0,-5000);camera.orthographicSize=5000;camera.nearClipPlane=.01f;camera.farClipPlane=20000;camera.clearFlags=CameraClearFlags.SolidColor;
            camera.backgroundColor=Color.magenta;camera.allowHDR=true;camera.allowMSAA=false;camera.cullingMask=~0;
            var extra=camera.GetUniversalAdditionalCameraData();extra.renderPostProcessing=false;extra.antialiasing=AntialiasingMode.None;extra.volumeLayerMask=0;
            var rt=new RenderTexture(64,16,24,RenderTextureFormat.ARGBFloat,RenderTextureReadWrite.Linear){filterMode=FilterMode.Point};rt.Create();camera.targetTexture=rt;
            var pixels=new Texture2D(64,16,TextureFormat.RGBAFloat,false,true);var batch=new Matrix4x4[4];var cases=new List<Case>();var samples=new List<InputSample>();
            try
            {
                for(int start=0;start<inputs.Count;start+=4)
                {
                    int count=Math.Min(4,inputs.Count-start);
                    for(int j=0;j<4;j++)batch[j]=inputs[start+Math.Min(j,count-1)].matrix;
                    var colors=Read(camera,rt,pixels,material,quad,batch,rect);
                    for(int j=0;j<count;j++)
                    {
                        var expected=Expected(batch[j],rect);int cpu=Mathf.RoundToInt(expected[0]*3),gpu=Mathf.RoundToInt(colors[j].r*3);
                        if(cpu!=gpu||Mathf.Abs(colors[j].g-expected[1])>.001f||colors[j].b>.001f)throw new InvalidOperationException("Actual instancing mismatch at input "+(start+j));
                        evidence.cpuCounts[cpu]++;evidence.gpuCounts[gpu]++;
                        samples.Add(new InputSample{prototype=inputs[start+j].prototype,nativeIndex=inputs[start+j].index,cpuLevel=cpu,gpuLevel=gpu,e=inputs[start+j].regionPosition.x,n=inputs[start+j].regionPosition.z,z=inputs[start+j].regionPosition.y});
                        evidence.maximumLevelError=Mathf.Max(evidence.maximumLevelError,Mathf.Abs(colors[j].r-expected[0]));
                    }
                }
                foreach(Vector3 shift in new[]{Vector3.zero,new Vector3(1024,0,0),new Vector3(-1024,0,1024),new Vector3(4096,0,-4096),new Vector3(-4096,0,4096),new Vector3(512.25f,0,-2048.75f)})
                for(int lod=0;lod<3;lod++)
                {
                    var movedRect=rect;movedRect.x+=shift.x;movedRect.y+=shift.z;
                    for(int j=0;j<4;j++){batch[j]=examples[j].matrix;batch[j].m03+=shift.x;batch[j].m13+=shift.y;batch[j].m23+=shift.z;}
                    var colors=Read(camera,rt,pixels,material,examples[0].mesh.lods[lod],batch,movedRect);
                    var record=new Case{label="actual-car_hatch_black-LOD"+lod,shift=shift,expected=new[]{0,1,2,3},actual=new int[4],phase=new float[4],pass=true};
                    for(int j=0;j<4;j++)
                    {
                        var expected=Expected(examples[j].matrix,rect);record.actual[j]=Mathf.RoundToInt(colors[j].r*3);record.phase[j]=colors[j].g;
                        record.pass&=record.actual[j]==j&&Mathf.Abs(colors[j].g-expected[1])<.001f&&colors[j].b<.001f;
                    }
                    cases.Add(record);if(!record.pass)throw new InvalidOperationException("Actual LOD/rebase instancing mismatch: "+record.label+" shift="+shift);
                }
                evidence.cases=cases.ToArray();evidence.perInstance=samples.ToArray();
                File.WriteAllText(Path.Combine(folder,"instanced-film-gpu-proof.json"),JsonUtility.ToJson(evidence,true));
                Debug.Log("G_FILM_GPU_RESULT: OK actualInstances="+inputs.Count+" cases="+cases.Count);
            }
            finally
            {
                camera.targetTexture=null;rt.Release();UnityEngine.Object.DestroyImmediate(rt);UnityEngine.Object.DestroyImmediate(pixels);
                UnityEngine.Object.DestroyImmediate(go);UnityEngine.Object.DestroyImmediate(quad);UnityEngine.Object.DestroyImmediate(material);
                s_KeepSet=null;
            }
        }
    }
}



