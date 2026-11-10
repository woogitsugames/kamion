# ADR 0047 — TRAKT modern front (`modern` cab variant), 1.5° front rake, honest front overhang

Status: accepted (2026-11-10, owner decisions D28 / D29)

## Context
Owner review of the B2 cab and of the rounding proposal: "still reads as a 1990s truck" (boxy grille, slab bumper, flat
sides) -> "nowy front, nowoczesny, od zera"; after proposal 1: "z profilu zbyt duży kąt" -> 1.5° chosen from the
7° / 3° / 1.5° sheet (`docs/reports/visual/truck-A6-exterior/modern-front/modern_rake.jpg`). Press photos of a current
European premium tractor were shown as a reference for proportion, roundness and surface quality only (CLAUDE.md rule 8).

## Decision
1. `tools/blender/truck/exterior/body.py`: `DEFAULT_SHAPE = "modern"` (`set_shape(name, rake)`; `b2` and `round` stay
   selectable with `build.py --shape`, they are no longer exported).
2. TRAKT language (own, fictional): gloss-black road-T mask (T bar under the windscreen wrapping the corners with the
   glass, tapered louvred stem through the bumper to the plate, brushed-aluminium lane-line dashes on the centreline),
   slim wrap-round LED lamps low in the R 0.38 m corner panels (one light-guide line + amber strip), one-volume bumper
   with a rolled chin, slim fog slots and a step slot, bulged visor, larger roof radii with tumblehome, body-colour
   rear roof spoiler, one aero mirror housing per side (class II + IV glass; class V kerb and class VI front mirror
   kept: the game's mirror contract is unchanged), body-colour arch flares, dark sill cladding with a kick-up line.
   Not used: lamp brows, stepped multi-bar signatures, badge styles or roof-lamp pods of any real maker.
3. Front plane: one plane in side view, 1.5° from vertical, plan crown R 10 m. The plane sits 0.08 m further back
   than B2 (`SHAPE_FACE_Y0`), frame horns and the cab tilt pivot move with it (y 1.42 -> 1.34 m).
4. `art-source/truck/dims.json` stays the single source of truth (ADR 0014): `front_overhang_m` 1.45 m is kept and is
   now true for the model (front-most body point 1.443 m; B2 measured 1.563 m, i.e. its combination was really
   16.58 m). `artic_length_m` 16.47 m unchanged. New key `roof_spoiler_top_m` 3.86 m (highest point; the roof skin
   stays `overall_height_m` 3.75 m, which the generators use as the roof plane). All new shape values: WORKING_VALUE.

## Consequences
- Interfaces regenerated from the generator: `door_interface.json` (door front shut line / side-glass front edge
  move rearward at the A-pillar because of the R 0.34-0.38 corner), `glass_interface.json`
  (`rake_deg_from_vertical` 1.5, shell sections with tumblehome). The interior reads both files; no hand edits.
- Exterior export (2026-11-10): LOD0 102 910 / LOD1 42 998 / LOD2 15 299 triangles (limits 140k / 45k / 15.5k,
  24-segment wheels at LOD2 per ADR 0039), `exterior/check_export.py` PASS. LOD2 keeps >= 30 % of the door shell
  (`MIN_RATIO`): below that the window opening collapsed down to the sill.
- Interior re-exported against the new interfaces: LOD0 92 991 / LOD1 42 009 / LOD2 21 850 (`wheel_stitch` dropped at
  LOD2: the larger glazing hides fewer faces), `interior/check_export.py` PASS, `sightline_test.py` PASS,
  `check_fit.py` PASS (29 vertices outside = 0.124 %, 0 in the glass zone).
- Known cost: the side-glass front edge sits ~0.24 m further back at the belt line, so the A-pillar / corner panel
  hides more of the near-side view than B2 did (not quantified here; `build.py --vis` gives the visibility map).
- dims sync 9/9, physics runner 147/147 (no physics value changed).
- Phone cost not measured in this task (no device): `UNVERIFIED`; LOD budgets are unchanged.
- Evidence: `docs/reports/visual/truck-A6-exterior/` (export QA renders, `fit_*.jpg`, `modern-front/`).
