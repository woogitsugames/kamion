using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Game.Rendering.Editor
{
    /// <summary>Editor-only, explicitly requested opaque/sky experiment. No saved preset or player binding.
    /// Transparent premultiplied surfaces intentionally keep their original tone path.</summary>
    public sealed class LightGradeLutWorldProbe : IDisposable
    {
        [Serializable] public sealed class Key
        {
            public string unity,urp;
            public int revision=1,lutSize,gradingMode;
            public bool hdr;
            public float black,white,toe,toeP,pivot,saturation,highlightDesaturation,dimColour;
        }
        [Serializable] sealed class Frame
        {
            public string camera,preset,key;
            public float physicalCaptureBypass,enabled;
            public Vector4 cabToeParity;
            public Vector4 actualSkyCap;
        }
        [Serializable] sealed class Proof
        {
            public string scope="Editor-only opaque+sky grade. Transparent glass excluded. No GPU or whole-frame equivalence claim.";
            public int size;
            public Frame[] frames;
        }
        readonly Texture3D m_Lut;
        readonly string m_Key;
        readonly Dictionary<int,Frame> m_Frames=new Dictionary<int,Frame>();
        string m_Error;
        Vector4 m_ParityToRestore;
        bool m_HasSavedParity;
        public static Key CaptureKey(LightingPreset preset)
        {
            var pipeline=AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/_Project/Rendering/Settings/URP_High.asset");
            if(preset==null || pipeline==null)throw new InvalidOperationException("Missing look key inputs");
            WorldAtmosphere.ResolveLook(preset,out float toe,out float toeP,out float pivot);
            return new Key{unity=Application.unityVersion,urp=UnityEditor.PackageManager.PackageInfo.FindForAssembly(typeof(UniversalRenderPipelineAsset).Assembly)?.version??"unknown",
                lutSize=pipeline.colorGradingLutSize,gradingMode=(int)pipeline.colorGradingMode,hdr=pipeline.supportsHDR,
                black=preset.lookBlackLevel,white=preset.lookWhiteClip,toe=toe,toeP=toeP,pivot=pivot,saturation=preset.lookSaturation,
                highlightDesaturation=preset.lookHighlightDesaturation,dimColour=preset.dimColourDesaturation};
        }
        public LightGradeLutWorldProbe(string folder,string preset,int size)
        {
            if(size!=16 && size!=32)throw new ArgumentException("Reviewed sizes16/32 only");
            m_Key=JsonUtility.ToJson(JsonUtility.FromJson<Key>(File.ReadAllText(Path.Combine(folder,preset+"-key.json"))));
            var bytes=File.ReadAllBytes(Path.Combine(folder,$"{preset}-lut{size}-RGBAHalf.raw"));
            if(bytes.Length!=size*size*size*8)throw new InvalidDataException("LUT byte count");
            // The QA runner unloads unused assets while opening its scene. This managed diagnostic owner is
            // not a scene component; retain the transient texture explicitly until Dispose releases it.
            m_Lut=new Texture3D(size,size,size,TextureFormat.RGBAHalf,false){filterMode=FilterMode.Bilinear,wrapMode=TextureWrapMode.Clamp,
                hideFlags=HideFlags.HideAndDontSave,name="Editor-only opaque look experiment"};
            m_Lut.SetPixelData(bytes,0);m_Lut.Apply(false,false);
        }
        public void Apply(Camera camera)
        {
            Shader.SetGlobalFloat("_KamionOpaqueGradeEnabled",0);
            if(m_Lut==null){m_Error="Diagnostic LUT unloaded before rendering";return;}
            if(!QualityProfileApplier.HasCurrent || QualityProfileApplier.Current.name!="Low" || QualityProfileApplier.Current.postProcessing){m_Error="LUT probe requires actual Low without post";return;}
            var env=EnvironmentLighting.Instance;
            if(env==null || env.Active==null){m_Error="Missing active environment";return;}
            var key=JsonUtility.ToJson(CaptureKey(env.Active));
            if(key!=m_Key){m_Error="Stale bake key in "+camera.name+" ("+camera.cameraType+"): "+key+" expected "+m_Key;return;}
            Shader.SetGlobalTexture("_KamionOpaqueGradeLut",m_Lut);
            Shader.SetGlobalFloat("_KamionOpaqueGradeSize",m_Lut.width);
            Shader.SetGlobalFloat("_KamionOpaqueGradeEnabled",1);
            // Cab/exterior already have a Low-only approximate D23 curve before KamionMixFog.
            // Disable that approximation only for this diagnostic display camera, otherwise the full bake applies twice.
            // Physical captures retain the original globals and bypass the entire opaque LUT.
            if(Shader.GetGlobalFloat("_KamionSkyCapOff")<.5f)
            {
                m_ParityToRestore=Shader.GetGlobalVector("_KamionToeParity");
                m_HasSavedParity=true;
                Shader.SetGlobalVector("_KamionToeParity",Vector4.zero);
            }
            // Use the SAME input compression as actual High, whose response this LUT approximates.
            // Chasing .98 independently can exceed the sampled response and flatten photographic clouds.
            var caps=EnvironmentLighting.GradedSkyCaps(env.Active);
            Shader.SetGlobalVector("_KamionSkyCap",new Vector4(caps.x,caps.y,1,0));
        }
        public void Observe(Camera camera)
        {
            var env=EnvironmentLighting.Instance;
            if(env!=null && env.Active!=null && camera.GetComponent<ControlCamera>()!=null)
                m_Frames[camera.GetInstanceID()]=new Frame{camera=camera.name,preset=env.Active.name,key=JsonUtility.ToJson(CaptureKey(env.Active)),
                    physicalCaptureBypass=Shader.GetGlobalFloat("_KamionSkyCapOff"),enabled=Shader.GetGlobalFloat("_KamionOpaqueGradeEnabled"),
                    cabToeParity=Shader.GetGlobalVector("_KamionToeParity"),actualSkyCap=Shader.GetGlobalVector("_KamionSkyCap")};
        }
        public void Write(string folder,int expected)
        {
            if(m_Error!=null)throw new InvalidOperationException(m_Error);
            if(m_Frames.Count!=expected)throw new InvalidOperationException($"Missing grade proof cameras {m_Frames.Count}/{expected}");
            foreach(var frame in m_Frames.Values)if(frame.enabled!=1 || frame.physicalCaptureBypass!=0 || frame.cabToeParity!=Vector4.zero || frame.key!=m_Key)throw new InvalidOperationException("Grade absent, stale final key, double cab curve or physical capture bypass active in main camera");
            var frames=new Frame[m_Frames.Count];m_Frames.Values.CopyTo(frames,0);
            File.WriteAllText(Path.Combine(folder,"opaque-grade-proof.json"),JsonUtility.ToJson(new Proof{size=m_Lut.width,frames=frames},true));
        }
        public void Dispose()
        {
            Shader.SetGlobalFloat("_KamionOpaqueGradeEnabled",0);
            Shader.SetGlobalFloat("_KamionOpaqueGradeSize",0);
            Shader.SetGlobalTexture("_KamionOpaqueGradeLut",null);
            UnityEngine.Object.DestroyImmediate(m_Lut);
            if(EnvironmentLighting.Instance!=null)EnvironmentLighting.Instance.Apply();
            if(m_HasSavedParity)Shader.SetGlobalVector("_KamionToeParity",m_ParityToRestore);
        }
    }
}
