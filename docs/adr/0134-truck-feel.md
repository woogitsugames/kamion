# ADR 0134 - Truck feel after the Fold test: gear-change nod, light-load skip shifts, smooth AMT torque, cab damping

Status: proposed (2026-11-12, agent truck-feel, session 12). Touches `AmtController`, `Engine` (engine brake during
up-shift sync), `VehicleModel` (one line), `GearboxDefinition`, the gearbox and tractor JSON, the physics runner (one metric,
one sample field) and the Stage 2 scenario generator. No UI, input, camera or ProjectSettings change.

## Context
Owner test on the Samsung Fold (APK `11db0552`, coupled combination, yard and Andersa street up to 59 km/h):
1. "it rocks a lot when accelerating, like a sports car - is that normal?" (cab view pitches on launch and on shifts);
2. "it changes gears very quickly - is that how it works? does the trailer have no weight, so it accelerates too fast?"
   Video frames: D4 -> D7 in ~4 s, 9 -> 41 km/h in ~8 s, D10 at ~45 km/h ~20 s after the start, 1250-1850 rpm at shifts.

### Diagnosis (physics runner, same C# sources as the build; `tests/physics/launch_feel.py`)
- **The trailer has mass, but the default spawn is the empty trailer.** `DrivingLabBootstrap` reads `PrefSpawn` with default
  `LabSpawn.Empty` (14.5 t combination: 7.5 t tractor + ~7 t curtainsider). The trailer is coupled (fifth-wheel constraint,
  kingpin load 2-10 t visible in telemetry). Only `autopilot=route` defaults to 40 t. So the owner drove a 14.5 t
  combination with a 368 kW / 2500 N m engine: 25 kW/t, three times the power-to-weight of a full 40 t truck.
- **Acceleration matches that mass.** Runner `launch_flat_comb`, full pedal: empty 0-50 km/h 10.2 s (mean 1.37 m/s²,
  peak 2.84 m/s² in the 4th-gear launch); laden 40 t 19.5 s (mean 0.71 m/s², peak 2.15). The video (9 -> 41 km/h in ~8 s,
  ~1.1 m/s² at part pedal) is consistent with the empty case. Reference: SAE 950136 (Proctor, Grimes et al. 1995, 219
  trucks in traffic) average over the first 50 ft 0.138 g bobtail, 0.106 g box, 0.085 g flatbed (1.35 / 1.04 / 0.83 m/s²);
  heavily loaded (27-36 t) trucks "on the order of 3.5 ft/s/s" (1.07 m/s²) max from rest on the level (Washburn, freight
  curriculum ch. 4.1, an engineering estimate without a cited test). The laden 0-50 mean of 0.71 m/s² sits in that band; the
  empty combination at 1.37-1.48 m/s² is at the bobtail level. Not a physics error.
- **Shift frequency follows from acceleration and the ratio step.** The TraXon set has ~1.29 per step, so a gear lasts
  Δv = 0.22 v; at 20 km/h and 1.4 m/s² that is ~1.1 s. Before: empty 4-5-6-7-8-9 (5 up-shifts to 50 km/h), laden the same
  5. The strategy never skipped a gear: the min-rpm-after-up-shift (1250 rpm at full pedal) rejects every two-step shift
  (1750 x 0.594 = 1040 rpm). Production AMTs skip gears when lightly loaded (I-Shift press test drive: "quickly to second or
  third and then skip-shift upward"; truckinginfo.com "Test drive: Volvo's I-Shift, a smooth operator"; drivers' reports
  that some AMTs do not skip are anecdotal).
- **The rocking is the chassis + cab pitch response to the torque gap of every shift.** The cab-view camera is a child of
  the cab-suspension pivot; the camera itself adds only a ≤ 4 cm translational head sway (no rotation), so everything the
  player sees as pitch is chassis pitch + cab pitch. Eye pitch (chassis nose-up minus cab nose-down) before: launch peak
  3.8° empty / 2.9° laden; per-shift nod (peak-to-peak within 1.5 s of the shift start) up to 5.4° empty / 4.6° laden, mean
  3.2 / 2.8°. Causes found in the CSVs:
  1. the clutch closed 200-300 rpm above synchronous speed (engine drag alone only slows the engine ~520 rpm/s during the
     0.2 s sync), dumping the engine inertia into the driveline: a +0.7 m/s² spike, then a dip with negative clutch torque;
  2. the torque came back linearly in 0.15 s and was cut linearly in 0.12 s (jerk steps of ~15-20 m/s³);
  3. the cab mounts at ζ 0.35 overshoot ~30 % and ring for 2-3 cycles at 1.5 Hz, roughly the shift rate of the empty truck;
  4. the steady chassis squat (~1.1° at 2.7 m/s²) is consistent with the spring rates (load transfer ~11 kN on a 3.7 m
     wheelbase, front leaf 426 kN/m, rear air ~250 kN/m) and 0 % anti-squat (tyre Fx is applied at the contact patch;
     the rear link geometry is not modelled). Not changed here (no source for the link geometry) - see Open items.

## Decision
1. **Light-load skip shift** (`skipShiftMinRpmAfter` 950 rpm, `skipShiftMinAccel` 1.5 m/s² x pedal, pedal > 50 %):
   a two-gear up-shift is taken when the engine lands at or above max(950 rpm, lugging guard = down-shift line - 150) and
   the truck still accelerates by at least 1.5 m/s² x pedal in the target gear. 950 rpm: the S1 fact-sheet curve gives
   2450 of 2500 N m (plateau from 980). The lugging-guard floor keeps it out of climbs (on 6 % the first version hunted:
   26 shifts / 9 down-shifts, fixed). Only light, firm-pedal launches skip; a 40 t truck never meets 1.5 m/s².
2. **Smooth torque ramps.** Fade-out 0.12 -> 0.20 s and fade-in 0.35 s (new `shiftTorqueRampInTime`), both smoothstep
   (no jerk step at either end). The clutch-open gap is unchanged.
3. **Up-shift synchronisation with the engine brake** (`upshiftEngineBrakeSync`): with the clutch open the AMT requests the
   engine brake while the engine is > 20 rpm above the new gear's speed; the clutch closes only within 40 rpm (or after
   0.3 s extra) and the engine brake is cut before the clutch transmits (`SyncBrakeCut`). The engine brake therefore never
   brakes the vehicle during a shift; the runner metric `max_shift_retard_torque_nm` now counts engine-brake torque only
   while the clutch command is > 0.01. Using the engine/exhaust brake to speed up up-shifts is how production AMTs are
   commonly described (UNVERIFIED, no manufacturer document opened). Audio note: `TruckAudioController.EngineBrake` reads
   `EngineBrakeState`, so a short engine-brake note may be heard during up-shifts; the leader/audio can gate it on
   `Amt.SyncBrakeRequest` if it sounds wrong.
4. **Cab mount damping ζ 0.35 -> 0.5** (WORKING_VALUE, frequency and gain unchanged). ζ 0.7 was also tried: part-pedal empty
   nod 3.62 -> 3.25°, kept at 0.5 as the smaller change.
5. Legacy defaults in `GearboxDefinition` keep the old behaviour (ramp-in 0, skip off, sync off); only the gearbox JSON
   switches them on.
6. New runner metric `max_shift_eye_pitch_swing_deg` (arg = window, 1.5 s) and checks: `launch_flat_comb` <= 4.0°,
   new scenario `launch_flat_comb_part60` (60 % pedal, owner-style) <= 3.8°. Both fail on the old code
   (5.39 / 4.57 and 4.50 / 3.23°).

All values are WORKING_VALUE unless marked; sources are cited above and in `docs/VEHICLE_REFERENCE_DATA.md`.

## Results (runner, dt 0.01 s; `artifacts/truck-feel/before|after|full`, overlay `before_after_overlay.png`)
| Case | 0-50 km/h before -> after | up-shifts to 50 km/h | per-shift eye nod max / mean | launch eye peak |
|---|---|---|---|---|
| empty, full pedal | 10.17 -> 9.85 s | 5 (4-5-6-7-8-9) -> 3 (4-6-8-9) | 5.39 / 3.22° -> 3.83 / 2.17° | 3.80 -> 2.95° |
| laden 40 t, full pedal | 19.51 -> 20.41 s | 5 -> 5 | 4.57 / 2.80° -> 3.40 / 2.02° | 2.87 -> 2.77° |
| empty, 60 % pedal | 13.91 -> 14.90 s | 5 -> 5 | 4.50 / 2.65° -> 3.62 / 2.15° | 3.30 -> 3.11° |
| laden 40 t, 60 % pedal | 32.89 -> 33.97 s | 5 -> 5 | 3.23 / 2.09° -> 2.34 / 1.54° | 2.08 -> 1.57° |

Cab pitch relative to the frame on launch: empty 2.15 -> 1.36°, laden 1.55 -> 1.02°. Chassis pitch unchanged (1.7-2.0°).
Other movers: launch_6pct_uphill_comb@laden40 0-15 km/h 4.59 -> 4.84 s (check 4.05-4.95 s, PlayMode reference
4.5 s ± 10 % - close to the edge, leader to watch the PlayMode run); launch_12pct min speed after 20 s 21.5 -> 19.8 km/h
(check >= 18); cab pitch in ABS stops 3.1-3.4°. Runner 107 scenarios / 550 checks green; xUnit 155/155 after regenerating
9 goldens. The golden diffs come from the new shift timing (gear/rpm traces, up to 1.6 km/h speed difference before the
event in 6 of them); every scenario check of those brake, lane-change and jackknife events still passes.

## Open items / owner decisions
- ~~Default load~~ decided, see the addendum below. Original note: The free-drive default is the empty trailer. A real 40 t combination feels heavy and
  slow (0-50 km/h ~20 s at full pedal, ~34 s at 60 %); the empty one is nearly twice as quick. Proposal: default the
  first start to `Cargo24t` (typical payload) or show the current load more prominently on spawn; the spawn menu
  (`Zestaw...`) already offers empty / 24 t / 40 t. Not changed here (UI/gameplay, owner's call).
- **Anti-squat of the drive axle.** The model has 0 % anti-squat, so the chassis squats ~1.1° at 2.7 m/s² and swings
  through the torque gap of each shift. Real 4-bellows rear suspensions carry part of the drive reaction through the links.
  Needs a sourced link geometry before modelling (no number invented here).
- **Launch jerk.** The launch clutch reaches full torque in ~0.4 s (0 -> 2.8 m/s² empty), which gives the largest single
  pitch peak (~3°). A slower, jerk-limited launch is plausible for production AMTs but would move the hill-start reference;
  left for a follow-up with the owner's feel input.
- Phone check by the leader: APK with this branch, cab view, empty and 40 t launches on the yard.

## Addendum 2026-11-12 - owner decision: default load 24 t (D-number assigned by the leader)
The owner decided that the game starts with the **24 t payload** (`LabSpawn.Cargo24t`, combination ~40 t) instead of the
empty trailer. `DrivingLabBootstrap.DefaultSpawn = Cargo24t`; `StoredOrDefaultSpawn` uses the stored `lab.spawn` value only
when the key exists. That key is written only by an explicit pick in the spawn menu (`Spawn(..., persist: true)`), so no
migration step is needed: players who never picked a load (the owner's Fold included) get 24 t on the next start, explicit
picks (empty / 40 t / solo) are kept. Unchanged: `trailer=` launch argument, `autopilot=route` (40 t), lab autopilot runs
(solo), and a stored Solo in a world scene still falls back to the empty coupled trailer. EditMode test `DefaultSpawnTests`.
With 24 t the free-drive launch is the "laden40" row of the table above: 0-50 km/h ~20 s at full pedal, ~34 s at 60 %,
sequential shifts, per-shift eye nod max 3.4 / 2.3 deg.

## Addendum 2026-11-12 - review fixes (REVIEW-2026-11-12-s12-0134-0135)
- P1 hill start: `CombinationLabTests.HillStart_6pct_40t_NoRollback` reference 4.5 -> 4.84 s (runner after ADR 0134);
  tolerance kept at the old absolute ±0.45 s (not widened); runner check `launch_6pct_uphill_comb@laden40` time_to_kmh(15)
  moved with it to 4.39-5.29 s. The slower start comes from the longer torque fade-out/in, not from the sync (sync time on
  the 40 t starts measured 0.20 s = no extra).
- P2 engine brake during sync: `Engine` now acts on the explicit `Engine.SyncBrakeActive` (= `Amt.SyncBrakeRequest`,
  set each step by `VehicleModel`) instead of comparing the engine speed with the rev-matching target, so a down-shift
  rev-match never gets a fuel cut.
- P2 shift-duration prediction: `totalShift` includes a running mean of the measured extra sync time of recent up-shifts
  (0 for the 40 t starts, ~0.1 s after an empty skip shift). Runner 107/107, xUnit 155/155, 6 goldens regenerated (shift
  timing only).
