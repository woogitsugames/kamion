using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering.Editor
{
    /// <summary>Editor-only actual-High bake and independent Low holdout. No runtime feature, saved scene or new product pass.
    /// The LUT includes the selected preset's shader presentation and actual High grading. It must not be applied twice.</summary>
    public static class LightGradeLutLab
    {
        [Serializable] sealed class Sample {public string id;public Vector3 input;public Color32 reference,output;}
        [Serializable] sealed class Measurement {public string name;public int size;public float meanAbsoluteRgb,maxRgb;public Sample[] samples;}
        [Serializable] sealed class Proof
        {
            public string preset,scope="Diagnostic only. Actual High response baked into RGBAHalf3D, Low sample in a lab shader. No production feature or GPU budget claim.";
            public string domain="q=sqrt(c/(1+c)); texel centre=(q*(N-1)+0.5)/N; inverse c=q²/(1-q²), last input clamped at9999";
            public float exposure,dimColour,actualHighMaster,requestedMaster,actualHighSaturation;
            public Measurement[] measurements;
        }
        static MethodInfo s_Render;
        static Material s_Material;
        static Camera s_Camera;
        static EnvironmentLighting s_Environment;
        static QualityProfileApplier s_Applier;

        static void SelectTier(string name)
        {
            QualityTiers.Apply(name);s_Applier.ApplyNow();s_Environment.Apply();
            if(s_Camera.GetUniversalAdditionalCameraData().renderPostProcessing!=(name=="High"))throw new InvalidOperationException("Wrong actual chart camera post state");
        }
        static Color32[] Render(Color[] values,int columns,int rows,int cellPixels,bool useLut,Texture3D lut=null)
        {
            var map=new Texture2D(columns,rows,TextureFormat.RGBAFloat,false,true){filterMode=FilterMode.Point,wrapMode=TextureWrapMode.Clamp};
            var padded=new Color[columns*rows];Array.Copy(values,padded,values.Length);map.SetPixels(padded);map.Apply();
            s_Material.SetTexture("_LabInput",map);s_Material.SetFloat("_LabUseLut",useLut?1:0);
            s_Material.SetTexture("_LabLut",lut);s_Material.SetFloat("_LabLutSize",lut!=null?lut.width:1);
            int width=columns*cellPixels,height=rows*cellPixels;
            s_Camera.aspect=(float)width/height;
            // Keep cell centres away from RCAS edges.
            var surface=GameObject.Find("grade lab input plane");surface.transform.localScale=new Vector3(2*s_Camera.aspect,2,1);
            var tier=QualityProfileApplier.Current;
            object[] args={s_Camera,width,height,0,null,tier.msaa,tier.renderScale};
            try{s_Render.Invoke(null,args);return (Color32[])s_Render.Invoke(null,args);}
            finally{UnityEngine.Object.DestroyImmediate(map);}
        }
        static Color32[] Centres(Color32[] pixels,int count,int columns,int cellPixels)
        {
            int width=columns*cellPixels;var values=new Color32[count];
            for(int i=0;i<count;i++)values[i]=pixels[(i/columns*cellPixels+cellPixels/2)*width+i%columns*cellPixels+cellPixels/2];
            return values;
        }
        static void SaveImage(string path,Color32[] pixels,int width,int height)
        {
            var tex=new Texture2D(width,height,TextureFormat.RGB24,false);tex.SetPixels32(pixels);tex.Apply();
            File.WriteAllBytes(path,tex.EncodeToPNG());UnityEngine.Object.DestroyImmediate(tex);
        }
        static Measurement Measure(string name,int size,Color[] inputs,Color32[] reference,Color32[] output)
        {
            float sum=0,max=0;var samples=new Sample[inputs.Length];
            for(int i=0;i<inputs.Length;i++){
                int r=Math.Abs(reference[i].r-output[i].r),g=Math.Abs(reference[i].g-output[i].g),b=Math.Abs(reference[i].b-output[i].b);
                sum+=r+g+b;max=Mathf.Max(max,Mathf.Max(r,Mathf.Max(g,b)));
                samples[i]=new Sample{id=i<64?"grey-"+i:"holdout-"+i,input=new Vector3(inputs[i].r,inputs[i].g,inputs[i].b),reference=reference[i],output=output[i]};
            }
            return new Measurement{name=name,size=size,meanAbsoluteRgb=sum/(inputs.Length*3),maxRgb=max,samples=samples};
        }
        public static void Run()
        {
            int exit=1;
            try{
                var args=Environment.GetCommandLineArgs();int at=Array.IndexOf(args,"-lightGradeLabOut");
                if(at<0)throw new ArgumentException("Missing -lightGradeLabOut");string folder=args[at+1];Directory.CreateDirectory(folder);
                s_Render=Type.GetType("Game.Editor.VisualQA.VisualQaRunner, Game.Editor",true).GetMethod("RenderToPixels",BindingFlags.NonPublic|BindingFlags.Static);
                if(s_Render==null)throw new MissingMethodException("World QA render path");
                var inputs=new Color[192];
                for(int i=0;i<64;i++){float v=i<32?(i==0?0:Mathf.Pow(10,-4f+(i-1)*3.2552725f/30f)):.18f+(i-32)*1.82f/31f;inputs[i]=new Color(v,v,v,1);}
                var random=new System.Random(10805);
                for(int i=64;i<inputs.Length;i++){float range=i<96?.04f:1.8f;inputs[i]=new Color((float)random.NextDouble()*range,(float)random.NextDouble()*range,(float)random.NextDouble()*range,1);}
                int imageCount=0;
                foreach(string presetName in new[]{"Clear","Overcast","Night"}){
                    EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
                    s_Camera=new GameObject("grade lab view").AddComponent<Camera>();s_Camera.tag="MainCamera";s_Camera.enabled=false;
                    s_Camera.orthographic=true;s_Camera.orthographicSize=1;s_Camera.transform.position=new Vector3(0,0,-10);
                    s_Camera.clearFlags=CameraClearFlags.SolidColor;s_Camera.backgroundColor=Color.black;s_Camera.nearClipPlane=.1f;s_Camera.farClipPlane=20;
                    QualityTiers.Apply("High");s_Applier=new GameObject("actual tier").AddComponent<QualityProfileApplier>();s_Applier.targetCamera=s_Camera;s_Applier.ApplyNow();
                    var preset=AssetDatabase.LoadAssetAtPath<LightingPreset>(LookDevAssets.LightingDir+"/LP_"+presetName+".asset");
                    if(preset==null)throw new InvalidOperationException("Missing real preset");
                    var host=new GameObject("actual environment");host.SetActive(false);s_Environment=host.AddComponent<EnvironmentLighting>();
                    s_Environment.presets=new[]{preset};host.SetActive(true);s_Environment.Apply();
                    var shader=Shader.Find("Hidden/KamionLightQA/GradeLutLab");if(shader==null)throw new InvalidOperationException("Missing lab shader");
                    s_Material=new Material(shader);var plane=GameObject.CreatePrimitive(PrimitiveType.Quad);plane.name="grade lab input plane";plane.GetComponent<Renderer>().sharedMaterial=s_Material;
                    SelectTier("High");
                    if(Shader.GetGlobalFloat("_KamionSkyCapOff")>.5f)throw new InvalidOperationException("Physical capture bypass unexpectedly active");
                    var highPixels=Render(inputs,16,12,32,false);var reference=Centres(highPixels,inputs.Length,16,32);
                    SaveImage(Path.Combine(folder,presetName+"-High-reference.png"),highPixels,512,384);imageCount++;
                    var stack=s_Camera.GetUniversalAdditionalCameraData().volumeStack??VolumeManager.instance.stack;
                    var curves=stack.GetComponent<ColorCurves>();var adjustment=stack.GetComponent<ColorAdjustments>();
                    var volume=s_Environment.GetComponentInChildren<Volume>();
                    if(volume==null || !volume.sharedProfile.TryGet(out ColorCurves requested))throw new InvalidOperationException("No requested look volume");
                    float actual=curves.master.value.Evaluate(.1f),wanted=requested.master.value.Evaluate(.1f);
                    if(Mathf.Abs(actual-wanted)>.001f || Mathf.Abs(adjustment.saturation.value-preset.lookSaturation)>.01f)throw new InvalidOperationException("High grading stack mismatch");
                    var cubes=new List<Texture3D>();
                    foreach(int size in new[]{16,32}){
                        int count=size*size*size,columns=Mathf.CeilToInt(Mathf.Sqrt(count)),rows=Mathf.CeilToInt((float)count/columns);
                        var grid=new Color[count];
                        float Expand(int k){float q=(float)k/(size-1);q=Mathf.Min(q*q,.9999f);return q/(1-q);}
                        for(int z=0;z<size;z++)for(int y=0;y<size;y++)for(int x=0;x<size;x++)grid[x+size*(y+size*z)]=new Color(Expand(x),Expand(y),Expand(z),1);
                        var pixels=Render(grid,columns,rows,8,false);var cells=Centres(pixels,count,columns,8);var colours=new Color[count];
                        for(int i=0;i<count;i++){colours[i]=((Color)cells[i]).linear;colours[i].a=1;}
                        var cube=new Texture3D(size,size,size,TextureFormat.RGBAHalf,false){filterMode=FilterMode.Bilinear,wrapMode=TextureWrapMode.Clamp,name=presetName+"-actualHigh-"+size};
                        cube.SetPixels(colours);cube.Apply(false,false);cubes.Add(cube);
                        File.WriteAllBytes(Path.Combine(folder,$"{presetName}-lut{size}-RGBAHalf.raw"),cube.GetPixelData<byte>(0).ToArray());
                    }
                    SelectTier("Low");var measurements=new List<Measurement>();
                    var low=Render(inputs,16,12,32,false);SaveImage(Path.Combine(folder,presetName+"-Low-baseline.png"),low,512,384);imageCount++;
                    measurements.Add(Measure("Low baseline",0,inputs,reference,Centres(low,inputs.Length,16,32)));
                    foreach(var cube in cubes){var pixels=Render(inputs,16,12,32,true,cube);SaveImage(Path.Combine(folder,$"{presetName}-Low-lut{cube.width}.png"),pixels,512,384);imageCount++;
                        measurements.Add(Measure("Low lab LUT",cube.width,inputs,reference,Centres(pixels,inputs.Length,16,32)));}
                    File.WriteAllText(Path.Combine(folder,presetName+"-proof.json"),JsonUtility.ToJson(new Proof{preset=presetName,exposure=s_Environment.Model.Exposure,dimColour=preset.dimColourDesaturation,
                        actualHighMaster=actual,requestedMaster=wanted,actualHighSaturation=adjustment.saturation.value,measurements=measurements.ToArray()},true));
                    foreach(var cube in cubes)UnityEngine.Object.DestroyImmediate(cube);UnityEngine.Object.DestroyImmediate(s_Material);
                }
                Debug.Log($"LIGHT_GRADE_LAB_RESULT: OK images={imageCount} cubes=6 holdoutPerPreset=192");exit=0;
            }catch(Exception ex){Debug.LogException(ex);Debug.Log("LIGHT_GRADE_LAB_RESULT: FAILED");}
            finally{EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);}
            if(Application.isBatchMode)EditorApplication.Exit(exit);
        }
    }
}

