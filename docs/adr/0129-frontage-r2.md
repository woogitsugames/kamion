# ADR 0129 — G3-B trade frontage, round 2 (review of ADR 0126)

Status: implemented on branch `frontage-r2` (main `f30837474` merged in, 2026-11-12); not merged. Gate 3 is NOT re-judged
here (visual-critic's job).
Source: `docs/reports/visual/REVIEW-2026-11-12-s12-0126.md` (P1 oval read as a disc, P1 gate sheets #21 / #22 compare
the 2024 state with 2017 / 2020 photos, P2 black glazing / empty car lot / white mast / rigid flags / white fence),
owner decision D51 (recognisability).

## Findings (before anything was changed)

| Review item | Cause in the data / generator |
|---|---|
| Glazing of the showrooms reads black on Low | The panes used the shared `glass` material. Its `_SkyOcc.y` = 0.9 (ADR 0060) cuts 90 % of the near-horizontal reflection on purpose: a punched window "sees the street". On a 29 x 3.5 m shopfront the same rule leaves albedo 0.03 = a black field. |
| Lattice mast "jasnobiały" | It already was the galvanised `downpipe` (albedo 0.30) but with metal 0.7: under the overcast sky a metal mirrors the sky to near white (the finding ADR 0114 made for the galvanised plot fence). |
| White fence in front of the row | OSM `barrier=fence` ways 344253283 (road front of the car-showroom plot) and 913217348 (second showroom plot). The rule hashes the colour (green / anthracite / galvanised); both drew galvanised, whose alpha-clip mesh reads as a white band from the road. Photos 2020 and 2024 show a dark steel fence. |
| Oval reads as a disc | One flat one-colour ellipse, 0.08 m between its two faces, no rim. |
| Flags rigid | One quad per side. |
| No cars in front of the showroom | The lot is neither an OSM `amenity=parking` nor a BDOT10k parking polygon, so the parking rule lays out no bay. The orthophoto 2024-05-27 shows two tight rows of (mostly white) panel vans and cars SE of the building end, noses to the road. |
| Gate sheets #21 / #22 vs 2017 / 2020 photos | Open 2024 photos of exactly this approach are already in `Data/raw/mapillary/fire-station/` (strudel, 2024-08-15, CC BY-SA 4.0): 490210580292738 (GPS between the stations of #21 and #22), 469512365899192, 1020363345994649. No newer open coverage was needed (nothing downloaded). |

## Decision

1. **`showroom_glass`** (materials.py, additive): same shader and pass as `glass` (Kamion/World PBR), only parameters:
   horizon cut `_SkyOcc.y` lower than a window's, base a touch lighter and bluer. The existing fresnel / environment
   term then draws the sky as a gradient over the pane (brighter towards the head, where the reflected ray climbs).
   `frontage.plan` uses it for every glazed run of a frontage (`glass:` key to override). No shader edit, no keyword.
2. **`frontage_galv`** (materials.py, additive): matt galvanised grey (no metal) for the lattice mast, the flag masts
   and their top arms.
3. **Oval board** (`frontage.oval_board`): light rim (0.09 m, `window_frame`), the colour field, two blank mid-tone
   blocks where the two words of the real board are (greeking: plain rectangles in the mast grey, no glyph, no name,
   no logo), 0.18 m thick with a dark edge on LOD0. One coplanar strip tessellation per side: no overlapping faces,
   so nothing can z-fight; the test checks that the areas add up to the ellipse.
4. **Lattice mast**: diagonals on both LODs (LOD1 had rings only: a ladder), LOD0 legs 0.11 m (0.16 read as
   scaffolding from close up), LOD1 legs 0.14 m (0.10 vanished at 80 m on Low in round 1).
5. **Feather banners** (`frontage.flag_row`): a mesh of 6 x 2 cells (LOD1 3 x 1) bowed away from the banner plane
   towards the hem, a different amplitude per mast, a short top arm.
6. **`car_row`** prop + `frontage.place_cars` (hook in `stage.py` after the rule car parks): display vehicles as
   instances of the existing `life_cars` prototypes (`van_<colour>`, `car_<body>_<colour>`; validated in `plan`), in
   tidy rows without the neighbour-repeat rule (a dealer row repeats models). 2 rows x 4 at the orthophoto positions.
   A vehicle within 2.2 m of one the parking rule already placed is skipped.
7. **`fence_style`** override kind (`furniture.fence_styles`, `fences(styles=)`): authored colour of an OSM fence
   way; a styled way that is no longer in the data is reported (`furniture.fences.style_stale`). Both ways above:
   anthracite.
8. **SERWIS fascia board** 1.6 x (`sign.scale` -> instance scale).
9. **2024 references for #21 / #22**: control cameras in `g3b_frontage_cameras.json` carry `reference_for` (the SBS
   camera ids they are the 2024 counterpart of) plus one more 2024 frame (1020363345994649) and a close view of the
   lot. The production SBS files (`sbs_references.json`, `sbs_cameras.json`, `sbs_extra_references.json`) are not
   touched (pose work belongs to the SBS stream); promoting these frames into the gate sheets is that stream's call.

No brand, logo or lettering anywhere (the oval and the totem stay plain fields, the banners plain yellow). All new
dimensions are `WORKING_VALUE` read off the 2024 photos and the orthophoto.

## Session 13 additions (after the first render of round 2)

- **Glazing was still black.** Seen square-on the reflected ray is horizontal and the fresnel term is ~0, so the
  environment term adds nothing whatever the horizon cut; the "gradient" of decision 1 only exists at grazing angles.
  `showroom_glass` albedo is now 0.26 / 0.31 / 0.37 (was 0.045 / 0.055 / 0.07): the mirrored sky is carried by the
  diffuse term and follows the ambient probe (grey under overcast, blue under a clear sky). Reference: strudel
  1020363345994649 (glazing about as light as the low sky, far lighter than the fascia). WORKING_VALUE; the test
  asserts glass > grey wall > fascia. Still no shader edit.
- **Control pose 1020363345994649** re-derived by resection (fascia end at +22.7 deg, flag row at +14.6 deg, hfov
  ~56 deg): E -227 N -256.5, 8 m from the GPS fix. The earlier pose (80 m further) looked past the whole row.
- **Display row**: `van_white, van_white2, van_silver, van_white` - two identical direct neighbours broke
  `test_cars_v4::test_parking_mix_and_neighbours` (W-N7 measures every vehicle instance, dealer rows included).

## Results (2026-11-12, merged with main `f30837474`, Low tier, editor)

- Pairs photo | before (main with ADR 0126, f8b85fa2) | after: `artifacts/frontage-r2/pairs-merged-Low-overcast/`,
  `pairs-merged-Low-clear/` (20 G3-B frames each), `pairs-2024-merged-Low-overcast/` (6 control cameras). Isolated
  pairs on the same base (before the merge, glazing still dark): `pairs-after-Low-*`.
- Review items: oval two-tone with rim (reads as a board), mast matt grey with diagonals, banners bowed, 8 display
  vehicles on the lot, road-front fence anthracite, glazing light blue-grey under the black fascia, SERWIS board
  1.6 x (still a grey rectangle from the road: the prototype has little contrast - open).
- Draw estimate, 20 G3-B cameras, Low-overcast (`stats-diff-after.txt`, same base): delta 0 ... +39, median 0; the
  +31 ... +39 frames are the four that see the lot (instanced vehicles). Against the merged tree
  (`stats-diff-merged.txt`): -34 ... +65, median 0 - that delta contains 333 main commits (pose changes of the SBS
  stream), not only this change. No phone numbers (UNVERIFIED on device).
- Tests: `pytest tests/gis tests/gate3` 825 passed, 1 xfailed (first pass after the merge: 2 failed, both fixed above); EditMode 403 / 403; `fidelity/run.py` refreshed.
- D51 (author's reading, NOT a visual-critic verdict): 150280503737744 recognisable (oval + dark showroom with light
  glazing + red-brown furniture showroom in the right order); 297817221966185 / 3281350541967811 depend on the SBS
  poses of main; the three 2024 control frames match the photo layout (showroom edge, flags, vans, oval).

## Open

- **EC chimneys behind the row are not drawn on Low**: they stand 1187 m from the 2024 camera station; Low
  `cameraFarClip` is 900 m (QualityProfile), so the landmark instances are clipped (Medium 1400 m shows them).
  Rendering / far-field domain: either a far-field silhouette of the two stacks or a per-layer far distance.
- White plot-kit fence of the neighbouring plot (not OSM ways 344253283 / 913217348) still reads white by the mast.
- SERWIS board contrast; flag row bearing and all heights are WORKING_VALUE until the owner photo session.
- Promoting the 2024 frames into the gate sheets (#21 / #22) is the SBS stream's call.
