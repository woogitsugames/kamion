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
    return (half3)(_KamionLampColor.rgb * pool);
}

#endif
