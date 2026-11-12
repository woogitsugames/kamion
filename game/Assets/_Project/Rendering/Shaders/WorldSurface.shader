// World surfaces from the region generator (terrain, carriageways, kerbs, sidewalks, bridges, markings).
// - World-space planar projection (XZ for up-facing, XY/ZY for walls): generator UVs are not needed, no seams between
//   chunks, texel density fixed in metres (_TileSize).
// - Anti-tiling: tier keyword _KAMION_WORLD_DETAIL adds a second sample at a different scale rotated by 37° and a
//   second macro-noise octave; without it (Low tier) one detail sample + one macro sample.
// - Albedo is calibrated: texture mean ≈ 0.5 (linear), result = _BaseColor × 2 × tex, so _BaseColor is the mean albedo
//   from the world manifest (asphalt 0.075, grass 0.11/0.15/0.06 …).
// - Markings: polygon offset (_OffsetFactor/_OffsetUnits) instead of relying on the +6 mm lift alone - 24-bit depth at
//   200 m resolves only ~5 cm with a 0.05 m near plane, so the lift alone z-fights.
// - Lighting: Lambert + Unity's minimalist GGX for the sun (with cascaded shadows), L2 SH ambient, environment reflection
//   with Fresnel, exponential fog. SRP-batcher compatible.
// - Far facades (_FAR_FACADE, ADR 0015 §2): LOD1 office/block walls carry a window grid in TEXCOORD_1 (one unit = one
//   window bay x one storey, pane rectangle _WindowGrid = (u0, u1, v0, v1) inside the unit). Panes are box-filtered by
//   the pixel footprint and fade to their mean coverage once a bay is smaller than ~1.5 px (no moire far away); per-pane
//   tone from a hash of the bay/storey index (blinds, curtains, dark rooms). Rows with storey index < 0 (plinth strip)
//   have no panes.
// - Street lamps at dusk (review r4 L3): _Emission (luminance cd/m^2, linear RGB; lamp glass materials, StreetLamps)
//   x global _KamionStreetLamps (0..1, from the sun elevation) x _KamionExposure; and (ADR 0062, every tier) analytic
//   light pools of the _KamionLampCount lamp heads nearest the view (_KamionLampPos xyz + fade weight, _KamionLampColor =
//   I·k/π): inverse-square Lambert with a full-cutoff luminaire (constant to 60° from the nadir, zero at 75°) and URP's
//   smooth range window (35 m) - a uniform-branch loop, no extra variants, no lights. The StreetLamps point lights
//   (High) light vehicles and props only; this shader no longer reads URP's additional lights.
Shader "Kamion/World Surface"
{
    Properties
    {
        _BaseColor ("Mean albedo (linear)", Color) = (0.5, 0.5, 0.5, 1)
        _BaseMap ("Detail albedo (mean 0.5, linear)", 2D) = "grey" {}
        _TileSize ("Detail tile size (m)", Float) = 4
        _DetailScale ("Second sample scale", Float) = 2.71
        _DetailMix ("Second sample weight", Range(0, 1)) = 0.5
        _MacroMap ("Macro noise (R: 1st octave, G: 2nd)", 2D) = "grey" {}
        _MacroSize ("Macro tile size (m)", Float) = 61
        _MacroStrength ("Macro albedo variation", Range(0, 1)) = 0.25
        _MacroTint ("Macro tint (multiplied where noise is high)", Color) = (1, 1, 1, 1)
        _DryTint ("Unmown / dry grass tint (ground masks B)", Color) = (1.22, 1.08, 0.72, 1)
        _Smoothness ("Smoothness", Range(0, 1)) = 0.1
        _SmoothnessVar ("Smoothness from detail (polish)", Range(0, 1)) = 0
        _Occlusion ("Ambient occlusion", Range(0, 1)) = 1
        _FadeWidth ("Marking line width for distance pre-filter (m, 0 = off)", Float) = 0
        _FadeColor ("Pre-filter background albedo (linear)", Color) = (0.075, 0.075, 0.072, 1)
        _OffsetFactor ("Depth offset factor", Float) = 0
        _OffsetUnits ("Depth offset units", Float) = 0
        [Toggle] _ReceiveShadows ("Receive shadows", Float) = 1
        _WindowGrid ("Far facade pane rect in a bay (u0, u1, v0, v1)", Vector) = (0.25, 0.75, 0.3, 0.8)
        _GlassColor ("Far facade glass albedo (linear)", Color) = (0.03, 0.035, 0.04, 1)
        _SkyOcc ("Sky occlusion: x down-facing ambient, y horizon reflection (0 = off; ADR 0060)", Vector) = (0, 0, 0, 0)
        _ArchitecturalGlass ("Architectural glass shadow receiver (ADR0098)", Float) = 0
        _Emission ("Emission luminance (cd/m2, linear; street lamp glass)", Color) = (0, 0, 0, 0)
        [Enum(UnityEngine.Rendering.CullMode)] _Cull ("Cull (lamp glass: Off - the generator's glass quad faces up)", Float) = 2
        [Toggle] _GroundMasks ("Terrain ground masks from COLOR_0 (R road distance/20 m, G forest floor, B unmown, A bare soil)", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" "UniversalMaterialType" = "Lit" }

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        CBUFFER_START(UnityPerMaterial)
            float4 _BaseColor;
            float4 _BaseMap_ST;
            float4 _MacroMap_ST;
            float4 _MacroTint;
            float4 _DryTint;
            float4 _FadeColor;
            float _FadeWidth;
            float _TileSize, _DetailScale, _DetailMix, _MacroSize, _MacroStrength;
            float _Smoothness, _SmoothnessVar, _Occlusion, _OffsetFactor, _OffsetUnits, _ReceiveShadows, _GroundMasks;
            float4 _WindowGrid;
            float4 _GlassColor;
            float4 _Emission;
            float4 _SkyOcc;
            float _ArchitecturalGlass;
        CBUFFER_END
        float _KamionStreetLamps, _KamionLampLights, _KamionExposure;
        float _KamionGlassShadowBias;
        #include "KamionLampPools.hlsl"
        #include "VegetationGround.hlsl"
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Offset [_OffsetFactor], [_OffsetUnits]
            Cull [_Cull] ZWrite On

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #pragma multi_compile_fragment _ _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile _ _KAMION_WORLD_DETAIL
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            #pragma shader_feature_local _FAR_FACADE

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Assets/_Project/Rendering/Shaders/KamionAtmosphere.hlsl"   // ADR 0080 height haze, Low tone toe, wetness
            #include "Assets/_Project/Rendering/Shaders/KamionWetReflections.hlsl" // ADR 0108 optional existing-cube wet response
            #include "Assets/_Project/Rendering/Shaders/KamionWorldGI.hlsl"   // ADR 0064 baked sky visibility + far ground shadows

            TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
            TEXTURE2D(_MacroMap); SAMPLER(sampler_MacroMap);

            struct Attributes
            {
                float4 positionOS : POSITION; float3 normalOS : NORMAL; half4 color : COLOR;
            #if defined(_FAR_FACADE)
                float2 uv1 : TEXCOORD1;
            #endif
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                half3 normalWS : TEXCOORD1;
                half fogFactor : TEXCOORD2;
                half4 masks : TEXCOORD3;
            #if defined(_FAR_FACADE)
                float2 uv1 : TEXCOORD4;
            #endif
                UNITY_VERTEX_INPUT_INSTANCE_ID
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings vert(Attributes v)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_TRANSFER_INSTANCE_ID(v, o);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                VertexPositionInputs p = GetVertexPositionInputs(v.positionOS.xyz);
                o.positionCS = p.positionCS;
                o.positionWS = p.positionWS;
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                o.fogFactor = KamionFogTau(p.positionWS, p.positionCS.w);
                o.masks = v.color;
            #if defined(_FAR_FACADE)
                o.uv1 = v.uv1;
            #endif
                return o;
            }

            // Planar projection in world metres; uses the absolute world position so chunks tile seamlessly.
            float2 ProjectUV(float3 pw, half3 n)
            {
                half3 a = abs(n);
                if (a.y >= 0.7) return pw.xz;
                return a.x > a.z ? pw.zy : pw.xy;
            }

            half4 frag(Varyings i) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                half3 n = normalize(i.normalWS);
                float2 uvm = ProjectUV(i.positionWS, n);

                half det = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uvm / _TileSize).r;
                half macro = SAMPLE_TEXTURE2D(_MacroMap, sampler_MacroMap, uvm / _MacroSize).r;
            #if defined(_KAMION_WORLD_DETAIL)
                const float2x2 rot = float2x2(0.7986, -0.6018, 0.6018, 0.7986);   // 37°
                half det2 = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, mul(rot, uvm) / (_TileSize * _DetailScale) + 0.37).r;
                det = lerp(det, det2, _DetailMix);
                half macro2 = SAMPLE_TEXTURE2D(_MacroMap, sampler_MacroMap, mul(rot, uvm) / (_MacroSize * 4.13)).g;
                macro = macro * 0.6 + macro2 * 0.4;
            #endif
                // Detail texture mean 0.5 → ×2; macro mean 0.5 → ±strength.
                half m = (macro - 0.5) * 2.0;
                half3 albedo = _BaseColor.rgb * (2.0 * det) * (1.0 + _MacroStrength * m);
                albedo *= lerp(half3(1, 1, 1), _MacroTint.rgb, saturate(m));
                if (_GroundMasks > 0.5)
                {
                    // Generator ground masks (docs/WORLD_GENERATION.md): G forest floor (needle/leaf litter with moss),
                    // B unmown grass (drier, yellower), A bare soil; R = distance to road or yard / 20 m → a 1 m strip of
                    // grit and sand along the paved edge. Albedos are linear means (WORKING_VALUE, judged against the
                    // Blender control renders until photo scans exist).
                    half4 k = i.masks;
                    half3 detail = (2.0 * det) * (1.0 + _MacroStrength * m);
                    albedo = lerp(albedo, albedo * _DryTint.rgb, k.b * 0.8);
                    // Same ground-mask response as World PBR; no extra samples or passes.
                    albedo = KamionGrassDryMatter(albedo, k, 1.0h);
                    albedo = lerp(albedo, half3(0.085, 0.072, 0.045) * detail, k.g);
                    albedo = lerp(albedo, half3(0.13, 0.11, 0.085) * detail, k.a);
                    half grit = KamionGrassGrit(k, macro);
                    albedo = lerp(albedo, half3(0.19, 0.17, 0.14) * detail, grit);
                }
                albedo = saturate(albedo);
                // Markings: a 0.12 m line covers less than a pixel at distance / grazing angles; the geometry then
                // sparkles. Pre-filter: blend towards the road albedo by the line's pixel coverage (fwidth footprint).
                if (_FadeWidth > 0.0)
                {
                    float footprint = length(fwidth(i.positionWS.xz));
                    half coverage = saturate(_FadeWidth * 1.5 / max(footprint, 1e-4));
                    albedo = lerp(_FadeColor.rgb, albedo, coverage);
                }
                half smooth = saturate(_Smoothness + _SmoothnessVar * (det - 0.5));
            #if defined(_FAR_FACADE)
                {
                    albedo *= i.masks.rgb;
                    float2 g = i.uv1;
                    float2 bay = floor(g);
                    float2 f = g - bay;
                    float2 fw = max(fwidth(g), 1e-4);
                    half isRibbon = step(0.6, i.masks.a) * step(i.masks.a, 0.88);
                    float4 wg = lerp(_WindowGrid, float4(0.08, 0.92, 0.32, 0.76), isRibbon);
                    // Box-filtered pane rectangle (signed distance to the nearest edge in pixels, clamped).
                    half mx = saturate(min(f.x - wg.x, wg.y - f.x) / fw.x + 0.5);
                    half my = saturate(min(f.y - wg.z, wg.w - f.y) / fw.y + 0.5);
                    half row = step(0.0, bay.y) * step(0.5, i.masks.a);
                    half mean = (wg.y - wg.x) * (wg.w - wg.z);
                    half sub = saturate(max(fw.x, fw.y) * 1.5 - 0.5);   // bay < ~1.5 px: use the mean coverage
                    half pane = lerp(mx * my, mean, sub) * row;
                    float h = frac(sin(dot(bay, float2(12.9898, 78.233))) * 43758.5453);
                    // Dark glass with the room behind it; ~1 in 6 panes with light blinds / curtains (WORKING_VALUE).
                    half3 glass = _GlassColor.rgb * lerp(0.75, 1.6, h);
                    glass = lerp(glass, half3(0.32, 0.30, 0.27), step(0.84, h) * 0.6);
                    glass = lerp(glass, _GlassColor.rgb * 1.15, sub);
                    albedo = lerp(albedo, glass, pane);
                    smooth = lerp(smooth, 0.9, pane * (1.0 - sub * 0.5));
                }
            #endif

                {
                    half3 tnWet = half3(0, 0, 1);
                    KamionWetSurface(n, macro, _GroundMasks > 0.5 ? 0.0 : step(0.95, n.y), _GroundMasks > 0.5 ? 0.15 : 1.0, albedo, smooth, tnWet);   // ADR 0080
                }
                float3 V = GetWorldSpaceNormalizeViewDir(i.positionWS);
                half NoV = saturate(dot(n, V));
                half perceptualRoughness = 1.0 - smooth;
                half r = max(perceptualRoughness * perceptualRoughness, 0.002);
                half r2 = r * r;
                const half3 specColor = half3(0.04, 0.04, 0.04);

                // Sun
                float3 shadowReceiver = i.positionWS;
                // ADR0098: explicit imported glazing semantic, not a roughness heuristic.
                // Bounded receiver-normal offset retains cast/frame shadows and does not move geometry.
                if (_KamionGlassShadowBias > 0.0 && _ArchitecturalGlass > 0.5)
                    shadowReceiver += n * _KamionGlassShadowBias;
                float4 shadowCoord = TransformWorldToShadowCoord(shadowReceiver);
                Light L = GetMainLight(shadowCoord, i.positionWS, half4(1, 1, 1, 1));
                half giK, giSun;
                KamionWorldGI(i.positionWS, n, giK, giSun);
                half atten = L.distanceAttenuation * lerp(1.0, KamionFarShadow(L.shadowAttenuation, giSun, i.positionWS), _ReceiveShadows);
                half NoL = saturate(dot(n, L.direction));
                float3 H = SafeNormalize(float3(L.direction) + V);
                half NoH = saturate(dot(n, H));
                half LoH = saturate(dot(L.direction, H));
                float d = NoH * NoH * (r2 - 1.0) + 1.00001;
                half spec = r2 / ((d * d) * max(0.1, LoH * LoH) * (r * 4.0 + 2.0));
                half3 color = (albedo * (1.0 - 0.04) + specColor * spec) * L.color * (atten * NoL);

                // Ambient: L2 SH (sky + ground) and environment reflection
                // sky occlusion (ADR 0060) on top of baked sky visibility giK (ADR 0064)
                half3 ambient = SampleSH(n) * albedo * (_Occlusion * giK) * (1.0 - _SkyOcc.x * saturate(-n.y));
                half3 R = reflect(-V, n);
                half fresnel = Pow4(1.0 - NoV);
                half grazing = saturate(smooth + 0.04);
                half3 env = KamionWetEnvironment(R, i.positionWS, n, perceptualRoughness, _Occlusion * giK) * lerp(specColor, grazing.xxx, fresnel) / (r2 + 1.0);
                env *= 1.0 - _SkyOcc.y * (1.0 - smoothstep(0.05, 0.45, R.y));
                color += ambient + env;
                color += albedo * KamionLampPools(i.positionWS, n);   // ADR 0062
                color += _Emission.rgb * (_KamionStreetLamps * _KamionExposure);

                color = KamionMixFog(color, i.fogFactor);
                return half4(color, 1.0);
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
            #pragma multi_compile_instancing
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"

            float3 _LightDirection;
            float3 _LightPosition;

            struct A { float4 positionOS : POSITION; float3 normalOS : NORMAL; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct V { float4 positionCS : SV_POSITION; };

            V ShadowVert(A v)
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
                return o;
            }
            half4 ShadowFrag(V i) : SV_Target { return 0; }
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode" = "DepthOnly" }
            ZWrite On ColorMask R Cull Back
            Offset [_OffsetFactor], [_OffsetUnits]

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex DepthVert
            #pragma fragment DepthFrag
            #pragma multi_compile_instancing
            struct A { float4 positionOS : POSITION; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct V { float4 positionCS : SV_POSITION; };
            V DepthVert(A v) { UNITY_SETUP_INSTANCE_ID(v); V o; o.positionCS = TransformObjectToHClip(v.positionOS.xyz); return o; }
            half4 DepthFrag(V i) : SV_Target { return 0; }
            ENDHLSL
        }
    }
    Fallback Off
}
