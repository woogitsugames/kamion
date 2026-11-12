# ADR 0141 — Map edge and background: far skyline beyond the Low far plane, road closures in render groups

Status: implemented on branch `edge-r6c` (base main `76c88d4fd`, main `611f116c9` merged in, 2026-11-12, s13); not merged.
A visual-critic review is still required; the D51 notes below are the author's. Phone: NOT measured (see Risks).
Source: ADR 0129 open point "kominy EC poza far clip Low (1187 m > 900 m)", ADR 0126 open point "kominy EC za
pierzeją", GPT handover `edge-r6` (B9 skyline, closures), ADR 0082 / 0085 / 0121 (map edge, far-field), ADR 0116 (EC stacks).

## Context

1. **Skyline.** The Low tier has a 900 m far plane. In four G3-B photo frames (Mapillary 3281350541967811,
   150280503737744, 297817221966185, 1528935774382039; CC BY-SA 4.0, reference only) the two red/white EC Białystok
   stacks stand 1251–1475 m from the camera (`artifacts/edge-r6c/skyline_probe.py`), so on Low they were cut by the
   far plane and the horizon behind the trade frontage was empty. The same applies to the tall blocks of the far-field
   ring seen from the DK8 viaduct: the whole western far-field sector is beyond 900 m.
2. **Closures.** The 36 road closures at the region edge were one renderer each with 4 materials (4 draws per
   closure) and a single U-20 board without a sign.
3. Diagnosed and **not** changed here: in SBS 303305168125936 the 48–56 m blocks (elevation +2.5..+3.7°, 645–741 m)
   are hidden by the BDOT forest `2BE4B432-6BC0` (pines 21–23 m at 160–240 m, elevation +4.4..+5.8°), i.e. by
   region vegetation, not by the far-field; the pose of that frame also has ~11° heading error.

## Decision

1. **Generator** (`tools/worldgen/streetscape/far_field.py`): a separate glTF node `far_skyline` in both far-field
   tiers. It receives, with unchanged geometry, ring buildings with source height >= 24 m (block / office / hall) and
   ring chimneys >= 40 m (both thresholds WORKING_VALUE: 24 m at 900 m is 1.5° above the horizon). A ring chimney
   within 25 m of a region landmark stack (`overrides.yaml kind=landmark` + `ec_chimneys.json`) is dropped and
   replaced by a plain banded cone with the stack's source height, diameters and band limits ("stand-in"). No
   position or height is invented. The flag travels in `TEXCOORD_1.x`: `-(x + 16)` = "clamp" (visible at any
   distance), `-(x + 4096)` = "beyond" (visible only behind the far plane). Triangles are sorted far-to-near.
2. **Shader** (`WorldSurface.shader`, only under `_FAR_FACADE`, i.e. only `M_far_field_buildings`; ForwardLit and
   DepthOnly): `KamionFarSkyline` changes clip-space z only. Screen position, perspective size and fog distance stay
   true. "clamp" vertices farther than `far - 40 m` are held 40..30 m in front of the far plane and at least
   4e-6 NDC in front of it (the URP skybox is drawn ~1e-6 NDC in front of the far plane; measured in the editor:
   3–6 m = 3.7e-7 NDC was overwritten by the sky). "beyond" is the exact complement of the far-plane clip, so the
   stand-in appears where the region's hero mesh is cut and the two never overlap. Orthographic cameras: unchanged /
   no stand-in. The far plane, fog and every other material are untouched.
3. **Import** (`WorldEdgeBuilder.BuildFarField`): renderer `WorldEdge/FarSkyline`, bounds = whole tile, no shadows.
4. **Closures** (`WorldEdgeBuilder`): colliders stay one box per closure. The visible part is clustered by single
   linkage at 150 m (WORKING_VALUE) into render groups, one mesh per group with 2 materials (concrete barriers;
   paint as linear vertex colour on the far-field paint material): 2 draws per group instead of 4 per closure.
   Each closure: concrete barrier row (2.0 m elements, 0.60 / 0.20 / 0.81 m), in front of it a double U-20 board
   (0.25 m boards, 0.5 m red/white fields as ADR 0082; 0.20 m gap and 1.20 m top edge WORKING_VALUE) and, on
   carriageways >= 5.5 m, a B-1 disc (0.90 m, rim 0.09 m, centre 1.85 m: WORKING_VALUE).

## Validation

Run on the branch after `git merge main` (`611f116c9`, no conflicts) and a full regeneration.

- `build_world.py`: 615 s, exit 0. Far-field Low 24500 -> 24548 tris (skyline node 2024), High 118524 -> 118588
  (skyline 5296); stand-ins: `ec-bialystok-chimney-1`, `ec-bialystok-chimney-2` (`far_field_qa.json`).
- Closures: 36 closures in 6 render groups, 8588 tris (rebuild log).
- `pytest tests/gis tests/gate3` (heavy slot, 14 min): 845 passed, 1 xfailed, 1 failed =
  `test_road_fidelity::test_report_not_stale` (the report on main is stale after the CRLF hash fix `a4cb9995`);
  after `fidelity/run.py` (exit 0, report committed) `tests/gis/test_road_fidelity.py`: 9 passed, 1 xfailed.
  New: `tests/gis/test_far_field.py` skyline cases (55 passed in the far-field files).
- EditMode: 412 total, 412 passed, 0 failed (`editmode-merged.log`, after the second merge of main `97996ef6b`; includes the 4 `WorldEdgeClosureSkylineTests`).
- import-region: `IMPORT_RESULT: OK`, 64 chunks, corridor 41, tiers Low+High; WORLD_MEMORY Low 122.7 MB (far_field 1.3 MB), High 264.8 MB (far_field 6.5 MB) (`import-merged.log`).
- Budget, Low, 120 cameras (control + gate3 + 42 SBS), `artifacts/edge-r6c/stats-diff.py`:

| Run | draws (min / median / max) | shadow casters (sum) | trisK (sum) |
|---|---|---|---|
| after vs baseline (same base main `76c88d4fd`, clean A/B) | -51 / -13 / +3 | 0 | +116 of 33055 (+0.35 %) |
| merged vs baseline (also contains main `76c88d4fd..97996ef6b`: ADR 0139, 0140, 0143) | -51 / -13 / +140 | -28 | +434 of 33055 (+1.3 %) |
| merged vs after (= what main `76c88d4fd..97996ef6b` added, not this ADR) | -21 / 0 / +139 | -28 | +318 of 33171 |

  The +1..+3 draws are the skyline renderer; the savings are the closure groups. Budget not worsened. The +140
  draws / +191 trisK outlier of the merged run is one camera, `sbs-g3-b-494288258686575`, whose pose ADR 0143 moved
  41 m back (main, not this ADR); edge, g3a and g3b route cameras are identical between after and merged.
- Second merge of main (`97996ef6b`, generated conflicts -> ours) + full regeneration chain
  (`artifacts/edge-r6c/run-merged.ps1`): build_all, build_world, fidelity, pytest, import, EditMode, visual-qa all
  exit 0; `pytest tests/gis tests/gate3`: 853 passed, 1 xfailed (879 s).
- Pairs (photo | before | after for SBS frames, before over after for control cameras), 960 px:
  `artifacts/edge-r6c/pairs/{Low-clear,Low-overcast}/*.jpg` (101 + 101), merged run:
  `artifacts/edge-r6c/pairs-merged/`; full-resolution horizon crops `artifacts/edge-r6c/crops/`.

### D51 (author's notes; visual-critic pending)

- 297817, 3281350, 150280, 1528935 (Low, clear and overcast): both EC stacks now stand on the horizon behind the
  frontage, red/white bands readable, in the direction where the photos show them; before: empty sky. This closes
  the open point of ADR 0129 on Low.
- P1-2 of `REVIEW-2026-11-12-s14-0139` (stacks on Low in 297817 and 150280 on the poses of main, ADR 0140 / 0143):
  merged run, Low-clear and Low-overcast, both stacks visible in both frames, lower part correctly hidden behind
  the pine belt, no flicker pattern in the 4x crop (`crops/ec-chimneys-merged-4x-297817-150280.jpg`,
  `crops/ec-297817-merged-b-vs-m-clear-overcast.jpg`, `crops/ec-150280-merged-b-vs-m-clear-overcast.jpg`). In
  overcast they are faint (tier fog) but readable. Editor render only; phone is risk 1.
- 150280 (pre-0143 pose): the stacks in the render are visibly smaller and further left than on the photo (crop
  `crops/z150280.jpg`). Position and height come from source data, so this is the SBS pose / FOV of that frame, not
  the skyline; not corrected here.
- `edge-*`: closures read as a closed road (double board + B-1) instead of a bare striped plank.
  Correction (r6d): the first version of this note also named `dk8-dk19-exit`. That camera has no closure in
  frame (before and after are the same picture apart from the changes of main); the claim was wrong and is withdrawn.
- Not done: haze on the stacks is the ordinary distance fog of the tier; at 1.3–1.5 km on Low-clear they are a
  little crisper than on the photos (owner / critic call).

## Revision r6d (review `REVIEW-2026-11-12-s15-0141`, branch `edge-r6d`)

1. **Doubled B-1 discs on `edge-west` (P1).** Cause: at the west edge each carriageway of Maczka (10 m) and its
   `trunk_link` (7 m / 6.5 m) are separate graph edges cut by the region edge; their closures stood 0.5 m and 0.9 m
   apart (WorldC scene), each with its own barrier row, boards and B-1. Fix in the importer
   (`WorldEdgeBuilder.MergeOverlappingClosures`): parallel closures (heading within 25 deg, at most 8 m apart along
   the road: WORKING_VALUE) whose barrier spans overlap become one visible closure over the union of both spans, in
   the frame of the wider road - one barrier row, one pair of boards, one B-1 per carriageway. Carriageways with a
   median between them and crossing roads stay separate. Colliders and `WorldBoundary.closures` are unchanged (one per
   road, `WorldEdgeRecoveryTests` contract). The closures are built in the Unity importer, not in the Python
   generator, so the regression test is EditMode (`WorldEdgeClosureSkylineTests`, 3 new cases with the scene
   coordinates of the four Maczka closures), not pytest.
2. **Grey "white" on U-20 / B-1 (P1).** The albedo was already linear 0.62 = sRGB 0.81 (the far-field chimney white),
   the material has no extra fog or AO: `far_field_buildings` is plain `Kamion/World Surface` with ordinary tier fog,
   SH ambient and baked sky visibility. In `edge-west` the boards face east and are in their own shade (ambient
   only), so the white dropped to the tone of the sunlit concrete behind; in `edge-north` (sunlit boards) the same
   paint rendered white. Sign sheeting is brighter than weathered chimney paint: white 0.62 -> 0.80 linear
   (sRGB 0.91), red 0.38 -> 0.52 linear (sRGB 0.75), both WORKING_VALUE. Chimney colours unchanged.
3. **Pine belt hides ~45 % of the stacks (P2): not changed.** The belt is BDOT forest `2BE4B432-6BC0`; its trees
   (pine 20.7 - 23.7 m, 400 - 470 m from the 297817 camera, elevation +3.3 .. +4.1 deg against about +5.4 deg for
   the top of a 120 m stack at 1.3 km) get their height from the species range of `vegetation.py`, not from a
   measurement. There is no canopy height source in the pipeline (no NMPT / lidar DSM in `Data/raw/gugik`), so the
   data cannot be called wrong or right here; lowering the trees to fit one photo would be a guess. Open: ingest
   GUGiK NMPT and derive forest heights from NMPT - NMT (separate task).

Validation r6d (branch from main `ca0bc16e0`; `RebuildEdgeBatch` on the scene imported for this ADR, no reimport):

- Rebuild log, both tiers: 36 closures, 34 visible after merging overlaps, 6 render groups, 8060 tris (was 8588).
  Render groups, materials and colliders unchanged, so draws are unchanged.
- EditMode: 423 total, 423 passed, 0 failed (`artifacts/edge-r6c/editmode-r6d.log`).
- `pytest tests/gis`: 886 passed, 1 xfailed, 1 failed = `test_road_fidelity::test_report_not_stale`. The report on
  main is stale for `tools/worldgen/roads/*.py` (import clean-up merged to main); this branch changes no Python and
  no data. Needs `tools/worldgen/fidelity/run.py` on main (integration).
- Renders Low clear + overcast, before = `merged`, after = `r6d` (`artifacts/edge-r6c/crops/r6d-*.png|jpg`):
  `edge-west` one B-1 per carriageway, no overlapping board rows; the white fields are clearly lighter than the
  concrete in overcast and on sunlit boards (`edge-north`); in `edge-west` clear the boards are still in their own
  shade and read light grey, lighter than before - that is lighting, not albedo. 297817: stacks unchanged
  (full-frame RMSE 0.0002 against `merged`).

## Risks / open

1. **GLES / Vulkan on the phone: UNVERIFIED.** The skyline depth sits 4e-6 NDC in front of the far plane. On a
   24-bit or 16-bit depth buffer, or with a non-reversed z (GLES3), the skyline can lose against the skybox or
   z-fight with it. `KamionNdcInFrontOfFar` has a non-reversed branch (`1 - 8e-6`) that was never executed on a
   device. To check on A16 during integration (Low, frame 297817 / route G3-B): stacks visible, no flicker; if not,
   raise the two constants or draw the skyline renderer after the skybox.
2. Beyond the far plane all skyline objects share almost one depth; ordering relies on the far-to-near index order
   inside one mesh. Region geometry closer than the far plane always wins (correct).
3. Thresholds 24 m / 40 m / 150 m link distance and the sign dimensions are WORKING_VALUE.
4. Known, not from this branch: 2 EditMode failures in `CarPaintMaterialTests` (present on main).
5. `docs/adr/README.md` index not regenerated here (`tools/docs/adr_index.py`, leader).
