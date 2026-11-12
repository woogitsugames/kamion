Shader "Hidden/KamionLightQA/GradeLutLab"
{
    SubShader {
        Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" }
        Pass {
            Cull Off
            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "../Shaders/KamionAtmosphere.hlsl"
            TEXTURE2D(_LabInput); SAMPLER(sampler_LabInput);
            TEXTURE3D(_LabLut); SAMPLER(sampler_LabLut);
            float _LabUseLut, _LabLutSize, _LabNative;
            struct V {float3 p:POSITION;float2 uv:TEXCOORD0;};
            struct I {float4 p:SV_POSITION;float2 uv:TEXCOORD0;};
            I vert(V v){I o;o.p=TransformObjectToHClip(v.p);o.uv=v.uv;return o;}
            half4 frag(I i):SV_Target {
                float3 c=SAMPLE_TEXTURE2D_LOD(_LabInput,sampler_LabInput,i.uv,0).rgb;
                if(_LabUseLut>1.5)return half4(KamionOpaqueTone(c),1);
                if(_LabUseLut>.5){
                    // Square-root rational domain: fine sampling near black, finite coverage of HDR values.
                    float3 q;
                    if(_LabNative>.5)q=saturate(LinearToLogC(max((float3)KamionDimColour(c),0.0)));
                    else q=sqrt(saturate(c/(1.0+c)));
                    q=(q*(_LabLutSize-1.0)+.5)/_LabLutSize;
                    return half4(SAMPLE_TEXTURE3D_LOD(_LabLut,sampler_LabLut,q,0).rgb,1);
                }
                return half4(KamionTone(c),1);
            }
            ENDHLSL
        }
    }
}
