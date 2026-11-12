using System.Collections.Generic;
using Game.Vehicle.Runtime;
using UnityEngine;
using UnityEngine.Rendering;

namespace Game.World.Import
{
    /// <summary>Persisted ONLY on owned diagnostic scenes. Binds a desired mode to the real,
    /// possibly recreated TruckLights component; never publishes a synthetic light source.</summary>
    [ExecuteAlways]
    public sealed class FurnitureSignQaRigMode : MonoBehaviour
    {
        public string mode="low";
        TruckLights m_Lamps;
        void OnEnable()
        {
            m_Lamps=null;
            RenderPipelineManager.beginContextRendering+=Begin;
            Apply();
        }
        void OnDisable() => RenderPipelineManager.beginContextRendering-=Begin;
        void Begin(ScriptableRenderContext context,List<Camera> cameras) => Apply();
        public void Apply()
        {
            if(m_Lamps==null) m_Lamps=Object.FindAnyObjectByType<TruckLights>();
            if(m_Lamps==null) return;
            m_Lamps.forceLowBeam=true;
            m_Lamps.highBeam=mode=="high";
            m_Lamps.enabled=mode!="source-disabled";
            if(m_Lamps.enabled) m_Lamps.Refresh();
        }
    }
}
