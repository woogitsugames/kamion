# ADR 0125 — gate 3 recognisability (G3-B): portal, signs, noise screens, HV line

Status: implemented on branch `gate3-signs` (base main `ce3f1a77`, 2026-11-11); not merged. Gate 3 itself is NOT
re-judged here (that is the visual-critic's job).
Source: `docs/reports/visual/REVIEW-2026-11-11-s11-sbs-r1-D51.md` (gate FAIL, G3-B 1/10 recognisable), owner decision
D51 (recognisability of the route before material polish).

## Findings (measured before anything was moved)

| Review item | What the data says | World or pose |
|---|---|---|
| #20 portal "200 m too far" | GUGiK orthophoto 2024 (0.25 m) shows the lattice portal across the northbound carriageway at region-local E,N = (-261, -208) +- 3 m. Mapillary richlv 2020 brackets it between 468708117568850 (GPS -252.7,-214.8, column ~15 m ahead) and 143559297695026 (GPS -269.3,-200.4, portal shadow at the camera); grobin 275528677534382 and kino 1056932506043672 agree. The generated portal stood at (-306.8, -171.3): **59 m too far** (the override said "40 m before the split, WORKING_VALUE"). | world (fixed); the pose of 275528 is additionally ~12 m ahead of the photo |
| #19 "no lattice portal" | zsolt 3281350541967811 shows the SAME portal from behind (grey board back). Its GPS is ~45 m off: the neighbouring frames of the sequence put the portal between stations that contradict three other GPS tracks and the orthophoto. | pose |
| #20 "D-1 on both sides" | The 2020 frame resolves them: warning triangles with a yellow plate (not D-1), a few metres before the portal; OSM has emergency signals of the fire-station exit 20 m further. | world (added) |
| #16 / #18 red-white board | Chevron board on the island nose of the right-turn slip (orthophoto: nose at -217.3, -240.3). 2024 frame: U-21 posts instead - the board is the 2017-2019 state. | world (added, low confidence) |
| #23 "no HV tower, no screen on the right" | Both exist in the render (BDOT10k OT_SULN_L / OT_BUWT_P tower at -369,-69, 20 m; OT_OIKM_L barrier from -319,-152). The tower bearing matches the photo (24 deg right of the axis). They are just faint at 470 px on Low overcast. | neither: legibility |
| #25 "no screen on the right" | Barrier exists (OT_OIKM_L from N = 93); the photo has it beside the camera, so the pose is ~15-20 m short. The dark band of the real wall is ~40 % of its height, ours was 1.0 m. | pose + style (fixed) |
| #24 "screen also on the left" | `bridge_style.noise_screen` put a screen on both deck edges. The photo has it on the right-hand (outer) edge only. OSM left/right does not enter: screens on decks are a style, barriers on the ground are separate BDOT/OSM lines. | world (fixed) |

## Decision

1. **Portal**: `andersa-putry-approach-gantry` re-anchored: 39 m before OSM node 12620261934 on way 266084693 (was 40 m
   before node 2840742308); generated centre (-260.8, -208.3), 0.4 m from the orthophoto reading. Board rows after the
   2020 frame.
2. **New module `tools/worldgen/streetscape/gate3_landmarks.py`**, override `kind: gate3_sign`: a sign assembly placed
   by `at_en` (orthophoto) or `along` (way / node / distance / side of travel). One assembly = one prototype
   `sign_g3_<key>` with ONE material `sign_<key>` (post, faces and backs share a <= 512 px texture written through the
   existing `boards` registry), so a sign costs one draw and <= 40 triangles. Faces are our own drawings: A-30 + text
   plate, U-4a, D-1, D-3, D-6, street-name plate (teal plate and post as in Białystok).
   Entries: two warning signs before the portal, U-4a on the island nose, two name plates and D-3 / D-6 at Rondo
   Bieżeństwa (the last four +- 3-5 m, low confidence: the island is under the deck on the orthophoto).
   An authored point that falls on the generated carriageway is moved 0.6 m behind the nearest carriageway edge when
   that edge is within 8 m (`snapped_m` in QA; the U-4a moved 5.4 m onto the generated island nose), otherwise the
   entry is reported stale. A point under a viaduct deck takes the terrain height, not the deck.
3. **Viaduct screens**: `bridge_style.set.screen_side: travel_right` (`roads.meshing.screen_sides`); the edge without
   a screen keeps its railing. Applied to the Putry viaduct; the southbound deck is assumed symmetric (UNVERIFIED).
4. **Ground noise barriers**: glazed style gets a joint rail at mid height of the glazing; zones 4-6 (al. Tysiąclecia)
   band 1.0 -> 1.8 m (WORKING_VALUE read against the posts).
5. **HV line**: no change - towers and conductors were already generated from BDOT10k / OSM (ADR 0022).

## Changes in files owned by the parallel "furniture" session (minimal, additive)

- `streetscape/props.py` `build_all`: two lines registering `gate3_landmarks.prototypes()`.
- `streetscape/furniture.py` `noise_wall`: three lines (mid rail of glazed barriers; barriers are this stream's domain).
- `streetscape/stage.py`: import + one call `G3.build(...)` before `clear_carriageway`.
No change in `signs.py`, `signs_route.py`, `fab_details.py`; `signs.square / d1 / _font` are only called.

## Not done / open

- **D-3 / D-6 at the northern slip of Rondo Bieżeństwa (#11) are NOT placed**: the generated junction has carriageway
  where the orthophoto has the small island (more than 8 m from any edge). Both entries stay in `overrides.yaml` and
  are listed under `gate3_landmarks.stale` until the junction stream builds that island and crossing.
- Draw estimate (editor, Low overcast, before batching) on the G3-B cameras: see `artifacts/gate3-signs/` stats; the
  baseline is main's imported world, which already differed from main's code, so the delta is not fully isolated.
- Pose errors confirmed, not fixed here (camera files belong to the SBS stream): 3281350 (~45 m along the road),
  275528 (~12 m), 1801374 (~15-20 m), 494288 (heading).
- Crossing with paved island at Rondo Bieżeństwa (#11), retail frontage (#21/#22), missing pier (#9/#10), gravel
  embankment: other domains (junctions / buildings / viaduct).
- Sign designations U-4a and the plate text are UNVERIFIED; board sizes WORKING_VALUE.
- Glass of the screens (`noise_glass`, alpha 0.10) was left alone: it is shared with every tier's look and was tuned in
  review r6 W-N2.

## Evidence

`artifacts/gate3-signs/` : `baseline/` and `after/` (renders, `stats-*.txt`, sheets), `STATUS.md`.
Tests: `tests/gis/test_gate3_landmarks.py`.
