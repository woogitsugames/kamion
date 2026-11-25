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
// Drive review s24 #11: the analytic unwiped regions read as upright smoke columns from the driver's eye.
// Keep this stylised road film for exterior views only (including the far pane seen through the cab).
// Cab views retain absorption, Fresnel, interior reflections and optional authored grime, without the sweep-shaped veil.
// ADR 0341 (windscreen-s24, critic s24 build5 #6 "sterile glass"): two cheap layers on the windscreen, both faces.
// - _GrimeMask (tools/rendering/windscreen_grime.py, glass object xy through _GrimeRect): R dust that scatters (edge
//   accumulation, speckle where the blades do not reach, ragged sweep border), G worn-blade arcs inside the sweeps, B insect
//   remains. High-frequency only (mm..cm, 5 % of the pane): no broad veil, the s24 #11 "smoke columns" stay gone. The
//   dust and the arcs light up through the Henyey-Greenstein phase against the sun; in diffuse light they are faint.
// - _CabReflection (tools/blender/truck/interior/bake_windscreen_reflection.py): the cab interior as albedo x AO seen
//   from the driver's eye mirrored in the windscreen plane (equirect, cab frame). For a plane the reflected ray continues
//   along E' -> P, so one texture lookup with R gives the dash image (exact for the driver's eye, centimetre parallax for
//   other heads), relit here by the sky SH, the cab fill (_CabFill) and the sun on the dash. Full path only; the Low /
//   Medium fast path keeps the analytic interior (one sample less) and gets the dirt mask.
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
        [NoScaleOffset] _GrimeMask ("ADR 0341 windscreen dirt (R dust, G wiper arcs, B insects), glass object xy", 2D) = "black" {}
        _GrimeRect ("ADR 0341 dirt mask rectangle: object x0, y0, 1 / width, 1 / height", Vector) = (-1.3, 0.75, 0.384615, 0.769231)
        _GrimeLayers ("ADR 0341 dust, arcs, insects strength (0 = off)", Vector) = (1, 1, 1, 0)
        [NoScaleOffset] _CabReflection ("ADR 0341 cab interior seen in the windscreen (equirect, cab frame, albedo x AO)", 2D) = "black" {}
        _CabReflectionGain ("ADR 0341 cab reflection gain (0 = analytic interior)", Range(0, 2)) = 0
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
            // ADR 0106: Low fast path (QualityProfile.glassFast, global keyword): Fresnel, body absorption, film phase, ambient SH
            // and fog transmittance per vertex, wiper sweeps in half precision (FragFast). A16 Low: the pane (~80 % of the cab
            // view) cost 3.6-4.3 ms GPU, the fast path saves 0.9 ms; control cameras PSNR 62-82 dB against the full path.
            #pragma multi_compile _ _KAMION_GLASS_FAST
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Assets/_Project/Rendering/Shaders/KamionAtmosphere.hlsl"   // ADR 0080 height haze, Low tone toe, wetness
            #include "KamionVehicleEnv.hlsl"
            float _KamionGlassDebug;    // ADR 0106 diagnostics (rq_ab glassdbg rq_glassdbg 1): 1 = constant colour (raster + blend floor of the pane)
            float _KamionCamOutside;    // CabInteriorLighting: 1 = view camera outside the cab, 0 = cab view or no cab lighting
            half4 _CabFill;             // CabInteriorLighting: rgb first-bounce fill per unit albedo (exposed), w sun transmittance
            half _CabEnclosure;         // CabInteriorLighting: share of the open-sky SH the closed cab blocks
            half _KamionWindscreenOff;  // ADR 0341 quality switch (QualityProfile.windscreenLayersOff): 1 = no dirt, analytic interior
            float4 _KamionGrimeUp[4];   // vehicle frames (ContactShadowCaster): height above the wheel-contact plane

            CBUFFER_START(UnityPerMaterial)
                float4 _Tint;
                float4 _GrimeMap_ST;
                float4 _CabCentreOS, _InteriorAlbedo, _WiperPivotA, _WiperPivotB, _WiperSweep;
                float _Opacity, _Smoothness, _Grime, _UseVertexColor, _Wiper, _WindscreenMinZ, _ExteriorTransmission, _SeeThroughClutter;
                float4 _GrimeRect, _GrimeLayers;
                float _CabReflectionGain;
            CBUFFER_END
            TEXTURE2D(_GrimeMap); SAMPLER(sampler_GrimeMap);
            TEXTURE2D(_GrimeMask); SAMPLER(sampler_GrimeMask);
            TEXTURE2D(_CabReflection); SAMPLER(sampler_CabReflection);

            // ADR 0341: dirt layers at this point of the pane (R dust, G arcs, B insects), scaled by _GrimeLayers.
            half3 WindscreenDirt(float3 positionOS)
            {
                [branch] if (_KamionWindscreenOff > 0.5) return half3(0, 0, 0);   // uniform: skips the sample
                float2 uv = (positionOS.xy - _GrimeRect.xy) * _GrimeRect.zw;
                return SAMPLE_TEXTURE2D(_GrimeMask, sampler_GrimeMask, uv).rgb * (half3)_GrimeLayers.xyz;
            }

            // ADR 0341: light the dirt adds (premultiplied) and the share of the transmitted scene it keeps.
            // Dust: veiling glare through the film phase, faint grey in diffuse light. Arcs: glare only, narrower lobe (phase^2).
            // Insects: dark, nearly opaque bodies (albedo ~0.08, translucent rims catch the sun a little).
            // glass-sky-s24 (critic s24 build #8 P0#2): the arcs drew a fan of bright thin lines over the whole sky ("cracks /
            // power lines"): glare x phase (both broad, up to 2 x 2 x sun) made them shine at any angle within ~90 deg of the
            // sun. Now a smear only lights up close to the sun (smoothstep cone cos 0.80 = ~37 deg, squared), and its added
            // light is capped by the sky ambient on the outer face (stand-in for the background luminance the premultiplied
            // pane cannot read): <= 0.6 x amb x G, i.e. a soft band of at most ~13 % of the sky behind it. The dust glare is
            // capped the same way (<= 1.2 x amb x R) so specks do not sparkle against the sky when the sun is far brighter.
            void DirtShade(half3 d, half3 amb, half3 glare, half cosScatter, out half3 add, out half keep)
            {
                half cone = smoothstep(0.80h, 1.0h, cosScatter);
                half3 arcs = min(glare * (cone * cone * 0.15h), amb * 0.6h);
                add = d.r * (amb * 0.10 + min(glare * 0.30, amb * 1.2h)) + d.g * arcs + d.b * (amb * 0.04 + glare * 0.08);
                keep = (1.0 - 0.08 * d.r) * (1.0 - 0.03 * d.g) * (1.0 - 0.65 * d.b);
            }

            // ADR 0341: cab interior reflected in the windscreen (inside face), relit for the current sky / sun.
            half3 CabReflectionEnv(half3 R, Light L)
            {
                float3 r = normalize(TransformWorldToObjectDir(float3(R)));
                float2 uv = float2(0.5 - atan2(r.z, r.x) * (0.5 * INV_PI), 0.5 + asin(clamp(r.y, -1.0, 1.0)) * INV_PI);
                half3 a = SAMPLE_TEXTURE2D_LOD(_CabReflection, sampler_CabReflection, uv, 0).rgb;    // albedo x AO
                half3 skyE = SampleSH(half3(0, 1, 0)) * (1.0 - _CabEnclosure);
                // Sun through the windscreen onto the dash top: sun ahead of the cab and above the horizon, dash directions only.
                float3 lo = TransformWorldToObjectDir(float3(L.direction));
                half sunDash = saturate(lo.y) * saturate(lo.z * 2.0) * smoothstep(-0.05, -0.25, r.y) * (_CabFill.w > 0.0 ? _CabFill.w : 0.75);
                return a * (skyE + _CabFill.rgb + L.color * sunDash) * _CabReflectionGain;
            }

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
                half4 fres : TEXCOORD9;     // F1, F (two interfaces), body absorption tAbs, film phase - per vertex (smooth in V)
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
                // View-dependent pane terms per vertex (518-vertex windscreen, a few degrees of view angle between vertices at
                // the driver's eye; these terms are smooth in the view angle). Same formulas as frag().
                float3 Vv = GetWorldSpaceNormalizeViewDir(p.positionWS);
                half NoVv = saturate(abs(dot(nW, (half3)Vv)));
                half F1v = 0.04 + 0.96 * Pow4(1.0 - NoVv) * (1.0 - NoVv);
                half cosTv = sqrt(saturate(1.0 - (1.0 - NoVv * NoVv) * 0.4328));
                Light Lv = GetMainLight();
                half cosSc = dot(-Lv.direction, (half3)Vv);
                o.fres = half4(F1v, 2.0 * F1v / (1.0 + F1v), exp2(log2(1.0 - _Opacity) / max(cosTv, 0.1)),
                               min(0.75 / pow(max(1.25 - cosSc, 0.05), 1.5), 2.0));
                o.fogFactor = exp(-o.fogFactor);   // fast path: transmittance of the aerial perspective (lerp in the fragment)
            #endif
                return o;
            }

            // 1 inside one wiper sweep (annulus sector), 0 outside, soft 2 cm border; also the arc streak phase.
            half Sweep(float2 p, float4 pivot, float2 sweepDeg, out float r)
            {
                float2 d = p - pivot.xy;
                r = length(d);
                float a = degrees(atan2(d.y, d.x));
                half inR = smoothstep(pivot.z - 0.06, pivot.z + 0.06, r) * (1.0 - smoothstep(pivot.w - 0.06, pivot.w + 0.06, r));
                half inA = smoothstep(sweepDeg.x - 8.0, sweepDeg.x + 8.0, a) * (1.0 - smoothstep(sweepDeg.y - 8.0, sweepDeg.y + 8.0, a));
                return inR * inA;
            }

        #if defined(_KAMION_GLASS_FAST)
            // ADR 0106: the wiper sweeps in half precision (object space within +-2.5 m: ~2 mm steps; atan2 by a minimax
            // polynomial, error well under 0.1 deg against the 16 deg border).
            half SweepH(half2 p, half4 pivot, half2 sweepDeg)
            {
                half2 d = p - pivot.xy;
                half r = length(d);
                half ax = abs(d.x), ay = abs(d.y);
                half a0 = min(ax, ay) / max(max(ax, ay), 1e-3h);
                half s2 = a0 * a0;
                half t = ((-0.0464964749h * s2 + 0.15931422h) * s2 - 0.327622764h) * s2 * a0 + a0;
                t = ay > ax ? 1.5707964h - t : t;
                t = d.x < 0.0h ? 3.1415927h - t : t;
                half a = (d.y < 0.0h ? -t : t) * 57.29578h;
                half inR = smoothstep(pivot.z - 0.06h, pivot.z + 0.06h, r) * (1.0h - smoothstep(pivot.w - 0.06h, pivot.w + 0.06h, r));
                half inA = smoothstep(sweepDeg.x - 8.0h, sweepDeg.x + 8.0h, a) * (1.0h - smoothstep(sweepDeg.y - 8.0h, sweepDeg.y + 8.0h, a));
                return inR * inA;
            }

            // Low fast path (QualityProfile.glassFast): the model of frag() with the view-dependent pane terms (Fresnel, body
            // absorption, film phase), the ambient SH and the fog transmittance interpolated from the vertices.
            half4 FragFast(Varyings i)
            {
                half3 n = normalize(i.normalWS);
                float3 V = GetWorldSpaceNormalizeViewDir(i.positionWS);
                half F1 = i.fres.x, F = i.fres.y, tAbs = i.fres.z, phase = i.fres.w;
                Light L = GetMainLight();
                half3 nOut = i.inside > 0.5 ? -n : n;
                half3 amb = i.amb;
                half film = 0;
                if (_Wiper > 0.0 && (i.inside < 0.5 || _KamionCamOutside > 0.5))
                {
                    half2 p = (half2)i.positionOS.xy;
                    half wiped = max(SweepH(p, (half4)_WiperPivotA, (half2)_WiperSweep.xy), SweepH(p, (half4)_WiperPivotB, (half2)_WiperSweep.xy));
                    half onScreen = step((half)_WiperSweep.z, p.y) * step(p.y, (half)_WiperSweep.w) * step((half)_WindscreenMinZ, (half)i.positionOS.z);
                    half hh = saturate((p.y - (half)_WiperSweep.z) / max((half)(_WiperSweep.w - _WiperSweep.z), 0.01h));
                    film = (1.0h - wiped) * (0.35h + 0.65h * (1.0h - hh) * (1.0h - hh)) * (half)_Wiper * onScreen;
                }
                half grime = SAMPLE_TEXTURE2D(_GrimeMap, sampler_GrimeMap, i.uv).r * _Grime + film;
                half3 dirt = WindscreenDirt(i.positionOS);
                half pr = saturate(1.0 - _Smoothness + film * 0.25 + dirt.r * 0.2);
                half3 R = reflect(-V, n);
                uint slot = unity_RendererUserValue;
                bool hasFrame = slot >= 1u && slot <= 4u;
                float h = hasFrame ? dot(i.positionWS, _KamionGrimeUp[slot - 1u].xyz) + _KamionGrimeUp[slot - 1u].w : 2.0;
                half3 env;
                if (i.inside > 0.5)
                {
                    half3 dash = _InteriorAlbedo.x * (i.skyE * 0.6 + L.color * saturate(L.direction.y) * 0.5);
                    half3 roof = _InteriorAlbedo.y * i.skyE * 0.15;
                    env = lerp(roof, dash, smoothstep(0.1, -0.2, R.y));
                }
                else env = KamionVehicleEnv(R, i.positionWS, pr, 1.0, h);
                float r = max(pr * pr, 0.01);
                float3 H = SafeNormalize(float3(L.direction) + V);
                float NoH = saturate(dot(float3(n), H));
                float d = 1.0 - NoH * NoH * (1.0 - r * r);
                half spec = (half)min((r * r) / (4.0 * PI * d * d) * saturate(dot(n, L.direction)) * F * 4.0, 2048.0);
                half trans = (1.0 - F) * tAbs * (1.0 - saturate(grime * 0.25));
                half glazing = hasFrame ? step(1.6, h) * step(h, 3.2) : 0.0;
                trans *= lerp(1.0, saturate(_ExteriorTransmission), glazing * (1.0 - i.inside));
                trans *= lerp(1.0, saturate(_SeeThroughClutter), glazing * i.inside * saturate(_KamionCamOutside));
                half3 glare = L.color * saturate(dot(nOut, L.direction)) * phase;
                half3 dirtAdd; half dirtKeep;
                half cosScatter = dot(-L.direction, V);   // fast path: phase comes from the vertex stage, the dirt cone needs it here
                DirtShade(dirt, amb, glare, cosScatter, dirtAdd, dirtKeep);    // ADR 0341, glass-sky-s24
                trans *= dirtKeep;
                half3 body = i.tint * amb * (1.0 - tAbs) * 0.25 * (1.0 - i.inside)
                           + (grime * amb + grime * glare) * 0.18 + dirtAdd;
                half3 col = body + env * lerp(F, F1, i.inside) + L.color * spec * (1.0 - i.inside * 0.7);
                [branch] if (_KamionGlassDebug == 3.0) return half4(dirt, 1);
                // ADR 0115: premultiplied glass contributes only its coverage share of atmospheric in-scatter.
                // The vertex already supplied exp(-tau); keep the fast path's transmittance and sampling policy.
                half4 pane = half4(col, saturate(1.0 - trans));
                pane.rgb = KamionTone(lerp(_KamionHazeColor.rgb * pane.a, pane.rgb, i.fogFactor));
                return pane;
            }
        #endif

            half4 frag(Varyings i) : SV_Target
            {
                [branch] if (_KamionGlassDebug == 1.0) return half4(0.004, 0.005, 0.005, 0.1);
            #if defined(_KAMION_GLASS_FAST)
                return FragFast(i);
            #else
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
                half3 amb = SampleSH(nOut);

                // ---- road film outside the wiper sweeps (windscreen) ----
                half film = 0;
                if (_Wiper > 0.0 && (i.inside < 0.5 || _KamionCamOutside > 0.5))
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
                half3 dirt = WindscreenDirt(i.positionOS);
                half pr = saturate(1.0 - _Smoothness + film * 0.25 + dirt.r * 0.2);
                half3 R = reflect(-V, n);
                // Height above the wheel-contact plane (vehicle frame of ContactShadowCaster; 2 m when the renderer has none).
                uint slot = unity_RendererUserValue;
                bool hasFrame = slot >= 1u && slot <= 4u;
                float h = hasFrame ? dot(i.positionWS, _KamionGrimeUp[slot - 1u].xyz) + _KamionGrimeUp[slot - 1u].w : 2.0;
                half3 env;
                if (i.inside > 0.5 && _CabReflectionGain > 0.0 && _KamionWindscreenOff < 0.5)
                {
                    env = CabReflectionEnv(R, L);    // ADR 0341: baked cab image (albedo x AO), relit
                }
                else if (i.inside > 0.5)
                {
                    // Cab interior in the reflection: dash below (lit by the sky through the glass and by the sun on its
                    // top), headliner and back wall above (sky light only). Exposed units like the SH ambient.
                    half3 skyE = SampleSH(half3(0, 1, 0));
                    half3 dash = _InteriorAlbedo.x * (skyE * 0.6 + L.color * saturate(L.direction.y) * 0.5);
                    half3 roof = _InteriorAlbedo.y * skyE * 0.15;
                    env = lerp(roof, dash, smoothstep(0.1, -0.2, R.y));
                }
                else
                {
                    // r6 E2: analytic ground below the horizon on the tiers without the vehicle capture (KamionVehicleEnv).
                    // ADR0087 WORKING_VALUE: filter the finite64/128px capture footprint, without changing
                    // the physical Fresnel/direct-sun roughness or substituting an analytic sky for the scene.
                    half captureRoughness = _KamionVehicleCapture > 0.5 ? max(pr, 0.09h) : pr;
                    env = KamionVehicleEnv(R, i.positionWS, captureRoughness, 1.0, h);
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
                half3 glare = L.color * saturate(dot(nOut, L.direction)) * phase;
                half3 dirtAdd; half dirtKeep;
                DirtShade(dirt, amb, glare, cosScatter, dirtAdd, dirtKeep);    // ADR 0341, glass-sky-s24
                trans *= dirtKeep;
                half3 body = i.tint * amb * (1.0 - tAbs) * 0.25 * (1.0 - i.inside)
                           + (grime * amb + grime * glare) * 0.18 + dirtAdd;
                [branch] if (_KamionGlassDebug == 2.0) return half4(i.inside > 0.5 ? env * 8.0 : half3(0, 0, 0), 1);
                [branch] if (_KamionGlassDebug == 3.0) return half4(dirt, 1);
                // From the cab only the first surface carries the dash reflection (no ghost from the outer face: docs/06,
                // r4 E2 "no double reflection"); from outside both surfaces mirror the sky.
                half3 col = body + env * lerp(F, F1, i.inside) + L.color * spec * (1.0 - i.inside * 0.7);
                half alpha = saturate(1.0 - trans);
                // Premultiplied glass adds only its alpha share of in-scatter: the transmitted scene already
                // contains fog. Full opaque in-scatter here added an extra grey veil over that background.
                col = KamionTone(lerp(_KamionHazeColor.rgb * alpha, col, exp(-i.fogFactor)));
                // Premultiplied "over": transmission is grey (1 - alpha); the tint shows in the body term only.
                return half4(col, alpha);
            #endif
            }
            ENDHLSL
        }
    }
    Fallback Off
}
