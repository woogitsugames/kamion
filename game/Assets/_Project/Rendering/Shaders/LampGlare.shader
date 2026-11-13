// ADR 0192 (review s19 0182 P2-8 "oprawy bez glare"): veiling glare around street-lamp lenses at dusk / night.
// Why not URP Bloom: bloom is off by design (docs/06 §2, LookDevAssets: no "HDR look") and the Low tier renders without
// HDR, so a threshold above 1 cannot separate a 2·10^5 cd/m² lens from a white wall there. Glare is an optical effect of
// the camera / eye around a very bright point source, so it is drawn only there: one additive billboard per lamp head
// (one mesh, one draw), constant angular size (it lives in the lens, not in the scene), brightness from the illuminance
// the lamp throws at the camera.
// Model (Stiles-Holladay disability glare, CIE 146): L_veil(phi) = K E / phi^2, phi in degrees, E = I(theta) / d^2 lux at
// the camera; K = 10 for the eye, here 0.4 (a phone camera lens scatters ~25x less than the eye - WORKING_VALUE, judged
// on renders). I(theta) = the full-cutoff luminaire of the pools (constant to 60 deg from the nadir, 4 % beyond 75 deg).
// phi < 0.12 deg is the lens itself (already clipped white); the halo fades to 0 at 3 deg.
Shader "Kamion/Lamp Glare"
{
    Properties { }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "Queue" = "Transparent+50" "RenderPipeline" = "UniversalPipeline" "IgnoreProjector" = "True" }
        Pass
        {
            Name "Glare"
            Tags { "LightMode" = "UniversalForward" }
            Blend One One
            ZWrite Off
            ZTest LEqual
            Cull Off

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            float4 _KamionLampGlare;    // x K x I_down x exposure x on (display units x deg^2 x m^2), y phi max (deg), z phi core (deg)
            float4 _KamionLampGlareColor;   // xyz lamp colour, max channel 1

            struct Attributes { float4 positionOS : POSITION; float2 uv : TEXCOORD0; };
            struct Varyings { float4 positionCS : SV_POSITION; float2 q : TEXCOORD0; half k : TEXCOORD1; };

            Varyings vert(Attributes v)
            {
                Varyings o;
                float3 head = TransformObjectToWorld(v.positionOS.xyz);
                float3 toCam = _WorldSpaceCameraPos - head;
                float d = max(length(toCam), 0.5);
                float3 dir = toCam / d;
                // luminaire intensity toward the camera: full cut-off (nadir = -y), floor 4 % for the lens edge
                float cosT = -dir.y;
                float prof = cosT <= 0.0 ? 0.0 : lerp(0.04, 1.0, saturate((cosT - 0.2588) / (0.5 - 0.2588)));
                float phiMax = _KamionLampGlare.y;
                float r = d * tan(radians(phiMax));
                float3 right = UNITY_MATRIX_V[0].xyz, up = UNITY_MATRIX_V[1].xyz;
                // 0.4 m toward the camera so the lamp housing does not cut the halo; scene objects in front still hide it
                float3 p = head + dir * min(0.4, d * 0.5) + (right * v.uv.x + up * v.uv.y) * r;
                o.positionCS = TransformWorldToHClip(p);
                o.q = v.uv;
                o.k = (half)(_KamionLampGlare.x * prof / (d * d));
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                float s = length(i.q);                      // 0 centre .. 1 = phi max
                float phi = max(s * _KamionLampGlare.y, _KamionLampGlare.z);
                float fade = saturate(1.0 - s * s);
                fade *= fade;
                half l = i.k * fade / (phi * phi);
                return half4(_KamionLampGlareColor.rgb * min(l, 4.0h), 0);
            }
            ENDHLSL
        }
    }
}
