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

## Measured: empty Boot scene on Galaxy A16 (Stage 0 baseline)
_Not measured yet — see `docs/reports/GATE-0.md` for the state of the measurement._
