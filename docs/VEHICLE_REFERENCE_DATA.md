# Vehicle reference data — tractor 4x2 (Stage 1, solo)

Every number used by the physics model, with unit, source and status:

- **SOURCED**: taken from a cited public document.
- **DERIVED**: computed from SOURCED values or from geometry (the calculation is given).
- **WORKING_VALUE**: engineering estimate for this vehicle class, **not** backed by a cited source. These need to be replaced or confirmed later (measurement, literature, OEM data).

The data files are the authority. This table documents them:
`game/Assets/_Project/Vehicle/Physics/Definitions/Data/*.json` (`schemaVersion` 1).

The vehicle is a **generic fictional** modern EU 4x2 long-haul tractor with a high sleeper cab (docs/07, decision D6). It copies no specific OEM model. Where an OEM document is cited, it is used only as a **class reference**.

## Sources

| ID | Source |
|---|---|
| S1 | Volvo Trucks fact sheet D13K500 (EU6 SCR), https://stpi.it.volvo.com/STPIFiles/Volvo/FactSheet/D13K500_Eng_010_338550297.pdf. Same figures on https://www.volvotrucks.co.nz/en-nz/trucks/trucks/volvo-fh/specifications/powertrain.html. Retrieved 2026-11-09 through a web search summary; the PDF itself was **not** opened. Re-check before calling this SOURCED in a gate review. |
| S2 | ZF product data sheet "TraXon Torque", https://www.zf.com/public/org/Product-data-sheet_TraXon-Torque_71520.pdf. It gives the standard 12-speed ratios 12.92 … 1.00, 0.77 and reverse 12.03. Retrieved 2026-11-09 through a web search summary; the PDF was not opened. |
| S3 | Council Directive 92/6/EEC, as amended by 2002/85/EC (speed limitation devices; N3 at 90 km/h). docs/04 §5 also lists the 90 km/h limiter as a fact to verify. |
| S4 | ETRTO / ISO tyre size designation, used geometrically: 315/80 R22.5 means section width 315 mm, aspect ratio 80 %, rim diameter 22.5 in. |
| S5 | UN Regulation No. 13, Annex 4: the definition of mean fully developed deceleration (MFDD) between 0.8 v0 and 0.1 v0. The numeric N3 type-0 requirement was **not** verified (search did not find the text). It is marked UNVERIFIED wherever it is used. |

## Mass and geometry (`tractor_4x2_generic.vehicle.json`)

| Parameter | Value | Unit | Status | Source / derivation |
|---|---|---|---|---|
| Curb mass (sum of mass elements) | 7500 | kg | WORKING_VALUE | Task brief (~7.5 t), typical for this class. There is no cited OEM document. |
| Mass breakdown (frame 900, engine+gearbox 1500, cab 1300, front axle+wheels 800, rear axle+duals 1300, fuel 600, misc 600, fifth wheel 200, cooling/bumper 300) | — | kg | WORKING_VALUE | Engineering split that adds up to 7500 kg |
| Centre of mass (vehicle frame) | x 0, y 1.09, z 2.37 | m | DERIVED | Mass-weighted mean of the elements (`MassProperties.Compute`) |
| Static axle loads | front 4806, rear 2694 | kg | DERIVED | Lever rule from the CoM and the axle positions |
| Inertia tensor | computed | kg m² | DERIVED | Box elements plus the parallel-axis theorem. It is **not** taken from a collider. |
| Wheelbase | 3.70 | m | WORKING_VALUE | Typical 4x2 long-haul tractor; no cited OEM document |
| Front track (wheel centres) | 2.05 | m | WORKING_VALUE | |
| Rear track (dual-pair centres) | 1.83 | m | WORKING_VALUE | |
| Aero CdA (solo tractor) | 7.4 | m² | WORKING_VALUE | Cd ≈ 0.8 × A ≈ 9.3 m² (2.55 m width × ~3.65 m effective height) |
| Air density | 1.2 | kg/m³ | DERIVED | ISA sea level at ~20 °C |

## Tire 315/80 R22.5 (`tire_315_80_r22_5.tire.json`)

| Parameter | Value | Unit | Status | Source / derivation |
|---|---|---|---|---|
| Nominal unloaded diameter | 1.0755 | m | DERIVED | S4: 22.5 × 25.4 + 2 × 0.80 × 315 mm |
| Effective radius (geometry + kinematics) | 0.51 | m | WORKING_VALUE | Between the static loaded and unloaded radius (0.538 m unloaded). It is a single value for both uses (simplification). |
| Width | 0.315 | m | SOURCED | S4 |
| Wheel inertia per tire (tire + rim + hub + rotor) | 20 | kg m² | WORKING_VALUE | ≈ 70 kg tire at r ≈ 0.45 m plus rim and rotor |
| Radial stiffness per tire | 1.0e6 | N/m | WORKING_VALUE | Typical order for heavy truck tires at service pressure |
| Peak μ, dry asphalt, at nominal load | 0.80 | – | WORKING_VALUE | Truck tires are usually quoted at 0.7–0.9 on dry asphalt; no cited source |
| μ load sensitivity | −0.08 per unit (Fz/Fz0 − 1) | – | WORKING_VALUE | |
| Nominal load Fz0 | 30 | kN | WORKING_VALUE | About the steer-axle load per tire |
| Longitudinal slip stiffness / Fz at Fz0 | 12 | 1/– | WORKING_VALUE | |
| Cornering stiffness / Fz at Fz0 | 7 | 1/rad | WORKING_VALUE | |
| Load exponents (K ∝ Fz^p), long. / lat. | 0.85 / 0.7 | – | WORKING_VALUE | Degressive stiffness. This is the source of understeer (see PHYSICS_VALIDATION). |
| MF shape Cx, Ex / Cy, Ey | 1.65, 0 / 1.35, −0.5 | – | WORKING_VALUE | Typical Pacejka-like shapes |
| Relaxation length x / y | 0.30 / 0.50 | m | WORKING_VALUE | |
| Low-speed damping time constant | 0.030 | s | WORKING_VALUE | Chosen for stability and damping at standstill (tuned) |
| Low-speed damping fade-out speed | 3.0 | m/s | WORKING_VALUE | |
| Rolling resistance coefficient | 0.0055 | – | WORKING_VALUE | Plausible for C3 long-haul tires. The EU tyre-label class limits (Reg. (EU) 2020/740) were not verified. |
| Pneumatic trail at zero slip | 0.06 | m | WORKING_VALUE | Used for the steering-feedback estimate only |

Wet asphalt friction scale: **0.625**, so peak μ ≈ 0.5. Status: WORKING_VALUE (`AnalyticGround.SurfaceProps`, runner only. In Unity it will come from the surface table).

## Suspension

| Parameter | Front (parabolic leaf) | Rear (air, 4 bellows) | Unit | Status | Derivation |
|---|---|---|---|---|---|
| Wheel rate per side | 213 000 | 91 000 | N/m | DERIVED from WORKING | k = m_corner (2π f)² with f = 1.5 Hz (front) and 1.3 Hz (rear). Both f values are WORKING_VALUE. |
| Cubic progression | 2.0e6 | 1.5e6 | N/m³ | WORKING_VALUE | |
| Travel (bump to droop) | 0.18 | 0.20 | m | WORKING_VALUE | |
| Static position | mid-travel | mid-travel | – | WORKING_VALUE | Spring preload is solved so that static load sits at mid travel |
| Bump-stop clearance / quadratic rate | 0.025 / 4e7 | 0.025 / 4e7 | m, N/m² | WORKING_VALUE | |
| Damper bump / rebound | 9000 / 18000 | 5000 / 10000 | N s/m | DERIVED from WORKING | ζ ≈ 0.3 of sqrt(k m); rebound is twice bump |
| Damper knee / high-speed slope factor | 0.3 / 0.4 | 0.3 / 0.4 | m/s, – | WORKING_VALUE | |
| Anti-roll stiffness (axle) | 200 000 | 300 000 | N m/rad | WORKING_VALUE | |

Cab suspension (visual/camera only in Stage 1). Pitch 1.5 Hz, roll 1.6 Hz, ζ 0.35, acceleration gain 0.55 rad/s² per m/s², limit ±4°. Status: WORKING_VALUE.

## Engine (`diesel_r6_13l_368kw.engine.json`)

| Parameter | Value | Unit | Status | Source / derivation |
|---|---|---|---|---|
| Configuration | 13 l inline-6 diesel | – | WORKING_VALUE | Class per docs/04 §2.6 and the task brief |
| Peak torque plateau | 2500 Nm @ 980–1270 rpm | N m | SOURCED (class reference) | S1 (D13K500) |
| Rated power | 368 kW @ 1530–1800 rpm | kW | SOURCED (class reference) | S1 |
| Torque at 1530 / 1800 rpm | 2297 / 1952 | N m | DERIVED | T = P / ω from 368 kW |
| Max engine speed | 2100 | rpm | SOURCED (class reference) | S1 |
| Torque at 500 / 600 / 800 / 950 / 1400 / 1900 / 2100 rpm | 900 / 1200 / 1900 / 2450 / 2420 / 1800 / 1500 | N m | WORKING_VALUE | Shape interpolation; the governor fades torque between 1900 and 2100 rpm |
| Motoring drag 0 / 600 / 1000 / 1500 / 2000 / 2400 rpm | 60 / 90 / 130 / 190 / 260 / 320 | N m | WORKING_VALUE | |
| Rotating inertia | 3.5 | kg m² | WORKING_VALUE | |
| Idle / stall | 600 / 350 | rpm | WORKING_VALUE | |
| Turbo lag (NA fraction / boost τ) | 0.45 / 0.35 s | – | WORKING_VALUE | |
| Economy band (for gearing check) | 950–1400 (optimum 1100–1300) | rpm | SOURCED (class reference) | S1 |

## Gearbox and driveline (`amt12_od_traxon_class.gearbox.json`)

| Parameter | Value | Unit | Status | Source / derivation |
|---|---|---|---|---|
| Forward ratios 1–12 | 12.92, 9.98, 7.69, 5.94, 4.57, 3.53, 2.83, 2.19, 1.68, 1.30, 1.00, 0.77 | – | SOURCED | S2 (TraXon standard 12-speed overdrive set) |
| Reverse ratio | 12.03 | – | SOURCED | S2 (first reverse ratio) |
| Gearbox efficiency | 0.97 | – | WORKING_VALUE | |
| Final drive ratio | 3.40 | – | DERIVED | Chosen so that 12th gear runs at ~1160 rpm at 85 km/h and ~1225 rpm at 90 km/h. That is inside the S1 optimum band 1100–1300 rpm. Calculation: 23.6 m/s / 0.51 m × 0.77 × 3.40 = 121 rad/s. |
| Final drive efficiency | 0.97 | – | WORKING_VALUE | |
| Clutch capacity | 4000 | N m | WORKING_VALUE | About 1.6 × peak engine torque |
| Shift phases (torque ramp / neutral / sync / clutch close) | 0.12 / 0.15 / 0.20 / 0.15 | s | WORKING_VALUE | About 0.6 s torque interruption in total |
| Up-shift rpm (light → full throttle) | 1250 → 1750 | rpm | WORKING_VALUE | |
| Down-shift rpm (light → full) | 850 → 1100 | rpm | WORKING_VALUE | |
| Min rpm after up-shift (light → full) | 950 → 1250 | rpm | WORKING_VALUE | |
| Max skip / cooldown | 2 gears / 1.0 s | – | WORKING_VALUE | |
| Launch rpm (light → full) / max launch gear | 800 → 1100 / 4 | rpm, – | WORKING_VALUE | The launch gear is chosen from mass and grade with a 2.5× force margin |
| Speed limiter | 90 | km/h | SOURCED | S3 |
| Limiter band (fuelling fade) | 2 | km/h | WORKING_VALUE | |
| Differential | open | – | WORKING_VALUE | No diff lock in Stage 1 |

## Brakes and steering

| Parameter | Value | Unit | Status | Source / derivation |
|---|---|---|---|---|
| Service brake torque per wheel end (front / rear) | 18 000 / 18 000 | N m | WORKING_VALUE | Enough to lock any wheel of a solo tractor, so ABS is needed |
| Spring (parking) brake torque per rear wheel end | 12 000 | N m | WORKING_VALUE | 12 % grade needs about 2.2 kN m per rear wheel end (DERIVED) |
| Pressure build-up / release τ | 0.25 / 0.30 | s | WORKING_VALUE | First-order lag. The pneumatic system model comes in Stage 2. |
| Spring brake τ | 0.6 | s | WORKING_VALUE | |
| ABS release / re-apply slip | 0.18 / 0.08 | – | WORKING_VALUE | Simple per-wheel modulation |
| ASR (engine intervention) slip threshold | 0.15 | – | WORKING_VALUE | |
| Hill start aid max hold | 2.0 | s | WORKING_VALUE | |
| Max road-wheel angle (virtual centre) | 40 | deg | WORKING_VALUE | |
| Max steer rate (road wheel) | 30 | deg/s | WORKING_VALUE | |
| Ackermann factor | 1.0 | – | WORKING_VALUE | Full Ackermann, with the rear axle as the reference line |
| Steering ratio (handwheel / road wheel) | 20 | – | WORKING_VALUE | |

## Solver settings (not vehicle data)

| Parameter | Value | Status |
|---|---|---|
| Fixed step | 0.01 s (100 Hz) | ADR 0004 |
| Wheel/driveline substeps | 4 (2.5 ms) | WORKING_VALUE. Benchmark on the Samsung A is still pending (ADR 0004). |
| Contact rays per wheel / arc | 15 rays over ±63° | WORKING_VALUE |
| Constraint iterations (clutch + brakes) | 4 | WORKING_VALUE |
