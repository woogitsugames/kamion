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
- 23:20 (takeover agent) r4 viewed: roof at albedo 0.36 still 95.2 % luma (overcast chase) and featureless. Cause found: `TruckExterior.shader` replaces the
  baked dirt mask on the Curtain slot (`CurtainGrime`), so `_roof_stains` never reached the game; brightness = grazing sky reflection + D23 clip, not albedo.
  r5: ROOF_RGB 0.50 (aged white PVC, CRRC 0.68-0.70 aged / Miller 2002 30-50 % loss; WORKING_VALUE), ROOF_ROUGH 0.72, soiling baked into C.rgb / C.a
  (`ROOF_STAIN_ALBEDO`), `a6_export.emit_override` rdm reads a linked clean roughness. Trailer r5 export PASS (89 000 / 24 500 / 7 850), frames `r5/`.
  Roof box luma r4 -> r5: High overcast 95.2 -> 93.3 (sd 3.2 -> 4.9, 0 % >= 97 %), High clear 97.9 -> 96.0, Low overcast 90.2 -> 89.5. Pooled dirt now visible.
  Render exit 1 = shutdown flake (frames complete, mono cleanup abort_threads, no crash stack; hit High clear in r5, Low lowsun in r4): narrow accept rule in `scripts/visual-qa.ps1`.
NEXT: band A/B: `KAMION_LIVERY_BAND=0 blender -b ... trailer_export.py -- --no-renders` -> `unity.ps1 -Step build` -> render `-Out cmp-noband -Tiers High -Lights overcast -Cameras trailer-side,truck-rear34,chase`
  -> `git checkout -- art-source/truck/trailer/export` -> `unity.ps1 -Step build`; then `git merge main`, `unity.ps1 -Step test`, ADR Measured, copy to main artifacts.
- 23:27 band A/B rendered (`cmp-noband/`, sheets `owner-band/band_AB_{trailer-side,truck-rear34}.jpg`; B via `KAMION_LIVERY_BAND=0`, committed export = A with band).
  `git merge main` (e76aae5) clean, no conflicts. After merge: build OK, frames `r5-merged/` OK, EditMode 188/188, PlayMode TraktTruckRig + TrailerCargoSwap 2/2.
  Budgets: ext 104 514 / 43 000 / 17 689 (r2 export, unchanged), trailer 89 000 / 24 500 / 7 850; both check_export PASS. ADR 0083 Measured / Self-critique filled.
  Unity side effects reverted (LP_*.asset reserialised by the build after the merge, M_Sky, Quality/ProjectSettings).
NEXT (lead): visual-critic on `r5/` + `owner-band/`; owner decision band / skirts; phone frames; then merge the branch.
- 23:35 D47 (owner): variant B, NO band, skirts stay. `LIVERY_BAND` default off (env `KAMION_LIVERY_BAND=1` = band). Trailer r6 export PASS (89 000 / 24 500 / 7 850),
  build OK, frames `r6/High-overcast/{chase,trailer-side,truck-rear34}` viewed (plain curtain, roof 93.0 / sd 5.9), EditMode 188/188.
NEXT: visual-critic conditional PASS (docs/reports/visual/REVIEW-2026-11-10-0070-0083.md, section 0083): P0 confirm default export = B + frames Low/High x overcast/clear/lowsun; P1 curtain folds / dirt / patches, roof < 90 %, cab paint gloss, windscreen, headlamps.
- 23:55 review round (trailer r7, r8): `_curtain_wear` (widths, weld lines, patches, scuffs, hem film) baked into curtain albedo; roof per-bay dirt + sag, albedo 0.44, roughness 0.92.
  Roof chase luma: High overcast 83.6, High clear 89.0, Low clear 86.7. B confirmed in the tint mask. Matrix B in `r6/` (24 frames). Trailer 89 000 / 24 500 / 7 850 PASS. EditMode 188/188.
  NOT done (shader / runtime, not truck-artist files): review P1 5 cab paint reflections, 6 windscreen, 7 daylight headlamps; P2 8-13.
NEXT (lead): hand P1 5-7 to rendering-perf; phone frames (P0 no. 2); re-review `r6/` by visual-critic; merge.
