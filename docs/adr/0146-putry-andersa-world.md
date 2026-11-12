# ADR 0146 — G3-B world fixes: Putry deck lamps and verge, Andersa SE ramp level (810896), portal follow-ups

Status: DRAFT on branch `putry-andersa` (base main `1b002a730`, 2026-11-12, s14); not merged. Validation section is
filled in after the build / import / renders. A visual-critic review is required.
Source: ADR 0143 "World findings" 1-3, `docs/reports/visual/REVIEW-2026-11-12-s14-0133.md` P2-4..7,
`docs/reports/visual/REVIEW-2026-11-12-s14-0139.md` P1-1, P2-2..5 (lead request, s14).

## 1. Median lamps of the DK8 decks over Rondo Putry (frame 494288258686575)

### Question
ADR 0143: with the pose fitted on the lamp ladder the photo's heads are "only ~6 m above the eye", arms ~2.6 m,
while the generated 12 m columns stand on the deck (console on the fascia): 3.5-5 m too high. Columns of 12 m on the
ground under the gap, or short columns on the deck?

### Data (measured; tools in `artifacts/putry-andersa/tools`, crops in `artifacts/putry-andersa/look`)

| What | Value | How |
|---|---|---|
| Where the column stands | **on the ground in the gap** | GUGiK 0.08 m, column 9 (E -502.2 N -27.3, `z_p9.jpg`, `zz_p9a.jpg`): the pole shadow starts at the base on the gravel of the gap floor and runs 7.7 m on it to the foot of the NE deck; column 8 the same. The base is in the middle of the 4.2 m gap, not at a fascia (a console would be 2 m long) |
| Gap floor below the deck | 4.9-6.2 m | NMT 1 m under the gap vs the generated deck (columns 5-10) |
| Luminaire height above the deck, from shadows | 10.0-10.7 m | luminaire shadow on the NE deck 11.3 m from the luminaire image (`zz_p9a.jpg`); sun 1.05-1.13 m of shadow per m (car roof shadow 1.0 m on `z_p1.jpg`: 1.07; UNVERIFIED +-15 %). Ground column 1 (E -759.9 N 63.5): fork shadow 10.8 m -> fork 9.6-10.3 m, + rise 1.0 m |
| Arm geometry | tips 3.4-4.0 m apart incl. the 0.65 m housings, rise ~1.0 m | orthophoto column 1 (arm images 3.96 m, arm shadows consistent with reach 1.9 m and rise 1.0 m), columns 8 / 9: 3.3 / 2.8-3.0 m |
| Focal length of photo 494288 | **1900 +-120 px of 2048** (vfov 44 deg) | lane-dash module on the deck 5.57 m (orthophoto, 8 modules = 44.6 m) vs dash rows on the photo (starts 162 / 109.6 / 82 / 66.8 px below the road vanishing point): eye height x focal = 1899 px m; eye height 1.0 m from the lane (dash -> edge line 3.49 x eye height, lane 3.50 m on the orthophoto) |
| Luminaire height above the deck, from the photo | 10.0 m | lamp 1 at 39.7 m (ladder ratios 1 : 1.88 : 2.86 : 3.9, pitch 34.8 m), head 431 px above the vanishing point -> 9.0 m above the eye; arm tips 173 px -> 3.6 m (orthophoto 3.4-4.0 m) |

The Mapillary SfM focal length of this frame (1.27 x width = 2602 px, vfov 32.9 deg, used by `sbs_cameras.json`) does
not fit the frame: it needs an eye height of 0.73 m and gives arms of 2.6 m. With it every angular size in the render
is 1.37 x the photo's, which is the "3.5-5 m too high" of ADR 0143.

### Decision
- The columns between the decks are **masts on the ground under the viaduct**, luminaires `LAMP_Y_H_M` = 10.3 m above
  the road (WORKING_VALUE, 9.4-11.3 m): prototype `lamp_double_mast_10m` (origin at deck level, shaft 7.5 m below
  it), placed at the measured point (no console, no move to the fascia). On the grass median: `lamp_double_10m`.
  The generated heads come down 1.7 m (12.0 -> 10.3 m), not 3.5-5 m.
- Arms: arcs (quarter ellipse, vertical at the column, flat at the housing), reach 1.3 m + housing = 1.95 m, rise
  1.0 m. Low mesh (LOD1): arm radius 0.06 m (`LAMP_Y_ARM_R_LOD1`), 3 arc sections.
- Row continued by 4 columns on the grass median to the median opening at the fire station (E -368.3 N -136.1 ...
  E -282.0 N -201.7; spacing 36-37 m; cells c_04_07 .. c_05_06 were already fetched, ADR 0133 only mosaicked two
  rows). Rule lamps of ways 284022563, 606396460, 560802655, 266084693 within 18 m of the row are replaced too.
  South-east of E -282 the rule lamps stay (UNVERIFIED).
- 18 m removal radius: it only removes rule lamps of the named ways (source prefix), so the lamps of the link road
  under / beside the deck (way 173956083, at E -473.6 N -3.5 etc.) are not touched.
- **For the pose stream (not changed here):** `sbs_cameras.json` / `sbs_references.json` of 494288 should use
  focal 0.93 x width (vfov 44.0 deg) and eye 1.0 m; probe `sbs-p146-494288-native`
  (`artifacts/putry-andersa/data/probe_cameras.json`), rendered below.

## 2. Right verge of the NW-bound deck (494288)

Photo, measured from the road vanishing point with eye 1.0 m: edge line centre -> kerb face 0.4 m; red-brown coated
cap; barrier posts ~0.75 m behind the kerb face; screen ~0.5 m behind the posts (kerb face -> screen ~1.3 m).
Orthophoto: 1.1 m from the edge line to the barrier; the caps on the median side are red. Generated: light concrete
cap 1.5 m, posts 1.25 m and screen 1.65 m behind the kerb face.
The screen height (3.0 m) fits the photo once the focal length is right (post 2.5-2.8 m above the barrier foot);
the "dark plinth" is the lower rails of the steel barrier in front of the glass.

Decision (`bridge_style` of `andersa-viaduct-putry-style`, WORKING_VALUE): `cap_w: 1.2`, `cap_mat: bridge_fascia_red`
(existing material, no new one), `barrier_face_m: 0.70`, `ramp_fascia: red` (Mapillary 810525063224609 /
209622370971977: fascia green on the spans, red on top of the block-faced ramp walls), screen posts as H-sections
(road-side flange 0.22 m + web; 20 triangles per post instead of 10).

## 3. Andersa SE of Rondo Putry (810896133189484, G3-B station ~245 m)

Cause: OSM tags both carriageways `layer=1` from the viaduct down to the junction at E -340, so their NMT samples
carry no weight (`profile.elevated`) and each carriageway got its own smooth descent between the deck and its end
node. At E -395 the NW-bound carriageway (way 1101181473) was at 134.5 m, the SE-bound one (way 173956078) at
132.6 m; with cap and barrier that is the 3-4 m wall in the frame. NMT across both at E -396: 131.7-132.1 m.
Photo: both carriageways level, grass median with a guardrail. Orthophoto: grass median with the lamp columns from
the abutment (E -462) on; the shadow of the NE screen narrows from 2.4 m at the abutment to 0.7 m at E -382.

Decision:
- `Data/Regions/bialystok-industrial-c/profile_ties.json` (authored_override in its own file):
  `dk8-putry-se-ramp-twin-level` - the NW-bound chain follows the solved profile of the SE-bound chain between
  E -478 N -38 and E -356 N -137 (`profile.build_profiles`, weight `ADJ_WEIGHT`), `median_fill: true`.
- `meshing.build_median_fills`: grass strip between the inner cap edges of both chains where both are walled ramps
  (80 m, 3.6-4.1 m wide, edges within 0.04 m), end walls at both ends; lamp columns 11-13 stand on it.
- The object at the right of the frame "seen from its back" is not a sign: it is the emergency signal of the fire
  station (OSM node 1847044938 `traffic_signals=emergency`, `signal_head_off`, dark at rest), facing the oncoming
  traffic. The photo's B-23 on the median lamp column (E -368 N -136) is not built: the sign atlas has no B-23 face.

## 4. Portal follow-ups (REVIEW s14-0139 P1-1 "tablice ~0,6 m za wysoko")

Cause (found on the r1 probes `p146-portal-*` and in `streetscape_qa.json`): the boards did not hang on the beam.
ADR 0127 moved the beam to the column feet read off the orthophoto (`columns_en`), the boards stayed at the chain
station of `distance_m`: board E -262.12 N -210.67 against the beam axis through (-267.0, -212.8) / (-258.6, -202.2)
= 2.46 m in front of the axis instead of 0.45 m. Seen level from the front (probe `p146-portal-front-level`) the
board covers the beam as authored (top 0.28 m above the top chord); from the driver's eye 15.2 m away (SBS pose
275528) the 2.0 m of depth read as 0.8 m of height (board top at 20.3 deg, beam top at 16.4 deg). Heights in the
generator were right all along (board centres 5.94 / 5.75 m, beam 5.5-6.1 m).

Decision: `streetscape.landmarks` projects every board of a portal onto the beam plane
(`p - travel * dot(p - ctr, travel) - travel * 0.45`); a cantilever is unchanged (its column is at the board
station). `beam_depth_m: 0.6` (the name carries decimetres, 0.55 already built `_b6`; frame: 28 px at 42 px/m).

## 5. Second round, found on the r1 pairs (anti-slop pass)

- **Cap coat.** `bridge_fascia_red` on the cap was a flat colour: sRGB R/G 1.89-2.05, cap / asphalt luminance
  1.14 (clear) / 1.44 (overcast); photo 494288 (cap in the shade of the screen, UNVERIFIED in sun) R/G ~1.4,
  luminance ~1.2. And it covered the ramp caps too, which are bare light concrete on 810896 (red wedge in the
  foreground of the r1 pair). New road material `bridge_cap_red` (concrete_precast set, colour 0.19 / 0.04 / 0.032,
  dark road film `vertex_grime` with `CAP_COAT_GRIME` 0.55 at the kerb -> 0.2), applied by `_emit_strip` only on
  span stations (`capm` = bridge and not walled). WORKING_VALUE.
- **Screen posts.** The thin H flange in `barrier_steel` showed diagonal stripes (plan-metre UV of the W-beam set).
  `screen_post_mat: noise_post` (green-grey paint, 810525 sunlit / 494288 shaded). WORKING_VALUE.
- **Mapped screen built twice.** OSM / BDOT10k map the screen of the ramp as a noise-barrier line; `noise_barriers`
  built it again as a ground barrier 0.5 m outside the ramp wall (slab section E -428 N -79: plinth 132.05 m, glass
  133.5-136.6 m, deck 135.1 m), in front of the wall and its band. `furniture.deck_screen_keepout`: mapped parts
  within 2.5 m (WORKING_VALUE) of a deck / ramp edge that carries a bridge_style screen are not built.
- **Mapped retaining wall built twice.** Same for the BDOT10k / OSM retaining-wall line of the ramp: `retaining()`
  put a 1 m concrete wall with a railing 0.5 m in front of the block wall. `furniture.ramp_wall_keepout` (2.5 m
  along both edges of walled stations, retaining walls only; fences are not cut).
- **Red band hidden.** The block facing ran to the cap top 5 mm in front of the painted band (`ramp_wall_blocks`
  to 135.24 m, `bridge_fascia_red` 134.69-135.26 m behind it). The facing now ends 0.02 m above the band bottom.

## Validation

TODO.

## Open

TODO.
