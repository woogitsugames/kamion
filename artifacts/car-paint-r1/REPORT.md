# G R4 / ADR0089

R4 functional repairs and scoped visual nonregression are accepted; dust realism remains PARTIAL. The earlier R3 overall visual PASS is withdrawn. Validated branch gpt-car-paint, source bf83923a70017d3a7bb926cd4830095dfcdcf4b1.

Fresh canonical merged-source R3 baseline and R4 final each contain 92 cameras in Low/High and clear/overcast: 368 genuine pairs. All camera, vehicle, region, projection and pipeline packets match; fixtures were built/installed before the final baseline import and never rebuilt afterward.

Retained Pearl upload correction and 22-segment LOD0 wheels. Replaced detached mid-door film by affine sill/axle UV1 and monotonic warm deposition with minimal dust at level 0 and 10/35/35/20 proportions. Seven active paint materials use one car_grime_clean map set, preserving legacy upper film through Mask.R; green/beige retain legacy maps. No new texture fetch.

Plate-only Lit vertex remapping uses the existing 27-cell atlas and exact local corners on 54 LOD0/1 primitives. Native geometry, UV0, material groups and paint UV1 remain exact; plate stride stays 24 bytes. Lightmap/deferred/mixed payload fallbacks retain UV0. Load-time Lit-inspector MotionVectors reset was fixed and independently replayed.

All 368 CPU counter records and four complete stats files are unchanged, including the original 59-route controls. Paint UV1 adds an estimated 584576 bytes of native vertex payload from stride 20 -> 24 across all 81 car LOD meshes, not total allocation. Scene dependency textures increase by 3 against pinned R3 binding substitution: +170368 ASTC mip bytes projected, +1813016 desktop Profiler bytes including engine/CPU overhead; neither is measured A16 residency.

Actual instancing proves 1009 dirt identities and 18 LOD/rebase cases; opacity probe covers 4712172 pixels. Plate proof covers 260 native/LOD/common-rebase/GI-off samples with zero center-UV error. These are bounded editor diagnostics, not phone timing, whole-fleet uniqueness or executed adaptive-resolution proof.

Final High-overcast door luma is 40.9841 versus 39.8909 before; bonnet is 78.7946 versus 78.7820. Maximum bonnet change across conditions is 0.02935 display luma. Dirt reads continuously from the sill but remains smooth and subtle; rear proof covers painted body from 0.315 m, not the plastic bumper.

Full EditMode passed 274/274 with exit 0, including 8 plate tests. Full canonical PBR regeneration reproduced 443 PNG/spec files byte-for-byte. Full GIS passed 526 tests with 1 known xfail in 638.73 s (exit 0); protected source proof verifies all 192 raw hashes, 90 unchanged fixtures and Fab 15 without fallback. Evidence: r4-final-validation.json, r4-final-budget.json, r4-canonical-pbr-parity.json, r4-clean-texture-residency.json and STATUS.md.

ROOT reviewed Low 184 and E reviewed High 184 plus native/far pairs. Historical truck-facing LOD/glass and wall-occluded 45 m cameras remain invalid fleet evidence. Integration must union shared WorldPBR, materials and importer changes, then regenerate products; no main merge, push, phone/ADB or C13 work was performed.
