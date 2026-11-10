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
