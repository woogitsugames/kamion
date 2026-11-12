# ADR 0133 — DK8 over Rondo Putry: median double-arm lamp row (authored), deck geometry unchanged

Status: implemented on branch `putry-deck` (base main `29f5cf85`, 2026-11-12, s12; main merged s13 `3feda88c8`); not merged. A visual-critic
review is still required; the D51 grades below are the author's.
Source: ADR 0130 (494288 "lamps: world, not pose"), `docs/reports/visual/REVIEW-2026-11-12-s12-0130-truck-r3.md`
(world follow-up "łuk i latarnie pomostu Putry"), ADR 0125 (screen on the outer edge), ADR 0105/0119 (underdeck).

## Context

On Mapillary 494288258686575 (szurek 2017, CC BY-SA 4.0, reference only) the NW-bound DK8 deck over Rondo Putry
has the noise screen on the right and a row of tall **double-arm (Y) columns behind the left, median-side barrier**.
The generator puts one single-arm `lamp_12m` every 36 m on the outer (right) cap of each one-way carriageway
(`furniture.lamps`, `standards.LAMP["GP"]`), so the render had lamps next to the screen and none on the left.
The reviewer also reported the deck "in a clear left curve" while the photo looks straight.

## Data (no positions invented)

- OSM: no `highway=street_lamp` node on or near the decks (11 in the whole region).
- GUGiK WMS HighResolution 0.08 m (cells c_02..c_04 x c_07..c_08 already in `Data/raw/refs/gugik-ortho-hr`):
  every head in the median is a Y column with two arms across the road; the outer edges of both decks carry no
  lamps. 14 columns from E -792 to E -396, spacing 32.2-36.7 m (mean 34.8). Base = start of the pole shadow
  (the top leans away from the nadir); read on 2x crops (`artifacts/putry-deck/data/sheet1.jpg`, `sheet2.jpg`,
  `median_lamps_ortho.json`). Lateral accuracy ~1 m (WORKING_VALUE). Lamps east of E -396 lie outside the fetched
  cells and are not authored (rule lamps stay there).
- In the 4.2 m gap between the two decks the base reads 1.1-2.0 m outside the NE deck fascia; the pole image is as
  long as that of a ~10-12 m ground lamp nearby, i.e. the column starts at deck level, not on the ground 6-8 m
  below. No drawings: the console on the deck fascia is WORKING_VALUE.
- Column on the photo, scaled on the visible shaft above the median barrier: luminaires ~12 m above the deck,
  arm reach ~2.4 m, rise ~1.1 m (WORKING_VALUE).
- Deck curve: the generated deck ribbons drawn over the same orthophoto (`data/plan_before.jpg`) follow both decks
  within the ortho edge accuracy along the whole curve; plan geometry is therefore not changed. The visible
  difference to the photo is not explained by plan data (see D51 below for what the lamps show about the pose).

## Decision

1. Authored row `Data/Regions/bialystok-industrial-c/lamp_rows.json` (an `authored_override` outside
   `overrides.yaml`, so the road-fidelity report does not go stale): the 14 measured points, the prototypes and
   `suppress_rule_lamps` = rule lamps of OSM ways 1101181473 / 173956078 within 18 m of the row.
2. `furniture.lamp_rows` runs after the clearing passes (carriageway / narrow island / under-deck / level): a point
   within 2.6 m of a bridge deck goes on a steel console 0.30 m outside the nearest deck edge, at the cap-top height
   (`lamp_double_console_12m`); otherwise a ground column `lamp_double_12m` seated on the terrain. Arms (+-y) across
   the road. A point that lands on a carriageway is skipped and reported.
3. `props.lamp_y`: straight column, two straight arms in a Y, the existing LED housing / glass materials (no new
   material). Console variant without the concrete footing.

## Validation

Run on the branch after `git merge main` (3feda88c8) and a full regeneration (build_world 582 s, import-region OK,
Low 121.0 MB / High 263.1 MB world memory).

- `streetscape_qa.json` `furniture.lamp_rows.dk8-putry-median-double-lamps`: placed 14 / 14, on deck consoles 11,
  ground columns 3, skipped on carriageway 0, rule lamps removed 23.
- `tests/gis/test_lamp_rows.py` 4/4; `pytest tests/gis tests/gate3`: 825 passed, 1 xfailed (heavy slot, 17 min); EditMode 403/403.
- SBS G3-B, Low, overcast + clear, 10 frames each (`artifacts/putry-deck/{before,after}/Low-*`, sheets
  `artifacts/putry-deck/pairs/*.jpg`; "before" = base main 29f5cf85, so deltas also contain unrelated main changes):
  instanced props draws per frame -7 .. +6 (494288: 88 -> 81; 209622 / 810525 / 810896: +6), instances -14 .. +1,
  drawsEst / trisK of the static meshes unchanged in every frame. Budget not worsened.

| Frame | Before | After |
|---|---|---|
| 494288 (on the NW deck) | single-arm lamps on the right, next to the screen; none on the left | Y columns behind the left median barrier, screen side clear - as on the photo |
| 4312632 / 468026 (from below, S) | single-arm heads above the deck parapet | double heads above the deck, rhythm ~35 m - as on the photo |

### D51 (author's grade; visual-critic pending)

"Would a driver recognise the Putry deck?" - on 494288: yes for the furniture (screen right, Y lamp row left,
barrier, two lanes), which was the blocker named in the 0130 review. Still different from the photo and NOT fixed
here: (1) the render bends right much more than the photo; plan geometry matches the 0.08 m ortho, so this is the
SBS camera pose (position along the curve / yaw) - next step is a pose re-solve of 494288 on the deck, not a deck
change; (2) the wide light-grey strip right of the edge line (photo: a narrower reddish-brown strip before the barrier);
(3) under-deck dark panels in 4312632 / 468026 (ADR 0105/0119 scope). Grade: G3-B furniture PASS (author),
deck curve/pose OPEN.