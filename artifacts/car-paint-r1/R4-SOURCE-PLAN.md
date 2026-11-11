# G R4 source and reference plan

Overall G appearance is FAIL after the independent 0089 review. Pearl upload and wheels remain accepted changes; R3 dirt is rejected. Baseline for this round is the merged main7265bd65 in G commitbc506639, not the old pre-0098 images. This plan precedes any candidate source/map regeneration. Unity remains held and D has capture priority.

## Actual coordinates and mesh evidence
Read-only r4-mesh-audit.py generated r4-mesh-audit.json: 81 source paint LOD rows (27 prototypes, 3 LODs), exact UV0=(longitudinal y, height z) metres, maximum error0; no UV1 in all81. Corrected library audit contains81 paint primitives, all without TEXCOORD_1. The initial72 count wrongly omitted nine van primitives; this was an audit filter error, not evidence of stale geometry. No geometry was written by the audit.

| Class | Sill m | Front / rear axle y m | Tyre / arch radius m | Nose / rear extent y m |
|---|---:|---:|---:|---:|
| Hatch | .19 | 1.25 / -1.37 | .316 / .361 | 2.13 / -2.13 |
| Sedan | .19 | 1.42 / -1.28 | .320 / .365 | 2.32 / -2.32 |
| Estate | .19 | 1.43 / -1.27 | .320 / .365 | 2.33 / -2.33 |
| SUV | .25 | 1.31 / -1.35 | .350 / .395 | 2.21 / -2.21 |
| Van | .27 | 1.52 / -1.48 | .345 / .390 | 2.45 / -2.45 |

Generator axes are right/nose/up. GLB converts position and normal to(-x,z,y); expected glTFast Unity conversion restores local(x,z,y): Unity Y is height, +Z is nose, -Z is rear. Runtime mesh/normal verification remains pending. Paint includes front/rear surfaces in every audited LOD; they are not assumed side-only. Existing UV0 remains unchanged. _UV_MESH0 uses UV0; adding a car-only UV1 payload does not select _UV_MESH1.

InstanceImporter currently keeps UV1 only when WorldPbrMaterials.Channels requests it. WorldMeshBake stores it as Float16x2, increasing native prototype stride by4 bytes per vertex, including nonpaint groups sharing that mesh. This is real extra memory, despite the existing shader uv.zw interpolant. Measure total actual native mesh bytes/descriptor before and after; current audit alone is not a memory-budget PASS.

## Bounded candidate, subject to ROOT review
1. Remove the old lower film from the existing car_grime generator maps, keeping upper dust, rain runs and peel separate. Do not reconstruct clean paint with an inverse sampled film or divide by a height envelope. Snapshot baseline maps first; regenerate only after baseline images. Confirm unchanged texture dimensions/count/sample count and document changed pixels. This source is art-source/world/materials/_src/sets_facade.py; scope confirmation requested from ROOT.
2. Add a tiny car-only export adapter after crease_normals, driven by the known prototype class. Encode UV1 height above the actual sill and a broad longitudinal deposition weight near/behind axles and the rear face. Do not edit positions, normals, UV0, indices, primitive/material groups or LOD geometry. Existing GLB UV-v conversion and importer must be tested. A source vertex adapter before crease_normals would lose alignment, so avoid it.
3. Shader deposition decreases continuously upward from the sill, with a bounded broad wheel/rear contribution and no detached top-cut band. Warm beige-grey linear albedo .20-.26 and opacity <=.5 are WORKING_VALUE candidates, not measured paint/dust reflectance. Apply consistent roughness/coat changes, preserve upper paint/bonnet. Level0 retains minimal dust. Keep the GI-relative deterministic seed and use thresholds10/35/35/20%; repeat actual GPU count, LOD and shifted-origin proof.
4. Mesh triangles can span4.926m. Do not claim detailed wheel-fan silhouettes from interpolated vertex masks or add geometry to make them. Keep the encoded envelope broad; inspect source-triangle overlays and mid-triangle samples for false seams or local detached maxima. If the sparse topology cannot support the result, return to ROOT before expanding scope.

## Reference and acceptance controls
Inspected refs/real-cars-contact.jpg at <=960px against its pinned Mapillary provenance. It supports darker black bodies, neutral wheels, lower-edge/rear road deposits, but is not a calibrated reflectance or dense close dirt reference. Proposed dust colour/opacity remain WORKING_VALUE; no exact photo albedo claim.

Fresh paired controls: r10_wheel_02 white estate side (vertical profile), r10_front_04, r10_rear_04, actual four dirt-level cars, r10b_black_05 door/bonnet plus nearby asphalt, grey/blue cars and current close wheel. Repeat clear/overcast Low/High on merged atmosphere; compare masked height bins to ensure no isolated maximum at .6-.8m and show dirt reaching sill/rear. Validate target identity and lower surfaces on fresh baseline. Native output size is not internal pipeline proof; capture actual scale packet.

Separate P2 controls: locate a valid sheet_far fleet camera without moving cars; plate repetition needs an instance-stable atlas strategy, not copied prototype variants. Inspect current atlas/UV and instanced path before proposing code. Neither is silently declared closed by the dirt change. Preserve all route59 budget comparisons and repeat relevant GIS/EditMode; A16 ALU cost remains UNVERIFIED without owner measurement.

Execution order after explicit release: canonical Truck/Trailer build -> install -> FINAL normal import -> input/192SHA/Fab and runtime camera/vehicle pose packets -> matched baseline -> small candidate/map sample -> ROOT review -> candidate captures. Both shared guards apply before every Unity launch; no automatic queued resumption.
## Inactive model revision after negative test
The first precomputed longitudinal weight failed a meaningful barycentric test on sedan LOD0: interpolation produced a spurious positive vertical weight gradient11.904/m. This candidate was rejected before activation. Approved replacement UV1 is signed height above sill and affine axle coordinate(y-rearAxle)/wheelbase. Both interpolate independently and exactly before quantization; broad triangular trails are evaluated in the fragment at axle coordinates0/1, with a bounded rear term. This adds several ALU operations, zero texture samples and no geometry; GPU cost is UNVERIFIED.

Inactive tests now cover all81 LODs and interior barycentric samples after Float16 quantization: maximum height error0.000467781m and opacity error0.000159228. Existing positions, normals, indices, UV0 and groups are byte-for-byte unchanged. Estimated additional native mesh storage584576 bytes includes every vertex group in affected meshes; actual imported descriptors and resident textures remain unmeasured. The old lower film can extend to about.966m in the specific256-resolution noise test; that is not a universal extent at every resolution.

At generator resolution1024, the optional legacy path matches every tested original field exactly; clean upper albedo/roughness above1.1m and all peel-height pixels remain exactly unchanged. Calibration uses the old gain, avoiding a whole-map brightness shift. New float32 CPU distribution on1009 actual fresh-world car/van positions is100/369/329/211 with zero mismatches across five tested origin shifts. A separate100000 exact-eighth-metre sample gives9976/35004/35077/19943, near10/35/35/20. These are CPU checks, not actual GPU or appearance PASS. Canonical R3 raw proof is192/0, Fab15/fallbackFalse; candidate source/maps remain inactive until matched BEFORE.