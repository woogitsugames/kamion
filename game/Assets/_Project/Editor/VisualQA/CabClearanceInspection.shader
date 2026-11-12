Shader "Hidden/Kamion/Cab Clearance Inspection"
{
    Properties { _Color ("Part colour", Color) = (1,1,1,1) }
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" }
        Pass
        {
            Tags { "LightMode"="UniversalForward" }
            Cull Off ZWrite On
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            CBUFFER_START(UnityPerMaterial)
                float4 _Color;
            CBUFFER_END
            float4 _CabInspectOrigin, _CabInspectRight, _CabInspectUp, _CabInspectForward, _CabInspectMin, _CabInspectMax;
            struct A { float4 positionOS:POSITION; float3 normalOS:NORMAL; };
            struct V { float4 positionCS:SV_POSITION; float3 positionWS:TEXCOORD0; float3 normalWS:TEXCOORD1; };
            V Vert(A input)
            {
                V output;
                output.positionWS=TransformObjectToWorld(input.positionOS.xyz);
                output.positionCS=TransformWorldToHClip(output.positionWS);
                output.normalWS=TransformObjectToWorldNormal(input.normalOS);
                return output;
            }
            half4 Frag(V input):SV_Target
            {
                float3 d=input.positionWS-_CabInspectOrigin.xyz;
                float3 p=float3(dot(d,_CabInspectRight.xyz),dot(d,_CabInspectUp.xyz),dot(d,_CabInspectForward.xyz));
                clip(p-_CabInspectMin.xyz); clip(_CabInspectMax.xyz-p);
                float shade=.35+.65*saturate(dot(normalize(input.normalWS),normalize(float3(-.4,1,-.5))));
                return half4(_Color.rgb*shade,1);
            }
            ENDHLSL
        }
    }
}
