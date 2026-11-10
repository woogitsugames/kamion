# ADR 0050 - Contact shadow / ambient occlusion under parked vehicles (instanced)

Status: accepted (2026-11-10)

## Context
Parked cars, vans and the yard tractor / trailer rigs (ADR 0041) are instanced props (`WorldInstances`). They had no
contact shadow: the ground under them was lit by the full sky SH, the darkest pixels under the cars were 13-16 % luma on
`stretch-01`, the cars "floated" and the parking deck read too bright. Only LOD0 casts a real shadow (InstanceImporter
shadow mask), i.e. on Low up to 12 m (cars) / 20 m (rigs), on High up to 37 / 60 m; LOD1 / LOD2 never cast. The player's
truck has `Kamion/Contact Shadow` (ADR 0021) with a ray-cast mesh rebuilt per frame - not usable for thousands of instances.

## Decision
1. **One flat patch per contact spec** (generator `life_props.contact_quad`, node `<vehicle>.contact`, material
   `vehicle_contact`): a quad 1 cm over the instance ground plane covering the footprint + 0.7 m (cars, vans) / 1.2 m
   (tractors) / 1.6 m (trailers). `InstanceImporter` makes one prototype `contact_<spec hash>` per distinct spec (7:
   4 car bodies, van, tractor, trailer) and adds every vehicle instance to it as well; `WorldInstances` culls it with the
   vehicles (fixed 300 m, `IsVehicle`), no shadows. Cost: **+1 instanced draw per spec in view (≤ 7)**, independent of
   the vehicle prototypes / LODs in view, 2 triangles per vehicle. (First version: one more submesh on every vehicle
   LOD = +69 draws on Low `stretch-01`; rejected.)
2. **Analytic shader `Kamion/World Vehicle Contact`** (Environment/Shaders), evaluated in the instance's object space,
   so the same mesh works for every instance without per-frame work:
   - ambient occlusion = 1 - product of open fractions of 2 body slabs (floor between the sills / bumper overhangs; tractor
     cab + tanks / rails; trailer floor / axle group) and up to 4 axles of tyre contact blobs, each the 2D strip view
     factor of ADR 0021 (`F = Fx Fz`). Darkest between the wheels and under the sills, ~0.5 at the body edge,
     < 0.25 at 0.3 m and < 0.05 at 0.6 m outside a car; the patch fades out over its last 0.3 m (no outline).
   - sun: analytic visibility of the main light through the vehicle's lower box (4 heights along the ray, soft
     rectangle), for the cases where the instance casts no real shadow.
   - multiplier = [E_sky (1 - occ) + E_sun min(shadowMap, sunVis)] / [E_sky + E_sun shadowMap] at the pixel (shadow map
     sampled as in ADR 0021, queue Geometry+499). Where the shadow map already darkens the ground only the sky part is
     removed - no double darkening with the real sun shadow; where it does not (LOD1+), the analytic test removes the sun.
3. **Parameters as data**: `life_props.contact_spec(name)` (WORKING_VALUE, read off the prototype dimensions) rides on
   the `.contact` node extras of `street_props.glb`; `InstanceImporter.ContactMaterial` makes one instanced material
   per distinct spec (one body in six colours shares one asset) and every vector is written on reimport.
   The shadow map is sampled 10 cm above the patch: the instance ground plane can lie a few cm under the rendered
   ground, and a sample below the casting ground self-shadowed in stripes (acne) that the ratio turned into dark bands.
   `tests/gis/test_vehicle_contact.py` ports the fragment function to numpy and checks the profile.

## Measured
See the section added after the visual loop (artifacts `artifacts/world-fixes/cars-ao/`).

## Consequences
- Cast shadows of LOD1+ vehicles beyond the patch (long low-sun shadows onto the street) are still missing; the analytic
  sun term only covers the ground under and right beside the body (fades at the patch edge).
- Vehicles parked across a kerb: the patch lies on the instance's ground plane; where the real ground is > 8 cm above it
  (kerb top) the patch is depth-rejected there (no darkening on the kerb top).
- Phone GPU cost not measured yet (UNVERIFIED; expected well under 0.1 ms on A16 Low: ~40 ALU + 1 shadow tap per patch
  pixel, patches are small on screen).
