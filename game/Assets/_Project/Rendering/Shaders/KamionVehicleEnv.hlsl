// Vehicle environment reflection (review r6 E1 / E2), shared by Kamion/Truck Exterior (clear coat) and Kamion/Truck Glass.
// Include after Lighting.hlsl.
//
// Low / Medium have no local capture: unity_SpecCube0 is the analytic SkyModel cube (EnvironmentLighting). That cube is
// direction-only and fades from the horizon colour to the ground over ~15 deg below the horizon, so a door or a pane, whose
// reflections point a few degrees down, mirrored "horizon haze" instead of the ground: no dark ground band in the paint, a
// flat milky reflection in the glass. Here the half-space below the horizon is an analytic ground plane seen from the
// shaded point's height h above the road: the reflected ray hits the ground at d = h * cos(dep) / sin(dep) and the aerial
// perspective over that distance (the scene fog extinction) blends it towards the horizon colour. A 2 m high point therefore
// sees bare ground down to ~0.1 deg below the horizon (d ~ 1 km), as a real door does. The sky half stays the cube.
// High / Ultra (VehicleReflectionCapture active, _KamionVehicleCapture = 1): the capture holds the real ground, kerbs and
// buildings already, so the cube sample is returned unchanged.
#ifndef KAMION_VEHICLE_ENV_INCLUDED
#define KAMION_VEHICLE_ENV_INCLUDED

float4 _KamionGroundEnv;      // rgb: diffuse ground radiance (exposed linear, EnvironmentLighting), a: fog extinction (1/m)
float4 _KamionHorizonEnv;     // rgb: horizon / fog colour (exposed linear), a = 1 when set
float _KamionVehicleCapture;  // 1 = the local vehicle capture is unity_SpecCube0 (High, Ultra)

// R: reflected direction (normalised). h: height of the shaded point above the road (m). Returns the specular environment
// radiance (exposed units), occlusion applied like GlossyEnvironmentReflection.
half3 KamionVehicleEnv(half3 R, float3 positionWS, half perceptualRoughness, half occlusion, float h)
{
    half3 env = GlossyEnvironmentReflection(R, positionWS, perceptualRoughness, occlusion);
    if (_KamionVehicleCapture > 0.5 || _KamionHorizonEnv.a < 0.5) return env;
    // Sky side just above the horizon (the cube is exact there): the colour the ground hazes into at large distance.
    half3 Rh = normalize(half3(R.x, 0.02, R.z));
    half3 horizon = GlossyEnvironmentReflection(Rh, positionWS, perceptualRoughness, occlusion);
    float dep = max(-(float)R.y, 1e-3);
    float dist = max(h, 0.3) * sqrt(saturate(1.0 - dep * dep)) / dep;
    half haze = 1.0 - exp(-_KamionGroundEnv.a * dist);
    half3 ground = lerp(_KamionGroundEnv.rgb * occlusion, horizon, haze);
    // Lobe width of the glossy sample in elevation (GGX: ~alpha radians), at least one cube texel (64 px, ~1.4 deg).
    half a = perceptualRoughness * perceptualRoughness;
    half w = smoothstep(-0.025 - a, 0.025 + a, R.y);
    return lerp(ground, R.y > 0.0 ? env : horizon, w);
}

#endif
