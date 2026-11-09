# Stage 2 — Trailer, air brakes, full driveline in Unity: plan and status

Gate definition: `docs/03_ETAPY_I_BRAMKI.md` (Etap 2). Owner-facing report: `docs/reports/GATE-2-draft.md`. Decisions: ADR 0009 (builds on 0004, 0007, 0008). Physics core and runner results: `docs/PHYSICS_VALIDATION.md` (vehicle-physics, unchanged here).
Status 2026-11-09: **everything except the on-phone part is done.** The Galaxy A16 stayed PIN-locked (`isKeyguardShowing=true` at every check), so Gate 0/1/2 device measurements and the owner feel test are still open.

Legend: ✅ done and verified · 🟡 done, verification pending · ⛔ blocked · ⬜ not started

## Checklist
| # | Item | Status | Evidence / where |
|---|---|---|---|
| 1 | Two-body adapter: `TrailerBody` Rigidbody (mass/CoM/inertia from `TrailerModel` incl. cargo), `VehicleBody` steps `CombinationModel`, force + torque per body, no PhysX joint | ✅ | `Vehicle/Runtime/VehicleBody.cs`, `TrailerBody.cs`; PlayMode `MassProperties_Trailer_IncludeCargo`; kingpin error ≤ 0.14 mm in every test |
| 1a | Static placement (tractor with kingpin load, coupled trailer, trailer on legs) | ✅ | `CombinationPlacement`; spawn drift 0.3 mm (`DrivingLab_SpawnPresets_CombinationAtRest`) |
| 1b | Graybox 13.6 m curtainsider at definition dimensions (13.6 × 2.55 × 4.0 m, tridem 385/65, landing gear with moving legs, rear portal, underrun bars, lamps) | ✅ | `GrayboxTrailerBuilder`, prefab `Trailer_Curtainsider_Graybox`; renders `editor-lab-combo-34/-side/-trailer-rear` |
| 1c | Cargo presets empty / 24 t / 40 t gross (= runner `laden40`) | ✅ | `CargoPresets` (same formula as the runner) |
| 1d | Coupling: arm jaw, reverse under, jaw locks; landing gear up/down; uncouple only with legs down | ✅ | `Coupling_UnderLoad_40t…`, `Coupling_Empty…`, end-to-end `DrivingLab_CoupleAndUncouple_ThroughTouchControls` |
| 1e | DrivingLab spawn presets Solo (coupling bay) / Pusta / 24 t / 40 t, launch extra `trailer` | ✅ | lab menu "Zestaw…"; `DrivingLabBootstrap.Spawn/SpawnAt` |
| 2 | Controls: endurance-brake stalk (0 / HS / R1–R4), brake cruise, manual/AMT, parking brake; keyboard X/Z, B, C, G, V | ✅ | `DriverIntent`, `TouchControls`, `KeyboardDriverInput`, HUD |
| 2a | HUD: air pressures (both service circuits), STOP low-air lamp, ABS lamp (active or fault), engine-brake and retarder lamps, articulation / kingpin load / trailer data in telemetry, CSV with the runner's Stage 2 columns | ✅ | `DrivingHud`, `VehicleTelemetryRecorder`; render `editor-lab-chase-hud` |
| 2b | Reversing camera (trailer rear; behind the cab when solo) | ✅ | `ReversingCamera`; renders `editor-lab-reverse-hud`, `editor-rt-reverse-dock-trailer-camera` |
| 2c | Render-texture mirrors on the cab (budget per tier, cab view only) + mirror insets (visual review #14) | ✅ editor · 🟡 phone cost | `RenderTextureMirror`, `VehicleCameraBudget`; renders `editor-lab-cab-eye`, `editor-rt-cab-left-mirror-turn` |
| 3 | Loading dock (5 bays, 1.20 m, rubber bumpers, guide lines) | ✅ | trailer stops on the bumpers, gap 0.120 m (`Capture_ReverseIntoDock_BumperContact`); render `editor-rt-reverse-dock-at-bumpers` |
| 3a | 7 % descent, 600 m, turning plateau, barriers | ✅ | `editor-lab-hill`; `Descent_7pct_40t_BrakeCruise30_NoServiceBrake` (on a test slab) |
| 3b | Wet skid pad 260 × 220 m with R100 circle; ABS/EBS fault toggle for the jackknife demo | ✅ | `editor-lab-wet`, `editor-rt-jackknife-wet-folding` |
| 4 | Engine audio: importer from the tools/audio manifest (ADPCM), EngineAudio fed from the physics, cab/exterior by camera, pneumatic one-shots, road + wind | ✅ editor · 🟡 listening test | `VehicleAudioImporter`, `TruckAudioController`; scene test: 2 voices at idle; APK Sounds 13.1 MB |
| 4a | WAVs out of git; build regenerates when missing | ✅ | `.gitignore`, `build-android.ps1` (`render_all.py --no-previews`), `BuildCommands` imports |
| 5 | UI bug "−0 m" over the gear "−" button | ✅ | cause: visual-QA Screen Space - Camera canvas; HUD now its own pass (`VisualQaRunner`) + near-opaque controls |
| 5a | Black mirror box in the cab view | ✅ | mirror glass shows the render texture |
| 5b | Visual review #14: GAZ vs D/P overlap, opaque controls, rpm contrast, Inter font, mirror strategy | ✅ | commit `6a3387c`; `editor-lab-cab-eye` |
| 6 | PlayMode tests (below) | ✅ | 26 PlayMode + 18 EditMode green |
| 7 | APK | ✅ | `kamion-0.1.0-<sha>.apk`, BUILD_RESULT Succeeded, 48 MB (Sounds 13.1 MB) |
| 7a | Visual QA (18 control cameras + 7 runtime captures), PNGs reviewed, defects fixed | ✅ | `artifacts/visual-qa/DrivingLab*/`; fixed: sign text overflow, mirror aim, reversing-camera script lost from prefab (one MonoBehaviour per file), HUD missing in QA pass |
| 8 | On phone: install, FPS p50/p95/p99 with the combination, mirrors/raycast cost, screenshots | ⛔ | phone PIN-locked |
| 8a | Gate 0 / Gate 1 device measurements | ⛔ | same |
| 9 | Owner feel test (hill start 40 t, emergency stop, roundabout, reversing to the dock, descent, coupling) | ⛔ | needs the phone; checklist in GATE-2-draft |

## Test results (Unity 6000.3.28f1, desktop editor, 2026-11-09)
`pwsh scripts/test.ps1` → EditMode 18/18, PlayMode 26/26 (+3 explicit capture tests: `-Filter Game.Tests.Stage2CaptureTests`).

| Test | Unity | Limit | Runner (PHYSICS_VALIDATION §3) |
|---|---|---|---|
| Coupling under 40 t (reverse at idle creep into the parked trailer) | 1 coupling, bump 43 kN, max Δv 0.14 m/s/step, kingpin load 0.97× static, error 0.14 mm | ≤ 150 kN, < 0.35 m/s, 0.9–1.1 | ≤ 62 kN, 0.97–0.98 |
| Coupling, empty trailer | bump 54 kN, 0.98× static | same | — |
| 40 t parked on 12 %, parking brake, 61 s | drift 1.7 / 4.6 mm (up / down), end speed ≤ 1.2 mm/s | < 1 cm, < 5 mm/s | ≤ 0.39 mm / 300 s |
| 40 t hill start 6 % | rollback 0.1 mm, 0–15 km/h 4.58 s, 5 shifts | < 5 cm, ±10 % of runner, ≤ 14 | 2.3 mm, 4.5 s, 5 shifts |
| 80→0 dry, ABS, empty | 38.94 m | ±10 % | 39.0 m (−0.2 %) |
| 80→0 dry, ABS, 40 t | 40.60 m | ±10 % | 40.5 m (+0.3 %) |
| Jackknife on wet, EBS fault, empty | 80.0° | ≥ 30° | 81.4° |
| Reversing: straight 12 s, steer 0.25, counter-steer −0.5 | straight 0.00°, folds to 42°, back to −38°, max 46°, ≤ 0.08°/step | < 2°, > 5°, < 95°, < 1°/step | — |
| 7 % descent, 40 t, brake cruise 30 km/h | mean 30.04 km/h (28.9–31.2), service brake 0 | 25–35 km/h, no service brake | 30.0 km/h |
| Zero GC, 2000 combination steps (40 t, both bodies, PhysX, visuals) | 0 allocations | 0 | 0 |
| Spawn presets at rest (scene) | drift ≤ 3.6 mm, kingpin error ≤ 0.02 mm | < 5 cm | — |
| Couple/uncouple through the touch buttons (scene, 4× time) | coupled after 3.3 s creep; uncouple with legs up refused; 0.97× static rolling | | |
| Dock bumpers (explicit capture test) | trailer rear stops 0.120 m from the dock face (bumpers 0.12 m) | > 0 | — |
| Stage 1 tests | unchanged (0–60 9.84 s, curb 15 cm Δv 0.092 m/s, solo 12 % ≤ 5 mm) | | |

## Requests to other owners
- **R5–R7 (vehicle-physics):** see ADR 0009 (lateral jaw throat, standstill kingpin share, `CombinationModel.SetTrailer`).
- **R8 (audio):** listening test in the app; retarder whine / compressor / start-stop layers still TODO (AUDIO_DESIGN §4).
- **R9 (rendering-perf):** measure mirror + reversing camera cost on the A16; decide whether Low drops mirror glass rendering to insets only.
- Stage 1 requests R1–R4 still open.

## Next steps
1. Owner unlocks the phone → Gate 0/1 commands from `docs/reports/GATE-1-draft.md`, then `pwsh scripts/device-metrics.ps1 -Launch -DurationSeconds 90 -Scene DrivingLab -Autopilot circle50 -Speed 40 -Trailer 40` (Stage 2 combination run).
2. Owner feel test on the phone (checklist in GATE-2-draft), list of remarks → tuning.
3. Track-A truck/trailer models replace the graybox when ready (same prefab interfaces).
