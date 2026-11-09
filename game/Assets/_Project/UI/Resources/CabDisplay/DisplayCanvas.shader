// Kamion cab displays (cluster, navigation, DIN units): the 2D content drawn into the screen render textures by
// Game.UI.CabDisplays.DisplayCanvas. One pass, no lighting; the result is sampled by Kamion/Cab Display (emission,
// exposure, readability floor), which owns the panel brightness - this shader only produces the sRGB screen image.
//
// Vertex: position in design pixels (y down), colour sRGB (UNorm8), texcoord0 = primitive data:
//   glyph : (u, v, -1, 0)                font atlas alpha
//   box   : (lx, ly, hx, hy), hx,hy >= 0 analytic coverage of a box of half extents (hx, hy), lx/ly = local pixel
//                                        position from the box centre (rotated boxes: lines, needles, ticks)
//   ring  : (lx, ly, rIn, -rOut)         analytic coverage of an annulus (rIn = 0: disc); lx/ly from the centre
// Coverage is 1 px wide (resolution-independent edges in the render texture), raised to _CoverageGamma: the render
// texture is sRGB and blends in linear, so light-on-dark text would look bolder than the PIL reference without it.
Shader "Hidden/Kamion/Display Canvas"
{
    Properties
    {
        _FontTex ("Font atlas (alpha)", 2D) = "white" {}
        _CoverageGamma ("Coverage gamma", Float) = 1.0
        _PixelScale ("Render-texture pixels per design pixel", Float) = 1.0
    }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "Queue" = "Transparent" }
        Pass
        {
            Blend SrcAlpha OneMinusSrcAlpha, One OneMinusSrcAlpha
            ZWrite Off ZTest Always Cull Off
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.0
            #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/Common.hlsl"

            TEXTURE2D(_FontTex); SAMPLER(sampler_FontTex);
            float4x4 _DisplayProj;
            float _CoverageGamma;
            float _PixelScale;

            struct A { float3 pos : POSITION; half4 col : COLOR; float4 uv : TEXCOORD0; };
            struct V { float4 cs : SV_POSITION; half4 col : COLOR; float4 uv : TEXCOORD0; };

            half3 ToLinear(half3 c) { return c <= 0.04045h ? c / 12.92h : pow((c + 0.055h) / 1.055h, 2.4h); }

            V vert(A a)
            {
                V o;
                o.cs = mul(_DisplayProj, float4(a.pos.xy, 0.0, 1.0));
                o.col = half4(ToLinear(a.col.rgb), a.col.a);
                o.uv = a.uv;
                return o;
            }

            half4 frag(V i) : SV_Target
            {
                float cov;
                if (i.uv.z < -0.5)
                {
                    cov = SAMPLE_TEXTURE2D(_FontTex, sampler_FontTex, i.uv.xy).a;
                }
                else if (i.uv.w < 0.0)
                {
                    // Distances are in design pixels; one render-texture pixel = 1 / _PixelScale design pixels.
                    float d = length(i.uv.xy) * _PixelScale;
                    float rOut = -i.uv.w * _PixelScale, rIn = i.uv.z * _PixelScale;
                    cov = saturate(rOut + 0.5 - d) * (rIn > 0.0 ? saturate(d - rIn + 0.5) : 1.0);
                }
                else
                {
                    float2 l = abs(i.uv.xy) * _PixelScale, h = i.uv.zw * _PixelScale;
                    cov = saturate(h.x + 0.5 - l.x) * saturate(h.y + 0.5 - l.y);
                }
                cov = pow(saturate(cov), _CoverageGamma);
                return half4(i.col.rgb, i.col.a * cov);
            }
            ENDHLSL
        }
    }
    Fallback Off
}
