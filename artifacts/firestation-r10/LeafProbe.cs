// Artifact-only QA. Temporarily compiled in ignored _Generated; never production importer/shader code.
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
public static class FireStationR7LeafProbe
{
    public static void Run()
    {
        string repo=Path.GetFullPath(Path.Combine(Application.dataPath,"../.."));
        string output=Path.Combine(repo,"artifacts/firestation-r10/leaf-probe/High-overcast");
        string asset="Assets/_Generated/World/bialystok-industrial-c/Materials/M_fire_station_thuja_shell.mat";
        Material mat=null;string before=null;int exit=1;
        Directory.CreateDirectory(output);
        try
        {
            mat=AssetDatabase.LoadAssetAtPath<Material>(asset);
            if(mat==null || mat.shader.name!="Universal Render Pipeline/Lit")throw new InvalidOperationException("Expected original hero URP Lit shell");
            before=EditorJsonUtility.ToJson(mat,true);File.WriteAllText(Path.Combine(output,"material-before.json"),before);
            Color tint=mat.GetColor("_BaseColor");Texture tex=mat.GetTexture("_BaseMap");
            float cutoff=mat.GetFloat("_Cutoff"),cull=mat.GetFloat("_Cull"),coverage=mat.GetFloat("_AlphaToMask");
            string[] oldPasses=Enumerable.Range(0,mat.passCount).Select(i=>mat.GetPassName(i)).ToArray();
            mat.shader=Shader.Find("Kamion/Vegetation");if(mat.shader==null)throw new InvalidOperationException("Vegetation shader missing");
            mat.shaderKeywords=new string[0];mat.EnableKeyword("_ALPHATEST_ON");
            mat.SetTexture("_BaseMap",tex);mat.SetColor("_BaseColor",tint);
            mat.SetFloat("_Cutoff",cutoff);mat.SetFloat("_Cull",cull);mat.SetFloat("_AlphaToMask",coverage);
            mat.SetFloat("_Transmission",.25f);mat.SetFloat("_CrownShade",0f);
            if(mat.HasProperty("_Wind"))mat.SetFloat("_Wind",0f); // Current shader contains no wind displacement.
            mat.renderQueue=2450;mat.enableInstancing=true;
            if(mat.GetTexture("_BaseMap")!=tex || Vector4.Distance(mat.GetColor("_BaseColor"),tint)>1e-6f)
                throw new InvalidOperationException("Alias texture/tint changed");
            File.WriteAllText(Path.Combine(output,"material-experiment.json"),EditorJsonUtility.ToJson(mat,true));
            File.WriteAllText(Path.Combine(output,"contract.txt"),
                "QA_ONLY_HIGH_HERO_SHELL\noldPassNames="+string.Join(",",oldPasses)+"\nnewPassNames="+
                string.Join(",",Enumerable.Range(0,mat.passCount).Select(i=>mat.GetPassName(i)))+
                "\nBaseMapPreserved=true\nBaseColorGammaPreserved="+tint+"\nBaseColorLinearEquivalent="+tint.linear+
                "\nCull="+cull+"\nCutoff="+cutoff+"\nAlphaToMask="+coverage+
                "\nTransmission=.25 CrownShade=0 Wind=0(no wind vertex motion in current shader)\n"+
                "One existing High material slot only, Low material unchanged. Vegetation adds SRPDefaultUnlit depth+Forward; drawsEst is NOT actual pass/GPU cost. PhoneGPU and temporal UNVERIFIED.\n");
            int count=Game.Editor.VisualQA.VisualQaRunner.Render("WorldC_High",2340,1080,"High",output,"overcast","fire-station-ref7197,fire-station-route");
            if(count!=2)throw new InvalidOperationException("Expected exactly2High frames");
            var field=typeof(Game.World.WorldInstances).GetField("m_Mats",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);
            var bindings=new System.Collections.Generic.List<string>();
            foreach(var world in UnityEngine.Object.FindObjectsByType<Game.World.WorldInstances>(FindObjectsSortMode.None))
            {
                var mats=field.GetValue(world) as Material[];if(mats==null)continue;
                foreach(var runtime in mats.Where(m=>m!=null && m.name.StartsWith("M_fire_station_thuja_shell")))
                {
                    bindings.Add(runtime.name+" shader="+runtime.shader.name+" BaseColor="+runtime.GetColor("_BaseColor")+
                        " CrownShade="+runtime.GetFloat("_CrownShade")+" Transmission="+runtime.GetFloat("_Transmission")+
                        " AlphaToMask="+runtime.GetFloat("_AlphaToMask"));
                    if(runtime.shader.name!="Kamion/Vegetation" || Vector4.Distance(runtime.GetColor("_BaseColor"),tint)>1e-6f)
                        throw new InvalidOperationException("Runtime shader/tint binding differs from QA source");
                }
            }
            bindings.Insert(0,"Runtime WorldInstances private material copies, inspected AFTER actual Render. Not a GPU uniform capture. Count="+bindings.Count);
            File.WriteAllLines(Path.Combine(output,"runtime-bindings.txt"),bindings);
            exit=0;Debug.Log("E_LEAF_PROBE_RESULT: OK rendered=2");
        }
        catch(Exception e){Debug.LogException(e);Debug.Log("E_LEAF_PROBE_RESULT: FAILED");}
        finally
        {
            if(mat!=null && before!=null)
            {
                EditorJsonUtility.FromJsonOverwrite(before,mat);EditorUtility.SetDirty(mat);AssetDatabase.SaveAssetIfDirty(mat);
                string restored=EditorJsonUtility.ToJson(mat,true);File.WriteAllText(Path.Combine(output,"material-restored.json"),restored);
                if(restored!=before){Debug.LogError("E_LEAF_RESTORE_JSON: DIFF; outer wrapper must restore exact YAML");exit=1;}
                else Debug.Log("E_LEAF_RESTORE_JSON: EXACT");
            }
        }
        if(Application.isBatchMode)EditorApplication.Exit(exit);
    }
}
