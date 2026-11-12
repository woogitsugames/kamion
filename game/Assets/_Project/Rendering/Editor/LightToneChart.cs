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
    /// <summary>Tier tone-response diagnostic. Inputs are already exposed linear values, not physical lux.
    /// The chart uses the world's KamionTone on Low, and the real EnvironmentLighting post volume on High.
    /// It does not duplicate the tone curve or create a production pass/scene.</summary>
    public static class LightToneChart
    {
        [Serializable] sealed class Patch { public string id; public Vector3 input; public Vector2 centrePixel; }
        [Serializable] sealed class Proof
        {
            public string tier, preset;
            public string scope="Exposed-linear chart through actual tier shader toe and environment grading; no lighting/material/photometry fit.";
            public float modelExposure, skyHorizontalLux, renderScale, whiteClip, saturation;
            public bool postProcessing;
            public bool gradingVerified;
            public float actualSaturation, actualMasterAt01, requestedMasterAt01;
            public Vector4 shaderToe;
            public Vector4 expectedShaderToe;
            public Patch[] patches;
        }

        public static void Run()
        {
            int exit=1;
            try
            {
                var args=Environment.GetCommandLineArgs(); int at=Array.IndexOf(args,"-lightToneChartOut");
                if(at<0) throw new ArgumentException("Missing -lightToneChartOut");
                string output=args[at+1];Directory.CreateDirectory(output);
                float[] grey={0,0.0025f,0.01f,0.03f,0.09f,0.18f,0.33f,0.5f,0.7f,1,1.8f,2.5f};
                Vector3[] colours={new Vector3(.5f,0,0),new Vector3(0,.5f,0),new Vector3(0,0,.5f),new Vector3(.5f,.5f,0),
                    new Vector3(0,.5f,.5f),new Vector3(.5f,0,.5f),new Vector3(.05f,.18f,.03f),new Vector3(.08f,.08f,.08f),
                    new Vector3(1.2f,1.2f,1.2f),new Vector3(.8f,.3f,.08f),new Vector3(.08f,.25f,.5f),new Vector3(.18f,.12f,.07f)};
                int images=0;
                var renderToPixels=Type.GetType("Game.Editor.VisualQA.VisualQaRunner, Game.Editor",true)
                    .GetMethod("RenderToPixels",BindingFlags.NonPublic|BindingFlags.Static);
                if(renderToPixels==null)throw new MissingMethodException("VisualQaRunner.RenderToPixels");
                foreach(string lighting in new[]{"Clear","Overcast","Dusk","Night"})
                foreach(string tier in new[]{"Low","High"})
                {
                    EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
                    QualityTiers.Apply(tier);
                    var camera=new GameObject("tone chart view").AddComponent<Camera>();camera.tag="MainCamera";camera.enabled=false;
                    camera.transform.position=new Vector3(0,0,-10);camera.transform.rotation=Quaternion.identity;
                    camera.orthographic=true;camera.orthographicSize=2.2f;camera.aspect=3;
                    camera.nearClipPlane=.1f;camera.farClipPlane=30;camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=Color.black;
                    var applier=new GameObject("actual tier binding").AddComponent<QualityProfileApplier>();
                    applier.targetCamera=camera;applier.ApplyNow();
                    var preset=AssetDatabase.LoadAssetAtPath<LightingPreset>(LookDevAssets.LightingDir+"/LP_"+lighting+".asset");
                    if(preset==null) throw new InvalidOperationException("Missing preset "+lighting);
                    var host=new GameObject("actual environment");host.SetActive(false);
                    var env=host.AddComponent<EnvironmentLighting>();env.presets=new[]{preset};
                    env.skyMaterial=AssetDatabase.LoadAssetAtPath<Material>(LookDevAssets.SkyMaterial);
                    env.sun=new GameObject("chart sun").AddComponent<Light>();env.sun.type=LightType.Directional;
                    host.SetActive(true);env.Apply();
                    var shader=Shader.Find("Hidden/KamionLightQA/ToneChart");
                    if(shader==null)throw new InvalidOperationException("Missing chart shader");
                    var patches=new List<Patch>();
                    for(int row=0;row<2;row++) for(int col=0;col<12;col++)
                    {
                        Vector3 input=row==0?Vector3.one*grey[col]:colours[col];
                        var quad=GameObject.CreatePrimitive(PrimitiveType.Quad);
                        quad.transform.position=new Vector3((col-5.5f)*1.05f,row==0?.7f:-.7f,0);
                        var material=new Material(shader);material.SetVector("_LabLinear",new Vector4(input.x,input.y,input.z,1));
                        quad.GetComponent<Renderer>().sharedMaterial=material;
                        Vector3 view=camera.WorldToViewportPoint(quad.transform.position);
                        patches.Add(new Patch{id=(row==0?"grey-":"colour-")+col,input=input,centrePixel=new Vector2(view.x*1200,(1-view.y)*400)});
                    }
                    var profile=QualityProfileApplier.Current;
                    object[] renderArgs={camera,1200,400,0,null,profile.msaa,profile.renderScale};
                    // Exactly the existing world QA path: Camera.Render, actual scale/MSAA, sRGB target and upscale.
                    renderToPixels.Invoke(null,renderArgs);
                    var pixels=(Color32[])renderToPixels.Invoke(null,renderArgs);
                    var stack=camera.GetUniversalAdditionalCameraData().volumeStack??VolumeManager.instance.stack;
                    var actualCurves=stack.GetComponent<ColorCurves>();
                    var actualAdjustments=stack.GetComponent<ColorAdjustments>();
                    var look=env.GetComponentInChildren<Volume>();
                    if(look==null || !look.sharedProfile.TryGet(out ColorCurves requestedCurves))throw new InvalidOperationException("Missing actual environment look volume");
                    float actualMaster=actualCurves.master.value.Evaluate(.1f), requestedMaster=requestedCurves.master.value.Evaluate(.1f);
                    WorldAtmosphere.ResolveLook(preset,out float toe,out float toeP,out float pivot);
                    Vector4 expectedToe=profile.postProcessing || toe<=0f?Vector4.zero:new Vector4(toe,toeP,LookGrading.ToeGain(toe,toeP,pivot)-1f,0);
                    Vector4 actualToe=Shader.GetGlobalVector("_KamionTone");
                    bool actualPost=camera.GetUniversalAdditionalCameraData().renderPostProcessing;
                    bool verified=actualPost==profile.postProcessing && Vector4.Distance(actualToe,expectedToe)<.0001f &&
                        (!profile.postProcessing || (Mathf.Abs(actualMaster-requestedMaster)<.001f && Mathf.Abs(actualAdjustments.saturation.value-preset.lookSaturation)<.01f));
                    if(!verified)throw new InvalidOperationException($"Actual High grading not verified: master{actualMaster}/{requestedMaster}, saturation{actualAdjustments.saturation.value}/{preset.lookSaturation}");
                    var png=new Texture2D(1200,400,TextureFormat.RGB24,false);png.SetPixels32(pixels);png.Apply();
                    string stem=Path.Combine(output,tier+"-"+lighting);
                    File.WriteAllBytes(stem+".png",png.EncodeToPNG());
                    File.WriteAllText(stem+".json",JsonUtility.ToJson(new Proof{tier=tier,preset=lighting,
                        modelExposure=env.Model.Exposure,skyHorizontalLux=env.Model.HorizontalIlluminanceLux,renderScale=profile.renderScale,
                        postProcessing=actualPost,whiteClip=preset.lookWhiteClip,
                        saturation=preset.lookSaturation,shaderToe=actualToe,expectedShaderToe=expectedToe,gradingVerified=verified,
                        actualSaturation=actualAdjustments.saturation.value,actualMasterAt01=actualMaster,requestedMasterAt01=requestedMaster,patches=patches.ToArray()},true));
                    UnityEngine.Object.DestroyImmediate(png);images++;
                }
                Debug.Log($"LIGHT_TONE_CHART_RESULT: OK images={images}");exit=0;
            }
            catch(Exception ex){Debug.LogException(ex);Debug.Log("LIGHT_TONE_CHART_RESULT: FAILED");}
            finally{EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);}
            if(Application.isBatchMode)EditorApplication.Exit(exit);
        }
    }
}
