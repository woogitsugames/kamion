# ADR 0004 — Vehicle physics architecture
Status: Accepted, 2026-11-09
Decision: Pure C# solver (`Game.Vehicle.Physics`, no UnityEngine dependency) computes tire, drivetrain, brake and aero forces; PhysX handles rigid bodies and world collisions; a Unity adapter applies forces at contact points. Fixed step 100 Hz with internal substeps for wheels/drivetrain (count decided by benchmark on Samsung A). The same sources compile in a plain .NET test project (`tools/physics-runner`) so physics can be iterated and tested without the Unity editor.
Consequences: No `transform.position +=` for vehicles; no physics in Update(); zero GC allocations per step.

## Addendum 2026-11-10: parking brake drive-away interlock, trailer braked in park, shift-gap check

Context. Owner feel test (S24+, APK f6abb8b, route G3-A, 40 t, touch pedals): "when accelerating and during gear
changes the truck is braked, I cannot go fast". It was the parking brake. `DrivingLabBootstrap` and `VehicleBody`
spawn the truck parked, and the owner drove off without releasing P. The phone log (`artifacts/owner/feel-test/20261110-s24/logcat-unity.txt`)
shows `parking=toggle` only at t = 89.7 s. Before that, at full throttle, the truck reached 15.9 km/h. After the release it
reached 90 km/h. The runner reproduces it (`owner_repro_p_on_comb@laden40`, HEAD 111f437): 16.9 km/h plateau. The 4-5 up-shift
at 16.6 km/h decelerates the combination by -1.55 m/s² in the clutch-open gap (normally -0.12) with 32 kN m of
spring-brake torque on the wheels. That is the "braked during the shift" feel. Physics cause: launch gear 4 at full load
gives 2360 N m x 5.94 x 3.4 x 0.94 = 45 kN m at the drive axle, against 2 x 16 kN m of tractor spring brake (sized
from UN R13 2.3.2, VEHICLE_REFERENCE_DATA). The trailer was not braked by the tractor's parking lever at all.
Owner requirement: "nie powinienem w ogóle ruszyć jak jest P" (the truck must not move at all with P on).

Decision.
1. **AMT drive-away interlock** (`AmtController.ParkingBrakeApplied`, `ParkingInterlockActive`, `ParkingInterlockEnabled`).
   The vehicle sets the flag from the lever or from spring brakes that are not fully released (state > 0.05, which also
   covers low circuit-3 air). Below 1 m/s, with D/R selected, the AMT stays in Idle: the clutch opens, the accelerator is
   ignored (engine at idle) and the launch gear is pre-selected. After the release the launch starts once the spring
   chambers are released (~0.8 s). The interlock does nothing above 1 m/s: if P is pulled while rolling, the spring brakes
   simply brake. Production AMT trucks are commonly described as refusing to pull away against the parking brake and warning
   the driver (UNVERIFIED, no manufacturer document opened). The behaviour is a WORKING_VALUE design.
2. **Cluster warning API** (`VehicleModel.ParkingBrakeWarning`, `ParkingBrakeWarningCount`). The warning is on while
   the parking brake is applied, D/R is selected, and either the interlock refuses a drive-away or the truck rolls faster
   than 1.5 m/s. The count goes up on each rising edge (chime event, poll and compare, zero GC). The HUD/cluster hookup
   belongs to gameplay-ui (e.g. `Flash("Hamulec postojowy!")` + chime on a count change in `DrivingLabBootstrap`,
   telltale in `CabScreens`). This addendum does not do it.
3. **Trailer braked in park** (`AirDefinition.trailerControlParkBar` = 7.5 bar, WORKING_VALUE). In the park position the
   tractor hand control valve also pressurises the yellow line, as European hand control valves with a trailer-control
   function do (they have a "test" position that releases the trailer so the tractor can be checked alone; UNVERIFIED, from
   memory of the valve type, no data sheet opened). It is the physical layer behind the interlock. With the interlock
   switched off, 40 t at full throttle in launch gear 4 for 11 s gives a peak of 0.05 km/h and 28 mm wind-up
   (`park_brake_hold_no_interlock_comb`). The clutch slips and heats to 135 °C, which is why the interlock exists.
   The spring-brake torque itself is unchanged (16 kN m per tractor rear wheel end). The tractor alone still holds 40 t on 12 % (UN R13 2.3.2).
4. **Standstill tyre relaxation (R6) keeps a braked wheel's own grade share.** A braked trailer wheel now relaxes towards
   Fz·tanθ (capped by its brake), not to 0. Unbraked wheels relax to 0 as before. Without this change, the braked trailer
   handed its whole grade force to the kingpin and the combination crept 6-9 mm on 12 %. `TrailerBrakeSystem.InitServiceChambers`
   starts the trailer chambers at the park pressure in scenarios that begin parked. The Unity `VehicleBody` spawn does not
   call it yet, so the trailer brakes apply about 0.5 s after the spawn (harmless).
5. **Shift-gap validation.** New runner metrics: `max_shift_retard_torque_nm` (wheel brakes + retarder + engine brake
   while an AMT shift is in progress; must be 0 unless commanded) and `min_accel_shift_gap_ms2` (worst per-gap mean dv/dt
   with the clutch open). Both are checked on `launch_flat_comb`. New scenarios: `park_brake_drive_away_comb` (P on +
   full throttle 10 s, then release), `park_brake_hold_no_interlock_comb`, `park_low_air_drive_away_comb` (2 bar, lever
   released). Each one fails on HEAD 111f437.

Consequences.
- P on, full throttle 10 s: 40 t 0.003 km/h (was 15.6), empty 0.0006 km/h (was 16.4, with a stall). Warning raised, clutch
  25-32 °C. After the release: 29 km/h 8 s after the throttle (normal launch, 40 t).
- P off, up-shifts (shift logic unchanged): 0.63 s interruption each (0.12 ramp + 0.15 neutral + 0.20 sync + 0.15 close),
  0 N m of brake/retarder/engine-brake torque in every shift. The gap deceleration is resistance only: laden
  -0.08 to -0.12 m/s² (rolling ~0.05 + aero), empty -0.09 to -0.21 m/s² (aero at 88 km/h). Instantaneous a_long swings
  of ±0.5-1 m/s² for ~0.2 s are the fifth-wheel surge when the driveline unloads, with zero net impulse.
  0-60 / 0-80 km/h: 40 t 26.9 / 46.2 s, empty 13.3 / 20.5 s, solo 9.7 / 13.8 s, all unchanged. The 40 t value is at the
  quick end of the 45-70 s expected for a 40 t / ~500 hp combination on flat (WORKING_VALUE plausibility band, no sourced
  test; the runner band stays 40-95 s, DERIVED).
- Parking on 12 %: the trailer now settles 3.5-4.8 mm after 5 s (was 1.3-3.6) and the tractor 1.0-2.1 mm (was 0.04-0.27).
  This is the relaxation moving load from the stiff initial split to the grade shares. It stops within 60 s (≤ 0.04 mm
  after 60 s). The limits are unchanged and pass (5 mm and 0.5 mm), but the trailer margin is now small.
- Feel: pressing the accelerator with P on gives an idle engine, no movement and a warning. Releasing P (~0.8 s spring
  release) and pressing again gives an ordinary launch.
