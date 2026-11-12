// House plot kit (ADR 0124): fences, gates, bins and garden plants of the single-family plots - one alpha-clip atlas,
// one material, chunk geometry (streetscape.plots / plot_kit). Replaces URP Lit for the `plot_kit` material.
//
// Why not URP Lit (ADR 0114): Lit with Cull Off lights a back face with the front normal, so ADR 0114 doubled every
// fence card (two quads 24 mm apart) - from 1 m the second card showed as a grey "ghost" of each spear head (review
// 0114 P1-r8-f); and crossed plant cards were lit per card (a vertical seam through every crown, P1-r8-e).
//
// How (the two-pass scheme and the lighting model of Kamion/Vegetation, without its impostor / HLOD variants):
// 1. Depth pass (SRPDefaultUnlit) with the clip / alpha-to-coverage; colour pass ZWrite Off, ZTest LEqual: hidden
//    card layers fail early-Z, lighting runs about once per visible pixel.
// 2. COLOR_0 selects the surface kind per vertex:
//      a = 0  hard surface (wood, steel, brick, concrete): geometric normal, FLIPPED on back faces - one card is a
//             correct two-sided panel; rgb * 2 = albedo tint (per-plot ageing: faded, greyed, darkened).
//      a = 1  foliage: rgb = normal * 0.5 + 0.5 in generator axes (x east, y north, z up), pointing away from the
//             plant's axis - all cards of one plant shade as one volume, no flip; back-lit transmission.
//             ADR 0132: the LENGTH of that vector (1 = open, shorter = deeper) is the plant's own occlusion - the foot
//             and the inside of a hedge / crown are darker than its lit skin (albedo factor, sun and ambient alike).
// 3. Lambert + main-light shadow + SH ambient (per vertex, both faces) + project fog. No specular, no reflection
//    probe: every surface of the kit is matt (rough 0.85 in ADR 0114).
Shader "Kamion/World PlotKit"
{
    Properties
    {
        _BaseMap ("Albedo (RGB) alpha (A)", 2D) = "white" {}
        _BaseColor ("Color", Color) = (1, 1, 1, 1)
        _Cutoff ("Alpha cutoff", Range(0, 1)) = 0.5
        _Transmission ("Foliage back-lit transmission", Range(0, 1)) = 0.22
        _AmbientTransmission ("Foliage diffuse transmission", Range(0, 1)) = 0.25
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
            half _AmbientTransmission;
            half _Cull;
            half _AlphaToMask;
        CBUFFER_END
        TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
        half4 _KamionLeafAmbient;       // global (WorldAtmosphere): x = ambient through the leaf on, y = leaf sheen

        half KitAlpha(float2 uv) { return SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv).a * _BaseColor.a; }
        // Alpha-to-coverage edge: alpha sharpened to ~1 pixel around the cutoff (as URP Lit's SharpenAlpha).
        half CoverageAlpha(half a) { return saturate((a - _Cutoff) / max(fwidth(a), 0.0001) + 0.5); }
        ENDHLSL

        Pass
        {
            Name "PlotKitDepth"
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
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap);
                return o;
            }
            half4 frag(V i) : SV_Target
            {
                half a = KitAlpha(i.uv);
                // The coverage path still discards fully uncovered texels (A16 Vulkan: the mask alone is not applied
                // on every target - Kamion/Vegetation).
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
            // LEqual + a small pull towards the camera instead of ZTest Equal (two shader programs: depth is not
            // guaranteed bit-identical on Vulkan); ZWrite Off keeps early-Z valid despite the clip below.
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
            #include "Assets/_Project/Rendering/Shaders/KamionAtmosphere.hlsl"   // ADR 0080 height haze, Low tone toe, wetness

            // SH ambient of a surface with normal n; t = share of the light arriving on the other face that passes
            // through (thin leaf: SH(n) + t SH(-n) = even bands * (1 + t) + odd band * (1 - t); Kamion/Vegetation).
            half3 KitAmbient(half3 n, half t)
            {
                half3 l0 = half3(unity_SHAr.w, unity_SHAg.w, unity_SHAb.w);
                half3 l1 = half3(dot(unity_SHAr.xyz, n), dot(unity_SHAg.xyz, n), dot(unity_SHAb.xyz, n));
                half3 l2 = SHEvalLinearL2(n, unity_SHBr, unity_SHBg, unity_SHBb, unity_SHC);
                return max((l0 + l2) * (1.0h + t) + l1 * (1.0h - t), half3(0.0h, 0.0h, 0.0h));
            }
            struct A { float4 positionOS : POSITION; float3 normalOS : NORMAL; float2 uv : TEXCOORD0; half4 color : COLOR; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct V
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 positionWS : TEXCOORD1;
                half4 normalWS : TEXCOORD2;      // w: 1 = foliage
                half4 tintFog : TEXCOORD3;       // rgb albedo tint, a fog
                half3 ambFront : TEXCOORD4;
                half3 ambBack : TEXCOORD5;
                UNITY_VERTEX_OUTPUT_STEREO
            };
            V vert(A v)
            {
                V o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                half fol = step(0.5h, v.color.a);
                // foliage normal: generator axes (east, north, up) -> mesh axes (x east, y up, z north)
                half3 nf = v.color.rgb * 2.0h - 1.0h;
                half nlen = max(length(nf), 0.001h);
                half occ = saturate(nlen * 1.02h);              // 8-bit colour: a unit vector reads 0.98-1.0
                nf /= nlen;
                float3 nOS = lerp(v.normalOS, float3(nf.x, nf.z, nf.y), fol);
                half3 n = TransformObjectToWorldNormal(nOS);
                o.normalWS = half4(n, fol);
                half t = fol * _AmbientTransmission * _KamionLeafAmbient.x;
                o.ambFront = KitAmbient(n, t);
                o.ambBack = lerp(KitAmbient(-n, 0.0h), o.ambFront, fol);
                o.positionWS = TransformObjectToWorld(v.positionOS.xyz);
                o.positionCS = TransformWorldToHClip(o.positionWS);
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap);
                o.tintFog = half4(lerp(v.color.rgb * 2.0h, half3(occ, occ, occ), fol), KamionFogTau(o.positionWS, o.positionCS.w));
                return o;
            }
            half4 frag(V i, bool front : SV_IsFrontFace) : SV_Target
            {
                half4 tex = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv) * _BaseColor;
                // Same coverage as the depth pass: fragments outside the texel would otherwise paint over samples
                // whose depth is still the background's.
                half alpha = 1.0;
                if (_AlphaToMask > 0.5) { alpha = CoverageAlpha(tex.a); clip(alpha - 0.0001); }
                else clip(tex.a - _Cutoff);
                half fol = i.normalWS.w;
                half3 n = normalize(i.normalWS.xyz);
                half back = (front || fol > 0.5h) ? 0.0h : 1.0h;
                n = lerp(n, -n, back);
                half3 ambient = lerp(i.ambFront, i.ambBack, back);
                half3 albedo = tex.rgb * i.tintFog.rgb;
                Light L = GetMainLight();
            #if defined(MAIN_LIGHT_CALCULATE_SHADOWS)
                L.shadowAttenuation = MainLightRealtimeShadow(TransformWorldToShadowCoord(i.positionWS));
            #endif
                half NoL = dot(n, L.direction);
                // foliage: wrapped diffuse (a plant is a volume of leaves, not a wall) + light through the leaf
                half sun = lerp(saturate(NoL), saturate(NoL * 0.6h + 0.4h) * 0.85h + _Transmission * saturate(-NoL), fol);
                half3 color = albedo * (L.color * (sun * L.shadowAttenuation * L.distanceAttenuation))
                            + (albedo + _KamionLeafAmbient.y * fol) * ambient;
                color = KamionMixFog(color, i.tintFog.a);
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
                clip(KitAlpha(i.uv) - _Cutoff);
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
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap);
                return o;
            }
            half4 frag(V i) : SV_Target
            {
                clip(KitAlpha(i.uv) - _Cutoff);
                return 0;
            }
            ENDHLSL
        }
    }
    FallBack Off
}
