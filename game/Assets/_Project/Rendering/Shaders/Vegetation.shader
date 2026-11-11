// Leaf cards, tree impostors and forest HLOD edge walls (QualityProfile.simpleFoliage, every tier since ADR 0013 r5).
//
// Why: the DK8 forest control camera on the Galaxy A16 (Mali-G57 MC2) is fragment bound - GPU 61 ms on Medium, 18 ms
// with the trees off, and the cost scales with render scale (device ablation 2026-11-09). URP Lit with alpha clip shades
// every overlapping card (discard disables early depth kill on a tiled GPU) with full PBR (GGX, reflection probe,
// cascaded shadow lookup).
//
// How:
// 1. Depth pass (LightMode SRPDefaultUnlit, drawn before UniversalForward for the same draw): alpha test or
//    alpha-to-coverage, depth only. The only pass with discard; its fragment is one (impostor: two) texture fetch.
// 2. Colour pass (UniversalForward): ZWrite Off, ZTest LEqual with a small depth offset - hidden card layers fail the
//    early depth test against pass 1 before shading (a shader that clips but does not write depth keeps early-Z on a
//    tiled GPU), so the lighting runs about once per visible pixel instead of once per overlapping card. Same clip /
//    coverage as pass 1, so the alpha-to-coverage edge under MSAA is kept.
// 3. Lighting: Lambert with the sun's shadow, a small transmission term for back-lit leaves (thin leaf, ~25% of the
//    diffuse, WORKING_VALUE), L2 SH ambient, fog. No specular lobe and no reflection probe: leaf specular at the URP
//    Lit smoothness 0.25 is a few % of the diffuse and the probe fetch was the costliest part of the old fragment.
//
// Variants (ADR 0023, world v3.4):
// _IMPOSTOR   one quad per tree turned to the camera about the tree's up axis (cylindrical billboard) instead of two
//             crossed quads (thin "fence" slivers and double overdraw at grazing angles). _BaseMap holds _Impostor.x
//             views around the tree side by side (tools/blender/world/make_trees.py, view k = camera at azimuth
//             2 pi k / N), _NormalOcc their view-space normal (RG) and sky visibility (B). The two views around the
//             camera azimuth are cross-faded (global _KamionImpostorBlend = 1; 0 = nearest view only, half the fetches).
//             Lit like the cards (sun + SH from the sky model), not with a baked light (review r3 W1/W2).
// _HLOD_EDGE  forest HLOD edge walls (ADR 0015): the same normal / visibility map in wall space; tangent frame from
//             screen derivatives (the walls carry no tangents).
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
        _AmbientTransmission ("Diffuse canopy transmission", Range(0, 1)) = 0.25
        [NoScaleOffset] _NormalOcc ("Normal XY (RG), sky visibility (B) - impostor / HLOD edge", 2D) = "bump" {}
        _Impostor ("Impostor: x views, y visibility strength (ambient), z visibility strength (sun)", Vector) = (6, 0.6, 0.35, 0)
        _CrownShade ("Leaf cards: sky occlusion of the lower crown (ambient; ADR 0088)", Range(0, 1)) = 0.5
        [Enum(UnityEngine.Rendering.CullMode)] _Cull ("Cull", Float) = 0
        [Toggle] _AlphaToMask ("Alpha to coverage", Float) = 0
        // ADR 0113: colour-pass depth state. Defaults = two-pass path (depth pass + ZWrite Off / pulled-in colour pass);
        // ForestFastPath sets 1 / 0 with the depth pass disabled for the single-pass HLOD edge walls.
        [HideInInspector] _VegZWrite ("Colour pass ZWrite", Float) = 0
        [HideInInspector] _VegOffset ("Colour pass depth offset", Float) = -1
    }
    SubShader
    {
        Tags { "RenderType" = "TransparentCutout" "RenderPipeline" = "UniversalPipeline" "Queue" = "AlphaTest" "IgnoreProjector" = "True" }

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        #pragma multi_compile_local _ _IMPOSTOR _HLOD_EDGE
        CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_ST;
            half4 _BaseColor;
            half _Cutoff;
            half _Transmission;
            half _AmbientTransmission;
            half _Cull;
            half _AlphaToMask;
            float4 _Impostor;
            half _CrownShade;
        CBUFFER_END
        TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
        TEXTURE2D(_NormalOcc); SAMPLER(sampler_NormalOcc);
        // Global (WorldInstances, per tier): 1 = cross-fade the two nearest impostor views, 0 = nearest view.
        half _KamionImpostorBlend;
        // ADR 0080 r11 (WorldAtmosphere): x = 1: the ambient includes the sky light transmitted through the leaf,
        // y = sheen: share of the ambient radiance mirrored by the leaf surface (0 = off, unset).
        half4 _KamionLeafAmbient;

        // Cylindrical billboard of an impostor quad (object space) and its two view UVs + blend weight. The quad's
        // corners are (+-w, h) in object space; the turn uses the instance matrix only (lean and yaw included).
        struct ImpostorVert { float3 positionOS; float4 uv; half t; float3 rightWS; float3 upWS; float3 toCamWS; };
        ImpostorVert Impostor(float3 positionOS, float2 uv)
        {
            ImpostorVert o;
            float3 ax = UNITY_MATRIX_M._m00_m10_m20, ay = UNITY_MATRIX_M._m01_m11_m21, az = UNITY_MATRIX_M._m02_m12_m22;
            float3 d = _WorldSpaceCameraPos - TransformObjectToWorld(float3(0, 0, 0));
            float a = atan2(-dot(d, ax), dot(d, az));           // camera azimuth in the bake's convention
            float sa, ca;
            sincos(a, sa, ca);
            float3 rightL = float3(-ca, 0, -sa);
            o.positionOS = rightL * ((uv.x * 2.0 - 1.0) * abs(positionOS.x)) + float3(0, positionOS.y, 0);
            float n = max(_Impostor.x, 1.0);
            float f = a * (n / (2.0 * PI));
            f = f < 0.0 ? f + n : f;
            float i0 = floor(f);
            float i1 = i0 + 1.0 >= n ? 0.0 : i0 + 1.0;
            o.t = (half)(f - i0);
            float2 u = TRANSFORM_TEX(uv, _BaseMap);
            o.uv = float4((i0 + u.x) / n, u.y, (i1 + u.x) / n, u.y);
            o.rightWS = normalize(mul((float3x3)UNITY_MATRIX_M, rightL));
            o.upWS = normalize(ay);
            o.toCamWS = normalize(mul((float3x3)UNITY_MATRIX_M, float3(-sa, 0, ca)));
            return o;
        }

        // Shared by every pass (same transform, so the depths agree to within the colour pass offset).
        float3 VegPositionOS(float3 positionOS, float2 uv)
        {
        #if defined(_IMPOSTOR)
            return Impostor(positionOS, uv).positionOS;
        #else
            return positionOS;
        #endif
        }
        float4 VegClipPos(float3 positionOS, float2 uv) { return TransformWorldToHClip(TransformObjectToWorld(VegPositionOS(positionOS, uv))); }
        float4 VegUV(float2 uv)
        {
        #if defined(_IMPOSTOR)
            return Impostor(float3(0, 0, 0), uv).uv;
        #else
            float2 u = TRANSFORM_TEX(uv, _BaseMap);
            return float4(u, u);
        #endif
        }
        half VegBlend(float2 uv)
        {
        #if defined(_IMPOSTOR)
            return Impostor(float3(0, 0, 0), uv).t;
        #else
            return 0;
        #endif
        }

        // Coverage (alpha) of the texel: impostors cross-fade two views (or take the nearest one).
        half VegAlpha(float4 uv, half t)
        {
        #if defined(_IMPOSTOR)
            if (_KamionImpostorBlend > 0.5)
                return lerp(SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv.xy).a, SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv.zw).a, t) * _BaseColor.a;
            return SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, t < 0.5 ? uv.xy : uv.zw).a * _BaseColor.a;
        #else
            return SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv.xy).a * _BaseColor.a;
        #endif
        }

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
            struct V { float4 positionCS : SV_POSITION; float4 uv : TEXCOORD0; half t : TEXCOORD1; UNITY_VERTEX_OUTPUT_STEREO };
            V vert(A v)
            {
                V o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.positionCS = VegClipPos(v.positionOS.xyz, v.uv);
                o.uv = VegUV(v.uv);
                o.t = VegBlend(v.uv);
                return o;
            }
            half4 frag(V i) : SV_Target
            {
                half a = VegAlpha(i.uv, i.t);
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
            // ADR 0113: [_VegZWrite] / [_VegOffset] = Off / -1 except the single-pass HLOD edge walls (On / 0, depth pass off).
            ZWrite [_VegZWrite] ZTest LEqual Offset [_VegOffset], [_VegOffset] Cull [_Cull]
            AlphaToMask [_AlphaToMask]
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            // ADR 0113 (QualityProfile.forestFast): HLOD edge walls take the L2 SH band per vertex (L0 + L1 stay per pixel,
            // URP's "mixed" SH mode), and no vegetation pixel beyond the shadow fade samples the shadow map.
            #pragma multi_compile _ _KAMION_VEG_FAST
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Assets/_Project/Rendering/Shaders/KamionAtmosphere.hlsl"   // ADR 0080 height haze, Low tone toe, wetness
            // ADR 0080 r11: ambient of a thin leaf = sky / ground light on the lit face + the light arriving on the other
            // face and passing through the leaf, SH(n) + t SH(-n). The L0 and L2 bands are even in n and L1 is odd, so
            // this is one SH evaluation with scaled bands (no second evaluation; per vertex on cards and impostors).
            // Without it the underside of a crown saw only the ground bounce and fell to black under the overcast toe.
            half3 LeafAmbient(half3 n)
            {
                // Diffuse light arriving through surrounding foliage includes
                // multiple scattering omitted by the direct-only visibility bake.
                // Keep this material-local; sky/exposure/global tint stay unchanged.
                half t = _AmbientTransmission * _KamionLeafAmbient.x * step(_Cull, 0.5h);
                half3 l0 = half3(unity_SHAr.w, unity_SHAg.w, unity_SHAb.w);
                half3 l1 = half3(dot(unity_SHAr.xyz, n), dot(unity_SHAg.xyz, n), dot(unity_SHAb.xyz, n));
                half3 l2 = SHEvalLinearL2(n, unity_SHBr, unity_SHBg, unity_SHBb, unity_SHC);
                return max((l0 + l2) * (1.0h + t) + l1 * (1.0h - t), half3(0.0h, 0.0h, 0.0h));
            }
            // ADR 0113: LeafAmbient with the L2 band given (per vertex); L0 + L1 (linear in n) per pixel.
            half3 LeafAmbientL2(half3 n, half3 l2)
            {
                half t = _AmbientTransmission * _KamionLeafAmbient.x * step(_Cull, 0.5h);
                half3 l0 = half3(unity_SHAr.w, unity_SHAg.w, unity_SHAb.w);
                half3 l1 = half3(dot(unity_SHAr.xyz, n), dot(unity_SHAg.xyz, n), dot(unity_SHAb.xyz, n));
                return max((l0 + l2) * (1.0h + t) + l1 * (1.0h - t), half3(0.0h, 0.0h, 0.0h));
            }
            // Main-light shadow. Fast path (ADR 0113): URP's distance fade (as URP Lit; the two-pass path had none) and no
            // shadow-map fetch beyond it - HLOD walls (> 70 m) and most impostors lie past the Low / Medium shadow distance.
            half VegShadow(float3 positionWS)
            {
            #if defined(MAIN_LIGHT_CALCULATE_SHADOWS)
            #if defined(_KAMION_VEG_FAST)
                half fade = GetMainLightShadowFade(positionWS);
                UNITY_BRANCH if (fade > 0.999h) return 1.0h;
                return lerp(MainLightRealtimeShadow(TransformWorldToShadowCoord(positionWS)), 1.0h, fade);
            #else
                return MainLightRealtimeShadow(TransformWorldToShadowCoord(positionWS));
            #endif
            #else
                return 1.0h;
            #endif
            }
            struct A { float4 positionOS : POSITION; float3 normalOS : NORMAL; float2 uv : TEXCOORD0; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct V
            {
                float4 positionCS : SV_POSITION;
                float4 uv : TEXCOORD0;
                float3 positionWS : TEXCOORD1;
                half3 normalWS : TEXCOORD2;
                half fogFactor : TEXCOORD3;
                half3 ambient : TEXCOORD4;
            #if defined(_IMPOSTOR)
                half3 rightWS : TEXCOORD5;
                half3 upWS : TEXCOORD6;
                half4 ambUpT : TEXCOORD7;        // xyz SH towards up, w view blend weight
                half3 ambDown : TEXCOORD8;
            #elif defined(_HLOD_EDGE) && defined(_KAMION_VEG_FAST)
                half3 ambL2 : TEXCOORD5;         // L2 SH band of the wall normal (even in n: valid for both faces)
            #endif
                UNITY_VERTEX_OUTPUT_STEREO
            };
            V vert(A v)
            {
                V o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
            #if defined(_IMPOSTOR)
                ImpostorVert iv = Impostor(v.positionOS.xyz, v.uv);
                float3 pOS = iv.positionOS;
                o.uv = iv.uv;
                o.normalWS = iv.toCamWS;
                o.rightWS = iv.rightWS;
                o.upWS = iv.upWS;
                // Ambient from the sky SH towards the camera, up and down per vertex, blended by the texel normal below
                // (per-pixel L2 SH costs ~30 ALU; the crown normals of the bake are smooth).
                o.ambient = LeafAmbient(iv.toCamWS);
                o.ambUpT = half4(LeafAmbient(iv.upWS), iv.t);
                o.ambDown = LeafAmbient(-iv.upWS);
            #else
                float3 pOS = v.positionOS.xyz;
                float2 u = TRANSFORM_TEX(v.uv, _BaseMap);
                o.uv = float4(u, u);
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                // Ambient per vertex: crown normals are smooth (generator), so per-pixel SH adds nothing visible.
                o.ambient = LeafAmbient(o.normalWS);
            #if defined(_HLOD_EDGE) && defined(_KAMION_VEG_FAST)
                o.ambL2 = SHEvalLinearL2(o.normalWS, unity_SHBr, unity_SHBg, unity_SHBb, unity_SHC);
            #endif
            #endif
                o.positionWS = TransformObjectToWorld(pOS);
                o.positionCS = TransformWorldToHClip(o.positionWS);
                o.fogFactor = KamionFogTau(o.positionWS, o.positionCS.w);
                return o;
            }
            half4 frag(V i, bool front : SV_IsFrontFace) : SV_Target
            {
            #if defined(_IMPOSTOR)
                half t = i.ambUpT.w;
                half4 tex, no;
                if (_KamionImpostorBlend > 0.5)
                {
                    tex = lerp(SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv.xy), SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv.zw), t);
                    no = lerp(SAMPLE_TEXTURE2D(_NormalOcc, sampler_NormalOcc, i.uv.xy), SAMPLE_TEXTURE2D(_NormalOcc, sampler_NormalOcc, i.uv.zw), t);
                }
                else
                {
                    float2 uv = t < 0.5 ? i.uv.xy : i.uv.zw;
                    tex = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv);
                    no = SAMPLE_TEXTURE2D(_NormalOcc, sampler_NormalOcc, uv);
                }
                tex *= _BaseColor;
            #else
                half4 tex = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv.xy) * _BaseColor;
            #endif
                // Same coverage as the depth pass: fragments outside the leaf would otherwise paint over samples whose
                // depth is still the background's.
                half alpha = 1.0;
                if (_AlphaToMask > 0.5) { alpha = CoverageAlpha(tex.a); clip(alpha - 0.0001); }
                else clip(tex.a - _Cutoff);
                half3 albedo = tex.rgb;
                half3 n = normalize(i.normalWS);
            #if !defined(_IMPOSTOR)
                n = front ? n : -n;             // impostor: the billboard always faces the camera, whatever its winding
            #endif
                half3 ambient = i.ambient;
                half occA = 1.0, occS = 1.0;
            #if !defined(_IMPOSTOR) && !defined(_HLOD_EDGE)
                // ADR 0060 (review r7 N-2): leaf-card normals point away from the crown centre (make_trees.py), so their
                // height on the crown is known: the lower half sees less sky through the leaves above it (the impostors
                // and HLOD walls carry a baked visibility instead). Unflipped normal: a card seen from its back keeps its place.
                occA = lerp(1.0 - _CrownShade, 1.0, smoothstep(-0.6, 0.75, normalize(i.normalWS).y));
            #endif
            #if defined(_IMPOSTOR)
                // View-space normal of the bake: x right, y up, z towards the camera.
                half2 nxy = no.xy * 2.0 - 1.0;
                half nz = sqrt(saturate(1.0 - dot(nxy, nxy)));
                n = normalize(nxy.x * i.rightWS + nxy.y * i.upWS + nz * n);
                ambient = nxy.y >= 0 ? lerp(i.ambient, i.ambUpT.xyz, nxy.y) : lerp(i.ambient, i.ambDown, -nxy.y);
                occA = lerp(1.0, no.b, _Impostor.y);
                occS = lerp(1.0, no.b, _Impostor.z);
            #elif defined(_HLOD_EDGE)
                {
                    // Wall space of the bake: x along u, y up (v), z out of the stand. Cotangent frame from derivatives.
                    half4 nm = SAMPLE_TEXTURE2D(_NormalOcc, sampler_NormalOcc, i.uv.xy);
                    half2 nxy = nm.xy * 2.0 - 1.0;
                    half nz = sqrt(saturate(1.0 - dot(nxy, nxy)));
                    float3 dp1 = ddx(i.positionWS), dp2 = ddy(i.positionWS);
                    float2 duv1 = ddx(i.uv.xy), duv2 = ddy(i.uv.xy);
                    float3 dp2perp = cross(dp2, n), dp1perp = cross(n, dp1);
                    float3 T = dp2perp * duv1.x + dp1perp * duv2.x;
                    float3 B = dp2perp * duv1.y + dp1perp * duv2.y;
                    float inv = rsqrt(max(max(dot(T, T), dot(B, B)), 1e-12));
                    n = normalize(T * inv * nxy.x + B * inv * nxy.y + n * nz);
                #if defined(_KAMION_VEG_FAST)
                    ambient = LeafAmbientL2(n, i.ambL2);
                #else
                    ambient = LeafAmbient(n);
                #endif
                    occA = lerp(1.0, nm.b, _Impostor.y);
                    occS = lerp(1.0, nm.b, _Impostor.z);
                }
            #endif
                Light L = GetMainLight();
                L.shadowAttenuation = VegShadow(i.positionWS);
                half NoL = dot(n, L.direction);
                half sun = saturate(NoL) + _Transmission * saturate(-NoL);
                // r11 sheen: the waxy leaf / needle surface mirrors a few percent of the sky whatever its pigment (the
                // grey-green of foliage under an overcast sky); dark needles (albedo 0.035) were black under the toe.
                half3 color = albedo * (L.color * (sun * L.shadowAttenuation * L.distanceAttenuation * occS))
                            + (albedo + _KamionLeafAmbient.y * step(_Cull, 0.5h)) * (ambient * occA);
                color = KamionMixFog(color, i.fogFactor);
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
            struct V { float4 positionCS : SV_POSITION; float4 uv : TEXCOORD0; half t : TEXCOORD1; };
            V vert(A v)
            {
                UNITY_SETUP_INSTANCE_ID(v);
                V o;
                float3 pw = TransformObjectToWorld(VegPositionOS(v.positionOS.xyz, v.uv));
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
                o.uv = VegUV(v.uv);
                o.t = VegBlend(v.uv);
                return o;
            }
            half4 frag(V i) : SV_Target
            {
                clip(VegAlpha(i.uv, i.t) - _Cutoff);
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
            struct V { float4 positionCS : SV_POSITION; float4 uv : TEXCOORD0; half t : TEXCOORD1; };
            V vert(A v)
            {
                UNITY_SETUP_INSTANCE_ID(v);
                V o;
                o.positionCS = VegClipPos(v.positionOS.xyz, v.uv);
                o.uv = VegUV(v.uv);
                o.t = VegBlend(v.uv);
                return o;
            }
            half4 frag(V i) : SV_Target
            {
                clip(VegAlpha(i.uv, i.t) - _Cutoff);
                return 0;
            }
            ENDHLSL
        }
    }
    FallBack Off
}
