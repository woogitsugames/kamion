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
        // ADR 0352: per-tree variation of instanced tree foliage (0 = off: hedges, Fab plants, HLOD walls).
        _TreeVar ("Tree variation: x brightness +-, y hue +-, z crown clump shading, w clump frequency (rad / m)", Vector) = (0, 0, 0, 1.5)
        // crown-lod-s24: LOD1 end distance of the tree (m at LOD scale 1; WorldInstances sets it on the runtime copies). 0 = no fade.
        [HideInInspector] _LodFadeEndM ("LOD1 -> impostor fade end (m at scale 1)", Float) = 0
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
            float4 _TreeVar;
            half _LodFadeEndM;
        CBUFFER_END
        TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
        TEXTURE2D(_NormalOcc); SAMPLER(sampler_NormalOcc);
        #include "Assets/_Project/Rendering/Shaders/KamionFarRing.hlsl"   // ADR 0354: far-field curtains (_HLOD_EDGE + renderer user value) clipped beyond loaded tiles
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
            // crown-lod-s24: the two views are 60 deg apart - a linear blend over the whole sector laid two different crowns
            // over each other (a soft, "melting" double image at 50 %). One view for most azimuths, a cross-fade only over
            // the middle +-0.2 of the sector (24 deg); WORKING_VALUE from the knyszyn-w spawn view of build #10.
            o.t = (half)smoothstep(0.3, 0.7, f - i0);
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

        // ADR 0352 (critic s24 wave 11 # 10: every crown of a species the same green, a rigid light / dark gradient).
        // Per-tree seed from the instance matrix: yaw and height scale differ per instance and do not change when the
        // floating origin moves the region root (a hash of the world position would re-tint every tree on a shift).
        // Every LOD of a tree is drawn with the same matrix, so cards and impostor take the same tint.
        half2 TreeSeed()
        {
            float3 ax = UNITY_MATRIX_M._m00_m10_m20, az = UNITY_MATRIX_M._m02_m12_m22;
            float2 k = float2(dot(float3(ax.x, ax.z, az.z), float3(127.1, 311.7, 74.7)), dot(float3(ax.z, az.x, ax.y + 1.0), float3(269.5, 183.3, 246.1)));
            return (half2)frac(sin(k) * 43758.5453);
        }
        // Albedo multiplier of the tree: brightness +-x, hue +-y (+ = yellower / sunlit, - = cooler blue-green).
        half3 TreeTint(half2 s)
        {
            half h = _TreeVar.y * (s.y * 2.0 - 1.0);
            return half3(1.0 + h, 1.0, 1.0 - 1.5 * h) * (1.0 + _TreeVar.x * (s.x * 2.0 - 1.0));
        }
        // Smooth pseudo-noise (-1..1) over the crown in model metres, phase per tree: lit and shaded clumps of foliage
        // a few metres across instead of one top-to-bottom ramp. Two warped sines: no texture, vertex stage only.
        half TreeClump(float3 positionOS, half2 s)
        {
            float3 p = positionOS * _TreeVar.w + float3(s.x, s.y, s.x + s.y) * 17.0;
            return (half)(sin(p.x + 1.7 * sin(p.z * 0.83 + p.y * 0.6)) * sin(p.y * 1.31 + 1.3 * sin(p.x * 0.71 - p.z * 1.13)));
        }

        // Alpha-to-coverage edge: alpha sharpened to ~1 pixel around the cutoff (as URP Lit's SharpenAlpha).
        // crown-lod-s24 (critic build #10 TOP 3): the GPU dithers a fractional coverage alpha into a screen-space sample
        // pattern (NVIDIA ordered dither) - a minified crown, all partial coverage, read as fixed stipple. Snapped to whole
        // samples of the target (global _KamionVegMsaa, Game.Rendering.VegetationCoverage; 0 = off) there is nothing left
        // to dither; 1 sample (mirrors without MSAA) = a plain 0.5 alpha test.
        half _KamionVegMsaa;
        half CoverageAlpha(half a, half cutoff)
        {
            half c = saturate((a - cutoff) / max(fwidth(a), 0.0001) + 0.5);
            return _KamionVegMsaa > 0.5 ? round(c * _KamionVegMsaa) / _KamionVegMsaa : c;
        }

        // crown-lod-s24: LOD1 leaf cards -> impostor cross-fade. Inside the last _KamionTreeFade.y of the LOD1 distance
        // WorldInstances draws both LODs of a tree; the cards' alpha cutoff rises to above 1 and the impostor's falls from
        // above 1 to its own, so the crown changes by leaf / texel shape (a dissolve in the texture) instead of a hard pop
        // or a screen-space dither pattern. Per instance from the camera distance to the tree origin (vertex stage, same
        // value on both passes). Global per camera (WorldInstances): x = tree card LOD scale, y = band share, z = 1 on.
        float4 _KamionTreeFade;
        half VegCutoff()
        {
        #if defined(_HLOD_EDGE)
            return _Cutoff;
        #else
            float e = _LodFadeEndM * _KamionTreeFade.x;
            if (_KamionTreeFade.z < 0.5 || e <= 0.0) return _Cutoff;
            float band = max(e * _KamionTreeFade.y, 0.001);
            half f = (half)saturate((distance(_WorldSpaceCameraPos, UNITY_MATRIX_M._m03_m13_m23) - (e - band)) / band);
        #if defined(_IMPOSTOR)
            return lerp(1.02h, _Cutoff, f);
        #else
            return lerp(_Cutoff, 1.02h, f);
        #endif
        #endif
        }

        // far-forest-look-s24 (ADR 0330 addendum 3): far-field curtains carry the column height H [m] in TEXCOORD1.y
        // (same on the bottom and top vertex of a column). v * H and H are affine across both triangles of a quad whose
        // columns differ in height, so v = (v * H) / H follows each column linearly: no diagonal crease or sheared crowns
        // (plain affine v bends along the triangle split - ADR 0330 r2 limited the slope to 14.6 deg, it did not remove
        // it). H = 0 (tile HLOD walls without TEXCOORD1, old far fields, the crossed impostors) keeps the plain v.
        // Packed into the free zw of the non-impostor UV: (u, v, v * H, H); EdgeUV returns (u, v) - one divide per pixel.
        float4 EdgeUVQ(float4 uv, float h)
        {
            return h > 0.0 ? float4(uv.xy, uv.y * h, h) : float4(uv.xy, uv.y, 1.0);
        }
        float4 EdgeUV(float4 uv)
        {
            float v = uv.z / max(uv.w, 1e-4);
            return float4(uv.x, v, uv.x, v);
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
            struct A
            {
                float4 positionOS : POSITION; float2 uv : TEXCOORD0;
            #if defined(_HLOD_EDGE)
                float2 uv1 : TEXCOORD1;          // y = curtain column height (far-forest-look-s24)
            #endif
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };
            struct V
            {
                float4 positionCS : SV_POSITION; float4 uv : TEXCOORD0; half2 t : TEXCOORD1;   /* x view blend, y alpha cutoff (crown-lod-s24) */
            #if defined(_HLOD_EDGE)
                float2 positionWSxz : TEXCOORD2; float3 farOwner : TEXCOORD3;   // ADR 0354 far-field ring clip
            #endif
                UNITY_VERTEX_OUTPUT_STEREO
            };
            V vert(A v)
            {
                V o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.positionCS = VegClipPos(v.positionOS.xyz, v.uv);
                o.uv = VegUV(v.uv);
                o.t = half2(VegBlend(v.uv), VegCutoff());
            #if defined(_HLOD_EDGE)
                o.positionWSxz = TransformObjectToWorld(v.positionOS.xyz).xz;
                o.farOwner = KamionFarRingOwner();
                o.uv = EdgeUVQ(o.uv, v.uv1.y);
            #endif
                return o;
            }
            half4 frag(V i) : SV_Target
            {
            #if defined(_HLOD_EDGE)
                if (KamionFarRingHidden(i.positionWSxz, i.farOwner)) discard;
                i.uv = EdgeUV(i.uv);
            #endif
                half a = VegAlpha(i.uv, i.t.x);
                // Alpha-to-coverage path still discards the fully uncovered texels (as URP Lit): the coverage mask alone
                // is not applied on every target (A16 Vulkan: cards rendered as opaque quads without this clip).
                if (_AlphaToMask > 0.5) { half c = CoverageAlpha(a, i.t.y); clip(c - 0.0001); return half4(0, 0, 0, c); }
                clip(a - i.t.y);
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
            struct A
            {
                float4 positionOS : POSITION; float3 normalOS : NORMAL; float2 uv : TEXCOORD0;
            #if defined(_HLOD_EDGE)
                float2 uv1 : TEXCOORD1;          // ADR 0330 addendum: x = extra foreshortened distance [m] on far_field (0 on tile HLOD), y = column height (far-forest-look-s24)
            #endif
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };
            struct V
            {
                float4 positionCS : SV_POSITION;
                float4 uv : TEXCOORD0;
                float3 positionWS : TEXCOORD1;
                half3 normalWS : TEXCOORD2;
                half2 fogFactor : TEXCOORD3;     // x fog, y alpha cutoff (crown-lod-s24 LOD fade)
                half3 ambient : TEXCOORD4;
            #if defined(_IMPOSTOR)
                half3 rightWS : TEXCOORD5;
                half3 upWS : TEXCOORD6;
                half4 ambUpT : TEXCOORD7;        // xyz SH towards up, w view blend weight
                half3 ambDown : TEXCOORD8;
            #elif defined(_HLOD_EDGE) && defined(_KAMION_VEG_FAST)
                half3 ambL2 : TEXCOORD5;         // L2 SH band of the wall normal (even in n: valid for both faces)
            #endif
            #if defined(_HLOD_EDGE)
                float3 farOwner : TEXCOORD6;     // ADR 0354 far-field ring clip
            #endif
            #if !defined(_HLOD_EDGE)
                half4 treeVar : TEXCOORD9;       // ADR 0352: rgb albedo multiplier of this tree, a crown clump noise (-1..1; cards)
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
                o.treeVar = half4(TreeTint(TreeSeed()), 0.0);
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
            #if !defined(_HLOD_EDGE)
                {
                    half2 seed = TreeSeed();
                    half clump = TreeClump(pOS, seed) * step(0.0001, _TreeVar.z);
                    o.treeVar = half4(TreeTint(seed) * (1.0 + 0.5 * _TreeVar.z * clump), clump);
                }
            #endif
            #endif
                o.positionWS = TransformObjectToWorld(pOS);
                o.positionCS = TransformWorldToHClip(o.positionWS);
            #if defined(_HLOD_EDGE)
                o.fogFactor = half2(KamionFogTauExtra(o.positionWS, o.positionCS.w, max(v.uv1.x, 0.0)), _Cutoff);
                o.farOwner = KamionFarRingOwner();
                o.uv = EdgeUVQ(o.uv, v.uv1.y);
            #else
                o.fogFactor = half2(KamionFogTau(o.positionWS, o.positionCS.w), VegCutoff());
            #endif
                return o;
            }
            half4 frag(V i, bool front : SV_IsFrontFace) : SV_Target
            {
            #if defined(_HLOD_EDGE)
                if (KamionFarRingHidden(i.positionWS.xz, i.farOwner)) discard;   // ADR 0354
                i.uv = EdgeUV(i.uv);
            #endif
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
                if (_AlphaToMask > 0.5) { alpha = CoverageAlpha(tex.a, i.fogFactor.y); clip(alpha - 0.0001); }
                else clip(tex.a - i.fogFactor.y);
            #if !defined(_HLOD_EDGE)
                half3 albedo = tex.rgb * i.treeVar.rgb;
            #else
                half3 albedo = tex.rgb;
            #endif
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
                // ADR 0352: the ramp follows the foliage clumps (+-0.45 of the normal's height), not one level line.
                occA = lerp(1.0 - _CrownShade, 1.0, smoothstep(-0.6, 0.75, normalize(i.normalWS).y + 0.45 * i.treeVar.a));
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
                    // ADR 0330 r2: normalize T and B independently — in the stacked far atlas (v compressed ~11x),
                    // sharing max(|T|, |B|) crushed vertical normal relief B by ~11x and skewed oblique quads.
                    float invT = rsqrt(max(dot(T, T), 1e-12));
                    float invB = rsqrt(max(dot(B, B), 1e-12));
                    n = normalize(T * invT * nxy.x + B * invB * nxy.y + n * nz);
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
                color = KamionMixFog(color, i.fogFactor.x);
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
            struct A
            {
                float4 positionOS : POSITION; float3 normalOS : NORMAL; float2 uv : TEXCOORD0;
            #if defined(_HLOD_EDGE)
                float2 uv1 : TEXCOORD1;
            #endif
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };
            struct V { float4 positionCS : SV_POSITION; float4 uv : TEXCOORD0; half2 t : TEXCOORD1;   /* x view blend, y alpha cutoff (crown-lod-s24) */ };
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
            #if defined(_HLOD_EDGE)
                o.uv = EdgeUVQ(o.uv, v.uv1.y);
            #endif
                o.t = half2(VegBlend(v.uv), VegCutoff());
                return o;
            }
            half4 frag(V i) : SV_Target
            {
            #if defined(_HLOD_EDGE)
                i.uv = EdgeUV(i.uv);
            #endif
                clip(VegAlpha(i.uv, i.t.x) - i.t.y);
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
            struct A
            {
                float4 positionOS : POSITION; float2 uv : TEXCOORD0;
            #if defined(_HLOD_EDGE)
                float2 uv1 : TEXCOORD1;          // y = curtain column height (far-forest-look-s24)
            #endif
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };
            struct V
            {
                float4 positionCS : SV_POSITION; float4 uv : TEXCOORD0; half2 t : TEXCOORD1;   /* x view blend, y alpha cutoff (crown-lod-s24) */
            #if defined(_HLOD_EDGE)
                float2 positionWSxz : TEXCOORD2; float3 farOwner : TEXCOORD3;   // ADR 0354 far-field ring clip
            #endif
            };
            V vert(A v)
            {
                UNITY_SETUP_INSTANCE_ID(v);
                V o;
                o.positionCS = VegClipPos(v.positionOS.xyz, v.uv);
                o.uv = VegUV(v.uv);
                o.t = half2(VegBlend(v.uv), VegCutoff());
            #if defined(_HLOD_EDGE)
                o.positionWSxz = TransformObjectToWorld(v.positionOS.xyz).xz;
                o.farOwner = KamionFarRingOwner();
                o.uv = EdgeUVQ(o.uv, v.uv1.y);
            #endif
                return o;
            }
            half4 frag(V i) : SV_Target
            {
            #if defined(_HLOD_EDGE)
                if (KamionFarRingHidden(i.positionWSxz, i.farOwner)) discard;
                i.uv = EdgeUV(i.uv);
            #endif
                clip(VegAlpha(i.uv, i.t.x) - i.t.y);
                return 0;
            }
            ENDHLSL
        }
    }
    FallBack Off
}
