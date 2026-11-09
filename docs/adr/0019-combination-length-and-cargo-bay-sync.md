# ADR 0019 - Combination length 16.50 m and cargo bay synced to the trailer model

Status: accepted (2026-11-09). Extends ADR 0014 (dims.json is the single source).

## Context
The trailer export manifest (`physics_crosscheck`) listed three open mismatches:
1. Tractor front -> kingpin = front_overhang 1.45 + wheelbase 3.70 - fifth_wheel_lead 0.55 = 4.60 m; with kingpin -> rear
   12.00 m (96/53/EC Annex I 1.6, trailer already at the limit) the combination was 16.60 m > 16.50 m (Annex I 1.1).
2. Physics cargo envelope: floorHeight 1.30 + height 2.70 = 4.00 m = legal maximum, no room for roof structure. The model
   has a clear height of 2.58 m under the top rail (~2.66 m under the bows).
3. cargoBay.frontZ 1.55 (physics) vs 1.572 (model, front wall 28 mm deep).

## Decision
- `fifth_wheel_lead_m` 0.55 -> **0.68 m** (WORKING_VALUE). Combination = 1.45 + 3.70 - 0.68 + 12.00 = **16.47 m**
  (3 cm margin; the minimum is 0.65 m = 16.50 m exactly). Upper bound from the cab: the cab back is 2.75 m ahead of the
  drive axle, so with lead 0.68 the trailer front radius (2.04 m legal, model 2.029 m) clears the cab-back plane by
  0.03 m at any articulation; lead 0.70+ would leave 0.01 m. 0.68 balances the two.
- Axle loads (40 t, uniform cargo, CoG 2.30 m): front 6.27 -> 6.62 t, drive 11.11 -> 10.76 t, tridem unchanged 22.62 t
  against drive axle 11.5 t / single non-driving axle 10 t / tridem 24 t (Directive 96/53/EC Annex I section 3; text not
  re-opened, UNVERIFIED). The drive axle had only 0.39 t margin before, now 0.74 t; the steer axle gains 0.35 t.
- The tractor's `fifth_wheel` mass element moves with the jaw (z 0.30 -> 0.43, 200 kg).
- Cargo bay follows the model: frontZ 1.572, length 13.512, width 2.50, **height 2.58** (floor 1.30 + 2.58 = 3.88 m, 12 cm
  below the 4.00 m roof top). The default cargo block is 2.0 m high (CoG 2.30 m), inside the bay; a full-height block
  would have its CoG at 2.59 m - pass `cogHeight`. Body mass element (curtains/roof/walls, 1300 kg) now spans floor top ->
  roof top: centre y 2.65 (was 2.60).
- New keys in dims.json: `artic_length_m` (DERIVED), `trailer_cargo_front_z_m`, `trailer_cargo_length_m`,
  `trailer_cargo_width_m`, `trailer_cargo_height_m`. `tests/physics/test_dims_sync.py` now covers all `trailer_*` keys,
  the 16.50 m limit (>= 2 cm margin), the cab-back clearance, and the cargo envelope below the roof.

## Consequences
- Runner: 98 scenarios / 482 checks and 146 unit tests green. Golden CSVs regenerated for 4 scenarios whose ABS cycle /
  shift phase moved (details and the list of >2 % movers in docs/PHYSICS_VALIDATION.md 6a). Stop distance +1.3 %,
  jackknife articulation 5-6 % smaller, laden hill start slower by shift timing in the first 30 s (7 instead of 5 shifts, same speed afterwards).
- **3D model (not changed here):** the tractor generator reads `fifth_wheel_lead_m` from dims.json
  (`tools/blender/truck/exterior/a6_export.py` `FIFTH_WHEEL_KINGPIN = (0, -WB + FIFTH_LEAD, FIFTH_H)` and `chassis.py
  fifth_wheel_and_rear`). After re-running the TRAKT export the fifth-wheel plate and the `FIFTH_WHEEL_KINGPIN` empty move
  0.13 m forward: Blender (tractor frame, origin ground under front axle, Y forward) y = -3.70 + 0.68 = -3.02 m (was
  -3.15 m); Unity vehicle frame (origin rear axle) z = 0.68 (was 0.55). The current `truck_exterior_manifest.json` still
  says 0.55 and will show a lead mismatch until re-exported. The trailer model is unaffected (its frame is the kingpin);
  the trailer cargo walls/roof keep their geometry, only the physics volume was reduced.
- Rear overhang is unchanged (0.80 m); the plate has 0.13 m more clearance to the rear frame end than a plate at 0.55.
