# Physics validation run 2026-11-12 21:11  (commit 34940850f)

| scenario | metric | value | min | max | status | source |
|---|---|---|---|---|---|---|
| straight_after_steer_pulse@solo | max_articulation_deg [10..14 s] | 0 |  | 0.05 | PASS | WORKING_VALUE: ADR 0151: released wheel -> trailer realigns; ideal-stick plate friction held 0.41 deg (40 t) for 20 s |
| straight_after_steer_pulse@solo | max_yaw_rate_dps [10..14 s] | 1.139E-05 |  | 0.05 | PASS | WORKING_VALUE: ADR 0151: straight wheels -> no steady turn (was 0.43 deg/s at 40 t) |
| straight_after_steer_pulse@solo | max_articulation_deg | 0 |  | 5 | PASS | WORKING_VALUE: the flick itself stays a mild manoeuvre |
| straight_after_steer_pulse@solo | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: no wheel lift |
| straight_after_steer_pulse@solo | max_dv_step_ms | 0.01342 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes |
| straight_after_steer_pulse@solo | max_fifth_wheel_error_mm | 0 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift |
| straight_after_steer_pulse@empty | max_articulation_deg [10..14 s] | 0.0004278 |  | 0.05 | PASS | WORKING_VALUE: ADR 0151: released wheel -> trailer realigns; ideal-stick plate friction held 0.41 deg (40 t) for 20 s |
| straight_after_steer_pulse@empty | max_yaw_rate_dps [10..14 s] | 7.72E-05 |  | 0.05 | PASS | WORKING_VALUE: ADR 0151: straight wheels -> no steady turn (was 0.43 deg/s at 40 t) |
| straight_after_steer_pulse@empty | max_articulation_deg | 2.364 |  | 5 | PASS | WORKING_VALUE: the flick itself stays a mild manoeuvre |
| straight_after_steer_pulse@empty | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: no wheel lift |
| straight_after_steer_pulse@empty | max_dv_step_ms | 0.01305 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes |
| straight_after_steer_pulse@empty | max_fifth_wheel_error_mm | 0.007432 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift |
| straight_after_steer_pulse@laden40 | max_articulation_deg [10..14 s] | 0.002657 |  | 0.05 | PASS | WORKING_VALUE: ADR 0151: released wheel -> trailer realigns; ideal-stick plate friction held 0.41 deg (40 t) for 20 s |
| straight_after_steer_pulse@laden40 | max_yaw_rate_dps [10..14 s] | 0.001051 |  | 0.05 | PASS | WORKING_VALUE: ADR 0151: straight wheels -> no steady turn (was 0.43 deg/s at 40 t) |
| straight_after_steer_pulse@laden40 | max_articulation_deg | 2.469 |  | 5 | PASS | WORKING_VALUE: the flick itself stays a mild manoeuvre |
| straight_after_steer_pulse@laden40 | wheel_lift | 0 |  | 0 | PASS | WORKING_VALUE: no wheel lift |
| straight_after_steer_pulse@laden40 | max_dv_step_ms | 0.01205 |  | 0.35 | PASS | WORKING_VALUE: no solver explosion / impulse spikes |
| straight_after_steer_pulse@laden40 | max_fifth_wheel_error_mm | 0.008234 |  | 5 | PASS | WORKING_VALUE: kingpin constraint drift |
