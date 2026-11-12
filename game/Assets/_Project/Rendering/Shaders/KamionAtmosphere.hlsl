// World atmosphere and look globals (ADR 0080, Game.Rendering.WorldAtmosphere). No keywords: everything is gated by
// uniforms whose unset value (0) means "off", so scenes without EnvironmentLighting render as before minus Unity fog.
//
// 1. Aerial perspective: Beer-Lambert extinction with the horizon in-scatter colour (as before, Koschmieder from the
//    preset's visibility) plus a ground haze layer whose density falls off exponentially with height:
//        sigma(y) = beta * (1 + a * exp(-(y - y0) / H))
//    integrated analytically along the view ray. The optical depth is evaluated per vertex (linear in view depth on a
//    flat triangle, like URP's ComputeFogFactor) and exponentiated per pixel: the same fragment cost as MixFog (one exp,
//    one lerp).
// 2. Tone toe for the tiers without post-processing (Low): c' = g c (c + (1 - s) p) / (c + p), the contrast variant of
//    LookGrading.Toe. The post tiers get the same function through the grading LUT (master curve) and leave s = 0 here.
// 3. Wet surfaces: _KamionWet (x wetness 0..1, y puddle share 0..1) for KamionWetSurface (World PBR / World Surface).
#ifndef KAMION_ATMOSPHERE_INCLUDED
#define KAMION_ATMOSPHERE_INCLUDED

float4 _KamionHaze;        // x beta (1/m), y ground-layer factor a, z 1 / H (1/m), w layer base height y0 (world)
float4 _KamionHazeColor;   // rgb exposed in-scatter colour (horizon)
float4 _KamionTone;        // x toe strength s (0 = off), y p, z g - 1
float4 _KamionWet;         // x wetness, y puddle share, z grass variation strength; w optional film floor (0 = legacy 0.52)

// Optical depth from the camera to a world position; viewDepth = positionCS.w of a perspective camera.
half KamionFogTau(float3 pw, float viewDepth)
{
    float hc = max((_WorldSpaceCameraPos.y - _KamionHaze.w) * _KamionHaze.z, -1.0);
    float hp = max((pw.y - _KamionHaze.w) * _KamionHaze.z, -1.0);
    float dh = hp - hc;
    float ec = exp(-hc);
    // mean of exp(-h) along the ray: (e^-hc - e^-hp) / (hp - hc)
    float m = abs(dh) > 0.02 ? (ec - exp(-hp)) / dh : ec;
    return (half)(_KamionHaze.x * max(viewDepth, 0.0) * (1.0 + _KamionHaze.y * m));
}

half3 KamionTone(half3 c)
{
    half3 k = 1.0h - (half)_KamionTone.x * (half)_KamionTone.y / (c + (half)_KamionTone.y + 1e-4h);
    return c * k * (1.0h + (half)_KamionTone.z);
}

// Replaces MixFog(color, fogFactor): fogFactor carries KamionFogTau.
half3 KamionMixFog(half3 c, half tau)
{
    c = lerp(_KamionHazeColor.rgb, c, exp(-tau));
    return KamionTone(c);
}

// Rain-wet surface (parameter, not weather simulation): water in the pores darkens rough materials (asphalt, concrete,
// paving: albedo x 0.55-0.75, Lekner and Dorf 1988 give ~0.5-0.7 for wet soil / asphalt, WORKING_VALUE), a water film
// raises the smoothness of up-facing faces, and standing water fills the low spots (pool: 0..1 from the macro map).
// Walls take a third of the effect (driven rain). No effect when _KamionWet.x = 0 (one uniform branch).
void KamionWetSurface(half3 n, half pool, half puddles, half film, inout half3 albedo, inout half smooth, inout half3 tn)
{
    if (_KamionWet.x <= 0.001) return;
    half up = saturate(n.y * 2.5h - 1.25h);
    half w = (half)_KamionWet.x * lerp(0.33h, 1.0h, up);
    half porous = saturate(1.0h - smooth * 1.6h);
    albedo *= lerp(1.0h, lerp(0.82h, 0.58h, porous), w * lerp(0.4h, 1.0h, film));
    half filmFloor = _KamionWet.w > 0.0 ? (half)_KamionWet.w : 0.52h;
    smooth = lerp(smooth, max(smooth, filmFloor), w * up * film);   // film: 1 paved, ~0.15 grass / soil (no water sheet)
    half t = 1.0h - (half)_KamionWet.y * (half)_KamionWet.x;
    half pud = smoothstep(t, t + 0.05h, pool) * up * puddles;
    smooth = lerp(smooth, 0.96h, pud);
    albedo *= 1.0h - 0.25h * pud;
    tn = normalize(lerp(tn, half3(0.0h, 0.0h, 1.0h), pud * 0.92h));
}

#endif
