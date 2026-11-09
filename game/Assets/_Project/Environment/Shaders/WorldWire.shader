// Kamion/World Wire - power-line conductors (generator layer "wires", ADR 0019, REVIEW r4 W-H2).
// The generator writes each conductor as a thin vertical ribbon: TEXCOORD_0 = (side -1/+1, physical half width m),
// COLOR_0 = 3D tangent * 0.5 + 0.5 in the generator frame (E, N, U) -> Unity (r, b, g). The vertex shader rebuilds the
// centre line and re-expands it towards the camera to at least _MinPixels px; alpha = physical width / drawn width, so a
// 24 mm wire 300 m away is a faint continuous 1 px line instead of dotted, broken geometry. The wire fades out with the
// cull distance of the poles (global _KamionWireFade = (start, end) m, set by WorldInstances from the power-pole
// prototypes): a conductor never outlives its poles.
Shader "Kamion/World Wire"
{
    Properties
    {
        _BaseColor ("Albedo (linear)", Color) = (0.11, 0.11, 0.105, 1)
        _MinPixels ("Minimum width (px)", Float) = 1.2
        _MaxAlpha ("Maximum opacity", Range(0, 1)) = 0.95
    }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "RenderPipeline" = "UniversalPipeline" "Queue" = "Transparent-50" }
        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            Cull Off

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float4 _BaseColor;
                float _MinPixels, _MaxAlpha;
            CBUFFER_END
            float4 _KamionWireFade;   // x start, y end (m); y <= 0: no fade

            struct Attributes
            {
                float4 positionOS : POSITION;
                half4 color : COLOR;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                half alpha : TEXCOORD0;
                half3 light : TEXCOORD1;
                half fogFactor : TEXCOORD2;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings vert(Attributes v)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                float side = v.uv.x >= 0.0 ? 1.0 : -1.0;
                float hw = max(v.uv.y, 1e-4);
                float3 pw = TransformObjectToWorld(v.positionOS.xyz);
                pw.y -= side * hw;                                       // centre line (the ribbon was vertical)
                float3 t = normalize(TransformObjectToWorldDir(float3(v.color.r, v.color.b, v.color.g) * 2.0 - 1.0));
                float3 toCam = GetCameraPositionWS() - pw;
                float dist = length(toCam);
                float3 s = cross(t, toCam / max(dist, 1e-4));
                float sl = length(s);
                s = sl > 1e-3 ? s / sl : float3(0, 1, 0);
                // size of one pixel at this distance (perspective: 2 d tan(fov/2) / height)
                float px = 2.0 * dist / (abs(UNITY_MATRIX_P._m11) * _ScreenParams.y);
                float drawn = max(hw, 0.5 * _MinPixels * px);
                pw += s * side * drawn;
                o.positionCS = TransformWorldToHClip(pw);
                half a = saturate(hw / drawn) * _MaxAlpha;
                if (_KamionWireFade.y > 0.0) a *= 1.0 - smoothstep(_KamionWireFade.x, _KamionWireFade.y, dist);
                o.alpha = a;
                // simple lighting of a thin cylinder: sky from above + half the sun
                Light L = GetMainLight();
                half3 amb = SampleSH(half3(0, 1, 0)) * 0.8 + SampleSH(half3(0, -1, 0)) * 0.2;
                o.light = _BaseColor.rgb * (amb + L.color * 0.5 * saturate(L.direction.y + 0.2));
                o.fogFactor = ComputeFogFactor(o.positionCS.z);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                half3 c = MixFog(i.light, i.fogFactor);
                return half4(c, i.alpha);
            }
            ENDHLSL
        }
    }
    Fallback Off
}
