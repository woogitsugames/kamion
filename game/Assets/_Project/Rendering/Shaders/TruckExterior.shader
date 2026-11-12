// TRAKT exterior (track A7): one opaque PBR shader for the Paint / Trim / Metal / Lights atlas slots.
// Contract: art-source/truck/exterior/export/truck_exterior_manifest.json "shader_contract".
// - _CMap: RGB albedo (sRGB), A roughness. _NMap: tangent normal (OpenGL +Y). _MMap: R AO, G dirt mask, B metallic
//   (Paint: B = paint mask). Paint: albedo = C.rgb * _PaintColor where the paint mask is set; TRAKT wordmark from the
//   decal atlas on uv1. Dirt: lerp to _DirtColor by M.g * _Dirt; dust is dielectric and rougher.
// - Lights slot (_KAMION_TRUCK_LAMPS): emission = _TruckLightState[uv2.x] (RGB luminance / _TruckLightNitsScale, written by
//   TruckLights) * _TruckLightNitsScale * uv2.y * _KamionExposure, decoded in float (EnvironmentLighting). Lamps are therefore in the same
//   exposed units as the sun and sky: a DRL is bright, a tail lamp is a dim red by day, both read correctly at dusk.
// - Lighting: URP UniversalFragmentPBR (main light + cascaded shadows, SH ambient x AO, reflection probe / custom
//   environment). Tyre deflection: renderers with rendering layer bit 8 (TruckVisualRig.TyreRenderingLayer, the wheel
//   meshes, origin = wheel centre) or bit 9 (TrailerVisualRig.TyreRenderingLayer, trailer wheels) are flattened in the vertex shader at _KamionTyreFlatRadius below the wheel centre
//   (world down) - the free-radius model tyre (0.538 m) on a 0.51 m physics rolling radius otherwise sinks ~2.8 cm into
//   the road. All passes (colour, shadow, depth) use the same displaced position.
// - Clear coat (Paint slot, review r3 E1): a second, smooth dielectric GGX layer (F0 0.04, _ClearCoatRoughness) over the
//   base paint, as in URP Complex Lit but without its extra variants: base * (1 - Fc) + coat env reflection * Fc (reflection
//   probe / environment, AO as specular occlusion) + coat sun highlight. Mask = paint mask * (1 - dust): dust sits on top
//   of the lacquer. Global _KamionClearCoatOff (QualityProfile.clearCoat false -> 1) is the tier switch. Optional metallic
//   flake (_Flake, off for the fleet white): mip-faded sparkle in the base specular, for dark metallic liveries.
// - Coated paint (ADR 0038, review r4 E1): under the coat the pigmented base is a rough scatterer, not a second glossy
//   plastic: its own specular lobe is widened to _CoatedBaseRoughness (the 0.36 base lobe was the "grey plastic" sheen).
//   The coat normal carries an orange-peel ripple (vehicle-frame position, ~6 mm wavelength, slope _OrangePeel) that fades
//   into the coat roughness once a ripple is below a pixel; the coat reflection gets a horizon occlusion (no sky through
//   the body). Solid fleet white -> no flake (manifest liveries.white).
// - Road grime (ADR 0038, review r4 E4): coverage = _Dirt x (baked M.g + procedural). Procedural part in the vehicle
//   frame published by ContactShadowCaster (globals _KamionGrime*, slot = renderer user value 1..4): height above the
//   wheel-contact plane (wavy top edge at _GrimeHeight), wheel-arch spray rings around each axle (biased rearwards),
//   vertical streak noise, x cavity (1 - AO). Heavier on non-paint slots (chassis, tanks) and on the wheels (radial
//   sidewall dust). Without a frame (slot 0) only the baked mask is used. Tier switch _KamionGrimeDetailOff (1 = height
//   gradient only, no arch loop / streak noise).
// - r6 (ADR 0038 addendum): coat env through KamionVehicleEnv.hlsl (analytic ground below the horizon on Low/Medium),
//   orange-peel lobe added in alpha, fp16-safe coat GGX, curtain soiling model (_CurtainGrime, trailer object frame).
Shader "Kamion/Truck Exterior"
{
    Properties
    {
        _CMap ("Albedo (RGB sRGB) + roughness (A)", 2D) = "white" {}
        _NMap ("Normal (OpenGL +Y)", 2D) = "bump" {}
        _MMap ("Mask (R AO, G dirt, B metallic / paint mask)", 2D) = "white" {}
        _DecalMap ("Decal atlas (uv1, Paint only)", 2D) = "black" {}
        _NormalStrength ("Normal strength", Range(0, 2)) = 1
        [Toggle] _IsPaint ("Paint slot (B = paint mask, decal on uv1)", Float) = 0
        _PaintColor ("Paint colour (linear)", Color) = (0.78, 0.785, 0.78, 1)
        _PaintRoughness ("Paint base roughness (under the clear coat)", Range(0, 1)) = 0.36
        _ClearCoat ("Clear coat amount", Range(0, 1)) = 1
        _ClearCoatRoughness ("Clear coat perceptual roughness", Range(0.02, 0.5)) = 0.08
        _Flake ("Metallic flake (0 = solid paint)", Range(0, 1)) = 0
        _FlakeScale ("Flake cells per atlas UV", Float) = 2500
        _PaintMetallic ("Paint metallic", Range(0, 1)) = 0
        _DecalColor ("Decal colour (linear)", Color) = (0.1, 0.104, 0.11, 1)
        _DecalMetallic ("Decal metallic", Range(0, 1)) = 1
        _DecalRoughness ("Decal roughness", Range(0, 1)) = 0.3
        _DirtColor ("Dirt colour (linear)", Color) = (0.15, 0.135, 0.11, 1)
        _Dirt ("Dirt amount (0 washed, 0.5 fleet, 1 very dirty)", Range(0, 1)) = 0.5
        _DryDustColor ("Dry matte-plastic dust: linear RGB, W strength (working)", Vector) = (0.07, 0.065, 0.055, 1)
        _CoatedBaseRoughness ("Base roughness under a full clear coat", Range(0, 1)) = 0.6
        _OrangePeel ("Orange peel slope (coat normal)", Range(0, 0.05)) = 0.012
        _GrimeHeight ("Road grime height above the wheel contact (m)", Range(0, 2)) = 0.8
        _GrimeChassis ("Grime multiplier on non-paint slots", Range(0, 3)) = 1.3
        _CurtainGrime ("Curtain soiling model: on, bottom y, top y, rear z (object space m; 0 = off)", Vector) = (0, 1.31, 3.88, -12)
        _CurtainAxles ("Curtain soiling: axle z (object space m) x3", Vector) = (-6.39, -7.7, -9.01, 0)
        _CurtainPosts ("Curtain soiling: post pitch, first post from rear, streak strength, overall scale", Vector) = (3.4, 0, 0.22, 0.7)
        [Toggle(_KAMION_TRUCK_LAMPS)] _Lamps ("Lamp emission from uv2 (Lights slot)", Float) = 0
        _DrlHighlightShoulder ("DRL exposed HDR highlight shoulder (0 = off)", Range(0, 2)) = 0.8
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" "UniversalMaterialType" = "Lit" }

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        CBUFFER_START(UnityPerMaterial)
            float4 _CMap_ST;
            float4 _PaintColor, _DecalColor, _DirtColor, _DryDustColor;
            float _NormalStrength, _IsPaint, _PaintRoughness, _PaintMetallic, _DecalMetallic, _DecalRoughness, _Dirt, _Lamps;
            float _ClearCoat, _ClearCoatRoughness, _Flake, _FlakeScale;
            float _DrlHighlightShoulder;
            float _CoatedBaseRoughness, _OrangePeel, _GrimeHeight, _GrimeChassis;
            float4 _CurtainGrime, _CurtainAxles, _CurtainPosts;
        CBUFFER_END
        float _KamionTyreFlatRadius;          // global (TruckVisualRig: tractor physics rolling radius 0.51 m), 0 = off
        float _KamionTrailerTyreFlatRadius;   // global (TrailerVisualRig: trailer physics rolling radius 0.515 m), 0 = off

        // ADR0087 candidate: bit10 is an explicit DOOR_L/R renderer semantic (all3LODs), bit0 stays set.
        // A shallow stamped-panel crown missing from the exactly planar source FBX/normal atlas.
        // 3.6mm/.65m and <1degree slope are qualitative WORKING_VALUE, not measured photo depth.
        // Door-object coordinates follow its hinge, cab suspension and world rebase; no world-position mask.
        float _KamionDoorCrownOff; // diagnostic ablation only; default0, no material/keyword variant
        float3 KamionDoorCrownGradient(float3 pOS, float3 normalOS, float paintMask, uint renderingLayer)
        {
            if (_KamionDoorCrownOff > 0.5 || (renderingLayer & (1u << 10)) == 0u || paintMask < 0.001)
                return float3(0,0,0);
            // Hinges from the source manifest: height1.6m, forward4.8902m; flat exterior skin at localx0.
            float2 uv = (pOS.zy - float2(-1.7402, -0.315)) / float2(1.3, 0.65);
            if (any(uv <= 0.0) || any(uv >= 1.0)) return float3(0,0,0);
            float skin = (1.0 - smoothstep(0.002, 0.008, abs(pOS.x))) * smoothstep(0.90, 0.98, abs(normalOS.x));
            float2 sn = sin(PI * uv), cs = cos(PI * uv);
            // h=A*sin(pi*u)^2*sin(pi*v)^2: both height and derivative are zero at every patch boundary.
            float2 derivative = 0.0036 * (2.0 * PI) * sn * cs * sn.yx * sn.yx / float2(1.3, 0.65);
            return float3(0, derivative.y, derivative.x) * (skin * saturate(paintMask));
        }

        // Loaded-tyre contact patch: clamp the part of the tyre below the contact plane onto it.
        // Rendering layer bit 8 = tractor wheels, bit 9 = trailer wheels (different tyre size, different rolling radius).
        float3 KamionTyreFlatten(float3 positionWS)
        {
            uint layer = GetMeshRenderingLayer();
            float r = (layer & (1u << 8)) != 0u ? _KamionTyreFlatRadius : ((layer & (1u << 9)) != 0u ? _KamionTrailerTyreFlatRadius : 0.0);
            if (r > 0.0)
            {
                float floorY = UNITY_MATRIX_M._m13 - r;
                positionWS.y = max(positionWS.y, floorY);
            }
            return positionWS;
        }
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
            #pragma shader_feature_local _KAMION_TRUCK_LAMPS
            #pragma multi_compile_fog
            #define _NORMALMAP 1

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Assets/_Project/Rendering/Shaders/KamionAtmosphere.hlsl"   // ADR 0080 height haze, Low tone toe, wetness
            #include "KamionVehicleEnv.hlsl"
            #include "KamionToeParity.hlsl"

            TEXTURE2D(_CMap); SAMPLER(sampler_CMap);
            TEXTURE2D(_NMap);
            TEXTURE2D(_MMap);
            TEXTURE2D(_DecalMap); SAMPLER(sampler_DecalMap);
            TEXTURE2D(_TruckLightState); SAMPLER(sampler_point_clamp);
            float _KamionExposure;
            float _TruckLightNitsScale; // TruckLights: nits per RGBAHalf encoded unit
            float3 TruckLampRadiance(float3 encoded)
            {
                // Keep both operations in float; expanding to nits in half would overflow before exposure.
                return encoded * (_TruckLightNitsScale * _KamionExposure);
            }
            // ADR 0115: local display calibration for the DRL guide only. Fixed low nits made the guide look unlit in sun,
            // while the D23 hard white clip erased the overcast guide. A luminance shoulder retains hue and the existing
            // emitter mask, before fp16 conversion and MSAA. WORKING_VALUE in exposed scene units, not lamp photometry.
            float3 TruckDrlHighlight(float3 radiance, float shoulder)
            {
                if (shoulder <= 0.0) return radiance;
                float y = max(dot(radiance, float3(0.2126, 0.7152, 0.0722)), 0.0);
                return radiance / (1.0 + y / max(shoulder, 1e-5));
            }
            float _KamionClearCoatOff;
            half4 _CabShadowLift;   // cab-view local shadow lift (CabInteriorLighting; 0 outside the cab view)
            // Grime vehicle frames (ContactShadowCaster): per slot right / up / forward with w = -dot(axis, origin); origin on
            // the wheel-contact plane. Axles: x = forward offset, y = wheel-centre height, z = radius, w = 1 valid.
            float4 _KamionGrimeRight[4], _KamionGrimeUp[4], _KamionGrimeFwd[4];
            float4 _KamionGrimeAxle[16];
            float _KamionGrimeDetailOff;   // tier switch (QualityProfileApplier): 0 = full (unset global), 1 = height only

            float KHash(float2 p) { return frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453); }
            float KNoise(float2 p)
            {
                float2 i = floor(p), f = frac(p);
                f = f * f * (3.0 - 2.0 * f);
                return lerp(lerp(KHash(i), KHash(i + float2(1, 0)), f.x), lerp(KHash(i + float2(0, 1)), KHash(i + float2(1, 1)), f.x), f.y);
            }

            // Procedural road grime 0..~1 in the vehicle frame lp (x right, y height above contact, z forward).
            half KamionGrime(float3 lp, uint slot, half detail)
            {
                float h = lp.y;
                // Wavy top edge: 1D noise along the body (~0.6 m features), +-25 %.
                float edge = _GrimeHeight * (0.75 + 0.5 * KNoise(float2(lp.z * 1.7 + lp.x * 0.9, 3.1)));
                edge = max(edge, 0.05);
                // Solid band up to ~40 % of the edge, fading to the edge, then a light dust film up to twice the edge.
                half g = 1.0 - smoothstep(0.4 * edge, edge, h);
                g += 0.18 * (1.0 - smoothstep(edge, 2.0 * edge, h));
                if (detail > 0.5)
                {
                    half arch = 0;
                    [unroll] for (uint k = 0u; k < 4u; k++)
                    {
                        float4 A = _KamionGrimeAxle[(slot - 1u) * 4u + k];
                        float dz = lp.z - A.x, dy = h - A.y;
                        float d = sqrt(dz * dz + dy * dy);
                        // Ring just outside the tyre (inner arch, mudguard, step), wider and stronger behind the wheel.
                        half behind = saturate(0.5 - dz / max(A.z, 0.1));
                        half ring = saturate(1.0 - abs(d - A.z - 0.1) / (0.25 + 0.3 * behind)) * (0.55 + 0.45 * behind);
                        arch = max(arch, ring * A.w);
                    }
                    g = max(g, arch);
                    // Vertical streaks / splatter (8 cm across, 0.7 m tall), faded to its mean below a pixel.
                    float2 q = float2((lp.z + lp.x) * 12.0, h * 1.4);
                    half fw = saturate(1.5 - 24.0 * max(fwidth(lp.z), fwidth(lp.x)));
                    half n = 0.65 * KNoise(q) + 0.35 * KNoise(q * 2.7 + 5.3);
                    g *= lerp(1.0, 0.55 + 0.9 * n, fw);
                }
                return g;
            }

            // Curtain soiling (review r6 T-N1: the baked mask put a dark blotchy "mould" on the rear third, 1.5-2.5 m up).
            // A PVC curtain gets dirty from where the dirt comes from, at low frequency only (no texel noise on the face):
            // (1) tyre spray band along the curtain bottom, 0.3-0.5 m with an undulating top edge (>= 1.5 m wavelength),
            //     densest ~0.9 m behind each axle and from the bogie to the rear end; (2) the wake film of the rear 1.3 m
            //     (low-pressure zone behind the box), heavier low; (3) runoff streaks down from the roof rail at the posts
            //     behind the curtain, fading over 1.3 m, energy-preserving when narrower than a pixel. Object space = the
            //     trailer frame (origin on the ground below the kingpin, +Z forward). Values WORKING_VALUE.
            half CurtainGrime(float3 os, half detail)
            {
                float hb = os.y - _CurtainGrime.y;
                float H = max(_CurtainGrime.z - _CurtainGrime.y, 0.5);
                float edge = lerp(0.30, 0.50, KNoise(float2(os.z * 0.55, 7.3)));
                half along = 0.45;
                [unroll] for (int k = 0; k < 3; k++)
                {
                    float dz = (os.z - (_CurtainAxles[k] - 0.9)) / 1.3;
                    along = max(along, exp(-dz * dz));
                }
                along = max(along, 0.85 * smoothstep(_CurtainAxles.z - 0.6, _CurtainAxles.z - 1.6, os.z));
                half spray = along * ((1.0 - smoothstep(0.55 * edge, edge, hb)) + 0.15 * (1.0 - smoothstep(edge, 1.6 * edge, hb)));
                float dr = os.z - _CurtainGrime.w;
                half wake = (1.0 - smoothstep(0.0, 1.3, dr)) * (0.18 + 0.22 * (1.0 - saturate(hb / H)));
                half g = max(spray, wake);
                if (detail > 0.5)
                {
                    float pitch = max(_CurtainPosts.x, 0.5);
                    float dzp = abs(frac((dr - _CurtainPosts.y) / pitch + 0.5) - 0.5) * pitch;
                    float width = max(0.08, fwidth(os.z) * 1.5);
                    half streak = saturate(exp(-dzp * dzp / (width * width)) * (0.08 / width));
                    half down = 1.0 - smoothstep(0.0, 1.3, _CurtainGrime.z - os.y);
                    g = max(g, streak * down * _CurtainPosts.z);
                }
                return g * _CurtainPosts.w;
            }

            // GGX specular of one smooth dielectric layer for the main light (D * Vis * F * NdotL), Unity light units.
            half3 CoatDirect(Light L, half3 n, half3 v, half rough, half F0)
            {
                // r6: float, not half. With alpha^2 ~ 4e-5 the half term NoH^2 (a2 - 1) + 1 cancels to ~0 or below at the
                // highlight centre and the peak (~1 / a2) overflows half: inf / NaN = the black blotches on the sun-grazed
                // cab side and curtain top at low sun (already speckled before; a sharper coat made them solid). On phone
                // GPUs half is real fp16, so the fix matters more there. The alpha floor 0.01 is the sun disc (0.53 deg)
                // seen as an area light: a mirror cannot concentrate the sun below its own angular size.
                float3 h = SafeNormalize(float3(L.direction) + float3(v));
                float NoH = saturate(dot(float3(n), h)), NoL = saturate(dot(n, L.direction)), LoH = saturate(dot(float3(L.direction), h));
                float a = max(rough * rough, 0.01), a2 = a * a;
                float d = 1.0 - NoH * NoH * (1.0 - a2);
                float F = F0 + (1.0 - F0) * Pow4(1.0 - LoH) * (1.0 - LoH);
                // Normalised GGX * Kelemen visibility (as URP DirectBRDFSpecular), * PI because Unity lights carry no 1/PI.
                float spec = a2 / (4.0 * d * d * max(0.1, LoH * LoH));
                return L.color * (half)min(spec * F * NoL * L.distanceAttenuation * L.shadowAttenuation, 2048.0);
            }

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                float4 tangentOS : TANGENT;
                float2 uv0 : TEXCOORD0;
                float2 uv1 : TEXCOORD1;
                float2 uv2 : TEXCOORD2;
            };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float4 uv01 : TEXCOORD0;
                float3 positionWS : TEXCOORD1;
                half3 normalWS : TEXCOORD2;
                half4 tangentWS : TEXCOORD3;
                half fogFactor : TEXCOORD4;
                float2 uv2 : TEXCOORD5;
            };

            Varyings vert(Attributes v)
            {
                Varyings o = (Varyings)0;
                float3 pw = KamionTyreFlatten(TransformObjectToWorld(v.positionOS.xyz));
                VertexNormalInputs n = GetVertexNormalInputs(v.normalOS, v.tangentOS);
                float4 pcs = TransformWorldToHClip(pw);
                o.positionCS = pcs;
                o.positionWS = pw;
                o.normalWS = n.normalWS;
                o.tangentWS = half4(n.tangentWS, v.tangentOS.w * GetOddNegativeScale());
                o.uv01 = float4(v.uv0, v.uv1);
                o.uv2 = v.uv2;
                o.fogFactor = KamionFogTau(pw, pcs.w);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                float2 uv = i.uv01.xy;
                half4 c = SAMPLE_TEXTURE2D(_CMap, sampler_CMap, uv);
                half4 m = SAMPLE_TEXTURE2D(_MMap, sampler_CMap, uv);
                half3 nTS = UnpackNormalScale(SAMPLE_TEXTURE2D(_NMap, sampler_CMap, uv), _NormalStrength);

                uint renderingLayer = GetMeshRenderingLayer();
                half isTyre = (renderingLayer & ((1u << 8) | (1u << 9))) != 0u ? 1.0 : 0.0;
                half geometricUp = normalize(i.normalWS).y;
                uint slot = unity_RendererUserValue;
                bool hasFrame = slot >= 1u && slot <= 4u;
                float3 lp = i.positionWS;
                if (hasFrame)
                {
                    float3 pw = i.positionWS;
                    lp = float3(dot(pw, _KamionGrimeRight[slot - 1u].xyz) + _KamionGrimeRight[slot - 1u].w,
                                dot(pw, _KamionGrimeUp[slot - 1u].xyz) + _KamionGrimeUp[slot - 1u].w,
                                dot(pw, _KamionGrimeFwd[slot - 1u].xyz) + _KamionGrimeFwd[slot - 1u].w);
                }
                half3 albedo = c.rgb;
                half rough = c.a;
                half metal = m.b;
                half coat = 0;
                if (_IsPaint > 0.5)
                {
                    half paint = m.b;
                    coat = paint * _ClearCoat * (1.0 - _KamionClearCoatOff);
                    albedo = lerp(albedo, albedo * _PaintColor.rgb, paint);
                    rough = lerp(rough, _PaintRoughness, paint);
                    // Pigmented base under the lacquer: a wide lobe, the gloss belongs to the coat.
                    rough = lerp(rough, max(rough, _CoatedBaseRoughness), coat);
                    metal = _PaintMetallic * paint;
                    half4 d = SAMPLE_TEXTURE2D(_DecalMap, sampler_DecalMap, i.uv01.zw);
                    albedo = lerp(albedo, _DecalColor.rgb, d.a);
                    metal = lerp(metal, _DecalMetallic, d.a);
                    rough = lerp(rough, _DecalRoughness, d.a);
                }
                half grime = m.g;
                if (hasFrame)
                {
                    half proc;
                    if (isTyre > 0.5)
                    {
                        // Sidewall dust: radial (rotation invariant), heaviest at the tread shoulder; rim gets brake dust.
                        float rr = length(i.positionWS - float3(UNITY_MATRIX_M._m03, UNITY_MATRIX_M._m13, UNITY_MATRIX_M._m23));
                        proc = 0.55 + 0.45 * smoothstep(0.25, 0.5, rr);
                    }
                    else
                        proc = KamionGrime(lp, slot, 1.0 - _KamionGrimeDetailOff) * (_IsPaint > 0.5 ? 1.0 : _GrimeChassis);
                    // Gloss trim (baked roughness < ~0.3: piano-black mask, lamp surrounds) sheds the light dust film: the
                    // chassis-weighted film (x _GrimeChassis) turned the gloss-black TRAKT mask matte grey (ADR 0047 r2).
                    // Only above the spray band: in the solid band and the wheel arches (polished tanks, chrome steps,
                    // lamp lenses at bumper height) wet road spray sticks to gloss surfaces too (ADR 0047 r3).
                    if (_IsPaint < 0.5 && isTyre < 0.5)
                    {
                        half shed = lerp(0.25, 1.0, smoothstep(0.18, 0.42, c.a));
                        half spray = 1.0 - smoothstep(0.5 * _GrimeHeight, 1.1 * _GrimeHeight, lp.y);
                        proc *= lerp(shed, 1.0, spray);
                    }
                    // AO still controls cavity retention. The whole recessed tread has low AO;
                    // its raised metal faces must shed independently of that broad cavity shadow.
                    half exposedMetalTop = _IsPaint < 0.5 ? m.b * (1.0 - isTyre) * smoothstep(0.55, 0.9, geometricUp) : 0.0;
                    proc *= lerp(1.4, 0.85, m.r) * lerp(1.0, 0.25, exposedMetalTop);
                    grime = max(grime * 0.8, proc);
                }
                if (_CurtainGrime.x > 0.5)
                    grime = CurtainGrime(TransformWorldToObject(i.positionWS), 1.0 - _KamionGrimeDetailOff);
                else if (isTyre < 0.5)
                {
                    // r8 (ADR 0061): settled dust on surfaces that face up (roof crown, deflector, tank and mudguard
                    // tops): nobody washes a cab roof. Scales with _Dirt; at the fleet 0.5 it takes ~13 % off the white
                    // and ~25 % off the coat there (review r7 N-17: roof pixels at 100 % on High overcast 4.8 -> 1.8 %;
                    // the rest is the D23 white clip at 0.7, LookGrading). WORKING_VALUE.
                    half up = smoothstep(0.35, 0.9, geometricUp);
                    grime = max(grime, 0.18 * up);
                }
                half dirt = saturate(grime * _Dirt * 1.8);
                coat *= 1.0 - saturate(dirt * 1.5);
                half3 soilColor = _DirtColor.rgb;
                if (hasFrame && _IsPaint < 0.5 && _Lamps < 0.5 && isTyre < 0.5)
                {
                    // Dry deposits on the upper matte-plastic mudguard differ from dark wet splash below.
                    // Linear vector data, not another sRGB tint; tyres, paint, lamps and metal remain excluded.
                    half dry = (1.0 - m.b) * smoothstep(0.35, 0.60, c.a) * smoothstep(0.35, 0.9, geometricUp)
                             * smoothstep(_GrimeHeight * 0.75, _GrimeHeight * 1.4, lp.y) * saturate(_DryDustColor.w);
                    soilColor = lerp(soilColor, _DryDustColor.rgb, dry);
                }
                albedo = lerp(albedo, soilColor, dirt);
                rough = lerp(rough, max(rough, 0.88), dirt);
                metal *= 1.0 - dirt;

                half sgn = i.tangentWS.w;
                half3 bit = sgn * cross(i.normalWS, i.tangentWS.xyz);
                half3 nWS = NormalizeNormalPerPixel(TransformTangentToWorld(nTS, half3x3(i.tangentWS.xyz, bit, i.normalWS)));
                if ((renderingLayer & (1u << 10)) != 0u && _IsPaint > 0.5)
                {
                    float3 pOS = TransformWorldToObject(i.positionWS);
                    float3 geometricNormalOS = TransformWorldToObjectDir(i.normalWS);
                    float3 gradientOS = KamionDoorCrownGradient(pOS, geometricNormalOS, m.b, renderingLayer);
                    // The same mapped macro normal drives the pigment BRDF and clearcoat, not a reflection-only gain.
                    nWS = normalize(nWS - TransformObjectToWorldDir(gradientOS, false));
                }


                InputData input = (InputData)0;
                input.positionWS = i.positionWS;
                input.normalWS = nWS;
                input.viewDirectionWS = GetWorldSpaceNormalizeViewDir(i.positionWS);
                input.shadowCoord = TransformWorldToShadowCoord(i.positionWS);
                input.fogCoord = i.fogFactor;
                input.bakedGI = SampleSH(nWS);
                input.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(i.positionCS);
                input.shadowMask = half4(1, 1, 1, 1);

                SurfaceData s = (SurfaceData)0;
                s.albedo = albedo;
                s.metallic = metal;
                s.smoothness = 1.0 - rough;
                s.occlusion = m.r;
                s.alpha = 1;
                s.normalTS = nTS;
            #if defined(_KAMION_TRUCK_LAMPS)
                // 16 x 1 state texture: texel x = light group id (0 = none).
                float u = (i.uv2.x + 0.5) / 16.0;
                float3 encoded = SAMPLE_TEXTURE2D_LOD(_TruckLightState, sampler_point_clamp, float2(u, 0.5), 0).rgb;
                float3 lampRadiance = TruckLampRadiance(encoded);
                // Manifest light group 1 = DRL; all other lamp groups keep their original linear radiance.
                if (abs(i.uv2.x - 1.0) < 0.25)
                    lampRadiance = TruckDrlHighlight(lampRadiance, _DrlHighlightShoulder);
                s.emission = (half3)(lampRadiance * saturate(i.uv2.y));
            #endif
                // Metallic flake: per-cell random normal tilt in the base specular only, faded out where a cell is
                // smaller than a pixel (no sparkle aliasing at distance).
                half3 nBase = nWS;
                if (_Flake > 0.0 && _IsPaint > 0.5)
                {
                    float2 cell = floor(uv * _FlakeScale);
                    float3 hsh = frac(sin(float3(dot(cell, float2(127.1, 311.7)), dot(cell, float2(269.5, 183.3)), dot(cell, float2(419.2, 371.9)))) * 43758.5453);
                    float px = max(length(ddx(uv * _FlakeScale)), length(ddy(uv * _FlakeScale)));
                    half fade = saturate(1.5 - px) * _Flake * m.b;
                    nBase = normalize(nWS + (half3(hsh) - 0.5) * 0.6 * fade);
                    input.normalWS = nBase;
                }
                // Gloss dielectric trim (piano-black mask, grille louvres, PC-ABS lamp shrouds: non-paint, non-metal, baked
                // roughness < ~0.3, ADR 0047 r3). A 4 % mirror of the open sky is what made the black louvres mid-grey: the
                // Low analytic cube and the High capture (no instanced trees / props) put open sky where a parked truck's
                // near-horizon reflections see buildings, trees and ground. Own env term for these pixels: Schlick F,
                // AO, horizon occlusion and a near-horizon obstruction; URP keeps the direct light (sun highlight).
                half glossTrim = (1.0 - _IsPaint) * (1.0 - isTyre) * (1.0 - saturate(metal * 2.0)) * (1.0 - smoothstep(0.22, 0.32, rough));
                if (glossTrim > 0.001) s.occlusion = m.r * (1.0 - glossTrim);
                half4 col = UniversalFragmentPBR(input, s);
                if (glossTrim > 0.001)
                {
                    half3 v = input.viewDirectionWS;
                    half NoV = saturate(dot(nWS, v));
                    half F = 0.04 + 0.96 * Pow4(1.0 - NoV) * (1.0 - NoV);
                    half3 R = reflect(-v, nWS);
                    half hor = saturate(1.0 + 1.2 * dot(R, i.normalWS));
                    // WORKING_VALUE: reflections below ~25 deg elevation keep 30 % (street-level clutter), open sky above.
                    half obst = lerp(0.3, 1.0, smoothstep(-0.05, 0.42, R.y));
                    // r8 (ADR 0061): a reflection that points steeply down (the face-down louvres: R.y ~ -0.7) sees the
                    // road in front of the bumper, not street-level clutter: 0.3 -> 0.5 below ~35 deg (the bumper and
                    // the truck's own shadow keep it under 1). Louvre faces at low sun: 4.3 % on Low, a black field.
                    obst = max(obst, 0.5 * smoothstep(-0.30, -0.60, R.y));
                    half3 env = GlossyEnvironmentReflection(R, i.positionWS, max(rough, 0.05), m.r) * (hor * hor * obst);
                    half3 diff = input.bakedGI * albedo * (1.0 - F) * m.r;
                    col.rgb += (env * F + diff) * glossTrim;
                }
                if (coat > 0.001)
                {
                    half3 v = input.viewDirectionWS;
                    // Orange peel: three crossed ripples (~6 mm) in the vehicle frame; below a pixel they become coat roughness.
                    float3 op = lp * 1050.0;
                    float3 ph = float3(dot(op, float3(0.83, 0.31, 0.46)), dot(op, float3(-0.27, 0.77, 0.58)), dot(op, float3(0.44, -0.52, 0.73)));
                    half fade = saturate(1.2 - max(max(fwidth(ph.x), fwidth(ph.y)), fwidth(ph.z)) * 0.35);
                    half3 tilt = cos(ph.x) * half3(0.83, 0.31, 0.46) + cos(ph.y) * half3(-0.27, 0.77, 0.58) + cos(ph.z) * half3(0.44, -0.52, 0.73);
                    half3 nCoat = normalize(nWS + (tilt - dot(tilt, nWS) * nWS) * (_OrangePeel * fade));
                    // Sub-pixel ripples widen the lobe: three crossed sinusoids of slope s have an RMS slope ~1.22 s, i.e. a
                    // GGX alpha ~1.75 s, added in quadrature to the coat alpha (r6 E1: the old 4 s added to the *perceptual*
                    // roughness squared gave alpha 0.054 = a satin coat that blurred the horizon and ground into one grey).
                    half aCoat = _ClearCoatRoughness * _ClearCoatRoughness, aPeel = 1.75 * _OrangePeel;
                    half coatRough = sqrt(sqrt(aCoat * aCoat + (1.0 - fade) * aPeel * aPeel));
                    half NoV = saturate(dot(nCoat, v));
                    half Fc = (0.04 + 0.96 * Pow4(1.0 - NoV) * (1.0 - NoV)) * coat;
                    half3 R = reflect(-v, nCoat);
                    // Horizon occlusion: reflection directions under the geometric surface see the body, not the sky.
                    half hor = saturate(1.0 + 1.2 * dot(R, i.normalWS));
                    // r6 E1: ground plane below the horizon seen from this height (dark ground band under the belt line,
                    // bright horizon at eye height) on the tiers without the vehicle capture.
                    half3 env = KamionVehicleEnv(R, i.positionWS, coatRough, m.r, hasFrame ? lp.y : 1.5) * (hor * hor);
                    Light L = GetMainLight(input.shadowCoord, i.positionWS, input.shadowMask);
                    half3 direct = CoatDirect(L, nCoat, v, coatRough, 0.04) * coat;
                    col.rgb = col.rgb * (1.0 - Fc) + env * Fc + direct;
                }
                // Cab view (review r4 L1): the A-pillars, door frames and mirror housings seen from the driver's seat get the
                // same local shadow lift as the interior (Kamion/Cab Interior); zero outside the cab view.
                half yl = dot(col.rgb, half3(0.2126, 0.7152, 0.0722));
                half ql = _CabShadowLift.y / (yl + _CabShadowLift.y + 1e-5);
                half gl = 1.0 + _CabShadowLift.x * ql * ql * ql;
                col.rgb = lerp(col.rgb * gl, (yl * gl).xxx, _CabShadowLift.z * (1.0 - 1.0 / gl));   // neutral lift (r5 L2)
                col.rgb = KamionToeParity(col.rgb);   // cab view on the tiers without the D23 LUT (identity elsewhere)
                col.rgb = KamionMixFog(col.rgb, i.fogFactor);
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
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"
            float3 _LightDirection;
            float3 _LightPosition;
            struct A { float4 positionOS : POSITION; float3 normalOS : NORMAL; };
            struct V { float4 positionCS : SV_POSITION; };
            V ShadowVert(A v)
            {
                V o;
                float3 pw = KamionTyreFlatten(TransformObjectToWorld(v.positionOS.xyz));
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
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex DepthVert
            #pragma fragment DepthFrag
            struct A { float4 positionOS : POSITION; };
            struct V { float4 positionCS : SV_POSITION; };
            V DepthVert(A v) { V o; o.positionCS = TransformWorldToHClip(KamionTyreFlatten(TransformObjectToWorld(v.positionOS.xyz))); return o; }
            half4 DepthFrag(V i) : SV_Target { return 0; }
            ENDHLSL
        }
    }
    Fallback Off
}
