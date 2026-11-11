// Analytic daylight sky (Preetham 1999 clear luminance × single-scattering colour LUT + CIE overcast), parameters computed
// on the CPU by Game.Rendering.SkyModel.
// Output is in exposed display units (same exposure as the sun light, ambient SH and fog), so the horizon matches the fog.
// Below the horizon the dome fades to the fog colour (aerial perspective of distant ground): no hard horizon seam.
// Interleaved-gradient-noise dither of ±0.5 LSB hides 8-bit banding on LDR tiers (no post-processing dither there).
// Cloud deck (ADR 0080): the overcast dome is modulated by a tileable noise texture (Game.Rendering.CloudNoise) projected
// on a plane above the viewer (perspective compresses it into bands toward the horizon), contrast fading into the haze at
// the horizon, mean 1 (the dome's illuminance, the ambient SH and the fog colour are unchanged). Per tier
// (_KamionCloud.y): 0 = 2 fetches, 1 = + fine detail (3), 2 = + relief toward the sun's azimuth (5). The overcast dome
// itself is brighter toward the sun's azimuth (_SkyMisc.z, SkyModel.OvercastDirectional).
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
            #include "Assets/_Project/Rendering/Shaders/KamionAtmosphere.hlsl"   // tone toe of the tiers without post (ADR 0080)

            float4 _SkyPerezY;      // A..D for Y
            float4 _SkyPerezX;      // A..D for x
            float4 _SkyPerezYc;     // A..D for y
            float4 _SkyPerezE;      // E for Y, x, y
            float4 _SkyZenith;      // x0/F0, y0/F0, clearScale*k/F0(Y), overcastZenith*k
            float4 _SkyMisc;        // overcast, sun disc radiance (exposed)
            float4 _SkySunDir;      // xyz towards the sun
            float4 _SkySunColor;    // linear, luminance 1
            float4 _SkyFogColor;    // exposed horizon colour
            float4 _SkyOvercastColor; // rgb: neutral after the optional WB adaptation (ADR 0043), a = 1 when set
            float _SunDiscScale;
            // Phone sky tone mapping (review r6 L4, D23): display caps of the dome as exposed luminance, x at the horizon,
            // y towards the zenith, z = 1 when set (EnvironmentLighting, from the tier's tone curve). _KamionSkyCapOff = 1
            // while the vehicle reflection capture renders (reflections keep the physical sky radiance).
            float4 _KamionSkyCap;
            float _KamionSkyDitherOff; // ADR0098 A/B; zero preserves existing sky dither.
            float _KamionSkyCapOff;
            TEXTURE2D(_SkyChroma); SAMPLER(sampler_SkyChroma);   // u = γ/π, v = sqrt(cos θ); rgb of luminance 1
            TEXTURE2D(_KamionCloudTex); SAMPLER(sampler_KamionCloudTex);   // R billows, G medium, B fine, A sheets; mean 0.5 each
            float4 _KamionCloud;       // x contrast (0 = off), y quality 0..2, z uv per plane unit, w horizon fade rate
            float4 _KamionCloudWind;   // xy uv offset of the deck, zw of the medium layer
            float4 _KamionCloudSun;    // xy unit XZ towards the sun's azimuth, z relief strength, w relief step (uv)
            float _KamionClearCloudCover; // ADR 0108: zero retains the original clear dome.
            float _KamionClearCloudPhoto;
            float4x4 _KamionClearCloudRotation;
            TEXTURE2D(_KamionClearCloudTex); SAMPLER(sampler_KamionClearCloudTex); // R opacity, G photographic relative luminance.

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
                    float2 uv = float2(gamma / PI, sqrt(saturate(d.y)));
                    uv = (uv * float2(63.0, 31.0) + 0.5) / float2(64.0, 32.0);     // texel centres of the 64×32 LUT
                    clear = SAMPLE_TEXTURE2D_LOD(_SkyChroma, sampler_SkyChroma, uv, 0).rgb * Y;
                }
                float over = _SkyZenith.w * (1.0 + 2.0 * cosTheta) / 3.0;
                float cg = max(cosGamma, 0.0);
                over *= 1.0 + _SkyMisc.z * cg * cg;      // thinner cloud toward the sun (normalised on the CPU)
                float3 oc = _SkyOvercastColor.a > 0.5 ? _SkyOvercastColor.rgb : float3(1.0, 1.0, 1.0);
                return lerp(clear, over * oc, _SkyMisc.x);
            }

            // Cloud deck luminance factor (mean 1): thick parts darker, thin parts lighter.
            half CloudDeck(float3 d, out half2 clearCloud)
            {
                clearCloud = 0.0;
                if (_KamionCloud.x <= 0.0 && _KamionClearCloudCover <= 0.0) return 1.0;
                bool photo = _KamionClearCloudPhoto > 0.5 && _KamionClearCloudCover > 0.0;
                if (photo)
                {
                    float3 ray = normalize(mul((float3x3)_KamionClearCloudRotation, d));
                    float2 uv = float2(frac(atan2(ray.x, ray.z) / (2.0 * PI) + 0.5), asin(clamp(ray.y, -1.0, 1.0)) / PI + 0.5);
                    // A longitude wrap is not a one-texture-wide pixel footprint. Correct the implicit U
                    // derivative across that boundary, or mip selection draws a vertical dashed seam.
                    float2 dx = ddx(uv), dy = ddy(uv);
                    dx.x -= round(dx.x); dy.x -= round(dy.x);
                    half2 source = SAMPLE_TEXTURE2D_GRAD(_KamionClearCloudTex, sampler_KamionClearCloudTex, uv, dx, dy).rg;
                    clearCloud = half2(source.r * (half)_KamionClearCloudCover * smoothstep(0.0, 0.06, d.y), source.g);
                    if (_KamionCloud.x <= 0.0) return 1.0; // Clear: one photographic fetch, no noise deck.
                }
                float2 p = d.xz / (max(d.y, 0.0) + 0.14);          // plane at height 1; +0.14: finite at the horizon
                float2 u = p * _KamionCloud.z + _KamionCloudWind.xy;
                half4 a = SAMPLE_TEXTURE2D(_KamionCloudTex, sampler_KamionCloudTex, u);
                half4 b = SAMPLE_TEXTURE2D(_KamionCloudTex, sampler_KamionCloudTex, u * 2.9 + _KamionCloudWind.zw);
                half n = a.a * 0.50 + a.r * 0.36 + b.g * 0.14;
                if (_KamionCloud.y > 0.5)
                    n += (SAMPLE_TEXTURE2D(_KamionCloudTex, sampler_KamionCloudTex, u * 7.7 + 0.31).b - 0.5) * 0.07;
                half relief = 0.0;
                if (_KamionCloud.y > 1.5)
                {
                    float2 us = u + _KamionCloudSun.xy * _KamionCloudSun.w;
                    half n2 = SAMPLE_TEXTURE2D(_KamionCloudTex, sampler_KamionCloudTex, us).a * 0.50
                            + SAMPLE_TEXTURE2D(_KamionCloudTex, sampler_KamionCloudTex, us).r * 0.36
                            + SAMPLE_TEXTURE2D(_KamionCloudTex, sampler_KamionCloudTex, us * 2.9 + _KamionCloudWind.zw).g * 0.14;
                    relief = (n - n2) * _KamionCloudSun.z;         // thinner toward the sun = lit edge
                }
                half s = smoothstep(0.26, 0.74, n);                // billow edges; symmetric, mean stays 0.5
                half fade = 1.0 - exp(-max(d.y, 0.0) * _KamionCloud.w);
                if (_KamionClearCloudCover > 0.0 && !photo)
                {
                    // Sparse billows leave blue gaps. Use the SAME two base fetches on Low (no new pass/texture).
                    half threshold = lerp(0.75h, 0.25h, (half)_KamionClearCloudCover);
                    clearCloud.x = smoothstep(threshold - 0.035h, threshold + 0.035h, n) * fade;
                    // Thicker cloud interiors are darker; the optional tier relief lights the sunward rim.
                    clearCloud.y = saturate(0.98h - saturate((n - threshold) * 5.0h) * 0.26h + relief * 0.15h);
                }
                return 1.0 + (half)_KamionCloud.x * fade * ((0.5 - s) * 2.0 + relief);
            }

            half4 frag(Varyings i) : SV_Target
            {
                float3 d = normalize(i.dir);
                float3 sky = SkyRadiance(d);
                half2 clearCloud;
                half deck = CloudDeck(d, clearCloud);
                // A phone keeps cloud-deck tone in an overcast sky (local tone mapping of the bright sky region) instead of
                // clipping the whole dome to 254: soft knee from 80 % of the cap, cap rising from the horizon value (matches
                // the fog, no seam) to the zenith value by ~30 deg elevation. Clear blue sky is below the knee: unchanged.
                if (_KamionSkyCap.z > 0.5 && _KamionSkyCapOff < 0.5)
                {
                    float cap = lerp(_KamionSkyCap.x, _KamionSkyCap.y, smoothstep(0.0, 0.5, d.y));
                    float Y = dot(sky, float3(0.2126, 0.7152, 0.0722));
                    float k = 0.8 * cap;
                    float Yc = Y <= k ? Y : k + (cap - k) * (1.0 - exp(-(Y - k) / max(cap - k, 1e-4)));
                    sky *= Yc / max(Y, 1e-5);
                }
                // After the cap: the cap is the phone's exposure of the deck, the structure is what it keeps of it. The
                // overcast share only (a clear dome has no deck; partly cloudy presets get a proportional hint).
                sky *= lerp(1.0, deck, _SkyMisc.x);
                if (_KamionClearCloudCover > 0.0)
                {
                    // The display cap gives Low and post tiers the same cloud tones. This does not alter the
                    // irradiance model, exposure, surface shading or the legacy overcast deck.
                    float cap = lerp(_KamionSkyCap.x, _KamionSkyCap.y, smoothstep(0.0, 0.5, d.y));
                    float cloudY = cap * lerp(0.35, 1.22, clearCloud.y);
                    // Reflection captures explicitly bypass display compression, as the analytic dome does.
                    if (_KamionSkyCapOff > 0.5)
                        cloudY = _SkyZenith.w * (1.0 + 2.0 * max(d.y, 0.0)) / 3.0 * clearCloud.y;
                    float3 cloud = lerp(_SkyFogColor.rgb, cloudY.xxx, smoothstep(0.0, 0.18, d.y));
                    sky = lerp(sky, cloud, clearCloud.x * (1.0 - _SkyMisc.x));
                }
                // Sun disc (0.53° nominal, slightly enlarged so it survives render scale), with limb darkening.
                float cosSun = dot(d, _SkySunDir.xyz);
                float r = 0.00465 * _SunDiscScale;               // angular radius in radians
                float ang = acos(clamp(cosSun, -1.0, 1.0));
                float disc = saturate(1.0 - ang / r);
                float limb = 0.4 + 0.6 * sqrt(disc);
                float3 sun = _SkySunColor.rgb * min(_SkyMisc.y, 64.0) * limb * step(1e-4, disc) * (1.0 - _SkyMisc.x);
                float3 c = sky + sun * smoothstep(0.0, 0.02, d.y + 0.01) * (1.0 - clearCloud.x);
                // Below the horizon: distant ground seen through the full aerial perspective = fog colour.
                float below = smoothstep(0.0, 0.03, -d.y);
                c = lerp(c, _SkyFogColor.rgb, below);
                c = KamionTone(c);
                // Banding: ±0.5 LSB of 8-bit sRGB in linear space (interleaved gradient noise, Jimenez 2014).
                float n = frac(52.9829189 * frac(dot(i.positionCS.xy, float2(0.06711056, 0.00583715)))) - 0.5;
                float3 srgb = LinearToSRGB(saturate(c)) + n * (1.0 - _KamionSkyDitherOff) / 255.0;
                c = lerp(c, SRGBToLinear(saturate(srgb)), step(c, 1.0));
                return half4(c, 1.0);
            }
            ENDHLSL
        }
    }
    Fallback Off
}
