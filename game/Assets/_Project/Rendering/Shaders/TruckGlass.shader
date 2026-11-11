// Thin-sheet vehicle glass (track A7): windscreen, door glass, lamp lenses (exterior Glass slot) and the cluster cover glass
// (interior). Premultiplied alpha: the scene behind is attenuated by (1 - alpha) and the Fresnel reflection is added.
// Tint from the vertex colour (sRGB, exterior contract: windscreen slightly green, lenses clear) times _Tint. Neither casts
// nor receives shadows.
// Reflection (review r3 E2 / r4 E2: "aquarium glass"):
// - outside face (normal away from the cab centre _CabCentreOS): Schlick F0 0.04 on the environment = the vehicle
//   reflection capture (VehicleReflectionCapture, High) or the sky cubemap (Low/Medium), plus the sun highlight;
// - inside face (seen from the cab): the cab is the "environment" - a cheap analytic interior radiance (dark dash in the
//   lower hemisphere of the reflected ray, headliner above) lit by the sky irradiance and the sun on the dash top, so the
//   windscreen carries the faint dash reflection a driver sees (docs/06 §4) instead of an outdoor horizon.
// Dirt (_Wiper > 0, windscreen only): a thin road film outside the two wiper sweeps (pivots and blade radii in the glass
// object space, from the exterior manifest), denser towards the bottom edge. The film scatters sky and sun light (haze)
// and roughens the reflection. Optional grime texture (interior T_Cab_GlassGrime on uv0) as before.
// ADR 0080 r11 (review 2026-11-10 B6): the sweep border is a 12 cm / 16 deg feathered transition (a blade leaves a
// ragged, smeared edge; the 2 cm / 2 deg border drew a sharp arc and a vertical line across the sky against the sun), the
// periodic 1.5 cm blade arcs are gone (concentric banding in the sky), and the sun glare of the film is capped at 2x
// isotropic (was 4x).
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
        _CabCentreOS ("Cab centre in object space (inside / outside face)", Vector) = (0, 1.0, -0.6, 0)
        _InteriorAlbedo ("Interior albedo seen in the glass (dash below, headliner above)", Vector) = (0.035, 0.12, 0, 0)
        _Wiper ("Road film outside the wiper sweeps (0 = off)", Range(0, 1)) = 0
        _WiperPivotA ("Wiper A pivot (object xy) + inner, outer radius", Vector) = (-1.0, 0.87, 0.18, 0.95)
        _WiperPivotB ("Wiper B pivot (object xy) + inner, outer radius", Vector) = (-0.08, 0.87, 0.18, 0.95)
        _WiperSweep ("Sweep start, end (deg from +X towards +Y), windscreen min/max object y", Vector) = (-5, 100, 0.8, 2.0)
        _WindscreenMinZ ("Windscreen: object z above this (front face of the cab)", Float) = 0.95
        _ExteriorTransmission ("Seen from outside: share of the cab behind the pane that reaches the eye (0.7 x cab occlusion)", Range(0, 1)) = 0.42
        _SeeThroughClutter ("Seen from outside: share of the far pane (path through the cab) not blocked by seats / curtains (ADR 0059)", Range(0, 1)) = 0.35
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
            // ADR 0106: Low fast path (QualityProfile.glassFast, global keyword): ambient SH per vertex (flat panes), polynomial
            // atan2 in the wiper sweeps. Same image within 1/255 (visual QA); A16 Low windscreen pass measured 3.6 ms GPU.
            #pragma multi_compile _ _KAMION_GLASS_FAST
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Assets/_Project/Rendering/Shaders/KamionAtmosphere.hlsl"   // ADR 0080 height haze, Low tone toe, wetness
            #include "KamionVehicleEnv.hlsl"
            float _KamionCamOutside;    // CabInteriorLighting: 1 = view camera outside the cab, 0 = cab view or no cab lighting
            float4 _KamionGrimeUp[4];   // vehicle frames (ContactShadowCaster): height above the wheel-contact plane

            CBUFFER_START(UnityPerMaterial)
                float4 _Tint;
                float4 _GrimeMap_ST;
                float4 _CabCentreOS, _InteriorAlbedo, _WiperPivotA, _WiperPivotB, _WiperSweep;
                float _Opacity, _Smoothness, _Grime, _UseVertexColor, _Wiper, _WindscreenMinZ, _ExteriorTransmission, _SeeThroughClutter;
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
                float3 positionOS : TEXCOORD5;
                half inside : TEXCOORD6;
            #if defined(_KAMION_GLASS_FAST)
                half3 amb : TEXCOORD7;      // SampleSH(outward normal), per vertex (planar panes)
                half3 skyE : TEXCOORD8;     // SampleSH(up)
            #endif
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
                o.fogFactor = KamionFogTau(p.positionWS, p.positionCS.w);
                o.positionOS = v.positionOS.xyz;
                // Inner face of the glass: its normal points towards the cab centre.
                o.inside = dot(v.normalOS, _CabCentreOS.xyz - v.positionOS.xyz) > 0.0 ? 1.0 : 0.0;
            #if defined(_KAMION_GLASS_FAST)
                half3 nW = normalize(o.normalWS);
                o.amb = SampleSH(o.inside > 0.5 ? -nW : nW);
                o.skyE = SampleSH(half3(0, 1, 0));
            #endif
                return o;
            }

            // ADR 0106: atan2 by a minimax polynomial (|error| < 1e-5 rad = 0.0006 deg; the sweep border is 16 deg wide).
            float KamionAtan2(float y, float x)
            {
                float ax = abs(x), ay = abs(y);
                float a = min(ax, ay) / max(max(ax, ay), 1e-6);
                float s = a * a;
                float r = ((-0.0464964749 * s + 0.15931422) * s - 0.327622764) * s * a + a;
                r = ay > ax ? 1.57079637 - r : r;
                r = x < 0.0 ? 3.14159274 - r : r;
                return y < 0.0 ? -r : r;
            }

            // 1 inside one wiper sweep (annulus sector), 0 outside, soft 2 cm border; also the arc streak phase.
            half Sweep(float2 p, float4 pivot, float2 sweepDeg, out float r)
            {
                float2 d = p - pivot.xy;
                r = length(d);
            #if defined(_KAMION_GLASS_FAST)
                float a = degrees(KamionAtan2(d.y, d.x));
            #else
                float a = degrees(atan2(d.y, d.x));
            #endif
                half inR = smoothstep(pivot.z - 0.06, pivot.z + 0.06, r) * (1.0 - smoothstep(pivot.w - 0.06, pivot.w + 0.06, r));
                half inA = smoothstep(sweepDeg.x - 8.0, sweepDeg.x + 8.0, a) * (1.0 - smoothstep(sweepDeg.y - 8.0, sweepDeg.y + 8.0, a));
                return inR * inA;
            }

            half4 frag(Varyings i) : SV_Target
            {
                half3 n = normalize(i.normalWS);
                float3 V = GetWorldSpaceNormalizeViewDir(i.positionWS);
                half NoV = saturate(abs(dot(n, V)));
                // One air-glass interface (Schlick, F0 0.04), then the pane: two interfaces with incoherent
                // inter-reflection, R2 = 2R / (1 + R) (r4 E2: 0.08 at normal incidence, ~0.1 at a 3/4 view, ~0.3 at 70 deg).
                half F1 = 0.04 + 0.96 * Pow4(1.0 - NoV) * (1.0 - NoV);
                half F = 2.0 * F1 / (1.0 + F1);
                // Body absorption over the refracted path (n 1.52): T_abs = (1 - _Opacity)^(1 / cos theta_t), so the
                // interior seen through the glass darkens towards grazing angles.
                half cosT = sqrt(saturate(1.0 - (1.0 - NoV * NoV) * 0.4328));
                half tAbs = exp2(log2(1.0 - _Opacity) / max(cosT, 0.1));
                Light L = GetMainLight();
                // ADR 0059: ambient on the OUTWARD normal (inside face: -n). The film sits on the outer surface; the body tint term
                // below exists on outside faces only, where nOut = n, so one SH evaluation serves both (no extra cost).
                half3 nOut = i.inside > 0.5 ? -n : n;
            #if defined(_KAMION_GLASS_FAST)
                half3 amb = i.amb;
            #else
                half3 amb = SampleSH(nOut);
            #endif

                // ---- road film outside the wiper sweeps (windscreen) ----
                half film = 0;
                if (_Wiper > 0.0)
                {
                    float2 p = i.positionOS.xy;
                    float rA, rB;
                    half wiped = max(Sweep(p, _WiperPivotA, _WiperSweep.xy, rA), Sweep(p, _WiperPivotB, _WiperSweep.xy, rB));
                    half onScreen = step(_WiperSweep.z, p.y) * step(p.y, _WiperSweep.w) * step(_WindscreenMinZ, i.positionOS.z);
                    float h = saturate((p.y - _WiperSweep.z) / max(_WiperSweep.w - _WiperSweep.z, 0.01));
                    // Film: densest at the bottom edge (spray from the road), a light veil elsewhere.
                    half outside = (1.0 - wiped) * (0.35 + 0.65 * (1.0 - h) * (1.0 - h));
                    film = outside * _Wiper * onScreen;
                }

                half grime = SAMPLE_TEXTURE2D(_GrimeMap, sampler_GrimeMap, i.uv).r * _Grime + film;
                half pr = saturate(1.0 - _Smoothness + film * 0.25);
                half3 R = reflect(-V, n);
                // Height above the wheel-contact plane (vehicle frame of ContactShadowCaster; 2 m when the renderer has none).
                uint slot = unity_RendererUserValue;
                bool hasFrame = slot >= 1u && slot <= 4u;
                float h = hasFrame ? dot(i.positionWS, _KamionGrimeUp[slot - 1u].xyz) + _KamionGrimeUp[slot - 1u].w : 2.0;
                half3 env;
                if (i.inside > 0.5)
                {
                    // Cab interior in the reflection: dash below (lit by the sky through the glass and by the sun on its
                    // top), headliner and back wall above (sky light only). Exposed units like the SH ambient.
                #if defined(_KAMION_GLASS_FAST)
                    half3 skyE = i.skyE;
                #else
                    half3 skyE = SampleSH(half3(0, 1, 0));
                #endif
                    half3 dash = _InteriorAlbedo.x * (skyE * 0.6 + L.color * saturate(L.direction.y) * 0.5);
                    half3 roof = _InteriorAlbedo.y * skyE * 0.15;
                    env = lerp(roof, dash, smoothstep(0.1, -0.2, R.y));
                }
                else
                {
                    // r6 E2: analytic ground below the horizon on the tiers without the vehicle capture (KamionVehicleEnv).
                    env = KamionVehicleEnv(R, i.positionWS, pr, 1.0, h);
                }

                // Float GGX with the sun-disc alpha floor 0.01 (r6, as Kamion/Truck Exterior CoatDirect): the half form
                // cancelled to ~0 at the highlight centre (alpha^2 ~ 4e-6) and overflowed fp16 on phone GPUs.
                float r = max(pr * pr, 0.01);
                float3 H = SafeNormalize(float3(L.direction) + V);
                float NoH = saturate(dot(float3(n), H));
                float d = 1.0 - NoH * NoH * (1.0 - r * r);
                half spec = (half)min((r * r) / (4.0 * PI * d * d) * saturate(dot(n, L.direction)) * F * 4.0, 2048.0);

                // Transmittance of the pane: reflection loss x body absorption x grime / film (the film also scatters).
                half trans = (1.0 - F) * tAbs * (1.0 - saturate(grime * 0.25));
                // r6 E2 "aquarium": from outside, the eye looks through the pane into a cab that our interior model leaves
                // nearly empty (no headrest curtains, bunk curtain, clutter) and out again through the far door glass. A
                // real cab stops most of that path: ~0.7 of the light that crosses the cab survives the second pane and the
                // interior clutter, times the cab occlusion (~0.6). WORKING_VALUE; inside faces (driver view) unchanged.
                // Cab glazing band only (1.6-3.2 m above the road): the lamp lenses share this material and must not dim
                // their reflectors / LEDs (headlamps ~1 m, roof marker lamps ~3.7 m).
                half glazing = hasFrame ? step(1.6, h) * step(h, 3.2) : 0.0;
                trans *= lerp(1.0, saturate(_ExteriorTransmission), glazing * (1.0 - i.inside));
                // ADR 0059 (r7/r8 N-8): seen from OUTSIDE the cab (CabInteriorLighting: _KamionCamOutside), an inside face is the far pane at the end of
                // the path through the cab: the eye looked across the empty cab and out of the opposite door glass at the
                // lit hall - the sharp bright "rectangle" in the windscreen. Seats, headrests, the passenger and the bunk
                // curtain block most of that path in a real cab (WORKING_VALUE 0.35: from the 3/4 front view the passenger
                // seat back, headrest and B-pillar trim cover roughly two thirds of the far door glass).
                trans *= lerp(1.0, saturate(_SeeThroughClutter), glazing * i.inside * saturate(_KamionCamOutside));
                // Body colour (the tint the blend cannot apply to the transmitted scene) - outside face only, small: from
                // the cab it reads as a milky veil over the road (r4 E2). Grime / film haze lit by sun and sky on both faces.
                // ADR 0059 (r7 N-16): the road film sits on the OUTER surface, so it is lit with the outward normal on both
                // faces. With the shading normal of the inside face, a low sun behind the cab lit the film seen from the
                // driver's seat (sun "through" the back wall): the wiper sweep borders drew a bright cone and the blade
                // arcs fine diagonal stripes across the sky. Sun term = sun on the outer surface x a Henyey-Greenstein
                // phase (g 0.5, relative to isotropic, capped): bright veiling glare only against the sun, as in a real cab.
                half cosScatter = dot(-L.direction, V);   // light travels along -L, leaves towards the eye along V
                half phase = min(0.75 / pow(max(1.25 - cosScatter, 0.05), 1.5), 2.0);
                half3 body = i.tint * amb * (1.0 - tAbs) * 0.25 * (1.0 - i.inside)
                           + (grime * amb + grime * L.color * saturate(dot(nOut, L.direction)) * phase) * 0.18;
                // From the cab only the first surface carries the dash reflection (no ghost from the outer face: docs/06,
                // r4 E2 "no double reflection"); from outside both surfaces mirror the sky.
                half3 col = body + env * lerp(F, F1, i.inside) + L.color * spec * (1.0 - i.inside * 0.7);
                half alpha = saturate(1.0 - trans);
                col = KamionMixFog(col, i.fogFactor);
                // Premultiplied "over": transmission is grey (1 - alpha); the tint shows in the body term only.
                return half4(col, alpha);
            }
            ENDHLSL
        }
    }
    Fallback Off
}
