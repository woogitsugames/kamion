# ADR 0143 — SBS poses r3: Putry deck 494288 re-resected, 810896 off the median, 482392 / 320326 (G3-A), 837235 pose vs world

Status: implemented on branch `sbs-poses-r3` (base main `9a1961db`, 2026-11-12, s14); not merged. Ready to merge. Data + analysis tools only:
no world geometry, no generator, no C#. Gate 3 is not re-judged here (visual-critic + `sbs_recognition.json` re-grade).
Source: `docs/reports/visual/REVIEW-2026-11-12-s14-0133.md` P1-1..3 (494288 bends right, wide light strip, 810896 behind a
retaining wall), `REVIEW-2026-11-12-s14-0128.md` P1-1 (320326 production pose shows only a cut edge of D-3) and P1-3
(482392 blue board), ADR 0140 (method, `scripts/sbs-low-pairs.ps1`), lead requests in s14.

## Finding before any change: stale world

The worktree's derived world and Unity import (copied from main) did not match the committed `world_manifest.json`, and
main's `overrides.yaml` had changed after the last committed build (`sbs_pairs.py preflight`: 13 chunk sizes +
overrides hash). World regenerated in the worktree (`build_world.py`, heavy slot, 607 s, road consistency 65 as before)
and imported (`import-region.ps1`); preflight OK. The regeneration also rewrites `generated/world_manifest.json`,
`generated/streetscape_qa.json`, `generated/far_field_qa.json`, `generated/landmarks/viaduct_putry_underdeck.spec.json`,
`Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json`, `art-source/world/props/{props_meta.json,street_props.glb}`;
these are **not committed** here (the lead regenerates main at integration).

## Method

As ADR 0140: photo measurements on ruler crops (`artifacts/sbs-poses-r3/look/`), resection where the world has good
anchors, diagnostic probes (`pose_confidence` C, `sbs-p143-*`, `tools/probes.py`), Low-overcast probe renders
(`tools/render.ps1`, Unity slot, side effects restored), contact sheets photo | production | probes
(`r1/sheet-*.jpg`, `r2/sheet-*.jpg`), the chosen probe written by `tools/finalize.py r1 r2 --write` as explicit authored
overrides + formula-identical `sbs_cameras.json` / `sbs_references.json` entries (`poselib.verify_all()`: 0 mismatches).

## Decision (authored overrides, WORKING_VALUE)

| Camera | Change | Anchors (photo vs model/render) |
|---|---|---|
| 494288 szurek 2017 (Putry deck NW-bound), conf. B | **41 m back (SE)** to E -486.3 N -30.7; **1.7 m right of the graph centreline** (~0.85 m right of the generated lane dash; ADR 0130 had 4.7 m = on the right edge line); eye 1.70 -> 1.15 m on the generated deck asphalt; heading 309.4 -> 316.8 (road tangent + 7.5); rectified horizon 0.72 -> 0.725 | Photo: lane dash X = -0.83 H and edge line X = +2.66 H from the near-road vanishing point (441, 687 of 1280x960) -> camera in the left part of the right lane, heading 6.8-7.5 deg right of the road; median lamp ladder: nearest lamp ~35-40 m ahead, ~33 m pitch (photo y and arm span ratios 1 : 1.8 : 2.5-3 : 3.3-4) -> `tools/fit494b.py` (lamp x + 1/d ladder with a free common lamp-height offset, dash line, road VP; roll free): s -32 m, rms 13.8 px. Rendered g0: straight road, dash slanting from the lower left, screen receding to x ~0.2 at the far left bend as on the photo. Photo roll ~-3.7 deg is not renderable |
| 810896 richlv 2020, conf. C | 3.5 m SW: out of the median (5.0 m left of the SE-bound centreline, next to the generated retaining wall) onto the left lane of SE-bound Andersa; eye 1.7 -> 1.0 m on the generated asphalt (`absolute_u_m` 133.657); heading kept (SfM 78.7) | Photo = car on SE-bound Andersa looking ~51 deg left of the road (kerb vanishing point x ~1440 px, original compass 132 = travel bearing); kerb ~2.5 H left of the camera; guardrail top below the horizon (eye ~1.0 m). **The frame stays unusable** until the world is fixed here (below) |
| 482392 richlv 2020 (G3-A), conf. B | +3.3 m E / -2.6 m N (the ADR 0128 shift of the same 2020-08-15 sequence), eye 1.7 -> 0.9 m, heading 242.7 -> 246.1, rectified horizon 0.75 | Near kerb from the bottom edge (x 0.62) to the right edge (y 0.83) as on the photo; far pier pair (1080/1145 vs photo 1050/1145 px) and abutment within ~40 px; near pier pairs still ~100 px left of the photo (pier spec is by eye, `confidence: low`) |
| 320326 richlv 2020 (G3-A), conf. B | **promoted the ADR 0128 probe**: E 541.5 N -690.4 U 140.52 (eye 0.9), heading 244.0, rectified horizon 0.7205 (pitch 18.3) | ADR 0128 geometry (zenith vanishing point, zebra corner), accepted in REVIEW s14-0128 (D-3 left, D-6 right on the kerbed nose); re-rendered on the regenerated main world: viaduct fascia line and roundabout kerb as on the photo. The D-3 / D-6 island is on branch `biezenstwa-island`; on main the frame shows the nose position without the signs until that merge |
| 837235 grobin 2019 | **none** | see below |

Rejected: 494288 at the ADR 0130 station with only the lateral fix (r1 `lat`: the road still bends hard right because
the camera stands at the start of the left bend where the right lane widens); 494288 with Mapillary heading 309.4 (road
VP 7 deg off); 482392 pier-column resection `fit482.py` (E 537.4 N -690.6, heading 252.5, residuals up to 32 px) -
rendered (r2 `pf`) it puts a large pier in the near left of the frame where the photo has open grass: the pier spec is
not good enough for resection; 810896 7 m SW / eye 1.6-1.7 (right lane / roof height: kerb too far, guardrail above the horizon).

## 837235: pose or world?

Pose consistent (ADR 0140, unchanged). The U-4a chevron stands ~6.5 m from the camera on the 2019 photo; the 0140 pose
is 6.9 m from the old nose position E -217.3 N -240.3 (bearing 36 deg right, photo x 0.861). ADR 0128 (branch
`biezenstwa-island`, decision 6) identifies that point as worn paint of the longer 2019 island and puts the board on
the 2024 island nose E -219.9 N -234.75: from the 0140 pose that is 13.0 m, 31 deg right (x ~0.81 of the frame).
On current main it is snapped 5.4 m to the far verge of the slip (E -212.0 N -239.1: 8.6 m, 75 deg right, outside the
frame). So the difference is **world epoch** (photo 2019, world 2024 by the lead's decision) plus the snap on main that
0128 removes - no pose change; after the 0128 merge 837235 shows the chevron smaller and further than on the photo, by
decision.

## World findings for other streams (not changed here)

1. **Putry deck median lamps (ADR 0133, 494288)**: with the pose fitted on the lamp ladder, the photo's heads are only
   ~6 m above the eye and the two arms span ~2.6 m (lamp 1: 108 px at ~40 m); the generated `lamp_double_12m` stands on
   the deck with heads 12 m above it and arms 2 x 2.4 m. Fit offset: forks 3.5-5 m too high. Either the columns stand
   on the ground under the 4.2 m gap (deck ~5 m above it) and are 12 m from there, or they are ~7-8 m columns with
   ~1.3 m arms. UNVERIFIED; check the shadow length on the 0.08 m orthophoto / a side photo (4312632558767412, 468026894483428).
2. **Putry deck right verge (494288, review P1-2)**: generated light paved strip ~2.5 m between the edge line and the
   guardrail + screen; photo: narrower red-brown strip, screen visibly closer and taller in the frame (top of the post at
   x 0.87: y 0.37 photo vs 0.45 render), concrete parapet with a dark plinth below the glass. The terrain seen through
   the glass near road level is a consequence of the low/transparent parapet, not of the pose (deck U 139.0 here).
3. **810896, Andersa SE of Putry (G3-B station ~245 m)**: the NW-bound carriageway is generated on a ~3-4 m retaining
   wall (`bridge` surface) right beside the SE-bound one (deck U 132.7); the photo has both carriageways at grade, a
   guardrail on the median kerb, a grass median and the opposite traffic at eye level, acoustic screens behind it, a
   truss portal with a green board at the far left. The B-23-like sign at the right is seen from its back in the render.
4. **482392 blue board**: a blue lane-direction board (straight + right arrow, two posts, F-10-type, designation
   UNVERIFIED) behind the right-hand guardrail under the western end of the Bieżeństwa viaduct; no such sign exists in
   `overrides.yaml` or the generated instances -> **world, not pose**. Estimate from the sa pose: bearing 283.5 deg from
   E 531.5 N -685.0, base ~15 px below the horizon -> ~38 m (E ~495 N ~-676, +-10 m along the ray). Needs the orthophoto
   / another frame before authoring. The W-beam along the slip also starts further on in the world than on the photo.
5. **Bieżeństwa viaduct piers** (482392, 320326): pier spec is by eye (`confidence: low`); both frames show the near
   pier pairs ~100 px off with any pose that matches the kerbs (also REVIEW s14-0128 P2-7, stream 0123).

## Validation

- Probe rounds r1 (16 probes + production, Low-overcast) and r2 (10), sheets `artifacts/sbs-poses-r3/r{1,2}/sheet-*.jpg`.
- Full Low set with the tool on this branch (regenerated world, preflight OK): `pwsh scripts/sbs-low-pairs.ps1
  -OutputRoot artifacts/sbs-poses-r3/after` (42 + 42 renders); before/after pairs for the changed frames, 960 px:
  `artifacts/sbs-poses-r3/pairs/Low-{overcast,clear}/` (photo | before over photo | after; before = old production
  poses rendered on the same regenerated world).
- `pytest tests/gis/test_sbs_gate3.py test_sbs_pairs.py test_sbs_photometry.py test_sbs_report.py tests/gate3`
  (heavy slot): 113 passed (`artifacts/sbs-poses-r3/pytest.log`).
- Author's look (D51 not re-graded): 494288 now a straight deck with the left bend far ahead, dash and edge line where
  the photo has them, screen right, lamp row left (lamps larger than on the photo, finding 1; right verge wider,
  finding 2); 320326 production now shows the nose / zebra corner under the viaduct as the 0128-reviewed probe;
  482392 kerb geometry as on the photo, no board (finding 4); 810896 camera on the carriageway, but the generated
  wall still fills the view (finding 3).

## Consequences / open

- `sbs_recognition.json` not touched: re-grade 494288 / 320326 / 482392 after the integration render (320326 only
  after `biezenstwa-island` is merged).
- 810896 remains a bad gate frame until finding 3 is fixed; keep it out of D51 grading.
- World follow-ups 1-5 for the world / furniture streams.
