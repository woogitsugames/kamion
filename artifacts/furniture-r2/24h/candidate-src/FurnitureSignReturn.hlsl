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
