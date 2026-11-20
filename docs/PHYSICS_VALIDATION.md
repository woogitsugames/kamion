# Physics validation — Stage 2, tractor 4x2 + semi-trailer

Status: **141 scenario runs (833 checks) and 287 xUnit tests are green** in the plain .NET runner (refreshed 2026-11-16, section 3; first Stage 2 sign-off 2026-11-09 with 93 runs / 141 tests, ADR 0009 requests R5–R7 in section 2a). The 96/53/EC turning ring is a regular scenario since D79 (trailer axles 7.63 m, ADR 0280 §10), no longer a known failure (remaining known failures: `tests/physics/scenarios_expected_fail/`). This covers the solo tractor, the empty combination (14.5 t) and the 40.0 t combination. Nothing has been run in Unity or on a device yet. Stage 1 history is in git (`ee235b4`).

Parameter provenance: `docs/VEHICLE_REFERENCE_DATA.md`. Most numbers are still WORKING_VALUE, so the tolerances mostly check **plausibility and numerical quality**. The exceptions are the items backed by UN R13 Annex 4 text (S5), the 90 km/h limiter (S3) and the class-reference engine and gearbox data (S1, S2, opened in Stage 2).

## 1. How to run

```powershell
$env:DOTNET_ROOT = "$env:LOCALAPPDATA\Microsoft\dotnet"; $env:PATH = "$env:DOTNET_ROOT;$env:PATH"
dotnet test tools/physics-runner -c Release                                   # 287 tests, ~35 s
dotnet run -c Release --project tools/physics-runner/Runner                   # 141 runs + multi-run checks + bench -> artifacts/physics/<ts>/
dotnet run -c Release --project tools/physics-runner/Runner -- --only brake_80_0_dry_abs_comb          # all variants of one scenario
dotnet run -c Release --project tools/physics-runner/Runner -- --only lane_change_80@laden40          # one variant
dotnet run -c Release --project tools/physics-runner/Runner -- --update-golden   # rewrite tests/golden/*.csv (review the diff!)
dotnet run -c Release --project tools/physics-runner/Runner -- --bench           # cost per step, 40 t combination
uv run tools/telemetry/plot.py artifacts/physics/<ts>/                         # one PNG per CSV
uv run python tests/physics/generate_stage2_scenarios.py tests/physics/scenarios tests/physics/scenarios_expected_fail   # regenerate the Stage 2 scenario JSONs
```

Scenario variants: a scenario with `"variants": ["solo", "empty", "laden40"]` expands to `<id>@solo`, `<id>@empty` and `<id>@laden40`. `laden40` is GCW = 40.0 t exactly (25.5 t cargo, CoG 2.3 m). A check can be limited to one variant.

## 2. Architecture (ADR 0004, extended)

```
game/Assets/_Project/Vehicle/Physics/          pure C# 9, no UnityEngine
  Definitions/  VehicleDefinition (+ air, retarder, fifthWheel, per-axle brake data), TrailerDefinition,
                CargoDefinition, EngineDefinition (+ engine brake curve), GearboxDefinition (+ AMT strategy)
  Components/   WheelGroup      contacts, steel / levelled air springs, tires, wheel spin, brake constraints (shared)
                Pneumatics      AirBrakeSystem (tractor), TrailerBrakeSystem, ABS state machine, Retarder
                FifthWheel      coupling constraint
                AmtController, Engine (+ engine brake), CabSuspension (3-DOF), Steering, TireModel
  VehicleModel  tractor: driveline, steering, air supply, endurance brakes, blending, hill hold
  TrailerModel  trailer body: axles, trailer brakes, landing gear, trailer aero share
  CombinationModel  one fixed step for both bodies + coupling; outputs force + torque per body
tools/physics-runner/Sim   RigidBody6Dof x2, AnalyticGround, scenarios/variants/events, drivers, metrics, telemetry, golden
tests/physics/scenarios    65 JSON files -> 93 runs
tests/golden               9 golden CSV subsets + tolerances.json
```

### One fixed step (`CombinationModel.Step`, 100 Hz)
1. **Tractor** (`VehicleModel.Step`): contacts and suspension (and air levelling); brake demands (pedal blending, hill hold, lever, brake cruise, ABS cut-off); air supply (compressor, governor, protection valve, leaks, red and yellow lines, spring chambers); AMT; engine-brake actuator; retarder. Then 4 substeps of: tires and wheel spin → **service chambers + ABS** → engine → clutch and brake Coulomb constraints (PGS) → wheel-deceleration signal.
2. **Air lines**: the red line charges the trailer reservoir. Red and yellow pressures go to the trailer.
3. **Trailer** (`TrailerModel.Step`): contacts and levelling; emergency relay; 4 substeps of tires → chambers + ABS → brake constraints; landing gear legs; trailer aero.
4. **Fifth wheel** (`FifthWheel.Solve`): both bodies' end-of-step velocities are predicted from the model forces plus gravity (the same semi-implicit Euler the host uses, including the gyroscopic term). Then 8 sequential-impulse iterations:
   - kingpin point: 3×3 block solve with Baumgarte 0.2 and a 0.5 m/s cap; during the 0.4 s after the jaw locks it is a 4 Hz critically damped soft constraint;
   - roll: implicit soft spring 1e7 N m/rad (stable for any stiffness);
   - soft one-sided stops on roll ±4°, pitch ±12° and articulation ±90° (3 Hz, critically damped: cab contact);
   - plate Coulomb friction about the kingpin.

   The impulses come back as a force at the kingpin plus a pure torque per body.

### Unity adapter for the combination (to be written by the leader / gameplay)
```csharp
// two Rigidbodies (tractor, trailer); NO PhysX joint between them
void FixedUpdate() {
    combo.Gravity = ToD(Physics.gravity);
    combo.Step(Time.fixedDeltaTime, ToState(tractorRb), ToState(trailerRb), input, groundQuery);
    tractorRb.AddForce(ToV3(combo.TractorForce));  tractorRb.AddTorque(ToV3(combo.TractorTorque));
    trailerRb.AddForce(ToV3(combo.TrailerForce));  trailerRb.AddTorque(ToV3(combo.TrailerTorque));
}
```
- Mass, CoM and the inertia tensor of both bodies come from `Tractor.MassProps` and `Trailer.MassProps`. The trailer's include the cargo. When the load changes, use `combo.SetCargo(cargo)` (no new model, see 2a) and copy `Trailer.MassProps` into the trailer Rigidbody again.
- The constraint predicts velocities with the model's own mass properties. PhysX integrates almost the same way. Any residual is removed by the Baumgarte feedback. The runner's kingpin error never exceeds 0.16 mm. On the phone, measure it again (`FifthWheel.PositionError`).
- Coupling: `combo.CouplingArmed = true`. The jaw locks automatically inside the capture window; the throat guides a kingpin up to ±0.18 m off the centre line into it (R5, 2a). Uncoupling is `combo.Uncouple()`. It is refused unless the landing gear is down (`Trailer.LandingGearDown`), because there is no chassis-ground collision to catch the nose.
- Driver inputs added in Stage 2: `RetarderLever` (0 off, 1 engine brake, 2–5 retarder stages), `BrakeCruiseKmh`, `ManualMode`, `ShiftUp`/`ShiftDown` (edge-triggered).

### 2a. Resolution of ADR 0009 requests R5–R7 (2026-11-09)

**R5, coupling throat** (`FifthWheel.ComputeThroatGuide`, called by `CombinationModel.Step` while the jaw is armed and open).
- The plate slot is a funnel that opens to the rear. Mouth ±0.18 m wide at 0.40 m behind the jaw centre, narrowing linearly to ±0.025 m at the jaw cup (about 18° lead-in ramps). All values are WORKING_VALUE: typical lead-in of a fifth wheel plate, not measured on a specific model (`FifthWheelDefinition.captureThroat*`).
- A kingpin inside the funnel and vertically within `captureHeight` that is wider than the local ramp half-width is pushed to the centre line by a spring-damper contact (3 MN/m, 150 kN s/m, capped at 80 kN), equal and opposite on both bodies at the kingpin. The 80 kN cap is about what the trailer feet and the tractor tires can give sideways.
- `TryCapture` is unchanged (5 cm radius, 12 cm vertical, 1.5 m/s, heading within 25°). The ramps bring the kingpin inside that radius.
- Result (reversing at about 3 km/h, trailer on its legs): couples from −0.18 to +0.17 m offset and up to ±5° yaw, bump 99–110 kN, dv ≤ 0.16 m/s/step; at ±0.21 m, 0.30 m and −0.45 m it does not couple (no false capture). Scenarios `couple_offset_right_15cm`, `couple_offset_left_18cm`, `couple_miss_25cm`; tests `CouplingThroat_*`.

**R6, kingpin load at standstill on locked brakes.**
- Cause (found with `couple_standstill_locked`: couple, hold service + parking brake, raise the legs): the old 0.67–0.9× was not a vertical effect. With every trailer wheel locked, any slow pitch change of the combination (the nose load moving from the legs to the plate, the tractor's air suspension re-levelling for about a minute) is a ~1 cm horizontal geometry mismatch. The tire stick springs stored it as 60–110 kN of longitudinal preload. That force acts at the plate height (1.2 m), and shifts the kingpin load by Fx·h / wheelbase (about 10 kN, 10 % of the 97 kN static load for 40 t). Parking brake only (trailer wheels free) was never affected.
- Fix (`TrailerModel.StandstillRelaxTau`, WORKING_VALUE 2 s): while the combination is coupled and stands still (|v| < 0.05 m/s) the longitudinal contact-patch deflection of the **trailer** wheels relaxes. That is the real carcass hysteresis and trailing-arm bush compliance that the rigid-axle model lacks. The tractor wheels and brakes keep holding, so on a slope the trailer settles by about F / k_tractor and stops: no creep (the 12 % parking scenarios, drift ≤ 5 mm, are unchanged). Lateral stick is untouched; jackknife and all golden telemetry still pass unchanged.
- Target refined in ADR 0280 §10.3 (2026-11-16): a braked trailer wheel relaxes to the **common-mode deflection of the tractor's braked wheels** (Σk·u / Σk, so a preload between the tractor's own axles cancels), not to its "own share" Fz·tanθ. The own-share target also bled the trailer's elastic share of the grade force onto the kingpin, and the empty trailer settled 5.0 mm on 12 % over ~60 s through the tractor's tyre and bellows compliance (4.97 mm at 7.70 m, 5.02 mm at 7.63 m; 0.00 mm with the relaxation off). Now 0.69 / 0.29 mm. The own share stays as the fallback when the tractor has no braked wheel in contact.
- Result: kingpin / static 1.005 (empty) and 1.014 (40 t) at 50–80 s after raising the legs on locked brakes (was 0.95 and 0.90 in the same scenario without the fix; 0.67 in the Unity case, which was not reproduced exactly).

**R7, trailer / cargo swap without rebuilding.**
- `CombinationModel.SetTrailer(TrailerModel trailer, bool coupled)`: replaces the trailer (or removes it with `null`), resets the fifth wheel without counting an uncoupling, clears the arming, re-levels both suspensions. The tractor model and the combination object stay.
- `CombinationModel.SetCargo(CargoDefinition)` / `TrailerModel.SetCargo(cargo, onKingpin)`: changes the load case of the existing trailer model in place (mass, CoM, inertia, static axle loads, pre-levelling). No new wheel group.
- Both are between-step calls. `TrailerModel.MassProps` and `.Cargo` are now properties that change on `SetCargo`: copy `MassProps` into the Rigidbody again. The step stays allocation-free (test `Step_DoesNotAllocate_AfterSetCargo`: 0 B over 500 steps after a cargo change).
- Tests `SetCargo_InPlace_SettlesToNewStaticLoad` (22 t, then back to empty: kingpin / static 1.000, 0.998), `SetTrailer_SwapsWithoutRebuildingTheCombination` (18 t swap 1.000, then solo).

## 3. Results (runner, dt = 0.01 s, 4 substeps; refreshed 2026-11-16, branch `trailer-763-d79` (ADR 0280 §10: trailer axles 7.63 m, standstill relaxation fix); earlier rows from `turning-circle-s23` @ `31c1383ca` where unchanged)

**141 scenario runs / 833 checks PASS, `dotnet test` 287/287** (Linux, .NET 8 SDK 8.0.428; same solver sources as Unity, ADR 0004;
nothing here ran in Unity/PhysX or a Windows player). Values are solo / empty / 40 t where the item has variants. Status of the
expectation as written in the scenario check: SOURCED = regulation point read in the text, DERIVED = formula / extrapolation,
WORKING = plausibility band. The Polish summary table is `docs/04_FIZYKA.md` §6a.

| docs/04 §6 | Scenario | Key result | Expected / tolerance | Status of expectation |
|---|---|---|---|---|
| 1 | park_12pct_down/up_comb (300 s, tractor spring brakes + trailer through the hand control valve) | creep 0.26 / 0.20 mm down, 0.21 / 0.06 mm up (empty / 40 t); trailer creep 0.69 / 0.65 mm down, **0.69 / 0.29 mm up** (was 4.97 mm empty uphill before ADR 0280 §10.3); max speed ≤ 0.32 mm/s | ≤ 5 mm; ≤ 1 mm/s | **SOURCED** 12 % (S5 2.3.2) + WORKING no-creep ✅ |
| 1 | park_flat_5min_comb, soak_30min_parked | drift 0.20 mm, KE ≤ 1.8e-5 J over 30 min, energy drift 0.62 J, air 12.5 bar | ≤ 5 mm, ≤ 1e-3 J, ≤ 5 J | WORKING ✅ |
| 2 | launch_6pct_uphill_comb (full throttle, HSA) | rollback 2.2 / 2.4 mm; 0–15 km/h 3.13 / 4.96 s; clutch 29 / 37 °C; 7 / 5 shifts | ≤ 5 cm; ≤ 250 °C | WORKING ✅ |
| 2 | launch_6pct_uphill_light_comb (35 % pedal, 40 t) | rollback 2.4 mm, 0–10 km/h 20.1 s | ≤ 5 cm | WORKING ✅ |
| 3 | launch_0_80_flat / launch_flat_comb | 0–60: 9.69 / 13.77 / 28.04 s; 0–80: **14.06** / 21.19 / 47.59 s | 40 t: 25–60 / 40–95 s; empty 0–80 ≥ 20 s | DERIVED (power-to-weight + shift losses); solo WORKING ✅ |
| 4 | top_speed_flat_comb | 89.38 / 89.17 km/h in 12th | ≤ 90.5, settles 88–90 (ADR 0082) | **SOURCED** S3 ✅ |
| 4a | limiter_downhill_2pct / 5pct_comb (40 t, full throttle held) | 2 %: max 94.3, min 93.8; 5 %: max 95.3, settled 94.0 km/h; service brake 0 | max ≤ 96, no drop below 88 | WORKING (overrun offset 4 km/h) ✅ |
| 4 | grade_5pct_steady (40 t) | 49.76 km/h, range 0.05 km/h, ≥ 1464 rpm | 44–60 km/h | DERIVED ≈ 54 km/h ✅ |
| 5 | **brake_60_0_dry_abs_comb** (new, engine disconnected: N with the brake) | **23.13 / 24.08 m**; MFDD 7.23 / 6.86 m/s² | **s ≤ 36.7 m, dm ≥ 5.0 m/s²** | **SOURCED**: UN R13 Annex 4 para 2.1.1, N3 Type-0 engine disconnected, v = 60 km/h, s ≤ 0.15 v + v²/130, dm ≥ 5.0 (read on the MLIT page image pp. 27–28, ADR 0280) ✅ |
| 5 | brake_80_0_dry_abs_comb | 39.03 / 41.31 m; MFDD 7.48 / 6.88 | ≤ 61.2 m; 5.0–8.0 | **DERIVED**: the same formula at 80 km/h is an extrapolation (was marked SOURCED until ADR 0280) ✅ |
| 5 | brake_50_0_dry_abs_comb | 16.65 / 17.52 m; MFDD 6.71 / 6.59 | ≤ 26.7 m; 5.0–8.0 | DERIVED (extrapolation at 50 km/h) ✅ |
| 5 | brake_80_0_dry (solo, ABS) | 34.26 m; MFDD 7.72 m/s² | 32–55 m; MFDD ≥ 5.0 | WORKING; MFDD bound DERIVED (R13 dm at 60 km/h applied at 80) ✅ |
| 5 | brake_80_0_wet (ABS) | 50.75 (solo) / 55.18 / 56.90 m; MFDD 4.92 / 4.80 / 4.68 | 45–95 m | WORKING ✅ |
| 5 | brake_80_0_dry / wet no ABS | dry 44.07 / 43.99 / 49.18 m; wet 75.58 / 78.32 / 82.00 m (locked) | longer than ABS | WORKING ✅ |
| 5 | brake_response_static | front 0.25 s, rear 0.31 s, trailer 0.54 / 0.53 s (75 % of final) | ≤ 0.6 s | **SOURCED** S5 4.1.1 ✅ |
| 5 | rear / trailer lock under ABS (all ABS runs) | 0 s above 2 m/s | ≤ 0.03 / 0.05 s | ✅ |
| 6 | downhill_7pct_typeIIA (40 t, 6 km, brake cruise 30 km/h) | mean 30.0 km/h, service brake 0, max 1930 rpm | 25–35 km/h, no service brake | **SOURCED** S5 1.8.2 ✅ |
| 6 | downhill_7pct_brake_cruise_60 / downhill_8pct_retarder_comb | 60.0 km/h (retarder ≤ 2856 N m) / 40.0 km/h (2192 N m) | 59–61.5 / 35–45; ≤ 4000 N m | S2 retarder limit ✅ |
| 6 | downhill_7pct_full_lever | range 0.001 km/h, engine-brake torque 1155 N m | stabilises | WORKING ✅ |
| 6 | downhill_7pct_service_pumping (endurance brakes off) | service circuits fall to 5.14 bar, warning on | ≤ 9, ≥ 3 bar, warning | WORKING ✅ |
| 6 | air_leak_rear_circuit (burst at 60 km/h, 40 t) | warning; rear circuit 0 bar; stop 32.54 m | ≤ 52.4 m (residual braking N3 laden from 40 km/h) | **SOURCED** S5 2.4.1 / S9 R3-161 (game test from 60 km/h is harder) ✅ |
| 6 | air_leak_park_circuit | trailer emergency braking + spring brakes stop the combination | stops | WORKING ✅ |
| 7 | **ring_96_53_comb** (game trailer: kingpin → tridem centre **7.63 m**, D79 correction, ADR 0280 §10) | outer 12.486 / 12.482 m, **inner 5.309 / 5.312 m**, ring width 7.177 / 7.170 m (at 7.70 m: inner 5.228 / 5.230 FAIL) | outer ≤ 12.50, inner ≥ 5.30 (width ≤ 7.20); margin guard width ≤ 7.18 (2 cm, WORKING; was 7.15 at 7.60 m) | **SOURCED** Directive 96/53/EC Annex I 1.5 (CELEX 01996L0053-20190814) + WORKING ✅ |
| 7 | circle_r50_10 / 35kmh_comb | offtracking 0.598 / 0.593 m at 10 km/h, 0.473 / 0.403 m at 35 km/h; a_y 1.88 m/s² at 35 km/h | 0.4–0.8 m at 10 km/h | DERIVED (√(R²+e²) − √(R²+e²−L²) = 0.59 m, L = 7.63 m) ✅ |
| 7 | rollover_r50_cog_low / high (40 t, speed ramp) | first wheel lift at **0.459 g** (CoG 1.9 m) / **0.339 g** (CoG 2.6 m) | 0.25–0.55 g; high < low | WORKING (literature 0.3–0.45 g, UNVERIFIED) ✅ |
| 8 | lane_change_80 | max articulation 0.84 / 0.81°; RA 0.992 / 0.997; residual ≤ 0.0004°; no lift | RA 0.8–1.6 | WORKING (literature RA 1.0–1.3, UNVERIFIED) ✅ |
| 9 | jackknife_wet_curve_noabs (EBS fault, empty) | **87.44°** articulation; drive axle locked 2.54 s | ≥ 30° (must be possible) | ✅ (state before ADR 0228 / PR #113) |
| 9 | jackknife_wet_curve_retarder_noabs (empty) | **92.65°** (soft cab stop 90° + 2.65°, D59 ≤ 3.5°); drive axle locked 1.85 s | ≥ 30° | ✅ |
| 9 | jackknife_wet_curve_abs_50 / _100 | 7.67 / 4.55° (empty), 5.16 / 5.16° (40 t), no lock | ≤ 10° | ✅ |
| 11 | curb_15cm_left_comb, speed_bump_comb | Fz peak 3.25 / 2.95 × static, trailer roll 2.79 / 3.39°; bump Fz ≤ 1.83×, cab heave ≤ 41.3 mm | ≤ 4×, ≤ 8°, ≤ 50 mm | WORKING ✅ |
| 11 | kerb_step_27cm_42kmh_comb (40 t, chassis colliders on, D58 / ADR 0165) | Fz 6.03×, front-axle airtime 0.39 s, bumper crush 0.036 m | 5.2–7.5×; ≤ 0.5 s; ≤ 0.05 m | WORKING ✅ |
| 12 | dt 50/60/100/120 Hz and substeps 2/4/8 (section 4) | ≤ 0.63 % (all metrics) | ≤ 5 % | WORKING ✅ |
| 14 | soak_30min_cycle (40 t, 20 cycles) | first vs last cycle cruise 73.01 / 72.44 km/h; energy drift +0.32 J; max articulation 2.24°; air ≥ 11.34 bar | no drift | WORKING ✅ |
| 15 | steer_sign_right / reverse_right_comb | +21.08 / +17.16 °/s forward, −3.98 / −3.16 °/s reversing | sign as solo | DERIVED ✅ |
| — | couple_standstill_locked (R6) | kingpin load 1.010 / 1.000 × static | 0.97–1.03 | DERIVED ✅ |
| — | couple_offset_right_15cm / left_18cm (R5); couple_miss_25cm | 1 coupling each, kingpin long. ≤ 36 / 84 kN; miss: 0 couplings | 1 / 0 couplings | WORKING ✅ |
| — | couple_uncouple | 1 coupling, kingpin load 0.986 / 0.972 × static, uncoupled trailer moves ≤ 3.1 mm | | WORKING ✅ |
| — | manual_mode_shifts (40 t) | gears 2→5 by hand, 4 over-revving requests refused, max 2072 rpm | ≤ 2130 rpm | S1 max revs ✅ |
| — | zero allocation (xUnit) | 0 bytes over 2000 steps, solo and 40 t combination | 0 | CLAUDE.md ✅ |

History: the Stage 2 table (2026-11-09, `artifacts/physics/stage2-final`) had 0–80 solo 13.8 s, 80→0 solo 34.9 m, jackknife
81.4°; the changes since are ADR 0134/0158/0165/0201/0201b (section 6d–6g) and ADR 0280 §10 (trailer axles 7.63 m, standstill relaxation target). Full per-check list: runner `summary.md` (not committed; ADR 0280 §10.5 has the before / after table).

## 3a. Kerb strike 14 cm at 50 km/h: wheel unload analysis (2026-11-09)

Scenario `curb_strike_14cm_50kmh_comb`: the left wheels of the whole combination drive over a 3 m long, 14 cm high block, so each left wheel climbs the block and then drops off it. Run `artifacts/physics/after`. CSV analysis per wheel: unloaded means no contact or Fz < 500 N, the same rule as `wheel_off_ground_time_s`.

| | empty | 40 t |
|---|---|---|
| Fz peak / static (front left, on the climb; bump stop engaged at 9.2 cm compression) | 3.90 | 3.53 |
| `wheel_off_ground_time_s` (union over all 10 wheel ends) | 0.70 s | 0.25 s |
| `max_wheel_airtime_s(1)` (longest single tractor-wheel unload) | 0.11 s (rear right, roll) | 0.08 s (rear left, drop) |
| `max_wheel_airtime_s` (all wheels) | 0.21 s (trailer axle 1 left) | 0.09 s |
| front axle airtime (the phone complaint) | 0.05 s (front left, drop off the end) | 0.02–0.04 s |
| body pitch / cab pitch peak | 2.9° / 3.0° | 3.5° / 3.7° |

Where the union time comes from (empty): (a) every left wheel **drops 14 cm off the block end**. Rear left loses contact for 0.09 s and front left for 0.05 s, because the drop is larger than droop travel plus static tire deflection. A real wheel with unsprung mass also flies about 50 ms: it falls 14 cm at roughly (spring force + m_u g)/m_u ≈ 100 m/s². (b) Trailer axle 1 left hangs at **full droop for 0.21 s** while axles 2–3 are still on the block, because the rigid trailer frame holds the left side up. (c) Wheels on the **opposite side** unload for 0.05–0.15 s on the climb, through the anti-roll stiffness (trailer 400 kN m/rad per axle against about 9 kN static load per empty wheel) and the body roll and pitch.

Levers tried, each run against both variants (sensitivity runs in `artifacts/physics/exp/`):
- **Tire radial stiffness**: no change. 1.0e6 / 1.1e6 N/m agree with the secant from a manufacturer datasheet (S7: 1.01e6 / 1.08e6).
- **Contact model (15 rays over ±63°)**: correct for the block. Contact starts at 43.5°, inside the arc. The response is the same at dt 1/50, 1/60 and 1/100 s and substeps 1, 2 and 4: Fz peak 3.87–3.98, union 0.70–0.72 s empty and 0.25–0.36 s laden. The core does **not** reproduce the phone values (Fz 6.8×, front axle 0.4 s, nose 8°).
- **Rebound damping halved** (rebound = bump): worse, union 0.77 / 0.37 s. The body is less damped.
- **Damper solved implicitly in series with the tire** (no ±2 m/s rate cap): worse, 0.75 / 0.36 s. The digressive cap acts as a blow-off. Not kept.
- **Droop**: static position at 0.4 / 0.35 of travel gives more droop but bottoms sooner: 0.84 / 0.40 s and Fz 4.9×. Real trailer travel is not longer than the model's (S8: 150 mm for a high-travel suspension; model 200 mm).
- **Dynamic bellows interconnection inside the tridem** (Maxwell element, line τ 0.02–0.3 s): 0.65–0.66 s empty. Axle 1 hangs past full droop, so sharing force between the bellows does not give it contact. A version with a pure lag was unstable (the walking mode was pumped). Not kept.
- **Anti-roll −50 %** (tractor rear and trailer): 0.47 / 0.18 s. This is the only lever with a large effect, but it has no source, and it would change rollover, lane-change and circle metrics. Not changed.

Conclusion: the union of airtime over 10 wheel ends **cannot reach < 0.15 s** for a 14 cm drop at 50 km/h with real travel. The five left wheel stations drop off one after the other, and each one flies for about 50 ms even on a real truck. The brief's "no long axle flight" is checked as the longest single-wheel unload: tractor ≤ 0.15 s (met: 0.11 / 0.08 s), all wheels ≤ 0.25 s empty and ≤ 0.12 s laden. The empty-tridem 0.21 s needs trailer frame torsion, which is not modelled (§7). The phone symptom is not in the core: the remaining suspects are in the Unity adapter.

### 3b. Unity adapter parity and the phone event (2026-11-09, evening)

PlayMode `KerbStrikeParityTests` runs the same block, speed hold, load cases and metrics as the runner in Unity (PhysX bodies, `UnityGroundQuery`, 15 rays, 4 substeps, 0.01 s). The block is built two ways: a BoxCollider on Default (the body colliders could touch it) and a MeshCollider with the DrivingLab slab topology on `WorldKerb` (wheel rays only, as in WorldC). CSVs: `artifacts/physics/unity-kerb/`; overlay plots: `tests/physics/plot_kerb_parity.py` → `artifacts/physics/kerb-parity/parity_*.png` (looked at: the Fz, compression, tyre deflection and pitch traces lie on top of each other).

| curb_strike_14cm_50kmh_comb | Fz / static | tractor single-wheel unload | all wheels | pitch peak | max \|dv\| |
|---|---|---|---|---|---|
| runner, empty | 3.90 | 0.11 s | 0.21 s | 1.66° | 0.068 |
| Unity box / mesh, empty | 3.90 / 3.90 | 0.11 / 0.11 s | 0.20 / 0.21 s | 1.67° | 0.068 |
| runner, 40 t | 3.53 | 0.08 s | 0.09 s | 1.99° | 0.079 |
| Unity box / mesh, 40 t | 3.56 / 3.56 | 0.08 / 0.08 s | 0.09 / 0.09 s | 1.98° | 0.081 |

The adapter agrees with the core within 1 % on every metric, and no PhysX body contact occurs. **Update 2026-11-18 (ADR 0228 r4):** the bump-stop unloading hysteresis (ADR 0228) lowers the wheel unload and pitch peaks; Fz peaks are unchanged by it. Runner on `alt-113-s24` (PR #113 + D79), first 6 s, = new constants in `KerbStrikeParityTests`: empty 3.68 / 0.08 s / 0.20 s / 1.44°, 40 t 3.30 / 0.08 s / 0.08 s / 1.42°; 27 cm step 6.03 / 0.33 s / 3.54° (main without hysteresis: 3.66 / 0.11 / 0.20 / 1.61°, 3.30 / 0.09 / 0.09 / 1.86°, 6.04 / 0.39 / 5.91°). Unity with #113 (int-h3-s23): 40 t pitch 1.38° (runner 1.42°). Tolerances unchanged; xUnit `KerbParityReferenceTests` re-runs the runner and fails when the constants go stale. The table above is the 2026-11-09 state. Ray normals on vertical mesh faces, ray count, step and substeps are therefore **not** the cause of the phone values.

**The phone event was not a 14 cm kerb.** Telemetry from r3 (`artifacts/device/RFGL34SJYDZ/20261109-180828`, t = 72.12–72.14 s): front left suspension compression goes 0.057 → 0.106 → 0.128 m and tyre deflection 0.036 → 0.117 → 0.212 m in two 10 ms steps. Their sum (the geometric rise of the ground under the ray fan) is 0.246 m. The front hardpoint itself rises about 3 cm (pitch −0.31 → −0.10°), so the effective step was **about 0.27 m**: a kerb on a higher carriageway or verge edge at the split, not the 5–14 cm kerb face. Scenario `kerb_step_27cm_42kmh_comb@laden40` (same block, 0.27 m, 42 km/h, 40 t) gives in the core Fz 6.50× static, tractor wheel unload 0.42 s (both front wheels 0.25 s), pitch +6.4°. On the phone: 6.8×, about 0.4 s, +8°. Unity (mesh) gives 6.48×, 0.45 s, +6.37°. The sum of compression and deflection at the peak is 0.251 m in the core and 0.254 m on the phone.

The only Unity-specific difference shows after the strike. When the nose comes down (−8°) with the front tyre deflected 0.19 m, the graybox **bumper collider touches the ground** (PhysX contact, 2.9 kN·s). This gives max |dv| 0.54 m/s per step (core 0.20; phone r3 0.59–0.71 m/s at landing) and damps the later oscillation (front Fz second peak 55 kN in Unity, 97 kN in the core). This is by design: PhysX owns chassis–world collisions, and the core has no body geometry.

Consequences: no adapter change is needed. The fix for the phone event is the world geometry (continuous kerb at carriageway splits, `806e89d`, already on main; check again after the WorldC s = 571 m blocker is fixed). The model gap that made it look so violent is the tyre: a linear radial spring with no bottoming lets the tyre deflect 0.19–0.21 m (section height of a 315/80 R22.5 is about 0.25 m), see §7.

## 4. Multi-run checks and cost

| Check | Values | Max deviation |
|---|---|---|
| Repeatability 0–60 / 0–80, headings 0°/37°/113° | 9.688 / 14.055 s | 0.00 % |
| dt 50/60/100/120 Hz: solo 0–80 | 14.212 / 14.210 / 14.055 / 14.070 s | 0.58 % |
| dt: solo dry stop | 34.173 / 34.211 / 34.264 / 34.281 m | 0.17 % |
| dt: circle R25 20 km/h lateral acceleration | 1.218 m/s² ×4 | 0.02 % |
| dt: 40 t dry ABS stop | 40.897 / 40.989 / 41.309 / 41.366 m | 0.59 % |
| dt: 40 t lane change max articulation | 0.823 / 0.824 / 0.826 / 0.827° | 0.28 % |
| dt: 40 t 0–60 | 28.395 / 28.283 / 28.042 / 28.161 s | 0.63 % |
| substeps 2/4/8: solo / 40 t dry stop | 34.506 / 34.264 / 34.599 m; 41.087 / 41.309 / 41.117 m | 0.56 % / 0.33 % |

(2026-11-16, `artifacts/tc-s23/run/summary.md`; the 2026-11-09 values are in git history.) Cost on that run (Linux desktop, Release,
`--bench`): mean 15.1 µs/step, p50 14.6, p99 28.5, max 289 µs — a different machine than the numbers below; neither is the
Windows reference PC nor a phone.

**Cost per fixed step**, full 40 t combination: 10 wheel ends × 15 rays, 4 substeps, clutch + brake PGS, fifth wheel 8 iterations, both body integrations. Desktop, Release, `--bench`, 30 000 steps:
- **p50 6.4–6.7 µs**;
- mean 6.0 µs on a quiet machine, 7.5–11 µs while another agent was running Unity;
- p99 6.8–34 µs depending on the same load.

Solo tractor: about 2–3 µs. This was measured on the desktop, **not** on a phone. The Samsung A budget (ADR 0004) still has to be measured.

## 5. Plot review (PNGs looked at) and what was fixed

Reviewed:
- launch 40 t 6 %; launch 40 t flat;
- brake 80→0 40 t dry and wet, ABS on and off;
- downhill 7 % brake cruise, full lever, Type-IIA and pumping;
- lane change 80 (40 t);
- jackknife without ABS (EBS fault and retarder), and with ABS;
- coupling and uncoupling;
- solo brake and launch;
- rollover (high CoG);
- park-circuit leak.

Several were reviewed again after each fix. Findings that changed the model:

1. **Gear hunting 4↔5↔6 on a 6 % climb with 40 t.** Speed was stuck at 15–20 km/h, with 40 shifts in 60 s. The cause: the grade bonus moved the down-shift line (1300 rpm) above the post-up-shift minimum (1250 rpm). Now an up-shift must land ≥ 100 rpm above the effective down-shift line, and the speed lost during the 0.55 s interruption is included. After the fix: 3→4→…→8 with 5 shifts, a steady climb to 41 km/h near rated power, and shifts at about 1850 rpm.
2. **Brake cruise limit cycle.** The lever stage chattered 2↔3 at 100 Hz, giving ±150 N m retarder ripple and +2 km/h offset. Brake cruise is now a PI controller inside the model that modulates the endurance brakes continuously. It holds exactly 60.0 km/h on 7 % with 40 t, with no service brake.
3. **Hard coupling impact.** The tractor reversed at 5 km/h into the braked trailer: 80 m/s² and 630 kN on the kingpin in one step. Two fixes: an AMT creep function (idle-speed approach at about 3 km/h), and a 0.4 s compliant jaw engagement. Now the bump is ≤ 62 kN.
4. **Tractor jump on uncoupling.** About 30–60 kN of kingpin load was released instantly into the levelled rear springs, and a wheel unloaded. Now the legs are cranked 7 cm past ground contact, so they lift the nose off the plate first. No wheel lift.
5. **Post-stop rebound after a locked-wheel stop** (also present in Stage 1: the +3.4 m/s² spike at the end of the solo brake run). The relaxation tire state kept about σ = 0.3 m of "deflection" from sliding. At standstill it acted as a spring and pushed the truck back up to 0.5 m/s. Below 3 m/s the deflection is now capped at the deflection at peak force (about 3 cm). The remaining post-stop motion is body pitch rebound, about 2° (physical).
6. **ABS depended on the fixed step.** Stop distance changed 5–6.5 % between 50 and 100 Hz, because the ABS loop ran per fixed step (20 ms at 50 Hz). The ABS, chamber pressures and the wheel-deceleration signal now run in the 2.5 ms wheel substeps. Deviation is now 0.09–0.29 %.
7. **Stage 1 note "rear lock ~0.1 s at brake onset".** Fixed by three things: EBS load sensing (the solo drive axle gets 25–36 % pressure), a wheel-deceleration "hold" criterion, and a slip-speed floor so the ABS does not dump in the last metres. Lock time is now 0 s in every ABS run (above 2 m/s).
8. **Stage 1 note "~2000 rpm overshoot in gears 4–5".** Fixed by an up-shift trigger on the predicted rpm, a 0.3 s same-direction hold-off (it was 1.0 s), and an over-rev guard. Max rpm in gears ≤ 6 is now 1668–1720 rpm.
9. **Launch with wheelspin.** The AMT left the launch state while the drive wheels spun (solo, 4th gear), and then cascaded down-shifts. Leaving launch now also requires small engine-to-road slip, referenced to vehicle speed.
10. **Jackknife at full pedal without ABS did not happen**, because all wheels lock and the combination slides as one body. That is physically right. The realistic failure cases were added instead: an EBS fault without load sensing at half pedal, where the light drive axle locks first (81°); and the retarder on wet with failed ABS (92°). The hard articulation stop gave a 2 m/s one-step impulse, so all fifth-wheel stops are now soft.
11. **Lane change too harsh, plus a driver weave.** 3.5 m over 40 m at 80 km/h is 0.34 g, almost the rollover threshold. The manoeuvre was changed to 70 m (path 0.18 g; the driver realises about 0.1 g). A 0.1–0.2 Hz weave after the manoeuvre came from the pure-pursuit driver, not the vehicle. A longer look-ahead and yaw-rate feedback in the driver removed it. A residual 0.04° articulation is plate-friction stick.
12. **Telemetry `a_lat` was the body-frame velocity derivative** (≈ 0 in a steady turn; also wrong in Stage 1). It is now v·r + dv_y/dt. The 12 % parking "drift" was vertical levelling settling, so creep is now measured in the ground plane.

Visual notes (not failures):
- Under ABS braking with 40 t, the kingpin pushes the tractor with about 100 kN, because the trailer is slightly under-braked by its ALB. Real EBS coupling-force control would reduce this. It is not modelled.
- In a hard stop the cab pitches about 3° and the body about 2°, with 2–3 visible pitch oscillations after stopping (ζ about 0.3).
- The AMT up-shifts once while coasting before a stop (11→12, then engine-brake down-shift). This is harmless.
- A 40 t hill start on 6 % launches in 3rd gear (2.5× force margin rule). That is plausible, but a real AMT may pick 1st or 2nd.

## 6. Golden telemetry

`tests/golden/*.csv` contains 9 scenarios:
- 40 t: hill start; dry and wet ABS stops; brake cruise; lane change;
- empty: wet stop without ABS; EBS-fault jackknife;
- solo: dry stop; 0–80.

Each file has 17 columns: speed, rpm, gear, accelerations, yaw, articulation, kingpin load, air pressures, retarder and engine-brake torque, two chamber pressures and two wheel loads. Sampling is 10 Hz, or 2 Hz for runs longer than 40 s; total 190 KB.

Tolerances are in `tests/golden/tolerances.json` as per-column absolute + relative values. A column may have up to 3 % outlier samples. Test: `Stage2Tests.GoldenTelemetry_Matches`. After an intended physics change, run `--update-golden` and review the CSV diff in the PR.

### 6a. Dimension sync, ADR 0019 (2026-11-09)

Fifth-wheel lead 0.55 -> 0.68 m (combination 16.47 m <= 16.50 m), cargo bay synced to the model (frontZ 1.572, length 13.512, width 2.50, height 2.58), body mass element centre y 2.60 -> 2.65. All 98 scenarios (482 checks) and 146 unit tests pass. Static loads laden40: front 6.27 -> 6.62 t, drive 11.11 -> 10.76 t. Metrics that moved more than 2 % against the previous run (all inside their check ranges): hill-start shift timing (ASR-limited launch, shift_count 5 -> 7, same speed after 30 s; overlay PNG looked at), coupling kingpin longitudinal peak -12.7 % (new jaw position), jackknife articulation -5 to -6 % (more front axle load), ABS stop mfdd -2.3 % with stop distance +1.3 %, speed-bump Fz ratio +4.4 % / cab heave +3.4 %. Goldens regenerated: brake_80_0_dry_abs_comb, brake_80_0_wet_abs_comb, jackknife_wet_curve_noabs_empty, launch_6pct_uphill_comb (ABS cycle / shift phase moved). Other goldens still pass unchanged.

### 6b. AMT down-shift hold, ADR 0024 (2026-11-10)

The PlayMode hill start (`CombinationLabTests.HillStart_6pct_40t`, 6.27 s against 4.5 s ± 10 %) failed for the same reason as the runner (6.17 s; its old 3-35 s range hid it). After the ASR-limited launch the engine was at 1293.6 rpm, rising at 220 rpm/s. That is under the 1300 rpm grade down-shift line, so the AMT shifted 3-2-3-4. Fix: no down-shift while the current gear still gives the up-shift acceptance acceleration (mirror rule); the lugging guard is judged one shift duration ahead; an over-rev up-shift needs a gear that holds speed; the rpm-rate filter starts at 0. Results: 6 % laden40 4.59 s / 5 shifts (pre-ADR 0019: 4.54 s / 5); 12 % laden40 19 → 4 shifts, steady 21.5 km/h instead of 4-5-4 hunting. Runner: 99 scenarios / 493 checks and 146 xUnit tests green. Movers > 2 % against main: hill starts (intended), downhill_7pct_brake_cruise_60 peak retarder torque −23 % (11-9 directly instead of 11-10-9 at t = 0, engine brake on sooner), launch_6pct_uphill_light_comb time_to_kmh(10) −8.5 % (the same 3-2-3 at 35 % pedal removed), jackknife_wet_curve(_retarder)_noabs@laden40 max_dv_step +4.5 to +6.7 % (0.042 / 0.269 m/s against the 0.35 limit; different shift at t = 0 shifts the lock event phase), plus fifth-wheel error and max_dv decreases in µm / mm/s. Goldens regenerated: launch_6pct_uphill_comb_laden40, jackknife_wet_curve_noabs_empty. Overlay plots (`tests/physics/plot_shift_overlay.py`) were reviewed for 6 % (before ADR 0019 / main / ADR 0024) and 12 % (main / ADR 0024).

Note (fixed 2026-11-10): the generator now carries the strict kerb checks of curb_strike_5cm/14cm and kerb_step_27cm (it used to emit looser ceilings, e.g. Fz 4.0 instead of 2.2 for 5 cm, 4.5 instead of 4.2 for 14 cm, wheel-off 0.1 instead of 0.08). It derives the kerb block from `art-source/truck/dims.json` (left tyre patches of front, dual rear and trailer tridem; combination 16.47 m, ADR 0019) and exits with the numbers if the block no longer fits. `tests/physics/test_scenario_strictness.py` fails when the generator drifts from the committed JSON or a kerb ceiling is raised. Runner after the change: 99 scenarios / 493 checks green.

### 6c. Parking brake drive-away and shift gap, ADR 0004 addendum (2026-11-10)

Owner feel test: "braked when accelerating and shifting" was P left on. The truck spawns parked, and at full throttle the
40 t combination dragged through the 2 x 16 kN m tractor spring brakes in launch gear 4 (45 kN m) up to 15.9 km/h on the
phone and 16.9 km/h in the runner. Each up-shift then fell at -1.55 m/s². New scenarios: `park_brake_drive_away_comb`
(empty, laden40), `park_brake_hold_no_interlock_comb`, `park_low_air_drive_away_comb`. `launch_flat_comb` also checks
`max_shift_retard_torque_nm` <= 1 N m and `min_accel_shift_gap_ms2` >= -0.3 m/s². All of them fail on 111f437.

| Run (laden40 unless noted) | before (111f437) | after |
|---|---|---|
| P on, full throttle 10 s: max speed | 15.6 km/h (empty 16.4, stall) | 0.003 km/h (empty 0.0006) |
| P on, interlock off: max speed / clutch temp | n/a | 0.05 km/h / 135 °C |
| Up-shift with P on: gap dv/dt, wheel brake torque | -1.55 m/s², 32 kN m | no shift (no movement) |
| P off: brake + retarder + engine brake torque in shifts | 0 | 0 |
| P off: worst per-gap mean dv/dt | -0.126 (empty -0.207) m/s² | unchanged |
| Shift interruption | 0.63 s | 0.63 s |
| 0-60 / 0-80 km/h | 26.9 / 46.2 s | unchanged |
| park_12pct trailer / tractor creep after 5 s (limit 5 mm) | 1.3-3.6 / 0.04-0.27 mm | 3.5-4.8 / 1.0-2.1 mm |

Evidence: `artifacts/physics/shift-brake/` (before/, after/ CSV + PNG, suite-before/, suite-after/ summaries).

Note (D42, 2026-11-16, ADR 0280 §10.5a): `park_brake_hold_no_interlock_comb@laden40` `creep_m` was 26.8 mm (main) and
55.2 mm (after the ADR 0280 §10.3 relaxation fix). Both values came from a leak, not from wind-up. The standstill
relaxation bled the trailer brakes' reaction to the engine push at 1.3 and then 4.1 mm/s with no end (55 mm at 12 s, 251 mm
at 60 s). While a towing wheel carries driveline torque, the braked trailer wheels now keep their deflection. The creep is
now 14.4 mm and stops there (13.95 mm at 60 s). It is the same at dt 1/50 to 1/120 (14.36-14.37 mm) and equal to the run
with relaxation off (14.29 mm).
Runner determinism (ADR 0004 addendum 2026-11-16): each scenario run loads its own definitions, so a test cannot change
the physics of a run on another xUnit thread.

### 6d. Truck feel after the Fold test, ADR 0134 (2026-11-12)

Owner: rocking "like a sports car" when accelerating, gears change "very quickly". Diagnosis: the free-drive default is the
empty trailer (14.5 t, 25 kW/t), the acceleration matches that mass (0-50 km/h 10.2 s empty / 19.5 s 40 t at full pedal),
and the nod came from each shift (clutch closing 200-300 rpm off synchronous speed, linear 0.12/0.15 s torque ramps, cab
ζ 0.35). Changes: light-load skip shift, smoothstep torque fade 0.20 s out / 0.35 s in, engine-brake up-shift sync, cab
ζ 0.5. New metric `max_shift_eye_pitch_swing_deg`, new scenario `launch_flat_comb_part60`.

| launch on flat | 0-50 km/h | up-shifts to 50 | per-shift eye nod max |
|---|---|---|---|
| empty, full pedal | 10.17 -> 9.85 s | 5 -> 3 | 5.39 -> 3.83° |
| 40 t, full pedal | 19.51 -> 20.41 s | 5 -> 5 | 4.57 -> 3.40° |
| empty, 60 % | 13.91 -> 14.90 s | 5 -> 5 | 4.50 -> 3.62° |
| 40 t, 60 % | 32.89 -> 33.97 s | 5 -> 5 | 3.23 -> 2.34° |

Runner 107 scenarios / 550 checks green, xUnit 155/155, 9 goldens regenerated (shift timing). Plots reviewed:
`artifacts/truck-feel/before_after_overlay.png`, `artifacts/truck-feel/{before,after}/*.feel.png`.

### 6e. Chassis colliders in the runner, F2 (ADR 0158, 2026-11-13)
F2 ("275 km/h airborne", M34 fuzz) was a free fall through the road, not energy injection. With all wheels off the ground
after a rollover, E = KE + PE never grew (largest step gain 0.000 kJ), the CoM fell to −3070 m, and `max_speed_kmh`
(SpeedFwd) was the fall velocity projected on the tumbling tractor's forward axis. The runner's stand-in bodies had no
chassis colliders (Unity has the graybox BoxColliders). `Sim/BodyGroundContact.cs` now adds them: box corners vs ground,
PGS non-penetration + Coulomb friction 0.6 (Unity default material), restitution 0, zero GC. `RigidBody6Dof` uses an
implicit gyroscopic update (the explicit one gained +136 % KE in a 30 s torque-free tumble). The F2 repro moved to
`scenarios/` with fall-through, rest and energy checks. `free_fall_drop_comb` checks free-flight ballistics:
|a_CoM − g| 0.0077 m/s², E gain 0. Runner: 129 scenarios / 730 checks green; the 707 pre-existing values unchanged except 33 at
≤ 0.15 %. `kerb_step_27cm_42kmh_comb` runs without colliders for now: its bumper corner strikes the road (dv 0.755 m/s;
Unity PlayMode on the same event 0.968 m/s), which is a decision for the leader (ADR 0158 Open 1).

### 6f. Straight run 0–80–0 autopilot for gates 1–2 (ADR 0195, 2026-11-13)
`StraightRunPilot` (Vehicle/Physics/Pilots) drives only the pedals, selector and wheel: brake 1 s → full throttle to 80 km/h →
PI hold 4 s → full brake to a stop. The same source drives the runner (`straightrun`, scenario `straight_0_80_0`, solo/empty/laden40,
39/39 checks) and the game (`autopilot=straight080`, fixed step, new 1300 m measurement straight in DrivingLab, z = 300).
Runner → Unity editor: 0–80 13.60 → 13.67 s / 20.54 → 20.68 s / 47.52 → 47.80 s; 80→0 35.69 → 35.62 m / 39.49 → 39.45 m /
40.52 → 40.78 m; MFDD 7.0–7.5 m/s², no wheel lock, lateral ≤ 4 mm; solo ×3 0.00 %. `Metrics.FirstBrake` is now the first
rising edge of the pedal (unchanged for all `brake_*` scenarios). Phone numbers: `gate12-phone.ps1 -Only s080_*` (leader).

### 6g. Axle loads 73/27 % and suspension retune, ADR 0201b (2026-11-15)

- Mass split calibrated to the S9 sheet (R3-013/014): solo without fuel 5.06 / 1.84 t (73.3 %), with fuel 5.35 / 2.15 t, 40 t 7.20 / 10.26 / 22.55 t. Front leaf 250 kN/m, front dampers 10/20 kN s/m, anti-roll 222 / 240 kN m/rad, rear air spring unchanged hardware (73 kN/m at the new reference load), rear bump stop 15 mm. AMT: shift schedule from the driver pedal (not the ASR-cut torque request), anti-stall clutch opening 8/s.
- Runner 135/135 (`artifacts/axleloads-0201b/final/`), tolerances unchanged; the 4 scenarios that the uncalibrated shift (ADR 0201 n1) broke: kerb 0.11 s / 3.66 (base 0.12 / 3.94), eye nod 3.64° (3.79°), rollover first lift 0.458 g (0.460 g), soak drift −2.8 J (1.4 J). The n1 soak drift (44.9 J) is the same at dt 0.005 s and 8 substeps (`soak-dt/`): physical settling after the stop, not the integrator.
- Solo 0–80 13.58 → 14.06 s (+3.5 %; masses alone +8.2 %, AMT fix −1.3 %): ASR-limited launch on the lighter drive axle. Solo 80→0 35.77 → 35.39 m; 40 t 47.54 → 47.58 s, 41.02 → 41.20 m.
- Goldens: 6 re-recorded (overlays `artifacts/axleloads-0201b/plots/golden-*.png`).
- **F2 energy source (owner decision 2026-11-15: fix the physics, not the test).** Per-step energy balance of the F2 mutation run without chassis colliders (`artifacts/axleloads-0201b/f2/energy-balance.txt`): the kingpin point / Baumgarte row does ≤ 40 J per step (mostly negative); the free-flight KE + PE gain came from (1) the **rebound of the compliant fifth-wheel stops** (pitch 10 Hz ζ 0.7, roll stop, yaw 3 Hz ζ 1: stored spring energy returned as relative velocity, e.g. 4.5 kJ of a 58 kJ plate-pitch impact) and (2) the **roll spring releasing energy injected by raycast tyre contact at grazing incidence** (lying combination: S = d/cos(tilt) − r jumped +0.19 → −0.50 m in one step, 1.6 MN per wheel, +52 kJ of wheel work in 10 ms). KE + PE + coupling elastic energy never grew in free flight. Fix: stops keep the soft spring-damper on approach but push the bodies apart at ≤ `stopRecoveryRateDegS` 0.5 deg/s (no rebound; ≤ 0.87 J of KE); no tyre contact when the surface normal is > `maxContactTiltDeg` 72.5° (acos 0.3, the existing clamp) from the suspension axis. F2 scan 230–260 kN/m step 0.5: before 42/61 values > 1 J (max 2044 J), after **0/61 (max 0.000 J)** (`f2/f2-scan.png`). .NET **277/277** (3 new tests in `F2CouplingEnergyTests`); runner 135/135 (789), 772 checks bit-identical, 17 changed (all PASS, `f2/runner-diff.txt`): A16 launch/brake values identical; kerb 15 cm roll +0.007° / trailer +0.010° (ray grazing the kerb's vertical face no longer loads the suspension); with-collider rollover F2 max dv/step 0.67 → 0.82 m/s (≤ 4.2) and kingpin error 5.7 → 14.0 mm (≤ 50), lying wheels no longer push; reverse dock laden final z −17.33 → −17.25 m (yaw stop without rebound).

### 6h. Tractor-trailer body contact (jackknife limit) and heavy landing, ADR 0228 (2026-11-15)

- The articulation is limited by the **physical contact** of the trailer body with the cab / mudguards / frame (`CouplingContact`, soft no-rebound contact rows in the fifth-wheel PGS, 5 Hz, ζ 0.3, recovery 0.05 m/s, μ 0.3), from the definitions' `bodyBoxes` (one geometry source with the runner's chassis colliders). Level first contact **117.12°** (trailer side wall on the cab rear corner); the ±90° angular stop is only the fallback without body boxes.
- New scenarios (`tests/physics/generate_jackknife_scenarios.py`): fold 90° (laden / empty: 108.6° / 105.4°, no contact), fold "120°" pushed into the cab (contact 7.5 / 9.3 s, excess over 117.12° 1.48 / 1.50°, penetration 0.046 / 0.051 m, yaw restitution 0.03), fast swing impact at 53–54°/s (penetration 0.050 / 0.053 m, peak contact force ~270 kN for ~0.1 s, dv/step 0.23 m/s), reverse with counter-steer then pull forward (final articulation ~0°), 0.5 m drop.
- Heavy landing: bump-stop unloading hysteresis (Hunt–Crossley form, h 4 s/m, compression elastic): 0.5 m drop 40 t rebound 0.68 → **0.39** of the drop energy, second take-off 0.27 s → **0**; empty 0.37 → 0.16; 1 m drop (`free_fall_drop_comb`) 0.78 → 0.30 (still 0.16 s airborne). Kerb Fz peaks unchanged (a symmetric version raised 14 cm kerb max_fz_ratio 3.66 → 5.76 and was rejected).
- Changed existing checks (**ADR 0228**): `reverse_dock_s_maneuver_comb` max articulation 95° → excess ≤ 1.5° over the contact angle + penetration ≤ 5 cm (folds to 118.2°). Golden `brake_80_0_dry_abs_comb@laden40` re-recorded (front bump stop in the 40 t stop; 41.31 → 41.25 m, MFDD 6.885 → 6.899 m/s²).
- Runner **145/145 (879 checks)**, .NET **295/295**, robustness bit-identical / 0 NaN, bench p50 +0.4 µs/step (`artifacts/jackknife-0228/`). Before/after plots: `artifacts/jackknife-0228/png/`.
- **H11 (2026-11-16, after merging main; review s22 #113 P1 + FFB #132):**
  - *Tight forward turn.* The flat graybox trailer front (corner 2.063 m, 7 mm to the cab back) touched the cab in tight turns once the plate pitched / rolled: runner probes at 55–60° articulation, hard stop from 13–20 km/h: 0.11–6.8 s of contact, 38–131 kN (mostly 40 t) (a "brake" on the trailer from the cab). The coupling outline now follows the art model's rounded front (swing 2.029 m, boxes BodyCoupling + Nose; `Body` stays the ground collider): 4.1 cm clearance, no contact up to 110° for |relative pitch| ≤ 1.13° / |roll| ≤ 1.44°. New scenarios `jackknife_tight_turn_forward_comb` (5 km/h, lock 0.57, 57.6 / 58.1°) and `jackknife_tight_turn_forward_10_comb` (10 km/h, other side, 57.3 / 58.5°), each with a full stop at 40 s: **0 contact** (checks `coupling_contact_s` = 0, penetration = 0, force = 0). Residual (open): a full stop from 13–20 km/h at 55–60° with 40 t still grazes after the stop (tractor rocks back ~1.2° nose-up; all contact at ≤ 1.33 km/h, 0.03–0.94 s, ≤ 0.61 mm, 25–99 kN peaks; FFB aligning term faded to ~0 below 1.1 km/h); empty at 60° / 20 km/h one speculative touch while turning in (18 km/h, 0.02 s, 0 mm, 10 kN). Probes `artifacts/jackknife-0228/h11/probe_scenarios/` (before: 0.11–6.8 s, 38–131 kN).
  - *Steering feedback.* The contact force does not enter `AligningTorqueTotal` directly, but it reverses the tractor's yaw in ~0.1 s and drags the steered axle sideways; the aligning torque swung −0.9 → +2.3 kN m in 80 ms (40 t fold into the cab) and the FFB model (ADR 0263 defaults) reversed −0.75 → +1.0 at its slew limit. `AligningTorqueTotal` is now lagged (0.5 s) while the bodies touch and 0.5 s after (raw value in `AligningTorqueRaw`, tyre forces unchanged): FFB rim-torque target change per 10 ms in the contact **0.34–0.49 N m** (was 2.0–4.5; kerb strikes 1.7–3.8 via the road-feel term; lane change 80 km/h 0.03), output step ≤ 0.061 (slew step 0.2). xUnit `JackknifeForceFeedbackTests` (real `ForceFeedbackModel` compiled from `game/Assets/_Project/Input`).
  - Runner **149/149 (915 checks)**; vs before H11 only `jackknife_reverse_countersteer_comb@laden40` changed (penetration 1.3 mm → 0). .NET **319/319**. Bench p50 13.4–14.3 µs vs 13.9–14.0 µs before (noise). Plots `artifacts/jackknife-0228/h11/png/` (`turn_*`, `ffb_*`).
- **r4 (2026-11-18, `alt-113-s24`, after merging main with D79 7.63 m):** golden `brake_80_0_dry_abs_comb@laden40` is the **main file again** (the #113 file was recorded on the 7.70 m geometry; the merged run passes the main file: worst column kingpin_fz 2.0 % outliers of 3 %; stop 41.385 m, MFDD 6.876; no body / coupling contact in the run). New metric `max_pitch_deg`; `KerbStrikeParityTests` constants from the runner (§3b). Residual cab brush after a hard stop in a 48–56° turn (ADR 0228 Otwarte 1) as scenarios `jackknife_turn_stop_brush_{20,15}_comb`: 40 t 1.10 / 0.09 s, 75.9 / 90.5 kN (first contact step, ~0 mm), 0.155 / 0.610 mm; bounds 1.5 s / 100 kN / 1 mm. Steering-feedback smoothing now hands back to the raw value at most hold + lag = 1.0 s after the last contact (was up to > 6.9 s; rim output unchanged); CSV column `aligning_torque_raw`. Runner **159/159 (987 checks)**, .NET **338/338**, pytest `tests/physics` 35 passed.

## 7. Known gaps / not modelled

- **Not run in Unity or on the phone.** PhysX integration of two bodies with this constraint, cost on the Samsung A, and the feel test (docs/03 Stage 2 gate) are still open.
- **No tyre bottoming (rim contact)**: the radial spring is linear without a deflection limit, so a step above about 0.2 m deflects the tyre 0.19–0.21 m and lets the body drop onto its bumper collider in Unity (§3b). A progressive end stop needs a source for the rim-contact deflection (not opened).
- **Items not covered by the runner:** §6.10 (reversing to a ramp, tight yard manoeuvres; needs a reversing driver, and a dock or ramp geometry), §6.13 (floating origin and streaming, Unity), §6.15 for input modes other than the direct steer command (touch, gyro: Unity input layer).
- ~~No chassis–ground or tractor–trailer collision geometry.~~ Chassis colliders since ADR 0158/0165; tractor–trailer side contact since ADR 0228 (jackknife ends on the cab at ~117°). Still not modelled: top-to-bottom contact (trailer body on a mudguard / the frame end), landing-gear legs and the gooseneck as contact geometry; the trailer front clears the cab back by 4.1 cm (rounded coupling outline since H11; a 40 t stop from ≥ 13 km/h at 55–57° still grazes after the stop, ADR 0228 Open 1).
- **Ruts are not modelled**: rays are in the wheel plane only. No dynamic load sharing between interconnected bellows (only static equalisation by levelling). A trial on the kerb strike made no difference (§3a). **No trailer frame torsion**: on a one-sided step the rigid frame lets a tridem axle hang at full droop (0.21 s, empty, §3a). **No unsprung mass**: wheel ends are massless, and the tire is in series with the suspension, so there is no wheel hop.
- **Brakes:** no thermal model or fade; no EBS coupling-force control; ABS uses the true contact-point speed as the reference speed (a real ECU estimates it); the trailer ABS is one generic layout. Compressed-air response is checked against R13 Annex 4 §4.1.1, but the Annex 6 method was not read.
- **Endurance brakes:** the retarder has no oil-temperature derating (only the 600 kW power cap); the EPG-only exhaust brake stage is not separate.
- **Parking brake:** the interlock is a design rule (production AMT behaviour UNVERIFIED). The "trailer test" position of the hand valve is not modelled. The HUD/chime hookup of `ParkingBrakeWarning` is open (gameplay-ui).
- **AMT:** no GPS predictive strategy; mass and grade are taken from the model, not estimated; the creep function is a fixed torque.
- **Unsourced numbers:** most trailer, air and brake parameters are WORKING_VALUE (see the reference data). The rollover threshold and rearward amplification bands rest on unopened literature.

## 8. Owner feel test (phone, Stage 2 gate), checklist

1. Hill start, 40 t on a steep street: no rollback, the engine note rises under load, no hunting after the start.
2. Emergency stop from 80 km/h, empty and 40 t: cab dive, ABS feel, straight line; then the same on wet.
3. Roundabout at 30–40 km/h with 40 t: trailer roll, offtracking over the inner kerb.
4. Reversing to the ramp with the trailer camera (needs Unity scene): articulation response, the stop at 90°.
5. Long descent with the retarder lever and brake cruise: speed held, no service brake.
6. Coupling to a parked trailer at walking pace: a bump, but not a hit.
7. Full accelerator with P on: no movement, engine at idle, parking-brake warning. Release P, wait ~1 s, accelerate: normal launch, no braking felt in the up-shifts.

Note for each item: mass feel, braking, steering wheel feedback, trailer behaviour.

## 9. Gate 3 swept path (G3-A, G3-B, Rondo Bieżeństwa lap), 2026-11-10

Script `tests/physics/swept_path_gate3.py`, test `tests/physics/test_swept_path_gate3.py`. The runner's `path` driver
uses Stanley steering on the steer axle and a PI speed controller; laden 40 t, flat ground. Geometry: the visual
`road`/`paved` meshes of the world build, rasterised at 0.10 m into carriageway / apron / kerb / off. Speed profile:
a_lat 1.2, decel 0.8, accel 0.4 m/s², ring capped at 15 or 25 km/h (all WORKING_VALUE). Driver lines: `lane` = route
smoothed σ 4 m (the raw route has kinks at OSM nodes; following it saturated the steering at 40° and made loops),
`wide` = steer axle moved outward by 0.5 × steady-state off-tracking (≤ 1.75 m). Both roundabout passages on the route
are first-exit right turns, so the ring is also checked with a 1.25-lap run on the Bieżeństwa ring centreline
(R 23.36 m).

| run | min tyre clearance to kerb line | where | apron use | body / props |
|---|---|---|---|---|
| G3-A lane, 15/25 km/h | **-1.10 m** (tridem, inner side) | Bieżeństwa exit corner, s 366-369 | 0 | trailer rear corner 0.6 m over the corner; props ≥ 0.93 m |
| G3-A wide, 15/25 km/h | -0.10 / +0.10 m (within raster tolerance) | same corner | 0 | props ≥ 0.81 m (gate, s 248) |
| G3-B lane / wide | +1.21 / +1.27 m | Putry entry s 1709-1714 / trunk_link s 1430 | 0 | props ≥ 3.07 m |
| Bieżeństwa lap 15/25 km/h | +1.61 m (steer, outer); tridem inner +2.6/+2.9 m from the apron edge | ring | 0 (apron not reached) | props ≥ 1.84 m |

Max articulation 32.8° (G3-A), steer 27°. Conclusion: the geometry can be driven. At the Bieżeństwa exit corner the
driver has to take a wide line; the AI or assist path should swing out there. The 2 m apron is never used because the
ring is wide for this vehicle. Guidance: WR-D-31-3 "Ronda" (Ministerstwo Infrastruktury, valid from 2022-11-30),
chapter "Jezdnia i pierścień". Its numeric widths and the design-vehicle definition were not read (UNVERIFIED).

## Touch steering in the loop (ADR 0149)

The runner also compiles the game's touch chain (`Input/TouchSteeringWheel.cs`, `SteeringColumn.cs`, `SteeringMath.cs`,
`DriverIntent.cs`; UnityEngine shim `tools/physics-runner/Sim/UnityShim.cs`). Driver type `touch` (`TouchDriver`):
replay of a measured thumb (`fingerKeys` [t, mm, held]) or a human model (preview 1.5 s with heading and heading rate,
perception delay 0.25 s, thumb lag 0.1 s, fixed thumb gain mm per m of lateral error; all WORKING_VALUE).

```powershell
dotnet run -c Release --project tools/physics-runner/Runner -- --touch-evidence artifacts/steer-r2/evidence
uv run tests/physics/plot_touch_feel.py artifacts/steer-r2/evidence
dotnet test tools/physics-runner -c Release --filter "FullyQualifiedName~TouchSteeringTests"
```

| metric (40 t, 35 km/h) | ADR 0135 curve | ADR 0149 | check |
|---|---|---|---|
| cab-wheel deg per mm | 23.5 | 14.7 | a_y per mm ≤ 60 km/h value (0.33 m/s²) between 20 and 60 km/h |
| replay of the owner's 4.4 mm flick: road wheel / heading at 5 s | 4.76° / 8.9° | 2.97° / 5.7° | ≤ 0.7× before |
| lane change, thumb 4 mm/m: PIO index (yaw-rate weave RMS) | 10.2 °/s | 0.06 °/s | < 0.75 °/s after, > 0.75 before |
| PIO onset thumb gain 30/35/40/50 km/h | 4/3/3/4 mm/m | 5/5/5/6 mm/m | no worse anywhere, ≥ 5 at 30-50 km/h |

Open (diagnostic only): after a released steering pulse the combination keeps a small articulation (40 t: −0.41°) and a
steady yaw rate (0.43 °/s) with straight wheels; solo returns to zero. Plate friction μ 0.08 is a WORKING_VALUE.

### Straight running after a released steering pulse (ADR 0151)

`straight_after_steer_pulse` (solo / empty / laden40): the owner's thumb flick replayed through the touch chain at
35 km/h, then released. From 10 to 14 s: max |articulation| ≤ 0.05° and max |yaw rate| ≤ 0.05 °/s. With the former
ideal-stick plate friction it failed (40 t: 0.413° / 0.426 °/s held for 20 s); with plate creep 1 °/s it passes
(0.0027° / 0.0011 °/s). Drag gesture above 60 km/h: lateral acceleration per mm held at the 60 km/h value; PIO onset
thumb gain at 70/80/90 km/h 6/6/5 → 8/10/10 mm/m.

## PC input chain in the loop (drive-feel-s24, 2026-11-20, ADR 0312)

`dotnet run -c Release --project tools/physics-runner/Runner -- --input-feel <dir> [--feel <json>]` drives the physics core with
the game's own keyboard / pad chain (`KeyboardAxisRamp`, `PadSteerFilter`, `SteeringColumn`, shipped `pad_keyboard_feel.json`
and `steering_feel.json`): full key / stick held at 20-90 km/h (40 t, cargo CoG 2.6 m, and empty), a 0.1 s key tap, and lane
changes by a human model (keyboard bang-bang with hysteresis; pad proportional, gains 0.25 / 0.5 / 1.0 per m). Plots:
`uv run tools/telemetry/plot_input_feel.py <before> <after> --cases ... --out <dir>`.
Before ADR 0312 a held key tipped the high-CoG 40 t combination at 30-90 km/h (wheel lift; rollover at 80/90); after: no
wheel lift, tractor peak ≤ 2.53 m/s², trailer ≤ 2.39 m/s² (< 0.8 x the 3.3 m/s² threshold of `rollover_r50_cog_high`);
a tap moves the combination 0.26 m in 4 s at 50/80 km/h (was 0.70 / 0.65). The 159-run suite is unchanged (987/987 PASS).
