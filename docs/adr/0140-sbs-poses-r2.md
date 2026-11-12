# ADR 0140 — SBS poses r2: re-resection against the 14 m Andersa portal, PARTIAL diagnosis, one-command Low pairs

Status: implemented on branch `sbs-poses-r2` (base main `76c88d4f`, 2026-11-12, s13); not merged. Data + tool only:
no world geometry, no C#. Gate 3 is not re-judged here (visual-critic).
Source: `docs/reports/visual/REVIEW-2026-11-12-s13-0127.md` P1-2 (poses resected from a 16 m portal stand too far),
ADR 0127 (portal span 16 -> 14 m, `columns_en`), ADR 0130 (method), GPT backlog "SBS r4" (P2 pitch 150280).

## Finding before any change: stale world in the worktree

The worktree's `Data/raw/derived/.../world` and the Unity import (copied from the main checkout) still carried the
pre-0127 portal (`sign_gantry_16_74` at (-260.8, -208.3)); the committed `world_manifest.json` is the 14 m build
(`sign_gantry_14_70` at (-262.8, -207.5), feet (-267.212, -212.934) / (-258.388, -202.066)). Rendering there would
have "calibrated" against the wrong portal. The derived world, `_Generated/World` and `Library` were copied from the
merged `g3b-lowread` worktree (manifest identical to main modulo EOL). The new preflight (below) catches this case.

## Method

`artifacts/sbs-poses-r2/tools/resect.py`: unknowns E, N, heading; observations = photo x of both portal columns
(rectified photo, 1280 px, measured on ruler crops `look/z*.png`, at beam level; projection at 6 m above the footing)
+ one independent prior:
- grobin 2019 frontal (275528, 837235): lateral position across the carriageway kept (lane dashes on both sides of
  the camera in photo and render: middle lane);
- zsolt 2017 rear (3281350, 297817): heading from the two EC chimneys (~1.3 km), photo x measured on
  `look/z328ch.png`, `look/z297ch.png` (chimney-2 left, chimney-1 right; ADR 0130 had them paired the other way
  for 297817, which left the heading 0.7 deg off).
Eye height and rectified horizon kept; U = generated road asphalt under the new position (chunk GLB ray) + eye.
Diagnostic probes (`pose_confidence` C, `sbs-p140-*`) rendered Low-overcast (r1: 29, r2: 3), sheets photo | before |
probes `artifacts/sbs-poses-r2/r{1,2}/sheet-*.jpg`; `tools/finalize.py r1 r2 --write` writes the chosen probe as
explicit authored overrides + the formula-identical `sbs_cameras.json` / `sbs_references.json` entries
(`poselib.verify_all()`: 0 mismatches). The `sbs_references.json` entries of 275528/837235 already existed (ADR 0130
follow-up); they are rewritten here with the new pose fields.

## Decision (authored overrides, WORKING_VALUE, confidence B)

| Camera | Change | Anchors (photo vs model/render) |
|---|---|---|
| 275528 grobin 2019 | 20.1 -> 15.2 m from the portal centre, heading +0.56 deg | columns x 0.295/0.753 (resid < 0.1 px); middle lane; beam top y 160 px photo vs 151-157 model (world portal 7.0 m by rule, photo ~6.5 m) |
| 837235 grobin 2019 | 7.0 m forward, 3.1 m right (right lane at the gore line), heading 306.8 -> 308.3; 68.2 -> 61.7 m from the portal | chevron at its **orthophoto** position (x 0.861, plate 155 px), portal west column x 584, predicted east column 729 vs photo beam end ~736, white block at the left edge in both; road VP agrees with the road axis (309.1) |
| 3281350 zsolt 2017 | 49.4 -> 44.4 m, heading +0.02 deg | columns x 189/560 px; EC chimneys x 910/936 px |
| 297817 zsolt 2017 | 119.1 -> 110.8 m, heading -0.54 deg | columns x 571/722 px; EC chimneys x 950/976 px (pairing fixed) |
| 150280 picturehoover 2020 | rectified horizon 0.62 -> 0.50, heading -2.2 deg | road VP y 356 / x 555 px photo vs 439 / 514 render (lane dash + left kerb), far road end |
| 3678296 grobin 2019 | rectified horizon 0.585 -> 0.559 | near-road VP y 384 px photo vs 403 px render |

Rejected: placing 837235 against the generated chevron (heading 304.6, VP 4.5 deg off the road axis, lateral 1.6 m
further left - inconsistent); 1801374 1.0-2.5 m right (r1 l1-l3: the lane dash then runs under / left of the camera,
the photo has it right of the camera as production does).

## World findings for other streams (not changed here)

- `andersa-elewatorska-island-u4a` (chevron): generated 5.4 m from its orthophoto `at_en` (snapped by
  `gate3_landmarks.SNAP_MAX_M` to the generated island) -> after the correct pose it stands behind the camera in
  837235; D51 for 837235 loses its main mark until the sign is placed at `at_en` (or the island nose moved).
- `andersa-gantry-warning-left/right`: 46 m before the node = 7 m before the portal (photo guess, ADR 0125); 275528
  shows them clearly in front of the portal -> after the correct pose they fall behind the camera. Station to be
  re-measured (orthophoto / 1056932506043672).
- 3281350/297817: chimney tops put the horizon ~0.04 lower than the portal top allows (66 px conflict in 3281350):
  either the 2017 portal is ~2 m taller than the 7.0 m rule (and 2019 is not) or it is another structure (one board
  in 2017, review P2-2). UNVERIFIED; horizon kept at ADR 0130 values.

## PARTIAL frames: pose or world (photo vs post-0127 Low render, ruler crops `artifacts/sbs-poses-r2/look/`)

| Frame | Pose | World (other streams) |
|---|---|---|
| 150280 picturehoover 2019 | **pose**: horizon 0.62 vs photo 0.50 (road vanishing point from lane dash + left kerb: photo y 356 px, render y 439 px of 720; far road end agrees: 340 vs 430); heading: VP x 555 vs 514 px -> -2.2 deg | yellow barrier left, red/white EC chimneys and the red-flag showroom right are present on the photo, not checked further |
| 3678296 grobin 2019 | minor: horizon 0.585 -> 0.559 (near-road VP photo 384 px vs render 403 px of 720; VP x within 6 px) | HV tower seen end-on (arms along the view axis, ADR 0127 open point: BDOT10k line direction vs photo broadside); two signal heads in the frame centre that the photo does not have; left treeline sparse |
| 494288 szurek 2017 | none: horizon (photo VP ~0.70-0.71 vs render 0.70) and screen post run agree | lamp row on the right kerb (photo: in the median, ADR 0130); deck curve tighter; screen milky/lined instead of clear PMMA (review P1-1); tube railing + concrete parapet instead of a guardrail |
| 1801374 gpsmapper 2019 | uncertain: horizon agrees (0.555 vs 0.565); render camera hugs the left edge line (left kerb leaves the frame at the bottom, x 0.31) while on the photo the left kerb leaves at the left edge, y 0.80 (camera several m from it); probes l1-l3 test 1-2.5 m right / lower eye | left: opposite carriageway is followed by a tall dark screen + houses in the render, a low mesh fence + billboard on the photo; the opposite carriageway reads ~2x farther on the photo (median width / its far geometry: check on the orthophoto); right: paved sidewalk/service strip between kerb and screen on the photo, grass verge in the render |
