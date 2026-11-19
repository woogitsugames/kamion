// ADR 0297 (owner decision 18.11 "rozjaśnij + poświata", review s24 L2: stop 197/255 next to a housing at 5/255, "a sticker").
// Veiling glare of the camera / eye around the truck's red rear signal lamps: the same optical model as the street-lamp glare
// (ADR 0192, LampGlare.shader) - one additive camera-facing quad per emitter cluster (one mesh, one draw per vehicle part),
// brightness from the illuminance the lamp throws at the camera, so the halo grows with the stop and vanishes when the lamp
// is off, seen from the front or rendered into the vehicle reflection cube.
// Why not URP Bloom: bloom is off by design (docs/06 §2) and the lamp emission is display-limited (ADR 0178 / 0197 hue
// limiter, max channel <= 0.8), so no threshold above 1 can single the lamps out; Low renders without post at all.
// Model (Stiles-Holladay / CIE 146): L_veil(phi) = K E / phi^2, phi in degrees, E = I / d^2 lux at the camera,
// I = L_lamp x A_emitter x cos(theta) (Lambertian lens, L from the 32 x 1 lamp-state texture of TruckLights, in cd/m^2);
// K = _HaloK (WORKING_VALUE 0.15 since ADR 0299, was 0.25 in ADR 0297; the street-lamp value is 0.4). The 1 / phi^2 profile is
// flattened inside the angular radius of the emitter (phi^2 + phi_core^2) and fades to 0 at _HaloMaxDeg. Output capped per
// channel (no clipping white).
Shader "Kamion/Truck Lamp Halo"
{
    Properties
    {
        _HaloK ("Veiling glare coefficient K (display x deg^2 per lux x exposure), WORKING_VALUE", Float) = 0.15
        _HaloMaxDeg ("Halo outer radius (deg)", Float) = 2.0
        _HaloCap ("Max display value of the halo per channel", Float) = 0.5
    }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "Queue" = "Transparent+40" "RenderPipeline" = "UniversalPipeline" "IgnoreProjector" = "True" }
        Pass
        {
            Name "Halo"
            Tags { "LightMode" = "UniversalForward" }
            Blend One One
            ZWrite Off
            ZTest LEqual
            Cull Off

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            TEXTURE2D(_TruckLightState); SAMPLER(sampler_point_clamp);
            #define KAMION_LAMP_TEXELS 32.0   // = LampPhotometry.StateTexels (TruckExterior.shader)
            float _KamionExposure;
            float _TruckLightNitsScale;
            float _KamionSkyCapOff;       // 1 while VehicleReflectionCapture renders: glare lives in the lens, not in the scene
            CBUFFER_START(UnityPerMaterial)
                float _HaloK, _HaloMaxDeg, _HaloCap;
            CBUFFER_END

            // positionOS = emitter cluster centre (all 4 corners), normal = lens axis, uv0 = corner (+-1),
            // uv1 = (light group id, emitter area m^2) - TruckLampHaloBuilder.
            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; float2 uv : TEXCOORD0; float2 data : TEXCOORD1; };
            struct Varyings { float4 positionCS : SV_POSITION; float3 q : TEXCOORD0; float3 k : TEXCOORD1; };

            Varyings vert(Attributes v)
            {
                Varyings o;
                float3 c = TransformObjectToWorld(v.positionOS.xyz);
                float3 n = normalize(TransformObjectToWorldDir(v.normalOS));
                float3 toCam = _WorldSpaceCameraPos - c;
                float d = max(length(toCam), 0.3);
                float3 dir = toCam / d;
                float cosT = dot(n, dir);
                float u = (v.data.x + 0.5) / KAMION_LAMP_TEXELS;
                float3 nits = SAMPLE_TEXTURE2D_LOD(_TruckLightState, sampler_point_clamp, float2(u, 0.5), 0).rgb * _TruckLightNitsScale;
                float area = max(v.data.y, 1e-6);
                // Lux at the camera x exposure x K: display units x deg^2. Float: nits x exposure overflows half.
                float3 k = _HaloK * nits * (area * saturate(cosT)) / (d * d) * _KamionExposure;
                float phiMax = _HaloMaxDeg;
                float phiCore = degrees(sqrt(area / PI) / d);
                float r = d * tan(radians(phiMax));
                float3 right = UNITY_MATRIX_V[0].xyz, up = UNITY_MATRIX_V[1].xyz;
                // Pulled toward the camera so the lamp housing does not cut the halo; nearer objects still hide it.
                float3 p = c + dir * min(0.12, d * 0.3) + (right * v.uv.x + up * v.uv.y) * r;
                o.positionCS = TransformWorldToHClip(p);
                o.q = float3(v.uv, phiCore / phiMax);
                o.k = k;
                // Off, seen from behind the lens or inside the reflection capture: degenerate quad, no fragments.
                if (cosT <= 0.0 || max(k.r, max(k.g, k.b)) <= 1e-7 || _KamionSkyCapOff > 0.5) o.positionCS = float4(0.0, 0.0, -2.0, 1.0);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                float s = length(i.q.xy);                 // 0 centre .. 1 = phi max
                float phi = s * _HaloMaxDeg;
                // The 1 / phi^2 core is flattened over the emitter's own angular radius (no cut-out ring: a dark gap between
                // the lens and the halo read as a target in after1); over the lens the halo only pushes the red channel,
                // which the display limiter already holds below white.
                float pc = max(i.q.z * _HaloMaxDeg, 0.05);
                float fade = saturate(1.0 - s * s);
                fade *= fade;
                float3 l = i.k * fade / (phi * phi + pc * pc);
                return half4(min(l, _HaloCap), 0);
            }
            ENDHLSL
        }
    }
}
