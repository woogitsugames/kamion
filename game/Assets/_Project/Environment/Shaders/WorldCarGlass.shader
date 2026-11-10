// Parked-car glazing of prop LOD0 (ADR 0041 par. 8). Thin dark tinted sheet over the modelled interior:
// premultiplied alpha, so the scene behind is attenuated by (1 - alpha) and the reflection is added on top.
// - Reflection: Schlick F0 0.04 on the environment probe, capped (_ReflectMax) and darkened for rays below the horizon
//   (they would hit the neighbouring cars and the paving, not the sky). URP Lit at smoothness 0.6 mirrored the whole
//   sky dome into every pane and the glass read milky light grey on High.
// - Sun glint (tight Blinn-Phong lobe).
// - Dust film from UV0: the generator writes a mask coordinate per vertex, e = max(|u|, |v|) is 1 at the lower
//   and side edges of a pane (outside the wiper sweep / where spray settles) and falls towards the centre. The film is
//   matt, lit by the sky and the sun, and makes the pane more opaque there. Per-car amount = UV scale.
// v4 (REVIEW r6 W-N8, milky panes on High): transmission 0.35 per face (alpha 0.65) onto the dark modelled interior, so a pane
// seen square-on is the dark cabin plus a 4 % reflection; the horizon darkening starts below the horizon (a pane seen
// at grazing angles mirrors the street and the sky band, not a black floor); the dust film only on the outer 25 % of
// the mask and lit at half strength (it was a bright veil over the upper half of every pane in sunlight).
// Both faces are drawn (Cull Off): seen through a near pane, the far pane's inner face attenuates the street behind
// the car a second time (with back faces culled a parked car was a clear window onto the paving behind it). The
// inner face mirrors the dark cabin, not the sky (env x 0.15, no glint).
// Privacy glass: panes whose UV0 u is offset by 4 (life_cars.PRIVACY_U: rear door / quarter windows and rear screen of
// SUVs, estates and half the hatches) use _PrivacyOpacity.
// v5 (ADR 0041 par. 10): sun glint = mirror image of the sun disk in float (the half-precision pow 900 was the "bright
// textured pattern"), reflection = sky above ~15 deg / street clutter (diffuse ground radiance) below, both faces of the
// sheet R = F (1 + T^2) instead of the free x 1.3; _Horizon is only the fallback when the ground globals are unset.
// Neither casts nor receives shadows. GPU instancing (prop instances).
Shader "Kamion/World Car Glass"
{
    Properties
    {
        _Tint ("Tint (body colour of the sheet)", Color) = (0.1, 0.14, 0.13, 1)
        _Opacity ("Absorption at normal incidence", Range(0, 1)) = 0.84
        _PrivacyOpacity ("Absorption of privacy panes", Range(0, 1)) = 0.80
        _Smoothness ("Smoothness", Range(0, 1)) = 0.95
        _Reflect ("Reflection strength", Range(0, 2)) = 1.0
        _ReflectMax ("Fresnel cap", Range(0, 1)) = 0.55
        _Horizon ("Reflection of rays below the horizon", Range(0, 1)) = 0.30
        _DustColor ("Dust film colour", Color) = (0.36, 0.34, 0.30, 1)
        _Dust ("Dust film amount", Range(0, 1)) = 0.6
    }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "RenderPipeline" = "UniversalPipeline" "Queue" = "Transparent" }

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Blend One OneMinusSrcAlpha
            ZWrite Off Cull Off

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            float4 _KamionGroundEnv;    // rgb: diffuse ground radiance (exposed), EnvironmentLighting
            float4 _KamionHorizonEnv;   // a = 1 when set

            CBUFFER_START(UnityPerMaterial)
                half4 _Tint, _DustColor;
                half _Opacity, _PrivacyOpacity, _Smoothness, _Reflect, _ReflectMax, _Dust, _Horizon;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                float2 uv0 : TEXCOORD0;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                half3 normalWS : TEXCOORD1;
                float2 uv : TEXCOORD2;
                half fogFactor : TEXCOORD3;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings vert(Attributes v)
            {
                Varyings o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.positionWS = TransformObjectToWorld(v.positionOS.xyz);
                o.positionCS = TransformWorldToHClip(o.positionWS);
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                o.uv = v.uv0;
                o.fogFactor = ComputeFogFactor(o.positionCS.z);
                return o;
            }

            half4 frag(Varyings i, FRONT_FACE_TYPE face : FRONT_FACE_SEMANTIC) : SV_Target
            {
                half front = IS_FRONT_VFACE(face, 1.0h, 0.0h);
                half3 n = normalize(i.normalWS) * (front > 0.5h ? 1.0h : -1.0h);
                half3 v = normalize(GetWorldSpaceViewDir(i.positionWS));
                half ndv = saturate(dot(n, v));
                half fres = min(_ReflectMax, 0.04h + 0.96h * pow(1.0h - ndv, 5.0h));

                half3 r = reflect(-v, n);
                // v5 (W-N8): what a parked car's pane mirrors. Below ~15 deg elevation the reflected ray of a pane 0.9-1.4 m
                // above the paving meets the neighbouring cars, the hall walls, trees and the paving itself, not open sky
                // (a car row 3 m away subtends ~8 deg, a 10 m hall 40 m away ~13 deg); that clutter is given the diffuse
                // ground radiance (_KamionGroundEnv, the lit-surface level of the scene, EnvironmentLighting). Above, the
                // sky cube. The old term mirrored the cube's bright horizon haze in every pane (ADR 0041 par. 9: x 0.30
                // only for rays 17 deg below the horizon). World props never see the vehicle capture: High = Low.
                half3 envSky = GlossyEnvironmentReflection(r, 1.0h - _Smoothness, 1.0h);
                half open = smoothstep(0.0h, 0.26h, r.y);    // WORKING_VALUE: open sky from ~15 deg up
                half3 clutter = _KamionHorizonEnv.a > 0.5 ? (half3)_KamionGroundEnv.rgb : envSky * _Horizon;
                half3 env = lerp(clutter, envSky, open) * lerp(0.15h, 1.0h, front);   // inner face: the dark cabin

                float2 muv = i.uv;
                half priv = step(2.0, abs(muv.x));
                muv.x -= sign(muv.x) * 4.0 * priv;
                half op = lerp(_Opacity, _PrivacyOpacity, priv);
                // Both faces of the sheet reflect; the inner one is seen through the body tint twice: R = F (1 + T^2),
                // T = 1 - op (clear 0.35 -> x 1.12, privacy 0.20 -> x 1.04). Replaces the free _Reflect gain (1.3).
                half tb = 1.0h - op;
                half refl = (1.0h + tb * tb) * _Reflect;

                Light sun = GetMainLight();
                // Sun glint = the mirror image of the sun disk, in float. The old pow(n.h, 900) x 12 in half precision
                // turned into a stipple of bright pixels over the whole pane (the "bright textured pattern" of ADR 0041
                // par. 9, tune5); in float it is a ~2 deg halo, and a GGX lobe (alpha 0.01) keeps a 5-10 deg tail that
                // whitened the whole pane whenever the sun stood behind the camera. Clean glass mirrors the 0.53 deg disk
                // only: half-vector within ~0.23 deg (slightly wider than the disk's 0.13 deg so it is never sub-pixel
                // at 10-20 m), radiance far above the white clip (x 600, the disk is ~10^4 x the sky).
                float3 hv = normalize((float3)sun.direction + (float3)v);
                float ndh = saturate(dot((float3)n, hv));
                const float cos0 = 0.99999188;   // cos(0.23 deg)
                half glint = (half)(600.0 * saturate((ndh - cos0) / (1.0 - cos0))) * front;
                half3 sky = SampleSH(n);
                half3 diffuse = (sky + sun.color * saturate(dot(n, sun.direction))) * lerp(0.3h, 1.0h, front);   // inner face: cabin shade

                half alpha = saturate(op + (1.0h - op) * fres);
                // the sheet itself scatters almost nothing (clean glass has no diffuse body): 0.2 of the tint term
                half3 col = _Tint.rgb * diffuse * (alpha * 0.2h) + (env * refl + sun.color * glint) * fres;

                half e = max(abs(muv.x), abs(muv.y));
                half d = smoothstep(0.75h, 1.0h, e) * _Dust;
                col = col * (1.0h - 0.6h * d) + _DustColor.rgb * diffuse * (0.5h * d);
                alpha = alpha + (1.0h - alpha) * d;
                half fog = ComputeFogIntensity(i.fogFactor);
                col = lerp(unity_FogColor.rgb * alpha, col, fog);
                return half4(col, alpha);
            }
            ENDHLSL
        }
    }
    FallBack Off
}
