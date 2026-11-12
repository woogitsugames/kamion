using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

namespace Game.Rendering.Editor
{
    /// <summary>UNCOMPILED candidate for round6. Diagnostic display-camera-only removal of Truck Glass contribution.
    /// Never writes a renderer asset or alters the owner's shader. Physical captures retain their original materials.</summary>
    public sealed class LightQaGlassIsolation : IDisposable
    {
        const string SourceShader="Kamion/Truck Glass", NeutralShader="Hidden/KamionLightQA/AbsentPane";
        sealed class Slot {public Renderer renderer;public int index;public Material original;}
        struct CameraState {public Camera camera;public bool previousActive;}
        [Serializable] public sealed class Frame {
            public string camera;public int replacementSlots;public float physicalBypass,cloudQuality;
        }
        [Serializable] sealed class Proof {
            public string scope="Editor display-camera-only pane contribution removal. No production/GPU or material-segmented fit claim.";
            public int collectedSlots,physicalCamerasObserved;public Frame[] frames;
        }
        readonly Material m_Neutral;
        readonly List<Slot> m_Slots=new List<Slot>();
        readonly Stack<CameraState> m_Stack=new Stack<CameraState>();
        readonly Dictionary<int,Frame> m_Frames=new Dictionary<int,Frame>();
        bool m_Active;
        int m_PhysicalObserved;
        string m_Error;
        public LightQaGlassIsolation()
        {
            var shader=Shader.Find(NeutralShader);
            if(shader==null)throw new InvalidOperationException("Missing explicit glass-isolation shader");
            m_Neutral=new Material(shader){hideFlags=HideFlags.HideAndDontSave,name="Editor-only absent pane"};
            EditorSceneManager.sceneOpened+=OnScene;
            RenderPipelineManager.beginCameraRendering+=OnBegin;
            RenderPipelineManager.endCameraRendering+=OnEnd;
        }
        void OnScene(Scene scene,OpenSceneMode mode)
        {
            SetActive(false);
            if(m_Stack.Count!=0){m_Error="Scene changed inside active camera rendering";m_Stack.Clear();}
            m_Slots.Clear();
            foreach(var root in scene.GetRootGameObjects())foreach(var renderer in root.GetComponentsInChildren<Renderer>(true)){
                var materials=renderer.sharedMaterials;
                for(int i=0;i<materials.Length;i++)if(materials[i]!=null && materials[i].shader!=null && materials[i].shader.name==SourceShader)
                    m_Slots.Add(new Slot{renderer=renderer,index=i,original=materials[i]});
            }
            if(m_Slots.Count==0)m_Error="No actual Truck Glass material slots in the opened QA scene";
        }
        void SetActive(bool requested)
        {
            if(m_Active==requested)return;
            foreach(var slot in m_Slots){
                if(slot.renderer==null)continue;
                var materials=slot.renderer.sharedMaterials;
                if(slot.index>=materials.Length){m_Error="Renderer material layout changed during diagnostic";continue;}
                var current=materials[slot.index];
                if(requested){
                    if(current!=slot.original && current!=m_Neutral){m_Error="Source pane slot changed externally";continue;}
                    materials[slot.index]=m_Neutral;
                }else{
                    if(current==m_Neutral)materials[slot.index]=slot.original;
                    else if(current!=slot.original){m_Error="Diagnostic pane slot changed externally";continue;}
                }
                slot.renderer.sharedMaterials=materials;
            }
            m_Active=requested;
        }
        int ActualNeutralSlots()
        {
            int count=0;
            foreach(var slot in m_Slots)if(slot.renderer!=null){
                var materials=slot.renderer.sharedMaterials;
                if(slot.index<materials.Length && materials[slot.index]==m_Neutral)count++;
            }
            return count;
        }
        void OnBegin(ScriptableRenderContext context,Camera camera)
        {
            bool physical=Shader.GetGlobalFloat("_KamionSkyCapOff")>.5f;
            bool display=camera!=null && camera.GetComponent<ControlCamera>()!=null && !physical;
            m_Stack.Push(new CameraState{camera=camera,previousActive=m_Active});
            SetActive(display);
            if(physical){m_PhysicalObserved++;if(ActualNeutralSlots()!=0)m_Error="Pane diagnostic leaked into physical capture";}
        }
        void OnEnd(ScriptableRenderContext context,Camera camera)
        {
            var control=camera!=null?camera.GetComponent<ControlCamera>():null;
            if(control!=null && Shader.GetGlobalFloat("_KamionSkyCapOff")<.5f){
                m_Frames[camera.GetInstanceID()]=new Frame{camera=control.id,replacementSlots=ActualNeutralSlots(),
                    physicalBypass=Shader.GetGlobalFloat("_KamionSkyCapOff"),cloudQuality=Shader.GetGlobalVector("_KamionCloud").y};
            }
            if(m_Stack.Count==0 || m_Stack.Peek().camera!=camera){
                m_Error="Unbalanced nested camera lifetime";m_Stack.Clear();SetActive(false);return;
            }
            SetActive(m_Stack.Pop().previousActive);
        }
        public void Write(string folder,int expected)
        {
            if(m_Error!=null)throw new InvalidOperationException(m_Error);
            if(m_Stack.Count!=0 || m_Active || ActualNeutralSlots()!=0)throw new InvalidOperationException("Pane diagnostic was not restored after camera rendering");
            if(m_Slots.Count==0 || m_Frames.Count!=expected)throw new InvalidOperationException("Missing pane diagnostic camera/slot proof");
            foreach(var frame in m_Frames.Values)if(frame.replacementSlots!=m_Slots.Count || frame.physicalBypass!=0)
                throw new InvalidOperationException("Pane isolation absent in actual exported display camera");
            var frames=new Frame[m_Frames.Count];m_Frames.Values.CopyTo(frames,0);
            File.WriteAllText(Path.Combine(folder,"pane-isolation-proof.json"),JsonUtility.ToJson(new Proof{
                collectedSlots=m_Slots.Count,physicalCamerasObserved=m_PhysicalObserved,frames=frames},true));
        }
        public void Dispose()
        {
            RenderPipelineManager.beginCameraRendering-=OnBegin;
            RenderPipelineManager.endCameraRendering-=OnEnd;
            EditorSceneManager.sceneOpened-=OnScene;
            SetActive(false);m_Stack.Clear();UnityEngine.Object.DestroyImmediate(m_Neutral);
        }
    }
}
