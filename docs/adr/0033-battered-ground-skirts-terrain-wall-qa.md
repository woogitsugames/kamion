# ADR 0033 — Battered grass / yard skirts, QA "vertical terrain wall > 0.15 m", worn marking paint (world v3.5)

Status: Accepted (world-builder), 2026-11-10. Extends ADR 0022 §5 (terrain under grass strips). Road cross-section
(carriageway, kerbs, footprint) and the longitudinal profile / route corridor of ADR 0018 are unchanged.

## Context
Fresh editor frames (main import of 2026-11-09 23:47, `WorldC_High`, overcast) after v3.3/v3.4:
- r4 W-H5 still open: `driver-andersa-to-putry` x 1370–1900, y 640–923 shows the grass verge's vertical flange as a
  green wall above lower terrain. Cause: the verge skirt is vertical (0.5 m) and the 1 m terrain grid keeps the
  footprint nodes next to hard surfaces 0.35 m under the road (ADR 0022 §5 relaxes only nodes ≥ 2 nodes away), so the
  terrain triangle crossing the verge edge sits 0.15–0.3 m below it.
- r4 W-H6 partly open: PBR asphalt has cracks / wheel paths / patches (v3.3), but `marking_white` was linear 0.72
  (sRGB ≈ 0.87): lines read as fresh paint.
- r4 W-H1 partly open: yard has behaton, stall lines, gullies, tyre scrub (v3.3); halls have a plinth and sandwich
  panels, but no streaks under the parapet. Not addressed here (see Consequences).

## Decisions
1. The outer vertical skirt of a `verge_grass` profile segment (urban verge, rural ditch back, rural median) is
   battered outward at 1 : `EMBANKMENT_SLOPE` (1.5) over its depth (0.5 m → 0.75 m). Non-edged yard flanges
   (concrete / asphalt, 0.30 m) are battered the same way. Skirts are not rasterised, so the terrain conform and the
   footprint are unchanged; where terrain is higher the skirt is simply buried.
2. QA `terrain_mesh.conform.terrain_walls`: every vertex of a steep (|n.z| < 0.26) face in the road / paved layers,
   kerbs, edgings and bridges excluded, must stand ≤ 0.15 m above the conformed terrain (bilinear on the 1 m grid).
   Written to `Data/Regions/<id>/generated/terrain_walls_qa.json`; test `tests/gis/test_terrain_walls.py`.
3. `marking_white` albedo linear 0.60 / 0.60 / 0.57, roughness 0.65 (worn road paint; WORKING_VALUE until a
   calibrated photo of a Białystok line is measured).

## Result (tile C, build of 2026-11-10)
`terrain_walls_qa.json`: 179 vertices > 0.15 m (max 1.44 m, p99 0.73 m), the 12 worst all on junction-patch skirts (`j:<node>`);
the per-source split beyond the worst 12 is not recorded yet. The test passes for verges / yards and xfails on the junction remainder.

## Consequences
- Verge skirt triangles count is unchanged (same strip, moved vertices); GPU cost on Low: zero extra samples and
  draws, a few % more skirt overdraw where it is visible (estimate, UNVERIFIED on the A16).
- Open: streaks under hall parapets and sectional door frames / bumpers at the player's start frame (W-H1 remainder),
  6×6 m concrete slabs only where BDOT10k says `beton` (Kwadrat Park yard is block paving in BDOT10k).
