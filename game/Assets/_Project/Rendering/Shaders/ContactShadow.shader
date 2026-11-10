// Contact shadow / ambient occlusion under a vehicle (ContactShadowCaster). Multiplicative blend on the ground:
// result = ground * (1 - occlusion * ambientShare), where
//   occlusion   = Fx * Fz * strength, F = 2D view factor of a slab (half-size a, height h) seen from ground offset x:
//                 F(x) = ½ [(a − x)/√((a − x)² + h²) + (a + x)/√((a + x)² + h²)]
//   ambientShare = E_sky / (E_sky + E_sun · NdotL · shadow) at this pixel (main-light shadow map sampled here), so in
//                 direct sun only the sky part is occluded and the real cast shadow does the rest.
// Fog fades the effect with distance like the ground it darkens. No depth write, Cull Off, one draw per vehicle.
Shader "Kamion/Contact Shadow"
{
    Properties { }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry+499" "IgnoreProjector" = "True" }
        Pass
        {
            Name "ContactShadow"
            Tags { "LightMode" = "UniversalForward" }
            Blend DstColor Zero
            ZWrite Off ZTest LEqual Cull Off
            Offset -1, -1

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            struct A { float4 positionOS : POSITION; float4 uv0 : TEXCOORD0; float2 uv1 : TEXCOORD1; };
            struct V
            {
                float4 positionCS : SV_POSITION;
                float4 slab : TEXCOORD0;     // x, z, a, b
                float2 hs : TEXCOORD1;       // h, strength
                float3 positionWS : TEXCOORD2;
                half fogFactor : TEXCOORD3;
            };

            V vert(A v)
            {
                V o;
                VertexPositionInputs p = GetVertexPositionInputs(v.positionOS.xyz);
                o.positionCS = p.positionCS;
                o.positionWS = p.positionWS;
                o.slab = v.uv0;
                o.hs = v.uv1;
                o.fogFactor = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            half Strip(half x, half a, half h)
            {
                half h2 = h * h;
                half l = a - x, r = a + x;
                return 0.5 * (l * rsqrt(l * l + h2) + r * rsqrt(r * r + h2));
            }

            half4 frag(V i) : SV_Target
            {
                half h = max(i.hs.x, 0.02);
                half occ = saturate(Strip(i.slab.x, i.slab.z, h)) * saturate(Strip(i.slab.y, i.slab.w, h)) * i.hs.y;
                // Ambient share of the ground lighting here (horizontal ground).
                half3 sky = SampleSH(half3(0, 1, 0));
                Light L = GetMainLight(TransformWorldToShadowCoord(i.positionWS));
                half3 sun = L.color * saturate(L.direction.y) * L.shadowAttenuation;
                half ys = dot(sky, half3(0.2126, 0.7152, 0.0722)), yd = dot(sun, half3(0.2126, 0.7152, 0.0722));
                half share = ys / max(ys + yd, 1e-4);
                half m = 1.0 - occ * share; m = 1.0 - occ; //DEBUG
                // Fog: the darkened ground is fogged too; fade the multiplier towards 1 with the fog visibility.
                #if defined(FOG_EXP) || defined(FOG_EXP2) || defined(FOG_LINEAR)
                    m = lerp(1.0, m, ComputeFogIntensity(i.fogFactor));
                #endif
                return half4(1, 0, 0, 1); //DEBUG2
            }
            ENDHLSL
        }
    }
    Fallback Off
}
