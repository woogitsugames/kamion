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
        static Shader CoatRadianceOff(string original)
        {
            string source=File.ReadAllText(original);
            const string result="col.rgb = col.rgb * (1.0 - Fc) + env * Fc + direct;";
            if (!source.Contains(result)) throw new InvalidOperationException("Coat radiance expression changed; inspect actual shader before ablation");
            source=source.Replace("Shader \"Kamion/Truck Exterior\"","Shader \"Hidden/Kamion/TruckCoatRadianceOff\"")
                .Replace(result,"col.rgb = col.rgb * (1.0 - Fc); // diagnostic: radiance only off, base roughness/attenuation intact")
                .Replace("\"KamionVehicleEnv.hlsl\"","\"Assets/_Project/Rendering/Shaders/KamionVehicleEnv.hlsl\"")
                .Replace("\"KamionToeParity.hlsl\"","\"Assets/_Project/Rendering/Shaders/KamionToeParity.hlsl\"");
            const string target="Assets/_Generated/TruckPaintProbe/CoatRadianceOff.shader";
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
        public static void RunBatch()
        {
            string round=EditorTools.Arg("-truckRound","before"), cameras=EditorTools.Arg("-truckCameras",Cameras);
            paneMode=EditorTools.Arg("-truckNoPane","0"); noPane=paneMode=="1"||paneMode=="windscreen";
            noCoat=EditorTools.Arg("-truckCoatOff","0")=="1";
            bool radianceOff=EditorTools.Arg("-truckCoatRadianceOff","0")=="1";
            string production=Path.Combine(Application.dataPath,"_Project/Rendering/Shaders/TruckExterior.shader");
            string originalHash=Hash(production);
            float originalCoatOff=Shader.GetGlobalFloat("_KamionClearCoatOff");
            panes.Clear(); paints.Clear(); int total=0;
            try
            {
                Shader diagnostic=radianceOff?CoatRadianceOff(production):null;
                EditorSceneManager.sceneOpened+=OnScene; QualityProfileApplier.Applied+=OnTier;
                foreach(string tier in new[]{"Low","High"})
                    foreach(string light in new[]{"overcast","clear","lowsun"})
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
                        if(radianceOff)
                        {
                            foreach(var paint in paints) if(paint.material.shader!=diagnostic) throw new InvalidOperationException("Radiance ablation paint binding reset");
                            Debug.Log("TRUCK_COAT_RADIANCE_AFTER_RENDER: boundMaterials="+paints.Count);
                        }
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
