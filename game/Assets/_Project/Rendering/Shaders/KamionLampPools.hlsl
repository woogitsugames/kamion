// Analytic street-lamp pools at dusk (ADR 0062, review r8 N-20), shared by Kamion/World Surface and Kamion/World PBR.
// StreetLamps sends the lamp heads nearest a focus 30 m ahead of the camera: _KamionLampPos[i] = (head xyz, fade weight),
// _KamionLampCount, _KamionLampColor = I·k/π (exposed units; Unity's Lambert has no 1/π). Inverse-square Lambert with a
// full-cutoff luminaire (constant to 60° from the nadir, zero at 75°) and URP's smooth range window (35 m). A uniform
// branch + loop, no variants, no lights, no shadows. Returns the irradiance to multiply with the diffuse albedo.
#ifndef KAMION_LAMP_POOLS_INCLUDED
#define KAMION_LAMP_POOLS_INCLUDED

float _KamionLampCount;
float4 _KamionLampColor;
float4 _KamionLampPos[8];
float _KamionHeadlampOn;
float4 _KamionHeadlampLeft, _KamionHeadlampRight, _KamionHeadlampAxisRight, _KamionHeadlampUp,
    _KamionHeadlampForward, _KamionHeadlampColor;

// ADR 0108 r2: approximate diffuse dipped-beam lobe, actual source anchors. Beam slope/cutoff/peak are
// WORKING_VALUE rather than a calibrated optical distribution. Uniform opt-in branch: no new pass or light.
float KamionHeadlampCone(float3 positionWS, half3 normal, float3 source)
{
    float3 ray = positionWS-source;
    float forward = dot(ray, _KamionHeadlampForward.xyz);
    if (forward <= 0.0 || forward >= 90.0) return 0.0;
    float invForward = rcp(max(forward, 1.0));
    float horizontalSlope = dot(ray, _KamionHeadlampAxisRight.xyz)*invForward;
    float verticalSlope = dot(ray, _KamionHeadlampUp.xyz)*invForward;
    float horizontal = saturate(1.0-abs(horizontalSlope)/0.35);
    float cutoff = saturate((-0.002-verticalSlope)*250.0);
    float lower = saturate((verticalSlope+0.14)/0.10);
    float d2 = max(dot(ray, ray), 1.0);
    float rangeWindow = saturate(1.0-d2*d2/(8100.0*8100.0));
    return horizontal*horizontal*cutoff*lower*rangeWindow*rangeWindow*
        saturate(dot(normal, -ray*rsqrt(d2)))/d2;
}

half3 KamionLampPools(float3 positionWS, half3 n)
{
    float pool = 0.0;
    if (_KamionLampCount > 0.5)
    {
        int lampCount = (int)_KamionLampCount;
        for (int li = 0; li < 8; li++)
        {
            if (li >= lampCount) break;
            float4 lp = _KamionLampPos[li];
            float3 dv = lp.xyz - positionWS;
            float d2 = max(dot(dv, dv), 1.0);
            float3 l = dv * rsqrt(d2);
            // l.y = cos of the angle from the luminaire's nadir: full to 60° (0.5), cut off at 75° (0.2588).
            float shape = saturate((l.y - 0.2588) * 4.1356);
            float win = saturate(1.0 - (d2 * d2) * 6.664e-7);   // (1 - (d/35)^4)^2
            pool += lp.w * shape * win * win * saturate(dot(n, l)) / d2;
        }
    }
    float3 lighting = _KamionLampColor.rgb * pool;
    if (_KamionHeadlampOn > 0.5)
        lighting += _KamionHeadlampColor.rgb *
            (KamionHeadlampCone(positionWS, n, _KamionHeadlampLeft.xyz)+
             KamionHeadlampCone(positionWS, n, _KamionHeadlampRight.xyz));
    return (half3)lighting;
}

#endif
