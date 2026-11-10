// Kamion/World PBR - generated PBR texture sets of the world (art-source/world/materials, ADR 0022).
// Contract: art-source/world/materials/materials_spec.json (packing, tile size, UV mode per set):
//   _BaseMap   sRGB albedo. "calibrated" sets carry the real albedo (_Tint = 1, _AlbedoScale = 1); "modulation" sets
//              (facades, props) are neutral grey with mean 0.5 and are tinted by the manifest colour (_AlbedoScale 2).
//   _NormalMap tangent space, OpenGL (+Y = +v).
//   _MaskMap   R metallic, G occlusion, B detail mask, A smoothness (Toksvig-filtered per tier by the generator).
//   _VarMap    R height, G element id (point sampled), B joint / crack / bare mask, A convexity (edge wear).
//   _MacroMap  macro_variation (64 m): R 8-64 m tone, G 2-16 m tone, B wear / dirt patches, A 0.5-4 m mottling.
// UV source (keywords): world planar (default; up-facing XZ, walls XY / ZY, absolute world metres so chunks tile
// seamlessly), _UV_MESH0 (TEXCOORD_0 in metres: kerbs, walls, props), _UV_MESH1 (TEXCOORD_1 in metres along / across
// the road: road_concrete joints follow the carriageway).
// Layers (keywords): _ROADWEAR (TEXCOORD_1 = lane coordinate, distance to the carriageway edge: polished wheel paths,
// gutter grime), _CRACKS (16 m crack layer, faded by the macro wear mask so whole stretches stay sound),
// _DECAL_PATCH (TEXCOORD_1.x = age: new black patch -> greyed like the road), _DECAL_ALPHA (alpha-blended decals:
// oil atlas 2x2 picked by TEXCOORD_1.y, tyre scrub profile across TEXCOORD_0.y, opacity x TEXCOORD_1.y), _GROUNDMASKS (terrain COLOR_0:
// R road distance / 20 m, G forest floor, B unmown, A bare soil), _SPLASH (walls: splash / dirt zone above the ground
// from TEXCOORD_0.y = metres above ground).
// _DECAL_PAINT (road markings, review r6 W-H6, ADR 0049): the base set is the road's own asphalt_worn in the same world
// planar UV; the paint film (_PaintColor) covers it except where TEXCOORD_1 (lane coordinate, exposure + age) says
// the wheels wore it through on the aggregate peaks (Var.R); grey-brown traffic film by age; distance pre-filter
// towards the asphalt by the line's pixel coverage.
// _GRASS_DETILE (grass sets: macro-masked bare soil, rotated second sample on Medium+; review r5 W-N3, ADR 0042).
// _CARPAINT (parked-car paint, ADR 0078): two-layer paint. Base coat = the tinted car_grime albedo with _CarPaint.x
// metal (aluminium flake / mica; 0 = solid colour) at roughness _CarPaint.w; clear coat = F0 0.04 GGX + sharp
// environment reflection at the set's smoothness (so road film and dust still matt it). Medium+ (_KAMION_WORLD_DETAIL):
// flake sparkle, a per-cell (object space, _CarFlake.x cells / m) tilt of the base-coat normal by _CarPaint.y, faded
// out once a pixel covers a cell (no shimmer / moire at distance; at 1080 rows that is beyond ~3.5 m). Pearl (_CarPaint.z): base-coat reflection shifts towards
// _PearlTint at grazing angles. Low: no flake, 0 extra fetches; cost = one more GGX lobe and env sample.
// Global tier keyword _KAMION_WORLD_DETAIL (Medium and up): element tone jitter, crack layer, second rotated macro
// octave, close-range photo detail (asphalt) - Low draws base + normal + mask + one macro sample only.
// Anti-shimmer: mips + per-tier aniso (QualityProfile), Toksvig smoothness from the generator, element jitter and
// photo detail fade out by pixel footprint / distance.
Shader "Kamion/World PBR"
{
    Properties
    {
        _BaseMap ("Base colour (sRGB)", 2D) = "grey" {}
        [Normal] _NormalMap ("Normal (OpenGL)", 2D) = "bump" {}
        _MaskMap ("Mask (R metal, G AO, B detail, A smoothness)", 2D) = "white" {}
        _VarMap ("Var (R height, G id, B joint, A convexity)", 2D) = "black" {}
        _MacroMap ("Macro variation (64 m)", 2D) = "grey" {}
        _CrackMap ("Crack layer mask", 2D) = "black" {}
        [Normal] _CrackNormal ("Crack layer normal", 2D) = "bump" {}
        _DetailAlbedo ("Photo detail albedo (x2 neutral)", 2D) = "grey" {}
        [Normal] _DetailNormal ("Photo detail normal", 2D) = "bump" {}
        _Tint ("Tint (linear, multiplies the texture)", Color) = (1, 1, 1, 1)
        _AlbedoScale ("Albedo scale (1 calibrated, 2 modulation)", Float) = 1
        _Tile ("Tile size (m): xy base, z crack layer, w photo detail", Vector) = (4, 4, 16, 1)
        _NormalStrength ("Normal strength", Range(0, 2)) = 1
        _SmoothnessScale ("Smoothness scale", Range(0, 2)) = 1
        _MetallicScale ("Metallic scale", Range(0, 1)) = 0
        _ElementJitter ("Element tone jitter (Var.G)", Range(0, 0.5)) = 0
        _ElementSize ("Element size (m, for the jitter fade)", Float) = 0.2
        _MacroSize ("Macro size (m)", Float) = 64
        _MacroStrength ("Macro tone strength", Range(0, 1)) = 0.2
        _MacroWear ("Macro wear-patch strength (B)", Range(0, 1)) = 0.15
        _CrackStrength ("Crack layer strength", Range(0, 1)) = 0.8
        _DetailFade ("Photo detail fade distance (m)", Float) = 25
        _WheelPolish ("Wheel-path polish (_ROADWEAR)", Range(0, 1)) = 0.5
        _GutterDirt ("Gutter grime (_ROADWEAR)", Range(0, 1)) = 0.5
        _DripBand ("Lane-centre oil / soot drip band between the wheel paths (_ROADWEAR)", Range(0, 1)) = 0
        _Grime ("Ground grime (_GRIME): x damp darkening, y damp threshold (macro pool), z joint dirt, w damp gloss", Vector) = (0.45, 0.62, 0.3, 0.5)
        _SkyOcc ("Sky occlusion: x down-facing ambient, y horizon reflection (0 = off; ADR 0060)", Vector) = (0, 0, 0, 0)
        _AgeTint ("Patch age target / base albedo ratio", Float) = 2.0
        _DecalAlpha ("Decal opacity", Range(0, 1)) = 1
        _SplashHeight ("Splash zone height (m)", Float) = 0.6
        _RunoffMap ("Parapet run-off (R soot, G rust; _RUNOFF)", 2D) = "black" {}
        _RunoffStrength ("Parapet run-off strength", Range(0, 1)) = 0.5
        _GroundTint ("Terrain grass ground-mask strength", Range(0, 1)) = 1
        _GrassFill ("Grass refill albedo (_GRASS_DETILE, linear; Vector: no sRGB conversion)", Vector) = (0.079, 0.109, 0.037, 1)
        _Stripe ("Stripes (_STRIPES): xy direction in UV0 metres, z period m", Vector) = (1, 0, 1, 0)
        _StripeA ("Stripe colour A (linear)", Color) = (0.55, 0.03, 0.02, 1)
        _StripeB ("Stripe colour B (linear)", Color) = (0.7, 0.7, 0.68, 1)
        _PaintColor ("Paint film albedo (linear, _DECAL_PAINT), a = smoothness", Vector) = (0.6, 0.6, 0.57, 0.35)
        _PaintWear ("Paint wear: x wheel-path, y age, z dirt film, w line width m", Vector) = (0.85, 0.25, 0.3, 0.12)
        _CarPaint ("Car paint (_CARPAINT): x base metal, y flake tilt, z pearl, w base-coat roughness", Vector) = (0, 0, 0, 0.5)
        _CarFlake ("Car flake: x cells per m, y fade scale (1 = gone when a pixel covers a cell)", Vector) = (400, 1, 0, 0)
        _PearlTint ("Pearl grazing tint (linear)", Color) = (1, 1, 1, 1)
        _OffsetFactor ("Depth offset factor", Float) = 0
        _OffsetUnits ("Depth offset units", Float) = 0
        [Enum(UnityEngine.Rendering.BlendMode)] _SrcBlend ("Src blend", Float) = 1
        [Enum(UnityEngine.Rendering.BlendMode)] _DstBlend ("Dst blend", Float) = 0
        [Toggle] _ZWrite ("ZWrite", Float) = 1
        [Enum(UnityEngine.Rendering.CullMode)] _Cull ("Cull", Float) = 2
        [Toggle] _ReceiveShadows ("Receive shadows", Float) = 1
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" "UniversalMaterialType" = "Lit" }

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        #include "../../Rendering/Shaders/KamionLampPools.hlsl"
        CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_ST;
            float4 _Tint;
            float4 _Tile;
            float _AlbedoScale, _NormalStrength, _SmoothnessScale, _MetallicScale;
            float _ElementJitter, _ElementSize, _MacroSize, _MacroStrength, _MacroWear, _CrackStrength, _DetailFade;
            float _WheelPolish, _GutterDirt, _AgeTint, _DecalAlpha, _SplashHeight, _GroundTint, _RunoffStrength;
            float4 _Stripe, _StripeA, _StripeB;
            float4 _GrassFill;
            float4 _PaintColor, _PaintWear;
            float4 _Grime, _SkyOcc;
            float _DripBand;
            float4 _CarPaint, _CarFlake, _PearlTint;
            float _OffsetFactor, _OffsetUnits, _SrcBlend, _DstBlend, _ZWrite, _Cull, _ReceiveShadows;
        CBUFFER_END
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Blend [_SrcBlend] [_DstBlend]
            ZWrite [_ZWrite]
            Cull [_Cull]
            Offset [_OffsetFactor], [_OffsetUnits]

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #pragma multi_compile_fragment _ _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile _ _KAMION_WORLD_DETAIL
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            #pragma shader_feature_local _ _UV_MESH0 _UV_MESH1
            #pragma shader_feature_local _ROADWEAR
            #pragma shader_feature_local _CRACKS
            #pragma shader_feature_local _PHOTO_DETAIL
            #pragma shader_feature_local _ _DECAL_PATCH _DECAL_ALPHA _DECAL_TYRE _DECAL_GRATE _DECAL_PAINT
            #pragma shader_feature_local _GROUNDMASKS
            #pragma shader_feature_local _GRASS_DETILE
            #pragma shader_feature_local _SPLASH
            #pragma shader_feature_local _RUNOFF
            #pragma shader_feature_local _STRIPES
            #pragma shader_feature_local _GRIME
            #pragma shader_feature_local _CARPAINT

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Assets/_Project/Rendering/Shaders/KamionWorldGI.hlsl"   // ADR 0064 baked sky visibility + far ground shadows

            TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
            TEXTURE2D(_NormalMap); SAMPLER(sampler_NormalMap);
            TEXTURE2D(_MaskMap); SAMPLER(sampler_MaskMap);
            TEXTURE2D(_VarMap); SAMPLER(sampler_point_repeat);
            TEXTURE2D(_MacroMap); SAMPLER(sampler_MacroMap);
            TEXTURE2D(_CrackMap); SAMPLER(sampler_CrackMap);
            TEXTURE2D(_CrackNormal);
            TEXTURE2D(_DetailAlbedo); SAMPLER(sampler_DetailAlbedo);
            TEXTURE2D(_DetailNormal);
            TEXTURE2D(_RunoffMap);

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                half4 color : COLOR;
                float2 uv0 : TEXCOORD0;
                float2 uv1 : TEXCOORD1;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                half3 normalWS : TEXCOORD1;
                half fogFactor : TEXCOORD2;
                half4 masks : TEXCOORD3;
                float4 uv : TEXCOORD4;      // xy TEXCOORD_0, zw TEXCOORD_1
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
                o.fogFactor = ComputeFogFactor(p.positionCS.z);
                o.masks = v.color;
                o.uv = float4(v.uv0, v.uv1);
                return o;
            }

            float Hash12(float2 p)
            {
                float3 p3 = frac(float3(p.xyx) * 0.1031);
                p3 += dot(p3, p3.yzx + 33.33);
                return frac((p3.x + p3.y) * p3.z);
            }

            // Tangent frame of a mesh UV set from screen derivatives (no tangents in the compact world meshes).
            void CotangentFrame(float3 N, float3 p, float2 uv, out float3 T, out float3 B)
            {
                float3 dp1 = ddx(p), dp2 = ddy(p);
                float2 duv1 = ddx(uv), duv2 = ddy(uv);
                float3 dp2perp = cross(dp2, N);
                float3 dp1perp = cross(N, dp1);
                T = dp2perp * duv1.x + dp1perp * duv2.x;
                B = dp2perp * duv1.y + dp1perp * duv2.y;
                float invmax = rsqrt(max(max(dot(T, T), dot(B, B)), 1e-12));
                T *= invmax; B *= invmax;
            }

            half4 frag(Varyings i, FRONT_FACE_TYPE isFront : FRONT_FACE_SEMANTIC) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                half3 n = normalize(i.normalWS);
                n *= IS_FRONT_VFACE(isFront, 1.0, -1.0);
                float3 pw = i.positionWS;

                // ---- UV (metres) and tangent frame
                float2 um; float3 T, B;
            #if defined(_UV_MESH0)
                um = i.uv.xy;
                CotangentFrame(n, pw, um, T, B);
            #elif defined(_UV_MESH1)
                // (-1, 5) = primitive without TEXCOORD_1 (junction patches): world planar instead
                if (i.uv.z < -0.5) { um = pw.xz; T = normalize(float3(1, 0, 0) - n * n.x); B = normalize(float3(0, 0, 1) - n * n.z); }
                else { um = i.uv.zw; CotangentFrame(n, pw, um, T, B); }
            #else
                half3 a = abs(n);
                if (a.y >= 0.7) { um = pw.xz; T = float3(1, 0, 0); B = float3(0, 0, 1); }
                else if (a.x > a.z) { um = pw.zy; T = float3(0, 0, 1); B = float3(0, 1, 0); }
                else { um = pw.xy; T = float3(1, 0, 0); B = float3(0, 1, 0); }
                T = normalize(T - n * dot(T, n));
                B = normalize(B - n * dot(B, n));
            #endif
            #if defined(_DECAL_ALPHA) || defined(_DECAL_TYRE)
                // decals: radial / strip UV in TEXCOORD_0; the albedo set is sampled in world metres beneath
                float2 uvb = pw.xz / _Tile.xy;
            #else
                float2 uvb = um / _Tile.xy;
            #endif
                float footprint = max(length(fwidth(um)), 1e-5);      // metres per pixel

                half4 base = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uvb);
                half4 mask = SAMPLE_TEXTURE2D(_MaskMap, sampler_MaskMap, uvb);
                half3 tn = UnpackNormalScale(SAMPLE_TEXTURE2D(_NormalMap, sampler_NormalMap, uvb), _NormalStrength);
                half3 albedo = base.rgb * _Tint.rgb * _AlbedoScale;
                half smooth = mask.a * _SmoothnessScale;
                half ao = mask.g;
                half metal = mask.r * _MetallicScale;
                half alpha = 1.0;

                // ---- macro variation (64 m; second rotated octave on Medium+)
                half4 macro = SAMPLE_TEXTURE2D(_MacroMap, sampler_MacroMap, pw.xz / _MacroSize);
            #if defined(_KAMION_WORLD_DETAIL)
                const float2x2 rot = float2x2(0.7986, -0.6018, 0.6018, 0.7986);   // 37 deg
                half4 macro2 = SAMPLE_TEXTURE2D(_MacroMap, sampler_MacroMap, mul(rot, pw.xz) / (_MacroSize * 4.13) + 0.37);
                macro.rg = macro.rg * 0.6 + macro2.gr * 0.4;
                macro.b = macro.b * 0.7 + macro2.b * 0.3;
            #endif

                // ---- grass de-tiling (review r5 W-N3 "odra"): the 3 m grass tile repeats its bare-soil spots (Var.B) at one
                // scale and contrast. Medium+: a second sample rotated 30 deg and scaled 1.37x, blended by the 2-16 m and
                // 0.5-4 m macro channels, so the 3 m period never shows. All tiers: bare soil survives only inside a
                // world-space macro mask (8-64 m damp / worn hollows + 0.5-4 m mottling, ~35 % of the area) and along the
                // carriageway edge (terrain COLOR_0.r); elsewhere the soil texels are refilled with the calibrated grass
                // albedo at their own luminance. Low: +1 fetch (Var), Medium+: +3 fetches. ADR 0042.
            #if defined(_GRASS_DETILE)
                {
                    half soil = SAMPLE_TEXTURE2D(_VarMap, sampler_BaseMap, uvb).b;
                #if defined(_KAMION_WORLD_DETAIL)
                    const float2x2 rg = float2x2(0.8660, -0.5, 0.5, 0.8660);
                    float2 uv2 = mul(rg, um) / (_Tile.xy * 1.37) + float2(0.41, 0.73);
                    half3 b2 = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv2).rgb * _Tint.rgb * _AlbedoScale;
                    half s2 = SAMPLE_TEXTURE2D(_VarMap, sampler_BaseMap, uv2).b;
                    half3 tn2 = UnpackNormalScale(SAMPLE_TEXTURE2D(_NormalMap, sampler_NormalMap, uv2), _NormalStrength);
                    half wmix = smoothstep(0.35, 0.65, macro.g * 0.7 + macro.a * 0.3);
                    albedo = lerp(albedo, b2, wmix);
                    soil = lerp(soil, s2, wmix);
                    tn = normalize(lerp(tn, tn2, wmix));
                #endif
                    half keep = smoothstep(0.45, 0.65, macro.b * 0.6 + macro.r * 0.4 + (macro.a - 0.5) * 0.5);
                #if defined(_GROUNDMASKS)
                    keep = max(keep, (1.0 - smoothstep(0.02, 0.12, i.masks.r)) * 0.8);   // trampled edge, ~0.4-2.4 m
                #endif
                    half glum = dot(_GrassFill.rgb, half3(0.2126, 0.7152, 0.0722));
                    half lumA = dot(albedo, half3(0.2126, 0.7152, 0.0722));
                    half3 refill = _GrassFill.rgb * clamp(lumA / max(glum, 1e-3), 0.6, 1.4);
                    albedo = lerp(albedo, refill, saturate(soil * 1.6) * (1.0 - keep));
                }
            #endif
                half tone = (macro.r - 0.5) * 1.4 + (macro.g - 0.5) * 0.6 + (macro.a - 0.5) * 0.4;
                albedo *= 1.0 + _MacroStrength * tone;
                half wear = saturate((macro.b - 0.5) * 2.0);          // > 0: worn / soiled patches
                albedo *= 1.0 + _MacroWear * (macro.b - 0.5) * 0.8;
                smooth *= 1.0 - _MacroWear * wear * 0.5;

                // ---- per-element tone jitter (paving blocks, slabs): Var.G id + world tile index, faded when an
                // element is smaller than ~2 px (no sparkle far away)
            #if defined(_KAMION_WORLD_DETAIL) && !defined(_DECAL_ALPHA) && !defined(_DECAL_TYRE)
                if (_ElementJitter > 0.0)
                {
                    half4 var = SAMPLE_TEXTURE2D_LOD(_VarMap, sampler_point_repeat, uvb, 0);
                    float id = var.g + Hash12(floor(uvb) + 17.0);
                    half j = (Hash12(float2(id * 97.0, 3.1)) - 0.5) * 2.0;
                    half fade = saturate(_ElementSize / (footprint * 2.5) - 0.5);
                    albedo *= 1.0 + _ElementJitter * j * fade;
                    // joints collect dirt / moss (Var.B)
                    albedo = lerp(albedo, albedo * half3(0.78, 0.8, 0.72), var.b * 0.5 * fade);
                }
            #endif

                // ---- crack layer (asphalt): open cracks darken, sealant bands glossy black; faded by macro wear so
                // whole stretches can be sound
            #if defined(_CRACKS) && defined(_KAMION_WORLD_DETAIL)
                {
                    float2 uc = pw.xz / _Tile.z;
                    half4 cm = SAMPLE_TEXTURE2D(_CrackMap, sampler_CrackMap, uc);
                    half amount = _CrackStrength * saturate(0.25 + (macro.b - 0.35) * 2.2);
                    albedo *= lerp(1.0, 0.35, cm.r * amount);
                    albedo = lerp(albedo, half3(0.03, 0.03, 0.03), cm.g * amount);
                    albedo *= 1.0 - cm.a * amount * 0.12;
                    smooth = lerp(smooth, 0.55, cm.g * amount);
                    half3 cn = UnpackNormalScale(SAMPLE_TEXTURE2D(_CrackNormal, sampler_CrackMap, uc), amount);
                    tn = normalize(half3(tn.xy + cn.xy, tn.z * cn.z));
                }
            #endif

                // ---- close-range photo detail (asphalt), fades out by _DetailFade
            #if defined(_PHOTO_DETAIL) && defined(_KAMION_WORLD_DETAIL)
                {
                    float dist = length(GetCameraPositionWS() - pw);
                    half f = saturate(1.0 - dist / _DetailFade) * mask.b;
                    if (f > 0.001)
                    {
                        float2 ud = pw.xz / _Tile.w;
                        half d = SAMPLE_TEXTURE2D(_DetailAlbedo, sampler_DetailAlbedo, ud).r;
                        albedo *= lerp(1.0, d * 4.594794, f);          // unity_ColorSpaceDouble (linear)
                        half3 dn = UnpackNormalScale(SAMPLE_TEXTURE2D(_DetailNormal, sampler_DetailAlbedo, ud), f);
                        tn = normalize(half3(tn.xy + dn.xy, tn.z * dn.z));
                    }
                }
            #endif

                // ---- road wear from TEXCOORD_1 = (lane coordinate, distance to carriageway edge); (-1, 5) = no data
            #if defined(_ROADWEAR)
                {
                    float2 w = i.uv.zw;
                    if (w.x > -0.5)        // (-1, 5) = no road data (junction patches, kerbs)
                    {
                        // wheel paths at ~0.25 / 0.75 of a lane: darker binder-rich, smoother
                        float lc = frac(w.x);
                        half wp = saturate(1.0 - abs(abs(lc - 0.5) - 0.24) / 0.11);
                        albedo *= 1.0 - 0.10 * wp * _WheelPolish;
                        smooth = lerp(smooth, smooth + 0.12, wp * _WheelPolish);
                        // gutter: grit, leaves and soot within ~0.6 m of the kerb
                        half g = (1.0 - smoothstep(0.05, 0.65, w.y)) * _GutterDirt;
                        albedo = lerp(albedo, albedo * half3(1.12, 1.06, 0.92) + half3(0.012, 0.010, 0.006), g);
                        smooth *= 1.0 - 0.4 * g;
                        // ADR 0060 (review r7 N-2): the gutter's lowest ~0.25 m stays damp (water runs along the kerb to the
                        // gullies), broken where the macro mottling says the grit is dry
                        half damp = (1.0 - smoothstep(0.08, 0.3, w.y)) * saturate(0.35 + (macro.a - 0.5) * 2.0 + (macro.b - 0.5)) * _GutterDirt;
                        albedo *= 1.0 - 0.5 * damp;
                        smooth = lerp(smooth, 0.55, damp);
                        // oil / soot drip band between the wheel paths (lane centre 0.5 +- ~0.12), mottled, strongest where
                        // traffic queues; WORKING_VALUE darkening, the band is ~0.8 m of a 3.5 m lane
                        half drip = saturate(1.0 - abs(lc - 0.5) / 0.13) * saturate(0.45 + (macro.a - 0.5) * 2.2 + (macro.g - 0.5) * 0.8);
                        albedo *= 1.0 - _DripBand * drip;
                    }
                }
            #endif

                // ---- ground grime (ADR 0060, review r7 N-2): dirty joints on every tier (Var.B, the Medium+ element jitter
                // only adds tone) and damp / oily hollows: water and fines stay in the low points (Var.R height) of the
                // 1.5-24 m wear patches (macro B) broken by the 0.5-4 m mottling (macro A). Paving, yard concrete, yard and
                // path asphalt. Low: +1 fetch (Var, bilinear).
            #if defined(_GRIME)
                {
                    half4 gv = SAMPLE_TEXTURE2D(_VarMap, sampler_BaseMap, uvb);
                    half jfade = saturate(0.012 / max(footprint, 1e-4));             // joints resolved: full dirt
                    albedo *= 1.0 - _Grime.z * gv.b * lerp(0.5, 1.0, jfade);
                    half pool = macro.b * 0.65 + macro.a * 0.35 - (gv.r - 0.7) * 0.06;
                    half wet = smoothstep(_Grime.y, _Grime.y + 0.025, pool);
                    albedo *= 1.0 - _Grime.x * wet;
                    smooth = lerp(smooth, max(smooth, 0.62), wet * _Grime.w);
                }
            #endif

                // ---- decals
            #if defined(_DECAL_PATCH)
                {
                    half age = saturate(i.uv.z);
                    albedo = lerp(albedo, albedo * _AgeTint, age * 0.85);
                    smooth *= 1.0 - 0.45 * age;
                }
            #endif
            #if defined(_DECAL_ALPHA)
                {
                    // 2x2 atlas, one stain per cell, centre 0.5/0.5 of the radial UV; cell from TEXCOORD_1.y
                    float cell = floor(saturate(i.uv.w) * 3.999);
                    float2 cxy = float2(fmod(cell, 2.0), floor(cell * 0.5));
                    float2 ua = (saturate(i.uv.xy) + cxy) * 0.5;
                    half4 st = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, ua);
                    half4 sm = SAMPLE_TEXTURE2D(_MaskMap, sampler_MaskMap, ua);
                    albedo = st.rgb * _Tint.rgb * _AlbedoScale;
                    smooth = sm.a * _SmoothnessScale;
                    ao = 1.0;
                    tn = half3(0, 0, 1);
                    alpha = st.a * _DecalAlpha;
                }
            #endif
            #if defined(_DECAL_TYRE)
                {
                    // rubber scrub along a wheel track: soft across the strip (TEXCOORD_0.y 0..1), faded at both ends
                    // (TEXCOORD_0.x metres, TEXCOORD_1.x length), broken up by the macro mottling
                    half across = 1.0 - abs(i.uv.y * 2.0 - 1.0);
                    half prof = smoothstep(0.0, 0.55, across);
                    half ends = saturate(i.uv.x / 2.5) * saturate((i.uv.z - i.uv.x) / 4.0);
                    half brk = saturate(0.55 + (macro.a - 0.5) * 2.5 + (macro.g - 0.5));
                    albedo = _Tint.rgb;
                    smooth = 0.42 * _SmoothnessScale;
                    ao = 1.0;
                    tn = half3(0, 0, 1);
                    // TEXCOORD_1.y = per-pass strength 0.6..1.4 (review r6 W-N11; older data without it: seed 0..1)
                    alpha = saturate(prof * ends * brk * _DecalAlpha * clamp(i.uv.w, 0.3, 1.5));
                }
            #endif

            #if defined(_DECAL_PAINT)
                {
                    // road paint over the asphalt beneath (albedo / smooth / tn hold that asphalt here)
                    float ex = i.uv.w;                                   // [0,1) longitudinal, [2,3) transverse; frac = age
                    half transverse = step(1.5, ex);
                    half age = (half)frac(ex);
                    half known = step(-0.5, i.uv.z);                     // (-1, 5) = no wear data
                    float lc = frac(i.uv.z);
                    half wp = saturate(1.0 - abs(abs(lc - 0.5) - 0.24) / 0.13) * known;
                    half peaks = SAMPLE_TEXTURE2D(_VarMap, sampler_BaseMap, uvb).r;     // aggregate tops wear first
                    half mott = (macro.a - 0.5) * 2.0;
                    half worn = _PaintWear.x * wp * transverse * (0.55 + 0.9 * age)     // tyres scrub the crossed marks
                              + _PaintWear.y * (0.35 + age) * (0.6 + 0.4 * wp)          // weathering everywhere
                              + 0.10 * mott;
                    // chipped, not faded: a narrow threshold on the peak-weighted wear gives sharp-edged bare spots
                    half cover = 1.0 - smoothstep(0.42, 0.58, saturate(worn) * (0.35 + 1.3 * peaks));
                    // traffic film: tyre soot and road dust, grey-brown, heavier on old marks and soiled patches
                    half dirt = saturate(_PaintWear.z * (0.75 + 0.5 * age) * (0.85 + 0.3 * macro.b) * (1.0 + 0.4 * wp * transverse));
                    half3 film = _PaintColor.rgb * (1.0 - dirt * half3(1.0, 1.0, 1.03));   // neutral grey film (r6 critic: beige read as concrete)
                    half3 asph = albedo;
                    albedo = lerp(asph, film, cover);
                    // pre-filter: a 0.12 m line (0.4 m for transverse marks) under a pixel blends to the asphalt beneath
                    float fp = max(length(fwidth(pw.xz)), 1e-4);
                    half lw = lerp(_PaintWear.w, 0.4, transverse);
                    albedo = lerp(asph, albedo, saturate(lw * 1.5 / fp));
                    smooth = lerp(smooth, _PaintColor.a * (1.0 - 0.3 * dirt), cover);
                    tn = normalize(lerp(tn, half3(0, 0, 1), cover * 0.75));   // the film fills the fine texture
                }
            #endif

            #if defined(_DECAL_GRATE)
                {
                    // cast-iron gully grate over TEXCOORD_0 0..1 (0.5 x 0.6 m): frame, slots along v, tyre-polished bar
                    // tops, black water below; edges box-filtered by the pixel footprint (no shimmer)
                    float2 g = i.uv.xy;
                    float2 fw = max(fwidth(g), 1e-4);
                    float2 e = min(g, 1.0 - g);
                    float em = min(e.x, e.y);
                    float fm = max(fw.x, fw.y);
                    half inner = saturate((em - 0.1) / fm + 0.5);               // 10 % frame all round
                    half frame = 1.0 - inner;
                    float sx = frac(g.x * 9.0);                                 // 9 slots across
                    half slot = saturate((0.30 - abs(sx - 0.5)) / (fw.x * 9.0) + 0.5);
                    float sy = abs(frac(g.y * 3.0) - 0.5);                      // 2 cross ribs along the slots
                    half rib = saturate((sy - 0.44) / (fw.y * 3.0) + 0.5);
                    half hole = slot * inner * (1.0 - rib);
                    half rust = saturate((macro.a - 0.45) * 3.0);
                    half3 iron = lerp(half3(0.035, 0.033, 0.03), half3(0.07, 0.045, 0.03), rust * 0.6);
                    albedo = lerp(iron * (1.0 + 0.25 * frame), half3(0.006, 0.006, 0.006), hole);
                    smooth = lerp(0.42 - 0.2 * rust, 0.7, hole);
                    ao = lerp(1.0, 0.3, hole);
                    tn = half3(0, 0, 1);
                }
            #endif

            #if defined(_STRIPES)
                {
                    // painted bands (boom arm red/white 0.5 m, hazard stripes 45 deg) in TEXCOORD_0 metres, box-filtered
                    float t = dot(i.uv.xy, _Stripe.xy) / max(_Stripe.z, 1e-3);
                    float ft = max(fwidth(t), 1e-4);
                    half k = saturate((abs(frac(t) - 0.5) - 0.25) / ft + 0.5);
                    albedo = lerp(_StripeA.rgb, _StripeB.rgb, k) * (0.9 + 0.2 * macro.a);
                    smooth = 0.45;
                }
            #endif

                // ---- terrain ground masks (COLOR_0)
            #if defined(_GROUNDMASKS)
                {
                    half4 k = i.masks;
                    half lum = dot(base.rgb, half3(0.2126, 0.7152, 0.0722));
                    half detl = saturate(lum / 0.095);
                    albedo = lerp(albedo, albedo * half3(1.22, 1.10, 0.92), k.b * 0.8 * _GroundTint);
                    // Pine-forest floor (bór sosnowy): needle litter in patches with feather moss and bilberry, not a
                    // uniform beige (review r3 W2 / r4 W-H8). Linear albedo: litter 0.045/0.035/0.021, moss + bilberry
                    // 0.034/0.049/0.019 (WORKING_VALUE, judged against the CC0 Tysiąclecia photos); patches from the
                    // 64 m macro map.
                    half mossy = saturate((macro.a - 0.30) * 3.0 + (macro.r - 0.5) + (detl - 0.5) * 0.6);
                    half3 floorAlb = lerp(half3(0.045, 0.035, 0.021), half3(0.034, 0.049, 0.019), mossy);
                    albedo = lerp(albedo, floorAlb * (0.6 + 0.8 * detl), k.g * _GroundTint);
                    albedo = lerp(albedo, half3(0.13, 0.11, 0.085) * (0.6 + 0.8 * detl), k.a * _GroundTint);
                    half grit = (1.0 - smoothstep(0.03, 0.07, k.r)) * 0.6 * _GroundTint;
                    albedo = lerp(albedo, half3(0.19, 0.17, 0.14) * (0.7 + 0.6 * detl), grit);
                }
            #endif

                // ---- walls: splash / soil zone above the ground (TEXCOORD_0.y = metres above ground)
            #if defined(_SPLASH)
                {
                    half s = 1.0 - smoothstep(0.0, _SplashHeight, i.uv.y);
                    s *= 0.6 + 0.4 * macro.a;
                    albedo = lerp(albedo, albedo * half3(0.72, 0.70, 0.64), s);
                    smooth *= 1.0 - 0.5 * s;
                }
            #endif

                // ---- halls: run-off streaks under the parapet coping (TEXCOORD_1 = u m, 1 + depth below the fascia /
                // per-building length scale; < 0.5 = no wall-top data). 24 x 4 m layer, faded to 0 in its last 0.4 m.
                // Strength varies along the wall and between halls with the macro map (no two halls alike).
            #if defined(_RUNOFF)
                if (i.uv.w > 0.5)
                {
                    // PNG row 0 (right under the coping) is texture v = 1 in Unity: v = 1 - depth / 4 m. Before
                    // (G3 wires-streaks-v2) v = depth / 4 sampled the faded last rows at the top and drew the streaks
                    // upside down 3-4 m lower. LOD1 walls start 0.25 m above their coping (depth < 0): clamped.
                    float2 ur = float2(i.uv.z / 24.0, 1.0 - clamp((i.uv.w - 1.0) * 0.25, 0.0, 0.985));
                    half3 ro = SAMPLE_TEXTURE2D(_RunoffMap, sampler_MacroMap, ur).rgb;
                    half k = _RunoffStrength * saturate(0.8 + (macro.r - 0.5) * 1.4 + (macro.g - 0.5) * 1.0);
                    albedo = lerp(albedo, albedo * half3(0.22, 0.21, 0.2), ro.r * k);
                    albedo = lerp(albedo, half3(0.075, 0.042, 0.022), ro.g * k * 0.8);
                    smooth *= 1.0 - 0.35 * ro.r * k;
                }
            #endif

                albedo = saturate(albedo);
                smooth = saturate(smooth);
                half3 nw = normalize(tn.x * T + tn.y * B + tn.z * n);

                // ---- lighting (same model as Kamion/World Surface: Lambert + GGX sun, SH ambient, env reflection)
                float3 V = GetWorldSpaceNormalizeViewDir(pw);
                half NoV = saturate(dot(nw, V));
                half perceptualRoughness = 1.0 - smooth;
                half r = max(perceptualRoughness * perceptualRoughness, 0.002);
                half r2 = r * r;
            #if defined(_CARPAINT)
                // clean = how much clear coat shows through the road film (the set's smoothness, 0.68 on clean paint)
                half clean = saturate((mask.a - 0.25) / 0.40);
                metal = _CarPaint.x * clean;
            #endif
                half3 specColor = lerp(half3(0.04, 0.04, 0.04), albedo, metal);
                half3 diffColor = albedo * (1.0 - metal) * (1.0 - 0.04);

                float4 shadowCoord = TransformWorldToShadowCoord(pw);
                Light L = GetMainLight(shadowCoord, pw, half4(1, 1, 1, 1));
                half giK, giSun;
                KamionWorldGI(pw, n, giK, giSun);
                half atten = L.distanceAttenuation * lerp(1.0, KamionFarShadow(L.shadowAttenuation, giSun, pw), _ReceiveShadows);
                half NoL = saturate(dot(nw, L.direction));
                // geometric normal terminator: no light through the back of a bumpy surface
                NoL *= saturate(dot(n, L.direction) * 8.0 + 0.5);
                float3 H = SafeNormalize(float3(L.direction) + V);
                half NoH = saturate(dot(nw, H));
                half LoH = saturate(dot(L.direction, H));
                float d = NoH * NoH * (r2 - 1.0) + 1.00001;
                half spec = r2 / ((d * d) * max(0.1, LoH * LoH) * (r * 4.0 + 2.0));
            #if defined(_CARPAINT)
                // base coat (flake layer): its own roughness, normal tilted per flake cell on Medium+
                half3 nb = nw;
                half rb = max(_CarPaint.w * _CarPaint.w, 0.02);
              #if defined(_KAMION_WORLD_DETAIL)
                {
                    float3 po = TransformWorldToObject(pw) * _CarFlake.x;
                    float3 cell = floor(po);
                    // sin-free hash (the sin hash of cell indices in the thousands banded into a visible weave)
                    float3 p3 = frac(cell * float3(0.1031, 0.1030, 0.0973));
                    p3 += dot(p3, p3.yxz + 33.33);
                    float3 hsh = frac((p3.xxy + p3.yxx) * p3.zyx);
                    // a flake cell must cover more than a pixel: full at footprint <= cell / 2, none at >= cell
                    half ffade = saturate(_CarFlake.y / (_CarFlake.x * max(length(fwidth(pw)), 1e-5)) - 1.0);
                    nb = normalize(nw + (half3)(hsh * 2.0 - 1.0) * (_CarPaint.y * ffade * clean));
                }
              #endif
                half NoHb = saturate(dot(nb, H));
                half rb2 = rb * rb;
                float db = NoHb * NoHb * (rb2 - 1.0) + 1.00001;
                half specB = rb2 / ((db * db) * max(0.1, LoH * LoH) * (rb * 4.0 + 2.0));
                half3 baseSpecCol = lerp(specColor, specColor * _PearlTint.rgb, _CarPaint.z * Pow4(1.0 - NoV));
                half coatF = 0.04 + 0.96 * Pow4(1.0 - LoH) * (1.0 - LoH);
                half3 color = (diffColor + baseSpecCol * (specB * metal) + (spec * coatF * clean).xxx) * L.color * (atten * NoL);
            #else
                half3 color = (diffColor + specColor * spec) * L.color * (atten * NoL);
            #endif

                // sky occlusion (ADR 0060) on top of baked sky visibility giK (ADR 0064)
                half3 ambient = SampleSH(nw) * diffColor * (ao * giK) * (1.0 - _SkyOcc.x * saturate(-nw.y));
                half3 R = reflect(-V, nw);
                half fresnel = Pow4(1.0 - NoV);
                half grazing = saturate(smooth + max(metal, 0.04));
                half3 env = GlossyEnvironmentReflection(R, perceptualRoughness, ao * giK) * lerp(specColor, grazing.xxx, fresnel) / (r2 + 1.0);
            #if defined(_CARPAINT)
                {
                    // clear coat: mirror of the sky / street at the coat's roughness, Schlick F0 0.04; under it the base
                    // coat reflects a blurred environment in its own (flake) colour
                    half coat = (0.04 + 0.96 * fresnel * (1.0 - NoV)) * clean;
                    half3 envCoat = GlossyEnvironmentReflection(R, perceptualRoughness, ao * giK) * coat;
                    half3 Rb = reflect(-V, nb);
                    half3 envBase = GlossyEnvironmentReflection(Rb, _CarPaint.w, ao * giK) * baseSpecCol * (metal * (1.0 - coat));
                    half3 envDull = GlossyEnvironmentReflection(R, perceptualRoughness, ao * giK) * (0.04 * (1.0 - clean)) / (r2 + 1.0);
                    env = envCoat + envBase + envDull;
                }
            #endif
                env *= 1.0 - _SkyOcc.y * (1.0 - smoothstep(0.05, 0.45, R.y));
                color += ambient + env;
                color += diffColor * KamionLampPools(pw, nw);   // dusk street-lamp pools (ADR 0062)

                color = MixFog(color, i.fogFactor);
                return half4(color, alpha);
            }
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode" = "ShadowCaster" }
            ZWrite On ZTest LEqual ColorMask 0 Cull [_Cull]

            HLSLPROGRAM
            #pragma target 3.5
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
            ZWrite [_ZWrite] ColorMask R Cull [_Cull]
            Offset [_OffsetFactor], [_OffsetUnits]

            HLSLPROGRAM
            #pragma target 3.5
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
