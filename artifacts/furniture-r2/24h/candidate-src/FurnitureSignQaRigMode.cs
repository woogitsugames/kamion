using System.Collections.Generic;
using Game.Vehicle.Runtime;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.World.Import
{
    /// <summary>Editor-only scoped fixture. Keeps the desired mode across scene reloads and
    /// binds it to real TruckLights before camera callbacks, never to a synthetic source.</summary>
    public static class FurnitureSignQaRigMode
    {
        static string s_Mode;
        static TruckLights s_Lamps;
        public static void Bind(string mode)
        {
            Unbind();s_Mode=mode;
            RenderPipelineManager.beginContextRendering+=Begin;
            Apply();
        }
        public static void Unbind()
        {
            RenderPipelineManager.beginContextRendering-=Begin;
            s_Lamps=null;
        }
        static void Begin(ScriptableRenderContext context,List<Camera> cameras) => Apply();
        static void Apply()
        {
            if(s_Lamps==null) s_Lamps=Object.FindAnyObjectByType<TruckLights>();
            if(s_Lamps==null) return;
            s_Lamps.forceLowBeam=true;
            s_Lamps.highBeam=s_Mode=="high";
            s_Lamps.enabled=s_Mode!="source-disabled";
            if(s_Lamps.enabled) s_Lamps.Refresh();
        }
    }
}
