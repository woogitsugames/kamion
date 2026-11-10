// TRAKT exterior (track A7): one opaque PBR shader for the Paint / Trim / Metal / Lights atlas slots.
// Contract: art-source/truck/exterior/export/truck_exterior_manifest.json "shader_contract".
// - _CMap: RGB albedo (sRGB), A roughness. _NMap: tangent normal (OpenGL +Y). _MMap: R AO, G dirt mask, B metallic
//   (Paint: B = paint mask). Paint: albedo = C.rgb * _PaintColor where the paint mask is set; TRAKT wordmark from the
//   decal atlas on uv1. Dirt: lerp to _DirtColor by M.g * _Dirt; dust is dielectric and rougher.
// - Lights slot (_KAMION_TRUCK_LAMPS): emission = _TruckLightState[uv2.x] (RGB luminance in cd/m^2, written by
//   TruckLights) * uv2.y * _KamionExposure (display value per cd/m^2, EnvironmentLighting). Lamps are therefore in the same
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
        [Toggle(_KAMION_TRUCK_LAMPS)] _Lamps ("Lamp emission from uv2 (Lights slot)", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" "UniversalMaterialType" = "Lit" }

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        CBUFFER_START(UnityPerMaterial)
            float4 _CMap_ST;
            float4 _PaintColor, _DecalColor, _DirtColor;
            float _NormalStrength, _IsPaint, _PaintRoughness, _PaintMetallic, _DecalMetallic, _DecalRoughness, _Dirt, _Lamps;
            float _ClearCoat, _ClearCoatRoughness, _Flake, _FlakeScale;
        CBUFFER_END
        float _KamionTyreFlatRadius;          // global (TruckVisualRig: tractor physics rolling radius 0.51 m), 0 = off
        float _KamionTrailerTyreFlatRadius;   // global (TrailerVisualRig: trailer physics rolling radius 0.515 m), 0 = off

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

            TEXTURE2D(_CMap); SAMPLER(sampler_CMap);
            TEXTURE2D(_NMap);
            TEXTURE2D(_MMap);
            TEXTURE2D(_DecalMap); SAMPLER(sampler_DecalMap);
            TEXTURE2D(_TruckLightState); SAMPLER(sampler_point_clamp);
            float _KamionExposure;
            float _KamionClearCoatOff;
            half4 _CabShadowLift;   // cab-view local shadow lift (CabInteriorLighting; 0 outside the cab view)   // tier switch (QualityProfileApplier): 0 = on (unset global), 1 = off

            // GGX specular of one smooth dielectric layer for the main light (D * Vis * F * NdotL), Unity light units.
            half3 CoatDirect(Light L, half3 n, half3 v, half rough, half F0)
            {
                half3 h = SafeNormalize(L.direction + v);
                half NoH = saturate(dot(n, h)), NoL = saturate(dot(n, L.direction)), LoH = saturate(dot(L.direction, h));
                half a2 = max(rough * rough, 0.0016); a2 *= a2;
                half d = NoH * NoH * (a2 - 1.0) + 1.00001;
                half F = F0 + (1.0 - F0) * Pow4(1.0 - LoH) * (1.0 - LoH);
                // Normalised GGX * Kelemen visibility (as URP DirectBRDFSpecular), * PI because Unity lights carry no 1/PI.
                half spec = a2 / (4.0 * d * d * max(0.1, LoH * LoH));
                return L.color * (spec * F * NoL * L.distanceAttenuation * L.shadowAttenuation);
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
                o.fogFactor = ComputeFogFactor(pcs.z);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                float2 uv = i.uv01.xy;
                half4 c = SAMPLE_TEXTURE2D(_CMap, sampler_CMap, uv);
                half4 m = SAMPLE_TEXTURE2D(_MMap, sampler_CMap, uv);
                half3 nTS = UnpackNormalScale(SAMPLE_TEXTURE2D(_NMap, sampler_CMap, uv), _NormalStrength);

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
                    metal = _PaintMetallic * paint;
                    half4 d = SAMPLE_TEXTURE2D(_DecalMap, sampler_DecalMap, i.uv01.zw);
                    albedo = lerp(albedo, _DecalColor.rgb, d.a);
                    metal = lerp(metal, _DecalMetallic, d.a);
                    rough = lerp(rough, _DecalRoughness, d.a);
                }
                half dirt = saturate(m.g * _Dirt);
                coat *= 1.0 - saturate(dirt * 1.5);
                albedo = lerp(albedo, _DirtColor.rgb, dirt);
                rough = saturate(rough + 0.35 * m.g * _Dirt);
                metal *= 1.0 - dirt;

                half sgn = i.tangentWS.w;
                half3 bit = sgn * cross(i.normalWS, i.tangentWS.xyz);
                half3 nWS = NormalizeNormalPerPixel(TransformTangentToWorld(nTS, half3x3(i.tangentWS.xyz, bit, i.normalWS)));

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
                half3 lum = SAMPLE_TEXTURE2D_LOD(_TruckLightState, sampler_point_clamp, float2(u, 0.5), 0).rgb;
                s.emission = lum * saturate(i.uv2.y) * _KamionExposure;
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
                half4 col = UniversalFragmentPBR(input, s);
                if (coat > 0.001)
                {
                    half3 v = input.viewDirectionWS;
                    // Coat sits on the geometric + macro normal (orange peel is far below the atlas resolution).
                    half NoV = saturate(dot(nWS, v));
                    half Fc = (0.04 + 0.96 * Pow4(1.0 - NoV) * (1.0 - NoV)) * coat;
                    half3 R = reflect(-v, nWS);
                    half3 env = GlossyEnvironmentReflection(R, i.positionWS, _ClearCoatRoughness, m.r);
                    Light L = GetMainLight(input.shadowCoord, i.positionWS, input.shadowMask);
                    half3 direct = CoatDirect(L, nWS, v, _ClearCoatRoughness, 0.04) * coat;
                    col.rgb = col.rgb * (1.0 - Fc) + env * Fc + direct;
                }
                // Cab view (review r4 L1): the A-pillars, door frames and mirror housings seen from the driver's seat get the
                // same local shadow lift as the interior (Kamion/Cab Interior); zero outside the cab view.
                half yl = dot(col.rgb, half3(0.2126, 0.7152, 0.0722));
                half ql = _CabShadowLift.y / (yl + _CabShadowLift.y + 1e-5);
                half gl = 1.0 + _CabShadowLift.x * ql * ql * ql;
                col.rgb = lerp(col.rgb * gl, (yl * gl).xxx, _CabShadowLift.z * (1.0 - 1.0 / gl));   // neutral lift (r5 L2)
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
