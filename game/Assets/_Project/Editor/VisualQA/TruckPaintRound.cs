using System;
using System.Collections.Generic;
using System.IO;
using Game.Editor.Build;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using Game.Rendering;

namespace Game.Editor.VisualQA
{
    public static class TruckPaintRound
    {
        public const string Cameras = "chase,truck-front,truck-34,truck-34r,truck-side,truck-rear34,truck-at-gate,trailer-34,trailer-side,cab-dash,cab-driver,cab-gate,cab-left,cab-right,cab-mirror-front,cab-mirrors-left,cab-mirrors-right";
        static bool noPane, noCoat;
        static string paneMode;
        static readonly List<(Renderer renderer,bool forced)> panes = new List<(Renderer,bool)>();
        static readonly List<(Material material,string json)> paints = new List<(Material,string)>();
        static void OnTier(QualityProfile.Tier ignored)
        {
            if (noCoat) Shader.SetGlobalFloat("_KamionClearCoatOff", 1f);
        }
        static void OnScene(Scene scene, OpenSceneMode mode)
        {
            if (!noPane) return;
            int count=0;
            foreach (var renderer in UnityEngine.Object.FindObjectsByType<MeshRenderer>(FindObjectsInactive.Include, FindObjectsSortMode.None))
                if (renderer.name.StartsWith(paneMode=="windscreen"?"GLASS_Windscreen":"GLASS_", StringComparison.Ordinal))
                {
                    panes.Add((renderer,renderer.forceRenderingOff));
                    // TruckVisualRig.Apply toggles enabled each camera. forceRenderingOff is independent.
                    renderer.forceRenderingOff=true; count++;
                }
            if (count==0) throw new InvalidOperationException("No cab panes found for actual no-pane reference");
            Debug.Log("TRUCK_NO_PANE: forceRenderingOff="+count+" (lamp lenses retained)");
        }
        static string Hash(string file)
        {
            using (var sha=System.Security.Cryptography.SHA256.Create())
                return BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes(file))).Replace("-","").ToLowerInvariant();
        }
        static Shader PaintDiagnostic(string original,string mode)
        {
            string source=File.ReadAllText(original);
            const string result="col.rgb = col.rgb * (1.0 - Fc) + env * Fc + direct;";
            if (!source.Contains(result)) throw new InvalidOperationException("Coat radiance expression changed; inspect actual shader before ablation");
            source=source.Replace("Shader \"Kamion/Truck Exterior\"","Shader \"Hidden/Kamion/TruckPaintDiagnostic_"+mode+"\"")
                .Replace("\"KamionVehicleEnv.hlsl\"","\"Assets/_Project/Rendering/Shaders/KamionVehicleEnv.hlsl\"")
                .Replace("\"KamionToeParity.hlsl\"","\"Assets/_Project/Rendering/Shaders/KamionToeParity.hlsl\"");
            if(mode=="radiance-off") source=source.Replace(result,"col.rgb = col.rgb * (1.0 - Fc);");
            else
            {
                source=source.Replace("if (coat > 0.001)","float3 debugFc=0, debugEnv=0; if (coat > 0.001)");
                source=source.Replace(result,@"debugFc=float3(Fc,NoV,coatRough);
                    float debugY=dot(env,float3(0.2126,0.7152,0.0722));
                    debugEnv=float3(debugY/(1.0+debugY),0.5+0.5*R.y,0.5+0.5*nWS.y);
                    "+result);
                string fields=mode=="mask"?"float3(coat,dirt,m.r)":mode=="fresnel"?"debugFc":mode=="env"?"debugEnv":throw new InvalidOperationException("Unknown paint diagnostic mode");
                source=source.Replace("return half4(col.rgb, 1);","return half4("+fields+",1);");
            }
            string target="Assets/_Generated/TruckPaintProbe/PaintDiagnostic_"+mode+".shader";
            string full=Path.Combine(EditorTools.ProjectRoot,target);
            Directory.CreateDirectory(Path.GetDirectoryName(full)); File.WriteAllText(full,source);
            AssetDatabase.ImportAsset(target,ImportAssetOptions.ForceSynchronousImport|ImportAssetOptions.ForceUpdate);
            var shader=AssetDatabase.LoadAssetAtPath<Shader>(target);
            if(shader==null||ShaderUtil.ShaderHasError(shader)) throw new InvalidOperationException("Coat radiance-only ablation shader failed");
            foreach(var guid in AssetDatabase.FindAssets("MI_Ext_Paint t:Material",new[]{"Assets/_Generated/Truck"}))
            {
                var material=AssetDatabase.LoadAssetAtPath<Material>(AssetDatabase.GUIDToAssetPath(guid));
                if(material==null||!material.HasProperty("_IsPaint")||material.GetFloat("_IsPaint")<0.5f) continue;
                paints.Add((material,EditorJsonUtility.ToJson(material))); material.shader=shader;
            }
            if(paints.Count!=3) throw new InvalidOperationException("Expected all3canonical paint materials, got "+paints.Count);
            return shader;
        }
        static Shader GlassDiagnostic(string mode)
        {
            string source=File.ReadAllText(Path.Combine(Application.dataPath,"_Project/Rendering/Shaders/TruckGlass.shader"));
            source=source.Replace("Shader \"Kamion/Truck Glass\"","Shader \"Hidden/Kamion/TruckGlassDiagnostic_"+mode+"\"")
                .Replace("\"KamionVehicleEnv.hlsl\"","\"Assets/_Project/Rendering/Shaders/KamionVehicleEnv.hlsl\"");
            bool nearOnly=mode=="near-transmission"||mode=="near-radiance-off";
            string fields=mode=="mask"?"float3(i.inside,glazing,hasFrame?1:0)":mode=="height"?"float3(saturate(h/5.0),NoV,F)":mode=="near-transmission"?"float3(trans,F,film)":mode=="near-radiance-off"?"float3(0,0,0)":throw new InvalidOperationException("Unknown glass probe");
            const string output="return half4(col, alpha);";
            if(!source.Contains(output))throw new InvalidOperationException("Glass output changed");
            source=source.Replace(output,"return half4("+fields+","+(mode=="near-radiance-off"?"alpha":"1")+");");
            string path="Assets/_Generated/TruckPaintProbe/GlassDiagnostic_"+mode+".shader";
            File.WriteAllText(Path.Combine(EditorTools.ProjectRoot,path),source);
            AssetDatabase.ImportAsset(path,ImportAssetOptions.ForceSynchronousImport|ImportAssetOptions.ForceUpdate);
            var shader=AssetDatabase.LoadAssetAtPath<Shader>(path);
            if(shader==null||ShaderUtil.ShaderHasError(shader))throw new InvalidOperationException("Glass diagnostic compile failed");
            foreach(var guid in AssetDatabase.FindAssets("t:Material",new[]{"Assets/_Generated/Truck"}))
            {
                var material=AssetDatabase.LoadAssetAtPath<Material>(AssetDatabase.GUIDToAssetPath(guid));
                if(material==null||material.shader==null||material.shader.name!="Kamion/Truck Glass"||(nearOnly&&material.name!="MI_Ext_Glass"))continue;
                paints.Add((material,EditorJsonUtility.ToJson(material))); material.shader=shader;
            }
            int expected=nearOnly?3:12;
            if(paints.Count!=expected)throw new InvalidOperationException("Expected"+expected+"cab/lens glass materials, got "+paints.Count);
            return shader;
        }

        public static void RunBatch()
        {
            string round=EditorTools.Arg("-truckRound","before"), cameras=EditorTools.Arg("-truckCameras",Cameras);
            paneMode=EditorTools.Arg("-truckNoPane","0"); noPane=paneMode=="1"||paneMode=="windscreen";
            noCoat=EditorTools.Arg("-truckCoatOff","0")=="1";
            bool radianceOff=EditorTools.Arg("-truckCoatRadianceOff","0")=="1";
            string meshProbe=EditorTools.Arg("-truckMeshProbe",null);
            bool paintDiagnostic=radianceOff||!string.IsNullOrEmpty(meshProbe);
            string glassProbe=EditorTools.Arg("-truckGlassProbe",null);
            if(paintDiagnostic&&!string.IsNullOrEmpty(glassProbe))throw new InvalidOperationException("Use separate paint/glass probe rounds");
            string production=Path.Combine(Application.dataPath,"_Project/Rendering/Shaders/TruckExterior.shader");
            string originalHash=Hash(production);
            float originalCoatOff=Shader.GetGlobalFloat("_KamionClearCoatOff");
            panes.Clear(); paints.Clear(); int total=0;
            try
            {
                Shader diagnostic=paintDiagnostic?PaintDiagnostic(production,radianceOff?"radiance-off":meshProbe):!string.IsNullOrEmpty(glassProbe)?GlassDiagnostic(glassProbe):null;
                EditorSceneManager.sceneOpened+=OnScene; QualityProfileApplier.Applied+=OnTier;
                foreach(string tier in EditorTools.Arg("-truckTiers","Low,High").Split(','))
                    foreach(string light in EditorTools.Arg("-truckLights","overcast,clear,lowsun").Split(','))
                    {
                        string target=Path.Combine(EditorTools.RepoRoot,"artifacts/truck-paint-r1",round,tier+"-"+light);
                        int count=VisualQaRunner.Render(tier=="High"?"WorldC_High":"WorldC",2340,1080,tier,target,light,cameras);
                        if(count!=cameras.Split(',').Length) throw new InvalidOperationException("Missing truck cameras "+target+" count="+count);
                        if(noPane)
                        {
                            int forced=0,enabled=0;
                            foreach(var pane in panes) if(pane.renderer!=null)
                            {
                                if(!pane.renderer.forceRenderingOff) throw new InvalidOperationException("Pane override lost after Apply: "+pane.renderer.name);
                                forced++; if(pane.renderer.enabled) enabled++;
                            }
                            if(forced==0) throw new InvalidOperationException("No live forced-off panes after render");
                            Debug.Log("TRUCK_NO_PANE_AFTER_RENDER: forcedOff="+forced+" enabled="+enabled);
                        }
                        if(paintDiagnostic||!string.IsNullOrEmpty(glassProbe))
                        {
                            foreach(var paint in paints) if(paint.material.shader!=diagnostic) throw new InvalidOperationException("Radiance ablation paint binding reset");
                            Debug.Log("TRUCK_COAT_RADIANCE_AFTER_RENDER: boundMaterials="+paints.Count);
                        }
                        if(EditorTools.Arg("-truckGlassAudit","0")=="1") TruckGlassAudit.Write(Path.Combine(target,"glass-mesh-audit.json"));
                        if(EditorTools.Arg("-truckEnvDirections","0")=="1") TruckPaintProbe.WriteEnvironmentDirections(Path.Combine(target,"environment-directions.json"));
                        total+=count; Debug.Log("TRUCK_ROUND_CONDITION: OK "+round+" "+tier+"-"+light+" count="+count);
                    }
            }
            finally
            {
                EditorSceneManager.sceneOpened-=OnScene; QualityProfileApplier.Applied-=OnTier;
                foreach(var pane in panes) if(pane.renderer!=null) pane.renderer.forceRenderingOff=pane.forced;
                foreach(var paint in paints) if(paint.material!=null)
                {
                    EditorJsonUtility.FromJsonOverwrite(paint.json,paint.material);
                    if(EditorJsonUtility.ToJson(paint.material)!=paint.json) throw new InvalidOperationException("Transient paint material restoration failed");
                }
                Shader.SetGlobalFloat("_KamionClearCoatOff",originalCoatOff);
                if(Hash(production)!=originalHash) throw new InvalidOperationException("Production shader changed during diagnostic");
                Debug.Log("TRUCK_ABLATION_CLEANUP: productionSHA="+originalHash+" restoredPaints="+paints.Count);
            }
            Debug.Log("TRUCK_ROUND_RESULT: OK "+round+" count="+total);
            if(Application.isBatchMode) EditorApplication.Exit(0);
        }
    }
}
