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
            // Hard shadows in the cab (no soft-shadow variants): the sun patches come through the glass edges and the
            // frit, soft filtering on a full-screen interior cost ~3 ms GPU on the S24+ High (A7 measurement, throttled).
            #pragma shader_feature_local _KAMION_CAB_DECAL
            #pragma multi_compile_fog
            #define _NORMALMAP 1

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            TEXTURE2D(_Detail); SAMPLER(sampler_Detail);
            TEXTURE2D(_Normal);
            TEXTURE2D(_AO); SAMPLER(sampler_AO);
            TEXTURE2D(_DecalAtlas); SAMPLER(sampler_DecalAtlas);
            half4 _CabFill;     // rgb: first-bounce irradiance / pi in exposed units (CabInteriorLighting)
            half _CabEnclosure; // share of the open-sky SH the closed cab blocks (roof, walls); 0 = open sky (unset global)
            half _CabGain;      // cab-view tone-mapping gain (1 = off)
            half4 _CabShadowLift; // x: strength k, y: knee k0 (exposed linear); gain = 1 + k (k0 / (Y + k0))^3, cab view only

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
                // Legend band of the atlas (icons, v < 0.5; manifest "MI_Cab_Decal" notes). A 10-13 mm legend is ~8-12 px
                // on the phone: the mip-averaged alpha of a 9 px stroke falls under 0.5 and the print vanished. Lower
                // clip keeps the stroke; printed legends are near-white paint and sit proud of the key, so they take the
                // key's AO only in part (interior legibility pass, ADR 0044).
                half legend = i.uv01.y < 0.5 ? 1.0 : 0.0;
                clip(d.a - lerp(_Cutoff, 0.16, legend));
                albedo = tint * d.rgb * (1.0 + 0.45 * legend);
                rough = i.color.a;
                ao = lerp(ao, max(ao, 0.8), legend);
            #else
                half4 det = SAMPLE_TEXTURE2D(_Detail, sampler_Detail, i.uv01.xy);
                half mixD = strength > 0.0 ? 1.0 : 0.0;
                // Wear (uv2.x, 0..~0.9): polished touch points. At phone resolution the authored 1 + 1.5 w / -0.25 w did not
                // read (ADR 0044): the wear is shaped (wk), broken up by the detail variation so it is not a vertex
                // gradient, and mostly a gloss change (hand-polished leather and plastic get shiny before they get pale).
                half wk = saturate(wear * 2.4 * (0.55 + 0.9 * det.r * mixD + 0.45 * (1.0 - mixD)));
                albedo = tint * lerp(1.0, (0.7 + 0.6 * det.r) * (0.4 + 0.6 * det.g), mixD) * lerp(1.0, det.a, perf) * (1.0 + 1.5 * wear + 1.3 * wk);
                rough = clamp(i.color.a + (det.b - 0.5) * 0.6 * mixD - 0.25 * wear - 0.3 * wk, 0.08, 1.0);
                // Panel gaps and creases: the AO atlas is ambient-only in URP, so in direct light a 2 mm gap had the
                // brightness of its panels. Deep AO also darkens the albedo: gaps read as thin dark lines.
                albedo *= lerp(0.4, 1.0, smoothstep(0.04, 0.28, ao));
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
                input.bakedGI = SampleSH(nWS) * (1.0 - _CabEnclosure) + _CabFill.rgb;
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
                // Grazing sheen: the windscreen and side glass are a large bright source in front of every cab surface;
                // the cab has no probe that sees them, so edges of keys, the wheel rim and seat bolsters had no highlight
                // and leather read like matte plastic. Fresnel-weighted ambient, scaled by smoothness (worn leather and
                // satin keys catch it, grained dash plastic does not), occluded by the AO atlas. ~8 ALU, no sample.
                half nv = saturate(dot(nWS, input.viewDirectionWS));
                half fr = 1.0 - nv; fr *= fr * fr;
                half sm = s.smoothness;
                col.rgb += input.bakedGI * (fr * sm * (0.4 + sm) * 3.0 * ao * (1.0 - metal));
                col.rgb *= _CabGain > 0.0 ? _CabGain : 1.0;   // unset global (0) = no gain
                // Local shadow lift (review r4 L1): a phone's local tone mapping lifts deep shade in a backlit cab. Smooth
                // in luminance (Y * gain stays monotone for k < 16), ~1 above 3 x the knee.
                half yl = dot(col.rgb, half3(0.2126, 0.7152, 0.0722));
                half q = _CabShadowLift.y / (yl + _CabShadowLift.y + 1e-5);
                half g = 1.0 + _CabShadowLift.x * q * q * q;
                // The lifted share is neutral (review r5 L2: black plastics turned brown under the warm low-sun fill); a
                // phone's local tone mapping lifts luminance, not the chroma of deep shade. z = desaturation of that share.
                col.rgb = lerp(col.rgb * g, (yl * g).xxx, _CabShadowLift.z * (1.0 - 1.0 / g));
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
