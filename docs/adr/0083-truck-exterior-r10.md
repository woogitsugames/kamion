# ADR 0083 — TRAKT exterior + curtainsider r10: side skirts, under-floor equipment, curtain livery band, roof sheet, rear lamps

Status: proposed (truck-artist, 2026-11-10). `visual-critic`: **conditional PASS**
(`docs/reports/visual/REVIEW-2026-11-10-0070-0083.md`, section 2). Owner decision **D47: no curtain band, skirts stay**. Editor frames only (WorldC, tiers High / Low, overcast / clear / lowsun): **UNVERIFIED on a phone**.
Source: owner order for session 6 ("strong jump in look quality"), lead brief r10. Continues ADR 0061 / 0072 (front,
low sun: not touched here).
Evidence: `artifacts/truck-ext-r10/` (`before/` = main 4c27a9b built in the worktree, `r1/` .. `r5/` = rounds, `r5-merged/` = after `git merge main`, `cmp-noband/` + `owner-band/` = curtain band A/B,
`sheets/` = before / after pairs, `blender/` = Cycles check renders, `logs/`, `STATUS.md`).

## What was wrong (seen in the `before/` frames, by impact from the chase / exterior cameras)
1. **Tractor had no side skirts**: between the step box and the drive axle only a 0.6 m tank and black boxes hung on the
   frame, the gap under the cab-to-trailer line was see-through. In the side and 3/4 views the unit read as a stripped
   chassis, not a long-haul tractor.
2. **Curtain was one flat grey sheet** (13.6 m x 2.7 m of a single tint): the largest surface of the combination had no
   graphic at all and read as a placeholder.
3. **Empty bay under the trailer floor** between the landing gear and the tridem (only two guard rails and a tool box).
4. **Roof sheet in the chase camera** (the view the player drives in) was the curtain colour, flat.
5. Side extenders behind the cab were black plastic slabs; tractor rear lamps were a slab with three flat tiles.
6. On Low (trailer LOD2) the curtain showed **black wavy lines** where the straps are dropped: the static AO bake had the
   straps as occluders 2 mm off the sheet.
7. The control camera `trailer-34` had a lamp post in the middle of the frame; there was no chase, side or rear-3/4
   control camera at all, so none of the above was ever in a control frame.

## Decision (all generated: `tools/blender/truck/exterior/*.py`, `tools/blender/truck/trailer/*.py`; no hand edits)
- `chassis.side_skirt` (`SIDE_SKIRTS`): body-colour skirt per side, y -1.158 .. -3.07 m, z 0.48 .. 1.205 m, 16 mm, rear
  cut-out R 0.68 m about the drive axle, fuel-filler notch on the driver side, panel joint, pressed swage line,
  quarter-turn latches, top return flange, six heat vents over the aftertreatment box, stays to the frame. The dark sill
  strip and its amber markers stay. Sizes are class-typical **WORKING_VALUE** (not measured on a vehicle).
- Side extenders: body colour (rubber trailing flap stays black).
- Tractor rear lamps: deep moulded housing, bezel, four crowned chambers (indicator / tail-stop / reverse / reflector),
  amber side marker in the outboard end. Light groups unchanged (`rear_lens_*` naming).
- `trailer_build.underfloor_equipment`: pallet box on both sides (black body, two galvanised drop doors with ribs, paddle
  latches, hinges, hanger straps), spare wheel 385/65 R22.5 in a hanging carrier (kerb side), two wheel chocks in a
  holder (driver side); the tool box moved 0.80 m forward. **WORKING_VALUE** sizes.
- Curtain livery (`LIVERY_BAND`): a broad diagonal band + pinstripe left in the untinted fabric white through the tint
  mask (`_livery_mask`, node label `tint_mask`, read by `trailer_export.emit_tint_mask`). No name, no logo; every curtain
  colour of the game gets the two-tone graphic from the same bake. Art-direction choice: the owner may veto
  (`LIVERY_BAND = False` restores the plain curtain).
- Roof sheet (`ROOF_OWN_COLOUR`): own white PVC, tint mask 0. Clean-sheet albedo **0.50**, roughness 0.72. Source for
  the albedo (building membranes, the closest published data; no measurement of a trailer sheet found, so
  **WORKING_VALUE**): white PVC single-ply solar reflectance 0.87-0.88 new and 0.68-0.70 after three years (CRRC values
  in the Duro-Last and Siplast Parasolo data sheets); field studies report a 30-50 % loss in three years (Miller et al.
  2002, cited by ORNL) = 0.44-0.61. A trailer roof is never washed: lower half of that range.
  History: 0.62 (r2), 0.44 (r3) and 0.36 (r4) all gave a featureless near-white roof in the chase frame (95.2 % luma at
  0.36). Cause found in r5: `TruckExterior.shader` replaces the baked dirt mask on the Curtain slot with the procedural
  `CurtainGrime` (curtain faces only), so the roof was rendered clean, and at the chase angle (about 10 deg grazing) the
  sky reflection plus the D23 white clip dominate over the albedo. Fix without touching the shader: the soiling (dirt
  pooled in the sag between the bows, run-off along the edges, dusty film; `_roof_stains`) is baked into the roof
  islands' **albedo and roughness** (`ROOF_STAIN_ALBEDO`, soot 0.10), not only into the dirt mask.
  `a6_export.emit_override` (rdm) now reads a linked clean roughness (was: default value only).
- Curtain AO: the sheets' own AO replaces the static AO inside the curtain islands (max of the two), so dropped straps
  leave no black line; the strap colour stays in the albedo there.
- Control cameras (`TruckAssetBuilder.AddControlCameras`): new `chase` (CameraRig framing with a trailer: 26 m behind,
  7.5 m up, 50 deg), `truck-side`, `truck-rear34`, `trailer-side`, `truck-34r`; `trailer-34` moved off the lamp post.
- LOD lists: skirt panel kept to LOD3, skirt / box small parts dropped at LOD1 / LOD2. No new material, slot, texture,
  shader property or keyword: draw calls per tier unchanged (same parts and slots).

## Measured (final state: exterior r2 export, trailer r5 export, after `git merge main` e76aae5)
| what | main 4c27a9b | r10 | limit (validator) |
|---|---|---|---|
| exterior LOD0 / LOD1 / LOD2 tris | 102 729 / 42 999 / 17 690 | 104 514 / 43 000 / 17 689 | 140 000 / 45 000 / 17 900 (`TRI_LIMIT`), check PASS |
| trailer LOD0 / LOD1 / LOD2 tris | 89 000 / 24 497 / 7 850 | 89 000 / 24 500 / 7 850 | 90 000 / 25 000 / 8 000, check PASS |
| materials / slots / textures / keywords | - | unchanged | - |

Exterior LOD0 grew by 1 785 triangles (skirts, lamps); the trailer stayed at its decimation target.
Roof box in the chase frame (130 x 110 px at 2340 px, grey mean / sd, share of pixels >= 97 %):
| frame | r4 (0.36, stains lost) | r5 (0.50, stains baked) |
|---|---|---|
| High overcast | 95.2 / 3.2 | 93.3 / 4.9, 0 % |
| High clear | 97.9 / 2.9 | 96.0 / 4.1, 28 % (sunlit white sheet) |
| High lowsun | 72.8 / 1.3 | 72.4 / 2.1, 0 % |
| Low overcast | 90.2 / 1.9 | 89.5 / 2.6, 0 % |
After the merge (main's new overcast): High overcast 93.0 / 5.9, Low overcast 89.5 / 3.4.
Tests after the merge: EditMode 188 / 188 passed (15 Truck / Trailer / Trakt cases among them); PlayMode
`TraktTruckRigTests` + `TrailerCargoSwapTests` 2 / 2 passed. Frame time, draw calls on a phone: **not measured**.

## Render exit 1 (r4 Low lowsun, r5 High clear)
Not a render fault: 2 of 18 visual-qa runs ended with a non-zero Unity exit code AFTER `VISUALQA_RESULT: OK rendered=8`
and all eight PNGs on disk; the log stops in `Cleanup mono` / `abort_threads: Failed aborting id ...` /
`debugger-agent: Unable to listen`, with no crash stack (different from the ADR 0051 D3D12 SaveCache crash). The same
tier / light passed on the next run. `scripts/visual-qa.ps1` now accepts exactly this case (result OK, N fresh PNGs,
`Cleanup mono` and `abort_threads` after the result line, no crash marker in the log) and prints a warning with the exit
code; everything else still fails. The exit code itself was not captured (the wrapper printed only the last lines).
`scripts/` is outside the truck-artist ownership: lead / build-qa to confirm.

## Curtain band A/B for the owner
`artifacts/truck-ext-r10/owner-band/band_AB_trailer-side.jpg`, `band_AB_truck-rear34.jpg` (A = with the band, B = plain
curtain; High overcast, same build otherwise). B is exported with `KAMION_LIVERY_BAND=0` (env switch of
`trailer_build.py`); the committed export is A. The skirts are in both.

## Self-critique (docs/06 par. 2), author's view only
- The band is a generic "fleet swoosh": it breaks the 13.6 m grey sheet, but it is also the most game-like element of
  the round. Plain B is closer to the anonymous rental curtainsiders in the references; A reads better at chase distance.
- Roof: pooled dirt is regular (three bays per panel, same phase on every panel); a real sheet has one or two bays much
  worse than the rest and patches. Acceptable at chase distance, visible from a bridge.
- Skirt panel is flat with one swage line; the latches are small. Clean, slightly "new".
- Tractor rear lamp lenses are saturated flat tiles in daylight (shader side).

## D47 and the review round (r6 - r8, trailer only; exterior export unchanged)
- **D47 (owner, 2026-11-10): variant B.** `LIVERY_BAND` is off by default; the band code stays behind
  `KAMION_LIVERY_BAND=1`. The committed trailer export is B: the tint mask (`T_Trl_Curtain_M`, blue channel) has no
  diagonal band any more (checked against the A export of commit 46f09b6). Sections above that describe the band
  describe variant A.
- Review P0 no. 1: frame matrix of B in `artifacts/truck-ext-r10/r6/` (High / Low x overcast / clear / lowsun; chase,
  trailer-side, truck-side, trailer-34; 24 frames, all six runs exit 0).
- Review P1 no. 3 (plain curtain = one grey): `_curtain_wear` bakes into the curtain albedo: tone steps between five
  welded widths (2.72 m, WORKING_VALUE) with weld lines, low-frequency blotches, chalked upper part, horizontal scuffs
  at loading height, three welded patches (one on the driver side, two on the kerb side), a road-film band along the
  hem that is heavier behind each axle and towards the rear. No graphic. The folds were already in the geometry and
  the normal map. Author's view: the result is still restrained; the hem band on the front half is weak.
- Review P1 no. 4 (roof): per-bay random dirt amount and off-centre pools (one or two bays clearly dirtier), run-off
  streaks instead of an even border, per-bay sag 3-11 mm (was 10 mm everywhere), albedo 0.44 (lower end of the cited
  range), roughness 0.92 (dusty, matt: the grazing sky reflection was the main term).
  Roof box in the chase frame, grey mean / sd: High overcast 83.6 / 4.3, High clear 89.0 / 4.3 (0.2 % >= 97 %),
  High lowsun 70.0 / 2.0, Low overcast 83.3 / 2.8, Low clear 86.7 / 2.1, Low lowsun 70.0 / 1.6.
- Trailer r8 export: 89 000 / 24 500 / 7 850, check PASS. EditMode 188 / 188.
- **Not done, not in the truck-artist ownership** (shader / runtime, each with its own ADR history; left for
  rendering-perf / vehicle): review P1 no. 5 cab paint reflections (`TruckExterior.shader`; the paint already has
  clear coat 1.0 at roughness 0.08, the chalk look comes from the dirt / tone path), no. 6 windscreen
  (`Kamion/Truck Glass`), no. 7 headlamps in daylight (`TruckLights.cs` light state + Lights slot emission).
  P2 no. 8 - 13 not started.

## Open
1. `visual-critic` review; phone frames (A16 Low, S24+ High) of `chase`, `truck-side`, `trailer-side`.
2. (closed by D47: no band, skirts stay.)
3. Low tier: trailer LOD2 wheel discs are visibly broken by decimation (present before r10, not touched).
4. Tractor lens colours are flat saturated tiles in daylight (shader / Lights slot, not geometry).
5. Cab side below the window is still a plain pressed panel (no crease); cab shell shape is owner-approved (D28 / D29)
   and was not touched.
6. Shader: the Curtain slot ignores the baked dirt mask everywhere, so the dirt slider does not change the roof
   (rendering-perf, if a washed roof is ever wanted).
7. `LICENSES.md`: no new asset, texture or third-party data in this round (procedural only).
