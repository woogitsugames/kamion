// Kamion/World Vehicle Contact - contact shadow / ambient occlusion under instanced parked vehicles (cars, vans, tractor
// units, semitrailers; ADR 0050). Same physics as Kamion/Contact Shadow (ADR 0021, the player's truck) but analytic in
// the instance's object space, so one flat quad per prototype LOD (one extra submesh = +1 instanced draw per batch) and
// no per-frame mesh work:
//   occlusion  = 1 - Π (1 - s_i · Fx_i · Fz_i) over 2 body slabs + up to 4 axles of tyre contact blobs, F = 2D view
//                factor of a strip of half size a at height h seen from ground offset x:
//                F(x) = ½ [(a − x)/√((a − x)² + h²) + (a + x)/√((a + x)² + h²)]  (darkest between the wheels and under
//                the sills, ~0.5 at the body edge, < 0.1 about 0.3 m outside a car)
//   sun        = analytic visibility of the main light through the vehicle's lower box (4 heights z0..z1 along the
//                ray to the sun), soft rectangle per sample. Needed where the vehicle does not cast a real shadow:
//                LOD1 / LOD2 never cast (InstanceImporter shadow mask), and on Low LOD0 ends at 12 m.
//   multiplier = [E_sky (1 − occ) + E_sun · min(shadowMap, sunVis)] / [E_sky + E_sun · shadowMap] at this pixel, so
//                where the shadow map already darkens the ground only the sky part is removed (no double darkening),
//                and where it does not the sun part is removed by the analytic test.
// The patch fades to 1 over _Patch.w at its edge (no visible quad outline). Fog fades it like the ground it darkens.
// Queue Geometry+499 as Kamion/Contact Shadow (opaque pass: the main-light shadow keywords are on; in the transparent
// pass Mobile_Renderer has receive shadows off). No ShadowCaster / DepthOnly pass: never casts, never writes depth.
Shader "Kamion/World Vehicle Contact"
{
    Properties
    {
        _Slab0 ("Body slab 0 (centre z, half x, half z, height) m", Vector) = (0, 0.9, 2.0, 0.24)
        _Slab1 ("Body slab 1 (centre z, half x, half z, height) m", Vector) = (0, 0.8, 2.3, 0.38)
        _Strength ("Strength (slab 0, slab 1, tyres, unused)", Vector) = (1, 0.8, 0.85, 0)
        _Tyre ("Tyre contact (centre |x|, half x, half z, height) m", Vector) = (0.75, 0.1, 0.1, 0.04)
        _Axles ("Axle z (unused axles = 1e4)", Vector) = (1.3, -1.3, 10000, 10000)
        _SunBox ("Sun box (centre z, half x, half z, opacity)", Vector) = (0, 0.9, 2.3, 1)
        _SunZ ("Sun box heights (z0, z1, penumbra m, penumbra per m)", Vector) = (0.2, 0.95, 0.04, 0.05)
        _Patch ("Patch (centre z, half x, half z, edge fade m)", Vector) = (0, 1.6, 3.0, 0.3)
    }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry+499" "IgnoreProjector" = "True" }
        Pass
        {
            Name "VehicleContact"
            Tags { "LightMode" = "UniversalForward" }
            Blend DstColor Zero
            ZWrite Off ZTest LEqual Cull Off
            Offset -1, -1

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float4 _Slab0, _Slab1, _Strength, _Tyre, _Axles, _SunBox, _SunZ, _Patch;
            CBUFFER_END

            struct A
            {
                float4 positionOS : POSITION;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };
            struct V
            {
                float4 positionCS : SV_POSITION;
                float2 posOS : TEXCOORD0;          // ground point in the vehicle frame (x right, z forward)
                float3 positionWS : TEXCOORD1;
                float4 sunOS : TEXCOORD2;          // xz: ground offset per metre of height towards the sun, w: sun up
                half fogFactor : TEXCOORD3;
            };

            V vert(A v)
            {
                V o;
                UNITY_SETUP_INSTANCE_ID(v);
                VertexPositionInputs p = GetVertexPositionInputs(v.positionOS.xyz);
                // 8 cm depth bias along the view ray (as Kamion/Contact Shadow): the quad lies on the instance's ground
                // plane, which can be a few cm under the rendered road (camber, terrain LOD).
                float3 toCam = _WorldSpaceCameraPos - p.positionWS;
                float3 biased = p.positionWS + toCam * min(0.08 * rsqrt(max(dot(toCam, toCam), 1e-4)), 0.5);
                o.positionCS = TransformWorldToHClip(biased);
                o.positionWS = p.positionWS;
                o.posOS = v.positionOS.xz;
                // Main light direction in the vehicle frame: transpose of the instance rotation (uniform scale only).
                float3 l = normalize(mul(transpose((float3x3)GetObjectToWorldMatrix()), _MainLightPosition.xyz));
                o.sunOS = float4(l.xz / max(l.y, 0.02), 0, l.y);
                o.fogFactor = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            half Strip(half x, half a, half h)
            {
                half h2 = h * h;
                half l = a - x, r = a + x;
                return 0.5 * (l * rsqrt(l * l + h2) + r * rsqrt(r * r + h2));
            }

            half Slab(float2 p, float4 s)
            {
                return saturate(Strip(p.x, s.y, s.w)) * saturate(Strip(p.y - s.x, s.z, s.w));
            }

            half4 frag(V i) : SV_Target
            {
                float2 p = i.posOS;
                // ---- ambient occlusion (product of the open fractions)
                half open = (1.0 - _Strength.x * Slab(p, _Slab0)) * (1.0 - _Strength.y * Slab(p, _Slab1));
                half ax = abs(p.x);
                half tx = saturate(Strip(ax - _Tyre.x, _Tyre.y, _Tyre.w));
                [unroll] for (int k = 0; k < 4; k++)
                    open *= 1.0 - _Strength.z * tx * saturate(Strip(p.y - _Axles[k], _Tyre.z, _Tyre.w));

                // ---- lighting split at this pixel (horizontal ground)
                half3 sky = SampleSH(half3(0, 1, 0));
                // Shadow map sampled 10 cm above the patch: the instance ground plane can lie a few cm under the rendered
                // ground (camber, terrain LOD), and a sample under the casting ground surface self-shadowed in stripes
                // (acne) that the ratio below turned into dark bands on sunlit ground.
                Light L = GetMainLight(TransformWorldToShadowCoord(i.positionWS + float3(0, 0.10, 0)));
                half3 sun = L.color * saturate(L.direction.y);
                half ys = dot(sky, half3(0.2126, 0.7152, 0.0722)), yd = dot(sun, half3(0.2126, 0.7152, 0.0722));
                half atten = L.shadowAttenuation;

                // Sky seen from under a body is a sliver near the horizon. Under an overcast sky (CIE standard overcast,
                // L ∝ 1 + 2 sin e) that sliver is darker than the mean: cosine-weighted open fraction o of a horizon band
                // carries o (1 + o) / 2 of the sky's light. Weighted by the diffuse share of the light (no direct sun ->
                // full; clear noon, ~0.3 diffuse -> ~0.1).
                half diffuse = ys / max(ys + yd, 1e-4);
                open = lerp(open, open * (1.0 + open) * 0.5, diffuse * diffuse);
                half occ = 1.0 - open;

                // ---- analytic sun visibility through the lower box
                half cover = 0;
                if (i.sunOS.w > 0.02)
                {
                    [unroll] for (int k = 0; k < 4; k++)
                    {
                        float z = lerp(_SunZ.x, _SunZ.y, k / 3.0);
                        float2 q = p + i.sunOS.xy * z;
                        float d = max(abs(q.x) - _SunBox.y, abs(q.y - _SunBox.x) - _SunBox.z);
                        float pen = _SunZ.z + _SunZ.w * z * length(i.sunOS.xy);
                        cover = max(cover, saturate(0.5 - d / pen));
                    }
                }
                half sunVis = 1.0 - cover * _SunBox.w;

                // ---- fade to nothing at the patch edge
                half edge = min(_Patch.y - ax, _Patch.z - abs(p.y - _Patch.x));
                half fade = saturate(edge / _Patch.w);
                fade *= fade * (3.0 - 2.0 * fade);
                occ *= fade;
                sunVis = lerp(1.0, sunVis, fade);

                half m = (ys * (1.0 - occ) + yd * min(atten, sunVis)) / max(ys + yd * atten, 1e-4);
                m = saturate(m);
                #if defined(FOG_EXP) || defined(FOG_EXP2) || defined(FOG_LINEAR)
                    m = lerp(1.0, m, ComputeFogIntensity(i.fogFactor));
                #endif
                return half4(m, m, m, 1);
            }
            ENDHLSL
        }
    }
    Fallback Off
}
