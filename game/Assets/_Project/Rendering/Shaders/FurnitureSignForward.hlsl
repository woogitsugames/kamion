// URP Lit fragment scaffold: copyright Unity Technologies ApS, Unity Companion License.
// ADR0120 r2: additive analytic return, no URP lights, texture samples or new passes.
// Angle response is an uncalibrated WORKING_VALUE, not a specified sheeting class.
// The Lit UnityPerMaterial buffer remains unchanged in EVERY pass, including UsePass.
// _EmissionColor is the existing coefficient slot; _EMISSION is never compiled in our forward pass.
float4 _FurnitureRetroHead0, _FurnitureRetroHead1, _FurnitureRetroHead2, _FurnitureRetroHead3;
float4 _FurnitureRetroForward, _FurnitureRetroUp, _FurnitureRetroState;
float _KamionExposure;

UNITY_INSTANCING_BUFFER_START(KamionSignProps)
    UNITY_DEFINE_INSTANCED_PROP(float4, _KamionSignWear)
UNITY_INSTANCING_BUFFER_END(KamionSignProps)

half SignWearHash(float2 p)
{
    return (half)frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453);
}

half SignWearNoise(float2 p)
{
    float2 i = floor(p);
    float2 f = frac(p);
    f = f * f * (3.0 - 2.0 * f);
    half a = SignWearHash(i);
    half b = SignWearHash(i + float2(1.0, 0.0));
    half c = SignWearHash(i + float2(0.0, 1.0));
    half d = SignWearHash(i + float2(1.0, 1.0));
    return lerp(lerp(a, b, (half)f.x), lerp(c, d, (half)f.x), (half)f.y);
}

half4 ApplySignWear(float2 uv, half4 wear, inout SurfaceData s)
{
    half age = wear.x;
    half dirt = wear.y;
    half flags = wear.z;
    half seed = wear.w;

    half nLow = SignWearNoise(uv * 7.5 + float2(seed * 37.0, 3.1));
    half nHi = SignWearNoise(uv * 24.0 + float2(1.7, seed * 31.0));
    half nDirt = 0.65h * nLow + 0.35h * nHi;

    // 1. Foil UV fading: red shifts toward chalky pinkish on older signs; slight yellow/blue chalking
    half fade = saturate((age - 0.14h) / 0.86h);
    half redDom = saturate((s.albedo.r - max(s.albedo.g, s.albedo.b)) * 2.4h) * saturate(1.0h - s.albedo.g * 7.0h);
    half3 fadedPink = half3(0.62h, 0.25h, 0.23h) * (0.92h + 0.16h * nLow);
    s.albedo = lerp(s.albedo, fadedPink, redDom * fade * 0.72h);

    half maxCh = max(s.albedo.r, max(s.albedo.g, s.albedo.b));
    half minCh = min(s.albedo.r, min(s.albedo.g, s.albedo.b));
    half chroma = saturate((maxCh - minCh) * 1.8h) * (1.0h - redDom);
    half lum = dot(s.albedo, half3(0.2126h, 0.7152h, 0.0722h));
    s.albedo = lerp(s.albedo, half3(lum, lum, lum) * 1.04h, chroma * fade * 0.22h);
    s.smoothness *= (1.0h - 0.45h * age);

    // 2. Bottom road dust / splash film preserving central pictogram legibility
    half bottomRamp = (half)smoothstep(0.50, 0.02, uv.y + (nDirt - 0.5h) * 0.16h);
    half dustMask = clamp(bottomRamp * (0.35h + 0.90h * dirt) * (0.65h + 0.70h * nDirt) * dirt, 0.0h, 0.55h);
    half3 dustCol = half3(0.18h, 0.165h, 0.135h) * (0.85h + 0.30h * nHi);
    s.albedo = lerp(s.albedo, dustCol, dustMask);
    s.smoothness = lerp(s.smoothness, 0.10h, dustMask);

    half retroAtten = saturate(1.0h - 0.28h * age - 0.50h * dustMask);

    // 3. Localized perimeter edge rust / chipped foil
    bool hasRust = (flags > 0.20h && flags < 0.52h) || flags > 0.85h;
    if (hasRust)
    {
        half aMin = 1.0h;
        aMin = min(aMin, SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, saturate(uv + float2( 0.032,  0.000))).a);
        aMin = min(aMin, SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, saturate(uv + float2(-0.032,  0.000))).a);
        aMin = min(aMin, SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, saturate(uv + float2( 0.000,  0.032))).a);
        aMin = min(aMin, SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, saturate(uv + float2( 0.000, -0.032))).a);
        half rectRim = (half)smoothstep(0.450, 0.495, max(abs(uv.x - 0.5), abs(uv.y - 0.5)));
        half shapeRim = saturate((1.0h - aMin) * 1.4h);
        half rim = max(rectRim, shapeRim);
        half ang = (half)(atan2(uv.y - 0.5, uv.x - 0.5) * 0.15915494 + 0.5);
        half rustPatch = SignWearNoise(float2(ang * 9.0 + seed * 29.0, seed * 11.0)) * SignWearNoise(uv * 28.0 + float2(seed * 17.0, 2.3));
        half rustMask = rim * (half)smoothstep(0.30, 0.56, rustPatch);
        half3 rustCol = lerp(half3(0.11h, 0.042h, 0.018h), half3(0.065h, 0.025h, 0.012h), nHi);
        s.albedo = lerp(s.albedo, rustCol, rustMask);
        s.metallic = lerp(s.metallic, 0.35h, rustMask * 0.5h);
        s.smoothness = lerp(s.smoothness, 0.14h, rustMask);
        retroAtten *= (1.0h - 0.75h * rustMask);
    }

    // 4. Single small weathered anonymous sticker in an opaque corner margin
    if (flags > 0.52h)
    {
        float2 cand[3];
        if (seed < 0.34h)      { cand[0] = float2(0.24, 0.24); cand[1] = float2(0.28, 0.76); cand[2] = float2(0.39, 0.30); }
        else if (seed < 0.68h) { cand[0] = float2(0.76, 0.24); cand[1] = float2(0.72, 0.76); cand[2] = float2(0.61, 0.30); }
        else                   { cand[0] = float2(0.28, 0.76); cand[1] = float2(0.24, 0.24); cand[2] = float2(0.39, 0.70); }

        float2 stPos = cand[0];
        bool stValid = false;
        [unroll]
        for (int k = 0; k < 3; k++)
        {
            float2 c = cand[k];
            half ca = min(
                min(SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, c).a,
                    SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, c + float2(0.030, 0.022)).a),
                SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, c - float2(0.030, 0.022)).a
            );
            if (!stValid && ca > 0.90h) { stPos = c; stValid = true; }
        }
        if (stValid)
        {
            float ang = (seed - 0.5) * 0.55;
            float cs = cos(ang), sn = sin(ang);
            float2 d = uv - stPos;
            float2 q = float2(cs * d.x + sn * d.y, -sn * d.x + cs * d.y);
            float2 box = abs(q) - float2(0.036, 0.022);
            half stMask = 1.0h - (half)smoothstep(0.0, 0.004, max(box.x, box.y));
            if (stMask > 0.001h)
            {
                half3 stAccent = seed < 0.35h ? half3(0.22h, 0.38h, 0.36h) : (seed < 0.70h ? half3(0.48h, 0.32h, 0.16h) : half3(0.42h, 0.19h, 0.18h));
                half band = (half)smoothstep(-0.003, 0.003, q.y);
                half3 stCol = lerp(half3(0.66h, 0.63h, 0.54h), stAccent, band * 0.65h) * (0.88h + 0.20h * nHi);
                s.albedo = lerp(s.albedo, stCol, stMask * 0.90h);
                s.smoothness = lerp(s.smoothness, 0.18h, stMask);
                retroAtten *= (1.0h - 0.80h * stMask);
            }
        }
    }

    return half4(retroAtten, 0, 0, 0);
}

float FurnitureHeadReturn(float4 source, float3 positionWS, float3 normalWS, float3 viewWS, float highBeam)
{
    if (source.w <= 0.0) return 0.0;
    float3 delta = source.xyz - positionWS;
    float distance2 = max(dot(delta, delta), 4.0);
    float3 L = delta * rsqrt(distance2);
    float3 toSign = -L;
    float axial = dot(toSign, _FurnitureRetroForward.xyz);
    float3 right = cross(_FurnitureRetroUp.xyz, _FurnitureRetroForward.xyz);
    float horizontal = abs(dot(toSign, right)) / max(axial, 0.001);
    float signedHorizontal = dot(toSign, right) / max(axial, 0.001);
    float vertical = dot(toSign, _FurnitureRetroUp.xyz) / max(axial, 0.001);
    // Horizontal beam 15..25 degrees. Vertical upper cut is wider on high beam.
    float beam = (1.0 - smoothstep(0.26795, 0.46631, horizontal)) * step(0.0, axial);
    float upperInner = lerp(0.01, 0.08, highBeam);
    float upperOuter = lerp(0.025, 0.16, highBeam);
    // Right-hand-traffic asymmetric low beam: qualitative 15-degree upsweep on a beam screen.
    // Working approximation, not a measured/approved lamp photometry; high beam keeps its own lobe.
    float rightUpsweep = (1.0 - highBeam) * min(max(signedHorizontal, 0.0) * 0.267949, 0.06);
    upperInner += rightUpsweep;
    upperOuter += rightUpsweep;
    beam *= smoothstep(-0.15, -0.05, vertical) * (1.0 - smoothstep(upperInner, upperOuter, vertical));
    // 1-cos(angle), avoiding acos. Roughly a two-degree working observation lobe.
    float observation = max(0.0, 1.0 - dot(L, viewWS));
    float angular = rcp(1.0 + observation / 0.00060917);
    float entrance = saturate(dot(normalWS, L));
    return source.w * beam * angular * angular * entrance / distance2;
}

half3 FurnitureReturnedLight(float3 positionWS, half3 normalWS, half3 viewWS)
{
    // Uniform branch: no source, disabled lamps, disabled data or distant truck => exactly zero.
    if (_FurnitureRetroState.x <= 0.0) return half3(0, 0, 0);
    float3 activeHead = _FurnitureRetroHead0.w > 0.0 ? _FurnitureRetroHead0.xyz : _FurnitureRetroHead2.xyz;
    float3 delta = positionWS - activeHead;
    if (dot(delta, delta) > 22500.0) return half3(0, 0, 0);
    float response = 0.5 * (FurnitureHeadReturn(_FurnitureRetroHead0, positionWS, normalWS, viewWS, 0.0)
                         + FurnitureHeadReturn(_FurnitureRetroHead1, positionWS, normalWS, viewWS, 0.0)
                         + FurnitureHeadReturn(_FurnitureRetroHead2, positionWS, normalWS, viewWS, 1.0)
                         + FurnitureHeadReturn(_FurnitureRetroHead3, positionWS, normalWS, viewWS, 1.0));
    // The display coefficient is authored at reference exposure 1 (WORKING_VALUE),
    // not as a measured RA table. Follow the SAME exposed scene units as the world's sun/lamp light.
    return (half3)(_EmissionColor.rgb * response * max(_KamionExposure, 0.0));
}

void FurnitureSignFragment(
    Varyings input
    , out half4 outColor : SV_Target0
#ifdef _WRITE_RENDERING_LAYERS
    , out uint outRenderingLayers : SV_Target1
#endif
)
{
    UNITY_SETUP_INSTANCE_ID(input);
    UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);

#if defined(_PARALLAXMAP)
#if defined(REQUIRES_TANGENT_SPACE_VIEW_DIR_INTERPOLATOR)
    half3 viewDirTS = input.viewDirTS;
#else
    half3 viewDirWS = GetWorldSpaceNormalizeViewDir(input.positionWS);
    half3 viewDirTS = GetViewDirectionTangentSpace(input.tangentWS, input.normalWS, viewDirWS);
#endif
    ApplyPerPixelDisplacement(viewDirTS, input.uv);
#endif

    SurfaceData surfaceData;
    InitializeStandardLitSurfaceData(input.uv, surfaceData);

    half4 signWear = (half4)UNITY_ACCESS_INSTANCED_PROP(KamionSignProps, _KamionSignWear);
    half retroAtten = 1.0h;
    if (dot(signWear, half4(1, 1, 1, 1)) > 0.001h)
    {
        retroAtten = ApplySignWear(input.uv, signWear, surfaceData).x;
    }

#ifdef LOD_FADE_CROSSFADE
    LODFadeCrossFade(input.positionCS);
#endif

    InputData inputData;
    InitializeInputData(input, surfaceData.normalTS, inputData);
    SETUP_DEBUG_TEXTURE_DATA(inputData, UNDO_TRANSFORM_TEX(input.uv, _BaseMap));

#if defined(_DBUFFER)
    ApplyDecalToSurfaceData(input.positionCS, surfaceData, inputData);
#endif

    InitializeBakedGIData(input, inputData);

    half4 color = UniversalFragmentPBR(inputData, surfaceData);
    #if defined(_FURNITURE_RETRO)
    color.rgb += FurnitureReturnedLight(inputData.positionWS, inputData.normalWS, inputData.viewDirectionWS) * surfaceData.albedo * retroAtten;
    #endif
    color.rgb = MixFog(color.rgb, inputData.fogCoord);
    color.a = OutputAlpha(color.a, IsSurfaceTypeTransparent(_Surface));

    outColor = color;

#ifdef _WRITE_RENDERING_LAYERS
    outRenderingLayers = EncodeMeshRenderingLayer();
#endif
}

