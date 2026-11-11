# S10 GPT coordination — 2026-11-11

User: up to three workers A/B/C, then D/E, each isolated current-main worktree;
continuous WIP commits, status and final report. No merge/push to main.

## Step 1 — read and dispatch
Read S10/task01 rules, HANDOVER s9, CLAUDE, agent rules, anti-slop, performance,
visual-qa and efficient-delegation skills, s9 reviews. Main advanced during setup
from dd5fc794 to 4f7da66c (documentation only, adding F/G); all three workers
and this coordination worktree start at 4f7da66c.

| Stream | Agent | Branch / worktree | Status | State |
|---|---|---|---|---|
| A 0086 tint gamma | fab_processor | gpt-tint-gamma | artifacts/tint-gamma-r1/STATUS.md | COMPLETE 38149050, scoped independent PASS |
| B 0088 vegetation | tree_surfaces | gpt-vegetation-r2 | artifacts/vegetation-r2/STATUS.md | running: real CC0 pine-needle quality pass |
| C 0098 light/post | world_integration | gpt-light-r12 | artifacts/light-r12/STATUS.md | running: final shoulder/glass policy validation |
| D 0099 surface wear | pending | gpt-surface-wear | artifacts/surface-wear-r1/STATUS.md | dependency satisfied by 471438fb; after G/E |
| E 0090 fire station r7 | pending | gpt-firestation-r7 | artifacts/firestation-r10/STATUS.md | queued after G |
| F 0087 truck paint | fab_processor | gpt-truck-paint | artifacts/truck-paint-r1/STATUS.md | running from 232fbada: canonical baseline |
| G 0089 car paint | pending | gpt-car-paint | artifacts/car-paint-r1/STATUS.md | NEXT free worker |

A owns importer tint/calibration; B vegetation geometry, leaf ambient and grass;
C lighting/post/atmosphere/shadow policy. Shared shader edits must be additive
and explicitly reconciled in reports. No nested agents. Latest direct user
steering: when workers finish, dispatch F, then G, then E, then D.

Main had an existing modified generated/world_manifest.json; do not touch it.
No active argon-car-paint branch exists; C leaves 0089 to stream G.
0095 log hits are only assignment/review docs, not a merge: D is not cleared.

NEXT COMMAND: `git -C C:/Users/matma/Documents/Claude/kamion log main --oneline --grep="merge.*0095" -5`; monitor A/B/C status and review concrete evidence.

## Step2 - bootstrap and tint evidence
Allthreeworkerscommittedbootstrap andstartedfreshbaselinebuild. C/B caughtandrestoredcopy-inducedtrackedmaterialsource drift; A usedPNG-onlyfilters. AactualWorldPBRGPUreadbackconfirmsdoublegamma (.18->.0272118raw, gammaencoded->.18), isolatinglights/exposure; probeinspection reviewedbycoordinator. B retains3runtimebands: geometricLOD0/1 plusbillboardLOD2, noforbiddenroadpolicymirroredit; reportsmustdescribethiscontractexactly.
NEXT COMMAND: review workers baseline Low/High clear/overcast captures afterfreshimport; continue main0095mergegatewatch.

## Step 3 — independent baseline file proof
All three fresh worlds contain 192 files matching their own manifest. Their
sorted file/hash signatures are identical (7579ea53d9ce10288f7ffb42ab9581b49db92e0fe31ce933b0485b964ec56b74).
Proof: baseline-world-proof.json, produced by read-only compare-baselines.py.
Workers are importing fresh material caches before matched baseline captures.
NEXT COMMAND: review A/B/C baseline frames and measured material/crown/post metrics; `git -C C:/Users/matma/Documents/Claude/kamion log main --oneline --grep="merge.*0095" -5`.

## Step 4 — owner queue correction and QA harness audit
Re-read the complete task after the user's explicit update. Queue is now
F → G → E → D; D still requires the actual 0095 merge. Main now d1895536
(regenerated 0096 world, 355 passed / 2 xfailed per leader; A/B/C remain isolated
on their already verified identical source-world baselines).
All baseline/after conditions use full scene control cameras plus s9 Gate3
building cameras. Low loads WorldC, High loads WorldC_High explicitly; the QA
runner does not auto-select the High scene from -Tier. C will repair ablation
pipeline overrides only for explicit override fields, preserving empty-Rq
baseline behavior. No ProjectSettings or main source changes are authorized.
NEXT COMMAND: review full 4-condition baselines, then worker implementation and experiment evidence; dispatch F from current main at the first free worker slot.

## Step 5 — baseline visual review and first experiment decisions
Reviewed all 59 Low-overcast baseline frames via A's eight sheets; also full-size
960 previews of High-clear house and High-overcast DK8, plus real CC0 firestation
and road references. Visible baseline issues: black dense pine tops, repeated
grass edge strips, regular crowns; clear house highlights clip. All three fresh
materials_spec hashes match (46b9e45a41c1ffadbba6bb3a1ce774b82ea446de01e994875c74876b1cfc05b1).
A's pure gamma fix preserved asphalt (~74) but raised hall (~96→138) and screen
(~28→57). Screen photo range 36–40 justifies recalibration. Remiza Low is below
the ±10 band while High already passes; A is testing a common plaster-only
1.15 linear gain, leaving glass/roof alone, with E conflict explicitly flagged.
B's first shape gallery rejected as too subtle/clustered; continuous branch
attachments and stronger silhouettes are being rebuilt at lower triangle cost.
DK8 crown-only baseline Low p10/p50 18.64/31.15, lt16 5.43%; healthy Andersa/Putry
ROIs prohibit a global leaf brightening. B will use species/material policy.
C proved empty-override harness parity (max 2 LSB noise). Both dithers off gave
banding and was rejected. Pre-LUT sky dither off plus final dither retained and
RCAS off is under edge/sharpness validation; original route exposure is healthy.
NEXT COMMAND: review A calibrated frames, B revised silhouettes/scene metrics and C edge/highlight diagnostics; keep the F→G→E→D queue and 0095 gate.

## Step 6 — real 0095 merge and focused review findings
Main advanced to 232fbada, with actual merge 471438fb (ADR0095). D's dependency
is now satisfied; dispatch order remains F, G, E, D as directly instructed.
A/B/C retain their fixed 4f7 baselines; future worktrees start from current main.
B's missing-Fab-hook suspicion was checked and retracted: streetscape/stage.py
line180 calls FD.apply, invoked by roads/build_world.py SS.run. B's actual nested
furniture.megascans has 15 available, 320 props, 954 replacements, 197 covers.
No source correction was needed or made.
A's first calibrated 236-frame matrix hits both remiza RGB bands and screen
reference range. Reviewed all 59 Low/High overcast matched pairs and key full
960 pairs: found curtain-family regression (dock3 ~55→112 sRGB), now separately
recalibrated against accepted 0092 cloth appearance. Canonical truck cache was
refreshed after that matrix: EditMode226/226 passes, GIS358 passes/2xfail before
last pigment-only change. Mixed vehicle fixtures must not be presented as a
matched whole-frame zero-cost proof; old-fixture matrix and canonical tests are
separately labeled. Final curtain frames/testing remain pending.
B focused same-frame DK8 Low p10/p50 improves18.64/31.15→32.72/43.36; lt16
5.43%→0. No draw increases in five Low/High focus cameras; full matrix pending.
C shadow split/bias tests improve trailer stair bands; generic glazing offsets
did not affect the actual hero glass material. C owns a tiny additive explicit
_ArchitecturalGlass setter in RegionImporter for kp_glass_block and is testing
bounded receiver bias; A notified of the separate common-file ownership.
NEXT COMMAND: finish independent A/B/C visual/code reviews and final tests; start F on the first free slot from latest main, then G/E/D.

## Step 7 — A complete, F dispatched; B/C final quality work
A complete at38149050 (implementation ab738b01), clean branch, no merge/push.
Independent scoped PASS saved in REVIEW-A-0086.md and copied/committed with A.
Final GIS359 passed/2 xfailed; EditMode226/226 including14 numeric tint tests.
All four-condition clearance covers59 cameras; final curtain regression resolved.
REPORT/ADR encoding was repaired, last validated SHA and fixture caveat explicit.
F is now running in its own current-main232fbada worktree, with canonical truck
build/install before baseline images and its own fixture SHA snapshot.
B's detached procedural pine cards remain a quality issue after the metrics pass;
coordinator verified/downloaded two official CC0 pine_tree_01 twig maps and
provided pinned source records. B is evaluating a clean crop at the same texture,
material and triangle budget, with no Fab source embedded in public assets.
C's8cm architectural-glass receiver offset removes the gross triangles while
measured narrow frame shadows remain;12cm is flatter. Keep smallest tested
acceptable8cm on kp_glass_block only, Medium/High only, with Low/casters unchanged.
Clear highlight shoulder still needs measured red<=240; do not call it passed yet.
NEXT COMMAND: review B full-needle world and C final empty-Rq matrix/tests; next free worker starts G from then-current main, followed by E and D.
