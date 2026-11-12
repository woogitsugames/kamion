# ADR 0126 — G3-B trade frontage (recognisability): authored facades of the showroom row

Status: implemented on branch `g3b-frontage` (base main `1d4674ab`, 2026-11-12); not merged. Gate 3 is NOT re-judged
here (visual-critic's job).
Source: `docs/reports/visual/REVIEW-2026-11-11-s11-sbs-r1-D51.md` blocker 6 ("pierzeja handlowo-usługowa wzdłuż G3-B",
frames #21 `sbs-g3-b-150280503737744`, #22 `-297817221966185`, partly #19 `-3281350541967811`), owner decision D51.

## Findings (before anything was changed)

The buildings were there (BDOT10k footprints, LoD1 2024 heights) but read as anonymous boxes:

| Building (region-local E, N) | Data | Generator gave | Photos / orthophoto show |
|---|---|---|---|
| `bdot:2BE4B431-C34A…` (-245, -315), 1074 m2, 6.55 m | BDOT FUNKCJA "magazyn" | sheet-clad hall with loading docks and a truck zone | furniture showroom: red-brown walls, a dark band of glazing under an overhanging dark roof edge (picturehoover 150280503737744 2020, strudel 490210580292738 2024, kino 806036451686717 2024) |
| `bdot:2BE4B431-C785…` (-219, -340), 1155 m2, 6.11 m | "obiekt handlowo-usługowy", 1 storey | office: light render, punched windows | car showroom: fully glazed road end under a tall fascia; three flag masts, a totem, a lattice mast with an oval board (on every photo 2017-2024) |
| `bdot:3c5cd1c0…` (-165, -376), 855 m2, 7.02 m | "obiekt handlowo-usługowy" | office | glazed showroom, dark fascia, glass roof over the NE half (orthophoto 2024-05-27; strudel 1395903477772426) |
| `bdot:d0f4dd2c…` (-280, -272), 663 m2, 14.35 m, 4 storeys | "budynek wielorodzinny" | block with balcony galleries on both long sides, hashed colour | white / light render, punched windows, loggias at the gable end only (kino 806036451686717, strudel 1447066149328933); built after 2020 (crane on the 2020 frame) |

Which year: the gate photos of these three frames are from 2017 and 2020 and show the car showroom **white with a red
entrance block and red flags**. The 2024 frames (strudel 469512365899192, 490210580292738) show it **re-clad dark with
yellow flags**. Every footprint and height of the region is the 2024 state (LoD1 2024, orthophoto 2024-05-27) and the
block next door did not exist in 2020, so the frontage is modelled as of 2024; the 2017-2020 colours are recorded in
the override `reason`. Consequence for the gate sheets: on #21 / #22 the showroom is dark where the old photo is white
and red. Extra pairs against the 2024 photos are in `artifacts/g3b-frontage/pairs-2024/`.

Pose remark (not changed here): the zsolt 2017 and strudel 2024 frames lag their GPS by tens of metres (the three
flag masts stand 2.7 m apart in a row parallel to the road, yet the photos separate them by ~1.75 deg: the camera is
~45 m from them, not ~110 m). ADR 0125 found the same for 3281350541967811.

## Decision

1. **New module `tools/worldgen/streetscape/frontage.py`**, building override key `set.frontage` (overrides.yaml =
   authored_overrides, survives every re-import): wall material, other material per compass facing, plinth, fascia
   band or overhanging roof slab, glazed runs (`facing`, `span` left-to-right seen from outside, `z` above the floor,
   mullion pitch, transom), accent fields, a functional fascia sign (existing `facade_sign_<code>` prototypes), and
   advertising structures in front of a wall: `flag_row`, `totem`, `sign_mast` (lattice mast + oval board).
   No lettering and no brand on any of them: the oval and the totem are plain colour fields, the flags plain banners.
2. The frontage is drawn on **both building layers from the same numbers** (LOD0 `buildings`, LOD1 `buildings_low`;
   LOD1 drops mullion sides and mast diagonals), so Low and High show the same row.
3. **Only existing materials** (`brick_red`, `plaster_accent_grey`, `hall_flashing`, `glass`, `plinth_dark`,
   `downpipe`, `paint_yellow`, `bin_plastic_blue`): no change to `materials.py`, shaders or the Unity importer.
   `hall_wall_*` is rejected in a frontage (those need wall-top UV1 on every triangle).
4. **Block overrides** in `buildings_mesh.build`: `wall_material` (now honoured for blocks and offices, was halls
   only), `balconies: false`, `bands: false` (one wall tone: no accent rows, gable or stairwell field).
5. Volumes stay data-driven: no height or footprint is overridden. `typology: office` on the furniture showroom
   removes the docks and the truck zone the "magazyn" function gave it.
6. Heights of the glazing bands and fascias are read off photo proportions; mast / flag / totem positions are the
   feet of their shadows on the orthophoto 2024-05-27 (+-1.5 m), heights from shadow length against a street lamp.
   All `WORKING_VALUE`, to be confirmed by the owner's photo session.

Files not touched: `streetscape/{plots,plot_kit,materials,stage}.py`, `WorldPlotKit` / `WorldPBR.shader` (ADR 0124
agent), signs / props / landmarks modules (GPT sessions). The advertising structures are part of the building mesh
(layers `buildings` / `buildings_low`, source = the building id), not street props.

## Results

RESULTS_PLACEHOLDER

## Open

- Gate sheets #21 / #22 compare against 2017 / 2020 photos (white + red showroom); a 2024 reference for these two
  stations would settle the colour question (owner photo session or newer Mapillary frames in `sbs_references.json`).
- Rear walls of the showrooms are not visible in any open photo (dark grey assumed).
- The glass roof of `bdot:3c5cd1c0` and the low annexes in front of the furniture showroom are not modelled.
- SBS poses of the zsolt frames (GPS lag) are unchanged.
