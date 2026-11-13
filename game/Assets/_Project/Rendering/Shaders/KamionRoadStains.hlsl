// ADR 0194: road stains and traffic wear (oil, repair patches, ruts). Kept in its own file so the shading code of
// Kamion/World PBR (lamp pools, ADR 0062/0191) and this surface-appearance code do not touch the same lines.
// Every function is opt-in per material (vector = 0 -> exact legacy result) so a reimport stays idempotent.
#ifndef KAMION_ROAD_STAINS_INCLUDED
#define KAMION_ROAD_STAINS_INCLUDED

// ---- oil stain (decal_oil, _DECAL_ALPHA). REVIEW s19-0179 P2: the stains read as LIGHT blurred splats. Cause
// (measured on the atlas): albedo is near-black (0.018 linear) but Mask.A = 0.48-0.52 in the stain cores and the decal
// normal is flat, so at the driver's grazing angle the overcast sky's mirror reflection outshines the matt asphalt
// (smoothness 0.09) next to it. Oil soaked into a porous wearing course stays nearly as rough as the asphalt; only the
// fresh film is a little glossier.
// look: x smoothness of an old (absorbed) stain, y smoothness of the freshest film, z coverage gamma (< 1 = denser
// core, crisper rim: the atlas alpha is a soft radial ramp), w = 1 on. WORKING_VALUE (ADR 0194).
void KamionOilStain(float4 look, half atlasSmooth, inout half smooth, inout half alpha)
{
    if (look.w < 0.5) return;
    // the atlas smoothness encodes freshness (cores 0.5, aged rims 0.2) -> remap into [x, y]
    half fresh = saturate((atlasSmooth - 0.2h) / 0.32h);
    smooth = lerp((half)look.x, (half)look.y, fresh);
    alpha = pow(saturate(alpha), (half)look.z);
}

#endif
