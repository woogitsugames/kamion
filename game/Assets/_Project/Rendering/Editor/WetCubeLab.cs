using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering.Editor
{
    /// <summary>Editor-only diagnostic, no saved scene or production reflection feature.
    /// Known wall at z8; exact ray-plane reflection is the reference, independent of the cube sampler.</summary>
    public static class WetCubeLab
    {
        public static void Run()
        {
            int exit = 1;
            bool originalPaused = VehicleReflectionCapture.Paused;
            try
            {
                string[] args = Environment.GetCommandLineArgs();
                int at = Array.IndexOf(args, "-wetCubeLabOut");
                string output = args[at+1]; Directory.CreateDirectory(output);
                int images = 0;
                foreach (string tier in new[] { "Low", "High" })
                {
                    EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                    RenderSettings.skybox = null;
                    QualityTiers.Apply(tier);
                    new GameObject("lab tier binding").AddComponent<QualityProfileApplier>().ApplyNow();
                    var unlit = Shader.Find("Universal Render Pipeline/Unlit");
                    var waterShader = Shader.Find("Hidden/KamionLightQA/WetCubeLab");
                    if (unlit == null || waterShader == null) throw new InvalidOperationException("Missing lab shaders");
                    GameObject Box(string name, Vector3 p, Vector3 scale, Color colour)
                    {
                        var go = GameObject.CreatePrimitive(PrimitiveType.Cube); go.name = name;
                        go.transform.position=p; go.transform.localScale=scale;
                        var mat = new Material(unlit); mat.SetColor("_BaseColor", colour);
                        go.GetComponent<Renderer>().sharedMaterial=mat; return go;
                    }
                    // Front faces all at z8. Distinct upper white / lower blue bands establish vertical orientation.
                    Box("known red wall", new Vector3(0,2,8.125f), new Vector3(4,4,0.25f), Color.red);
                    Box("upper white band", new Vector3(0,3.25f,7.98f), new Vector3(3,0.25f,0.02f), Color.white);
                    Box("lower blue band", new Vector3(0,1,7.98f), new Vector3(3,0.25f,0.02f), Color.blue);
                    var water=GameObject.CreatePrimitive(PrimitiveType.Plane); water.name="diagnostic mirror plane";
                    water.transform.localScale=new Vector3(4,1,4);
                    var renderer=water.GetComponent<Renderer>(); renderer.enabled=false;
                    var material=new Material(waterShader); renderer.sharedMaterial=material;
                    material.SetColor("_LabBackground",new Color(0.08f,0.12f,0.18f).linear);
                    var source=new GameObject("existing cube source").AddComponent<VehicleReflectionCapture>();
                    if (!source.Enabled) throw new InvalidOperationException("Lab tier did not enable the existing capture");
                    var cubeCamera=Resources.FindObjectsOfTypeAll<Camera>().Single(c=>c.name=="CaptureCamera" && c.transform.parent!=null && c.transform.parent.name=="VehicleReflectionCapture (runtime)");
                    cubeCamera.clearFlags=CameraClearFlags.SolidColor; cubeCamera.backgroundColor=new Color(0.08f,0.12f,0.18f);
                    source.RenderAllNow(); VehicleReflectionCapture.Paused=true;
                    if (!source.Enabled || source.FacesRendered<6) throw new InvalidOperationException("No complete existing cube");
                    Vector3 origin=cubeCamera.transform.position;
                    material.SetVector("_LabCaptureOrigin", new Vector4(origin.x,origin.y,origin.z,1));
                    source.DumpStrip(Path.Combine(output,tier+"-cube_envcube.png"));
                    renderer.enabled=true;
                    var camera=new GameObject("lab view").AddComponent<Camera>(); camera.enabled=false;
                    camera.clearFlags=CameraClearFlags.SolidColor; camera.backgroundColor=new Color(0.08f,0.12f,0.18f);
                    camera.fieldOfView=60; camera.nearClipPlane=0.1f; camera.farClipPlane=100; camera.allowHDR=false;
                    var data=camera.GetUniversalAdditionalCameraData(); data.renderPostProcessing=false; data.renderShadows=false;
                    var rt=new RenderTexture(1280,720,24,RenderTextureFormat.ARGB32); rt.Create();
                    foreach (int lateral in new[] {0,3})
                    {
                        camera.transform.position=new Vector3(lateral,2.2f,-6);
                        camera.transform.rotation=Quaternion.LookRotation(new Vector3(0,0.6f,5)-camera.transform.position,Vector3.up);
                        foreach(int mode in new[]{0,1,2,3})
                        {
                            material.SetFloat("_Mode",mode);
                            var request=new UniversalRenderPipeline.SingleCameraRequest {destination=rt};
                            if(!RenderPipeline.SupportsRenderRequest(camera,request)) throw new InvalidOperationException("Unsupported lab render request");
                            RenderPipeline.SubmitRenderRequest(camera,request);
                            var previous=RenderTexture.active; RenderTexture.active=rt;
                            var png=new Texture2D(1280,720,TextureFormat.RGB24,false);
                            png.ReadPixels(new Rect(0,0,1280,720),0,0); png.Apply(); RenderTexture.active=previous;
                            File.WriteAllBytes(Path.Combine(output,$"{tier}-x{lateral}-mode{mode}.png"),png.EncodeToPNG());
                            UnityEngine.Object.DestroyImmediate(png); images++;
                        }
                    }
                    File.WriteAllText(Path.Combine(output,tier+"-proof.txt"),$"tier={tier}; cube={source.Cube.width}; faces={source.FacesRendered}; source={origin}; cameraPositions=(0/3,2.2,-6); wallFrontZ=8; upperWhiteY=3.25; lowerBlueY=1; modes=0 exact ray-plane / 1 raw cube / 2 sphere20 / 3 known wall-plane parallax; shader mip=0; no production feature");
                    rt.Release(); UnityEngine.Object.DestroyImmediate(rt);
                }
                Debug.Log($"WET_CUBE_LAB_RESULT: OK images={images}"); exit=0;
            }
            catch(Exception ex) { Debug.LogException(ex); Debug.Log("WET_CUBE_LAB_RESULT: FAILED"); }
            finally { VehicleReflectionCapture.Paused=originalPaused; EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single); }
            if(Application.isBatchMode) EditorApplication.Exit(exit);
        }
    }
}
