// Analytic daylight sky (Preetham 1999 clear + CIE overcast), parameters computed on the CPU by Game.Rendering.SkyModel.
// Output is in exposed display units (same exposure as the sun light, ambient SH and fog), so the horizon matches the fog.
// Below the horizon the dome fades to the fog colour (aerial perspective of distant ground): no hard horizon seam.
// Interleaved-gradient-noise dither of ±0.5 LSB hides 8-bit banding on LDR tiers (no post-processing dither there).
Shader "Kamion/Sky"
{
    Properties
    {
        _SunDiscScale ("Sun disc radius multiplier", Range(1, 4)) = 1.6
    }
    SubShader
    {
        Tags { "Queue" = "Background" "RenderType" = "Background" "PreviewType" = "Skybox" "RenderPipeline" = "UniversalPipeline" }
        Cull Off ZWrite Off

        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.0
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/Color.hlsl"

            float4 _SkyPerezY;      // A..D for Y
            float4 _SkyPerezX;      // A..D for x
            float4 _SkyPerezYc;     // A..D for y
            float4 _SkyPerezE;      // E for Y, x, y
            float4 _SkyZenith;      // x0/F0, y0/F0, clearScale*k/F0(Y), overcastZenith*k
            float4 _SkyMisc;        // overcast, sun disc radiance (exposed)
            float4 _SkySunDir;      // xyz towards the sun
            float4 _SkySunColor;    // linear, luminance 1
            float4 _SkyFogColor;    // exposed horizon colour
            float _SunDiscScale;

            struct Attributes { float4 positionOS : POSITION; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings { float4 positionCS : SV_POSITION; float3 dir : TEXCOORD0; UNITY_VERTEX_OUTPUT_STEREO };

            Varyings vert(Attributes v)
            {
                Varyings o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.dir = v.positionOS.xyz;
                return o;
            }

            float Perez(float4 p, float e, float cosTheta, float gamma, float cosGamma)
            {
                return (1.0 + p.x * exp(p.y / max(cosTheta, 0.01))) * (1.0 + p.z * exp(p.w * gamma) + e * cosGamma * cosGamma);
            }

            float3 XyYToRec709(float x, float y, float Y)
            {
                y = max(y, 1e-4);
                float X = x / y * Y, Z = (1.0 - x - y) / y * Y;
                return max(0.0, float3(
                    3.2404542 * X - 1.5371385 * Y - 0.4985314 * Z,
                   -0.9692660 * X + 1.8760108 * Y + 0.0415560 * Z,
                    0.0556434 * X - 0.2040259 * Y + 1.0572252 * Z));
            }

            float3 SkyRadiance(float3 d)
            {
                float cosTheta = max(d.y, 0.001);
                float cosGamma = clamp(dot(d, _SkySunDir.xyz), -1.0, 1.0);
                float gamma = acos(cosGamma);
                float3 clear = 0;
                if (_SkyMisc.x < 1.0)
                {
                    float Y = Perez(_SkyPerezY, _SkyPerezE.x, cosTheta, gamma, cosGamma) * _SkyZenith.z;
                    float cosThetaC = max(cosTheta, 0.104528);   // chromaticity no lower than 6° (Preetham magenta horizon)
                    float x = Perez(_SkyPerezX, _SkyPerezE.y, cosThetaC, gamma, cosGamma) * _SkyZenith.x;
                    float y = Perez(_SkyPerezYc, _SkyPerezE.z, cosThetaC, gamma, cosGamma) * _SkyZenith.y;
                    clear = XyYToRec709(x, y, Y);
                }
                float over = _SkyZenith.w * (1.0 + 2.0 * cosTheta) / 3.0;
                return lerp(clear, over.xxx, _SkyMisc.x);
            }

            half4 frag(Varyings i) : SV_Target
            {
                float3 d = normalize(i.dir);
                float3 sky = SkyRadiance(d);
                // Sun disc (0.53° nominal, slightly enlarged so it survives render scale), with limb darkening.
                float cosSun = dot(d, _SkySunDir.xyz);
                float r = 0.00465 * _SunDiscScale;               // angular radius in radians
                float ang = acos(clamp(cosSun, -1.0, 1.0));
                float disc = saturate(1.0 - ang / r);
                float limb = 0.4 + 0.6 * sqrt(disc);
                float3 sun = _SkySunColor.rgb * min(_SkyMisc.y, 64.0) * limb * step(1e-4, disc) * (1.0 - _SkyMisc.x);
                float3 c = sky + sun * smoothstep(0.0, 0.02, d.y + 0.01);
                // Below the horizon: distant ground seen through the full aerial perspective = fog colour.
                float below = smoothstep(0.0, 0.03, -d.y);
                c = lerp(c, _SkyFogColor.rgb, below);
                // Banding: ±0.5 LSB of 8-bit sRGB in linear space (interleaved gradient noise, Jimenez 2014).
                float n = frac(52.9829189 * frac(dot(i.positionCS.xy, float2(0.06711056, 0.00583715)))) - 0.5;
                float3 srgb = LinearToSRGB(saturate(c)) + n / 255.0;
                c = lerp(c, SRGBToLinear(saturate(srgb)), step(c, 1.0));
                return half4(c, 1.0);
            }
            ENDHLSL
        }
    }
    Fallback Off
}
