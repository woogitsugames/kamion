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
// _DECAL_PATCH (TEXCOORD_1.x = age; TEXCOORD_1.y = kind + seed), _DECAL_ALPHA (alpha-blended decals:
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
        _AsphaltWear ("Asphalt: tone, wheel darkening, Low cracks, Low photo detail (ADR0118)", Vector) = (1, 0, 0, 0)
        _WheelPolish ("Wheel-path polish (_ROADWEAR)", Range(0, 1)) = 0.5
        _GutterDirt ("Gutter grime (_ROADWEAR)", Range(0, 1)) = 0.5
        _DripBand ("Lane-centre oil / soot drip band between the wheel paths (_ROADWEAR)", Range(0, 1)) = 0
        _Grime ("Ground grime (_GRIME): x damp darkening, y damp threshold (macro pool), z joint dirt, w damp gloss", Vector) = (0.45, 0.62, 0.3, 0.5)
        _PavingVar ("Sidewalk paving variation (ADR 0349): x batch, y stains, z joint boost, w repair patches", Vector) = (0, 0, 0, 0)
        _PavingWeed ("Sidewalk edge weeds (ADR 0349): x weed strength, y kerb band m, z block jitter, w enabled", Vector) = (0, 0, 0, 0)
        _Tactile ("Tactile warning slabs (ADR 0349): x tile m, y dome pitch m, z dome radius m, w relief", Vector) = (0, 0, 0, 0)
        _KerbWear ("Kerb wear: joint dirt, mineral film, film threshold, enabled (ADR0118)", Vector) = (0, 0, 0.55, 0)
        [HideInInspector] _SidewalkTiles ("Sidewalk slab/asphalt tile sizes (m)", Vector) = (0, 0, 0, 0)
        [HideInInspector] _WalkSlabBaseMap ("Sidewalk slab albedo", 2D) = "grey" {}
        [HideInInspector] _WalkSlabNormalMap ("Sidewalk slab normal", 2D) = "bump" {}
        [HideInInspector] _WalkSlabMaskMap ("Sidewalk slab mask", 2D) = "white" {}
        [HideInInspector] _WalkSlabVarMap ("Sidewalk slab joints", 2D) = "black" {}
        [HideInInspector] _WalkAsphaltBaseMap ("Footway asphalt albedo", 2D) = "grey" {}
        [HideInInspector] _WalkAsphaltNormalMap ("Footway asphalt normal", 2D) = "bump" {}
        [HideInInspector] _WalkAsphaltMaskMap ("Footway asphalt mask", 2D) = "white" {}
        [HideInInspector] _TownKerb ("Town kerb wear", Float) = 0
        _GroundWearExclude ("Ground wear exclusion: object-local E/N bounds, min/max (ADR0118)", Vector) = (0, 0, 0, 0)
        _GroundGrimeBase ("Ground grime inside exclusion: original coefficients (ADR0118)", Vector) = (0.45, 0.62, 0.3, 0.5)
        _SkyOcc ("Sky occlusion: x down-facing ambient, y horizon reflection (0 = off; ADR 0060)", Vector) = (0, 0, 0, 0)
        _LowNoShadow ("No shadow casting below the world-detail tier (Low; ADR 0123)", Float) = 0
        _VertexGrime ("Vertex grime (_VERTEX_GRIME, COLOR_0.r): rgb grime albedo (linear), w roughness gain (ADR 0123)", Vector) = (0.1, 0.1, 0.09, 0.3)
        _VertexWeed ("Vertex weeds (_VERTEX_GRIME, COLOR_0.g): rgb weed albedo (linear), w = 1 on (ADR 0144)", Vector) = (0.07, 0.09, 0.035, 0)
        _BronzePatina ("Bronze patina (_BRONZE_PATINA, COLOR_0.r): rgb linear patina albedo, w strength (ADR 0331)", Vector) = (0.065, 0.130, 0.088, 0)
        _BronzeRubbed ("Bronze rubbed (_BRONZE_PATINA, COLOR_0.g): rgb linear rubbed albedo, w strength (ADR 0331)", Vector) = (0.66, 0.46, 0.20, 0)
        _BronzeParams ("Bronze params (_BRONZE_PATINA): x patina smooth, y rubbed smooth, z rubbed metal, w vertex AO strength", Vector) = (0.18, 0.62, 0.88, 0.65)
        _GroundBounce ("Ground bounce on down-facing normals: rgb = ground albedo x form factor (linear), w = 1 on (ADR 0144)", Vector) = (0, 0, 0, 0)
        _AgeTint ("Patch age target / base albedo ratio", Float) = 2.0
        _PatchSeam ("Repair: seam width m, darkening, fresh tone, aged tone (ADR0118)", Vector) = (0, 0, 1, 1)
        _DecalAlpha ("Decal opacity", Range(0, 1)) = 1
        _DecalCells ("Decal atlas cells per side (_DECAL_ALPHA): 2 oil atlas, 1 whole UV", Float) = 2
        _GrimeTraffic ("Yard grime by traffic (ADR 0194): x open raise, y busy drop, z wall zone m, w 1 = on", Vector) = (0, 0, 15, 0)
        _OilLook ("Oil stain (ADR 0194): x aged smoothness, y fresh smoothness, z coverage gamma, w 1 = on", Vector) = (0, 0, 1, 0)
        _SplashHeight ("Splash zone height (m)", Float) = 0.6
        _SplashBand ("Ground-contact band (_SPLASH, weathering-s24): x height m, y strength, z spatter, w 1 = on", Vector) = (0.3, 0, 0, 0)
        _RoofTile ("Roof tile grid (_ROOF_WEATHER): x tile width m, y course m, z half-offset courses 0/1, w odd-tile strength", Vector) = (0.2, 0.35, 0, 0)
        _RoofWeather ("Roof weathering (_ROOF_WEATHER): x moss, y dirt runs, z lichen, w sheet ribs 0/1", Vector) = (1, 1, 1, 0)
        _RunoffMap ("Parapet run-off (R soot, G rust; _RUNOFF)", 2D) = "black" {}
        _RunoffStrength ("Parapet run-off strength", Range(0, 1)) = 0.5
        _GroundTint ("Terrain grass ground-mask strength", Range(0, 1)) = 1
        _RegionOriginEN ("Field mosaic (ADR 0298): xy EPSG:2180 of the region origin, z 1 = on", Vector) = (0, 0, 0, 0)
        _GrassFill ("Grass refill albedo (_GRASS_DETILE, linear; Vector: no sRGB conversion)", Vector) = (0.079, 0.109, 0.037, 1)
        _Stripe ("Stripes (_STRIPES): xy direction in UV0 metres, z period m", Vector) = (1, 0, 1, 0)
        _StripeA ("Stripe colour A (linear)", Color) = (0.55, 0.03, 0.02, 1)
        _StripeB ("Stripe colour B (linear)", Color) = (0.7, 0.7, 0.68, 1)
        _PaintColor ("Paint film albedo (linear, _DECAL_PAINT), a = smoothness", Vector) = (0.6, 0.6, 0.57, 0.35)
        _PaintWear ("Paint wear: x wheel-path, y age, z dirt film, w line width m", Vector) = (0.85, 0.25, 0.3, 0.12)
        _PaintFreshWear ("Fresh road paint: wheel, weather, dirt, substrate multipliers (ADR0118)", Vector) = (1, 1, 1, 1)
        _CarPaint ("Car paint (_CARPAINT): x base metal, y flake tilt, z pearl, w base-coat roughness", Vector) = (0, 0, 0, 0.5)
        _CarFlake ("Car flake: x cells/m, y fade, w film mode (0 off, 1 car, 2 yard)", Vector) = (400, 1, 0, 0)
        _PearlTint ("Pearl grazing tint (linear)", Color) = (1, 1, 1, 1)
        _PanelTone ("Panel tone (_PANELTONE): xy cladding module in UV0 m (length, course), z per-panel hash share, w butt-joint line", Vector) = (6, 1, 0.35, 0.3)
        _OffsetFactor ("Depth offset factor", Float) = 0
        _OffsetUnits ("Depth offset units", Float) = 0
        [Enum(UnityEngine.Rendering.BlendMode)] _SrcBlend ("Src blend", Float) = 1
        [Enum(UnityEngine.Rendering.BlendMode)] _DstBlend ("Dst blend", Float) = 0
        [Toggle] _ZWrite ("ZWrite", Float) = 1
        [Enum(UnityEngine.Rendering.CullMode)] _Cull ("Cull", Float) = 2
        [Toggle] _ReceiveShadows ("Receive shadows", Float) = 1
        _ShadowNormalBiasScale ("Opt-in caster normal-bias scale (ADR0155)", Range(0, 1)) = 1
        _NightWindows ("Night windows (_NIGHTWIN, ADR 0192): 1 facade_atlas, 2 facade_far rows", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" "UniversalMaterialType" = "Lit" }

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        #include "../../Rendering/Shaders/KamionLampPools.hlsl"
        #include "../../Rendering/Shaders/VegetationGround.hlsl"
        #include "../../Rendering/Shaders/KamionRoadStains.hlsl"   // ADR 0194
        CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_ST;
            float4 _Tint;
            float4 _Tile;
            float _AlbedoScale, _NormalStrength, _SmoothnessScale, _MetallicScale;
            float _ElementJitter, _ElementSize, _MacroSize, _MacroStrength, _MacroWear, _CrackStrength, _DetailFade;
            float _WheelPolish, _GutterDirt, _AgeTint, _DecalAlpha, _DecalCells, _SplashHeight, _GroundTint, _RunoffStrength;
            float4 _PanelTone;
            float4 _Stripe, _StripeA, _StripeB;
            float4 _GrassFill;
            float4 _PaintColor, _PaintWear;
            float4 _PaintFreshWear;
            float4 _AsphaltWear;
            float4 _PatchSeam;
            float4 _Grime, _SkyOcc, _VertexWeed, _GroundBounce;
            float4 _PavingVar, _PavingWeed, _Tactile;   // ADR 0349 sidewalk paving variation + tactile warning domes
            float4 _VertexGrime;
            float4 _BronzePatina, _BronzeRubbed, _BronzeParams;   // ADR 0331 weathered cast bronze + patina
            float _LowNoShadow;
            float4 _KerbWear;
            float4 _SidewalkTiles;
            float _TownKerb;
            float4 _GroundWearExclude, _GroundGrimeBase;
            float _DripBand;
            float4 _OilLook, _GrimeTraffic;   // ADR 0194 (KamionRoadStains.hlsl)
            float4 _CarPaint, _CarFlake, _PearlTint;
            float _OffsetFactor, _OffsetUnits, _SrcBlend, _DstBlend, _ZWrite, _Cull, _ReceiveShadows;
            float _ShadowNormalBiasScale;
            float _NightWindows;
            float4 _RegionOriginEN;   // ADR 0298 field mosaic
            float4 _SplashBand, _RoofTile, _RoofWeather;   // weathering-s24
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
            #pragma shader_feature_local _VERTEX_GRIME
            #pragma shader_feature_local _BRONZE_PATINA
            #pragma shader_feature_local _CARPAINT
            #pragma shader_feature_local _PANELTONE
            #pragma shader_feature_local _NIGHTWIN
            #pragma shader_feature_local _FACADE_TINT
            #pragma shader_feature_local _ROOF_WEATHER
            #pragma shader_feature_local _TOWN_PAVEMENT

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Assets/_Project/Rendering/Shaders/KamionAtmosphere.hlsl"   // ADR 0080 height haze, Low tone toe, wetness
            #include "Assets/_Project/Rendering/Shaders/KamionWorldGI.hlsl"   // ADR 0064 baked sky visibility + far ground shadows
            #include "Assets/_Project/Environment/Shaders/KamionFieldMosaic.hlsl"   // ADR 0298 farmland mosaic per pixel

            TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
            TEXTURE2D(_NormalMap); SAMPLER(sampler_NormalMap);
            TEXTURE2D(_MaskMap); SAMPLER(sampler_MaskMap);
            TEXTURE2D(_VarMap); SAMPLER(sampler_point_repeat);
            TEXTURE2D(_WalkSlabBaseMap);
            TEXTURE2D(_WalkSlabNormalMap);
            TEXTURE2D(_WalkSlabMaskMap);
            TEXTURE2D(_WalkSlabVarMap);
            TEXTURE2D(_WalkAsphaltBaseMap);
            TEXTURE2D(_WalkAsphaltNormalMap);
            TEXTURE2D(_WalkAsphaltMaskMap);
            TEXTURE2D(_MacroMap); SAMPLER(sampler_MacroMap);
            TEXTURE2D(_CrackMap); SAMPLER(sampler_CrackMap);
            TEXTURE2D(_CrackNormal);
            TEXTURE2D(_DetailAlbedo); SAMPLER(sampler_DetailAlbedo);
            TEXTURE2D(_DetailNormal);
            TEXTURE2D(_RunoffMap);
            #if defined(_NIGHTWIN)
            #include "Assets/_Project/Rendering/Shaders/KamionNightWindows.hlsl"   // ADR 0192 lit windows
            TEXTURE2D(_KamionNightAtlasId); TEXTURE2D(_KamionNightAtlasT); SAMPLER(sampler_KamionNightAtlasT);
            TEXTURE2D(_KamionNightFarId); TEXTURE2D(_KamionNightFarT);
            float4 _KamionNightAtlasId_TexelSize, _KamionNightFarId_TexelSize;
            #endif

            #if defined(_CARPAINT)
            // ADR0089: four painted-shell film levels, including clean. Region-relative origin remains stable
            // when WorldInstances and the existing GI rectangle move together during a floating-origin shift.
            // Computed per vertex and carried flat: no per-fragment hash or additional texture sample.
            float2 CarInstanceFilm(float2 originXZ)
            {
                uint2 cell = (uint2)(int2)floor((originXZ - _KamionGIRect.xy) * 4.0 + 0.37);
                uint h = cell.x * 1664525u + cell.y * 1013904223u;
                h ^= h >> 16; h *= 2246822519u; h ^= h >> 13;
                uint level = h < 429496730u ? 0u : (h < 1932735283u ? 1u : (h < 3435973837u ? 2u : 3u));
                return float2(level * (1.0 / 3.0), (h & 1023u) * (1.0 / 1024.0));
            }
            #endif

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
                #if defined(_CARPAINT)
                nointerpolation float2 carFilm : TEXCOORD5;
                #endif
                #if defined(_NIGHTWIN)
                float3 posOS : TEXCOORD6;       // ADR 0192: window anchor (object space, camera independent)
                float3 posRel : TEXCOORD7;      // camera-relative position: precise screen derivatives
                #endif
                #if defined(_GROUNDMASKS)
                float2 posEN : TEXCOORD8;       // ADR 0298: object space = region-local E/N (field mosaic)
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
                o.uv = float4(v.uv0, v.uv1);
                #if defined(_GROUNDMASKS)
                o.posEN = v.positionOS.xz;
                #endif
                #if defined(_CARPAINT)
                o.carFilm = CarInstanceFilm(float2(GetObjectToWorldMatrix()._m03, GetObjectToWorldMatrix()._m23));
                #endif
                #if defined(_NIGHTWIN)
                o.posOS = v.positionOS.xyz;
                o.posRel = p.positionWS - _WorldSpaceCameraPos;
                #endif
                return o;
            }

            float Hash12(float2 p)
            {
                float3 p3 = frac(float3(p.xyx) * 0.1031);
                p3 += dot(p3, p3.yzx + 33.33);
                return frac((p3.x + p3.y) * p3.z);
            }

            // Value noise 0..1 (ALU only, no texture fetch): broken outline of hand-laid asphalt repairs (build #3 P2).
            float ValueNoise12(float2 p)
            {
                float2 i = floor(p), f = frac(p);
                float2 u = f * f * (3.0 - 2.0 * f);
                return lerp(lerp(Hash12(i), Hash12(i + float2(1, 0)), u.x),
                            lerp(Hash12(i + float2(0, 1)), Hash12(i + float2(1, 1)), u.x), u.y);
            }

            // ADR 0335: tone of the worn pavement over kilometres (90 m resurfaced / sun-bleached stretches, 23 m patched
            // binder, 7 m re-surfaced bits, +-2.5 % warm / cool). Object space (stable across origin rebases). Shared by the
            // road ribbons / plates (_ROADWEAR) and the repair patches (_DECAL_PATCH, road-patches-s24): a patch is shaded
            // RELATIVE to the stretch it sits on - before, an old repair on a dark (x0.5) stretch read as a pale plate and a
            // fresh one on a bleached stretch as a black hole (critic wave 11 pkt 2, dw671 cab-view-b).
            half3 KamionRoadTone(float2 pt)
            {
                half tv = (half)(ValueNoise12(pt / 90.0) * 0.55 + ValueNoise12(pt / 23.0 + 11.0) * 0.45);
                half hue = (half)(ValueNoise12(pt / 140.0 + 41.0) - 0.5);
                half3 tint = half3(1.0 + 0.05 * hue, 1.0, 1.0 - 0.05 * hue);
                half mid = (half)(ValueNoise12(pt / 7.0 + 83.0) - 0.5);
                return (1.0 + 1.4 * (tv - 0.5) + 0.3 * mid) * tint;
            }

            // Inward distance (m) to a rounded rectangle from the distances b = (to the x edges, to the y edges): the straight
            // sides away from the corners, an arc of radius rc inside a corner box. (The older mask used
            // min(b, rc - |max(rc - b, 0)|), which caps the interior at rc: fine for rc >= 6 cm with the 3-7 cm noise of
            // that mask, but a hole-ridden patch for saw-cut corners of 2 cm - ADR 0335, render r5.)
            float RoundedInset(float2 b, float rc)
            {
                float2 d = max(rc - b, 0.0);
                return (d.x > 0.0 && d.y > 0.0) ? rc - length(d) : min(b.x, b.y);
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
                half paintFresh = 0.0;
                half paintRenewed = 0.0;
            #if defined(_DECAL_PAINT)
                // Fresh longitudinal [4,5), transverse [6,7). Renewed over milled overlay (ADR 0335 P2):
                // [8,9) longitudinal, [10,11) transverse. Preserve legacy no-data (-1,5).
                paintFresh = step(4.0, i.uv.w) * (1.0 - step(5.0, i.uv.w))
                           + step(6.0, i.uv.w) * (1.0 - step(7.0, i.uv.w));
                paintRenewed = step(8.0, i.uv.w) * (1.0 - step(9.0, i.uv.w))
                             + step(10.0, i.uv.w) * (1.0 - step(11.0, i.uv.w));
            #endif

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

                #if defined(_CARPAINT)
                if (_CarFlake.w > 0.5) uvb.x += i.carFilm.y;
                #endif

            #if defined(_TOWN_PAVEMENT)
                // ADR 0237 s24: surface index is constant across a triangle, also at material boundaries.
                int walkType = _SidewalkTiles.x > 0.0 && i.masks.a > 0.5 ? (int)round(i.masks.r * 3.0) : 0;
                float2 du = ddx(uvb), dv = ddy(uvb);
                half4 base, mask, normalTex;
                UNITY_BRANCH
                if (walkType >= 2)
                {
                    float2 size = walkType == 2 ? _SidewalkTiles.xy : _SidewalkTiles.zw;
                    uvb = um / size;
                    du *= _Tile.xy / size;
                    dv *= _Tile.xy / size;
                    UNITY_BRANCH
                    if (walkType == 2)
                    {
                        base = SAMPLE_TEXTURE2D_GRAD(_WalkSlabBaseMap, sampler_BaseMap, uvb, du, dv);
                        mask = SAMPLE_TEXTURE2D_GRAD(_WalkSlabMaskMap, sampler_MaskMap, uvb, du, dv);
                        normalTex = SAMPLE_TEXTURE2D_GRAD(_WalkSlabNormalMap, sampler_NormalMap, uvb, du, dv);
                    }
                    else
                    {
                        base = SAMPLE_TEXTURE2D_GRAD(_WalkAsphaltBaseMap, sampler_BaseMap, uvb, du, dv);
                        mask = SAMPLE_TEXTURE2D_GRAD(_WalkAsphaltMaskMap, sampler_MaskMap, uvb, du, dv);
                        normalTex = SAMPLE_TEXTURE2D_GRAD(_WalkAsphaltNormalMap, sampler_NormalMap, uvb, du, dv);
                    }
                }
                else
                {
                    base = SAMPLE_TEXTURE2D_GRAD(_BaseMap, sampler_BaseMap, uvb, du, dv);
                    mask = SAMPLE_TEXTURE2D_GRAD(_MaskMap, sampler_MaskMap, uvb, du, dv);
                    normalTex = SAMPLE_TEXTURE2D_GRAD(_NormalMap, sampler_NormalMap, uvb, du, dv);
                    if (walkType == 1) base.rgb *= half3(1.01h, 0.60h, 0.53h); // aged red concrete; WORKING_VALUE
                }
            #else
                const int walkType = 0;
                half4 base = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uvb);
                half4 mask = SAMPLE_TEXTURE2D(_MaskMap, sampler_MaskMap, uvb);
                half4 normalTex = SAMPLE_TEXTURE2D(_NormalMap, sampler_NormalMap, uvb);
            #endif
                half3 tn = UnpackNormalScale(normalTex, _NormalStrength);
                #if defined(_CARPAINT)
                half carFilmOpacity = 0.0h;
                if (_CarFlake.w > 0.5)
                {
                    // WORKING_VALUE: source UV1 is height above the actual class sill
                    // and an affine rear=0/front=1 axle coordinate. No film inversion.
                    half frontTrail = saturate(1.0h - abs(i.uv.w - 0.87h) / 0.28h);
                    half rearTrail = saturate(1.0h - abs(i.uv.w + 0.13h) / 0.28h);
                    half rearFace = saturate((-i.uv.w - 0.20h) * 8.0h);
                    half deposition = max(max(frontTrail, rearTrail), rearFace);
                    half amount, falloff;
                    half keepUpper = 0.0h;
                    if (_CarFlake.w < 1.5)
                    {
                        amount = 0.08h + 0.92h * i.carFilm.x;
                        falloff = 0.16h + 0.06h * i.carFilm.x;
                        // ADR0089 life r3 A, WORKING_VALUE: broader only behind
                        // axles and on the rear. Still monotone above the sill,
                        // bounded by the existing 0.5 opacity, no new sampling.
                        falloff += deposition * (0.12h + 0.12h * i.carFilm.x)
                                 + rearFace * 0.10h * (0.25h + 0.75h * i.carFilm.x);
                        // ADR0089 life r3 C, WORKING_VALUE: the level-2 rear
                        // still looked freshly washed from 5.7 m. Broaden the
                        // rear-quarter/tail only, never detach film from the sill.
                        amount = saturate(amount + rearFace * 0.16h * (0.25h + 0.75h * i.carFilm.x));
                        falloff += rearFace * (0.18h + 0.18h * i.carFilm.x);
                        // Preserve the existing passenger-car bonnet/roof response.
                        // Static cabs opt out: their previous plain paint had no such layer.
                        keepUpper = smoothstep(0.45h, 0.85h, abs(n.y)) * smoothstep(0.6, 0.8, um.y);
                        half upperFilm = saturate(mask.r);
                        half3 legacyMultiplier = (1.0h - 0.30h * upperFilm) * half3(1.0h, 1.0h - 0.08h * upperFilm, 1.0h - 0.22h * upperFilm);
                        base.rgb *= lerp(half3(1, 1, 1), legacyMultiplier, keepUpper);
                        mask.a = saturate(mask.a - 0.35h * upperFilm * keepUpper);
                    }
                    else
                    {
                        // ADR 0122 C, WORKING_VALUE: yard-cab film was almost
                        // invisible with the passenger-car sill envelope.
                        // Keep the four instance levels, broaden only static cabs.
                        amount = 0.25h + 0.75h * i.carFilm.x;
                        falloff = 0.32h + 0.16h * i.carFilm.x;
                    }
                    half vertical = exp2(-max(i.uv.z, 0.0) / falloff * 1.442695h);
                    carFilmOpacity = 0.5h * amount * vertical * (0.72h + 0.28h * deposition) * (1.0h - keepUpper);
                    mask.a = lerp(mask.a, 0.25h, carFilmOpacity);
                }
                #endif
                half3 albedo = base.rgb * _Tint.rgb * _AlbedoScale;
                #if defined(_CARPAINT)
                albedo = lerp(albedo, half3(0.240h, 0.230h, 0.205h), carFilmOpacity);
                #endif
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
                // ---- ADR 0295 (review 2026-11-18 P1-4 "jednolity szum na wszystkim"): kept sward away from the roads
                // (terrain COLOR_0: R > 10-18 m from a road / yard, B dryness below 0.3-0.6 = lawns, gardens, meadows
                // and crops of the field mosaic) carries no scorched straw patches and no bare-soil spots, and half
                // the 8-64 m tone clouds - a meadow is one sward, a field one crop. Dry unmown ground (B high) and
                // the verge beside the road keep every patch. No fetch, no keyword; strength = _GroundTint.
                // ---- ADR 0298: farmland mosaic per pixel (flag in COLOR_0.b), before anything reads the masks
                // ADR 0334: the use of the strip replaces the grass colour by a cover weight (fieldAlb.a), not a tint
                half4 fieldAlb = half4(0.0h, 0.0h, 0.0h, 0.0h);
                half2 fieldSlope = half2(0.0h, 0.0h);     // ADR 0334 r2: furrows / rows of the field (dE, dN)
            #if defined(_GROUNDMASKS)
                {
                    float2 enDx = ddx(i.posEN), enDy = ddy(i.posEN);     // outside the branch (gradients)
                    half2 mbD = half2(ddx(i.masks.b), ddy(i.masks.b));
                    if (_RegionOriginEN.z > 0.5)
                        KamionFieldMosaic(i.posEN, _RegionOriginEN.xy, footprint, enDx, enDy, mbD, macro.g, macro.a, i.masks, fieldAlb, fieldSlope);
                }
            #endif
                half swardCalm = 0.0;
            #if defined(_GRASS_DETILE) && defined(_GROUNDMASKS)
                swardCalm = _GroundTint * smoothstep(0.5, 0.9, i.masks.r) * (1.0 - smoothstep(0.30, 0.60, i.masks.b))
                            * (1.0 - i.masks.g) * (1.0 - i.masks.a);
            #endif
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
                    keep *= 1.0 - swardCalm;
                #if defined(_GROUNDMASKS)
                    keep = max(keep, KamionGrassGrit(i.masks, macro.a));
                #endif
                    half glum = dot(_GrassFill.rgb, half3(0.2126, 0.7152, 0.0722));
                    half lumA = dot(albedo, half3(0.2126, 0.7152, 0.0722));
                    half3 refill = _GrassFill.rgb * clamp(lumA / max(glum, 1e-3), 0.6, 1.4);
                    albedo = lerp(albedo, refill, saturate(soil * 1.6) * (1.0 - keep));
                    // ---- ADR 0311 dopisek (bank-smear-s24): a ditch bank seen almost edge-on (tykocin route_s0160: 33 deg
                    // cut slope, eye 2.5 m above the road) packs 3-5 m of planar UV into a few pixels across the bank and
                    // keeps full detail along it - a footprint 15-100x longer than wide, beyond the sampler's anisotropy
                    // (PC High 8x). The tile then shows as streaks running along the bank: an olive "smeared texture"
                    // ribbon (diag render KAMION_QA_DIAG colorby:wpos / nrm, artifacts/bank-smear-s24). On sloped facets
                    // at such a footprint the tile is read once more with an isotropic footprint (its major axis on both
                    // axes: the tile mean of that area, no streaks) and only its luminance is kept on the calibrated
                    // sward colour; normal / occlusion / smoothness detail fade to flat / the tile mean. Flat ground keeps
                    // the existing distance look (facet-slope gate). +2 fetches inside the branch only. WORKING_VALUE
                    // thresholds, judged on route_s0160.
                    {
                        float2 gx = ddx(uvb), gy = ddy(uvb);
                        float major2 = max(dot(gx, gx), dot(gy, gy));
                        float area = abs(gx.x * gy.y - gx.y * gy.x);
                        half aniso = (half)(major2 / max(area, 1e-12));                   // footprint length / width
                        // slope of the facet itself: the terrain band's vertex normals are central differences over 2 m
                        // and read a 33 deg ditch side as ~15 deg next to the bottom of the V
                        float3 gnf = cross(ddy(pw), ddx(pw));
                        half gny = (half)(abs(gnf.y) * rsqrt(max(dot(gnf, gnf), 1e-20)));
                        half graze = smoothstep(4.0h, 12.0h, aniso) * smoothstep(0.98h, 0.88h, gny);
                        if (graze > 0.0h)
                        {
                            float2 gi = float2(sqrt(major2), 0.0);
                            half3 iso = SAMPLE_TEXTURE2D_GRAD(_BaseMap, sampler_BaseMap, uvb, gi, gi.yx).rgb * _Tint.rgb * _AlbedoScale;
                            half4 mIso = SAMPLE_TEXTURE2D_GRAD(_MaskMap, sampler_MaskMap, uvb, gi, gi.yx);
                            half lumI = dot(iso, half3(0.2126, 0.7152, 0.0722));
                            half3 sward = _GrassFill.rgb * clamp(lumI / max(glum, 1e-3), 0.75, 1.25);
                            albedo = lerp(albedo, sward, graze);
                            ao = lerp(ao, mIso.g, graze);
                            smooth = lerp(smooth, mIso.a * _SmoothnessScale, graze);
                            tn = normalize(lerp(tn, half3(0.0h, 0.0h, 1.0h), graze));
                        }
                    }
                    // ---- ADR 0080: a lawn is not one green. _KamionWet.z = strength (0 = the old look; set per preset).
                    // No extra fetch: the 64 m macro map and the tile's own luminance drive everything.
                    //  - clumps: lusher, darker, greener tufts (clover / fresh growth) in 0.5-4 m mottling;
                    //  - scorched patches: straw-coloured, lighter (sun-burnt / trampled / dog spots) where the 8-64 m
                    //    tone and the wear mask agree, edges broken by the mottling;
                    //  - micro shading: blade tips lighter, gaps between tufts darker (the tile's luminance as height);
                    //  - Medium+: daisies / dandelions as 4-5 cm dots in the lush clumps, faded out by pixel footprint
                    //    (gone by ~12 m), never on the scorched patches.
                    half gv = (half)_KamionWet.z;
                    if (gv > 0.0)
                    {
                        half lumG = dot(albedo, half3(0.2126, 0.7152, 0.0722));
                        half clump = smoothstep(0.42, 0.68, macro.a * 0.7 + macro.g * 0.3) * (1.0 - 0.5 * swardCalm);
                        albedo *= lerp(half3(1, 1, 1), half3(0.74, 0.86, 0.70), clump * gv);
                        half burn = smoothstep(0.58, 0.68, macro.r * 0.55 + macro.b * 0.45 - (macro.a - 0.5) * 0.35) * (1.0 - 0.9 * swardCalm);
                        half3 straw = half3(1.55, 1.30, 0.72) * lumG * 1.15;
                        albedo = lerp(albedo, straw, burn * 0.5 * gv);
                        half micro = saturate(lumG / max(glum, 1e-3) - 0.5);          // 0 gaps .. 1 tips
                        albedo *= lerp(1.0, lerp(0.72, 1.16, micro), gv * saturate(0.06 / footprint));
                    #if defined(_KAMION_WORLD_DETAIL)
                        half ff = saturate(0.022 / footprint - 0.6) * gv;
                        if (ff > 0.0)
                        {
                            float2 cu = pw.xz / 0.09;
                            float2 ci = floor(cu);
                            float hsh = Hash12(ci);
                            float2 cf = cu - ci - 0.5 - (float2(Hash12(ci + 7.3), Hash12(ci + 3.1)) - 0.5) * 0.5;
                            half dot1 = saturate(1.0 - dot(cf, cf) / 0.05);
                            half present = step(0.965, hsh) * smoothstep(0.5, 0.75, clump) * (1.0 - burn);
                            half3 petal = hsh > 0.983 ? half3(0.62, 0.50, 0.04) : half3(0.66, 0.66, 0.60);
                            albedo = lerp(albedo, petal, saturate(dot1 * 3.0) * present * ff);
                        }
                    #endif
                    }
                }
            #endif
                // ADR 0334 r3: luminance of the DE-TILED grass (after the rotated second sample) - the field mosaic used the
                // raw first sample for its blade detail, so the 3 m tile showed through every meadow and crop
                half grassLum = dot(albedo, half3(0.2126, 0.7152, 0.0722));
                half tone = ((macro.r - 0.5) * 1.4 + (macro.g - 0.5) * 0.6 + (macro.a - 0.5) * 0.4) * (1.0 - 0.5 * swardCalm);
            #if defined(_PANELTONE)
                {
                    // ADR 0092 (review 2026-11-11 s9 par. 4): a coated sandwich-panel wall does not drift in tone like a
                    // cloud - every panel is one sheet from one coil, so the tone steps at the panel joints. The macro
                    // drift is sampled once per panel (at its centre, in the wall's own UV0 metres: u along, v up) and
                    // mixed with a per-panel hash (lot-to-lot difference of neighbouring panels). One point sample.
                    float2 cellf = um / _PanelTone.xy;
                    float2 cell = floor(cellf);
                    float2 pc = (cell + 0.5) * _PanelTone.xy;
                    half4 mp = SAMPLE_TEXTURE2D_LOD(_MacroMap, sampler_MacroMap, pc / _MacroSize + 0.19, 0);
                    float3 p3 = frac(float3(cell.xyx) * float3(0.1031, 0.1030, 0.0973));
                    p3 += dot(p3, p3.yzx + 33.33);
                    half hsh = frac((p3.x + p3.y) * p3.z);
                    half drift = (mp.r - 0.5) * 1.4 + (mp.g - 0.5) * 0.6 + (mp.a - 0.5) * 0.4;
                    tone = drift * (1.0 - _PanelTone.z) + (hsh - 0.5) * 2.0 * _PanelTone.z;
                    // butt joint between two panels of a course (the set draws only the horizontal shadow gaps)
                    float du = abs(frac(cellf.x) - 0.5) * _PanelTone.x;                  // 0 at mid-panel
                    float fwu = max(fwidth(um.x), 1e-4);
                    half jl = 1.0 - saturate((0.5 * _PanelTone.x - du - 0.006) / fwu);
                    albedo *= 1.0 - _PanelTone.w * jl * saturate(0.012 / fwu);
                }
            #endif
                albedo *= 1.0 + _MacroStrength * tone;
                half wear = saturate((macro.b - 0.5) * 2.0);          // > 0: worn / soiled patches
                albedo *= 1.0 + _MacroWear * (macro.b - 0.5) * 0.8;
                smooth *= 1.0 - _MacroWear * wear * 0.5;

                // ---- per-element tone jitter (paving blocks, slabs): Var.G id + world tile index, faded when an
                // element is smaller than ~2 px (no sparkle far away)
            #if defined(_KAMION_WORLD_DETAIL) && !defined(_DECAL_ALPHA) && !defined(_DECAL_TYRE)
                if (_ElementJitter > 0.0 && walkType != 3)
                {
                #if defined(_TOWN_PAVEMENT)
                    half4 var = walkType == 2 ? SAMPLE_TEXTURE2D_LOD(_WalkSlabVarMap, sampler_point_repeat, uvb, 0)
                                              : SAMPLE_TEXTURE2D_LOD(_VarMap, sampler_point_repeat, uvb, 0);
                #else
                    half4 var = SAMPLE_TEXTURE2D_LOD(_VarMap, sampler_point_repeat, uvb, 0);
                #endif
                    float id = var.g + Hash12(floor(uvb) + 17.0);
                    half j = (Hash12(float2(id * 97.0, 3.1)) - 0.5) * 2.0;
                    half fade = saturate((walkType == 2 ? 0.35 : _ElementSize) / (footprint * 2.5) - 0.5);
                    albedo *= 1.0 + _ElementJitter * j * fade;
                    if (_PavingWeed.w > 0.5)
                    {
                        // Subtle per-block warm/cool cement hue drift (ADR 0349)
                        half h2 = (Hash12(float2(id * 53.0, 9.7)) - 0.5) * 2.0;
                        albedo *= half3(1.0 + 0.038 * h2 * fade, 1.0 + 0.008 * h2 * fade, 1.0 - 0.044 * h2 * fade);
                    }
                    // joints collect dirt / moss (Var.B)
                    albedo = lerp(albedo, albedo * half3(0.78, 0.8, 0.72), var.b * 0.5 * fade);
                }
            #endif

                // ---- crack layer (asphalt): open cracks darken, sealant bands glossy black; faded by macro wear so
                // whole stretches can be sound
            #if defined(_CRACKS)
            #if !defined(_KAMION_WORLD_DETAIL)
                if (_AsphaltWear.z > 0.5 && paintFresh < 0.5) // existing mask, no crack normal on Low
            #endif
                {
                    float2 uc = pw.xz / _Tile.z;
                    half4 cm = SAMPLE_TEXTURE2D(_CrackMap, sampler_CrackMap, uc);
                    half amount = _CrackStrength * saturate(0.25 + (macro.b - 0.35) * 2.2) * (1.0 - paintFresh);
                #if defined(_ROADWEAR)
                    {
                        // ADR 0323 (critic wave 6 pkt 2.2): edge distress. The outer 0.6-1.8 m of a carriageway (unsupported
                        // edge, water in the shoulder) cracks first: the crack layer is at full strength there in 5-20 m
                        // stretches (object-space value noise, stable across origin rebases) and the ravelled surface
                        // is a little lighter. Ribbons only (TEXCOORD_1.y = distance to the edge; plates carry >= 20).
                        float ed = i.uv.w;
                        half eb = (half)((1.0 - smoothstep(0.6, 1.8, ed)) * step(-0.5, i.uv.z) * step(ed, 15.0));
                        float2 pe = TransformWorldToObject(pw).xz;
                        eb *= (half)smoothstep(0.42, 0.62, ValueNoise12(pe / 11.0) * 0.7 + ValueNoise12(pe / 3.1 + 5.0) * 0.3);
                        eb *= 1.0 - paintFresh;
                        amount = saturate(amount + _CrackStrength * eb);
                        albedo *= 1.0 + 0.07 * eb;
                    }
                #endif
                    albedo *= lerp(1.0, 0.35, cm.r * amount);
                    albedo = lerp(albedo, half3(0.03, 0.03, 0.03), cm.g * amount);
                    albedo *= 1.0 - cm.a * amount * 0.22;
                    // ADR 0131: aged, dust-filmed bitumen sealant - a dark band only slightly smoother than the asphalt
                    // around it (+0.06, WORKING_VALUE). At 0.55 the env term at grazing NoV (grazing = smooth)
                    // out-reflected the 0.03 albedo and the sealant read as white chalk, also under an overcast sky;
                    // at 0.24 it cancelled the dark albedo exactly (invisible from the driver's eye height).
                    smooth = lerp(smooth, smooth + 0.06, cm.g * amount);
                #if defined(_KAMION_WORLD_DETAIL)
                    half3 cn = UnpackNormalScale(SAMPLE_TEXTURE2D(_CrackNormal, sampler_CrackMap, uc), amount);
                    tn = normalize(half3(tn.xy + cn.xy, tn.z * cn.z));
                #endif
                }
            #endif

                // ---- close-range photo detail (asphalt), fades out by _DetailFade
            #if defined(_PHOTO_DETAIL)
            #if !defined(_KAMION_WORLD_DETAIL)
                if (_AsphaltWear.w > 0.001 && paintFresh < 0.5) // explicit Low albedo-only detail
            #endif
                {
                    float dist = length(GetCameraPositionWS() - pw);
                    half f = saturate(1.0 - dist / _DetailFade) * mask.b * (1.0 - paintFresh);
                #if !defined(_KAMION_WORLD_DETAIL)
                    f *= _AsphaltWear.w;
                #endif
                    if (f > 0.001)
                    {
                        float2 ud = pw.xz / _Tile.w;
                        half d = SAMPLE_TEXTURE2D(_DetailAlbedo, sampler_DetailAlbedo, ud).r;
                        albedo *= lerp(1.0, d * 4.594794, f);          // unity_ColorSpaceDouble (linear)
                    #if defined(_KAMION_WORLD_DETAIL)
                        half3 dn = UnpackNormalScale(SAMPLE_TEXTURE2D(_DetailNormal, sampler_DetailAlbedo, ud), f);
                        tn = normalize(half3(tn.xy + dn.xy, tn.z * dn.z));
                    #endif
                    }
                }
            #endif

                // ---- road wear from TEXCOORD_1 = (lane coordinate, distance to carriageway edge); (-1, 5) = no data
            #if defined(_ROADWEAR)
                {
                    float2 w = i.uv.zw;
                    half onPlate = (half)step(15.0, w.y);    // junction plate vertices (roads.meshing._patch_uv1)
                    half plate = KamionPlateWear(w);          // ADR 0194: junction box, wheel paths smeared by turning
                    albedo *= lerp(_AsphaltWear.x, _PaintFreshWear.w, paintFresh);
                    // ADR 0335 (critic build #5 pkt 4: "asfalt jednolity na prostych"): the pavement is not one tone for
                    // kilometres. Two octaves of object-space noise (stable across origin rebases, identical on ribbons,
                    // plates and junction patches, so no seams): 90 m = resurfaced / sun-bleached stretches, 23 m = patched
                    // binder; +-9..12 % lightness (r2: x1.7, +-6 % at 7 m) and a +-2.5 % warm / cool shift (tar-rich brown vs. weathered grey).
                    // Fresh asphalt stays uniform. WORKING_VALUE, judged against Commons DW671 (cs11749508).
                    {
                        albedo *= lerp(half3(1, 1, 1), KamionRoadTone(TransformWorldToObject(pw).xz), 1.0 - paintFresh);
                    }
                    float rwFpx = max(length(fwidth(pw.xz)), 1e-4);
                    float rwFwx = fwidth(w.x);
                    if (w.x > -0.5)        // (-1, 5) = no road data (junction patches, kerbs)
                    {
                        float rwDist = length(GetCameraPositionWS() - pw);
                        // ADR 0335 P2: perspective foreshortening + loss of close-range normal/detail relief made distant
                        // wheel paths read darker than near the camera. Pre-filter the analytical stripe and high-freq
                        // noise by pixel footprint, and attenuate contrast gently with distance (1.0 <= 25 m -> 0.50 >= 130 m).
                        // WORKING_VALUE.
                        // P2b (rut-far-s24): same-ground measurement showed the 0.50 / 25-130 m ramp left the final-pixel rut
                        // depth flat to 120 m (near albedo texture hides the stripes, far texture mips away and leaves them as the
                        // only dark lines to the horizon), so: 1.0 <= 20 m -> 0.40 >= 120 m.
                        // render-artifacts-s24 (critic wave 11 P1 #6 "pionowe ciemne smugi zbiegajace sie do horyzontu";
                        // measured route-s1846: 3 equally dark continuous bands per lane, -12..-16 %, visible to the horizon;
                        // gone with _ROADWEAR off, unchanged with shadows / wires off): the bands converge in perspective,
                        // so their far contrast must die, not halve: 1.0 <= 15 m -> 0.15 >= 90 m. WORKING_VALUE.
                        half rwDistAtten = (half)(1.0 - 0.85 * smoothstep(15.0, 90.0, rwDist));
                        // one 38 m object-space noise: the track fade below AND the lateral wander of the wheel paths
                        // (drivers do not hold the lane line to the centimetre: +-5 % of a lane over tens of metres)
                        half n38 = (half)ValueNoise12(TransformWorldToObject(pw).xz / 38.0 + 53.0);
                        // wheel paths at ~0.25 / 0.75 of a lane: darker binder-rich, smoother
                        float lc = frac(w.x);
                        // P2b: area-preserving prefilter (box ~ pixel footprint): the stripe widens to >= 1.2 px and its amplitude
                        // drops by the same ratio, so far away it converges to the track's mean darkening instead of aliasing
                        // (the old `* saturate(0.11 / fwx)` shrank the area and never engaged below ~300 m).
                        // render-artifacts-s24: smoothstep profile (the linear tent had a dark ridge line in its middle), 0.13 lane
                        half rwW = (half)max(0.13, 1.2 * rwFwx);
                        half lw = (half)abs(abs(lc - 0.5 + (n38 - 0.5h) * 0.10h) - 0.24);
                        half wp = (1.0h - smoothstep(0.0h, rwW, lw)) * (0.13h / rwW);
                        wp *= lerp(1.0h, (half)KAMION_PLATE_WHEEL_KEEP, plate);
                    #if defined(KAMION_RUT_PROBE_OFF)
                        wp = 0;     // measurement probe only (ADR 0335 P2b): final-pixel rut contrast = render(on) - render(off)
                    #endif
                        // build #3 P3 (DK65 / Knyszyn roundabout mouths): the wheel paths ran as continuous dark stripes of
                        // one strength along every lane (3 per lane: 2 paths + drip band), bending with the flared
                        // single-lane ribbons around the splitter islands - the same stripe pattern at every mouth.
                        // Real polish varies along the road with braking / loading: broken into 1-6 m patches (object-
                        // space value noise, stable across origin rebases), keeping 55-125 % of the old strength
                        // (mean ~0.84); on junction plates (lane coordinate interpolated over large triangles) half
                        // of that. WORKING_VALUE, judged against the build #3 frame t=1530.
                        {
                            float2 po = TransformWorldToObject(pw).xz;
                            half brkHi = lerp(0.5h, (half)ValueNoise12(po / 1.3 + 17.0), (half)saturate(0.5 / rwFpx));
                            half brk = (half)(ValueNoise12(po / 4.3) * 0.65) + brkHi * 0.35h;
                            half keep = lerp(0.55h, 1.25h, smoothstep(0.32h, 0.72h, brk));
                            wp *= keep * lerp(1.0h, 0.5h, onPlate);
                        }
                        // ADR0118: traffic polish darkens binder; existing macro breaks continuous bands.
                        // Traffic accumulation varies over metres (G: 2-16 m), not the sub-metre A noise.
                        // Keep the original mean modulation 0.825 while avoiding a fine grid in wheel paths.
                        half traffic = _AsphaltWear.y * (0.70 + 0.25 * macro.g);
                        // ADR 0335: x1.35 (r1 x1.25 was invisible from the cab, r2 x2.0 read as rails - critic round 3), and the
                        // contrast of a track fades to 35-100 % over 20-60 m stretches (object-space noise)
                        // render-artifacts-s24: x1.35 -> x0.75 (with the wider smooth profile: ~-6 % in the path core near the cab)
                        half trackFade = (half)lerp(0.35, 1.0, smoothstep(0.30, 0.60, n38));
                        albedo *= 1.0 - wp * 0.75 * trackFade * rwDistAtten * (0.10 * _WheelPolish + traffic) * (1.0 - paintFresh);
                        smooth = lerp(smooth, smooth + 0.12, wp * _WheelPolish * rwDistAtten);
                    #if !defined(_DECAL_PAINT)
                        // gutter: grit, leaves and soot within ~0.6 m of the kerb
                        half g = (1.0 - smoothstep(0.05, 0.65, w.y)) * _GutterDirt;
                        albedo = lerp(albedo, albedo * half3(1.12, 1.06, 0.92) + half3(0.012, 0.010, 0.006), g);
                        smooth *= 1.0 - 0.4 * g;
                        // ADR 0060 (review r7 N-2): the gutter's lowest ~0.25 m stays damp (water runs along the kerb to the
                        // gullies), broken where the macro mottling says the grit is dry
                        half damp = (1.0 - smoothstep(0.08, 0.3, w.y)) * saturate(0.35 + (macro.a - 0.5) * 2.0 + (macro.b - 0.5)) * _GutterDirt;
                        albedo *= 1.0 - 0.5 * damp;
                        smooth = lerp(smooth, 0.55, damp);
                        // ADR 0335: edge discolouration of the carriageway (ribbons only: plates carry w.y >= 15) in 3-14 m
                        // stretches: dark run-off / exhaust film (up to -17 %, outer 0.1-0.9 m) or pale sand-and-dust residue
                        // (ADR 0335 P2: widened gently to 0.35-1.40 m with multi-scale tongues toward ref cs11749508). WORKING_VALUE.
                        {
                            float2 pg = TransformWorldToObject(pw).xz;
                            half ev = (half)smoothstep(0.38, 0.62, ValueNoise12(pg / 7.0 + 29.0) * 0.75 + ValueNoise12(pg / 1.9 + 5.0) * 0.25);
                            half onRibbon = (half)step(w.y, 15.0) * (half)(1.0 - paintFresh);
                            half tongue = (half)(0.2 + 0.7 * ValueNoise12(pg / 1.3 + 71.0));
                            half eband = (half)(1.0 - smoothstep(0.1, tongue, w.y)) * onRibbon;
                            half sandTongue = (half)(0.35 + 1.05 * (ValueNoise12(pg / 1.5 + 71.0) * 0.65 + ValueNoise12(pg / 4.3 + 19.0) * 0.35));
                            half sband = (half)(1.0 - smoothstep(0.12, sandTongue, w.y)) * onRibbon;
                            half sandy = (half)smoothstep(0.66, 0.42, ValueNoise12(pg / 13.0 + 61.0));   // ~55 % of the length
                            albedo *= 1.0 - 0.17 * eband * ev * (0.6 + 0.4 * macro.b);
                            half sandW = 0.62h * sband * (1.0h - ev) * sandy;
                            albedo = lerp(albedo, half3(0.17, 0.145, 0.11), sandW);
                            smooth *= 1.0h - 0.35h * sandW;
                        }
                    #endif
                        // oil / soot drip band between the wheel paths (lane centre 0.5 +- ~0.12), mottled, strongest where
                        // traffic queues; WORKING_VALUE darkening, the band is ~0.8 m of a 3.5 m lane
                        // ADR 0335: the band is not a ruler line along every lane - it wanders +-8 % of a lane, is absent
                        // from ~35 % of the road (17 m stretches of object-space noise; cars that do not leak) and where it
                        // exists it is a trail of drops (1 m noise) with the odd 0.3-0.8 m blot (darker, glossier).
                        float2 pdr = TransformWorldToObject(pw).xz;
                        half wander = (half)((ValueNoise12(pdr / 5.0 + 3.0) - 0.5) * 0.16);
                        half present = (half)smoothstep(0.30, 0.55, ValueNoise12(pdr / 17.0 + 7.0));
                        half dropNoise = lerp(0.5h, (half)ValueNoise12(pdr / 0.9 + 19.0), (half)saturate(0.45 / rwFpx));
                        half drops = (half)lerp(0.45, 1.0, smoothstep(0.35, 0.65, dropNoise));
                        half drip = saturate(1.0 - abs(lc - 0.5 - wander) / 0.12) * saturate(0.45 + (macro.a - 0.5) * 2.2 + (macro.g - 0.5) * 0.8);
                        drip *= present * drops * 1.2h;   // render-artifacts-s24: 1.9 -> 1.2 (read as a third rail per lane)
                        half blot = (half)smoothstep(0.80, 0.88, ValueNoise12(pdr / 0.55 + 23.0)) * (half)saturate(0.35 / rwFpx) * saturate(1.0 - abs(lc - 0.5 - wander) / 0.2) * present;
                        drip = max(drip, blot * 1.8h);
                        drip *= lerp(1.0h, (half)KAMION_PLATE_DRIP_KEEP, plate);
                        albedo *= 1.0 - _DripBand * drip * rwDistAtten * (1.0 - paintFresh);
                        smooth = lerp(smooth, smooth + 0.12h, blot * (1.0 - paintFresh));
                    }
                }
            #endif

                // ADR0118: leave a separately owned site at its original material response.
                // World chunk mesh coordinates are authoring E/N; object space survives origin shifts.
                // Inside the bounds: exactly zero new wear. Outside: an 8 m transition avoids a visible seam.
                half groundWear = 1.0;
                if (_GroundWearExclude.z > _GroundWearExclude.x && _GroundWearExclude.w > _GroundWearExclude.y)
                {
                    float2 localEN = TransformWorldToObject(pw).xz;
                    float2 outside = max(_GroundWearExclude.xy - localEN, localEN - _GroundWearExclude.zw);
                    groundWear = saturate(max(outside.x, outside.y) * 0.125);
                }

                // ---- ground grime (ADR 0060, review r7 N-2): dirty joints on every tier (Var.B, the Medium+ element jitter
                // only adds tone) and damp / oily hollows: water and fines stay in the low points (Var.R height) of the
                // 1.5-24 m wear patches (macro B) broken by the 0.5-4 m mottling (macro A). Paving, yard concrete, yard and
                // path asphalt. Low: +1 fetch (Var, bilinear).
            #if defined(_GRIME)
                if (walkType != 3)
                {
                #if defined(_TOWN_PAVEMENT)
                    half4 gv = walkType == 2 ? SAMPLE_TEXTURE2D_GRAD(_WalkSlabVarMap, sampler_BaseMap, uvb, du, dv)
                                             : SAMPLE_TEXTURE2D_GRAD(_VarMap, sampler_BaseMap, uvb, du, dv);
                #else
                    half4 gv = SAMPLE_TEXTURE2D(_VarMap, sampler_BaseMap, uvb);
                #endif
                    float4 grime = _Grime;
                    if (groundWear < 1.0) grime = lerp(_GroundGrimeBase, _Grime, groundWear);
                    half jfade = saturate(0.012 / max(footprint, 1e-4));             // joints resolved: full dirt
                    albedo *= 1.0 - grime.z * gv.b * lerp(0.5, 1.0, jfade);
                    half pool = macro.b * 0.65 + macro.a * 0.35 - (gv.r - 0.7) * 0.06;
                    half thr = grime.y + KamionYardGrimeBias(_GrimeTraffic, i.uv.zw);   // ADR 0194
                    half wet = smoothstep(thr, thr + 0.025, pool);
                    albedo *= 1.0 - grime.x * wet;
                    smooth = lerp(smooth, max(smooth, 0.62), wet * grime.w);

                    // ---- ADR 0349 (dopisek neon-paving-s24): concrete block variation mask (zero extra draws / fetches).
                    // Deterministic from object-space E/N (survives floating-origin rebases); multiplied by groundWear so
                    // Kwadrat Park stays protected.
                    if (_PavingWeed.w > 0.5 && groundWear > 0.001)
                    {
                        float2 po = TransformWorldToObject(pw).xz;
                        float2 p45 = po - 45.0 * floor(po / 45.0);
                        half gw = groundWear;

                        // (a) 3 concrete pallet / batch tones stepped along 0.20 m paver courses
                        float course = walkType == 2 ? 0.35 : 0.20;
                        float2 pq = floor(p45 / course) * course;
                        float bv = ValueNoise12(pq / 5.5 + 13.7) * 0.65 + ValueNoise12(pq / 2.4 + 31.1) * 0.35;
                        half bCool = (half)(1.0 - smoothstep(0.34, 0.40, bv));
                        half bWarm = (half)smoothstep(0.60, 0.66, bv);
                        half3 batchMul = half3(1.0h, 1.0h, 0.99h);
                        batchMul = lerp(batchMul, half3(0.95h, 0.99h, 1.05h) * (1.0h + _PavingVar.x * 0.85h), bCool);
                        batchMul = lerp(batchMul, half3(1.07h, 1.01h, 0.91h) * (1.0h - _PavingVar.x * 0.95h), bWarm);
                        albedo *= lerp(half3(1.0h, 1.0h, 1.0h), batchMul, gw);

                        // (b) Sparse utility-trench / repair patches of different paving (~30 % of 8.5 m cells)
                        if (_PavingVar.w > 0.01)
                        {
                            float2 cell = floor(po / 8.5);
                            float h0 = Hash12(cell + 19.3);
                            if (h0 > 0.70)
                            {
                                float2 ctr = (cell + 0.25 + 0.50 * float2(Hash12(cell + 4.1), Hash12(cell + 8.7))) * 8.5;
                                float2 hsz = float2(0.55 + 0.85 * Hash12(cell + 12.3), 0.45 + 0.65 * Hash12(cell + 27.9));
                                float2 dp = abs(floor(po / course + 0.5) * course - ctr) - hsz;
                                float pDist = max(dp.x, dp.y);
                                half pMask = (half)(1.0 - smoothstep(-0.04, 0.04, pDist)) * _PavingVar.w * gw;
                                half pRim = (half)(1.0 - smoothstep(0.0, 0.09, abs(pDist))) * _PavingVar.w * gw;
                                float kindP = Hash12(cell + 43.2);
                                half3 pTone = kindP > 0.5
                                    ? half3(1.22h, 1.23h, 1.25h)   // newer pale-cool replacement pavers
                                    : half3(0.76h, 0.72h, 0.68h);  // darker warm-charcoal relaid blocks
                                albedo *= lerp(half3(1.0h, 1.0h, 1.0h), pTone, pMask);
                                // pale bedding-sand seam around the cut border
                                albedo = lerp(albedo, albedo * half3(1.14h, 1.11h, 1.02h) + half3(0.012h, 0.010h, 0.006h), pRim * 0.45h);
                                smooth = lerp(smooth, smooth * (kindP > 0.5 ? 1.15h : 0.82h), pMask);
                            }
                        }

                        // (c) Organic dark stains / leaf tannin + pale dusty efflorescence blotches
                        float stD = ValueNoise12(p45 / 2.2 + 5.3) * 0.60 + ValueNoise12(p45 / 0.65 + 17.9) * 0.40;
                        half darkStain = (half)smoothstep(0.58, 0.78, stD) * _PavingVar.y * gw;
                        albedo *= lerp(half3(1.0h, 1.0h, 1.0h), half3(0.64h, 0.62h, 0.56h), darkStain);
                        smooth *= 1.0h - 0.35h * darkStain;

                        float stL = ValueNoise12(p45 / 3.1 + 41.2) * 0.55 + ValueNoise12(p45 / 0.85 + 63.7) * 0.45;
                        half paleStain = (half)smoothstep(0.66, 0.85, stL) * (1.0h - darkStain) * _PavingVar.y * 0.65h * gw;
                        albedo = lerp(albedo, albedo * half3(1.16h, 1.15h, 1.10h) + half3(0.014h, 0.013h, 0.010h), paleStain);

                        // (d) Darker earthy joints (Var.B + Mask.G AO, mip-friendly)
                        half jointM = max(gv.b, saturate((0.88h - mask.g) * 3.0h));
                        half pjFade = (half)saturate(0.035 / max(footprint, 1e-4));
                        half jAmt = jointM * _PavingVar.z * lerp(0.45h, 1.0h, pjFade) * gw;
                        albedo = lerp(albedo, albedo * half3(0.56h, 0.53h, 0.46h), jAmt);
                        smooth *= 1.0h - 0.50h * jAmt;

                        // (e) Sparse muted weeds / moss in joints near kerb (u ~ 0.15 m) and back edge (u >= 1.5 m)
                        // Guarded against legacy (0, 0) and (-1, 5) missing UV1.
                        if (_PavingWeed.x > 0.01 && i.uv.z >= -0.5 && i.uv.w > 0.08 && i.uv.w < 10.0)
                        {
                            half nearKerb = 1.0h - (half)smoothstep(0.08, _PavingWeed.y, abs(i.uv.w - 0.15));
                            half nearBack = (half)smoothstep(1.45, 2.05, i.uv.w);
                            half edgeZone = max(nearKerb, nearBack);
                            float wn = ValueNoise12(p45 / 2.6 + 73.1) * 0.55 + ValueNoise12(p45 / 0.48 + 11.4) * 0.45;
                            float wFine = ValueNoise12(p45 / 0.14 + 29.7);
                            half tuft = (half)smoothstep(0.55, 0.73, wn) * (0.55h + 0.45h * (half)wFine);
                            half jCrack = saturate(jointM * 1.55h + saturate((0.90h - mask.g) * 2.5h) * 0.45h);
                            half weedM = jCrack * edgeZone * tuft * _PavingWeed.x * gw * lerp(0.35h, 1.0h, pjFade);
                            half3 weedCol = lerp(half3(0.055h, 0.078h, 0.028h), half3(0.095h, 0.092h, 0.038h), (half)wFine);
                            albedo = lerp(albedo, weedCol, weedM);
                            smooth = lerp(smooth, 0.08h, weedM);
                        }
                    }
                }
            #endif

            #if defined(_TOWN_PAVEMENT)
                if (walkType == 3)
                {
                    // Sparse bituminous reinstatement, with a softer edge than the joints of relaid blocks.
                    float2 po = TransformWorldToObject(pw).xz;
                    float2 cell = floor(po / 9.0);
                    float seed = Hash12(cell + 53.0);
                    float2 centre = (cell + 0.25 + 0.5 * float2(seed, Hash12(cell + 67.0))) * 9.0;
                    float2 edge = float2(0.6 + seed, 0.45 + seed * 0.6) - abs(po - centre);
                    float inset = RoundedInset(edge, 0.025);
                    half patch = step(0.72, seed) * smoothstep(-footprint, footprint, inset);
                    albedo *= 1.0h - 0.22h * patch;
                    smooth = lerp(smooth, max(smooth, 0.2h), patch * 0.25h);
                }
            #endif

                // ADR0118 r2: opt-in kerb mineral dirt, using already fetched masks only.
                // The kerb scan stores 1-joints in Mask.B (source PNG contract checked).
                // No new texture, UV channel or keyword variant on Low.
                if (_KerbWear.w > 0.5)
                {
                    half joints = saturate(1.0 - mask.b);
                    half film = smoothstep(_KerbWear.z, _KerbWear.z + 0.18, macro.b * 0.6 + macro.a * 0.4);
                    albedo *= (1.0 - groundWear * _KerbWear.x * joints) * (1.0 - groundWear * _KerbWear.y * film);
                }
            #if defined(_TOWN_PAVEMENT)
                if (_TownKerb > 0.5 && i.masks.a > 0.5)
                {
                    float along = i.uv.z;
                    float seed = Hash12(float2(floor(along), i.masks.r * 79.0));
                    albedo *= lerp(0.93h, 1.07h, seed);
                    // Small spalls near the gutter-side edge, represented by exposed aggregate on the top face.
                    float offset = frac(along) - (0.20 + seed * 0.52);
                    float depth = (0.018 + 0.010 * seed) * saturate(1.0 - abs(offset) / (0.035 + 0.040 * seed));
                    float aa = max(fwidth(i.uv.w), 0.001);
                    half spall = step(0.86, seed) * smoothstep(0.67, 0.9, n.y)
                               * smoothstep(-aa, aa, depth - i.uv.w) * step(0.001, depth);
                    albedo = lerp(albedo, albedo * 0.71h + 0.012h, spall);
                    smooth *= 1.0h - 0.4h * spall;
                }
            #endif

                // ---- decals
            #if defined(_DECAL_PATCH)
                {
                    half age = saturate(i.uv.z);
                    // ADR 0335: 1 milled overlay, 2 trench, 3 hot mix, 4 rut fill.
                    // Kind 0 uses the original mask and age response for yard repairs and old data.
                    float wRaw = i.uv.w;
                    float kindF = (wRaw >= 1.0 && wRaw < 5.0) ? floor(wRaw) : 0.0;
                    bool roadRepair = kindF > 0.5 && _PatchSeam.x > 0.0;
                    if (!roadRepair)
                    {
                        albedo = lerp(albedo, albedo * _AgeTint, age * 0.85);
                        smooth *= 1.0 - 0.45 * age;
                    }
                    if (_PatchSeam.x > 0.0)
                    {
                        // UV0 is normalised once per complete repair before chunk clipping (yard_wear.py).
                        // Recover perpendicular metres from the surface Jacobian: seal width stays physical on every
                        // patch size, orientation, or kerb-clipped shear (ADR 0335 P2).
                        float2 ux = ddx(i.uv.xy), uy = ddy(i.uv.xy);
                        float3 px = ddx(pw), py = ddy(pw);
                        float det = ux.x * uy.y - ux.y * uy.x;
                        float invAbs = 1.0 / max(abs(det), 1e-10);
                        float3 Eu0 = px * uy.y - py * ux.y;
                        float3 Ev0 = py * ux.x - px * uy.x;
                        float lenEu = length(Eu0), lenEv = length(Ev0);
                        float sinTheta = length(cross(Eu0 / max(lenEu, 1e-12), Ev0 / max(lenEv, 1e-12)));
                        float2 sizeM = float2(lenEu, lenEv) * (invAbs * max(sinTheta, 0.25));
                        float2 borderM = min(i.uv.xy, 1.0 - i.uv.xy) * sizeM;
                        // build #3 P2 (anti-slop): no ruler-straight rectangles. Rounded corners (radius 0.10-0.45 m
                        // from the patch seed, capped by the patch size) and a ragged outline from two octaves of value
                        // noise in object space (stable across floating-origin rebases); amplitude 0.05-0.14 m.
                        // The outer few cm blend into the road (alpha), so the outline reads as a worn joint.
                        // WORKING_VALUE, judged against the DW671 frames of build #3.
                        // ADR 0323 (critic wave 6 pkt 2.2 "nadal prostokatne"): two kinds of repair from the patch seed.
                        // Spray-injection / hand-laid blob (55 %): stadium outline eaten by 0.3-0.9 m noise up to
                        // 0.4 x the patch size, soft feathered edge. Saw-cut patch (45 %): nearly straight cuts with a
                        // hand-poured bitumen overband along them.
                        // ADR 0335 P2: keep bitumen overband width physical and even across opposite edges (0.70-1.00 x
                        // _PatchSeam.x, i.e. 4.2-6.0 cm); perimeter gaps modulate opacity (`sealMask`), not width.
                        float seed = roadRepair ? frac(wRaw) : wRaw;
                        float mn = min(sizeM.x, sizeM.y);
                        float2 objectXZ = TransformWorldToObject(pw).xz;
                        float2 on = objectXZ + seed * 97.0;
                        float n1 = ValueNoise12(on / 0.9), n2 = ValueNoise12(on / 0.28), n3 = ValueNoise12(on / 0.07);
                        // Keep the sub-pixel teeth from aliasing in a grazing view. The broad inset
                        // still breaks up the profile when the fine teeth fade.
                        float2 gp = on - 45.0 * floor(on / 45.0);
                        float fpx = max(length(fwidth(pw.xz)), 1e-4);
                        float broad = ValueNoise12(on / 0.72 + 13.0);
                        float chips = ValueNoise12(gp / 0.095 + 29.0);
                        float bite = min(mn * 0.19, 0.025 + 0.20 * broad * broad
                                                 + 0.045 * chips * saturate(0.095 / fpx));
                        float aa;
                        // bitumen overband 2-4 cm (_PatchSeam.x = 0.032 m -> 2.2-3.2 cm), straddling the cut
                        float baseSw = _PatchSeam.x * (0.70 + 0.30 * n2);
                        float sw;
                        float edgeM;
                        half hasSeal;
                        half sealMask;
                        float fth;
                        if (kindF < 0.5)
                        {
                        half blob = (half)step(frac(seed * 5.31), 0.55);
                        float rc = lerp(min(0.06 + 0.10 * frac(seed * 7.13), 0.45 * mn), 0.5 * mn, blob);
                        edgeM = min(min(borderM.x, borderM.y), rc - length(max(rc - borderM, 0.0)));
                        float amp = lerp(0.03 + 0.04 * frac(seed * 3.71), min(0.18 + 0.20 * frac(seed * 3.71), 0.4 * mn), blob);
                        edgeM -= amp * (n1 * 0.6 + n2 * 0.4) + 0.012 * n3;
                        fth = lerp(0.02, 0.06, blob);
                        hasSeal = max(1.0 - blob, (half)step(frac(seed * 11.7), 0.4));
                        sw = baseSw * hasSeal;
                        sealMask = hasSeal * (half)smoothstep(0.88, 0.72, n1);
                        }
                        else if (kindF < 1.5)
                        {
                            // MILLED overlay (frezowanie + nakladka): the transverse cuts follow the drum, but each end
                            // has its own skew (+-3 deg: the cut is marked by eye), and on 40 % of the overlays one end is
                            // staggered by 0.1-0.4 m over half the width (two passes of a 1 m drum). The longitudinal edges follow
                            // the old lane joint, hand-raked: 5-15 cm wander + bites. Sealed along the transverse cuts. WORKING_VALUE.
                            float vY = (i.uv.y - 0.5) * sizeM.y;                                     // lateral m from the axis
                            float sk = (i.uv.x < 0.5 ? frac(seed * 17.3) : frac(seed * 23.9)) - 0.5;
                            sk *= 0.10;
                            float endD = borderM.x - (sk * vY + 0.5 * abs(sk) * sizeM.y) - 0.35 * bite;
                            float latD = borderM.y - bite;
                            float rcn = min((0.04 + 0.16 * frac(seed * 7.13)) * (0.3 + 1.4 * n1), 0.4 * mn);
                            edgeM = RoundedInset(float2(endD, latD), rcn) - 0.006 * n3;
                            // staggered end: subtract the box {distance to that end < st, on one lateral half}
                            float st = step(frac(seed * 5.7), 0.40) * (0.10 + 0.30 * frac(seed * 8.1));
                            float dEnd = (frac(seed * 4.3) < 0.5 ? i.uv.x : 1.0 - i.uv.x) * sizeM.x;
                            float sideY = (frac(seed * 2.9) < 0.5 ? vY : -vY) - 0.15 * (frac(seed * 3.3) - 0.5) * sizeM.y;
                            edgeM = st > 0.0 ? min(edgeM, max(dEnd - st, -sideY)) : edgeM;
                            fth = 0.022;
                            hasSeal = 1.0;
                            sw = baseSw;
                            sealMask = (half)(smoothstep(0.78, 0.58, n1) * step(min(endD, dEnd - st), latD + sw));
                        }
                        else if (kindF < 2.5)
                        {
                            // TRENCH backfill (wykop pod instalacje): half saw-cut (corner 2-6 cm), half dug with a bucket
                            // (12-40 cm); sides wander 5-15 cm over 0.5-2 m (the cut follows the trench, not a ruler), spalled
                            // bites along the cut; 45 % L-shaped (a corner box of 25-45 % x 30-55 % never dug: the trench turns or
                            // a second, shorter cut), a continuous hand-poured overband, worn in stretches. WORKING_VALUE.
                            float rc = min(frac(seed * 3.3) < 0.5 ? 0.02 + 0.04 * frac(seed * 7.13) : 0.12 + 0.28 * frac(seed * 7.13), 0.45 * mn);
                            float2 bW = borderM - bite;
                            edgeM = RoundedInset(bW, rc);
                            edgeM -= 0.012 * (n2 - 0.5) + 0.006 * n3;
                            half notch = (half)step(frac(seed * 9.7), 0.45) * (half)step(1.4, mn);
                            float dE = (frac(seed * 4.3) < 0.5 ? i.uv.x : 1.0 - i.uv.x) * sizeM.x;
                            float dS = (frac(seed * 2.9) < 0.5 ? i.uv.y : 1.0 - i.uv.y) * sizeM.y;
                            float nx = (0.25 + 0.20 * frac(seed * 12.1)) * sizeM.x, ny = (0.30 + 0.25 * frac(seed * 14.9)) * sizeM.y;
                            edgeM = notch > 0.5 ? min(edgeM, max(dE - nx, dS - ny) - 0.02 * (n2 - 0.5)) : edgeM;
                            fth = 0.012;
                            hasSeal = 1.0;
                            sw = baseSw;
                            sealMask = (half)smoothstep(0.80, 0.60, n1);
                        }
                        else if (kindF < 3.5)
                        {
                            // HOT-MIX pothole (lata "na goraco"): an irregular oval, lobed by two octaves of noise, soft
                            // smeared rim (4-9 cm), no overband. Distance field of an ellipse in the UV square.
                            float2 q = i.uv.xy * 2.0 - 1.0;
                            float r = length(q) * (1.0 + 0.55 * n1 + 0.45 * n2 + 0.08 * n3);
                            edgeM = min((1.2 - r) * 0.42 * mn, min(borderM.x, borderM.y));
                            edgeM -= 0.035 * (n3 - 0.3) + 0.02 * (n2 - 0.5) + 0.6 * bite;            // chipped, uneven rim
                            fth = 0.015 + 0.02 * frac(seed * 9.1);
                            hasSeal = 0.0;
                            sw = 0.0;
                            sealMask = 0.0;
                        }
                        else
                        {
                            // RUT fill (laty na koleinach): a strip along the wheel path whose width wanders 60-115 %,
                            // pointed / ragged ends over the first 12 % of the length, soft sides with 3-6 cm noise.
                            float t = 1.0 - abs(i.uv.x * 2.0 - 1.0);               // 0 at the ends, 1 in the middle
                            float taper = smoothstep(0.0, 0.14, t);
                            float wv = 0.6 + 0.55 * ValueNoise12(objectXZ / 3.2 + seed * 31.0);
                            float latD = (0.5 - abs(i.uv.y - 0.5)) * sizeM.y - 0.5 * sizeM.y * (1.0 - wv * lerp(0.15, 1.0, taper));
                            float endD = borderM.x - 0.25 * ValueNoise12(objectXZ / 0.5 + seed * 7.0) - 0.02;
                            edgeM = min(latD - 0.045 * (n2 * 0.7 + n1 * 0.5) - bite, endD);
                            fth = 0.035;
                            hasSeal = step(frac(seed * 11.7), 0.3);
                            sw = baseSw * hasSeal;
                            sealMask = hasSeal * (half)smoothstep(0.88, 0.72, n1);
                        }
                        // road-patches-s24: the overband straddles the cut (half on the patch, half on the old road), so the
                        // outline moves in by half its width (+4 mm) to keep the outer half inside the quad, and the seal is
                        // composited with its own opacity - before, it lay on the 0..fth alpha ramp of the patch edge and
                        // faded out with distance exactly where it should read as the dark joint line.
                        float sHalf = 0.5 * sw;
                        edgeM -= (sHalf + 0.004) * step(0.001, sw);
                        aa = max(fwidth(edgeM), 0.002);
                        half alphaPatch = (half)smoothstep(0.0, fth + aa, edgeM);
                        // box-filtered band |edgeM| < sHalf; sub-pixel bands keep (roughly) their area instead of vanishing
                        half seam = (half)(saturate((sHalf + 0.5 * aa - abs(edgeM)) / aa) * saturate(3.0 * sHalf / aa))
                                  * (half)step(0.001, sw) * sealMask;
                        half3 roadTone = KamionRoadTone(objectXZ);
                        if (roadRepair)
                        {
                            // The clean scan is calibrated at 0.062 linear; worn asphalt
                            // starts at 0.08 * 0.90 before traffic wear. Use the whole local
                            // road tone at every age. Some young batches have light aggregate.
                            half batch = (half)lerp(0.93, 1.02, frac(seed * 13.3));
                            half young = 1.0h - (half)smoothstep(0.15, 0.5, age);
                            half pale = (half)step(0.55, frac(seed * 19.13)) * young;
                            half grain = (half)((ValueNoise12(gp / 0.035) - 0.5) * 0.18 * saturate(0.05 / fpx)
                                               + (ValueNoise12(gp / 0.13 + 7.0) - 0.5) * 0.09);
                            albedo *= roadTone * (0.072h / 0.062h) * (batch + 0.11h * pale)
                                    * (1.0h + grain * lerp(0.5h, 1.0h, age) + 0.035h * (n1 - 0.5h));
                            smooth = min(smooth, lerp(0.12h, 0.10h, age));
                            tn = normalize(lerp(tn, half3(0, 0, 1), 0.28h * young));

                            // Even a saw-cut trench has intact stretches between spots
                            // of sealant. Keep the centre opaque where repairs cover paint.
                            seam *= (half)smoothstep(0.48, 0.73, ValueNoise12(on / 0.46 + 53.0));
                            alpha = max(alphaPatch * ((kindF == 2.0 || kindF == 3.0) ? 1.0h : 0.84h), seam * 0.58h);
                            albedo *= 1.0h - seam * _PatchSeam.y * lerp(0.55h, 0.30h, age);
                            smooth = lerp(smooth, 0.13h, seam);
                        }
                        else
                        {
                            alpha = max(alphaPatch, seam * 0.94h);
                            half tone = (half)((0.88 + 0.26 * frac(seed * 13.3)) * (0.93 + 0.14 * n1));
                            albedo *= lerp(_PatchSeam.z, _PatchSeam.w * 0.82, age) * tone;
                            albedo *= lerp(half3(1, 1, 1), roadTone, (half)lerp(0.6, 1.0, saturate(age * 2.0)));
                            albedo *= lerp(half3(1.06, 1.0, 0.93), half3(1, 1, 1), (half)saturate(age * 1.6));
                            albedo *= (half)lerp(0.8, 1.0, saturate(age * 3.0));
                            albedo *= 1.0 - seam * _PatchSeam.y * lerp(1.0, 0.55, age);
                            smooth = min(smooth, (half)lerp(0.17, 0.11, age));
                            smooth = lerp(smooth, lerp(0.22, 0.14, age), seam);
                        }
                        tn = normalize(lerp(tn, half3(0, 0, 1), seam * 0.8h));
                    }
                }
            #endif
            #if defined(_DECAL_ALPHA)
                {
                    // 2x2 atlas, one stain per cell, centre 0.5/0.5 of the radial UV; cell from TEXCOORD_1.y.
                    // ADR 0131: _DecalCells 1 = the whole UV (Fab manhole / drain covers, their own atlas rects).
                    float cells = max(_DecalCells, 1.0);
                    float cell = floor(saturate(i.uv.w) * (cells * cells - 0.001));
                    float2 cxy = float2(fmod(cell, cells), floor(cell / cells));
                    float2 ua = (saturate(i.uv.xy) + cxy) / cells;
                    half4 st = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, ua);
                    half4 sm = SAMPLE_TEXTURE2D(_MaskMap, sampler_MaskMap, ua);
                    albedo = st.rgb * _Tint.rgb * _AlbedoScale;
                    smooth = sm.a * _SmoothnessScale;
                    ao = 1.0;
                    tn = half3(0, 0, 1);
                    half oilStrength = i.uv.z > 0.0 ? i.uv.z : 1.0; // legacy/yard/bus data = 0
                    alpha = saturate(st.a * _DecalAlpha * oilStrength);
                    KamionOilStain(_OilLook, sm.a, smooth, alpha);   // ADR 0194: absorbed oil stays matt and dark
                }
            #endif
            #if defined(_DECAL_TYRE)
                {
                    // rubber scrub along a wheel track: soft across the strip (TEXCOORD_0.y 0..1), faded at both ends
                    // (TEXCOORD_0.x metres, TEXCOORD_1.x length), broken up by the macro mottling
                    half across = 1.0 - abs(i.uv.y * 2.0 - 1.0);
                    half prof = smoothstep(0.0, 0.55, across);
                    // ADR0099: negative physical length reserves a short gate approach;
                    // WORKING_VALUE .65/.90m fades. Nonnegative legacy data stays exact.
                    half ends;
                    if (i.uv.z < 0.0)
                        ends = saturate(i.uv.x / 0.65) * saturate((abs(i.uv.z) - i.uv.x) / 0.90);
                    else
                        ends = saturate(i.uv.x / 2.5) * saturate((i.uv.z - i.uv.x) / 4.0);
                    half brk = saturate(0.55 + (macro.a - 0.5) * 2.5 + (macro.g - 0.5));
                    // ADR 0092: strength >= 2.5 = a solid band (tyre rub on a kerb nose must not vanish where the macro
                    // mottling happens to be low); driving lines and soil bands (<= 1.5) keep the break-up
                    brk = max(brk, saturate(i.uv.w - 1.5));
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
                    float ex = i.uv.w - 4.0 * paintFresh - 8.0 * paintRenewed; // [0,1) longitudinal, [2,3) transverse; frac = age
                    half transverse = step(1.5, ex);
                    half age = (half)frac(ex);
                    half known = step(-0.5, i.uv.z);                     // (-1, 5) = no wear data
                    float lc = frac(i.uv.z);
                    // ADR0099 WORKING_VALUE: ~0.60m contact band at lane3.5m; asphalt polish stays wider.
                    half wp = saturate(1.0 - abs(abs(lc - 0.5) - 0.24) / 0.085) * known;
                    half peaks = SAMPLE_TEXTURE2D(_VarMap, sampler_BaseMap, uvb).r;     // aggregate tops wear first
                    half mott = (macro.a - 0.5) * 2.0;
                    // ADR 0323 (critic wave 6 pkt 2.2 "wytarte linie"): a longitudinal line is not worn evenly - where
                    // traffic crosses or rides it (curves, overtaking, field accesses) 3-12 m of it are chipped on the aggregate peaks - speckled, not erased (1.3 erased the line: it read as a dashed edge line; 0.8 still erased 5-10 m; 0.6). Chipped towards
                    // the asphalt. No crossing data per line: stretches from object-space value noise. WORKING_VALUE.
                    float2 pp = TransformWorldToObject(pw).xz;
                    half stretch = (half)smoothstep(0.52, 0.76, ValueNoise12(pp / 6.5) * 0.75 + ValueNoise12(pp / 1.7 + 3.0) * 0.25);
                    half worn = _PaintWear.x * wp * transverse * (0.55 + 0.9 * age) * lerp(1.0, _PaintFreshWear.x, paintFresh)
                              + _PaintWear.y * (0.35 + age) * (0.6 + 0.4 * wp) * lerp(1.0, _PaintFreshWear.y, paintFresh)
                              + _PaintWear.y * 0.6 * (0.5 + age) * stretch * (1.0 - transverse) * (1.0 - paintFresh)
                              + 0.10 * mott;
                    // ADR 0335 P2: markings repainted over a milled-and-overlaid patch are crisp, cleaner and visibly
                    // brighter than surrounding weathered paint (low wear, low traffic film, fresh white albedo). WORKING_VALUE.
                    worn *= lerp(1.0h, 0.12h, paintRenewed);
                    // chipped, not faded: a narrow threshold on the peak-weighted wear gives sharp-edged bare spots
                    half cover = 1.0 - smoothstep(0.42, 0.58, saturate(worn) * (0.35 + 1.3 * peaks));
                    // traffic film: tyre soot and road dust, grey-brown, heavier on old marks and soiled patches
                    half dirt = saturate(_PaintWear.z * (0.75 + 0.5 * age) * (0.85 + 0.3 * macro.b) * (1.0 + 0.4 * wp * transverse));
                    dirt *= lerp(1.0, _PaintFreshWear.z, paintFresh) * lerp(1.0h, 0.15h, paintRenewed);
                    half3 paintCol = _PaintColor.rgb * lerp(1.0h, 1.22h, paintRenewed);
                    half3 film = paintCol * (1.0 - dirt * half3(1.0, 1.0, 1.03));   // neutral grey film (r6 critic: beige read as concrete)
                    half3 asph = albedo;
                    albedo = lerp(asph, film, cover);
                    // pre-filter: a 0.12 m line (0.4 m for transverse marks) under a pixel blends to the asphalt beneath
                    float fp = max(length(fwidth(pw.xz)), 1e-4);
                    half lw = lerp(_PaintWear.w, 0.4, transverse);
                    albedo = lerp(asph, albedo, saturate(lw * 1.5 / fp));
                    smooth = lerp(smooth, _PaintColor.a * (1.0 - 0.3 * dirt) + 0.08h * paintRenewed, cover);
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
                    // ADR0109: additive ground-only dry matter, behind the existing data keyword.
                    albedo = KamionGrassDryMatter(albedo, k, _GroundTint);
                    // ADR 0334: crop / stubble / meadow colour of the field mosaic over the grass; the grass texture
                    // keeps its luminance detail (blades, gaps) around the field colour, 0.0976 = luminance of _GrassFill
                    half fdet = lerp(1.0h, clamp(grassLum / 0.0976h, 0.6h, 1.4h), 0.7h);
                    albedo = lerp(albedo, fieldAlb.rgb * fdet, fieldAlb.a);
                    // Pine-forest floor (bór sosnowy): needle litter in patches with feather moss and bilberry, not a
                    // uniform beige (review r3 W2 / r4 W-H8). Linear albedo: litter 0.045/0.035/0.021, moss + bilberry
                    // 0.034/0.049/0.019 (WORKING_VALUE, judged against the CC0 Tysiąclecia photos); patches from the
                    // 64 m macro map.
                    half mossy = saturate((macro.a - 0.30) * 3.0 + (macro.r - 0.5) + (detl - 0.5) * 0.6);
                    half3 floorAlb = lerp(half3(0.045, 0.035, 0.021), half3(0.034, 0.049, 0.019), mossy);
                    albedo = lerp(albedo, floorAlb * (0.6 + 0.8 * detl), k.g * _GroundTint);
                    albedo = lerp(albedo, half3(0.13, 0.11, 0.085) * (0.6 + 0.8 * detl), k.a * _GroundTint);
                    half grit = KamionGrassGrit(k, macro.a) * _GroundTint;
                    albedo = lerp(albedo, half3(0.19, 0.17, 0.14) * (0.7 + 0.6 * detl), grit);
                }
            #endif

                // ---- ADR 0348: per-wall / per-gable plaster & plinth shade from COLOR_0 (rgb * 2 linear, a = mask).
                // Vertices without COLOR_0 get Color32(255,0,0,0) in WorldMeshBake -> a = 0 -> exact no-op.
            #if defined(_FACADE_TINT)
                albedo *= lerp(half3(1.0h, 1.0h, 1.0h), i.masks.rgb * 2.0h, i.masks.a);
            #endif

                // ---- weathering-s24 (ADR 0238 / 0348 addendum): roof covering weathering from COLOR_0 written by
                // streetscape.roofs.weather_col: r age, g moss x slope aspect, b metres below the ridge / 6, a = 0.5 + 0.5 x
                // building seed (>= 0.5 on; vertices without COLOR_0 bake to a = 0 -> exact no-op). UV0 = metres along the
                // eave / up the slope from the eave. Dirt runs down the fall line (more water toward the eave), a damp
                // dirty band over the gutter, odd tiles (soaked dark / replaced pale / greyed) on the real tile grid of the
                // set (_RoofTile), moss in the laps at the eave and along the ridge, lichen crusts (Medium+). ALU only,
                // no texture fetch. Strengths WORKING_VALUE (refs Data/raw/refs/posesje, tykocin-rynek-commons).
            #if defined(_ROOF_WEATHER)
                if (i.masks.a > 0.25)
                {
                    half age = i.masks.r;
                    half mossK = saturate(i.masks.g * _RoofWeather.x);
                    float vE = max(i.uv.y, 0.0);
                    float vR = i.masks.b * 6.0;
                    float seed = (i.masks.a - 0.5) * 200.0;
                    float2 ru = i.uv.xy;
                    // dirt runs: two octaves across the slope, stretched 10-30x down it
                    half s1 = ValueNoise12(float2((ru.x + seed) * 1.9, vE * 0.10 + seed));
                    half s2 = ValueNoise12(float2((ru.x + seed) * 6.3 + 13.7, vE * 0.30));
                    half streak = saturate((s1 * 0.6 + s2 * 0.4 - 0.42) * 2.6);
                    streak *= smoothstep(0.15, 1.2, vR) * (0.55 + 0.45 * (1.0 - smoothstep(0.5, 5.0, vE)));
                    half ks = streak * _RoofWeather.y * (0.45 + 0.55 * age);
                    // a dirt film converges every covering to grey-brown: darkens red / brown tile, lifts graphite sheet
                    albedo = lerp(albedo * (1.0 - 0.30 * ks), half3(0.085, 0.080, 0.070), 0.35 * ks);
                    smooth *= 1.0 - 0.3 * ks;
                    albedo *= 1.0 - 0.20 * age * _RoofWeather.y * (1.0 - smoothstep(0.05, 0.7, vE));   // damp band over the gutter
                    // odd tiles on the grid of the set (row 0 at the eave, half-offset courses for plain / interlocking tile)
                    if (_RoofTile.w > 0.001)
                    {
                        float row = floor(ru.y / _RoofTile.y);
                        float col = floor((ru.x + 0.5 * _RoofTile.x * _RoofTile.z * frac(row * 0.5) * 2.0) / _RoofTile.x);
                        float2 tid = float2(col, row);
                        half h1 = Hash12(tid + seed * 1.13);
                        half h2 = Hash12(tid * 1.7 + seed + 31.0);
                        // soaked tiles come in loose groups (a 2-3 m cell lifts / drops the share), replaced ones alone
                        half grp = ValueNoise12(tid * float2(_RoofTile.x, _RoofTile.y) * 0.45 + seed * 0.31);
                        half share = (0.03 + 0.10 * age) * (0.4 + 1.2 * grp);
                        half odd = step(1.0 - share, h1);
                        half3 f = h2 < 0.55 ? half3(0.84, 0.82, 0.80) : (h2 < 0.8 ? half3(1.12, 1.08, 1.03) : half3(0.94, 0.97, 0.92));
                        half jit = 1.0 + (h2 - 0.5) * 0.10 * (0.3 + 0.7 * age);
                        half3 tf = lerp(half3(1.0, 1.0, 1.0), f, odd) * jit;
                        half tfade = 1.0 - smoothstep(_RoofTile.x * 0.25, _RoofTile.x * 0.8, footprint);
                        half3 tmean = (1.0 - share * 0.06).xxx;           // mean of tf over many tiles (no tone pop with distance)
                        albedo *= lerp(half3(1.0, 1.0, 1.0), lerp(tmean, tf, tfade), _RoofTile.w);
                    }
                    // neon-outbuildings2-s24 (ADR 0238 d. props-fix r2): down-slope ribs (trapezoidal T-18 / corrugated
                    // sheet), sheet lap joints (~1.05 m), and subtle weathering / rust / fade variation on metal/sheet roofs
                    // (0 extra draws, 0 extra textures, anti-shimmer filtered via fwidth(ru.x)). WORKING_VALUE.
                    if (_RoofWeather.w > 0.5)
                    {
                        half isCorr = (half)step(0.65, frac(seed * 0.371));     // 65 % trapezoidal T-18, 35 % corrugated
                        float pitch = lerp(0.20, 0.14, (float)isCorr);
                        float fwx = max(fwidth(ru.x), 1e-4);
                        half ribFade = (half)saturate(pitch * 0.55 / fwx);
                        float ph = frac((ru.x + seed * 0.13) / pitch);
                        // Trapezoidal profile: trough [0..0.46], rise [0.46..0.58], crest [0.58..0.88], fall [0.88..1.0]
                        half hTrap = (half)(smoothstep(0.45, 0.58, ph) * (1.0 - smoothstep(0.87, 0.99, ph)));
                        half sTrap = (half)(smoothstep(0.44, 0.51, ph) * (1.0 - smoothstep(0.54, 0.60, ph))
                                          - smoothstep(0.86, 0.92, ph) * (1.0 - smoothstep(0.95, 1.0, ph)));
                        // Corrugated profile: sine wave along eave (ribs run down-slope)
                        half hCorr = (half)(0.5 - 0.5 * cos(ph * 6.2831853));
                        half sCorr = (half)(sin(ph * 6.2831853) * 0.72);
                        half ribH = lerp(hTrap, hCorr, isCorr);
                        half ribSlope = lerp(sTrap * 0.85h, sCorr, isCorr);
                        // Replace flat metal-tile course normal with strong down-slope rib normal (anti-aliased at distance)
                        tn = normalize(lerp(half3(0.0h, 0.0h, 1.0h), tn, 0.25h) + half3(-ribSlope * ribFade, 0.0h, 0.0h));
                        // Trough AO + crest catchlight along the slope
                        albedo *= lerp(1.0h, lerp(0.80h, 1.18h, ribH), ribFade);
                        ao *= lerp(1.0h, lerp(0.80h, 1.0h, ribH), ribFade);
                        smooth = lerp(smooth * 0.78h, smooth * 1.12h, ribH * ribFade);
                        // Per-sheet lap seams (~1.05 m wide sheets) + per-sheet tone drift + per-building oxidised grey tint
                        float sheetId = floor((ru.x + seed * 0.19) / 1.05);
                        half shHash = (half)Hash12(float2(sheetId, floor(seed * 3.1) + 7.0));
                        float lapDist = abs(frac((ru.x + seed * 0.19) / 1.05) - 0.5) * 1.05;
                        half lapLine = (1.0h - (half)smoothstep(0.008, 0.025 + fwx, 0.525 - lapDist)) * (half)saturate(0.04 / fwx);
                        half bTone = lerp(0.88h, 1.48h, (half)frac(seed * 0.173) * saturate(age * 1.15h));
                        albedo *= bTone * (1.0h + (shHash - 0.5h) * (0.14h + 0.12h * age)) * (1.0h - 0.24h * lapLine);
                        // Subtle rust / oxidised streaks in rib troughs & along sheet laps on aged outbuildings
                        half rNoise = (half)ValueNoise12(float2((ru.x + seed) * 2.4, vE * 0.28 + seed * 0.7));
                        half rMask = smoothstep(0.56h, 0.84h, rNoise + 0.18h * (1.0h - ribH) + 0.15h * lapLine)
                                   * saturate((age - 0.30h) * 1.4h) * (0.55h + 0.45h * (1.0h - (half)smoothstep(0.6, 4.5, vE)));
                        albedo = lerp(albedo, half3(0.11h, 0.055h, 0.032h) * (0.85h + 0.3h * rNoise), rMask * 0.48h);
                        smooth *= 1.0h - 0.45h * rMask;
                    }
                    // moss: eave zone (wider on older roofs) and along the ridge, a few tufts anywhere; in the laps
                    half zone = max(1.0 - smoothstep(0.25, 1.4 + 0.8 * age, vE), 0.75 * (1.0 - smoothstep(0.1, 0.55, vR)));
                    zone = max(zone, 0.30);
                    half lap = _RoofTile.y > 0.001 ? smoothstep(0.55, 0.95, frac(ru.y / _RoofTile.y)) : 0.0;
                    half n1 = ValueNoise12(ru * 2.1 + seed);
                    half n2 = ValueNoise12(ru * 6.7 + seed * 0.7 + 5.0);
                    half nz = n1 * 0.6 + n2 * 0.4 + 0.18 * lap;
                    half th = 1.02 - 0.70 * mossK * zone;
                    half m = smoothstep(th, th + 0.14, nz) * step(0.001, mossK);
                    albedo = lerp(albedo, half3(0.048, 0.058, 0.030) * (0.75 + 0.5 * n2), m * 0.8);
                    smooth *= 1.0 - 0.6 * m;
                #if defined(_KAMION_WORLD_DETAIL)
                    half lv = ValueNoise12(ru * 23.0 + seed * 1.9);
                    half lth = 1.0 - 0.28 * saturate(mossK * 1.3) * (0.5 + 0.5 * zone);
                    half lic = smoothstep(lth, lth + 0.06, lv) * (1.0 - smoothstep(0.01, 0.03, footprint)) * _RoofWeather.z;
                    albedo = lerp(albedo, half3(0.30, 0.29, 0.22), lic * 0.55);
                #endif
                }
            #endif

                // ---- walls: splash / soil zone above the ground (TEXCOORD_0.y = metres above ground)
            #if defined(_SPLASH)
                {
                    half s = 1.0 - smoothstep(0.0, _SplashHeight, i.uv.y);
                    s *= 0.6 + 0.4 * macro.a;
                    albedo = lerp(albedo, albedo * half3(0.72, 0.70, 0.64), s);
                    smooth *= 1.0 - 0.5 * s;
                    // weathering-s24: ground-contact band (rain splash + soil thrown up by the drops) _SplashBand.x m high
                    // with a ragged top, soil specks denser toward the ground (Medium+) and a damp dark line in the last
                    // 7 cm. i.uv.y = metres above the terrain on plinths (above the reference ground elsewhere).
                    if (_SplashBand.w > 0.5)
                    {
                        float vz = i.uv.y;
                        half en = ValueNoise12(float2(i.uv.x * 3.1, 7.3)) * 0.6 + ValueNoise12(float2(i.uv.x * 11.0, 2.1)) * 0.4;
                        float top = _SplashBand.x * (0.65 + 0.6 * en);
                        half band = (1.0 - smoothstep(top * 0.45, top, vz)) * (0.55 + 0.45 * macro.a);
                        half sp = 0.0;
                    #if defined(_KAMION_WORLD_DETAIL)
                        float2 cs = float2(i.uv.x, vz) * float2(48.0, 52.0);
                        half dens = saturate(1.0 - vz / (top * 1.7));
                        float2 ci = floor(cs);
                        half hp = Hash12(ci), hq = Hash12(ci + 17.3), hr = Hash12(ci + 41.7);
                        float2 dc = frac(cs) - (0.25 + 0.5 * float2(hq, hr));             // speck off the cell centre
                        half rad = 0.10 + 0.22 * hr;                                        // and of its own size
                        sp = step(1.0 - 0.38 * dens * dens, hp) * (1.0 - smoothstep(rad * 0.6, rad, length(dc)));
                        sp *= _SplashBand.z * (1.0 - smoothstep(0.006, 0.02, footprint));
                    #endif
                        half contact = 1.0 - smoothstep(0.0, 0.07, vz);
                        half kb = saturate(band) * _SplashBand.y;
                        albedo = lerp(albedo, albedo * half3(0.50, 0.46, 0.40), kb);
                        albedo *= 1.0 - (0.45 * sp + 0.30 * contact) * _SplashBand.y;
                        smooth *= 1.0 - 0.4 * kb;
                    }
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
                    // ADR 0092: v >= 48 = the face hangs under a window sill (v - 64 = 1 + depth below the sill). A sill
                    // collects dust over its whole length and sheds it at every joint: streaks 1.7x denser and stronger
                    // than under the coping, and a dirt line right under the sill flashing (0.2 m, WORKING_VALUE).
                    half sill = step(48.0, i.uv.w);
                    float depth = i.uv.w - 1.0 - 64.0 * sill;
                    float2 ur = float2(i.uv.z * lerp(1.0, 1.7, sill) / 24.0 + 0.31 * sill, 1.0 - clamp(depth * lerp(0.25, 0.4, sill), 0.0, 0.985));
                    // ADR 0107 (review 0097 P1-f "jedna centralna kropla"): v >= 112 = sill-local data. A sill sheds its
                    // water at its two ENDS (the flashing has end caps: two whiskers) and wets the wall right under its
                    // drip edge over its whole length (a weak wide band). TEXCOORD_1.u = signed metres from the nearer
                    // sill end (left half < 0, right half > 0), v = 128 + 8 * rnd + 1 + depth below the sill / length
                    // scale (rnd 0-7 per window, 1 + depth < 8). The whisker length differs per end (rnd); the band
                    // takes its fine vertical structure from the run-off map. Additive: the older modes are untouched.
                    half sill2 = step(112.0, i.uv.w);
                    float srnd = floor((i.uv.w - 128.0) * 0.125) * sill2;
                    depth -= (64.0 + 8.0 * srnd) * sill2;
                    half sside = step(0.0, i.uv.z);
                    ur = lerp(ur, float2(i.uv.z * 1.7 / 24.0 + srnd * 0.137 + sside * 0.37, 1.0 - clamp(depth * 0.4, 0.0, 0.985)), sill2);
                    half3 ro = SAMPLE_TEXTURE2D(_RunoffMap, sampler_MacroMap, ur).rgb;
                    ro.r = saturate(ro.r * (1.0 + 0.8 * sill) + sill * 0.3 * (1.0 - smoothstep(0.0, 0.2, depth)) * (0.5 + macro.a));
                    half k = _RunoffStrength * saturate(0.8 + (macro.r - 0.5) * 1.4 + (macro.g - 0.5) * 1.0);
                    if (sill2 > 0.5)
                    {
                        // ADR 0114 (review 0107 P1-r7-g: the 0107 mark read as a pale rectangle with thin edges, 2-5
                        // sRGB levels, gone from 20 m). |u| >= 2 = the wall strip just OUTSIDE the sill end, so a whisker
                        // is centred on the sill end (the reveal line) instead of ending on the edge of the column under
                        // the window. Whisker: 9 cm wide under the sill, 4 cm at its tip, soft 3 cm flanks, per-end length
                        // 0.55-1.0 scale lengths; the wet band under the drip edge lives inside the sill only and is gone
                        // 0.25 scale lengths down. Strength floor 0.5: the plaster factor of the parapet layer (x 0.6)
                        // left a sill mark at ~3 levels. WORKING_VALUE, measured from 5 m and 20 m (ADR 0114 table).
                        // ADR 0124 (review 0114 P1-r8-g: "dwie identyczne nóżki o twardej górnej krawędzi, symetryczne";
                        // weakest 10 % of the marks ~5 sRGB levels from 20 m). Per END of the sill (hash of rnd and side):
                        // 28 % of the ends shed nothing, the rest get their own length (0.35-1.0 scale lengths) and
                        // strength (0.6-1.0). Shape of run-off water: a stain 15 cm wide right under the end cap that
                        // narrows to 3.6 cm at its tip, flanks feathered over 5-9 cm and broken by the run-off map,
                        // fading in over the first 3 cm (no hard top line) and wandering sideways on its way down.
                        // One sill in five also drips somewhere along its length (a short streak inside the sill).
                        // Strength floor 0.62. WORKING_VALUE; measured from 5 m and 20 m (ADR 0124 table).
                        float au = abs(i.uv.z);
                        half outside = step(1.5, au);
                        float sde = au - 2.0 * outside;                       // metres from the sill end
                        half h1 = frac(srnd * 0.618 + sside * 0.37 + 0.13);
                        half h2 = frac(srnd * 0.377 + sside * 0.71 + 0.29);
                        half present = step(0.28, h1);
                        half slen = 0.35 + 0.65 * h2;
                        half sstr = 0.6 + 0.4 * frac(h1 * 7.3);
                        float sdw = sde + (macro.a - 0.5) * 0.07 * saturate(depth * 1.5) * (1.0 - 2.0 * outside);
                        float hw = lerp(0.075, 0.018, saturate(depth / slen));
                        half fadeIn = smoothstep(-0.01, 0.03 + 0.05 * h2, depth);
                        half whisk = present * sstr * (1.0 - smoothstep(hw, hw + 0.05 + 0.04 * ro.r, abs(sdw)))
                                   * (1.0 - smoothstep(0.2 * slen, slen, depth)) * fadeIn * (0.72 + 0.28 * ro.r);
                        half band = (1.0 - outside) * (0.3 + 0.5 * ro.r) * (1.0 - smoothstep(0.03, 0.25, depth)) * 0.5;
                        half dripAt = 0.22 + 0.25 * frac(srnd * 0.291 + 0.05);
                        half drip = step(0.8, frac(srnd * 0.459 + 0.21)) * (1.0 - outside) * (1.0 - sside)
                                  * (1.0 - smoothstep(0.012, 0.045, abs(au - dripAt))) * (1.0 - smoothstep(0.12, 0.55, depth)) * 0.7;
                        ro.r = saturate(max(max(whisk, band), drip));
                        ro.g *= whisk * 0.5;
                        k = max(k, 0.62);
                    }
                    albedo = lerp(albedo, albedo * half3(0.22, 0.21, 0.2), ro.r * k);
                    albedo = lerp(albedo, half3(0.075, 0.042, 0.022), ro.g * k * 0.8);
                    smooth *= 1.0 - 0.35 * ro.r * k;
                }
            #endif

                // ---- ADR 0080: wet surface parameter (global _KamionWet; no effect at 0). Standing water in the macro
                // low spots of paved / asphalt sets only (grass, decals with their own film: no puddles).
            #if defined(_GRASS_DETILE) || defined(_DECAL_ALPHA) || defined(_DECAL_TYRE) || defined(_GROUNDMASKS)
                KamionWetSurface(n, 0.0, 0.0, 0.15, albedo, smooth, tn);
            #else
                KamionWetSurface(n, macro.b * 0.6 + macro.a * 0.4, step(0.95, n.y), 1.0, albedo, smooth, tn);
            #endif
            #if defined(_VERTEX_GRIME)
                {
                    // ADR 0123: road film on authored parts of a mesh (COLOR_0.r, 0 where the generator wrote none): bridge
                    // caps behind the barrier read as a clean bright footway (REVIEW s10-0117 P1-3). The grime keeps 40 %
                    // of the set's own mottling, so panel joints fade with it instead of printing through.
                    half vg = i.masks.r;
                    half tone = 0.6 + 0.8 * dot(base.rgb, half3(0.3333, 0.3333, 0.3333));
                    albedo = lerp(albedo, _VertexGrime.rgb * tone, vg);
                    smooth *= 1.0 - _VertexGrime.w * vg;
                    // ADR 0144 (REVIEW s14-0128 P1-2): weeds between the stones where the mesh carries COLOR_0.g (kerb-side
                    // growth on a gravel island nose), broken up by two octaves of value noise (0.35 m / 0.12 m cells) so
                    // the per-vertex weight reads as tufts, not as a soft stain. Off unless the manifest sets vertex_weed.
                    half wg = i.masks.g * _VertexWeed.w;
                    if (wg > 0.01)
                    {
                        float2 q = pw.xz * 2.9;
                        float2 f0 = floor(q), fr = frac(q);
                        fr = fr * fr * (3.0 - 2.0 * fr);
                        #define KH(p) frac(sin(dot(p, float2(12.9898, 78.233))) * 43758.5453)
                        half n1 = lerp(lerp(KH(f0), KH(f0 + float2(1, 0)), fr.x), lerp(KH(f0 + float2(0, 1)), KH(f0 + float2(1, 1)), fr.x), fr.y);
                        q = pw.xz * 8.3 + 17.0; f0 = floor(q); fr = frac(q);
                        half n2 = lerp(lerp(KH(f0), KH(f0 + float2(1, 0)), fr.x), lerp(KH(f0 + float2(0, 1)), KH(f0 + float2(1, 1)), fr.x), fr.y);
                        #undef KH
                        half nz = n1 * 0.65 + n2 * 0.35;
                        half th = 1.05 - 0.85 * wg;
                        half wd = smoothstep(th, th + 0.10, nz);
                        albedo = lerp(albedo, _VertexWeed.rgb * (0.7 + 0.6 * n2), wd);
                        smooth *= 1.0 - 0.5 * wd;
                    }
                }
            #endif
            #if defined(_BRONZE_PATINA)
                {
                    // ADR 0331 ("Brąz i patyna"): COLOR_0 = (R patina cavity/drip, G convex wear, B baked AO, A enabled).
                    // Keep flat cloak planes unified aged bronze (no camo blotches): threshold geometric cavity/wear
                    // masks and use bronze_cast_tint oxide/grain only as subtle micro-breakup (zero extra fetches).
                    half bEn = i.masks.a;
                    half texOxide = saturate(1.0h - mask.b);
                    half grain = saturate(base.r * _AlbedoScale);
                    half grainDev = clamp(grain - 1.0h, -0.5h, 0.5h);
                    // Calm base cast-bronze modulation around _Tint (linear) with subtle warm/cool facet drift
                    half3 baseBronze = _Tint.rgb * (1.0h + 0.28h * grainDev);
                    baseBronze *= lerp(half3(0.95h, 0.98h, 1.01h), half3(1.05h, 1.01h, 0.95h), saturate(1.0h - texOxide));
                    albedo = lerp(albedo, baseBronze, bEn);
                    // Cavity / drip patina (concentrated in hollows, ruff pleats, seam & drips under the ruff)
                    half patMask = smoothstep(0.22h, 0.85h, i.masks.r);
                    half pat = saturate(patMask * (0.82h + 0.36h * texOxide)) * _BronzePatina.w * bEn;
                    // Rubbed warm bronze highlights on convex ridges (nose, brow, beard, crown rims, cloak fold ridges)
                    half rubMask = smoothstep(0.16h, 0.82h, i.masks.g);
                    half rub = saturate(rubMask * (0.85h + 0.30h * (1.0h - texOxide))) * (1.0h - 0.75h * pat) * _BronzeRubbed.w * bEn;
                    albedo = lerp(albedo, _BronzeRubbed.rgb * (1.0h + 0.20h * grainDev), rub);
                    smooth = lerp(smooth, _BronzeParams.y, rub);
                    metal = lerp(metal, _BronzeParams.z, rub);
                    // Matte greenish copper-carbonate/sulphate patina in crevices & drips under the ruff
                    albedo = lerp(albedo, _BronzePatina.rgb * (1.0h + 0.24h * grainDev), pat);
                    smooth = lerp(smooth, _BronzeParams.x, pat);
                    metal = lerp(metal, 0.14h, pat);
                    // Baked geometric AO deepens eye sockets, under-nose/mouth, beard grooves & ruff pleats
                    ao *= lerp(1.0h, lerp(1.0h, i.masks.b, _BronzeParams.w), bEn);
                }
            #endif
                // ---- ADR 0349 (dopisek neon-paving-s24): procedural tactile warning slabs (25x25 cm, 5x5 blister domes)
                // Uniform branch (_Tactile.w) -> zero extra keywords, zero extra texture memory.
                if (_Tactile.w > 0.5)
                {
                    float2 tu = i.uv.xy;
                    float fw = max(length(fwidth(tu)), 1e-4);
                    float2 p45t = TransformWorldToObject(pw).xz;
                    p45t = p45t - 45.0 * floor(p45t / 45.0);
                    // 25 x 25 cm tile grid + subtle per-tile batch variation
                    float2 tileId = floor(tu / _Tactile.x);
                    float2 tileF = frac(tu / _Tactile.x);
                    float2 tileEdge = min(tileF, 1.0 - tileF) * _Tactile.x;
                    half tJoint = (1.0h - (half)smoothstep(0.002, 0.005 + fw, min(tileEdge.x, tileEdge.y))) * (half)saturate(0.025 / fw);
                    half tileVar = (half)((Hash12(tileId + 7.3) - 0.5) * 0.10);
                    // 5 x 5 truncated-cone blister domes per tile (pitch = 50 mm, r = 14 mm)
                    float2 dCell = (frac(tu / _Tactile.y) - 0.5) * _Tactile.y;
                    float dR = length(dCell);
                    float r0 = _Tactile.z;
                    half domeFade = (half)saturate(0.016 / fw);
                    half domeTop = (1.0h - (half)smoothstep(r0 * 0.85, r0 + fw, dR)) * domeFade;
                    half domeRim = (half)(smoothstep(r0 * 0.45, r0 * 0.72, dR) * (1.0 - smoothstep(r0 * 0.85, r0 + fw, dR))) * domeFade;
                    half domeRing = (half)(smoothstep(r0 * 0.88, r0 * 1.05, dR) * (1.0 - smoothstep(r0 * 1.15, r0 * 1.55 + fw, dR))) * domeFade;
                    // Fine weathered concrete grain + mild soiling (no ghost 20x10 brick lines from _BaseMap)
                    half grain = (half)((ValueNoise12(p45t / 0.03) - 0.5) * 0.08 * saturate(0.04 / fw));
                    half mott = (macro.a - 0.5h) * 0.14h + (macro.b - 0.5h) * 0.10h;
                    albedo = _Tint.rgb * (1.0h + tileVar + mott + grain);
                    albedo *= 1.0h - 0.42h * tJoint;
                    albedo *= 1.0h - 0.32h * domeRing;
                    albedo *= 1.0h + 0.12h * domeTop;
                    ao = (1.0h - 0.35h * tJoint) * (1.0h - 0.25h * domeRing);
                    smooth = lerp(0.14h, 0.24h, domeTop) * (1.0h - 0.4h * tJoint);
                    float2 dir = dCell / max(dR, 1e-5);
                    half2 dNorm = (half2)(-dir * (domeRim * _Tactile.w * 0.80));
                    tn = normalize(half3(dNorm, 1.0h));
                }

                albedo = saturate(albedo);
                smooth = saturate(smooth);
                metal = saturate(metal);
                ao = saturate(ao);
                half3 nw = normalize(tn.x * T + tn.y * B + tn.z * n);
            #if defined(_GROUNDMASKS)
                // ADR 0334 r2: furrows and drill rows tilt the ground normal (region-local E / N = world X / Z)
                nw = normalize(nw + half3(fieldSlope.x, 0.0h, fieldSlope.y));
            #endif

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
            #if defined(_CARPAINT)
                // r10b: the pigment between the flakes still scatters (a metallic paint is not a bare metal): half of the
                // base-coat metal comes off the diffuse term, not all of it. With (1 - metal) dark metallics kept 25-45 %
                // of their albedo and went black under an overcast sky (review 0080 P1 #2). WORKING_VALUE.
                diffColor = albedo * (1.0 - 0.5 * metal) * (1.0 - 0.04);
                // The flakes (aluminium, mica) are not as dark as the pigment around them: their reflectance sits
                // _CarFlake.z above the paint colour. Black / navy metallic turns charcoal where the base coat mirrors
                // the sky instead of staying a black hole (door of the black hatch at overcast: sRGB 15 next to
                // asphalt 70 before). WORKING_VALUE.
                specColor = lerp(half3(0.04, 0.04, 0.04), albedo + _CarFlake.z, metal);
            #endif

            #if defined(_PANELTONE)
                // ADR 0092: the clear preset's sun runs almost along the 180 m dock wall; the receiver then self-shadows
                // in sawtooth patches (Medium) / soft clouds (High). Normal-offset receiver bias on this wall only, up
                // to 0.25 m when the sun grazes it (shadows cast on the wall move by less than that).
                float4 shadowCoord = TransformWorldToShadowCoord(pw + n * (0.03 + 0.22 * saturate(1.0 - abs(dot(n, _MainLightPosition.xyz)) * 3.0)));
            #else
                float4 shadowCoord = TransformWorldToShadowCoord(pw);
            #endif
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
                // ADR 0144 (REVIEW s14-0123 P2-5): a soffit is lit by light thrown back from the ground, not by the lower
                // hemisphere of the sky probe (dark green here: the soffit came out near black-green where the photos have
                // light grey concrete). _GroundBounce.rgb = ground albedo x form factor; the light that reaches the ground
                // is taken as the sky irradiance on an up-facing plane (the sun term is left out: WORKING model).
                half dn = saturate(-nw.y) * _GroundBounce.w;
                half3 shAmb = SampleSH(nw);
                if (dn > 0.001) shAmb = lerp(shAmb, SampleSH(half3(0, 1, 0)) * _GroundBounce.rgb, dn);
                half3 ambient = shAmb * diffColor * (ao * giK) * (1.0 - _SkyOcc.x * saturate(-nw.y));
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
                    // r10b: the flake tilt belongs to the sun lobe (sparkle); the sky seen in the base coat is a wide
                    // lobe, a full per-cell tilt of it read as salt-and-pepper grain on silver from 1.5 m
                    half3 Rb = reflect(-V, normalize(lerp(nw, nb, 0.3)));
                    half3 envBase = GlossyEnvironmentReflection(Rb, _CarPaint.w, ao * giK) * baseSpecCol * (metal * (1.0 - coat));
                    half3 envDull = GlossyEnvironmentReflection(R, perceptualRoughness, ao * giK) * (0.04 * (1.0 - clean)) / (r2 + 1.0);
                    env = envCoat + envBase + envDull;
                }
            #endif
                env *= 1.0 - _SkyOcc.y * (1.0 - smoothstep(0.05, 0.45, R.y));
                color += ambient + env;
                color += KamionLampPoolsLit(pw, nw, V, r, r2, diffColor, specColor);   // street-lamp pools (ADR 0062, 0191)

            #if defined(_NIGHTWIN)
                {
                    // ADR 0192: lit windows. Derivatives outside the branch (uniform anyway); atlas / far-row data by mode.
                    float3x3 w2o = (float3x3)GetWorldToObjectMatrix();
                    float3 dRx = mul(w2o, ddx(i.posRel)), dRy = mul(w2o, ddy(i.posRel));
                    float2 dUx = ddx(um), dUy = ddy(um);
                    [branch] if (_KamionWindowsLum.y > 0.5)
                    {
                        bool farRows = _NightWindows > 1.5;
                        float2 tile = _Tile.xy;
                        float2 wrap = floor(um / tile);
                        float2 auv = um / tile - wrap;
                        float4 ts = farRows ? _KamionNightFarId_TexelSize : _KamionNightAtlasId_TexelSize;
                        int2 tx = min((int2)(auv * ts.zw), (int2)ts.zw - 1);
                        half4 id = farRows ? LOAD_TEXTURE2D(_KamionNightFarId, tx) : LOAD_TEXTURE2D(_KamionNightAtlasId, tx);
                        float cls = round(id.a * 255.0 / 32.0);
                        [branch] if (cls > 0.5)
                        {
                            half2 tc = farRows ? SAMPLE_TEXTURE2D(_KamionNightFarT, sampler_KamionNightAtlasT, auv).rg
                                               : SAMPLE_TEXTURE2D(_KamionNightAtlasT, sampler_KamionNightAtlasT, auv).rg;
                            float2 c = (id.rg + wrap) * tile;
                            float3 anchor = KamionNwAnchor(i.posOS, dRx, dRy, um, dUx, dUy, c);
                            color += KamionNightWindow(anchor, cls, tc.r, tc.g, albedo);
                        }
                    }
                }
            #endif
                color = KamionMixFog(color, i.fogFactor);
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
            #pragma shader_feature_local_vertex _SHADOW_NORMAL_BIAS_SCALE
            #pragma multi_compile_instancing
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            #pragma multi_compile_vertex _ _KAMION_WORLD_DETAIL
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
                float3 biasedPosition = ApplyShadowBias(pw, nw, ld);
            #if defined(_SHADOW_NORMAL_BIAS_SCALE)
                // Thin adjacent deck surfaces separated by normal inset left periodic light holes on the island.
                // Preserve URP's depth offset. Other materials compile the original ApplyShadowBias path above.
                float3 depthOnly = pw + ld * _ShadowBias.x;
                biasedPosition = lerp(depthOnly, biasedPosition, _ShadowNormalBiasScale);
            #endif
                float4 cs = TransformWorldToHClip(biasedPosition);
            #if UNITY_REVERSED_Z
                cs.z = min(cs.z, UNITY_NEAR_CLIP_VALUE);
            #else
                cs.z = max(cs.z, UNITY_NEAR_CLIP_VALUE);
            #endif
            #if !defined(_KAMION_WORLD_DETAIL)
                // ADR 0123 (REVIEW s10-0117 P1-1): on the Low tier the shadow map cannot resolve the two beams of a
                // deck barrier 0.2 m apart - their shadow fell on the cap as a checkerboard (r4_deck_bz_eye2). Materials
                // flagged _LowNoShadow (manifest "shadow_low": false) cast nothing there: all vertices collapse.
                if (_LowNoShadow > 0.5) cs = float4(-2.0, -2.0, -2.0, 1.0);
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
