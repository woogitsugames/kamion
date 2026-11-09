// Leaf cards and tree impostors on the Low/Medium tiers (QualityProfile.simpleFoliage; ADR 0013).
//
// Why: the DK8 forest control camera on the Galaxy A16 (Mali-G57 MC2) is fragment bound - GPU 61 ms on Medium, 18 ms
// with the trees off, and the cost scales with render scale (device ablation 2026-11-09). URP Lit with alpha clip shades
// every overlapping card (discard disables early depth kill on a tiled GPU) with full PBR (GGX, reflection probe,
// cascaded shadow lookup).
//
// How:
// 1. Depth pass (LightMode SRPDefaultUnlit, drawn before UniversalForward for the same draw): alpha test or
//    alpha-to-coverage, depth only. The only pass with discard; its fragment is one texture fetch.
// 2. Colour pass (UniversalForward): ZWrite Off, ZTest LEqual with a small depth offset - hidden card layers fail the
//    early depth test against pass 1 before shading (a shader that clips but does not write depth keeps early-Z on a
//    tiled GPU), so the lighting runs about once per visible pixel instead of once per overlapping card. Same clip /
//    coverage as pass 1, so the alpha-to-coverage edge under MSAA is kept.
// 3. Lighting: Lambert with the sun's shadow, a small transmission term for back-lit leaves (thin leaf, ~25% of the
//    diffuse, WORKING_VALUE), L2 SH ambient, fog. No specular lobe and no reflection probe: leaf specular at the URP
//    Lit smoothness 0.25 is a few % of the diffuse and the probe fetch was the costliest part of the old fragment.
// Material properties match URP Lit (_BaseMap, _BaseColor, _Cutoff, _Cull, _AlphaToMask), so a Lit material can be
// switched to this shader at runtime without re-authoring.
Shader "Kamion/Vegetation"
{
    Properties
    {
        _BaseMap ("Albedo (RGB) alpha (A)", 2D) = "white" {}
        _BaseColor ("Color", Color) = (1, 1, 1, 1)
        _Cutoff ("Alpha cutoff", Range(0, 1)) = 0.5
        _Transmission ("Back-lit transmission", Range(0, 1)) = 0.25
        [Enum(UnityEngine.Rendering.CullMode)] _Cull ("Cull", Float) = 0
        [Toggle] _AlphaToMask ("Alpha to coverage", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType" = "TransparentCutout" "RenderPipeline" = "UniversalPipeline" "Queue" = "AlphaTest" "IgnoreProjector" = "True" }

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_ST;
            half4 _BaseColor;
            half _Cutoff;
            half _Transmission;
            half _Cull;
            half _AlphaToMask;
        CBUFFER_END
        TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);

        // Shared by the depth and colour passes (same transform, so the depths agree to within the colour pass offset).
        float4 VegClipPos(float3 positionOS) { return TransformWorldToHClip(TransformObjectToWorld(positionOS)); }

        // Alpha-to-coverage edge: alpha sharpened to ~1 pixel around the cutoff (as URP Lit's SharpenAlpha).
        half CoverageAlpha(half a)
        {
            return saturate((a - _Cutoff) / max(fwidth(a), 0.0001) + 0.5);
        }
        ENDHLSL

        Pass
        {
            Name "VegetationDepth"
            Tags { "LightMode" = "SRPDefaultUnlit" }
            ZWrite On ZTest LEqual ColorMask 0 Cull [_Cull]
            AlphaToMask [_AlphaToMask]
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            struct A { float4 positionOS : POSITION; float2 uv : TEXCOORD0; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct V { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; UNITY_VERTEX_OUTPUT_STEREO };
            V vert(A v)
            {
                V o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.positionCS = VegClipPos(v.positionOS.xyz);
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap);
                return o;
            }
            half4 frag(V i) : SV_Target
            {
                half a = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv).a * _BaseColor.a;
                // Alpha-to-coverage path still discards the fully uncovered texels (as URP Lit): the coverage mask alone
                // is not applied on every target (A16 Vulkan: cards rendered as opaque quads without this clip).
                if (_AlphaToMask > 0.5) { half c = CoverageAlpha(a); clip(c - 0.0001); return half4(0, 0, 0, c); }
                clip(a - _Cutoff);
                return 0;
            }
            ENDHLSL
        }

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            // LEqual + a small pull towards the camera instead of ZTest Equal: the two passes are separate shader programs
            // and the compiler does not guarantee bit-identical depth (Vulkan without Invariant: every leaf failed Equal on
            // the Mali-G57). ZWrite Off keeps the early depth test valid despite the clip / coverage below.
            ZWrite Off ZTest LEqual Offset -1, -1 Cull [_Cull]
            AlphaToMask [_AlphaToMask]
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
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
                half fogFactor : TEXCOORD3;
                half3 ambient : TEXCOORD4;
                UNITY_VERTEX_OUTPUT_STEREO
            };
            V vert(A v)
            {
                V o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.positionCS = VegClipPos(v.positionOS.xyz);
                o.positionWS = TransformObjectToWorld(v.positionOS.xyz);
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap);
                o.fogFactor = ComputeFogFactor(o.positionCS.z);
                // Ambient per vertex: crown normals are smooth (generator), so per-pixel SH adds nothing visible.
                o.ambient = SampleSH(o.normalWS);
                return o;
            }
            half4 frag(V i, bool front : SV_IsFrontFace) : SV_Target
            {
                half4 tex = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv) * _BaseColor;
                // Same coverage as the depth pass: fragments outside the leaf would otherwise paint over samples whose
                // depth is still the background's.
                half alpha = 1.0;
                if (_AlphaToMask > 0.5) { alpha = CoverageAlpha(tex.a); clip(alpha - 0.0001); }
                else clip(tex.a - _Cutoff);
                half3 albedo = tex.rgb;
                half3 n = normalize(i.normalWS);
                n = front ? n : -n;
                Light L = GetMainLight(TransformWorldToShadowCoord(i.positionWS));
                half NoL = dot(n, L.direction);
                half sun = saturate(NoL) + _Transmission * saturate(-NoL);
                half3 color = albedo * (L.color * (sun * L.shadowAttenuation * L.distanceAttenuation) + i.ambient);
                color = MixFog(color, i.fogFactor);
                return half4(color, alpha);
            }
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode" = "ShadowCaster" }
            ZWrite On ZTest LEqual ColorMask 0 Cull Off
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"
            float3 _LightDirection;
            float3 _LightPosition;
            struct A { float4 positionOS : POSITION; float3 normalOS : NORMAL; float2 uv : TEXCOORD0; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct V { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; };
            V vert(A v)
            {
                UNITY_SETUP_INSTANCE_ID(v);
                V o;
                float3 pw = TransformObjectToWorld(v.positionOS.xyz);
                float3 nw = TransformObjectToWorldNormal(v.normalOS);
            #if _CASTING_PUNCTUAL_LIGHT_SHADOW
                float3 ld = normalize(_LightPosition - pw);
            #else
                float3 ld = _LightDirection;
            #endif
                float4 cs = TransformWorldToHClip(ApplyShadowBias(pw, nw, ld));
            #if UNITY_REVERSED_Z
                cs.z = min(cs.z, UNITY_NEAR_CLIP_VALUE);
            #else
                cs.z = max(cs.z, UNITY_NEAR_CLIP_VALUE);
            #endif
                o.positionCS = cs;
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap);
                return o;
            }
            half4 frag(V i) : SV_Target
            {
                clip(SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv).a * _BaseColor.a - _Cutoff);
                return 0;
            }
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode" = "DepthOnly" }
            ZWrite On ColorMask R Cull [_Cull]
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            struct A { float4 positionOS : POSITION; float2 uv : TEXCOORD0; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct V { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; };
            V vert(A v)
            {
                UNITY_SETUP_INSTANCE_ID(v);
                V o;
                o.positionCS = VegClipPos(v.positionOS.xyz);
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap);
                return o;
            }
            half4 frag(V i) : SV_Target
            {
                clip(SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv).a * _BaseColor.a - _Cutoff);
                return 0;
            }
            ENDHLSL
        }
    }
    FallBack Off
}
