#ifndef KAMION_WET_REFLECTIONS_INCLUDED
#define KAMION_WET_REFLECTIONS_INCLUDED
#include "KamionVehicleEnv.hlsl"
float4 _KamionWetCaptureOrigin; // xyz last actual capture point, w stable/valid and preset opt-in

// Existing environment term only. No new capture/pass. The transition shell needs two environment reads;
// the near region substitutes the existing cube read. Box-filter mips and sphere parallax are approximations.
half3 KamionWetEnvironment(half3 R, float3 positionWS, half3 n, half roughness, half occlusion)
{
    if (_KamionWetCaptureOrigin.w < 0.5 || _KamionVehicleCapture < 0.5 || _KamionWet.x <= 0.001 || n.y < 0.95 || roughness > 0.5)
        return GlossyEnvironmentReflection(R, roughness, occlusion);
    float3 offset = positionWS - _KamionWetCaptureOrigin.xyz;
    float distanceSq = dot(offset, offset);
    if (distanceSq >= 144.0) return GlossyEnvironmentReflection(R, roughness, occlusion);
    half weight = (1.0h - smoothstep(64.0, 144.0, distanceSq)) * saturate((half)_KamionWet.x * 2.0h);
    // Intersect a fixed local sphere, then look back from the actual source. No invented planar reflection.
    float b = dot(offset, R);
    float t = -b + sqrt(max(b*b + 400.0 - distanceSq, 0.0));
    half3 direction = normalize(offset + R*t);
    float alpha = (float)roughness * roughness;
    half mip = clamp(log2(max(alpha * max(_KamionVehicleEnvParams.y, 1.0) * 0.5, 1.0)), 0.0, _KamionVehicleEnvParams.x);
    half3 local = SAMPLE_TEXTURECUBE_LOD(_KamionVehicleEnvCube, sampler_KamionVehicleEnvCube, direction, mip).rgb * occlusion;
    if (weight >= 0.999h) return local;
    return lerp(GlossyEnvironmentReflection(R, roughness, occlusion), local, weight);
}
#endif
