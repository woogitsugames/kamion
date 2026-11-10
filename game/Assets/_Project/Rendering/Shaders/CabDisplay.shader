// TRAKT cab displays (12.3" cluster, infotainment, tachograph, radio; review r3 C1): a backlit LCD behind its cover glass.
// - Emission only, black base: no detail / wear / perforation / AO masks of the cab plastics, no ambient, no fog.
// - Display value = screen texture × clamp(_Luminance [cd/m^2] × _KamionExposure, _MinDisplay, _MaxDisplay). The scene
//   exposure makes it follow the light like a real panel at dusk, the floor keeps it readable in direct sun (a real
//   cluster is hard to read there; a game instrument must not be), the cap avoids a glowing slab at night.
//   Texture black (~0.02) stays black: contrast = texture contrast (≥ 8:1 target), nothing is added on top.
// - Cover-glass reflection: a weak Fresnel term from the environment (F0 0.04, smooth), no grime.
Shader "Kamion/Cab Display"
{
    Properties
    {
        _BaseMap ("Screen (sRGB)", 2D) = "black" {}
        _Luminance ("Panel luminance at full white (cd/m^2)", Float) = 500
        _MinDisplay ("Readability floor (exposed value of full white)", Float) = 0.45
        _MaxDisplay ("Cap (exposed value of full white)", Float) = 0.9
        _Reflection ("Cover glass reflection scale", Range(0, 1)) = 1
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" }

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_ST;
            float _Luminance, _MinDisplay, _MaxDisplay, _Reflection;
        CBUFFER_END
        ENDHLSL

        Pass
        {
            Name "Display"
            Tags { "LightMode" = "UniversalForward" }
            Cull Back ZWrite On
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "KamionToeParity.hlsl"
            TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
            float _KamionExposure;
            struct A { float4 positionOS : POSITION; float3 normalOS : NORMAL; float2 uv : TEXCOORD0; };
            struct V { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; float3 positionWS : TEXCOORD1; half3 normalWS : TEXCOORD2; };
            V vert(A v)
            {
                V o;
                o.positionWS = TransformObjectToWorld(v.positionOS.xyz);
                o.positionCS = TransformWorldToHClip(o.positionWS);
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap);
                return o;
            }
            half4 frag(V i) : SV_Target
            {
                half3 screen = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv).rgb;
                float k = _KamionExposure > 0.0 ? _KamionExposure : 1e-3;
                half gain = clamp(_Luminance * k, _MinDisplay, _MaxDisplay);
                half3 n = normalize(i.normalWS);
                float3 Vd = GetWorldSpaceNormalizeViewDir(i.positionWS);
                half NoV = saturate(dot(n, Vd));
                half fresnel = 0.04 + 0.96 * Pow4(1.0 - NoV) * (1.0 - NoV);
                half3 env = GlossyEnvironmentReflection(reflect(-Vd, n), 0.05, 1.0) * fresnel * _Reflection;
                return half4(KamionCabToeInverse(KamionToeParity(screen * gain + env), _KamionCabToeInvDisplay), 1.0);   // D23 toe without the LUT (cab view, ADR 0044 r7)
            }
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode" = "DepthOnly" }
            ZWrite On ColorMask R Cull Back
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex DepthVert
            #pragma fragment DepthFrag
            struct A { float4 positionOS : POSITION; };
            struct V { float4 positionCS : SV_POSITION; };
            V DepthVert(A v) { V o; o.positionCS = TransformObjectToHClip(v.positionOS.xyz); return o; }
            half4 DepthFrag(V i) : SV_Target { return 0; }
            ENDHLSL
        }
    }
    Fallback Off
}
