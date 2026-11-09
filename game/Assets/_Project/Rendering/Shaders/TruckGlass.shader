// Thin-sheet vehicle glass (track A7): windscreen, door glass, lamp lenses (exterior Glass slot) and the cluster cover glass
// (interior). Premultiplied alpha: the scene behind is attenuated by (1 - alpha) and the Fresnel reflection of the
// environment (reflection probe / EnvironmentLighting cubemap) plus the sun highlight is added. Tint from the vertex
// colour (sRGB, exterior contract: windscreen slightly green, lenses clear) times _Tint. Optional grime (interior
// T_Cab_GlassGrime on uv0) adds diffuse haze that catches the light. Neither casts nor receives shadows.
Shader "Kamion/Truck Glass"
{
    Properties
    {
        _Tint ("Tint (linear, multiplies vertex colour)", Color) = (1, 1, 1, 1)
        _Opacity ("Absorption at normal incidence", Range(0, 1)) = 0.12
        _Smoothness ("Smoothness", Range(0, 1)) = 0.96
        _GrimeMap ("Grime (R, uv0)", 2D) = "black" {}
        _Grime ("Grime amount", Range(0, 1)) = 0
        [Toggle] _UseVertexColor ("Tint from vertex colour", Float) = 1
    }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "RenderPipeline" = "UniversalPipeline" "Queue" = "Transparent" }

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Blend One OneMinusSrcAlpha
            ZWrite Off Cull Back

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float4 _Tint;
                float4 _GrimeMap_ST;
                float _Opacity, _Smoothness, _Grime, _UseVertexColor;
            CBUFFER_END
            TEXTURE2D(_GrimeMap); SAMPLER(sampler_GrimeMap);

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; half4 color : COLOR; float2 uv0 : TEXCOORD0; };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                half3 normalWS : TEXCOORD1;
                half3 tint : TEXCOORD2;
                float2 uv : TEXCOORD3;
                half fogFactor : TEXCOORD4;
            };

            Varyings vert(Attributes v)
            {
                Varyings o = (Varyings)0;
                VertexPositionInputs p = GetVertexPositionInputs(v.positionOS.xyz);
                o.positionCS = p.positionCS;
                o.positionWS = p.positionWS;
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                o.tint = _Tint.rgb * (_UseVertexColor > 0.5 ? SRGBToLinear(v.color.rgb) : half3(1, 1, 1));
                o.uv = v.uv0;
                o.fogFactor = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            half4 frag(Varyings i, bool front : SV_IsFrontFace) : SV_Target
            {
                half3 n = normalize(i.normalWS);
                float3 V = GetWorldSpaceNormalizeViewDir(i.positionWS);
                half NoV = saturate(abs(dot(n, V)));
                half F = 0.04 + 0.96 * Pow4(1.0 - NoV) * (1.0 - NoV);
                half pr = 1.0 - _Smoothness;
                half3 R = reflect(-V, n);
                half3 env = GlossyEnvironmentReflection(R, pr, 1.0);

                Light L = GetMainLight();
                half r = max(pr * pr, 0.002);
                float3 H = SafeNormalize(float3(L.direction) + V);
                half NoH = saturate(dot(n, H));
                half d = NoH * NoH * (r * r - 1.0) + 1.00001;
                half spec = (r * r) / (4.0 * PI * d * d) * saturate(dot(n, L.direction)) * F * 4.0;

                half grime = SAMPLE_TEXTURE2D(_GrimeMap, sampler_GrimeMap, i.uv).r * _Grime;
                half3 amb = SampleSH(n);
                half absorb = saturate(_Opacity + grime * 0.25);
                // Body colour of the glass (what is absorbed and scattered) + grime haze lit by sun and sky.
                half3 body = i.tint * amb * _Opacity * 0.5 + grime * (amb + L.color * saturate(dot(n, L.direction))) * 0.18;
                half3 col = body + env * F + L.color * spec;
                half alpha = saturate(absorb + F);
                col = MixFog(col, i.fogFactor);
                // Premultiplied "over": transmission is grey (1 - alpha); the tint shows in the body term only.
                return half4(col, alpha);
            }
            ENDHLSL
        }
    }
    Fallback Off
}
