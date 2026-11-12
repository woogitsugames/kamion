Shader "Hidden/KamionLightQA/ToneChart"
{
    Properties { _LabLinear ("Exposed linear input", Vector) = (0.18,0.18,0.18,1) }
    SubShader {
        Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" }
        Pass {
            Cull Off
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "../Shaders/KamionAtmosphere.hlsl"
            float4 _LabLinear;
            float4 vert(float3 p:POSITION):SV_POSITION { return TransformObjectToHClip(p); }
            half4 frag():SV_Target { return half4(KamionTone(_LabLinear.rgb),1); }
            ENDHLSL
        }
    }
}
