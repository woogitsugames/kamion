using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using UnityEngine;
using UnityEngine.Experimental.Rendering;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering.Editor
{
    /// <summary>Explicit Editor High reference: retain HDR opaque values in the intermediate before post, while the
    /// existing QA runner still resolves into its ARGB32 target. Does not alter assets, player code or Low.</summary>
    public sealed class LightHdrQaReference : IDisposable
    {
        [Serializable] public sealed class Frame
        {
            public string camera,targetFormat,descriptorFormat,colorBeforePostFormat;
            public bool hdrEnabled,postEnabled;
        }
        [Serializable] sealed class Proof {public string scope="Editor High pre-post format diagnostic. No Low/player pass.";public bool forceHdr;public Frame[] frames;}
        static readonly PropertyInfo s_Features=typeof(ScriptableRenderer).GetProperty("rendererFeatures",BindingFlags.Instance|BindingFlags.NonPublic);
        readonly Camera m_Target;
        readonly bool m_ForceHdr;
        readonly Feature m_Feature;
        readonly HashSet<ScriptableRenderer> m_Renderers=new HashSet<ScriptableRenderer>();
        readonly Dictionary<int,Frame> m_Frames=new Dictionary<int,Frame>();
        string m_Error;
        bool Matches(Camera camera)=>camera!=null && (m_Target!=null?camera==m_Target:camera.GetComponent<ControlCamera>()!=null);
        public LightHdrQaReference(Camera target=null,bool forceHdr=true)
        {
            if(s_Features==null)throw new MissingMemberException("Actual renderer feature list");
            m_Target=target;m_ForceHdr=forceHdr;m_Feature=ScriptableObject.CreateInstance<Feature>();m_Feature.hideFlags=HideFlags.HideAndDontSave;
            m_Feature.owner=this;m_Feature.Create();RenderPipelineManager.beginCameraRendering+=OnBegin;
        }
        void OnBegin(ScriptableRenderContext context,Camera camera)
        {
            if(!Matches(camera))return;
            var data=camera.GetUniversalAdditionalCameraData();
            if(!data.renderPostProcessing || !QualityProfileApplier.HasCurrent || QualityProfileApplier.Current.name!="High"){
                m_Error="HDR reference requires actual High post camera";return;
            }
            var renderer=data.scriptableRenderer;
            var features=(List<ScriptableRendererFeature>)s_Features.GetValue(renderer);
            if(!features.Contains(m_Feature))features.Add(m_Feature);m_Renderers.Add(renderer);
        }
        public string GetProof(int expected)
        {
            if(m_Error!=null)throw new InvalidOperationException(m_Error);
            if(m_Frames.Count!=expected)throw new InvalidOperationException($"HDR camera proof incomplete {m_Frames.Count}/{expected}");
            foreach(var f in m_Frames.Values)if(!f.hdrEnabled || !f.postEnabled || (m_ForceHdr && (f.descriptorFormat!="R16G16B16A16_SFloat" || f.colorBeforePostFormat!="R16G16B16A16_SFloat")))
                throw new InvalidOperationException("HDR reference did not retain actual half-float color before post");
            var frames=new Frame[m_Frames.Count];m_Frames.Values.CopyTo(frames,0);return JsonUtility.ToJson(new Proof{forceHdr=m_ForceHdr,frames=frames},true);
        }
        public void Write(string folder,int expected)=>File.WriteAllText(Path.Combine(folder,"hdr-reference-proof.json"),GetProof(expected));
        public void Dispose()
        {
            RenderPipelineManager.beginCameraRendering-=OnBegin;
            foreach(var renderer in m_Renderers)((List<ScriptableRendererFeature>)s_Features.GetValue(renderer)).Remove(m_Feature);
            m_Feature.Dispose();UnityEngine.Object.DestroyImmediate(m_Feature);
        }
        public sealed class Feature : ScriptableRendererFeature
        {
            internal LightHdrQaReference owner;
            ReferencePass m_Pass;
            public override void Create(){if(owner!=null)m_Pass=new ReferencePass(owner);}
            public override void OnCameraPreCull(ScriptableRenderer renderer,in CameraData cameraData)
            {
                if(owner==null || !owner.Matches(cameraData.camera))return;
                // This is a ref-return property backed by UniversalCameraData in this URP version.
                if(owner.m_ForceHdr)cameraData.cameraTargetDescriptor.graphicsFormat=GraphicsFormat.R16G16B16A16_SFloat;
            }
            public override void AddRenderPasses(ScriptableRenderer renderer,ref RenderingData renderingData)
            {
                if(owner!=null && owner.Matches(renderingData.cameraData.camera))renderer.EnqueuePass(m_Pass);
            }
        }
        sealed class ReferencePass : ScriptableRenderPass
        {
            readonly LightHdrQaReference m_Owner;
            public ReferencePass(LightHdrQaReference owner){m_Owner=owner;renderPassEvent=RenderPassEvent.BeforeRenderingPostProcessing;requiresIntermediateTexture=owner.m_ForceHdr;}
            public override void RecordRenderGraph(RenderGraph graph,ContextContainer frameData)
            {
                var camera=frameData.Get<UniversalCameraData>();if(m_Owner==null || !m_Owner.Matches(camera.camera))return;
                var resources=frameData.Get<UniversalResourceData>();
                var color=resources.activeColorTexture;
                if(!color.IsValid()){m_Owner.m_Error="HDR reference missing pre-post color";return;}
                var control=camera.camera.GetComponent<ControlCamera>();
                m_Owner.m_Frames[camera.camera.GetInstanceID()]=new Frame{camera=control!=null?control.id:camera.camera.name,
                    hdrEnabled=camera.isHdrEnabled,postEnabled=camera.camera.GetUniversalAdditionalCameraData().renderPostProcessing,
                    targetFormat=camera.camera.targetTexture!=null?camera.camera.targetTexture.graphicsFormat.ToString():"backbuffer",
                    descriptorFormat=camera.cameraTargetDescriptor.graphicsFormat.ToString(),colorBeforePostFormat=graph.GetRenderTargetInfo(color).format.ToString()};
                // Introspection only. No blit, draw, texture copy or extra full-screen effect is recorded here.
            }
        }
    }
}
