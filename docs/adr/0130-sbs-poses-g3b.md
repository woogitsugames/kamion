# ADR 0130 — SBS G3-B pose calibration: 3281350, 297817, 1801374, 494288

Status: implemented on branch `sbs-poses` (base main `587adc32`, 2026-11-12, s12); not merged. Data only: no world,
no SBS tool, no C# change. Gate 3 is not re-judged here; the D51 grades below are the author's, a visual-critic review
is still required.
Source: `docs/reports/visual/REVIEW-2026-11-12-s12-gpt-batch-d.md` (pose table, "uwagi do sbs r4" 2), ADR 0103/0111
(SBS method, confidence), ADR 0125 (portal re-anchored to the GUGiK orthophoto, zsolt GPS error), lead commit
`5e3552a2` (275528-04, 837235-12 promoted).

## Context

After `5e3552a2` G3-B had 4/10 RECOGNISABLE. The remaining pose blockers: the two zsolt 2017 frames (GPS of the
sequence wrong by tens of metres), gpsmapper 1801374 (screen far, should be next to the camera), szurek 494288 on the
Putry deck (lamps on the wrong side, "wrong carriageway or heading"). `prepare` must not be run (it downloads and
rectifies photos), so the poses are written as explicit `authored_overrides` and the matching `sbs_cameras.json` /
`sbs_references.json` entries are produced with the exact `prepare()` camera formula.

## Method

1. `artifacts/sbs-poses/tools/poselib.py` re-implements the Mapillary branch of `prepare()` by importing
   `tools/refs/sbs_gate3.py` (grid heading, rectified horizon, vfov, pose). Check: it reproduces every committed
   Mapillary camera of `sbs_cameras.json` to < 2 mm. The two lead-promoted cameras (`5e3552a2`) differed by 0.056 m
   (0.52 was used as the rectified horizon): fixed by making `rectified_horizon_y_fraction: 0.52` explicit in their
   overrides (keeps the reviewed pitch; look_at changes 0.1 mm) and writing their `sbs_references.json` entries.
2. Photo resection where the photo shows the portal: generated/orthophoto portal `andersa-putry-approach-gantry` at
   E,N (-260.8, -208.3), span 16 m (ADR 0125); leg bearings measured on the rectified photo; absolute heading from the
   two EC chimneys (overrides.yaml EPSG:2180 positions, ~1.3 km away, so their bearing barely depends on position).
3. Diagnostic probes (`pose_confidence` C, ids `sbs-p130-*`) rendered Low-overcast in two rounds (r1 37 probes incl.
   3 top-down overviews, r2 29 incl. production "before"), contact sheets photo | before | probes
   (`artifacts/sbs-poses/r{1,2}/sheet-*.jpg`). Chosen variant must have >= 2 independent anchors; a vanishing point or
   horizon alone is not an anchor.
4. Height: generated `road_asphalt` (or deck `road_asphalt`) under the camera from a vertical ray through the chunk
   GLBs (`artifacts/sbs-poses/tools/deckray.py`, verified against the stored 494288 deck hit 140.188 m) + eye.
   Horizon: measured on the rectified photo as `rectified_horizon_y_fraction` (far road / treeline); the old manual
   values 0.62-0.68 were 0.06-0.09 too high for the zsolt and szurek frames.

## Decision (authored overrides, WORKING_VALUE, confidence B)

| Camera | Delta vs GPS (E, N) | Eye / U | Heading | Rect. horizon | Anchors (photo vs render) |
|---|---|---|---|---|---|
| `sbs-g3-b-3281350541967811` zsolt 2017 | -60.98, +40.40 m (~73 m back along Andersa) | 1.4 m car / 131.655 | SfM (chimneys agree within 0.1 deg) | 0.77 (was 0.685) | lattice portal behind, over the left (northbound) carriageway: legs x 0.145/0.434 vs 0.14/0.43; low hall at the left edge, low white block right at the horizon |
| `sbs-g3-b-297817221966185` zsolt 2017 | -68.88, +49.56 m (~85 m back) | 1.4 m / 132.875 | +1.15 deg (chimneys) | 0.75 | same portal far ahead in the centre (x 0.445-0.566 vs 0.44-0.56); blue industrial hall at the left edge x 0-0.2 in both; showroom oval mast bearing ~x 0.91 consistent |
| `sbs-g3-b-1801374876712141` gpsmapper 2019 | -3.47, +19.70 m (20 m forward, heading 350) | 2.2 m / 137.927 | SfM | 0.56 (was 0.624) | noise screen starts close at the right edge; wide grass median with the opposite carriageway at x 0-0.3 on the left |
| `sbs-g3-b-494288258686575` szurek 2017 | +1.81, +2.40 m (3 m right on the deck) | 1.7 m / 141.849 (deck 140.149) | SfM | 0.72 (was 0.665) | dark screen posts close at the right receding to x ~0.2; median barrier / second deck at the left edge |

The two zsolt frames are 2.7 s apart in one sequence and both land ~73-85 m behind their GPS along the road, i.e. one
consistent sequence offset (ADR 0125 said "~45 m", measured on one frame without resection).
Note vs ADR 0126 ("zsolt frames ~45 m from the flag masts"): the portal width (16 m at 7.4 deg) puts 297817 ~120 m
before the portal; the showroom's oval mast then lands at x ~0.91 as on the photo. Which masts 0126 measured is not
recorded; left open.

## D51 (author's grade, Low-overcast render vs photo; visual-critic review required)

| Frame | Before | After | Why not more |
|---|---|---|---|
| 3281350 | NOT (no portal) | RECOGNISABLE (weak) | portal is a grey frame on Low, photo truss is taller (world portal 7.4 m, photo implies ~8.5-9 m, UNVERIFIED); 2017 construction fence / van not modelled |
| 297817 | PARTIAL (portal close, wrong) | RECOGNISABLE (weak) | showroom colours 2017 vs 2024 (ADR 0126), lamp close left missing, EC chimneys lost in Low fog |
| 1801374 | PARTIAL | PARTIAL | screen is a post fence, photo has a tall transparent panel screen; the tall double lamp (photo x 0.68) and the billboard on the left are not in the world |
| 494288 | PARTIAL | PARTIAL | **lamps: world, not pose.** On the photo the lamp row stands in the median (left); the generated deck puts the lamps on the right kerb next to the screen. No pose puts them left without faking it with a heading turn (r2 c6 +3 deg does, rejected). Screen in the world is lighter and lower |

G3-B by this grade: 6/10 RECOGNISABLE (2 weak), 4 PARTIAL, 0 NOT (from 4/5/1) — still FAIL.

## Validation

`uv run --project tools/refs python -m pytest tests/gate3 tests/gis/test_sbs_gate3.py tests/gis/test_sbs_photometry.py tests/gis/test_sbs_report.py -q` (heavy slot): 109 passed. 4-state render (`sbs-gate3.ps1 -RenderOnly`, Low/High x overcast/clear, 42 cameras) at `a300b826`-epoch data; the later 275528/837235 consistency fix moves a look_at by 0.1 mm, so `cameras_sha256` of that capture is stale -> rerender before any compose.

## Consequences / open

- World follow-ups (other sessions): Putry deck lamp row to the median (494288); Andersa portal height/truss on Low
  (ADR 0127 read); Tysiaclecia noise screen type and the double-arm lamp (1801374).
- `sbs_recognition.json` (GPT register, bound to render SHAs) not touched — must be re-graded after the 4-state render.
- Weakest G3-A poses were not re-calibrated in this round (time); same tooling applies (`make_r2.py` pattern).
- Evidence: `artifacts/sbs-poses/` (photo | before | after pairs, r1/r2 sheets, maps, plan.json per probe).
