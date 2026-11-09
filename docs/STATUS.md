# STATUS — 2026-11-09

## Stage 0 — in progress
- Done: starter docs imported, environment audit, repo + LFS + .gitignore, ADR 0001–0005.
- In progress: Unity Hub + 6000.3.28f1 install, Android toolchain, parallel tracks (physics core in pure C#, truck concepts A1/A2, OSM analysis of industrial-zone candidates).
- Blocked / needs owner: Unity Personal licence activation (sign-in in Unity Hub); Samsung A connected with USB debugging; repo visibility (public vs private per D11).

## Stage 0 — build-qa update (2026-11-09)
- Done: project hygiene + asmdefs, Android player settings + URP tiers as code (ADR 0006), Boot scene with diagnostics overlay and frame-time CSV, batchmode build/visual-QA/test/device scripts, doctor green, clean-clone build verified, APK installed on Galaxy A16, physics + audio code compile in Unity.
- Blocked / needs owner: Galaxy A16 is behind a PIN lock screen — unlock it so the Boot scene can be measured (FPS p50/p95/p99, PSS, temperature, phone screenshot). See docs/reports/GATE-0.md.

## Stage 1 — driving lab (integration, 2026-11-09)
- Done: physics Stage 2 merged (`92a6a97`); Unity adapter `Vehicle/Runtime` (PhysX body + pure C# solver, 100 Hz, zero GC/step, ADR 0008); graybox tractor prefab at dims.json dimensions; generated `DrivingLab` scene (pad, circles, figure-eight, 6/12 % ramps, 8/15 cm curbs, bump, ruts, six surfaces); input layer (`IDriverInput`: touch wheel, pedals, gyro, keyboard, autopilot); cab/chase/orbit cameras; HUD + telemetry overlay + CSV; Boot → DrivingLab; APK `kamion-0.1.0-72402a4971` builds clean; visual QA reviewed, 5 defects fixed. Tests: EditMode 18/18, PlayMode 10/10 (0–60 9.84 s vs runner 9.678 s; 12 % parked drift ≤ 5 mm/60 s; curb 15 cm max Δv 0.092 m/s; 0 GC).
- Plan/checklist: `docs/plan/STAGE-1.md`. Owner report draft: `docs/reports/GATE-1-draft.md`.
- Blocked / needs owner: Galaxy A16 PIN-locked during the whole session → no install/run/FPS/screenshot for Gate 0 or Gate 1; owner feel test pending (steering range, self-centre, gyro sign, pedal curves).
- Open requests: surface table with sourced values in the core (vehicle-physics); AMT shift pitch rock on the empty tractor; trailer in DrivingLab (stretch).

## Stage 2 — trailer, air brakes, full driveline in Unity (integration, 2026-11-09)
- Done: two-body adapter (tractor + trailer Rigidbodies, `CombinationModel`, no PhysX joint, ADR 0009); graybox 13.6 m curtainsider; cargo empty / 24 t / 40 t; coupling, landing gear, uncoupling; DrivingLab presets Solo/Pusta/24 t/40 t, coupling bay, 5-bay loading dock with bumpers, 600 m 7 % road, wet skid pad, ABS/EBS fault toggle; stalk (HS, R1–R4), brake cruise, air gauges, STOP/ABS/HS/RET lamps, articulation telemetry; reversing cameras; render-texture mirrors + cab insets; engine audio imported from tools/audio and driven by the physics; visual review #14 UI fixes (Inter font). Tests: EditMode 18/18, PlayMode 24/24 (+3 explicit captures) (runner match 0.2–2 %: 80→0 ABS 38.9/40.6 m, hill start 4.58 s, descent 30.0 km/h, jackknife 80°). APK `kamion-0.1.0-91960ba015` builds (48.5 MB).
- Plan/checklist: `docs/plan/STAGE-2.md`. Owner report draft: `docs/reports/GATE-2-draft.md`.
- Blocked / needs owner: Galaxy A16 still PIN-locked → no device numbers for Gates 0/1/2, no feel test; decision mirror insets vs look-around.
- Open requests: R5 jaw throat (lateral capture), R6 standstill kingpin share, R7 `CombinationModel.SetTrailer` (vehicle-physics); audio listening test + missing layers; mirror/raycast cost on the A16 (rendering-perf).
