# ADR 0061 — TRAKT front r8: welded letters, flat wipers, atlas packing that really packs, LOD2 louvres

Status: accepted for the geometry / atlas part (truck-artist, 2026-11-10); **the low-sun grille criterion is not met**
(open, see the end). Not reviewed by `visual-critic`. Source: `docs/reports/visual/REVIEW-2026-11-10-r7.md` §14 item 6
(N-1 rest, letters and wipers), E7, N-17. Continues ADR 0047 (r7b / r7c).
Evidence: `artifacts/front-r8/` (`before/` = main f9143ba rebuilt in the worktree, `final/` = this change;
`metrics_*.txt` from `tools/measure_r8.py`, `sheets/`, `checks/`, `STATUS.md`). Editor frames only, WorldC, truck-34
(+ the new `truck-front`), tiers Low / High, overcast / lowsun. No phone frame: UNVERIFIED on device.

## What was wrong (measured)
1. **TRAKT letters** were 17 bevelled stroke boxes overlapping at the joints with a 0.15-0.2 mm depth stagger: dark
   notches at every joint (share of stroke pixels darker than the stroke / bar midpoint 20-40 %), 1.2 mm chamfers far
   below a pixel, strokes 24 mm = 2.6 render pixels on Low.
2. **Wiper arms** were 16 mm eight-sided rods of satin plastic: the up-facing facets mirrored the sky and were under a
   pixel wide, the arm rendered as a row of light dots (High overcast: 85 dot components over the two arms).
3. **The atlas was never packed.** `a6_export.unwrap_atlases` edits the UVs through the mesh API (texel priority) and
   then calls `uv.pack_islands`; without a UV selection Blender 4.2 leaves the islands where smart-project put them
   (reproduced in a 40-box test). All exports up to r7c therefore had **no margin between islands**. On the Low atlas
   (512 px, ASTC 8x8; Trim 29 px/m) a louvre face was 1.5 texels, a letter stroke 2.8, a wiper arm facet 0.4-0.7: their
   albedo, roughness, AO and dirt were their neighbours'. On Low the louvre field broke into blotches (roughness
   crossing the shader's gloss-trim limit texel by texel) and the letters were mottled.
4. **LOD2 louvres**: with the top removed (r7c) each gap showed 25 mm of the dark tray, 3 px on Low; `cab_pivot` is
   dropped at LOD2 and left two dark pockets in the joint between the mask and the bumper.

## Decision
- `body._wordmark_on_face`: one welded prism per letter (EXACT union of the stroke prisms, coplanar faces merged,
  triangulated in the generator, `Mesh.validate()` so the manifest counts what the FBX round trip keeps), no chamfer,
  stroke weight 1.8 -> 2.2 (28 mm at the 150 mm cap height; `WORDMARK_WEIGHT`, WORKING_VALUE). 274 triangles, kept
  whole at every LOD (`NO_DECIMATE`).
- `body.wiper_arm` / `wiper_blade`: tapered flat strap (30 -> 22 -> 18 mm wide, 6-10 mm thick) parallel to the glass
  and a five-sided 24 mm blade; new material `wiper_black` (matt black, roughness 0.60, WORKING_VALUE). Pivots, lengths
  and the parked position are unchanged (the interior placeholder and the glass shader's sweep use the same numbers).
- `a6_export`: `uv.select_all` before `uv.pack_islands`, margin 0.002 (8 px of 4096; the old 0.004 was never applied);
  `widen_thin_islands`: islands of the letters, wipers, lane dashes, bar end caps and louvres are stretched across their
  narrow direction to 6 texels on the Low atlas (`THIN_PIECES`). Texel density (manifest): Paint 638 -> 651 px/m,
  Trim 231 -> 246, Metal 903 -> 791, Lights 1440 -> 1374 on High (Low = 1/8).
- `check_export.py`: fails when two UV islands of a baked slot overlap (polygon centre inside another island). The
  first r8 export had 3 528 such polygons before the selection fix; main (r7c) has 0, this export 0.
- LOD2: louvre faces drawn out by 30 % of their height along their slope (`GRID_FACE_EXT`, gap 25 -> ~15 mm);
  `cab_pivot` and `frame_horn` stay in LOD2. LOD2 target 17 700 -> 17 690.
- E7: mirror housings, arms, kerb and front mirror heads: `plastic_satin` (0.36) -> `mirror_plastic` (grained black,
  roughness 0.58; review r7: 0.5-0.6).
- `TruckExterior.shader`: (a) settled dust on up-facing surfaces, scaled by `_Dirt` (N-17); (b) gloss-trim reflections
  pointing steeply down (the face-down louvres) keep 0.5 instead of 0.3 of the environment: they see the road in front
  of the bumper, not street-level clutter. Both WORKING_VALUE. No new material property, no new variant.
- New control camera `truck-front` (cab front nearly head-on, 30 deg field).

## Measured (truck-34, before -> final; see `metrics_before.txt` / `metrics_final.txt` for every number)
The table is filled from the final run in `artifacts/front-r8/STATUS.md` and the hand-over report; the v4 run (same
geometry, one letter triangle set different) gave:
- letters: notch share Low 0.20-0.23 -> 0.00, High 0.32-0.40 -> 0.00-0.005; coverage IoU Low 0.48-0.56 -> 0.76-0.81,
  High 0.57-0.59 -> 0.94-0.95;
- wipers: dot components High overcast 85 -> 20, High lowsun 42 -> 0, Low overcast 9 -> 0;
- light blotches above the bar (pixels > cowl median + 12, outside the wipers): Low overcast 103 -> 16, Low lowsun 13 -> 0;
  cab-interior pixels in the cowl band: 0 before and after;
- grille, clusters > 3 x 3 px under 5 %: Low overcast 0 -> 0, High overcast 0 -> 0, **Low lowsun 10 -> 9 (largest
  3665 -> 3344 px), High lowsun 7 -> 3**;
- roof crown pixels >= 99 % (review box), High overcast 4.8 % -> 1.8 %;
- triangles LOD0 103 161 -> 102 729, LOD1 43 000 -> 42 999, LOD2 17 699 -> 17 690; draw calls unchanged (same parts and
  slots; no new material). `check_export.py` PASS; `front_leak.py` LOD0 / LOD1 PASS, LOD2 the one ray of r7b / r7c;
  EditMode 146 / 146.

## Open
1. **Low lowsun grille: not met.** After the atlas fix the louvre field is regular bands, but the faces sit at 5.4 %
   (p5 3.9 %), the gaps lower. Raising the gloss trim's albedo (dust haze 0.018 -> 0.031) changed nothing measurable
   and was taken out; the steep-down reflection change gave +0.7 point on Low and nothing on High (not understood:
   UNVERIFIED which term carries the louvre luminance on High). Low writes plain sRGB while High goes through the D23
   curve (black floor 1.5 %, toe): the same linear value is ~1.2 points lower on Low (`KamionToeParity.hlsl` does this
   for the cab view only). A toe for the exterior on the no-post tiers, or a debug pass of the gloss-trim terms, is a
   rendering decision.
2. N-17: the rest of the roof clip is the D23 white clip at 0.7 (`LookGrading`: "lit white paint reaches 100 %"). More
   dust would turn the roof grey.
3. E7 is a material change only; the housing from the seat (`cab-dash`, `cab-left`) was not measured.
4. `truck-front` has no "before" frame with the final camera position.
5. No phone frame, no `visual-critic` review.
