// QA-only, no material mutation. Final HighOV hero matrix slice plus actual runtime material bindings.
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
public static class FireStationR7BindingCapture
{
    public static void Run()
    {
        int exit=1;string repo=Path.GetFullPath(Path.Combine(Application.dataPath,"../.."));
        string output=Path.Combine(repo,"artifacts/firestation-r10/round1/High-overcast");
        try
        {
            int count=Game.Editor.VisualQA.VisualQaRunner.Render("WorldC_High",2340,1080,"High",output,"overcast",
                "fire-station-ref7197,fire-station-route,fire-station-abeam,fire-station-above");
            if(count!=4)throw new InvalidOperationException("Expected4hero cameras");
            var field=typeof(Game.World.WorldInstances).GetField("m_Mats",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);
            var bindings=new System.Collections.Generic.List<string>();
            foreach(var world in UnityEngine.Object.FindObjectsByType<Game.World.WorldInstances>(FindObjectsSortMode.None))
            {
                var mats=field.GetValue(world) as Material[];if(mats==null)continue;
                foreach(var mat in mats.Where(m=>m!=null && m.name.StartsWith("M_fire_station_thuja_shell")))
                {
                    bindings.Add(mat.name+" shader="+mat.shader.name+" gammaBaseColor="+mat.GetColor("_BaseColor")+
                        " linearEquivalent="+mat.GetColor("_BaseColor").linear+" BaseMap="+mat.GetTexture("_BaseMap").name+
                        " Cull="+mat.GetFloat("_Cull")+" Cutoff="+mat.GetFloat("_Cutoff")+" AlphaToMask="+mat.GetFloat("_AlphaToMask")+
                        " Transmission="+mat.GetFloat("_Transmission")+" CrownShade="+mat.GetFloat("_CrownShade"));
                    if(mat.shader.name!="Kamion/Vegetation" || mat.GetFloat("_CrownShade")!=0f || mat.GetFloat("_Transmission")!=.25f)
                        throw new InvalidOperationException("Production runtime binding incorrect");
                }
            }
            if(bindings.Count==0)throw new InvalidOperationException("No production hero runtime material found");
            bindings.Insert(0,"READONLY_FINAL_FACTORY_RUNTIME_BINDINGS after4actualframes. NotGPUuniform/timing capture. Count="+bindings.Count);
            File.WriteAllLines(Path.Combine(output,"runtime-bindings.txt"),bindings);
            string path="Assets/_Generated/World/bialystok-industrial-c/Materials/M_fire_station_thuja_shell.mat";
            var asset=AssetDatabase.LoadAssetAtPath<Material>(path);
            File.WriteAllText(Path.Combine(output,"factory-material.json"),EditorJsonUtility.ToJson(asset,true));
            Debug.Log("E_FINAL_BINDING_RESULT: OK rendered=4");exit=0;
        }
        catch(Exception e){Debug.LogException(e);Debug.Log("E_FINAL_BINDING_RESULT: FAILED");}
        if(Application.isBatchMode)EditorApplication.Exit(exit);
    }
}
