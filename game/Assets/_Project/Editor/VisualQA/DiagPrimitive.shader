// bank-smear-s24: visual-qa diagnostics only (KAMION_QA_DIAG "colorby:prim|vcol|vcolb", VisualQaRunner).
// _Mode 0: flat colour per triangle (hash of SV_PrimitiveID, tinted by _BaseColor = per-renderer key) - slivers and
// overlapping layers show up as long single-colour wedges; 1: COLOR_0.rgb; 2: COLOR_0.b as grey.
// Editor-only folder: never in a player build.
Shader "Hidden/Kamion/DiagPrimitive"
{
    Properties
    {
        _BaseColor ("Key colour", Color) = (1, 1, 1, 1)
        _Mode ("Mode", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" }
        Pass
        {
            Name "DiagPrimitive"
            Tags { "LightMode" = "UniversalForward" }
            Cull Off
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 4.0
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            CBUFFER_START(UnityPerMaterial)
                half4 _BaseColor;
                float _Mode;
            CBUFFER_END
            struct A { float4 positionOS : POSITION; half4 color : COLOR; };
            struct V { float4 positionCS : SV_POSITION; half4 color : COLOR; };
            V vert(A v) { V o; o.positionCS = TransformObjectToHClip(v.positionOS.xyz); o.color = v.color; return o; }
            half4 frag(V i, uint pid : SV_PrimitiveID) : SV_Target
            {
                if (_Mode > 1.5) return half4(i.color.bbb, 1);
                if (_Mode > 0.5) return half4(i.color.rgb, 1);
                uint h = pid * 2654435761u; h ^= h >> 15; h *= 2246822519u; h ^= h >> 13;
                half3 c = half3((h & 255u) / 255.0, ((h >> 8) & 255u) / 255.0, ((h >> 16) & 255u) / 255.0);
                return half4(lerp(c, _BaseColor.rgb, 0.35h), 1);
            }
            ENDHLSL
        }
    }
}
