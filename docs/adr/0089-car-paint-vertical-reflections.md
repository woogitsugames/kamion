# ADR 0089: parked-car paint, wheels, deposition and plate variation

Status: bounded R4 repair selected after independent ROOT/E visual review; dust realism PARTIAL. Historical R3 visual acceptance is withdrawn, not a calibration reference.

Keep the earlier causal Pearl Color-property upload correction, neutral tyres/rims and 22-segment existing LOD0 wheels. No pigment/exposure lift, fourth runtime LOD or unrelated quality reduction.

Export affine signed height above the actual class sill and longitudinal axle coordinate in UV1 after normal splitting. All 81 car LOD meshes keep positions/normals/indices/UV0/groups; native stride 20 to 24 adds an estimated 584576 payload bytes, not total allocation, including nonpaint vertices sharing each stream.

Use bounded broad wheel/rear weights and exponential height decay in CARPAINT. Minimal dust at level 0; deterministic GI-relative float32 origin hash selects 10/35/35/20 levels. No detached height envelope, inverse legacy-film division, new geometry or texture sample. Deposition colour, falloff and opacity are WORKING_VALUE rather than measured albedo.

Only seven active paint materials use car_grime_clean. Preserve legacy calibration and wrap gutter; Mask.R carries removed legacy-film coverage for forward upper-role restoration, with smoothness subtraction. Green/beige stay legacy; actual metallic override remains separate. Initial un-restored bonnet +14.543% was rejected before import.

Reuse the existing plate atlas with 27 eligible cells. Add exact local plate UV1 corners to 54 LOD0/1 primitives inside the already-present stream, with unchanged UV0 fallback. One shared URP Lit forward vertex wrapper retains original fragment and auxiliary passes; no new texture, material instance or draw split. LOD2 has no plate.

Enable the local vertex keyword only after fresh-library and actual native indexed-corner validation. Reject old/mixed payloads and unsupported pipeline eligibility; shader lightmap or invalid-GI paths keep UV0. GI validity uses texel size, independently of visibility strength. No whole-fleet uniqueness claim.

Preserve LightMode-tag pass state around exact car_plate factory switches. The inherited Lit CustomEditor rewrote unknown-shader MotionVectors on load; remove that generated-only inspector association. Persisted replay proves disabled motion, Opaque queue 2000 and existing texture/ST/roughness.

Final 368 CPU records are unchanged; source adds ALU and data, not a measured GPU-time saving. Scene dependency texture union is 7 versus counterfactual R3 4: +170368 ASTC mip payload bytes; desktop Profiler delta +1813016 includes overhead. A16 residency/timing remain UNVERIFIED. Evidence and limitations: artifacts/car-paint-r1/REPORT.md, SELF-CRITICISM.md, r4-final-validation.json, r4-plate-native-parity.json and GPU proofs. Preserve canonical fixtures/pose packets; shared shader/material/importer integration requires a bounded union and canonical regeneration.
