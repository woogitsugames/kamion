// TRAKT cab interior (track A7). Contract: art-source/truck/interior/export/cab_interior_manifest.json "shader_contract".
// Vertex data carries the authoring materials: color.rgb tint (sRGB), color.a base roughness, uv0 tiled detail,
// uv1 AO atlas, uv2.x wear, uv2.y detail strength, uv3.x perforation flag, uv3.y metallic.
//
// Cab lighting (visual review r2, A6 #1 P0: low sun turned the cab black). The baked AO atlas is the cab's sky
// visibility; URP's per-object SH ambient sees the open sky and the sun patches are the only other light. A real cab is
// also lit by sunlight that enters the glass and bounces off the dash, floor and seats. CabInteriorLighting computes that
// first-bounce irradiance once per frame on the CPU (integrating-sphere estimate from the sun, sky and glass areas, in
// exposed units) and passes it as _CabFill; here ambient = (SH(n) + _CabFill) * AO. _CabGain is the cab-view local tone
// mapping of the D23 phone look (a phone lifts the interior of a backlit scene). No extra light, no extra pass: Low safe.
// _KAMION_CAB_DECAL: alpha-clipped decal atlas on uv0 (stitching, icons, grilles), AO from uv1 like the opaque slots so
// stitching does not glow under the sky ambient (review A6 #5).
Shader "Kamion/Cab Interior"
{
    Properties
    {
        _Detail ("Detail (R variation, G micro-AO, B roughness, A perforation)", 2D) = "grey" {}
        _Normal ("Normal (OpenGL +Y)", 2D) = "bump" {}
        _AO ("AO atlas (uv1)", 2D) = "white" {}
        _DecalAtlas ("Decal atlas (uv0, RGB tint x, A clip)", 2D) = "white" {}
        _Cutoff ("Decal alpha clip", Range(0, 1)) = 0.5
        [Toggle(_KAMION_CAB_DECAL)] _IsDecal ("Decal slot", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" "UniversalMaterialType" = "Lit" }

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        CBUFFER_START(UnityPerMaterial)
            float4 _Detail_ST;
            float _Cutoff, _IsDecal;
        CBUFFER_END
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Cull Back ZWrite On

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #pragma multi_compile_fragment _ _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma shader_feature_local _KAMION_CAB_DECAL
            #pragma multi_compile_fog
            #define _NORMALMAP 1

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            TEXTURE2D(_Detail); SAMPLER(sampler_Detail);
            TEXTURE2D(_Normal);
            TEXTURE2D(_AO); SAMPLER(sampler_AO);
            TEXTURE2D(_DecalAtlas); SAMPLER(sampler_DecalAtlas);
            half4 _CabFill;     // rgb: first-bounce irradiance / pi in exposed units (CabInteriorLighting)
            half _CabGain;      // cab-view tone-mapping gain (1 = off)

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                float4 tangentOS : TANGENT;
                half4 color : COLOR;
                float2 uv0 : TEXCOORD0;
                float2 uv1 : TEXCOORD1;
                float2 uv2 : TEXCOORD2;
                float2 uv3 : TEXCOORD3;
            };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float4 uv01 : TEXCOORD0;
                float4 uv23 : TEXCOORD1;
                float3 positionWS : TEXCOORD2;
                half3 normalWS : TEXCOORD3;
                half4 tangentWS : TEXCOORD4;
                half4 color : TEXCOORD5;
                half fogFactor : TEXCOORD6;
            };

            Varyings vert(Attributes v)
            {
                Varyings o = (Varyings)0;
                VertexPositionInputs p = GetVertexPositionInputs(v.positionOS.xyz);
                VertexNormalInputs n = GetVertexNormalInputs(v.normalOS, v.tangentOS);
                o.positionCS = p.positionCS;
                o.positionWS = p.positionWS;
                o.normalWS = n.normalWS;
                o.tangentWS = half4(n.tangentWS, v.tangentOS.w * GetOddNegativeScale());
                o.uv01 = float4(v.uv0, v.uv1);
                o.uv23 = float4(v.uv2, v.uv3);
                o.color = half4(SRGBToLinear(v.color.rgb), v.color.a);
                o.fogFactor = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                half3 tint = i.color.rgb;
                half wear = i.uv23.x, strength = i.uv23.y, perf = i.uv23.z, metal = i.uv23.w;
                half ao = SAMPLE_TEXTURE2D(_AO, sampler_AO, i.uv01.zw).r;
                half3 albedo;
                half rough;
                half3 nTS = half3(0, 0, 1);
            #if defined(_KAMION_CAB_DECAL)
                half4 d = SAMPLE_TEXTURE2D(_DecalAtlas, sampler_DecalAtlas, i.uv01.xy);
                clip(d.a - _Cutoff);
                albedo = tint * d.rgb;
                rough = i.color.a;
            #else
                half4 det = SAMPLE_TEXTURE2D(_Detail, sampler_Detail, i.uv01.xy);
                half mixD = strength > 0.0 ? 1.0 : 0.0;
                albedo = tint * lerp(1.0, (0.7 + 0.6 * det.r) * (0.4 + 0.6 * det.g), mixD) * lerp(1.0, det.a, perf) * (1.0 + 1.5 * wear);
                rough = saturate(i.color.a + (det.b - 0.5) * 0.4 * mixD - 0.25 * wear);
                nTS = UnpackNormalScale(SAMPLE_TEXTURE2D(_Normal, sampler_Detail, i.uv01.xy), 1.25 * strength);
            #endif
                half sgn = i.tangentWS.w;
                half3 bit = sgn * cross(i.normalWS, i.tangentWS.xyz);
                half3 nWS = NormalizeNormalPerPixel(TransformTangentToWorld(nTS, half3x3(i.tangentWS.xyz, bit, i.normalWS)));

                InputData input = (InputData)0;
                input.positionWS = i.positionWS;
                input.normalWS = nWS;
                input.viewDirectionWS = GetWorldSpaceNormalizeViewDir(i.positionWS);
                input.shadowCoord = TransformWorldToShadowCoord(i.positionWS);
                input.fogCoord = i.fogFactor;
                // AO multiplies the whole indirect term in UniversalFragmentPBR (occlusion), the fill included.
                input.bakedGI = SampleSH(nWS) + _CabFill.rgb;
                input.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(i.positionCS);
                input.shadowMask = half4(1, 1, 1, 1);

                SurfaceData s = (SurfaceData)0;
                s.albedo = saturate(albedo);
                s.metallic = metal;
                s.smoothness = 1.0 - rough;
                s.occlusion = ao;
                s.alpha = 1;
                s.normalTS = nTS;
                half4 col = UniversalFragmentPBR(input, s);
                col.rgb *= _CabGain > 0.0 ? _CabGain : 1.0;   // unset global (0) = no gain
                col.rgb = MixFog(col.rgb, i.fogFactor);
                return half4(col.rgb, 1);
            }
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode" = "ShadowCaster" }
            ZWrite On ZTest LEqual ColorMask 0 Cull Back

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex ShadowVert
            #pragma fragment ShadowFrag
            #pragma shader_feature_local _KAMION_CAB_DECAL
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"
            float3 _LightDirection;
            float3 _LightPosition;
            TEXTURE2D(_DecalAtlas); SAMPLER(sampler_DecalAtlas);
            struct A { float4 positionOS : POSITION; float3 normalOS : NORMAL; float2 uv0 : TEXCOORD0; };
            struct V { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; };
            V ShadowVert(A v)
            {
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
                o.uv = v.uv0;
                return o;
            }
            half4 ShadowFrag(V i) : SV_Target
            {
            #if defined(_KAMION_CAB_DECAL)
                clip(SAMPLE_TEXTURE2D(_DecalAtlas, sampler_DecalAtlas, i.uv).a - _Cutoff);
            #endif
                return 0;
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
            #pragma shader_feature_local _KAMION_CAB_DECAL
            TEXTURE2D(_DecalAtlas); SAMPLER(sampler_DecalAtlas);
            struct A { float4 positionOS : POSITION; float2 uv0 : TEXCOORD0; };
            struct V { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; };
            V DepthVert(A v) { V o; o.positionCS = TransformObjectToHClip(v.positionOS.xyz); o.uv = v.uv0; return o; }
            half4 DepthFrag(V i) : SV_Target
            {
            #if defined(_KAMION_CAB_DECAL)
                clip(SAMPLE_TEXTURE2D(_DecalAtlas, sampler_DecalAtlas, i.uv).a - _Cutoff);
            #endif
                return 0;
            }
            ENDHLSL
        }
    }
    Fallback Off
}
