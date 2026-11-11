// Forest HLOD canopy (ADR 0113, QualityProfile.forestFast): the opaque crown shell of the merged forest cells (ADR 0015),
// drawn instead of URP Lit on the tiers with the forest fast path.
//
// Why: on the Galaxy A16 (Mali-G57 MC2, Low) the HLOD canopy costs 0.9 ms GPU (ADR 0106 A/B) with URP Lit at smoothness
// 0.05 - a full PBR fragment (per-pixel environment fetch, GGX, shadow-map fetch, additional-light loop) for a surface that
// is always > 70 m away (forestHlodM), beyond every tier's shadow distance.
//
// How: the same BRDF as URP Lit for a dielectric (metallic 0, specular highlights and environment reflections on, so the
// image matches the Lit material it replaces) with the terms that vary slowly over the smooth crown shell moved to the
// vertex: SH ambient (as URP's per-vertex SH mode), the glossy environment fetch at roughness 0.95 (mip ~6 of the sky
// cube: nearly constant over a crown) and Unity fog (URP Lit computes its fog factor per vertex too). Per pixel: albedo,
// Lambert + the GGX lobe of the sun, the Fresnel weight of the environment term. No realtime shadow (the HLOD is always
// past the shadow fade: forestHlodM 70 m > shadowDistance 35 / 60 m) and no additional lights (street lamps are emission
// only at the HLOD distance on Low; ADR 0113 notes).
// Properties match URP Lit (_BaseMap, _BaseColor, _Smoothness), so ForestFastPath copies a Lit material without re-authoring.
Shader "Kamion/Forest Canopy"
{
    Properties
    {
        _BaseMap ("Albedo", 2D) = "white" {}
        _BaseColor ("Color", Color) = (1, 1, 1, 1)
        _Smoothness ("Smoothness", Range(0, 1)) = 0.05
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" "IgnoreProjector" = "True" }

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_ST;
            half4 _BaseColor;
            half _Smoothness;
        CBUFFER_END
        TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            ZWrite On ZTest LEqual Cull Back
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            struct A { float4 positionOS : POSITION; float3 normalOS : NORMAL; float2 uv : TEXCOORD0; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct V
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 positionWS : TEXCOORD1;
                half3 normalWS : TEXCOORD2;
                half3 ambient : TEXCOORD3;       // SH(n) (URP bakedGI)
                half4 envFog : TEXCOORD4;        // rgb glossy environment radiance, a fog factor
                UNITY_VERTEX_OUTPUT_STEREO
            };
            V vert(A v)
            {
                V o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.positionWS = TransformObjectToWorld(v.positionOS.xyz);
                o.positionCS = TransformWorldToHClip(o.positionWS);
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap);
                half3 n = (half3)TransformObjectToWorldNormal(v.normalOS);
                o.normalWS = n;
                o.ambient = SampleSH(n);
                half3 V = (half3)GetWorldSpaceNormalizeViewDir(o.positionWS);
                half3 r = reflect(-V, n);
                o.envFog.rgb = GlossyEnvironmentReflection(r, 1.0h - _Smoothness, 1.0h);
                o.envFog.a = ComputeFogFactor(o.positionCS.z);
                return o;
            }
            half4 frag(V i) : SV_Target
            {
                half3 albedo = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv).rgb * _BaseColor.rgb;
                half3 n = normalize(i.normalWS);
                half3 V = (half3)GetWorldSpaceNormalizeViewDir(i.positionWS);
                // URP InitializeBRDFData, metallic 0.
                half oneMinusReflectivity = kDielectricSpec.a;
                half reflectivity = 1.0h - oneMinusReflectivity;
                half3 diffuse = albedo * oneMinusReflectivity;
                half3 specular = kDielectricSpec.rgb;
                half perceptualRoughness = 1.0h - _Smoothness;
                half roughness = max(perceptualRoughness * perceptualRoughness, HALF_MIN_SQRT);
                half roughness2 = max(roughness * roughness, HALF_MIN);
                half grazingTerm = saturate(_Smoothness + reflectivity);
                // URP GlobalIllumination + EnvironmentBRDF (environment radiance per vertex).
                half NoV = saturate(dot(n, V));
                half fresnelTerm = Pow4(1.0h - NoV);
                half surfaceReduction = 1.0h / (roughness2 + 1.0h);
                half3 color = i.ambient * diffuse + i.envFog.rgb * (surfaceReduction * lerp(specular, grazingTerm.xxx, fresnelTerm));
                // URP LightingPhysicallyBased + DirectBRDFSpecular, no shadow (always past the fade).
                Light L = GetMainLight();
                half NdotL = saturate(dot(n, L.direction));
                float3 H = SafeNormalize(float3(L.direction) + float3(V));
                half NoH = saturate(dot(float3(n), H));
                half LoH = saturate(dot(float3(L.direction), H));
                float d = NoH * NoH * (roughness2 - 1.0h) + 1.00001f;
                half specTerm = roughness2 / ((d * d) * max(0.1h, LoH * LoH) * (roughness * 4.0h + 2.0h));
            #if REAL_IS_HALF
                specTerm = clamp(specTerm - HALF_MIN, 0.0, 1000.0);
            #endif
                color += (diffuse + specular * specTerm) * (L.color * (L.distanceAttenuation * NdotL));
                color = MixFog(color, i.envFog.a);
                return half4(color, 1.0h);
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
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            struct A { float4 positionOS : POSITION; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct V { float4 positionCS : SV_POSITION; };
            V vert(A v) { UNITY_SETUP_INSTANCE_ID(v); V o; o.positionCS = TransformObjectToHClip(v.positionOS.xyz); return o; }
            half4 frag(V i) : SV_Target { return 0; }
            ENDHLSL
        }
    }
    FallBack Off
}
