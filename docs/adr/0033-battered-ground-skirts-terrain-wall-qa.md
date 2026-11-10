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

## Addendum (v3.5.1): the actual Andersa wall
The battered skirt did not change the `driver-andersa-to-putry` frame. A ray cast of the pixel band against the
generated GLBs hit `road / verge_grass` with normal (−0.50, −0.61, 0.61): a 52° grass face, not a skirt and not the
terrain. Two causes in the rural ditch profile:
4. Inside a curve `_emit_strip` squeezes the side profile horizontally (fold protection) but kept the depths, so the
   0.6 m ditch steepened from 1:1.5 to ~1:0.8. Rural / rural-median stations now scale their depths with the same
   factor (shallower ditch, slopes kept); the bottom skirt keeps its full depth.
5. The ditch back slope used a run of `(d + z1)·1.5` with `z1 < 0` (rise `d − z1`): 1:1.2 everywhere. Now
   `(d − z1)·1.5`; the rural side profile is ~0.2 m wider (cross-section width only; carriageway, kerbs and the
   ADR 0018 longitudinal profile / route corridor unchanged).
6. The QA also flags grass / gravel faces steeper than ~1:1.33 with > 0.15 m height (`steep_grass`), and no longer
   counts skirt vertices whose 4 surrounding nodes are covered by other ground surfaces (buried skirts).
   The test is a ratchet: per-category counts may not rise above the last build (103 points on 2026-11-10:
   85 junction skirts, 10 yard skirts, 8 steep verge faces) and no new category may appear. Target 0.

## Consequences
- Verge skirt triangles count is unchanged (same strip, moved vertices); GPU cost on Low: zero extra samples and
  draws, a few % more skirt overdraw where it is visible (estimate, UNVERIFIED on the A16).
- Open: streaks under hall parapets and sectional door frames / bumpers at the player's start frame (W-H1 remainder),
  6×6 m concrete slabs only where BDOT10k says `beton` (Kwadrat Park yard is block paving in BDOT10k).

## Addendum (v3.5.2): junction "walls" were slivers; poles seated on the mesh surface
7. Plan-area log (`terrain_walls_qa.json` -> `skirt_area`: per source exposed face m², horizontal run, max h). 84 of the
   85 junction points (`j:<node>`) came from Delaunay fill triangles whose 3 vertices lie on one gutter line: 12-266 m
   runs, 1-3 cm wide, hidden under the kerb face. A face thinner than the threshold (2·area / longest edge < 0.15 m)
   cannot show a wall taller than 0.15 m, so the QA skips it (`thin_steep_faces_skipped`, 130 faces on 2026-11-10).
   The same rule removed 5 yard-edge points (8 -> 3 concrete). Ratchet 103 -> 14: 1 junction, 6 yard skirts,
   8 steep verge faces. Open: `j:n1847044961` (Rondo Putry, e -578 n 85): a 23 m fill triangle 0.16 m thick along a
   gutter with a vertical curve (a 0.14 m fin / dip at the kerb); an inner point ring for the Delaunay fill did not
   remove it and was reverted (route patch tessellation unchanged).
8. Ground-standing poles (lamps, signal poles / masts, sign posts, power poles) are seated on the exact top of the
   generated ground meshes (road + paved layers: carriageway, kerb top, island top, apron, footway, verge, yard;
   `streetscape.furniture.SurfaceTop`) instead of the 1 m raster, lowest of the centre + 4 footing points at the
   family's footing radius (lamp 0.25 m, sign post 0.04 m), the axis at most 0.40 m below the centre surface
   (`SEAT_MAX_BURY`, WORKING_VALUE), never above the collision surface there (or the terrain collider where only a
   visual verge ribbon covers the point). Footing steps > 5 cm are logged (`streetscape_qa.json` -> `pole_footing_steps`).
   The sign post prototype embeds 0.1 instead of 0.3 of its unit height: instances scale z by the post height
   (`sz` 3-5), so the old embed put the bottom 1.1-1.5 m under the base and the audit read the A-7 / C-12 / E-1 posts at
   the Bieżeństwa and Putry approaches as buried 0.85 m.
9. The gate 3 audit counts kerb colliders (`col_concrete_kerb`) as ground: kerb and raised island tops are what a
   C-9 post on a splitter island or a lamp behind the kerb stands on. Offenders are listed up to 6 per prototype
   (the 60 largest were all plates / signal heads exempt by design, hiding the lamps).
