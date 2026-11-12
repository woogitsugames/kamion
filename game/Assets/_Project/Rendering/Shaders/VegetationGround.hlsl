// ADR0088. Contextual ground detail; no extra samples, passes or material splits.
// R = road/yard distance /20m; G forest; B mowing/dryness; A mapped exposed ground.
#ifndef KAMION_VEGETATION_GROUND_INCLUDED
#define KAMION_VEGETATION_GROUND_INCLUDED
half3 KamionGrassDryMatter(half3 green, half4 ground, half strength)
{
    // ADR0109 candidate B: retain every photographed blade and existing tint.
    // A constant straw fill flattened the source texture (candidate A rejected).
    // B now modulates colour and brightness multiplicatively at metre scale.
    // Ratios/range are WORKING_VALUE; no added texture fetch, pass or _Tint.
    half dry = smoothstep(0.05h, 0.95h, ground.b);
    half amount = dry * 0.65h * saturate(strength);
    half3 pigment = lerp(half3(1.0h, 1.0h, 1.0h), half3(1.50h, 1.08h, 1.40h), amount);
    half gain = lerp(1.0h, 0.70h + 0.60h * dry, saturate(strength));
    return green * pigment * gain;
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
