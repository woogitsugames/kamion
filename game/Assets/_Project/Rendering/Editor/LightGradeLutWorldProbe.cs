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
            if(Shader.IsKeywordEnabled("_KAMION_OPAQUE_GRADE_LAB"))throw new InvalidOperationException("Prior grade probe keyword still enabled");
            if(size!=16 && size!=32)throw new ArgumentException("Reviewed sizes16/32 only");
            m_Key=JsonUtility.ToJson(JsonUtility.FromJson<Key>(File.ReadAllText(Path.Combine(folder,preset+"-key.json"))));
            var bytes=File.ReadAllBytes(Path.Combine(folder,$"{preset}-lut{size}-RGBAHalf.raw"));
            if(bytes.Length!=size*size*size*8)throw new InvalidDataException("LUT byte count");
            m_Lut=new Texture3D(size,size,size,TextureFormat.RGBAHalf,false){filterMode=FilterMode.Bilinear,wrapMode=TextureWrapMode.Clamp,name="Editor-only opaque look experiment"};
            m_Lut.SetPixelData(bytes,0);m_Lut.Apply(false,false);
        }
        float InverseGrey(float display)
        {
            float target=LookGrading.SrgbToLinear(display),lo=0,hi=4;
            for(int i=0;i<32;i++){
                float mid=(lo+hi)*.5f,q=Mathf.Sqrt(mid/(1+mid));
                q=(q*(m_Lut.width-1)+.5f)/m_Lut.width;
                var c=m_Lut.GetPixelBilinear(q,q,q);
                if(c.r*.2126f+c.g*.7152f+c.b*.0722f<target)lo=mid;else hi=mid;
            }
            return (lo+hi)*.5f;
        }
        public void Apply(Camera camera)
        {
            Shader.SetGlobalFloat("_KamionOpaqueGradeEnabled",0);
            if(!QualityProfileApplier.HasCurrent || QualityProfileApplier.Current.name!="Low" || QualityProfileApplier.Current.postProcessing){m_Error="LUT probe requires actual Low without post";return;}
            var env=EnvironmentLighting.Instance;
            if(env==null || env.Active==null){m_Error="Missing active environment";return;}
            var key=JsonUtility.ToJson(CaptureKey(env.Active));
            if(key!=m_Key){m_Error="Stale bake key: "+key+" expected "+m_Key;return;}
            Shader.SetGlobalTexture("_KamionOpaqueGradeLut",m_Lut);
            Shader.EnableKeyword("_KAMION_OPAQUE_GRADE_LAB");
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
            // Sky's compression must target the baked response instead of the legacy Low toe.
            Shader.SetGlobalVector("_KamionSkyCap",new Vector4(InverseGrey(EnvironmentLighting.SkyCapHorizonDisplay),InverseGrey(EnvironmentLighting.SkyCapZenithDisplay),1,0));
        }
        public void Observe(Camera camera)
        {
            var env=EnvironmentLighting.Instance;
            if(env!=null && env.Active!=null && camera.GetComponent<ControlCamera>()!=null)
                m_Frames[camera.GetInstanceID()]=new Frame{camera=camera.name,preset=env.Active.name,key=JsonUtility.ToJson(CaptureKey(env.Active)),
                    physicalCaptureBypass=Shader.GetGlobalFloat("_KamionSkyCapOff"),enabled=Shader.GetGlobalFloat("_KamionOpaqueGradeEnabled"),
                    cabToeParity=Shader.GetGlobalVector("_KamionToeParity")};
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
            Shader.DisableKeyword("_KAMION_OPAQUE_GRADE_LAB");
            Shader.SetGlobalFloat("_KamionOpaqueGradeSize",0);
            Shader.SetGlobalTexture("_KamionOpaqueGradeLut",null);
            UnityEngine.Object.DestroyImmediate(m_Lut);
            if(EnvironmentLighting.Instance!=null)EnvironmentLighting.Instance.Apply();
            if(m_HasSavedParity)Shader.SetGlobalVector("_KamionToeParity",m_ParityToRestore);
        }
    }
}
