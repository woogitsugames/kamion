Shader "Hidden/KamionLightQA/WetCubeLab"
{
    Properties { _Mode ("Diagnostic mode", Float) = 0 }
    SubShader {
        Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" }
        Pass {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            TEXTURECUBE(_KamionVehicleEnvCube); SAMPLER(sampler_KamionVehicleEnvCube);
            float _Mode;
            float4 _LabCaptureOrigin;
            float4 _LabBackground;
            struct V { float3 p:POSITION; float3 n:NORMAL; };
            struct I { float4 p:SV_POSITION; float3 w:TEXCOORD0; float3 n:TEXCOORD1; };
            I vert(V v) { I o; o.w=TransformObjectToWorld(v.p); o.p=TransformWorldToHClip(o.w); o.n=TransformObjectToWorldNormal(v.n); return o; }
            half4 frag(I i):SV_Target {
                float3 R=reflect(-normalize(_WorldSpaceCameraPos-i.w),normalize(i.n));
                float t=(8.0-i.w.z)/max(R.z,0.0001);
                float3 hit=i.w+R*t;
                if (_Mode<0.5) {
                    half3 c=_LabBackground.rgb;
                    if(R.z>0 && t>0 && abs(hit.x)<2 && hit.y>0 && hit.y<4) {
                        c=half3(1,0,0);
                        if(abs(hit.y-3.25)<0.125 && abs(hit.x)<1.5) c=1;
                        if(abs(hit.y-1.0)<0.125 && abs(hit.x)<1.5) c=half3(0,0,1);
                    }
                    return half4(c,1);
                }
                float3 direction=R;
                if(_Mode>1.5 && _Mode<2.5) {
                    float3 offset=i.w-_LabCaptureOrigin.xyz;
                    float b=dot(offset,R);
                    float exit=-b+sqrt(max(b*b+400-dot(offset,offset),0));
                    direction=normalize(offset+R*exit);
                }
                if(_Mode>2.5) {
                    if(R.z<=0 || t<=0) return half4(_LabBackground.rgb,1);
                    direction=normalize(hit-_LabCaptureOrigin.xyz);
                }
                return half4(SAMPLE_TEXTURECUBE_LOD(_KamionVehicleEnvCube,sampler_KamionVehicleEnvCube,direction,0).rgb,1);
            }
            ENDHLSL
        }
    }
}
