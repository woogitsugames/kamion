using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;
using UnityEngine.Rendering.RenderGraphModule.Util;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering.Editor
{
    /// <summary>Editor-only copy of URP's actual High internal LogC LUT, before its transient graph resource expires.
    /// Temporarily attaches to renderer instances, never renderer-data assets. No player/Low render pass.</summary>
    public sealed class LightNativeGradeLutCapture : IDisposable
    {
        [Serializable] public sealed class CopyState
        {
            public bool hdrEnabled;
            public string cameraFormat,lutFormat;
            public int gradingMode;
        }
        [Serializable] public sealed class CopyStates {public CopyState[] states;}
        readonly List<CopyState> m_States=new List<CopyState>();
        static readonly PropertyInfo s_Features=typeof(ScriptableRenderer).GetProperty("rendererFeatures",BindingFlags.Instance|BindingFlags.NonPublic);
        readonly Camera m_Camera;
        readonly int m_Size;
        readonly RenderTexture m_Copy;
        readonly RTHandle m_Handle;
        readonly CaptureFeature m_Feature;
        readonly HashSet<ScriptableRenderer> m_Renderers=new HashSet<ScriptableRenderer>();
        string m_Error;
        public int RecordedCopies {get;private set;}
        public string SourceFormat {get;private set;}
        public string StateJson => JsonUtility.ToJson(new CopyStates{states=m_States.ToArray()},true);

        public LightNativeGradeLutCapture(Camera camera,int size)
        {
            if(camera==null || size!=32 || s_Features==null)throw new ArgumentException("Expected actual High32 capture context");
            m_Camera=camera;m_Size=size;
            m_Copy=new RenderTexture(size*size,size,0,RenderTextureFormat.ARGBHalf,RenderTextureReadWrite.Linear){
                name="Editor-only actual High grading LUT copy",hideFlags=HideFlags.HideAndDontSave,
                filterMode=FilterMode.Point,wrapMode=TextureWrapMode.Clamp,useMipMap=false,antiAliasing=1};
            m_Copy.Create();m_Handle=RTHandles.Alloc(m_Copy);
            m_Feature=ScriptableObject.CreateInstance<CaptureFeature>();m_Feature.hideFlags=HideFlags.HideAndDontSave;
            m_Feature.owner=this;m_Feature.Create();
            RenderPipelineManager.beginCameraRendering+=OnBegin;
        }
        void OnBegin(ScriptableRenderContext context,Camera camera)
        {
            if(camera!=m_Camera)return;
            var data=camera.GetUniversalAdditionalCameraData();
            if(!data.renderPostProcessing || !QualityProfileApplier.HasCurrent || QualityProfileApplier.Current.name!="High"){
                m_Error="Native LUT copy requires actual High with post";return;
            }
            var renderer=data.scriptableRenderer;
            var features=(List<ScriptableRendererFeature>)s_Features.GetValue(renderer);
            if(!features.Contains(m_Feature))features.Add(m_Feature);
            m_Renderers.Add(renderer);
        }
        public Texture3D ReadCube()
        {
            if(m_Error!=null || RecordedCopies==0)throw new InvalidOperationException(m_Error??"Native grading LUT pass never recorded");
            var previous=RenderTexture.active;
            var read=new Texture2D(m_Size*m_Size,m_Size,TextureFormat.RGBAHalf,false,true){hideFlags=HideFlags.HideAndDontSave};
            try{
                RenderTexture.active=m_Copy;read.ReadPixels(new Rect(0,0,m_Copy.width,m_Copy.height),0,0,false);read.Apply(false,false);
                var strip=read.GetPixels();var values=new Color[m_Size*m_Size*m_Size];
                // URP strip layout: R inside each N-wide block, G on rows, B selects the horizontal block.
                for(int z=0;z<m_Size;z++)for(int y=0;y<m_Size;y++)for(int x=0;x<m_Size;x++)
                    values[x+m_Size*(y+m_Size*z)]=strip[x+m_Size*z+m_Size*m_Size*y];
                var cube=new Texture3D(m_Size,m_Size,m_Size,TextureFormat.RGBAHalf,false){
                    name="Editor-only native High LogC LUT",hideFlags=HideFlags.HideAndDontSave,
                    filterMode=FilterMode.Bilinear,wrapMode=TextureWrapMode.Clamp};
                cube.SetPixels(values);cube.Apply(false,false);return cube;
            }finally{RenderTexture.active=previous;UnityEngine.Object.DestroyImmediate(read);}
        }
        public void Dispose()
        {
            RenderPipelineManager.beginCameraRendering-=OnBegin;
            foreach(var renderer in m_Renderers){
                var features=(List<ScriptableRendererFeature>)s_Features.GetValue(renderer);features.Remove(m_Feature);
            }
            m_Feature.Dispose();UnityEngine.Object.DestroyImmediate(m_Feature);
            m_Handle.Release();m_Copy.Release();UnityEngine.Object.DestroyImmediate(m_Copy);
        }

        public sealed class CaptureFeature : ScriptableRendererFeature
        {
            internal LightNativeGradeLutCapture owner;
            CopyPass m_Pass;
            public override void Create(){m_Pass=new CopyPass(owner);}
            public override void AddRenderPasses(ScriptableRenderer renderer,ref RenderingData renderingData)
            {
                if(owner!=null && renderingData.cameraData.camera==owner.m_Camera)renderer.EnqueuePass(m_Pass);
            }
        }
        sealed class CopyPass : ScriptableRenderPass
        {
            readonly LightNativeGradeLutCapture m_Owner;
            public CopyPass(LightNativeGradeLutCapture owner){m_Owner=owner;renderPassEvent=RenderPassEvent.AfterRenderingPostProcessing;}
            public override void RecordRenderGraph(RenderGraph graph,ContextContainer frameData)
            {
                if(m_Owner==null)return;
                var camera=frameData.Get<UniversalCameraData>();
                if(camera.camera!=m_Owner.m_Camera)return;
                var source=frameData.Get<UniversalResourceData>().internalColorLut;
                if(!source.IsValid()){m_Owner.m_Error="Actual High internalColorLut missing";return;}
                var info=graph.GetRenderTargetInfo(source);
                if(info.width!=m_Owner.m_Size*m_Owner.m_Size || info.height!=m_Owner.m_Size){
                    m_Owner.m_Error=$"Unexpected native LUT dimensions {info.width}x{info.height}";return;
                }
                m_Owner.SourceFormat=info.format.ToString();
                m_Owner.m_States.Add(new CopyState{hdrEnabled=camera.isHdrEnabled,cameraFormat=camera.cameraTargetDescriptor.graphicsFormat.ToString(),
                    lutFormat=info.format.ToString(),gradingMode=(int)frameData.Get<UniversalPostProcessingData>().gradingMode});
                var destination=graph.ImportTexture(m_Owner.m_Handle);
                graph.AddBlitPass(source,destination,Vector2.one,Vector2.zero,filterMode:RenderGraphUtils.BlitFilterMode.ClampNearest,
                    passName:"Editor-only copy actual High grading LUT");
                m_Owner.RecordedCopies++;
            }
        }
    }
}
