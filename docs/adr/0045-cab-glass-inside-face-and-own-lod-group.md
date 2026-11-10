# ADR 0045 — Cab glazing: inside face at import, own LOD group with LOD0 near on every tier

Status: accepted (2026-11-10)

## Context
The sky agent (ADR 0043) found that `-NoGlass` did not change the Low `cab-dash` frame: the driver saw sky with no glass.
Measured (editor probe on the TRAKT prefab, 2026-11-10): every exterior `GLASS_*` mesh (LOD0-2) is a single sheet whose
normals all face away from the driver eye (0 of 259 windscreen LOD0 vertices face the eye; the eye ray hits a back face).
`Kamion/Truck Glass` is `Cull Back` and its header expects an inside face (normal towards `_CabCentreOS`), so the glass was
invisible from the cab on **every** tier (High cab-driver with/without `-NoGlass`: 0.0 % pixels changed), not only on Low.
On Low the LOD0 glass was additionally disabled (exterior chain = LOD2 only).

## Decision
1. `TruckAssetBuilder.DoubleSidedGlass`: at prefab build, a glass mesh with no normal facing the eye gets an inside face
   (duplicated vertices, flipped normals/tangents, reversed winding), saved to `Assets/_Generated/Truck/Meshes/*_2S.asset`.
   Self-disabling: once the exterior export ships double-sided glass nothing is added. No Blender re-export.
2. Glass leaves the exterior LOD group: own `LODGroup` (`CabBody/CabGlassLOD`), `TruckVisualRig.GlassLodsFor`: LOD0 glass
   is the near level on every tier down to max(first exterior threshold, interior cull 0.12), then the tier's exterior chain.
   Low: LOD0 > 0.12, LOD2 to cull; Medium: LOD0 > 0.18, LOD2; High: as the body.

## Cost
Glass LOD0 912 -> 1824 triangles (inside face), transparent, no shadows; only one face of the sheet survives Cull Back
per view, so overdraw is unchanged. Phone cost not measured (no device in this task): `UNVERIFIED`, expected negligible.

## Evidence
`docs/reports/visual/adr0045/` (Low cab-driver before / after / after `-NoGlass`). Low WorldC clear: cab-dash 41.5 %,
cab-driver 68.8 % pixels differ with vs without `-NoGlass` (before: 0.0 %); truck-34 exterior 0.5 % vs before.
Tests: `TruckCabGlassTierTests` (EditMode).
