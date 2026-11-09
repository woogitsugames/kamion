# Performance budgets (initial, Stage 0)

Status: **initial**. Targets are `WORKING_VALUE`s until measured scenes exist; rendering-perf owns refinement.
Measurement tool: Boot diagnostics (`DiagnosticsSampler`, rolling 600-frame window, nearest-rank percentiles) +
`scripts/device-metrics.ps1` (full-session CSV, percentiles after a 5 s warm-up, `dumpsys meminfo` PSS, battery temperature).

## Targets per device class

| Device / tier | Target FPS | Frame-time p95 | Frame-time p99 | Memory (PSS) | Thermal | Status |
|---|---|---|---|---|---|---|
| Galaxy A16 (Helio G99, Mali-G57 MC2, 4 GB) / Medium | 30 | ≤ 34.0 ms | ≤ 40 ms | ≤ 1.2 GB total app | no throttling (status ≤ light) after 30 min | WORKING_VALUE |
| Galaxy A16 / Low | 30 (60 optional in menus) | ≤ 34.0 ms | ≤ 40 ms | ≤ 1.0 GB | same | WORKING_VALUE |
| Galaxy S24+ / High–Ultra | 60 | ≤ 17.0 ms | ≤ 20 ms | ≤ 2.0 GB | same | not measured (phone not connected yet) |

Rationale: 4 GB devices kill background-heavy apps around 1–1.5 GB PSS; Android `lowmemorykiller` thresholds are device-specific → re-check on A16 when real content exists.

## Per-frame CPU/GPU split (to be filled from Stage 1 profiling)
Physics fixed step, vehicle, world streaming, rendering CPU, GPU — not budgeted yet; needs a non-empty scene.

### Vehicle physics step (Stage 1)
| What | Value | Where measured | Status |
|---|---|---|---|
| Fixed step | 100 Hz (`fixedDeltaTime` 0.01 s), ≤ 10 steps per rendered frame | ProjectSettings/TimeManager.asset | set |
| Tractor solver + Unity adapter per step (excl. PhysX simulate) | 23–26 µs mean | desktop editor, PlayMode tests (`VehicleBody.AverageStepMicros`) | **desktop only — not a phone number** |
| Ground raycasts per step | 60 (4 wheel ends × 15 rays) | by construction | measure PhysX query cost on A16 |
| GC allocations per fixed step | 0 | PlayMode `FixedStep_ZeroGcAllocation` (2000 steps) | ✅ |
| Galaxy A16, DrivingLab with autopilot (R50, 40 km/h): FPS p50/p95/p99, PSS, temperature | — | `pwsh scripts/device-metrics.ps1 -Launch -DurationSeconds 90 -Scene DrivingLab -Autopilot circle50 -Speed 40` | **not measured — phone locked (2026-11-09)** |

### Vehicle combination (Stage 2)
| What | Value | Where measured | Status |
|---|---|---|---|
| Tractor + trailer solver + Unity adapter per step (excl. PhysX simulate), 40 t, cruising with steer | **61 µs mean** (solo tractor 23 µs) | desktop editor (Mono), PlayMode `Combination_FixedStep_ZeroGcAllocation` | **desktop only — not a phone number** |
| Same core, .NET runner (Release, no Unity) | p50 6.4–6.7 µs | `docs/PHYSICS_VALIDATION.md` §4 | desktop |
| Ground raycasts per step, combination | 152 (10 wheel ends × 15 + 2 landing-gear legs) → 15 200/s | by construction | measure on A16; `RaycastCommand` batching is the fallback |
| GC allocations per combination step | 0 | PlayMode, 2000 steps | ✅ |
| Extra cameras in the cab view | 2 mirror cameras alternating (≈ 1 extra scene render/frame on Low/Medium), render textures 224/288/384/512 px high (Low/Medium/High/Ultra), far clip 150/250/400 m, no shadows/post/MSAA | `VehicleCameraBudget` | WORKING_VALUE — measure GPU/CPU on A16 |
| Reversing camera | only in R (or forced), 320×180 … 640×360, every 2nd frame on Low/Medium | `VehicleCameraBudget` | WORKING_VALUE |
| Vehicle audio memory | ADPCM Compressed In Memory, build report "Sounds" 13.1 MB | `artifacts/logs/build-*.log` | matches AUDIO_DESIGN §6 estimate (≈ 13 MB) |
| Galaxy A16, DrivingLab, 40 t combination on autopilot | — | `pwsh scripts/device-metrics.ps1 -Launch -DurationSeconds 90 -Scene DrivingLab -Autopilot circle50 -Speed 40 -Trailer 40` | **not measured — phone locked** |

## Measured: empty Boot scene on Galaxy A16 (Stage 0 baseline)
_Not measured yet — see `docs/reports/GATE-0.md` for the state of the measurement._

## World rendering per tier (look development, ADR 0010) — all UNMEASURED
Assumptions for the imported world (WorldC). Source of the settings: `game/Assets/_Project/Rendering/Resources/QualityProfile.asset`.
"Estimate" columns come from `SceneStats` in the visual-QA runner (CPU-side frustum + LOD selection, submeshes before SRP
batching, `artifacts/visual-qa/WorldC/it5/*/stats.txt`, 2026-11-09) — they are **not GPU counters and not phone numbers**.

| | Low | Medium | High | Ultra |
|---|---|---|---|---|
| Budget: draw calls (before SRP batching) | 250 | 350 | 800 | 1000 |
| Budget: triangles in view | 350 k | 550 k | 1.5 M | 2 M |
| Budget: texture memory | 64 MB | 96 MB | 256 MB | 384 MB |
| Budget: main-light shadow pass | 1.0 ms | 1.5 ms | 2.0 ms | 3.0 ms |
| Estimate: Andersa driver view (draws / tris) | 44 / 269 k | 73 / 485 k | 97 / 838 k (High, LOD bias 1.5) | — |
| Estimate: Rondo Putry from 40 m | 54 / 445 k | 66 / 653 k (over) | 85 / 1.06 M | — |
| Estimate: truck at the gate (draws / shadow-caster draws) | 186 / 170 | 186 / 340 | 189 / 510 | — |
| World textures (8 × 512² / 256², ASTC 6×6 on Android) | ≈ 1.3 MB | same | same | same |
| Status | UNMEASURED | UNMEASURED | UNMEASURED (no flagship) | UNMEASURED (no flagship) |

Findings to act on once the A16 is measured:
- **Graybox tractor + trailer ≈ 178 renderers**: ~180 draws and ×cascades shadow-caster draws by themselves. The real truck
  model must be merged per material (target < 30 draws for the combination) — the world is cheap next to it.
- **Terrain LOD0 (135 k tris per 256 m chunk) dominates the triangle count**; Medium uses LOD bias 0.8 and still exceeds
  550 k in the roundabout overview (not a driving view). If the A16 is vertex-bound: drop LOD0 except the chunk under the
  truck, or ask world-builder for a 1.5 m LOD0.
- **Meshes in the APK: 220.8 MB** (all chunk LODs ship, ADR 0011) → PSS risk on 4 GB; measure with
  `scripts/device-metrics.ps1 -Launch -Scene WorldC -Autopilot route -Speed 50`.
- Post-processing on Medium (HDR + Neutral uber pass at 0.85 scale ≈ 1.8 Mpx) is the first thing to switch off if the GPU
  frame is over 33 ms; Low already runs without it and looks nearly the same.

Device runs to do (phone was PIN-locked 2026-11-09): WorldC Low/Medium, route autopilot at 50 km/h, 90 s and 30 min:
p50/p95/p99, PSS, temperature; Frame Debugger / Arm Performance Studio for the draw and shadow numbers above.
