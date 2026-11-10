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
