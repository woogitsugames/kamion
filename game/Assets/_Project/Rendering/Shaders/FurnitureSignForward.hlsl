// URP Lit fragment scaffold: copyright Unity Technologies ApS, Unity Companion License.
// ADR0120 r2: additive analytic return, no URP lights, texture samples or new passes.
// Angle response is an uncalibrated WORKING_VALUE, not a specified sheeting class.
// The Lit UnityPerMaterial buffer remains unchanged in EVERY pass, including UsePass.
// _EmissionColor is the existing coefficient slot; _EMISSION is never compiled in our forward pass.
float4 _FurnitureRetroHead0, _FurnitureRetroHead1, _FurnitureRetroHead2, _FurnitureRetroHead3;
float4 _FurnitureRetroForward, _FurnitureRetroUp, _FurnitureRetroState;
float _KamionExposure;

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
    float vertical = dot(toSign, _FurnitureRetroUp.xyz) / max(axial, 0.001);
    // Horizontal beam 15..25 degrees. Vertical upper cut is wider on high beam.
    float beam = (1.0 - smoothstep(0.26795, 0.46631, horizontal)) * step(0.0, axial);
    float upperInner = lerp(0.01, 0.08, highBeam);
    float upperOuter = lerp(0.025, 0.16, highBeam);
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
    // The display coefficient is authored at reference exposure 1/512 (WORKING_VALUE),
    // not as a measured RA table. Follow the SAME exposed scene units as the world's sun/lamp light.
    return (half3)(_EmissionColor.rgb * response * max(_KamionExposure, 0.0) * 512.0);
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
    color.rgb += FurnitureReturnedLight(inputData.positionWS, inputData.normalWS, inputData.viewDirectionWS) * surfaceData.albedo;
    #endif
    color.rgb = MixFog(color.rgb, inputData.fogCoord);
    color.a = OutputAlpha(color.a, IsSurfaceTypeTransparent(_Surface));

    outColor = color;

#ifdef _WRITE_RENDERING_LAYERS
    outRenderingLayers = EncodeMeshRenderingLayer();
#endif
}

