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

## Revision r2 (2026-11-10, owner review of the first Unity frames)
- A-pillar: obstruction from the driver eye point (azimuth between the windscreen's clear edge and the side-glass
  front edge, z 2.25 / 2.50 / 2.75 m): B2 2.6 / 4.2 / 5.8 deg, modern r1 14.7 / 15.3 / 16.0 deg, modern r2
  4.0 / 4.6 / 5.2 deg (target <= B2 + 1 deg: met at and above eye height, +1.4 deg at 2.25 m). These are the
  exterior openings; the interior A-pillar trim (build_interior) is what the driver sees and was not re-measured. Means: windscreen wraps ~60 deg round the R 0.36 m corner
  (`ws_bottom_x` 1.25, `ws_top_x` 1.16), door glass starts 0.17 m ahead of the corner-arc centre (`win_front`).
  Right pillar (seen from the left seat) at eye height: B2 2.1 deg, r1 7.9 deg, r2 2.4 deg.
- Headlamps: lens 0.19-0.28 m tall (was 0.12-0.18), 100 mm modules, light signature = half road-T per lamp (24 mm
  bar along the top round the corner + stem down the mask side).
- Side windows: rounded corners R 0.08 m (shell opening, glass and one frame band follow the outline).
- Gloss-black mask rendered matte grey in Unity: the atlas is correct (albedo sRGB 0.10, roughness 0.16-0.20, baked
  dirt 0.00); the cause was the procedural road film of `TruckExterior.shader` (ADR 0038), weighted x1.3
  (`_GrimeChassis`) on every non-paint slot, plus the sky reflection of a smooth dielectric. Fix in the shader: gloss
  trim (baked roughness < ~0.3) keeps 25 % of the film. The remaining lift is the physical 4 % sky reflection.
- r2 exports: exterior LOD0 102 062 / LOD1 42 999 / LOD2 15 300, interior LOD0 93 345 / LOD1 42 175 / LOD2 21 906
  (`rear_lid_` dropped at LOD2); both check_export PASS, sightline PASS, check_fit PASS (12 vertices = 0.051 % outside,
  0 in the glass zone). Unity frames: `docs/reports/visual/truck-A6-exterior/modern-front/unity2/`.

## Revision r3 shader (2026-11-10, rendering review of r2)
- r2 gloss-film shed (x 0.25 below baked roughness ~0.3) now applies only above the spray band (0.5-1.1 x _GrimeHeight):
  polished tanks, chrome steps and lenses at bumper/arch height keep the full wet road spray; the mask keeps the shed.
- Black louvres read mid-grey (overcast sRGB ~50-110) although albedo (linear 0.01), roughness (0.09) and baked dirt (0)
  are correct: it is the 4 % mirror of open sky. Low's analytic cube and the High capture (no instanced trees/props) give
  open sky where near-horizon reflections of a parked truck see buildings, trees and ground. Gloss dielectric trim
  (non-paint, non-metal, roughness < 0.22-0.32) gets its own env term: Schlick F, AO, horizon occlusion and a
  near-horizon obstruction lerp(0.3, 1, smoothstep(-0.05, 0.42, R.y)) (WORKING_VALUE); URP keeps the direct light.
  truck-34 grille mean sRGB: Low overcast 51 -> 44, High overcast 60 -> 51, lowsun 25-29 -> 19-24; paint, glass, lamps
  unchanged. Cost: one extra env sample on gloss-trim pixels only (~1-2 % of the truck-34 frame); not measured on a phone.
  Evidence: artifacts/owner/modern-front/shader/. Geometry follow-up (truck-artist): louvre faces tilted face-down.

## Revision r3 (2026-11-10): what the driver really sees at the left A-pillar
- New tool `tools/blender/truck/pillar_obstruction.py`: rays from the eye point against the exported exterior LOD0 +
  interior LOD1 (glass transparent), azimuth step 0.25 deg, pitch -6 / 0 / +6 deg. Pillar wedge (contiguous blocked
  span between the windscreen and the door glass) at pitch 0: B2 11.0 deg, modern r2 16.25 deg, modern r3 7.0 deg
  (full export; all pitches in `modern-front/pillar_obstruction_r3.json`: 7.0 / 7.0 / 6.75 deg).
  The r2 "4.6 deg" was the exterior opening only; the wedge in the cab came from interior parts built for the old
  box corner: the box pillar trim, the parked windscreen curtain and grab handle beside it, the side-frit print at
  x 1.11 m (now clear glass) and the door-glass channel that the exterior fit smeared across the corner arc.
- `build_interior.py`: the pillar trim is lofted along the strip between the two glass edges (`apillar_frame`),
  62 mm deep along the sight line and 10 mm wider than the opaque strip per side; grab handle, tweeter and the
  parked curtain sit on the sight line behind it; the frit print and the door-glass channel follow the exterior
  opening / corner arc. Old interface files (no opening data) still build the A6 box pillar.
- Door-mirror housing seen from the seat: 12.5 deg (B2 11.5 deg, two separate heads) - not changed here.

## Revision r4 (2026-11-10): face-down louvres, class VI mirror that shows the ground, slimmer door-mirror head
- Louvres (5 in the mask stem + 3 in the bumper): the face is tilted 20 deg face-down (`LOUVRE_TILT`, WORKING_VALUE;
  top edge = nose with a 4 mm land, the face falls back 18 mm over its 50 mm height), so it mirrors the road and the
  dark ground instead of the sky; the lane-line dashes lie on the tilted faces. The r3 shader env term stays.
- Class VI front mirror: the old head sat above the sun visor (z 3.28 m; from the eye point the header hid it) with
  the glass tilted 35 deg up at the sky. Now it hangs in front of the top of the windscreen on the passenger side
  (centre 0.96 / 1.58 / 2.96 m, visible from the eye point through the glass), aimed with `mirror_aim`: the central
  ray from the eye reflects to the ground 1.0 m ahead of the bumper face, 0.76 m to the passenger side. Field
  requirement used for the target: UN ECE R46 class VI = ground strip from the front plane to 2.0 m ahead, from the
  driver-side plane to 2.0 m outboard of the passenger side - regulation text not opened, UNVERIFIED. The mirror
  camera frame travels in `truck_exterior_manifest.json` (`MIRROR_Front` pivot / normal / axes), regenerated.
- Door-mirror head: 0.25 x ~0.15 m -> 0.222 x ~0.115 m (glass 0.198 m wide), blades 40 x 70 mm. Obstruction from
  the eye point (`pillar_obstruction.py`, full export, pitch -6 / 0 / +6): r3 12.5 / 12.5 / 12.75 deg ->
  r4 10.75 / 11.25 / 11.25 deg (B2 11.5 deg); A-pillar wedge unchanged 7.0 / 7.0 / 6.75
  (`modern-front/pillar_obstruction_r4.json`).
- r4 export: exterior LOD0 101 592 / LOD1 43 000 / LOD2 15 297, `exterior/check_export.py` PASS. Interior not touched.
  Unity frames: `artifacts/owner/modern-front/unity4/`. Phone cost not measured: UNVERIFIED (triangle counts lower).

## Addendum r6 geometry (2026-11-10, review r6 E-N2 / E-N3 / E-N4 / E7 / T-N2 + mirror follow-ups of ADR 0042)
Frames: `artifacts/owner/modern-front/r6-geo/` (`before` = main with the r4 export, `v3` = this change; `small/` = sheets;
`geo_measure.py` = the regions, 1024 x 473 space, display luminance %). truck-34, editor, High / Low overcast.
- **E-N2 T bar corners.** `mask_bar()` replaces the flat `grille_bar` face: flat middle band (letters), top and bottom
  40 mm roll back 10 mm (top mirrors the sky, bottom the ground), 72 columns (< 3 deg per facet round the R 0.36 m
  corner), 14 mm chamfer at both wrapped ends and a 16 mm brushed-aluminium end cap (same metal as the letters and the
  lane dashes; own motif, WORKING_VALUE). `mask_gloss` albedo 0.010 -> 0.018 linear. Corner box 458-480 x 232-247:
  p50 / p99 High 7.1 / 23.7 -> 8.0 / 36.4 (target >= 8 / >= 30: met, p50 at the limit), Low 5.5 / 12.2 -> 5.5 / 34.1
  (**p50 not met**). On Low the whole bar is that dark (flat face beside the letters: 4.3 %, High 17.5 %), i.e. it is
  the Low gloss-trim environment term (analytic cube x obstruction, r3 shader), not the corner geometry: open,
  rendering-perf.
- **E-N3 louvres.** No new change: the r4 face-down louvres were not in the r6 frames (main's generated prefab was
  stale). Louvre field 390-455 x 247-283: sRGB mean High 43.2 / Low 38.6 (target <= 45), bright stripes 6.1 / 10.9 %
  (target <= 20 %). The r6 box 380-440 x 240-290 also covers the white corner panel in this frame (57.7 / 51.4).
- **E-N4 wordmark.** Letters stay geometry with a chamfer; cap height 100 -> 150 mm, stroke 1.6x -> 1.8x, wider
  spacing. Readable in truck-34 Low lowsun and Low overcast (before: "TIuKT").
- **E7 mirror back.** Door-mirror back shell: body colour -> dark grained plastic (display 69.8 -> 27.4 %).
- **T-N2 bright parallelograms under the trailer.** Not trailer geometry: the contact-shadow patch
  (`ContactShadowCaster`) was 6 flat quads spanning ~6 m across; on the crowned road their middle sank below the
  asphalt and the depth test cut holes. `Slab.columns` (tractor 3, trailer 5 x 10 rows; 0 = 2 keeps old scenes),
  trailer underside 1.00 -> 0.85 m, strength 0.85 -> 0.9 (WORKING_VALUE). Asphalt under the trailer / beside
  (655-690 x 285-291 vs 250-330 x 380-420): High 80 % -> 45 %, Low 77 % -> 41 % (target <= 50 %), max under the
  trailer 53 -> 30 % (asphalt 50 %). Raycasts per frame ~28 -> ~76: phone cost not measured, UNVERIFIED.
  The scenes need `WorldTruckInstaller.InstallBatch` to pick the new slabs up.
- **Mirrors (hand-over from the mirror task).** New tool `tools/blender/truck/mirror_visibility.py` (rays from the eye
  point to every MIRROR_* glass, exterior LOD0 + interior LOD1, glass transparent;
  `modern-front/mirror_visibility_r6.json`). Class V kerb glass: 0 % visible (line of sight ended in the passenger
  door) -> 100 %: the head moved from under the door-mirror housing (z 1.98 m) to a short stalk at the passenger
  corner, centre (1.22, 1.42, 2.20) m, seen through the wrapped lower corner of the windscreen (below 2.15 m the dash
  hides it), aimed at the ground 1.05 m outboard of the cab side. Class VI: centre 2.99 -> 2.89 m, clear of the
  folded-down passenger sun visor in `cab-mirror-front`. Passenger class II: 100 % visible in the ray test (class IV
  right 86 %, left 95 %: the cab side / door edge), no change. EditMode incl. `MirrorFieldOfVisionTests`: 107 / 107.
- Export: exterior LOD0 103 367 / LOD1 42 996 / LOD2 15 434 (r4: 101 592 / 43 000 / 15 297; +1.7 % / 0 / +0.9 %),
  `exterior/check_export.py` PASS (wheels within 2 %). `NO_DECIMATE` keeps the sill cladding and the end caps whole.
- **Open:** (1) LOD1 still shows a dark wedge across the driver-side corner panel and door
  (`docs/reports/visual/truck-A6-exterior/lod1_34przod.jpg`, already in the r4 export; not the sill cladding);
  (2) Low corner p50 (above); (3) Low lowsun corner p50 / p99 1.6 / 19.9 %; (4) no phone frame: UNVERIFIED on device;
  (5) not reviewed by `visual-critic` yet.
## Addendum r6b (2026-11-10, truck-artist): LOD1 dark wedge - root cause and fix
- **Cause.** `decimate_pieces.ratio_for` applied the per-piece floor `MIN_RATIO` only when it was *larger* than
  `lights_min`. At LOD1 `lights_min` is 0.5 and the door floor 0.30, so `door_shell_*` had no floor and collapsed
  2029 -> 402 triangles (0.2): the outer skin between the diagonal front shut line and the window folded onto the dark
  rim / inner faces. Measured against the LOD0 piece (`artifacts/owner/modern-front/r6b/lod1_diag.py`, nearest-face
  test): 0.86-0.91 m2 of 3.2 m2 per door with the wrong slot and 0.86-0.88 m2 facing backwards. Not normals, UVs or
  the sill cladding (`NO_DECIMATE` of r6 stays, it was a second, smaller effect).
- **Fix.** The floor applies on its own (`lo = max(lo, MIN_RATIO * n)`): doors 608 / 607 triangles, wrong-slot area
  0, back-facing 0.002 m2. LOD1 42 996 -> 43 000 (budget moved from other pieces, k 152.8 -> 148.6); LOD0 103 367 and
  LOD2 15 434 unchanged (their FBX and the atlases are the committed r6 files: the re-bake differs by a few pixels
  only). `exterior/check_export.py` PASS. Frames: `artifacts/owner/modern-front/r6b/lod1/lod1_34przod_{before,after}.jpg`
  (Cycles, game materials), in engine `before-ext/` vs `after-ext/` `Medium-overcast/truck-34.png` (Medium shows LOD1).
