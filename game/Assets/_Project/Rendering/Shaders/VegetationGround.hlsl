// ADR0088. Contextual ground detail; no extra samples, passes or material splits.
// R = road/yard distance /20m; G forest; B mowing/dryness; A mapped exposed ground.
#ifndef KAMION_VEGETATION_GROUND_INCLUDED
#define KAMION_VEGETATION_GROUND_INCLUDED
half3 KamionGrassDryMatter(half3 green, half4 ground, half detail, half strength, half3 linearTint)
{
    // ADR0109: metre-scale B controls a blend of living blades and straw,
    // rather than only a small hue multiplier. Linear albedo WORKING_VALUE;
    // detail comes from the caller's existing sample (no added texture fetch).
    half dry = smoothstep(0.18h, 0.92h, ground.b);
    half3 straw = half3(0.145h, 0.125h, 0.055h) * detail * linearTint;
    return lerp(green, straw, dry * 0.65h * saturate(strength));
}
half KamionGrassExposure(half4 ground)
{
    // No invented sand/salt band around maintained lawns or every paved edge.
    // Exposed industrial soil and unmanaged verge are the existing mapped contexts.
    half rough = smoothstep(0.40h, 0.85h, ground.b);
    return saturate(max(ground.a, rough * 0.55h) * (1.0h - ground.g));
}
half KamionGrassGrit(half4 ground, half patch)
{
    // Width 8..55cm = WORKING_VALUE, varying with the existing spatial macro map.
    half width = lerp(0.08h, 0.55h, saturate(patch));
    half edge = 1.0h - smoothstep(width * 0.35h, width, ground.r * 20.0h);
    return edge * KamionGrassExposure(ground) * 0.45h;
}
#endif
