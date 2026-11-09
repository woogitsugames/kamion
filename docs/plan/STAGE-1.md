# Stage 1 — Driving lab (tractor solo): plan and status

Gate definition: `docs/03_ETAPY_I_BRAMKI.md` (Etap 1). Owner-facing report: `docs/reports/GATE-1-draft.md`. Decisions: ADR 0008.
Status 2026-11-09: **everything except the on-phone part is done.** The Galaxy A16 was PIN-locked for the whole session, so nothing has run on the device yet.

Legend: ✅ done and verified · 🟡 done, verification pending · ⛔ blocked · ⬜ not started

## Checklist
| # | Item | Status | Evidence / where |
|---|---|---|---|
| 1 | Unity adapter `Vehicle/Runtime/VehicleBody`: Rigidbody mass/CoM/inertia from definitions, 100 Hz, multi-ray ground raycasts, forces at contact points, interpolation | ✅ | PlayMode `MassProperties_FromDefinition_NotFromColliders`; TimeManager 0.01 s |
| 1a | Zero GC per fixed step | ✅ | PlayMode `FixedStep_ZeroGcAllocation`: 2000 steps, 0 GC.Alloc (UTF constraint, control detected) |
| 1b | Merge physics Stage 2 (trailer, air brakes, AMT manual) and adapt | ✅ | merge `92a6a97`; adapter uses `InitParking`, `Gravity`, edge-triggered shifts |
| 2 | Graybox tractor prefab at true dimensions (dims.json + physics wheel geometry), wheels steer/spin/travel, cab on cab-suspension pivot, steering wheel follows handwheel angle | ✅ | `Vehicle/Runtime/Prefabs/Tractor4x2_Graybox.prefab`; EditMode `TractorDimensions_InSyncWith_DimsJson`; renders `lab-truck-34`, `lab-truck-side` |
| 3 | `DrivingLab` scene generated: 400×400 m pad, lane with 10 m marks, R25/R50, figure-eight, ramps 6/12 %, curbs 8/15 cm (platforms + side curbs), speed bump, ruts, surfaces (dry/wet asphalt, concrete, cobbles, gravel, grass), signs, lighting | ✅ | `World/Scenes/DrivingLab.unity` via `DrivingLabSceneBuilder`; renders `lab-overview`, `lab-obstacles`, `lab-ramps`, `lab-surfaces`, `lab-circles` |
| 3a | Surface coefficients for cobbles / gravel / grass | 🟡 | placeholders (WORKING_VALUE, unsourced) in `SurfaceTable` → request R1 |
| 4 | Input layer `IDriverInput`: touch wheel (range 270°/900°, self-centre from speed + aligning torque, dead zone, 20 ms smoothing), analog pedals, D/N/R, A/M + −/+, parking brake, gyro (calibrate, 1€, ±35°, suspend on pause/orientation), keyboard, autopilot | ✅ code + tests · 🟡 feel on phone | EditMode logic tests; PlayMode `SteeringSign_AllInputModes_AgreeWithWheelAngleAndYaw` |
| 4a | Layout on 1080×2340 with notch safe area, two thumbs | ✅ editor · 🟡 phone | `lab-cab-eye`, `lab-chase-hud` (A16 cut-out simulated) |
| 5 | Cameras: cab eye point (dims.json) + damped head motion + look-around; chase; orbit; switch button | ✅ editor · 🟡 phone | `lab-cab-eye`; `CameraRig` |
| 6 | Telemetry overlay (speed, rpm, gear, inputs, per-wheel Fz/slip/slip angle/compression/surface, air, step time, frame percentiles) + CSV toggle (runner column names, `persistentDataPath/telemetry/`) | ✅ | PlayMode autopilot test writes 2795 rows; `tools/telemetry/plot.py` renders it (`docs/reports/gate1/editor-autopilot-r50-telemetry.jpg`) |
| 7 | PlayMode tests: steering sign all modes, 12 % parked 60 s < 1 cm, 0–60 within ±10 % of the runner, curb 15 cm no teleport | ✅ | see "Test results" |
| 8 | DrivingLab in the build (Boot → "Plac testowy" button; launch extra `scene`), APK | ✅ | `kamion-0.1.0-72402a4971.apk` 35.1 MB, BUILD_RESULT Succeeded errors=0 warnings=0 |
| 8a | Visual QA of DrivingLab (9 control cameras), PNGs reviewed, defects fixed | ✅ | `scripts/visual-qa.ps1 -Scene DrivingLab`; 5 defects fixed in `4fbed43` |
| 8b | On phone: install, run, FPS p50/p95/p99 while driving (autopilot), screenshot | ⛔ | phone locked (`isKeyguardShowing=true` at every check) |
| 8c | Gate 0 device measurement (Boot scene) | ⛔ | same reason |
| 9 | Docs: STATUS, this plan, GATE-1-draft, ADR 0008, budgets | ✅ | |
| — | Gate items still open from docs/03: 3× 0–80 repeatable ±3 % **on the phone**; full docs/04 §6 tractor set in Unity (only the subset above runs in PlayMode); owner feel test | ⬜ | Stage 1 gate needs the phone |

## Test results (Unity 6000.3.28f1, desktop editor, 2026-11-09)
`pwsh scripts/test.ps1` → EditMode 18/18, PlayMode 10/10.

| Test | Result | Limit | Reference |
|---|---|---|---|
| 0–60 km/h, flat, full throttle after 1 s on the service brake | **9.84 s** | runner ±10 % (8.71–10.65 s) | runner 9.678 s (PHYSICS_VALIDATION §3, launch_0_80_flat) → +1.7 % |
| Parked 12 %, facing uphill, 61 s after 3 s settle | 1.7–1.9 mm drift | < 10 mm, end speed < 5 mm/s | runner ≤ 0.39 mm over 300 s; the Unity drift is settling in the first ~20 s, then flat |
| Parked 12 %, facing downhill | 2.5–5.0 mm drift (across runs) | < 10 mm | as above |
| Curb 15 cm both wheels at 8 km/h | max \|Δv\| 0.092 m/s per step; unexplained displacement 0.044 mm; Fz peak 2.60× static | 0.35 m/s; 2 mm; 4× | runner 0.096 m/s, 2.88× |
| Steering sign: keyboard, touch wheel, gyro, autopilot | all positive command → positive road-wheel angle → positive yaw rate | sign | docs/04 §6.15 |
| Zero GC, 2000 fixed steps | 0 allocations | 0 | CLAUDE.md |
| Autopilot R50 at 40 km/h (DrivingLab scene, 28 s) | 39.0 km/h, radius error ≤ 0.47 m after 15 s, 2795 CSV rows | ±4 km/h, < 2 m | end-to-end path used for device measurement |
| Solver + adapter cost per step (desktop editor, not PhysX) | 23–26 µs mean | — | **not a phone number** |

## Requests to other owners
- **R1 (vehicle-physics):** own a surface table in the core (`SurfaceId` → friction/rolling-resistance scale) with sourced or explicitly WORKING_VALUE entries for cobbles, gravel, grass, mud. `Vehicle/Runtime/SurfaceTable` then becomes a lookup only.
- **R2 (vehicle-physics):** each AMT upshift of the empty tractor rocks the body ±1.5° in pitch, and the front axle load swings 15–30 kN (visible in `editor-autopilot-r50-telemetry.jpg`). Check whether this is plausible for an empty tractor or too much shift shock.
- **R3 (vehicle-physics):** the parked-12 % settle in Unity (≤ 5 mm) is larger than in the runner (≤ 0.4 mm). It is within the 1 cm gate, but the cause is not known (PhysX integration vs the runner's integrator). Worth a look when the trailer adapter lands.
- **R4 (tools/telemetry):** `plot.py` leaves empty trailer panels for solo CSVs.

## Next steps
1. Owner unlocks the phone → run the Gate 0 and Gate 1 commands in `docs/reports/GATE-1-draft.md`, fill in the numbers.
2. Owner feel test on the A16 (steering range, self-centre, pedal curves, gyro sign), list of remarks → tuning.
3. Stretch: trailer in DrivingLab via `CombinationModel` (two Rigidbodies, no PhysX joint).
4. Measure raycast cost on the phone; batch with `RaycastCommand` if needed.
