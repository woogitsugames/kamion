// QA-only, no material mutation. Final HighOV hero matrix slice plus actual runtime material bindings.
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
public static class FireStationR7BindingCapture
{
    static string Arg(string key,string fallback)
    {
        var args=Environment.GetCommandLineArgs();int i=Array.IndexOf(args,key);
        return i>=0 && i+1<args.Length?args[i+1]:fallback;
    }
    public static void Run()
    {
        int exit=1;string repo=Path.GetFullPath(Path.Combine(Application.dataPath,"../.."));
        string tier=Arg("-eTier","High"),phase=Arg("-ePhase","round1-runtime");
        string output=Path.Combine(repo,"artifacts/firestation-r10",phase,tier+"-overcast");
        try
        {
            string sourcePath="Assets/_Generated/World/bialystok-industrial-c/Materials/M_fire_station_thuja_shell.mat";
            var source=AssetDatabase.LoadAssetAtPath<Material>(sourcePath);
            if(source==null || source.shader.name!="Universal Render Pipeline/Lit")throw new InvalidOperationException("Shared source must remain URP Lit");
            string sourceBefore=EditorJsonUtility.ToJson(source,true);Directory.CreateDirectory(output);
            File.WriteAllText(Path.Combine(output,"factory-material-before.json"),sourceBefore);
            int count=Game.Editor.VisualQA.VisualQaRunner.Render(tier=="High"?"WorldC_High":"WorldC",2340,1080,tier,output,"overcast",
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
                        " Transmission="+(mat.HasProperty("_Transmission")?mat.GetFloat("_Transmission").ToString():"N/A")+" CrownShade="+(mat.HasProperty("_CrownShade")?mat.GetFloat("_CrownShade").ToString():"N/A"));
                    if(tier=="High" && (mat.shader.name!="Kamion/Vegetation" || mat.GetFloat("_CrownShade")!=0f || mat.GetFloat("_Transmission")!=.25f))
                        throw new InvalidOperationException("High production runtime binding incorrect");
                    if(tier=="Low" && (mat.shader.name!="Universal Render Pipeline/Lit" || mat!=source))
                        throw new InvalidOperationException("Low must use original shared Lit material, including nearLOD0");
                    if(Vector4.Distance(mat.GetColor("_BaseColor"),source.GetColor("_BaseColor"))>1e-6f || mat.GetTexture("_BaseMap")!=source.GetTexture("_BaseMap"))
                        throw new InvalidOperationException("Runtime tint/texture altered");
                }
            }
            if(bindings.Count==0)throw new InvalidOperationException("No production hero runtime material found");
            bindings.Insert(0,"READONLY_FINAL_FACTORY_RUNTIME_BINDINGS activeTier="+Game.Rendering.QualityProfileApplier.Current.name+" after4actualframes. NotGPUuniform/timing capture. Count="+bindings.Count);
            File.WriteAllLines(Path.Combine(output,"runtime-bindings.txt"),bindings);
            string sourceAfter=EditorJsonUtility.ToJson(source,true);
            File.WriteAllText(Path.Combine(output,"factory-material-after.json"),sourceAfter);
            if(sourceAfter!=sourceBefore)throw new InvalidOperationException("Runtime mutated shared source material");
            Debug.Log("E_FINAL_BINDING_RESULT: OK rendered=4");exit=0;
        }
        catch(Exception e){Debug.LogException(e);Debug.Log("E_FINAL_BINDING_RESULT: FAILED");}
        if(Application.isBatchMode)EditorApplication.Exit(exit);
    }
}
