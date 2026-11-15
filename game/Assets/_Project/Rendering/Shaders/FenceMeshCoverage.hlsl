// Welded panel fence mesh (ADR 0239): coverage of the alpha-tested wire texture, energy-conserving with distance.
//
// Problem (BACKLOG B-082, REVIEW-2026-11-14-s20-0185 P1-3): a 5 mm wire every 50 mm is narrower than a pixel from ~4 m
// (A16 Low: 810 px over 60 deg -> 1.4 mrad / px). A fixed cutoff then has two wrong answers:
//   - coverage-preserving mips keep ~15 % of the texels above the cutoff at every mip -> blobs that beat against the
//     pixel grid (white moire lattice at 40 m, review 0179 P11-094);
//   - plain box mips: the mean alpha (~0.15) is below the cutoff everywhere -> the mesh is gone from ~10 m, posts only.
// What a camera sees there is neither: the wires average into a veil that covers ~15 % of each pixel.
//
// Here: the texture keeps PLAIN box mips (mean alpha of a mip texel = share of it the wire covers, UV0 in metres) and
//   near  (pixel footprint on the fence < FADE_NEAR_M): the classic sharp cutoff, as URP Lit (wires are resolved);
//   far   (footprint > FADE_FAR_M): alpha is the coverage. It is spent on a fixed screen-space noise so that the mean
//         over neighbouring pixels equals alpha: without MSAA whole pixels (alpha >= noise), with alpha-to-coverage
//         (all tiers run MSAA 2x/4x) in half-pixel steps - alpha out is 0, 0.5 or 1, the three values every
//         alpha-to-coverage implementation maps the same way at 2x and 4x.
// No time term in the noise: there is no temporal AA on any tier, a changing pattern would flicker.
// Constants are WORKING_VALUE (derived from the 3 texel = 5.9 mm wire of fence_mesh.png, not yet seen on the phone)
// and are mirrored in Game.Rendering.FenceMeshCoverage (EditMode test FenceMeshCoverageTests).
#ifndef KAMION_FENCE_MESH_COVERAGE_INCLUDED
#define KAMION_FENCE_MESH_COVERAGE_INCLUDED

#define FENCE_MESH_FADE_NEAR_M 0.0033   // m of fence per pixel: the wire is still ~1.8 px wide, cutoff stays sharp
#define FENCE_MESH_FADE_FAR_M 0.0093    // the wire is ~0.6 px: box-mip peak alpha falls under the cutoff from here on
#define FENCE_MESH_FAR_GAIN 1.0         // far coverage / mean alpha (1 = physical share of the pixel)
#define FENCE_MESH_A2C_LEVELS 2.0       // coverage steps per pixel under alpha-to-coverage (0, 1/2, 1)

// Interleaved gradient noise (Jimenez 2014), uniform in [0, 1) over neighbouring pixels. pixel = SV_POSITION.xy.
float FenceMeshNoise(float2 pixel)
{
    return frac(52.9829189 * frac(dot(pixel, float2(0.06711056, 0.00583715))));
}

// 0 = sharp cutoff, 1 = coverage. uvM: fence UV in metres (TRANSFORM_TEX applied, scale 1).
half FenceMeshFade(float2 uvM)
{
    float2 dx = ddx(uvM), dy = ddy(uvM);
    float footprint = sqrt(max(dot(dx, dx), dot(dy, dy)));
    return (half)saturate((footprint - FENCE_MESH_FADE_NEAR_M) / (FENCE_MESH_FADE_FAR_M - FENCE_MESH_FADE_NEAR_M));
}

// Alpha to write (alpha-to-coverage input when a2c, else 1 for every surviving pixel); discards uncovered pixels.
// a: texture alpha * _BaseColor.a, cutoff: _Cutoff, a2c: the target is multisampled and AlphaToMask is on.
half FenceMeshAlpha(half a, half cutoff, float2 uvM, float2 pixel, bool a2c)
{
    half t = FenceMeshFade(uvM);
    half sharp = saturate((a - cutoff) / max(fwidth(a), 0.0001h) + 0.5h);
    half c = lerp(sharp, saturate(a * FENCE_MESH_FAR_GAIN), t);
    half d = (half)FenceMeshNoise(pixel);
    half alpha;
    if (a2c)
        alpha = lerp(c, min(floor(c * FENCE_MESH_A2C_LEVELS + d) / FENCE_MESH_A2C_LEVELS, 1.0h), t);
    else
        alpha = step(lerp(0.5h, max(d, 0.004h), t), c);
    clip(alpha - 0.0001h);
    return alpha;
}
#endif
