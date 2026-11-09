# Physics validation — Stage 2, tractor 4x2 + semi-trailer

Status: **93 scenario runs (445 checks) and 141 xUnit tests are green** in the plain .NET runner (2026-11-09; ADR 0009 requests R5–R7 resolved on branch `worktree-agent-a949c191e8892b0e8`, see section 2a). This covers the solo tractor, the empty combination (14.5 t) and the 40.0 t combination. Nothing has been run in Unity or on a device yet. Stage 1 history is in git (`ee235b4`).

Parameter provenance: `docs/VEHICLE_REFERENCE_DATA.md`. Most numbers are still WORKING_VALUE, so the tolerances mostly check **plausibility and numerical quality**. The exceptions are the items backed by UN R13 Annex 4 text (S5), the 90 km/h limiter (S3) and the class-reference engine and gearbox data (S1, S2, opened in Stage 2).

## 1. How to run

```powershell
$env:DOTNET_ROOT = "$env:LOCALAPPDATA\Microsoft\dotnet"; $env:PATH = "$env:DOTNET_ROOT;$env:PATH"
dotnet test tools/physics-runner -c Release                                   # 141 tests, ~10 s
dotnet run -c Release --project tools/physics-runner/Runner                   # 93 runs + multi-run checks + bench -> artifacts/physics/<ts>/
dotnet run -c Release --project tools/physics-runner/Runner -- --only brake_80_0_dry_abs_comb          # all variants of one scenario
dotnet run -c Release --project tools/physics-runner/Runner -- --only lane_change_80@laden40          # one variant
dotnet run -c Release --project tools/physics-runner/Runner -- --update-golden   # rewrite tests/golden/*.csv (review the diff!)
dotnet run -c Release --project tools/physics-runner/Runner -- --bench           # cost per step, 40 t combination
uv run tools/telemetry/plot.py artifacts/physics/<ts>/                         # one PNG per CSV
uv run python tests/physics/generate_stage2_scenarios.py tests/physics/scenarios   # regenerate the Stage 2 scenario JSONs
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
- Result: kingpin / static 1.005 (empty) and 1.014 (40 t) at 50–80 s after raising the legs on locked brakes (was 0.95 and 0.90 in the same scenario without the fix; 0.67 in the Unity case, which was not reproduced exactly).

**R7, trailer / cargo swap without rebuilding.**
- `CombinationModel.SetTrailer(TrailerModel trailer, bool coupled)`: replaces the trailer (or removes it with `null`), resets the fifth wheel without counting an uncoupling, clears the arming, re-levels both suspensions. The tractor model and the combination object stay.
- `CombinationModel.SetCargo(CargoDefinition)` / `TrailerModel.SetCargo(cargo, onKingpin)`: changes the load case of the existing trailer model in place (mass, CoM, inertia, static axle loads, pre-levelling). No new wheel group.
- Both are between-step calls. `TrailerModel.MassProps` and `.Cargo` are now properties that change on `SetCargo`: copy `MassProps` into the Rigidbody again. The step stays allocation-free (test `Step_DoesNotAllocate_AfterSetCargo`: 0 B over 500 steps after a cargo change).
- Tests `SetCargo_InPlace_SettlesToNewStaticLoad` (22 t, then back to empty: kingpin / static 1.000, 0.998), `SetTrailer_SwapsWithoutRebuildingTheCombination` (18 t swap 1.000, then solo).

## 3. Results (runner, dt = 0.01 s, 4 substeps; run `artifacts/physics/stage2-final`)

Values are for solo / empty / 40 t where the item has variants. ✅ = all checks of the scenario passed.

| docs/04 §6 | Scenario | Key result | Expected / tolerance | Status of expectation |
|---|---|---|---|---|
| 1 | park_12pct_down/up_comb (300 s, tractor spring brakes only) | creep after 60 s ≤ 1.8e-7 m; total creep ≤ 0.39 mm; max speed ≤ 0.66 mm/s | ≤ 0.5 mm / ≤ 5 mm / ≤ 1 mm/s | **SOURCED** 12 % (S5 2.3.2) + WORKING no-creep ✅ |
| 1 | park_flat_5min_comb, soak_30min_parked | drift 5e-7 m, KE 2e-7 J over 30 min, air 12.5 bar | ≤ 5 mm, ≤ 1e-3 J, ≥ 10.5 bar | WORKING ✅ |
| 2 | launch_6pct_uphill_comb (full throttle, HSA) | rollback 2.1 / 2.3 mm; 0–15 km/h 2.5 / 4.5 s; clutch 30 / 37 °C; 7 / 5 shifts | ≤ 5 cm; ≤ 250 °C; ≤ 14 shifts | WORKING ✅ |
| 2 | launch_6pct_uphill_light_comb (35 % pedal, 40 t) | rollback 2.3 mm, 0–10 km/h 19.7 s | ≤ 5 cm | WORKING ✅ |
| 3 | launch_0_80_flat / launch_flat_comb | 0–60: 9.7 / 13.3 / 26.9 s; 0–80: 13.8 / 20.5 / 46.2 s | 40 t: 25–60 / 40–95 s | DERIVED (power-to-weight + shift losses) ✅ |
| 4 | top_speed_flat_comb | 89.4 / 89.2 km/h in 12th | ≤ 90.5, settles 87–90 | **SOURCED** S3 ✅ |
| 4 | grade_5pct_steady (40 t) | 50.2 km/h steady, ±0.03 km/h, 1516 rpm | 44–60 km/h | DERIVED: η P / (m g (sin α + f_r) + aero) ≈ 54 km/h ✅ |
| 5 | brake_80_0_dry (ABS) | 34.9 / 39.0 / 40.5 m; MFDD 7.41 / 7.48 / 7.07 m/s² | ≤ 61.2 m; 5.0–8.0 | WORKING (R13 N3 type-0 figures UNVERIFIED) ✅ |
| 5 | brake_80_0_wet (ABS) | 50.9 (solo, Stage 1 file) / 54.9 / 56.5 m; MFDD 5.0 / 4.8 / 4.7 | 45–95 m | WORKING ✅ |
| 5 | brake_80_0_dry / wet no ABS | dry 44.7 / 44.6 / 49.1 m; wet 75.4 / 78.2 / 81.9 m (locked) | longer than ABS | WORKING ✅ |
| 5 | brake_response_static | front 0.25 s, rear 0.31 s, trailer 0.53–0.54 s (75 % of final) | ≤ 0.6 s | **SOURCED** S5 4.1.1 ✅ |
| 5 | rear / trailer lock under ABS (all ABS runs) | 0 s above 2 m/s | ≤ 0.03 / 0.05 s | Stage 1 note fixed ✅ |
| 6 | downhill_7pct_typeIIA (40 t, 6 km, brake cruise 30 km/h) | mean 30.0 km/h, service brake 0, max 1971 rpm | 25–35 km/h, no service brake | **SOURCED** S5 1.8.2 ✅ |
| 6 | downhill_7pct_brake_cruise_60 | 60.0 km/h ± 0.000; EB ≈ 200 kW + retarder ≈ 170 kW (≤ 3103 Nm) | 59–61.5; ≤ 4000 Nm | S2 retarder limit ✅ |
| 6 | downhill_7pct_full_lever | speed settles (range 0.001 km/h over 40 s), EB torque 1173 Nm | stabilises | WORKING ✅ |
| 6 | downhill_7pct_service_pumping (endurance brakes off) | service circuits fall to 5.06 bar, warning on | ≤ 9 bar, ≥ 3 bar, warning | WORKING (real consequence) ✅ |
| 6 | air_leak_rear_circuit (burst at 60 km/h) | warning; rear circuit 0 bar; stop 33.1 m on the remaining circuits | ≤ 64.4 m | **SOURCED** S5 2.2 secondary braking ✅ |
| 6 | air_leak_park_circuit | trailer emergency braking + spring brakes stop the combination | stops | WORKING ✅ |
| 7 | circle_r50_10/35kmh_comb | offtracking 0.61 / 0.60 m at 10 km/h, 0.48 / 0.41 m at 35 km/h; a_y within 1 % of v²/R | 0.4–0.8 m at 10 km/h | DERIVED (√(R²+e²) − √(R²+e²−L²) = 0.59 m) ✅ |
| 7 | rollover_r50_cog_low / high (40 t, speed ramp) | first wheel lift at **0.462 g** (CoG 1.9 m) / **0.341 g** (CoG 2.6 m) | 0.25–0.55 g; high < low | WORKING (literature 0.3–0.45 g, UNVERIFIED) ✅ |
| 8 | lane_change_60 / 80 (double, 3.5 m over 50 / 70 m; path peak 0.18–0.19 g, driver-realised 0.09–0.10 g) | max articulation 0.8–1.4°; RA 0.96–0.99; residual ≤ 0.04°; no lift | RA 0.8–1.6 | WORKING (literature RA 1.0–1.3, UNVERIFIED) ✅ |
| 9 | jackknife_wet_curve_noabs (EBS fault: no ABS, no load sensing, half pedal, steering held) | **81.4°** articulation (empty); drive axle locked 2.95 s | ≥ 30° (must be possible) | ✅ |
| 9 | jackknife_wet_curve_retarder_noabs (lever 5 on wet, ABS failed) | **92°** (empty; reaches the soft cab stop); drive axle locked 1.7 s | ≥ 30° | ✅ |
| 9 | jackknife_wet_curve_abs_50 / _100 (ABS + load sensing working) | 4.8–7.2° max, no lock | ≤ 10° | ✅ |
| 11 | curb_15cm_left_comb, speed_bump_comb (+ Stage 1 curbs) | Fz peak ≤ 3.45× static, trailer roll ≤ 3.3°, cab heave ≤ 46 mm, no teleport | ≤ 4×, ≤ 8°, ≤ 50 mm | WORKING ✅ |
| 12 | dt 50/100/120 Hz and substeps 2/4/8 (section 4) | ≤ 1.0 % (all metrics) | ≤ 5 % | WORKING ✅ |
| 14 | soak_30min_cycle (40 t, 20 × accelerate / lane change / stop) | first vs last cycle cruise 74.0 / 73.5 km/h; standstill speed 4.6e-5 / 4.3e-5 m/s; kingpin error ≤ 0.03 mm; max articulation 2.3°; air ≥ 11.4 bar | no drift | WORKING ✅ |
| 15 | steer_sign_right / reverse_right_comb | +17.4 to +22 °/s forward, −3.1 to −3.9 °/s reversing | sign as solo | DERIVED ✅ |
| — | couple_standstill_locked (R6) | kingpin load 1.005 / 1.014 × static on locked brakes with legs up, speed < 5 mm/s | 0.97–1.03 | DERIVED ✅ |
| — | couple_offset_right_15cm, couple_offset_left_18cm (R5) | couples with a 15 cm / 18 cm offset (4° yaw), bump ≤ 107 kN, kingpin error < 5 mm after the engagement | 1 coupling | WORKING ✅ |
| — | couple_miss_25cm (R5) | no coupling at 25 cm | 0 couplings | WORKING ✅ |
| — | couple_uncouple | 1 coupling, kingpin load 0.97–0.98 × static after raising the legs, coupling bump ≤ 62 kN, dv ≤ 0.14 m/s/step, uncoupled trailer moves ≤ 3 mm | | WORKING ✅ |
| — | manual_mode_shifts (40 t) | gears 2→5 by hand, 4 over-revving requests refused, max 2074 rpm | ≤ 2130 rpm | S1 max revs ✅ |
| — | zero allocation (test) | 0 bytes over 2000 steps, solo and 40 t combination | 0 | CLAUDE.md ✅ |

All 21 Stage 1 solo scenarios still pass. Their values moved slightly:
- 0–80 is now 13.8 s (it was 14.2 s), because the AMT no longer over-revs.
- The dry stop is now 34.9 m (it was 33.3 m), because EBS load sensing gives less rear pressure solo.
- The solo 12 % parking now measures creep in the ground plane, because the rear suspension levels.

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

## 4. Multi-run checks and cost

| Check | Values | Max deviation |
|---|---|---|
| Repeatability 0–60 / 0–80, headings 0°/37°/113° | 9.678 / 13.825 s | 0.00 % |
| dt 50/100/120 Hz: solo 0–80 | 14.05 / 13.83 / 13.85 s | 0.99 % |
| dt: solo dry stop | 34.85 / 34.91 / 34.89 m | **0.09 %** (Stage 1: 0.64 %; before the substep ABS fix: 5.3 %) |
| dt: 40 t dry ABS stop | 40.45 / 40.52 / 40.67 m | 0.29 % (before the fix: 6.5 %) |
| dt: 40 t lane change max articulation | 0.801 / 0.802 / 0.803° | 0.09 % |
| dt: 40 t 0–60 | 27.05 / 26.90 / 26.92 s | 0.35 % |
| substeps 2/4/8: solo / 40 t dry stop | 34.61–34.99 / 40.52–40.82 m | 0.66 % / 0.49 % |

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

## 7. Known gaps / not modelled

- **Not run in Unity or on the phone.** PhysX integration of two bodies with this constraint, cost on the Samsung A, and the feel test (docs/03 Stage 2 gate) are still open.
- **Items not covered by the runner:** §6.10 (reversing to a ramp, tight yard manoeuvres; needs a reversing driver, and a dock or ramp geometry), §6.13 (floating origin and streaming, Unity), §6.15 for input modes other than the direct steer command (touch, gyro: Unity input layer).
- **No chassis–ground or tractor–trailer collision geometry.** Jackknife ends on the soft 90° stop, rollover scenarios stop at wheel lift, and uncoupling requires the legs to be down.
- **Ruts are not modelled**: rays are in the wheel plane only. No dynamic load sharing between interconnected bellows (only static equalisation by levelling). A trial on the kerb strike made no difference (§3a). **No trailer frame torsion**: on a one-sided step the rigid frame lets a tridem axle hang at full droop (0.21 s, empty, §3a). **No unsprung mass**: wheel ends are massless, and the tire is in series with the suspension, so there is no wheel hop.
- **Brakes:** no thermal model or fade; no EBS coupling-force control; ABS uses the true contact-point speed as the reference speed (a real ECU estimates it); the trailer ABS is one generic layout. Compressed-air response is checked against R13 Annex 4 §4.1.1, but the Annex 6 method was not read.
- **Endurance brakes:** the retarder has no oil-temperature derating (only the 600 kW power cap); the EPG-only exhaust brake stage is not separate.
- **AMT:** no GPS predictive strategy; mass and grade are taken from the model, not estimated; the creep function is a fixed torque.
- **Unsourced numbers:** most trailer, air and brake parameters are WORKING_VALUE (see the reference data). The rollover threshold and rearward amplification bands rest on unopened literature.

## 8. Owner feel test (phone, Stage 2 gate), checklist

1. Hill start, 40 t on a steep street: no rollback, the engine note rises under load, no hunting after the start.
2. Emergency stop from 80 km/h, empty and 40 t: cab dive, ABS feel, straight line; then the same on wet.
3. Roundabout at 30–40 km/h with 40 t: trailer roll, offtracking over the inner kerb.
4. Reversing to the ramp with the trailer camera (needs Unity scene): articulation response, the stop at 90°.
5. Long descent with the retarder lever and brake cruise: speed held, no service brake.
6. Coupling to a parked trailer at walking pace: a bump, but not a hit.

Note for each item: mass feel, braking, steering wheel feedback, trailer behaviour.
