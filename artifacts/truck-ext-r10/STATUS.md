# truck-ext-r10 (ADR 0083) — TRAKT exterior + curtainsider, realism round r10 — truck-artist
Worktree `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\agent-a4049e15e1ab8c681`, branch `worktree-agent-a4049e15e1ab8c681` (from main 4c27a9b).
Setup: game/Library + game/Assets/_Generated robocopied from main, LFS pulled, interior LOD0 FBX copied (not in git). No Data/raw needed so far.

## Log
- 22:15 setup done; baseline frames: `pwsh artifacts/truck-ext-r10/tools/unity.ps1 -Step render -Out before -Tiers High,Low -Lights overcast,clear`
NEXT: look at before/*, write the gap list here, then edit tools/blender/truck/exterior/*.py and trailer/trailer_build.py.
- 22:40 baseline frames in `before/` (8 cameras; new QA cameras chase, truck-side, truck-rear34, trailer-side, truck-34r in TruckAssetBuilder; trailer-34 moved off the lamp post).
  Gap list (by impact): (1) tractor has no side skirts - bare chassis, small tank, reads as a stripped 90s unit; (2) curtain = flat uniform grey, no livery;
  (3) empty bay under the trailer between landing gear and tridem; (4) dark side extenders; (5) tractor rear lamps = boxes on a bar;
  (6) cab side is a flat slab below the window; (7) trailer roof plain from the chase camera.
- r1 code: chassis.side_skirt (SIDE_SKIRTS), side extenders body colour, trailer underfloor_equipment (spare wheel, pallet box, chocks), curtain band livery (LIVERY_BAND, tint mask).
NEXT: `bash artifacts/truck-ext-r10/tools/full.sh r1` (exports both, Unity build, frames) then look at r1/High-overcast/*.png.
- 23:05 r1 done (frames `r1/`, check_export PASS both; ext LOD0 103 474 / LOD1 43 000 / LOD2 17 690; trailer 88 999 / 24 494 / 7 847). Skirts + band read well.
  r1 self-critique: left trailer bay still empty (boxes were kerb side only), roof from the chase camera is a flat curtain-coloured sheet, tractor rear lamps are slabs.
- r2 code (not exported yet): pallet boxes both sides, toolbox 0.8 m forward, chocks, roof tarp own light grey + pooled dirt (ROOF_OWN_COLOUR), tractor multi-chamber rear lamps.
NEXT: `bash artifacts/truck-ext-r10/tools/full.sh r2` then look at r2/High-overcast/{chase,trailer-side,truck-rear34}.png; exported art is NOT committed yet (commit after the final round).
- 22:50 r2 + r3 done (frames `r2/`, `r3/`): pallet boxes both sides OK, tractor lamps OK; roof albedo 0.62 clipped white in chase (luma 97.6 %), 0.44 still 93.8 % ov / 97.7 % clear -> r4 uses 0.36.
  r3: curtain-only AO merged into the curtain islands: the black wavy strap lines on Low (present in `before/`) are gone.
- r4 running: `trailer_export` (roof 0.36, stains x1.0) -> build -> frames High/Low x overcast/clear/lowsun into `r4/`.
NEXT (if killed): rerun r4 = trailer export + `pwsh artifacts/truck-ext-r10/tools/unity.ps1 -Step build` + `-Step render -Out r4 -Lights overcast,clear,lowsun -Cameras truck-34,truck-front,trailer-34,chase,truck-side,truck-rear34,trailer-side,truck-34r`;
  then `-Step test`, fill ADR 0083 "Measured", `git add art-source/truck/*/export` (LFS) and commit, copy artifacts/truck-ext-r10 to the main checkout.
- 22:55 STOP at the 95 % limit (lead order). r4 exported + built + rendered (`r4/`, High/Low x overcast/clear/lowsun; Low lowsun render exit 1: NOT looked at).
  r4 frames NOT yet viewed (roof albedo 0.36 + stains: unverified). check_export PASS for both (ext r2 export: LOD0 104 514 / LOD1 43 000 / LOD2 17 689; trailer r4: 89 000 / 24 500 / 7 850).
  Exported art (FBX + atlases + manifests, r2 exterior / r4 trailer) is committed in this commit. EditMode tests NOT run. ADR 0083 "Measured" not filled. No visual-critic review, no phone.
NEXT: look at `artifacts/truck-ext-r10/r4/High-overcast/chase.png` (roof), then
  `pwsh artifacts/truck-ext-r10/tools/unity.ps1 -Step test` ; `bash artifacts/truck-ext-r10/tools/sheets.sh before r4` ; fill ADR 0083 Measured ; rerun `-Step render -Out r4 -Tiers Low -Lights lowsun`.
