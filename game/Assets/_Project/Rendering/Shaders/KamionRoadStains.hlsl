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

// ---- junction plates (_ROADWEAR). roads.meshing._patch_uv1 adds PLATE_EDGE_FLAG (20 m) to UV1.y of plate vertices
// that carry lane data; legacy data (edge <= ~12 m) is unaffected. Returns 1 on a plate and restores the edge distance.
#define KAMION_PLATE_EDGE_FLAG 20.0
#define KAMION_PLATE_WHEEL_KEEP 0.35     // WORKING_VALUE: share of the lane-locked wheel-path contrast left on a plate
#define KAMION_PLATE_DRIP_KEEP 0.4      // WORKING_VALUE: share of the lane-centre drip band left on a plate
half KamionPlateWear(inout float2 w)
{
    half plate = step(15.0, w.y);
    w.y -= KAMION_PLATE_EDGE_FLAG * plate;
    return plate;
}

// ---- yard grime follows the traffic (_GRIME on paved yards; manifest "grime_traffic"). The damp / oily pools of
// ADR 0060 were spread evenly over every yard ("ten sam brud wszędzie"). Trucks stand and manoeuvre along the walls
// (dock aprons) and water / fines collect at the edges; the open middle of a yard is swept dry by traffic and wind.
// Paved UV1 = (distance to the area edge m, distance to a building wall m), capped at 50 m (streetscape.paved).
// traffic: x threshold raise in the open (cleaner), y threshold drop where busy (damper), z wall zone m, w 1 = on.
// Returns the offset added to the pool threshold; meshes without UV1 (0, 0) and materials without data: 0.
half KamionYardGrimeBias(float4 traffic, float2 uv1)
{
    if (traffic.w < 0.5 || (uv1.x <= 0.0 && uv1.y <= 0.0)) return 0.0h;
    half nearWall = 1.0h - smoothstep(traffic.z * 0.3, traffic.z, uv1.y);
    half nearEdge = 1.0h - smoothstep(0.3, 2.5, uv1.x);
    half busy = max(nearWall, nearEdge);
    return (half)traffic.x * (1.0h - busy) - (half)traffic.y * busy;
}

#endif
