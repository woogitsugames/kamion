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
                half3 env = GlossyEnvironmentReflection(r, 1.0h - _Smoothness, 1.0h);
                env *= lerp(_Horizon, 1.0h, smoothstep(-0.30h, 0.12h, r.y)) * lerp(0.15h, 1.0h, front);

                Light sun = GetMainLight();
                half3 hv = normalize(sun.direction + v);
                half glint = pow(saturate(dot(n, hv)), 900.0h) * 12.0h * front;
                half3 sky = SampleSH(n);
                half3 diffuse = (sky + sun.color * saturate(dot(n, sun.direction))) * lerp(0.3h, 1.0h, front);   // inner face: cabin shade

                float2 muv = i.uv;
                half priv = step(2.0, abs(muv.x));
                muv.x -= sign(muv.x) * 4.0 * priv;
                half op = lerp(_Opacity, _PrivacyOpacity, priv);
                half alpha = saturate(op + (1.0h - op) * fres);
                // the sheet itself scatters almost nothing (clean glass has no diffuse body): 0.2 of the tint term
                half3 col = _Tint.rgb * diffuse * (alpha * 0.2h) + (env * _Reflect + sun.color * glint) * fres;

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
