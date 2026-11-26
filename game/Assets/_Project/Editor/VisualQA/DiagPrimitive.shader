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
            struct A { float4 positionOS : POSITION; float3 normalOS : NORMAL; half4 color : COLOR; };
            struct V { float4 positionCS : SV_POSITION; half4 color : COLOR; float3 nWS : TEXCOORD0; float3 pWS : TEXCOORD1; };
            V vert(A v) { V o; o.pWS = TransformObjectToWorld(v.positionOS.xyz); o.positionCS = TransformWorldToHClip(o.pWS); o.color = v.color; o.nWS = TransformObjectToWorldNormal(v.normalOS); return o; }
            half4 frag(V i, uint pid : SV_PrimitiveID) : SV_Target
            {
                if (_Mode > 3.5) return half4(frac(i.pWS.x), frac(i.pWS.z), frac(i.pWS.y * 4.0), 1);   // world E / N metre and 25 cm height ramps
                if (_Mode > 2.5)
                {
                    // R = abs(vertex normal y), G = abs(geometric normal y), B = 1 where the two pick a different planar projection (0.7)
                    float3 g = normalize(cross(ddy(i.pWS), ddx(i.pWS)));
                    float vy = abs(normalize(i.nWS).y), gy = abs(g.y);
                    return half4(vy, gy, (vy >= 0.7) != (gy >= 0.7) ? 1 : 0, 1);
                }
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
