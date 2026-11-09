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

## Measured: empty Boot scene on Galaxy A16 (Stage 0 baseline)
_Not measured yet — see `docs/reports/GATE-0.md` for the state of the measurement._
