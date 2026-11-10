// Kamion/World Wire - power-line conductors (generator layer "wires", ADR 0022, REVIEW r4 W-H2, G3 wires r2).
// The generator writes each conductor as a thin vertical ribbon: TEXCOORD_0 = (side -1/+1, physical half width m),
// COLOR_0 = 3D tangent * 0.5 + 0.5 in the generator frame (E, N, U) -> Unity (r, b, g). The vertex shader rebuilds the
// centre line and re-expands it towards the camera.
// Anti-aliased thin line (G3 visual review: dashes at render scale 1.00, worse at 0.80):
//   - the pixel size comes from _ScaledScreenParams (URP: the camera target after renderScale / the ADR 0046 adaptive
//     scale), not _ScreenParams (the unscaled back buffer) - at scale 0.80 the old 1.2 px floor was really 0.96 px;
//   - the core is at least _MinPixels wide and the ribbon is widened by _AAPixels on each side; the fragment shader
//     box-filters the core against a 1 px pixel from the interpolated cross coordinate in pixels, so the line never
//     depends on which pixel centres (or MSAA samples) the triangle happens to hit: continuous, no crawl in motion;
//   - alpha = physical width / core width (energy conserving: a 24 mm wire 300 m away is a faint continuous line);
//   - fades out with the cull distance of the poles (global _KamionWireFade = (start, end) m, set by WorldInstances
//     from the power-pole prototypes): a conductor never outlives its poles.
Shader "Kamion/World Wire"
{
    Properties
    {
        _BaseColor ("Albedo (linear)", Color) = (0.11, 0.11, 0.105, 1)
        _MinPixels ("Minimum core width (px)", Float) = 1.2
        _AAPixels ("Anti-aliasing fringe per side (px)", Float) = 1.0
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
                float _MinPixels, _AAPixels, _MaxAlpha;
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
                float2 wline : TEXCOORD0;     // x signed distance from the centre (px), y core half width (px)
                half alpha : TEXCOORD3;
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
                // size of one rendered pixel at this distance (perspective: 2 d tan(fov/2) / height of the scaled target)
                float px = 2.0 * dist / (abs(UNITY_MATRIX_P._m11) * max(_ScaledScreenParams.y, 1.0));
                float hwPx = hw / px;                                    // physical half width in pixels
                float corePx = max(hwPx, 0.5 * _MinPixels);              // drawn core half width
                float outPx = corePx + _AAPixels;                        // + filter fringe
                pw += s * side * (outPx * px);
                o.positionCS = TransformWorldToHClip(pw);
                o.wline = float2(side * outPx, corePx);
                half a = saturate(hwPx / corePx) * _MaxAlpha;
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
                // box filter of the core [-c, c] against a 1 px pixel centred at d: overlap length, clamped to [0, 1]
                float d = abs(i.wline.x);
                float c = i.wline.y;
                half cov = saturate(min(d + 0.5, c) - max(d - 0.5, -c));
                half3 col = MixFog(i.light, i.fogFactor);
                return half4(col, i.alpha * cov);
            }
            ENDHLSL
        }
    }
    Fallback Off
}
