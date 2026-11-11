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
| A 0086 tint gamma | fab_processor | gpt-tint-gamma | artifacts/tint-gamma-r1/STATUS.md | running: bootstrap and diagnosis |
| B 0088 vegetation | tree_surfaces | gpt-vegetation-r2 | artifacts/vegetation-r2/STATUS.md | running: bootstrap and diagnosis |
| C 0098 light/post | world_integration | gpt-light-r12 | artifacts/light-r12/STATUS.md | running: bootstrap and diagnosis |
| D 0099 surface wear | pending | gpt-surface-wear | artifacts/surface-wear-r1/STATUS.md | wait for actual merge of 0095 into main |
| E 0090 fire station r7 | pending | gpt-firestation-r7 | artifacts/firestation-r10/STATUS.md | after a worker completes |
| F 0087 truck paint | pending | gpt-truck-paint | artifacts/truck-paint-r1/STATUS.md | added by updated task document; queue |
| G 0089 car paint | pending | gpt-car-paint | artifacts/car-paint-r1/STATUS.md | added by updated task document; queue |

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
