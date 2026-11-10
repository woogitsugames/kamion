# ADR 0083 — TRAKT exterior + curtainsider r10: side skirts, under-floor equipment, curtain livery band, roof sheet, rear lamps

Status: proposed (truck-artist, 2026-11-10). **Not reviewed by `visual-critic`** (the author does not approve his own
work). Editor frames only (WorldC, tiers High / Low, overcast / clear): **UNVERIFIED on a phone**.
Source: owner order for session 6 ("strong jump in look quality"), lead brief r10. Continues ADR 0061 / 0072 (front,
low sun: not touched here).
Evidence: `artifacts/truck-ext-r10/` (`before/` = main 4c27a9b built in the worktree, `r1/`, `r2/`, `r3/` = rounds,
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
- Roof sheet (`ROOF_OWN_COLOUR`): own light-grey PVC (albedo 0.44, tint mask 0) with dirt pooled between the bows and
  run-off along the edges (`_roof_stains`, goes into the baked dirt mask). r2 used albedo 0.62: the roof clipped to white
  through the D23 curve in the chase frame (luma mean 97.6 %, 95 % of the box >= 97 %), hence 0.44.
- Curtain AO: the sheets' own AO replaces the static AO inside the curtain islands (max of the two), so dropped straps
  leave no black line; the strap colour stays in the albedo there.
- Control cameras (`TruckAssetBuilder.AddControlCameras`): new `chase` (CameraRig framing with a trailer: 26 m behind,
  7.5 m up, 50 deg), `truck-side`, `truck-rear34`, `trailer-side`, `truck-34r`; `trailer-34` moved off the lamp post.
- LOD lists: skirt panel kept to LOD3, skirt / box small parts dropped at LOD1 / LOD2. No new material, slot, texture,
  shader property or keyword: draw calls per tier unchanged (same parts and slots).

## Measured
See the table at the end of `artifacts/truck-ext-r10/STATUS.md` (filled from the final export logs and manifests).

## Self-critique (docs/06 §2), author's view only
See `artifacts/truck-ext-r10/STATUS.md` "Self-critique".

## Open
1. `visual-critic` review; phone frames (A16 Low, S24+ High) of `chase`, `truck-side`, `trailer-side`.
2. Owner decision on the curtain band (art direction) and on the skirts (they hide the tank the A4 sheets showed).
3. Low tier: trailer LOD2 wheel discs are visibly broken by decimation (present before r10, not touched).
4. Tractor lens colours are flat saturated tiles in daylight (shader / Lights slot, not geometry).
5. Cab side below the window is still a plain pressed panel (no crease); cab shell shape is owner-approved (D28 / D29)
   and was not touched.
