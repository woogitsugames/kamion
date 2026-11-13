# ADR 0173 — World determinism between builds: line-ending-free source hashes, no wall clock in derived data, per-candidate tree attributes

Status: implemented on branch `determ-0173` (base main `3a60019ff`, 2026-11-13, s17); not merged. Unity import +
renders re-run twice on identical data (main world) after PHONE_RUN cleared; the new world (run4) NOT imported/rendered. Supersedes nothing; extends ADR 0096
(PYTHONHASHSEED independence of the road stage).
Source: reviews `docs/reports/visual/REVIEW-2026-11-13-s17-0161.md` / `-0167.md` ("rozkład drzew/impostorów różni
się między buildami, 1–3 % pikseli", +7,5 % triangles in `stretch-05-docks`).

## Measurements

1. **Same code, two runs (worktree, `build_world.py --region bialystok-industrial-c`, 605 s each):** the 199 files of
   `Data/raw/derived/bialystok-industrial-c/world` (instances_*.json, GLB, HLOD, colliders) are **byte-identical**
   (`tools/worldgen/qa/compare_world.py`), `generated/` identical. The only differing file was
   `far_field_gis_cache.json` (`extracted_in_s` wall-clock field).
2. **Committed files that showed as modified after a rebuild in a worktree:** four were line endings only (git
   checkout CRLF vs generator LF, empty `git diff`). `world_manifest.json` changed two `sources_sha256` lines:
   `overrides.yaml` and `roads.graph.json` were hashed as raw bytes, and the worktree checkout has CRLF where main has
   LF (CRLF-stripped hash == committed hash). Content of the world did not change.
3. **So the generator is deterministic for fixed input; the reviewed differences come from different code/input
   between the two builds.** One mechanism made a *local* edit change trees *far away*: `vegetation.place.emit`
   drew height / variant / yaw / lean from the feature's random stream only for trees that passed the clearance
   test. A new kerb, paved area or building that removed one tree shifted the stream for every later tree of the
   same BDOT feature (whole forest stand, the understorey and edge passes after it, a whole tree row / group).

## Decision

- `build_world` and `far_field._sha256` hash text inputs (`.json/.geojson/.yaml/.yml`) with CRLF normalised to LF:
  the world manifest and the far-field cache key no longer depend on the checkout.
- No wall-clock time in derived data: `extracted_in_s` removed from the far-field GIS cache (printed instead).
- `vegetation.emit` draws the four attributes (same calls, same order as before) for **every candidate point**;
  the clearance test only drops the tree afterwards. A local edit now removes the trees on it and leaves every other
  tree as it was; a BDOT feature with no dropped candidate keeps its exact old stream.
- Tests (`tools/worldgen/tests/test_determinism_0173.py`, ~1 s): CRLF/LF hash equality; two `vegetation.place`
  runs identical; a 10 × 10 m blocked patch changes no tree further than 3 m from it (fails on the old code);
  classification of `compare_world.py` (identical / order only / content).
- Tool: `uv run --project tools/worldgen python tools/worldgen/qa/compare_world.py <dirA> <dirB>` — byte compare of
  two derived worlds, with order-only vs content diagnosis of instance files.

## Consequences

- One-time change of the look, only in features where the clearance test dropped a candidate: their later trees
  get new height / variant / yaw / lean, and the understorey and edge passes of such forest stands (positions drawn
  after the main pass) get new positions. Features untouched by roads / paving / buildings are bit-identical.
  After this, edits stay local. Chunk GLBs change slightly (forest HLOD / canopies derived from the trees).
- Unity side, measured: two `import-region.ps1 -Tiers Low` of identical data give `Instances.asset` files that differ
  byte-wise (Unity assigns random local fileIDs to sub-assets and writes them in fileID order) but are identical in
  content: 1076/1076 objects equal after mapping fileIDs to names (`tools/worldgen/qa/compare_unity_asset.py`).
  Two `visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear` runs on that import: 33/48 frames pixel-identical,
  the rest ≤ 0,018 % pixels (`stretch-05-docks` 0,015 %). So the 1–3 % tree differences in the reviews are NOT
  import or capture noise: they come from changed inputs/code between the two builds, amplified by the stream shift
  fixed here. The +7,5 % triangles of `stretch-05-docks` were not reproduced on identical data (not measured
  on the new world).
## Numbers of the one-time change (run1 = main code `3a60019ff`, run4 = this ADR; whole region)

| | run1 | run4 |
|---|---|---|
| trees + shrubs (instances_*.json) | 121 628 | 121 616 (−12) |
| same position | — | 100 626 (82,7 %) |
| fully identical record (position, species, h, v, yaw, lean) | — | 50 027 (41 %) |
| per prototype delta | — | shrub −131, birch +90, pine +30, maple +26, alder −22, linden −5 |
| derived files differing (of 199) | — | 152 (instances + chunk GLB / HLOD bytes, sizes within ±30 B) |

Two runs of the same code: 199/199 derived files byte-identical (after removing `extracted_in_s`).
Not measured: import/renders of the run4 world (one-time look change) — after merge: `build_world` +
`import-region.ps1` + SBS/visual-critic of the forest frames. Evidence: `artifacts/determ-0173/evidence.txt`.