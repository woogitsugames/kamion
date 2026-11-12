using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
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
            public int renderWidth,renderHeight,renderSequence;
            public string exportedFile,exportedSha256;
        }
        [Serializable] sealed class Proof {
            public string scope="Editor display-camera-only pane contribution removal. No production/GPU or material-segmented fit claim.";
            public int collectedSlots,physicalCamerasObserved;public Frame[] frames;
        }
        readonly Material m_Neutral;
        readonly List<Slot> m_Slots=new List<Slot>();
        readonly Stack<CameraState> m_Stack=new Stack<CameraState>();
        readonly Dictionary<int,Frame> m_Frames=new Dictionary<int,Frame>();
        readonly Dictionary<string,Frame> m_Exports=new Dictionary<string,Frame>(StringComparer.Ordinal);
        readonly string m_Output;
        readonly int m_Width,m_Height;
        readonly DateTime m_Started=DateTime.UtcNow;
        Frame m_LastControlFrame;
        int m_Sequence;
        bool m_Active;
        int m_PhysicalObserved;
        string m_Error;
        public LightQaGlassIsolation(string output,int width,int height)
        {
            m_Output=Path.GetFullPath(output);m_Width=width;m_Height=height;
            var args=Environment.GetCommandLineArgs();int timing=Array.IndexOf(args,"-qaTimeFrames");
            if(timing>=0 && timing+1<args.Length && args[timing+1]!="0")
                throw new ArgumentException("Pane export proof requires timing renders disabled");
            var shader=Shader.Find(NeutralShader);
            if(shader==null)throw new InvalidOperationException("Missing explicit glass-isolation shader");
            m_Neutral=new Material(shader){hideFlags=HideFlags.HideAndDontSave,name="Editor-only absent pane"};
            EditorSceneManager.sceneOpened+=OnScene;
            RenderPipelineManager.beginCameraRendering+=OnBegin;
            RenderPipelineManager.endCameraRendering+=OnEnd;
            Application.logMessageReceived+=OnExportLog;
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
            if(control!=null){
                var target=camera.targetTexture;
                m_LastControlFrame=new Frame{camera=control.id,replacementSlots=ActualNeutralSlots(),
                    physicalBypass=Shader.GetGlobalFloat("_KamionSkyCapOff"),cloudQuality=Shader.GetGlobalVector("_KamionCloud").y,
                    renderWidth=target!=null?target.width:0,renderHeight=target!=null?target.height:0,renderSequence=++m_Sequence};
                m_Frames[camera.GetInstanceID()]=m_LastControlFrame;
            }
            if(m_Stack.Count==0 || m_Stack.Peek().camera!=camera){
                m_Error="Unbalanced nested camera lifetime";m_Stack.Clear();SetActive(false);return;
            }
            SetActive(m_Stack.Pop().previousActive);
        }
        void OnExportLog(string message,string trace,LogType type)
        {
            // The current runner writes PNG then logs this exact marker. Timing renders are rejected above;
            // mask renders follow the marker. The most recent ControlCamera end therefore belongs to the
            // exported world readback, rather than merely an earlier warm-up. Recheck this contract after merge.
            const string prefix="[VISUALQA] ";int arrow=message.IndexOf(" → ",StringComparison.Ordinal);
            if(!message.StartsWith(prefix,StringComparison.Ordinal) || arrow<prefix.Length)return;
            try{
                string id=message.Substring(prefix.Length,arrow-prefix.Length);
                string file=Path.GetFullPath(message.Substring(arrow+3));
                if(!string.Equals(Path.GetDirectoryName(file),m_Output,StringComparison.OrdinalIgnoreCase))return;
                var frame=m_LastControlFrame;
                float scale=QualityProfileApplier.HasCurrent?QualityProfileApplier.Current.renderScale:1f;
                if(Path.GetFileName(file)!=id+".png" || frame==null || frame.camera!=id ||
                   frame.renderWidth!=Mathf.Max(16,Mathf.RoundToInt(m_Width*scale)) ||
                   frame.renderHeight!=Mathf.Max(16,Mathf.RoundToInt(m_Height*scale)) ||
                   frame.physicalBypass!=0 || frame.replacementSlots!=m_Slots.Count ||
                   File.GetLastWriteTimeUtc(file)<m_Started || m_Exports.ContainsKey(id)){
                    m_Error="Export marker is not correlated with the actual isolated display readback";return;
                }
                using(var sha=SHA256.Create())using(var stream=File.OpenRead(file))
                    frame.exportedSha256=BitConverter.ToString(sha.ComputeHash(stream)).Replace("-",string.Empty);
                frame.exportedFile=file;m_Exports.Add(id,frame);
            }catch(Exception ex){m_Error="Pane export proof: "+ex.Message;}
        }
        public void Write(string folder,int expected)
        {
            if(m_Error!=null)throw new InvalidOperationException(m_Error);
            if(m_Stack.Count!=0 || m_Active || ActualNeutralSlots()!=0)throw new InvalidOperationException("Pane diagnostic was not restored after camera rendering");
            if(m_Slots.Count==0 || m_Exports.Count!=expected)throw new InvalidOperationException("Missing exported pane diagnostic camera/slot proof");
            foreach(var frame in m_Exports.Values)if(frame.replacementSlots!=m_Slots.Count || frame.physicalBypass!=0 || string.IsNullOrEmpty(frame.exportedSha256))
                throw new InvalidOperationException("Pane isolation absent in actual exported display camera");
            var frames=new Frame[m_Exports.Count];m_Exports.Values.CopyTo(frames,0);
            File.WriteAllText(Path.Combine(folder,"pane-isolation-proof.json"),JsonUtility.ToJson(new Proof{
                collectedSlots=m_Slots.Count,physicalCamerasObserved=m_PhysicalObserved,frames=frames},true));
        }
        public void Dispose()
        {
            RenderPipelineManager.beginCameraRendering-=OnBegin;
            RenderPipelineManager.endCameraRendering-=OnEnd;
            EditorSceneManager.sceneOpened-=OnScene;
            Application.logMessageReceived-=OnExportLog;
            SetActive(false);m_Stack.Clear();UnityEngine.Object.DestroyImmediate(m_Neutral);
        }
    }
}
